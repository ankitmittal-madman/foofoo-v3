from pathlib import Path

MIGRATION = Path("database/migrations/102_expose_recommendation_catalogue_gaps.sql")
VALIDATION = Path("database/validation/954_expose_recommendation_catalogue_gaps_validation.sql")
ROLLBACK = Path("database/rollback/102_expose_recommendation_catalogue_gaps_rollback.sql")
WORKFLOW = Path(".github/workflows/recommendation-catalogue-gap-audit.yml")
TRANCHE_MIGRATION = Path(
    "database/migrations/103_measure_catalogue_enrichment_tranche.sql"
)
TRANCHE_VALIDATION = Path(
    "database/validation/955_measure_catalogue_enrichment_tranche_validation.sql"
)
TRANCHE_ROLLBACK = Path(
    "database/rollback/103_measure_catalogue_enrichment_tranche_rollback.sql"
)
QUALITY_MIGRATION = Path(
    "database/migrations/104_measure_published_catalogue_quality.sql"
)
QUALITY_VALIDATION = Path(
    "database/validation/956_measure_published_catalogue_quality_validation.sql"
)
QUALITY_ROLLBACK = Path(
    "database/rollback/104_measure_published_catalogue_quality_rollback.sql"
)
REMEDIATION_MIGRATION = Path(
    "database/migrations/105_measure_meal_class_remediation.sql"
)
REMEDIATION_VALIDATION = Path(
    "database/validation/957_measure_meal_class_remediation_validation.sql"
)
REMEDIATION_ROLLBACK = Path(
    "database/rollback/105_measure_meal_class_remediation_rollback.sql"
)
REMEDIATION_WORKFLOW = Path(
    ".github/workflows/recommendation-meal-class-remediation-audit.yml"
)


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
    assert "recommendation-catalogue-enrichment-tranche-report.json" in text
    assert "recommendation-catalogue-published-quality-report.json" in text
    assert "AUX_RE_MODE" not in text
    assert "fly deploy" not in text


def test_tranche_report_is_dry_run_aggregate_and_uses_existing_quality_policy():
    """Potential status reclosure must be measured against governed evidence before any write."""
    text = TRANCHE_MIGRATION.read_text()

    assert "catalogue_enrichment_tranche_report" in text
    assert "active_and_publishable_except_ontology_status" in text
    assert "seed_required_fields', 13" in text
    assert "seed_class_confidence_minimum', 0.700" in text
    assert "strict_taxonomy_confidence_minimum', 0.800" in text
    assert "strict_ingredient_confidence_minimum', 0.800" in text
    assert "UPDATE public.dishes" not in text
    assert "INSERT INTO public.dishes" not in text
    for forbidden_table in ("profiles", "households", "feedback_events", "recommendation_events"):
        assert forbidden_table not in text


def test_tranche_report_has_reconciliation_validation_and_reversible_boundary():
    """Every candidate must reconcile to either strict readiness or manual review."""
    validation = TRANCHE_VALIDATION.read_text()
    rollback = TRANCHE_ROLLBACK.read_text()

    for invariant in (
        "catalogue enrichment tranche readiness does not reconcile",
        "catalogue enrichment tranche status counts do not reconcile",
        "catalogue enrichment tranche class confidence does not reconcile",
        "catalogue enrichment tranche taxonomy confidence does not reconcile",
        "catalogue enrichment tranche ingredient confidence does not reconcile",
    ):
        assert invariant in validation
    assert "DROP FUNCTION IF EXISTS re_engine.catalogue_enrichment_tranche_report()" in rollback


def test_workflow_handles_clean_install_extension_and_read_only_revalidation():
    """The already-live gap function must extend safely without pretending partial state is clean."""
    text = WORKFLOW.read_text()

    assert "action=apply_all" in text
    assert "action=apply_tranche_and_quality" in text
    assert "action=apply_quality" in text
    assert "action=validate" in text
    assert "unsafe partial catalogue audit boundary" in text
    assert "database/migrations/103_measure_catalogue_enrichment_tranche.sql" in text
    assert "database/validation/955_measure_catalogue_enrichment_tranche_validation.sql" in text
    assert text.count("          path:") == 1


