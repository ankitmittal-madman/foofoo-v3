from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path

import pytest

from database.etl.dish_ingestion import db as db_module
from database.etl.dish_ingestion import pipeline


class _FakeCursor:
    """Minimal cursor placeholder used by the pipeline lifecycle double."""


class _FakeDatabase:
    """Record import lifecycle calls without opening a database connection."""

    instances: list[_FakeDatabase] = []

    def __init__(self) -> None:
        self.started_actor: str | None = None
        self.completed = False
        self.completion_counters: dict | None = None
        self.failed_report: dict | None = None
        self.closed = False
        self.__class__.instances.append(self)

    @contextmanager
    def transaction(self):
        yield _FakeCursor()

    def load_cuisines(self, _cur) -> dict:
        return {}

    def load_meal_classes(self, _cur) -> list:
        return []

    def load_existing_dishes(self, _cur) -> list:
        return []

    def load_dish_ids_with_image(self, _cur) -> set:
        return set()

    def start_import_run(
        self, _cur, _source_name, _source_checksum, _run_mode, triggered_by
    ) -> str:
        self.started_actor = triggered_by
        return "run-1"

    def complete_import_run(self, _cur, _run_id, counters, _report) -> None:
        self.completed = True
        self.completion_counters = counters

    def fail_import_run(self, _cur, _run_id, summary_report) -> bool:
        self.failed_report = summary_report
        return True

    def close(self) -> None:
        self.closed = True


def _prepare_pipeline(monkeypatch: pytest.MonkeyPatch) -> None:
    """Replace external adapters and database access with deterministic lifecycle doubles."""
    _FakeDatabase.instances.clear()
    monkeypatch.setattr(db_module, "Database", _FakeDatabase)
    monkeypatch.setattr(pipeline, "_file_checksum", lambda _path: "a" * 64)
    monkeypatch.setattr(pipeline, "get_adapter", lambda _cuisines, _classes: object())
    monkeypatch.setattr(pipeline, "GroqAdapter", object)


def test_apply_run_closes_completed_and_records_workflow_actor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A successful apply run must become completed and close its connection."""
    _prepare_pipeline(monkeypatch)
    monkeypatch.setenv("FOOFOO_IMPORT_ACTOR", "github-actions:123:1")
    monkeypatch.setattr(pipeline, "load_and_normalize", lambda _path: iter(()))

    report = pipeline.run_pipeline(Path("source.csv"), dry_run=False)

    database = _FakeDatabase.instances[0]
    assert report["verified_against_live_db"] is True
    assert database.started_actor == "github-actions:123:1"
    assert database.completed is True
    assert database.completion_counters == {"total_rows": 0}
    assert database.failed_report is None
    assert database.closed is True


@pytest.mark.parametrize("failure", [RuntimeError("boom"), KeyboardInterrupt()])
def test_apply_run_closes_failed_on_error_or_interruption(
    monkeypatch: pytest.MonkeyPatch, failure: BaseException
) -> None:
    """Exceptions and cancellation-style interrupts must terminally fail their run lineage."""
    _prepare_pipeline(monkeypatch)

    def fail_rows(_path):
        raise failure
        yield  # pragma: no cover - preserves generator execution semantics

    monkeypatch.setattr(pipeline, "load_and_normalize", fail_rows)

    with pytest.raises(type(failure)):
        pipeline.run_pipeline(Path("source.csv"), dry_run=False)

    database = _FakeDatabase.instances[0]
    assert database.completed is False
    assert database.failed_report is not None
    assert database.failed_report["status"] == "failed"
    assert database.failed_report["failure_type"] == type(failure).__name__
    assert database.closed is True


def test_ingestion_workflow_is_serialized_identity_bound_and_has_cleanup_time() -> None:
    """Production ingestion must reject ambiguous targets and finish before the job hard timeout."""
    text = Path(".github/workflows/dish-image-generation.yml").read_text()

    assert "environment: production" in text
    assert "cancel-in-progress: false" in text
    assert "secrets.FOOFOO_SUPABASE_URI" in text
    assert "secrets.DATABASE_URL" not in text
    assert "secrets.SUPABASE_DB_URL" not in text
    assert "database_identifies_project" in text
    assert "FOOFOO_IMPORT_ACTOR: github-actions:" in text
    assert "timeout --signal=TERM --kill-after=30s 330m" in text
    assert "timeout-minutes: 340" in text
    assert "args=(database/etl/ingest_dish_dataset.py)" in text
    assert '${{ runner.temp }}/dish-ingestion-report.json' in text


def test_import_run_terminal_updates_are_forward_only_and_actor_linked() -> None:
    """The persistence layer must identify its actor and never rewrite terminal run states."""
    text = Path("database/etl/dish_ingestion/db.py").read_text()

    assert "status, triggered_by" in text
    assert "(source_name, source_checksum, run_mode, actor)" not in text
    assert text.count("AND status = 'running'") == 2
    assert "import run completion requires one running row" in text
