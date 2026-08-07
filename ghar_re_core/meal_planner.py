"""
ghar_re.meal_planner — WP-18 onboarding→plan→dish surfaces.

Builds the user-facing planning artefacts on top of the existing scoring/cohort stack, without
touching the Core Spine math. Everything here RANKS or GROUPS dishes/classes the engine already
scores; nothing new decides eligibility (scoring.eligible stays the sole filter) or invents a score.

Four surfaces (the WP-18 flow):
  1. cold_start_top15(hh)          — after onboarding: 15 diverse, top-scoring dishes to like/seed
  2. slot_options(hh, slot)        — a slot's 4–5 best dish options
  3. weekly_class_plan(hh)         — 7 days × slots, each with the top-3 meal CLASSES to choose from
  4. dishes_for_class(hh, slot, c) — RECONCILIATION: only dishes of the chosen class for that day

The reconciliation contract (4) is the guarantee the Founder asked for: once a day's meal CLASS is
finalized (from 3), the dishes shown that day come ONLY from that class — dish_to_class_code(d) == c —
ranked by the same score. Class plan and dish list can never disagree.

All functions take a raw household dict (fixtures.HOUSEHOLDS shape), derive θ once, and return
plain JSON-serialisable dicts so the FastAPI layer can hand them straight back.
"""

import datetime
import math
import random

from ghar_re_core import scoring as S
from ghar_re_core import cohort_plan as CP
from ghar_re_core import knowledge as K
from ghar_re_core.catalogue import Catalogue
from ghar_re_core.config import CONFIG
from ghar_re_core.derivation import derive_theta
from ghar_re_core.pipeline import make_context

MAIN_SLOTS = ("breakfast", "lunch", "dinner")
WEEK = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
_CLASS_NAMES = None
MMR_LAMBDA = 0.75
_RICH_TAGS = {"buttery", "creamy", "ghee_rich", "coconut_rich", "oily"}


def _class_names():
    """meal_class_code -> human class_name, cached (for labelling the weekly plan)."""
    global _CLASS_NAMES
    if _CLASS_NAMES is None:
        import csv

        _CLASS_NAMES = {}
        with open(CP._src_path("meal_class_master.csv"), newline="") as f:
            for r in csv.DictReader(f):
                _CLASS_NAMES[r["meal_class_code"]] = r["class_name"]
    return _CLASS_NAMES


def _dish_view(d, theta, ctx, objective, score=None, label_class=None):
    """The JSON shape the app needs for one dish/meal card. image_url + recipe are attached by the
    service layer (Cloudinary / recipe store) — kept out of core so the math package stays data-only.
    `label_class`: when a dish is surfaced under a specific reconciled class (multi-membership — the
    dish belongs to several classes), label it with THAT class rather than its primary, since that is
    the class the user finalized it under. Falls back to the dish's primary class otherwise."""
    code = label_class or K.dish_to_class_code(d.name)
    explanation = S.explain_dish(d, theta, ctx, objective)
    return {
        "name": d.name,
        "cuisine": d.cuisine,
        "diet": d.diet,
        "meal_class_code": code,
        "meal_class_name": _class_names().get(code),
        "spice_level": d.spice_level,
        "heaviness": d.heaviness,
        "total_mins": d.total_mins,
        "score": round(S.score(d, theta, ctx, objective) if score is None else score, 4),
        "explanation": {
            "base_total": explanation["base_total"],
            "q15_contribution": explanation["q15_contribution"],
            "weather_contribution": explanation["weather_contribution"],
            "top_contributors": sorted(
                explanation["base_contributors"],
                key=lambda item: abs(item["weighted"]),
                reverse=True,
            )[:3],
        },
    }


def _candidate_lineage(d, score, slot):
    """Private core→Edge candidate evidence; stripped before any client response."""
    return {
        "name": d.name,
        "score": round(float(score), 6),
        "slot": slot,
        "meal_class_code": K.dish_to_class_code(d.name),
    }


def _ranked(cat, theta, ctx, objective, predicate=None, preference_by_dish=None):
    """(score, dish) for every slot-appropriate, eligible dish, best first. `predicate` further
    restricts the pool (e.g. to one meal class) without ever loosening eligibility."""
    out = []
    for d in cat:
        if S.m_slot(d, ctx) == 0.0:  # not valid for this slot
            continue
        if not S.eligible(d, theta, ctx):  # A1–A5 correctness/observance filters
            continue
        if predicate is not None and not predicate(d):
            continue
        # Online affinities are deliberately a bounded re-rank term, not a hard filter and not a
        # mutation of the frozen Core Spine. Explicit Never/Not-Today intent is handled separately
        # through exclude_dish_names before this function is called.
        affinity = float((preference_by_dish or {}).get(d.name, 0.0) or 0.0)
        affinity = max(-1.0, min(1.0, affinity))
        out.append((S.score(d, theta, ctx, objective) + 0.35 * affinity, d))
    out.sort(key=lambda x: -x[0])
    return out


