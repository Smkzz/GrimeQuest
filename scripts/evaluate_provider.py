"""Run a real vision-provider qualification without retaining image contents.

Usage:
  python scripts/evaluate_provider.py eval/manifest.json --output evidence/provider-eval.json

Required environment:
  GQ_PROVIDER_BASE
  GQ_PROVIDER_MODEL
Optional:
  GQ_PROVIDER_KEY

The report stores case ids and scored outcomes only. It never stores image bytes,
data URLs, OCR label text, prompts or provider credentials.
"""
from __future__ import annotations

import argparse
import asyncio
import base64
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import time
from urllib.parse import urlsplit

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server.evaluation import (
    CompareCase,
    EvalManifest,
    ProductCase,
    TargetCase,
    resolve_dataset_file,
    score_compare,
    score_product,
    score_target,
    summarize,
)
from server.provider import ProviderFailure, VisionProvider, verify_openrouter_key_limit, verify_openrouter_zdr_model

MAX_SOURCE_BYTES = 8_000_000
MAX_SOURCE_PIXELS = 12_000_000
CLIENT_MAX_EDGE = 1280
MAX_DATA_URL = 2_700_000


def normalized_data_url(path: Path) -> str:
    """Mirror the browser's upload normalization closely enough for evaluation."""
    raw = path.read_bytes()
    if not raw or len(raw) > MAX_SOURCE_BYTES:
        raise ValueError("Evaluation image must be between 1 byte and 8 MB")
    try:
        with Image.open(io.BytesIO(raw)) as im:
            if getattr(im, "n_frames", 1) != 1:
                raise ValueError("Animated images are not supported")
            width, height = im.size
            if width < 64 or height < 64 or width * height > MAX_SOURCE_PIXELS:
                raise ValueError("Evaluation image must be at least 64x64 and at most 12 megapixels")
            im.load()
            im = ImageOps.exif_transpose(im)
            rgb = Image.new("RGB", im.size, "white")
            if im.mode in ("RGBA", "LA") or "transparency" in im.info:
                rgba = im.convert("RGBA")
                rgb.paste(rgba, mask=rgba.getchannel("A"))
            else:
                rgb.paste(im.convert("RGB"))
            rgb.thumbnail((CLIENT_MAX_EDGE, CLIENT_MAX_EDGE), Image.Resampling.LANCZOS)
            out = io.BytesIO()
            rgb.save(out, "JPEG", quality=85, optimize=True)
    except (OSError, ValueError) as exc:
        raise ValueError("Invalid or unsupported evaluation image") from exc
    data = "data:image/jpeg;base64," + base64.b64encode(out.getvalue()).decode()
    if len(data) > MAX_DATA_URL:
        raise ValueError("Normalized evaluation image exceeds the application upload bound")
    return data


async def run_case(provider: VisionProvider, root: Path, case) -> dict:
    try:
        if isinstance(case, TargetCase):
            image = normalized_data_url(resolve_dataset_file(root, case.image))
            observation = await provider.analyze(image)
            return score_target(case, observation)
        if isinstance(case, CompareCase):
            before = normalized_data_url(resolve_dataset_file(root, case.before))
            after = normalized_data_url(resolve_dataset_file(root, case.after))
            observation = await provider.compare(before, after)
            return score_compare(case, observation)
        if isinstance(case, ProductCase):
            front = normalized_data_url(resolve_dataset_file(root, case.front))
            back = normalized_data_url(resolve_dataset_file(root, case.back))
            observation = await provider.product(front, back)
            return score_product(case, observation.name, observation.label_readable)
        raise TypeError("Unsupported evaluation case")
    except (ProviderFailure, ValueError, OSError) as exc:
        return {
            "id": case.id,
            "task": case.task,
            "critical": [],
            "error": type(exc).__name__,
        }


