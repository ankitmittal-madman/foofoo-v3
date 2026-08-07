from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from aux_re_service.training import db_ingestion as ingestion
from openpyxl import Workbook


def _workbook(path: Path, *, orphan_user: bool = False) -> None:
    """Create the smallest workbook that exercises the governed source-row contract."""
    workbook = Workbook()
    workbook.remove(workbook.active)
    values = {
        "DATA_households": (["household_id", "current_state_id", "household_size"], [["HH1", "MH", 1]]),
        "DATA_users": (["user_id", "household_id"], [["U1", "MISSING" if orphan_user else "HH1"]]),
        "DATA_food_preferences": (["preference_id", "household_id"], [["P1", "HH1"]]),
        "DATA_meal_history": (
            ["meal_event_id", "household_id", "canonical_dish_id", "meal_date"],
            [["ME1", "HH1", "DISH_POHA", "2026-08-01"]],
        ),
        "DATA_recommendation_events": (
            ["event_id", "user_id", "household_id", "dish_id"],
            [["EV1", "U1", "HH1", "DISH_POHA"]],
        ),
    }
    for name, (headers, rows) in values.items():
        sheet = workbook.create_sheet(name)
        sheet.append(headers)
        for row in rows:
            sheet.append(row)
    workbook.save(path)


def _training_dir(path: Path) -> Path:
    """Create a checksummed minimal domain-shaped artifact package."""
    path.mkdir()
    artifacts = {
        "canonical_food_ontology.json": json.dumps(
            {"dishes": [{"id": "DISH_POHA", "source_datasets": ["dataset_1"]}]}
        )
        + "\n",
        "household_features.jsonl": json.dumps({"household_id": "dataset_1:HH1"}) + "\n",
        "interactions.jsonl": json.dumps(
            {
                "event_id": "dataset_1:EV1",
                "household_id": "dataset_1:HH1",
                "dish_id": "DISH_POHA",
                "source_dataset": "dataset_1",
            }
        )
        + "\n",
        "weekly_signals.jsonl": json.dumps({"household_id": "dataset_1:HH1"}) + "\n",
        "household_preference_graph.jsonl": (
            json.dumps(
                {"source": "DISH_POHA", "relation": "liked_by", "target": "dataset_1:HH1"}
            )
            + "\n"
        )
        * 2,
    }
    hashes = {}
    for name, value in artifacts.items():
        (path / name).write_text(value)
        hashes[name] = hashlib.sha256(value.encode()).hexdigest()
    (path / "manifest.json").write_text(
        json.dumps(
            {
                "version": "test-training-v1",
                "generated_at": "2026-08-07T00:00:00Z",
                "synthetic_only": True,
                "sha256": hashes,
            }
        )
    )
    return path


def test_source_rows_preserve_excel_location_and_reject_orphans(tmp_path: Path):
    workbook = tmp_path / "dataset.xlsx"
    _workbook(workbook, orphan_user=True)
    rows = ingestion.read_workbook(workbook, "dataset_1")
    ingestion.validate_relationships(rows)
    user = next(row for row in rows if row.sheet_name == "DATA_users")
    assert user.source_row_number == 2
    assert user.source_record_key == "U1"
    assert user.validation_status == "rejected"
    assert "orphan:household_id->DATA_households.household_id" in user.errors


def test_build_ingestion_is_deterministic_and_writes_no_production_targets(tmp_path: Path):
    first = tmp_path / "first.xlsx"
    second = tmp_path / "second.xlsx"
    _workbook(first)
    _workbook(second)
    training = _training_dir(tmp_path / "training")
    one, rows, records = ingestion.build_ingestion(first, second, training)
    two, _, _ = ingestion.build_ingestion(first, second, training)
    assert one["batch_id"] == two["batch_id"]
    assert one["synthetic_only"] is True
    assert one["production_targets"] == []
    assert all(record.target_table.startswith("research.") for record in records)
    assert not ({record.target_table for record in records} & ingestion.PRODUCTION_DENYLIST)
    assert one["source_rows"]["total"] == len(rows)
    assert one["normalized_records"]["total"] == 5
    assert one["normalized_records"]["exact_duplicates_skipped"] == 1


def test_manifest_checksum_drift_fails_closed(tmp_path: Path):
    training = _training_dir(tmp_path / "training")
    (training / "interactions.jsonl").write_text("changed\n")
    with pytest.raises(ValueError, match="checksum failures"):
        ingestion.verify_manifest(training)


def test_unsafe_destination_configuration_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    training = _training_dir(tmp_path / "training")
    monkeypatch.setitem(ingestion.TARGETS, "dish", "public.dishes")
    with pytest.raises(RuntimeError, match="unsafe training destination"):
        ingestion.build_normalized_records(training, "batch", [])


def test_migration_keeps_training_tables_private_and_has_rollback():
    root = Path(__file__).parents[2]
    migration = (root / "database/migrations/088_govern_synthetic_training_ingestion.sql").read_text()
    rollback = (
        root / "database/rollback/088_govern_synthetic_training_ingestion_rollback.sql"
    ).read_text()
    assert "FROM PUBLIC, anon, authenticated" in migration
    assert "CHECK (synthetic_only)" in migration
    assert "DROP TABLE IF EXISTS research.training_source_rows" in rollback
    assert "public.profiles" not in rollback