# Beginner-cook time budget (minutes) for the soft re-rank below. Deliberately NOT a
# base_weights.yaml W_k or a new BASE-formula term: the FROZEN Core Spine's §S2 PART B formula
# (docs/architecture/ghar-re/ghar_re_v1_0_core_spine_FROZEN.md, "B9. Weight defaults") is closed at
# exactly 7 named W_k terms + PRIOR[zone][slot] — it does not include an effort/time term despite
# base_weights.yaml's orphaned `W_EFFORT: 0.40` and derivation.py's unconsumed `effort_ceiling`
# theta field (neither is read anywhere in scoring.py; confirmed by grep). Extending BASE itself
# to consume either would silently go beyond what's actually frozen/ratified, so this stays
# entirely a meal_planner.py RANKING adjustment instead (this module's own charter: "RANKS or
# GROUPS dishes the engine already scores... nothing new decides eligibility or invents a score" —
# scores are never touched, only pick ORDER, via a stable partition, same spirit as _diversify's
# own class/cuisine caps below). Founder should revisit whether W_EFFORT/effort_ceiling ought to be
# formally added to a future Core Spine revision instead of staying dormant config.
_BEGINNER_TIME_BUDGET_MINS = 45


def _apply_cook_capability_bias(ranked, cook_capability):
    """Stable-partition an already-`_ranked()` (score, dish) list so a 'beginner' household sees
    dishes within `_BEGINNER_TIME_BUDGET_MINS` ranked ahead of longer ones, WITHOUT changing any
    dish's score or excluding anything — a beginner can still see an ambitious dish, just later.
    No-op (returns `ranked` unchanged) for 'intermediate'/'advanced'/unknown cook_capability, or
    when a dish has no total_mins to compare (never demoted for missing data)."""
    if cook_capability != "beginner":
        return ranked
    within_budget = [
        pair
        for pair in ranked
        if pair[1].total_mins is None or pair[1].total_mins <= _BEGINNER_TIME_BUDGET_MINS
    ]
    over_budget = [
        pair
        for pair in ranked
        if pair[1].total_mins is not None and pair[1].total_mins > _BEGINNER_TIME_BUDGET_MINS
    ]
    return within_budget + over_budget


def _adaptive_diversity_policy(novelty_budget=0.15, richness_debt=0.0):
    """Bounded post-eligibility policy derived only from persisted observed cadence."""
    novelty = max(0.0, min(1.0, float(novelty_budget or 0.0)))
    richness = max(0.0, min(1.0, float(richness_debt or 0.0)))
    relevance_lambda = max(0.50, min(0.85, MMR_LAMBDA - 0.40 * (novelty - 0.15)))
    max_rich_ratio = max(0.25, 0.50 - min(0.25, richness))
    return relevance_lambda, max_rich_ratio


