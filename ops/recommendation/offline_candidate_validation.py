"""Governed offline comparison for frozen-baseline and Aux candidate retrieval.

The evaluator consumes privacy-minimized, outcome-labelled holdout cases. It deliberately owns no
database access and accepts no profile or household identifiers. Synthetic data may exercise the
format, but can never produce an active-promotion decision.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "recommendation-offline-validation-v1"
UUID = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    re.IGNORECASE,
)
PUBLICATION = re.compile(r"^sha256:[0-9a-f]{64}$")
FORBIDDEN_KEYS = {
    "user_id",
    "profile_id",
    "household_id",
    "email",
    "phone",
    "address",
}


class ValidationInputError(ValueError):
    """Raised when evidence is unsafe, incomplete or not comparable."""


def _reject_identity(value: Any) -> None:
    if isinstance(value, dict):
        forbidden = FORBIDDEN_KEYS.intersection(value)
        if forbidden:
            raise ValidationInputError(f"identity field is forbidden: {sorted(forbidden)[0]}")
        for item in value.values():
            _reject_identity(item)
    elif isinstance(value, list):
        for item in value:
            _reject_identity(item)


def _ids(case: dict[str, Any], field: str) -> list[str]:
    value = case.get(field)
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValidationInputError(f"{field} must be a string array")
    return list(dict.fromkeys(value))


def _recall(ranked: list[str], relevant: set[str]) -> float:
    return len(set(ranked).intersection(relevant)) / len(relevant) if relevant else 0.0


def _reciprocal_rank(ranked: list[str], relevant: set[str]) -> float:
    for rank, dish_id in enumerate(ranked, start=1):
        if dish_id in relevant:
            return 1.0 / rank
    return 0.0


def evaluate(document: dict[str, Any]) -> dict[str, Any]:
    """Return deterministic aggregate gates without retaining case-level user evidence."""
    _reject_identity(document)
    if document.get("schema_version") != SCHEMA_VERSION:
        raise ValidationInputError("unsupported schema_version")
    dataset = document.get("dataset")
    cases = document.get("cases")
    resilience = document.get("resilience_cases")
    if not isinstance(dataset, dict) or not isinstance(cases, list) or not cases:
        raise ValidationInputError("dataset and at least one case are required")
    if not isinstance(resilience, list) or not resilience:
        raise ValidationInputError("at least one Ghar resilience case is required")

    versions: set[str] = set()
    baseline_recall = candidate_recall = 0.0
    baseline_mrr = candidate_mrr = 0.0
    candidate_identity_total = candidate_identity_valid = 0
    baseline_violations = candidate_violations = 0
    slices: dict[str, list[tuple[float, float]]] = defaultdict(list)

    for case in cases:
        if not isinstance(case, dict) or not isinstance(case.get("case_id"), str):
            raise ValidationInputError("each case requires an opaque case_id")
        baseline = _ids(case, "baseline_candidate_ids")
        candidate = _ids(case, "aux_candidate_ids")
        relevant = set(_ids(case, "relevant_dish_ids"))
        forbidden = set(_ids(case, "forbidden_dish_ids"))
        if not relevant:
            raise ValidationInputError("every comparison case requires an observed relevant dish")
        version = case.get("publication_version")
        if not isinstance(version, str) or not PUBLICATION.fullmatch(version):
            raise ValidationInputError("every Aux result requires a full publication hash")
        versions.add(version)
        candidate_identity_total += len(candidate)
        candidate_identity_valid += sum(bool(UUID.fullmatch(item)) for item in candidate)
        baseline_violations += len(set(baseline).intersection(forbidden))
        candidate_violations += len(set(candidate).intersection(forbidden))
        base_case_recall = _recall(baseline, relevant)
        aux_case_recall = _recall(candidate, relevant)
        baseline_recall += base_case_recall
        candidate_recall += aux_case_recall
        baseline_mrr += _reciprocal_rank(baseline, relevant)
        candidate_mrr += _reciprocal_rank(candidate, relevant)
        raw_slices = case.get("slices", ["all"])
        if not isinstance(raw_slices, list) or not raw_slices:
            raise ValidationInputError("each case requires at least one aggregate slice")
        for slice_name in raw_slices:
            if not isinstance(slice_name, str) or not slice_name.strip():
                raise ValidationInputError("slice names must be non-empty strings")
            slices[slice_name].append((base_case_recall, aux_case_recall))

    count = len(cases)
    safe_fallback = all(
        isinstance(item, dict)
        and item.get("aux_state") in {"timeout", "unavailable", "rejected"}
        and item.get("ghar_safe_deterministic_fallback") is True
        for item in resilience
    )
    governance = {
        "consented_real_outcomes": dataset.get("consented_real_outcomes") is True,
        "household_disjoint": dataset.get("household_disjoint") is True,
        "time_split": dataset.get("time_split") is True,
        "not_synthetic": dataset.get("synthetic") is False,
    }
    slice_metrics = {
        name: {
            "case_count": len(values),
            "baseline_recall": round(sum(v[0] for v in values) / len(values), 6),
            "aux_recall": round(sum(v[1] for v in values) / len(values), 6),
        }
        for name, values in sorted(slices.items())
    }
    no_slice_regression = all(
        values["aux_recall"] >= values["baseline_recall"] for values in slice_metrics.values()
    )
    baseline_recall /= count
    candidate_recall /= count
    baseline_mrr /= count
    candidate_mrr /= count
    gates = {
        "governed_holdout": all(governance.values()),
        "single_publication": len(versions) == 1,
        "canonical_identity": candidate_identity_total > 0
        and candidate_identity_valid == candidate_identity_total,
        "zero_aux_safety_violations": candidate_violations == 0,
        "aux_beats_frozen_baseline": candidate_recall > baseline_recall
        and candidate_mrr >= baseline_mrr,
        "no_slice_recall_regression": no_slice_regression,
        "ghar_resilience": safe_fallback,
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "case_count": count,
        "publication_versions": sorted(versions),
        "governance": governance,
        "metrics": {
            "baseline_recall": round(baseline_recall, 6),
            "aux_recall": round(candidate_recall, 6),
            "baseline_mrr": round(baseline_mrr, 6),
            "aux_mrr": round(candidate_mrr, 6),
            "baseline_safety_violations": baseline_violations,
            "aux_safety_violations": candidate_violations,
            "aux_canonical_identity_rate": round(
                candidate_identity_valid / candidate_identity_total, 6
            )
            if candidate_identity_total
            else 0.0,
        },
        "slices": slice_metrics,
        "gates": gates,
        "eligible_for_active_evaluation": all(gates.values()),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = evaluate(json.loads(args.evidence.read_text(encoding="utf-8")))
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0 if result["eligible_for_active_evaluation"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
