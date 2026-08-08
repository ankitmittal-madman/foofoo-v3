from __future__ import annotations

import pytest

from ops.recommendation.offline_candidate_validation import (
    SCHEMA_VERSION,
    ValidationInputError,
    evaluate,
)

VERSION = "sha256:" + "a" * 64
POHA = "00000000-0000-4000-8000-000000000001"
IDLI = "00000000-0000-4000-8000-000000000002"
DOSA = "00000000-0000-4000-8000-000000000003"


def evidence() -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "dataset": {
            "consented_real_outcomes": True,
            "household_disjoint": True,
            "time_split": True,
            "synthetic": False,
        },
        "cases": [
            {
                "case_id": "case-00000000000000000000000000000001",
                "baseline_candidate_ids": [IDLI],
                "aux_candidate_ids": [POHA, IDLI],
                "relevant_dish_ids": [POHA],
                "forbidden_dish_ids": [DOSA],
                "publication_version": VERSION,
                "slices": ["veg", "breakfast"],
            },
            {
                "case_id": "case-00000000000000000000000000000002",
                "baseline_candidate_ids": [DOSA, IDLI],
                "aux_candidate_ids": [IDLI, DOSA],
                "relevant_dish_ids": [IDLI],
                "forbidden_dish_ids": [],
                "publication_version": VERSION,
                "slices": ["veg", "lunch"],
            },
        ],
        "resilience_cases": [{"aux_state": "timeout", "ghar_safe_deterministic_fallback": True}],
    }


def test_real_disjoint_safe_improvement_is_eligible_for_active_evaluation():
    result = evaluate(evidence())

    assert result["eligible_for_active_evaluation"] is True
    assert result["metrics"] == {
        "baseline_recall": 0.5,
        "aux_recall": 1.0,
        "baseline_mrr": 0.25,
        "aux_mrr": 1.0,
        "baseline_safety_violations": 0,
        "aux_safety_violations": 0,
        "aux_canonical_identity_rate": 1.0,
    }
    assert result["slices"]["veg"]["case_count"] == 2


@pytest.mark.parametrize(
    ("mutation", "failed_gate"),
    [
        (lambda value: value["dataset"].update(synthetic=True), "governed_holdout"),
        (
            lambda value: value["cases"][0]["aux_candidate_ids"].append(DOSA),
            "zero_aux_safety_violations",
        ),
        (
            lambda value: value["resilience_cases"][0].update(
                ghar_safe_deterministic_fallback=False
            ),
            "ghar_resilience",
        ),
        (
            lambda value: value["cases"][0].update(aux_candidate_ids=[IDLI]),
            "aux_beats_frozen_baseline",
        ),
    ],
)
def test_promotion_fails_closed_when_required_evidence_is_missing(mutation, failed_gate):
    value = evidence()
    mutation(value)

    result = evaluate(value)

    assert result["gates"][failed_gate] is False
    assert result["eligible_for_active_evaluation"] is False


def test_identity_fields_and_noncanonical_aux_ids_are_not_accepted_as_evidence():
    value = evidence()
    value["profile_id"] = "private"
    with pytest.raises(ValidationInputError, match="identity field"):
        evaluate(value)

    value = evidence()
    value["cases"][0]["aux_candidate_ids"] = ["legacy-name-key"]
    result = evaluate(value)
    assert result["gates"]["canonical_identity"] is False


def test_mixed_publications_cannot_form_one_comparison():
    value = evidence()
    value["cases"][1]["publication_version"] = "sha256:" + "b" * 64

    result = evaluate(value)

    assert result["gates"]["single_publication"] is False
    assert result["eligible_for_active_evaluation"] is False


@pytest.mark.parametrize(
    "mutation",
    [
        lambda value: value["dataset"].update(operator_note="not aggregate"),
        lambda value: value["cases"][0].update(extra_context="private"),
        lambda value: value["cases"][0].update(slices=["household:private"]),
        lambda value: value["resilience_cases"][0].update(detail="internal"),
    ],
)
def test_non_allowlisted_fields_and_slice_labels_cannot_reach_the_report(mutation):
    value = evidence()
    mutation(value)

    with pytest.raises(ValidationInputError):
        evaluate(value)
