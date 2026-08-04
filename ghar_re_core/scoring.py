"""
ghar_re.scoring — Hard Filters (Core Spine §S2 PART A) + BASE score (§S2 PART B) + Q15 gain (§S3).

All weights/thresholds come from data/source/*.yaml (via ghar_re.config) and the KB (via
ghar_re.knowledge). Nothing scoring-related is hardcoded. Section refs are cited inline.
"""
from ghar_re_core.config import CONFIG
from ghar_re_core import knowledge as K
from ghar_re_core import catalogue as C
from ghar_re_core import cohort_intel


# =====================================================================================
# PART A — HARD FILTERS (§S2 PART A). A dish survives iff ALL predicates hold.
# =====================================================================================
def pass_diet(dish, theta, ctx):
    """A1 hard filter: does this dish match the household's diet (Q5) and meat exclusions (Q6)?
    A veg_egg mode or a configured veg-day can temporarily tighten a non-veg/eggetarian household
    to veg for that one session — a restriction only, never a loosening."""
    # A1 diet (Q5/Q6). veg_egg mode / veg-day can tighten to veg for the session.
    diet = theta["diet"]["value"]
    modes = ctx.get("active_modes", [])
    veg_day = ctx.get("weekday") in theta["veg_days"]["value"]
    effective = diet
    if "veg_egg" in modes or veg_day:
        effective = "veg"                     # session tighten (restriction only, upward)
    if effective == "vegan":
        return dish.vegan_compatible
    if effective == "veg":
        return dish.diet == "veg"
    if effective in ("eggetarian", "egg"):
        return dish.diet in ("veg", "egg")
    # non_veg: allow all, minus explicit meat exclusions (Q6 no_beef/no_pork/...)
    excl = theta["meat_exclusions"]["value"]
    if excl:
        meat_classes = {"no_beef": "beef", "no_pork": "pork", "no_red_meat": {"mutton", "lamb", "beef", "pork"}}
        for e in excl:
            banned = meat_classes.get(e)
            if banned:
                banned = {banned} if isinstance(banned, str) else banned
                if set(dish.main_ingredients) & banned:
                    return False
    return True


def pass_jain(dish, theta, ctx):
    """A2 hard filter: if the household is Jain (Q8), only Jain-compatible dishes pass. Not
    negotiable by any mode or context — Jain observance is always enforced when set."""
    # A2 Jain (Q8) — HARD.
    return (not theta["is_jain"]["value"]) or (dish.jain_compatible == "Y")


def pass_allergen(dish, theta, ctx):
    """A3 hard filter, safety-critical: rejects any dish carrying an allergen the household has
    declared (Q9/Q10). Covers explicit-ingredient allergens plus the known hidden-derivative
    carriers in catalogue.HIDDEN_DERIVATIVE_ALLERGENS (e.g. hing/asafoetida and soy sauce both
    commonly carry wheat/gluten as a commercial-form carrier, not an intrinsic ingredient
    property) — see catalogue.dish_allergens() for the cited list. Not an exhaustive
    cross-contamination/hidden-derivative layer covering every possible commercial-product risk,
    only the specific, sourced cases catalogued so far."""
    # A3 allergen (Q9/Q10) — SAFETY-CRITICAL basic pass + known hidden-derivative carriers.
    hh_allergens = set(theta["allergens"]["value"])
    return not (C.dish_allergens(dish) & hh_allergens)


