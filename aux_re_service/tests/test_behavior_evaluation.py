from __future__ import annotations

from dataclasses import replace

from aux_re_service.config import Mode, Settings
from aux_re_service.evaluation import evaluate
from aux_re_service.ranking import LocalReranker
from aux_re_service.schemas import Candidate, RecommendationRequest


def request(candidates, **overrides):
    payload = {
        "user_id": "u",
        "household_id": "h",
        "meal_slot": "dinner",
        "region": "Maharashtra",
        "preferences": ["Maharashtrian"],
        "pantry_items": [],
        "recent_meals": [],
        "candidate_limit": 1,
        "debug": True,
        "existing_result": {
            "items": [],
            "metrics": {
                "quality_score": 0.1,
                "diversity_score": 0.0,
                "safety_score": 1.0,
                "alignment_score": 0.0,
            },
        },
        "candidates": candidates,
    }
    payload.update(overrides)
    return RecommendationRequest.model_validate(payload)


def candidate(candidate_id, **overrides):
    payload = {
        "id": candidate_id,
        "name": candidate_id,
        "ingredients": [],
        "diet_types": ["vegetarian"],
        "regions": [],
        "cuisines": [],
        "meal_slots": ["dinner"],
        "collaborative_score": 0.5,
        "freshness": 0.5,
        "nutrition_fit": 0.5,
    }
    payload.update(overrides)
    return payload


def top_id(req):
    result, _ = LocalReranker().rank([Candidate.model_validate(row) for row in req.candidates], req)
    return result.items[0]["id"]


def test_region_household_pantry_and_repetition_change_ranking():
    regional = candidate("regional", regions=["Maharashtra"], cuisines=["Maharashtrian"])
    pantry = candidate("pantry", ingredients=["rice"], pantry_match=0.0)
    assert top_id(request([regional, pantry])) == "regional"
    assert (
        top_id(request([regional, pantry], region="Kerala", preferences=[], pantry_items=["rice"]))
        == "pantry"
    )
    familiar = candidate("familiar", regions=["Maharashtra"], cuisines=["Maharashtrian"])
    novel = candidate("novel", regions=["Maharashtra"], cuisines=["Maharashtrian"])
    assert top_id(request([familiar, novel], recent_meals=["familiar"])) == "novel"


def test_meal_slot_and_allergy_are_hard_filters():
    unsafe = candidate("unsafe", ingredients=["groundnut"], collaborative_score=1.0)
    wrong_slot = candidate("breakfast", meal_slots=["breakfast"], collaborative_score=1.0)
    safe = candidate("safe", collaborative_score=0.1)
    req = request([unsafe, wrong_slot, safe], allergies=["peanut"])
    result, rejected = LocalReranker().rank(
        [Candidate.model_validate(row) for row in req.candidates], req
    )
    assert result.items[0]["id"] == "safe"
    assert {row["id"] for row in rejected} == {"unsafe", "breakfast"}


def test_offline_replay_reports_deterministic_policy_accuracy():
    safe = candidate(
        "regional",
        regions=["Maharashtra"],
        cuisines=["Maharashtrian"],
        freshness=0.9,
        nutrition_fit=0.9,
        collaborative_score=0.9,
    )
    active = replace(
        Settings.from_env(),
        enabled=True,
        mode=Mode.ACTIVE,
        allow_override=True,
        min_delta=0.05,
    )
    req = request([safe]).model_dump(mode="json")
    summary = evaluate(
        [{"request": req, "expected_decision_reason": "auxiliary_won_policy_gate"}], active
    )
    assert summary.expected_decision_accuracy == 1.0
    assert summary.auxiliary_selection_rate == 1.0
    assert summary.mean_candidate_count == 1.0
