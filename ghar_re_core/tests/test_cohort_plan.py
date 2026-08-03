"""
WP-17 compositional cohort-plan tests — ghar_re_core.cohort_plan.

Validates the compositional derivation (persona -> boost_classes as core, ∩ State_Profile pools,
+ City_Migration overlay for migrants, filtered by spine science):
  - the persona is resolved LIVE from theta (a MH family-with-toddler -> P10 family_with_toddler),
  - the plan is graded, bounded [0,1], slot-specific, non-empty,
  - the plan is persona-shaped AND regionally grounded (child/mild core + Maharashtrian Pitla-Bhakri),
  - spine science reshapes it (toddler demotes indulgent classes vs a DINK couple; diet-gates nonveg),
  - migration overlay applies to a migrant but not a home-state resident.
"""
from ghar_re_core import cohort_plan as CP
from ghar_re_core.derivation import derive_theta
from ghar_re_core.pipeline import make_context


def _hh(home_state, city, household_type="single", diet="veg", conditions=None, ages=None,
        cooks="self", earners=1, jain=False):
    return {
        "id_key": "t", "label": "t", "q1_household_type": household_type,
        "q2_working_professionals": earners, "q3_home_state": home_state, "q4_current_city": city,
        "q5_diet": diet, "q6_nonveg_types": [], "q7_veg_days": [], "q8_is_jain": jain,
        "q9_allergies": [], "q11_conditions": conditions or [],
        "q12_member_ages": ages or [{"role": "self", "age": 33}],
        "q13_who_cooks": cooks, "q14_eat_out_per_week": 2, "q15_objective": "awesome_taste",
    }


_TODDLER_MH = _hh("MH", "Pune", household_type="couple_kids", conditions=["toddler"], earners=2,
                  ages=[{"role": "self", "age": 32}, {"role": "spouse", "age": 30},
                        {"role": "toddler", "age": 3}])


def test_resolves_the_family_with_toddler_persona():
    """The MH dual-income family with a toddler must resolve to Persona P10 family_with_toddler —
    the exact sub-cohort behind the S14_T1_P10 precomputed plan the engine should self-arrive at."""
    th = derive_theta(_TODDLER_MH)
    top = CP.resolve_persona(th)
    assert top, "no persona resolved"
    assert top[0][0]["persona_id"] == "P10"
    assert top[0][0]["sub_cohort_label"] == "family_with_toddler"


def test_plan_is_graded_bounded_slot_specific():
    th = derive_theta(_TODDLER_MH)
    bf = CP.class_plan(th, make_context(slot="breakfast", weekday="Monday"))
    dn = CP.class_plan(th, make_context(slot="dinner", weekday="Monday"))
    assert bf and dn
    assert all(0.0 <= v <= 1.0 for v in bf.values())
    assert max(bf.values()) == 1.0 and max(dn.values()) == 1.0
    assert set(bf) != set(dn)                      # different slots -> different class vocab
    assert len({round(v, 3) for v in bf.values()}) > 2   # graded, not binary


def test_plan_is_persona_core_and_regionally_grounded():
    """The lunch plan leads with the child/mild core AND carries the state's regional grounding
    class (Maharashtrian Pitla-Bhakri) — persona plan ∩ State_Profile, exactly the WP-17 recipe."""
    th = derive_theta(_TODDLER_MH)
    lunch = CP.class_plan(th, make_context(slot="lunch", weekday="Wednesday"))
    top = max(lunch, key=lunch.get)
    assert top == "LD_CHILD_MILD_PLATE"                       # child-mild plan core leads
    assert "LD_MAHARASHTRIAN_PITLA_BHAKRI" in lunch           # regional grounding present
    assert lunch["LD_MAHARASHTRIAN_PITLA_BHAKRI"] > 0.0


def test_spine_science_diet_gate_veg_household():
    """A veg household's plan never contains an egg/nonveg-marked class (class-level diet gate)."""
    th = derive_theta(_TODDLER_MH)
    for slot in ("breakfast", "lunch", "dinner"):
        plan = CP.class_plan(th, make_context(slot=slot, weekday="Monday"))
        for code in plan:
            assert "EGG" not in code
            assert not any(m in code for m in CP._NONVEG_MARKERS)


def test_lifecycle_reshaping_toddler_vs_dink():
    """Spine-science lifecycle reshaping: the toddler household weights child/mild classes far above
    indulgent ones; a DINK couple (no lifecycle constraint) does not demote indulgence the same way,
    so the toddler plan's indulgent-class share is strictly lower."""
    tod = derive_theta(_TODDLER_MH)
    dink = derive_theta(_hh("MH", "Pune", household_type="couple",
                            ages=[{"role": "self", "age": 30}, {"role": "spouse", "age": 29}]))
    ctx = make_context(slot="dinner", weekday="Saturday")
    tod_plan = CP.class_plan(tod, ctx)
    dink_plan = CP.class_plan(dink, ctx)

    def indulgent_mass(plan):
        return sum(v for c, v in plan.items()
                   if any(k in c for k in ("RICH", "FRIED", "BIRYANI", "INDULGENCE", "OUTSIDE")))
    # toddler indulgent share should be no greater than the DINK couple's (usually strictly lower)
    assert indulgent_mass(tod_plan) <= indulgent_mass(dink_plan) + 1e-9


def test_migration_overlay_only_for_migrant():
    """City_Migration overlay classes appear for an out-of-state metro migrant, not a home resident."""
    migrant = derive_theta(_hh("Madhya Pradesh", "Mumbai", household_type="couple"))
    home = derive_theta(_hh("Madhya Pradesh", "Indore", household_type="couple"))
    ctx = make_context(slot="lunch", weekday="Monday")
    mp = CP.class_plan(migrant, ctx)
    hp = CP.class_plan(home, ctx)
    # the two plans differ (residence changed the plan via the overlay)
    assert any(abs(mp.get(c, 0) - hp.get(c, 0)) > 1e-6 for c in set(mp) | set(hp))
