"""Offline replay harness for deterministic, labeled auxiliary-service scenarios."""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import Settings
from .schemas import RecommendationRequest
from .service import run


@dataclass(frozen=True)
class EvaluationSummary:
    scenarios: int
    expected_decision_accuracy: float
    constraint_pass_rate: float
    auxiliary_selection_rate: float
    fallback_rate: float
    mean_quality: float
    mean_diversity: float
    mean_candidate_count: float
    mean_alignment: float
    mean_latency_ms: float
    safety_violation_rate: float
    model_failure_rate: float
    auxiliary_win_rate: float

    def as_dict(self) -> dict[str, int | float]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class RankingMetrics:
    households: int
    precision_at_k: float
    recall_at_k: float
    ndcg_at_k: float
    catalog_coverage: float
    intra_list_diversity: float
    repetition_rate: float
    safety_violations: int
    novelty_score: float
    household_fit: float
    region_fit: float
    pantry_fit: float
    freshness_fit: float

    def as_dict(self) -> dict[str, int | float]:
        return self.__dict__.copy()


def compare_scorecards(
    baseline: RankingMetrics, candidate: RankingMetrics
) -> dict[str, float | int | bool]:
    """Return a before/after scorecard suitable for model updates and ablations."""
    higher_is_better = (
        "precision_at_k",
        "recall_at_k",
        "ndcg_at_k",
        "catalog_coverage",
        "intra_list_diversity",
        "novelty_score",
        "household_fit",
        "region_fit",
        "pantry_fit",
        "freshness_fit",
    )
    output: dict[str, float | int | bool] = {
        name: float(getattr(candidate, name)) - float(getattr(baseline, name))
        for name in higher_is_better
    }
    output["repetition_rate"] = baseline.repetition_rate - candidate.repetition_rate
    output["safety_violations"] = baseline.safety_violations - candidate.safety_violations
    output["safe_to_promote"] = (
        candidate.safety_violations == 0
        and candidate.ndcg_at_k >= baseline.ndcg_at_k
        and candidate.recall_at_k >= baseline.recall_at_k
        and candidate.intra_list_diversity >= baseline.intra_list_diversity
    )
    return output


def ranking_metrics(
    predictions: dict[str, list[str]],
    relevant: dict[str, set[str]],
    *,
    catalog: set[str],
    ingredients: dict[str, set[str]] | None = None,
    recent: dict[str, set[str]] | None = None,
    unsafe: dict[str, set[str]] | None = None,
    popularity: dict[str, float] | None = None,
    household_scores: dict[str, dict[str, float]] | None = None,
    region_scores: dict[str, dict[str, float]] | None = None,
    pantry_scores: dict[str, dict[str, float]] | None = None,
    freshness_scores: dict[str, dict[str, float]] | None = None,
    k: int = 10,
) -> RankingMetrics:
    """Compute repeatable ranking, diversity, repetition, and safety metrics."""
    if not predictions or k < 1:
        raise ValueError("predictions must be non-empty and k must be positive")
    ingredients = ingredients or {}
    recent = recent or {}
    unsafe = unsafe or {}
    popularity = popularity or {}
    household_scores = household_scores or {}
    region_scores = region_scores or {}
    pantry_scores = pantry_scores or {}
    freshness_scores = freshness_scores or {}
    precision = recall = ndcg = diversity = repetition = novelty = 0.0
    household_fit = region_fit = pantry_fit = freshness_fit = 0.0
    violations = 0
    recommended: set[str] = set()
    for household, values in predictions.items():
        ranked = values[:k]
        truth = relevant.get(household, set())
        hits = [index for index, item in enumerate(ranked) if item in truth]
        precision += len(hits) / k
        recall += len(hits) / max(1, len(truth))
        dcg = sum(1.0 / math.log2(index + 2) for index in hits)
        ideal = sum(1.0 / math.log2(index + 2) for index in range(min(len(truth), k)))
        ndcg += dcg / ideal if ideal else 0.0
        similarities = []
        for index, left in enumerate(ranked):
            for right in ranked[index + 1 :]:
                a = ingredients.get(left, set())
                b = ingredients.get(right, set())
                similarities.append(len(a & b) / max(1, len(a | b)))
        diversity += 1.0 - (sum(similarities) / len(similarities) if similarities else 0.0)
        repetition += sum(item in recent.get(household, set()) for item in ranked) / max(
            1, len(ranked)
        )
        novelty += sum(1.0 - popularity.get(item, 0.0) for item in ranked) / max(1, len(ranked))
        household_fit += sum(
            household_scores.get(household, {}).get(item, 0.5) for item in ranked
        ) / max(1, len(ranked))
        region_fit += sum(region_scores.get(household, {}).get(item, 0.5) for item in ranked) / max(
            1, len(ranked)
        )
        pantry_fit += sum(pantry_scores.get(household, {}).get(item, 0.5) for item in ranked) / max(
            1, len(ranked)
        )
        freshness_fit += sum(
            freshness_scores.get(household, {}).get(item, 0.5) for item in ranked
        ) / max(1, len(ranked))
        violations += sum(item in unsafe.get(household, set()) for item in ranked)
        recommended.update(ranked)
    count = len(predictions)
    return RankingMetrics(
        households=count,
        precision_at_k=precision / count,
        recall_at_k=recall / count,
        ndcg_at_k=ndcg / count,
        catalog_coverage=len(recommended) / max(1, len(catalog)),
        intra_list_diversity=diversity / count,
        repetition_rate=repetition / count,
        safety_violations=violations,
        novelty_score=novelty / count,
        household_fit=household_fit / count,
        region_fit=region_fit / count,
        pantry_fit=pantry_fit / count,
        freshness_fit=freshness_fit / count,
    )


