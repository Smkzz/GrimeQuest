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
from .cloud_vision import CloudVisionReader, CloudVisionUnavailable
from .barcodes import BarcodeLookup, valid_gtin
from .models import ImageRequest, ProductRequest, BarcodeRequest, StartRequest, VerifyRequest, MatchRequest, Attestations, TargetAnalysis
from .policy import CATALOG, PRODUCTS, POLICY_VERSION, match_product, adjudicate
from .provider import VisionProvider, ProviderFailure, verify_openrouter_zdr_model, verify_openrouter_beta_spend_cap
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
                if scope["path"].startswith("/api/") or scope["path"] in ("/update.html", "/update.js", "/update.css"):
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
            # Same-origin, JSON and upload bounds apply to Cloud Vision OCR.
            # The operator owns its API key; players never supply credentials.
            local_ocr = scope["path"] in ("/api/read-labels", "/api/product-lookup")
            if not local_ocr and not self.settings.ready:
                return await reject(503, "LIVE_NOT_CONFIGURED", "AI analysis is unavailable; camera quests and text-only OCR remain usable.")
            if not local_ocr and not self.settings.public_live and not hmac.compare_digest(h.get("x-gq-access", "").encode(), self.settings.access_code.encode()):
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


class BetaPreflight:
    """Fail-closed ZDR/model/key checks before any paid public preview request."""
    def __init__(self, settings: Settings, provider_injected: bool):
        self.settings = settings
        self.governed = settings.public_live and not provider_injected
        self.verified = not self.governed
        self.valid_until = 0.0
        self._lock = asyncio.Lock()

    async def refresh(self) -> bool:
        if not self.governed:
            return True
        if time.monotonic() < self.valid_until:
            return self.verified
        async with self._lock:
            if time.monotonic() < self.valid_until:
                return self.verified
            self.verified = False
            stage = 'CONFIG'
            try:
                if (urlsplit(self.settings.provider_base).hostname != 'openrouter.ai'
                        or self.settings.provider_model != 'google/gemini-2.5-flash-lite'
                        or not self.settings.provider_key):
                    raise ProviderFailure('Public preview requires the fixed ZDR model and an operator-held key.')
                stage = 'SPEND_CAP'
                spend = await verify_openrouter_beta_spend_cap(self.settings.provider_key)
                stage = 'ZDR_ROUTE'
                endpoints = await verify_openrouter_zdr_model(self.settings.provider_key, self.settings.provider_model)
                stage = 'FINAL'
                if not spend['verified'] or not endpoints['verified']:
                    raise ProviderFailure('Provider preflight is incomplete.')
                self.verified = True
                self.valid_until = time.monotonic() + 300
                print('GQ_PUBLIC_BETA_PREFLIGHT_PASS', flush=True)
            except Exception as exc:
                # Only codes from this reviewed closed vocabulary may reach logs.
                # Never log untrusted exception text, balances, keys or photos.
                known = {'KEY_METADATA_UNAVAILABLE','KEY_METADATA_SCHEMA','SPEND_CAP_MISSING',
                         'SPEND_CAP_RESETTING','BYOK_NOT_CAPPED','WRONG_KEY_ROLE',
                         'SPEND_CAP_INVALID','SPEND_CAP_EXHAUSTED','KEY_METADATA_NETWORK_ERROR'}
                reason = str(exc) if isinstance(exc, ProviderFailure) and str(exc) in known else 'UNSPECIFIED'
                self.verified = False
                self.valid_until = time.monotonic() + 45
                print('GQ_PUBLIC_BETA_PREFLIGHT_BLOCKED_' + stage + '_' + reason, flush=True)
            return self.verified

    def cached_ready(self) -> bool:
        return self.verified and (not self.governed or time.monotonic() < self.valid_until)

    async def require(self) -> None:
        if not await self.refresh():
            raise HTTPException(503, 'AI preview is temporarily unavailable; Camera Quest works without it.')

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


