"""Same-origin API and static PWA. Default configuration performs zero AI calls."""
import asyncio
from collections import deque
from contextlib import asynccontextmanager
import hmac
import os
from pathlib import Path
import secrets
import time
from urllib.parse import urlsplit

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .config import Settings
from .images import normalize_image, InvalidImage
from .models import ImageRequest, ProductRequest, StartRequest, VerifyRequest, MatchRequest, Attestations, TargetAnalysis
from .policy import CATALOG, PRODUCTS, POLICY_VERSION, match_product, adjudicate
from .provider import VisionProvider, ProviderFailure
from .tickets import Tickets, InvalidTicket

ROOT = Path(__file__).resolve().parent.parent
VERSION = "0.1.0"

HEADERS = {
    "content-security-policy": "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data: blob:; media-src 'self' blob:; connect-src 'self'; worker-src 'self'; manifest-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'",
    "x-content-type-options": "nosniff",
    "referrer-policy": "no-referrer",
    "permissions-policy": "camera=(self), microphone=(), geolocation=(), payment=()",
    "x-frame-options": "DENY",
    "cross-origin-resource-policy": "same-origin",
    "cross-origin-opener-policy": "same-origin",
    "origin-agent-cluster": "?1",
    "x-permitted-cross-domain-policies": "none",
}

class Boundary:
    """Reject wrong hosts, cross-origin calls and oversized streamed bodies early."""
    def __init__(self, app, settings: Settings):
        self.app, self.settings = app, settings
        self.allowed_hosts = {"localhost", "127.0.0.1", "[::1]", "testserver"}
        if settings.app_origin:
            self.allowed_hosts.add(urlsplit(settings.app_origin).hostname)

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        h = {k.decode("latin-1").lower(): v.decode("latin-1") for k, v in scope["headers"]}
        async def safe_send(message):
            if message["type"] == "http.response.start":
                extra = dict(HEADERS)
                if scope["path"].startswith("/api/"):
                    extra["cache-control"] = "no-store"
                elif scope["path"] in ("/", "/index.html", "/sw.js"):
                    extra["cache-control"] = "no-cache"
                if self.settings.app_origin:
                    extra["strict-transport-security"] = "max-age=31536000"
                existing = [(k, v) for k, v in message.get("headers", []) if k.decode().lower() not in extra]
                message["headers"] = existing + [(k.encode(), v.encode()) for k, v in extra.items()]
            await send(message)
        async def reject(status, code, message):
            response = JSONResponse({"error": {"code": code, "message": message}}, status_code=status)
            await response(scope, receive, safe_send)
        host = h.get("host", "")
        try:
            hostname = urlsplit("http://" + host).hostname
        except ValueError:
            hostname = None
        health_probe = scope["method"] == "GET" and scope["path"] == "/api/health"
        if not health_probe and hostname not in self.allowed_hosts and not (hostname == "::1" and "[::1]" in self.allowed_hosts):
            return await reject(400, "HOST", "Host is not allowed.")
        if scope["path"].startswith("/api/") and scope["method"] == "POST":
            allowed_origins = {"http://" + host, "https://" + host}
            if self.settings.app_origin:
                allowed_origins = {self.settings.app_origin.rstrip("/")}
            if h.get("origin") not in allowed_origins or h.get("sec-fetch-site") == "cross-site":
                return await reject(403, "ORIGIN", "Same-origin requests are required.")
            if not self.settings.ready:
                return await reject(503, "LIVE_NOT_CONFIGURED", "Live analysis is not configured. Practice mode never contacts an AI service.")
            if not self.settings.public_live and not hmac.compare_digest(h.get("x-gq-access", "").encode(), self.settings.access_code.encode()):
                return await reject(401, "ACCESS", "Enter the private access code in Settings.")
            if h.get("content-type", "").split(";")[0].strip().lower() != "application/json":
                return await reject(415, "CONTENT_TYPE", "application/json is required.")
            try:
                declared = int(h.get("content-length", "0"))
            except ValueError:
                return await reject(400, "BODY", "Invalid request size.")
            if declared < 0 or declared > 5_700_000:
                return await reject(413, "BODY_LIMIT", "Request exceeds the 5.7 MB limit.")
            body = bytearray()
            try:
                async with asyncio.timeout(12):
                    while True:
                        part = await receive()
                        if part["type"] == "http.disconnect":
                            return
                        body.extend(part.get("body", b""))
                        if len(body) > 5_700_000:
                            return await reject(413, "BODY_LIMIT", "Request exceeds the 5.7 MB limit.")
                        if not part.get("more_body", False):
                            break
            except TimeoutError:
                return await reject(408, "BODY_TIMEOUT", "Upload timed out.")
            done = False
            original_receive = receive
            async def replay():
                nonlocal done
                if not done:
                    done = True
                    return {"type": "http.request", "body": bytes(body), "more_body": False}
                return await original_receive()
            return await self.app(scope, replay, safe_send)
        return await self.app(scope, receive, safe_send)

