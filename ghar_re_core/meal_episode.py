"""Complete-meal episode projection and practicality intelligence.

This module is additive to the frozen dish scorer. It turns already-safe plates into the final
product decision object, then re-ranks those objects by an explicit v1 success estimate:

    P(success) = P(choose) * P(execute | choose) * P(no regret | execute)

The execution and regret models are deliberately transparent rule models until real outcome data
can support calibrated learned artifacts. Every estimate carries its feature and model version;
none of these soft terms can restore a dish removed by the upstream hard-safety filters.
"""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any, Iterable

from ghar_re_core import episode_grammar, pairing


EPISODE_MODEL_VERSION = "episode-practicality-rule-v1"
INTENT_CODES = (
    "routine",
    "quick",
    "light",
    "comfort",
    "indulgent",
    "discovery",
    "leftover_use",
    "festive",
    "recovery",
)
_RICH_TAGS = {"buttery", "creamy", "ghee_rich", "coconut_rich", "oily"}
_COMPLEX_METHODS = {"deep_fried", "baked", "grilled", "dum", "stuffed"}


def _sigmoid(value: float) -> float:
    return 1.0 / (1.0 + math.exp(-max(-30.0, min(30.0, value))))


def _softmax(values: list[float]) -> list[float]:
    if not values:
        return []
    peak = max(values)
    exp = [math.exp(min(30.0, value - peak)) for value in values]
    total = sum(exp) or 1.0
    return [value / total for value in exp]


def _plate_dishes(plate: dict[str, Any]) -> list[Any]:
    if plate["form"] == "pair":
        return [plate["dry"], plate["liquid"]]
    return [plate["hero"]]


def infer_intent(household: dict[str, Any], ctx: dict[str, Any]) -> dict[str, float]:
    """Return a normalized, inspectable latent-intent prior from request-time evidence."""
    weights = dict.fromkeys(INTENT_CODES, 0.05)
    weights["routine"] = 0.42
    slot = ctx.get("slot", "dinner")
    weekday = ctx.get("weekday", "Monday")
    time_budget = ctx.get("time_budget_minutes")
    modes = set(ctx.get("active_modes") or [])
    objective = household.get("q15_objective")
    weather = ctx.get("weather_condition")

    if time_budget is not None and float(time_budget) <= 35:
        weights["quick"] += 0.6
    if household.get("q13_who_cooks") == "order_tiffin":
        weights["quick"] += 0.35
    if weekday not in ("Saturday", "Sunday") and slot == "dinner":
        weights["routine"] += 0.2
        weights["quick"] += 0.15
    if weather == "rain" or ctx.get("is_raining"):
        weights["comfort"] += 0.45
    if objective in ("healthy_living", "into_fitness", "protein_calculator"):
        weights["light"] += 0.3
    if "festival" in modes:
        weights["festive"] += 1.0
    if ctx.get("leftover_dish_names"):
        weights["leftover_use"] += 0.5
    if ctx.get("recovery_mode"):
        weights["recovery"] += 0.7
    if ctx.get("discovery_mode"):
        weights["discovery"] += 0.7

    total = sum(weights.values()) or 1.0
    return {key: round(value / total, 6) for key, value in weights.items()}


def _work_features(
    dishes: Iterable[Any], support: str | None, ctx: dict[str, Any]
) -> dict[str, Any]:
    dishes = list(dishes)
    prep = sum(max(0, int(getattr(dish, "prep_mins", 0) or 0)) for dish in dishes)
    cook = [max(0, int(getattr(dish, "cook_mins", 0) or 0)) for dish in dishes]
    # Parallel cooking is possible for multi-component plates. The critical path is intentionally
    # conservative: all prep plus the longest cook operation, not the implausible sum of all waits.
    critical_path = prep + (max(cook) if cook else 0)
    active_minutes = prep + round(sum(cook) * 0.35)
    methods = {
        method for dish in dishes for method in (getattr(dish, "cooking_method", None) or [])
    }
    all_ingredients = {
        ingredient for dish in dishes for ingredient in getattr(dish, "ingredient_names", [])
    }
    pantry = set(ctx.get("pantry_ingredient_names") or [])
    known_pantry = len(all_ingredients & pantry)
    pantry_coverage = known_pantry / len(all_ingredients) if all_ingredients and pantry else None
    vessel_count = max(1, len(dishes) + (1 if support else 0))
    burner_peak = min(2, max(1, len(dishes)))
    complex_method_count = len(methods & _COMPLEX_METHODS)
    return {
        "active_minutes": active_minutes,
        "critical_path_minutes": critical_path,
        "vessel_count": vessel_count,
        "burner_peak": burner_peak,
        "ingredient_count": len(all_ingredients),
        "complex_method_count": complex_method_count,
        "pantry_coverage": round(pantry_coverage, 4) if pantry_coverage is not None else None,
        "feature_version": EPISODE_MODEL_VERSION,
        "estimation_confidence": 0.65 if pantry else 0.45,
    }


