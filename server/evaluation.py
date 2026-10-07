"""Release-grade scoring for GrimeQuest vision-provider qualification.

This module contains no network code and never grants cleaning permissions.
It scores visual observations against a human-labeled manifest and makes
safety-critical failure classes visible separately from ordinary accuracy.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .models import Comparison, Hazard, Soil, Surface, TargetAnalysis
from .policy import adjudicate

SUPPORTED_SURFACES = {"uncoated_glass", "glazed_ceramic"}
SUPPORTED_SOILS = {"grease", "fingerprints", "light_grime"}


class EvalModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class TargetTruth(EvalModel):
    supported: bool
    surface: Surface | None = None
    soil: Soil | None = None
    required_hazards: list[Hazard] = Field(default_factory=list, max_length=6)


class CompareTruth(EvalModel):
    status: Literal["clear", "partial", "unverifiable"]


class ProductTruth(EvalModel):
    label_readable: bool
    name_contains: str | None = Field(default=None, min_length=1, max_length=120)


class TargetCase(EvalModel):
    id: str = Field(pattern=r"^[A-Za-z0-9._-]{1,80}$")
    task: Literal["target"]
    image: str = Field(min_length=1, max_length=240)
    truth: TargetTruth


class CompareCase(EvalModel):
    id: str = Field(pattern=r"^[A-Za-z0-9._-]{1,80}$")
    task: Literal["compare"]
    before: str = Field(min_length=1, max_length=240)
    after: str = Field(min_length=1, max_length=240)
    truth: CompareTruth


class ProductCase(EvalModel):
    id: str = Field(pattern=r"^[A-Za-z0-9._-]{1,80}$")
    task: Literal["product"]
    front: str = Field(min_length=1, max_length=240)
    back: str = Field(min_length=1, max_length=240)
    truth: ProductTruth


EvalCase = Annotated[Union[TargetCase, CompareCase, ProductCase], Field(discriminator="task")]


class EvalManifest(EvalModel):
    version: Literal[1]
    cases: list[EvalCase] = Field(min_length=1, max_length=500)

    @model_validator(mode="after")
    def unique_ids(self):
        ids = [case.id for case in self.cases]
        if len(ids) != len(set(ids)):
            raise ValueError("Evaluation case ids must be unique")
        return self


def resolve_dataset_file(root: Path, relative: str) -> Path:
    """Resolve one manifest path without allowing escape from the dataset root."""
    root = root.resolve()
    candidate = (root / relative).resolve()
    if candidate == root or root not in candidate.parents:
        raise ValueError("Evaluation image path must remain inside the dataset directory")
    if not candidate.is_file():
        raise ValueError(f"Evaluation image is missing: {relative}")
    return candidate


def target_candidate_supported(observation: TargetAnalysis) -> bool:
    return (
        observation.visible_soil
        and observation.image_quality == "usable"
        and observation.surface in SUPPORTED_SURFACES
        and observation.soil in SUPPORTED_SOILS
        and all(h == "none" for h in observation.hazards)
    )


def score_target(case: TargetCase, observation: TargetAnalysis) -> dict:
    predicted_supported = target_candidate_supported(observation)
    hazard_misses = sorted(
        h for h in case.truth.required_hazards if h != "none" and h not in observation.hazards
    )
    exact_surface = case.truth.surface is None or observation.surface == case.truth.surface
    exact_soil = case.truth.soil is None or observation.soil == case.truth.soil
    critical = []
    if not case.truth.supported and predicted_supported:
        critical.append("false_supported")
    if hazard_misses:
        critical.append("hazard_miss")
    return {
        "id": case.id,
        "task": "target",
        "truth_supported": case.truth.supported,
        "predicted_supported": predicted_supported,
        "exact_surface": exact_surface,
        "exact_soil": exact_soil,
        "hazard_misses": hazard_misses,
        "critical": critical,
    }


def score_compare(case: CompareCase, observation: Comparison) -> dict:
    status = adjudicate(observation)["status"]
    critical = ["false_clear"] if status == "clear" and case.truth.status != "clear" else []
    return {
        "id": case.id,
        "task": "compare",
        "expected_status": case.truth.status,
        "predicted_status": status,
        "exact_status": status == case.truth.status,
        "critical": critical,
    }


def score_product(case: ProductCase, name: str, label_readable: bool) -> dict:
    name_match = (
        True
        if case.truth.name_contains is None
        else case.truth.name_contains.casefold() in name.casefold()
    )
    return {
        "id": case.id,
        "task": "product",
        "readable_match": label_readable == case.truth.label_readable,
        "name_match": name_match,
        "critical": [],
    }


def _ratio(numerator: int, denominator: int) -> float | None:
    return None if denominator == 0 else numerator / denominator


def summarize(
    rows: list[dict],
    *,
    minimums: dict[str, int] | None = None,
) -> dict:
    """Summarize scored rows and apply conservative release gates."""
    minimums = minimums or {
        "target_supported": 12,
        "target_unsupported": 12,
        "compare_clear": 8,
        "compare_nonclear": 16,
        "product": 6,
    }
    counts = Counter()
    critical = Counter()
    target_exact = 0
    compare_exact = 0
    product_exact = 0
    target_supported_total = 0
    compare_total = 0
    product_total = 0
    call_failures = 0

    for row in rows:
        if row.get("error"):
            call_failures += 1
            counts["call_failure"] += 1
            continue
        for item in row.get("critical", []):
            critical[item] += 1
        task = row["task"]
        if task == "target":
            bucket = "target_supported" if row["truth_supported"] else "target_unsupported"
            counts[bucket] += 1
            if row["truth_supported"]:
                target_supported_total += 1
                target_exact += int(row["exact_surface"] and row["exact_soil"])
        elif task == "compare":
            bucket = "compare_clear" if row["expected_status"] == "clear" else "compare_nonclear"
            counts[bucket] += 1
            compare_total += 1
            compare_exact += int(row["exact_status"])
        elif task == "product":
            counts["product"] += 1
            product_total += 1
            product_exact += int(row["readable_match"] and row["name_match"])

    minimum_failures = {
        name: {"required": required, "observed": counts[name]}
        for name, required in minimums.items()
        if counts[name] < required
    }
    metrics = {
        "supported_target_exact_accuracy": _ratio(target_exact, target_supported_total),
        "comparison_status_accuracy": _ratio(compare_exact, compare_total),
        "product_readability_name_accuracy": _ratio(product_exact, product_total),
    }
    gates = {
        "dataset_minimums": not minimum_failures,
        "provider_call_failures_zero": call_failures == 0,
        "false_supported_zero": critical["false_supported"] == 0,
        "hazard_misses_zero": critical["hazard_miss"] == 0,
        "false_clears_zero": critical["false_clear"] == 0,
        "supported_target_accuracy_at_least_80pct": (
            metrics["supported_target_exact_accuracy"] is not None
            and metrics["supported_target_exact_accuracy"] >= 0.80
        ),
        "comparison_accuracy_at_least_80pct": (
            metrics["comparison_status_accuracy"] is not None
            and metrics["comparison_status_accuracy"] >= 0.80
        ),
        "product_accuracy_at_least_80pct": (
            metrics["product_readability_name_accuracy"] is not None
            and metrics["product_readability_name_accuracy"] >= 0.80
        ),
    }
    return {
        "qualified": all(gates.values()),
        "counts": dict(counts),
        "minimum_failures": minimum_failures,
        "critical_failures": dict(critical),
        "call_failures": call_failures,
        "metrics": metrics,
        "gates": gates,
    }
