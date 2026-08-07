"""Read-only production preference-training orchestration.

The database remains the authority for readiness and point-in-time export eligibility. Raw rows
exist only inside a TemporaryDirectory and are never uploaded. This command does not change model
configuration, deploy a service, or activate an artifact.
"""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

from ghar_re_core.config import CONFIG
from ghar_re_core.training.train_pref_model import train

DATABASE_ENV_NAMES = ("DATABASE_URL", "SUPABASE_DB_URL", "FOOFOO_SUPABASE_URI")


@dataclass(frozen=True)
class ReadinessSnapshot:
    real_labeled_events: int
    positive_events: int
    negative_events: int
    distinct_households: int
    identity_resolved_events: int
    attributed_to_slate_events: int
    identity_coverage: float
    slate_attribution_coverage: float
    eligible_training_events: int
    eligible_training_households: int
    eligible_positive_events: int
    eligible_negative_events: int
    is_ready: bool

    @classmethod
    def from_mapping(cls, row: Mapping[str, Any]) -> ReadinessSnapshot:
        total = int(row["real_labeled_events"])
        attributed = int(row["attributed_to_slate_events"])
        exact_legacy_corpus = attributed == total
        return cls(
            real_labeled_events=total,
            positive_events=int(row["positive_events"]),
            negative_events=int(row["negative_events"]),
            distinct_households=int(row["distinct_households"]),
            identity_resolved_events=int(row["identity_resolved_events"]),
            attributed_to_slate_events=attributed,
            identity_coverage=float(row["identity_coverage"]),
            slate_attribution_coverage=float(row["slate_attribution_coverage"]),
            # Rolling deployments may briefly run this code before migration 090. V1 can only be
            # considered eligible when its entire corpus is exact; partial legacy attribution is
            # reported but remains closed until v2 is available.
            eligible_training_events=int(row.get("eligible_training_events", attributed)),
            eligible_training_households=int(
                row.get(
                    "eligible_training_households",
                    row["distinct_households"] if exact_legacy_corpus else 0,
                )
            ),
            eligible_positive_events=int(
                row.get(
                    "eligible_positive_events",
                    row["positive_events"] if exact_legacy_corpus else 0,
                )
            ),
            eligible_negative_events=int(
                row.get(
                    "eligible_negative_events",
                    row["negative_events"] if exact_legacy_corpus else 0,
                )
            ),
            is_ready=bool(row["is_ready"]),
        )


def database_url(environ: Mapping[str, str] | None = None) -> str:
    values = environ or os.environ
    for name in DATABASE_ENV_NAMES:
        value = values.get(name)
        if value:
            return value
    raise RuntimeError(
        "No production database connection configured; set DATABASE_URL, SUPABASE_DB_URL, "
        "or FOOFOO_SUPABASE_URI."
    )


def fetch_readiness(connection: Any) -> ReadinessSnapshot:
    with connection.cursor() as cursor:
        cursor.execute(
            "select to_regprocedure(%s) is not null as available",
            ("ml.preference_training_readiness_v2(integer,integer)",),
        )
        availability = cursor.fetchone()
        v2_available = bool(
            availability.get("available") if isinstance(availability, Mapping) else availability[0]
        )
        function_name = (
            "ml.preference_training_readiness_v2"
            if v2_available
            else "ml.preference_training_readiness"
        )
        cursor.execute(
            f"select * from {function_name}(%s, %s)",  # noqa: S608 — fixed allowlisted names
            (CONFIG.pref_training_min_events, CONFIG.pref_training_min_households),
        )
        row = cursor.fetchone()
        if row is None:
            raise RuntimeError("Preference training readiness query returned no row")
        if not isinstance(row, Mapping):
            columns = [item[0] for item in cursor.description]
            row = dict(zip(columns, row, strict=True))
        return ReadinessSnapshot.from_mapping(row)


def fetch_shadow_evaluation(connection: Any) -> list[dict[str, Any]]:
    """Return aggregate online shadow evidence; never household-level observations."""
    with connection.cursor() as cursor:
        cursor.execute("select * from ml.preference_shadow_evaluation()")
        rows = cursor.fetchall()
        if not rows:
            return []
        if isinstance(rows[0], Mapping):
            mapped = [dict(row) for row in rows]
        else:
            columns = [item[0] for item in cursor.description]
            mapped = [dict(zip(columns, row, strict=True)) for row in rows]
        return [
            {
                key: float(value) if isinstance(value, Decimal) else value
                for key, value in row.items()
            }
            for row in mapped
        ]


def export_rows(connection: Any, destination: Path) -> int:
    """Stream exact-attribution rows to an ephemeral JSONL file without loading all into RAM."""
    count = 0
    with destination.open("x", encoding="utf-8") as output, connection.cursor() as cursor:
        cursor.execute("select ml.preference_training_export_rows() as export_row")
        for result in cursor:
            value = result[0] if not isinstance(result, Mapping) else result["export_row"]
            output.write(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")
            count += 1
    os.chmod(destination, 0o600)
    return count


def _atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False
    ) as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        temp_name = handle.name
    os.replace(temp_name, path)


def run(
    connection: Any,
    *,
    readiness_out: Path,
    artifact_out: Path,
    eval_out: Path,
) -> dict[str, Any]:
    readiness = fetch_readiness(connection)
    result: dict[str, Any] = {
        "status": "not_ready",
        "readiness": asdict(readiness),
        "shadow_evaluation": fetch_shadow_evaluation(connection),
        "thresholds": {
            "min_real_events": CONFIG.pref_training_min_events,
            "min_households": CONFIG.pref_training_min_households,
        },
    }
    if not readiness.is_ready:
        _atomic_json(readiness_out, result)
        return result

    artifact_out.parent.mkdir(parents=True, exist_ok=True)
    eval_out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="foofoo-pref-training-") as private_dir:
        export_path = Path(private_dir) / "private-feedback-export.jsonl"
        exported = export_rows(connection, export_path)
        if exported != readiness.eligible_training_events:
            raise RuntimeError(
                "Readiness/export count changed during the read-only snapshot; refusing a "
                "non-reproducible training run"
            )
        report = train(str(export_path), str(artifact_out), str(eval_out))

    result.update(
        status="candidate_passed" if report["promotion_gate"]["passed"] else "candidate_rejected",
        exported_rows=exported,
        model_version=report["artifact_metadata"]["model_version"],
        promotion_gate=report["promotion_gate"],
    )
    _atomic_json(readiness_out, result)
    return result


def connect_read_only(dsn: str) -> Any:
    import psycopg2

    connection = psycopg2.connect(dsn, connect_timeout=15, application_name="foofoo-pref-training")
    connection.set_session(readonly=True, autocommit=False)
    with connection.cursor() as cursor:
        cursor.execute("set local statement_timeout = '5min'")
    return connection


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--readiness-out", type=Path, required=True)
    parser.add_argument("--artifact-out", type=Path, required=True)
    parser.add_argument("--eval-out", type=Path, required=True)
    args = parser.parse_args(argv)

    connection = connect_read_only(database_url())
    try:
        result = run(
            connection,
            readiness_out=args.readiness_out,
            artifact_out=args.artifact_out,
            eval_out=args.eval_out,
        )
        connection.rollback()
    finally:
        connection.close()
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
