"""
ghar_re.pairing — Pairing guardrails + Assemble-7 (Core Spine §S4).

Hard gates + soft compat terms from pairing_rules.yaml. Cross-referenced against KB §N1
negative_priors (the in_spine=yes rows ARE what pairing_rules.yaml encodes — same rule, one
source). Standalone bypass, plate_score formula, greedy assemble-7 (no-duplicate guard +
discovery-dial cap), default carb attach (§S4.4 + KB §R2a).
"""
from ghar_re.config import CONFIG
from ghar_re import knowledge as K
from ghar_re import scoring as S


RICH_TAGS = {"buttery", "creamy", "ghee_rich", "coconut_rich"}


# ---------------------------------------------------------------------------
# §S4.2 pairing guardrails
# ---------------------------------------------------------------------------
def both_rich(d, l):
    # G1 (KB §N1 row 1): no two heavy/creamy gravies.
    return bool(set(d.richness) & RICH_TAGS) and bool(set(l.richness) & RICH_TAGS)


DALS = {"toor_dal", "moong_dal", "chana_dal", "urad_dal", "masoor_dal", "black_lentil", "kidney_beans", "chickpeas"}
COCONUT = {"coconut_fresh", "coconut_milk", "coconut_desiccated", "dried_coconut", "coconut_cream"}


def same_base(d, l):
    # G2 (KB §N1 row 2): not two tomato-onion / two coconut / same primary dal.
    # Proxy for the §1 ING base-cosine gate, using MAIN ingredients.
    dm, lm = set(d.main_ingredients), set(l.main_ingredients)
    # two coconut-dominant
    if (dm & COCONUT) and (lm & COCONUT):
        return True
    # same primary dal/pulse in both
    if (dm & DALS) and (dm & DALS) == (lm & DALS) and (lm & DALS):
        return True
    # both tomato-onion gravies (both carry tomato AND onion as mains)
    if {"tomato", "onion"} <= dm and {"tomato", "onion"} <= lm:
        return True
    return False


def cuisine_dist(d, l):
    # §1 hierarchical cuisine distance (distance_weights.yaml cuisine_hierarchy_distance).
    ch = CONFIG.distance["cuisine_hierarchy_distance"]
    if d.cuisine == l.cuisine:
        return ch["same_cuisine"]
    if d.cuisine_group and d.cuisine_group == l.cuisine_group:
        # same parent (e.g. chettinad<-tamil) is closer, but group-level here
        return ch["same_group"]
    if d.zone and d.zone == l.zone:
        return ch["same_broad_region"]
    return ch["else"]


def allowed(d, l):
    # HARD gates — pair not formed if any violated (pairing_rules.yaml hard_gates).
    hg = CONFIG.pairing["hard_gates"]
    if hg.get("not_both_rich") and both_rich(d, l):
        return False
    if hg.get("not_same_base") and same_base(d, l):
        return False
    if hg.get("cuisine_coherence") and cuisine_dist(d, l) > CONFIG.theta_region:
        return False
    # G3 (no two dry) is automatic: we only ever pair one DRY with one LIQUID.
    return True


def compat(d, l):
    # SOFT terms -> compat in [-1,+1] (pairing_rules.yaml soft_terms).
    b_balance = CONFIG.soft("b_balance")
    b_protein = CONFIG.soft("b_protein")
    p_sametaste = CONFIG.soft("p_sametaste")
    val = 0.0
    # G5 richness balance: one rich/medium + one light
    d_rich = bool(set(d.richness) & (RICH_TAGS | {"oily"}))
    l_rich = bool(set(l.richness) & (RICH_TAGS | {"oily"}))
    if d_rich != l_rich:
        val += b_balance
    # G6 protein-veg balance: pulse/protein liquid + veg dry (or vice versa)
    protein_cat = {"dal_lentil", "kebab", "egg_dish", "curry"}
    l_protein = bool(set(l.dish_category) & {"dal_lentil"}) or l.diet in ("non_veg", "egg")
    d_veg = "dry_sabzi" in d.dish_category
    if l_protein and d_veg:
        val += b_protein
    # mild penalty for identical dominant taste
    if set(d.primary_taste) & set(l.primary_taste):
        val -= p_sametaste
    return max(-1.0, min(1.0, val))


# ---------------------------------------------------------------------------
# §S4.3 plate score
# ---------------------------------------------------------------------------
def plate_score(plate, scores):
    lam = CONFIG.lambda_pair
    if plate["form"] == "pair":
        d, l = plate["dry"], plate["liquid"]
        return (scores[d.name] + scores[l.name]) * (1 + lam * compat(d, l))
    hero = plate["hero"]
    return scores[hero.name]


