"""
ghar_re_core.calibration — post-onboarding "dish pick" calibration grid.

Same charter as meal_planner.py (see its module docstring): built ON TOP of the existing
scoring/eligibility stack, WITHOUT touching the Core Spine math. Nothing here decides eligibility
(scoring.eligible stays the sole filter) or invents a score (scoring.score is the sole score) —
this module only picks WHICH already-eligible, already-scored dishes to surface and in what role.

The idea (ported from scareme21-create/NewFoo's ghar_re/calibration.py design, RFC-CALIB-001,
adapted without its distance.py — that module doesn't exist in this engine and building it is out
of scope for this change): per slot, show 5 dishes — a few genuinely good matches (expected
positives) mixed with a couple of plausible lower-middle-ranked challengers. Challengers remain
100% safe/diet-compliant and informative, but never come from the bizarre bottom tail merely to
manufacture a strong negative signal. If a user likes one, that is a useful early correction.

`cell_role` ("expected_positive" | "planted_negative") is engine-internal bookkeeping for the
feedback substrate — the client must never render it, only echo it back on a feedback event.
"""

import random

from ghar_re_core import knowledge as K
from ghar_re_core import scoring as S
from ghar_re_core.catalogue import Catalogue
from ghar_re_core.meal_planner import MAIN_SLOTS, _class_names, _theta_obj
from ghar_re_core.pipeline import make_context

DEFAULT_N_POSITIVE = 3
DEFAULT_N_NEGATIVE = 2
CHALLENGER_MIN_QUANTILE = 0.30
CHALLENGER_MAX_QUANTILE = 0.70
MAX_GRID_SOUPS = 1


def _is_soup(dish):
    return "soup" in dish.name.casefold() or "soup" in set(dish.dish_category or [])


def _ranked_eligible(cat, theta, ctx, objective):
    """(score, dish) for every slot-appropriate, eligible dish, best first. Same two-line filter
    meal_planner._ranked applies (S.m_slot + S.eligible) — kept as a local copy here rather than an
    import of that underscore-prefixed helper, so this file never reaches into meal_planner's
    private surface, only its public constants/helpers (MAIN_SLOTS, _class_names, _theta_obj are
    already treated as shared WP-18-surface plumbing, not Core Spine math)."""
    out = []
    for d in cat:
        if S.m_slot(d, ctx) == 0.0:
            continue
        if not S.eligible(d, theta, ctx):
            continue
        out.append((S.score(d, theta, ctx, objective), d))
    out.sort(key=lambda x: -x[0])
    return out


def _dish_cell(d, theta, ctx, objective, score, cell_role):
    code = K.dish_to_class_code(d.name)
    return {
        "name": d.name,
        "cuisine": d.cuisine,
        "diet": d.diet,
        "meal_class_code": code,
        "meal_class_name": _class_names().get(code),
        "spice_level": d.spice_level,
        "heaviness": d.heaviness,
        "total_mins": d.total_mins,
        "score": round(score, 4),
        "cell_role": cell_role,
    }


def _pick_positives(ranked, n, max_soups=1):
    """Top-n by score, capped 1-per-class and 1-per-cuisine (same diversity spirit as
    meal_planner._diversify, reimplemented at this small 3-item scale). Falls back to filling from
    the remainder if the caps are too tight to reach n — never fabricates a dish."""
    picked, seen_class, seen_cuisine, soup_count = [], set(), set(), 0
    for score, d in ranked:
        code = K.dish_to_class_code(d.name)
        if (
            code in seen_class
            or d.cuisine in seen_cuisine
            or (_is_soup(d) and soup_count >= max_soups)
        ):
            continue
        picked.append((score, d))
        seen_class.add(code)
        seen_cuisine.add(d.cuisine)
        soup_count += int(_is_soup(d))
        if len(picked) >= n:
            return picked
    chosen = {id(d) for _, d in picked}
    for score, d in ranked:
        if id(d) not in chosen and (not _is_soup(d) or soup_count < max_soups):
            picked.append((score, d))
            chosen.add(id(d))
            soup_count += int(_is_soup(d))
            if len(picked) >= n:
                break
    # A soup-only/thin safe catalogue is preferable to returning fewer choices.
    for score, d in ranked:
        if len(picked) >= n:
            break
        if id(d) not in chosen:
            picked.append((score, d))
            chosen.add(id(d))
    return picked[:n]


