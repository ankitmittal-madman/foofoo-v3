from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from uuid import UUID

import pytest

from ops.recommendation import user_audit

RECOVERY_MIGRATION = Path("database/migrations/113_measure_preference_attribution_recovery.sql")
RECOVERY_VALIDATION = Path(
    "database/validation/965_measure_preference_attribution_recovery_validation.sql"
)
RECOVERY_ROLLBACK = Path(
    "database/rollback/113_measure_preference_attribution_recovery_rollback.sql"
)
RECOVERY_WORKFLOW = Path(
    ".github/workflows/recommendation-preference-attribution-recovery-audit.yml"
)
FRESH_ATTRIBUTION_MIGRATION = Path(
    "database/migrations/117_measure_fresh_preference_attribution.sql"
)
FRESH_ATTRIBUTION_VALIDATION = Path(
    "database/validation/969_measure_fresh_preference_attribution_validation.sql"
)
FRESH_ATTRIBUTION_ROLLBACK = Path(
    "database/rollback/117_measure_fresh_preference_attribution_rollback.sql"
)
FRESH_ATTRIBUTION_WORKFLOW = Path(".github/workflows/recommendation-fresh-attribution-slo.yml")
FRESH_ATTRIBUTION_SCOPE_MIGRATION = Path(
    "database/migrations/119_scope_fresh_preference_attribution.sql"
)
FRESH_ATTRIBUTION_SCOPE_VALIDATION = Path(
    "database/validation/971_scope_fresh_preference_attribution_validation.sql"
)
FRESH_ATTRIBUTION_SCOPE_ROLLBACK = Path(
    "database/rollback/119_scope_fresh_preference_attribution_rollback.sql"
)

PROFILE_ID = UUID("621a406a-1778-4951-b1a2-8e05c09449c8")


class FakeCursor:
    def __init__(self, value):
        self.value = value
        self.params = []
        self.fetch_count = 0

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def execute(self, _query, params):
        self.params.append(params)

    def fetchone(self):
        self.fetch_count += 1
        if self.fetch_count == 1:
            return {"current_city": "Mumbai"}
        return {"user_audit": self.value}


class FakeConnection:
    def __init__(self, value):
        self.cursor_value = FakeCursor(value)

    def cursor(self):
        return self.cursor_value


def test_user_audit_is_parameterized_and_json_safe():
    connection = FakeConnection(
        {
            "profile": {"home_state": "MP"},
            "score": Decimal("0.625"),
            "updated_at": datetime(2026, 8, 6, tzinfo=UTC),
        }
    )
    result = user_audit.fetch_user_audit(connection, PROFILE_ID)
    assert connection.cursor_value.params == [
        (str(PROFILE_ID),),
        ("Maharashtra", str(PROFILE_ID)),
    ]
    assert result["score"] == 0.625
    assert result["updated_at"] == "2026-08-06T00:00:00+00:00"


def test_user_audit_counts_json_dimensions_with_postgres_supported_function():
    assert "jsonb_object_length" not in user_audit.AUDIT_SQL
    assert user_audit.AUDIT_SQL.count("jsonb_object_keys") == 3
    assert "tag_affinity_dimensions" in user_audit.AUDIT_SQL


def test_user_audit_only_counts_training_grade_point_in_time_attribution():
    sql = user_audit.AUDIT_SQL
    assert "usable_feature_snapshots" in sql
    assert "jsonb_typeof(fs.values->'household') = 'object'" in sql
    assert "fs.values->'household' <> '{}'::jsonb" in sql
    assert "JOIN public.outcome_events o ON o.idempotency_key = f.id" in sql
    assert "JOIN public.slate_items i ON i.slate_id = s.id" in sql
    assert "JOIN public.dishes d ON d.id = f.dish_id" in sql
    assert "exact_attribution_coverage" in sql
    assert "'not_today','swap','edit'" not in sql


def test_user_audit_reports_private_persisted_variety_state():
    assert "FROM public.variety_window_state" not in user_audit.AUDIT_SQL
    assert "FROM re_engine.variety_window_state" in user_audit.AUDIT_SQL
    assert "'status', 'not_implemented'" not in user_audit.AUDIT_SQL
    assert "recent_dish_dimensions" in user_audit.AUDIT_SQL


