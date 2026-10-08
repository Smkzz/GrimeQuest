"""Global product identity suggestions, never cleaning-product safety authority.

Read-only Open Facts community sources. Public barcode/name searches send only
the user's explicit numeric GTIN or typed query, never camera/photo contents.
Entries remain unreviewed until a person confirms the exact physical product.
"""
from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass
from typing import Any

import httpx


# Fixed, reviewed Open Facts hosts (no user-defined URLs or redirects).
# Household products first, followed by cosmetics, foods and pet foods.
PLATFORMS: tuple[tuple[str, str, str], ...] = (
    ("general", "Open Products Facts", "https://world.openproductsfacts.org"),
    ("beauty", "Open Beauty Facts", "https://world.openbeautyfacts.org"),
    ("food", "Open Food Facts", "https://world.openfoodfacts.org"),
    ("petfood", "Open Pet Food Facts", "https://world.openpetfoodfacts.org"),
)
SOURCE = PLATFORMS[0][1]
HOST = PLATFORMS[0][2]
FIELDS = "code,product_name,product_name_en,product_name_fi,brands,quantity"
USER_AGENT = "GrimeQuest/0.3 (https://grimequest-web-production.up.railway.app/; product identity)"
MAX_BARCODE_RESPONSE = 65_536
MAX_SEARCH_RESPONSE = 230_000


def valid_gtin(raw: object) -> bool:
    if not isinstance(raw, str) or not re.fullmatch(r"[0-9]{8}|[0-9]{12,14}", raw):
        return False
    total = sum(int(ch) * (3 if i % 2 == 0 else 1)
                for i, ch in enumerate(reversed(raw[:-1])))
    return ((10 - total % 10) % 10) == int(raw[-1])


def normalize_query(raw: object) -> str:
    """Permit international letters/scripts, but bound length and discard controls."""
    if not isinstance(raw, str):
        raise ValueError("Enter a product name or brand.")
    query = " ".join(raw.split())
    if not 2 <= len(query) <= 72 or not any(ch.isalnum() for ch in query):
        raise ValueError("Enter 2 to 72 characters of a product name or brand.")
    if any(not ch.isprintable() for ch in query):
        raise ValueError("Product search must contain ordinary printable text.")
    return query


def _clean(value: object, limit: int) -> str:
    if not isinstance(value, str):
        return ""
    printable = "".join(ch if ch.isprintable() else " " for ch in value)
    return " ".join(printable.split())[:limit]


def _title(record: dict[str, Any]) -> str:
    # Prefer the contributor's main product title, not a hard-coded country.
    for key in ("product_name", "product_name_en", "product_name_fi"):
        name = _clean(record.get(key), 180)
        if len(name) >= 3:
            return name
    for key in sorted(record):
        if key.startswith("product_name_"):
            name = _clean(record.get(key), 180)
            if len(name) >= 3:
                return name
    return ""


def _matches_gtin(returned: str, requested: str) -> bool:
    # Community registries may normalize UPC-A with a leading zero.
    return returned == requested or returned.lstrip("0") == requested.lstrip("0")


@dataclass(frozen=True)
class BarcodeSuggestion:
    barcode: str
    found: bool
    name: str
    brand: str
    quantity: str
    source: str = SOURCE
    category: str = "general"

    def public(self) -> dict:
        platform = next((p for p in PLATFORMS if p[0] == self.category), PLATFORMS[0])
        return {
            "barcode": self.barcode,
            "found": self.found,
            "name": self.name,
            "brand": self.brand,
            "quantity": self.quantity,
            "source": platform[1],
            "category": platform[0],
            "source_url": platform[2] + "/product/" + self.barcode,
            "review_status": "unreviewed",
            "recommendation_permission": False,
            "notice": (
                "Open Facts is community-contributed and may be incomplete or wrong. "
                "Check the exact physical package. A barcode or search result "
                "does not verify cleaning instructions, hazards or surface compatibility."
            ),
        }


def unknown(barcode: str) -> BarcodeSuggestion:
    return BarcodeSuggestion(barcode, False, "", "", "")


