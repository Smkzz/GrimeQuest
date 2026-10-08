"""Conservative, bounded product-identity fallbacks for GTINs missing in Open Facts.

These providers are *identity hints*, NEVER instructions or cleaning safety evidence.
Only a numeric barcode leaves the app, with fixed upstream endpoints.
"""
from __future__ import annotations

import asyncio
from collections import deque
import json
import os
import time

import httpx

from .barcodes import BarcodeSuggestion, _bounded_json, _clean, _matches_gtin, valid_gtin

UPC_URL = "https://api.upcitemdb.com/prod/trial/lookup"
EAN_URL = "https://ean-suche.net/api/produkt/"
SERPER_URL = "https://google.serper.dev/search"
MAX_UPSTREAM_BYTES = 90_000


class ExtendedLookup:
    """Respect free-provider burst limits; never spend on search without an owner key."""

    def __init__(self, serper_key: str | None = None):
        self.serper_key = (
            os.getenv("GQ_SERPER_API_KEY", "").strip()
            if serper_key is None else serper_key.strip()
        )
        self._lock = asyncio.Lock()
        self._usage: dict[str, deque[float]] = {
            "upc_minute": deque(), "upc_day": deque(),
            "ean_hour": deque(), "web_minute": deque(), "web_day": deque(),
        }

    async def _admit(self, *limits: tuple[str, int, float]) -> bool:
        now = time.monotonic()
        async with self._lock:
            for name, _, seconds in limits:
                q = self._usage[name]
                while q and q[0] <= now - seconds:
                    q.popleft()
            if any(len(self._usage[name]) >= ceiling for name, ceiling, _ in limits):
                return False
            for name, _, _ in limits:
                self._usage[name].append(now)
            return True

    async def structured(self, client: httpx.AsyncClient, barcode: str) -> BarcodeSuggestion | None:
        if not valid_gtin(barcode):
            return None

        async def upc() -> BarcodeSuggestion | None:
            # Provider free trial: 100 total queries/day, 6 lookups/minute per IP.
            # Reserve headroom for others sharing Railway's outgoing address.
            if not await self._admit(("upc_minute", 4, 60), ("upc_day", 80, 86400)):
                return None
            data = await _bounded_json(client, UPC_URL, {"upc": barcode}, MAX_UPSTREAM_BYTES)
            if not data or data.get("code") != "OK" or not isinstance(data.get("items"), list):
                return None
            for item in data["items"][:5]:
                if not isinstance(item, dict):
                    continue
                identifiers = [item.get(k) for k in ("ean", "upc", "gtin")]
                if not any(
                    isinstance(v, str) and valid_gtin(v) and _matches_gtin(v, barcode)
                    for v in identifiers
                ):
                    continue
                name = _clean(item.get("title"), 180)
                if len(name) < 3:
                    continue
                return BarcodeSuggestion(
                    barcode, True, name, _clean(item.get("brand"), 100),
                    "", "UPCitemdb", "upc"
                )
            return None

        async def ean() -> BarcodeSuggestion | None:
            # Public/commercial use requires a visible backlink to EAN-Suche.
            if not await self._admit(("ean_hour", 45, 3600)):
                return None
            data = await _bounded_json(client, EAN_URL + barcode, {}, MAX_UPSTREAM_BYTES)
            if not data or data.get("ok") is not True or data.get("found") is not True:
                return None
            returned = data.get("ean")
            if not isinstance(returned, str) or not valid_gtin(returned) or not _matches_gtin(returned, barcode):
                return None
            name = _clean(data.get("product_name"), 180)
            if len(name) < 3:
                return None
            return BarcodeSuggestion(barcode, True, name, "", "", "EAN-Suche", "ean")

        results = await asyncio.gather(upc(), ean(), return_exceptions=True)
        return next((r for r in results if isinstance(r, BarcodeSuggestion)), None)

    async def web(self, client: httpx.AsyncClient, barcode: str) -> BarcodeSuggestion | None:
        if not valid_gtin(barcode) or not self.serper_key:
            return None
        # Optional operator-funded search; never require configuration from players.
        if not await self._admit(("web_minute", 2, 60), ("web_day", 30, 86400)):
            return None
        try:
            async with asyncio.timeout(3.8):
                async with client.stream(
                    "POST", SERPER_URL,
                    json={"q": '"' + barcode + '" product', "num": 5},
                    headers={"X-API-KEY": self.serper_key,
                             "Accept": "application/json",
                             "User-Agent": "GrimeQuest/0.3 (product identity)"},
                ) as response:
                    if response.status_code != 200:
                        return None
                    buffer = bytearray()
                    async for chunk in response.aiter_bytes():
                        if len(buffer) + len(chunk) > MAX_UPSTREAM_BYTES:
                            return None
                        buffer.extend(chunk)
            data = json.loads(buffer)
        except (httpx.HTTPError, ValueError, TypeError, asyncio.TimeoutError):
            return None
        if not isinstance(data, dict) or not isinstance(data.get("organic"), list):
            return None
        # Only a result mentioning the *exact* scanned code is even offered
        # as a possible match. No search title/snippet becomes safety advice.
        for item in data["organic"][:5]:
            if not isinstance(item, dict):
                continue
            name = _clean(item.get("title"), 180)
            snippet = _clean(item.get("snippet"), 500)
            if barcode not in name + " " + snippet or len(name) < 3:
                continue
            return BarcodeSuggestion(barcode, True, name, "", "", "Web search", "web")
        return None
