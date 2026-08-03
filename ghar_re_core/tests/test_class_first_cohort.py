"""
WP-15 / WP-16 class-first cohort layer tests.

Covers the curated dish->class lookup (knowledge.dish_to_class_code) and the graded, cold-start-
weighted S_cohort term (scoring.s_cohort, config.w_cohort_effective) — WP-16's graded successor to
WP-15's binary membership check. The cohort MODEL itself (migration blend, generalization,
holdout reproduction) is covered separately in test_cohort_intel.py.
"""
import json
import os

from ghar_re_core import fixtures as F
from ghar_re_core import knowledge as K
from ghar_re_core import scoring as S
from ghar_re_core.catalogue import Catalogue
from ghar_re_core.config import CONFIG
from ghar_re_core.derivation import derive_theta
from ghar_re_core.pipeline import make_context

HH = {h["id_key"]: h for h in F.HOUSEHOLDS}
_BUNDLE_CATALOGUE = os.path.join(
    os.path.dirname(__file__), "..", "..", "ghar_re_service", "data", "bundle", "catalogue.json"
)
_SRC = os.path.join(os.path.dirname(__file__), "..", "..", "data", "source", "class_first_v1")
_SLOTS = ("breakfast", "lunch", "dinner", "snacks")


def _lifted_dish_and_ctx(theta, cat):
    """Find a (dish, ctx) where the cohort term actually lifts the dish (s_cohort>0), scanning
    slots — which fixture dishes the cohort plan lifts is household+slot specific, so we don't
    assume a particular slot has a match for the small 39-dish fixture catalogue."""
    for slot in _SLOTS:
        ctx = make_context(slot=slot, weekday="Monday")
        for d in cat:
            if S.s_cohort(d, theta, ctx) > 0:
                return d, ctx
    return None, None


def test_dish_to_class_code_known_match_and_miss():
    # "Masala Dosa" is a curated Class_Dish_Options_v3 entry (BF_FERMENTED_CREPE_PAN family).
    assert K.dish_to_class_code("Masala Dosa") is not None
    assert K.dish_to_class_code("Masala Dosa") == K.dish_to_class_code("masala dosa")  # case-insensitive
    # A deliberately nonsense name must return None, never a fabricated/fuzzy guess.
    assert K.dish_to_class_code("Totally Not A Real Dish Name XYZ") is None


def test_s_cohort_is_graded_zero_to_one_never_fabricated():
    theta = derive_theta(HH["single_professional_blr"])
    ctx = make_context(slot="dinner", weekday="Monday")
    cat = Catalogue()
    # unmatched dish (no curated class) -> exactly 0.0, never a guessed value
    unmatched = next(d for d in cat if K.dish_to_class_code(d.name) is None)
    assert S.s_cohort(unmatched, theta, ctx) == 0.0
    # every dish's grade is within [0,1] (graded affinity, not binary and not unbounded)
    for d in cat:
        v = S.s_cohort(d, theta, ctx)
        assert 0.0 <= v <= 1.0


def test_s_cohort_contributes_additively_with_coldstart_weight():
    # score = BASE*GAIN + w_cohort_effective(n)*S_cohort. The cohort term is additive: the full
    # score minus BASE*GAIN must equal exactly w_cohort_effective(0)*S_cohort for a new household.
    theta = derive_theta(HH["single_professional_blr"])
    cat = Catalogue()
    objective = HH["single_professional_blr"].get("q15_objective")
    dish, ctx = _lifted_dish_and_ctx(theta, cat)  # cold-start weight (no interaction_count in ctx)
    assert dish is not None
    base_gain = S.base(dish, theta, ctx) * S.gain_q15(dish, objective)
    full = S.score(dish, theta, ctx, objective)
    contrib = S.s_cohort(dish, theta, ctx)
    w = CONFIG.w_cohort_effective(0)
    assert round(full - base_gain, 6) == round(w * contrib, 6)


def test_coldstart_weight_decays_with_interaction_count():
    # Strong at n=0, decays toward the floor with volume (the Founder cold-start directive).
    w0 = CONFIG.w_cohort_effective(0)
    w_half = CONFIG.w_cohort_effective(25)
    w_big = CONFIG.w_cohort_effective(100000)
    floor = CONFIG.cohort["cohort"]["w_cohort_floor"]
    assert w0 > w_half > w_big
    assert round(w_big, 4) == round(floor, 4)  # asymptotes to the floor
    # ctx carries interaction_count through to the effective weight in score()
    theta = derive_theta(HH["single_professional_blr"])
    cat = Catalogue()
    obj = HH["single_professional_blr"].get("q15_objective")
    dish, ctx = _lifted_dish_and_ctx(theta, cat)
    assert dish is not None
    cold = S.score(dish, theta, ctx, obj)
    warm = S.score(dish, theta, dict(ctx, interaction_count=100000), obj)
    assert cold > warm  # the same dish is lifted more for a brand-new household


