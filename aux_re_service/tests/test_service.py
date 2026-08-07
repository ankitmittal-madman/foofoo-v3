from __future__ import annotations

import copy
from dataclasses import replace

from aux_re_service.config import Mode, Settings
from aux_re_service.main import app
from aux_re_service.schemas import RecommendationRequest
from aux_re_service.service import run
from fastapi.testclient import TestClient


def settings(**overrides) -> Settings:
    base = Settings(
        enabled=True,
        mode=Mode.ACTIVE,
        min_delta=0.05,
        min_confidence=0.55,
        require_constraint_pass=True,
        use_local_reranker=True,
        log_all=False,
        allow_override=True,
        qdrant_url=None,
        qdrant_collection="recipes",
        candidate_pool_path=None,
        model_artifact_dir=None,
    )
    return replace(base, **overrides)


def payload(**overrides) -> dict:
    body = {
        "user_id": "user-1",
        "household_id": "home-1",
        "meal_slot": "dinner",
        "region": "Maharashtra",
        "preferences": ["Maharashtrian", "dal"],
        "pantry_items": ["lentils", "rice"],
        "recent_meals": ["paneer tikka"],
        "candidate_limit": 2,
        "existing_result": {
            "items": [{"id": "legacy-1", "name": "Original choice"}],
            "metrics": {
                "quality_score": 0.2,
                "confidence": 0.6,
                "diversity_score": 0.1,
                "safety_score": 1.0,
                "alignment_score": 0.1,
            },
            "opaque_legacy_field": {"must": "survive"},
        },
        "candidates": [
            {
                "id": "varan-bhaat",
                "name": "Varan Bhaat",
                "ingredients": ["lentils", "rice", "turmeric"],
                "diet_types": ["vegetarian", "vegan"],
                "regions": ["Maharashtra"],
                "cuisines": ["Maharashtrian"],
                "meal_slots": ["dinner"],
                "pantry_match": 1.0,
                "nutrition_fit": 0.9,
                "freshness": 0.9,
                "collaborative_score": 0.8,
                "popularity": 0.2,
            },
            {
                "id": "bhakri-pithla",
                "name": "Bhakri Pithla",
                "ingredients": ["chickpea flour", "millet"],
                "diet_types": ["vegetarian", "vegan"],
                "regions": ["Maharashtra"],
                "cuisines": ["Maharashtrian"],
                "meal_slots": ["dinner"],
                "pantry_match": 0.7,
                "nutrition_fit": 0.8,
                "freshness": 0.8,
                "collaborative_score": 0.7,
                "popularity": 0.1,
            },
        ],
    }
    body.update(overrides)
    return body


def test_disabled_bypasses_auxiliary_and_preserves_existing_exactly():
    raw = payload()
    original = copy.deepcopy(raw["existing_result"])
    response = run(RecommendationRequest.model_validate(raw), settings(enabled=False))
    assert response.decision_reason == "auxiliary_disabled"
    assert response.auxiliary_result is None
    assert response.selected_result == original
    assert raw["existing_result"] == original


def test_shadow_runs_and_never_overrides():
    response = run(RecommendationRequest.model_validate(payload()), settings(mode=Mode.SHADOW))
    assert response.auxiliary_result is not None
    assert response.selected_result == response.existing_result
    assert response.decision_reason == "shadow_mode_no_override"


def test_compare_can_select_only_after_policy_win():
    response = run(RecommendationRequest.model_validate(payload()), settings(mode=Mode.COMPARE))
    assert response.decision == "auxiliary"
    assert response.decision_reason == "auxiliary_won_policy_gate"


def test_active_override_can_be_killed_independently():
    response = run(RecommendationRequest.model_validate(payload()), settings(allow_override=False))
    assert response.decision == "existing"
    assert response.decision_reason == "override_disabled"


def test_hard_allergy_constraint_rejects_auxiliary():
    raw = payload(allergies=["lentils", "chickpea flour"])
    response = run(RecommendationRequest.model_validate(raw), settings())
    assert response.decision == "existing"
    assert response.decision_reason == "hard_constraint_failed"
    assert not response.constraint_checks.passed


def test_minimum_delta_keeps_existing():
    response = run(RecommendationRequest.model_validate(payload()), settings(min_delta=0.9))
    assert response.decision == "existing"
    assert response.decision_reason == "improvement_below_threshold"


