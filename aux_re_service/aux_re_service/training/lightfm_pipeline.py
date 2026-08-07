"""Train and evaluate a real local LightFM hybrid baseline."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def _jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _item_features(ontology: dict[str, Any]) -> dict[str, list[str]]:
    features = {}
    for dish in ontology["dishes"]:
        features[dish["id"]] = sorted(
            {
                *(f"slot:{value}" for value in dish["meal_slots"]),
                *(f"diet:{value}" for value in dish["diet_types"]),
                *(f"region:{value}" for value in dish["regions"]),
                *(f"cuisine:{value}" for value in dish["cuisines"]),
                *(f"ingredient:{value}" for value in dish["ingredients"]),
            }
        )
    return features


def _time_split(
    positives: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in positives:
        grouped[row["household_id"]].append(row)
    train = []
    test = []
    for values in grouped.values():
        values.sort(key=lambda row: (row["timestamp"], row["dish_id"]))
        unique_items = {row["dish_id"] for row in values}
        if len(unique_items) >= 2:
            test.append(values[-1])
            train.extend(values[:-1])
        else:
            train.extend(values)
    return train, test


def _ranking_metrics(
    model: Any,
    test: list[dict[str, Any]],
    train: list[dict[str, Any]],
    user_id_map: dict[str, int],
    item_id_map: dict[str, int],
    user_features: Any,
    item_features: Any,
    *,
    k: int,
) -> dict[str, float]:
    import numpy as np

    seen: dict[str, set[str]] = defaultdict(set)
    for row in train:
        seen[row["household_id"]].add(row["dish_id"])
    hits = reciprocal_dcg = 0.0
    recommended: set[str] = set()
    reverse_items = {index: item for item, index in item_id_map.items()}
    all_indices = np.arange(len(item_id_map))
    evaluated = 0
    for row in test:
        user_id = row["household_id"]
        target = row["dish_id"]
        if user_id not in user_id_map or target not in item_id_map:
            continue
        user_indices = np.full(len(all_indices), user_id_map[user_id])
        scores = model.predict(
            user_indices,
            all_indices,
            user_features=user_features,
            item_features=item_features,
            num_threads=1,
        )
        ranking = [
            reverse_items[index]
            for index in np.argsort(-scores)
            if reverse_items[index] not in seen[user_id]
        ][:k]
        recommended.update(ranking)
        evaluated += 1
        if target in ranking:
            rank = ranking.index(target)
            hits += 1.0
            reciprocal_dcg += 1.0 / math.log2(rank + 2)
    divisor = max(1, evaluated)
    return {
        "evaluated_households": float(evaluated),
        f"recall_at_{k}": hits / divisor,
        f"precision_at_{k}": hits / divisor / k,
        f"ndcg_at_{k}": reciprocal_dcg / divisor,
        "catalog_coverage": len(recommended) / max(1, len(item_id_map)),
    }


def _popularity_metrics(
    test: list[dict[str, Any]], train: list[dict[str, Any]], items: list[str], *, k: int
) -> dict[str, float]:
    popularity: dict[str, float] = defaultdict(float)
    seen: dict[str, set[str]] = defaultdict(set)
    for row in train:
        popularity[row["dish_id"]] += float(row["weight"])
        seen[row["household_id"]].add(row["dish_id"])
    global_ranking = sorted(items, key=lambda item: (-popularity[item], item))
    hits = reciprocal_dcg = 0.0
    recommended: set[str] = set()
    for row in test:
        ranking = [item for item in global_ranking if item not in seen[row["household_id"]]][:k]
        recommended.update(ranking)
        if row["dish_id"] in ranking:
            rank = ranking.index(row["dish_id"])
            hits += 1.0
            reciprocal_dcg += 1.0 / math.log2(rank + 2)
    divisor = max(1, len(test))
    return {
        "evaluated_households": float(len(test)),
        f"recall_at_{k}": hits / divisor,
        f"precision_at_{k}": hits / divisor / k,
        f"ndcg_at_{k}": reciprocal_dcg / divisor,
        "catalog_coverage": len(recommended) / max(1, len(items)),
    }


def train(
    data_dir: Path,
    artifact_path: Path,
    report_path: Path,
    *,
    epochs: int = 20,
    components: int = 32,
    k: int = 10,
    seed: int = 20260807,
) -> dict[str, Any]:
    try:
        import joblib
        from lightfm import LightFM  # type: ignore[import-not-found]
        from lightfm.data import Dataset  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError("LightFM training requires Python 3.11 and the models extra") from exc

    interactions = _jsonl(data_dir / "interactions.jsonl")
    household_rows = _jsonl(data_dir / "household_features.jsonl")
    ontology = json.loads((data_dir / "canonical_food_ontology.json").read_text())
    positives = [row for row in interactions if float(row["weight"]) > 0]
    train_rows, test_rows = _time_split(positives)
    household_features = {row["household_id"]: row["features"] for row in household_rows}
    item_features_by_id = _item_features(ontology)
    users = sorted(household_features)
    items = sorted(item_features_by_id)
    user_feature_names = sorted(
        {value for values in household_features.values() for value in values}
    )
    item_feature_names = sorted(
        {value for values in item_features_by_id.values() for value in values}
    )

    dataset = Dataset(user_identity_features=True, item_identity_features=True)
    dataset.fit(users, items, user_features=user_feature_names, item_features=item_feature_names)
    user_features = dataset.build_user_features(
        ((user, features) for user, features in household_features.items()), normalize=True
    )
    item_features = dataset.build_item_features(
        ((item, features) for item, features in item_features_by_id.items()), normalize=True
    )
    train_interactions, train_weights = dataset.build_interactions(
        (row["household_id"], row["dish_id"], max(0.05, float(row["weight"])))
        for row in train_rows
        if row["dish_id"] in item_features_by_id and row["household_id"] in household_features
    )
    model = LightFM(
        no_components=components,
        loss="warp",
        learning_schedule="adagrad",
        random_state=seed,
        user_alpha=1e-5,
        item_alpha=1e-5,
    )
    model.fit(
        train_interactions,
        sample_weight=train_weights,
        user_features=user_features,
        item_features=item_features,
        epochs=epochs,
        num_threads=1,
        verbose=False,
    )
    user_id_map, _, item_id_map, _ = dataset.mapping()
    metrics = _ranking_metrics(
        model,
        test_rows,
        train_rows,
        user_id_map,
        item_id_map,
        user_features,
        item_features,
        k=k,
    )
    baseline_metrics = _popularity_metrics(test_rows, train_rows, items, k=k)
    metric_deltas = {
        name: metrics[name] - baseline_metrics[name]
        for name in (f"recall_at_{k}", f"precision_at_{k}", f"ndcg_at_{k}", "catalog_coverage")
    }
    promotion_gate_passed = (
        metrics[f"recall_at_{k}"] >= 0.20
        and metrics[f"ndcg_at_{k}"] >= 0.08
        and metrics["catalog_coverage"] >= 0.50
        and metric_deltas[f"ndcg_at_{k}"] >= 0.0
    )
    fingerprint = hashlib.sha256(
        (data_dir / "manifest.json").read_bytes()
        + json.dumps(metrics, sort_keys=True).encode()
        + f"{epochs}:{components}:{seed}".encode()
    ).hexdigest()
    metadata = {
        "format": "foofoo-lightfm-v1",
        "model_type": "LightFM-WARP-hybrid",
        "model_version": f"sha256:{fingerprint}",
        "created_at": datetime.now(UTC).isoformat(),
        "synthetic_only": True,
        "promotion_gate_passed": promotion_gate_passed,
        "activation_scope": "shadow_validation_only",
        "epochs": epochs,
        "components": components,
        "seed": seed,
        "train_interactions": int(train_interactions.nnz),
        "holdout_interactions": len(test_rows),
        "metrics": metrics,
        "popularity_baseline": baseline_metrics,
        "metric_deltas": metric_deltas,
    }
    artifact = {
        "metadata": metadata,
        "model": model,
        "user_features": user_features,
        "item_features": item_features,
        "user_id_map": user_id_map,
        "item_id_map": item_id_map,
    }
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact, artifact_path, compress=3)
    report_path.write_text(json.dumps(metadata, indent=2) + "\n")
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser(description="Train FooFoo's local LightFM baseline")
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--components", type=int, default=32)
    parser.add_argument("--k", type=int, default=10)
    args = parser.parse_args()
    metadata = train(
        args.data_dir,
        args.artifact,
        args.report,
        epochs=args.epochs,
        components=args.components,
        k=args.k,
    )
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