def pass_weaning(dish, theta, ctx):
    """A4 hard filter, applied only to SHARED-hero plates: when the household has a weaning-age
    member, a dish must be low-spice (<=1) AND soft/smooth/mashable-textured AND free of
    crunchy/crispy/dense/chewy textures. This is the one age-driven HARD filter in the engine —
    every other age effect (spice ceiling, texture floor for non-weaning cases) is a soft demote
    in m_age(), not a rejection."""
    # A4 weaning (D5 age) — the ONE age HARD filter, applied to SHARED-hero plates.
    # spice_level <= 1 AND soft/smooth/mashable texture AND no whole nuts/seeds/hard.
    if not theta["weaning_present"]["value"]:
        return True
    soft_tex = {"soft", "smooth", "mashable", "fluffy", "sticky"}
    if dish.spice_level is not None and dish.spice_level > 1:
        return False
    if not (set(dish.texture) & soft_tex):
        return False
    hard = {"crunchy", "crispy", "dense", "chewy"}
    if set(dish.texture) & hard:
        return False
    return True


def pass_exclude_dish_ids(dish, theta, ctx):
    """WP-8G hard filter (Option A — server-side exclusion): rejects a dish whose id appears in
    the request's `exclude_dish_ids` (additive/optional — omitted or empty is a no-op, matching
    every existing caller/fixture that predates this field). Always a hard pool-stage exclusion,
    never a scoring penalty, so an excluded dish can never surface even at score rank 1 — see
    docs/project-history/work-packages/[DRAFT]_WP-8G_Recommendation_Variety_on_Refresh_v1.0.md
    §1 Option A."""
    excl = ctx.get("exclude_dish_ids")
    if not excl:
        return True
    return dish.id not in set(excl)


def pass_mode_fasting(dish, theta, ctx):
    """A5 hard filter, only active when 'fasting' is in the context's active_modes: restricts to
    farali (fasting-permitted) dishes. A no-op filter (everything passes) outside fasting mode."""
    # A5 fasting mode — farali_compatible only when Fasting is on.
    if "fasting" not in ctx.get("active_modes", []):
        return True
    return dish.farali_compatible


def pass_calorie(plate_cals, ctx):
    """A6 optional, plate-level filter: if the context sets a calorie_target, rejects plates that
    exceed it by more than the configured epsilon tolerance (default 10%). Always passes when no
    target is set — this filter is off by default."""
    # A6 optional calorie lens (plate-level). Off unless a target is set.
    target = ctx.get("calorie_target")
    if not target:
        return True
    eps = CONFIG.filters["hard_filters"].get("A6_epsilon", 0.10)
    return plate_cals <= target * (1 + eps)


def eligibility_funnel(catalogue, theta, ctx, shared_hero=True):
    """Non-authoritative, additive: replays eligible()'s EXACT filter order (A1-A5) over the
    whole catalogue and reports how many dishes survive after each stage. NEVER used to decide
    eligibility itself — eligible() below remains the sole source of truth for filtering; this
    exists only so a caller can report the funnel breakdown ("802 total -> N after diet -> ...")
    for observability, without eligible()'s early-return short-circuiting hiding the intermediate
    counts. Reuses eligible()'s own pass_* functions, so the two can never silently drift apart.
    Returns an ordered list of {"stage": str, "count": int} dicts, ending at the same count
    len([d for d in catalogue if eligible(d, theta, ctx, shared_hero)]) would give."""
    survivors = list(catalogue)  # materialize once — Catalogue is iterable but not sized
    funnel = [{"stage": "catalogue_total", "count": len(survivors)}]
    stages = [("after_diet_filter", pass_diet), ("after_jain_filter", pass_jain),
              ("after_allergen_filter", pass_allergen)]
    if shared_hero:
        stages.append(("after_weaning_filter", pass_weaning))
    stages.append(("after_fasting_filter", pass_mode_fasting))
    stages.append(("after_exclude_dish_ids_filter", pass_exclude_dish_ids))
    for stage_name, check in stages:
        survivors = [d for d in survivors if check(d, theta, ctx)]
        funnel.append({"stage": stage_name, "count": len(survivors)})
    return funnel


