"""Export privacy-safe live Aux health and final-serving guardrails from production.

The database session is read-only. Only the two service-only aggregate functions are queried; no
profile, household, request, event, candidate or dish row is selected or written.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from ops.recommendation.protected_identity import database_identifies_project
from ops.recommendation.rollout_decision import _reject_identity
from ops.recommendation.rollout_evidence import HEALTH_SCHEMA

PUBLICATION = re.compile(r"^sha256:[0-9a-f]{64}$")
HEALTH_FIELDS = (
    "observation_date",
    "mode",
    "publication_version",
    "event_count",
    "retrieved_count",
    "unavailable_count",
    "timeout_count",
    "comparable_event_count",
    "avg_candidate_count",
    "avg_aux_latency_ms",
    "p95_aux_latency_ms",
    "avg_served_candidate_coverage",
)


def _timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamps must include a timezone")
    return parsed.astimezone(UTC)


def _render_timestamp(value: datetime) -> str:
    return value.astimezone(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _json_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def export_aggregates(
    connection: Any,
    since: datetime,
    until: datetime,
    publication_version: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Read only the governed aggregates and return their strict JSON documents."""
    if since >= until or until - since > timedelta(days=31):
        raise ValueError("a forward-moving window of at most 31 days is required")
    if not PUBLICATION.fullmatch(publication_version):
        raise ValueError("a full publication hash is required")
    with connection.cursor() as cursor:
        cursor.execute("set local statement_timeout = '30s'")
        cursor.execute("select * from re_engine.aux_shadow_health(%s, %s)", (since, until))
        raw_rows = cursor.fetchall()
        cursor.execute(
            "select re_engine.production_guardrail_aggregate(%s, %s, %s)",
            (since, until, publication_version),
        )
        guardrail_rows = cursor.fetchall()
    if len(guardrail_rows) != 1:
        raise RuntimeError("production guardrail aggregate returned an invalid cardinality")
    guardrails = guardrail_rows[0][0]
    if isinstance(guardrails, str):
        guardrails = json.loads(guardrails)
    if not isinstance(guardrails, dict):
        raise RuntimeError("production guardrail aggregate did not return an object")
    rows = [
        {key: _json_value(value) for key, value in zip(HEALTH_FIELDS, row, strict=True)}
        for row in raw_rows
    ]
    window = {
        "since": _render_timestamp(since),
        "until": _render_timestamp(until),
    }
    health = {
        "schema_version": HEALTH_SCHEMA,
        "source": "re_engine.aux_shadow_health",
        "publication_version": publication_version,
        "window": window,
        "rows": rows,
    }
    if guardrails.get("window") != window:
        raise RuntimeError("live aggregate windows do not match")
    _reject_identity(health)
    _reject_identity(guardrails)
    return health, guardrails


def _atomic_json(path: Path, value: dict[str, Any]) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite live evidence: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--since", required=True)
    parser.add_argument("--until", required=True)
    parser.add_argument("--publication-version", required=True)
    parser.add_argument("--health-output", type=Path, required=True)
    parser.add_argument("--guardrail-output", type=Path, required=True)
    args = parser.parse_args()
    database_url = os.environ.get("FOOFOO_SUPABASE_URI", "")
    project_ref = os.environ.get("PRODUCTION_PROJECT_REF", "")
    if not project_ref or not database_identifies_project(database_url, project_ref):
        raise RuntimeError("production database identity is missing or ambiguous")
    import psycopg2

    application_name = f"foofoo-aux-evidence-{os.environ.get('GITHUB_RUN_ID', 'local')}"[:63]
    with psycopg2.connect(
        database_url, application_name=application_name, connect_timeout=10
    ) as connection:
        connection.set_session(readonly=True)
        health, guardrails = export_aggregates(
            connection,
            _timestamp(args.since),
            _timestamp(args.until),
            args.publication_version,
        )
    _atomic_json(args.health_output, health)
    _atomic_json(args.guardrail_output, guardrails)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
