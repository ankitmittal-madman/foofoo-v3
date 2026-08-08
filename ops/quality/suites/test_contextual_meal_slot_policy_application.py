"""Regression tests for the approval-bound contextual slot-set application boundary."""

from __future__ import annotations

from pathlib import Path

MIGRATION = Path(
    "database/migrations/120_govern_contextual_meal_slot_policy_application.sql"
)
VALIDATION = Path(
    "database/validation/972_govern_contextual_meal_slot_policy_application_validation.sql"
)
ROLLBACK = Path(
    "database/rollback/120_govern_contextual_meal_slot_policy_application_rollback.sql"
)
WORKFLOW = Path(
    ".github/workflows/recommendation-contextual-meal-slot-policy-application.yml"
)
POLICY_SHA256 = "5afca8a6da05a6070abc6678d0a4f73924cafad62835e9152916efe6e7596154"


def test_application_boundary_is_exact_approval_bound_and_reversible() -> None:
    """Application must bind all evidence and retain exact before/after dish arrays."""
    migration = MIGRATION.read_text(encoding="utf-8")

    for required in (
        POLICY_SHA256,
        "p_expected_proposal_count <> 775",
        "p_expected_evidence_link_count <> 3121",
        "p_expected_manifest_row_count <> 2003",
        "an explicit Product approval reference is required",
        "contextual proposal, evidence or manifest cohort drifted",
        "contextual slot-set proposal distribution drifted",
        "contextual application evidence does not match checked-in manifest",
        "previous_meal_occasion",
        "applied_meal_occasion",
        "approval_reference",
        "FOR UPDATE OF p, d",
        "proposal_status = 'approved'",
        "proposal_status = 'applied'",
        "proposal_status = 'rolled_back'",
        "contextual rollback refused because current state is partial or changed",
        "publication_changed', false",
        "serving_changed', false",
    ):
        assert required in migration


def test_application_ledger_is_private_and_function_gated() -> None:
    """Clients cannot inspect or mutate approval evidence, while service writes use functions."""
    migration = MIGRATION.read_text(encoding="utf-8")
    validation = VALIDATION.read_text(encoding="utf-8")

    assert "ENABLE ROW LEVEL SECURITY" in migration
    assert "FROM PUBLIC, anon, authenticated" in migration
    assert "REVOKE ALL ON ops.dish_meal_slot_set_applications FROM service_role" in migration
    assert "GRANT SELECT ON ops.dish_meal_slot_set_applications TO service_role" in migration
    assert "contextual meal-slot application ledger must enforce RLS" in validation
    assert "contextual application functions must remain service-only" in validation
    assert "application ledger, proposal and dish state diverged" in validation


def test_schema_rollback_disables_mutation_without_erasing_evidence() -> None:
    """Schema rollback must preserve the ledger and direct operators to restore facts first."""
    rollback = ROLLBACK.read_text(encoding="utf-8")

    assert "Use ops.rollback_contextual_meal_slot_set_policy first" in rollback
    assert "DROP FUNCTION IF EXISTS ops.apply_contextual_meal_slot_set_policy" in rollback
    assert "DROP FUNCTION IF EXISTS ops.rollback_contextual_meal_slot_set_policy" in rollback
    assert "DROP TABLE" not in rollback
    assert "DELETE FROM" not in rollback
    assert "UPDATE public.dishes" not in rollback


def test_workflow_requires_protected_human_approval_and_forces_aux_off() -> None:
    """Only exact protected confirmations may mutate, and every mutation forces Aux routing off."""
    workflow = WORKFLOW.read_text(encoding="utf-8")

    for required in (
        "environment: production",
        "github.ref == 'refs/heads/main'",
        "install-contextual-meal-slot-policy-boundary",
        "apply-contextual-meal-slot-policy-v1",
        "rollback-contextual-meal-slot-policy-v1",
        "APPROVAL_REFERENCE",
        "REVIEWED_BY",
        "database_identifies_project",
        "AUX_RE_MODE=off",
        'EXPECTED_PROPOSAL_COUNT: "775"',
        'EXPECTED_EVIDENCE_LINK_COUNT: "3121"',
        'EXPECTED_MANIFEST_ROW_COUNT: "2003"',
        "expected_contextual_source_manifest",
        "database/validation/972_govern_contextual_meal_slot_policy_application_validation.sql",
    ):
        assert required in workflow
    assert "fly deploy" not in workflow
    assert "publish-recommendation-catalogue" not in workflow
    assert "cancel-in-progress: false" in workflow


def test_install_only_path_cannot_change_dishes_or_proposals() -> None:
    """Installing the boundary alone must emit explicit non-serving evidence."""
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert 'if: inputs.action != \'install_only\'' in workflow
    assert 'if: inputs.action == \'apply\'' in workflow
    assert 'if: inputs.action == \'rollback\'' in workflow
    assert "dishes_changed: false" in workflow
    assert "proposals_changed: false" in workflow
    assert "publication_changed: false" in workflow
    assert "serving_changed: false" in workflow