def eligible(dish, theta, ctx, shared_hero=True):
    """All correctness/observance filters A1-A5 (A6 is plate-level, applied in pairing).
    shared_hero=False relaxes the weaning floor for the non-shared 'extra' plates of the 7."""
    if not pass_diet(dish, theta, ctx):
        return False
    if not pass_jain(dish, theta, ctx):
        return False
    if not pass_allergen(dish, theta, ctx):
        return False
    if shared_hero and not pass_weaning(dish, theta, ctx):
        return False
    if not pass_mode_fasting(dish, theta, ctx):
        return False
    if not pass_exclude_dish_ids(dish, theta, ctx):
        return False
    return True


# =====================================================================================
# PART B — BASE score (§S2 PART B).  BASE = Σ_k W_k · conf_k · m_k  (+ PRIOR).  conf_k=1.0 v1.
# =====================================================================================
def _cuis(dish, state):
    """§B1 cuis(x, state): how well a dish's cuisine matches a given state, from 1.00 (exact same
    state of origin) down to 0.40 (same broad zone) to 0.0 (no relation) — the core regional-fit
    building block m_palette() blends across a household's home and local state."""
    # §B1 cuis(x,S): 1.00 same state, 0.70 same parent, 0.40 same group/zone, 0.15 adjacent, else 0.
    if dish.state_origin == state:
        return 1.00
    dish_zone = dish.zone
    state_zone = K.STATE_ZONE.get(state)
    if dish_zone and state_zone and dish_zone == state_zone:
        return 0.40
    return 0.0


def m_palette(dish, theta):
    """§B1 regional-fit BASE term: how well a dish matches this household's palette, blending
    its home-state fit and local-state fit by the D4 blend ratio. Experimental-tier dishes are
    further scaled down by rho_disc (the household's discovery/familiarity dial), so adventurous
    households see more of them and cautious ones see fewer."""
    # §B1 regional fit, D4-blended (blend home vs local). experimental gated by rho_disc.
    blend = theta["blend"]["value"]
    home = theta["home_state"]["value"]
    local_state = _zone_state(theta["local_zone"]["value"])
    val = blend * _cuis(dish, home) + (1 - blend) * _cuis(dish, local_state)
    if dish.scope_tier == "experimental":
        val *= theta["rho_disc"]["value"]
    return val


def m_slot(dish, ctx):
    """§B2 BASE term: 1.0 if this dish is valid for the current meal slot (breakfast/lunch/
    dinner/snacks), else 0.0 — a dish that doesn't fit the slot contributes nothing here (it may
    still be filtered out entirely elsewhere)."""
    # §B2: 1 if slot in dish.meal_type else 0.
    return 1.0 if ctx["slot"] in dish.meal_type else 0.0


def m_season(dish, ctx):
    """§B3 BASE term: how well a dish fits the standing season (summer/winter/monsoon), reusing
    the dish's weather_affinity tags as a proxy for seasonal thermal fit. Returns 1.0 for a
    strong seasonal match, 0.5 as a neutral default, 0.0 for a clear seasonal mismatch (e.g. a
    deep-fried heavy dish in summer)."""
    # §B3 standing seasonal thermal fit, reusing WE weather_affinity tags. Signed→[0,1]-ish.
    season = ctx.get("season")
    wa = set(dish.weather_affinity)
    if season == "summer":
        if "hot_weather" in wa:
            return 1.0
        if {"deep_fried"} & set(dish.cooking_method) or dish.heaviness == 3:
            return 0.0
        return 0.5
    if season == "winter":
        if "cold_weather" in wa:
            return 1.0
        return 0.5
    if season == "monsoon":
        if "rainy" in wa:
            return 1.0
        return 0.5
    return 0.5


def sig(dish):
    """§B4 signature-boost BASE term: how famous/iconic this dish is, taken directly from its
    pre-computed sig_score (0 for an unscored dish, up to 1.0 for a national icon like Butter
    Chicken or Masala Dosa)."""
    # §B4 signature boost — graded sig(x) in [0,1] from sig_scores (KB §S1 band rule).
    return dish.sig_score