def test_user_audit_measures_refreshes_with_legacy_and_episode_identities():
    sql = user_audit.AUDIT_SQL
    assert "recent_refresh_events" in sql
    assert "nullif(plate->>'episode_hash', '')" in sql
    assert "nullif(plate->>'display_name', '')" in sql
    assert "nullif(plate->>'name', '')" in sql
    assert "PARTITION BY slot ORDER BY created_at" in sql
    assert "meaningful_refresh_rate" in sql
    assert "'refresh_quality'" in sql


def test_user_audit_measures_served_regional_naming_and_richness_quality():
    sql = user_audit.AUDIT_SQL
    assert sql.count("%s") == 2
    assert "recent_served_components" in sql
    assert "public.dish_regional_affinities" in sql
    assert "home.review_status <> 'rejected'" in sql
    assert "local.review_status <> 'rejected'" in sql
    assert "home_or_local_affinity_count" in sql
    assert "regional_affinity_coverage" in sql
    assert "canonical_name_match_count" in sql
    assert "canonical_name_mismatch_count" in sql
    assert "above_neutral_richness_rate" in sql
    assert "richness_score > 0.5" in sql
    assert "'served_catalogue_quality'" in sql
    assert "'served_richness'" in sql


def test_user_audit_emits_aggregate_recommendation_evidence_not_raw_plates():
    sql = user_audit.AUDIT_SQL
    assert "'recent_recommendation_summary'" in sql
    assert "'recent_recommendations'" not in sql
    assert "jsonb_agg(to_jsonb(recent_recs)" not in sql
    assert "served_success_count" in sql
    assert "reported_plate_count" in sql


def test_user_audit_fails_closed_for_missing_profile():
    with pytest.raises(RuntimeError, match="Profile does not exist"):
        user_audit.fetch_user_audit(FakeConnection({"profile": None}), PROFILE_ID)


def test_audit_writer_uses_private_permissions(tmp_path):
    output = tmp_path / "audit.json"
    user_audit.write_audit(output, {"profile": {"home_state": "MP"}})
    assert output.stat().st_mode & 0o777 == 0o600
    assert '"home_state": "MP"' in output.read_text()


def test_preference_recovery_report_requires_exact_point_in_time_evidence():
    text = RECOVERY_MIGRATION.read_text()

    assert "preference_attribution_recovery_report" in text
    assert "SECURITY DEFINER" in text
    assert "jsonb_typeof(fs.values->'household') = 'object'" in text
    assert "fs.values->'household' <> '{}'::jsonb" in text
    assert "count(*)::integer AS match_count" in text
    assert "WHEN match_count > 1 THEN 'ambiguous_served_item_match'" in text
    assert "unique_served_item_required', true" in text
    assert "automatic_recovery_allowed', false" in text
    for mutation in ("INSERT INTO", "UPDATE public", "DELETE FROM"):
        assert mutation not in text


def test_preference_recovery_report_is_private_reconciled_and_reversible():
    migration = RECOVERY_MIGRATION.read_text()
    validation = RECOVERY_VALIDATION.read_text()
    rollback = RECOVERY_ROLLBACK.read_text()

    assert "FROM PUBLIC, anon, authenticated" in migration
    assert "TO service_role" in migration
    assert "routes do not reconcile" in validation
    assert "outcome counts do not reconcile" in validation
    assert "DROP FUNCTION IF EXISTS ml.preference_attribution_recovery_report()" in rollback
    assert "feedback_events" not in rollback
    assert "outcome_events" not in rollback


def test_preference_recovery_workflow_is_protected_and_read_only_after_install():
    text = RECOVERY_WORKFLOW.read_text()

    assert "environment: production" in text
    assert "github.ref == 'refs/heads/main'" in text
    assert "database_identifies_project" in text
    assert "pg_advisory_xact_lock" in text
    assert "--single-transaction" in text
    assert "SET TRANSACTION READ ONLY" in text
    assert "recommendation-preference-attribution-recovery.json" in text
    assert "automatic_recovery_allowed == false" in text
    assert "AUX_RE_MODE" not in text
    assert "fly deploy" not in text


