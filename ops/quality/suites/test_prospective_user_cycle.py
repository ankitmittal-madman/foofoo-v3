import json
from io import BytesIO
from urllib.error import HTTPError
from uuid import UUID

import pytest

from ops.recommendation import prospective_user_cycle as cycle

PROFILE_ID = UUID("621a406a-1778-4951-b1a2-8e05c09449c8")


class Response:
    def __init__(self, body):
        self.body = json.dumps(body).encode()

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def read(self):
        return BytesIO(self.body).read()


def test_authentication_fails_before_returning_token_for_wrong_profile():
    def opener(_request, timeout):
        assert timeout == 45
        return Response({"user": {"id": str(UUID(int=1))}, "access_token": "secret"})

    with pytest.raises(RuntimeError, match="does not belong"):
        cycle.authenticate(
            "https://example.test", "anon", "user@example.test", "pw", PROFILE_ID, opener=opener
        )


def test_refresh_cycle_reports_aggregate_change_without_dish_names_or_tokens():
    calls = []

    def opener(request, timeout):
        assert timeout == 45
        payload = json.loads(request.data)
        calls.append(payload)
        slot = payload["slot"]
        generation = payload["refresh_generation"]
        return Response(
            {
                "slate_id": f"slate-{slot}-{generation}",
                "episodes": [
                    {"episode_hash": f"{slot}-{generation}-{index}", "display_name": f"Dish {index}"}
                    for index in range(4)
                ],
            }
        )

    report = cycle.run_refresh_cycle("https://example.test", "anon", "token", opener=opener)
    serialized = json.dumps(report)
    assert len(calls) == 6
    assert all(result["set_changed"] for result in report["slots"].values())
    assert "Dish" not in serialized
    assert "token" not in serialized


def test_episode_validation_requires_unique_modern_slate_lineage():
    with pytest.raises(RuntimeError, match="duplicate"):
        cycle.episode_identities(
            {"slate_id": "one", "episodes": [{"episode_hash": "same"}, {"episode_hash": "same"}]}
        )
    with pytest.raises(RuntimeError, match="lineage"):
        cycle.episode_identities({"episodes": [{"episode_hash": "one"}]})


def test_report_writer_is_private(tmp_path):
    path = tmp_path / "report.json"
    cycle.write_report(path, {"identity_verified": True})
    assert path.stat().st_mode & 0o777 == 0o600


def test_http_error_diagnostics_only_admit_bounded_machine_codes():
    safe = HTTPError("https://example.test", 400, "bad", {}, BytesIO(b'{"code":"invalid_credentials","message":"secret detail"}'))
    unsafe = HTTPError("https://example.test", 400, "bad", {}, BytesIO(b'{"code":"bad code: leaked"}'))
    assert cycle.safe_http_error_code(safe) == "invalid_credentials"
    assert cycle.safe_http_error_code(unsafe) is None
