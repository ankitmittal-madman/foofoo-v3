from __future__ import annotations

from pathlib import Path

import pytest

from ops.recommendation.dish_source_manifest import (
    build_direct_source_manifest,
    direct_slot_from_course,
)

SOURCE = Path("database/seeds/IndianFoodDatasetCSV.csv")


@pytest.mark.parametrize(
    ("course", "expected"),
    [
        ("Lunch", "lunch"),
        ("Dinner", "dinner"),
        ("Snack", "snacks"),
        ("Appetizer", "snacks"),
        ("South Indian Breakfast", "breakfast"),
        ("World Breakfast", "breakfast"),
        ("North Indian Breakfast", "breakfast"),
        ("Indian Breakfast", "breakfast"),
        ("Main Course", None),
    ],
)
def test_direct_slot_mapping_matches_governed_sql(course: str, expected: str | None) -> None:
    """Only the eight exact source-course labels may become direct meal-slot evidence."""
    assert direct_slot_from_course(course) == expected


def test_checked_in_manifest_is_deterministic_bounded_and_identity_free(tmp_path: Path) -> None:
    """The checked-in dataset must produce the reviewed direct-row count and safe columns."""
    first = tmp_path / "first.tsv"
    second = tmp_path / "second.tsv"

    assert build_direct_source_manifest(SOURCE, first) == 4806
    assert build_direct_source_manifest(SOURCE, second) == 4806
    assert first.read_bytes() == second.read_bytes()
    rows = first.read_text().splitlines()
    assert len(rows) == 4806
    for row in rows:
        source_srno, fingerprint, direct_slot = row.split("\t")
        assert int(source_srno) >= 0
        assert len(fingerprint) == 64
        assert direct_slot in {"breakfast", "lunch", "dinner", "snacks"}
