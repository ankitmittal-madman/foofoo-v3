from __future__ import annotations

import json
import re
from decimal import Decimal
from pathlib import Path

import pytest

from ops.recommendation.auto_engine import (
    _load_production_snapshot,
    run_auto_engine,
)
from ops.recommendation.auto_engine_inspector import (
    AUDIT_QUERIES,
    PRODUCTION_ENTITY_NAMES,
    RESEARCH_ENTITY_NAMES,
    inspect_database,
)
from ops.recommendation.auto_engine_ontology import load_ontology, map_and_score_records
from ops.recommendation.auto_engine_research import generate_research_records
from ops.recommendation.auto_engine_store import (
    DryRunTrainingStore,
    MemoryTrainingStore,
    payload_sha256,
)
from ops.recommendation.auto_engine_training import _prepare_research_snapshot
from ops.recommendation.auto_engine_types import AutoEngineConfig

ROOT = Path(__file__).parents[3]
ONTOLOGY = ROOT / "aux_re_service/data/training/v1/canonical_food_ontology.json"


class FakeCursor:
    def __init__(self, counts):
        self.counts = counts
        self.entity = ""
        self.description = None

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def execute(self, query, _params=None):
        match = re.search(r"auto_engine:([a-z_]+)", query)
        if not match:
            raise AssertionError(f"unexpected query: {query}")
        self.entity = match.group(1)

    def fetchone(self):
        total, usable = self.counts.get(self.entity, (0, 0))
        return {
            "total_records": total,
            "usable_records": usable,
            "missing_fields": max(0, total - usable),
            "duplicate_records": 0,
            "orphan_records": 0,
            "low_confidence_records": 0,
        }


class FakeConnection:
    def __init__(self, counts):
        self.counts = counts

    def cursor(self):
        return FakeCursor(self.counts)


def strong_counts():
    values = dict.fromkeys(AUDIT_QUERIES, (1_000, 1_000))
    values.update(
        dishes=(200, 200),
        ontology_relations=(1_000, 1_000),
        households=(6_000, 6_000),
        feedback_events=(20_000, 20_000),
        labeled_training_rows=(20_000, 20_000),
        ingredients=(200, 200),
        substitutions=(100, 100),
        regions=(36, 36),
        candidate_vectors=(200, 200),
    )
    return values


def test_inspector_reads_every_required_db_entity_before_deciding():
    report = inspect_database(FakeConnection(strong_counts()), AutoEngineConfig())
    assert len(report.rows) == len(AUDIT_QUERIES)
    assert report.enrichment_targets == ()
    assert report.strong_enough_for_baseline is True
    assert report.model_readiness["lightgcn"]["ready"] is True
    assert report.model_readiness["kgat"]["ready"] is True


def test_inspector_routes_research_queries_to_the_training_connection():
    production = FakeConnection(strong_counts())
    training = FakeConnection(
        {
            "research_household_personas": (24, 24),
            "research_interactions": (240, 240),
            "research_weekly_plans": (24, 24),
            "research_substitutions": (37, 37),
        }
    )
    report = inspect_database(production, AutoEngineConfig(), research_connection=training)
    by_name = {row.entity_type: row for row in report.rows}
    assert tuple(by_name) == PRODUCTION_ENTITY_NAMES + RESEARCH_ENTITY_NAMES
    assert by_name["research_interactions"].total_records == 240
    assert by_name["dishes"].total_records == 200


def test_production_snapshot_rejects_missing_or_reordered_entities(tmp_path):
    snapshot = tmp_path / "snapshot.json"
    snapshot.write_text(
        json.dumps(
            {
                "format": "foofoo-production-audit-v1",
                "entities": [
                    {
                        "entity_type": name,
                        "source_table": AUDIT_QUERIES[name][0],
                        "total_records": 1,
                        "usable_records": 1,
                    }
                    for name in reversed(PRODUCTION_ENTITY_NAMES)
                ],
            }
        )
    )
    with pytest.raises(RuntimeError, match="missing, extra, or reordered"):
        _load_production_snapshot(snapshot)


def test_postgres_research_fetch_is_bounded_and_parameterized():
    from ops.recommendation.auto_engine_store import PostgresTrainingStore

    class Cursor:
        description = [("record_key",)]

        def __init__(self):
            self.query = ""
            self.params = ()

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def execute(self, query, params):
            self.query = query
            self.params = params

        def fetchall(self):
            return []

    cursor = Cursor()

    class Connection:
        def cursor(self):
            return cursor

    rows = PostgresTrainingStore(Connection()).fetch_research_records(
        "research.interactions", 50_000
    )

    assert rows == []
    assert "LIMIT %s" in cursor.query
    assert "ORDER BY target_table, record_key" in cursor.query
    assert cursor.params == ("research.interactions", 50_000)


