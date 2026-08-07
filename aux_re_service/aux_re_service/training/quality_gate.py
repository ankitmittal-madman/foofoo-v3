"""Validate generated artifacts and report honest model-readiness gates."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def _jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def evaluate(training_dir: Path, retrieval_dir: Path, model_report_path: Path) -> dict[str, Any]:
    manifest = json.loads((training_dir / "manifest.json").read_text())
    ontology = json.loads((training_dir / "canonical_food_ontology.json").read_text())
    interactions = _jsonl(training_dir / "interactions.jsonl")
    model = json.loads(model_report_path.read_text())
    candidates = json.loads((retrieval_dir / "candidates.json").read_text())["candidates"]
    points = json.loads((retrieval_dir / "qdrant_points.json").read_text())["points"]

    checksum_failures = []
    for name, expected in manifest["sha256"].items():
        actual = hashlib.sha256((training_dir / name).read_bytes()).hexdigest()
        if actual != expected:
            checksum_failures.append(name)

    dishes = ontology["dishes"]
    coverage = {
        field: sum(bool(dish[field]) for dish in dishes) / max(1, len(dishes))
        for field in ("ingredients", "diet_types", "regions", "meal_slots")
    }
    household_positive_counts = Counter(
        row["household_id"] for row in interactions if float(row["weight"]) > 0
    )
    dense_households = sum(value >= 5 for value in household_positive_counts.values())
    real_interactions = 0 if manifest["synthetic_only"] else len(interactions)
    metric_names = ("recall_at_10", "ndcg_at_10", "catalog_coverage")
    lightfm_checks = {
        "report_promotion_gate": bool(model["promotion_gate_passed"]),
        "beats_popularity": all(model["metric_deltas"][name] >= 0 for name in metric_names),
        "shadow_only": model["activation_scope"] == "shadow_validation_only",
        "artifact_exists": model_report_path.with_name("lightfm_v1.joblib").stat().st_size > 0,
    }
    artifact_checks = {
        "checksums_valid": not checksum_failures,
        "ontology_candidate_count_matches": len(dishes) == len(candidates),
        "qdrant_point_count_matches": len(candidates) == len(points),
        "qdrant_vectors_are_64d": all(len(point["vector"]) == 64 for point in points),
        "lightfm": lightfm_checks,
    }
    shadow_gate_passed = all(
        [
            artifact_checks["checksums_valid"],
            artifact_checks["ontology_candidate_count_matches"],
            artifact_checks["qdrant_point_count_matches"],
            artifact_checks["qdrant_vectors_are_64d"],
            *lightfm_checks.values(),
        ]
    )
    graph_blockers = []
    if manifest["synthetic_only"]:
        graph_blockers.append("no_real_interactions")
    if dense_households < 5000:
        graph_blockers.append("insufficient_households_with_5_positive_events")
    kgat_blockers = list(graph_blockers)
    if coverage["ingredients"] < 0.90:
        kgat_blockers.append("ingredient_coverage_below_90_percent")
    if coverage["diet_types"] < 0.95:
        kgat_blockers.append("diet_coverage_below_95_percent")
    if coverage["regions"] < 0.90:
        kgat_blockers.append("region_coverage_below_90_percent")

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "shadow_gate_passed": shadow_gate_passed,
        "production_activation_allowed": False,
        "production_blockers": ["synthetic_training_data", "no_online_shadow_or_ab_evidence"],
        "artifact_checks": artifact_checks,
        "checksum_failures": checksum_failures,
        "data": {
            "dishes": len(dishes),
            "households": manifest["households"],
            "interactions": len(interactions),
            "real_interactions": real_interactions,
            "households_with_5_positive_events": dense_households,
            "ontology_coverage": coverage,
        },
        "models": {
            "lightfm": {
                "ready_for_shadow": shadow_gate_passed,
                "ready_for_active": False,
                "metrics": model["metrics"],
                "baseline": model["popularity_baseline"],
            },
            "lightgcn": {"ready": not graph_blockers, "blockers": graph_blockers},
            "kgat": {"ready": not kgat_blockers, "blockers": kgat_blockers},
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate FooFoo auxiliary ML artifacts")
    parser.add_argument("--training-dir", type=Path, required=True)
    parser.add_argument("--retrieval-dir", type=Path, required=True)
    parser.add_argument("--model-report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = evaluate(args.training_dir, args.retrieval_dir, args.model_report)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    if not report["shadow_gate_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
