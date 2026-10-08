"""Bounded, privacy-preserving Finnish/English label OCR.

Product labels are visually complex. A single preprocessed confidence-aware
pass per photo stays within the server's CPU allowance. Timeouts return an
uncertain, editable draft instead of aborting the whole game. No OCR output
verifies warning completeness or chemical safety.
"""
from __future__ import annotations

import base64
import binascii
from dataclasses import dataclass
from io import BytesIO
import math
import os
import shutil
import subprocess
import unicodedata
from functools import lru_cache
from PIL import Image, ImageOps
from .models import ProductObservation


NAME_UNREADABLE = "Product name unclear — enter manually"


class LabelOcrUnavailable(RuntimeError):
    pass


def _worker_env() -> dict[str, str]:
    """Never pass the app's provider API key or other secrets to subprocesses."""
    env = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "LANG": "C.UTF-8",
        "OMP_THREAD_LIMIT": "1",
        "OMP_NUM_THREADS": "1",
    }
    if os.environ.get("TESSDATA_PREFIX"):
        env["TESSDATA_PREFIX"] = os.environ["TESSDATA_PREFIX"]
    return env


@lru_cache(maxsize=1)
def available() -> bool:
    if not shutil.which("tesseract"):
        return False
    try:
        proc = subprocess.run(
            ["tesseract", "--list-langs"], capture_output=True, timeout=3,
            env=_worker_env(), check=False
        )
        if proc.returncode != 0:
            return False
        langs = set(proc.stdout.decode("utf-8", "replace").split())
        return {"fin", "eng"}.issubset(langs)
    except (OSError, subprocess.SubprocessError):
        return False


@dataclass(frozen=True)
class _Line:
    text: str
    confidence: float
    words: tuple[str, ...]
    top: int


@dataclass(frozen=True)
class _Reading:
    lines: tuple[_Line, ...]
    confidence: float
    letters: int
    height: int

    @property
    def text(self) -> str:
        return "\n".join(line.text for line in self.lines)[:5500]

    def sufficient(self, directions: bool = False) -> bool:
        count = sum(len(word) >= 3 for line in self.lines for word in line.words)
        return (
            self.confidence >= 69
            and self.letters >= (19 if directions else 12)
            and count >= (3 if directions else 2)
        )


def _empty(height: int) -> _Reading:
    return _Reading((), 0, 0, height)


def _parse_tsv(data: bytes, height: int) -> _Reading:
    """Use real word confidences. OCR text is never treated as instructions."""
    groups: dict[tuple[str, str, str, str], list[tuple[str, float, int]]] = {}
    for row in data.decode("utf-8", "replace").splitlines()[1:]:
        fields = row.split("\t", 11)
        if len(fields) != 12 or fields[0] != "5":
            continue
        try:
            confidence = float(fields[10])
            top = int(fields[7])
        except (ValueError, OverflowError):
            continue
        word = unicodedata.normalize("NFKC", fields[11]).strip()[:80]
        if (
            not math.isfinite(confidence) or confidence < 40
            or not any(ch.isalpha() or ch.isdigit() for ch in word)
        ):
            continue
        key = (fields[1], fields[2], fields[3], fields[4])
        groups.setdefault(key, []).append((word, confidence, top))
        if sum(len(v) for v in groups.values()) >= 450:
            break

    lines: list[_Line] = []
    for group in groups.values():
        words = tuple(word for word, _, _ in group)
        text = " ".join(words).strip()[:400]
        if text:
            total = sum(max(1, sum(c.isalnum() for c in word)) for word in words)
            mean = sum(conf * max(1, sum(c.isalnum() for c in word)) for word, conf, _ in group) / total
            lines.append(_Line(text, mean, words, min(top for _, _, top in group)))
    lines.sort(key=lambda line: line.top)
    lines = lines[:70]
    letters = sum(c.isalpha() for line in lines for c in line.text)
    weight = sum(min(sum(c.isalpha() for c in line.text), 100) for line in lines)
    score = (sum(line.confidence * min(sum(c.isalpha() for c in line.text), 100) for line in lines) / weight) if weight else 0
    return _Reading(tuple(lines), score, letters, height)


