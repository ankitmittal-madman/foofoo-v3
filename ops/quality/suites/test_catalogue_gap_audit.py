from pathlib import Path


MIGRATION = Path("database/migrations/102_expose_recommendation_catalogue_gaps.sql")
VALIDATION = Path("database/validation/954_expose_recommendation_catalogue_gaps_validation.sql")
ROLLBACK = Path("database/rollback/102_expose_recommendation_catalogue_gaps_rollback.sql")
WORKFLOW = Path(".github/workflows/recommendation-catalogue-gap-audit.yml")


def test_gap_report_is_aggregate_service_only_and_user_free():
    """The production audit must expose only counts through a service-only function."""
    text = MIGRATION.read_text()

    assert "catalogue_publication_gap_report" in text
    assert "RETURNS jsonb" in text
    assert "SECURITY DEFINER" in text
    assert "FROM PUBLIC, anon, authenticated" in text
    assert "GRANT EXECUTE" in text
    for forbidden_table in ("profiles", "households", "feedback_events", "recommendation_events"):
        assert forbidden_table not in text


def test_gap_report_mirrors_every_publication_requirement():
    """The gap audit must count every gate that controls the canonical publication."""
    text = MIGRATION.read_text()

    for gate in (
        "ontology_status",
        "diet_type",
        "is_jain",
        "allergen_flags",
        "cuisine_id",
        "dish_ingredients",
        "dish_meal_class_mappings",
        "hero_role",
        "spice_level",
        "heaviness",
        "cooking_method",
        "texture",
        "richness",
        "weather_affinity",
        "meal_type",
    ):
        assert gate in text
    assert "review_status <> 'rejected'" in text
    assert "requirements_per_active_dish', 15" in text


def test_gap_report_has_reconciliation_validation_and_rollback():
    """The report must fail deployment if inventory, funnel, or distribution counts drift."""
    validation = VALIDATION.read_text()
    rollback = ROLLBACK.read_text()

    for invariant in (
        "stored catalogue inventory does not reconcile",
        "active catalogue inventory does not reconcile",
        "catalogue readiness funnel is not monotonic",
        "missing-gate distribution does not cover every active dish",
        "zero-gap dishes do not match publishable dishes",
    ):
        assert invariant in validation
    assert "DROP FUNCTION IF EXISTS re_engine.catalogue_publication_gap_report()" in rollback


def test_gap_audit_workflow_is_protected_bounded_and_does_not_route_aux():
    """The production workflow must verify identity, serialize schema work, and leave serving off."""
    text = WORKFLOW.read_text()

    assert "environment: production" in text
    assert "github.ref == 'refs/heads/main'" in text
    assert "database_identifies_project" in text
    assert "pg_advisory_xact_lock" in text
    assert "--single-transaction" in text
    assert "SET TRANSACTION READ ONLY" in text
    assert "recommendation-catalogue-gap-report.json" in text
    assert "AUX_RE_MODE" not in text
    assert "fly deploy" not in text
