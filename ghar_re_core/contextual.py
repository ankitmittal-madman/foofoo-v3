"""Governed post-eligibility household context for both dish and complete-meal ranking.

Only authority-labelled request signals are accepted. Explicit health/fitness goals receive a
bounded contribution; inferred weekday time pressure is weaker, confidence-capped, and affects
effort only. Nothing in this module changes diet, allergen, Jain, medical, or other safety gates.
"""

from __future__ import annotations

import datetime
from typing import Any, Iterable

from ghar_re_core import scoring


FEATURE_VERSION = "governed-context-v1"


def _signals(ctx: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = ctx.get("governed_context_signals")
    if not isinstance(rows, list):
        return {}
    result = {}
    now = datetime.datetime.now(datetime.timezone.utc)
    for raw in rows[:20]:
        if not isinstance(raw, dict) or raw.get("feature_version") != FEATURE_VERSION:
            continue
        code = str(raw.get("feature_code") or "")
        authority = str(raw.get("authority") or "")
        allowed_use = str(raw.get("allowed_use") or "")
        correction = str(raw.get("correction_state") or "active")
        try:
            confidence = max(0.0, min(1.0, float(raw.get("confidence", 0.0))))
        except (TypeError, ValueError):
            continue
        if correction == "rejected":
            continue
        expires = raw.get("expires_at")
        if authority == "inferred":
            if correction != "confirmed":
                confidence = min(0.70, confidence)
            if expires and correction != "confirmed":
                try:
                    parsed = datetime.datetime.fromisoformat(str(expires).replace("Z", "+00:00"))
                    if parsed.tzinfo is None:
                        parsed = parsed.replace(tzinfo=datetime.timezone.utc)
                    if parsed <= now:
                        continue
                except ValueError:
                    continue
        if code == "health_objective" and authority == "explicit" and allowed_use == "strong_rank":
            result[code] = {**raw, "confidence": confidence}
        elif (
            code == "weekday_time_pressure"
            and authority == "inferred"
            and allowed_use == "soft_rank"
        ):
            result[code] = {**raw, "confidence": confidence}
    return result


def dish_contribution(dish: Any, ctx: dict[str, Any]) -> dict[str, Any]:
    signals = _signals(ctx)
    reasons = []
    explicit = inferred = 0.0
    objective = signals.get("health_objective")
    if objective:
        value = str(objective.get("value") or "")
        confidence = float(objective["confidence"])
        if value == "healthy_living":
            fit = scoring.gs_light(dish)
            explicit = 0.10 * confidence * (fit - 0.5)
            reasons.append({"feature_code": value, "authority": "explicit", "fit": fit})
        elif value in {"into_fitness", "protein_calculator"}:
            fit = 0.70 * scoring.gs_protein(dish) + 0.30 * scoring.gs_light(dish)
            explicit = 0.10 * confidence * (fit - 0.5)
            reasons.append({"feature_code": value, "authority": "explicit", "fit": fit})

    pressure = signals.get("weekday_time_pressure")
    day_type = str(ctx.get("day_type") or "")
    if not day_type:
        day_type = "weekend" if ctx.get("weekday") in {"Saturday", "Sunday"} else "weekday"
    if pressure and day_type == "weekday":
        try:
            value = max(0.0, min(1.0, float(pressure.get("value", 0.0))))
        except (TypeError, ValueError):
            value = 0.0
        total_mins = getattr(dish, "total_mins", None)
        if total_mins is not None:
            minutes = max(0.0, float(total_mins))
            effort_fit = 1.0 if minutes <= 35 else -1.0 if minutes >= 60 else 1 - 2 * (minutes - 35) / 25
            inferred = 0.05 * float(pressure["confidence"]) * value * effort_fit
            reasons.append(
                {
                    "feature_code": "weekday_time_pressure",
                    "authority": "inferred",
                    "fit": effort_fit,
                }
            )
    explicit = max(-0.05, min(0.05, explicit))
    inferred = max(-0.04, min(0.04, inferred))
    return {
        "total": max(-0.08, min(0.08, explicit + inferred)),
        "explicit": explicit,
        "inferred": inferred,
        "reasons": reasons,
        "feature_version": FEATURE_VERSION,
    }


def plate_contribution(dishes: Iterable[Any], ctx: dict[str, Any]) -> dict[str, Any]:
    parts = [dish_contribution(dish, ctx) for dish in dishes]
    if not parts:
        return {"total": 0.0, "explicit": 0.0, "inferred": 0.0, "reasons": [], "feature_version": FEATURE_VERSION}
    count = len(parts)
    return {
        "total": sum(part["total"] for part in parts) / count,
        "explicit": sum(part["explicit"] for part in parts) / count,
        "inferred": sum(part["inferred"] for part in parts) / count,
        "reasons": [reason for part in parts for reason in part["reasons"]][:4],
        "feature_version": FEATURE_VERSION,
    }


def class_contribution(class_code: str, class_meta: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    """Bounded class-level context so the weekly plan reflects goals before dish reconciliation."""
    signals = _signals(ctx)
    category = str(class_meta.get("category") or "").casefold()
    code = str(class_code).casefold()
    explicit = inferred = 0.0
    reasons = []
    objective = signals.get("health_objective")
    health_like = any(token in category or token in code for token in ("health", "protein", "salad", "light"))
    indulgent = any(token in category or token in code for token in ("rich", "fried", "festive", "indulg"))
    if objective:
        value = str(objective.get("value") or "")
        if value == "healthy_living":
            explicit = 0.08 if health_like else -0.04 if indulgent else 0.0
        elif value in {"into_fitness", "protein_calculator"}:
            protein_like = "protein" in category or "protein" in code
            explicit = 0.08 if protein_like else 0.03 if health_like else -0.04 if indulgent else 0.0
        if explicit:
            reasons.append({"feature_code": value, "authority": "explicit"})
    pressure = signals.get("weekday_time_pressure")
    if pressure and str(ctx.get("day_type")) == "weekday":
        try:
            value = max(0.0, min(1.0, float(pressure.get("value", 0.0))))
        except (TypeError, ValueError):
            value = 0.0
        quick_like = any(token in category or token in code for token in ("quick", "one_pot", "light_repeatable"))
        slow_like = indulgent or "weekend" in code
        direction = 1.0 if quick_like else -1.0 if slow_like else 0.0
        inferred = 0.03 * float(pressure["confidence"]) * value * direction
        if inferred:
            reasons.append({"feature_code": "weekday_time_pressure", "authority": "inferred"})
    return {
        "total": max(-0.10, min(0.10, explicit + inferred)),
        "explicit": explicit,
        "inferred": inferred,
        "reasons": reasons,
        "feature_version": FEATURE_VERSION,
    }
