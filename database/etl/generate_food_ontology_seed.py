"""Build the deterministic food-ontology seed from FooFoo's research bundle.

The generated SQL never copies a worksheet shape into production. It converts the class-first
research CSV and catalogue JSON into normalized meal-class families, dish/class mappings and
per-field assertions with confidence and provenance.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CLASS_DIR = ROOT / "data" / "source" / "class_first_v1"
CATALOGUE = ROOT / "ghar_re_service" / "data" / "bundle" / "catalogue.json"
OUTPUT = ROOT / "database" / "seeds" / "146_seed_food_ontology.sql"
SNAPSHOT_OUTPUT = CLASS_DIR / "food_ontology_snapshot.json"

TAXONOMY_FIELDS = (
    "cuisine",
    "diet",
    "cooking_method",
    "spice_level",
    "heaviness",
    "texture",
    "richness",
    "weather_affinity",
    "meal_type",
    "state_origin",
    "hero_role",
    "jain_compatible",
    "farali_compatible",
)


def _json_literal(value: object) -> str:
    """Serialize data for a PostgreSQL dollar-quoted JSON literal."""
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _slots(slot_group: str) -> list[str]:
    """Convert the research slot group into normalized runtime slot rows."""
    return {
        "Breakfast": ["breakfast"],
        "Lunch/Dinner": ["lunch", "dinner"],
        "Dinner": ["dinner"],
        "Snack": ["snack"],
    }[slot_group]


def load_sources() -> tuple[
    list[dict[str, str]],
    list[dict[str, str]],
    list[dict[str, str]],
    list[dict[str, object]],
]:
    """Load the three checked-in sources shared by the SQL and recommendation snapshot."""
    with (CLASS_DIR / "meal_class_master.csv").open(encoding="utf-8", newline="") as handle:
        classes = list(csv.DictReader(handle))
    with (CLASS_DIR / "dish_class_map.csv").open(encoding="utf-8", newline="") as handle:
        mappings = list(csv.DictReader(handle))
    with (CLASS_DIR / "class_dish_options.csv").open(encoding="utf-8", newline="") as handle:
        curated = list(csv.DictReader(handle))
    catalogue = json.loads(CATALOGUE.read_text(encoding="utf-8"))
    return classes, mappings, curated, catalogue


def normalized_mappings(
    mappings: list[dict[str, str]], curated: list[dict[str, str]]
) -> list[dict[str, object]]:
    """Union full-coverage classifications with legacy curated membership without duplicates."""
    rows: list[dict[str, object]] = [
        {
            "dish_name": row["dish_name"],
            "meal_class_code": row["meal_class_code"],
            "slot_group": row["slot_group"],
            "method": row["method"],
            "confidence": float(row["confidence"]),
            "source": "class_first_v1/dish_class_map.csv",
        }
        for row in mappings
    ]
    seen = {(str(row["dish_name"]).strip().casefold(), str(row["meal_class_code"])) for row in rows}
    for row in curated:
        key = (row["dish_name"].strip().casefold(), row["meal_class_code"])
        if key in seen:
            continue
        rows.append(
            {
                "dish_name": row["dish_name"],
                "meal_class_code": row["meal_class_code"],
                "slot_group": row["slot_group"],
                "method": "curated_exact",
                "confidence": 1.0,
                "source": "class_first_v1/class_dish_options.csv",
            }
        )
        seen.add(key)
    return rows


def build_snapshot(
    classes: list[dict[str, str]],
    mappings: list[dict[str, str]],
    curated: list[dict[str, str]],
    catalogue: list[dict[str, object]],
) -> dict[str, object]:
    """Build the immutable ontology projection consumed by the current recommender.

    This deliberately contains only planning-safe class membership metadata. Raw source evidence,
    AI candidates and review history remain in Postgres and can never enter the scoring process by
    being copied into the runtime bundle. Primary selection matches the legacy lookup exactly:
    curated rows win, then the first non-secondary class-first mapping.
    """
    role_by_class = {row["meal_class_code"]: row["planning_role_v3"] for row in classes}
    curated_primary: dict[str, str] = {}
    for row in curated:
        curated_primary.setdefault(row["dish_name"].strip().casefold(), row["meal_class_code"])

    rows_by_dish: dict[str, list[dict[str, object]]] = {}
    first_mapping: dict[str, str] = {}
    for row in normalized_mappings(mappings, curated):
        key = str(row["dish_name"]).strip().casefold()
        first_mapping.setdefault(key, str(row["meal_class_code"]))
        confidence = float(row["confidence"])
        rows_by_dish.setdefault(key, []).append(
            {
                "class_code": row["meal_class_code"],
                "slot_group": row["slot_group"],
                "planning_role": role_by_class[row["meal_class_code"]],
                "method": row["method"],
                "confidence": confidence,
                "review_status": "accepted" if confidence >= 0.75 else "provisional",
                "source": row["source"],
            }
        )

    dishes = []
    for dish in catalogue:
        name = str(dish["name"])
        key = name.strip().casefold()
        primary = curated_primary.get(key) or first_mapping.get(key)
        dishes.append(
            {
                "name": name,
                "primary_class_code": primary,
                "mappings": rows_by_dish.get(key, []),
            }
        )
    catalogue_keys = {str(dish["name"]).strip().casefold() for dish in catalogue}
    promoted_mapping_count = sum(len(rows_by_dish.get(key, [])) for key in catalogue_keys)
    # The historical curated files also contain fixture names, aliases and composed meal labels
    # that are intentionally not canonical catalogue dishes.  Snapshot v2 carries those exact
    # lookup entries so the runtime no longer needs the source CSVs while preserving every class
    # lookup and multi-membership result byte-for-byte.
    lookup_names: dict[str, str] = {}
    for row in [*curated, *mappings]:
        key = row["dish_name"].strip().casefold()
        lookup_names.setdefault(key, row["dish_name"].strip())
    catalogue_names = {
        str(dish["name"]).strip().casefold(): str(dish["name"]) for dish in catalogue
    }
    lookup_entries = []
    for key in sorted(set(rows_by_dish) - catalogue_keys):
        primary = curated_primary.get(key) or first_mapping.get(key)
        lookup_entries.append(
            {
                "name": catalogue_names.get(key, lookup_names[key]),
                "canonical_dish": catalogue_names.get(key),
                "primary_class_code": primary,
                "mappings": rows_by_dish[key],
            }
        )
    return {
        "schema_version": 2,
        "source": [
            "class_first_v1/dish_class_map.csv",
            "class_first_v1/class_dish_options.csv",
        ],
        "promotion_mode": "immutable_bundle",
        "dish_count": len(dishes),
        "source_mapping_count": len(mappings),
        "mapping_count": promoted_mapping_count,
        "lookup_entry_count": len(lookup_entries),
        "runtime_lookup_count": len(set(rows_by_dish) | catalogue_keys),
        "unmatched_source_dishes": sorted(
            {
                row["dish_name"]
                for row in mappings
                if row["dish_name"].strip().casefold() not in catalogue_keys
            }
        ),
        "dishes": dishes,
        "lookup_entries": lookup_entries,
    }


def build_seed(
    classes: list[dict[str, str]] | None = None,
    mappings: list[dict[str, str]] | None = None,
    curated: list[dict[str, str]] | None = None,
    catalogue: list[dict[str, object]] | None = None,
) -> str:
    """Return idempotent SQL derived exclusively from checked-in research sources."""
    if classes is None or mappings is None or curated is None or catalogue is None:
        classes, mappings, curated, catalogue = load_sources()

    families = sorted({row["class_family_code"] for row in classes if row["class_family_code"]})
    family_payload = [
        {"code": code, "name": code.removeprefix("FAM_").replace("_", " ").title()}
        for code in families
    ]
    class_payload = [
        {
            "code": row["meal_class_code"],
            "family": row["class_family_code"],
            "role": row["planning_role_v3"],
            "weekday": int(row["weekday_fit_1_5"]),
            "weekend": int(row["weekend_fit_1_5"]),
        }
        for row in classes
    ]

    mapping_payload: list[dict[str, object]] = []
    role_by_class = {row["meal_class_code"]: row["planning_role_v3"] for row in classes}
    canonical_name_by_key = {
        str(dish["name"]).strip().casefold(): str(dish["name"]) for dish in catalogue
    }
    for row in normalized_mappings(mappings, curated):
        planning_role = role_by_class[str(row["meal_class_code"])]
        item_role = {
            "MAIN_PRIMARY": "primary",
            "ADDON_ONLY_NOT_PRIMARY": "addon",
            "COMBO_TEMPLATE_NOT_PRIMARY": "combo_component",
        }[planning_role]
        for slot in _slots(row["slot_group"]):
            mapping_payload.append(
                {
                    "dish": canonical_name_by_key.get(
                        str(row["dish_name"]).strip().casefold(), row["dish_name"]
                    ),
                    "class": row["meal_class_code"],
                    "slot": slot,
                    "role": item_role,
                    "method": row["method"],
                    "confidence": float(row["confidence"]),
                    "source": row["source"],
                }
            )

    assertion_payload = [
        {"dish": dish["name"], "field": field, "value": dish[field], "confidence": 0.9}
        for dish in catalogue
        for field in TAXONOMY_FIELDS
        if field in dish and dish[field] is not None and dish[field] != []
    ]

    return f"""-- Seed: 146_seed_food_ontology.sql
