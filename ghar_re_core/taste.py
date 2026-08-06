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

_TAG_DIMENSION_ATTRIBUTES = {
    "meal_type": "meal_type",
    "dish_category": "dish_category",
    "cooking_method": "cooking_method",
    "primary_taste": "primary_taste",
    "texture": "texture",
    "richness": "richness",
}


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


def _bounded_map(values) -> dict[str, float]:
    result = {}
    if not isinstance(values, dict):
        return result
    for key, raw in values.items():
        if not isinstance(key, str):
            continue
        try:
            result[key] = max(-1.0, min(1.0, float(raw)))
        except (TypeError, ValueError):
            continue
    return result


def _mean_evidence(keys, affinities) -> float | None:
    values = [affinities[key] for key in keys if key in affinities]
    return sum(values) / len(values) if values else None


def _semantic_affinity(dish, preference_by_class, preference_by_tag) -> float | None:
    """Average independent class and tag projections for an unseen dish.

    Each projection is already derived from explicit outcomes. Averaging prevents a dish with
    many tags from receiving a larger score merely because it has richer catalogue metadata.
    """
    sources = []
    class_value = _mean_evidence(K.dish_to_class_codes(dish.name), preference_by_class)
    if class_value is not None:
        sources.append(class_value)
    tag_keys = []
    for dimension, attribute in _TAG_DIMENSION_ATTRIBUTES.items():
        tag_keys.extend(f"{dimension}:{value}" for value in getattr(dish, attribute, []) or [])
    tag_value = _mean_evidence(tag_keys, preference_by_tag)
    if tag_value is not None:
        sources.append(tag_value)
    return sum(sources) / len(sources) if sources else None


def expand_preferences(
    preference_by_dish,
    catalogue,
    preference_by_class=None,
    preference_by_tag=None,
) -> dict[str, float]:
    """Canonicalize explicit feedback and transfer its strongest related-dish signal.

    Unknown names and malformed values are ignored. A transferred value is capped below the
    explicit signal (``TRANSFER_SCALE``), preventing inferred taste from overruling a direct vote.
    """
    explicit: dict[str, float] = {}
    raw_dish_preferences = preference_by_dish if isinstance(preference_by_dish, dict) else {}
    for name, raw_affinity in list(raw_dish_preferences.items())[-MAX_SEEDS:]:
        dish = catalogue.get(name)
        if dish is None:
            continue
        try:
            affinity = max(-1.0, min(1.0, float(raw_affinity)))
        except (TypeError, ValueError):
            continue
        explicit[dish.name] = affinity

    class_affinities = _bounded_map(preference_by_class)
    tag_affinities = _bounded_map(preference_by_tag)
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
        semantic = _semantic_affinity(candidate, class_affinities, tag_affinities)
        if semantic is not None:
            semantic *= TRANSFER_SCALE
            if abs(semantic) > abs(strongest):
                strongest = semantic
        if strongest:
            expanded[candidate.name] = max(-TRANSFER_SCALE, min(TRANSFER_SCALE, strongest))
    return expanded
