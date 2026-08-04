"""
ghar_re.pairing — Pairing guardrails + Assemble-7 (Core Spine §S4).

Hard gates + soft compat terms from pairing_rules.yaml. Cross-referenced against KB §N1
negative_priors (the in_spine=yes rows ARE what pairing_rules.yaml encodes — same rule, one
source). Standalone bypass, plate_score formula, greedy assemble-7 (no-duplicate guard +
discovery-dial cap), default carb attach (§S4.4 + KB §R2a).
"""
from ghar_re_core.config import CONFIG
from ghar_re_core import scoring as S
from ghar_re_core import decision_log
from ghar_re_core import exploration
from ghar_re_core import similarity as SIM


RICH_TAGS = {"buttery", "creamy", "ghee_rich", "coconut_rich"}


# ---------------------------------------------------------------------------
# §S4.2 pairing guardrails
# ---------------------------------------------------------------------------
def both_rich(d, l):
    """True if BOTH the dry dish `d` and liquid dish `l` are rich/heavy (buttery, creamy,
    ghee-rich, or coconut-rich) — the pairing hard gate that stops two heavy gravies being
    served together (KB §N1 row 1)."""
    # G1 (KB §N1 row 1): no two heavy/creamy gravies.
    return bool(set(d.richness) & RICH_TAGS) and bool(set(l.richness) & RICH_TAGS)


def same_base(d, l, idf):
    """True if the dry dish `d` and liquid dish `l` share the same underlying base — the pairing
    hard gate that stops two too-similar-tasting dishes being served together (KB §N1 row 2).

    Core Spine FROZEN §S4 line 555 defines this exactly: "derived from the §1 ING block on base
    ingredients... Use cosine(base-ingredient vectors) > theta_base" (theta_base=0.6, line 641).
    `idf` is the catalogue-wide IDF-weighted vector built by `similarity.build_idf()` — required,
    not optional, since the cosine gate is meaningless without a real corpus behind it; callers
    build it once per catalogue via `build_plates()` below, not per pair.

    This REPLACES the previous set-intersection proxy (coconut/dal/tomato-onion special-casing)
    that stood in for this gate — the proxy is gone, not layered underneath; the real formula
    governs the gate entirely now, per Founder direction (2026-08 RE compliance review)."""
    # G2 (KB §N1 row 2): base-ingredient cosine gate, exactly per Core Spine FROZEN §S4 line 555.
    va = {ing: idf[ing] for ing in set(d.main_ingredients) if ing in idf}
    vb = {ing: idf[ing] for ing in set(l.main_ingredients) if ing in idf}
    return SIM.cosine(va, vb) > CONFIG.theta_base


def cuisine_dist(d, l):
    """How far apart two dishes' cuisines are, on the hierarchical scale from
    distance_weights.yaml: 0 (same cuisine) < same cuisine_group < same broad zone < else.
    Used by allowed() to decide whether a cross-cuisine pair is coherent enough to serve."""
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


def allowed(d, l, idf):
    """Whether a dry dish `d` and liquid dish `l` may be formed into a pair at all. Checks every
    configured hard gate (not-both-rich, not-same-base, cuisine-coherence) — the pair is only
    ever built if ALL of them pass; any single violation rejects the pair outright. `idf` is the
    catalogue-wide IDF vector required by the same_base() cosine gate (see same_base's docstring)."""
    # HARD gates — pair not formed if any violated (pairing_rules.yaml hard_gates).
    hg = CONFIG.pairing["hard_gates"]
    if hg.get("not_both_rich") and both_rich(d, l):
        return False
    if hg.get("not_same_base") and same_base(d, l, idf):
        return False
    if hg.get("cuisine_coherence") and cuisine_dist(d, l) > CONFIG.theta_region:
        return False
    # G3 (no two dry) is automatic: we only ever pair one DRY with one LIQUID.
    return True


