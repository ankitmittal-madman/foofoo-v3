import pytest

from ops.recommendation import catalogue_db_publish as db_publish
from ops.recommendation import catalogue_publication as publication


class FakeCursor:
    def __init__(self, connection):
        self.connection = connection
        self.query = ""
        self.params = ()
        self.description = None
        self._last_result = None

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def execute(self, query, params=None):
        self.query = query
        self.params = params or ()
        if "insert into public.catalogue_versions" in query:
            new_id = f"version-{len(self.connection.versions) + 1}"
            self.connection.versions.append(
                {
                    "id": new_id,
                    "publication_version": params[0],
                    "dish_count": params[1],
                    "generated_by": params[2],
                    "notes": params[3],
                }
            )
            self._last_result = (new_id,)
        elif "insert into public.catalogue_dishes" in query:
            version_id, dish_id, payload = params
            self.connection.dishes.append(
                {"version_id": version_id, "dish_id": dish_id, "payload": payload}
            )
        elif "select * from re_engine.catalogue_publication_coverage" in query:
            self._last_result = self.connection.coverage
        elif "select re_engine.catalogue_publication_rows" in query:
            after, limit = self.params
            rows = [r for r in self.connection.rows if after is None or r["id"] > after][:limit]
            self._batch = [{"publication_row": r} for r in rows]
        elif "select mode, active_version_id" in query:
            self._last_result = self.connection.rollout_state
        elif "update public.catalogue_rollout_state" in query:
            mode, active_version_id, updated_by = params
            self.connection.rollout_state = {
                "mode": mode,
                "active_version_id": active_version_id,
                "updated_at": "now",
                "updated_by": updated_by,
            }

    def fetchone(self):
        return self._last_result

    def fetchall(self):
        return getattr(self, "_batch", [])


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
        self.versions: list[dict] = []
        self.dishes: list[dict] = []
        self.rollout_state = {
            "mode": "OFF",
            "active_version_id": None,
            "updated_at": "t0",
            "updated_by": "migration_102_default",
        }
        self.committed = False

    def cursor(self):
        return FakeCursor(self)

    def commit(self):
        self.committed = True


def row(dish_id: str) -> dict:
    return {
        "schema_version": publication.ROW_SCHEMA_VERSION,
        "id": dish_id,
        "name": f"dish-{dish_id}",
        "ingredients": [],
        "meal_slots": ["lunch"],
        "meal_classes": [],
    }


def test_publish_to_db_creates_one_version_and_matching_dish_rows():
    conn = FakeConnection([row("1"), row("2"), row("3")])
    result = db_publish.publish_to_db(conn, generated_by="test-runner")
    assert result.dish_count == 3
    assert result.publication_version.startswith("sha256:")
    assert len(conn.versions) == 1
    assert len(conn.dishes) == 3
    assert conn.committed is True


def test_publish_to_db_refuses_when_nothing_is_publishable():
    conn = FakeConnection([], publishable=0)
    with pytest.raises(RuntimeError, match="No publishable dishes"):
        db_publish.publish_to_db(conn, generated_by="test-runner")
    assert conn.versions == []


def test_two_publishes_of_different_content_create_two_versions_not_a_mutation():
    conn = FakeConnection([row("1")])
    first = db_publish.publish_to_db(conn, generated_by="run-1")
    conn.rows.append(row("2"))
    conn.coverage["publishable_dishes"] = 2
    second = db_publish.publish_to_db(conn, generated_by="run-2")

    assert first.version_id != second.version_id
    assert first.publication_version != second.publication_version
    assert len(conn.versions) == 2
    # Every previously inserted version row is still present untouched (insert-only).
    assert conn.versions[0]["publication_version"] == first.publication_version


def test_rollout_state_defaults_to_off_and_publish_never_touches_it():
    conn = FakeConnection([row("1")])
    before = db_publish.read_rollout_state(conn)
    assert before["mode"] == "OFF"
    db_publish.publish_to_db(conn, generated_by="test-runner")
    after = db_publish.read_rollout_state(conn)
    assert after["mode"] == "OFF"
    assert after["active_version_id"] is None


def test_set_rollout_state_requires_active_version_id_off_the_off_mode():
    conn = FakeConnection([row("1")])
    with pytest.raises(ValueError, match="active_version_id is required"):
        db_publish.set_rollout_state(
            conn, mode="LIVE", active_version_id=None, updated_by="founder"
        )


def test_set_rollout_state_rejects_unknown_mode():
    conn = FakeConnection([row("1")])
    with pytest.raises(ValueError, match="invalid rollout mode"):
        db_publish.set_rollout_state(
            conn, mode="ON", active_version_id="v1", updated_by="founder"
        )


def test_set_rollout_state_can_move_to_shadow_with_explicit_version():
    conn = FakeConnection([row("1")])
    result = db_publish.publish_to_db(conn, generated_by="test-runner")
    db_publish.set_rollout_state(
        conn, mode="SHADOW", active_version_id=result.version_id, updated_by="founder"
    )
    state = db_publish.read_rollout_state(conn)
    assert state["mode"] == "SHADOW"
    assert state["active_version_id"] == result.version_id
