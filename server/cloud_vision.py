"""Google Cloud Vision text recognition, independently consented and cost-gated.

Two normalized in-memory JPEGs -> one synchronous EU-region Vision REST batch.
No provider key in URLs, browser, logs or transcripts; no retries or storage.
Cloud OCR never grants chemical/surface compatibility or hygiene claims.
"""
from __future__ import annotations

import math
import re
import unicodedata
from urllib.parse import quote

import httpx

from .models import ProductObservation


NAME_UNREADABLE = "Product name unclear — enter manually"
VISION_HOST = "https://eu-vision.googleapis.com"
_STOP_WORDS = frozenset({
    "WARNING", "CAUTION", "DANGER", "VAROITUS", "KÄYTTÖOHJE", "KAYTTOOHJE",
    "DIRECTIONS", "INSTRUCTIONS", "INGREDIENTS", "INNEHÅLL", "AINEKSET",
    "ATTENTION", "NOTICE", "PRECAUTION", "STORAGE", "SÄILYTYS",
})


class CloudVisionUnavailable(RuntimeError):
    """Sanitized; must never contain API credentials or upstream responses."""


def _clean_text(raw: object, limit: int = 2600) -> str:
    if not isinstance(raw, str):
        return ""
    cleaned = unicodedata.normalize("NFKC", raw[:limit * 2])
    lines = []
    for line in cleaned.splitlines():
        # Reject hidden control characters and excessive whitespace.
        line = "".join(ch for ch in line if ch.isprintable())
        line = " ".join(line.split()).strip()[:260]
        if line:
            lines.append(line)
        if len(lines) == 65:
            break
    return "\n".join(lines)[:limit]


def _text_from_response(item: object) -> str:
    if not isinstance(item, dict) or item.get("error"):
        return ""
    full = item.get("fullTextAnnotation")
    if isinstance(full, dict):
        text = _clean_text(full.get("text"))
        if text:
            return text
    annotations = item.get("textAnnotations")
    if isinstance(annotations, list) and annotations and isinstance(annotations[0], dict):
        return _clean_text(annotations[0].get("description"))
    return ""


def _page_confidence(item: object) -> float | None:
    if not isinstance(item, dict):
        return None
    full = item.get("fullTextAnnotation")
    if not isinstance(full, dict):
        return None
    pages = full.get("pages")
    if not isinstance(pages, list):
        return None
    values: list[float] = []
    for page in pages[:6]:
        if not isinstance(page, dict):
            continue
        val = page.get("confidence")
        if type(val) in (float, int) and math.isfinite(val) and 0 < val <= 1:
            values.append(float(val))
    return sum(values) / len(values) if values else None


def _plausible_name(front: str, confidence: float | None) -> str | None:
    if confidence is not None and confidence < 0.68:
        return None
    for line in front.splitlines()[:14]:
        if len(line) > 85:
            continue
        words = ["".join(c for c in part if c.isalpha()) for part in line.split()]
        valid = [w for w in words if len(w) >= 3]
        if len(valid) < 2 or sum(len(word) for word in valid) < 8:
            continue
        if any(word.upper() in _STOP_WORDS for word in valid):
            continue
        name = line.strip(" |<>-_=—:·")[:240]
        if len(name) >= 8 and not name.startswith("Product name unclear"):
            return name
    return None


def _image_payload(data_url: str) -> str:
    if not isinstance(data_url, str) or len(data_url) > 2_800_000:
        raise CloudVisionUnavailable("The label image cannot be read. Enter its text manually.")
    prefix, separator, encoded = data_url.partition(",")
    if not separator or prefix != "data:image/jpeg;base64" or not 32 <= len(encoded) <= 2_700_000:
        raise CloudVisionUnavailable("The label image cannot be read. Enter its text manually.")
    return encoded


class CloudVisionReader:
    """Fixed EU endpoint; real HTTP can be replaced by MockTransport in tests."""

    def __init__(self, api_key: str = "", project_id: str = "", transport=None, timeout: float = 12.0):
        self._key = api_key
        self._project_id = project_id
        self._transport = transport
        self._timeout = timeout

    @property
    def ready(self) -> bool:
        return (
            isinstance(self._key, str) and 20 <= len(self._key) <= 256
            and isinstance(self._project_id, str)
            and re.fullmatch(r"[a-z][a-z0-9-]{4,61}[a-z0-9]", self._project_id) is not None
        )

    @property
    def endpoint(self) -> str:
        # Project syntax is validated before any API call to prevent URL injection.
        if not self.ready:
            raise CloudVisionUnavailable("Automatic label reading is not configured.")
        return f"{VISION_HOST}/v1/projects/{quote(self._project_id, safe='')}/locations/eu/images:annotate"

    async def read(self, front_url: str, back_url: str) -> ProductObservation:
        if not self.ready:
            raise CloudVisionUnavailable("Automatic label reading is not configured.")
        front = _image_payload(front_url)
        back = _image_payload(back_url)
        request = {
            "requests": [
                {
                    "image": {"content": front},
                    "features": [{"type": "TEXT_DETECTION"}],
                    "imageContext": {"languageHints": ["fi", "en"]},
                },
                {
                    "image": {"content": back},
                    "features": [{"type": "DOCUMENT_TEXT_DETECTION"}],
                    "imageContext": {"languageHints": ["fi", "en"]},
                },
            ]
        }
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(self._timeout),
                follow_redirects=False,
                trust_env=False,
                transport=self._transport
            ) as client:
                async with client.stream(
                    "POST",
                    self.endpoint,
                    headers={"x-goog-api-key": self._key, "content-type": "application/json"},
                    json=request
                ) as response:
                    if response.status_code != 200:
                        raise CloudVisionUnavailable("Google label recognition is unavailable. Enter text manually.")
                    received = bytearray()
                    async for part in response.aiter_bytes():
                        received.extend(part)
                        if len(received) > 1_500_000:
                            raise CloudVisionUnavailable("The recognition response was too large.")
            data = __import__("json").loads(received)
            entries = data.get("responses") if isinstance(data, dict) else None
            if not isinstance(entries, list) or len(entries) != 2 or any(
                not isinstance(x, dict) or x.get("error") for x in entries
            ):
                raise CloudVisionUnavailable("The label scan was incomplete. Enter text manually.")
            front_text = _text_from_response(entries[0])
            back_text = _text_from_response(entries[1])
            name = _plausible_name(front_text, _page_confidence(entries[0]))
            text = (
                "FRONT LABEL — GOOGLE CLOUD VISION (UNVERIFIED)\n"
                + (front_text or "[No reliable text recognized]") +
                "\n\nDIRECTIONS / WARNINGS — GOOGLE CLOUD VISION (UNVERIFIED)\n"
                + (back_text or "[No reliable text recognized]")
            )
            readable = bool(name and len(front_text) >= 12 and len(back_text) >= 20)
            if not readable:
                text += (
                    "\n\n[TEXT QUALITY WARNING: The name, directions or warnings "
                    "could not be fully recognized. Consult the original bottle.]"
                )
            return ProductObservation(
                name=(name or NAME_UNREADABLE),
                label_readable=readable,
                label_text=text[:6000],
                warnings_observed=[],
            )
        except CloudVisionUnavailable:
            raise
        except (httpx.HTTPError, ValueError, TypeError, KeyError, OverflowError) as exc:
            raise CloudVisionUnavailable(
                "Automatic label recognition is temporarily unavailable. Enter text manually."
            ) from exc
