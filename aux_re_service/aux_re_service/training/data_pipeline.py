"""Audit and canonicalize the supplied synthetic Indian household datasets."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from openpyxl import load_workbook

POSITIVE_EVENTS = {
    "cooked": 1.0,
    "locked": 0.95,
    "saved": 0.8,
    "planned": 0.7,
    "rated": 0.6,
    "substituted": 0.45,
    "search": 0.12,
    "viewed": 0.05,
}
NEGATIVE_EVENTS = {"never": -1.0, "skipped": -0.8, "not_today": -0.35}
PREFERENCE_WEIGHTS = {"love": 1.0, "like": 0.7, "neutral": 0.05, "avoid": -0.8, "never": -1.0}
MEMBER_SENTIMENT_WEIGHTS = {
    "love": 1.0,
    "like": 0.65,
    "neutral": 0.05,
    "dislike": -0.65,
    "hate": -1.0,
    "avoid": -1.0,
}
NON_VEG_WORDS = {"chicken", "mutton", "fish", "gosht", "mangsho", "prawn", "egg"}
CUISINE_REGIONS = {
    "andhra": "south",
    "bengali": "east",
    "gujarati": "west",
    "goan": "west",
    "kashmiri": "north",
    "kerala": "south",
    "maharashtrian": "west",
    "malabar": "south",
    "mughlai": "north",
    "odia": "east",
    "punjabi": "north",
    "rajasthani": "north",
    "tamil": "south",
    "telangana": "south",
    "up": "north",
}
ALLERGEN_INGREDIENTS = {
    "peanut": "peanut",
    "groundnut": "peanut",
    "milk": "dairy",
    "curd": "dairy",
    "paneer": "dairy",
    "wheat": "wheat",
    "cashew": "tree_nut",
    "almond": "tree_nut",
    "fish": "fish",
    "prawn": "shellfish",
    "mustard": "mustard",
    "egg": "egg",
}
SPICE_GROUPS = {
    "chilli_forward": {"chilli", "chilli_powder", "green_chilli", "red_chilli"},
    "warming_whole_spices": {
        "cardamom_green",
        "cardamom_black",
        "cinnamon",
        "clove",
        "pepper",
        "star_anise",
    },
    "tempering_spices": {
        "cumin",
        "cumin_seeds",
        "mustard",
        "mustard_seeds",
        "nigella_seeds",
        "fenugreek",
        "asafoetida",
    },
}
NUTRITION_TRAITS = {
    "contains_pulse": {"dal", "lentil", "chana", "chickpea", "rajma", "beans", "moong"},
    "contains_dairy": {"milk", "curd", "paneer", "yogurt"},
    "contains_egg": {"egg"},
    "contains_fish_or_seafood": {"fish", "prawn", "shrimp"},
    "contains_meat": {"chicken", "mutton", "lamb", "goat"},
    "contains_leafy_green": {"spinach", "palak", "methi", "amaranth"},
    "contains_millet": {"millet", "ragi", "jowar", "bajra"},
}


def normalize_name(value: str) -> str:
    value = value.casefold().replace("&", " and ")
    return " ".join(re.sub(r"[^a-z0-9]+", " ", value).split())


def lookup_key(value: str) -> str:
    return " ".join(sorted(token for token in normalize_name(value).split() if token != "and"))


def canonical_id(name: str) -> str:
    token = re.sub(r"[^A-Z0-9]+", "_", normalize_name(name).upper()).strip("_")
    if token:
        return f"DISH_{token[:64]}"
    return "DISH_" + hashlib.sha256(name.encode()).hexdigest()[:16].upper()


def rows(path: Path, sheet: str) -> list[dict[str, Any]]:
    workbook = load_workbook(path, read_only=True, data_only=True)
    try:
        worksheet = workbook[sheet]
        iterator = worksheet.iter_rows(values_only=True)
        headers = [str(value) for value in next(iterator)]
        return [
            dict(zip(headers, values, strict=False))
            for values in iterator
            if any(value is not None and value != "" for value in values)
        ]
    finally:
        workbook.close()


def sheet_inventory(path: Path) -> list[dict[str, Any]]:
    workbook = load_workbook(path, read_only=True, data_only=True)
    try:
        inventory = []
        for worksheet in workbook.worksheets:
            iterator = worksheet.iter_rows(values_only=True)
            headers = [str(value) for value in next(iterator, ())]
            row_count = sum(
                1
                for values in iterator
                if any(value is not None and value != "" for value in values)
            )
            inventory.append({"sheet": worksheet.title, "rows": row_count, "columns": headers})
        return inventory
    finally:
        workbook.close()


@dataclass(frozen=True)
class AuditFinding:
    severity: str
    dataset: str
    check: str
    count: int
    detail: str


def _missing_fk(
    child_rows: Iterable[dict[str, Any]],
    child_key: str,
    parent_rows: Iterable[dict[str, Any]],
    parent_key: str,
) -> int:
    parents = {row[parent_key] for row in parent_rows}
    return sum(row.get(child_key) not in parents for row in child_rows)


def audit_dataset(path: Path, label: str) -> dict[str, Any]:
    inventory = sheet_inventory(path)
    sheet_names = {entry["sheet"] for entry in inventory}
    required = {
        "DATA_households",
        "DATA_users",
        "DATA_food_preferences",
        "DATA_meal_history",
        "DATA_recommendation_events",
    }
    findings: list[AuditFinding] = []
    missing_sheets = sorted(required - sheet_names)
    if missing_sheets:
        findings.append(
            AuditFinding(
                "error", label, "required_sheets", len(missing_sheets), ",".join(missing_sheets)
            )
        )
        return {
            "dataset": label,
            "path": str(path),
            "inventory": inventory,
            "findings": [asdict(row) for row in findings],
        }

    loaded = {name: rows(path, name) for name in sheet_names if name.startswith("DATA_")}
    for name, values in loaded.items():
        primary_key = next(iter(values[0])) if values else None
        if primary_key:
            ids = [row[primary_key] for row in values]
            duplicates = len(ids) - len(set(ids))
            if duplicates:
                findings.append(
                    AuditFinding("error", label, f"{name}.duplicate_pk", duplicates, primary_key)
                )

    missing_user_households = _missing_fk(
        loaded["DATA_users"], "household_id", loaded["DATA_households"], "household_id"
    )
    missing_history_households = _missing_fk(
        loaded["DATA_meal_history"], "household_id", loaded["DATA_households"], "household_id"
    )
    missing_event_households = _missing_fk(
        loaded["DATA_recommendation_events"],
        "household_id",
        loaded["DATA_households"],
        "household_id",
    )
    for check, count in (
        ("users.household_fk", missing_user_households),
        ("history.household_fk", missing_history_households),
        ("events.household_fk", missing_event_households),
    ):
        if count:
            findings.append(AuditFinding("error", label, check, count, "orphan rows"))

    fk_checks = (
        ("members.household_fk", "DATA_members", "household_id", "DATA_households", "household_id"),
        (
            "preferences.household_fk",
            "DATA_food_preferences",
            "household_id",
            "DATA_households",
            "household_id",
        ),
        (
            "regional.household_fk",
            "DATA_regional_taste",
            "household_id",
            "DATA_households",
            "household_id",
        ),
        (
            "exclusions.household_fk",
            "DATA_exclusions",
            "household_id",
            "DATA_households",
            "household_id",
        ),
        (
            "consumers.meal_fk",
            "DATA_meal_consumers",
            "meal_event_id",
            "DATA_meal_history",
            "meal_event_id",
        ),
        ("events.user_fk", "DATA_recommendation_events", "user_id", "DATA_users", "user_id"),
    )
    for check, child, child_key, parent, parent_key in fk_checks:
        if child not in loaded or parent not in loaded:
            continue
        count = _missing_fk(loaded[child], child_key, loaded[parent], parent_key)
        if count:
            findings.append(AuditFinding("error", label, check, count, "orphan rows"))

    dish_ids = {
        row.get("canonical_dish_id")
        for row in loaded["DATA_meal_history"]
        if row.get("canonical_dish_id")
    }
    event_dishes = {
        row.get("dish_id") for row in loaded["DATA_recommendation_events"] if row.get("dish_id")
    }
    findings.append(
        AuditFinding(
            "info", label, "dish_namespace", len(dish_ids | event_dishes), "unique dish ids"
        )
    )
    findings.append(
        AuditFinding(
            "warning",
            label,
            "synthetic_provenance",
            len(loaded["DATA_meal_history"]) + len(loaded["DATA_recommendation_events"]),
            "AI-generated rows are suitable for pipeline validation, not production-lift claims",
        )
    )
    return {
        "dataset": label,
        "path": str(path),
        "inventory": inventory,
        "findings": [asdict(row) for row in findings],
    }


def _json_list(value: Any) -> list[str]:
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    try:
        parsed = json.loads(str(value))
        return [str(item) for item in parsed] if isinstance(parsed, list) else [str(parsed)]
    except json.JSONDecodeError:
        return [str(value)]


def _state_regions(catalog: dict[str, Any]) -> dict[str, str]:
    return {row["state_id"]: row["region"] for row in catalog["states"]}


def _recipe_metadata(recipe: dict[str, Any]) -> dict[str, Any]:
    ingredients = [str(value).split(" — ", 1)[0] for value in recipe.get("ingredients", [])]
    normalized_ingredients = {normalize_name(value).replace(" ", "_") for value in ingredients}
    diet = str(recipe.get("diet") or "").casefold()
    diet_types = {
        "veg": ["vegetarian"],
        "vegetarian": ["vegetarian"],
        "vegan": ["vegan"],
        "non_veg": ["nonvegetarian"],
        "non-veg": ["nonvegetarian"],
    }.get(diet, [])
    allergens = sorted(
        {
            allergen
            for ingredient in ingredients
            for token, allergen in ALLERGEN_INGREDIENTS.items()
            if token in ingredient.casefold()
        }
    )
    raw_spice_level = recipe.get("spice_level")
    spice_level = None
    if raw_spice_level not in (None, ""):
        spice_level = max(1, min(5, int(raw_spice_level)))
    spice_profiles = [
        group
        for group, tokens in SPICE_GROUPS.items()
        if normalized_ingredients & tokens
    ]
    if spice_level is not None:
        spice_profiles.append(
            "mild" if spice_level <= 2 else "medium" if spice_level == 3 else "hot"
        )
    nutrition_traits = [
        trait
        for trait, tokens in NUTRITION_TRAITS.items()
        if any(any(token in ingredient for token in tokens) for ingredient in normalized_ingredients)
    ]
    attributes = recipe.get("attribute_basis", {})
    return {
        "ingredients": ingredients,
        "diet_types": diet_types,
        "allergens": allergens,
        "spice_level": spice_level,
        "spice_profiles": sorted(set(spice_profiles)),
        "nutrition_traits": sorted(set(nutrition_traits)),
        "dish_categories": sorted(
            str(value) for value in attributes.get("dish_category", []) if value
        ),
        "cooking_methods": sorted(
            str(value) for value in attributes.get("cooking_method", []) if value
        ),
        "cook_minutes": int(recipe.get("total_mins") or 0) or None,
    }


def build_ontology(
    catalog_path: Path, primary_workbook: Path, enrichment_workbook: Path, recipes_path: Path
) -> tuple[dict[str, Any], dict[str, str]]:
    catalog = json.loads(catalog_path.read_text())
    recipes = json.loads(recipes_path.read_text())
    recipes_by_name = {lookup_key(name): value for name, value in recipes.items()}
    dishes: dict[str, dict[str, Any]] = {}
    name_to_id: dict[str, str] = {}

    for source in catalog["dishes"]:
        dish_id = source["dish_id"]
        name = source["dish_name"]
        recipe = recipes_by_name.get(lookup_key(name), {})
        ingredients, recipe_diets, allergens = _recipe_metadata(recipe)
        diets = recipe_diets or [
            "vegetarian" if tag == "veg" else str(tag) for tag in source.get("diet_tags", [])
        ]
        cuisine = str(recipe.get("cuisine") or "")
        dishes[dish_id] = {
            "id": dish_id,
            "name": name,
            "aliases": [],
            "ingredients": ingredients,
            "allergens": allergens,
            "diet_types": diets,
            "cuisines": [cuisine] if cuisine else [],
            "regions": [CUISINE_REGIONS[cuisine]] if cuisine in CUISINE_REGIONS else [],
            "observed_regions": [],
            "meal_slots": [str(value).casefold() for value in source.get("slots", [])],
            "cooking_methods": recipe.get("attribute_basis", {}).get("cooking_method", []),
            "source_datasets": ["dataset_1_catalog"],
        }
        name_to_id[lookup_key(name)] = dish_id

    state_region = _state_regions(catalog)
    for workbook, source_name in (
        (primary_workbook, "dataset_1"),
        (enrichment_workbook, "dataset_2"),
    ):
        households = {row["household_id"]: row for row in rows(workbook, "DATA_households")}
        history = rows(workbook, "DATA_meal_history")
        stats: dict[str, dict[str, Counter[str]]] = defaultdict(lambda: defaultdict(Counter))
        raw_names: dict[str, Counter[str]] = defaultdict(Counter)
        for event in history:
            normalized = lookup_key(str(event["dish_raw_name"]))
            dish_id = name_to_id.get(normalized)
            if dish_id is None:
                dish_id = canonical_id(str(event["dish_raw_name"]))
                name_to_id[normalized] = dish_id
            raw_names[dish_id][str(event["dish_raw_name"])] += 1
            stats[dish_id]["slots"][str(event["meal_slot"]).casefold()] += 1
            household = households.get(event["household_id"], {})
            state = str(household.get("current_state_id") or "")
            region = state_region.get(state, state.casefold())
            if region:
                stats[dish_id]["regions"][region] += 1
            if dish_id not in dishes:
                name = str(event["dish_raw_name"])
                recipe = recipes_by_name.get(normalized, {})
                is_non_veg = bool(set(normalized.split()) & NON_VEG_WORDS)
                ingredients, recipe_diets, allergens = _recipe_metadata(recipe)
                cuisine = str(recipe.get("cuisine") or "")
                dishes[dish_id] = {
                    "id": dish_id,
                    "name": name,
                    "aliases": [],
                    "ingredients": ingredients,
                    "allergens": allergens,
                    "diet_types": recipe_diets
                    or (["nonvegetarian"] if is_non_veg else ["unknown"]),
                    "cuisines": [cuisine] if cuisine else [],
                    "regions": [CUISINE_REGIONS[cuisine]] if cuisine in CUISINE_REGIONS else [],
                    "observed_regions": [],
                    "meal_slots": [],
                    "cooking_methods": recipe.get("attribute_basis", {}).get("cooking_method", []),
                    "source_datasets": [],
                }
            if source_name not in dishes[dish_id]["source_datasets"]:
                dishes[dish_id]["source_datasets"].append(source_name)

        for dish_id, dimensions in stats.items():
            if not dishes[dish_id]["meal_slots"]:
                dishes[dish_id]["meal_slots"] = sorted(dimensions["slots"])
            dishes[dish_id]["observed_regions"] = [
                name for name, _ in dimensions["regions"].most_common(4)
            ]
            if not dishes[dish_id]["regions"]:
                dishes[dish_id]["regions"] = dishes[dish_id]["observed_regions"]
            aliases = [
                name
                for name, _ in raw_names[dish_id].most_common()
                if name != dishes[dish_id]["name"]
            ]
            dishes[dish_id]["aliases"] = aliases

    ordered = sorted(dishes.values(), key=lambda row: row["id"])
    nodes = []
    relations = []
    seen_nodes: set[str] = set()
    for dish in ordered:
        nodes.append({"id": dish["id"], "type": "dish", "name": dish["name"]})
        seen_nodes.add(dish["id"])
        relation_dimensions = (
            ("ingredients", "ingredient", "contains"),
            ("cuisines", "cuisine", "belongs_to"),
            ("regions", "region", "eaten_in"),
            ("meal_slots", "meal_slot", "served_at"),
            ("diet_types", "diet_type", "compatible_with"),
            ("cooking_methods", "cooking_technique", "cooked_with"),
        )
        for field, node_type, relation in relation_dimensions:
            for value in dish[field]:
                target = f"{node_type.upper()}_{canonical_id(str(value)).removeprefix('DISH_')}"
                if target not in seen_nodes:
                    nodes.append({"id": target, "type": node_type, "name": value})
                    seen_nodes.add(target)
                relations.append({"source": dish["id"], "relation": relation, "target": target})
    return {
        "version": "indian-food-ontology-v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "nodes": nodes,
        "relations": relations,
        "dishes": ordered,
    }, name_to_id


def _event_weight(event: dict[str, Any]) -> float:
    event_type = str(event.get("event_type") or "").casefold()
    if event_type == "rated" and event.get("feedback_score") is not None:
        return (float(event["feedback_score"]) - 3.0) / 2.0
    return POSITIVE_EVENTS.get(event_type, NEGATIVE_EVENTS.get(event_type, 0.1))


def build_interactions(
    workbook: Path, dataset_name: str, name_to_id: dict[str, str]
) -> list[dict[str, Any]]:
    output: dict[tuple[str, str, str], dict[str, Any]] = {}
    prefix = f"{dataset_name}:"
    valid_households = {str(row["household_id"]) for row in rows(workbook, "DATA_households")}
    for event in rows(workbook, "DATA_recommendation_events"):
        if str(event["household_id"]) not in valid_households:
            continue
        dish_id = str(event["dish_id"])
        key = (prefix + str(event["household_id"]), dish_id, str(event.get("event_at") or ""))
        output[key] = {
            "household_id": key[0],
            "dish_id": dish_id,
            "timestamp": key[2],
            "meal_slot": str(event.get("meal_slot") or "").casefold(),
            "weight": _event_weight(event),
            "event_type": str(event.get("event_type") or ""),
            "source_dataset": dataset_name,
        }
    for event in rows(workbook, "DATA_meal_history"):
        dish_id = name_to_id.get(
            lookup_key(str(event["dish_raw_name"])), str(event["canonical_dish_id"])
        )
        satisfaction = float(event.get("satisfaction_score") or 3)
        weight = max(-1.0, min(1.0, (satisfaction - 3.0) / 2.0))
        key = (prefix + str(event["household_id"]), dish_id, str(event.get("meal_date") or ""))
        row = {
            "household_id": key[0],
            "dish_id": dish_id,
            "timestamp": key[2],
            "meal_slot": str(event.get("meal_slot") or "").casefold(),
            "weight": weight,
            "event_type": "meal_history",
            "source_dataset": dataset_name,
        }
        prior = output.get(key)
        if prior is None or abs(weight) > abs(float(prior["weight"])):
            output[key] = row
    return sorted(
        output.values(), key=lambda row: (row["household_id"], row["timestamp"], row["dish_id"])
    )


def build_household_features(workbook: Path, dataset_name: str) -> list[dict[str, Any]]:
    prefix = f"{dataset_name}:"
    preferences: dict[str, list[str]] = defaultdict(list)
    for row in rows(workbook, "DATA_food_preferences"):
        preferences[str(row["household_id"])].append(
            str(row.get("diet_pattern") or "unknown").casefold()
        )
    regional: dict[str, list[str]] = defaultdict(list)
    for row in rows(workbook, "DATA_regional_taste"):
        regional[str(row["household_id"])].append(
            str(row.get("cuisine_region_id") or "unknown").casefold()
        )
    output = []
    for row in rows(workbook, "DATA_households"):
        household_id = str(row["household_id"])
        output.append(
            {
                "household_id": prefix + household_id,
                "features": sorted(
                    {
                        f"state:{str(row.get('current_state_id') or 'unknown').casefold()}",
                        f"origin:{str(row.get('origin_state_ids') or 'unknown').casefold()}",
                        f"setup:{str(row.get('living_setup') or 'unknown').casefold()}",
                        f"size:{min(8, int(row.get('household_size') or 1))}",
                        *(f"diet:{value}" for value in preferences.get(household_id, ["unknown"])),
                        *(f"region:{value}" for value in regional.get(household_id, [])),
                    }
                ),
            }
        )
    return output


def write_artifacts(
    output_dir: Path,
    audits: list[dict[str, Any]],
    ontology: dict[str, Any],
    interactions: list[dict[str, Any]],
    households: list[dict[str, Any]],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "dataset_audit.json").write_text(
        json.dumps({"datasets": audits}, indent=2, default=str) + "\n"
    )
    (output_dir / "canonical_food_ontology.json").write_text(
        json.dumps(ontology, indent=2, default=str) + "\n"
    )
    (output_dir / "interactions.jsonl").write_text(
        "".join(json.dumps(row, default=str) + "\n" for row in interactions)
    )
    (output_dir / "household_features.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in households)
    )
    manifest: dict[str, Any] = {
        "version": "foofoo-training-v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "synthetic_only": True,
        "ontology_dishes": len(ontology["dishes"]),
        "interactions": len(interactions),
        "positive_interactions": sum(float(row["weight"]) > 0 for row in interactions),
        "negative_interactions": sum(float(row["weight"]) < 0 for row in interactions),
        "households": len(households),
        "sha256": {},
    }
    for name in (
        "dataset_audit.json",
        "canonical_food_ontology.json",
        "interactions.jsonl",
        "household_features.jsonl",
    ):
        manifest["sha256"][name] = hashlib.sha256((output_dir / name).read_bytes()).hexdigest()
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit and canonicalize FooFoo training datasets")
    parser.add_argument("--dataset-1", type=Path, required=True)
    parser.add_argument("--dataset-2", type=Path, required=True)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--recipes", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    audits = [
        audit_dataset(args.dataset_1, "dataset_1"),
        audit_dataset(args.dataset_2, "dataset_2"),
    ]
    ontology, name_to_id = build_ontology(
        args.catalog, args.dataset_1, args.dataset_2, args.recipes
    )
    interactions = build_interactions(args.dataset_1, "dataset_1", name_to_id)
    interactions.extend(build_interactions(args.dataset_2, "dataset_2", name_to_id))
    households = build_household_features(args.dataset_1, "dataset_1")
    households.extend(build_household_features(args.dataset_2, "dataset_2"))
    write_artifacts(args.output_dir, audits, ontology, interactions, households)


if __name__ == "__main__":
    main()
