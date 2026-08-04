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
    }


def _ranked(cat, theta, ctx, objective, predicate=None):
    """(score, dish) for every slot-appropriate, eligible dish, best first. `predicate` further
    restricts the pool (e.g. to one meal class) without ever loosening eligibility."""
    out = []
    for d in cat:
        if S.m_slot(d, ctx) == 0.0:               # not valid for this slot
            continue
        if not S.eligible(d, theta, ctx):          # A1–A5 correctness/observance filters
            continue
        if predicate is not None and not predicate(d):
            continue
        out.append((S.score(d, theta, ctx, objective), d))
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
    within_budget = [pair for pair in ranked
                     if pair[1].total_mins is None or pair[1].total_mins <= _BEGINNER_TIME_BUDGET_MINS]
    over_budget = [pair for pair in ranked
                   if pair[1].total_mins is not None and pair[1].total_mins > _BEGINNER_TIME_BUDGET_MINS]
    return within_budget + over_budget


def _diversify(ranked, n, per_class=2, per_cuisine=3, rng=None):
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
    deferred = []
    for score, d in ranked:
        code = K.dish_to_class_code(d.name)
        if seen_class.get(code, 0) >= per_class:
            continue
        if seen_cuisine.get(d.cuisine, 0) >= per_cuisine:
            continue
        if epsilon > 0 and rng.random() < epsilon:
            deferred.append((score, d))          # exploration: give a later candidate its turn
            continue
        picked.append((score, d))
        seen_class[code] = seen_class.get(code, 0) + 1
        seen_cuisine[d.cuisine] = seen_cuisine.get(d.cuisine, 0) + 1
        if len(picked) >= n:
            return picked
    # top-up if caps (or deferrals) left us short — deferred picks first, then the remainder,
    # so an exploration deferral still gets a genuine second chance rather than being discarded.
    if len(picked) < n:
        chosen = {id(d) for _, d in picked}
        for score, d in deferred + ranked:
            if id(d) not in chosen:
                picked.append((score, d))
                chosen.add(id(d))
                if len(picked) >= n:
                    break
    return picked[:n]


def _theta_obj(household):
    """Derive θ + resolve the household's objective once."""
    theta = derive_theta(household)
    objective = household.get("q15_objective") or CONFIG.default_objective
    return theta, objective


def cold_start_top15(household, catalogue=None, n=15, weekday="Monday", household_id=None):
    """Surface 1 — the post-onboarding preference primer: the n (default 15) top-scoring, DIVERSE
    dishes across breakfast/lunch/dinner, for the user to like and seed their taste profile. Diverse
    = capped per meal class and per cuisine so it spans the plan, not one class 15 times.

    `household_id`: when given, seeds a household-stable RNG so `_diversify` applies
    CONFIG.bandit_epsilon exploration (see its docstring) — two households with identical answers
    (same cohort, same theta) get varied top-n sets instead of always converging on the exact same
    15 dishes, while a given household's own result stays stable call-to-call until its answers or
    the catalogue actually change. Omitted (None) => no exploration, exact prior deterministic
    behaviour (existing tests/fixtures that don't pass household_id are unaffected)."""
    cat = catalogue or Catalogue()
    theta, objective = _theta_obj(household)
    rng = random.Random(household_id) if household_id is not None else None
    # pool the best of each main slot, then diversify across the merged pool
    pool = {}
    for slot in MAIN_SLOTS:
        ctx = make_context(slot=slot, weekday=weekday)
        for score, d in _ranked(cat, theta, ctx, objective)[:20]:
            prev = pool.get(d.name)
            if prev is None or score > prev[0]:
                pool[d.name] = (score, d, slot, ctx)
    ranked = sorted(((v[0], v[1]) for v in pool.values()), key=lambda x: -x[0])
    ranked = _apply_cook_capability_bias(ranked, household.get("cook_capability"))
    picked = _diversify(ranked, n, rng=rng)
    slot_of = {v[1].name: (v[2], v[3]) for v in pool.values()}
    return {
        "household": household.get("label"),
        "kind": "cold_start_top_dishes",
        "count": len(picked),
        "dishes": [dict(_dish_view(d, theta, slot_of[d.name][1], objective, score),
                        slot=slot_of[d.name][0]) for score, d in picked],
    }


