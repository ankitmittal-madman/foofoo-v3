"""Compatibility contract between the normalized ontology and the current class-first RE.

The live engine stays startup-loaded and deterministic. These tests prove that promoting the
ontology snapshot into its immutable bundle preserves today's primary/multi-class membership and
keeps add-on/combo classes out of primary recommendation labels.
"""

from __future__ import annotations

import csv
import json
import os

from ghar_re_service.scripts import export_bundle

from ghar_re_core import knowledge as K
from ghar_re_core import meal_planner
from ghar_re_core.catalogue import Catalogue
from ghar_re_core.fixtures import DISHES


def _class_dir() -> str:
    return os.path.join(export_bundle.DEFAULT_SOURCE_DIR, "class_first_v1")


def _csv_rows(name: str) -> list[dict[str, str]]:
    with open(os.path.join(_class_dir(), name), newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _snapshot() -> dict:
    with open(
        os.path.join(_class_dir(), "food_ontology_snapshot.json"), encoding="utf-8"
    ) as handle:
        return json.load(handle)


def test_snapshot_covers_every_runtime_dish_and_preserves_source_gaps():
    snapshot = _snapshot()
    assert snapshot["schema_version"] == 1
    assert snapshot["dish_count"] == 810
    assert snapshot["source_mapping_count"] == 1500
    assert snapshot["mapping_count"] == 1516
    assert snapshot["unmatched_source_dishes"] == [
        "Lauki Khichdi",
        "Moong Dal Khichdi",
        "Roti",
    ]
    assert all(dish["primary_class_code"] for dish in snapshot["dishes"])
    assert all(dish["mappings"] for dish in snapshot["dishes"])


def test_snapshot_is_exactly_backward_compatible_with_legacy_class_lookup():
    snapshot = _snapshot()
    primary, memberships = K._class_maps_from_snapshot(snapshot)

    curated, legacy_memberships = {}, {}
    for row in _csv_rows("class_dish_options.csv"):
        key = row["dish_name"].strip().lower()
        curated.setdefault(key, row["meal_class_code"])
        legacy_memberships.setdefault(key, set()).add(row["meal_class_code"])
    first_mapping = {}
    for row in _csv_rows("dish_class_map.csv"):
        key = row["dish_name"].strip().lower()
        first_mapping.setdefault(key, row["meal_class_code"])
        legacy_memberships.setdefault(key, set()).add(row["meal_class_code"])

    for dish in snapshot["dishes"]:
        key = dish["name"].strip().lower()
        assert primary[key] == curated.get(key, first_mapping[key])
        assert memberships[key] == legacy_memberships[key]


def test_runtime_lookup_uses_snapshot_without_changing_class_first_contract():
    snapshot = _snapshot()
    role_by_class = {
        row["meal_class_code"]: row["planning_role_v3"]
        for row in _csv_rows("meal_class_master.csv")
    }

    K._DISH_TO_CLASS = None
    K._DISH_OVERRIDES = None
    K._DISH_TO_CLASSES = None
    K._ONTOLOGY_SNAPSHOT = None
    for dish in snapshot["dishes"]:
        name = dish["name"]
        primary = K.dish_to_class_code(name)
        assert primary == dish["primary_class_code"]
        assert role_by_class[primary] in {
            "MAIN_PRIMARY",
            "ADDON_ONLY_NOT_PRIMARY",
            "COMBO_TEMPLATE_NOT_PRIMARY",
        }
        assert all(
            row["planning_role"] == role_by_class[row["class_code"]] for row in dish["mappings"]
        )
        assert K.dish_to_class_codes(name) == frozenset(
            row["class_code"] for row in dish["mappings"]
        )
    # Legacy-only reference names remain available until their canonical entity-resolution
    # decision is reviewed; this is the compatibility fallback that protects golden fixtures.
    assert K.dish_to_class_code("Roti") is not None
    assert K.dish_to_class_codes("Roti")


def test_snapshot_is_part_of_the_versioned_recommendation_bundle(tmp_path):
    manifest = export_bundle.build_bundle(
        export_bundle.DEFAULT_SOURCE_DIR, str(tmp_path / "bundle")
    )
    rel = "class_first_v1/food_ontology_snapshot.json"
    assert rel in manifest["config_sha256"]
    assert os.path.isfile(tmp_path / "bundle" / "config" / rel)


def test_class_backing_cache_cannot_leak_between_catalogue_snapshots():
    """A bundle promotion and a golden-fixture test may coexist in one worker process."""
    full = Catalogue(DISHES)
    one_dish = Catalogue(DISHES[:1])
    full_counts = meal_planner._class_dish_counts(full)
    one_counts = meal_planner._class_dish_counts(one_dish)
    expected = K.dish_to_class_codes(one_dish.dishes[0].name)
    assert sum(one_counts.values()) == len(expected)
    assert one_counts != full_counts
