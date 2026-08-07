"""Deterministic expert-style Indian household research generation.

This role uses checked-in, curated food knowledge and the canonical ontology. It does not call an
LLM, a paid API, or create fake production users. Output is research-only training evidence.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from .auto_engine_types import AutoEngineConfig, InspectionReport

REGION_PROFILES = (
    "north",
    "south",
    "east",
    "west",
    "central",
    "north_east",
)
DIET_PROFILES = ("vegetarian", "mostly_vegetarian", "non_vegetarian", "vegan")
HOUSEHOLD_SHAPES = (
    ("young_couple", ("adult", "adult")),
    ("family_school_child", ("adult", "adult", "school_child")),
    ("multigenerational", ("adult", "adult", "school_child", "elder")),
    ("single_professional", ("adult",)),
    ("elder_couple", ("elder", "elder")),
    ("family_toddler", ("adult", "adult", "toddler")),
)
SLOTS = ("breakfast", "lunch", "dinner")
SEASONS = ("summer", "monsoon", "winter")
RESEARCH_PROVENANCE = (
    "curated:FAO_India_food_based_dietary_guidelines",
    "curated:ICMR_NIN_Indian_Food_Composition_Tables",
    "supplied:FooFoo_AI_prepared_household_datasets",
    "method:deterministic_expert_templates",
)


def _compatible(dish: dict[str, Any], *, region: str, diet: str, slot: str) -> bool:
    slots = {str(value).lower() for value in dish.get("meal_slots", [])}
    regions = {str(value).lower() for value in dish.get("regions", [])}
    if slots and slot not in slots:
        return False
    if not _diet_compatible(dish, diet):
        return False
    return not regions or region in regions


def _diet_compatible(dish: dict[str, Any], diet: str) -> bool:
    diets = {str(value).lower() for value in dish.get("diet_types", [])}
    if diet in {"vegetarian", "mostly_vegetarian"} and not diets.intersection(
        {"veg", "vegetarian", "vegan"}
    ):
        return False
    return not (diet == "vegan" and "vegan" not in diets)


def _allergy_safe(dish: dict[str, Any], allergies: list[str]) -> bool:
    dish_allergens = {str(value).lower() for value in dish.get("allergens", [])}
    return not dish_allergens.intersection(value.lower() for value in allergies)


def _choose_dish(
    dishes: list[dict[str, Any]],
    *,
    region: str,
    diet: str,
    allergies: list[str],
    slot: str,
    offset: int,
    excluded: set[str] | None = None,
) -> dict[str, Any]:
    safe_dishes = [dish for dish in dishes if _allergy_safe(dish, allergies)]
    compatible = [
        dish for dish in safe_dishes if _compatible(dish, region=region, diet=diet, slot=slot)
    ]
    slot_and_diet = [
        dish
        for dish in safe_dishes
        if _diet_compatible(dish, diet)
        and (not dish.get("meal_slots") or slot in {str(v).lower() for v in dish["meal_slots"]})
    ]
    diet_safe = [dish for dish in safe_dishes if _diet_compatible(dish, diet)]
    pools = (compatible, slot_and_diet, diet_safe, safe_dishes)
    if not any(pools):
        raise RuntimeError("canonical ontology has no allergy-safe dish for research persona")
    excluded_ids = excluded or set()
    for candidates in pools:
        unseen = [dish for dish in candidates if dish["id"] not in excluded_ids]
        if unseen:
            return unseen[offset % len(unseen)]
    pool = next(candidates for candidates in pools if candidates)
    return pool[offset % len(pool)]


def generate_research_records(
    inspection: InspectionReport,
    ontology: dict[str, Any],
    config: AutoEngineConfig,
) -> list[dict[str, Any]]:
    """Generate bounded records only when DB inspection identified coverage gaps."""
    if not inspection.enrichment_targets:
        return []
    existing = {row.entity_type: row.usable_records for row in inspection.rows}
    if (
        existing.get("research_household_personas", 0) >= config.research_household_limit
        and existing.get("research_interactions", 0) >= config.research_interaction_limit
        and existing.get("research_weekly_plans", 0) >= config.research_household_limit
    ):
        return []
    dishes = sorted(ontology.get("dishes", []), key=lambda row: row["id"])
    if not dishes:
        raise RuntimeError("canonical ontology contains no dishes; research generation refused")
    dishes_by_id = {dish["id"]: dish for dish in dishes}

    region_counts = Counter(
        str(region).lower() for dish in dishes for region in dish.get("regions", []) if region
    )
    ontology_regions = tuple(
        region
        for region, _count in sorted(region_counts.items(), key=lambda item: (-item[1], item[0]))[
            :8
        ]
    )
    region_profiles = ontology_regions or REGION_PROFILES
    records: list[dict[str, Any]] = []
    household_contexts: list[dict[str, Any]] = []
    household_count = config.research_household_limit
    for index in range(household_count):
        region = region_profiles[index % len(region_profiles)]
        diet = DIET_PROFILES[index % len(DIET_PROFILES)]
        shape, age_groups = HOUSEHOLD_SHAPES[index % len(HOUSEHOLD_SHAPES)]
        household_id = f"expert-hh-{index + 1:03d}"
        season = SEASONS[index % len(SEASONS)]
        allergies = ["peanut"] if index % 11 == 0 else (["dairy"] if index % 13 == 0 else [])
        nutrition_needs: list[str] = []
        if "elder" in age_groups:
            nutrition_needs.extend(("easy_digest", "moderate_sodium"))
        if "school_child" in age_groups or "toddler" in age_groups:
            nutrition_needs.append("protein_variety")
        household = {
            "record_type": "household_persona",
            "household_id": household_id,
            "region": region,
            "diet": diet,
            "household_shape": shape,
            "age_groups": list(age_groups),
            "allergies": allergies,
            "nutrition_needs": nutrition_needs or ["balanced_home_meal"],
            "weekday_cook_minutes": (15, 25, 35, 45)[index % 4],
            "weekend_cook_minutes": (30, 60, 90)[index % 3],
            "cooking_style": ("pressure_cooker", "stovetop", "batch_cooking")[index % 3],
            "equipment": ["stovetop", ("pressure_cooker", "mixer", "microwave")[index % 3]],
            "repetition_tolerance": ("low", "medium", "high")[index % 3],
            "spice_preference": (1, 2, 3, 4)[index % 4],
            "season": season,
            "features": [
                f"region:{region}",
                f"diet:{diet}",
                f"shape:{shape}",
                f"season:{season}",
                f"repetition:{('low', 'medium', 'high')[index % 3]}",
            ],
        }
        records.append(
            {
                "target_table": "research.household_personas",
                "record_key": household_id,
                "payload": household,
                "explanation": "Coverage-balanced household planning persona; not a real user.",
            }
        )
        household_contexts.append(
            {"household_id": household_id, "region": region, "diet": diet, "allergies": allergies}
        )
        for member_index, age_group in enumerate(age_groups):
            records.append(
                {
                    "target_table": "research.user_personas",
                    "record_key": f"{household_id}:member-{member_index + 1}",
                    "payload": {
                        "record_type": "user_persona",
                        "household_id": household_id,
                        "member_id": f"member-{member_index + 1}",
                        "age_group": age_group,
                        "diet": diet,
                        "allergies": allergies,
                    },
                    "explanation": "Synthetic member role attached to a research household.",
                }
            )

        weekly: list[dict[str, str]] = []
        household_dishes: list[str] = []
        used_dishes: set[str] = set()
        for day in range(7):
            for slot_index, slot in enumerate(("lunch", "dinner")):
                dish = _choose_dish(
                    dishes,
                    region=region,
                    diet=diet,
                    allergies=allergies,
                    slot=slot,
                    offset=index * 7 + day * 2 + slot_index,
                    excluded=used_dishes,
                )
                weekly.append({"day": str(day + 1), "slot": slot, "dish_id": dish["id"]})
                household_dishes.append(dish["id"])
                used_dishes.add(dish["id"])
        records.append(
            {
                "target_table": "research.weekly_plans",
                "record_key": f"{household_id}:week-1",
                "payload": {
                    "record_type": "weekly_plan",
                    "household_id": household_id,
                    "season": season,
                    "region": region,
                    "meals": weekly,
                    "dish_ids": household_dishes,
                    "repeat_count": len(household_dishes) - len(set(household_dishes)),
                    "regional_match_ratio": round(
                        sum(
                            not dishes_by_id[meal["dish_id"]].get("regions")
                            or region
                            in {
                                str(value).lower()
                                for value in dishes_by_id[meal["dish_id"]]["regions"]
                            }
                            for meal in weekly
                        )
                        / len(weekly),
                        4,
                    ),
                },
                "explanation": "Fourteen-slot weekly plan with explicit repetition evidence.",
            }
        )

        for slot_index, slot in enumerate(SLOTS):
            dish = _choose_dish(
                dishes,
                region=region,
                diet=diet,
                allergies=allergies,
                slot=slot,
                offset=index * 3 + slot_index,
            )
            records.append(
                {
                    "target_table": "research.meal_examples",
                    "record_key": f"{household_id}:{slot}",
                    "payload": {
                        "record_type": "meal_example",
                        "household_id": household_id,
                        "dish_id": dish["id"],
                        "dish_name": dish["name"],
                        "meal_slot": slot,
                        "region": region,
                        "regional_match": not dish.get("regions")
                        or region in {str(value).lower() for value in dish["regions"]},
                        "season": season,
                        "pantry_items": dish.get("ingredients", [])[:6],
                        "diet_types": dish.get("diet_types", []),
                        "allergens": dish.get("allergens", []),
                        "nutrition_traits": dish.get("nutrition_traits", []),
                        "leftover_intent": index % 4 == 0 and slot == "dinner",
                    },
                    "explanation": "Ontology-backed meal-slot and pantry scenario.",
                }
            )

    interaction_limit = config.research_interaction_limit
    event_cycle = (
        ("cooked", 1.0),
        ("liked", 0.8),
        ("planned", 0.6),
        ("skipped", -0.7),
        ("rejected", -1.0),
        ("repeat_fatigue", -0.55),
    )
    for index in range(interaction_limit):
        household_context = household_contexts[index % household_count]
        household_id = household_context["household_id"]
        slot = SLOTS[index % len(SLOTS)]
        dish = _choose_dish(
            dishes,
            region=household_context["region"],
            diet=household_context["diet"],
            allergies=household_context["allergies"],
            slot=slot,
            offset=index * 7 + index // household_count,
        )
        event_type, weight = event_cycle[index % len(event_cycle)]
        records.append(
            {
                "target_table": "research.interactions",
                "record_key": f"{household_id}:{dish['id']}:{index:04d}",
                "payload": {
                    "record_type": "interaction",
                    "household_id": household_id,
                    "dish_id": dish["id"],
                    "dish_name": dish["name"],
                    "event_type": event_type,
                    "weight": weight,
                    "meal_slot": slot,
                    "region": household_context["region"],
                    "regional_match": not dish.get("regions")
                    or household_context["region"]
                    in {str(value).lower() for value in dish["regions"]},
                    "day_type": "weekend" if index % 7 in {5, 6} else "weekday",
                },
                "explanation": "Balanced positive, negative, rejection and repetition signal.",
            }
        )

    for context in household_contexts:
        for allergy in context["allergies"]:
            unsafe = next(
                (
                    dish
                    for dish in dishes
                    if allergy in {str(value).lower() for value in dish.get("allergens", [])}
                ),
                None,
            )
            if unsafe is None:
                continue
            records.append(
                {
                    "target_table": "research.constraint_examples",
                    "record_key": f"{context['household_id']}:allergy:{allergy}:{unsafe['id']}",
                    "payload": {
                        "record_type": "hard_constraint",
                        "household_id": context["household_id"],
                        "dish_id": unsafe["id"],
                        "constraint_type": "allergy",
                        "constraint_value": allergy,
                        "expected_outcome": "block",
                    },
                    "explanation": "Explicit allergy example whose only valid outcome is blocking.",
                }
            )

    substitutes = [dish for dish in dishes if dish.get("substitutes")]
    for dish in substitutes[: min(48, len(substitutes))]:
        substitute_id = sorted(dish["substitutes"])[0]
        records.append(
            {
                "target_table": "research.substitution_examples",
                "record_key": f"{dish['id']}:{substitute_id}",
                "payload": {
                    "record_type": "substitution",
                    "dish_id": dish["id"],
                    "substitute_dish_id": substitute_id,
                    "reason": "ontology_supported_household_substitution",
                },
                "explanation": "Canonical substitution used as explicit graph evidence.",
            }
        )
    return records


def provenance_tags() -> tuple[str, ...]:
    return RESEARCH_PROVENANCE
