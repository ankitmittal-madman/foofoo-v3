"""Immediate, explainable taste transfer for the online-feedback cold-data phase.

The learned preference model remains deliberately disabled until it has enough trustworthy
outcomes.  Exact likes/dislikes should still teach the system something useful in the meantime:
this module transfers a bounded fraction of an explicit dish affinity to catalogue dishes with
overlapping culinary attributes.  It never changes eligibility, and exact feedback always wins.
"""

from __future__ import annotations

from ghar_re_core import knowledge as K


TRANSFER_SCALE = 0.6
MIN_SIMILARITY = 0.32
MAX_SEEDS = 100


def _jaccard(left, right) -> float:
    left, right = set(left or []), set(right or [])
    union = left | right
    return len(left & right) / len(union) if union else 0.0


def content_similarity(left, right) -> float:
    """Transparent [0,1] similarity over stable catalogue attributes."""
    left_classes = K.dish_to_class_codes(left.name)
    right_classes = K.dish_to_class_codes(right.name)
    same_class = 1.0 if left_classes & right_classes else 0.0
    same_cuisine = 1.0 if left.cuisine == right.cuisine else 0.0
    return (
        0.30 * same_class
        + 0.20 * same_cuisine
        + 0.20 * _jaccard(left.main_ingredients, right.main_ingredients)
        + 0.10 * _jaccard(left.dish_category, right.dish_category)
        + 0.08 * _jaccard(left.primary_taste, right.primary_taste)
        + 0.05 * _jaccard(left.cooking_method, right.cooking_method)
        + 0.04 * _jaccard(left.richness, right.richness)
        + 0.03 * _jaccard(left.texture, right.texture)
    )


def canonicalize_names(names, catalogue) -> list[str]:
    """Resolve aliases to display-canonical names and preserve unknown names for suppression."""
    result = []
    seen = set()
    for value in names or []:
        if not isinstance(value, str):
            continue
        dish = catalogue.get(value)
        canonical = dish.name if dish is not None else " ".join(value.split())
        key = canonical.casefold()
        if canonical and key not in seen:
            result.append(canonical)
            seen.add(key)
    return result


def expand_preferences(preference_by_dish, catalogue) -> dict[str, float]:
    """Canonicalize explicit feedback and transfer its strongest related-dish signal.

    Unknown names and malformed values are ignored. A transferred value is capped below the
    explicit signal (``TRANSFER_SCALE``), preventing inferred taste from overruling a direct vote.
    """
    explicit = {}
    if not isinstance(preference_by_dish, dict):
        return explicit
    for name, raw_affinity in list(preference_by_dish.items())[-MAX_SEEDS:]:
        dish = catalogue.get(name)
        if dish is None:
            continue
        try:
            affinity = max(-1.0, min(1.0, float(raw_affinity)))
        except (TypeError, ValueError):
            continue
        explicit[dish.name] = affinity

    expanded = dict(explicit)
    seeds = [(catalogue.get(name), affinity) for name, affinity in explicit.items()]
    for candidate in catalogue:
        if candidate.name in explicit:
            continue
        strongest = 0.0
        for seed, affinity in seeds:
            similarity = content_similarity(seed, candidate)
            if similarity < MIN_SIMILARITY:
                continue
            transferred = affinity * similarity * TRANSFER_SCALE
            if abs(transferred) > abs(strongest):
                strongest = transferred
        if strongest:
            expanded[candidate.name] = max(-TRANSFER_SCALE, min(TRANSFER_SCALE, strongest))
    return expanded