def m_age(dish, theta):
    """§B5/D5 BASE term: softly demotes (never hard-rejects) a dish whose spice level exceeds the
    household's spice ceiling, or whose texture violates a soft-texture floor (e.g. for a
    household with a senior member) — the graded counterpart to the hard weaning filter."""
    # §B5/D5: soft demote spice above ceiling and texture-floor violations.
    d5 = CONFIG.D("D5_household")
    p_spice, p_tex = d5["penalties"]["p_spice"], d5["penalties"]["p_tex"]
    ceiling = theta["spice_ceiling"]["value"]
    over = max(0, (dish.spice_level or 0) - ceiling)
    tex_violation = 0
    if theta["texture_floor"]["value"] == "soft":
        soft_tex = {"soft", "smooth", "fluffy", "sticky"}
        if not (set(dish.texture) & soft_tex):
            tex_violation = 1
    return 1 - min(over * p_spice + tex_violation * p_tex, 1.0)


def m_household(dish, theta):
    """§B6 BASE term: how well a dish fits this household's structure — e.g. a batch-friendly
    whole-meal dish scores higher for a joint/large household, and a mild/familiar dish scores
    higher in proportion to the household's variety pressure (continuous, not a single cliff at
    0.8) and how far below the household's spice ceiling the dish actually sits — so two dishes
    in the same meal class no longer collapse to the same 0.5/0.7 fit for every household sharing
    that class; the ranking now moves with the household's own batch/mildness posture."""
    # §B6 household structure soft-fit. single->one-pot; couple+kids->mild/familiar (graded); joint->batch.
    bp = theta["batch_posture"]["value"]
    vp = theta["variety_pressure"]["value"]
    ceiling = theta["spice_ceiling"]["value"]
    fit = 0.5
    if bp and "whole_meal" in dish.dish_category:
        fit += 0.2
    if dish.spice_level is not None and ceiling:
        headroom = max(0.0, (ceiling - dish.spice_level) / ceiling)  # 1.0 mild, 0.0 at the ceiling
        fit += vp * headroom * 0.3     # scales with household's own variety pressure, not a step
    return min(1.0, fit)


def m_weather(dish, theta, ctx):
    """§B7 TRANSIENT signed weather term, resolving to the household's OWN regional comfort hero
    (KB §R3). Never a filter. Returns value in [-1, +1]; scaled by W_WEATHER in base()."""
    wcond = _weather_tag(ctx)                 # 'rainy'/'hot_weather'/'cold_weather'/None
    if wcond is None:
        return 0.0
    wa = set(dish.weather_affinity)
    val = 0.0
    if wcond == "rainy":
        # + comfort/fried in-tag ; - raw/salad
        if "rainy" in wa or {"deep_fried", "shallow_fried"} & set(dish.cooking_method):
            val += 0.5
        if "salad_raita" in dish.dish_category:
            val -= 0.5
    elif wcond == "hot_weather":
        if "hot_weather" in wa or "light" in dish.richness or dish.serving_temp == "chilled":
            val += 0.5
        if {"deep_fried"} & set(dish.cooking_method) or dish.heaviness == 3 or (dish.spice_level or 0) >= 4:
            val -= 0.5
    elif wcond == "cold_weather":
        if "cold_weather" in wa or {"ghee_rich", "buttery", "creamy"} & set(dish.richness):
            val += 0.5

    # ---- the critical rule: resolve to THIS household's KB §R3 comfort hero, not a generic one.
    hero_names = _comfort_heroes_for(theta, wcond)
    if dish.name in hero_names:
        val += 0.5                             # zone-specific comfort hero gets the decisive lift
    return max(-1.0, min(1.0, val))


