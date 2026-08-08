from __future__ import annotations

import pytest

from ops.recommendation.rollout_decision import (
    SCHEMA_VERSION,
    RolloutEvidenceError,
    evaluate,
)

VERSION = "sha256:" + "a" * 64


def evidence(mode: str = "shadow") -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "current_mode": mode,
        "publication_version": VERSION,
        "targets": {
            "min_shadow_events": 100,
            "min_retrieval_rate": 0.98,
            "max_timeout_rate": 0.01,
            "min_comparable_event_rate": 0.95,
            "min_avg_served_candidate_coverage": 0.8,
            "max_p95_aux_latency_ms": 200,
        },
        "offline_report": {
            "publication_versions": [VERSION],
            "eligible_for_active_evaluation": True,
        },
        "load_report": {
            "service": "aux",
            "evaluation": {"mode": "gated", "passed": True},
        },
        "shadow_health": [
            {
                "mode": mode if mode != "off" else "shadow",
                "publication_version": VERSION,
                "event_count": 100,
                "retrieved_count": 99,
                "timeout_count": 1,
                "comparable_event_count": 98,
                "p95_aux_latency_ms": 180,
                "avg_served_candidate_coverage": 0.85,
            }
        ],
        "guardrails": {
            "hard_constraint_violations": 0,
            "catalogue_version_mismatches": 0,
            "canonical_identity_failures": 0,
            "intended_date_integrity_failures": 0,
            "ghar_fallback_failures": 0,
        },
    }


def test_all_ratified_gates_make_shadow_eligible_for_controlled_canary():
    result = evaluate(evidence())

    assert result["eligible_for_canary"] is True
    assert result["kill_switch_required"] is False
    assert result["decision"] == "eligible_for_canary"
    assert result["metrics"]["retrieval_rate"] == 0.99


@pytest.mark.parametrize(
    ("mutate", "gate"),
    [
        (lambda value: value["offline_report"].update(eligible_for_active_evaluation=False), "offline_quality"),
        (lambda value: value["load_report"]["evaluation"].update(passed=False), "gated_load"),
        (lambda value: value["shadow_health"][0].update(retrieved_count=90), "retrieval_availability"),
        (lambda value: value["shadow_health"][0].update(comparable_event_count=80), "canonical_comparability"),
        (lambda value: value["shadow_health"][0].update(avg_served_candidate_coverage=0.7), "served_candidate_coverage"),
    ],
)
def test_shadow_remains_shadow_when_any_promotion_gate_fails(mutate, gate):
    value = evidence()
    mutate(value)
    result = evaluate(value)

    assert result["gates"][gate] is False
    assert result["decision"] == "remain_shadow"
    assert result["eligible_for_canary"] is False


@pytest.mark.parametrize(
    "mutate",
    [
        lambda value: value["guardrails"].update(hard_constraint_violations=1),
        lambda value: value["guardrails"].update(catalogue_version_mismatches=1),
        lambda value: value["shadow_health"][0].update(timeout_count=5),
        lambda value: value["shadow_health"][0].update(p95_aux_latency_ms=250),
        lambda value: value["shadow_health"][0].update(avg_served_candidate_coverage=0.7),
    ],
)
def test_active_operational_breach_requires_immediate_off_switch(mutate):
    value = evidence("active")
    mutate(value)
    result = evaluate(value)

    assert result["kill_switch_required"] is True
    assert result["decision"] == "disable_aux"
    assert result["required_action"] == "set AUX_RE_MODE=off"


def test_identity_fields_and_missing_ratified_targets_fail_closed():
    value = evidence()
    value["household_id"] = "private"
    with pytest.raises(RolloutEvidenceError, match="identity field"):
        evaluate(value)

    value = evidence()
    del value["targets"]["max_timeout_rate"]
    with pytest.raises(RolloutEvidenceError, match="ratified rollout targets"):
        evaluate(value)