def _pick_negatives(ranked, positives, n, max_soups=1):
    """Draw informative challengers from the lower-middle of the safe ranked pool.

    The old implementation walked the list backwards, systematically selecting the strangest
    eligible tail items. A 30–70% band still probes uncertainty without making onboarding look
    broken. Diversity constraints are relaxed only when the safe catalogue is too thin to fill.
    """
    used_class = {K.dish_to_class_code(d.name) for _, d in positives}
    used_cuisine = {d.cuisine for _, d in positives}
    positive_ids = {id(d) for _, d in positives}
    start = max(len(positives), int(len(ranked) * CHALLENGER_MIN_QUANTILE))
    stop = max(start + n, int(len(ranked) * CHALLENGER_MAX_QUANTILE))
    challenger_band = ranked[start : min(len(ranked), stop)]
    picked, seen_cuisine, soup_count = [], set(), 0
    for score, d in reversed(challenger_band):
        code = K.dish_to_class_code(d.name)
        if (
            id(d) in positive_ids
            or code in used_class
            or d.cuisine in used_cuisine
            or d.cuisine in seen_cuisine
            or (_is_soup(d) and soup_count >= max_soups)
        ):
            continue
        picked.append((score, d))
        seen_cuisine.add(d.cuisine)
        soup_count += int(_is_soup(d))
        if len(picked) >= n:
            return picked
    chosen = {id(d) for _, d in picked}
    # Backfill from the best remaining safe candidates, not the pathological bottom tail.
    for score, d in ranked:
        if (
            id(d) not in chosen
            and id(d) not in positive_ids
            and (not _is_soup(d) or soup_count < max_soups)
        ):
            picked.append((score, d))
            chosen.add(id(d))
            soup_count += int(_is_soup(d))
            if len(picked) >= n:
                break
    for score, d in ranked:
        if len(picked) >= n:
            break
        if id(d) not in chosen and id(d) not in positive_ids:
            picked.append((score, d))
            chosen.add(id(d))
    return picked[:n]


def calibration_grid(
    household,
    catalogue=None,
    weekday="Monday",
    household_id=None,
    n_positive=DEFAULT_N_POSITIVE,
    n_negative=DEFAULT_N_NEGATIVE,
    exclude_dish_names=None,
    preference_by_dish=None,
):
    """The post-onboarding calibration grid: for each of breakfast/lunch/dinner, n_positive
    expected-positive dishes + n_negative plausible challengers (still safe/diet-eligible),
    order-shuffled per household+slot so cell_role is never positionally guessable.

    `household_id`: when given, seeds a household+slot-stable RNG for the shuffle only — never
    affects WHICH dishes are chosen, only their on-screen order. Omitted (None) => deterministic
    (positives first, then negatives), useful for tests.

    Online preferences and exclusions use the same score/filter contract as the landing-page
    surfaces. A returning user therefore does not receive a frozen onboarding grid after giving
    feedback, while every replacement still passes the original hard eligibility gates."""
    cat = catalogue or Catalogue()
    theta, objective = _theta_obj(household)
    slots = {}
    candidate_lineage = []
    used_across_slots = set()
    soup_count = 0
    for slot in MAIN_SLOTS:
        ctx = make_context(slot=slot, weekday=weekday)
        ctx["exclude_dish_names"] = list(exclude_dish_names or [])
        ctx["preference_by_dish"] = dict(preference_by_dish or {})
        ranked = [
            pair
            for pair in _ranked_eligible(cat, theta, ctx, objective)
            if pair[1].name not in used_across_slots
        ]
        candidate_lineage.extend(
            {
                "name": dish.name,
                "score": round(float(score), 6),
                "slot": slot,
                "meal_class_code": K.dish_to_class_code(dish.name),
            }
            for score, dish in ranked
        )
        available_soups = max(0, MAX_GRID_SOUPS - soup_count)
        positives = _pick_positives(ranked, n_positive, max_soups=available_soups)
        available_soups -= sum(_is_soup(dish) for _, dish in positives)
        negatives = _pick_negatives(
            ranked,
            positives,
            n_negative,
            max_soups=max(0, available_soups),
        )
        cells = [
            _dish_cell(d, theta, ctx, objective, sc, "expected_positive") for sc, d in positives
        ] + [_dish_cell(d, theta, ctx, objective, sc, "planted_negative") for sc, d in negatives]
        if household_id is not None:
            random.Random(f"{household_id}:{slot}:calibration").shuffle(cells)
        slots[slot] = cells
        soup_count += sum(_is_soup(dish) for _, dish in positives + negatives)
        used_across_slots.update(cell["name"] for cell in cells)
    return {
        "household": household.get("label"),
        "kind": "calibration_grid",
        "slots": slots,
        "_candidate_lineage": candidate_lineage,
    }