def prior_boost(dish, theta, ctx):
    """§B8 BASE term: sums up every authored PRIOR[zone][slot] boost (KB §R2) that applies to
    this dish for the household's region and the current meal slot — e.g. a small extra lift for
    "idli/dosa" dishes at South breakfast. Zero if no configured prior matches."""
    # §B8 PRIOR[zone][slot] additive authored boost (KB §R2), matched tolerantly to the dish.
    zone = theta["region"]["value"]
    slot = ctx["slot"]
    total = 0.0
    for (z, s, mk, mv, boost, _tags, _ds) in K.PRIOR_ZONE_SLOT:
        if z != zone or s != slot:
            continue
        if _prior_matches(dish, mk, mv):
            total += boost
    return total


def base(dish, theta, ctx):
    """BASE = Σ_k W_k·conf_k·m_k + PRIOR[zone][slot]  (§S2 PART B). conf_k pinned 1.0 (v1).

    Delegates to ghar_re_core.modules_default.DEFAULT_REGISTRY's phase="base" modules (Phase 1
    ScoringModule registry refactor) — the 7 W_k-weighted terms + prior_boost, combined as a
    weighted sum. Each underlying m_palette/m_slot/.../prior_boost function body is UNCHANGED;
    only how they're invoked/composed moved into the registry, so this is score-neutral by
    construction. Imported lazily (not at module top) to avoid a circular import: modules_default
    imports scoring's own functions to build its BoundModule wrappers."""
    from ghar_re_core.modules_default import DEFAULT_REGISTRY
    total, _ = DEFAULT_REGISTRY.combine(dish, theta, ctx, phase="base")
    return total


# =====================================================================================
# PART C — Q15 GAIN (§S3). GAIN = 1 + Σ_g gamma[obj][g]·gs_g(x). kappa pinned 1.0 (v1).
# =====================================================================================
def _cal_n(dish):
    """Normalize a dish's calorie count to a 0-1 scale (0 at ~30 kcal, 1 at ~800 kcal), for use
    as a sub-signal in the Q15 gain-score components below. Returns 0.0 for a dish with no
    recorded calories."""
    return max(0.0, min((dish.calories - 30) / 770.0, 1.0)) if dish.calories else 0.0


def _heaviness_n(dish):
    """Normalize a dish's 1-3 heaviness rating to a 0-1 scale, for use as a sub-signal in the
    Q15 gain-score components below. Returns 0.0 for a dish with no recorded heaviness."""
    return (dish.heaviness - 1) / 2.0 if dish.heaviness else 0.0


def gs_indulgence(dish):
    """Q15 gain-score component: how 'indulgent' a dish is (rich/fried/heavy/high-calorie),
    averaged from richness tags, cooking method, heaviness, and calories into a single 0-1
    score. Feeds gain_q15() for objectives like 'awesome_taste' that reward indulgence."""
    rich = {"buttery", "creamy", "ghee_rich", "coconut_rich", "oily"}
    fried = {"deep_fried", "shallow_fried", "dum_cooked"}
    return sum([
        1.0 if set(dish.richness) & rich else 0.0,
        1.0 if set(dish.cooking_method) & fried else 0.0,
        _heaviness_n(dish),
        _cal_n(dish),
    ]) / 4.0


def gs_light(dish):
    """Q15 gain-score component: how 'light' a dish is (the inverse of indulgence) — plain/light
    richness, light cooking methods, and low calories/heaviness. Feeds gain_q15() for objectives
    like 'healthy_living' that reward lighter dishes."""
    light = {"light", "plain"}
    lightcook = {"steamed", "boiled", "grilled", "raw", "tempered"}
    return sum([
        1.0 if set(dish.richness) & light else 0.0,
        1.0 if set(dish.cooking_method) & lightcook else 0.0,
        1 - _cal_n(dish),
        1 - _heaviness_n(dish),
    ]) / 4.0


