"""Export governed RecBole/LightGCN/KGAT inputs without claiming model readiness."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


def _jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _epoch(value: str) -> int:
    try:
        return int(datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp())
    except ValueError:
        return 0


def export(training_dir: Path, output_dir: Path) -> dict[str, int | bool | list[str]]:
    ontology = json.loads((training_dir / "canonical_food_ontology.json").read_text())
    interactions = _jsonl(training_dir / "interactions_train.jsonl")
    household_edges = _jsonl(training_dir / "household_preference_graph.jsonl")
    output_dir.mkdir(parents=True, exist_ok=True)

    positive = [row for row in interactions if float(row["weight"]) > 0]
    interaction_lines = ["user_id:token\titem_id:token\trating:float\ttimestamp:float"]
    interaction_lines.extend(
        "\t".join(
            (
                row["household_id"],
                row["dish_id"],
                str(float(row["weight"])),
                str(_epoch(str(row["timestamp"]))),
            )
        )
        for row in positive
    )
    (output_dir / "foofoo.inter").write_text("\n".join(interaction_lines) + "\n")

    item_lines = [
        "item_id:token\tmeal_slots:token_seq\tregions:token_seq\tdiets:token_seq"
        "\tcategories:token_seq\tnutrition_traits:token_seq"
    ]
    for dish in ontology["dishes"]:
        item_lines.append(
            "\t".join(
                (
                    dish["id"],
                    " ".join(dish["meal_slots"]) or "unknown",
                    " ".join(dish["regions"]) or "unknown",
                    " ".join(dish["diet_types"]) or "unknown",
                    " ".join(dish.get("dish_categories", [])) or "unknown",
                    " ".join(dish.get("nutrition_traits", [])) or "unknown",
                )
            )
        )
    (output_dir / "foofoo.item").write_text("\n".join(item_lines) + "\n")

    kg_lines = ["head_id:token\trelation_id:token\ttail_id:token"]
    kg_lines.extend(
        f"{row['source']}\t{row['relation']}\t{row['target']}" for row in ontology["relations"]
    )
    kg_lines.extend(
        f"{row['source']}\t{row['relation']}\t{row['target']}" for row in household_edges
    )
    (output_dir / "foofoo.kg").write_text("\n".join(kg_lines) + "\n")
    link_lines = ["item_id:token\tentity_id:token"]
    link_lines.extend(f"{dish['id']}\t{dish['id']}" for dish in ontology["dishes"])
    (output_dir / "foofoo.link").write_text("\n".join(link_lines) + "\n")

    report: dict[str, int | bool | list[str]] = {
        "interactions": len(positive),
        "items": len(ontology["dishes"]),
        "ontology_relations": len(ontology["relations"]),
        "household_relations": len(household_edges),
        "lightgcn_training_allowed": False,
        "kgat_training_allowed": False,
        "blockers": [
            "synthetic_only_interactions",
            "insufficient_per_household_interaction_density",
            "ingredient_coverage_below_90_percent",
        ],
    }
    (output_dir / "readiness.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Export gated RecBole and KGAT datasets")
    parser.add_argument("--training-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(export(args.training_dir, args.output_dir), indent=2))


if __name__ == "__main__":
    main()
