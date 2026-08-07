"""Dated dish and food-attribute rhythm for post-eligibility ranking.

The database materializes explicit outcomes and served impressions separately. This module only
interprets that bounded read model for one requested meal moment; it never changes hard safety or
eligibility. Exact dishes, cuisines, richness tags, and cooking methods retain separate evidence
so a rich weekday lunch does not suppress dinner or a weekend meal.
"""

from __future__ import annotations

import datetime
from typing import Any, Iterable


MAIN_SLOTS = {"breakfast", "lunch", "dinner"}
DIMENSION_WEIGHTS = {
    "dish": 1.0,
    "cuisine": 0.55,
    "richness": 0.35,
    "cooking_method": 0.25,
}
DEFAULT_SPACING_DAYS = {
    "dish": {"weekday": 5.0, "weekend": 7.0},
    "cuisine": {"weekday": 3.0, "weekend": 7.0},
    "richness": {"weekday": 2.0, "weekend": 3.0},
    "cooking_method": {"weekday": 2.0, "weekend": 3.0},
}


def normalize_key(value: Any) -> str:
    """Return the same compact case-insensitive key used by the SQL read model."""
    return " ".join(str(value or "").casefold().split())


def _date(value: Any) -> datetime.date | None:
    try:
        return datetime.date.fromisoformat(str(value)[:10])
    except (TypeError, ValueError):
        return None


def _bounded_int(value: Any, maximum: int = 1000) -> int:
    try:
        return max(0, min(maximum, int(value or 0)))
    except (TypeError, ValueError):
        return 0


def _prior_date(
    state: dict[str, Any], array_field: str, fallback_field: str, planned_date: datetime.date
) -> datetime.date | None:
    values = state.get(array_field)
    parsed = []
    if isinstance(values, list):
        parsed = [item for item in (_date(value) for value in values[:100]) if item is not None]
    prior = [value for value in parsed if value < planned_date]
    if prior:
        return max(prior)
    fallback = _date(state.get(fallback_field))
    return fallback if fallback is not None and fallback < planned_date else None


def normalize_state(value: Any) -> dict[tuple[str, str, str, str], dict[str, Any]]:
    """Index a bounded, untrusted Edge payload by slot/day-type/dimension/entity."""
    if not isinstance(value, list):
        return {}
    result: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for raw in value[:1000]:
        if not isinstance(raw, dict):
            continue
        slot = normalize_key(raw.get("meal_slot"))
        day_type = normalize_key(raw.get("day_type"))
        dimension = normalize_key(raw.get("dimension_code"))
        entity = normalize_key(raw.get("entity_key"))
        if (
            slot in MAIN_SLOTS
            and day_type in {"weekday", "weekend"}
            and dimension in DIMENSION_WEIGHTS
            and entity
        ):
            result[(slot, day_type, dimension, entity)] = raw
    return result


def prepare_context(ctx: dict[str, Any]) -> dict[str, Any]:
    """Attach normalized temporal inputs once so every candidate does not reparse the payload."""
    if "_temporal_attribute_index" not in ctx:
        ctx["_temporal_attribute_index"] = normalize_state(ctx.get("temporal_attribute_state"))
    planned_date = _date(ctx.get("date"))
    if planned_date is not None:
        ctx["_planned_meal_date"] = planned_date
    day_type = normalize_key(ctx.get("day_type"))
    if day_type not in {"weekday", "weekend"}:
        weekday = str(ctx.get("weekday") or "")
        day_type = "weekend" if weekday in {"Saturday", "Sunday"} else "weekday"
    ctx["_meal_day_type"] = day_type
    return ctx


def dish_entities(dish: Any) -> dict[str, set[str]]:
    """Project one catalogue dish onto the temporal dimensions understood by the database."""
    return {
        "dish": {normalize_key(getattr(dish, "name", ""))},
        "cuisine": {normalize_key(getattr(dish, "cuisine", ""))},
        "richness": {
            normalize_key(value) for value in (getattr(dish, "richness", None) or [])
        },
        "cooking_method": {
            normalize_key(value) for value in (getattr(dish, "cooking_method", None) or [])
        },
    }