def _richness(dishes: Iterable[Any]) -> float:
    dishes = list(dishes)
    if not dishes:
        return 0.0
    values = []
    for dish in dishes:
        tag_rich = 1.0 if set(getattr(dish, "richness", []) or []) & _RICH_TAGS else 0.0
        heaviness = max(0.0, min(1.0, float(getattr(dish, "heaviness", 0) or 0) / 3.0))
        values.append(0.55 * heaviness + 0.45 * tag_rich)
    return sum(values) / len(values)


def _execution_probability(
    work: dict[str, Any],
    household: dict[str, Any],
    ctx: dict[str, Any],
    familiarity: float,
) -> float:
    time_budget = ctx.get("time_budget_minutes")
    time_overrun = 0.0
    if time_budget is not None:
        time_overrun = max(0.0, work["critical_path_minutes"] - float(time_budget)) / 30.0
    capability = household.get("cook_capability") or ctx.get("cook_capability") or "intermediate"
    skill_adjustment = {"beginner": -0.35, "intermediate": 0.0, "advanced": 0.2}.get(
        capability, 0.0
    )
    pantry_adjustment = 0.0
    if work["pantry_coverage"] is not None:
        pantry_adjustment = 0.8 * (work["pantry_coverage"] - 0.5)
    logit = (
        1.9
        + skill_adjustment
        + 0.65 * familiarity
        + pantry_adjustment
        - 0.025 * work["active_minutes"]
        - 0.18 * max(0, work["vessel_count"] - 2)
        - 0.25 * work["complex_method_count"]
        - 0.9 * time_overrun
    )
    return _sigmoid(logit)


def _cadence_tier(richness: float, work: dict[str, Any], ctx: dict[str, Any]) -> str:
    if "festival" in set(ctx.get("active_modes") or []):
        return "festive"
    if richness >= 0.72 or work["active_minutes"] >= 55:
        return "weekly_rich"
    if richness >= 0.52 or work["active_minutes"] >= 40:
        return "occasional"
    if richness <= 0.28 and work["active_minutes"] <= 28:
        return "daily_staple"
    return "regular_rotation"


