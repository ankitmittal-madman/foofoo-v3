import json

from ops.recommendation import catalogue_operational_report as report_mod
from ops.recommendation.catalogue_eligibility import REQUIRED_TAXONOMY_FIELDS

FULL_TAXONOMY = list(REQUIRED_TAXONOMY_FIELDS)


class FakeCursor:
    def __init__(self, connection):
        self.connection = connection
        self.params = ()
        self.query = ""
        self.description = None

    def __enter__(self):
        return self

    def __exit__(self, *_a):
        return None

    def execute(self, query, params=None):
        self.query = query
        self.params = params or ()

    def fetchall(self):
        if "from public.dishes d" in self.query:
            return self.connection.gap_rows
        return []

    def fetchone(self):
        if "catalogue_versions order by created_at" in self.query:
            return self.connection.latest_version
        if "select mode, active_version_id" in self.query:
            return self.connection.rollout_state
        return None


class FakeConnection:
    def __init__(self, gap_rows, latest_version=None, rollout_state=None):
        self.gap_rows = gap_rows
        self.latest_version = latest_version
        self.rollout_state = rollout_state or {
            "mode": "OFF",
            "active_version_id": None,
            "updated_at": "t",
            "updated_by": "system_default",
        }

    def cursor(self):
        return FakeCursor(self)


def gap_row(dish_id, **overrides):
    base = dict(
        dish_id=dish_id,
        is_active=True,
        ontology_status="enriched",
        diet_type="veg",
        is_jain=True,
        allergen_flags=0,
        cuisine_id="c1",
        has_ingredient_mapping=True,
        has_meal_class_mapping=True,
        has_meal_slot_mapping=True,
        taxonomy_fields=FULL_TAXONOMY,
    )
    base.update(overrides)
    return base


def test_operational_report_totals_and_reasons(tmp_path):
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps({"bundle_version": "sha256:deadbeef", "catalogue_sha256": "x"})
    )
    rows = [
        gap_row("1"),
        gap_row("2", is_active=False),
        gap_row("3", diet_type=None, cuisine_id=None),
    ]
    conn = FakeConnection(
        rows,
        latest_version={
            "id": "v1",
            "publication_version": "sha256:" + "a" * 64,
            "created_at": "2026-08-01T00:00:00Z",
            "dish_count": 1,
        },
    )
    result = report_mod.build_operational_report(conn, fallback_manifest_path=manifest)

    assert result["total_dishes"] == 3
    assert result["active_dishes"] == 2
    assert result["eligible_dishes"] == 1
    assert result["rejected_by_reason"]["inactive"] == 1
    assert result["rejected_by_reason"]["diet_type_missing"] == 1
    assert result["published_catalogue"]["publication_version"] == "sha256:" + "a" * 64
    assert result["fallback_catalogue"]["available"] is True
    assert result["fallback_catalogue"]["bundle_version"] == "sha256:deadbeef"
    assert result["rollout_state"]["mode"] == "OFF"
    assert sum(result["gap_bucket_counts"].values()) == 3


def test_operational_report_handles_no_published_version_yet(tmp_path):
    manifest = tmp_path / "missing-manifest.json"
    conn = FakeConnection([gap_row("1")], latest_version=None)
    result = report_mod.build_operational_report(conn, fallback_manifest_path=manifest)
    assert result["published_catalogue"] is None
    assert result["fallback_catalogue"]["available"] is False
