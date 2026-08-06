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


def test_user_audit_fails_closed_for_missing_profile():
    with pytest.raises(RuntimeError, match="Profile does not exist"):
        user_audit.fetch_user_audit(FakeConnection({"profile": None}), PROFILE_ID)


def test_audit_writer_uses_private_permissions(tmp_path):
    output = tmp_path / "audit.json"
    user_audit.write_audit(output, {"profile": {"home_state": "MP"}})
    assert output.stat().st_mode & 0o777 == 0o600
    assert '"home_state": "MP"' in output.read_text()
