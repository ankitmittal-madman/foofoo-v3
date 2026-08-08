"""Read-only SQL that assembles one :class:`DishRecord` per dish for the gap report/validator.

Reuses the same production read boundary conventions as ``catalogue_publication.py``
(``connect_read_only`` / ``production_database_url``) — this module only adds the query shape
needed for per-dish, per-field gap bucketing, which the existing 097 SQL functions do not
expose (they only return aggregate counts and the already-filtered publishable set).
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from typing import Any

from ops.recommendation.catalogue_eligibility import DishRecord

# One row per dish with every field the eligibility rule and gap bucketer need. Deliberately
# scans public.dishes plus only the mapping/taxonomy tables the rule references — no user,
# household, or event tables are touched.
GAP_QUERY = """
select
  d.id::text as dish_id,
  d.is_active,
  d.ontology_status,
  d.diet_type,
  d.is_jain,
  d.allergen_flags,
  d.cuisine_id::text as cuisine_id,
  exists (
    select 1 from public.dish_ingredients di
    where di.dish_id = d.id and di.review_status <> 'rejected'
  ) as has_ingredient_mapping,
  exists (
    select 1 from public.dish_meal_class_mappings m
    where m.dish_id = d.id and m.review_status <> 'rejected'
  ) as has_meal_class_mapping,
  exists (
    select 1 from public.dish_meal_class_mappings m
    where m.dish_id = d.id
      and m.review_status <> 'rejected'
      and m.slot in ('breakfast', 'lunch', 'dinner', 'snack')
  ) as has_meal_slot_mapping,
  coalesce(array_agg(cur.field_key) filter (where cur.field_key is not null), '{}') as taxonomy_fields
from public.dishes d
left join public.dish_taxonomy_current cur on cur.dish_id = d.id
left join public.dish_taxonomy_assertions a
  on a.id = cur.assertion_id and a.review_status <> 'rejected'
group by d.id, d.is_active, d.ontology_status, d.diet_type, d.is_jain, d.allergen_flags, d.cuisine_id
order by d.id
"""


def _mapping(cursor: Any, row: Any) -> Mapping[str, Any]:
    """Return a cursor result as a mapping for both real and lightweight test cursors."""
    if isinstance(row, Mapping):
        return row
    columns = [item[0] for item in cursor.description]
    return dict(zip(columns, row, strict=True))


def iter_dish_records(connection: Any) -> Iterator[DishRecord]:
    """Stream one :class:`DishRecord` per row in ``public.dishes`` (all 3,409, active or not)."""
    with connection.cursor() as cursor:
        cursor.execute(GAP_QUERY)
        for raw in cursor.fetchall():
            row = _mapping(cursor, raw)
            taxonomy = row["taxonomy_fields"] or []
            # dish_taxonomy_current.field_key can legitimately be null only via the left join
            # when no assertion rows exist at all; the filter above already drops those nulls,
            # so this is just excluding an empty-array/None edge case defensively.
            yield DishRecord(
                dish_id=str(row["dish_id"]),
                is_active=bool(row["is_active"]),
                ontology_status=row["ontology_status"],
                diet_type=row["diet_type"],
                is_jain=row["is_jain"],
                allergen_flags=row["allergen_flags"],
                cuisine_id=row["cuisine_id"],
                has_ingredient_mapping=bool(row["has_ingredient_mapping"]),
                has_meal_class_mapping=bool(row["has_meal_class_mapping"]),
                has_meal_slot_mapping=bool(row["has_meal_slot_mapping"]),
                taxonomy_fields=frozenset(taxonomy),
            )
