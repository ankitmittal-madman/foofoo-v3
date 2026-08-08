"""Reproducible gap report: bucket every dish into exactly one gap bucket.

Read-only. Reuses :mod:`ops.recommendation.catalogue_eligibility` for the underlying per-field
checks so the gap report and the deterministic validator can never silently disagree about what
"missing" means for a given field.

Bucketing rule (priority order — a dish lands in the FIRST bucket it matches, checked top to
bottom; this ordering is the reproducible tie-break and must not be changed without a version
bump to ``GAP_REPORT_RULE_VERSION``):

  1. inactive_or_rejected   — is_active = false, OR ontology_status = 'rejected'
  2. missing_meal_class     — no non-rejected dish_meal_class_mappings row
  3. missing_meal_slot      — has a meal-class mapping, but none carries a valid slot
  4. missing_ingredients    — no non-rejected dish_ingredients row
  5. missing_diet_jain_allergen — diet_type, is_jain, or allergen_flags is null/invalid
  6. missing_cuisine        — cuisine_id is null
  7. missing_taxonomy       — one or more of the 8 required taxonomy fields absent
  8. publishable            — everything above passed (equivalent to evaluate_dish().passed)

Every dish (active or not, enriched or not) is bucketed exactly once. Buckets 1-7 are exclusive
gap reasons; bucket 8 is the complement of the validator's pass condition. This lets
`sum(bucket counts) == total_dishes` be asserted as an invariant in tests.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass

from ops.recommendation.catalogue_eligibility import (
    REQUIRED_TAXONOMY_FIELDS,
    VALID_DIET_TYPES,
    DishRecord,
)

GAP_REPORT_RULE_VERSION = "catalogue-gap-report-v1"

BUCKET_ORDER: tuple[str, ...] = (
    "inactive_or_rejected",
    "missing_meal_class",
    "missing_meal_slot",
    "missing_ingredients",
    "missing_diet_jain_allergen",
    "missing_cuisine",
    "missing_taxonomy",
    "publishable",
)


@dataclass(frozen=True)
class GapBucketResult:
    """One dish's single, mutually-exclusive gap bucket."""

    dish_id: str
    bucket: str


def bucket_dish(dish: DishRecord) -> str:
    """Return the single bucket name this dish falls into, per the priority order above."""
    if not dish.is_active or dish.ontology_status == "rejected":
        return "inactive_or_rejected"
    if not dish.has_meal_class_mapping:
        return "missing_meal_class"
    if not dish.has_meal_slot_mapping:
        return "missing_meal_slot"
    if not dish.has_ingredient_mapping:
        return "missing_ingredients"
    if (
        dish.diet_type is None
        or dish.diet_type not in VALID_DIET_TYPES
        or dish.is_jain is None
        or dish.allergen_flags is None
    ):
        return "missing_diet_jain_allergen"
    if dish.cuisine_id is None:
        return "missing_cuisine"
    if any(f not in dish.taxonomy_fields for f in REQUIRED_TAXONOMY_FIELDS):
        return "missing_taxonomy"
    if dish.ontology_status != "enriched":
        # Active, fully mapped/taxonomized, but ontology pipeline hasn't marked it enriched yet.
        return "missing_taxonomy"
    return "publishable"


def build_gap_report(dishes: Sequence[DishRecord]) -> dict[str, object]:
    """Bucket every dish exactly once and return counts plus per-dish assignments.

    ``counts`` always sums to ``len(dishes)`` by construction (every dish returns exactly one
    bucket name from :func:`bucket_dish`, and that name is always a member of ``BUCKET_ORDER``).
    """
    assignments = [GapBucketResult(dish_id=d.dish_id, bucket=bucket_dish(d)) for d in dishes]
    counts = Counter(a.bucket for a in assignments)
    ordered_counts = {name: counts.get(name, 0) for name in BUCKET_ORDER}
    return {
        "rule_version": GAP_REPORT_RULE_VERSION,
        "total_dishes": len(dishes),
        "counts": ordered_counts,
        "assignments": assignments,
    }