def slot_options(household, slot, catalogue=None, n=5, weekday="Monday", class_code=None):
    """Surface 2 — a slot's 4–5 best meal options. If `class_code` is given, this is also the
    reconciliation path (surface 4): only dishes of that class are considered."""
    cat = catalogue or Catalogue()
    theta, objective = _theta_obj(household)
    ctx = make_context(slot=slot, weekday=weekday)
    # multi-membership (WP-17.1): a dish is eligible for a class if that class is ANY of its classes
    # (primary or secondary), not only its single primary — so behavioural DN_ dinner classes reconcile
    # to the dishes they overlap with the LD_ pool, instead of falling back to regional plates.
    pred = (lambda d: class_code in K.dish_to_class_codes(d.name)) if class_code else None
    ranked = _ranked(cat, theta, ctx, objective, predicate=pred)
    picked = ranked[:n] if class_code else _diversify(ranked, n, per_class=1, per_cuisine=2)
    return {
        "household": household.get("label"),
        "slot": slot,
        "weekday": weekday,
        "class_code": class_code,
        "count": len(picked),
        "options": [_dish_view(d, theta, ctx, objective, score, label_class=class_code)
                    for score, d in picked],
    }


def dishes_for_class(household, slot, class_code, catalogue=None, n=8, weekday="Monday"):
    """Surface 4 — RECONCILIATION. Given a day's finalized meal CLASS, return only the eligible
    dishes of that class for the slot, best-scored first. Thin wrapper over slot_options so the
    class-filter path can never diverge from the option-ranking path."""
    return dict(slot_options(household, slot, catalogue=catalogue, n=n, weekday=weekday,
                             class_code=class_code), kind="reconciled_class_dishes")


_RECENT_WINDOW = 2   # days a class is held back from re-topping the same slot, once it has led


def weekly_class_plan(household, top_classes=3, catalogue=None):
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
    meta = CP._class_meta()
    days = []
    recent_leaders = {slot: [] for slot in MAIN_SLOTS}   # slot -> class codes that led on recent days
    for day in WEEK:
        slots = {}
        full_plans = {}
        for slot in MAIN_SLOTS:
            ctx = make_context(slot=slot, weekday=day)
            plan = CP.class_plan(theta, ctx)
            full_plans[slot] = plan
            ranked = sorted(plan.items(), key=lambda x: -x[1])
            held_back = set(recent_leaders[slot])
            top, deferred = [], []
            for code, weight in ranked:
                if backing.get(code, 0) == 0:      # never offer a class with no dishes to reconcile to
                    continue
                item = {
                    "class_code": code,
                    "class_name": _class_names().get(code, code),
                    "plan_weight": round(weight, 4),
                    "dish_count": backing.get(code, 0),
                }
                if code in held_back:
                    deferred.append(item)          # led recently — only used if the pool runs dry
                    continue
                top.append(item)
                if len(top) >= top_classes:
                    break
            for item in deferred:                  # pool too thin to fill without repeating — allow it
                if len(top) >= top_classes:
                    break
                top.append(item)
            slots[slot] = top
            recent_leaders[slot] = ([top[0]["class_code"]] if top else []) + recent_leaders[slot]
            recent_leaders[slot] = recent_leaders[slot][:_RECENT_WINDOW]
        if day in ("Saturday", "Sunday"):
            _ensure_weekend_special(slots, full_plans, backing, meta, top_classes)
        days.append({"weekday": day, "slots": slots})
    return {"household": household.get("label"), "kind": "weekly_class_plan", "days": days}


def _ensure_weekend_special(slots, full_plans, backing, meta, top_classes):
    """If neither lunch nor dinner already leads with a gravy-rich/special class for this weekend
    day, promote the best diet-compatible, dish-backed special class (from the household's OWN
    full class_plan, so diet/Jain/allergen gating is never bypassed) to the front of whichever main
    slot it belongs to. No-op if the household's plan contains no eligible special class at all
    (e.g. every special class was diet-gated out) — never fabricates a class outside the plan."""
    already = any(item["class_code"] in CP._WEEKEND_SPECIAL_CLASSES
                  for slot in ("lunch", "dinner") for item in slots.get(slot, []))
    if already:
        return
    candidates = []
    for slot in ("lunch", "dinner"):
        for code, weight in full_plans.get(slot, {}).items():
            if code in CP._WEEKEND_SPECIAL_CLASSES and backing.get(code, 0) > 0:
                candidates.append((weight, slot, code))
    if not candidates:
        return
    weight, slot, code = max(candidates, key=lambda x: x[0])
    promoted = {
        "class_code": code,
        "class_name": _class_names().get(code, code),
        "plan_weight": round(weight, 4),
        "dish_count": backing.get(code, 0),
    }
    slots[slot] = [promoted] + [i for i in slots.get(slot, []) if i["class_code"] != code]
    slots[slot] = slots[slot][:top_classes]


_DISH_COUNTS = None


def _class_dish_counts(cat):
    """meal_class_code -> number of catalogue dishes mapped to it (cached per catalogue identity)."""
    global _DISH_COUNTS
    if _DISH_COUNTS is None:
        counts: dict = {}
        for d in cat:
            for code in K.dish_to_class_codes(d.name):  # multi-membership: count every class a dish backs
                counts[code] = counts.get(code, 0) + 1
        _DISH_COUNTS = counts
    return _DISH_COUNTS