def _diversify(ranked, n, per_class=2, per_cuisine=3, rng=None, richness_debt=0.0):
    """Take the top n dishes while capping repeats per meal class and per cuisine, so the surface
    isn't 15 near-identical dals. Falls back to filling from the remainder if the caps are too
    tight to reach n.

    `rng`: when given (household-seeded, see cold_start_top15), applies CONFIG.bandit_epsilon
    exploration — the same already-Founder-approved rate ghar_re_core.exploration uses for the
    weekly-pairing swap (bandit_weights.yaml, code-level safety default 0.0) — so two households
    that land on an identical theta (e.g. same cohort answers) don't always converge on the exact
    same top-n: at each candidate, with probability epsilon, the pick is deferred to let a later
    candidate have a turn, rather than always taking the next-best greedy option. Deterministic
    per household (stable seed) and a strict no-op when rng is None, so every existing caller
    (slot_options/dishes_for_class, and any cold_start_top15 call with no household_id) keeps its
    exact prior greedy behaviour — this never touches score or eligibility, only pick order."""
    epsilon = CONFIG.bandit_epsilon if rng is not None else 0.0
    picked, seen_class, seen_cuisine = [], {}, {}
    _, max_rich_ratio = _adaptive_diversity_policy(richness_debt=richness_debt)
    max_rich = max(1, math.ceil(n * max_rich_ratio))
    rich_count = 0
    soup_count = 0
    deferred = []
    for score, d in ranked:
        code = K.dish_to_class_code(d.name)
        if seen_class.get(code, 0) >= per_class:
            continue
        if seen_cuisine.get(d.cuisine, 0) >= per_cuisine:
            continue
        if _dish_is_rich(d) and rich_count >= max_rich:
            continue
        if _dish_is_soup(d) and soup_count >= 1:
            continue
        if epsilon > 0 and rng.random() < epsilon:
            deferred.append((score, d))  # exploration: give a later candidate its turn
            continue
        picked.append((score, d))
        seen_class[code] = seen_class.get(code, 0) + 1
        seen_cuisine[d.cuisine] = seen_cuisine.get(d.cuisine, 0) + 1
        rich_count += int(_dish_is_rich(d))
        soup_count += int(_dish_is_soup(d))
        if len(picked) >= n:
            return picked
    # Top up while preserving visible richness/soup limits. Relax only if the eligible catalogue
    # cannot fill the requested count, matching _mmr_rerank's safety-first fallback behavior.
    if len(picked) < n:
        chosen = {id(d) for _, d in picked}
        for score, d in deferred + ranked:
            if (
                id(d) not in chosen
                and (not _dish_is_rich(d) or rich_count < max_rich)
                and (not _dish_is_soup(d) or soup_count < 1)
            ):
                picked.append((score, d))
                chosen.add(id(d))
                rich_count += int(_dish_is_rich(d))
                soup_count += int(_dish_is_soup(d))
                if len(picked) >= n:
                    break
        if len(picked) < n:
            for score, d in deferred + ranked:
                if id(d) not in chosen:
                    picked.append((score, d))
                    chosen.add(id(d))
                    if len(picked) >= n:
                        break
    return picked[:n]


def _dish_similarity(left, right):
    """Bounded content similarity for MMR: class, cuisine and main-ingredient overlap."""
    same_class = 1.0 if K.dish_to_class_code(left.name) == K.dish_to_class_code(right.name) else 0.0
    same_cuisine = 1.0 if left.cuisine == right.cuisine else 0.0
    left_ingredients, right_ingredients = set(left.main_ingredients), set(right.main_ingredients)
    union = left_ingredients | right_ingredients
    ingredient_overlap = len(left_ingredients & right_ingredients) / len(union) if union else 0.0
    return 0.5 * same_class + 0.3 * same_cuisine + 0.2 * ingredient_overlap


def _dish_is_rich(dish):
    return bool(set(dish.richness or []) & _RICH_TAGS) or (dish.heaviness or 0) >= 3


def _dish_is_soup(dish):
    return "soup" in dish.name.casefold() or "soup" in set(dish.dish_category or [])


def _bounded_history_counts(value):
    """Normalize untrusted contract maps without allowing negative or unbounded pressure."""
    if not isinstance(value, dict):
        return {}
    normalized = {}
    for raw_key, raw_count in list(value.items())[:100]:
        key = str(raw_key).strip()
        try:
            count = int(raw_count)
        except (TypeError, ValueError):
            continue
        if key and count > 0:
            normalized[key] = min(1000, count)
    return normalized


def _historical_similarity(dish, recent_class_counts, recent_cuisine_counts):
    """Bounded exposure similarity aligned with the persisted seven-day variety caps."""
    class_code = K.dish_to_class_code(dish.name)
    class_count = recent_class_counts.get(class_code, 0) if class_code else 0
    cuisine_count = recent_cuisine_counts.get(dish.cuisine.casefold(), 0)
    return max(min(1.0, class_count / 3.0), min(1.0, cuisine_count / 2.0))


