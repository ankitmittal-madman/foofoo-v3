"""Regression tests for the approval-bound, reversible direct meal-slot policy cohort."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from ops.recommendation.direct_meal_slot_policy import build_manifest, load_policy

POLICY = Path("ops/recommendation/policies/direct_meal_slot_mapping_policy_v1.json")
SOURCE = Path("database/seeds/IndianFoodDatasetCSV.csv")
MIGRATION = Path("database/migrations/116_govern_direct_meal_slot_policy_application.sql")
VALIDATION = Path(
    "database/validation/968_govern_direct_meal_slot_policy_application_validation.sql"
)
ROLLBACK = Path("database/rollback/116_govern_direct_meal_slot_policy_application_rollback.sql")
WORKFLOW = Path(".github/workflows/recommendation-meal-slot-policy-application.yml")
POLICY_SHA256 = "2dda4d35c8ab9314c89b6e56ab2d637eb9e7ba1fce9d3f113242813bdb01d3db"


def test_policy_is_exact_count_bound_and_requires_explicit_approval() -> None:
    """The checked-in mapping must identify one exact cohort and one controversial mapping."""
    document = json.loads(POLICY.read_text(encoding="utf-8"))
    mappings, digest = load_policy(POLICY)

    assert digest == POLICY_SHA256
    assert hashlib.sha256(POLICY.read_bytes()).hexdigest() == POLICY_SHA256
    assert document["requires_explicit_approval"] is True
    assert document["approval_scope"] == {
        "proposal_count": 1802,
        "evidence_link_count": 7222,
        "manifest_direct_row_count": 4806,
        "slot_counts": {
            "breakfast": 275,
            "dinner": 294,
            "lunch": 667,
            "snacks": 566,
        },
    }
    assert mappings["appetizer"] == "snacks"
    assert len(mappings) == 8


def test_policy_manifest_is_deterministic_and_identity_free(tmp_path: Path) -> None:
    """The application manifest must reproduce the verified 4,806 direct source rows exactly."""
    first = tmp_path / "first.tsv"
    second = tmp_path / "second.tsv"

    first_summary = build_manifest(SOURCE, POLICY, first)
    second_summary = build_manifest(SOURCE, POLICY, second)

    assert first.read_bytes() == second.read_bytes()
    assert first_summary == second_summary
    assert first_summary["direct_manifest_rows"] == 4806
    assert first_summary["policy_sha256"] == POLICY_SHA256
    assert len(first.read_text(encoding="utf-8").splitlines()) == 4806
    assert "dish_name" not in first_summary
    assert "source_name" not in first_summary


def test_policy_rejects_implicit_approval_or_mapping_expansion(tmp_path: Path) -> None:
    """Changing approval semantics or adding a course must invalidate the governed policy."""
    document = json.loads(POLICY.read_text(encoding="utf-8"))
    document["requires_explicit_approval"] = False
    changed = tmp_path / "changed.json"
    changed.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(ValueError, match="explicit approval"):
        load_policy(changed)

    document["requires_explicit_approval"] = True
    document["mappings"]["brunch"] = "breakfast"
    changed.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(ValueError, match="vocabulary"):
        load_policy(changed)


def test_application_sql_is_hash_pinned_atomic_and_reversible() -> None:
    """The mutation boundary must bind policy, evidence, before/after state and safe rollback."""
    migration = MIGRATION.read_text(encoding="utf-8")
    validation = VALIDATION.read_text(encoding="utf-8")
    rollback = ROLLBACK.read_text(encoding="utf-8")

    for required in (
        POLICY_SHA256,
        "p_expected_proposal_count <> 1802",
        "p_expected_evidence_link_count <> 7222",
        "p_expected_manifest_row_count <> 4806",
        "proposal distribution drifted from approved scope",
        "direct_meal_slot_proposal_row_manifest_report",
        "passes_row_manifest_integrity",
        "previous_meal_occasion",
        "applied_meal_occasion",
        "approval_reference",
        "FOR UPDATE OF p, d",
        "proposal_status = 'approved'",
        "proposal_status = 'applied'",
        "d.meal_occasion IS DISTINCT FROM a.applied_meal_occasion",
        "serving_changed', false",
        "publication_changed', false",
    ):
        assert required in migration
    assert "ENABLE ROW LEVEL SECURITY" in migration
    assert "FROM PUBLIC, anon, authenticated" in migration
    assert "REVOKE ALL ON ops.dish_meal_slot_applications FROM service_role" in migration
    assert "application ledger must enforce RLS" in validation
    assert "preserving every before/after" in rollback
    assert "DROP TABLE" not in rollback
    assert "UPDATE public.dishes" not in rollback


def test_workflow_requires_protected_approval_and_forces_aux_off() -> None:
    """Only main plus exact confirmations and protected approval may mutate the cohort."""
    workflow = WORKFLOW.read_text(encoding="utf-8")

    for required in (
        "environment: production",
        "github.ref == 'refs/heads/main'",
        "apply-direct-meal-slot-policy-v1",
        "rollback-direct-meal-slot-policy-v1",
        "APPROVAL_REFERENCE",
        "REVIEWED_BY",
        "database_identifies_project",
        "AUX_RE_MODE=off",
        "direct_meal_slot_policy",
        POLICY_SHA256,
        "\\getenv approval_reference APPROVAL_REFERENCE",
        "database/validation/968_govern_direct_meal_slot_policy_application_validation.sql",
        "test_direct_meal_slot_policy_application.py",
    ):
        assert required in workflow
    assert "fly deploy" not in workflow
    assert "publish-recommendation-catalogue" not in workflow
    assert "cancel-in-progress: false" in workflow
