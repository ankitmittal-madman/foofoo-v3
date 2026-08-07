from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

import pytest

from ops.recommendation.relocate_auto_engine_research import (
    FORMAT,
    _canonical,
    _read_transfer,
    _validate_record,
)

ROOT = Path(__file__).parents[3]


def sample_record() -> dict[str, object]:
    payload = {"record_type": "interaction", "household_id": "expert-hh-001"}
    return {
        "id": "00000000-0000-0000-0000-000000000001",
        "target_table": "research.interactions",
        "record_key": "expert-hh-001:event-1",
        "payload": payload,
        "payload_sha256": hashlib.sha256(_canonical(payload)).hexdigest(),
        "source_type": "expert_research_synthetic",
        "generation_method": "expert-household-research-v1",
        "confidence": "0.9100",
        "confidence_band": "high",
        "ontology_mapping_status": "mapped",
        "ontology_version": "indian-food-ontology-v2",
        "provenance_tags": ["method:deterministic_expert_templates"],
        "explanation": "Synthetic test record.",
        "first_batch_id": "sha256:test",
        "last_batch_id": "sha256:test",
        "version": 1,
        "created_at": "2026-08-07 00:00:00+00",
        "updated_at": "2026-08-07 00:00:00+00",
        "synthetic_only": True,
        "source_dataset_version": "legacy:auto-engine",
        "generation_version": "auto-engine-v1",
        "transformation_version": "auto-engine-v1",
        "source_lineage": [],
    }


def test_transfer_rejects_non_synthetic_or_unapproved_targets():
    record = sample_record()
    record["synthetic_only"] = False
    with pytest.raises(RuntimeError, match="only synthetic"):
        _validate_record(record)

    record = sample_record()
    record["target_table"] = "public.profiles"
    with pytest.raises(RuntimeError, match="unsafe transfer target"):
        _validate_record(record)


def test_transfer_manifest_detects_content_tampering(tmp_path):
    transfer = tmp_path / "records.jsonl.gz"
    manifest = tmp_path / "manifest.json"
    line = _canonical(sample_record()) + b"\n"
    with gzip.open(transfer, "wb") as output:
        output.write(line)
    manifest.write_text(
        json.dumps(
            {
                "format": FORMAT,
                "record_count": 1,
                "content_sha256": "0" * 64,
                "target_counts": {"research.interactions": 1},
            }
        )
    )
    with pytest.raises(RuntimeError, match="content checksum"):
        _read_transfer(transfer, manifest)


def test_workflows_never_use_production_as_auto_engine_write_target():
    auto_engine = (ROOT / ".github/workflows/recommendation-auto-engine.yml").read_text()
    assert "TRAINING_DATABASE_URL" in auto_engine
    assert "environment: training" in auto_engine
    assert "--production-snapshot" in auto_engine
    assert "write-auto-engine-training-project" in auto_engine

    relocation = (ROOT / ".github/workflows/relocate-auto-engine-research.yml").read_text()
    assert "environment: production" in relocation
    assert "environment: training" in relocation
    assert "relocate-auto-engine-research" in relocation
