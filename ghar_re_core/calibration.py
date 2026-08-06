"""
ghar_re_core.calibration — post-onboarding "dish pick" calibration grid.

Same charter as meal_planner.py (see its module docstring): built ON TOP of the existing
scoring/eligibility stack, WITHOUT touching the Core Spine math. Nothing here decides eligibility
(scoring.eligible stays the sole filter) or invents a score (scoring.score is the sole score) —
this module only picks WHICH already-eligible, already-scored dishes to surface and in what role.

The idea (ported from scareme21-create/NewFoo's ghar_re/calibration.py design, RFC-CALIB-001,
adapted without its distance.py — that module doesn't exist in this engine and building it is out
of scope for this change): per slot, show 5 dishes — a few genuinely good matches (expected
positives) mixed with a couple of deliberately weak-fit ones (planted "mismatch" dishes, still
100% safe/diet-compliant — they still pass scoring.eligible, they're just poor personal fits). If a
user likes a mismatch dish, that is a strong, cheap correction signal for calibrating their taste
profile early — stronger than only ever confirming the engine's own top guesses.

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


def _pick_positives(ranked, n):
    """Top-n by score, capped 1-per-class and 1-per-cuisine (same diversity spirit as
    meal_planner._diversify, reimplemented at this small 3-item scale). Falls back to filling from
    the remainder if the caps are too tight to reach n — never fabricates a dish."""
    picked, seen_class, seen_cuisine = [], set(), set()
    for score, d in ranked:
        code = K.dish_to_class_code(d.name)
        if code in seen_class or d.cuisine in seen_cuisine:
            continue
        picked.append((score, d))
        seen_class.add(code)
        seen_cuisine.add(d.cuisine)
        if len(picked) >= n:
            return picked
    chosen = {id(d) for _, d in picked}
    for score, d in ranked:
        if id(d) not in chosen:
            picked.append((score, d))
            chosen.add(id(d))
            if len(picked) >= n:
                break
    return picked[:n]


def _pick_negatives(ranked, positives, n):
    """From the same eligible (safe/diet-compliant) pool, draw n dishes from the bottom of the
    ranked list — a weak personal fit, never an ineligible one — excluding any cuisine/class a
    positive already used, capped 1-per-cuisine among themselves. This is the meal-distance-proxy
    substitute for NewFoo's distance.py (not present in this engine; out of scope to add here):
    "low score" stands in for "far from what the household actually wants", using only fields
    scoring.py already computes. Backfills without the cuisine constraint if the pool is too thin —
    never relaxes eligibility, never fabricates a dish."""
    used_class = {K.dish_to_class_code(d.name) for _, d in positives}
    used_cuisine = {d.cuisine for _, d in positives}
    picked, seen_cuisine = [], set()
    for score, d in reversed(ranked):
        code = K.dish_to_class_code(d.name)
        if code in used_class or d.cuisine in used_cuisine or d.cuisine in seen_cuisine:
            continue
        picked.append((score, d))
        seen_cuisine.add(d.cuisine)
        if len(picked) >= n:
            return picked
    chosen = {id(d) for _, d in picked}
    excluded = {id(d) for _, d in positives}
    for score, d in reversed(ranked):
        if id(d) not in chosen and id(d) not in excluded:
            picked.append((score, d))
            chosen.add(id(d))
            if len(picked) >= n:
                break
    return picked[:n]


def calibration_grid(household, catalogue=None, weekday="Monday", household_id=None,
                      n_positive=DEFAULT_N_POSITIVE, n_negative=DEFAULT_N_NEGATIVE):
    """The post-onboarding calibration grid: for each of breakfast/lunch/dinner, n_positive
    expected-positive dishes + n_negative planted-mismatch dishes (still safe/diet-eligible),
    order-shuffled per household+slot so cell_role is never positionally guessable.

    `household_id`: when given, seeds a household+slot-stable RNG for the shuffle only — never
    affects WHICH dishes are chosen, only their on-screen order. Omitted (None) => deterministic
    (positives first, then negatives), useful for tests."""
    cat = catalogue or Catalogue()
    theta, objective = _theta_obj(household)
    slots = {}
    used_across_slots = set()
    for slot in MAIN_SLOTS:
        ctx = make_context(slot=slot, weekday=weekday)
        ranked = [
            pair for pair in _ranked_eligible(cat, theta, ctx, objective)
            if pair[1].name not in used_across_slots
        ]
        positives = _pick_positives(ranked, n_positive)
        negatives = _pick_negatives(ranked, positives, n_negative)
        cells = (
            [_dish_cell(d, theta, ctx, objective, sc, "expected_positive") for sc, d in positives]
            + [_dish_cell(d, theta, ctx, objective, sc, "planted_negative") for sc, d in negatives]
        )
        if household_id is not None:
            random.Random(f"{household_id}:{slot}:calibration").shuffle(cells)
        slots[slot] = cells
        used_across_slots.update(cell["name"] for cell in cells)
    return {
        "household": household.get("label"),
        "kind": "calibration_grid",
        "slots": slots,
    }
