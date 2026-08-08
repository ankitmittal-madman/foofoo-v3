"""Regression tests for contextual multi-slot proposals that cannot change serving facts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from ops.recommendation.contextual_meal_slot_policy import build_manifest, load_policy

POLICY = Path("ops/recommendation/policies/contextual_meal_slot_candidate_policy_v1.json")
SOURCE = Path("database/seeds/IndianFoodDatasetCSV.csv")
MIGRATION = Path("database/migrations/118_govern_contextual_meal_slot_set_proposals.sql")
VALIDATION = Path(
    "database/validation/970_govern_contextual_meal_slot_set_proposals_validation.sql"
)
ROLLBACK = Path("database/rollback/118_govern_contextual_meal_slot_set_proposals_rollback.sql")
WORKFLOW = Path(".github/workflows/recommendation-contextual-meal-slot-proposals.yml")
POLICY_SHA256 = "5afca8a6da05a6070abc6678d0a4f73924cafad62835e9152916efe6e7596154"


def test_candidate_policy_is_exact_proposal_only_and_approval_bound() -> None:
    """Coarse source categories must identify one bounded review cohort, not accepted truth."""
    document = json.loads(POLICY.read_text(encoding="utf-8"))
    mappings, digest = load_policy(POLICY)

    assert digest == POLICY_SHA256
    assert hashlib.sha256(POLICY.read_bytes()).hexdigest() == POLICY_SHA256
    assert document["proposal_only"] is True
    assert document["requires_explicit_approval"] is True
    assert document["candidate_scope"]["proposal_count"] == 775
    assert document["candidate_scope"]["manifest_candidate_row_count"] == 2003
    assert document["candidate_scope"]["slot_set_dish_counts"] == {
        "breakfast,lunch": 2,
        "lunch,dinner": 773,
    }
    assert mappings["dessert"] == ("lunch", "dinner")
    assert len(mappings) == 5


def test_contextual_manifest_is_deterministic_and_identity_free(tmp_path: Path) -> None:
    """The exact source file must produce the same fixed-category 2,003-row manifest."""
    first = tmp_path / "first.tsv"
    second = tmp_path / "second.tsv"

    first_summary = build_manifest(SOURCE, POLICY, first)
    second_summary = build_manifest(SOURCE, POLICY, second)

    assert first.read_bytes() == second.read_bytes()
    assert first_summary == second_summary
    assert first_summary["manifest_candidate_rows"] == 2003
    assert first_summary["policy_sha256"] == POLICY_SHA256
    assert len(first.read_text(encoding="utf-8").splitlines()) == 2003
    assert "dish_name" not in first_summary
    assert "source_name" not in first_summary


def test_candidate_policy_rejects_implicit_application_or_mapping_drift(tmp_path: Path) -> None:
    """Changing approval semantics or one proposed slot set must invalidate the policy hash."""
    document = json.loads(POLICY.read_text(encoding="utf-8"))
    changed = tmp_path / "changed.json"
    document["proposal_only"] = False
    changed.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(ValueError, match="proposal-only"):
        load_policy(changed)

    document["proposal_only"] = True
    document["mappings"]["dessert"] = ["snacks"]
    changed.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(ValueError, match="mapping differs"):
        load_policy(changed)


def test_proposal_sql_is_private_count_bound_and_non_serving() -> None:
    """Only an exact row-verified cohort may become pending; public dish facts stay untouched."""
    migration = MIGRATION.read_text(encoding="utf-8")
    validation = VALIDATION.read_text(encoding="utf-8")
    rollback = ROLLBACK.read_text(encoding="utf-8")

    for required in (
        POLICY_SHA256,
        "p_expected_candidate_count <> 775",
        "p_expected_manifest_row_count <> 2003",
        "contextual meal-slot candidate count drift",
        "contextual meal-slot candidate slot-set distribution drifted",
        "contextual meal-slot candidate category distribution drifted",
        "contextual proposal evidence does not match the checked-in row manifest",
        "DEFERRABLE INITIALLY DEFERRED",
        "contextual meal-slot proposal identity and policy are immutable",
        "invalid contextual meal-slot proposal lifecycle transition",
        "proposal_only', true",
        "dishes_changed', false",
        "publication_changed', false",
        "serving_changed', false",
    ):
        assert required in migration
    assert "ENABLE ROW LEVEL SECURITY" in migration
    assert "REVOKE ALL ON ops.dish_meal_slot_set_proposals FROM service_role" in migration
    assert "UPDATE public.dishes" not in migration
    assert "INSERT INTO public.dishes" not in migration
    assert "contextual meal-slot proposal tables must enforce RLS" in validation
    assert "preserving every proposal and evidence row" in rollback
    assert "DROP TABLE" not in rollback


def test_protected_workflow_generates_only_pending_review_artifacts() -> None:
    """Production generation must be exact, protected and disconnected from serving controls."""
    workflow = WORKFLOW.read_text(encoding="utf-8")

    for required in (
        "environment: production",
        "github.ref == 'refs/heads/main'",
        "generate-contextual-meal-slot-proposals-v1",
        "database_identifies_project",
        POLICY_SHA256,
        'EXPECTED_CANDIDATE_COUNT: "775"',
        'EXPECTED_MANIFEST_ROW_COUNT: "2003"',
        "expected_contextual_source_manifest",
        "--single-transaction",
        "pending_review",
        "database/validation/970_govern_contextual_meal_slot_set_proposals_validation.sql",
    ):
        assert required in workflow
    assert "AUX_RE_MODE=" not in workflow
    assert "fly deploy" not in workflow
    assert "publish-recommendation-catalogue" not in workflow
    assert "cancel-in-progress: false" in workflow
