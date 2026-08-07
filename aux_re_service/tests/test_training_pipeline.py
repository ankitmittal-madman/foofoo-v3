from __future__ import annotations

import hashlib
import json
from pathlib import Path

from aux_re_service.evaluation import ranking_metrics
from aux_re_service.training.data_pipeline import canonical_id, normalize_name
from aux_re_service.training.quality_gate import evaluate
from aux_re_service.training.retrieval_pipeline import build

ROOT = Path(__file__).parents[2]
TRAINING = ROOT / "aux_re_service" / "data" / "training" / "v1"


def test_generated_training_manifest_is_complete_and_checksummed():
    manifest = json.loads((TRAINING / "manifest.json").read_text())
    assert manifest["synthetic_only"] is True
    assert manifest["ontology_dishes"] == 86
    assert manifest["interactions"] == 35000
    assert manifest["positive_interactions"] > 20000
    assert manifest["negative_interactions"] > 5000
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
        (ROOT / "aux_re_service" / "data" / "models" / "lightfm_v1_report.json").read_text()
    )
    assert report["model_type"] == "LightFM-WARP-hybrid"
    assert report["promotion_gate_passed"] is True
    assert report["metric_deltas"]["recall_at_10"] > 0
    assert report["metric_deltas"]["ndcg_at_10"] > 0
    assert report["activation_scope"] == "shadow_validation_only"


def test_quality_gate_allows_shadow_but_defers_graph_models_and_active_use():
    report = evaluate(
        TRAINING,
        ROOT / "aux_re_service" / "data" / "retrieval" / "v1",
        ROOT / "aux_re_service" / "data" / "models" / "lightfm_v1_report.json",
    )
    assert report["shadow_gate_passed"] is True
    assert report["production_activation_allowed"] is False
    assert report["models"]["lightfm"]["ready_for_shadow"] is True
    assert report["models"]["lightgcn"]["ready"] is False
    assert report["models"]["kgat"]["ready"] is False
    assert "no_real_interactions" in report["models"]["lightgcn"]["blockers"]