def test_fresh_attribution_slo_requires_exact_recent_serving_evidence():
    """New feedback is healthy only when one exact served episode owns its outcome."""
    text = FRESH_ATTRIBUTION_MIGRATION.read_text()

    assert "fresh_preference_attribution_report" in text
    assert "f.created_at >= p_since" in text
    assert "interval '90 days'" in text
    assert "jsonb_typeof(fs.values->'household') = 'object'" in text
    assert "o.idempotency_key = l.id" in text
    assert "si.episode_hash = o.episode_hash" in text
    for route in (
        "missing_canonical_identity",
        "missing_recommendation_event",
        "missing_slate",
        "missing_point_in_time_run",
        "missing_outcome",
        "mismatched_outcome_slate",
        "missing_episode_identity",
        "no_served_item_match",
        "ambiguous_served_item_match",
        "exact",
    ):
        assert route in text
    assert "'minimum_sample_size', 20" in text
    assert "'target_exact_attribution_rate', 0.9500" in text
    for mutation in ("INSERT INTO", "UPDATE public", "DELETE FROM"):
        assert mutation not in text


def test_fresh_attribution_slo_is_private_reconciled_and_reversible():
    """The SLO exposes aggregates only and can be removed without touching evidence."""
    migration = FRESH_ATTRIBUTION_MIGRATION.read_text()
    validation = FRESH_ATTRIBUTION_VALIDATION.read_text()
    rollback = FRESH_ATTRIBUTION_ROLLBACK.read_text()

    assert "FROM PUBLIC, anon, authenticated" in migration
    assert "TO service_role" in migration
    assert "routes do not reconcile" in validation
    assert "counts do not reconcile" in validation
    assert "SLO contract is invalid" in validation
    assert "fresh_preference_attribution_report(timestamptz)" in rollback
    assert "feedback_events" not in rollback
    assert "outcome_events" not in rollback


def test_fresh_attribution_workflow_is_bounded_protected_and_actionable():
    """Production monitoring installs safely, emits counts only and fails a mature bad sample."""
    text = FRESH_ATTRIBUTION_WORKFLOW.read_text()

    assert "environment: production" in text
    assert "github.ref == 'refs/heads/main'" in text
    assert "database_identifies_project" in text
    assert 'case "$WINDOW_HOURS" in 24|168|720)' in text
    assert "pg_advisory_xact_lock" in text
    assert "--single-transaction" in text
    assert "119_scope_fresh_preference_attribution.sql" in text
    assert "971_scope_fresh_preference_attribution_validation.sql" in text
    assert "SET TRANSACTION READ ONLY" in text
    assert "recommendation-fresh-attribution-slo.json" in text
    assert 'test "$status" != "fail"' in text
    assert "policy.identity_exposed == false" in text
    assert "policy.training_changed == false" in text
    assert "AUX_RE_MODE" not in text
    assert "fly deploy" not in text


def test_fresh_attribution_v2_is_cutover_aware_and_dish_scoped():
    """Legacy and meal-class evidence cannot pollute the repaired dish writer's SLO."""
    migration = FRESH_ATTRIBUTION_SCOPE_MIGRATION.read_text()
    validation = FRESH_ATTRIBUTION_SCOPE_VALIDATION.read_text()
    rollback = FRESH_ATTRIBUTION_SCOPE_ROLLBACK.read_text()

    assert "preference_attribution_slo_control" in migration
    assert "v_effective_since := greatest(p_since, v_monitoring_started_at)" in migration
    assert "f.target_type = 'dish'" in migration
    assert "excluded_non_dish_event_count" in migration
    assert "'cutover_aware', true" in migration
    assert "'dish_preference_targets_only', true" in migration
    assert "fresh-preference-attribution-v2" in validation
    assert "application roles" in validation
    assert "DROP TABLE IF EXISTS ml.preference_attribution_slo_control" in rollback
    for mutation in ("UPDATE public.feedback_events", "DELETE FROM", "TRUNCATE"):
        assert mutation not in migration