# ---------------------------------------------------------------------------
# §S4.4 + KB §R2a — default carb attach (editable). liquid-hero type first, else region.
# ---------------------------------------------------------------------------
def default_carb(plate, theta):
    if plate["form"] == "standalone":
        return None                            # standalone gets NO support
    # hero used for the by-type rule = the liquid hero (pair) or the single hero
    hero = plate.get("liquid") or plate.get("hero")
    name = hero.name.lower()
    # by liquid-hero type (strongest signal) — §S4.4 by-type table / KB §R2a
    if "rajma" in name or "sambar" in name or "rasam" in name or "kadhi" in name or "macher jhol" in name:
        return "Rice"
    if "chole" in name:
        return "Poori"                          # festive/specific pairing (chole-poori)
    # by region fallback (§S4.4 region table)
    region = theta["region"]["value"]
    home_state = theta["home_state"]["value"]
    rice_regions = {"South", "East"}
    if region in rice_regions:
        return "Rice"
    # KB §R2a ⚑ Gujarati/Rajasthani = Roti·Rice SPLIT — tie-break to Roti (same as North tie-break).
    return "Roti"                               # Punjab-North / Gujarat / Rajasthan / MH / Bihar -> roti


# ---------------------------------------------------------------------------
# §S4.6 Assemble-7 — greedy with no-duplicate guard + discovery-dial cap.
# ---------------------------------------------------------------------------
def build_plates(catalogue, theta, ctx, objective):
    """Return candidate plates (pairs/singles/standalones) with plate_score, from eligible dishes."""
    # score every eligible SHARED-hero dish
    elig = [d for d in catalogue if S.eligible(d, theta, ctx, shared_hero=True)]
    # pools by hero_role (snacks/accompaniments excluded from B/L/D plates; supports not scored)
    poolable = [d for d in elig if d.hero_role in ("dry", "liquid", "single", "standalone")
                and S.m_slot(d, ctx) > 0]
    scores = {d.name: S.score(d, theta, ctx, objective) for d in poolable}

    DRY = [d for d in poolable if d.hero_role == "dry"]
    LIQ = [d for d in poolable if d.hero_role == "liquid"]
    SINGLE = [d for d in poolable if d.hero_role == "single"]
    STANDALONE = [d for d in poolable if d.hero_role == "standalone"]

    plates = []
    for d in DRY:
        for l in LIQ:
            if allowed(d, l):
                p = dict(form="pair", dry=d, liquid=l, heroes={d.name, l.name})
                plates.append(p)
    for s in SINGLE:
        plates.append(dict(form="single", hero=s, heroes={s.name}))
    for t in STANDALONE:
        plates.append(dict(form="standalone", hero=t, heroes={t.name}))

    for p in plates:
        p["score"] = plate_score(p, scores)
        p["experimental"] = any(
            (getattr(h, "scope_tier", None) == "experimental")
            for h in _plate_dishes(p))
    return plates, scores


def assemble_7(catalogue, theta, ctx, objective, n=7):
    plates, scores = build_plates(catalogue, theta, ctx, objective)
    plates.sort(key=lambda p: p["score"], reverse=True)

    rho = theta["rho_disc"]["value"]
    disc_cap = int(rho * n)                     # v1 ~0 (familiarity-first)
    chosen, used_heroes, disc_used = [], set(), 0
    for p in plates:
        if len(chosen) >= n:
            break
        # (a) no-duplicate guard: skip if any hero already used
        if p["heroes"] & used_heroes:
            continue
        # (b) discovery dial cap
        if p["experimental"]:
            if disc_used >= disc_cap:
                continue
            disc_used += 1
        chosen.append(p)
        used_heroes |= p["heroes"]

    # attach support (§S4.4) to non-standalone plates
    for p in chosen:
        p["support"] = default_carb(p, theta)
        p["plate_calories"] = _plate_calories(p)
    # A6 optional calorie lens (plate-level) — drop over-target plates if a target is set
    if ctx.get("calorie_target"):
        chosen = [p for p in chosen if S.pass_calorie(p["plate_calories"], ctx)]
    return chosen


def _plate_dishes(p):
    if p["form"] == "pair":
        return [p["dry"], p["liquid"]]
    return [p["hero"]]


def _plate_calories(p):
    cals = sum((d.calories or 0) for d in _plate_dishes(p))
    return cals


def plate_label(p):
    if p["form"] == "pair":
        s = f"{p['dry'].name} + {p['liquid'].name}"
    else:
        s = p["hero"].name
    if p.get("support"):
        s += f"  (+ {p['support']})"
    return s
