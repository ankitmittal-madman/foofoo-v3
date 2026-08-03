"""
ghar_re.cohort_intel — WP-16 Cohort Intelligence layer.

The "make cold-start feel like the persona-DB plan, derived not copied" engine. Consumes the two
offline-built artifacts from ghar_re_service/scripts/prepare_cohort_intel.py:

  class_first_v1/cohort_class_model.json  - factorized log-linear class-affinity model, LEARNED
                                            from the excel's 20,664 Weekly_Class_Plan_v3 rows.
  class_first_v1/migration_overlay.csv    - City_Migration_Overlay_v3 (the "MP-in-Mumbai" science):
                                            origin x destination -> home/local/national blend.
  class_first_v1/state_profile.csv        - state -> region_archetype (a model feature).

Public surface used by scoring.s_cohort():
  class_affinity(theta, ctx)  -> {meal_class_code: grade in [0,1]} for ctx's slot + day-type,
                                 already migration-blended. Top class = 1.0.
  cohort_membership(theta)    -> ranked persona anchors (explainability / decision-trace only).

This does NOT filter or gate candidates and never reads the source .xlsx at runtime — it turns the
authored class science into ONE graded, additive score term (scoring.s_cohort), matched live from
theta, exactly as WP-15 established for the binary version this replaces. Where WP-15 asked only
"is this dish's class in the cohort's plan? (1/0)", this asks "how strongly does a household of this
shape, living where it lives, plan this dish's class right now? ([0,1])" — and generalizes to
household feature-combinations the excel never enumerated (the model is factorized, not a row lookup).
"""
import csv as _csv
import json as _json
import math as _math
import os as _os

# ---------------------------------------------------------------------------
# theta -> the six model features (must mirror prepare_cohort_intel.FEATURES exactly, and every
# one must be recomputable here from theta — that contract is what makes the trained model usable
# live rather than only replayable on the training cohorts).
# ---------------------------------------------------------------------------

# household_type (theta) -> the excel's 5 onboarding main cohorts (Main_Cohort_Hierarchy).
_HOUSEHOLD_TO_MC = {
    "single": "MC1", "flatmates": "MC1",
    "couple": "MC2",
    "couple_kids": "MC3",
    "couple_kids_parents": "MC4", "joint": "MC4",
}
# D2 time_route -> Cohort_Matrix_v3 time_pressure band (the model was trained on these bands).
_TIME_ROUTE_TO_PRESSURE = {"OUTSOURCE": "high", "SIMPLIFY": "medium", "DELEGATE": "low"}
# current-residence state -> the migration destination-group a metro maps to (City_Migration_Overlay
# destination_group_code). Only the metro groups; anything else resolves to a home-state group.
_STATE_TO_METRO_GROUP = {
    "Maharashtra": "MUMBAI_PUNE", "Delhi": "DELHI_NCR",
    "Karnataka": "BENGALURU_HYD_CHENNAI", "Telangana": "BENGALURU_HYD_CHENNAI",
    "Tamil Nadu": "BENGALURU_HYD_CHENNAI", "Gujarat": "AHMEDABAD_SURAT",
    "West Bengal": "KOLKATA_EAST", "Goa": "GOA_COASTAL",
}

_MODEL = None
_MIGRATION = None
_STATE_ARCHETYPE = None
_MISSING_FLOOR = None  # per-partition log-prob floor for a (feature,value) with no learned row


def _src_path(name):
    """Resolve a class_first_v1 artifact via the SAME config-dir seam every other runtime config
    file uses (ghar_re_core.config.SRC, GHAR_RE_CONFIG_DIR-aware), so it works from both a checked-
    out repo and the service's baked bundle (see knowledge.py / config.py on why a path relative to
    this file would break in a container)."""
    from ghar_re_core.config import SRC
    return _os.path.join(SRC, "class_first_v1", name)


