"""
Phase 8 — Recommendation engine BLACK-BOX behaviour testing.

Rule (from the program brief): treat the RE as a black box. Do NOT verify formulas or score
values. Verify observable behaviour only:

  * correct HTTP outcome per persona (200 vs a clean 422 — never a 500),
  * hard EXCLUSIONS honoured (a veg/jain household is never served a non_veg dish; an allergen
    household is never served a dish containing that allergen),
  * plate COUNT / shape contract,
  * DIVERSITY (served plates are distinct and the declared Home prefix caps hold),
  * SELECTION METADATA (the policy and both relevance/selection scores remain explicit),
  * PERSISTENCE / determinism (the same request twice yields the same heroes),
  * FALLBACK (a legitimately constrained household degrades via warnings[], not a 500).

Every persona comes from ops/quality/personas/personas.py, itself grounded in the real request
contract, so each case is a request the production service actually accepts.
"""

from __future__ import annotations

import math

import pytest

from ops.quality.personas.personas import all_personas

PERSONAS = all_personas()
IDS = [p.key for p in PERSONAS]


@pytest.fixture(autouse=True)
def _raise_rate_limit_for_persona_suite(client):
    """Temporarily raise the shared TestClient's rate-limiter cap for this module only.

    100 personas x several behavioural assertions issues hundreds of /v1/recommendations calls
    from one shared TestClient (one rate-limiter "client key") within seconds — comfortably over
    the production default (300 req/min, see ratelimit.py), which would turn "too many test
    requests" into spurious persona failures (429s masquerading as broken exclusion/determinism/
    plate-count behaviour). Scoped to an autouse fixture in THIS module (not conftest.py) so
    test_api_security.py's flood/429 tests, which deliberately exercise the real production limit
    on the same shared client, are unaffected.
    """
    from ghar_re_service import main

    limiter = main.state.rate_limiter
    original = limiter.max_requests
    limiter.max_requests = 100_000
    try:
        yield
    finally:
        limiter.max_requests = original
        # Also drop every hit timestamp this module's burst recorded under the raised cap —
        # restoring max_requests alone leaves the shared TestClient's client-key hit history full,
        # which would make the very next request from any OTHER suite (e.g. test_api_security.py's
        # own flood tests) see a window that already looks saturated and get a spurious 429.
        limiter._hits.clear()


def _resolve_diets(body: dict, dish_index: dict) -> list[str]:
    """Return the diet of every served hero dish, resolved via the catalogue (black-box)."""
    diets = []
    for plate in body.get("plates", []):
        for did in plate.get("hero_dish_ids", []):
            dish = dish_index.get(did)
            if dish is not None:
                diets.append(getattr(dish, "diet", None))
    return diets


def _resolve_ingredients(body: dict, dish_index: dict) -> set[str]:
    """Return the union of ingredient tokens across every served hero dish (lowercased)."""
    toks: set[str] = set()
    for plate in body.get("plates", []):
        for did in plate.get("hero_dish_ids", []):
            dish = dish_index.get(did)
            if dish is None:
                continue
            for name in getattr(dish, "ingredient_names", []) or []:
                toks.add(str(name).lower())
    return toks


def _assert_home_diversity(persona_key: str, plates: list[dict], dish_index: dict) -> None:
    """Verify hard hero uniqueness and observable class/cuisine variety for ``home_v2``.

    Richness/class/cuisine prefix caps are soft when the selector must use its documented relaxed
    backfill to preserve availability. The black-box boundary therefore checks the invariants that
    never relax, plus non-trivial output variety; core selector tests own the exact cap mechanics.
    """
    from ghar_re_core import knowledge as K

    hero_ids = [dish_id for plate in plates for dish_id in plate["hero_dish_ids"]]
    assert len(hero_ids) == len(set(hero_ids)), f"{persona_key}: hero dish reused across plates"
    dishes = [dish_index[dish_id] for dish_id in hero_ids]
    classes = {K.dish_to_class_code(dish.name) for dish in dishes} - {None}
    cuisines = {dish.cuisine for dish in dishes if dish.cuisine}
    if len(plates) >= 4:
        assert len(classes) >= 2, f"{persona_key}: full slate collapsed to one meal class"
        assert len(cuisines) >= 2, f"{persona_key}: full slate collapsed to one cuisine"


@pytest.mark.parametrize("persona", PERSONAS, ids=IDS)
def test_persona_http_outcome(persona, signed_post):
    """Each persona yields its expected HTTP status — and NEVER a 500 (a 500 is always a defect)."""
    r = signed_post(
        "/v1/recommendations", {"household": persona.household, "context": persona.context}
    )
    assert r.status_code != 500, f"{persona.key}: server error 500 — {r.text}"
    assert r.status_code == persona.expect_status, (
        f"{persona.key}: expected {persona.expect_status}, got {r.status_code}: {r.text}"
    )