-- Generated deterministically by database/etl/generate_food_ontology_seed.py.
-- Sources: class_first_v1/{{meal_class_master,dish_class_map}}.csv and bundle/catalogue.json.
-- Apply after migration 056. Safe to rerun; accepted human review is never overwritten.

WITH rows AS (
  SELECT * FROM jsonb_to_recordset($json${_json_literal(family_payload)}$json$::jsonb)
    AS x(code text, name text)
)
INSERT INTO public.meal_class_families (family_code, display_name)
SELECT code, name FROM rows
ON CONFLICT (family_code) DO UPDATE SET display_name = EXCLUDED.display_name;

WITH rows AS (
  SELECT * FROM jsonb_to_recordset($json${_json_literal(class_payload)}$json$::jsonb)
    AS x(code text, family text, role text, weekday smallint, weekend smallint)
)
UPDATE public.meal_classes c
SET class_family_code = rows.family,
    planning_role = rows.role,
    weekday_fit_1_5 = rows.weekday,
    weekend_fit_1_5 = rows.weekend,
    is_addon = (rows.role = 'ADDON_ONLY_NOT_PRIMARY')
FROM rows WHERE c.class_code = rows.code;

WITH rows AS (
  SELECT * FROM jsonb_to_recordset($json${_json_literal(mapping_payload)}$json$::jsonb)
    AS x(dish text, class text, slot text, role text, method text, confidence numeric, source text)
)
INSERT INTO public.dish_meal_class_mappings (
  dish_id, class_code, slot, item_role, confidence, source_name, classification_method,
  source_type, review_status
)
SELECT d.id, rows.class, rows.slot, rows.role, rows.confidence,
       rows.source, rows.method, 'internal_research',
       CASE WHEN rows.confidence >= 0.75 THEN 'accepted' ELSE 'provisional' END
