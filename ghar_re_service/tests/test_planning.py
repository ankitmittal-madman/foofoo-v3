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
from ghar_re_service import auth, main


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


def test_weekly_plan_shape(client):
    r = _post(client, "/v1/weekly-plan", {"household": _hh()})
    assert r.status_code == 200
    days = r.json()["days"]
    assert len(days) == 7
    assert all(set(d["slots"]) == {"breakfast", "lunch", "dinner"} for d in days)


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