def gs_protein(dish):
    """Q15 gain-score component: how protein-forward a dish is, proxied from its diet type and
    dish category (non_veg/egg dishes and dal/kebab/egg categories score higher) until real
    macro-gram protein data is available in a future version. Feeds gain_q15() for objectives
    like 'into_fitness'."""
    # proxy (diet+category) until dish_macro real grams in v2.
    protein_cat = {"dal_lentil", "kebab", "egg_dish"}
    proxy = 0.6 if (dish.diet in ("non_veg", "egg") or set(dish.dish_category) & protein_cat) else 0.2
    return sum([
        1.0 if dish.diet in ("non_veg", "egg") else 0.0,
        1.0 if set(dish.dish_category) & protein_cat else 0.0,
        proxy,
    ]) / 3.0


def gain_q15(dish, objective):
    """§S3 GAIN_Q15: the multiplier applied to a dish's BASE score based on the household's
    stated Q15 objective (e.g. 'awesome_taste', 'healthy_living', 'into_fitness'), computed as
    1 plus a weighted combination of the indulgence/light/protein gain-score components, clamped
    to the configured gain_bounds. Falls back to the default objective if none is given."""
    cfg = CONFIG
    obj = objective or cfg.default_objective
    g = cfg.gamma(obj)
    kappa = cfg.kappa_v1                       # v1 pinned 1.0
    raw = 1 + kappa * (g["indulgence"] * gs_indulgence(dish)
                       + g["light"] * gs_light(dish)
                       + g["protein"] * gs_protein(dish))
    lo, hi = cfg.gain_bounds
    return max(lo, min(hi, raw))


def s_cohort(dish, theta, ctx):
    """§WP-16 S_cohort(x;cohort): the Core Spine master formula's `w_cohort·S_cohort` term, now a
    GRADED [0,1] class affinity (WP-15 shipped the binary 0/1 predecessor). Looks up this dish's
    curated meal class (K.dish_to_class_code) and returns how strongly a household of this shape —
    living where it lives — plans that class right now, from the migration-blended, model-learned
    class-affinity distribution (cohort_intel.class_affinity). 0.0 if the dish has no curated class
    or its class has no affinity in this slot/day-type. Still additive, still never a filter/gate;
    the LIVE theta match (never a stored persona) is unchanged from WP-15."""
    class_code = K.dish_to_class_code(dish.name)
    if class_code is None:
        return 0.0
    return cohort_intel.class_affinity(theta, ctx).get(class_code, 0.0)


def s_foreign(dish):
    """§WP-16.1: 1.0 if this dish is foreign (zone=Global — Chinese/continental/etc.), else 0.0.
    Foreign food is never in any persona-DB cohort plan, so at cold-start it carries a decaying
    demote (see score / CONFIG.foreign_demote_effective). Never a filter — a soft demote only."""
    return 1.0 if dish.zone == "Global" else 0.0


def score(dish, theta, ctx, objective):
    """score = BASE × GAIN_Q15 + w_cohort(n)·S_cohort − foreign_demote(n)·S_foreign
    + w_pref·S_pref (− PENALTY[assemble]).

    Both cohort weight and foreign demote are WP-16 cold-start-strong, decaying with
    ctx['interaction_count'] (0 for a new household — every live household today).

    The `w·S_cohort − wf·S_foreign` term is computed via DEFAULT_REGISTRY's phase="cohort"
    modules (Phase 1 ScoringModule registry refactor): s_foreign's module models its effective
    weight as NEGATIVE (see modules_default.py), so combine()'s plain weighted sum already nets
    out to the same subtraction — no special-casing needed here. s_cohort/s_foreign's own bodies
    are unchanged.

    The `+ w_pref·S_pref` term (Phase 3) is computed via DEFAULT_REGISTRY's phase="pref" — an
    EXPLICIT, separate combine() call, never folded into the phase="cohort" or phase="base" calls
    above, so this is the only place phase="pref" is allowed to affect a live score. In every
    deployment today s_pref itself returns 0.0 (ghar_re_core/preference.py — no artifact loaded)
    AND its weight (CONFIG.w_pref, pref_model.yaml) also defaults to 0.0, so `pref_val` is
    unconditionally 0.0 and this call is a byte-for-byte no-op (golden-master proves it)."""
    from ghar_re_core.modules_default import DEFAULT_REGISTRY
    cohort_val, _ = DEFAULT_REGISTRY.combine(dish, theta, ctx, phase="cohort")
    pref_val, _ = DEFAULT_REGISTRY.combine(dish, theta, ctx, phase="pref")
    return base(dish, theta, ctx) * gain_q15(dish, objective) + cohort_val + pref_val


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def _weather_tag(ctx):
    """Map the injected/mocked weather context (Core Spine B7; weather API mocked) to a tag,
    using weather_rules.yaml thermal thresholds."""
    th = CONFIG.weather_thresholds
    if ctx.get("is_raining") or ctx.get("weather_condition") == "rain":
        return "rainy"
    t = ctx.get("temp_c")
    if t is not None and t >= th["HOT_temp_c_gte"]:
        return "hot_weather"
    if t is not None and t <= th["COLD_temp_c_lte"]:
        return "cold_weather"
    if ctx.get("weather_condition") == "heatwave":
        return "hot_weather"
    if ctx.get("weather_condition") == "cold_snap":
        return "cold_weather"
    return None


