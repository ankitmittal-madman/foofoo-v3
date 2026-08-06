"""Deterministic comparator; this is the only component allowed to select an override."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .config import Mode, Settings
from .schemas import ConstraintCheck, RecommendationSet


@dataclass(frozen=True)
class Decision:
    selected: dict[str, Any]
    code: str
    reason: str


def existing_metrics(result: dict[str, Any]) -> dict[str, float]:
    metrics = result.get("metrics", {})

    def bounded(value: Any) -> float:
        return max(0.0, min(1.0, float(value)))

    return {
        "quality": bounded(metrics.get("quality_score", result.get("quality_score", 0.5))),
        "confidence": bounded(metrics.get("confidence", result.get("confidence", 0.5))),
        "diversity": bounded(metrics.get("diversity_score", result.get("diversity_score", 0.0))),
        "safety": bounded(metrics.get("safety_score", result.get("safety_score", 1.0))),
        "alignment": bounded(metrics.get("alignment_score", result.get("alignment_score", 0.0))),
    }


def decide(
    existing: dict[str, Any],
    auxiliary: RecommendationSet | None,
    constraints: ConstraintCheck,
    settings: Settings,
) -> Decision:
    if not settings.enabled:
        return Decision(existing, "existing", "auxiliary_disabled")
    if auxiliary is None:
        return Decision(existing, "existing", "auxiliary_unavailable")
    if settings.mode is Mode.SHADOW:
        return Decision(existing, "existing", "shadow_mode_no_override")
    if settings.require_constraint_pass and not constraints.passed:
        return Decision(existing, "existing", "hard_constraint_failed")
    if not auxiliary.items:
        return Decision(existing, "existing", "no_safe_auxiliary_candidates")
    if auxiliary.confidence < settings.min_confidence:
        return Decision(existing, "existing", "confidence_below_threshold")

    old = existing_metrics(existing)
    delta = auxiliary.quality_score - old["quality"]
    if delta < settings.min_delta:
        return Decision(existing, "existing", "improvement_below_threshold")
    if auxiliary.safety_score < old["safety"]:
        return Decision(existing, "existing", "auxiliary_less_safe")
    if auxiliary.diversity_score < old["diversity"]:
        return Decision(existing, "existing", "auxiliary_less_diverse")
    if auxiliary.alignment_score < old["alignment"]:
        return Decision(existing, "existing", "auxiliary_less_aligned")
    if not settings.allow_override:
        return Decision(existing, "existing", "override_disabled")
    return Decision(auxiliary.model_dump(), "auxiliary", "auxiliary_won_policy_gate")