def _mmr_rerank(
    ranked,
    n,
    diversity_lambda=None,
    novelty_budget=0.15,
    richness_debt=0.0,
    recent_class_counts=None,
    recent_cuisine_counts=None,
):
    """MMR reranking with deterministic current-slate and seven-day diversity constraints."""
    if not ranked or n <= 0:
        return []
    adaptive_lambda, max_rich_ratio = _adaptive_diversity_policy(
        novelty_budget=novelty_budget, richness_debt=richness_debt
    )
    diversity_lambda = adaptive_lambda if diversity_lambda is None else diversity_lambda
    recent_class_counts = _bounded_history_counts(recent_class_counts)
    recent_cuisine_counts = {
        key.casefold(): count
        for key, count in _bounded_history_counts(recent_cuisine_counts).items()
    }
    candidates = list(ranked)
    scores = [score for score, _ in candidates]
    low, high = min(scores), max(scores)

    def relevance(score):
        return (score - low) / (high - low) if high > low else 1.0

    if recent_class_counts or recent_cuisine_counts:
        first_index = max(
            range(len(candidates)),
            key=lambda index: (
                diversity_lambda * relevance(candidates[index][0])
                - (1.0 - diversity_lambda)
                * _historical_similarity(
                    candidates[index][1], recent_class_counts, recent_cuisine_counts
                ),
                candidates[index][0],
                candidates[index][1].name,
            ),
        )
        selected = [candidates.pop(first_index)]
    else:
        # Preserve the pre-history path byte-for-byte: the top relevance candidate leads.
        selected = [candidates.pop(0)]
    while candidates and len(selected) < n:
        next_size = len(selected) + 1
        rich_count = sum(_dish_is_rich(dish) for _, dish in selected)
        soup_count = sum(_dish_is_soup(dish) for _, dish in selected)
        allowed = [
            index
            for index, (_, dish) in enumerate(candidates)
            if (
                not _dish_is_rich(dish)
                or rich_count < max(1, math.ceil(next_size * max_rich_ratio))
            )
            and (not _dish_is_soup(dish) or soup_count < 1)
        ]
        # Relax only when the safe/eligible catalogue cannot fill the requested response.
        candidate_indices = allowed or range(len(candidates))
        best_index = max(
            candidate_indices,
            key=lambda index: (
                diversity_lambda * relevance(candidates[index][0])
                - (1.0 - diversity_lambda)
                * max(
                    _historical_similarity(
                        candidates[index][1], recent_class_counts, recent_cuisine_counts
                    ),
                    max(
                        _dish_similarity(candidates[index][1], chosen[1]) for chosen in selected
                    ),
                ),
                candidates[index][0],
                candidates[index][1].name,
            ),
        )
        selected.append(candidates.pop(best_index))
    if len(selected) < n:
        chosen = {dish.name for _, dish in selected}
        selected.extend(pair for pair in ranked if pair[1].name not in chosen)
    return selected[:n]


def _theta_obj(household):
    """Derive θ + resolve the household's objective once."""
    theta = derive_theta(household)
    objective = household.get("q15_objective") or CONFIG.default_objective
    return theta, objective


def cold_start_top15(
    household,
    catalogue=None,
    n=15,
    weekday="Monday",
    household_id=None,
    variety_salt=None,
    exclude_dish_names=None,
    preference_by_dish=None,
    richness_debt=0.0,
):
    """Surface 1 — the post-onboarding preference primer: the n (default 15) top-scoring, DIVERSE
    dishes across breakfast/lunch/dinner, for the user to like and seed their taste profile. Diverse
    = capped per meal class and per cuisine so it spans the plan, not one class 15 times.

    `household_id`: when given, seeds a household-stable RNG so `_diversify` applies
    CONFIG.bandit_epsilon exploration (see its docstring) — two households with identical answers
    (same cohort, same theta) get varied top-n sets instead of always converging on the exact same
    15 dishes. Omitted (None) => no exploration, exact prior deterministic behaviour (existing
    tests/fixtures that don't pass household_id are unaffected).

    `variety_salt`: mixed into the same seed alongside household_id so a GIVEN household's own
    list also varies — e.g. a fresh top-15 each day the user revisits cold-start, instead of the
    exact same list forever (the Founder-reported "doesn't feel dynamic" gap: seeding purely by
    household_id made the swap pattern replay identically on every repeat view, since a real
    household's id never changes). Defaults to today's UTC date (YYYY-MM-DD) when omitted, so
    the default behaviour is "changes once a day," not "changes every request" — the underlying
    ranking is theta/score-derived and untouched either way; only which already-eligible,
    already-scored dish the exploration tie-break defers to shift. Pass an explicit value (e.g.
    in tests) for a reproducible seed."""
    cat = catalogue or Catalogue()
    theta, objective = _theta_obj(household)
    excluded = set(exclude_dish_names or [])
    if household_id is None:
        rng = None
    else:
        salt = variety_salt if variety_salt is not None else datetime.date.today().isoformat()
        rng = random.Random(f"{household_id}:{salt}")
    # pool the best of each main slot, then diversify across the merged pool
    pool = {}
    for slot in MAIN_SLOTS:
        ctx = make_context(slot=slot, weekday=weekday)
        for score, d in _ranked(
            cat,
            theta,
            ctx,
            objective,
            predicate=lambda dish: dish.name not in excluded,
            preference_by_dish=preference_by_dish,
        )[:20]:
            prev = pool.get(d.name)
            if prev is None or score > prev[0]:
                pool[d.name] = (score, d, slot, ctx)
    ranked = sorted(((v[0], v[1]) for v in pool.values()), key=lambda x: -x[0])
    ranked = _apply_cook_capability_bias(ranked, household.get("cook_capability"))
    picked = _diversify(ranked, n, rng=rng, richness_debt=richness_debt)
    slot_of = {v[1].name: (v[2], v[3]) for v in pool.values()}
    return {
        "household": household.get("label"),
        "kind": "cold_start_top_dishes",
        "count": len(picked),
        "dishes": [
            dict(
                _dish_view(d, theta, slot_of[d.name][1], objective, score), slot=slot_of[d.name][0]
            )
            for score, d in picked
        ],
        "_candidate_lineage": [
            _candidate_lineage(d, score, slot_of[d.name][0]) for score, d in ranked
        ],
    }


