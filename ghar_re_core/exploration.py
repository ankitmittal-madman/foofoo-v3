"""
ghar_re_core.exploration — epsilon-greedy CLASS-LEVEL exploration (Phase 2, selection-stage).

This is deliberately NOT a ScoringModule: it never touches m_k(x) math, never appears in
Contribution[]/combine(), and is not registered in ghar_re_core.modules_default.DEFAULT_REGISTRY.
It runs strictly AFTER pairing.build_plates()/assemble_7()'s greedy ranking+selection has already
picked the served plates — its only job is to decide whether ONE of those already-chosen plates
should be swapped for a lower-ranked-but-still-eligible plate from a meal CLASS this household's
own served/rejected history (`ctx['dish_feedback_counts']`) shows is under-served, so a household
sees a little variety rather than the same greedy top-N forever.

No dish's score is ever changed here — CONFIG.bandit_epsilon (data/source/bandit_weights.yaml,
code-level safety default 0.0) only decides WHETHER to explore; ctx['_rng_seed'] (test-only, never
part of the production request schema — see contracts/ghar-re-v1.schema.json, which does not
define it) makes that one dice-roll reproducible for tests.
"""
import random

from ghar_re_core import knowledge as K
from ghar_re_core.config import CONFIG


def _plate_principal(plate):
    """The one Dish object that best represents a plate's meal CLASS: the dry hero for a pair
    (mirrors ghar_re_service.engine._principal_hero's own "dry represents the pair" choice), or
    the sole hero for a single/standalone plate."""
    if plate["form"] == "pair":
        return plate["dry"]
    return plate["hero"]


def _plate_class(plate):
    """The curated meal_class_code (ghar_re_core.knowledge.dish_to_class_code) for a plate's
    principal dish, or None if that dish has no curated/derived class."""
    return K.dish_to_class_code(_plate_principal(plate).name)


def _plate_label(plate):
    """Short human-readable label for a plate, for exploration_trace entries only (never used in
    scoring) — avoids importing ghar_re_core.pairing (which imports scoring, not exploration) just
    for its plate_label() formatting helper."""
    if plate["form"] == "pair":
        return f"{plate['dry'].name} + {plate['liquid'].name}"
    return plate["hero"].name


def _served_counts_by_class(dish_feedback_counts):
    """Fold `ctx['dish_feedback_counts']` (a list of {dish_id/name, served, rejected} dicts —
    Phase 0's feedback-plumbing shape) into meal_class_code -> total `served` count, so a class
    with zero (or comparatively few) served dishes in this household's own history is identifiable
    as "under-served" without inventing a separate signal. A dish with no curated class, or with
    no `served` key at all, contributes nothing (treated as 0) rather than raising."""
    counts: dict[str, int] = {}
    for row in dish_feedback_counts or []:
        name = row.get("dish_name") or row.get("name") or row.get("dish_id")
        if not name:
            continue
        class_code = K.dish_to_class_code(name)
        if class_code is None:
            continue
        counts[class_code] = counts.get(class_code, 0) + int(row.get("served", 0) or 0)
    return counts


def epsilon_greedy_select(chosen, candidate_plates, ctx):
    """Epsilon-greedy class-level exploration over an already-ranked/selected plate list.

    `chosen`: the plates pairing.assemble_7's greedy no-duplicate-guard walk already picked
        (already-ranked output — this function never re-ranks/re-scores anything).
    `candidate_plates`: the full scored candidate pool (pairing.build_plates's output) that
        `chosen` was drawn from, so a swap-in candidate can only ever be something that was
        already eligible and already scored.
    `ctx`: request context; reads `dish_feedback_counts` (served/rejected history) and the
        test-only `_rng_seed` (never part of the production request schema).

    With probability CONFIG.bandit_epsilon (YAML default 0.15, code-level safety default 0.0 —
    see ghar_re_core/config.py), replaces the single LOWEST-scored already-chosen plate with the
    best-available not-yet-chosen candidate from a genuinely more under-served meal class (strictly
    fewer served dishes in `dish_feedback_counts` than the class being replaced), provided the swap
    introduces no duplicate hero dish among the plates that remain. Falls through to a no-op
    (returns `chosen` unchanged, empty trace) if epsilon is 0, the dice roll lands on "exploit", or
    no such candidate exists.

    Returns (new_chosen, exploration_trace) — `exploration_trace` is a list of phase="explore"
    trace dicts (never a Contribution — this is not a ScoringModule) describing any swap made, for
    observability/decision-trace purposes only."""
    chosen = list(chosen)
    epsilon = CONFIG.bandit_epsilon
    if not chosen or not epsilon or epsilon <= 0:
        return chosen, []

    seed = ctx.get("_rng_seed")
    rng = random.Random(seed) if seed is not None else random.Random()
    if rng.random() >= epsilon:
        return chosen, []                              # exploit — no swap this call

    served_counts = _served_counts_by_class(ctx.get("dish_feedback_counts"))

    # Swap target = the lowest-scored already-chosen plate (least to lose by replacing it).
    swap_target = min(chosen, key=lambda p: p["score"])
    remaining = [p for p in chosen if p is not swap_target]
    remaining_heroes: set = set()
    for p in remaining:
        remaining_heroes |= p["heroes"]
    target_class = _plate_class(swap_target)
    target_served = served_counts.get(target_class, 0)

    chosen_ids = {id(p) for p in chosen}
    best, best_key = None, None
    for cand in candidate_plates:
        if id(cand) in chosen_ids:
            continue
        if cand["heroes"] & remaining_heroes:
            continue                                   # would duplicate a hero still in use
        cls = _plate_class(cand)
        if cls is None or cls == target_class:
            continue                                   # only swap in a genuinely different class
        served = served_counts.get(cls, 0)
        if served >= target_served:
            continue                                   # not actually MORE under-served
        # tie-break among equally under-served candidates: prefer the least-served class, then
        # (CONFIG.bandit_exploration_boost-nudged) higher plate score — never alters the score
        # itself, only which equally-under-served candidate wins the tie-break.
        key = (served, -(cand["score"] + CONFIG.bandit_exploration_boost))
        if best is None or key < best_key:
            best, best_key = cand, key

    if best is None:
        return chosen, []

    new_chosen = remaining + [best]
    trace = [{
        "phase": "explore",
        "module": "epsilon_greedy_select",
        "epsilon": epsilon,
        "swapped_out": _plate_label(swap_target),
        "swapped_out_class": target_class,
        "swapped_in": _plate_label(best),
        "swapped_in_class": _plate_class(best),
        "explanation": (
            f"exploration swap: replaced '{_plate_label(swap_target)}' (class={target_class}, "
            f"served={target_served}) with '{_plate_label(best)}' (class={_plate_class(best)}, "
            f"served={served_counts.get(_plate_class(best), 0)}) — the swapped-in class is more "
            f"under-served in this household's own feedback history."
        ),
    }]
    return new_chosen, trace
