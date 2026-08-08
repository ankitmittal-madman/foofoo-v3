from __future__ import annotations

import hashlib
import json
from pathlib import Path

from aux_re_service.evaluation import ranking_metrics
from aux_re_service.training.data_pipeline import canonical_id, normalize_name
from aux_re_service.training.graph_export import export
from aux_re_service.training.quality_gate import evaluate
from aux_re_service.training.retrieval_pipeline import (
    build,
    iter_publication_points,
    publication_candidate,
    upload_publication,
)

ROOT = Path(__file__).parents[2]
TRAINING = ROOT / "aux_re_service" / "data" / "training" / "v1"


def test_generated_training_manifest_is_complete_and_checksummed():
    manifest = json.loads((TRAINING / "manifest.json").read_text())
    assert manifest["synthetic_only"] is True
    assert manifest["ontology_dishes"] == 86
    assert manifest["interactions"] == 64842
    assert manifest["positive_interactions"] > 46000
    assert manifest["negative_interactions"] > 17000
    assert manifest["weekly_signal_households"] == 10000
    assert manifest["household_graph_edges"] == 29020
    assert manifest["validation_interactions"] > 4000
    assert manifest["test_interactions"] > 4000
    for name, expected in manifest["sha256"].items():
        assert hashlib.sha256((TRAINING / name).read_bytes()).hexdigest() == expected


def test_dataset_audit_exposes_dataset_two_orphans():
    audit = json.loads((TRAINING / "dataset_audit.json").read_text())
    by_name = {row["dataset"]: row for row in audit["datasets"]}
    errors = {
        finding["check"]: finding["count"]
        for finding in by_name["dataset_2"]["findings"]
        if finding["severity"] == "error"
    }
    assert errors["events.household_fk"] == 5
    assert errors["members.household_fk"] == 5
    assert errors["events.user_fk"] == 5


def test_canonical_name_normalization_is_deterministic():
    assert normalize_name(" Bhakri & Pithla ") == "bhakri and pithla"
    assert canonical_id("Bhakri & Pithla") == "DISH_BHAKRI_AND_PITHLA"


def test_retrieval_artifact_builder_outputs_vectors_and_graph(tmp_path):
    ontology = {
        "dishes": [
            {
                "id": "DISH_A",
                "name": "A",
                "ingredients": ["rice"],
                "allergens": [],
                "diet_types": ["vegetarian"],
                "cuisines": ["south"],
                "regions": ["south"],
                "meal_slots": ["lunch"],
                "dish_categories": [],
                "spice_profiles": [],
                "spice_level": None,
                "nutrition_traits": [],
                "seasons": [],
                "occasions": [],
                "substitutes": [],
                "cook_minutes": None,
            },
            {
                "id": "DISH_B",
                "name": "B",
                "ingredients": ["rice", "lentil"],
                "allergens": [],
                "diet_types": ["vegetarian"],
                "cuisines": ["south"],
                "regions": ["south"],
                "meal_slots": ["lunch"],
                "dish_categories": [],
                "spice_profiles": [],
                "spice_level": None,
                "nutrition_traits": [],
                "seasons": [],
                "occasions": [],
                "substitutes": [],
                "cook_minutes": None,
            },
        ]
    }
    path = tmp_path / "ontology.json"
    path.write_text(json.dumps(ontology))
    summary = build(path, tmp_path / "out")
    points = json.loads((tmp_path / "out" / "qdrant_points.json").read_text())
    graph = json.loads((tmp_path / "out" / "knowledge_graph.json").read_text())
    assert summary == {"candidates": 2, "relations": 2, "points": 2}
    assert len(points["points"][0]["vector"]) == 64
    assert graph["relations"]["DISH_A"] == ["DISH_B"]


def _published_row(dish_id: str) -> dict:
    return {
        "id": dish_id,
        "name": "Published Poha",
        "diet_type": "veg",
        "is_jain": True,
        "allergen_flags": 32,
        "cook_time_minutes": 20,
        "popularity_score": 0.7,
        "acceptance_rate_30d": 0.8,
        "ontology_confidence": 0.9,
        "meal_slots": ["breakfast"],
        "meal_classes": [{"class_code": "BF_POHA_UPMA", "slot": "breakfast"}],
        "cuisine": {
            "name": "Maharashtrian",
            "group": "west",
            "state_origin": "Maharashtra",
        },
        "ingredients": [
            {"name": "rice", "allergen_flags": 0},
            {"name": "sesame", "allergen_flags": 64},
        ],
        "regional_affinities": [{"region_code": "west"}],
        "taxonomy": {
            "dish_category": ["breakfast"],
            "primary_taste": ["savory"],
            "spice_level": 2,
            "weather_affinity": ["all_weather"],
        },
    }


def _publication(tmp_path: Path) -> tuple[Path, str]:
    directory = tmp_path / "publication"
    directory.mkdir()
    row = _published_row("00000000-0000-0000-0000-000000000001")
    content = json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n"
    (directory / "catalogue.jsonl").write_text(content)
    digest = hashlib.sha256(content.encode()).hexdigest()
    version = f"sha256:{digest}"
    (directory / "manifest.json").write_text(
        json.dumps(
            {
                "schema_version": "recommendation-catalogue-publication-v1",
                "publication_version": version,
                "row_count": 1,
                "catalogue_jsonl_sha256": digest,
            }
        )
    )
    return directory, version


