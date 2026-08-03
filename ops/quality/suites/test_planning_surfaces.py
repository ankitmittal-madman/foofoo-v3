"""
Phase 4/5/8 — WP-18 planning surfaces (the meal-planning API the mobile app drives).

Covers the five signed planning endpoints:
  /v1/cold-start, /v1/meal-plan, /v1/weekly-plan, /v1/class-dishes, /v1/recipe.

Each is signed + rate-limited exactly like /v1/recommendations, so every test posts via the HMAC
`signed_post` helper. These tests assert observable behaviour (auth gate, 200 vs clean 422, basic
result shape), not planner math.
"""

from __future__ import annotations

import pytest

HH = {
    "q1_household_type": "couple", "q2_working_professionals": 2, "q3_home_state": "Maharashtra",
    "q4_current_city": "Pune", "q5_diet": "veg", "q7_veg_days": [], "q8_is_jain": False,
    "q9_allergies": [], "q11_conditions": [], "q12_member_ages": [{"role": "self", "age": 34}, {"role": "adult", "age": 31}], "q13_who_cooks": "self",
    "q14_eat_out_per_week": 1, "q15_objective": "healthy_living",
}
CTX = {"slot": "dinner", "season": "monsoon", "weather": {"is_raining": True, "temp_c": 27}}

HOUSEHOLD_SURFACES = ["/v1/cold-start", "/v1/meal-plan", "/v1/weekly-plan", "/v1/class-dishes"]


@pytest.mark.parametrize("path", HOUSEHOLD_SURFACES)
def test_household_surface_requires_signature(client, path):
    """Every planning surface rejects an unsigned request with 401 before doing any work."""
    r = client.post(path, json={"household": HH, "context": CTX})
    assert r.status_code == 401


@pytest.mark.parametrize("path", HOUSEHOLD_SURFACES)
def test_household_surface_missing_household_is_422(signed_post, path):
    """A planning surface with no household is a clean 422, never a 500."""
    r = signed_post(path, {"context": CTX})
    assert r.status_code == 422, r.text
    assert r.json()["error"] == "invalid_request"


def test_cold_start_returns_result(signed_post):
    r = signed_post("/v1/cold-start", {"household": HH, "context": CTX})
    assert r.status_code == 200, r.text
    body = r.json()
    assert "request_id" in body
    assert isinstance(body, dict)


def test_meal_plan_returns_result(signed_post):
    r = signed_post("/v1/meal-plan", {"household": HH, "context": CTX})
    assert r.status_code == 200, r.text
    assert "request_id" in r.json()


def test_weekly_plan_returns_result(signed_post):
    r = signed_post("/v1/weekly-plan", {"household": HH, "context": CTX})
    assert r.status_code == 200, r.text
    assert "request_id" in r.json()


def test_recipe_surface_signed_and_handles_missing_dish(signed_post, client):
    """/v1/recipe needs no household but is still signed; a bad/absent dish id must not 500."""
    r_unsigned = client.post("/v1/recipe", json={"dish_id": "md5:Butter Chicken"})
    assert r_unsigned.status_code == 401
    r = signed_post("/v1/recipe", {"dish_id": "md5:__does_not_exist__"})
    assert r.status_code in {200, 422, 404}, r.text
    assert r.status_code != 500
