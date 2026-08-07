"""
Calibration grid tests — ghar_re_core.calibration (the post-onboarding dish-pick surface).

Validates: each slot returns n_positive expected-positive + n_negative planted-negative cells;
every cell (positive AND negative) independently passes scoring.eligible (negatives are a weak
personal fit, never an ineligible/unsafe dish); no duplicate dish within a slot; deterministic
dish selection for a given household+weekday (household_id only affects on-screen shuffle order).
"""

from collections import Counter

from ghar_re_core import calibration as C
from ghar_re_core import scoring as S
from ghar_re_core.catalogue import Catalogue
from ghar_re_core.derivation import derive_theta
from ghar_re_core.meal_planner import MAIN_SLOTS
from ghar_re_core.pipeline import make_context


def _hh(**over):
    base = {
        "id_key": "t",
        "label": "t",
        "q1_household_type": "couple_kids",
        "q2_working_professionals": 2,
        "q3_home_state": "MH",
        "q4_current_city": "Pune",
        "q5_diet": "veg",
        "q6_nonveg_types": [],
        "q7_veg_days": [],
        "q8_is_jain": False,
        "q9_allergies": [],
        "q11_conditions": ["school_child"],
        "q12_member_ages": [{"role": "self", "age": 35}, {"role": "child", "age": 9}],
        "q13_who_cooks": "self",
        "q14_eat_out_per_week": 1,
        "q15_objective": "awesome_taste",
    }
    base.update(over)
    return base


def test_calibration_grid_shape_and_roles():
    hh = _hh()
    res = C.calibration_grid(hh)
    assert res["kind"] == "calibration_grid"
    assert set(res["slots"].keys()) == set(MAIN_SLOTS)
    for slot in MAIN_SLOTS:
        cells = res["slots"][slot]
        assert len(cells) == C.DEFAULT_N_POSITIVE + C.DEFAULT_N_NEGATIVE
        roles = Counter(c["cell_role"] for c in cells)
        assert roles["expected_positive"] == C.DEFAULT_N_POSITIVE
        assert roles["planted_negative"] == C.DEFAULT_N_NEGATIVE
        names = [c["name"] for c in cells]
        assert len(set(names)) == len(names)  # no duplicate dish within a slot

    all_names = [cell["name"] for slot in MAIN_SLOTS for cell in res["slots"][slot]]
    assert len(set(all_names)) == len(all_names)  # no repetition across meal slots
    assert len(res["_candidate_lineage"]) > len(all_names)
    assert {row["slot"] for row in res["_candidate_lineage"]} == set(MAIN_SLOTS)
    cat = Catalogue()
    assert sum(C._is_soup(cat.get(name)) for name in all_names) <= C.MAX_GRID_SOUPS


def test_calibration_cells_are_all_eligible():
    """Planted negatives are a weak fit, never an unsafe/ineligible dish — every returned name
    must independently pass scoring.eligible for its own slot's theta/context."""
    hh = _hh()
    cat = Catalogue()
    theta = derive_theta(hh)
    res = C.calibration_grid(hh, catalogue=cat)
    by_name = {d.name: d for d in cat}
    for slot in MAIN_SLOTS:
        ctx = make_context(slot=slot, weekday="Monday")
        for cell in res["slots"][slot]:
            dish = by_name[cell["name"]]
            assert S.eligible(dish, theta, ctx), f"{cell['name']} ({slot}) failed eligibility"


def test_calibration_challengers_do_not_come_from_the_bizarre_bottom_tail():
    hh = _hh(q3_home_state="MP", q4_current_city="Mumbai")
    cat = Catalogue()
    theta = derive_theta(hh)
    for slot in MAIN_SLOTS:
        ctx = make_context(slot=slot, weekday="Monday")
        ranked = C._ranked_eligible(cat, theta, ctx, hh["q15_objective"])
        positives = C._pick_positives(ranked, C.DEFAULT_N_POSITIVE)
        challengers = C._pick_negatives(ranked, positives, C.DEFAULT_N_NEGATIVE)
        rank_by_name = {dish.name: index for index, (_, dish) in enumerate(ranked)}
        tail_start = max(
            len(positives) + C.DEFAULT_N_NEGATIVE,
            int(len(ranked) * C.CHALLENGER_MAX_QUANTILE),
        )
        if len(ranked) >= C.DEFAULT_N_POSITIVE + C.DEFAULT_N_NEGATIVE + 2:
            assert all(rank_by_name[dish.name] <= tail_start for _, dish in challengers)


def test_calibration_grid_deterministic_without_household_id():
    hh = _hh()
    res1 = C.calibration_grid(hh, weekday="Monday")
    res2 = C.calibration_grid(hh, weekday="Monday")
    for slot in MAIN_SLOTS:
        names1 = [c["name"] for c in res1["slots"][slot]]
        names2 = [c["name"] for c in res2["slots"][slot]]
        assert names1 == names2


def test_calibration_grid_household_id_shuffles_order_only():
    """household_id seeds the on-screen shuffle, never which dishes are chosen."""
    hh = _hh()
    plain = C.calibration_grid(hh, weekday="Monday")
    seeded = C.calibration_grid(hh, weekday="Monday", household_id="hh-42")
    for slot in MAIN_SLOTS:
        plain_names = {c["name"] for c in plain["slots"][slot]}
        seeded_names = {c["name"] for c in seeded["slots"][slot]}
        assert plain_names == seeded_names


def test_calibration_grid_excludes_recently_served_dishes_across_every_slot():
    hh = _hh()
    first = C.calibration_grid(hh, weekday="Monday")
    served = [cell["name"] for cells in first["slots"].values() for cell in cells]
    refreshed = C.calibration_grid(hh, weekday="Monday", exclude_dish_names=served)
    refreshed_names = {cell["name"] for cells in refreshed["slots"].values() for cell in cells}
    assert refreshed_names.isdisjoint(served)


def test_calibration_grid_applies_online_dish_affinity_to_scores():
    hh = _hh()
    baseline = C.calibration_grid(hh, weekday="Monday")
    liked = next(
        cell
        for cells in baseline["slots"].values()
        for cell in cells
        if cell["cell_role"] == "expected_positive"
    )
    personalized = C.calibration_grid(
        hh,
        weekday="Monday",
        preference_by_dish={liked["name"]: 1.0},
    )
    personalized_cell = next(
        cell
        for cells in personalized["slots"].values()
        for cell in cells
        if cell["name"] == liked["name"]
    )
    assert personalized_cell["score"] == round(liked["score"] + 0.35, 4)
