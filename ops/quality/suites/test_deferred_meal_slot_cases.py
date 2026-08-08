"""Regression gates for the final private deferred meal-slot case cohort."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

POLICY = Path("ops/recommendation/policies/deferred_meal_slot_case_policy_v1.json")
MIGRATION = Path("database/migrations/123_govern_deferred_meal_slot_cases.sql")
VALIDATION = Path("database/validation/975_govern_deferred_meal_slot_cases_validation.sql")
ROLLBACK = Path("database/rollback/123_govern_deferred_meal_slot_cases_rollback.sql")
WORKFLOW = Path(".github/workflows/recommendation-deferred-meal-slot-cases.yml")
POLICY_SHA256 = "339916734763f073080cec4079f51401955da7af5df996076c1cc851b92b68da"


def test_case_policy_pins_production_audit_without_serving_authority() -> None:
    """The exact 23-case result must be hash-bound and unable to authorize serving changes."""
    document = json.loads(POLICY.read_text(encoding="utf-8"))

    assert hashlib.sha256(POLICY.read_bytes()).hexdigest() == POLICY_SHA256
    assert document == {
        "audit_policy_sha256": (
            "94d5f198bbb1244d631a23c5dc95200a6be860d6609dfc6a6bb0c1a7cb5717ac"
        ),
        "candidate_slot_set_counts": {"breakfast": 2, "dinner": 1, "lunch,dinner": 2},
        "case_count": 23,
        "case_route_counts": {
            "conflicting_direct_slots": 1,
            "requires_food_role_review": 17,
            "shifted_contextual_slot_candidate": 2,
            "shifted_direct_slot_candidate": 3,
        },
        "diet_evidence_link_count": 88,
        "policy_version": "deferred-meal-slot-case-generation-v1",
        "report_only_source_policy": "deferred-course-shifted-field-audit-v1",
        "schema_version": "deferred-meal-slot-case-policy-v1",
        "serving_mutation_allowed": False,
    }


def test_case_schema_is_private_immutable_and_separate_from_dish_truth() -> None:
    """Case and evidence rows remain private review state, never public dish facts."""
    migration = MIGRATION.read_text(encoding="utf-8")
    validation = VALIDATION.read_text(encoding="utf-8")
    rollback = ROLLBACK.read_text(encoding="utf-8")

    for required in (
        "CREATE TABLE ops.deferred_meal_slot_cases",
        "CREATE TABLE ops.deferred_meal_slot_case_evidence",
        "ENABLE ROW LEVEL SECURITY",
        "deferred_meal_slot_case_lifecycle_guard",
        "deferred_meal_slot_case_evidence_immutable",
        "case_status text NOT NULL DEFAULT 'pending_review'",
        "automatic_acceptance_allowed', false",
        "dish_changed', false",
        "proposal_changed', false",
        "publication_changed', false",
        "serving_changed', false",
    ):
        assert required in migration
    assert "must remain service-only" in validation
    assert "UPDATE public.dishes" not in migration
    assert "INSERT INTO public.dishes" not in migration
    assert "dish_meal_slot_proposals" not in migration
    assert "dish_meal_slot_set_proposals" not in migration
    assert "DROP TABLE" not in rollback
    assert "Retained private deferred meal-slot case ledger" in rollback


def test_generator_fails_closed_on_exact_routes_slots_and_evidence() -> None:
    """Generation must reconcile the production audit rather than accept a partial cohort."""
    migration = MIGRATION.read_text(encoding="utf-8")

    for required in (
        POLICY_SHA256,
        "p_expected_manifest_row_count <> 62",
        "p_expected_case_count <> 23",
        "p_expected_diet_evidence_link_count <> 88",
        "recovery_route = 'shifted_direct_slot_candidate') <> 3",
        "recovery_route = 'shifted_contextual_slot_candidate') <> 2",
        "recovery_route = 'requires_food_role_review') <> 17",
        "recovery_route = 'conflicting_direct_slots') <> 1",
        "array_to_string(proposed_slots, ',') = 'breakfast') <> 2",
        "array_to_string(proposed_slots, ',') = 'dinner') <> 1",
        "array_to_string(proposed_slots, ',') = 'lunch,dinner') <> 2",
        "<> 'dinner,snacks'",
        "deferred case source evidence integrity failed",
        "stored deferred case evidence does not exactly match generated evidence",
    ):
        assert required in migration


def test_workflow_has_separate_install_and_generate_gates() -> None:
    """Production writes only private pending cases and proves dish/proposal state is unchanged."""
    workflow = WORKFLOW.read_text(encoding="utf-8")

    for required in (
        "environment: production",
        "github.ref == 'refs/heads/main'",
        "install-deferred-meal-slot-case-boundary",
        "generate-deferred-meal-slot-cases-v1",
        "database_identifies_project",
        POLICY_SHA256,
        "before_dishes=",
        "after_dishes=",
        "before_proposals=",
        "after_proposals=",
        "total_cases == 23",
        "diet_evidence_links == 88",
        "case_status == \"pending_review\"",
        "automatic_acceptance_allowed == false",
        "deferred-meal-slot-case-generation.json",
    ):
        assert required in workflow
    assert "AUX_RE_MODE=" not in workflow
    assert "fly deploy" not in workflow
    assert "publish-recommendation-catalogue" not in workflow
    assert "cancel-in-progress: false" in workflow
