"""
WP-18 planning-surface e2e tests (FastAPI TestClient): the onboarding→plan→dish endpoints.

Signs raw bytes exactly like test_service.py (the WP-18 routes are SIGNED_PATHS too). Validates the
five surfaces and — the key contract — that /v1/class-dishes reconciles: every returned dish belongs
to the selected class.
"""

import hashlib
import hmac
import json
import time

import pytest
from fastapi.testclient import TestClient
from ghar_re_service.providers import DEV_INSECURE_SECRET

from ghar_re_core import fixtures as F
from ghar_re_service import auth, engine, main


@pytest.fixture(scope="module")
def client():
    with TestClient(main.app) as c:
        yield c


def _hh():
    hh = [h for h in F.HOUSEHOLDS if h["id_key"] == "couple_mumbai_mh"][0]
    return {k: v for k, v in hh.items() if k != "id_key"}


def _post(client, path, payload):
    raw = json.dumps(payload).encode()
    ts = int(time.time())
    sig = hmac.new(
        DEV_INSECURE_SECRET.encode(), f"{ts}.".encode() + raw, hashlib.sha256
    ).hexdigest()
    return client.post(
        path,
        content=raw,
        headers={
            "content-type": "application/json",
            auth.SIGNATURE_HEADER: f"t={ts},v1={sig}",
        },
    )


def test_cold_start_returns_15_diverse_dishes(client):
    r = _post(client, "/v1/cold-start", {"household": _hh()})
    assert r.status_code == 200
    body = r.json()
    assert body["kind"] == "cold_start_top_dishes"
    assert len(body["dishes"]) == 15
    for d in body["dishes"]:
        assert (
            "meal_class_code" in d
            and "image_url" in d
            and d["slot"] in ("breakfast", "lunch", "dinner")
        )


def test_meal_plan_slot_options(client):
    r = _post(client, "/v1/meal-plan", {"household": _hh(), "slot": "dinner"})
    assert r.status_code == 200
    assert len(r.json()["options"]) == 8
    assert r.json()["options"][0]["explanation"]["top_contributors"]


@pytest.mark.parametrize(
    ("role", "age", "expected_class"),
    [
        ("child", 9, "LD_CHILD_MILD_PLATE"),
        ("senior", 70, "LD_ELDERLY_SOFT_DIGESTIVE"),
    ],
)
def test_meal_plan_addons_accept_live_member_role_vocabulary(client, role, age, expected_class):
    household = _hh()
    household["q12_member_ages"] = [{"role": "adult", "age": 35}, {"role": role, "age": age}]
    r = _post(
        client,
        "/v1/meal-plan",
        {"household": household, "slot": "dinner", "count": 8},
    )
    assert r.status_code == 200
    addon = next(item for item in r.json()["addons"] if item["member_role"] == role)
    assert addon["class_code"] == expected_class
    assert addon["dish"]