FROM rows JOIN public.dishes d ON d.name = rows.dish
JOIN public.meal_classes c ON c.class_code = rows.class
ON CONFLICT (dish_id, class_code, slot) DO UPDATE
SET item_role = EXCLUDED.item_role,
    confidence = EXCLUDED.confidence,
    source_name = EXCLUDED.source_name,
    classification_method = EXCLUDED.classification_method,
    source_type = EXCLUDED.source_type,
    review_status = EXCLUDED.review_status,
    updated_at = now()
WHERE public.dish_meal_class_mappings.review_status <> 'accepted'
  AND EXCLUDED.confidence >= public.dish_meal_class_mappings.confidence;

WITH rows AS (
  SELECT * FROM jsonb_to_recordset($json${_json_literal(assertion_payload)}$json$::jsonb)
    AS x(dish text, field text, value jsonb, confidence numeric)
), inserted AS (
  INSERT INTO public.dish_taxonomy_assertions (
    id, dish_id, field_key, value_json, confidence, source_name, source_type, review_status
  )
  SELECT md5('foofoo-ontology-v1:' || d.id::text || ':' || rows.field)::uuid,
         d.id, rows.field, rows.value, rows.confidence,
         'ghar_re_service/data/bundle/catalogue.json', 'internal_research', 'provisional'
  FROM rows JOIN public.dishes d ON d.name = rows.dish
  ON CONFLICT (id) DO UPDATE
  SET value_json = EXCLUDED.value_json,
      confidence = EXCLUDED.confidence,
      updated_at = now()
  WHERE public.dish_taxonomy_assertions.review_status = 'provisional'
  RETURNING id, dish_id, field_key
)
INSERT INTO public.dish_taxonomy_current (dish_id, field_key, assertion_id, selected_by)
SELECT dish_id, field_key, id, 'seed:146' FROM inserted
ON CONFLICT (dish_id, field_key) DO NOTHING;

WITH class_confidence AS (
  SELECT dish_id, max(confidence) AS confidence
  FROM public.dish_meal_class_mappings
  WHERE review_status <> 'rejected'
  GROUP BY dish_id
), field_coverage AS (
  SELECT dish_id, count(*) AS field_count
  FROM public.dish_taxonomy_current
  GROUP BY dish_id
)
UPDATE public.dishes d
SET ontology_confidence = least(0.900, cc.confidence),
    ontology_status = CASE
      WHEN fc.field_count >= {len(TAXONOMY_FIELDS)} AND cc.confidence >= 0.700 THEN 'enriched'
      ELSE 'review'
    END,
    ontology_last_reviewed_at = now()
FROM class_confidence cc
JOIN field_coverage fc ON fc.dish_id = cc.dish_id
WHERE d.id = cc.dish_id;

UPDATE public.dish_enrichment_jobs j
SET status = CASE WHEN d.ontology_status = 'enriched' THEN 'complete' ELSE 'review' END,
    missing_fields = CASE
      WHEN d.ontology_status = 'enriched' THEN '{{}}'::text[]
      ELSE missing_fields
    END,
    updated_at = now()
FROM public.dishes d
WHERE j.dish_id = d.id AND j.status NOT IN ('failed','complete');
"""


def main() -> None:
    """Write the SQL seed and the recommendation-compatible immutable ontology projection."""
    classes, mappings, curated, catalogue = load_sources()
    OUTPUT.write_text(build_seed(classes, mappings, curated, catalogue), encoding="utf-8")
    SNAPSHOT_OUTPUT.write_text(
        json.dumps(
            build_snapshot(classes, mappings, curated, catalogue), ensure_ascii=False, indent=2
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"wrote {OUTPUT.relative_to(ROOT)}")
    print(f"wrote {SNAPSHOT_OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