def test_research_snapshot_normalizes_postgres_decimal_confidence(tmp_path):
    household = {
        "payload": {"household_id": "hh-1", "features": ["diet:vegetarian"]}
    }
    interaction = {
        "record_key": "event-1",
        "payload": {
            "household_id": "hh-1",
            "dish_id": "poha",
            "event_type": "like",
            "weight": 1.0,
        },
        "confidence": Decimal("0.9100"),
    }

    class Store:
        def fetch_research_records(self, target_table, _limit):
            if target_table == "research.household_personas":
                return [household]
            if target_table == "research.interactions":
                return [interaction]
            return []

    destination = tmp_path / "snapshot"
    counts = _prepare_research_snapshot(Store(), ONTOLOGY, destination, AutoEngineConfig())
    saved = json.loads((destination / "interactions.jsonl").read_text())

    assert counts == {"households": 1, "interactions": 1}
    assert saved["confidence"] == 0.91


def test_weak_db_triggers_bounded_expert_research_and_ontology_mapping():
    config = AutoEngineConfig(research_household_limit=4, research_interaction_limit=24)
    inspection = inspect_database(FakeConnection({}), config)
    ontology = load_ontology(ONTOLOGY)
    proposed = generate_research_records(inspection, ontology, config)
    mapped, summary = map_and_score_records(proposed, ontology, config)
    target_tables = {record.target_table for record in mapped}
    assert {
        "research.household_personas",
        "research.user_personas",
        "research.meal_examples",
        "research.interactions",
        "research.weekly_plans",
        "research.substitution_examples",
    } <= target_tables
    assert summary["rejected"] == 0
    assert all(record.confidence >= config.minimum_confidence for record in mapped)
    assert all(record.provenance_tags for record in mapped)
    assert all(record.ontology_mapping_status in {"mapped", "not_applicable"} for record in mapped)
    dishes = {dish["id"]: dish for dish in ontology["dishes"]}
    households = {
        record.payload["household_id"]: record.payload
        for record in mapped
        if record.target_table == "research.household_personas"
    }
    for record in mapped:
        if record.target_table != "research.interactions" or record.payload["weight"] <= 0:
            continue
        allergies = set(households[record.payload["household_id"]]["allergies"])
        assert not allergies.intersection(dishes[record.payload["dish_id"]]["allergens"])


def test_seed_repeats_are_idempotent_and_report_exact_table_counts(tmp_path):
    config = AutoEngineConfig(research_household_limit=3, research_interaction_limit=18)
    connection = FakeConnection({})
    store = MemoryTrainingStore()
    first = run_auto_engine(
        connection,
        store=store,
        mode="dry_run",
        ontology_path=ONTOLOGY,
        output_dir=tmp_path / "first",
        config=config,
    )
    second = run_auto_engine(
        connection,
        store=store,
        mode="dry_run",
        ontology_path=ONTOLOGY,
        output_dir=tmp_path / "second",
        config=config,
    )
    assert first["seeding"]["total_inserted"] == first["research_generation"]["generated_records"]
    assert first["seeding"]["total_rejected"] == 0
    assert first["research_generation"]["batch_confidence"] >= config.minimum_confidence
    assert first["research_generation"]["batch_confidence_band"] in {"high", "medium"}
    assert second["seeding"]["total_inserted"] == 0
    assert second["seeding"]["total_skipped"] == first["seeding"]["total_inserted"]
    assert first["batch_id"] == second["batch_id"]
    assert first["run_id"] != second["run_id"]


def test_dry_run_reads_existing_db_staging_and_reports_skip(monkeypatch):
    config = AutoEngineConfig(research_household_limit=1, research_interaction_limit=1)
    inspection = inspect_database(FakeConnection({}), config)
    ontology = load_ontology(ONTOLOGY)
    proposed = generate_research_records(inspection, ontology, config)
    mapped, _ = map_and_score_records(proposed, ontology, config)
    record = mapped[0]
    stored = {
        "record_key": record.record_key,
        "payload": record.payload,
        "payload_sha256": payload_sha256(record.payload),
        "confidence": record.confidence,
        "confidence_band": record.confidence_band,
        "ontology_mapping_status": record.ontology_mapping_status,
        "ontology_version": record.ontology_version,
        "source_type": record.source_type,
        "generation_method": record.generation_method,
        "provenance_tags": list(record.provenance_tags),
        "explanation": record.explanation,
        "first_batch_id": "prior",
        "last_batch_id": "prior",
        "version": 1,
    }
    store = DryRunTrainingStore(object())
    monkeypatch.setattr(
        store.source,
        "fetch_research_records_by_keys",
        lambda target, keys: [stored]
        if target == record.target_table and record.record_key in keys
        else [],
    )
    run_id, _ = store.begin_run("batch", config.engine_version, "dry_run", config.as_dict())
    counts = store.seed_records(run_id, "batch", [record], config.minimum_confidence)
    assert counts[record.target_table].inserted == 0
    assert counts[record.target_table].skipped == 1