def slot_options(
    household,
    slot,
    catalogue=None,
    n=8,
    weekday="Monday",
    class_code=None,
    context=None,
    exclude_dish_names=None,
    preference_by_dish=None,
):
    """Surface 2 — a slot's 4–5 best meal options. If `class_code` is given, this is also the
    reconciliation path (surface 4): only dishes of that class are considered."""
    cat = catalogue or Catalogue()
    theta, objective = _theta_obj(household)
    context = context or {}
    weather = context.get("weather") or {}
    ctx = make_context(
        slot=slot,
        weekday=weekday,
        season=context.get("season", "transitional"),
        weather_condition=weather.get("weather_condition") or weather.get("condition"),
        temp_c=weather.get("temp_c"),
        is_raining=bool(weather.get("is_raining", False)),
        active_modes=context.get("active_modes") or [],
        calorie_target=context.get("calorie_target"),
    )
    ctx["interaction_count"] = max(0, int(context.get("interaction_count", 0) or 0))
    ctx["novelty_budget"] = max(0.0, min(1.0, float(context.get("novelty_budget", 0.15) or 0)))
    ctx["richness_debt"] = max(0.0, min(1.0, float(context.get("richness_debt", 0) or 0)))
    ctx["recent_class_counts"] = context.get("recent_class_counts") or {}
    ctx["recent_cuisine_counts"] = context.get("recent_cuisine_counts") or {}
    excluded = set(exclude_dish_names or [])

    # multi-membership (WP-17.1): a dish is eligible for a class if that class is ANY of its classes
    # (primary or secondary), not only its single primary — so behavioural DN_ dinner classes reconcile
    # to the dishes they overlap with the LD_ pool, instead of falling back to regional plates.
    def pred(d):
        if d.name in excluded:
            return False
        return class_code in K.dish_to_class_codes(d.name) if class_code else True

    ranked = _ranked(
        cat, theta, ctx, objective, predicate=pred, preference_by_dish=preference_by_dish
    )
    picked = (
        ranked[:n]
        if class_code
        else _mmr_rerank(
            ranked,
            n,
            novelty_budget=ctx["novelty_budget"],
            richness_debt=ctx["richness_debt"],
            recent_class_counts=ctx["recent_class_counts"],
            recent_cuisine_counts=ctx["recent_cuisine_counts"],
        )
    )
    return {
        "household": household.get("label"),
        "slot": slot,
        "weekday": weekday,
        "class_code": class_code,
        "count": len(picked),
        "options": [
            _dish_view(d, theta, ctx, objective, score, label_class=class_code)
            for score, d in picked
        ],
        "_candidate_lineage": [_candidate_lineage(d, score, slot) for score, d in ranked],
    }


def dishes_for_class(
    household,
    slot,
    class_code,
    catalogue=None,
    n=8,
    weekday="Monday",
    context=None,
    exclude_dish_names=None,
    preference_by_dish=None,
):
    """Surface 4 — RECONCILIATION. Given a day's finalized meal CLASS, return only the eligible
    dishes of that class for the slot, best-scored first. Thin wrapper over slot_options so the
    class-filter path can never diverge from the option-ranking path."""
    return dict(
        slot_options(
            household,
            slot,
            catalogue=catalogue,
            n=n,
            weekday=weekday,
            class_code=class_code,
            context=context,
            exclude_dish_names=exclude_dish_names,
            preference_by_dish=preference_by_dish,
        ),
        kind="reconciled_class_dishes",
    )


