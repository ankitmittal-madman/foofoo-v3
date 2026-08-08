"""Regression tests for identity-free shifted-field evidence over deferred meal slots."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import pytest

from ops.recommendation.deferred_meal_slot_evidence import build_manifest, load_policy

POLICY = Path("ops/recommendation/policies/deferred_meal_slot_shifted_field_policy_v1.json")
SOURCE = Path("database/seeds/IndianFoodDatasetCSV.csv")
MIGRATION = Path("database/migrations/121_audit_deferred_meal_slot_shifted_field_evidence.sql")
VALIDATION = Path(
    "database/validation/973_audit_deferred_meal_slot_shifted_field_evidence_validation.sql"
)
ROLLBACK = Path(
    "database/rollback/121_audit_deferred_meal_slot_shifted_field_evidence_rollback.sql"
)
WORKFLOW = Path(".github/workflows/recommendation-deferred-meal-slot-audit.yml")
POLICY_SHA256 = "94d5f198bbb1244d631a23c5dc95200a6be860d6609dfc6a6bb0c1a7cb5717ac"


def test_policy_is_exact_report_only_and_field_bound() -> None:
    """The audit must use only the known shifted field and fixed malformed-course vocabulary."""
    document = json.loads(POLICY.read_text(encoding="utf-8"))

    assert load_policy(POLICY) == POLICY_SHA256
    assert hashlib.sha256(POLICY.read_bytes()).hexdigest() == POLICY_SHA256
    assert document["report_only"] is True
    assert document["shifted_field"] == "cuisine_raw"
    assert document["source_scope"]["manifest_row_count"] == 62
    assert document["source_scope"]["route_row_counts"]["unresolved_food_role"] == 50


def test_manifest_is_deterministic_complete_and_identity_free(tmp_path: Path) -> None:
    """All 62 malformed rows must reproduce one aggregate-safe four-column manifest."""
    first = tmp_path / "first.tsv"
    second = tmp_path / "second.tsv"
    first_summary = build_manifest(SOURCE, POLICY, first)
    second_summary = build_manifest(SOURCE, POLICY, second)

    assert first.read_bytes() == second.read_bytes()
    assert first_summary == second_summary
    assert first_summary["manifest_row_count"] == 62
    assert len(first.read_text(encoding="utf-8").splitlines()) == 62
    assert all(len(line.split("\t")) == 4 for line in first.read_text().splitlines())
    with first.open(encoding="utf-8", newline="") as handle:
        parsed = list(csv.reader(handle, delimiter="\t"))
    assert all(len(row) == 4 for row in parsed)
    assert any(row[2] == "unresolved_food_role" and row[3] == "" for row in parsed)
    assert '\t""\n' in first.read_text(encoding="utf-8")
    assert "dish_name" not in first_summary
    assert "url" not in first_summary


def test_policy_rejects_name_inference_or_mapping_drift(tmp_path: Path) -> None:
    """A widened heuristic or changed mapping must require a new reviewed policy."""
    document = json.loads(POLICY.read_text(encoding="utf-8"))
    changed = tmp_path / "changed.json"
    document["shifted_field"] = "recipe_name"
    changed.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(ValueError, match="field-bound"):
        load_policy(changed)

    document["shifted_field"] = "cuisine_raw"
    document["direct_mappings"]["world breakfast"] = ["lunch"]
    changed.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(ValueError, match="mapping drifted"):
        load_policy(changed)


def test_sql_report_is_exact_private_aggregate_and_non_mutating() -> None:
    """Production reporting must bind all counts and expose no row or dish identity."""
    migration = MIGRATION.read_text(encoding="utf-8")
    validation = VALIDATION.read_text(encoding="utf-8")
    rollback = ROLLBACK.read_text(encoding="utf-8")

    for required in (
        POLICY_SHA256,
        "p_expected_manifest_row_count <> 62",
        "p_expected_diet_deferred_dish_count <> 22",
        "p_expected_direct_conflict_dish_count <> 1",
        "deferred production dish scope drifted",
        "deferred production evidence failed checked-in manifest integrity",
        "shifted_direct_slot_candidate",
        "shifted_contextual_slot_candidate",
        "requires_food_role_review",
        "name_inference_used', false",
        "automatic_acceptance_allowed', false",
        "dish_changed', false",
        "publication_changed', false",
        "serving_changed', false",
    ):
        assert required in migration
    assert "deferred shifted-field report must remain service-only" in validation
    assert "UPDATE public.dishes" not in migration
    assert "INSERT INTO public.dishes" not in migration
    assert "DROP FUNCTION IF EXISTS" in rollback
    assert "DROP TABLE" not in rollback


def test_workflow_is_protected_read_only_and_uploads_only_aggregate_report() -> None:
    """The protected run must verify identity and never publish, deploy or alter Aux mode."""
    workflow = WORKFLOW.read_text(encoding="utf-8")

    for required in (
        "environment: production",
        "github.ref == 'refs/heads/main'",
        "audit-deferred-meal-slot-shifted-field-v1",
        "database_identifies_project",
        POLICY_SHA256,
        "BEGIN TRANSACTION READ ONLY",
        "expected_deferred_course_manifest",
        "diet_deferred_dish_count == 22",
        "direct_conflict_dish_count == 1",
        "deferred-meal-slot-shifted-field-report.json",
    ):
        assert required in workflow
    assert "AUX_RE_MODE=" not in workflow
    assert "fly deploy" not in workflow
    assert "publish-recommendation-catalogue" not in workflow
    assert "cancel-in-progress: false" in workflow
