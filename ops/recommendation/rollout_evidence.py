"""Compose one privacy-minimized Aux rollout artifact from independently governed reports."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

from ops.quality.runner.network_load_test import REPORT_SCHEMA as LOAD_SCHEMA
from ops.recommendation.offline_candidate_validation import SCHEMA_VERSION as OFFLINE_SCHEMA
from ops.recommendation.rollout_decision import SCHEMA_VERSION as EVIDENCE_SCHEMA
from ops.recommendation.rollout_decision import (
    TARGETS,
    ZERO_GUARDRAILS,
    RolloutEvidenceError,
    evaluate,
)

HEALTH_SCHEMA = "aux-shadow-health-export-v1"
GUARDRAIL_SCHEMA = "recommendation-guardrail-report-v1"
TARGET_SCHEMA = "recommendation-rollout-targets-v1"


def _exact(value: Any, keys: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        raise RolloutEvidenceError(f"{label} has an unsupported shape")
    return value


def _timestamp(value: Any, label: str) -> datetime:
    if not isinstance(value, str):
        raise RolloutEvidenceError(f"{label} must be an ISO-8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise RolloutEvidenceError(f"{label} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise RolloutEvidenceError(f"{label} must include a timezone")
    return parsed


def compose(
    *,
    current_mode: str,
    offline: dict[str, Any],
    load: dict[str, Any],
    health: dict[str, Any],
    guardrails: dict[str, Any],
    targets: dict[str, Any],
    source_sha256: dict[str, str],
) -> dict[str, Any]:
    """Validate independent aggregate reports, bind their lineage, and preview the decision."""
    if offline.get("schema_version") != OFFLINE_SCHEMA:
        raise RolloutEvidenceError("offline report schema is unsupported")
    if load.get("schema_version") != LOAD_SCHEMA:
        raise RolloutEvidenceError("load report schema is unsupported")
    health = _exact(
        health,
        {"schema_version", "source", "publication_version", "window", "rows"},
        "shadow health report",
    )
    guardrails = _exact(
        guardrails,
        {
            "schema_version",
            "source",
            "measurement_status",
            "publication_version",
            "window",
            "counts",
        },
        "guardrail report",
    )
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
        health["schema_version"] != HEALTH_SCHEMA
        or health["source"] != "re_engine.aux_shadow_health"
    ):
        raise RolloutEvidenceError("shadow health must come from the governed aggregate function")
    if (
        guardrails["schema_version"] != GUARDRAIL_SCHEMA
        or guardrails["source"] != "production_guardrail_aggregate"
        or guardrails["measurement_status"] != "measured"
    ):
        raise RolloutEvidenceError("guardrails must be measured by the production aggregate")
    if targets["schema_version"] != TARGET_SCHEMA or targets["ratified"] is not True:
        raise RolloutEvidenceError("rollout targets are not ratified")
    if (
        not isinstance(targets["approval_reference"], str)
        or not targets["approval_reference"].strip()
    ):
        raise RolloutEvidenceError("ratified targets require an approval reference")
    _timestamp(targets["approved_at"], "approved_at")
    if not isinstance(health["rows"], list) or not health["rows"]:
        raise RolloutEvidenceError("shadow health contains no aggregate rows")
    observed_modes = {row.get("mode") for row in health["rows"] if isinstance(row, dict)}
    if observed_modes not in ({"shadow"}, {"active"}):
        raise RolloutEvidenceError("live health must contain exactly one rollout mode")
    observed_mode = next(iter(observed_modes))
    if current_mode == "auto":
        current_mode = observed_mode
    elif current_mode != observed_mode:
        raise RolloutEvidenceError("declared rollout mode does not match live health")
    if not isinstance(health["window"], dict) or set(health["window"]) != {"since", "until"}:
        raise RolloutEvidenceError("shadow health window is invalid")
    if guardrails["window"] != health["window"]:
        raise RolloutEvidenceError("guardrail and shadow windows must match exactly")
    since = _timestamp(health["window"]["since"], "window.since")
    until = _timestamp(health["window"]["until"], "window.until")
    if since >= until:
        raise RolloutEvidenceError("evidence window must be forward-moving")
    if not isinstance(guardrails["counts"], dict) or set(guardrails["counts"]) != ZERO_GUARDRAILS:
        raise RolloutEvidenceError("guardrail counters are incomplete")
    if not isinstance(targets["targets"], dict) or set(targets["targets"]) != TARGETS:
        raise RolloutEvidenceError("ratified target values are incomplete")

    version = health["publication_version"]
    if guardrails["publication_version"] != version or targets["publication_version"] != version:
        raise RolloutEvidenceError("health, guardrail and target publications do not match")
    if offline.get("publication_versions") != [version] or load.get("publication_versions") != [
        version
    ]:
        raise RolloutEvidenceError("offline or load publication does not match live evidence")
    required_sources = {"offline", "load", "health", "guardrails", "targets"}
    if set(source_sha256) != required_sources or not all(
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
        for value in source_sha256.values()
    ):
        raise RolloutEvidenceError("all source SHA-256 values are required")

    evidence = {
        "schema_version": EVIDENCE_SCHEMA,
        "current_mode": current_mode,
        "publication_version": version,
        "targets": targets["targets"],
        "offline_report": offline,
        "load_report": load,
        "shadow_health": health["rows"],
        "guardrails": guardrails["counts"],
        "evidence_provenance": {
            "source_sha256": dict(sorted(source_sha256.items())),
            "window": health["window"],
            "target_approval_reference": targets["approval_reference"],
            "targets_approved_at": targets["approved_at"],
        },
    }
    evaluate(evidence)
    return evidence


def _load(path: Path) -> tuple[dict[str, Any], str]:
    raw = path.read_bytes()
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RolloutEvidenceError("source report is not valid JSON") from exc
    if not isinstance(value, dict):
        raise RolloutEvidenceError("source report must be a JSON object")
    return value, hashlib.sha256(raw).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--current-mode", required=True, choices=("auto", "off", "shadow", "active")
    )
    parser.add_argument("--offline", type=Path, required=True)
    parser.add_argument("--load", type=Path, required=True)
    parser.add_argument("--health", type=Path, required=True)
    parser.add_argument("--guardrails", type=Path, required=True)
    parser.add_argument("--targets", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite rollout evidence: {args.output}")
    documents: dict[str, dict[str, Any]] = {}
    hashes: dict[str, str] = {}
    for name in ("offline", "load", "health", "guardrails", "targets"):
        documents[name], hashes[name] = _load(getattr(args, name))
    evidence = compose(current_mode=args.current_mode, source_sha256=hashes, **documents)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{args.output.name}.", dir=args.output.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(evidence, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, args.output)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