def search_dishes(
    household,
    catalogue=None,
    query="",
    cuisine=None,
    diet=None,
    slot=None,
    max_total_mins=None,
    limit=30,
    weekday="Monday",
    context=None,
):
    """Safety-aware catalogue search using the same hard eligibility rules as recommendations.

    Search is intentionally performed over the startup-loaded in-memory catalogue: the production
    catalogue is small enough for a bounded scan, and this avoids a second database-backed safety
    implementation drifting from `eligible()`. Results are relevance-first (name prefix/name
    substring/cuisine), then recommendation score, with deterministic ordering.
    """
    cat = catalogue or Catalogue()
    theta, objective = _theta_obj(household)
    context = context or {}
    weather = context.get("weather") or {}
    ctx = make_context(
        slot=slot or "dinner",
        weekday=weekday,
        season=context.get("season", "transitional"),
        weather_condition=weather.get("weather_condition") or weather.get("condition"),
        temp_c=weather.get("temp_c"),
        is_raining=bool(weather.get("is_raining", False)),
    )
    needle = str(query or "").strip().casefold()
    cuisine_filter = str(cuisine or "").strip().casefold()
    diet_filter = str(diet or "").strip().casefold()
    matches = []
    for dish in cat:
        if not S.eligible(dish, theta, ctx):
            continue
        if slot and S.m_slot(dish, ctx) == 0.0:
            continue
        if cuisine_filter and dish.cuisine.casefold() != cuisine_filter:
            continue
        if diet_filter and dish.diet.casefold() != diet_filter:
            continue
        if max_total_mins is not None and (
            dish.total_mins is None or dish.total_mins > int(max_total_mins)
        ):
            continue
        haystack = f"{dish.name} {dish.cuisine} {K.dish_to_class_code(dish.name) or ''}".casefold()
        if needle and needle not in haystack:
            continue
        relevance = 3 if dish.name.casefold().startswith(needle) and needle else 0
        relevance += 2 if needle and needle in dish.name.casefold() else 0
        relevance += 1 if needle and needle in dish.cuisine.casefold() else 0
        score = S.score(dish, theta, ctx, objective)
        matches.append((relevance, score, dish.name, dish))
    matches.sort(key=lambda item: (-item[0], -item[1], item[2]))
    selected = matches[: max(1, min(int(limit), 50))]
    return {
        "kind": "dish_search",
        "query": query,
        "count": len(selected),
        "options": [
            _dish_view(dish, theta, ctx, objective, score) for _, score, _, dish in selected
        ],
        "_candidate_lineage": [
            _candidate_lineage(dish, score, slot or "dinner") for _, score, _, dish in matches
        ],
    }


_RECENT_WINDOW = 2  # days a class is held back from re-topping the same slot, once it has led
_MAX_WEEKLY_LEADS_PER_SLOT = 2


