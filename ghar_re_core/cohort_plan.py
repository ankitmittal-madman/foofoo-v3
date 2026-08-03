"""
ghar_re.cohort_plan — WP-17 COMPOSITIONAL cohort class-plan derivation.

WHY THIS EXISTS
WP-16 shipped a learned factorized frequency model (cohort_intel.class_affinity) that reproduces the
persona-DB weekly plan by generalizing over feature counts. It works, but it PLATEAUS at ~37% class
overlap with a specific precomputed cohort (e.g. S14_T1_P10): a frequency model favours classes
common across ALL cohorts (Dal-Roti is everywhere) over the state-distinctive ones that make a
persona's plan its own (Pitla-Bhakri for a Maharashtra family, Khichdi for a toddler). Reproducing a
PERSONA-SPECIFIC plan needs COMPOSITION, not frequency.

WHAT IT DOES (exactly the Founder's WP-17 recipe)
  resolve persona (household_type + lifecycle_stage + health + diet)            -> Persona_Master_v3
    -> persona.{slot}_boost_classes as the PLAN CORE (the child-friendly/mild/regional classes)
    ∩  State_Profile_v3 slot pools (regional grounding — Pitla-Bhakri, Coconut-Stew for Maharashtra)
    +  City_Migration_Overlay_v3 classes for MIGRANTS only
    filtered by SPINE SCIENCE (diet gate, lifecycle boosts/demotes, heaviness ceiling)
    -> a graded {meal_class_code: [0,1]} cohort class plan for this slot + day-type.

This is DERIVATION from the authored masters (Persona_Master / State_Profile / City_Migration_Overlay
/ Meal_Class_Master), not a copy of any precomputed Cohort_Matrix row — the household is resolved
LIVE from theta and the plan is composed from the masters, so a household whose exact cohort was
never enumerated still gets a coherent, persona-shaped, regionally-grounded plan.

cohort_intel.class_affinity() blends THIS (primary) with the learned model (secondary smoothing), so
the plate feels like the persona-DB plan while still generalizing. No .xlsx is read at runtime; all
inputs are the checked-in/baked class_first_v1 CSVs, resolved through the same config-dir seam.
"""
import csv as _csv
import os as _os

_PERSONAS = None
_STATE_PROFILE = None
_CLASS_META = None
_MIGRATION = None

# household_type (theta) -> the excel's 5 onboarding main cohorts (Main_Cohort_Hierarchy). Mirror of
# cohort_intel._HOUSEHOLD_TO_MC, kept here so cohort_plan has no import-time dependency on that module
# (cohort_intel imports THIS module; a late import both ways would work but this map is 6 stable rows).
_HOUSEHOLD_TO_MC = {
    "single": "MC1", "flatmates": "MC1",
    "couple": "MC2",
    "couple_kids": "MC3",
    "couple_kids_parents": "MC4", "joint": "MC4",
}

# ctx slot -> (persona boost column, [state pool columns], secondary persona boost column or None).
# Dinner draws on the persona's DN boost AND its LD boost (a family eats lunch-type LD dishes at
# dinner too), plus the state's dinner pool (which itself carries both DN and LD classes).
_SLOT_COLS = {
    "breakfast": ("bf_boost_classes", ["breakfast_class_pool"], None),
    "lunch": ("ld_boost_classes", ["weekday_lunch_class_pool"], None),
    "dinner": ("dn_boost_classes", ["weekday_dinner_class_pool"], "ld_boost_classes"),
    "snack": ("sn_boost_classes", ["snack_class_pool"], None),
}
_WEEKEND_POOL = "weekend_special_class_pool"

_NONVEG_MARKERS = ("CHICKEN", "FISH", "MUTTON", "PRAWN", "CRAB", "KEEMA", "PORK", "RED_MEAT",
                   "SEAFOOD", "NONVEG", "TANDOORI", "MUSLIM_BIRYANI", "SMOKED_PORK", "MEAT_STEW",
                   "XACUTI")


