"""Build a temporary, identity-free manifest for direct meal-slot source verification."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from database.etl.dish_ingestion.normalize import load_and_normalize

DIRECT_COURSE_SLOTS = {
    "lunch": "lunch",
    "dinner": "dinner",
    "snack": "snacks",
    "appetizer": "snacks",
    "south indian breakfast": "breakfast",
    "world breakfast": "breakfast",
    "north indian breakfast": "breakfast",
    "indian breakfast": "breakfast",
}


def direct_slot_from_course(course: str) -> str | None:
    """Map one exact source course to a canonical slot, or return no direct evidence."""
    return DIRECT_COURSE_SLOTS.get(course.strip().lower())


def build_direct_source_manifest(source_path: Path, output_path: Path) -> int:
    """Write checked-in direct-course row keys to a temporary tab-separated manifest.

    The manifest contains only source row number, deterministic fingerprint and fixed slot. It is
    intended for a protected database session and must not be uploaded as a workflow artifact.
    """
    seen_srnos: set[int] = set()
    manifest_rows: list[tuple[int, str, str]] = []
    for row in load_and_normalize(source_path):
        if row.srno < 0 or row.srno in seen_srnos:
            raise ValueError("source manifest requires unique non-negative source row numbers")
        seen_srnos.add(row.srno)
        direct_slot = direct_slot_from_course(row.normalized["course_raw"])
        if direct_slot is not None:
            manifest_rows.append((row.srno, row.fingerprint, direct_slot))

    if not manifest_rows:
        raise ValueError("source manifest contains no direct meal-slot evidence")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerows(manifest_rows)
    return len(manifest_rows)


def main() -> int:
    """Build a manifest and print only its schema and aggregate row count."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    row_count = build_direct_source_manifest(args.source, args.output)
    print(
        json.dumps(
            {
                "schema_version": "dish-direct-source-manifest-v1",
                "direct_manifest_rows": row_count,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
