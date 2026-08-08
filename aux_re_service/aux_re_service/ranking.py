"""Deterministic local weighted reranking, debiasing, and diversity selection."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .safety import check_candidate
from .schemas import Candidate, RecommendationRequest, RecommendationSet


@dataclass(frozen=True)
class ScoredCandidate:
    candidate: Candidate
    score: float
    features: dict[str, float]


def _overlap(left: list[str], right: list[str]) -> float:
    a = {value.casefold() for value in left}
    b = {value.casefold() for value in right}
    return len(a & b) / max(1, len(a | b))


def _preference_fit(candidate: Candidate, request: RecommendationRequest) -> float:
    candidate_signals = candidate.cuisines + candidate.regions + candidate.ingredients
    fits = [_overlap(request.preferences, candidate_signals)]
    fits.extend(
        _overlap(member.preferences, candidate_signals) for member in request.household_members
    )
    nonempty = [value for value in fits if value > 0]
    if not request.preferences and not any(
        member.preferences for member in request.household_members
    ):
        return 0.5
    if not nonempty:
        return 0.0
    # Blend average household satisfaction with the least-satisfied represented member.
    return 0.75 * (sum(fits) / len(fits)) + 0.25 * min(fits)


def _meal_class_fit(candidate: Candidate, request: RecommendationRequest) -> float:
    """Give explicit class actions more authority than dish-projected class evidence."""
    if not candidate.meal_classes:
        return 0.5
    has_sourced_state = bool(
        request.preference_by_direct_class or request.preference_by_projected_class
    )
    scores = []
    for class_code in candidate.meal_classes:
        if has_sourced_state:
            score = 0.75 * request.preference_by_direct_class.get(
                class_code, 0.0
            ) + 0.25 * request.preference_by_projected_class.get(class_code, 0.0)
        else:
            score = request.preference_by_class.get(class_code, 0.0)
        scores.append(max(-1.0, min(1.0, score)))
    return 0.5 + 0.5 * max(scores)


def _governed_context_adjustment(
    candidate: Candidate, request: RecommendationRequest
) -> tuple[float, list[str]]:
    """Signed, bounded post-safety adjustment; rejected/expired inference is a no-op."""
    now = request.timestamp
    adjustment = 0.0
    reasons: list[str] = []
    for signal in request.governed_context_signals:
        if signal.correction_state == "rejected":
            continue
        if signal.expires_at is not None and signal.correction_state != "confirmed":
            expires = signal.expires_at
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=now.tzinfo)
            if expires <= now:
                continue
        if signal.feature_code == "health_objective":
            objective = str(signal.value)
            if objective == "healthy_living":
                adjustment += 0.55 * signal.confidence * (candidate.nutrition_fit - 0.5)
                reasons.append("explicit:healthy_living")
            elif objective in {"into_fitness", "protein_calculator"}:
                traits = {value.casefold() for value in candidate.nutrition_traits}
                protein_fit = 1.0 if traits & {"high_protein", "protein_rich"} else 0.5
                fit = 0.70 * protein_fit + 0.30 * candidate.nutrition_fit
                adjustment += 0.55 * signal.confidence * (fit - 0.5)
                reasons.append(f"explicit:{objective}")
        elif signal.feature_code == "weekday_time_pressure" and request.day_type == "weekday":
            try:
                pressure = max(0.0, min(1.0, float(signal.value)))
            except (TypeError, ValueError):
                continue
            if candidate.cook_minutes is not None:
                minutes = candidate.cook_minutes
                effort_fit = (
                    1.0 if minutes <= 35 else -1.0 if minutes >= 60 else 1 - 2 * (minutes - 35) / 25
                )
                confidence = (
                    signal.confidence
                    if signal.correction_state == "confirmed"
                    else min(0.70, signal.confidence)
                )
                adjustment += 0.45 * confidence * pressure * effort_fit
                reasons.append("inferred:weekday_time_pressure")
    return max(-1.0, min(1.0, adjustment)), reasons


def _features(candidate: Candidate, request: RecommendationRequest) -> dict[str, float]:
    preference_fit = _preference_fit(candidate, request)
    regional_fit = (
        0.5
        if not request.region
        else float(request.region.casefold() in {region.casefold() for region in candidate.regions})
    )
    novelty = (
        0.0
        if candidate.id.casefold() in {m.casefold() for m in request.recent_meals}
        or candidate.name.casefold() in {m.casefold() for m in request.recent_meals}
        else 1.0
    )
    weekly_diversity = (
        0.0
        if candidate.id.casefold() in {meal.casefold() for meal in request.weekly_meals}
        or candidate.name.casefold() in {meal.casefold() for meal in request.weekly_meals}
        else 1.0
    )
    pantry = max(candidate.pantry_match, _overlap(request.pantry_items, candidate.ingredients))
    leftover_fit = _overlap(request.leftover_items, candidate.ingredients)
    if not request.leftover_items:
        leftover_fit = 0.5
    schedule_fit = 0.5
    if request.available_cook_minutes is not None and candidate.cook_minutes is not None:
        schedule_fit = float(candidate.cook_minutes <= request.available_cook_minutes)
    context_scores = []
    if request.season:
        context_scores.append(
            0.5
            if not candidate.seasons
            else float(
                request.season.casefold() in {value.casefold() for value in candidate.seasons}
            )
        )
    if request.occasion:
        context_scores.append(
            0.5
            if not candidate.occasions
            else float(
                request.occasion.casefold() in {value.casefold() for value in candidate.occasions}
            )
        )
    context_fit = sum(context_scores) / len(context_scores) if context_scores else 0.5
    spice_fit = 0.5
    if request.preferred_spice_level is not None and candidate.spice_level is not None:
        spice_fit = 1.0 - abs(request.preferred_spice_level - candidate.spice_level) / 4.0
    context_adjustment, _ = _governed_context_adjustment(candidate, request)
    return {
        "household_fit": preference_fit,
        "meal_class_fit": _meal_class_fit(candidate, request),
        "regional_fit": regional_fit,
        "freshness": candidate.freshness,
        "novelty": novelty,
        "pantry_fit": pantry,
        "nutrition_fit": candidate.nutrition_fit,
        "collaborative": candidate.collaborative_score,
        "debias": 1.0 - candidate.popularity,
        "weekly_diversity": weekly_diversity,
        "schedule_fit": schedule_fit,
        "season_occasion_fit": context_fit,
        "leftover_fit": leftover_fit,
        "spice_fit": spice_fit,
        "governed_context_adjustment": context_adjustment,
    }


WEIGHTS = {
    "household_fit": 0.12,
    "meal_class_fit": 0.04,
    "regional_fit": 0.10,
    "freshness": 0.07,
    "novelty": 0.09,
    "pantry_fit": 0.10,
    "nutrition_fit": 0.09,
    "collaborative": 0.10,
    "debias": 0.04,
    "weekly_diversity": 0.08,
    "schedule_fit": 0.06,
    "season_occasion_fit": 0.05,
    "leftover_fit": 0.03,
    "spice_fit": 0.03,
    "governed_context_adjustment": 0.06,
}


class LocalReranker:
    def rank(
        self, candidates: list[Candidate], request: RecommendationRequest
    ) -> tuple[RecommendationSet, list[dict[str, Any]]]:
        scored: list[ScoredCandidate] = []
        rejected: list[dict[str, Any]] = []
        for candidate in candidates:
            check = check_candidate(candidate, request)
            if not check.passed:
                rejected.append({"id": candidate.id, "reasons": check.reasons})
                continue
            features = _features(candidate, request)
            score = sum(WEIGHTS[name] * value for name, value in features.items())
            scored.append(ScoredCandidate(candidate, score, features))
        scored.sort(key=lambda row: (-row.score, row.candidate.id))

        selected: list[ScoredCandidate] = []
        remaining = scored[:]
        while remaining and len(selected) < request.candidate_limit:
            best = min(
                remaining,
                key=lambda row: (
                    -(
                        row.score
                        - 0.18
                        * max(
                            (
                                _overlap(row.candidate.ingredients, old.candidate.ingredients)
                                for old in selected
                            ),
                            default=0.0,
                        )
                    ),
                    row.candidate.id,
                ),
            )
            selected.append(best)
            remaining.remove(best)

        if not selected:
            return RecommendationSet(
                items=[],
                quality_score=0,
                confidence=0,
                diversity_score=0,
                safety_score=0,
                alignment_score=0,
            ), rejected
        pair_similarities = [
            _overlap(left.candidate.ingredients, right.candidate.ingredients)
            for index, left in enumerate(selected)
            for right in selected[index + 1 :]
        ]
        diversity = 1.0 - (
            sum(pair_similarities) / len(pair_similarities) if pair_similarities else 0.0
        )
        quality = sum(row.score for row in selected) / len(selected)
        alignment = sum(
            row.features["household_fit"] + row.features["regional_fit"] for row in selected
        ) / (2 * len(selected))
        confidence = min(
            1.0, 0.45 + 0.45 * quality + 0.10 * min(1.0, len(scored) / request.candidate_limit)
        )
        items = []
        for row in selected:
            item = row.candidate.model_dump()
            item["auxiliary_score"] = round(row.score, 6)
            item["reason_codes"] = [name for name, value in row.features.items() if value >= 0.7]
            _, context_reasons = _governed_context_adjustment(row.candidate, request)
            item["governed_context_reasons"] = context_reasons
            items.append(item)
        return RecommendationSet(
            items=items,
            quality_score=round(quality, 6),
            confidence=round(confidence, 6),
            diversity_score=round(diversity, 6),
            safety_score=1.0,
            alignment_score=round(alignment, 6),
        ), rejected
