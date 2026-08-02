"""
WP-16 Cohort Intelligence tests — the learned, migration-blended class-affinity model.

Validates that the factorized model (cohort_intel + cohort_class_model.json):
  - produces graded, slot/day-type-specific, bounded affinities,
  - reproduces the authored persona-DB plan for a real cohort (learned-from-excel fidelity),
  - generalizes to a feature combination while staying sane,
  - applies the City_Migration_Overlay blend (the "MP-in-Mumbai" science),
  - exposes soft sub-cohort membership for explainability.
"""
import csv
import os

from ghar_re_core import cohort_intel as CI
from ghar_re_core.derivation import derive_theta
from ghar_re_core.pipeline import make_context

_SRC = os.path.join(os.path.dirname(__file__), "..", "..", "data", "source", "class_first_v1")


def _hh(home_state, city, household_type="single", diet="veg", cooks="self",
        objective="awesome_taste", jain=False):
    """Minimal valid raw household (fixtures.HOUSEHOLDS shape) for building a theta."""
    return {
        "id_key": "t", "label": "t", "q1_household_type": household_type,
        "q2_working_professionals": 1, "q3_home_state": home_state, "q4_current_city": city,
        "q5_diet": diet, "q6_nonveg_types": [], "q7_veg_days": [], "q8_is_jain": jain,
        "q9_allergies": [], "q11_conditions": [], "q12_member_ages": [{"role": "self", "age": 33}],
        "q13_who_cooks": cooks, "q14_eat_out_per_week": 2, "q15_objective": objective,
    }


# The exact feature set the model was trained on (prepare_cohort_intel.FEATURES). Mirrored here as
# a contract check: theta_features() must produce exactly these, all non-empty, or the model can't
# be scored live. Kept in sync with the model artifact's own meta.features below.
_EXPECTED_FEATURES = {"state_ut", "region_archetype", "city_tier_code",
                      "main_cohort_id", "time_pressure", "nonveg_mode"}


def test_theta_features_complete_and_recomputable():
    theta = derive_theta(_hh("Maharashtra", "Mumbai"))
    feats = CI.theta_features(theta)
    assert set(feats) == _EXPECTED_FEATURES
    assert all(feats[f] for f in _EXPECTED_FEATURES)
    # the model artifact must declare the same feature list it was trained on
    assert set(CI._model()["meta"]["features"]) == _EXPECTED_FEATURES


def test_class_affinity_graded_slot_specific_and_bounded():
    theta = derive_theta(_hh("Tamil Nadu", "Chennai"))
    bf = CI.class_affinity(theta, make_context(slot="breakfast", weekday="Monday"))
    dn = CI.class_affinity(theta, make_context(slot="dinner", weekday="Monday"))
    assert bf and dn
    assert set(bf) != set(dn)                      # different slots -> different class vocab/plan
    assert all(0.0 <= v <= 1.0 for v in bf.values())
    assert max(bf.values()) == 1.0                 # top class normalized to 1.0
    # graded, not binary: more than two distinct non-zero grades exist
    assert len({round(v, 3) for v in bf.values() if v > 0}) > 2


def test_model_reproduces_a_real_cohort_primary_class():
    """Learned-from-excel fidelity: for a household whose features match a real Cohort_Matrix row,
    the model's top-affinity breakfast class must be one the persona DB actually plans for cohorts
    of that state (the class appears in that state's cohort weekday breakfast mix). This proves the
    model learned the authored plan, not noise."""
    # Andhra Pradesh cohorts: gather every class the DB uses in weekday breakfast for that state.
    ap_bf_classes = set()
    with open(os.path.join(_SRC, "cohort_matrix.csv"), newline="") as f:
        for r in csv.DictReader(f):
            if r["state_ut"] == "Andhra Pradesh":
                ap_bf_classes.update(c for c in (r["weekday_breakfast_class_mix"] or "").split("|") if c)
    assert ap_bf_classes
    theta = derive_theta(_hh("Andhra Pradesh", "Visakhapatnam"))
    aff = CI.class_affinity(theta, make_context(slot="breakfast", weekday="Monday"))
    top_class = max(aff, key=aff.get)
    assert top_class in ap_bf_classes


def test_generalizes_to_feature_combo_without_crashing():
    # A veg Jain couple in a tier-2 home city — still yields a sane, bounded, non-empty plan.
    theta = derive_theta(_hh("Rajasthan", "Kota", household_type="couple", diet="veg", jain=True))
    aff = CI.class_affinity(theta, make_context(slot="lunch", weekday="Sunday"))
    assert aff and max(aff.values()) == 1.0
    assert all(0.0 <= v <= 1.0 for v in aff.values())


def test_migration_overlay_shifts_the_plan():
    """The MP-in-Mumbai science: an MP household living in Mumbai should get a class plan that
    differs from the same MP household living in an MP home city — because the migration overlay
    blends in current-city lifestyle classes. Uses lunch weekday where overlay classes are richest."""
    home = derive_theta(_hh("Madhya Pradesh", "Indore"))       # home-state resident (non-migrant)
    migrant = derive_theta(_hh("Madhya Pradesh", "Mumbai"))    # MP-in-Mumbai
    assert CI.destination_group(migrant) == "MUMBAI_PUNE"
    assert CI.destination_group(home).startswith("HOME_STATE")
    ctx = make_context(slot="lunch", weekday="Monday")
    aff_home = CI.class_affinity(home, ctx)
    aff_migrant = CI.class_affinity(migrant, ctx)
    # the two plans are not identical — residence changed the blended affinity
    assert any(abs(aff_home.get(c, 0) - aff_migrant.get(c, 0)) > 1e-6
               for c in set(aff_home) | set(aff_migrant))


def test_home_state_2letter_code_is_normalized_end_to_end():
    """Regression for the confirmed production bug: the live app writes profiles.home_state as a
    2-letter code ('MP'), but the engine keys on full names. Without normalization the region and
    cohort layers silently no-op (test_10: MP/Mumbai got weird cross-regional plates). derive_theta
    must normalize the code so region resolves and the cohort affinity is non-degenerate — and it
    must be identical to passing the full name."""
    from ghar_re_core import knowledge as K

    assert K.normalize_state("MP") == "Madhya Pradesh"
    assert K.normalize_state("mp") == "Madhya Pradesh"  # case-insensitive
    assert K.normalize_state("Madhya Pradesh") == "Madhya Pradesh"  # identity for full names
    assert K.normalize_state("Nowhere") == "Nowhere"  # unknown token passes through

    code = derive_theta(_hh("MP", "Mumbai", household_type="couple_kids"))
    name = derive_theta(_hh("Madhya Pradesh", "Mumbai", household_type="couple_kids"))
    assert code["home_state"]["value"] == "Madhya Pradesh"
    assert code["region"]["value"] == "Central" and code["region"]["value"] == name["region"]["value"]
    ctx = make_context(slot="dinner", weekday="Saturday")
    assert CI.class_affinity(code, ctx) == CI.class_affinity(name, ctx)  # code == full name, identical


def test_cohort_membership_returns_ranked_anchors():
    theta = derive_theta(_hh("Kerala", "Kochi"))
    mem = CI.cohort_membership(theta, k=3)
    assert 1 <= len(mem) <= 3
    assert all(0.0 <= m["match"] <= 1.0 for m in mem)
    assert mem == sorted(mem, key=lambda m: -m["match"])   # ranked best-first
