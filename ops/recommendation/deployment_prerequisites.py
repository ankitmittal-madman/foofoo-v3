"""Report recommendation deployment configuration readiness without exposing values."""

from __future__ import annotations

import argparse
import json
import os
from collections.abc import Mapping, Sequence
from pathlib import Path

SCHEMA_VERSION = "recommendation-modernization-readiness-v1"

TARGET_PHASES: dict[str, tuple[str, ...]] = {
    "foundation": (
        "schema_and_catalogue",
        "qdrant_publication",
        "ghar_deployment",
        "aux_deployment",
        "edge_and_mode_control",
    ),
    "shadow": (
        "schema_and_catalogue",
        "qdrant_publication",
        "ghar_deployment",
        "aux_deployment",
        "edge_and_mode_control",
        "deployed_load_gate",
    ),
    "rollout": (
        "schema_and_catalogue",
        "qdrant_publication",
        "ghar_deployment",
        "aux_deployment",
        "edge_and_mode_control",
        "deployed_load_gate",
        "rollout_evidence",
    ),
}

PHASE_REQUIREMENTS: dict[str, tuple[str, ...]] = {
    "schema_and_catalogue": (
        "FOOFOO_SUPABASE_URI",
        "PRODUCTION_PROJECT_REF",
    ),
    "qdrant_publication": (
        "AUX_RE_QDRANT_URL",
        "AUX_RE_QDRANT_ALLOWED_HOST",
        "AUX_RE_QDRANT_API_KEY",
    ),
    "ghar_deployment": (
        "FLY_API_TOKEN",
        "FLY_GHAR_APP",
    ),
    "aux_deployment": (
        "FLY_API_TOKEN",
        "FLY_AUX_APP",
        "AUX_RE_SERVICE_SECRET",
        "AUX_RE_QDRANT_URL",
        "AUX_RE_QDRANT_ALLOWED_HOST",
        "AUX_RE_QDRANT_API_KEY",
    ),
    "edge_and_mode_control": (
        "SUPABASE_ACCESS_TOKEN",
        "PRODUCTION_PROJECT_REF",
        "FLY_AUX_APP",
        "FLY_GHAR_APP",
        "AUX_RE_SERVICE_SECRET",
    ),
    "deployed_load_gate": (
        "AUX_RE_SERVICE_URL",
        "AUX_RE_SERVICE_SECRET",
        "AUX_LOAD_REQUESTS",
        "AUX_LOAD_CONCURRENCY",
        "AUX_LOAD_TIMEOUT_SECONDS",
        "AUX_LOAD_MAX_P95_MS",
        "AUX_LOAD_MAX_ERROR_RATE",
        "AUX_LOAD_MIN_THROUGHPUT_RPS",
    ),
    "rollout_evidence": (
        "AUX_ROLLOUT_APPROVAL_REFERENCE",
        "AUX_ROLLOUT_APPROVED_AT",
        "AUX_ROLLOUT_MAX_P95_AUX_LATENCY_MS",
        "AUX_ROLLOUT_MAX_TIMEOUT_RATE",
        "AUX_ROLLOUT_MIN_COMPARABLE_EVENT_RATE",
        "AUX_ROLLOUT_MIN_RETRIEVAL_RATE",
        "AUX_ROLLOUT_MIN_SERVED_CANDIDATE_COVERAGE",
        "AUX_ROLLOUT_MIN_SHADOW_EVENTS",
    ),
}

SECRET_NAMES = frozenset(
    {
        "AUX_RE_QDRANT_API_KEY",
        "AUX_RE_SERVICE_SECRET",
        "FLY_API_TOKEN",
        "FOOFOO_SUPABASE_URI",
        "SUPABASE_ACCESS_TOKEN",
    }
)


def required_names(target_phase: str = "rollout") -> frozenset[str]:
    return frozenset(
        name for phase in TARGET_PHASES[target_phase] for name in PHASE_REQUIREMENTS[phase]
    )


def readiness_report(
    environment: Mapping[str, str], target_phase: str = "foundation"
) -> dict[str, object]:
    """Return names and booleans only; never copy configuration values into evidence."""
    evaluated_phases = TARGET_PHASES[target_phase]
    phases: dict[str, object] = {}
    for phase, names in PHASE_REQUIREMENTS.items():
        missing = [name for name in names if not environment.get(name, "").strip()]
        phases[phase] = {
            "ready": not missing,
            "required_count": len(names),
            "configured_count": len(names) - len(missing),
            "missing_names": missing,
        }

    scoped_names = required_names(target_phase)
    all_missing = sorted(name for name in scoped_names if not environment.get(name, "").strip())
    return {
        "schema_version": SCHEMA_VERSION,
        "validation_scope": "configuration-name-presence-only",
        "deployment_authorized": False,
        "target_phase": target_phase,
        "evaluated_phases": list(evaluated_phases),
        "ready": not all_missing,
        "required_name_count": len(scoped_names),
        "configured_name_count": len(scoped_names) - len(all_missing),
        "missing_names": all_missing,
        "phases": phases,
        "contains_values": False,
    }


def write_report(path: Path, report: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--target-phase", choices=tuple(TARGET_PHASES), default="foundation")
    args = parser.parse_args(argv)
    report = readiness_report(os.environ, args.target_phase)
    write_report(args.output, report)
    return 0 if report["ready"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
