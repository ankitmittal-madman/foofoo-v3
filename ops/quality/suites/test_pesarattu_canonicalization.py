from __future__ import annotations

import csv
from pathlib import Path

CORRECTIONS = Path("data/source/dish_identity_corrections_v1.csv")
MIGRATION = Path("database/migrations/115_canonicalize_pesarattu_upma_identity.sql")
VALIDATION = Path("database/validation/967_canonicalize_pesarattu_upma_identity_validation.sql")
ROLLBACK = Path("database/rollback/115_canonicalize_pesarattu_upma_identity_rollback.sql")
WORKFLOW = Path(".github/workflows/canonicalize-pesarattu-upma.yml")


def test_pesarattu_duplicate_merge_is_explicit_and_alias_preserving() -> None:
    """The serving correction must be reviewed data, not an implicit code-only rename."""
    rows = list(csv.DictReader(CORRECTIONS.open(newline="", encoding="utf-8")))

    assert rows == [
        {
            "duplicate_name": "Pesarattu MLC",
            "canonical_name": "Pesarattu Upma",
            "retained_aliases": "Pesarattu MLC|MLA Pesarattu",
            "evidence": (
                "Authored rows have identical ingredient composition and both describe "
                "upma-stuffed pesarattu; MLC is not a canonical dish label."
            ),
        }
    ]


def test_database_canonicalization_preserves_history_and_future_resolution() -> None:
    """Production keeps the legacy UUID but removes it from active canonical serving."""
    migration = MIGRATION.read_text()
    validation = VALIDATION.read_text()

    assert "Pesarattu MLC [retired duplicate]" in migration
    assert "is_active = false" in migration
    assert "'Pesarattu MLC', 'dedupe_merge'" in migration
    assert "'MLA Pesarattu'" in migration
    assert "DELETE FROM public.dishes" not in migration
    for alias in ("Pesarattu MLC", "MLA Pesarattu"):
        assert f"resolve_canonical_dish_identity('{alias}')" in validation
    assert "Pesarattu Upma" in validation


def test_database_canonicalization_has_scoped_rollback() -> None:
    """Rollback touches only the two inserted aliases and the preserved retired row."""
    rollback = ROLLBACK.read_text()

    assert "Pesarattu MLC [retired duplicate]" in rollback
    assert "Pesarattu MLC" in rollback
    assert "MLA Pesarattu" in rollback
    assert "DROP TABLE" not in rollback
    assert "DELETE FROM public.dishes" not in rollback


def test_production_canonicalization_workflow_is_protected_and_revalidatable() -> None:
    """Deployment must prove project identity, serialize writes and emit counts only."""
    workflow = WORKFLOW.read_text()

    assert "environment: production" in workflow
    assert "github.ref == 'refs/heads/main'" in workflow
    assert "database_identifies_project" in workflow
    assert "pg_advisory_xact_lock" in workflow
    assert "--single-transaction" in workflow
    assert "SET TRANSACTION READ ONLY" in workflow
    assert "115_canonicalize_pesarattu_upma_identity.sql" in workflow
    assert "967_canonicalize_pesarattu_upma_identity_validation.sql" in workflow
    assert "identity_exposed', false" in workflow
    assert "feedback_changed', false" in workflow
    assert "recommendation_history_changed', false" in workflow
