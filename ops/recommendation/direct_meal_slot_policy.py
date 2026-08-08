"""Validate the governed direct-slot policy and build its temporary source-row manifest."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any

from database.etl.dish_ingestion.normalize import load_and_normalize

SCHEMA_VERSION = "direct-meal-slot-mapping-policy-v1"
POLICY_VERSION = "direct-import-course-slot-v1"
CANONICAL_SLOTS = {"breakfast", "lunch", "dinner", "snacks"}
EXPECTED_COURSES = {
    "appetizer",
    "dinner",
    "indian breakfast",
    "lunch",
    "north indian breakfast",
    "snack",
    "south indian breakfast",
    "world breakfast",
}


def load_policy(path: Path) -> tuple[dict[str, str], str]:
    """Load one exact policy file and return its governed mapping plus content hash.

    @param path - Checked-in JSON policy selected by the protected workflow.
    @returns The normalized direct-course mapping and SHA-256 of the exact file bytes.
    @throws ValueError when structure, vocabulary or approval controls drift.
    """
    raw = path.read_bytes()
    document: Any = json.loads(raw)
    if not isinstance(document, dict) or set(document) != {
        "approval_scope",
        "schema_version",
        "policy_version",
        "requires_explicit_approval",
        "mappings",
    }:
        raise ValueError("direct meal-slot policy has an unsupported structure")
    if document["schema_version"] != SCHEMA_VERSION:
        raise ValueError("direct meal-slot policy schema version is invalid")
    if document["policy_version"] != POLICY_VERSION:
        raise ValueError("direct meal-slot policy version is invalid")
    if document["requires_explicit_approval"] is not True:
        raise ValueError("direct meal-slot policy must require explicit approval")
    if document["approval_scope"] != {
        "proposal_count": 1802,
        "evidence_link_count": 7222,
        "manifest_direct_row_count": 4806,
        "slot_counts": {"breakfast": 275, "dinner": 294, "lunch": 667, "snacks": 566},
    }:
        raise ValueError("direct meal-slot policy approved scope is invalid")
    mappings = document["mappings"]
    if not isinstance(mappings, dict) or set(mappings) != EXPECTED_COURSES:
        raise ValueError("direct meal-slot policy course vocabulary is incomplete or expanded")
    if any(not isinstance(slot, str) or slot not in CANONICAL_SLOTS for slot in mappings.values()):
        raise ValueError("direct meal-slot policy contains a non-canonical slot")
    return dict(mappings), hashlib.sha256(raw).hexdigest()


def build_manifest(source_path: Path, policy_path: Path, output_path: Path) -> dict[str, Any]:
    """Build an identity-free source-row manifest using the exact governed mapping policy.

    @param source_path - Checked-in normalized dish-source CSV.
    @param policy_path - Checked-in policy whose exact hash will be approved and recorded.
    @param output_path - Ephemeral TSV path used only within one protected database session.
    @returns Aggregate policy and manifest metadata safe for a workflow artifact.
    @throws ValueError when source row identity is invalid or no direct rows exist.
    """
    mappings, policy_sha256 = load_policy(policy_path)
    seen_srnos: set[int] = set()
    rows: list[tuple[int, str, str]] = []
    for row in load_and_normalize(source_path):
        if row.srno < 0 or row.srno in seen_srnos:
            raise ValueError("source manifest requires unique non-negative source row numbers")
        seen_srnos.add(row.srno)
        slot = mappings.get(row.normalized["course_raw"].strip().lower())
        if slot is not None:
            rows.append((row.srno, row.fingerprint, slot))
    if not rows:
        raise ValueError("governed direct meal-slot manifest contains no rows")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        csv.writer(handle, delimiter="\t", lineterminator="\n").writerows(rows)
    return {
        "schema_version": "direct-meal-slot-policy-manifest-summary-v1",
        "policy_version": POLICY_VERSION,
        "policy_sha256": policy_sha256,
        "mapping_count": len(mappings),
        "direct_manifest_rows": len(rows),
        "approval_scope": document_scope(policy_path),
        "requires_explicit_approval": True,
    }


def document_scope(policy_path: Path) -> dict[str, Any]:
    """Return the exact count-bound cohort declared by a validated policy file."""
    document = json.loads(policy_path.read_text(encoding="utf-8"))
    return dict(document["approval_scope"])


def main(argv: list[str] | None = None) -> int:
    """Validate policy, build an ephemeral manifest and print aggregate metadata only."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    print(json.dumps(build_manifest(args.source, args.policy, args.output), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