class Budget:
    """Single-process bounds, not a dollar budget. Production must keep one worker."""
    def __init__(self, limit: int, daily_limit: int = 200):
        self.limit = limit
        self.daily_limit = daily_limit
        self.events: deque[tuple[float, str]] = deque()
        self.active = 0

    @asynccontextmanager
    async def slot(self, client: str):
        now = time.monotonic()
        while self.events and self.events[0][0] < now - 86400:
            self.events.popleft()
        hourly = sum(t >= now - 3600 for t, _ in self.events)
        client_hourly = sum(t >= now - 3600 and c == client for t, c in self.events)
        if self.active >= 2 or hourly >= self.limit or len(self.events) >= self.daily_limit or client_hourly >= 20:
            raise HTTPException(429, "Analysis capacity reached. Try later; no result has been fabricated.")
        self.events.append((now, client))
        self.active += 1
        try:
            yield
        finally:
            self.active -= 1


def create_app(settings: Settings | None = None, provider=None, tickets: Tickets | None = None) -> FastAPI:
    settings = (settings or Settings.from_env()).validate()
    app = FastAPI(
        title="GrimeQuest",
        version=VERSION,
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
        telemetry={"tracing": False, "metrics": False, "logs": False, "operation_spans": False, "auto_configure": False},
    )
    app.add_middleware(Boundary, settings=settings)
    signer = tickets or Tickets(settings.ticket_secret.encode("utf-8") if settings.ticket_secret else None)
    vision = provider or VisionProvider(settings.provider_base, settings.provider_model, settings.provider_key)
    budget = Budget(settings.max_calls_hour, settings.max_calls_day)
    # Only bounded receipts/results are cached, never images or product label text.
    results: dict[str, tuple[float, dict]] = {}
    in_flight: set[str] = set()
    app.state.budget = budget
    decode_slots = asyncio.Semaphore(2)

    async def decode(value: str):
        # Pixel decoding is bounded independently of the paid model-call budget.
        async with decode_slots:
            return await asyncio.to_thread(normalize_image, value)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc):
        return JSONResponse({"error": {"code": "VALIDATION", "message": "Request data is invalid. Images, labels and model output must match the supported schema."}}, status_code=422)

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc):
        return JSONResponse({"error": {"code": "REQUEST", "message": str(exc.detail)}}, status_code=exc.status_code)

    @app.exception_handler(InvalidImage)
    async def image_error(request: Request, exc):
        return JSONResponse({"error": {"code": "IMAGE", "message": str(exc)}}, status_code=422)

    @app.exception_handler(InvalidTicket)
    async def ticket_error(request: Request, exc):
        return JSONResponse({"error": {"code": "TICKET", "message": str(exc)}}, status_code=409)

    @app.exception_handler(ProviderFailure)
    async def provider_error(request: Request, exc):
        return JSONResponse({"error": {"code": "VISION", "message": str(exc)}}, status_code=502)

    @app.get("/api/health")
    async def health():
        return {"status": "ok", "version": VERSION, "live_ready": settings.ready, "policy_version": POLICY_VERSION,
                "catalog_version": CATALOG["version"], "provider_host": urlsplit(settings.provider_base).hostname if settings.ready else None,
                "provider_model": settings.provider_model if settings.ready else None,
                "max_calls_hour": settings.max_calls_hour, "max_calls_day": settings.max_calls_day,
                "access_mode": "public_rate_limited" if settings.public_live else "private_code",
                "workflow_receipts_persistent": bool(settings.ticket_secret),
                "source_sha": os.getenv("RAILWAY_GIT_COMMIT_SHA", ""),
                "deployment_id": os.getenv("RAILWAY_DEPLOYMENT_ID", ""),
                "replica_region": os.getenv("RAILWAY_REPLICA_REGION", ""),
                "real_world_validation": "not_performed"}

    @app.get("/api/catalog")
    async def catalog():
        return CATALOG

    @app.post("/api/match")
    async def match(body: MatchRequest):
        return match_product(body.surface, body.soil, body.product_id, body.attestations, body.hazards)

    @app.post("/api/analyze-target")
    async def analyze_target(body: ImageRequest, request: Request):
        image = await decode(body.image)
        async with budget.slot(request.client.host if request.client else "unknown"):
            observation = await vision.analyze(image.data_url)
        # Validate again even if an injected adapter claims a typed response.
        observation = TargetAnalysis.model_validate(observation.model_dump())
        payload = {"id": secrets.token_urlsafe(16), "before_digest": image.digest,
                   "analysis": observation.model_dump(), "policy": POLICY_VERSION, "catalog": CATALOG["version"]}
        return {"analysis": observation, "target_ticket": signer.sign("target", payload), "provenance": "model_observation"}

    @app.post("/api/analyze-product")
    async def analyze_product(body: ProductRequest, request: Request):
        front, back = await asyncio.gather(decode(body.front_image), decode(body.back_image))
        async with budget.slot(request.client.host if request.client else "unknown"):
            observation = await vision.product(front.data_url, back.data_url)
        return {"observation": observation, "review_status": "unreviewed", "recommendation_permission": False,
                "notice": "Label transcription may be wrong or incomplete. It cannot add compatibility rules. Manually compare your bottle with a reviewed catalog entry."}

    @app.post("/api/start")
    async def start(body: StartRequest):
        target = signer.read(body.target_ticket, "target")
        analysis = TargetAnalysis.model_validate(target["analysis"])
        if target["policy"] != POLICY_VERSION or target["catalog"] != CATALOG["version"]:
            raise HTTPException(409, "Catalog or policy changed; rescan the target.")
        if not analysis.visible_soil or analysis.image_quality != "usable":
            raise HTTPException(409, "A usable before photo with a visible target is required.")
        result = match_product(body.surface, body.soil, body.product_id, body.attestations, analysis.hazards)
        if result["status"] != "eligible":
            return JSONResponse({"match": result}, status_code=409)
        payload = {**target, "surface": body.surface, "soil": body.soil, "product_id": body.product_id,
                   "attestations": body.attestations.model_dump()}
        return {"encounter_id": target["id"], "encounter_ticket": signer.sign("encounter", payload), "match": result,
                "notice": "Do not mix or layer cleaners. An app cannot detect residues or guarantee safety."}

    @app.post("/api/verify")
    async def verify(body: VerifyRequest, request: Request):
        encounter = signer.read(body.encounter_ticket, "encounter")
        if encounter["policy"] != POLICY_VERSION or encounter["catalog"] != CATALOG["version"]:
            raise HTTPException(409, "Policy changed; no verification was issued.")
        current = match_product(encounter["surface"], encounter["soil"], encounter["product_id"],
                                Attestations.model_validate(encounter["attestations"]), encounter["analysis"]["hazards"])
        if current["status"] != "eligible":
            raise HTTPException(409, "Product eligibility changed; no verification was issued.")
        before, after = await asyncio.gather(decode(body.before_image), decode(body.after_image))
        if before.digest != encounter["before_digest"]:
            raise HTTPException(409, "The before photo does not match this encounter.")
        if before.digest == after.digest:
            return {"encounter_id": encounter["id"], "status": "unverifiable", "xp": 0,
                    "reason": "The same image was supplied twice. Capture a new after photo.", "provenance": "deterministic_guard"}
        now = time.monotonic()
        for key, (when, _) in list(results.items()):
            if now - when > 7200:
                del results[key]
        key = encounter["id"] + ":" + after.digest
        final_key = encounter["id"] + ":clear"
        if final_key in results:
            return results[final_key][1]
        if key in results:
            return results[key][1]
        if encounter["id"] in in_flight:
            raise HTTPException(409, "This encounter is already being checked.")
        if len(results) >= 999:
            raise HTTPException(429, "Receipt capacity reached; no analysis was started.")
        in_flight.add(encounter["id"])
        try:
            async with budget.slot(request.client.host if request.client else "unknown"):
                comparison = await vision.compare(before.data_url, after.data_url)
            decision = adjudicate(comparison)
            result = {"encounter_id": encounter["id"], **decision, "provenance": "model_observation",
                      "policy_version": POLICY_VERSION, "before_digest": before.digest, "after_digest": after.digest}
            result["receipt"] = signer.sign("completion", result, ttl=86400)
            results[key] = (now, result)
            if decision["status"] == "clear":
                results[final_key] = (now, result)
            return result
        finally:
            in_flight.discard(encounter["id"])

    app.mount("/", StaticFiles(directory=ROOT / "web", html=True), name="web")
    return app

app = create_app()
