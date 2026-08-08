"""Build and optionally upload deterministic local retrieval artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import urllib.error
import urllib.request
import uuid
from collections.abc import Iterator, Mapping
from pathlib import Path
from typing import Any

from ..qdrant_endpoint import qdrant_base
from ..retrieval import local_embedding

PUBLICATION_SCHEMA_VERSION = "recommendation-catalogue-publication-v1"
ALLERGEN_FLAG_NAMES = {
    1: "nuts",
    2: "dairy",
    4: "gluten",
    8: "shellfish",
    16: "egg",
    32: "soy",
    64: "sesame",
    128: "fish",
    256: "mustard",
}
SPICE_LEVELS = {
    "low": 1,
    "low_spice": 1,
    "spice_low": 1,
    "spice_level_low": 1,
    "mild": 2,
    "mild_spice": 2,
    "spice_mild": 2,
    "spice_level_mild": 2,
    "mild_to_medium": 2,
    "medium": 3,
    "medium_spice": 3,
    "medium_spicy": 3,
    "moderate": 3,
    "moderate_spice": 3,
    "spice_medium": 3,
    "spice_level_medium": 3,
    "medium_high": 4,
    "medium_high_spice": 4,
    "medium_to_high": 4,
    "medium_to_hot": 4,
    "spice_level_medium_high": 4,
    "high": 5,
    "spice_high": 5,
}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else ([] if value is None else [value])


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _allergens_from_flags(value: Any) -> set[str]:
    flags = int(value or 0)
    return {name for bit, name in ALLERGEN_FLAG_NAMES.items() if flags & bit}


def _bounded_score(value: Any, default: float) -> float:
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return default


def _spice_level(value: Any) -> int | None:
    if value in (None, ""):
        return None
    if isinstance(value, bool):
        raise ValueError("boolean spice level is invalid")
    if isinstance(value, (int, float)) or str(value).strip().isdigit():
        level = int(value)
        if 1 <= level <= 5:
            return level
        raise ValueError("numeric spice level must be between 1 and 5")
    normalized = re.sub(r"[^a-z0-9]+", "_", str(value).strip().lower()).strip("_")
    try:
        return SPICE_LEVELS[normalized]
    except KeyError as exc:
        raise ValueError(f"unsupported spice level label: {normalized}") from exc


def publication_candidate(row: Mapping[str, Any], publication_version: str) -> dict[str, Any]:
    """Project one governed publication row into the runtime Aux candidate vocabulary."""
    taxonomy = _mapping(row.get("taxonomy"))
    cuisine = _mapping(row.get("cuisine"))
    ingredients = _list(row.get("ingredients"))
    ingredient_names = [
        str(value["name"])
        for value in ingredients
        if isinstance(value, Mapping) and value.get("name")
    ]
    allergens = _allergens_from_flags(row.get("allergen_flags"))
    for ingredient in ingredients:
        if isinstance(ingredient, Mapping):
            allergens.update(_allergens_from_flags(ingredient.get("allergen_flags")))

    raw_diet = str(row.get("diet_type") or "")
    diet_types = {
        "veg": ["vegetarian"],
        "vegan": ["vegetarian", "vegan"],
        "egg": ["egg"],
        "non_veg": ["non_vegetarian"],
    }.get(raw_diet, [])
    if row.get("is_jain") is True:
        diet_types.append("jain")

    cuisine_values = [str(value) for value in (cuisine.get("name"), cuisine.get("group")) if value]
    region_values = [str(cuisine["state_origin"])] if cuisine.get("state_origin") else []
    region_values.extend(
        str(value["region_code"])
        for value in _list(row.get("regional_affinities"))
        if isinstance(value, Mapping) and value.get("region_code")
    )
    meal_classes = [
        str(value["class_code"])
        for value in _list(row.get("meal_classes"))
        if isinstance(value, Mapping) and value.get("class_code")
    ]
    candidate = {
        "id": str(row["id"]),
        "name": str(row["name"]),
        "ingredients": ingredient_names,
        "allergens": sorted(allergens),
        "diet_types": list(dict.fromkeys(diet_types)),
        "cuisines": list(dict.fromkeys(cuisine_values)),
        "regions": list(dict.fromkeys(region_values)),
        "meal_slots": [str(value) for value in _list(row.get("meal_slots"))],
        "meal_classes": list(dict.fromkeys(meal_classes)),
        "dish_categories": [str(value) for value in _list(taxonomy.get("dish_category"))],
        "spice_profiles": [str(value) for value in _list(taxonomy.get("primary_taste"))],
        "spice_level": _spice_level(taxonomy.get("spice_level")),
        "nutrition_traits": [str(value) for value in _list(taxonomy.get("nutrition_trait"))],
        "seasons": [str(value) for value in _list(taxonomy.get("weather_affinity"))],
        "occasions": [str(value) for value in _list(taxonomy.get("occasion"))],
        "substitutes": [],
        "cook_minutes": row.get("cook_time_minutes"),
        "pantry_match": 0.0,
        "nutrition_fit": 0.5,
        "freshness": 0.5,
        "collaborative_score": _bounded_score(row.get("acceptance_rate_30d"), 0.5),
        "popularity": _bounded_score(row.get("popularity_score"), 0.0),
        "publication_version": publication_version,
        "ontology_confidence": row.get("ontology_confidence"),
    }
    # Validate the exact runtime shape before any point reaches a serving index.
    from ..schemas import Candidate

    return Candidate.model_validate(candidate).model_dump()


def _publication_manifest(directory: Path) -> dict[str, Any]:
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("schema_version") != PUBLICATION_SCHEMA_VERSION:
        raise ValueError("unsupported catalogue publication schema")
    version = manifest.get("publication_version")
    expected_hash = manifest.get("catalogue_jsonl_sha256")
    expected_count = manifest.get("row_count")
    if not isinstance(version, str) or not isinstance(expected_hash, str):
        raise ValueError("catalogue publication manifest is incomplete")
    if version != f"sha256:{expected_hash}" or re.fullmatch(r"[0-9a-f]{64}", expected_hash) is None:
        raise ValueError("catalogue publication version is not bound to its content hash")
    rows_path = directory / "catalogue.jsonl"
    digest = hashlib.sha256()
    count = 0
    with rows_path.open("rb") as handle:
        for line in handle:
            digest.update(line)
            try:
                publication_candidate(json.loads(line), version)
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError(
                    "catalogue publication candidate violates the manifest contract"
                ) from exc
            count += 1
    if digest.hexdigest() != expected_hash or count != expected_count:
        raise ValueError("catalogue publication content does not match its manifest")
    return manifest


def iter_publication_points(
    directory: Path, manifest: Mapping[str, Any] | None = None
) -> Iterator[dict[str, Any]]:
    """Yield canonical Qdrant points from a preverified publication in constant memory."""
    manifest = manifest or _publication_manifest(directory)
    version = str(manifest["publication_version"])
    with (directory / "catalogue.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            candidate = publication_candidate(json.loads(line), version)
            text = " ".join(
                str(value)
                for field in (
                    "name",
                    "ingredients",
                    "cuisines",
                    "regions",
                    "meal_slots",
                    "meal_classes",
                    "diet_types",
                    "dish_categories",
                    "spice_profiles",
                    "nutrition_traits",
                    "seasons",
                    "occasions",
                )
                for value in (
                    candidate[field] if isinstance(candidate[field], list) else [candidate[field]]
                )
            )
            yield {"id": candidate["id"], "vector": local_embedding(text), "payload": candidate}


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
        "dish_categories": dish["dish_categories"],
        "spice_profiles": dish["spice_profiles"],
        "spice_level": dish["spice_level"],
        "nutrition_traits": dish["nutrition_traits"],
        "seasons": dish["seasons"],
        "occasions": dish["occasions"],
        "substitutes": dish["substitutes"],
        "cook_minutes": dish["cook_minutes"],
        "pantry_match": 0.0,
        "nutrition_fit": 0.5,
        "freshness": 0.5,
        "collaborative_score": 0.5,
        "popularity": 0.0,
        "ontology_version": "indian-food-ontology-v2",
    }


def _similar(left: dict[str, Any], right: dict[str, Any]) -> float:
    score = 0.0
    for field, weight in (
        ("ingredients", 0.45),
        ("cuisines", 0.25),
        ("regions", 0.15),
        ("meal_slots", 0.10),
        ("diet_types", 0.05),
        ("dish_categories", 0.05),
        ("spice_profiles", 0.03),
        ("seasons", 0.02),
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
                *candidate["dish_categories"],
                *candidate["spice_profiles"],
                *candidate["nutrition_traits"],
                *candidate["seasons"],
                *candidate["occasions"],
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


def _request(
    url: str,
    method: str,
    payload: dict[str, Any],
    timeout: float,
    api_key: str | None = None,
) -> dict[str, Any]:
    headers = {"content-type": "application/json"}
    if api_key:
        headers["api-key"] = api_key
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers=headers,
        method=method,
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 -- caller validates the exact governed endpoint
        return json.load(response)


def upload(
    points_path: Path,
    qdrant_url: str,
    collection: str,
    *,
    timeout: float = 5.0,
    allowed_host: str | None = None,
    api_key: str | None = None,
) -> int:
    base = qdrant_base(qdrant_url, allowed_host)
    artifact = json.loads(points_path.read_text())
    try:
        _request(
            f"{base}/collections/{collection}",
            "PUT",
            {"vectors": {"size": artifact["vector_size"], "distance": "Cosine"}},
            timeout,
            api_key,
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
            api_key,
        )
    return len(points)


def upload_publication(
    publication_dir: Path,
    qdrant_url: str,
    collection: str,
    *,
    timeout: float = 5.0,
    batch_size: int = 128,
    allowed_host: str | None = None,
    api_key: str | None = None,
) -> dict[str, Any]:
    """Stream one immutable publication into a new, explicitly versioned Qdrant collection."""
    manifest = _publication_manifest(publication_dir)
    version = str(manifest["publication_version"])
    version_token = version.removeprefix("sha256:")[:12]
    if re.fullmatch(r"[A-Za-z0-9_-]+", collection) is None:
        raise ValueError("Qdrant collection contains unsupported characters")
    if version_token not in collection:
        raise ValueError("Qdrant collection name must include the publication hash prefix")
    base = qdrant_base(qdrant_url, allowed_host)
    _request(
        f"{base}/collections/{collection}",
        "PUT",
        {"vectors": {"size": 64, "distance": "Cosine"}},
        timeout,
        api_key,
    )
    uploaded = 0
    batch: list[dict[str, Any]] = []
    for point in iter_publication_points(publication_dir, manifest):
        batch.append(point)
        if len(batch) < batch_size:
            continue
        _request(
            f"{base}/collections/{collection}/points?wait=true",
            "PUT",
            {"points": batch},
            timeout,
            api_key,
        )
        uploaded += len(batch)
        batch = []
    if batch:
        _request(
            f"{base}/collections/{collection}/points?wait=true",
            "PUT",
            {"points": batch},
            timeout,
            api_key,
        )
        uploaded += len(batch)
    verified_manifest = _publication_manifest(publication_dir)
    if verified_manifest["publication_version"] != version:
        raise RuntimeError("catalogue publication changed during Qdrant upload")
    count_result = _request(
        f"{base}/collections/{collection}/points/count",
        "POST",
        {"exact": True},
        timeout,
        api_key,
    )
    indexed = int((count_result.get("result") or {}).get("count", -1))
    if uploaded != int(manifest["row_count"]) or indexed != uploaded:
        raise RuntimeError("Qdrant publication count verification failed")
    return {
        "publication_version": version,
        "collection": collection,
        "uploaded": uploaded,
        "verified_count": indexed,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build or upload FooFoo retrieval artifacts")
    parser.add_argument("--ontology", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--upload-points", type=Path)
    parser.add_argument("--upload-publication", type=Path)
    parser.add_argument("--qdrant-url", default="http://127.0.0.1:6333")
    parser.add_argument("--qdrant-allowed-host")
    parser.add_argument("--qdrant-api-key-env")
    parser.add_argument("--collection", default="foofoo_recipes")
    args = parser.parse_args()
    api_key = None
    if args.qdrant_api_key_env:
        api_key = os.environ.get(args.qdrant_api_key_env)
        if not api_key:
            parser.error("the selected Qdrant API key environment variable is empty")
    if args.ontology and args.output_dir:
        print(json.dumps(build(args.ontology, args.output_dir), indent=2))
    elif args.upload_points:
        print(
            json.dumps(
                {
                    "uploaded": upload(
                        args.upload_points,
                        args.qdrant_url,
                        args.collection,
                        allowed_host=args.qdrant_allowed_host,
                        api_key=api_key,
                    )
                }
            )
        )
    elif args.upload_publication:
        print(
            json.dumps(
                upload_publication(
                    args.upload_publication,
                    args.qdrant_url,
                    args.collection,
                    allowed_host=args.qdrant_allowed_host,
                    api_key=api_key,
                ),
                indent=2,
            )
        )
    else:
        parser.error(
            "provide --ontology and --output-dir, --upload-points, or --upload-publication"
        )


if __name__ == "__main__":
    main()