def test_low_confidence_keeps_existing():
    response = run(RecommendationRequest.model_validate(payload()), settings(min_confidence=1.0))
    assert response.decision == "existing"
    assert response.decision_reason == "confidence_below_threshold"


def test_governed_context_prefers_quick_weekday_candidate_without_changing_safety():
    raw = payload(day_type="weekday")
    for candidate in raw["candidates"]:
        candidate.update({
            "pantry_match": 0.5,
            "nutrition_fit": 0.5,
            "freshness": 0.5,
            "collaborative_score": 0.5,
            "popularity": 0.5,
            "ingredients": ["vegetables"],
        })
    raw["candidates"][0]["cook_minutes"] = 25
    raw["candidates"][1]["cook_minutes"] = 75
    raw["governed_context_signals"] = [{
        "feature_code": "weekday_time_pressure",
        "value": 0.8,
        "authority": "inferred",
        "confidence": 0.65,
        "sources": ["q2_working_professionals", "q13_who_cooks"],
        "allowed_use": "soft_rank",
        "correction_state": "active",
        "feature_version": "governed-context-v1",
    }]
    response = run(RecommendationRequest.model_validate(raw), settings(min_delta=-1))
    assert response.auxiliary_result.items[0]["id"] == "varan-bhaat"
    assert response.auxiliary_result.items[0]["governed_context_reasons"] == [
        "inferred:weekday_time_pressure"
    ]


def test_unconfirmed_inference_cannot_claim_explicit_confidence():
    raw = payload(governed_context_signals=[{
        "feature_code": "weekday_time_pressure",
        "value": 0.8,
        "authority": "inferred",
        "confidence": 1,
        "sources": ["q2_working_professionals"],
        "allowed_use": "soft_rank",
        "correction_state": "active",
        "feature_version": "governed-context-v1",
    }])
    try:
        RecommendationRequest.model_validate(raw)
    except ValueError as error:
        assert "confidence" in str(error)
    else:
        raise AssertionError("unconfirmed inference should fail validation")


def test_less_diverse_auxiliary_keeps_existing():
    raw = payload()
    raw["existing_result"]["metrics"]["diversity_score"] = 1.0
    raw["candidates"][1]["ingredients"] = ["lentils", "rice", "cumin"]
    response = run(RecommendationRequest.model_validate(raw), settings())
    assert response.decision_reason == "auxiliary_less_diverse"


def test_disabled_reranker_fails_safely_to_existing():
    response = run(
        RecommendationRequest.model_validate(payload(debug=True)),
        settings(use_local_reranker=False),
    )
    assert response.decision_reason == "auxiliary_unavailable"
    assert response.selected_result == response.existing_result
    assert response.debug_trace == {"error_type": "RuntimeError"}


def test_retrieval_source_failure_preserves_other_candidates(tmp_path):
    response = run(
        RecommendationRequest.model_validate(payload(debug=True)),
        settings(candidate_pool_path=str(tmp_path / "missing.json")),
    )
    assert response.auxiliary_result is not None
    assert response.debug_trace["retrieval_failures"] == {"precomputed_pool": "FileNotFoundError"}


def test_reranker_failure_falls_back_without_leaking_details(monkeypatch):
    def broken_rank(*_args, **_kwargs):
        raise RuntimeError("sensitive internal details")

    monkeypatch.setattr("aux_re_service.service.LocalReranker.rank", broken_rank)
    response = run(RecommendationRequest.model_validate(payload(debug=True)), settings())
    assert response.decision == "existing"
    assert response.decision_reason == "auxiliary_unavailable"
    assert response.debug_trace == {"error_type": "RuntimeError"}


def test_health_and_http_contract(monkeypatch):
    monkeypatch.setenv("AUX_REC_ENABLED", "false")
    with TestClient(app) as client:
        assert client.get("/healthz").json() == {"status": "alive"}
        assert client.get("/readyz").status_code == 200
        body = client.post("/v1/recommendations", json=payload()).json()
    assert body["decision_reason"] == "auxiliary_disabled"
    assert body["selected_result"] == body["existing_result"]
    assert set(body["timings_ms"]) == {"retrieval", "reranking", "selection", "total"}
