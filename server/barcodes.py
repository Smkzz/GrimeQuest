"""Unverified cleaning-product identification by EAN/UPC/GTIN, not by photo OCR.

Uses Open Products Facts community records. Product names can be missing or
incorrect. No label/surface compatibility, warnings or chemical advice are
inferred from a GTIN or crowd-sourced title. Photos never leave the browser.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

import httpx


SOURCE = "Open Products Facts"
HOST = "https://world.openproductsfacts.org"
USER_AGENT = "GrimeQuest/0.2 (https://grimequest-web-production.up.railway.app/; barcode lookup)"


def valid_gtin(raw: object) -> bool:
    if not isinstance(raw, str) or not re.fullmatch(r"[0-9]{8}|[0-9]{12,14}", raw):
        return False
    total = sum(int(ch) * (3 if i % 2 == 0 else 1)
                for i, ch in enumerate(reversed(raw[:-1])))
    return ((10 - total % 10) % 10) == int(raw[-1])


def _clean(value: object, limit: int) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(c for c in value if c.isprintable()).strip()[:limit]


@dataclass(frozen=True)
class BarcodeSuggestion:
    barcode: str
    found: bool
    name: str
    brand: str
    quantity: str
    source: str = SOURCE

    def public(self) -> dict:
        return {
            "barcode": self.barcode,
            "found": self.found,
            "name": self.name,
            "brand": self.brand,
            "quantity": self.quantity,
            "source": self.source,
            "source_url": HOST + "/product/" + self.barcode,
            "review_status": "unreviewed",
            "recommendation_permission": False,
            "notice": (
                "Community-submitted product names may be wrong, incomplete or outdated. "
                "Check the actual bottle and variant. GTIN lookup never verifies "
                "directions, hazards or surface compatibility."
            )
        }


def unknown(barcode: str) -> BarcodeSuggestion:
    return BarcodeSuggestion(barcode, False, "", "", "")


class BarcodeLookup:
    """No arbitrary URL, redirects, external credential or photo upload."""

    def __init__(self, transport=None):
        self.transport = transport

    async def lookup(self, barcode: str) -> BarcodeSuggestion:
        if not valid_gtin(barcode):
            raise ValueError("A valid 8, 12, 13 or 14-digit barcode with its check digit is required.")
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(4.5), follow_redirects=False,
                trust_env=False, transport=self.transport,
            ) as client:
                async with client.stream(
                    "GET", HOST + "/api/v2/product/" + barcode + ".json",
                    params={"fields": "code,product_name,product_name_fi,product_name_en,brands,quantity"},
                    headers={"User-Agent": USER_AGENT, "Accept": "application/json"}
                ) as response:
                    if response.status_code in (404, 410):
                        return unknown(barcode)
                    if response.status_code != 200:
                        return unknown(barcode)
                    content = bytearray()
                    async for part in response.aiter_bytes():
                        content.extend(part)
                        if len(content) > 65_536:
                            return unknown(barcode)
            payload = httpx.Response(200,content=bytes(content)).json()
            if not isinstance(payload, dict) or payload.get("status") != 1:
                return unknown(barcode)
            record = payload.get("product")
            if not isinstance(record, dict):
                return unknown(barcode)
            remote_code = str(payload.get("code") or record.get("code") or barcode)
            # Some upstream APIs add a leading 0 when normalizing UPC-A.
            if remote_code != barcode and remote_code.lstrip("0") != barcode.lstrip("0"):
                return unknown(barcode)
            name = (
                _clean(record.get("product_name_fi"), 180) or
                _clean(record.get("product_name"), 180) or
                _clean(record.get("product_name_en"), 180)
            )
            brand = _clean(record.get("brands"), 100)
            quantity = _clean(record.get("quantity"), 80)
            if len(name) < 3:
                return unknown(barcode)
            # Preserve the community's product title exactly: combining name
            # and brand can accidentally invent an exact product variant.
            return BarcodeSuggestion(barcode, True, name, brand, quantity)
        except (httpx.HTTPError, ValueError, TypeError, OverflowError):
            # Unavailable community index is not a gameplay failure.
            return unknown(barcode)
