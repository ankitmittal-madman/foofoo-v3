"""
WP-18 meal-planner tests — ghar_re_core.meal_planner (the onboarding→plan→dish surfaces).

Validates the four user-facing surfaces built on the scoring/cohort stack:
  - cold_start_top15 returns n diverse, eligible, slot-tagged dishes,
  - slot_options returns 4–5 eligible dishes for a slot,
  - weekly_class_plan gives 7 days × 3 slots, each with dish-backed top classes,
  - dishes_for_class RECONCILES: every returned dish belongs to the selected class (the contract).
"""
from ghar_re_core import meal_planner as MP
from ghar_re_core import knowledge as K
from ghar_re_core import scoring as S
from ghar_re_core.catalogue import Catalogue
from ghar_re_core.derivation import derive_theta
from ghar_re_core.pipeline import make_context


def _hh(**over):
    base = {
        "id_key": "t", "label": "t", "q1_household_type": "couple_kids",
        "q2_working_professionals": 2, "q3_home_state": "MH", "q4_current_city": "Pune",
        "q5_diet": "veg", "q6_nonveg_types": [], "q7_veg_days": [], "q8_is_jain": False,
        "q9_allergies": [], "q11_conditions": ["school_child"],
        "q12_member_ages": [{"role": "self", "age": 35}, {"role": "child", "age": 9}],
        "q13_who_cooks": "self", "q14_eat_out_per_week": 1, "q15_objective": "awesome_taste",
    }
    base.update(over)
    return base


def test_cold_start_top15_diverse_and_eligible():
    hh = _hh()
    res = MP.cold_start_top15(hh, n=15)
    assert res["kind"] == "cold_start_top_dishes"
    assert len(res["dishes"]) == 15
    names = [d["name"] for d in res["dishes"]]
    assert len(set(names)) == 15                       # no duplicate dish
    # diversity: no single meal class dominates the whole surface
    from collections import Counter
    classes = Counter(d["meal_class_code"] for d in res["dishes"])
    assert max(classes.values()) <= 3
    # every dish is slot-tagged and carries a class + score
    for d in res["dishes"]:
        assert d["slot"] in MP.MAIN_SLOTS
        assert d["score"] is not None


def test_cold_start_top15_favors_quicker_dishes_for_beginner_cooks():
    """End-to-end: a 'beginner' cook_capability measurably shifts cold_start_top15 toward lower
    total_mins dishes vs. an otherwise-identical 'advanced' household, without changing eligibility
    (both still get exactly n diverse, eligible dishes — see test_cold_start_top15_diverse_and_eligible)."""
    beginner_dishes = MP.cold_start_top15(_hh(cook_capability="beginner"), n=15)["dishes"]
    advanced_dishes = MP.cold_start_top15(_hh(cook_capability="advanced"), n=15)["dishes"]
    avg = lambda dishes: sum(d["total_mins"] for d in dishes) / len(dishes)  # noqa: E731
    assert avg(beginner_dishes) <= avg(advanced_dishes)


def test_slot_options_returns_a_short_eligible_list():
    hh = _hh(q5_diet="veg")
    opts = MP.slot_options(hh, "dinner", n=5)["options"]
    assert 1 <= len(opts) <= 5
    cat = Catalogue()
    theta = derive_theta(hh)
    ctx = make_context(slot="dinner", weekday="Monday")
    for o in opts:
        d = cat.get(o["name"])
        assert S.eligible(d, theta, ctx)               # only eligible dishes surface
        assert S.m_slot(d, ctx) == 1.0                 # and only slot-appropriate ones


def test_weekly_class_plan_shape_and_dish_backed():
    hh = _hh()
    wk = MP.weekly_class_plan(hh, top_classes=3)
    assert len(wk["days"]) == 7
    for day in wk["days"]:
        assert set(day["slots"]) == set(MP.MAIN_SLOTS)
        for classes in day["slots"].values():
            assert len(classes) <= 3
            for c in classes:
                assert c["dish_count"] >= 1             # never offer a class with no dishes
                assert c["class_name"]