def test_published_quality_report_is_count_only_and_does_not_change_eligibility():
    """Republishing must be preceded by aggregate quality proof, not a hidden gate mutation."""
    text = QUALITY_MIGRATION.read_text()

    assert "catalogue_published_quality_report" in text
    assert "eligible_count" in text
    assert "strict_quality_ready" in text
    assert "quality_review_required" in text
    assert "class_confidence_minimum', 0.700" in text
    assert "UPDATE public.dishes" not in text
    assert "INSERT INTO public.dishes" not in text
    assert "catalogue_publication_rows" not in text
    for forbidden_table in ("profiles", "households", "feedback_events", "recommendation_events"):
        assert forbidden_table not in text


def test_published_quality_report_reconciles_with_live_publication_and_rolls_back_cleanly():
    """The quality cohort must equal the existing publication cohort and remain reversible."""
    validation = QUALITY_VALIDATION.read_text()
    rollback = QUALITY_ROLLBACK.read_text()

    for invariant in (
        "catalogue published quality count does not match publication eligibility",
        "catalogue published quality readiness does not reconcile",
        "catalogue published ontology confidence does not reconcile",
        "catalogue published class confidence does not reconcile",
        "catalogue published taxonomy confidence does not reconcile",
        "catalogue published ingredient confidence does not reconcile",
    ):
        assert invariant in validation
    assert "DROP FUNCTION IF EXISTS re_engine.catalogue_published_quality_report()" in rollback


def test_meal_class_remediation_report_is_aggregate_read_only_and_provenance_aware():
    """Weak mappings must be explained by evidence source without exposing dish identity."""
    text = REMEDIATION_MIGRATION.read_text()

    assert "catalogue_meal_class_remediation_report" in text
    assert "best_meal_class_confidence_below_0_700" in text
    assert "classification_method" in text
    assert "source_type" in text
    assert "has_curated_exact" in text
    assert "has_human_review" in text
    assert "'identity_exposed', false" in text
    assert "'automatic_confidence_upgrade_allowed', false" in text
    assert "UPDATE public." not in text
    assert "INSERT INTO public." not in text
    for forbidden_table in ("profiles", "households", "feedback_events", "recommendation_events"):
        assert forbidden_table not in text


def test_meal_class_remediation_report_reconciles_and_rolls_back_cleanly():
    """All candidates must reconcile across cohort, evidence and confidence summaries."""
    validation = REMEDIATION_VALIDATION.read_text()
    rollback = REMEDIATION_ROLLBACK.read_text()

    for invariant in (
        "catalogue meal-class remediation cohorts do not reconcile",
        "catalogue meal-class remediation ontology states do not reconcile",
        "catalogue meal-class remediation methods do not reconcile",
        "catalogue meal-class remediation sources do not reconcile",
        "catalogue meal-class remediation review states do not reconcile",
        "catalogue meal-class remediation confidence does not reconcile",
        "catalogue meal-class remediation mapping cardinality does not reconcile",
    ):
        assert invariant in validation
    assert (
        "DROP FUNCTION IF EXISTS re_engine.catalogue_meal_class_remediation_report()"
        in rollback
    )


def test_meal_class_remediation_workflow_is_protected_and_keeps_aux_untouched():
    """The diagnostic must prove DB identity, serialize install and never route Aux."""
    text = REMEDIATION_WORKFLOW.read_text()

    assert "environment: production" in text
    assert "github.ref == 'refs/heads/main'" in text
    assert "database_identifies_project" in text
    assert "pg_advisory_xact_lock" in text
    assert "--single-transaction" in text
    assert "SET TRANSACTION READ ONLY" in text
    assert "recommendation-meal-class-remediation-report.json" in text
    assert "AUX_RE_MODE" not in text
    assert "fly deploy" not in text
