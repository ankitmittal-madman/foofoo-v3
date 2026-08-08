from __future__ import annotations

import pytest

from ops.recommendation.rollout_decision import RolloutEvidenceError
from ops.recommendation.rollout_evidence import (
    GUARDRAIL_SCHEMA,
    HEALTH_SCHEMA,
    TARGET_SCHEMA,
    compose,
)

VERSION = "sha256:" + "a" * 64
WINDOW = {"since": "2026-08-01T00:00:00Z", "until": "2026-08-08T00:00:00Z"}


def sources() -> dict:
    return {
        "current_mode": "shadow",
        "offline": {
            "schema_version": "recommendation-offline-validation-v1",
            "publication_versions": [VERSION],
            "eligible_for_active_evaluation": True,
        },
        "load": {
            "schema_version": "recommendation-load-report-v2",
            "service": "aux",
            "publication_versions": [VERSION],
            "evaluation": {"mode": "gated", "passed": True},
        },
        "health": {
            "schema_version": HEALTH_SCHEMA,
            "source": "re_engine.aux_shadow_health",
            "publication_version": VERSION,
            "window": WINDOW,
            "rows": [
                {
                    "mode": "shadow",
                    "publication_version": VERSION,
                    "event_count": 100,
                    "retrieved_count": 99,
                    "timeout_count": 1,
                    "comparable_event_count": 98,
                    "p95_aux_latency_ms": 180,
                    "avg_served_candidate_coverage": 0.85,
                }
            ],
        },
        "guardrails": {
            "schema_version": GUARDRAIL_SCHEMA,
            "source": "production_guardrail_aggregate",
            "measurement_status": "measured",
            "publication_version": VERSION,
            "window": WINDOW,
            "counts": {
                "hard_constraint_violations": 0,
                "catalogue_version_mismatches": 0,
                "canonical_identity_failures": 0,
                "intended_date_integrity_failures": 0,
                "ghar_fallback_failures": 0,
            },
        },
        "targets": {
            "schema_version": TARGET_SCHEMA,
            "ratified": True,
            "approval_reference": "product-gate-2026-08",
            "approved_at": "2026-08-01T00:00:00Z",
            "publication_version": VERSION,
            "targets": {
                "min_shadow_events": 100,
                "min_retrieval_rate": 0.98,
                "max_timeout_rate": 0.01,
                "min_comparable_event_rate": 0.95,
                "min_avg_served_candidate_coverage": 0.8,
                "max_p95_aux_latency_ms": 200,
            },
        },
        "source_sha256": dict.fromkeys(
            ("offline", "load", "health", "guardrails", "targets"), "b" * 64
        ),
    }


def test_composer_binds_all_aggregate_sources_and_previews_a_valid_decision():
    evidence = compose(**sources())

    assert evidence["publication_version"] == VERSION
    assert evidence["evidence_provenance"]["source_sha256"]["health"] == "b" * 64
    assert "household_id" not in str(evidence)


def test_composer_can_derive_but_not_misstate_the_live_rollout_mode():
    automatic = sources()
    automatic["current_mode"] = "auto"
    assert compose(**automatic)["current_mode"] == "shadow"

    incorrect = sources()
    incorrect["current_mode"] = "active"
    with pytest.raises(RolloutEvidenceError, match="does not match live health"):
        compose(**incorrect)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda value: value["targets"].update(ratified=False),
        lambda value: value["guardrails"].update(measurement_status="assumed"),
        lambda value: value["guardrails"].update(
            window={**WINDOW, "until": "2026-08-09T00:00:00Z"}
        ),
        lambda value: value["load"].update(publication_versions=["sha256:" + "c" * 64]),
        lambda value: value["health"].update(source="manual_query"),
    ],
)
def test_composer_rejects_unratified_assumed_or_mixed_evidence(mutate):
    value = sources()
    mutate(value)
    with pytest.raises(RolloutEvidenceError):
        compose(**value)


def test_composer_rejects_identity_hidden_inside_a_source_report():
    value = sources()
    value["offline"]["household_id"] = "private"

    with pytest.raises(RolloutEvidenceError, match="identity field"):
        compose(**value)
