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
COMPONENT_MIGRATION = Path(
    "database/migrations/106_govern_dish_component_compatibility.sql"
)
COMPONENT_VALIDATION = Path(
    "database/validation/958_govern_dish_component_compatibility_validation.sql"
)
COMPONENT_ROLLBACK = Path(
    "database/rollback/106_govern_dish_component_compatibility_rollback.sql"
)
COMPONENT_WORKFLOW = Path(
    ".github/workflows/recommendation-component-compatibility-audit.yml"
)
COMPLETE_COMPONENT_MIGRATION = Path(
    "database/migrations/107_complete_serving_role_readiness_coverage.sql"
)
COMPLETE_COMPONENT_VALIDATION = Path(
    "database/validation/959_complete_serving_role_readiness_coverage_validation.sql"
)
COMPLETE_COMPONENT_ROLLBACK = Path(
    "database/rollback/107_complete_serving_role_readiness_coverage_rollback.sql"
)
MEAL_SLOT_MIGRATION = Path(
    "database/migrations/108_measure_meal_slot_remediation.sql"
)
MEAL_SLOT_VALIDATION = Path(
    "database/validation/960_measure_meal_slot_remediation_validation.sql"
)
MEAL_SLOT_ROLLBACK = Path(
    "database/rollback/108_measure_meal_slot_remediation_rollback.sql"
)
MEAL_SLOT_WORKFLOW = Path(
    ".github/workflows/recommendation-meal-slot-remediation-audit.yml"
)
MEAL_SLOT_PROPOSAL_MIGRATION = Path(
    "database/migrations/109_govern_direct_meal_slot_proposals.sql"
)
MEAL_SLOT_PROPOSAL_VALIDATION = Path(
    "database/validation/961_govern_direct_meal_slot_proposals_validation.sql"
)
MEAL_SLOT_PROPOSAL_ROLLBACK = Path(
    "database/rollback/109_govern_direct_meal_slot_proposals_rollback.sql"
)
MEAL_SLOT_PROPOSAL_WORKFLOW = Path(
    ".github/workflows/recommendation-meal-slot-proposals.yml"
)
MEAL_SLOT_REVIEW_MIGRATION = Path(
    "database/migrations/110_report_direct_meal_slot_proposal_review.sql"
)
MEAL_SLOT_REVIEW_VALIDATION = Path(
    "database/validation/962_report_direct_meal_slot_proposal_review_validation.sql"
)
MEAL_SLOT_REVIEW_ROLLBACK = Path(
    "database/rollback/110_report_direct_meal_slot_proposal_review_rollback.sql"
)
MEAL_SLOT_REVIEW_WORKFLOW = Path(
    ".github/workflows/recommendation-meal-slot-proposal-review.yml"
)
MEAL_SLOT_PROVENANCE_MIGRATION = Path(
    "database/migrations/111_measure_direct_meal_slot_proposal_provenance.sql"
)
MEAL_SLOT_PROVENANCE_VALIDATION = Path(
    "database/validation/963_measure_direct_meal_slot_proposal_provenance_validation.sql"
)
MEAL_SLOT_PROVENANCE_ROLLBACK = Path(
    "database/rollback/111_measure_direct_meal_slot_proposal_provenance_rollback.sql"
)
MEAL_SLOT_PROVENANCE_WORKFLOW = Path(
    ".github/workflows/recommendation-meal-slot-proposal-provenance.yml"
)
MEAL_SLOT_SOURCE_INTEGRITY_MIGRATION = Path(
    "database/migrations/112_measure_direct_meal_slot_proposal_source_integrity.sql"
)
MEAL_SLOT_SOURCE_INTEGRITY_VALIDATION = Path(
    "database/validation/964_measure_direct_meal_slot_proposal_source_integrity_validation.sql"
)
MEAL_SLOT_SOURCE_INTEGRITY_ROLLBACK = Path(
    "database/rollback/112_measure_direct_meal_slot_proposal_source_integrity_rollback.sql"
)
MEAL_SLOT_SOURCE_INTEGRITY_WORKFLOW = Path(
    ".github/workflows/recommendation-meal-slot-proposal-source-integrity.yml"
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


def test_component_compatibility_is_slot_aware_reviewed_and_separate_from_class_identity():
    """Supporting dishes need governed grammar compatibility, not invented primary classes."""
    text = COMPONENT_MIGRATION.read_text()

    assert "food.dish_component_compatibility" in text
    assert "ops.dish_component_compatibility_proposals" in text
    assert "canonical_meal_slot" in text
    assert "WHEN 'snack' THEN 'snacks'" in text
    assert "grammar_role = 'side'" in text
    assert "component_role IN ('staple','side','accompaniment')" in text
    assert "review_status IN ('accepted','superseded')" in text
    assert "reviewed_by text NOT NULL" in text
    assert "automatic_proposal_acceptance_allowed', false" in text
    assert "publication_gate_changed', false" in text
    assert "UPDATE public.dishes" not in text
    assert "INSERT INTO public.dish_meal_class_mappings" not in text


def test_component_grammar_guard_fails_closed_and_tables_are_service_only():
    """A component assertion must match a grammar slot/role and stay off client APIs."""
    migration = COMPONENT_MIGRATION.read_text()
    validation = COMPONENT_VALIDATION.read_text()

    assert "validate_dish_component_grammar" in migration
    assert "NEW.meal_slot = ANY(v_meal_slots)" in migration
    assert "v_required_roles ? NEW.grammar_role" in migration
    assert "component compatibility requires a published grammar" in migration
    assert "accepted component compatibility may only be superseded" in migration
    assert "component proposal evidence is immutable" in migration
    assert "invalid component proposal lifecycle transition" in migration
    assert "applied proposal must reference its matching accepted compatibility fact" in migration
    assert "ENABLE ROW LEVEL SECURITY" in migration
    assert "FROM PUBLIC, anon, authenticated" in migration
    for invariant in (
        "dish component compatibility tables must enforce RLS",
        "dish component compatibility data must remain service-only",
        "accepted component compatibility violates grammar or review provenance",
        "component proposal lifecycle provenance is invalid",
        "applied component proposal does not match its accepted fact",
        "catalogue serving routes do not reconcile",
        "catalogue serving hero roles do not reconcile",
    ):
        assert invariant in validation


def test_component_compatibility_has_exact_rollback_boundary():
    """The additive component foundation must be removable without touching catalogue facts."""
    rollback = COMPONENT_ROLLBACK.read_text()

    for statement in (
        "DROP FUNCTION IF EXISTS re_engine.catalogue_serving_role_readiness_report()",
        "DROP TABLE IF EXISTS ops.dish_component_compatibility_proposals",
        "DROP TABLE IF EXISTS food.dish_component_compatibility",
        "DROP FUNCTION IF EXISTS ops.validate_component_proposal_application()",
        "DROP FUNCTION IF EXISTS ops.protect_component_proposal_lifecycle()",
        "DROP FUNCTION IF EXISTS food.protect_dish_component_compatibility()",
        "DROP FUNCTION IF EXISTS food.validate_dish_component_grammar()",
        "DROP FUNCTION IF EXISTS re_engine.canonical_meal_slot(text)",
    ):
        assert statement in rollback
    assert "DROP TABLE IF EXISTS public.dishes" not in rollback
    assert "DROP TABLE IF EXISTS public.dish_meal_class_mappings" not in rollback


def test_component_audit_workflow_is_protected_atomic_and_keeps_aux_off():
    """Production measurement installs atomically and cannot deploy or route either RE service."""
    text = COMPONENT_WORKFLOW.read_text()

    assert "environment: production" in text
    assert "github.ref == 'refs/heads/main'" in text
    assert "database_identifies_project" in text
    assert "unsafe partial component compatibility state" in text
    assert "action=extend_coverage" in text
    assert "107_complete_serving_role_readiness_coverage.sql" in text
    assert "959_complete_serving_role_readiness_coverage_validation.sql" in text
    assert "pg_advisory_xact_lock" in text
    assert "--single-transaction" in text
    assert "SET TRANSACTION READ ONLY" in text
    assert "recommendation-component-compatibility-report.json" in text
    assert "AUX_RE_MODE" not in text
    assert "fly deploy" not in text


def test_complete_serving_role_report_reconciles_every_active_dish_and_slot():
    """Expanded dishes without meal slots must remain visible in the readiness denominator."""
    migration = COMPLETE_COMPONENT_MIGRATION.read_text()
    validation = COMPLETE_COMPONENT_VALIDATION.read_text()

    assert "catalogue_serving_role_readiness_report_v2" in migration
    assert "active_dishes_without_canonical_slot" in migration
    assert "missing_canonical_meal_slot" in migration
    assert "active_dishes_with_unrecognized_slot" in migration
    assert "'all_active_dishes_reconciled', true" in migration
    assert "'publication_gate_changed', false" in migration
    for invariant in (
        "canonical-slot dish coverage does not reconcile",
        "complete catalogue dish routes do not reconcile",
        "complete catalogue hero roles do not reconcile",
        "complete catalogue slot routes do not reconcile",
    ):
        assert invariant in validation


def test_complete_serving_role_report_is_additive_private_and_reversible():
    """Coverage correction preserves v1 evidence and cannot expose identities or alter serving."""
    migration = COMPLETE_COMPONENT_MIGRATION.read_text()
    rollback = COMPLETE_COMPONENT_ROLLBACK.read_text()

    assert "SECURITY DEFINER" in migration
    assert "FROM PUBLIC, anon, authenticated" in migration
    assert "UPDATE public." not in migration
    assert "INSERT INTO public." not in migration
    assert "DROP FUNCTION IF EXISTS re_engine.catalogue_serving_role_readiness_report_v2()" in rollback
    assert "catalogue_serving_role_readiness_report()" not in rollback


def test_meal_slot_remediation_uses_fixed_aggregate_source_evidence_only():
    """Raw import courses may guide non-serving proposals but must never leave the DB."""
    text = MEAL_SLOT_MIGRATION.read_text()

    assert "catalogue_meal_slot_remediation_report" in text
    assert "public.import_row_results" in text
    assert "public.dish_source_rows" in text
    assert "single_direct_slot_proposal" in text
    assert "contextual_course_review" in text
    assert "conflicting_direct_slot_evidence" in text
    assert "'raw_source_text_exposed', false" in text
    assert "'fixed_evidence_categories_only', true" in text
    assert "'direct_slot_proposal_is_non_serving', true" in text
    assert "UPDATE public." not in text
    assert "INSERT INTO public." not in text


def test_meal_slot_remediation_reconciles_and_rolls_back_without_touching_v2():
    """Every slotless dish has one route and every direct proposal has one canonical slot."""
    validation = MEAL_SLOT_VALIDATION.read_text()
    rollback = MEAL_SLOT_ROLLBACK.read_text()

    for invariant in (
        "catalogue current slot states do not reconcile",
        "catalogue meal-slot remediation routes do not reconcile",
        "catalogue direct meal-slot proposals do not reconcile",
    ):
        assert invariant in validation
    assert "DROP FUNCTION IF EXISTS re_engine.catalogue_meal_slot_remediation_report()" in rollback
    assert "catalogue_serving_role_readiness_report_v2" not in rollback


def test_meal_slot_audit_is_protected_read_only_and_keeps_aux_untouched():
    """The evidence run may install one report but cannot create proposals or route traffic."""
    text = MEAL_SLOT_WORKFLOW.read_text()

    assert "environment: production" in text
    assert "github.ref == 'refs/heads/main'" in text
    assert "database_identifies_project" in text
    assert "catalogue_serving_role_readiness_report_v2" in text
    assert "pg_advisory_xact_lock" in text
    assert "--single-transaction" in text
    assert "SET TRANSACTION READ ONLY" in text
    assert "recommendation-meal-slot-remediation-report.json" in text
    assert "AUX_RE_MODE" not in text
    assert "fly deploy" not in text


def test_direct_meal_slot_proposals_are_evidence_linked_pending_and_non_serving():
    """Exact course evidence may create a proposal but cannot mutate serving truth."""
    text = MEAL_SLOT_PROPOSAL_MIGRATION.read_text()

    assert "ops.dish_meal_slot_proposals" in text
    assert "ops.dish_meal_slot_proposal_evidence" in text
    assert "DEFERRABLE INITIALLY DEFERRED" in text
    assert "meal-slot proposal requires at least one direct evidence row" in text
    assert "meal-slot proposal identity and evidence are immutable" in text
    assert "invalid meal-slot proposal lifecycle transition" in text
    assert "automatic_acceptance_allowed', false" in text
    assert "serving_changed', false" in text
    assert "publication_changed', false" in text
    assert "UPDATE public.dishes" not in text
    assert "INSERT INTO public.dish_meal_class_mappings" not in text


def test_direct_proposal_generator_is_idempotent_count_bound_and_service_only():
    """Generation must stop on drift and reruns must reuse the exact proposal version."""
    migration = MEAL_SLOT_PROPOSAL_MIGRATION.read_text()
    validation = MEAL_SLOT_PROPOSAL_VALIDATION.read_text()

    assert "direct meal-slot candidate count drift" in migration
    assert "ON CONFLICT (dish_id, proposed_slot, proposal_method, proposal_version) DO NOTHING" in migration
    assert "materialized meal-slot proposals do not match candidate count" in migration
    assert "FROM PUBLIC, anon, authenticated" in migration
    for invariant in (
        "governed meal-slot proposal tables must enforce RLS",
        "governed meal-slot proposals must remain service-only",
        "direct proposal table writes must remain function-gated",
        "governed meal-slot proposal is missing evidence",
        "governed meal-slot proposal evidence does not match dish and slot",
        "governed meal-slot proposal review provenance is incomplete",
    ):
        assert invariant in validation


def test_direct_proposal_rollback_preserves_evidence_and_disables_generation():
    """Rollback must retain generated review records while removing further mutation paths."""
    text = MEAL_SLOT_PROPOSAL_ROLLBACK.read_text()

    assert "REVOKE INSERT, UPDATE ON ops.dish_meal_slot_proposals" in text
    assert "REVOKE EXECUTE ON FUNCTION re_engine.direct_slot_from_import_course" in text
    assert "DROP FUNCTION IF EXISTS ops.generate_direct_meal_slot_proposals" in text
    assert "DROP FUNCTION IF EXISTS re_engine.direct_slot_from_import_course" not in text
    assert "DROP TABLE" not in text


def test_direct_proposal_workflow_is_protected_exact_count_and_aux_free():
    """Only the audited direct count may become pending proposals; no serving system is touched."""
    text = MEAL_SLOT_PROPOSAL_WORKFLOW.read_text()

    assert "environment: production" in text
    assert "github.ref == 'refs/heads/main'" in text
    assert "expected_candidate_count" in text
    assert "catalogue_meal_slot_remediation_report" in text
    assert "pg_advisory_xact_lock" in text
    assert "--single-transaction" in text
    assert "pending_review" in text
    assert "recommendation-meal-slot-proposal-generation.json" in text
    assert "AUX_RE_MODE" not in text
    assert "fly deploy" not in text


def test_direct_proposal_review_report_is_bounded_read_only_and_user_free():
    """The review pack may show catalogue names but no raw import or user information."""
    migration = MEAL_SLOT_REVIEW_MIGRATION.read_text()
    validation = MEAL_SLOT_REVIEW_VALIDATION.read_text()

    assert "p_sample_per_slot > 25" in migration
    assert "md5(p.dish_id::text || ':meal-slot-proposal-v1')" in migration
    assert "'dish_name', s.dish_name" in migration
    assert "'catalogue_names_exposed_for_review', true" in migration
    assert "'user_data_exposed', false" in migration
    assert "'raw_source_text_exposed', false" in migration
    assert "'automatic_acceptance_allowed', false" in migration
    assert "UPDATE public." not in migration
    assert "INSERT INTO public." not in migration
    for invariant in (
        "direct meal-slot proposal review report must remain service-only",
        "direct meal-slot proposal review counts do not reconcile",
        "direct meal-slot proposal review evidence does not reconcile",
        "direct meal-slot proposal review sample exceeds its bound",
        "direct meal-slot proposal review sample exposes an unapproved field",
    ):
        assert invariant in validation


def test_direct_proposal_review_report_has_exact_rollback():
    """Review-report rollback removes only the report and preserves proposal evidence."""
    text = MEAL_SLOT_REVIEW_ROLLBACK.read_text()

    assert "DROP FUNCTION IF EXISTS re_engine.direct_meal_slot_proposal_review_report" in text
    assert "DROP TABLE" not in text
    assert "ops.dish_meal_slot_proposals" not in text


def test_direct_proposal_review_workflow_is_read_only_bounded_and_aux_free():
    """The protected review run cannot approve, apply, publish or deploy anything."""
    text = MEAL_SLOT_REVIEW_WORKFLOW.read_text()

    assert "environment: production" in text
    assert "github.ref == 'refs/heads/main'" in text
    assert "database_identifies_project" in text
    assert "expected_proposal_count" in text
    assert "expected_evidence_link_count" in text
    assert "sample_per_slot" in text
    assert "SET TRANSACTION READ ONLY" in text
    assert "recommendation-meal-slot-proposal-review.json" in text
    assert "catalogue_names_exposed_for_review" in text
    assert "automatic_acceptance_allowed == false" in text
    assert "AUX_RE_MODE" not in text
    assert "fly deploy" not in text


def test_direct_proposal_provenance_distinguishes_applied_and_repeated_lineage():
    """Evidence-link multiplicity must not be represented as independent source proof."""
    text = MEAL_SLOT_PROVENANCE_MIGRATION.read_text()

    assert "direct_meal_slot_proposal_provenance_report" in text
    assert "public.import_runs" in text
    assert "r.run_mode = 'apply'" in text
    assert "r.run_mode = 'dry_run'" in text
    assert "s.row_fingerprint" in text
    assert "(r.source_name, r.source_checksum)" in text
    for route in (
        "no_applied_source_evidence",
        "repeated_same_logical_source_row",
        "multiple_rows_same_applied_source_file",
        "multiple_versions_same_source_name",
        "multiple_source_names_not_independence_proof",
    ):
        assert route in text
    assert "'evidence_link_is_independent_source_proof', false" in text
    assert "'automatic_confidence_upgrade_allowed', false" in text


def test_direct_proposal_provenance_is_aggregate_private_and_non_mutating():
    """The lineage audit may count source structure but cannot expose it or change facts."""
    migration = MEAL_SLOT_PROVENANCE_MIGRATION.read_text()
    validation = MEAL_SLOT_PROVENANCE_VALIDATION.read_text()

    assert "RETURNS jsonb" in migration
    assert "SECURITY DEFINER" in migration
    assert "FROM PUBLIC, anon, authenticated" in migration
    for policy in (
        "'identity_exposed', false",
        "'source_name_exposed', false",
        "'source_checksum_exposed', false",
        "'raw_source_text_exposed', false",
        "'proposal_changed', false",
        "'serving_changed', false",
        "'publication_changed', false",
    ):
        assert policy in migration
    for forbidden in (
        "UPDATE ops.dish_meal_slot_proposals",
        "INSERT INTO ops.dish_meal_slot_proposals",
        "UPDATE public.",
        "INSERT INTO public.",
        "raw_payload",
        "normalized_payload",
    ):
        assert forbidden not in migration
    for invariant in (
        "direct meal-slot proposal provenance report must remain service-only",
        "direct meal-slot proposal provenance routes do not reconcile",
        "direct meal-slot proposal provenance links do not reconcile",
        "direct meal-slot proposal provenance policy is invalid",
    ):
        assert invariant in validation


def test_direct_proposal_provenance_has_exact_non_destructive_rollback():
    """Rollback removes only the report and preserves proposals and source evidence."""
    text = MEAL_SLOT_PROVENANCE_ROLLBACK.read_text()

    assert (
        "DROP FUNCTION IF EXISTS re_engine.direct_meal_slot_proposal_provenance_report()"
        in text
    )
    assert "DROP TABLE" not in text
    assert "ops.dish_meal_slot_proposals" not in text
    assert "public.dish_source_rows" not in text


def test_direct_proposal_provenance_workflow_is_read_only_count_bound_and_aux_free():
    """The protected production audit must reconcile exact evidence without routing traffic."""
    text = MEAL_SLOT_PROVENANCE_WORKFLOW.read_text()

    assert "environment: production" in text
    assert "github.ref == 'refs/heads/main'" in text
    assert "database_identifies_project" in text
    assert "expected_proposal_count" in text
    assert "expected_evidence_link_count" in text
    assert "pg_advisory_xact_lock" in text
    assert "--single-transaction" in text
    assert "SET TRANSACTION READ ONLY" in text
    assert "recommendation-meal-slot-proposal-provenance.json" in text
    assert "evidence_link_is_independent_source_proof == false" in text
    assert "automatic_confidence_upgrade_allowed == false" in text
    assert "AUX_RE_MODE" not in text
    assert "fly deploy" not in text


def test_direct_proposal_source_integrity_checks_exact_source_and_completed_apply():
    """Every accepted source link must match the runtime source and a completed apply run."""
    text = MEAL_SLOT_SOURCE_INTEGRITY_MIGRATION.read_text()

    assert "direct_meal_slot_proposal_source_integrity_report" in text
    assert "p_expected_source_name" in text
    assert "p_expected_source_checksum" in text
    assert "r.run_mode = 'apply'" in text
    assert "r.status = 'completed'" in text
    for route in (
        "no_evidence",
        "missing_import_lineage",
        "unexpected_source_identity",
        "expected_source_non_apply",
        "expected_source_incomplete_run",
        "expected_completed_apply_only",
    ):
        assert route in text
    assert "'source_integrity_gate_is_approval', false" in text
    assert "'automatic_acceptance_allowed', false" in text


def test_direct_proposal_source_integrity_is_private_aggregate_and_non_mutating():
    """The exact source may be compared in memory but cannot be exposed or change facts."""
    migration = MEAL_SLOT_SOURCE_INTEGRITY_MIGRATION.read_text()
    validation = MEAL_SLOT_SOURCE_INTEGRITY_VALIDATION.read_text()

    assert "SECURITY DEFINER" in migration
    assert "FROM PUBLIC, anon, authenticated" in migration
    for policy in (
        "'identity_exposed', false",
        "'expected_source_name_exposed', false",
        "'expected_source_checksum_exposed', false",
        "'raw_source_text_exposed', false",
        "'proposal_changed', false",
        "'serving_changed', false",
        "'publication_changed', false",
    ):
        assert policy in migration
    for forbidden in (
        "UPDATE ops.dish_meal_slot_proposals",
        "INSERT INTO ops.dish_meal_slot_proposals",
        "UPDATE public.",
        "INSERT INTO public.",
        "raw_payload",
        "normalized_payload",
    ):
        assert forbidden not in migration
    for invariant in (
        "direct meal-slot proposal source-integrity report must remain service-only",
        "direct meal-slot proposal source-integrity routes do not reconcile",
        "direct meal-slot proposal source-integrity links do not reconcile",
        "direct meal-slot proposal source-integrity policy is invalid",
    ):
        assert invariant in validation


def test_direct_proposal_source_integrity_has_exact_non_destructive_rollback():
    """Rollback removes only the audit function and preserves all proposal lineage."""
    text = MEAL_SLOT_SOURCE_INTEGRITY_ROLLBACK.read_text()

    assert "direct_meal_slot_proposal_source_integrity_report(text, text)" in text
    assert "DROP TABLE" not in text
    assert "ops.dish_meal_slot_proposals" not in text
    assert "public.dish_source_rows" not in text


def test_direct_proposal_source_integrity_workflow_hashes_checked_in_source_only():
    """The protected audit derives source identity from Git and never routes Aux traffic."""
    text = MEAL_SLOT_SOURCE_INTEGRITY_WORKFLOW.read_text()

    assert "environment: production" in text
    assert "github.ref == 'refs/heads/main'" in text
    assert "database_identifies_project" in text
    assert "database/seeds/IndianFoodDatasetCSV.csv" in text
    assert "sha256sum -- \"$source_path\"" in text
    assert "\\getenv expected_source_name EXPECTED_SOURCE_NAME" in text
    assert "\\getenv expected_source_checksum EXPECTED_SOURCE_CHECKSUM" in text
    assert '-v expected_source_name="$expected_source_name"' not in text
    assert "expected_proposal_count" in text
    assert "expected_evidence_link_count" in text
    assert "pg_advisory_xact_lock" in text
    assert "--single-transaction" in text
    assert "SET TRANSACTION READ ONLY" in text
    assert "recommendation-meal-slot-proposal-source-integrity.json" in text
    assert "expected_source_name_exposed == false" in text
    assert "automatic_acceptance_allowed == false" in text
    assert "AUX_RE_MODE" not in text
    assert "fly deploy" not in text