def test_publication_projection_preserves_canonical_identity_and_safety():
    dish_id = "00000000-0000-0000-0000-000000000001"
    candidate = publication_candidate(_published_row(dish_id), "sha256:test")
    assert candidate["id"] == dish_id
    assert candidate["publication_version"] == "sha256:test"
    assert candidate["diet_types"] == ["vegetarian", "jain"]
    assert candidate["allergens"] == ["sesame", "soy"]
    assert candidate["regions"] == ["Maharashtra", "west"]
    assert candidate["meal_classes"] == ["BF_POHA_UPMA"]


def test_publication_points_are_verified_and_streamed(tmp_path):
    directory, version = _publication(tmp_path)
    points = list(iter_publication_points(directory))
    assert len(points) == 1
    assert points[0]["id"] == "00000000-0000-0000-0000-000000000001"
    assert points[0]["payload"]["publication_version"] == version
    assert len(points[0]["vector"]) == 64

    with (directory / "catalogue.jsonl").open("a") as handle:
        handle.write("{}\n")
    try:
        list(iter_publication_points(directory))
    except ValueError as error:
        assert "manifest" in str(error)
    else:
        raise AssertionError("tampered publication should fail verification")


def test_publication_upload_uses_new_versioned_collection_and_verifies_count(tmp_path, monkeypatch):
    directory, version = _publication(tmp_path)
    calls = []

    def fake_request(url, method, payload, timeout):
        calls.append((url, method, payload, timeout))
        if url.endswith("/points/count"):
            return {"result": {"count": 1}}
        return {"result": True}

    monkeypatch.setattr("aux_re_service.training.retrieval_pipeline._request", fake_request)
    collection = f"foofoo_recipes__{version.removeprefix('sha256:')[:12]}"
    report = upload_publication(directory, "http://localhost:6333", collection)
    assert report["uploaded"] == report["verified_count"] == 1
    assert calls[0][0].endswith(f"/collections/{collection}")
    assert calls[0][1] == "PUT"
    assert calls[1][2]["points"][0]["payload"]["publication_version"] == version


def test_ranking_metrics_cover_quality_diversity_repetition_and_safety():
    metrics = ranking_metrics(
        {"h": ["a", "b"]},
        {"h": {"b"}},
        catalog={"a", "b", "c"},
        ingredients={"a": {"rice"}, "b": {"lentil"}},
        recent={"h": {"a"}},
        unsafe={"h": {"b"}},
        k=2,
    )
    assert metrics.precision_at_k == 0.5
    assert metrics.recall_at_k == 1.0
    assert metrics.intra_list_diversity == 1.0
    assert metrics.repetition_rate == 0.5
    assert metrics.safety_violations == 1


def test_trained_lightfm_report_beats_popularity_baseline():
    report = json.loads(
        (ROOT / "aux_re_service" / "data" / "models" / "lightfm_v2_report.json").read_text()
    )
    assert report["format"] == "foofoo-lightfm-v2"
    assert report["model_type"] == "LightFM-WARP-hybrid"
    assert report["promotion_gate_passed"] is True
    assert report["metric_deltas"]["recall_at_10"] > 0
    assert report["metric_deltas"]["ndcg_at_10"] > 0
    assert report["activation_scope"] == "shadow_validation_only"
    assert report["production_eligible"] is False


def test_quality_gate_allows_shadow_but_defers_graph_models_and_active_use():
    report = evaluate(
        TRAINING,
        ROOT / "aux_re_service" / "data" / "retrieval" / "v1",
        ROOT / "aux_re_service" / "data" / "models" / "lightfm_v2_report.json",
    )
    assert report["shadow_gate_passed"] is True
    assert report["production_activation_allowed"] is False
    assert report["models"]["lightfm"]["ready_for_shadow"] is True
    assert report["models"]["lightgcn"]["ready"] is False
    assert report["models"]["kgat"]["ready"] is False
    assert "no_real_interactions" in report["models"]["lightgcn"]["blockers"]


def test_ontology_contains_substitution_season_spice_and_household_relations():
    ontology = json.loads((TRAINING / "canonical_food_ontology.json").read_text())
    relations = {row["relation"] for row in ontology["relations"]}
    node_types = {row["type"] for row in ontology["nodes"]}
    assert {"substitutes_for", "similar_to", "incompatible_with"} <= relations
    assert {"season", "occasion", "spice_profile", "nutrition_trait", "allergy"} <= node_types
    assert any(dish["substitutes"] for dish in ontology["dishes"])


def test_graph_exports_are_ready_but_training_is_truthfully_blocked(tmp_path):
    report = export(TRAINING, tmp_path)
    assert report["interactions"] > 25000
    assert report["lightgcn_training_allowed"] is False
    assert report["kgat_training_allowed"] is False
    assert (tmp_path / "foofoo.inter").is_file()
    assert (tmp_path / "foofoo.kg").is_file()
