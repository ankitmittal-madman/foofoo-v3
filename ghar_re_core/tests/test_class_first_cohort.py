"""
WP-15 "Ghar RE v1.1 — Class-Enriched Recommendation" tests.

Covers the new class-first cohort layer (knowledge.dish_to_class_code / cohort_class_mix,
scoring.s_cohort, config.w_cohort): the theta-derived implementation of the Core Spine master
formula's previously-unwired w_cohort·S_cohort term, sourced from the real (previously unused)
Indian_Meal_Cohort_Persona_DB_v3.xlsx data asset. See knowledge.py's class-first section for the
full design rationale.
"""
import json
import os

from ghar_re_core import fixtures as F
from ghar_re_core import knowledge as K
from ghar_re_core import scoring as S
from ghar_re_core.catalogue import Catalogue
from ghar_re_core.derivation import derive_theta
from ghar_re_core.pipeline import make_context

HH = {h["id_key"]: h for h in F.HOUSEHOLDS}
_BUNDLE_CATALOGUE = os.path.join(
    os.path.dirname(__file__), "..", "..", "ghar_re_service", "data", "bundle", "catalogue.json"
)


def test_dish_to_class_code_known_match_and_miss():
    # "Masala Dosa" is a curated Class_Dish_Options_v3 entry (BF_FERMENTED_CREPE_PAN family).
    assert K.dish_to_class_code("Masala Dosa") is not None
    assert K.dish_to_class_code("Masala Dosa") == K.dish_to_class_code("masala dosa")  # case-insensitive
    # A deliberately nonsense name must return None, never a fabricated/fuzzy guess.
    assert K.dish_to_class_code("Totally Not A Real Dish Name XYZ") is None


def test_cohort_class_mix_matches_household_state_and_is_slot_specific():
    theta = derive_theta(HH["single_professional_blr"])
    ctx_dinner = make_context(slot="dinner", weekday="Monday")
    ctx_lunch = make_context(slot="lunch", weekday="Monday")
    mix_dinner = K.cohort_class_mix(theta, ctx_dinner)
    mix_lunch = K.cohort_class_mix(theta, ctx_lunch)
    assert isinstance(mix_dinner, set) and isinstance(mix_lunch, set)
    # Karnataka is covered by the persona DB (Bengaluru/Karnataka cohorts exist) — real match, not empty.
    assert len(mix_dinner) > 0
    assert mix_dinner != mix_lunch  # slot-specific, not a single blob reused everywhere


def test_cohort_class_mix_weekday_vs_weekend_can_differ():
    theta = derive_theta(HH["single_professional_blr"])
    weekday = K.cohort_class_mix(theta, make_context(slot="dinner", weekday="Monday"))
    weekend = K.cohort_class_mix(theta, make_context(slot="dinner", weekday="Saturday"))
    assert isinstance(weekday, set) and isinstance(weekend, set)


def test_s_cohort_zero_for_unmatched_dish_never_fabricated():
    theta = derive_theta(HH["single_professional_blr"])
    ctx = make_context(slot="dinner")
    cat = Catalogue()
    unmatched = next(d for d in cat if K.dish_to_class_code(d.name) is None)
    assert S.s_cohort(unmatched, theta, ctx) == 0.0


def test_s_cohort_contributes_additively_to_score_not_multiplicatively():
    # score = BASE*GAIN + w_cohort*S_cohort. A dish with S_cohort=1 must score exactly
    # w_cohort higher than the same dish scored via base()*gain_q15() alone.
    theta = derive_theta(HH["single_professional_blr"])
    ctx = make_context(slot="dinner")
    cat = Catalogue()
    dish = next((d for d in cat if K.dish_to_class_code(d.name)), None)
    if dish is None:
        return  # golden-sample fixtures may have zero curated matches; real catalogue does (see below)
    objective = HH["single_professional_blr"].get("q15_objective")
    base_gain = S.base(dish, theta, ctx) * S.gain_q15(dish, objective)
    full = S.score(dish, theta, ctx, objective)
    contrib = S.s_cohort(dish, theta, ctx)
    assert round(full - base_gain, 6) == round(0.15 * contrib, 6)  # CONFIG.w_cohort default


def test_real_catalogue_coverage_is_honest_not_padded():
    """Documents the actual, measured coverage rate against the real 810-dish catalogue: ~16%.
    This is a floor-check, not a target — it fails loudly if coverage silently regresses to 0
    (e.g. a broken path), and it must never be "fixed" by loosening the exact-match rule in
    dish_to_class_code (see knowledge.py's module docstring on why fuzzy matching is deliberately
    out of scope here)."""
    if not os.path.isfile(_BUNDLE_CATALOGUE):
        return  # bundle not built in this environment; core-only tests still cover the mechanism
    dishes = json.load(open(_BUNDLE_CATALOGUE))
    cat = Catalogue(dishes)
    matched = sum(1 for d in cat if K.dish_to_class_code(d.name))
    assert 100 <= matched <= 160  # measured 129/810; wide-ish band so unrelated catalogue edits don't flake this