def _src_path(name):
    """Resolve a class_first_v1 artifact via the shared config-dir seam (works from repo + bundle)."""
    from ghar_re_core.config import SRC
    return _os.path.join(SRC, "class_first_v1", name)


def _personas():
    """Persona_Master_v3 rows, cached."""
    global _PERSONAS
    if _PERSONAS is None:
        with open(_src_path("persona_master.csv"), newline="") as f:
            _PERSONAS = list(_csv.DictReader(f))
    return _PERSONAS


def _state_profile():
    """state_ut -> State_Profile_v3 row (class pools + region), cached."""
    global _STATE_PROFILE
    if _STATE_PROFILE is None:
        _STATE_PROFILE = {}
        with open(_src_path("state_profile.csv"), newline="") as f:
            for r in _csv.DictReader(f):
                _STATE_PROFILE[r["state_ut"]] = r
    return _STATE_PROFILE


def _class_meta():
    """meal_class_code -> {slot_group, diet_type, heaviness, category, is_addon, meat}, cached."""
    global _CLASS_META
    if _CLASS_META is None:
        _CLASS_META = {}
        with open(_src_path("meal_class_master.csv"), newline="") as f:
            for r in _csv.DictReader(f):
                code = r["meal_class_code"]
                _CLASS_META[code] = {
                    "slot_group": r["slot_group"],
                    "diet_type": r["diet_type"],
                    "heaviness": r["heaviness"],
                    "category": r["class_category"],
                    "is_addon": "ADDON_ONLY" in (r.get("planning_role_v3") or ""),
                    "meat": any(m in code for m in _NONVEG_MARKERS),
                }
    return _CLASS_META


def _migration():
    """(origin_state, destination_group) -> overlay row, cached."""
    global _MIGRATION
    if _MIGRATION is None:
        _MIGRATION = {}
        with open(_src_path("migration_overlay.csv"), newline="") as f:
            for r in _csv.DictReader(f):
                _MIGRATION[(r["origin_state_ut"], r["destination_group_code"])] = r
    return _MIGRATION


def _persona_stage(health):
    """Persona lifecycle_health free-text -> the coarse lifecycle_stage vocabulary theta uses
    (mirror of prepare_cohort_intel.lifecycle_stage, so persona and theta speak the same language)."""
    h = (health or "").lower()
    if "infant" in h or "baby" in h or "0-6m" in h or "6-18m" in h:
        return "infant"
    if "toddler" in h:
        return "toddler"
    if "pregnan" in h or "preconception" in h or "lactat" in h:
        return "pregnancy"
    if "elder" in h or "recovery" in h or "senior" in h:
        return "elder"
    if "teen" in h:
        return "teen"
    if "school" in h or "picky child" in h or "child" in h:
        return "school_child"
    return "none"


def _nv_family(mode):
    """Coarse nonveg-mode family (veg / egg / nonveg / jain) for persona matching."""
    mode = (mode or "").lower()
    if "jain" in mode:
        return "jain"
    if "veg" in mode and "non" not in mode:
        return "veg"
    if "egg" in mode:
        return "egg"
    return "nonveg"


def _theta_nv_family(theta):
    """theta -> nonveg family, using diet + Jain flag."""
    if theta["is_jain"]["value"]:
        return "jain"
    diet = theta["diet"]["value"]
    if diet == "veg":
        return "veg"
    if diet in ("eggetarian", "egg"):
        return "egg"
    return "nonveg"


