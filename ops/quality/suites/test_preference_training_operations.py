from pathlib import Path

import pytest

from ops.recommendation import preference_training as operations


class FakeCursor:
    def __init__(self, readiness, exports=()):
        self.readiness = readiness
        self.exports = list(exports)
        self.description = None
        self.query = ""

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def execute(self, query, _params=None):
        self.query = query

    def fetchone(self):
        return self.readiness

    def __iter__(self):
        return iter((row,) for row in self.exports)


class FakeConnection:
    def __init__(self, readiness, exports=()):
        self.readiness = readiness
        self.exports = exports

    def cursor(self):
        return FakeCursor(self.readiness, self.exports)


def readiness(ready=False, events=271):
    return {
        "real_labeled_events": events,
        "positive_events": events - 12,
        "negative_events": 12,
        "distinct_households": 79,
        "identity_resolved_events": events,
        "attributed_to_slate_events": events if ready else 0,
        "identity_coverage": 1.0,
        "slate_attribution_coverage": 1.0 if ready else 0.0,
        "is_ready": ready,
    }


def test_database_url_accepts_existing_secret_aliases_and_fails_closed():
    assert operations.database_url({"FOOFOO_SUPABASE_URI": "postgres://example"}) == (
        "postgres://example"
    )
    with pytest.raises(RuntimeError, match="No production database"):
        operations.database_url({})


def test_not_ready_writes_aggregate_report_without_export_or_artifact(tmp_path, monkeypatch):
    monkeypatch.setattr(
        operations,
        "export_rows",
        lambda *_args, **_kwargs: pytest.fail("private rows must not export before readiness"),
    )
    report_path = tmp_path / "readiness.json"
    result = operations.run(
        FakeConnection(readiness()),
        readiness_out=report_path,
        artifact_out=tmp_path / "model.joblib",
        eval_out=tmp_path / "eval.json",
    )
    assert result["status"] == "not_ready"
    assert report_path.exists()
    assert not (tmp_path / "model.joblib").exists()


def test_ready_snapshot_trains_ephemerally_and_publishes_governed_result(tmp_path, monkeypatch):
    rows = [
        {
            "household": {},
            "ctx": {},
            "dish_name": "Poha",
            "event_type": "like",
            "data_source": "real",
            "household_id": "hh-1",
        }
    ]
    observed_export = None

    def fake_train(export_path, artifact_path, eval_path):
        nonlocal observed_export
        observed_export = Path(export_path)
        assert observed_export.exists()
        Path(artifact_path).write_bytes(b"candidate")
        Path(eval_path).write_text("{}")
        return {
            "promotion_gate": {"passed": True, "checks": {}},
            "artifact_metadata": {"model_version": "sha256:candidate"},
        }

    monkeypatch.setattr(operations, "train", fake_train)
    result = operations.run(
        FakeConnection(readiness(ready=True, events=1), rows),
        readiness_out=tmp_path / "readiness.json",
        artifact_out=tmp_path / "model.joblib",
        eval_out=tmp_path / "eval.json",
    )
    assert result["status"] == "candidate_passed"
    assert result["model_version"] == "sha256:candidate"
    assert observed_export is not None and not observed_export.exists()
