"""Validate and package aggregate offline, load and ratified target inputs for Aux rollout."""

from __future__ import annotations

import argparse
import json
import os
import re
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path
from typing import Any

from ops.quality.runner.network_load_test import REPORT_SCHEMA as LOAD_SCHEMA
from ops.recommendation.offline_candidate_validation import SCHEMA_VERSION as OFFLINE_SCHEMA
from ops.recommendation.rollout_decision import TARGETS, _reject_identity, _targets
from ops.recommendation.rollout_evidence import TARGET_SCHEMA

PUBLICATION = re.compile(r"^sha256:[0-9a-f]{64}$")
OFFLINE_KEYS = {
    "schema_version",
    "case_count",
    "publication_versions",
    "governance",
    "metrics",
    "slices",
    "gates",
    "eligible_for_active_evaluation",
}
LOAD_KEYS = {
    "schema_version",
    "service",
    "url_origin",
    "publication_versions",
    "metrics",
    "evaluation",
}
TARGET_ENV = {
    "min_shadow_events": "AUX_ROLLOUT_MIN_SHADOW_EVENTS",
    "min_retrieval_rate": "AUX_ROLLOUT_MIN_RETRIEVAL_RATE",
    "max_timeout_rate": "AUX_ROLLOUT_MAX_TIMEOUT_RATE",
    "min_comparable_event_rate": "AUX_ROLLOUT_MIN_COMPARABLE_EVENT_RATE",
    "min_avg_served_candidate_coverage": "AUX_ROLLOUT_MIN_SERVED_CANDIDATE_COVERAGE",
    "max_p95_aux_latency_ms": "AUX_ROLLOUT_MAX_P95_AUX_LATENCY_MS",
}


class RolloutInputError(ValueError):
    """Raised when a source report or approved policy cannot become rollout evidence."""


def _exact(value: Any, keys: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        raise RolloutInputError(f"{label} has an unsupported aggregate shape")
    return value


def build_target_policy(publication_version: str, environ: Mapping[str, str]) -> dict[str, Any]:
    """Build the target document only from protected environment configuration."""
    if not PUBLICATION.fullmatch(publication_version):
        raise RolloutInputError("a full publication hash is required")
    approval_reference = environ.get("AUX_ROLLOUT_APPROVAL_REFERENCE", "").strip()
    approved_at = environ.get("AUX_ROLLOUT_APPROVED_AT", "").strip()
    if not approval_reference or not approved_at:
        raise RolloutInputError("target approval reference and timestamp are required")
    try:
        parsed_approval = datetime.fromisoformat(approved_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise RolloutInputError("target approval timestamp is invalid") from exc
    if parsed_approval.tzinfo is None:
        raise RolloutInputError("target approval timestamp requires a timezone")
    raw_targets: dict[str, int | float] = {}
    for key, environment_key in TARGET_ENV.items():
        raw = environ.get(environment_key, "").strip()
        try:
            value = float(raw)
        except ValueError as exc:
            raise RolloutInputError(f"protected target {key} is missing or invalid") from exc
        if key == "min_shadow_events" and not value.is_integer():
            raise RolloutInputError("min_shadow_events must be a whole number")
        raw_targets[key] = int(value) if key == "min_shadow_events" else value
    try:
        targets = _targets(raw_targets)
    except ValueError as exc:
        raise RolloutInputError(str(exc)) from exc
    return {
        "schema_version": TARGET_SCHEMA,
        "ratified": True,
        "approval_reference": approval_reference,
        "approved_at": approved_at,
        "publication_version": publication_version,
        "targets": targets,
    }


def validate_inputs(
    offline: dict[str, Any],
    load: dict[str, Any],
    targets: dict[str, Any],
    publication_version: str,
) -> None:
    """Require aggregate-only passing reports and one approved catalogue generation."""
    _reject_identity(offline)
    _reject_identity(load)
    _reject_identity(targets)
    offline = _exact(offline, OFFLINE_KEYS, "offline report")
    load = _exact(load, LOAD_KEYS, "load report")
    targets = _exact(
        targets,
        {
            "schema_version",
            "ratified",
            "approval_reference",
            "approved_at",
            "publication_version",
            "targets",
        },
        "target policy",
    )
    if (
        offline["schema_version"] != OFFLINE_SCHEMA
        or offline["eligible_for_active_evaluation"] is not True
        or offline["publication_versions"] != [publication_version]
    ):
        raise RolloutInputError("offline quality is not eligible for this publication")
    evaluation = load.get("evaluation")
    if (
        load["schema_version"] != LOAD_SCHEMA
        or load["service"] != "aux"
        or load["publication_versions"] != [publication_version]
        or not isinstance(evaluation, dict)
        or evaluation.get("mode") != "gated"
        or evaluation.get("passed") is not True
    ):
        raise RolloutInputError("Aux load evidence is not gated and passing for this publication")
    if (
        targets["schema_version"] != TARGET_SCHEMA
        or targets["ratified"] is not True
        or targets["publication_version"] != publication_version
        or set(targets.get("targets", {})) != TARGETS
    ):
        raise RolloutInputError("target policy is not ratified for this publication")


def _read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RolloutInputError("source report must be a JSON object")
    return value


def _write_new(path: Path, value: dict[str, Any]) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    descriptor = os.open(path, flags, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", type=Path, required=True)
    parser.add_argument("--load", type=Path, required=True)
    parser.add_argument("--publication-version", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    offline = _read(args.offline)
    load = _read(args.load)
    targets = build_target_policy(args.publication_version, os.environ)
    validate_inputs(offline, load, targets, args.publication_version)
    args.output_dir.mkdir(parents=True, exist_ok=False)
    _write_new(args.output_dir / "offline.json", offline)
    _write_new(args.output_dir / "load.json", load)
    _write_new(args.output_dir / "targets.json", targets)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