def test_strong_db_uses_existing_data_and_does_not_generate_filler(tmp_path):
    report = run_auto_engine(
        FakeConnection(strong_counts()),
        store=MemoryTrainingStore(),
        mode="dry_run",
        ontology_path=ONTOLOGY,
        output_dir=tmp_path,
    )
    assert report["research_generation"]["triggered"] is False
    assert report["research_generation"]["generated_records"] == 0
    assert report["seeding"]["total_inserted"] == 0
    assert report["readiness"]["existing_recommender_untouched"] is True
    assert report["readiness"]["fallback_required"] is True


def test_weak_production_db_reuses_sufficient_staged_research(tmp_path):
    counts = {
        "research_household_personas": (24, 24),
        "research_interactions": (240, 240),
        "research_weekly_plans": (24, 24),
    }
    report = run_auto_engine(
        FakeConnection(counts),
        store=MemoryTrainingStore(),
        mode="dry_run",
        ontology_path=ONTOLOGY,
        output_dir=tmp_path,
    )
    assert report["db_audit"]["enrichment_targets"]
    assert report["research_generation"]["triggered"] is False
    assert report["research_generation"]["generated_records"] == 0


def test_audit_mode_never_generates_or_seeds(tmp_path):
    report = run_auto_engine(
        FakeConnection({}),
        store=MemoryTrainingStore(),
        mode="audit",
        ontology_path=ONTOLOGY,
        output_dir=tmp_path,
    )
    assert report["db_audit"]["enrichment_targets"]
    assert report["research_generation"]["generated_records"] == 0
    assert report["seeding"]["total_inserted"] == 0


def test_execute_refreshes_retrieval_and_trains_shadow_challenger(tmp_path, monkeypatch):
    from aux_re_service.training import lightfm_pipeline, retrieval_pipeline

    def fake_retrieval(_ontology_path, output_dir):
        output_dir.mkdir(parents=True)
        (output_dir / "qdrant_points.json").write_text('{"points": []}')
        return {"candidates": 86, "relations": 688, "points": 86}

    def fake_lightfm(_data_dir, artifact, report, **_kwargs):
        artifact.write_bytes(b"governed-shadow-candidate")
        report.write_text("{}")
        return {
            "metrics": {"recall_at_10": 0.2, "ndcg_at_10": 0.1, "catalog_coverage": 0.6},
            "promotion_gate_passed": False,
            "production_eligible": False,
        }

    monkeypatch.setattr(retrieval_pipeline, "build", fake_retrieval)
    monkeypatch.setattr(lightfm_pipeline, "train", fake_lightfm)
    report = run_auto_engine(
        FakeConnection({}),
        store=MemoryTrainingStore(),
        mode="execute",
        ontology_path=ONTOLOGY,
        output_dir=tmp_path,
        config=AutoEngineConfig(research_household_limit=10, research_interaction_limit=60),
    )
    by_name = {model["model_name"]: model for model in report["training"]["models"]}
    assert by_name["ontology_retrieval"]["status"] == "refreshed"
    assert by_name["lightfm_research_challenger"]["status"] == "trained"
    assert by_name["lightfm_research_challenger"]["gate_checks"]["production_eligible"] is False
    assert report["evaluation"]["safety"]["positive_safety_violations"] == 0
    assert report["evaluation"]["repeat_rate"] <= 0.1
    assert report["evaluation"]["regional_relevance"] >= 0.7
    assert report["evaluation"]["research_scenario_metrics"]["weekly_catalog_diversity"] >= 0.8
    assert report["evaluation"]["household_fit"] == 1.0
    assert report["readiness"]["existing_recommender_untouched"] is True


def test_control_plane_is_private_and_confidence_constrained():
    migration = (ROOT / "database/migrations/087_auto_training_control_plane.sql").read_text()
    assert "research.auto_training_records" in migration
    assert "confidence BETWEEN 0 AND 1" in migration
    assert "REVOKE ALL" in migration
    assert "FROM PUBLIC, anon, authenticated" in migration
    assert "UNIQUE (target_table, record_key)" in migration


def test_report_is_json_serializable_and_contains_all_required_sections(tmp_path):
    report = run_auto_engine(
        FakeConnection({}),
        store=MemoryTrainingStore(),
        mode="dry_run",
        ontology_path=ONTOLOGY,
        output_dir=tmp_path,
        config=AutoEngineConfig(research_household_limit=2, research_interaction_limit=12),
    )
    json.dumps(report)
    assert {
        "db_audit",
        "research_generation",
        "seeding",
        "ontology",
        "training",
        "evaluation",
        "readiness",
        "next_actions",
    } <= report.keys()