def compat(d, l):
    """How well-matched an ALREADY-ALLOWED dry+liquid pair is, as a single number from -1 to +1:
    positive for good richness balance and protein-veg balance, negative when both dishes share
    the same dominant taste. Used to nudge (not gate) the pair's combined plate_score."""
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
    # FIXED (Founder-ratified 2026-08-04, reports/re_audit/10_remaining_work.md #6): l_protein
    # previously only tested {"dal_lentil"}, silently excluding kebab/egg_dish/curry liquids from
    # the b_protein bonus unless their diet also happened to be non_veg/egg. Widened to the full
    # protein_cat set below, per the fix this comment block previously described but deliberately
    # deferred. CHANGES SCORING OUTPUT for affected plates — golden-master files were regenerated
    # in the same change (`python -m ghar_re_core.tests.test_golden_master --update`), diff
    # reviewed, not silently absorbed.
    protein_cat = {"dal_lentil", "kebab", "egg_dish", "curry"}
    l_protein = bool(set(l.dish_category) & protein_cat) or l.diet in ("non_veg", "egg")
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
    """The final score for one candidate plate: for a dry+liquid pair, the two dishes' individual
    scores summed and adjusted by their compat() bonus/penalty; for a single/standalone plate,
    just that one dish's score. This is the number assemble_7 sorts plates by."""
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
    """Which carb/support ('Rice', 'Roti', 'Poori', or None) should be attached to a served
    plate, decided first by the liquid hero's own type (e.g. sambar -> Rice) and falling back to
    the household's region. Standalone plates (already a complete meal) get no support."""
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


def assemble_7(catalogue, theta, ctx, objective, n=7, household_label=None, with_trace=False):
    """The final "which 7 plates does this household get" decision (§S4.6). Greedily walks every
    candidate plate best-score-first, skipping any plate that reuses an already-served hero dish
    (no-duplicate guard) and capping how many 'experimental'/discovery plates can be served
    (discovery-dial cap, driven by the household's rho_disc). Attaches a default carb/support to
    each chosen plate, optionally drops plates over a calorie target, logs the decision (see
    decision_log module), and returns the final list of plates actually served — the household's
    dish pool for this context. `n` defaults to 7 (one plate for each of the 7 configured slots);
    `household_label` is passed through only for logging.

    `with_trace=True` additionally returns (chosen, decision_trace) — the same funnel/winners/
    alternatives payload log_assemble7_decision would log, built unconditionally via
    decision_log.build_decision_trace() regardless of logger configuration, for callers (e.g.
    pipeline.recommend()) that want to persist or return it rather than only log it."""
    funnel = S.eligibility_funnel(catalogue, theta, ctx, shared_hero=True)
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

    # Phase 2 selection-stage epsilon-greedy class-level exploration (ghar_re_core.exploration) —
    # runs AFTER the greedy no-duplicate-guard ranking/selection above, on its already-chosen
    # output. NOT a ScoringModule (no dish score is ever touched); a total no-op whenever
    # CONFIG.bandit_epsilon is 0 (its code-level safety default, and the value implied for every
    # golden-master fixture, which sets no dish_feedback_counts/_rng_seed).
    chosen, exploration_trace = exploration.epsilon_greedy_select(chosen, plates, ctx)

    # attach support (§S4.4) to non-standalone plates
    for p in chosen:
        p["support"] = default_carb(p, theta)
        p["plate_calories"] = _plate_calories(p)
    # A6 optional calorie lens (plate-level) — drop over-target plates if a target is set
    if ctx.get("calorie_target"):
        chosen = [p for p in chosen if S.pass_calorie(p["plate_calories"], ctx)]

    # Decision logging only (see decision_log module docstring): reads the already-decided
    # `plates`/`chosen`, never influences them. A no-op unless a handler is attached to the
    # "ghar_re_core.decision" logger.
    decision_log.log_assemble7_decision(household_label, ctx, objective, plates, chosen, funnel)

    if with_trace:
        trace = decision_log.build_decision_trace(household_label, ctx, objective, plates, chosen, funnel)
        # Additive-only: exploration_trace is empty ([]) whenever exploration didn't fire (the
        # golden-master/every-live-household case), so this never changes existing trace shape
        # for a no-op call — it only ever ADDS a key, never removes/renames one.
        trace["exploration_trace"] = exploration_trace
        return chosen, trace
    return chosen


def _plate_dishes(p):
    """The list of underlying Dish objects that make up plate `p` — both dishes for a pair,
    or just the one hero dish for a single/standalone."""
    if p["form"] == "pair":
        return [p["dry"], p["liquid"]]
    return [p["hero"]]


def _plate_calories(p):
    """Total calories for plate `p`, summing every dish it contains (treating a missing calorie
    value as 0 rather than failing)."""
    cals = sum((d.calories or 0) for d in _plate_dishes(p))
    return cals


def plate_label(p):
    """A short human-readable name for plate `p` (e.g. 'Rajma + Steamed Rice  (+ Rice)') used in
    the CLI demo output and decision-log entries — never used in scoring."""
    if p["form"] == "pair":
        s = f"{p['dry'].name} + {p['liquid'].name}"
    else:
        s = p["hero"].name
    if p.get("support"):
        s += f"  (+ {p['support']})"
    return s