def evaluate(rows: list[dict[str, Any]], settings: Settings) -> EvaluationSummary:
    if not rows:
        raise ValueError("evaluation dataset must contain at least one scenario")
    correct = constraint_passes = selected = fallbacks = violations = model_failures = 0
    quality = diversity = candidate_count = alignment = latency = 0.0
    for row in rows:
        response = run(RecommendationRequest.model_validate(row["request"]), settings)
        correct += response.decision_reason == row["expected_decision_reason"]
        constraint_passes += response.constraint_checks.passed
        violations += int(not response.constraint_checks.passed)
        selected += response.decision == "auxiliary"
        fallbacks += response.decision == "existing" and settings.enabled
        if response.auxiliary_result:
            quality += response.auxiliary_result.quality_score
            diversity += response.auxiliary_result.diversity_score
            alignment += response.auxiliary_result.alignment_score
        trace = response.debug_trace or {}
        candidate_count += float(trace.get("candidate_count", 0))
        latency += response.timings_ms["total"]
        model_trace = response.model_metadata.get("model_trace", {}).get("lightfm", {})
        model_failures += model_trace.get("reason") not in {
            "disabled",
            "scored",
            "unknown_household",
            "no_known_candidates",
            "synthetic_artifact_shadow_only",
        }
    count = len(rows)
    return EvaluationSummary(
        scenarios=count,
        expected_decision_accuracy=correct / count,
        constraint_pass_rate=constraint_passes / count,
        auxiliary_selection_rate=selected / count,
        fallback_rate=fallbacks / count,
        mean_quality=quality / count,
        mean_diversity=diversity / count,
        mean_candidate_count=candidate_count / count,
        mean_alignment=alignment / count,
        mean_latency_ms=latency / count,
        safety_violation_rate=violations / count,
        model_failure_rate=model_failures / count,
        auxiliary_win_rate=selected / count,
    )


def evaluate_file(path: Path, settings: Settings) -> EvaluationSummary:
    payload = json.loads(path.read_text())
    rows = payload if isinstance(payload, list) else payload["scenarios"]
    return evaluate(rows, settings)


def main() -> None:
    parser = argparse.ArgumentParser(description="Replay labeled auxiliary recommendation cases")
    parser.add_argument("dataset", type=Path)
    args = parser.parse_args()
    print(json.dumps(evaluate_file(args.dataset, Settings.from_env()).as_dict(), indent=2))


if __name__ == "__main__":
    main()