def _model():
    """Load and cache the trained class-affinity model (parsed once per process)."""
    global _MODEL
    if _MODEL is None:
        with open(_src_path("cohort_class_model.json")) as f:
            _MODEL = _json.load(f)
    return _MODEL


def _state_archetype():
    """state_ut -> region_archetype, cached, from the extracted State_Profile_v3."""
    global _STATE_ARCHETYPE
    if _STATE_ARCHETYPE is None:
        _STATE_ARCHETYPE = {}
        with open(_src_path("state_profile.csv"), newline="") as f:
            for r in _csv.DictReader(f):
                _STATE_ARCHETYPE[r["state_ut"]] = r["region_archetype"]
    return _STATE_ARCHETYPE


def _migration():
    """(origin_state, destination_group) -> overlay row, cached, from City_Migration_Overlay_v3."""
    global _MIGRATION
    if _MIGRATION is None:
        _MIGRATION = {}
        with open(_src_path("migration_overlay.csv"), newline="") as f:
            for r in _csv.DictReader(f):
                _MIGRATION[(r["origin_state_ut"], r["destination_group_code"])] = r
    return _MIGRATION


def _nonveg_mode(theta):
    """Approximate the excel's nonveg_mode from theta's diet + Jain flag (coarse by design — a
    smoothed model feature, not an exact persona lookup)."""
    if theta["is_jain"]["value"]:
        return "jain"
    diet = theta["diet"]["value"]
    if diet == "veg":
        return "veg_default"
    if diet in ("eggetarian", "egg"):
        return "egg_only"
    return "default"


def _time_pressure_band(theta):
    """Band θ's numeric time_pressure (WP-16.2) to the persona-DB's high/medium/low. Falls back to
    the coarse time_route mapping only if the numeric field is absent (older θ)."""
    tp = theta.get("time_pressure", {}).get("value")
    if tp is None:
        return _TIME_ROUTE_TO_PRESSURE.get(theta["time_route"]["value"], "medium")
    return "high" if tp >= 0.6 else "medium" if tp >= 0.35 else "low"


def theta_features(theta, state=None):
    """The model features for this household. `state` overrides the state_ut/region_archetype pair
    (used for the 'local-city lifestyle' side of the migration blend). WP-16.2 added lifecycle_stage
    (sub-cohort granularity) and a numeric-banded time_pressure — must stay in sync with
    prepare_cohort_intel.FEATURES."""
    st = state or theta["home_state"]["value"]
    return {
        "state_ut": st,
        "region_archetype": _state_archetype().get(st, "UNKNOWN"),
        "city_tier_code": theta["city_tier"]["value"],
        "main_cohort_id": _HOUSEHOLD_TO_MC.get(theta["household_type"]["value"], "MC1"),
        "lifecycle_stage": theta.get("lifecycle_stage", {}).get("value", "none"),
        "time_pressure": _time_pressure_band(theta),
        "nonveg_mode": _nonveg_mode(theta),
    }


def _local_state(theta):
    """The current-residence STATE, guarded: theta['local_state'] is derived via a small city->state
    map that returns the raw city name for unrecognized cities (derivation._state_of_city). Treating
    such a name as a foreign state would spuriously flag a migrant, so any value that isn't a known
    state (not in State_Profile_v3) falls back to the home state — i.e. 'assume non-migrant unless we
    can positively resolve a different residence state'."""
    home = theta["home_state"]["value"]
    local = theta["local_state"]["value"]
    return local if local in _state_archetype() else home


def destination_group(theta):
    """Resolve this household's City_Migration_Overlay destination group from home vs current state
    and city tier. Home-state residents map to HOME_STATE_TIER1/2; out-of-state metro residents map
    to their metro group; anything else falls back to the home-state group of the current tier."""
    home = theta["home_state"]["value"]
    local = _local_state(theta)
    tier = theta["city_tier"]["value"]
    if local == home:
        return "HOME_STATE_TIER1" if tier == "T1" else "HOME_STATE_TIER2"
    grp = _STATE_TO_METRO_GROUP.get(local)
    if grp:
        return grp
    return "HOME_STATE_TIER1" if tier == "T1" else "HOME_STATE_TIER2"