def _comfort_heroes_for(theta, weather_tag):
    """KB §R3 comfort_hero(zone, weather) resolved to THIS household — prefer the sub-zone
    (e.g. West-MH) via home_state, else the base zone. Returns the set of hero dish names."""
    kb_weather = K.WEATHER_TAG_TO_KB.get(weather_tag)
    if not kb_weather:
        return set()
    home_state = theta["home_state"]["value"]
    subzone = K.STATE_TO_KB_SUBZONE.get(home_state)
    region = theta["region"]["value"]
    keys = [k for k in (subzone, region) if k]
    heroes = set()
    for (zone, weather, name, _verified, _ds) in K.COMFORT_HERO_MAP:
        if weather == kb_weather and zone in keys:
            # resolve the KB hero NAME to the concrete golden dish name (exact match)
            heroes.add(K.COMFORT_HERO_TO_DISH.get(name, name))
    return heroes


def _prior_matches(dish, match_kind, match_value):
    """Check whether a dish satisfies one PRIOR_ZONE_SLOT row's match rule. `match_kind` selects
    how to interpret `match_value`: a name substring, a dish_category tag, a hero_role, a
    cuisine, or (for 'structure'/'attribute' rows describing a whole PLATE like
    'roti+sabzi+dal') a composite whole-meal/thali dish that carries every token."""
    mv = match_value.lower()
    if match_kind == "dish_name":
        return mv in dish.name.lower()
    if match_kind == "dish_category":
        return match_value in dish.dish_category
    if match_kind == "hero_role":
        return dish.hero_role == match_value
    if match_kind == "cuisine":
        return dish.cuisine == match_value
    if match_kind in ("structure", "attribute"):
        # Structure priors (e.g. 'roti+sabzi+dal') describe a PLATE, not a single dish. At dish-scoring
        # time require the dish to actually BE that composite (a whole_meal/thali carrying ALL tokens),
        # so a bare 'dal' token does NOT spuriously boost every dish whose name contains "dal".
        toks = mv.replace("+", " ").split()
        hay = (dish.name.lower() + " " + " ".join(dish.dish_category)).lower()
        is_composite = bool({"whole_meal", "thali_combo"} & set(dish.dish_category))
        return is_composite and all(t in hay for t in toks)
    return False


def _zone_state(zone):
    """Pick one representative state for a broad zone (e.g. 'Delhi' for North), used by
    m_palette() when it needs a concrete state to score local-palette fit against. Defaults to
    Delhi for any unrecognized zone."""
    # representative state for a zone (for local-palette m_palette). Uses KB STATE_ZONE inverse.
    rep = {"North": "Delhi", "South": "Tamil Nadu", "East": "West Bengal",
           "West": "Maharashtra", "Central": "Madhya Pradesh", "Northeast": "Assam"}
    return rep.get(zone, "Delhi")