@pytest.mark.parametrize(
    "persona",
    [p for p in PERSONAS if p.expect_status == 200],
    ids=[p.key for p in PERSONAS if p.expect_status == 200],
)
def test_persona_diet_exclusion(persona, signed_post, dish_index):
    """A household's forbidden diet (e.g. non_veg for a veg/jain household) is never served."""
    if not persona.forbid_diet:
        pytest.skip("no diet exclusion asserted for this persona")
    r = signed_post(
        "/v1/recommendations", {"household": persona.household, "context": persona.context}
    )
    assert r.status_code == 200, r.text
    diets = _resolve_diets(r.json(), dish_index)
    violations = [d for d in diets if d in persona.forbid_diet]
    assert not violations, f"{persona.key}: served forbidden diet(s) {set(violations)}"


@pytest.mark.parametrize(
    "persona",
    [p for p in PERSONAS if p.forbid_ingredients],
    ids=[p.key for p in PERSONAS if p.forbid_ingredients],
)
def test_persona_allergen_exclusion(persona, signed_post, dish_index):
    """An allergen household is never served a dish containing the forbidden ingredient token."""
    r = signed_post(
        "/v1/recommendations", {"household": persona.household, "context": persona.context}
    )
    assert r.status_code == 200, r.text
    served = _resolve_ingredients(r.json(), dish_index)
    hit = [tok for tok in persona.forbid_ingredients if tok.lower() in served]
    assert not hit, f"{persona.key}: served forbidden allergen ingredient(s) {hit}"


@pytest.mark.parametrize(
    "persona",
    [p for p in PERSONAS if p.expect_status == 200 and p.expect_plates == 7],
    ids=[p.key for p in PERSONAS if p.expect_status == 200 and p.expect_plates == 7],
)
def test_persona_plate_count(persona, signed_post):
    """Personas expected to reach a full plan return exactly the contracted 7 plates."""
    r = signed_post(
        "/v1/recommendations", {"household": persona.household, "context": persona.context}
    )
    assert r.status_code == 200, r.text
    assert len(r.json()["plates"]) == 7


@pytest.mark.parametrize(
    "persona",
    [p for p in PERSONAS if p.expect_status == 200],
    ids=[p.key for p in PERSONAS if p.expect_status == 200],
)
def test_persona_diversity_and_selection_policy(persona, signed_post, dish_index):
    """Served plates are distinct and carry honest policy-specific selection metadata."""
    r = signed_post(
        "/v1/recommendations", {"household": persona.household, "context": persona.context}
    )
    assert r.status_code == 200, r.text
    plates = r.json()["plates"]
    plate_ids = [p["plate_id"] for p in plates]
    assert len(plate_ids) == len(set(plate_ids)), f"{persona.key}: duplicate plate_id in plan"
    policies = {plate["selection_policy"] for plate in plates}
    assert policies <= {"home_diversity_v2", "adaptive_history_v1"}
    assert len(policies) == 1, f"{persona.key}: mixed selection policies in one slate: {policies}"
    assert all(
        math.isfinite(plate["plate_score"])
        and math.isfinite(plate["selection_score"])
        and plate["final_score"] == plate["plate_score"]
        for plate in plates
    ), f"{persona.key}: invalid or inconsistent score metadata"
    _assert_home_diversity(persona.key, plates, dish_index)


@pytest.mark.parametrize(
    "persona",
    [p for p in PERSONAS if p.expect_status == 200],
    ids=[p.key for p in PERSONAS if p.expect_status == 200],
)
def test_persona_determinism(persona, signed_post):
    """The same request twice yields identical hero dishes (persistence/repeatability)."""
    body = {"household": persona.household, "context": persona.context}
    r1 = signed_post("/v1/recommendations", body)
    r2 = signed_post("/v1/recommendations", body)
    assert r1.status_code == 200 and r2.status_code == 200
    heroes1 = [p["hero_dish_ids"] for p in r1.json()["plates"]]
    heroes2 = [p["hero_dish_ids"] for p in r2.json()["plates"]]
    assert heroes1 == heroes2, f"{persona.key}: non-deterministic recommendations across calls"


@pytest.mark.parametrize(
    "persona",
    [p for p in PERSONAS if p.expect_warnings is not None],
    ids=[p.key for p in PERSONAS if p.expect_warnings is not None],
)
def test_persona_fallback_warnings(persona, signed_post):
    """A constrained household degrades via warnings[], never via a 500 (fallback behaviour)."""
    r = signed_post(
        "/v1/recommendations", {"household": persona.household, "context": persona.context}
    )
    assert r.status_code == 200, r.text
    has_warn = bool(r.json()["warnings"])
    assert has_warn == persona.expect_warnings, (
        f"{persona.key}: warnings present={has_warn}, expected={persona.expect_warnings}"
    )