def _partition_key(ctx):
    """ctx -> the model's 'slot|day-type' partition key."""
    daytype = "weekend" if ctx.get("weekday") in ("Saturday", "Sunday") else "weekday"
    return f"{ctx['slot']}|{daytype}"


def _raw_affinity(part, feats):
    """Pooled log-linear score per class for one feature set, over a partition's class vocabulary.
    Missing (feature,value) rows contribute the partition's smoothing floor rather than dropping the
    class — the same 'absent evidence is weak, not disqualifying' stance base()'s W_SIG takes."""
    vocab = part["classes"]
    floor = _math.log(0.5 / max(len(vocab), 1))   # matches the Laplace floor prepare_ uses
    scores = {}
    for c in vocab:
        s = 0.0
        for f, v in feats.items():
            fp = part["features"].get(f, {}).get(v)
            s += (fp.get(c, floor) if fp else floor)
        scores[c] = s
    return scores


def _softmax_scaled(scores):
    """Softmax over classes, then scale so the top class = 1.0 -> a graded [0,1] affinity where the
    single best class is 1.0 and everything else is its relative pull."""
    if not scores:
        return {}
    mx = max(scores.values())
    exp = {c: _math.exp(s - mx) for c, s in scores.items()}
    z = sum(exp.values()) or 1.0
    dist = {c: exp[c] / z for c in scores}
    top = max(dist.values()) or 1.0
    return {c: dist[c] / top for c in scores}


# Per-(household,slot/day-type) affinity cache. class_affinity() is called once per candidate dish
# (~810/request) but depends only on theta + the ctx partition, so we compute the distribution once
# and reuse it. Keyed by a signature of exactly the theta fields + ctx bits the computation reads.
_AFF_CACHE: dict = {}
_AFF_CACHE_MAX = 512


def _aff_signature(theta, ctx):
    """Hashable signature of everything class_affinity() actually depends on."""
    return (
        theta["home_state"]["value"], theta["local_state"]["value"], theta["city_tier"]["value"],
        theta["household_type"]["value"], theta["time_route"]["value"],
        theta["diet"]["value"], theta["is_jain"]["value"], _partition_key(ctx),
    )


def class_affinity(theta, ctx):
    """Migration-blended graded class affinity for ctx's slot + day-type: {class_code: [0,1]}.
    Memoized per household+partition (see _AFF_CACHE) so scoring 810 dishes computes it once.

    Blends the model's home-state affinity and current-city-lifestyle affinity by the household's
    City_Migration_Overlay weights (home_state_signature / current_city_lifestyle), then adds the
    national_modern weight to the overlay's named modern classes. A non-migrant (local == home)
    reduces cleanly to pure home-state affinity."""
    sig = _aff_signature(theta, ctx)
    cached = _AFF_CACHE.get(sig)
    if cached is not None:
        return cached
    result = _class_affinity_uncached(theta, ctx)
    if len(_AFF_CACHE) >= _AFF_CACHE_MAX:
        _AFF_CACHE.clear()
    _AFF_CACHE[sig] = result
    return result


