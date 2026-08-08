from __future__ import annotations

import json
import time
from dataclasses import replace

from aux_re_service.config import Mode, Settings
from aux_re_service.experiments import assign
from aux_re_service.feedback import LocalFeedbackStore
from aux_re_service.main import app
from aux_re_service.schemas import FeedbackEvent, RecommendationRequest
from aux_re_service.service import run
from aux_re_service.training.feedback_pipeline import normalize
from fastapi.testclient import TestClient

from aux_re_service import auth


def feedback_payload(**overrides):
    payload = {
        "event_id": "feedback-1",
        "user_id": "U-1",
        "household_id": "HH-1",
        "dish_id": "DISH_POHA",
        "event_type": "cooked",
        "meal_slot": "breakfast",
        "context": {"day_type": "weekday"},
    }
    payload.update(overrides)
    return payload


def recommendation_payload():
    return {
        "user_id": "U-1",
        "household_id": "HH-1",
        "meal_slot": "dinner",
        "existing_result": {
            "items": [{"id": "old", "name": "Old"}],
            "metrics": {
                "quality_score": 0.1,
                "confidence": 0.5,
                "diversity_score": 0.0,
                "safety_score": 1.0,
                "alignment_score": 0.0,
            },
        },
        "candidates": [
            {
                "id": "new",
                "name": "New",
                "meal_slots": ["dinner"],
                "collaborative_score": 1.0,
                "nutrition_fit": 1.0,
                "freshness": 1.0,
            }
        ],
    }


def active_settings(**overrides):
    base = replace(
        Settings.from_env(),
        enabled=True,
        mode=Mode.ACTIVE,
        allow_override=True,
        min_delta=0.0,
        min_confidence=0.0,
        experiment_enabled=True,
    )
    return replace(base, **overrides)


def test_feedback_store_is_idempotent(tmp_path):
    path = tmp_path / "feedback.jsonl"
    store = LocalFeedbackStore(path.resolve())
    event = FeedbackEvent.model_validate(feedback_payload())
    assert store.append(event) is True
    assert store.append(event) is False
    assert [json.loads(line)["event_id"] for line in path.read_text().splitlines()] == [
        "feedback-1"
    ]


def test_feedback_http_is_disabled_by_default_and_writes_when_enabled(monkeypatch, tmp_path):
    secret = "test-shared-secret"
    monkeypatch.setenv("AUX_REC_SERVICE_SECRET", secret)
    raw_body = json.dumps(feedback_payload(), separators=(",", ":")).encode()

    def post(client):
        timestamp = int(time.time())
        return client.post(
            "/v1/feedback",
            content=raw_body,
            headers={
                "content-type": "application/json",
                auth.SIGNATURE_HEADER: (
                    f"t={timestamp},v1={auth.signature(secret, timestamp, raw_body)}"
                ),
            },
        )

    monkeypatch.setenv("AUX_REC_FEEDBACK_ENABLED", "false")
    with TestClient(app) as client:
        assert post(client).status_code == 503

    path = (tmp_path / "feedback.jsonl").resolve()
    monkeypatch.setenv("AUX_REC_FEEDBACK_ENABLED", "true")
    monkeypatch.setenv("AUX_REC_FEEDBACK_PATH", str(path))
    with TestClient(app) as client:
        first = post(client).json()
        second = post(client).json()
        metrics = client.get("/metrics").text
    assert first == {"accepted": True, "stored": True, "event_id": "feedback-1"}
    assert second == {"accepted": True, "stored": False, "event_id": "feedback-1"}
    assert "foofoo_aux_re_feedback_received_total" in metrics


def test_experiment_assignment_is_stable_and_control_never_overrides():
    control = active_settings(experiment_percent=0.0)
    assert assign("HH-1", control) == assign("HH-1", control)
    response = run(RecommendationRequest.model_validate(recommendation_payload()), control)
    assert response.decision == "existing"
    assert response.decision_reason == "experiment_control"
    assert response.model_metadata["experiment"]["variant"] == "control"

    treatment = active_settings(experiment_percent=1.0)
    response = run(RecommendationRequest.model_validate(recommendation_payload()), treatment)
    assert response.decision == "auxiliary"
    assert response.model_metadata["experiment"]["variant"] == "treatment"


def test_feedback_pipeline_builds_positive_negative_vote_and_substitution_rows(tmp_path):
    source = tmp_path / "feedback.jsonl"
    events = [
        feedback_payload(
            event_id="vote", event_type="household_vote", member_id="M-1", feedback_score=5
        ),
        feedback_payload(event_id="reject", event_type="rejected"),
        feedback_payload(
            event_id="swap",
            event_type="substituted",
            substitute_dish_id="DISH_UPMA",
        ),
    ]
    source.write_text("".join(json.dumps(row) + "\n" for row in events))
    report = normalize(source, tmp_path / "normalized.jsonl", tmp_path / "report.json")
    assert report["valid_unique_events"] == 3
    assert report["normalized_interactions"] == 4
    assert report["positive_interactions"] == 2
    assert report["negative_interactions"] == 2
    assert report["household_votes"] == 1
