from __future__ import annotations

import pytest
from aux_re_service.lightfm_runtime import LightFMArtifactError, LightFMScorer
from aux_re_service.schemas import Candidate, RecommendationRequest


class FakeModel:
    def predict(self, _users, items, **_kwargs):
        return [float(item) for item in items]


def artifact(*, synthetic=False, promoted=True):
    return {
        "metadata": {
            "format": "foofoo-lightfm-v1",
            "model_version": "sha256:test",
            "synthetic_only": synthetic,
            "promotion_gate_passed": promoted,
        },
        "model": FakeModel(),
        "user_features": object(),
        "item_features": object(),
        "user_id_map": {"dataset_1:HH-1": 0},
        "item_id_map": {"DISH_A": 0, "DISH_B": 1},
    }


def request(household_id="HH-1"):
    return RecommendationRequest.model_validate(
        {
            "user_id": "u",
            "household_id": household_id,
            "meal_slot": "dinner",
            "existing_result": {"items": []},
        }
    )


def test_artifact_rejects_synthetic_or_unpromoted_by_default():
    with pytest.raises(LightFMArtifactError, match="synthetic"):
        LightFMScorer(artifact(synthetic=True), allow_synthetic=False, allow_unpromoted=False)
    with pytest.raises(LightFMArtifactError, match="promotion"):
        LightFMScorer(artifact(promoted=False), allow_synthetic=False, allow_unpromoted=False)


def test_model_scores_known_candidates_and_keeps_unknown_candidates():
    scorer = LightFMScorer(artifact(), allow_synthetic=False, allow_unpromoted=False)
    candidates = [
        Candidate(id="DISH_A", name="A", collaborative_score=0.2),
        Candidate(id="DISH_B", name="B", collaborative_score=0.2),
        Candidate(id="DISH_UNKNOWN", name="Unknown", collaborative_score=0.2),
    ]
    output, trace = scorer.apply(candidates, request(), blend_weight=1.0)
    assert trace.applied and trace.scored_candidates == 2
    assert output[1].collaborative_score > output[0].collaborative_score
    assert output[2].collaborative_score == 0.2
    assert candidates[0].collaborative_score == 0.2


def test_unknown_household_falls_back_without_scoring():
    scorer = LightFMScorer(artifact(), allow_synthetic=False, allow_unpromoted=False)
    candidates = [Candidate(id="DISH_A", name="A")]
    output, trace = scorer.apply(candidates, request("new-household"), blend_weight=1.0)
    assert output == candidates
    assert trace.reason == "unknown_household"