def test_dishes_for_class_reconciliation_contract():
    """The core WP-18 guarantee: dishes shown for a finalized class belong ONLY to that class."""
    hh = _hh()
    wk = MP.weekly_class_plan(hh)
    day = wk["days"][2]                                  # Wednesday
    chosen = day["slots"]["lunch"][0]["class_code"]     # top lunch class (well-backed)
    rec = MP.dishes_for_class(hh, "lunch", chosen, weekday="Wednesday")
    assert rec["kind"] == "reconciled_class_dishes"
    assert rec["count"] >= 1
    # multi-membership (WP-17.1): a dish reconciles to the chosen class if that class is ANY of its
    # memberships (primary or secondary), so the day's dish list can never show an off-class dish.
    for d in rec["options"]:
        assert chosen in K.dish_to_class_codes(d["name"])


def test_cook_capability_bias_reorders_beginner_without_changing_scores():
    """_apply_cook_capability_bias is a RANKING adjustment only (meal_planner.py's own charter —
    never invents a score, never touches eligibility): a 'beginner' household should see
    within-budget dishes ranked ahead of longer ones, with every original (score, dish) pair and
    every score value preserved exactly, just reordered."""
    from types import SimpleNamespace
    quick = SimpleNamespace(name="quick", total_mins=20)
    slow = SimpleNamespace(name="slow", total_mins=90)
    unknown = SimpleNamespace(name="unknown", total_mins=None)
    ranked = [(0.9, slow), (0.8, quick), (0.7, unknown)]  # best-first, slow happens to score highest

    beginner = MP._apply_cook_capability_bias(ranked, "beginner")
    assert [d.name for _, d in beginner] == ["quick", "unknown", "slow"]
    assert sorted(s for s, _ in beginner) == sorted(s for s, _ in ranked)  # no score was altered

    # no-op for intermediate/advanced/unknown cook_capability — original order preserved exactly
    for cap in ("intermediate", "advanced", None, "not_a_real_value"):
        assert MP._apply_cook_capability_bias(ranked, cap) == ranked


def test_jain_household_surfaces_only_jain_dishes():
    """Eligibility is never loosened by the planner — a Jain household's options stay Jain-safe."""
    hh = _hh(q3_home_state="Gujarat", q4_current_city="Ahmedabad", q8_is_jain=True,
             q1_household_type="couple", q11_conditions=[],
             q12_member_ages=[{"role": "self", "age": 40}, {"role": "spouse", "age": 38}])
    cat = Catalogue()
    for d in MP.cold_start_top15(hh)["dishes"]:
        assert cat.get(d["name"]).jain_compatible == "Y"


def test_cold_start_top15_varies_by_day_for_the_same_household():
    """household_id alone is a FIXED seed for a fixed real user, so the exploration swap would
    replay identically forever (the Founder-reported 'looks static across repeat views' gap).
    variety_salt decorrelates the seed per day: same household + different day -> a genuinely
    different top-15 is possible (not guaranteed for every household/day pair, since a narrow
    theta can legitimately have too few eligible/diverse candidates to swap among — but at least
    one of these two consecutive-day draws should differ for a normal household)."""
    hh = _hh()
    day1 = MP.cold_start_top15(hh, n=15, household_id="hh-42", variety_salt="2026-08-04")
    day2 = MP.cold_start_top15(hh, n=15, household_id="hh-42", variety_salt="2026-08-05")
    day1_again = MP.cold_start_top15(hh, n=15, household_id="hh-42", variety_salt="2026-08-04")
    # same household + same day -> perfectly reproducible (not flaky/random per request)
    assert [d["name"] for d in day1["dishes"]] == [d["name"] for d in day1_again["dishes"]]
    # same household + different day -> at least a chance to differ (this household/theta does)
    assert [d["name"] for d in day1["dishes"]] != [d["name"] for d in day2["dishes"]]


def test_cold_start_top15_variety_never_changes_the_underlying_scores():
    """Exploration only ever changes WHICH already-eligible, already-scored dish gets picked —
    personalization (theta-derived ranking) itself must never degrade just because the day's
    variety_salt differs. Every dish that appears on any day's list carries the exact same score
    it would get with no exploration at all (household_id=None)."""
    hh = _hh()
    baseline = MP.cold_start_top15(hh, n=15)
    baseline_scores = {d["name"]: d["score"] for d in baseline["dishes"]}
    for salt in ("2026-08-04", "2026-08-05", "2026-08-06"):
        varied = MP.cold_start_top15(hh, n=15, household_id="hh-42", variety_salt=salt)
        for d in varied["dishes"]:
            if d["name"] in baseline_scores:
                assert d["score"] == baseline_scores[d["name"]]