def _suggest(record: dict[str, Any], platform: tuple[str, str, str],
             requested: str | None = None) -> BarcodeSuggestion | None:
    code_raw = record.get("code")
    if not isinstance(code_raw, str) or not valid_gtin(code_raw):
        return None
    if requested and not _matches_gtin(code_raw, requested):
        return None
    name = _title(record)
    if not name:
        return None
    return BarcodeSuggestion(
        requested or code_raw, True, name, _clean(record.get("brands"), 100),
        _clean(record.get("quantity"), 80), platform[1], platform[0],
    )


async def _bounded_json(client: httpx.AsyncClient, path: str,
                        params: dict[str, str], max_bytes: int) -> dict | None:
    # URL always points at a constant Open Facts host. Never read unlimited
    # upstream JSON into Railway's 500 MB process and never follow redirects.
    try:
        async with client.stream("GET", path, params=params, headers={
            "User-Agent": USER_AGENT, "Accept": "application/json"
        }) as response:
            if response.status_code != 200:
                return None
            data = bytearray()
            async for chunk in response.aiter_bytes():
                if len(data) + len(chunk) > max_bytes:
                    return None
                data.extend(chunk)
        payload = __import__("json").loads(data)
        return payload if isinstance(payload, dict) else None
    except (httpx.HTTPError, ValueError, TypeError, OverflowError):
        return None


def _rank(suggestion: BarcodeSuggestion, term: str) -> tuple[int, str]:
    title = suggestion.name.casefold()
    brand = suggestion.brand.casefold()
    words = term.casefold()
    score = 0
    if title == words:
        score = 100
    elif title.startswith(words):
        score = 80
    elif words in title:
        score = 60
    elif words in brand:
        score = 45
    else:
        pieces = [x for x in words.split() if len(x) >= 2]
        score = sum(9 for x in pieces if x in title or x in brand)
    if suggestion.category == "general":
        score += 8
    elif suggestion.category == "beauty":
        score += 4
    return -score, suggestion.name.casefold()


class BarcodeLookup:
    """Four worldwide Open Facts categories, one request per fixed host."""

    def __init__(self, transport=None):
        self.transport = transport

    async def lookup(self, barcode: str) -> BarcodeSuggestion:
        if not valid_gtin(barcode):
            raise ValueError("A valid 8, 12, 13 or 14-digit barcode with its check digit is required.")
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(3.5), follow_redirects=False,
            trust_env=False, transport=self.transport
        ) as client:
            for platform in PLATFORMS:
                payload = await _bounded_json(
                    client, platform[2] + "/api/v2/product/" + barcode + ".json",
                    {"fields": FIELDS}, MAX_BARCODE_RESPONSE
                )
                if not payload or payload.get("status") != 1:
                    continue
                record = payload.get("product")
                if not isinstance(record, dict):
                    continue
                candidate = _suggest(
                    {**record, "code": payload.get("code") or record.get("code") or barcode},
                    platform, requested=barcode
                )
                if candidate is not None:
                    return candidate
        return unknown(barcode)

    async def search(self, term: str) -> list[BarcodeSuggestion]:
        query = normalize_query(term)
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(4.0), follow_redirects=False,
            trust_env=False, transport=self.transport
        ) as client:
            async def one(platform: tuple[str, str, str]) -> list[BarcodeSuggestion]:
                payload = await _bounded_json(client, platform[2] + "/cgi/search.pl", {
                    "search_terms": query, "search_simple": "1",
                    "action": "process", "json": "1",
                    "page_size": "8", "fields": FIELDS,
                }, MAX_SEARCH_RESPONSE)
                rows = payload.get("products") if payload else None
                if not isinstance(rows, list):
                    return []
                suggestions = []
                for row in rows[:8]:
                    if isinstance(row, dict):
                        result = _suggest(row, platform)
                        if result:
                            suggestions.append(result)
                return suggestions
            batches = await asyncio.gather(*(one(platform) for platform in PLATFORMS))
        unique: dict[str, BarcodeSuggestion] = {}
        # First source wins for duplicate GTINs; no combinations of upstream
        # data with conflicting or invented fields.
        for batch in batches:
            for item in batch:
                unique.setdefault(item.barcode, item)
        return sorted(unique.values(), key=lambda item: _rank(item, query))[:10]