def weekly_class_plan(
    household,
    top_classes=3,
    catalogue=None,
    preference_by_dish=None,
    preference_by_direct_class=None,
    preference_by_projected_class=None,
):
    """Surface 3 — the weekly class plan: for each day × main slot, the top-`top_classes` meal
    CLASSES (from the compositional cohort plan) for the user to select and finalize. Selecting a
    class then drives dishes_for_class (surface 4) for that day/slot. Also reports, per class, how
    many catalogue dishes back it — so the UI can avoid finalizing a class with no dishes (the
    thin-DN_-class coverage issue surfaced for test_17).

    The whole week is computed in this one pass, so two cross-day rules can be enforced in-process
    with no persisted history: (1) a class that led a slot on a recent day is held back from leading
    it again for `_RECENT_WINDOW` days (falls back to it only if the slot's pool is that thin), so
    the same top-1 class/dish doesn't repeat day after day; (2) each weekend day (Sat/Sun) is checked
    for at least one gravy-rich/special lunch-or-dinner class — if the household's own plan doesn't
    already lead with one, the best diet-compatible, dish-backed special class is promoted to the
    front of that slot's list, so a holiday doesn't default to a routine weekday plate."""
    cat = catalogue or Catalogue()
    theta, _ = _theta_obj(household)
    backing = _class_dish_counts(cat)
    dish_projected_affinity = (
        _bounded_class_affinity(preference_by_projected_class)
        if preference_by_projected_class is not None
        else _class_preference_affinity(cat, preference_by_dish)
    )
    direct_class_affinity = _bounded_class_affinity(preference_by_direct_class)
    meta = CP._class_meta()
    days = []
    recent_leaders = {
        slot: [] for slot in MAIN_SLOTS
    }  # slot -> class codes that led on recent days
    leader_counts = {slot: {} for slot in MAIN_SLOTS}
    for day in WEEK:
        slots = {}
        full_plans = {}
        for slot in MAIN_SLOTS:
            ctx = make_context(slot=slot, weekday=day)
            plan = CP.class_plan(theta, ctx)
            full_plans[slot] = plan
            # A direct class action is more authoritative than a class inferred from dish
            # feedback. When both exist, direct evidence owns 75% of the same bounded 0.35
            # preference term; with only projected evidence, the previous behaviour is preserved.
            class_affinity = {
                code: _combined_class_affinity(
                    code, direct_class_affinity, dish_projected_affinity
                )[0]
                for code in plan
            }
            ranked = sorted(
                plan.items(),
                key=lambda item: -(item[1] + 0.35 * class_affinity.get(item[0], 0.0)),
            )
            candidates = []
            for code, weight in ranked:
                if backing.get(code, 0) == 0:  # never offer a class with no dishes to reconcile to
                    continue
                _, direct_share, projected_share = _combined_class_affinity(
                    code, direct_class_affinity, dish_projected_affinity
                )
                candidates.append(
                    {
                        "class_code": code,
                        "class_name": _class_names().get(code, code),
                        "plan_weight": round(weight, 4),
                        "preference_contribution": round(0.35 * class_affinity.get(code, 0.0), 4),
                        "direct_class_preference_contribution": round(0.35 * direct_share, 4),
                        "dish_projected_preference_contribution": round(
                            0.35 * projected_share, 4
                        ),
                        "dish_count": backing.get(code, 0),
                    }
                )
            held_back = set(recent_leaders[slot])
            leader = next(
                (
                    item
                    for item in candidates
                    if item["class_code"] not in held_back
                    and leader_counts[slot].get(item["class_code"], 0) < _MAX_WEEKLY_LEADS_PER_SLOT
                ),
                None,
            )
            if leader is None and candidates:
                # A thin pool can make the two-day holdback impossible. Prefer the least-recent,
                # least-used candidate rather than blindly repeating the highest-score leader.
                leader = max(
                    enumerate(candidates),
                    key=lambda pair: (
                        recent_leaders[slot].index(pair[1]["class_code"])
                        if pair[1]["class_code"] in recent_leaders[slot]
                        else _RECENT_WINDOW + 1,
                        -leader_counts[slot].get(pair[1]["class_code"], 0),
                        -pair[0],
                    ),
                )[1]
            top = [] if leader is None else [leader]
            top.extend(item for item in candidates if item is not leader)
            top = top[:top_classes]
            slots[slot] = top
        if day in ("Saturday", "Sunday"):
            _ensure_weekend_special(
                slots,
                full_plans,
                backing,
                meta,
                top_classes,
                recent_leaders,
                leader_counts,
            )
        # Record leaders only after all repair rules have run. Previously the weekend promotion
        # happened after this bookkeeping, so Sunday's repetition check saw the displaced class
        # rather than the special class that was actually served at rank one.
        for slot in MAIN_SLOTS:
            if not slots[slot]:
                continue
            code = slots[slot][0]["class_code"]
            recent_leaders[slot] = ([code] + recent_leaders[slot])[:_RECENT_WINDOW]
            leader_counts[slot][code] = leader_counts[slot].get(code, 0) + 1
        days.append({"weekday": day, "slots": slots})
    return {
        "household": household.get("label"),
        "kind": "weekly_class_plan",
        "days": days,
        "constraint_report": _weekly_constraint_report(days),
    }


def _weekly_constraint_report(days):
    """Describe any residual leader constraints after greedy repair instead of hiding them."""
    violations = []
    for slot in MAIN_SLOTS:
        leaders = [day["slots"][slot][0]["class_code"] for day in days if day["slots"][slot]]
        for index, code in enumerate(leaders):
            if code in leaders[max(0, index - _RECENT_WINDOW) : index]:
                violations.append(
                    {
                        "rule": "recent_leader_holdback",
                        "slot": slot,
                        "day_index": index,
                        "class_code": code,
                    }
                )
        for code in set(leaders):
            if leaders.count(code) > _MAX_WEEKLY_LEADS_PER_SLOT:
                violations.append(
                    {
                        "rule": "weekly_leader_cap",
                        "slot": slot,
                        "class_code": code,
                        "observed": leaders.count(code),
                        "maximum": _MAX_WEEKLY_LEADS_PER_SLOT,
                    }
                )
    for day_index in (5, 6):
        if day_index >= len(days):
            continue
        if not any(
            days[day_index]["slots"][slot]
            and days[day_index]["slots"][slot][0]["class_code"] in CP._WEEKEND_SPECIAL_CLASSES
            for slot in ("lunch", "dinner")
        ):
            violations.append({"rule": "weekend_special_leader", "day_index": day_index})
    return {"status": "satisfied" if not violations else "degraded", "violations": violations}


