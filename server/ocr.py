"""Bounded, local Tesseract text extraction for product labels.

No external vision API, model provider, local photo file or persistent transcript.
All text is untrusted, may be inaccurate, and never authorizes a cleaner.
"""
import base64
import os
import re
import shutil
import subprocess
from functools import lru_cache
from .models import ProductObservation


class LabelOcrUnavailable(RuntimeError):
    pass


@lru_cache(maxsize=1)
def available() -> bool:
    """Check actual OCR binary and Finnish+English packs, not AI credentials."""
    if not shutil.which("tesseract"):
        return False
    try:
        proc = subprocess.run(
            ["tesseract", "--list-langs"], capture_output=True, timeout=3,
            env={**os.environ, "OMP_THREAD_LIMIT": "1"}, check=False
        )
        if proc.returncode != 0:
            return False
        langs = set(proc.stdout.decode("utf-8", "replace").split())
        return {"fin", "eng"}.issubset(langs)
    except (OSError, subprocess.SubprocessError):
        return False


def _text(data_url: str) -> str:
    if not available():
        raise LabelOcrUnavailable("Label text reading is temporarily unavailable. Enter the label manually.")
    prefix, sep, encoded = data_url.partition(",")
    if prefix != "data:image/jpeg;base64" or not sep or len(encoded) > 2_800_000:
        raise LabelOcrUnavailable("The label photo is not in a supported format.")
    try:
        jpeg = base64.b64decode(encoded, validate=True)
        if not 32 <= len(jpeg) <= 2_000_000:
            raise LabelOcrUnavailable("The photo exceeds the OCR input limit.")
        # stdin/stdout means no transient photo or transcript files.
        process = subprocess.run(
            ["tesseract", "stdin", "stdout", "-l", "fin+eng", "--psm", "6"],
            input=jpeg, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            timeout=12, check=False,
            env={**os.environ, "OMP_THREAD_LIMIT": "1", "OMP_NUM_THREADS": "1"},
        )
        if process.returncode != 0 or len(process.stdout) > 80_000:
            raise LabelOcrUnavailable("Could not read the label. Try brighter light or enter the text manually.")
        lines = []
        for raw in process.stdout.decode("utf-8", "replace").splitlines():
            line = " ".join(raw.replace("\x00", "").split())
            if line:
                lines.append(line[:400])
            if len(lines) >= 80:
                break
        return "\n".join(lines)[:5_600]
    except LabelOcrUnavailable:
        raise
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        raise LabelOcrUnavailable("Could not read the label. Try a clearer photo or enter it manually.") from exc


def recognize_product(front_image: str, back_image: str) -> ProductObservation:
    """OCR only. Never interpret warnings, safety or chemical compatibility."""
    front = _text(front_image)
    back = _text(back_image)
    front_lines = [line for line in front.splitlines() if len(line.strip()) >= 3]
    name = (front_lines[0][:240] if front_lines else "Product name unreadable — enter manually")
    # Report both partial reads rather than claiming all warnings are legible.
    readable = (sum(c.isalpha() for c in front) >= 6
                and sum(c.isalpha() for c in back) >= 12)
    sections = (
        "FRONT LABEL — AUTOMATIC OCR (UNVERIFIED)\n" + (front or "[No text recognized]") +
        "\n\nDIRECTIONS / WARNINGS — AUTOMATIC OCR (UNVERIFIED)\n" + (back or "[No text recognized]")
    )
    return ProductObservation(
        name=name, label_readable=readable, label_text=sections[:6000],
        warnings_observed=[]  # Never fabricate interpretations of a warning.
    )