def create_app(settings: Settings | None = None, provider=None, tickets: Tickets | None = None,
               label_reader: CloudVisionReader | None = None, barcode_lookup: BarcodeLookup | None = None) -> FastAPI:
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
    beta = BetaPreflight(settings, provider is not None)
    app.state.beta = beta
    cloud_labels = label_reader if label_reader is not None else CloudVisionReader(
        settings.google_vision_api_key, settings.google_vision_project_id
    )
    cloud_labels_enabled = settings.google_vision_enabled and cloud_labels.ready
    app.state.cloud_labels = cloud_labels
    product_index = barcode_lookup or BarcodeLookup()
    app.state.barcode_index = product_index
    barcode_events: deque[float] = deque()
    barcode_cache: dict[str, tuple[float, dict]] = {}
    barcode_lock = asyncio.Lock()
    app.state.barcode_requests = barcode_events

    @app.on_event('startup')
    async def preflight_public_beta():
        if beta.governed:
            # OpenRouter metadata preflight; no model inference.
            asyncio.create_task(beta.refresh())
        if cloud_labels_enabled and os.getenv("GQ_VISION_DIAGNOSTIC_ON_START", "0") == "1":
            # Operator-only temporary qualification, never on by default.
            # Synthetic local image, two Cloud Vision feature units per run.
            async def check_vision():
                try:
                    code = await cloud_labels.synthetic_diagnostic()
                except Exception:
                    code = "PROBE_FAILURE"
                # Strict fixed vocabulary: this MUST NOT log keys, data,
                # raw Google errors, decoded OCR text or arbitrary strings.
                permitted = ("PASS_HTTP_200", "CONFIG_MISSING", "NETWORK_TIMEOUT",
                             "NETWORK_OR_PARSE", "PROBE_FAILURE")
                if code not in permitted and not (
                    code.startswith("HTTP_") and len(code) <= 75 and all(
                        c.isascii() and (c.isupper() or c.isdigit() or c == "_")
                        for c in code
                    )
                ):
                    code = "PROBE_FAILURE"
                print("GQ_CLOUD_VISION_DIAGNOSTIC_" + code, flush=True)
            asyncio.create_task(check_vision())
    budget = Budget(settings.max_calls_hour, settings.max_calls_day)
    # Only bounded receipts/results are cached, never images or product label text.
    results: dict[str, tuple[float, dict]] = {}
    in_flight: set[str] = set()
    app.state.budget = budget
    decode_slots = asyncio.Semaphore(2)
    ocr_slots = asyncio.Semaphore(1)
    ocr_events: deque[float] = deque()
    app.state.ocr_calls = ocr_events
    # These limits are conservative demo throttles, NOT an external hard
    # monetary budget. Set project quotas and billing controls in Google Cloud.
    OCR_HOURLY_SCANS = 6
    OCR_DAILY_SCANS = 12

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

    @app.exception_handler(CloudVisionUnavailable)
    async def ocr_error(request: Request, exc):
        # Stable diagnostic codes only. No Google raw response, API key, OCR
        # transcript, project identifier or user's image is ever logged.
        code = exc.code
        if not (isinstance(code, str) and 1 <= len(code) <= 75 and
                all(c.isascii() and (c.isupper() or c.isdigit() or c == "_") for c in code)):
            code = "UNKNOWN"
        print("GQ_CLOUD_VISION_OCR_FAILURE_" + code, flush=True)
        return JSONResponse(
            {"error": {"code": "OCR", "message": str(exc)}}, status_code=503
        )

    @app.exception_handler(ProviderFailure)
    async def provider_error(request: Request, exc):
        return JSONResponse({"error": {"code": "VISION", "message": str(exc)}}, status_code=502)

    @app.get("/api/health")
    async def health():
        return {"status": "ok", "version": VERSION, "live_ready": settings.ready and beta.cached_ready(), "policy_version": POLICY_VERSION,
                "catalog_version": CATALOG["version"], "provider_host": urlsplit(settings.provider_base).hostname if settings.ready else None,
                "provider_model": settings.provider_model if settings.ready else None,
                "max_calls_hour": settings.max_calls_hour, "max_calls_day": settings.max_calls_day,
                "access_mode": "public_rate_limited" if settings.public_live else "private_code",
                "workflow_receipts_persistent": bool(settings.ticket_secret),
                "source_sha": os.getenv("RAILWAY_GIT_COMMIT_SHA", ""),
                "deployment_id": os.getenv("RAILWAY_DEPLOYMENT_ID", ""),
                "replica_region": os.getenv("RAILWAY_REPLICA_REGION", ""),
                "real_world_validation": "not_performed", "label_ocr_ready": cloud_labels_enabled,
                "label_ocr_processor": "google_cloud_vision" if cloud_labels_enabled else "disabled"}

    @app.get("/api/catalog")
    async def catalog():
        return CATALOG

    @app.post("/api/match")
    async def match(body: MatchRequest):
        return match_product(body.surface, body.soil, body.product_id, body.attestations, body.hazards)

    @app.post("/api/analyze-target")
    async def analyze_target(body: ImageRequest, request: Request):
        await beta.require()
        image = await decode(body.image)
        async with budget.slot(request.client.host if request.client else "unknown"):
            observation = await vision.analyze(image.data_url)
        # Validate again even if an injected adapter claims a typed response.
        observation = TargetAnalysis.model_validate(observation.model_dump())
        payload = {"id": secrets.token_urlsafe(16), "before_digest": image.digest,
                   "analysis": observation.model_dump(), "policy": POLICY_VERSION, "catalog": CATALOG["version"]}
        return {"analysis": observation, "target_ticket": signer.sign("target", payload), "provenance": "model_observation"}

    @app.post("/api/product-lookup")
    async def product_lookup(body: BarcodeRequest):
        """Opt-in community lookup by identifier only. Never send photos."""
        gtin = body.barcode
        if not valid_gtin(gtin):
            raise HTTPException(422, "Check the digits printed beneath the barcode. The check digit does not match.")
        now = time.monotonic()
        async with barcode_lock:
            cached = barcode_cache.get(gtin)
            if cached and cached[0] > now:
                return cached[1]
            while barcode_events and barcode_events[0] < now - 60:
                barcode_events.popleft()
            if len(barcode_events) >= 8:
                raise HTTPException(429, "Community lookup is temporarily busy. Enter the product name manually.")
            barcode_events.append(now)
        suggestion = await product_index.lookup(gtin)
        public = suggestion.public()
        # Community names are only suggestions and never manufacturer evidence.
        async with barcode_lock:
            if len(barcode_cache) >= 128:
                barcode_cache.clear()
            barcode_cache[gtin] = (time.monotonic() + (3600 if public["found"] else 300), public)
        return public

    @app.post("/api/read-labels")
    async def read_labels(body: ProductRequest, request: Request):
        """One consented EU Cloud Vision batch for the two normalized images."""
        if not cloud_labels_enabled:
            raise HTTPException(503, "Automatic label reading is unavailable. Enter the label manually.")
        now = time.monotonic()
        while ocr_events and ocr_events[0] < now - 86400:
            ocr_events.popleft()
        hourly = sum(t >= now - 3600 for t in ocr_events)
        if len(ocr_events) >= OCR_DAILY_SCANS or hourly >= OCR_HOURLY_SCANS or ocr_slots.locked():
            raise HTTPException(429, "Automatic reading capacity reached. Enter the label manually.")
        # All request validation and same-origin/consent guards ran before this.
        async with ocr_slots:
            front, back = await asyncio.gather(decode(body.front_image), decode(body.back_image))
            ocr_events.append(time.monotonic())
            observation = await cloud_labels.read(front.data_url, back.data_url)
        return {
            "observation": observation,
            "review_status": "unreviewed",
            "recommendation_permission": False,
            "extraction": "google_cloud_vision",
            "provider_calls": 1,  # One batch with two billable OCR image units.
            "notice": "Google Cloud Vision text may be wrong or incomplete. Compare the name, directions and every warning with the original bottle. OCR never approves a cleaner.",
        }

    @app.post("/api/analyze-product")
    async def analyze_product(body: ProductRequest, request: Request):
        await beta.require()
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
        await beta.require()
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
