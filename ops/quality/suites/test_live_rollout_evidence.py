from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from ops.recommendation.live_rollout_evidence import export_aggregates

VERSION = "sha256:" + "a" * 64
SINCE = datetime(2026, 8, 1, tzinfo=UTC)
UNTIL = datetime(2026, 8, 8, tzinfo=UTC)
WINDOW = {
    "since": "2026-08-01T00:00:00.000000Z",
    "until": "2026-08-08T00:00:00.000000Z",
}


class Cursor:
    def __init__(self, results):
        self.results = iter(results)
        self.current = None

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return None

    def execute(self, query, params=None):
        if query.startswith("set local"):
            return
        self.current = next(self.results)

    def fetchall(self):
        return self.current


class Connection:
    def __init__(self, health_rows, guardrail):
        self.results = [health_rows, [(guardrail,)]]

    def cursor(self):
        return Cursor(self.results)


def guardrail(window=WINDOW):
    return {
        "schema_version": "recommendation-guardrail-report-v1",
        "source": "production_guardrail_aggregate",
        "measurement_status": "measured",
        "publication_version": VERSION,
        "window": window,
        "counts": {
            "hard_constraint_violations": 0,
            "catalogue_version_mismatches": 0,
            "canonical_identity_failures": 0,
            "intended_date_integrity_failures": 0,
            "ghar_fallback_failures": 0,
        },
    }


def test_live_export_contains_only_governed_aggregate_rows():
    health_rows = [
        (
            date(2026, 8, 7),
            "shadow",
            VERSION,
            100,
            99,
            1,
            1,
            98,
            Decimal("75.25"),
            Decimal("42.5"),
            Decimal("80"),
            Decimal("0.85"),
        )
    ]

    health, guards = export_aggregates(Connection(health_rows, guardrail()), SINCE, UNTIL, VERSION)

    assert health["window"] == WINDOW
    assert health["rows"][0]["avg_served_candidate_coverage"] == 0.85
    assert guards["measurement_status"] == "measured"
    assert all(
        key not in str(health) for key in ("profile_id", "household_id", "request_id", "dish_id")
    )


def test_live_export_rejects_mismatched_aggregate_windows():
    with pytest.raises(RuntimeError, match="windows do not match"):
        export_aggregates(
            Connection([], guardrail({**WINDOW, "until": "2026-08-09T00:00:00Z"})),
            SINCE,
            UNTIL,
            VERSION,
        )
