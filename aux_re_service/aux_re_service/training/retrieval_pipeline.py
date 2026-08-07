"""Build and optionally upload deterministic local retrieval artifacts."""

from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path
from typing import Any

from ..retrieval import local_embedding


def _candidate(dish: dict[str, Any]) -> dict[str, Any]:
    diet_types = [value for value in dish["diet_types"] if value != "unknown"]
    return {
        "id": dish["id"],
        "name": dish["name"],
        "ingredients": dish["ingredients"],
        "allergens": dish["allergens"],
        "diet_types": diet_types,
        "cuisines": dish["cuisines"],
        "regions": dish["regions"],
        "meal_slots": dish["meal_slots"],
        "pantry_match": 0.0,
        "nutrition_fit": 0.5,
        "freshness": 0.5,
        "collaborative_score": 0.5,
        "popularity": 0.0,
        "ontology_version": "indian-food-ontology-v1",
    }


def _similar(left: dict[str, Any], right: dict[str, Any]) -> float:
    score = 0.0
    for field, weight in (
        ("ingredients", 0.45),
        ("cuisines", 0.25),
        ("regions", 0.15),
        ("meal_slots", 0.10),
        ("diet_types", 0.05),
    ):
        a = set(left[field])
        b = set(right[field])
        if a or b:
            score += weight * len(a & b) / len(a | b)
    return score


def build(ontology_path: Path, output_dir: Path) -> dict[str, int]:
    ontology = json.loads(ontology_path.read_text())
    candidates = [_candidate(dish) for dish in ontology["dishes"]]
    by_id = {candidate["id"]: candidate for candidate in candidates}
    relations: dict[str, list[str]] = {}
    for candidate in candidates:
        ranked = sorted(
            (
                (_similar(candidate, other), other["id"])
                for other in candidates
                if other["id"] != candidate["id"]
            ),
            key=lambda row: (-row[0], row[1]),
        )
        relations[candidate["id"]] = [dish_id for score, dish_id in ranked[:8] if score > 0]

    points = []
    for candidate in candidates:
        text = " ".join(
            [
                candidate["name"],
                *candidate["ingredients"],
                *candidate["cuisines"],
                *candidate["regions"],
                *candidate["meal_slots"],
                *candidate["diet_types"],
            ]
        )
        points.append(
            {
                "id": str(uuid.uuid5(uuid.NAMESPACE_URL, f"foofoo:dish:{candidate['id']}")),
                "vector": local_embedding(text),
                "payload": candidate,
            }
        )
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "candidates.json").write_text(
        json.dumps({"candidates": candidates}, indent=2) + "\n"
    )
    (output_dir / "knowledge_graph.json").write_text(
        json.dumps({"candidates": by_id, "relations": relations}, indent=2) + "\n"
    )
    (output_dir / "qdrant_points.json").write_text(
        json.dumps({"vector_size": 64, "points": points}, separators=(",", ":")) + "\n"
    )
    return {
        "candidates": len(candidates),
        "relations": sum(len(values) for values in relations.values()),
        "points": len(points),
    }


def _local_base(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in {"http", "https"} or parsed.hostname not in {
        "localhost",
        "127.0.0.1",
        "::1",
        "qdrant",
    }:
        raise ValueError("Qdrant URL must reference a local service")
    return url.rstrip("/")


def _request(url: str, method: str, payload: dict[str, Any], timeout: float) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"content-type": "application/json"},
        method=method,
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 local URL only
        return json.load(response)


def upload(points_path: Path, qdrant_url: str, collection: str, *, timeout: float = 5.0) -> int:
    base = _local_base(qdrant_url)
    artifact = json.loads(points_path.read_text())
    try:
        _request(
            f"{base}/collections/{collection}",
            "PUT",
            {"vectors": {"size": artifact["vector_size"], "distance": "Cosine"}},
            timeout,
        )
    except urllib.error.HTTPError as exc:
        if exc.code != 409:
            raise
    points = artifact["points"]
    for start in range(0, len(points), 128):
        _request(
            f"{base}/collections/{collection}/points?wait=true",
            "PUT",
            {"points": points[start : start + 128]},
            timeout,
        )
    return len(points)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build or upload FooFoo retrieval artifacts")
    parser.add_argument("--ontology", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--upload-points", type=Path)
    parser.add_argument("--qdrant-url", default="http://127.0.0.1:6333")
    parser.add_argument("--collection", default="foofoo_recipes")
    args = parser.parse_args()
    if args.ontology and args.output_dir:
        print(json.dumps(build(args.ontology, args.output_dir), indent=2))
    elif args.upload_points:
        print(
            json.dumps({"uploaded": upload(args.upload_points, args.qdrant_url, args.collection)})
        )
    else:
        parser.error("provide --ontology and --output-dir, or --upload-points")


if __name__ == "__main__":
    main()
