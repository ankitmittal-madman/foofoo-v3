"""
ghar_re.scoring — Hard Filters (Core Spine §S2 PART A) + BASE score (§S2 PART B) + Q15 gain (§S3).

All weights/thresholds come from data/source/*.yaml (via ghar_re.config) and the KB (via
ghar_re.knowledge). Nothing scoring-related is hardcoded. Section refs are cited inline.
"""
from ghar_re_core.config import CONFIG
from ghar_re_core import knowledge as K
from ghar_re_core import catalogue as C


# =====================================================================================
# PART A — HARD FILTERS (§S2 PART A). A dish survives iff ALL predicates hold.
# =====================================================================================
def pass_diet(dish, theta, ctx):
    # A1 diet (Q5/Q6). veg_egg mode / veg-day can tighten to veg for the session.
    diet = theta["diet"]["value"]
    modes = ctx.get("active_modes", [])
    veg_day = ctx.get("weekday") in theta["veg_days"]["value"]
    effective = diet
    if "veg_egg" in modes or veg_day:
        effective = "veg"                     # session tighten (restriction only, upward)
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
    # A2 Jain (Q8) — HARD.
    return (not theta["is_jain"]["value"]) or (dish.jain_compatible == "Y")


def pass_allergen(dish, theta, ctx):
    # A3 allergen (Q9/Q10) — SAFETY-CRITICAL basic pass (hidden-derivative layer out of scope).
    hh_allergens = set(theta["allergens"]["value"])
    return not (C.dish_allergens(dish) & hh_allergens)


def pass_weaning(dish, theta, ctx):
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


def pass_mode_fasting(dish, theta, ctx):
    # A5 fasting mode — farali_compatible only when Fasting is on.
    if "fasting" not in ctx.get("active_modes", []):
        return True
    return dish.farali_compatible


def pass_calorie(plate_cals, ctx):
    # A6 optional calorie lens (plate-level). Off unless a target is set.
    target = ctx.get("calorie_target")
    if not target:
        return True
    eps = CONFIG.filters["hard_filters"].get("A6_epsilon", 0.10)
    return plate_cals <= target * (1 + eps)


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
    return True


# =====================================================================================
# PART B — BASE score (§S2 PART B).  BASE = Σ_k W_k · conf_k · m_k  (+ PRIOR).  conf_k=1.0 v1.
# =====================================================================================
def _cuis(dish, state):
    # §B1 cuis(x,S): 1.00 same state, 0.70 same parent, 0.40 same group/zone, 0.15 adjacent, else 0.
    if dish.state_origin == state:
        return 1.00
    dish_zone = dish.zone
    state_zone = K.STATE_ZONE.get(state)
    if dish_zone and state_zone and dish_zone == state_zone:
        return 0.40
    return 0.0


def m_palette(dish, theta):
    # §B1 regional fit, D4-blended (blend home vs local). experimental gated by rho_disc.
    blend = theta["blend"]["value"]
    home = theta["home_state"]["value"]
    local_state = _zone_state(theta["local_zone"]["value"])
    val = blend * _cuis(dish, home) + (1 - blend) * _cuis(dish, local_state)
    if dish.scope_tier == "experimental":
        val *= theta["rho_disc"]["value"]
    return val


def m_slot(dish, ctx):
    # §B2: 1 if slot in dish.meal_type else 0.
    return 1.0 if ctx["slot"] in dish.meal_type else 0.0


def m_season(dish, ctx):
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
    # §B4 signature boost — graded sig(x) in [0,1] from sig_scores (KB §S1 band rule).
    return dish.sig_score


def m_age(dish, theta):
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
    # §B6 household structure soft-fit. single->one-pot; couple+kids->mild/familiar; joint->batch.
    bp = theta["batch_posture"]["value"]
    fit = 0.5
    if bp and "whole_meal" in dish.dish_category:
        fit = 0.7
    if theta["variety_pressure"]["value"] >= 0.8 and dish.spice_level is not None and dish.spice_level <= 2:
        fit = max(fit, 0.7)     # kid-heavy household leans mild/familiar
    return fit


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
    # §B8 PRIOR[zone][slot] additive authored boost (KB §R2), matched tolerantly to the dish.
    zone = theta["region"]["value"]
    slot = ctx["slot"]
    total = 0.0
    for (z, s, mk, mv, boost, tags, ds) in K.PRIOR_ZONE_SLOT:
        if z != zone or s != slot:
            continue
        if _prior_matches(dish, mk, mv):
            total += boost
    return total