def resolve_persona(theta, k=2):
    """Resolve the household's best-matching Persona_Master anchors LIVE from theta. Scores every
    persona on the sub-cohort-defining signals — main cohort, lifecycle stage (the strongest: it is
    what separates a toddler family from the family average), diet family, and time-pressure band —
    and returns the top-k [(persona_row, score_fraction)] best-first. Compositional core, not a
    stored persona id: the match is recomputed each call."""
    want_mc = _HOUSEHOLD_TO_MC.get(theta["household_type"]["value"], "MC1")
    want_stage = theta.get("lifecycle_stage", {}).get("value", "none")
    want_nv = _theta_nv_family(theta)
    tp = theta.get("time_pressure", {}).get("value")
    want_tp = "high" if (tp or 0) >= 0.6 else "medium" if (tp or 0) >= 0.35 else "low"
    scored = []
    for p in _personas():
        s = 0.0
        s += 2.0 if p.get("main_cohort_id") == want_mc else 0.0
        # lifecycle is the decisive sub-cohort signal — weight it highest
        if want_stage != "none" and _persona_stage(p.get("lifecycle_health")) == want_stage:
            s += 4.0
        s += 2.0 if _nv_family(p.get("nonveg_mode")) == want_nv else 0.0
        s += 1.0 if (p.get("time_pressure") or "").lower().replace("very ", "") == want_tp else 0.0
        scored.append((s, p))
    scored.sort(key=lambda x: -x[0])
    total = max(scored[0][0], 1.0) if scored else 1.0
    return [(p, round(s / total, 3)) for s, p in scored[:k] if s > 0]


def _split(cell):
    """'A|B|C' -> ['A','B','C'] (empty-safe)."""
    return [c for c in (cell or "").split("|") if c]


def _add(plan, code, w):
    """Accumulate the max weight seen for a class (a class named by several sources takes the
    strongest, plus a small reinforcement handled by the caller)."""
    plan[code] = max(plan.get(code, 0.0), w)


def _diet_ok(theta, meta):
    """Class-level diet gate (dish-level pass_diet/pass_jain still enforce per dish). veg households
    never plan an egg/nonveg class; egg households never plan a meat class; Jain is left to the dish
    filter (a Jain household still plans veg classes, its dishes just get Jain-filtered)."""
    fam = _theta_nv_family(theta)
    if fam == "veg":
        return not meta["meat"] and meta["diet_type"] != "egg"
    if fam == "egg":
        return not meta["meat"]
    if fam == "jain":
        return not meta["meat"] and meta["diet_type"] != "egg"
    return True  # nonveg: everything allowed


def _lifecycle_multiplier(theta, code, meta):
    """SPINE SCIENCE: the 'enhanced computation'. Reshape the plan by the household's lifecycle and
    heaviness ceiling — boost mild/child/soft/light classes and demote heavy/rich/indulgent ones for
    toddler/infant/elder households, so a family-with-toddler's plan leads with mild, child-safe,
    lighter classes (the S14_T1_P10 shape) rather than the generic regional average."""
    stage = theta.get("lifecycle_stage", {}).get("value", "none")
    heavy_ceiling = theta.get("heaviness_ceiling", {}).get("value", 3)
    cat = meta["category"]
    heavy = meta["heaviness"] == "heavy"
    mild = any(k in code for k in ("CHILD", "KID", "MILD", "LIGHT", "KHICHDI", "SOFT", "ELDERLY",
                                   "CURD_RICE", "DAL_RICE"))
    indulgent = cat in ("indulgent_weekend", "heavy_home", "regional_heavy") or heavy or \
        any(k in code for k in ("RICH", "FRIED", "BIRYANI", "MUSLIM", "TANDOORI", "OUTSIDE",
                                "WEEKEND_INDULGENCE", "PASTA_PIZZA"))
    m = 1.0
    if stage in ("infant", "toddler", "school_child"):
        if mild:
            m *= 1.35
        if indulgent:
            m *= 0.55
    elif stage == "elder":
        if mild:
            m *= 1.3
        if indulgent:
            m *= 0.5
    elif stage == "pregnancy":
        if mild or cat in ("health_protein", "health_light"):
            m *= 1.2
        if indulgent:
            m *= 0.7
    # heaviness ceiling (e.g. senior present -> 2): demote heavy classes regardless of stage
    if heavy and isinstance(heavy_ceiling, (int, float)) and heavy_ceiling <= 2:
        m *= 0.6
    return m