def build_meal_episodes(
    plates: list[dict[str, Any]],
    household: dict[str, Any],
    ctx: dict[str, Any],
) -> list[dict[str, Any]]:
    """Project safe plates to versioned episodes and re-rank by predicted successful execution."""
    choose_probs = _softmax(
        [
            float(plate["score"])
            + (
                0.0
                if plate.get("_score_includes_temporal")
                else float(plate.get("_temporal_contribution", 0.0))
            )
            for plate in plates
        ]
    )
    intent = infer_intent(household, ctx)
    episodes: list[dict[str, Any]] = []
    for plate, p_choose in zip(plates, choose_probs, strict=True):
        dishes = _plate_dishes(plate)
        support = plate.get("support")
        grammar = episode_grammar.grammar_for_plate(plate, ctx.get("slot", "dinner"))
        components = [
            {
                "dish_id": dish.id,
                "dish_name": dish.name,
                "component_role": (
                    "dry_hero"
                    if plate["form"] == "pair" and dish is plate["dry"]
                    else "liquid_hero"
                    if plate["form"] == "pair"
                    else "hero"
                ),
                "grammar_role": "primary" if dish_index == 0 else "side",
                "is_required": True,
                "cuisine": dish.cuisine,
                "richness": list(dish.richness or []),
                "cooking_method": list(dish.cooking_method or []),
                "heaviness": dish.heaviness,
            }
            for dish_index, dish in enumerate(dishes)
        ]
        if support:
            components.append(
                {
                    "dish_id": None,
                    "dish_name": support,
                    "component_role": "staple",
                    "grammar_role": "side",
                    "is_required": True,
                }
            )
        episode_grammar.validate_component_roles(
            grammar, [component["grammar_role"] for component in components]
        )
        content = {
            "form": plate["form"],
            "grammar_code": grammar["grammar_code"],
            "grammar_version": grammar["version"],
            "components": [
                (c["dish_id"], c["dish_name"], c["component_role"], c["grammar_role"])
                for c in components
            ],
            "model_version": EPISODE_MODEL_VERSION,
        }
        episode_hash = hashlib.sha256(
            json.dumps(content, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        work = _work_features(dishes, support, ctx)
        richness = _richness(dishes)
        # Cohort-scored, non-experimental plates are a conservative familiarity proxy in v1.
        familiarity = 0.35 if plate.get("experimental") else 0.75
        p_execute = _execution_probability(work, household, ctx, familiarity)
        p_regret = _sigmoid(
            -2.25
            + 0.018 * work["active_minutes"]
            + 0.65 * richness
            + (0.35 if plate.get("experimental") else 0.0)
        )
        p_success = p_choose * p_execute * (1.0 - p_regret)
        cadence_tier = _cadence_tier(richness, work, ctx)
        primary_intent = max(intent, key=lambda code: intent[code])
        reasons = [
            f"{cadence_tier.replace('_', ' ')} for this household context",
            f"about {work['active_minutes']} active minutes",
        ]
        if support:
            reasons.append(f"complete plate with {support}")
        temporal_explanation = plate.get("_temporal_explanation") or {
            "total": 0.0, "explicit": 0.0, "due": 0.0, "exposure": 0.0, "dimensions": []
        }
        if float(temporal_explanation.get("due", 0.0) or 0.0) > 0:
            reasons.insert(0, "fits this meal moment's learned rotation")
        elif float(temporal_explanation.get("total", 0.0) or 0.0) < -0.02:
            reasons.append("spaced against recent similar meals")
        episodes.append(
            {
                "episode_hash": episode_hash,
                "grammar_code": grammar["grammar_code"],
                "grammar_version": grammar["version"],
                "plate_form": plate["form"],
                "display_name": pairing.plate_label(plate),
                "components": components,
                "intent": primary_intent,
                "intent_posterior": intent,
                "practicality": work,
                "cadence_tier": cadence_tier,
                "richness_score": round(richness, 6),
                "temporal_contribution": round(
                    float(temporal_explanation.get("total", 0.0) or 0.0), 6
                ),
                "temporal_explanation": temporal_explanation,
                "predictions": {
                    "p_choose": round(p_choose, 6),
                    "p_execute": round(p_execute, 6),
                    "p_regret": round(p_regret, 6),
                    "p_success": round(p_success, 6),
                    "model_version": EPISODE_MODEL_VERSION,
                    "calibration_status": "rule_baseline_untrained",
                },
                "reasons": reasons[:3],
                "source_plate_score": round(float(plate["score"]), 6),
            }
        )
    episodes.sort(
        key=lambda item: (
            item["predictions"]["p_success"],
            item["source_plate_score"],
            item["episode_hash"],
        ),
        reverse=True,
    )
    for rank, episode in enumerate(episodes, 1):
        episode["rank"] = rank
    return episodes


def build_class_meal_episodes(
    household: dict[str, Any],
    ctx: dict[str, Any],
    class_code: str,
    catalogue: Any,
    count: int = 4,
    exclude_dish_names: list[str] | None = None,
    preference_by_dish: dict[str, float] | None = None,
) -> list[dict[str, Any]]:
    """Build episode fallbacks that preserve a finalized weekly meal class.

    A class option may currently map to a single complete/standalone dish rather than a curated
    multi-component grammar. In that case the v1 episode adds the core's editable regional staple
    for non-standalone dishes. This is explicitly a fallback projection; curated episode rows can
    replace it by content hash without changing the client contract.
    """
    from ghar_re_core.derivation import derive_theta
    from ghar_re_core.meal_planner import dishes_for_class

    options = dishes_for_class(
        household,
        ctx.get("slot", "dinner"),
        class_code,
        catalogue=catalogue,
        n=max(1, min(count, 8)),
        weekday=ctx.get("weekday", "Monday"),
        context=ctx,
        exclude_dish_names=exclude_dish_names or [],
        preference_by_dish=preference_by_dish or {},
    )["options"]
    theta = derive_theta(household)
    plates: list[dict[str, Any]] = []
    for option in options:
        dish = catalogue.get(option["name"])
        if dish is None:
            continue
        form = "standalone" if dish.hero_role == "standalone" else "single"
        plate = {
            "form": form,
            "hero": dish,
            "heroes": {dish.name},
            "score": float(option["score"]),
            "experimental": getattr(dish, "scope_tier", None) == "experimental",
            "_temporal_contribution": float(
                option.get("explanation", {}).get("temporal_contribution", 0.0) or 0.0
            ),
            "_temporal_explanation": {
                "total": float(
                    option.get("explanation", {}).get("temporal_contribution", 0.0) or 0.0
                ),
                "explicit": float(
                    option.get("explanation", {}).get("temporal_explicit_contribution", 0.0)
                    or 0.0
                ),
                "due": float(
                    option.get("explanation", {}).get("temporal_due_contribution", 0.0) or 0.0
                ),
                "exposure": float(
                    option.get("explanation", {}).get("temporal_exposure_contribution", 0.0)
                    or 0.0
                ),
                "dimensions": option.get("explanation", {}).get("temporal_dimensions", []),
            },
            "_score_includes_temporal": True,
        }
        plate["support"] = pairing.default_carb(plate, theta)
        plates.append(plate)
    return build_meal_episodes(plates, household, ctx)
