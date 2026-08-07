from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

import pytest

from ops.recommendation import user_audit

PROFILE_ID = UUID("621a406a-1778-4951-b1a2-8e05c09449c8")


class FakeCursor:
    def __init__(self, value):
        self.value = value
        self.params = None

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def execute(self, _query, params):
        self.params = params

    def fetchone(self):
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
    assert connection.cursor_value.params == (str(PROFILE_ID),)
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


def test_user_audit_fails_closed_for_missing_profile():
    with pytest.raises(RuntimeError, match="Profile does not exist"):
        user_audit.fetch_user_audit(FakeConnection({"profile": None}), PROFILE_ID)


def test_audit_writer_uses_private_permissions(tmp_path):
    output = tmp_path / "audit.json"
    user_audit.write_audit(output, {"profile": {"home_state": "MP"}})
    assert output.stat().st_mode & 0o777 == 0o600
    assert '"home_state": "MP"' in output.read_text()