def test_foreign_dishes_demoted_at_coldstart_and_decays():
    """WP-16.1: a foreign (zone=Global) dish carries a cold-start demote that decays with interaction
    volume; a regional Indian dish is never demoted. s_foreign is a pure 0/1 zone flag. Uses the real
    bundle catalogue (the 39-dish fixture has no foreign dishes)."""
    # the effective demote is strong at n=0 and decays toward the floor (config-level, no catalogue)
    assert CONFIG.foreign_demote_effective(0) > CONFIG.foreign_demote_effective(100000)
    if not os.path.isfile(_BUNDLE_CATALOGUE):
        return  # bundle not built here; config-level decay still asserted above
    cat = Catalogue(json.load(open(_BUNDLE_CATALOGUE)))
    foreign = next(d for d in cat if d.zone == "Global")
    indian = next(d for d in cat if d.zone and d.zone != "Global")
    assert S.s_foreign(foreign) == 1.0 and S.s_foreign(indian) == 0.0
    theta = derive_theta(HH["single_professional_blr"])
    ctx = make_context(slot="dinner")
    obj = HH["single_professional_blr"].get("q15_objective")
    # the SAME foreign dish scores lower cold-start than warm; an Indian dish carries no foreign demote
    assert S.score(foreign, theta, ctx, obj) < S.score(foreign, theta, dict(ctx, interaction_count=100000), obj)
    base_gain = S.base(indian, theta, ctx) * S.gain_q15(indian, obj)
    cohort_term = CONFIG.w_cohort_effective(0) * S.s_cohort(indian, theta, ctx)
    assert round(S.score(indian, theta, ctx, obj), 6) == round(base_gain + cohort_term, 6)  # no demote term


def test_real_catalogue_coverage_is_full_and_honest():
    """WP-17: EVERY catalogue dish now resolves to a meal class (dish_class_map.csv, the nutritionist/
    chef classifier) — coverage is no longer the ceiling on the class-first plan. Coverage went
    129 (exact) -> 202 (WP16-F1 precision-safe) -> 810/810 (WP-17 full). Honesty is preserved not by
    a low recall but by the per-row method + confidence tag: curated_exact reproduces authored truth,
    chef_rubric is a transparent, diet-gated, attribute-derived classification. This asserts the map
    is (a) full and (b) diet-safe: no veg catalogue dish is ever assigned an egg/nonveg-marked class
    via the DERIVED path (a curated_exact authored row may, and is honoured as authored truth)."""
    if not os.path.isfile(_BUNDLE_CATALOGUE):
        return  # bundle not built in this environment; core-only tests still cover the mechanism
    dishes = json.load(open(_BUNDLE_CATALOGUE))
    cat = Catalogue(dishes)
    matched = sum(1 for d in cat if K.dish_to_class_code(d.name))
    assert matched >= 780  # ~full coverage; a small tail may lack a class if the catalogue grows

    # diet safety of the DERIVED rows: a veg dish's chef_rubric class must not be egg/nonveg-marked.
    import csv as _csv
    src = os.path.join(_SRC, "dish_class_map.csv")
    if os.path.isfile(src):
        by_diet = {d.name: d.diet for d in cat}
        NV = ("CHICKEN", "FISH", "MUTTON", "PRAWN", "CRAB", "KEEMA", "PORK", "SEAFOOD",
              "NONVEG", "TANDOORI", "SMOKED", "MEAT_STEW", "XACUTI")
        with open(src, newline="") as f:
            for r in _csv.DictReader(f):
                # WP-17.1: both derived paths (primary chef_rubric + chef_rubric_secondary
                # multi-membership) go through the same diet gate, so both must be diet-safe.
                if r["method"] not in ("chef_rubric", "chef_rubric_secondary"):
                    continue
                if by_diet.get(r["dish_name"]) == "veg":
                    code = r["meal_class_code"]
                    assert "EGG" not in code and not any(m in code for m in NV), \
                        f"veg dish {r['dish_name']} chef-mapped to non-veg class {code}"
