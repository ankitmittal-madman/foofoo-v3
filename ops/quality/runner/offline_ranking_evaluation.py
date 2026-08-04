"""Offline ranking evaluation over exported impression/relevance judgments.

Input is JSON Lines, one request per line:
{"request_id":"...", "segment":"cold_start", "ranked_ids":[...], "relevant_ids":[...],
 "scores":[0.8,...]}

The evaluator is intentionally model-agnostic so the same frozen replay set can compare rules,
online affinities, or a future trained model without changing metric definitions.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from pathlib import Path


def _dcg(relevances: list[int]) -> float:
    return sum(value / math.log2(index + 2) for index, value in enumerate(relevances))


def evaluate(rows: list[dict], k: int = 8) -> dict:
    if not rows:
        raise ValueError("evaluation set is empty")
    catalogue: set[str] = set()
    exposures: Counter[str] = Counter()
    per_segment: dict[str, list[dict[str, float]]] = defaultdict(list)
    brier_terms: list[float] = []
    for row in rows:
        ranked = [str(value) for value in row.get("ranked_ids", [])][:k]
        relevant = {str(value) for value in row.get("relevant_ids", [])}
        if not ranked:
            raise ValueError(f"{row.get('request_id', '<unknown>')}: ranked_ids is empty")
        catalogue.update(ranked)
        exposures.update(ranked)
        binary = [1 if dish_id in relevant else 0 for dish_id in ranked]
        ideal = [1] * min(len(relevant), k) + [0] * max(0, k - len(relevant))
        ideal_dcg = _dcg(ideal[: len(ranked)])
        metrics = {
            "ndcg_at_k": _dcg(binary) / ideal_dcg if ideal_dcg else 0.0,
            "recall_at_k": sum(binary) / len(relevant) if relevant else 0.0,
        }
        per_segment[str(row.get("segment") or "all")].append(metrics)
        scores = row.get("scores")
        if isinstance(scores, list) and len(scores) >= len(binary):
            for score, target in zip(scores, binary, strict=False):
                probability = max(0.0, min(1.0, float(score)))
                brier_terms.append((probability - target) ** 2)

    def summarize(items: list[dict[str, float]]) -> dict[str, float]:
        return {
            key: round(sum(item[key] for item in items) / len(items), 6)
            for key in ("ndcg_at_k", "recall_at_k")
        }

    all_items = [item for items in per_segment.values() for item in items]
    total_exposures = sum(exposures.values())
    probabilities = [count / total_exposures for count in exposures.values()]
    entropy = -sum(p * math.log(p) for p in probabilities) if probabilities else 0.0
    max_entropy = math.log(len(exposures)) if len(exposures) > 1 else 1.0
    return {
        "requests": len(rows),
        "k": k,
        **summarize(all_items),
        "catalogue_coverage": len(catalogue),
        "exposure_entropy_normalized": round(entropy / max_entropy, 6),
        "brier_score": round(sum(brier_terms) / len(brier_terms), 6) if brier_terms else None,
        "segments": {name: summarize(items) for name, items in sorted(per_segment.items())},
    }


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path, help="JSONL replay/judgment set")
    parser.add_argument("--k", type=int, default=8)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--min-ndcg", type=float, default=0.0)
    args = parser.parse_args()
    result = evaluate(load_jsonl(args.input), args.k)
    rendered = json.dumps(result, indent=2, sort_keys=True)
    if args.output:
        args.output.write_text(rendered + "\n")
    print(rendered)
    return 0 if result["ndcg_at_k"] >= args.min_ndcg else 1


if __name__ == "__main__":
    raise SystemExit(main())