def _name(reading: _Reading) -> str | None:
    """Do not put one-line decorative noise such as '| MTT' in the name field."""
    excluded = {"DIRECTIONS", "WARNINGS", "VAROITUS", "KÄYTTÖOHJE", "INGREDIENTS",
                "INGREDIENSER", "FRONT", "LABEL", "CAUTION", "ATTENTION", "WARNING"}
    for line in reading.lines:
        pieces = ["".join(c for c in word if c.isalpha()) for word in line.words]
        valid = [w for w in pieces if len(w) >= 3]
        if (
            len(valid) < 2 or len(line.text) > 90 or line.confidence < 78
            or sum(len(word) for word in valid) < 8
            or any(word.upper() in excluded for word in valid)
        ):
            continue
        # A single recognizable decorative word plus "VS" isn't a product name.
        candidate = line.text.strip(" |<>-_=—:·")[:240]
        if sum(c.isalpha() for c in candidate) >= 8:
            return candidate
    return None


def _prepare(jpeg: bytes) -> tuple[bytes, int]:
    """One bounded grayscale/contrast pass, never repeated or persisted."""
    try:
        with Image.open(BytesIO(jpeg)) as image:
            if image.format != "JPEG" or image.width * image.height > 3_000_000:
                raise LabelOcrUnavailable("Label photo dimensions are unsupported.")
            # 1600-pixel full-resolution uploads are unnecessarily costly to
            # OCR on the 0.5 vCPU host. For labels, frame the print close-up.
            image.thumbnail((1200, 1200), Image.Resampling.LANCZOS)
            contrast = ImageOps.autocontrast(image.convert("L"), cutoff=1)
            out = BytesIO()
            contrast.save(out, "PNG", optimize=False)
            return out.getvalue(), contrast.height
    except (OSError, ValueError) as exc:
        raise LabelOcrUnavailable("Label photo could not be processed.") from exc


def _run(image: bytes, *, psm: str, height: int) -> _Reading:
    try:
        result = subprocess.run(
            ["tesseract", "stdin", "stdout", "-l", "fin+eng", "--psm", psm, "tsv"],
            input=image, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            timeout=5.0, check=False, env=_worker_env()
        )
        if result.returncode != 0 or len(result.stdout) > 250_000:
            return _empty(height)
        return _parse_tsv(result.stdout, height)
    except (OSError, subprocess.SubprocessError):
        # The engine may stall on a graphic-heavy bottle under low CPU.
        # subprocess.run kills/reaps on timeout. A missed label is better than
        # a 503 response: the UI asks the player to correct the draft.
        return _empty(height)


def _read(data_url: str, *, directions: bool = False) -> _Reading:
    if not available():
        raise LabelOcrUnavailable("Label reading is temporarily unavailable. Enter the label manually.")
    prefix, sep, encoded = data_url.partition(",")
    if prefix != "data:image/jpeg;base64" or not sep or len(encoded) > 2_800_000:
        raise LabelOcrUnavailable("The label photo is not in a supported format.")
    try:
        jpeg = base64.b64decode(encoded, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise LabelOcrUnavailable("Label photo encoding is invalid.") from exc
    if not 32 <= len(jpeg) <= 2_000_000:
        raise LabelOcrUnavailable("The photo exceeds the OCR input limit.")
    try:
        with Image.open(BytesIO(jpeg)) as img:
            if img.format != "JPEG" or img.width * img.height > 3_000_000:
                raise LabelOcrUnavailable("Label photo dimensions are unsupported.")
            height = img.height
    except OSError as exc:
        raise LabelOcrUnavailable("Label photo is invalid.") from exc

    # One Tesseract call PER PHOTO. No hidden second 6.5-second retry.
    # Dense directions work better with --psm 6; graphic fronts use sparse 11.
    # A timeout returns an empty reading, never a paid/cloud fallback or 503.
    prepared, height = _prepare(jpeg)
    return _run(prepared, psm="6" if directions else "11", height=height)


def recognize_product(front_image: str, back_image: str) -> ProductObservation:
    """Returns unverified editable text; cannot mint chemical-use permissions."""
    front = _read(front_image)
    back = _read(back_image, directions=True)
    candidate = _name(front)
    readable = bool(candidate and front.sufficient() and back.sufficient(directions=True))
    text = (
        "FRONT LABEL — AUTOMATIC OCR (UNVERIFIED)\n"
        + (front.text or "[No reliable text recognized]")
        + "\n\nDIRECTIONS / WARNINGS — AUTOMATIC OCR (UNVERIFIED)\n"
        + (back.text or "[No reliable text recognized]")
    )
    if not readable:
        text += "\n\n[OCR QUALITY WARNING: one or both photos were not read reliably. Retake close-up photos or enter missing text manually. Never assume warnings are complete.]"
    return ProductObservation(
        name=(candidate or NAME_UNREADABLE)[:240],
        label_readable=readable,
        label_text=text[:6000],
        warnings_observed=[],  # Do not infer warnings from OCR.
    )
