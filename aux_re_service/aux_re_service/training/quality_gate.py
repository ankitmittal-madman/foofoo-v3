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
    household_features = _jsonl(training_dir / "household_features.jsonl")
    weekly_signals = _jsonl(training_dir / "weekly_signals.jsonl")
    preference_graph = _jsonl(training_dir / "household_preference_graph.jsonl")
    split_train = _jsonl(training_dir / "interactions_train.jsonl")
    split_validation = _jsonl(training_dir / "interactions_validation.jsonl")
    split_test = _jsonl(training_dir / "interactions_test.jsonl")
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
        for field in (
            "ingredients",
            "diet_types",
            "regions",
            "meal_slots",
            "substitutes",
            "spice_profiles",
            "nutrition_traits",
        )
    }
    coverage["seasons_or_occasions"] = sum(
        bool(dish["seasons"] or dish["occasions"]) for dish in dishes
    ) / max(1, len(dishes))
    household_positive_counts = Counter(
        row["household_id"] for row in interactions if float(row["weight"]) > 0
    )
    dense_households = sum(value >= 5 for value in household_positive_counts.values())
    real_interactions = 0 if manifest["synthetic_only"] else len(interactions)
    event_ids = [row["event_id"] for row in interactions]
    dish_ids = {dish["id"] for dish in dishes}
    household_ids = {row["household_id"] for row in household_features}
    split_ids = [
        {row["event_id"] for row in values}
        for values in (split_train, split_validation, split_test)
    ]
    metric_names = ("recall_at_10", "ndcg_at_10", "catalog_coverage")
    model_artifact_path = model_report_path.with_name(
        model_report_path.name.replace("_report.json", ".joblib")
    )
    lightfm_checks = {
        "report_promotion_gate": bool(model["promotion_gate_passed"]),
        "beats_popularity": all(model["metric_deltas"][name] >= 0 for name in metric_names),
        "shadow_only": model["activation_scope"] == "shadow_validation_only",
        "artifact_exists": model_artifact_path.is_file() and model_artifact_path.stat().st_size > 0,
    }
    artifact_checks = {
        "checksums_valid": not checksum_failures,
        "ontology_candidate_count_matches": len(dishes) == len(candidates),
        "qdrant_point_count_matches": len(candidates) == len(points),
        "qdrant_vectors_are_64d": all(len(point["vector"]) == 64 for point in points),
        "interaction_event_ids_unique": len(event_ids) == len(set(event_ids)),
        "interaction_dishes_resolve": all(row["dish_id"] in dish_ids for row in interactions),
        "interaction_households_resolve": all(
            row["household_id"] in household_ids for row in interactions
        ),
        "splits_are_disjoint": not (
            (split_ids[0] & split_ids[1])
            or (split_ids[0] & split_ids[2])
            or (split_ids[1] & split_ids[2])
        ),
        "splits_cover_interactions": sum(len(values) for values in split_ids) == len(interactions),
        "negative_samples_present": any(float(row["weight"]) < 0 for row in interactions),
        "weekly_signals_present": len(weekly_signals) >= manifest["households"] * 0.95,
        "household_preference_graph_present": bool(preference_graph),
        "lightfm": lightfm_checks,
    }
    shadow_gate_passed = all(
        [
            artifact_checks["checksums_valid"],
            artifact_checks["ontology_candidate_count_matches"],
            artifact_checks["qdrant_point_count_matches"],
            artifact_checks["qdrant_vectors_are_64d"],
            artifact_checks["interaction_event_ids_unique"],
            artifact_checks["interaction_dishes_resolve"],
            artifact_checks["interaction_households_resolve"],
            artifact_checks["splits_are_disjoint"],
            artifact_checks["splits_cover_interactions"],
            artifact_checks["negative_samples_present"],
            artifact_checks["weekly_signals_present"],
            artifact_checks["household_preference_graph_present"],
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
            "negative_interactions": sum(float(row["weight"]) < 0 for row in interactions),
            "weekly_signal_households": len(weekly_signals),
            "household_preference_edges": len(preference_graph),
            "split_counts": {
                "train": len(split_train),
                "validation": len(split_validation),
                "test": len(split_test),
            },
            "ontology_coverage": coverage,
        },
        "recurring_reviews": {
            "code_change": "unit_lint_type_and_container",
            "data_refresh": "checksums_schema_fk_dedupe_labels_and_splits",
            "model_update": "baseline_delta_and_shadow_gate",
            "weekly": "shadow_safety_and_fallback_review",
            "monthly": "diversity_repetition_region_and_household_fit_review",
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