def class_plan(theta, ctx):
    """The compositional cohort class plan for ctx's slot + day-type: {meal_class_code: [0,1]}.

    Persona boost classes are the plan CORE (rank-weighted); State_Profile regional pools ground it
    (and a class in BOTH is reinforced); the City_Migration overlay is added for migrants; then the
    spine-science diet gate + lifecycle/heaviness reshaping is applied; finally the top class is
    normalized to 1.0. Empty dict if the slot is unknown."""
    slot = ctx.get("slot")
    cols = _SLOT_COLS.get(slot)
    if cols is None:
        return {}
    boost_col, pool_cols, secondary_col = cols
    daytype = "weekend" if ctx.get("weekday") in ("Saturday", "Sunday") else "weekday"

    personas = resolve_persona(theta)
    state = theta["home_state"]["value"]
    sp = _state_profile().get(state, {})
    meta = _class_meta()

    plan: dict = {}
    core = set()  # persona-boost classes (the plan core) — for the ∩ reinforcement below

    # 1. PERSONA BOOST = plan core, rank-weighted, blended across the top personas by match fraction.
    for p, frac in personas:
        for rank, code in enumerate(_split(p.get(boost_col))):
            core.add(code)
            _add(plan, code, frac * (1.0 - 0.12 * rank))
        if secondary_col:  # dinner also draws on the persona's LD boosts, at a lower weight
            for rank, code in enumerate(_split(p.get(secondary_col))):
                _add(plan, code, 0.7 * frac * (1.0 - 0.12 * rank))

    # 2. STATE POOLS = regional grounding. A class already in the persona core is REINFORCED (this is
    #    the ∩ — persona plan grounded in the household's regional reality); a state-only class enters
    #    at a moderate regional-default weight.
    pool = list(pool_cols)
    if daytype == "weekend":
        pool.append(_WEEKEND_POOL)
    for col in pool:
        base_w = 0.55 if col != _WEEKEND_POOL else 0.4
        for code in _split(sp.get(col)):
            if code in core:
                plan[code] = min(1.0, plan.get(code, 0.0) + 0.25)  # ∩ reinforcement
            else:
                _add(plan, code, base_w)
    # nonveg households also plan the state's nonveg pool (fish/chicken for a coastal MH family)
    if _theta_nv_family(theta) in ("nonveg", "egg"):
        for code in _split(sp.get("nonveg_class_pool")):
            _add(plan, code, 0.5)

    # 3. CITY MIGRATION OVERLAY — migrants only (the "MP-in-Mumbai" science); a home-state resident's
    #    plan stays regionally pure.
    _apply_migration(theta, plan)

    # 4. SPINE SCIENCE — diet gate + lifecycle/heaviness reshaping.
    out = {}
    for code, w in plan.items():
        m = meta.get(code)
        # unknown codes (a pool naming a class absent from the master) are dropped, never guessed.
        if m is None:
            continue
        if not _diet_ok(theta, m):
            continue
        w *= _lifecycle_multiplier(theta, code, m)
        if w > 0:
            out[code] = w

    top = max(out.values()) if out else 0.0
    if top <= 0:
        return {}
    return {c: round(w / top, 4) for c, w in out.items()}


def _apply_migration(theta, plan):
    """Add City_Migration_Overlay national-modern classes for a genuine migrant (local state != home
    state). Reuses cohort_intel's destination-group resolution so the two layers agree on who is a
    migrant and which overlay row applies."""
    from ghar_re_core import cohort_intel as CI
    home = theta["home_state"]["value"]
    local = CI._local_state(theta)
    if local == home:
        return
    row = _migration().get((home, CI.destination_group(theta)))
    if not row:
        return
    w_nat = float(row.get("national_modern_weight") or 0.0)
    for code in _split(row.get("overlay_meal_classes")):
        _add(plan, code, min(1.0, 0.45 + w_nat))
