"""Validate the contextual slot candidate policy and build an identity-free row manifest."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from database.etl.dish_ingestion.normalize import load_and_normalize

SCHEMA_VERSION = "contextual-meal-slot-candidate-policy-v1"
POLICY_VERSION = "contextual-import-course-slot-set-v1"
EXPECTED_MAPPINGS = {
    "brunch": ("breakfast", "lunch"),
    "dessert": ("lunch", "dinner"),
    "main course": ("lunch", "dinner"),
    "one pot dish": ("lunch", "dinner"),
    "side dish": ("lunch", "dinner"),
}
EVIDENCE_CATEGORIES = {
    "brunch": "brunch_candidate",
    "dessert": "dessert_candidate",
    "main course": "main_course_candidate",
    "one pot dish": "one_pot_candidate",
    "side dish": "side_dish_candidate",
}
EXPECTED_SCOPE = {
    "proposal_count": 775,
    "manifest_candidate_row_count": 2003,
    "category_dish_counts": {
        "brunch": 2,
        "dessert": 247,
        "main course": 120,
        "one pot dish": 12,
        "side dish": 394,
    },
    "slot_set_dish_counts": {"breakfast,lunch": 2, "lunch,dinner": 773},
    "deferred_dish_counts": {
        "conflicting_direct_evidence": 1,
        "diet_value_in_course_field": 22,
    },
}


def load_policy(path: Path) -> tuple[dict[str, tuple[str, ...]], str]:
    """Return one exact proposal-only policy and the hash that identifies its review scope.

    @param path - Checked-in candidate policy selected by a protected workflow.
    @returns Normalized course-to-slot-set mappings and SHA-256 of the exact file bytes.
    @throws ValueError when mappings, counts or approval controls differ from the reviewed shape.
    """
    raw = path.read_bytes()
    document: Any = json.loads(raw)
    if not isinstance(document, dict) or set(document) != {
        "candidate_scope",
        "mappings",
        "policy_version",
        "proposal_only",
        "requires_explicit_approval",
        "schema_version",
    }:
        raise ValueError("contextual meal-slot candidate policy has an unsupported structure")
    if document["schema_version"] != SCHEMA_VERSION:
        raise ValueError("contextual meal-slot candidate policy schema is invalid")
    if document["policy_version"] != POLICY_VERSION:
        raise ValueError("contextual meal-slot candidate policy version is invalid")
    if document["proposal_only"] is not True:
        raise ValueError("contextual meal-slot policy must remain proposal-only")
    if document["requires_explicit_approval"] is not True:
        raise ValueError("contextual meal-slot policy must require explicit approval before apply")
    if document["candidate_scope"] != EXPECTED_SCOPE:
        raise ValueError("contextual meal-slot candidate scope is invalid")
    mappings = document["mappings"]
    if not isinstance(mappings, dict) or set(mappings) != set(EXPECTED_MAPPINGS):
        raise ValueError("contextual meal-slot course vocabulary is incomplete or expanded")
    normalized = {
        course: tuple(slots) if isinstance(slots, list) else ()
        for course, slots in mappings.items()
    }
    if normalized != EXPECTED_MAPPINGS:
        raise ValueError("contextual meal-slot mapping differs from the candidate policy")
    return normalized, hashlib.sha256(raw).hexdigest()


def build_manifest(source_path: Path, policy_path: Path, output_path: Path) -> dict[str, Any]:
    """Write fixed contextual course evidence for an ephemeral production verification session.

    @param source_path - Checked-in normalized dish-source CSV.
    @param policy_path - Candidate policy whose exact hash controls proposal generation.
    @param output_path - Temporary TSV path that must never be uploaded as an artifact.
    @returns Aggregate-only policy and manifest metadata safe for workflow evidence.
    @throws ValueError when source row identity or the exact manifest distribution drifts.
    """
    mappings, policy_sha256 = load_policy(policy_path)
    seen_srnos: set[int] = set()
    rows: list[tuple[int, str, str, str]] = []
    category_rows: Counter[str] = Counter()
    for row in load_and_normalize(source_path):
        if row.srno < 0 or row.srno in seen_srnos:
            raise ValueError("contextual manifest requires unique non-negative source row numbers")
        seen_srnos.add(row.srno)
        course = row.normalized["course_raw"].strip().lower()
        slots = mappings.get(course)
        if slots is not None:
            category_rows[course] += 1
            rows.append((row.srno, row.fingerprint, EVIDENCE_CATEGORIES[course], ",".join(slots)))
    if len(rows) != EXPECTED_SCOPE["manifest_candidate_row_count"]:
        raise ValueError("contextual manifest row count drifted from the candidate policy")
    if category_rows != Counter(
        {"brunch": 4, "dessert": 659, "main course": 315, "one pot dish": 33, "side dish": 992}
    ):
        raise ValueError("contextual manifest source distribution drifted")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        csv.writer(handle, delimiter="\t", lineterminator="\n").writerows(rows)
    return {
        "schema_version": "contextual-meal-slot-candidate-manifest-summary-v1",
        "policy_version": POLICY_VERSION,
        "policy_sha256": policy_sha256,
        "mapping_count": len(mappings),
        "manifest_candidate_rows": len(rows),
        "manifest_category_rows": dict(sorted(category_rows.items())),
        "candidate_scope": EXPECTED_SCOPE,
        "proposal_only": True,
        "requires_explicit_approval": True,
    }


def main(argv: list[str] | None = None) -> int:
    """Validate the policy, build its temporary manifest and print aggregate metadata only."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    print(json.dumps(build_manifest(args.source, args.policy, args.output), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
