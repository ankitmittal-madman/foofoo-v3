"""Offline replay harness for deterministic, labeled auxiliary-service scenarios."""

from __future__ import annotations

import argparse
import json
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

    def as_dict(self) -> dict[str, int | float]:
        return self.__dict__.copy()


def evaluate(rows: list[dict[str, Any]], settings: Settings) -> EvaluationSummary:
    if not rows:
        raise ValueError("evaluation dataset must contain at least one scenario")
    correct = constraint_passes = selected = fallbacks = 0
    quality = diversity = candidate_count = 0.0
    for row in rows:
        response = run(RecommendationRequest.model_validate(row["request"]), settings)
        correct += response.decision_reason == row["expected_decision_reason"]
        constraint_passes += response.constraint_checks.passed
        selected += response.decision == "auxiliary"
        fallbacks += response.decision == "existing" and settings.enabled
        if response.auxiliary_result:
            quality += response.auxiliary_result.quality_score
            diversity += response.auxiliary_result.diversity_score
        trace = response.debug_trace or {}
        candidate_count += float(trace.get("candidate_count", 0))
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
