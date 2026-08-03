"""
ghar_re.derivation — D1-D7 Household Intelligence Layer (D1-D7 FROZEN).

Turns the raw Q1-Q15 answers into the Derived Household Profile θ. Every derived field is emitted
as a record (value, confidence, source, kind, stability, version, timestamp) per D1-D7 §1.1.
All constants come from data/source/derivation_params.yaml (never hardcoded).

v1 pins: confidence = 1.0 everywhere; D7 latent = {} (not implemented); kappa handled in scoring.
"""
import math
from datetime import datetime, timezone

from ghar_re_core.config import CONFIG
from ghar_re_core import knowledge as K

VERSION = "D-layer v1.0"


def _sigmoid(x):
    """Standard logistic sigmoid, squashing any real number into (0, 1). Used to turn the D1
    income-proxy weighted sum into a 0-1 'income score'."""
    return 1.0 / (1.0 + math.exp(-x))


def field(value, source, kind, stability, confidence=1.0):
    """A θ field record per D1-D7 §1.1 (v1 confidence pinned 1.0)."""
    return dict(value=value, confidence=confidence, source=source, kind=kind,
                stability=stability, version=VERSION,
                timestamp=datetime.now(timezone.utc).isoformat())


def _age_band(age):
    """Map a member's numeric age to one of the five age bands (<=24, 25-34, 35-50, 51-64, 65+)
    the derivation weight tables (age_factor, age_novelty, etc.) are keyed by."""
    if age <= 24:
        return "<=24"
    if age <= 34:
        return "25-34"
    if age <= 50:
        return "35-50"
    if age <= 64:
        return "51-64"
    return "65+"


def _primary_age(ages):
    """Representative adult age for D1/D3 factors (the eldest working-age member)."""
    adults = [a["age"] for a in ages if a["age"] >= 18]
    return max(adults) if adults else max(a["age"] for a in ages)