def _class_preference_affinity(cat, preference_by_dish):
    """Return a bounded mean observed affinity for each class.

    Only dishes with explicit online state contribute. Multi-membership dishes teach every class
    they genuinely back; unknown catalogue names are ignored. Averaging prevents a class with many
    dishes from winning merely because it has more catalogue rows.
    """
    if not preference_by_dish:
        return {}
    totals, counts = {}, {}
    for dish in cat:
        if dish.name not in preference_by_dish:
            continue
        affinity = float(preference_by_dish.get(dish.name, 0.0) or 0.0)
        affinity = max(-1.0, min(1.0, affinity))
        for code in K.dish_to_class_codes(dish.name):
            totals[code] = totals.get(code, 0.0) + affinity
            counts[code] = counts.get(code, 0) + 1
    return {code: totals[code] / counts[code] for code in totals}


def _bounded_class_affinity(value):
    """Normalize an untrusted class-affinity map at the core boundary."""
    if not isinstance(value, dict):
        return {}
    normalized = {}
    for raw_code, raw_affinity in list(value.items())[:250]:
        code = str(raw_code).strip()
        try:
            affinity = float(raw_affinity)
        except (TypeError, ValueError):
            continue
        if code and math.isfinite(affinity):
            normalized[code] = max(-1.0, min(1.0, affinity))
    return normalized


def _combined_class_affinity(code, direct, projected):
    """Return combined affinity plus separately explainable direct/projected shares."""
    projected_value = projected.get(code, 0.0)
    if code not in direct:
        return projected_value, 0.0, projected_value
    direct_share = 0.75 * direct[code]
    projected_share = 0.25 * projected_value
    return direct_share + projected_share, direct_share, projected_share


def _ensure_weekend_special(
    slots, full_plans, backing, meta, top_classes, recent_leaders, leader_counts
):
    """If neither lunch nor dinner already leads with a gravy-rich/special class for this weekend
    day, promote the best diet-compatible, dish-backed special class (from the household's OWN
    full class_plan, so diet/Jain/allergen gating is never bypassed) to the front of whichever main
    slot it belongs to. No-op if the household's plan contains no eligible special class at all
    (e.g. every special class was diet-gated out) — never fabricates a class outside the plan."""
    already = any(
        slots.get(slot) and slots[slot][0]["class_code"] in CP._WEEKEND_SPECIAL_CLASSES
        for slot in ("lunch", "dinner")
    )
    if already:
        return
    candidates = []
    for slot in ("lunch", "dinner"):
        for code, weight in full_plans.get(slot, {}).items():
            if code in CP._WEEKEND_SPECIAL_CLASSES and backing.get(code, 0) > 0:
                candidates.append((weight, slot, code))
    if not candidates:
        return
    unrepeated = [
        candidate
        for candidate in candidates
        if candidate[2] not in set(recent_leaders[candidate[1]])
        and leader_counts[candidate[1]].get(candidate[2], 0) < _MAX_WEEKLY_LEADS_PER_SLOT
    ]
    weight, slot, code = max(unrepeated or candidates, key=lambda x: x[0])
    promoted = {
        "class_code": code,
        "class_name": _class_names().get(code, code),
        "plan_weight": round(weight, 4),
        "preference_contribution": 0.0,
        "direct_class_preference_contribution": 0.0,
        "dish_projected_preference_contribution": 0.0,
        "dish_count": backing.get(code, 0),
    }
    slots[slot] = [promoted] + [i for i in slots.get(slot, []) if i["class_code"] != code]
    slots[slot] = slots[slot][:top_classes]


_DISH_COUNTS = None
_DISH_COUNTS_CATALOGUE = None


def _class_dish_counts(cat):
    """meal_class_code -> number of catalogue dishes mapped to it (cached per catalogue identity)."""
    global _DISH_COUNTS, _DISH_COUNTS_CATALOGUE
    if _DISH_COUNTS is None or _DISH_COUNTS_CATALOGUE is not cat:
        counts: dict = {}
        for d in cat:
            for code in K.dish_to_class_codes(
                d.name
            ):  # multi-membership: count every class a dish backs
                counts[code] = counts.get(code, 0) + 1
        # Publish the count map before its owner. A concurrent request can at worst recompute; it
        # can never observe a catalogue identity paired with another catalogue's counts.
        _DISH_COUNTS = counts
        _DISH_COUNTS_CATALOGUE = cat
    return _DISH_COUNTS