def base(dish, theta, ctx):
    """BASE = Σ_k W_k·conf_k·m_k + PRIOR[zone][slot]  (§S2 PART B). conf_k pinned 1.0 (v1)."""
    cfg = CONFIG
    conf = cfg.all_conf_k
    val = (cfg.W("W_PALETTE") * conf * m_palette(dish, theta)
           + cfg.W("W_SLOT") * conf * m_slot(dish, ctx)
           + cfg.W("W_SEASON") * conf * m_season(dish, ctx)
           + cfg.W("W_SIG") * conf * sig(dish)
           + cfg.W("W_AGE") * conf * m_age(dish, theta)
           + cfg.W("W_HOUSE") * conf * m_household(dish, theta)
           + cfg.W("W_WEATHER") * conf * m_weather(dish, theta, ctx)   # signed
           + prior_boost(dish, theta, ctx))
    return val


# =====================================================================================
# PART C — Q15 GAIN (§S3). GAIN = 1 + Σ_g gamma[obj][g]·gs_g(x). kappa pinned 1.0 (v1).
# =====================================================================================
def _cal_n(dish):
    return max(0.0, min((dish.calories - 30) / 770.0, 1.0)) if dish.calories else 0.0


def _heaviness_n(dish):
    return (dish.heaviness - 1) / 2.0 if dish.heaviness else 0.0


def gs_indulgence(dish):
    rich = {"buttery", "creamy", "ghee_rich", "coconut_rich", "oily"}
    fried = {"deep_fried", "shallow_fried", "dum_cooked"}
    return sum([
        1.0 if set(dish.richness) & rich else 0.0,
        1.0 if set(dish.cooking_method) & fried else 0.0,
        _heaviness_n(dish),
        _cal_n(dish),
    ]) / 4.0


def gs_light(dish):
    light = {"light", "plain"}
    lightcook = {"steamed", "boiled", "grilled", "raw", "tempered"}
    return sum([
        1.0 if set(dish.richness) & light else 0.0,
        1.0 if set(dish.cooking_method) & lightcook else 0.0,
        1 - _cal_n(dish),
        1 - _heaviness_n(dish),
    ]) / 4.0


def gs_protein(dish):
    # proxy (diet+category) until dish_macro real grams in v2.
    protein_cat = {"dal_lentil", "kebab", "egg_dish"}
    proxy = 0.6 if (dish.diet in ("non_veg", "egg") or set(dish.dish_category) & protein_cat) else 0.2
    return sum([
        1.0 if dish.diet in ("non_veg", "egg") else 0.0,
        1.0 if set(dish.dish_category) & protein_cat else 0.0,
        proxy,
    ]) / 3.0


def gain_q15(dish, objective):
    cfg = CONFIG
    obj = objective or cfg.default_objective
    g = cfg.gamma(obj)
    kappa = cfg.kappa_v1                       # v1 pinned 1.0
    raw = 1 + kappa * (g["indulgence"] * gs_indulgence(dish)
                       + g["light"] * gs_light(dish)
                       + g["protein"] * gs_protein(dish))
    lo, hi = cfg.gain_bounds
    return max(lo, min(hi, raw))


def score(dish, theta, ctx, objective):
    """score = BASE × GAIN_Q15  (+ w_pref·S_pref[=0 v1]  − PENALTY[handled in assemble])."""
    return base(dish, theta, ctx) * gain_q15(dish, objective)


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
    for (zone, weather, name, verified, ds) in K.COMFORT_HERO_MAP:
        if weather == kb_weather and zone in keys:
            # resolve the KB hero NAME to the concrete golden dish name (exact match)
            heroes.add(K.COMFORT_HERO_TO_DISH.get(name, name))
    return heroes


def _prior_matches(dish, match_kind, match_value):
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
    # representative state for a zone (for local-palette m_palette). Uses KB STATE_ZONE inverse.
    rep = {"North": "Delhi", "South": "Tamil Nadu", "East": "West Bengal",
           "West": "Maharashtra", "Central": "Madhya Pradesh", "Northeast": "Assam"}
    return rep.get(zone, "Delhi")