def test_meal_episode_surface_returns_complete_practical_slate(client):
    r = _post(
        client,
        "/v1/meal-episodes",
        {
            "household": _hh(),
            "context": {
                "slot": "dinner",
                "weekday": "Monday",
                "time_budget_minutes": 35,
                "pantry_ingredient_names": ["rice", "salt", "onion"],
            },
            "count": 4,
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["kind"] == "meal_episode_slate"
    assert 1 <= len(body["episodes"]) <= 4
    assert body["policy_code"] == "episode_success_rule_v1"
    assert len(body["eligible_episode_hashes"]) >= len(body["episodes"])
    assert {episode["episode_hash"] for episode in body["episodes"]}.issubset(
        set(body["eligible_episode_hashes"])
    )
    assert body["config_version"]
    top = body["episodes"][0]
    assert top["grammar_code"] in {"SINGLE_PRIMARY", "BASE_WITH_SIDES"}
    assert top["grammar_version"] == 1
    assert top["components"]
    assert top["practicality"]["active_minutes"] >= 0
    assert 0 <= top["predictions"]["p_execute"] <= 1
    assert top["predictions"]["calibration_status"] == "rule_baseline_untrained"
    assert all(
        left["predictions"]["p_success"] >= right["predictions"]["p_success"]
        for left, right in zip(body["episodes"], body["episodes"][1:], strict=False)
    )


def test_meal_episode_surface_enforces_canonical_request_contract(client):
    response = _post(
        client,
        "/v1/meal-episodes",
        {"household": _hh(), "context": {"slot": "dinner"}, "count": 9},
    )
    assert response.status_code == 422
    assert response.json()["error"] == "invalid_request"


def test_meal_episode_surface_preserves_finalized_class(client):
    weekly = _post(client, "/v1/weekly-plan", {"household": _hh()}).json()
    class_code = weekly["days"][0]["slots"]["dinner"][0]["class_code"]
    response = _post(
        client,
        "/v1/meal-episodes",
        {
            "household": _hh(),
            "class_code": class_code,
            "context": {"slot": "dinner", "weekday": "Monday"},
            "count": 3,
        },
    )
    assert response.status_code == 200
    from ghar_re_core import knowledge as K

    for episode in response.json()["episodes"]:
        for component in episode["components"]:
            if component["dish_id"] is not None:
                assert class_code in K.dish_to_class_codes(component["dish_name"])


def test_final_meal_episode_guardrail_audit_rechecks_identity_and_safety(monkeypatch):
    canonical_id = "00000000-0000-4000-8000-000000000001"
    canonical_dish = object()

    class Catalogue:
        def get_dish(self, dish_id):
            return canonical_dish if dish_id == canonical_id else None

    monkeypatch.setattr(engine.S, "eligible", lambda dish, theta, context: dish is canonical_dish)
    episodes = [
        {
            "components": [
                {"dish_id": canonical_id, "dish_name": "Known"},
                {"dish_id": "not-a-canonical-id", "dish_name": "Unknown"},
                {"dish_id": None, "dish_name": "Roti"},
            ]
        }
    ]

    audit = engine._meal_episode_guardrail_audit(
        episodes, _hh(), {"slot": "dinner"}, Catalogue(), "2026-08-08"
    )

    assert audit == {
        "schema_version": "ghar-final-guardrail-audit-v1",
        "measurement_status": "measured",
        "served_dish_count": 2,
        "hard_constraint_violations": 0,
        "canonical_identity_failures": 1,
        "intended_meal_date": "2026-08-08",
    }


def test_search_is_filtered_ranked_and_safety_aware(client):
    r = _post(
        client,
        "/v1/search",
        {
            "household": _hh(),
            "query": "paneer",
            "slot": "dinner",
            "limit": 10,
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["kind"] == "dish_search"
    assert body["count"] <= 10
    assert all("paneer" in f"{dish['name']} {dish['cuisine']}".lower() for dish in body["options"])


def test_meal_plan_honours_online_suppression_and_affinity(client):
    baseline = _post(client, "/v1/meal-plan", {"household": _hh(), "slot": "dinner", "count": 8})
    assert baseline.status_code == 200
    first = baseline.json()["options"][0]["name"]
    promoted = baseline.json()["options"][-1]["name"]
    personalized = _post(
        client,
        "/v1/meal-plan",
        {
            "household": _hh(),
            "slot": "dinner",
            "count": 8,
            "exclude_dish_names": [first],
            "preference_by_dish": {promoted: 1.0},
            "context": {"interaction_count": 12},
        },
    )
    assert personalized.status_code == 200
    names = [dish["name"] for dish in personalized.json()["options"]]
    assert first not in names
    assert names.index(promoted) < 7


def test_visible_episode_prefix_caps_rich_and_repeated_soup_options():
    def episode(name, richness):
        return {
            "display_name": name,
            "richness_score": richness,
            "components": [{"dish_name": name, "grammar_role": "primary"}],
        }

    ranked = [
        episode("Cream Soup", 0.9),
        episode("Paneer Gravy", 0.9),
        episode("Tomato Soup", 0.2),
        episode("Dal Makhani", 0.9),
        episode("Poha", 0.1),
        episode("Bhindi", 0.1),
    ]
    visible = engine._select_visible_episode_diversity(ranked, 4)
    assert sum(item["richness_score"] >= 0.6 for item in visible) <= 2
    assert sum("soup" in item["display_name"].casefold() for item in visible) <= 1


def test_visible_episode_prefix_defers_repeated_primary_meal_classes():
    def episode(name):
        return {
            "display_name": name,
            "richness_score": 0.1,
            "components": [{"dish_name": name, "grammar_role": "primary"}],
        }

    ranked = [
        episode("Mysore Masala Dosa"),
        episode("Masala Dosa"),
        episode("Set Dosa"),
        episode("Poha"),
        episode("Upma"),
        episode("Misal Pav"),
    ]

    visible = engine._select_visible_episode_diversity(ranked, 4)

    assert [item["display_name"] for item in visible] == [
        "Mysore Masala Dosa",
        "Poha",
        "Upma",
        "Misal Pav",
    ]


def test_visible_episode_prefix_backfills_repeated_classes_when_pool_is_thin():
    def episode(name):
        return {
            "display_name": name,
            "richness_score": 0.1,
            "components": [{"dish_name": name, "grammar_role": "primary"}],
        }

    ranked = [episode("Mysore Masala Dosa"), episode("Masala Dosa"), episode("Poha")]

    visible = engine._select_visible_episode_diversity(ranked, 3)

    assert len(visible) == 3
    assert [item["display_name"] for item in visible] == [
        "Mysore Masala Dosa",
        "Poha",
        "Masala Dosa",
    ]


def test_weekly_plan_shape(client):
    r = _post(client, "/v1/weekly-plan", {"household": _hh()})
    assert r.status_code == 200
    days = r.json()["days"]
    assert len(days) == 7
    assert all(set(d["slots"]) == {"breakfast", "lunch", "dinner"} for d in days)
    assert all(
        "preference_contribution" in meal_class
        for day in days
        for classes in day["slots"].values()
        for meal_class in classes
    )


def test_weekly_plan_uses_direct_class_signal_without_dish_expansion(client):
    baseline = _post(client, "/v1/weekly-plan", {"household": _hh()}).json()
    dinner = baseline["days"][0]["slots"]["dinner"]
    leading, target = dinner[0]["class_code"], dinner[2]["class_code"]
    response = _post(
        client,
        "/v1/weekly-plan",
        {
            "household": _hh(),
            "preference_by_direct_class": {leading: -1.0, target: 1.0},
            "preference_by_projected_class": {leading: 0.0, target: 0.0},
        },
    )
    assert response.status_code == 200
    personalized = response.json()["days"][0]["slots"]["dinner"]
    assert [item["class_code"] for item in personalized].index(target) < 2
    target_view = next(item for item in personalized if item["class_code"] == target)
    assert target_view["direct_class_preference_contribution"] > 0


def test_weekly_plan_uses_dated_slot_specific_temporal_state(client):
    baseline = _post(
        client,
        "/v1/weekly-plan",
        {"household": _hh(), "context": {"date": "2026-08-03"}},
    ).json()
    target = baseline["days"][0]["slots"]["lunch"][0]["class_code"]
    response = _post(
        client,
        "/v1/weekly-plan",
        {
            "household": _hh(),
            "context": {
                "date": "2026-08-03",
                "temporal_class_state": [
                    {
                        "meal_slot": "lunch",
                        "day_type": "weekday",
                        "class_code": target,
                        "last_positive_meal_date": "2026-08-02",
                        "mean_positive_spacing_days": 4,
                    }
                ],
            },
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["days"][0]["date"] == "2026-08-03"
    target_view = next(
        item for item in body["days"][0]["slots"]["lunch"] if item["class_code"] == target
    )
    assert target_view["temporal_contribution"] < 0


def test_class_dishes_reconciliation(client):
    """The WP-18 guarantee end-to-end: dishes for a finalized class all belong to that class."""
    wk = _post(client, "/v1/weekly-plan", {"household": _hh()}).json()
    lunch_classes = wk["days"][0]["slots"]["lunch"]
    assert lunch_classes, "no lunch classes offered"
    chosen = lunch_classes[0]["class_code"]
    r = _post(
        client,
        "/v1/class-dishes",
        {"household": _hh(), "slot": "lunch", "class_code": chosen, "weekday": "Monday"},
    )
    assert r.status_code == 200
    opts = r.json()["options"]
    assert opts
    # multi-membership reconciliation: the chosen class is among each dish's memberships.
    from ghar_re_core import knowledge as K

    assert all(chosen in K.dish_to_class_codes(o["name"]) for o in opts)


def test_recipe_detail(client):
    dish = _post(client, "/v1/cold-start", {"household": _hh()}).json()["dishes"][0]["name"]
    r = _post(client, "/v1/recipe", {"dish_name": dish})
    assert r.status_code == 200
    body = r.json()
    assert body["dish_name"] == dish
    assert body["recipe"] is not None
    assert body["recipe"]["steps"] and body["recipe"]["ingredients"]


def test_cold_start_requires_household(client):
    r = _post(client, "/v1/cold-start", {"slot": "dinner"})
    assert r.status_code == 422