def _class_affinity_uncached(theta, ctx):
    """The actual class-affinity computation (see class_affinity for the memoized entry point)."""
    model = _model()
    part = model["slots"].get(_partition_key(ctx))
    if part is None:
        return {}
    home = theta["home_state"]["value"]
    local = _local_state(theta)
    row = _migration().get((home, destination_group(theta)))
    if row:
        w_home = float(row["home_state_signature_weight"])
        w_local = float(row["current_city_lifestyle_weight"])
        w_nat = float(row["national_modern_weight"])
        overlay_classes = [c for c in (row.get("overlay_meal_classes") or "").split("|") if c]
    else:
        w_home, w_local, w_nat, overlay_classes = 1.0, 0.0, 0.0, []

    is_migrant = local != home
    aff_home = _softmax_scaled(_raw_affinity(part, theta_features(theta)))
    if w_local > 0 and is_migrant:
        aff_local = _softmax_scaled(_raw_affinity(part, theta_features(theta, state=local)))
    else:
        aff_local, w_home, w_local = {}, w_home + w_local, 0.0  # fold local weight into home

    vocab = part["classes"]
    blended = {c: w_home * aff_home.get(c, 0.0) + w_local * aff_local.get(c, 0.0) for c in vocab}
    # The City_Migration_Overlay's local-cuisine + national-modern class injection is for MIGRANTS
    # (the "MP-in-Mumbai" case). For a home-state resident it double-counts modern classes the
    # per-slot model already captures and crowds out the household's own traditional plan
    # (S14_T1_P10's weekday lunch has NO salad-bowl/delivery — those are migrant overlay artefacts).
    # So only apply the overlay bump for a genuine migrant.
    if is_migrant:
        for c in overlay_classes:
            if c in blended:
                blended[c] += w_nat        # national-modern push toward the overlay's modern classes
    top = max(blended.values()) if blended else 0.0
    learned = dict.fromkeys(vocab, 0.0) if top <= 0 else {c: blended[c] / top for c in vocab}

    # WP-17: blend the COMPOSITIONAL persona/state/migration plan (primary) with this learned
    # frequency model (secondary smoothing). The compositional plan carries the persona-specific,
    # regionally-grounded structure a frequency model washes out; the learned model keeps the plan
    # graded and generalizing over the classes the composition doesn't name. Weights from config.
    from ghar_re_core import cohort_plan
    from ghar_re_core.config import CONFIG
    comp = cohort_plan.class_plan(theta, ctx)
    w_comp, w_learn = CONFIG.class_plan_weights
    keys = set(learned) | set(comp)
    fused = {c: w_comp * comp.get(c, 0.0) + w_learn * learned.get(c, 0.0) for c in keys}
    ftop = max(fused.values()) if fused else 0.0
    if ftop <= 0:
        return {c: round(learned.get(c, 0.0), 4) for c in vocab}
    return {c: round(v / ftop, 4) for c, v in fused.items()}


def cohort_membership(theta, k=3):
    """Soft sub-cohort membership: the k persona anchors (Persona_Master_v3) this household most
    resembles, each with a match fraction. Explainability/decision-trace only — the class affinity
    above comes from the generalizing model, NOT from a single matched persona (that is the WP-16
    'science, not a fixed-persona lookup' line). Returns [] if the persona file isn't present."""
    try:
        with open(_src_path("persona_master.csv"), newline="") as f:
            personas = list(_csv.DictReader(f))
    except FileNotFoundError:
        return []
    feats = theta_features(theta)
    want_mc = feats["main_cohort_id"]
    want_tp = feats["time_pressure"]
    want_nv = feats["nonveg_mode"]
    scored = []
    for p in personas:
        m = 0
        m += 1 if p.get("main_cohort_id") == want_mc else 0
        m += 1 if (p.get("time_pressure") or "").lower() == want_tp else 0
        m += 1 if _nv_family(p.get("nonveg_mode")) == _nv_family(want_nv) else 0
        scored.append((m / 3.0, p["persona_id"], p.get("sub_cohort_label") or p.get("persona_name")))
    scored.sort(reverse=True)
    return [{"persona_id": pid, "label": lbl, "match": round(frac, 3)}
            for frac, pid, lbl in scored[:k]]


def _nv_family(mode):
    """Coarse nonveg-mode family for membership matching (veg / egg / nonveg / jain)."""
    mode = (mode or "").lower()
    if "jain" in mode:
        return "jain"
    if "veg" in mode and "non" not in mode:
        return "veg"
    if "egg" in mode:
        return "egg"
    return "nonveg"
