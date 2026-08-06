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


def _features(candidate: Candidate, request: RecommendationRequest) -> dict[str, float]:
    household_preferences = list(request.preferences)
    for member in request.household_members:
        household_preferences.extend(member.preferences)
    preference_fit = max(
        _overlap(
            household_preferences, candidate.cuisines + candidate.regions + candidate.ingredients
        ),
        0.5 if not household_preferences else 0.0,
    )
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
    pantry = max(candidate.pantry_match, _overlap(request.pantry_items, candidate.ingredients))
    return {
        "household_fit": preference_fit,
        "regional_fit": regional_fit,
        "freshness": candidate.freshness,
        "novelty": novelty,
        "pantry_fit": pantry,
        "nutrition_fit": candidate.nutrition_fit,
        "collaborative": candidate.collaborative_score,
        "debias": 1.0 - candidate.popularity,
    }


WEIGHTS = {
    "household_fit": 0.20,
    "regional_fit": 0.12,
    "freshness": 0.12,
    "novelty": 0.14,
    "pantry_fit": 0.14,
    "nutrition_fit": 0.13,
    "collaborative": 0.10,
    "debias": 0.05,
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
            items.append(item)
        return RecommendationSet(
            items=items,
            quality_score=round(quality, 6),
            confidence=round(confidence, 6),
            diversity_score=round(diversity, 6),
            safety_score=1.0,
            alignment_score=round(alignment, 6),
        ), rejected
