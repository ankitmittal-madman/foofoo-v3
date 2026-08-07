import json
import sqlite3
from pathlib import Path

import pytest

from ops.recommendation import catalogue_publication as publication


class FakeCursor:
    def __init__(self, connection):
        self.connection = connection
        self.query = ""
        self.params = ()
        self.description = None

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def execute(self, query, params=None):
        self.query = query
        self.params = params or ()

    def fetchone(self):
        return self.connection.coverage

    def fetchall(self):
        after, limit = self.params
        rows = [row for row in self.connection.rows if after is None or row["id"] > after][:limit]
        return [{"publication_row": row} for row in rows]


class FakeConnection:
    def __init__(self, rows, publishable=None):
        self.rows = rows
        count = len(rows) if publishable is None else publishable
        self.coverage = {
            "active_dishes": count,
            "enriched_dishes": count,
            "safety_closed_dishes": count,
            "class_mapped_dishes": count,
            "publishable_dishes": count,
        }

    def cursor(self):
        return FakeCursor(self)


def row(dish_id: str, name: str) -> dict:
    return {
        "schema_version": publication.ROW_SCHEMA_VERSION,
        "id": dish_id,
        "name": name,
        "ingredients": [{"name": "example"}],
        "meal_slots": ["lunch"],
        "meal_classes": [{"class_code": "example"}],
    }


def test_database_url_fails_closed_without_an_explicit_production_read_target():
    assert publication.database_url({"DATABASE_URL": "postgres://example"}) == "postgres://example"
    with pytest.raises(RuntimeError, match="No production database"):
        publication.database_url({})


def test_publication_streams_bounded_pages_and_writes_content_addressed_manifest(tmp_path):
    rows = [row("0001", "Poha"), row("0002", "Idli"), row("0003", "Dosa")]
    target = tmp_path / "publication"

    manifest = publication.publish(FakeConnection(rows), target, page_size=2)

    exported = [json.loads(line) for line in (target / "catalogue.jsonl").read_text().splitlines()]
    assert exported == rows
    assert manifest["row_count"] == 3
    assert manifest["publication_version"].startswith("sha256:")
    assert manifest["catalogue_sqlite_sha256"]
    assert json.loads((target / "manifest.json").read_text()) == manifest
    with sqlite3.connect(target / "catalogue.sqlite3") as index:
        assert index.execute("SELECT dish_id, name FROM catalogue ORDER BY dish_id").fetchall() == [
            ("0001", "Poha"),
            ("0002", "Idli"),
            ("0003", "Dosa"),
        ]
        assert index.execute("SELECT count(*) FROM dish_slots WHERE slot='lunch'").fetchone() == (
            3,
        )


def test_publication_refuses_count_drift_and_leaves_no_partial_target(tmp_path):
    target = tmp_path / "publication"
    with pytest.raises(RuntimeError, match="count mismatch"):
        publication.publish(FakeConnection([row("0001", "Poha")], publishable=2), target)
    assert not target.exists()


def test_publication_refuses_existing_target_and_invalid_page_size(tmp_path):
    target = tmp_path / "publication"
    target.mkdir()
    with pytest.raises(FileExistsError):
        publication.publish(FakeConnection([row("0001", "Poha")]), target)
    with pytest.raises(ValueError, match="page_size"):
        list(publication.iter_publication_rows(FakeConnection([]), page_size=0))


def test_sql_boundary_is_service_only_and_does_not_reference_user_tables():
    sql = Path("database/migrations/097_publish_scalable_recommendation_catalogue.sql").read_text()
    assert "catalogue_publication_rows" in sql
    assert "FROM PUBLIC, anon, authenticated" in sql
    assert "feedback_events" not in sql
    assert "profiles" not in sql
    assert "households" not in sql