async def main_async(args) -> int:
    manifest_path = Path(args.manifest).resolve()
    dataset_root = manifest_path.parent
    manifest_bytes = manifest_path.read_bytes()
    manifest = EvalManifest.model_validate_json(manifest_bytes)

    base = os.getenv("GQ_PROVIDER_BASE", "").rstrip("/")
    model = os.getenv("GQ_PROVIDER_MODEL", "")
    key = os.getenv("GQ_PROVIDER_KEY", "")
    if not base or not model:
        raise SystemExit("GQ_PROVIDER_BASE and GQ_PROVIDER_MODEL are required")
    parsed = urlsplit(base)
    if parsed.scheme != "https" or not parsed.hostname:
        raise SystemExit("Provider base must be HTTPS for evaluation")
    if parsed.hostname != "openrouter.ai":
        raise SystemExit("This budget-capped qualification runner supports only the verified OpenRouter billing API.")
    if model in {"openrouter/free", "openrouter/auto"}:
        raise SystemExit("Choose a fixed model identifier; variable free routers cannot qualify.")

    # Critical authorization boundary: NO inference and NO image upload occurs
    # until the provider itself confirms an enforceable, non-resetting total cap.
    try:
        budget_receipt = await verify_openrouter_key_limit(key, maximum_usd=0.50)
    except ProviderFailure as exc:
        raise SystemExit(
            "No paid request was made: use a dedicated OpenRouter API key with a "
            "non-resetting total spend limit of at most $0.50."
        ) from exc

    # A ZDR-filtered endpoint must advertise both JSON response formatting
    # and the parameters used by this adapter. This costs no inference credits.
    try:
        zdr_receipt = await verify_openrouter_zdr_model(key, model)
    except ProviderFailure as exc:
        raise SystemExit(
            "No paid request was made: the selected fixed model lacks a verified "
            "ZDR endpoint with compatible structured-output parameters."
        ) from exc

    cases = manifest.cases[: args.max_cases] if args.max_cases else manifest.cases
    provider = VisionProvider(base, model, key, timeout=args.timeout)
    rows = []
    for index, case in enumerate(cases, start=1):
        row = await run_case(provider, dataset_root, case)
        rows.append(row)
        status = "ERROR" if row.get("error") else ("CRITICAL" if row.get("critical") else "OK")
        print(f"[{index}/{len(cases)}] {case.id} {case.task}: {status}")
        # A call failure or a safety-critical error cannot be recovered into a
        # qualified run. Stop immediately to conserve the finite test budget.
        if row.get("error") or row.get("critical"):
            print("Stopped after an unqualified observation; further calls would waste budget.")
            break
        if args.delay_ms and index != len(cases):
            await asyncio.sleep(args.delay_ms / 1000)

    minimums = None
    if args.allow_small:
        minimums = {
            "target_supported": 1,
            "target_unsupported": 1,
            "compare_clear": 1,
            "compare_nonclear": 1,
            "product": 1,
        }
    summary = summarize(rows, minimums=minimums)
    report = {
        "format": "grimequest-provider-eval-v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "provider_host": parsed.hostname,
        "provider_model": model,
        "provider_key_limit_verified": budget_receipt,
        "zdr_endpoint_preflight": zdr_receipt,
        "routing_policy": {"zdr": True, "data_collection": "deny", "require_parameters": True},
        "cases_requested": len(cases),
        "development_small_dataset": bool(args.allow_small),
        "privacy": "No image bytes, data URLs, OCR label text, prompts, access codes or provider credentials are stored in this report.",
        "summary": summary,
        "rows": rows,
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    print(f"Report: {output}")
    return 0 if summary["qualified"] else 2


def parse_args():
    parser = argparse.ArgumentParser(description="Qualify a GrimeQuest vision provider on a labeled image set.")
    parser.add_argument("manifest", help="Path to evaluation manifest JSON")
    parser.add_argument("--output", default="evidence/provider-eval.json", help="JSON report path")
    parser.add_argument("--delay-ms", type=int, default=250, help="Delay between provider calls")
    parser.add_argument("--timeout", type=float, default=30, help="Per provider call timeout in seconds")
    parser.add_argument("--max-cases", type=int, default=0, help="Run only the first N cases; 0 means all")
    parser.add_argument("--allow-small", action="store_true", help="Development only: lower dataset minimums to one per bucket")
    args = parser.parse_args()
    if args.delay_ms < 0 or not 1 <= args.timeout <= 120 or args.max_cases < 0:
        parser.error("Invalid timing or case-limit arguments")
    return args


def main():
    raise SystemExit(asyncio.run(main_async(parse_args())))


if __name__ == "__main__":
    main()