def derive_theta(hh):
    """hh = a raw household dict (fixtures.HOUSEHOLDS shape). Returns θ = {field_name: record}."""
    cfg = CONFIG
    # Normalize q3_home_state: the live app writes a 2-letter code ("MP"), but every state-keyed
    # structure in the engine keys on the full name ("Madhya Pradesh"). Without this the whole
    # regional/cohort layer silently no-ops for real users (see knowledge.normalize_state). Identity
    # for values already in full-name form, so fixtures/golden are unaffected.
    hh = {**hh, "q3_home_state": K.normalize_state(hh["q3_home_state"])}
    theta = {}
    ages = hh["q12_member_ages"]
    size = len(ages)
    dependents = sum(1 for a in ages if a["age"] < 18 or a["age"] >= 65)
    zone_home = K.STATE_ZONE.get(hh["q3_home_state"])
    # city tier from fixtures (CITY_TIER) -> tier1/2/3
    from ghar_re_core import fixtures as F
    city_tier = F.CITY_TIER.get(hh["q4_current_city"], "tier2")

    # ---------------- D1 — income proxy (D1-D7 §4 D1) ----------------
    d1 = cfg.D("D1_income")
    w = d1["weights"]
    earners_n = min(hh["q2_working_professionals"] / 2.0, 1.0)
    depend_ratio = dependents / size if size else 0.0
    city_tier_n = d1["city_tier_n"][city_tier]
    cook_hired = 1 if hh["q13_who_cooks"] == "hired_cook" else 0
    eatout_n = min(hh["q14_eat_out_per_week"] / d1["eatout_divisor"], 1.0)
    age_factor = d1["age_factor"][_age_band(_primary_age(ages))]
    s_income = _sigmoid(w["a0"] + w["a_earn"] * earners_n + w["a_dep"] * (1 - depend_ratio)
                        + w["a_city"] * city_tier_n + w["a_cook"] * cook_hired
                        + w["a_eat"] * eatout_n + w["a_age"] * age_factor)
    sub = [earners_n, (1 - depend_ratio), city_tier_n, cook_hired, eatout_n]
    mean = sum(sub) / len(sub)
    stdev = math.sqrt(sum((x - mean) ** 2 for x in sub) / len(sub))
    income_conf = 1 - min(2 * stdev, 1.0)
    if income_conf < d1["conf_lo"]:
        s_income = s_income + (0.45 - s_income) * 0.5  # pull toward 0.45 when unsure (conservative)
    cuts = d1["band_cuts"]
    income_band = ("low" if s_income < cuts["low_below"]
                   else "high" if s_income >= cuts["high_at_or_above"] else "mid")
    theta["income_band"] = field(income_band, "D1", "derived", "stable", confidence=round(income_conf, 3))
    theta["s_income"] = field(round(s_income, 4), "D1", "derived", "stable", confidence=round(income_conf, 3))

    # ---------------- D4 — origin<->local blend (needs zone) ----------------
    d4 = cfg.D("D4_blend")
    w4 = d4["weights"]
    zone_local = K.STATE_ZONE.get(_state_of_city(hh["q4_current_city"]), zone_home)
    is_migrant = (zone_home != zone_local)     # ZONE-crossing per KB §R1, not raw state string
    elders = 1 if any(a["age"] >= 65 for a in ages) else 0
    af = d1["age_factor"][_age_band(_primary_age(ages))]
    tenure_n = d4["tenure_n_default"]
    if not is_migrant:
        blend = 1.0
    else:
        blend = w4["c0"] + w4["c_elder"] * elders + w4["c_age"] * af - w4["c_tenure"] * tenure_n
        blend = max(w4["blend_min"], min(1.0, blend))
    theta["blend"] = field(round(blend, 4), "D4", "derived", "stable")
    theta["is_migrant"] = field(is_migrant, "D4", "derived", "stable")
    theta["home_state"] = field(hh["q3_home_state"], "explicit", "explicit", "stable")
    theta["home_zone"] = field(zone_home, "D4", "derived", "stable")
    theta["local_zone"] = field(zone_local, "D4", "derived", "stable")
    # local_state + city_tier carried into θ (WP-16): the Cohort-Intelligence layer needs the
    # CURRENT-residence state and its tier (T1/T2) to resolve the City_Migration_Overlay_v3 blend
    # and the class-affinity model's city_tier feature. city_tier was already computed above for D1;
    # exposing it here (as the excel's T1/T2 code) avoids re-deriving it in cohort_intel.
    theta["local_state"] = field(_state_of_city(hh["q4_current_city"]), "D4", "derived", "stable")
    theta["city_tier"] = field("T1" if city_tier == "tier1" else "T2", "D4", "derived", "stable")
    # region = the resolved palette zone; the more-weighted side wins for comfort-hero resolution.
    theta["region"] = field(zone_home if blend >= 0.5 else zone_local, "D4", "derived", "dynamic")
    # slot-specific blend (D4 slot offsets)
    so = d4["slot_offsets"]
    theta["blend_slot"] = field(
        {"breakfast": max(blend, so["breakfast_min"]),
         "lunch": round(blend + so["lunch_delta"], 4),
         "dinner": round(blend + so["dinner_delta"], 4)},
        "D4", "derived", "dynamic")

    # ---------------- D2 — time route + effort ceiling (needs D1) ----------------
    d2 = cfg.D("D2_time_route")
    ec = d2["effort_ceiling"]
    who = hh["q13_who_cooks"]
    # General household time-pressure (0-1), computed for EVERY cook arrangement (not just 'self'):
    # more earners and dependents raise it, eating out lowers it. Stored in θ (WP-16.2) so the cohort
    # layer bands it to high/medium/low — the previous coarse who_cooks→route→band path lost this
    # (a dual-income family-with-toddler that self-cooks is genuinely HIGH pressure, but mapped to
    # 'medium', diverging from the persona-DB toddler cohort which is 'high'; see cohort_intel).
    time_pressure = max(0.0, min(1.0, 0.5 * earners_n + 0.3 * (1 if dependents else 0) - 0.2 * eatout_n))
    if who == "hired_cook":
        effort_ceiling = ec["hired_cook"]
        time_route, reason = "DELEGATE", "hired cook present"
    elif who == "order_tiffin":
        effort_ceiling = ec["order_tiffin"]
        time_route, reason = "OUTSOURCE", "order/tiffin household"
    elif who == "family":
        effort_ceiling = ec["family"]
        time_route, reason = "SIMPLIFY", "family member cooks"
    else:  # self
        effort_ceiling = ec["self_weekday"]  # weekday default; weekend raises at context time
        if time_pressure > 0.5 and income_band == "high":
            time_route, reason = "OUTSOURCE", "dual-income / high time-pressure"
        else:
            time_route, reason = "SIMPLIFY", "low income / cook in-house"
    theta["time_route"] = dict(field(time_route, "D2", "derived", "dynamic"), reason=reason)
    theta["time_pressure"] = field(round(time_pressure, 3), "D2", "derived", "dynamic")
    theta["effort_ceiling"] = field(effort_ceiling, "D2", "derived", "dynamic")

    # ---------------- D3 — adventurousness (needs D1, D4) ----------------
    d3 = cfg.D("D3_adventurousness")
    w3 = d3["weights"]
    age_novelty = d3["age_novelty"][_age_band(_primary_age(ages))]
    hh_novelty = d3["hh_novelty"][hh["q1_household_type"]]
    migr_expo = 1 - blend
    A = w3["b0"] + w3["b_age"] * age_novelty + w3["b_hh"] * hh_novelty \
        + w3["b_inc"] * s_income + w3["b_migr"] * migr_expo + w3["b_eat"] * eatout_n
    A = max(0.0, min(1.0, A))
    rho_disc = d3["rho_floor"] + A * d3["rho_span_v1"]      # v1 familiarity-first (~0.05-0.10)
    theta["adventurousness"] = field(round(A, 4), "D3", "derived", "stable")
    theta["rho_disc"] = field(round(rho_disc, 4), "D3", "derived", "dynamic")

    # ---------------- D5 — household constraint set ----------------
    d5 = cfg.D("D5_household")
    roles = [a["role"] for a in ages]
    has_weaning = any(a["age"] < 2 for a in ages) or "weaning" in roles
    has_senior = any(a["age"] >= 65 for a in ages) or "senior" in roles
    # spice ceiling = min tolerance across members (map each member's band -> spice_tol)
    def _member_band(a):
        if a["age"] < 2:
            return "weaning"
        if a["age"] <= 3:
            return "toddler"
        if a["age"] <= 12:
            return "child"
        if a["age"] <= 19:
            return "teen"
        if a["age"] >= 65:
            return "senior"
        return "adult"
    spice_ceiling = min(d5["spice_tol"][_member_band(a)] for a in ages)
    texture_floor = "soft" if (has_weaning or has_senior) else "none"
    heaviness_ceiling = d5["heaviness_ceiling_senior"] if has_senior else 3
    variety_pressure = d5["variety_pressure"][hh["q1_household_type"]]
    batch_posture = 1 if hh["q1_household_type"] in ("joint", "couple_kids_parents") else 0
    # lifecycle_stage (WP-16.2): the dependent-driven sub-cohort signal (infant/toddler/school_child/
    # teen/elder/pregnancy/none), derived from member ages + roles + Q11 conditions. This is the
    # granularity WP-16 v1 dropped by keying only on main_cohort — it lets the cohort model isolate a
    # family-with-TODDLER (persona-DB SC3A) from the family average, restoring the child-appropriate
    # class plan (see cohort_intel.theta_features / persona-DB Subcohort_Routing).
    conds = {c.lower() for c in hh.get("q11_conditions", [])}
    role_set = {r.lower() for r in roles}

    def _lifecycle_stage():
        if any(a["age"] < 1 for a in ages) or {"infant"} & conds:
            return "infant"
        if any(a["age"] <= 3 for a in ages) or {"toddler", "weaning"} & (conds | role_set):
            return "toddler"
        if {"pregnancy", "pregnant", "preconception", "lactating"} & conds:
            return "pregnancy"
        if any(a["age"] >= 65 for a in ages) or {"senior"} & role_set or {"elderly", "recovery", "elder"} & conds:
            return "elder"
        if any(13 <= a["age"] <= 19 for a in ages) or {"teen"} & conds:
            return "teen"
        if any(4 <= a["age"] <= 12 for a in ages) or {"school_child", "school", "picky child", "child"} & conds:
            return "school_child"
        return "none"

    theta["lifecycle_stage"] = field(_lifecycle_stage(), "D5", "derived", "stable")
    theta["household_type"] = field(hh["q1_household_type"], "explicit", "explicit", "stable")
    theta["weaning_present"] = field(has_weaning, "D5", "derived", "stable")
    theta["spice_ceiling"] = field(spice_ceiling, "D5", "derived", "stable")
    theta["texture_floor"] = field(texture_floor, "D5", "derived", "stable")
    theta["heaviness_ceiling"] = field(heaviness_ceiling, "D5", "derived", "stable")
    theta["variety_pressure"] = field(variety_pressure, "D5", "derived", "stable")
    theta["batch_posture"] = field(batch_posture, "D5", "derived", "stable")

    # ---------------- D6 — tiered constraints (community prior + explicit) ----------------
    # Explicit Q5-Q8 ALWAYS win; community prior is the soft base (KB §C1 / community_priors.csv).
    theta["diet"] = field(hh["q5_diet"], "explicit", "explicit", "stable")
    theta["meat_exclusions"] = field([t for t in hh["q6_nonveg_types"] if t.startswith("no_")],
                                     "explicit", "explicit", "stable")
    theta["is_jain"] = field(bool(hh["q8_is_jain"]), "explicit", "explicit", "stable")
    theta["allergens"] = field(list(hh["q9_allergies"]), "explicit", "explicit", "stable")
    theta["veg_days"] = field(list(hh["q7_veg_days"]), "explicit", "explicit", "stable")
    cp = _community_prior(hh["q3_home_state"])
    theta["community_prior"] = field(cp, "D6", "derived", "stable")
    # non_veg_cadence: community default unless Q6 explicitly narrows (v1: use community default)
    theta["non_veg_cadence"] = field(cp["default_non_veg_cadence"] if cp else None,
                                     "D6", "derived", "stable")

    # ---------------- D7 — latent (v1 = {}) ----------------
    theta["latent"] = field({}, "D7", "derived", "dynamic")

    return theta


# --- community prior lookup (KB §C1) ---
# Reads from the loaded EngineConfig (CONFIG.community_priors), NOT from a file directly, so this
# derivation module has zero file-path knowledge (RE-DOC-11 §1/§2). The config LOADER owns the I/O.
def _community_prior(state):
    """Look up the community dietary-prior row (zone, diet_lean, default_non_veg_cadence) for a
    household's home state. Returns None if the state has no configured prior — a legitimate
    'no soft default available' case, not an error."""
    return CONFIG.community_priors.get(state)


# --- city -> home state (for D4 local-zone resolution) ---
_CITY_STATE = {
    "Bengaluru": "Karnataka", "Delhi": "Delhi", "Mumbai": "Maharashtra", "Pune": "Maharashtra",
    "Ahmedabad": "Gujarat", "Chennai": "Tamil Nadu", "Hyderabad": "Telangana", "Kolkata": "West Bengal",
}


def _state_of_city(city):
    """Resolve a current-residence city to its state, for computing the household's 'local' zone
    in D4. Falls back to returning the input unchanged for any city not in the lookup table."""
    return _CITY_STATE.get(city, city)
