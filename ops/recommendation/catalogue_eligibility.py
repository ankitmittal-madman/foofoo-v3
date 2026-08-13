"""Deterministic per-dish publication eligibility validator.

Implements exactly the eligibility rule already enforced in aggregate by
``re_engine.catalogue_publication_coverage()``/``catalogue_publication_rows()``
(database/migrations/097_publish_scalable_recommendation_catalogue.sql), but at per-dish
granularity: every dish gets a pass/fail verdict plus the exact list of reasons it failed.
Never guesses or autofills missing data — a field that is absent fails, full stop.

This module is pure Python and has no database dependency. Callers assemble a
``DishRecord`` for each dish (typically by joining ``public.dishes`` with the mapping/taxonomy
tables below) and pass it to :func:`evaluate_dish`.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

# The 8 taxonomy fields the rule requires as a complete set (097's ARRAY[...] <@ check).
REQUIRED_TAXONOMY_FIELDS: tuple[str, ...] = (
    "hero_role",
    "spice_level",
    "heaviness",
    "cooking_method",
    "texture",
    "richness",
    "weather_affinity",
    "meal_type",
)

VALID_DIET_TYPES = frozenset({"veg", "non_veg", "egg", "vegan"})


@dataclass(frozen=True)
class DishRecord:
    """Minimal per-dish facts needed to evaluate eligibility. No user data is included.

    ``taxonomy_fields`` and ``present_meal_slots``/``present_meal_classes`` are expected to
    already exclude rows with ``review_status = 'rejected'`` — the same exclusion the SQL rule
    applies (di.review_status <> 'rejected', m.review_status <> 'rejected', etc.).
    """

    dish_id: str
    is_active: bool
    ontology_status: str | None
    diet_type: str | None
    is_jain: bool | None
    allergen_flags: int | None
    cuisine_id: str | None
    has_ingredient_mapping: bool
    has_meal_class_mapping: bool
    has_meal_slot_mapping: bool
    taxonomy_fields: frozenset[str] = field(default_factory=frozenset)


@dataclass(frozen=True)
class EligibilityResult:
    """Pass/fail verdict for one dish plus the exact, ordered list of failing reasons."""

    dish_id: str
    passed: bool
    reasons: tuple[str, ...]


def evaluate_dish(dish: DishRecord) -> EligibilityResult:
    """Evaluate one dish against the fixed eligibility rule. Never relaxes it, never autofills.

    Reasons are returned in a fixed, documented order so output is reproducible and diffable
    run over run; every reason present names exactly the field/mapping that is missing or
    invalid.
    """
    reasons: list[str] = []

    if not dish.is_active:
        reasons.append("inactive")
    if dish.ontology_status != "enriched":
        reasons.append(f"ontology_status_not_enriched:{dish.ontology_status or 'null'}")
    if dish.diet_type is None:
        reasons.append("diet_type_missing")
    elif dish.diet_type not in VALID_DIET_TYPES:
        reasons.append(f"diet_type_invalid:{dish.diet_type}")
    if dish.is_jain is None:
        reasons.append("jain_compatibility_missing")
    if dish.allergen_flags is None:
        reasons.append("allergen_flags_missing")
    if dish.cuisine_id is None:
        reasons.append("cuisine_mapping_missing")
    if not dish.has_ingredient_mapping:
        reasons.append("ingredient_mapping_missing")
    if not dish.has_meal_class_mapping:
        reasons.append("meal_class_mapping_missing")
    if not dish.has_meal_slot_mapping:
        reasons.append("meal_slot_mapping_missing")

    missing_taxonomy = [f for f in REQUIRED_TAXONOMY_FIELDS if f not in dish.taxonomy_fields]
    if missing_taxonomy:
        reasons.append("taxonomy_incomplete:" + ",".join(missing_taxonomy))

    return EligibilityResult(dish_id=dish.dish_id, passed=not reasons, reasons=tuple(reasons))


def evaluate_dishes(dishes: Sequence[DishRecord]) -> list[EligibilityResult]:
    """Evaluate a batch of dishes; order of the input is preserved in the output."""
    return [evaluate_dish(dish) for dish in dishes]


def dish_record_from_row(row: Mapping[str, object]) -> DishRecord:
    """Build a :class:`DishRecord` from a flat mapping (e.g. a SQL row already joined/aggregated
    by the caller). Expects the exact key names used by :class:`DishRecord`'s fields; raises
    ``KeyError`` rather than silently defaulting a missing key, matching the "never guess"
    requirement.
    """
    taxonomy = row["taxonomy_fields"]
    return DishRecord(
        dish_id=str(row["dish_id"]),
        is_active=bool(row["is_active"]),
        ontology_status=row["ontology_status"],  # type: ignore[arg-type]
        diet_type=row["diet_type"],  # type: ignore[arg-type]
        is_jain=row["is_jain"],  # type: ignore[arg-type]
        allergen_flags=row["allergen_flags"],  # type: ignore[arg-type]
        cuisine_id=row["cuisine_id"],  # type: ignore[arg-type]
        has_ingredient_mapping=bool(row["has_ingredient_mapping"]),
        has_meal_class_mapping=bool(row["has_meal_class_mapping"]),
        has_meal_slot_mapping=bool(row["has_meal_slot_mapping"]),
        taxonomy_fields=frozenset(taxonomy) if taxonomy else frozenset(),  # type: ignore[arg-type]
    )