def _state_contribution(
    state: dict[str, Any],
    planned_date: datetime.date,
    dimension: str,
    day_type: str,
) -> tuple[float, float, float]:
    """Return explicit spacing, learned-due reward, and weak exposure pressure."""
    last_positive = _prior_date(
        state, "positive_meal_dates_28d", "last_positive_meal_date", planned_date
    )
    last_negative = _prior_date(
        state, "negative_meal_dates_28d", "last_negative_meal_date", planned_date
    )
    last_exposed = _prior_date(
        state, "exposure_meal_dates_14d", "last_exposed_meal_date", planned_date
    )
    try:
        learned = float(state.get("mean_positive_spacing_days") or 0.0)
    except (TypeError, ValueError):
        learned = 0.0
    target = max(
        1.0,
        min(28.0, learned if learned > 0 else DEFAULT_SPACING_DAYS[dimension][day_type]),
    )
    weight = DIMENSION_WEIGHTS[dimension]
    explicit = due = exposure = 0.0
    if last_positive is not None:
        elapsed = max(0, (planned_date - last_positive).days)
        if elapsed < target:
            explicit -= 0.20 * weight * (target - elapsed) / target
        elif (
            _bounded_int(state.get("explicit_positive_count_28d")) >= 2
            and elapsed <= 2.0 * target
        ):
            # A repeated observed rhythm may become gently due. One isolated choice never creates
            # a recurring schedule, and this reward remains much smaller than a negative signal.
            due += 0.06 * weight * (1.0 - abs(elapsed - target) / target)
    if last_negative is not None:
        elapsed = max(0, (planned_date - last_negative).days)
        if elapsed < 14:
            explicit -= 0.16 * weight * (14 - elapsed) / 14
    exposure_count = _bounded_int(state.get("exposure_count_14d"), 100)
    if last_exposed is not None and exposure_count > 0:
        elapsed = max(0, (planned_date - last_exposed).days)
        if elapsed < 7:
            exposure -= min(0.04 * weight, 0.01 * exposure_count * weight) * (7 - elapsed) / 7
    return explicit, due, exposure


def dish_contribution(dish: Any, ctx: dict[str, Any]) -> dict[str, Any]:
    """Explain the bounded temporal adjustment for one safe catalogue candidate."""
    prepare_context(ctx)
    planned_date = ctx.get("_planned_meal_date")
    index = ctx.get("_temporal_attribute_index")
    slot = normalize_key(ctx.get("slot"))
    day_type = str(ctx.get("_meal_day_type"))
    if not isinstance(planned_date, datetime.date) or not isinstance(index, dict):
        return {"total": 0.0, "explicit": 0.0, "due": 0.0, "exposure": 0.0, "dimensions": []}

    dimension_parts = []
    explicit_total = due_total = exposure_total = 0.0
    for dimension, entity_keys in dish_entities(dish).items():
        candidates = []
        for entity_key in entity_keys:
            state = index.get((slot, day_type, dimension, entity_key))
            if state:
                explicit, due, exposure = _state_contribution(
                    state, planned_date, dimension, day_type
                )
                candidates.append((explicit + due + exposure, explicit, due, exposure, entity_key))
        if not candidates:
            continue
        # Multiple richness/method tags describe the same dish. Use the strongest matching tag
        # per dimension so enrichment density cannot multiply a household signal.
        total, explicit, due, exposure, entity_key = max(
            candidates, key=lambda item: abs(item[0])
        )
        explicit_total += explicit
        due_total += due
        exposure_total += exposure
        dimension_parts.append(
            {
                "dimension": dimension,
                "entity": entity_key,
                "contribution": round(total, 6),
            }
        )

    explicit_total = max(-0.30, min(0.0, explicit_total))
    due_total = max(0.0, min(0.08, due_total))
    exposure_total = max(-0.08, min(0.0, exposure_total))
    total = max(-0.38, min(0.08, explicit_total + due_total + exposure_total))
    return {
        "total": total,
        "explicit": explicit_total,
        "due": due_total,
        "exposure": exposure_total,
        "dimensions": sorted(
            dimension_parts, key=lambda item: abs(item["contribution"]), reverse=True
        )[:4],
    }


def plate_contribution(dishes: Iterable[Any], ctx: dict[str, Any]) -> dict[str, Any]:
    """Average component evidence so a two-dish plate is not penalized twice for its size."""
    parts = [dish_contribution(dish, ctx) for dish in dishes]
    if not parts:
        return {"total": 0.0, "explicit": 0.0, "due": 0.0, "exposure": 0.0, "dimensions": []}
    count = len(parts)
    dimensions = [item for part in parts for item in part["dimensions"]]
    return {
        "total": sum(part["total"] for part in parts) / count,
        "explicit": sum(part["explicit"] for part in parts) / count,
        "due": sum(part["due"] for part in parts) / count,
        "exposure": sum(part["exposure"] for part in parts) / count,
        "dimensions": sorted(
            dimensions, key=lambda item: abs(item["contribution"]), reverse=True
        )[:4],
    }
