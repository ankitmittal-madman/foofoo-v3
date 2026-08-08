"""Deterministic Aux promotion and kill-switch decision from aggregate governed evidence."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "recommendation-rollout-decision-v1"
PUBLICATION = re.compile(r"^sha256:[0-9a-f]{64}$")
FORBIDDEN_KEYS = {"user_id", "profile_id", "household_id", "request_id", "email", "phone"}
TARGETS = {
    "min_shadow_events",
    "min_retrieval_rate",
    "max_timeout_rate",
    "min_comparable_event_rate",
    "min_avg_served_candidate_coverage",
    "max_p95_aux_latency_ms",
}
ZERO_GUARDRAILS = {
    "hard_constraint_violations",
    "catalogue_version_mismatches",
    "canonical_identity_failures",
    "intended_date_integrity_failures",
    "ghar_fallback_failures",
}


class RolloutEvidenceError(ValueError):
    """Raised when decision evidence is unsafe, incomplete or internally inconsistent."""


def _reject_identity(value: Any) -> None:
    if isinstance(value, dict):
        forbidden = FORBIDDEN_KEYS.intersection(value)
        if forbidden:
            raise RolloutEvidenceError(f"identity field is forbidden: {sorted(forbidden)[0]}")
        for item in value.values():
            _reject_identity(item)
    elif isinstance(value, list):
        for item in value:
            _reject_identity(item)


def _number(mapping: dict[str, Any], key: str) -> float:
    value = mapping.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
        raise RolloutEvidenceError(f"{key} must be a non-negative number")
    return float(value)


def _count(mapping: dict[str, Any], key: str) -> int:
    value = _number(mapping, key)
    if not value.is_integer():
        raise RolloutEvidenceError(f"{key} must be an integer count")
    return int(value)


def _targets(value: Any) -> dict[str, float]:
    if not isinstance(value, dict) or set(value) != TARGETS:
        raise RolloutEvidenceError("all and only ratified rollout targets are required")
    result = {key: _number(value, key) for key in TARGETS}
    for key in (
        "min_retrieval_rate",
        "max_timeout_rate",
        "min_comparable_event_rate",
        "min_avg_served_candidate_coverage",
    ):
        if result[key] > 1:
            raise RolloutEvidenceError(f"{key} must be between 0 and 1")
    if result["min_shadow_events"] < 1 or result["max_p95_aux_latency_ms"] <= 0:
        raise RolloutEvidenceError("event and latency targets must be positive")
    return result


def evaluate(document: dict[str, Any]) -> dict[str, Any]:
    """Return a machine-actionable decision without changing runtime configuration."""
    _reject_identity(document)
    if document.get("schema_version") != SCHEMA_VERSION:
        raise RolloutEvidenceError("unsupported schema_version")
    mode = document.get("current_mode")
    if mode not in {"off", "shadow", "active"}:
        raise RolloutEvidenceError("current_mode must be off, shadow or active")
    expected_version = document.get("publication_version")
    if not isinstance(expected_version, str) or not PUBLICATION.fullmatch(expected_version):
        raise RolloutEvidenceError("a full publication hash is required")
    targets = _targets(document.get("targets"))

    offline = document.get("offline_report")
    load = document.get("load_report")
    rows = document.get("shadow_health")
    guardrails = document.get("guardrails")
    if not isinstance(offline, dict) or not isinstance(load, dict):
        raise RolloutEvidenceError("offline and load reports are required")
    if not isinstance(rows, list) or not rows:
        raise RolloutEvidenceError("aggregate shadow health rows are required")
    if not isinstance(guardrails, dict) or set(guardrails) != ZERO_GUARDRAILS:
        raise RolloutEvidenceError("all and only hard guardrail counters are required")
    guardrail_values = {key: _count(guardrails, key) for key in ZERO_GUARDRAILS}

    offline_versions = offline.get("publication_versions")
    offline_version_ok = offline_versions == [expected_version]
    offline_ok = offline.get("eligible_for_active_evaluation") is True and offline_version_ok
    load_ok = (
        load.get("service") == "aux"
        and load.get("publication_versions") == [expected_version]
        and isinstance(load.get("evaluation"), dict)
        and load["evaluation"].get("mode") == "gated"
        and load["evaluation"].get("passed") is True
    )

    event_count = retrieved_count = timeout_count = comparable_count = 0.0
    coverage_numerator = 0.0
    coverage_denominator = 0.0
    p95_latency = 0.0
    observed_versions: set[str] = set()
    for row in rows:
        if not isinstance(row, dict) or row.get("mode") not in {"shadow", "active"}:
            raise RolloutEvidenceError("shadow health rows require shadow or active mode")
        row_events = _count(row, "event_count")
        row_retrieved = _count(row, "retrieved_count")
        row_timeout = _count(row, "timeout_count")
        row_comparable = _count(row, "comparable_event_count")
        if row_retrieved > row_events or row_timeout > row_events or row_comparable > row_events:
            raise RolloutEvidenceError("shadow health counts are inconsistent")
        version = row.get("publication_version")
        if version is not None:
            if not isinstance(version, str) or not PUBLICATION.fullmatch(version):
                raise RolloutEvidenceError("shadow row publication version is invalid")
            observed_versions.add(version)
        coverage = row.get("avg_served_candidate_coverage")
        if coverage is not None:
            if not isinstance(coverage, (int, float)) or not 0 <= coverage <= 1:
                raise RolloutEvidenceError("shadow coverage must be null or between 0 and 1")
            coverage_numerator += float(coverage) * row_comparable
            coverage_denominator += row_comparable
        event_count += row_events
        retrieved_count += row_retrieved
        timeout_count += row_timeout
        comparable_count += row_comparable
        p95_latency = max(p95_latency, _number(row, "p95_aux_latency_ms"))

    if event_count <= 0:
        raise RolloutEvidenceError("shadow health must contain observed events")
    retrieval_rate = retrieved_count / event_count
    timeout_rate = timeout_count / event_count
    comparable_rate = comparable_count / event_count
    average_coverage = coverage_numerator / coverage_denominator if coverage_denominator else None
    publication_ok = observed_versions == {expected_version}
    no_guardrail_breach = all(value == 0 for value in guardrail_values.values())
    gates = {
        "offline_quality": offline_ok,
        "gated_load": load_ok,
        "single_publication": publication_ok,
        "minimum_shadow_volume": event_count >= targets["min_shadow_events"],
        "retrieval_availability": retrieval_rate >= targets["min_retrieval_rate"],
        "timeout_rate": timeout_rate <= targets["max_timeout_rate"],
        "canonical_comparability": comparable_rate >= targets["min_comparable_event_rate"],
        "served_candidate_coverage": average_coverage is not None
        and average_coverage >= targets["min_avg_served_candidate_coverage"],
        "aux_latency": p95_latency <= targets["max_p95_aux_latency_ms"],
        "hard_guardrails": no_guardrail_breach,
    }
    operational_breach = not all(
        gates[key]
        for key in (
            "single_publication",
            "retrieval_availability",
            "timeout_rate",
            "canonical_comparability",
            "served_candidate_coverage",
            "aux_latency",
            "hard_guardrails",
        )
    )
    kill_switch = mode == "active" and operational_breach
    eligible = mode == "shadow" and all(gates.values())
    decision = (
        "disable_aux"
        if kill_switch
        else "eligible_for_canary"
        if eligible
        else "stay_off"
        if mode == "off"
        else "remain_shadow"
        if mode == "shadow"
        else "continue_canary"
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "publication_version": expected_version,
        "current_mode": mode,
        "metrics": {
            "event_count": int(event_count),
            "retrieval_rate": round(retrieval_rate, 6),
            "timeout_rate": round(timeout_rate, 6),
            "comparable_event_rate": round(comparable_rate, 6),
            "avg_served_candidate_coverage": round(average_coverage, 6)
            if average_coverage is not None
            else None,
            "p95_aux_latency_ms": p95_latency,
        },
        "targets": targets,
        "gates": gates,
        "eligible_for_canary": eligible,
        "kill_switch_required": kill_switch,
        "decision": decision,
        "required_action": "set AUX_RE_MODE=off" if kill_switch else None,
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
    if result["kill_switch_required"]:
        return 2
    return 0 if result["eligible_for_canary"] or result["decision"] == "stay_off" else 1


if __name__ == "__main__":
    raise SystemExit(main())
