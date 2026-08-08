"""Build an identity-free manifest for malformed Course rows using adjacent-field evidence."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from database.etl.dish_ingestion.normalize import load_and_normalize

POLICY_VERSION = "deferred-course-shifted-field-audit-v1"
SCHEMA_VERSION = "deferred-meal-slot-shifted-field-policy-v1"
DIET_VALUES = {
    "eggetarian",
    "high protein vegetarian",
    "no onion no garlic (sattvic)",
    "non vegeterian",
    "sugar free diet",
    "vegan",
    "vegetarian",
}
DIRECT_MAPPINGS = {
    "appetizer": ("snacks",),
    "dinner": ("dinner",),
    "indian breakfast": ("breakfast",),
    "lunch": ("lunch",),
    "north indian breakfast": ("breakfast",),
    "snack": ("snacks",),
    "south indian breakfast": ("breakfast",),
    "world breakfast": ("breakfast",),
}
CONTEXTUAL_MAPPINGS = {
    "brunch": ("breakfast", "lunch"),
    "dessert": ("lunch", "dinner"),
    "main course": ("lunch", "dinner"),
    "one pot dish": ("lunch", "dinner"),
    "side dish": ("lunch", "dinner"),
}
EXPECTED_ROUTES = {
    "shifted_contextual:lunch,dinner": 2,
    "shifted_direct:breakfast": 6,
    "shifted_direct:dinner": 1,
    "shifted_direct:lunch": 1,
    "shifted_direct:snacks": 2,
    "unresolved_food_role": 50,
}


def load_policy(path: Path) -> str:
    """Validate the exact report-only shifted-field policy and return its byte hash."""
    raw = path.read_bytes()
    document: Any = json.loads(raw)
    expected = {
        "contextual_mappings",
        "diet_values_in_course",
        "direct_mappings",
        "policy_version",
        "report_only",
        "schema_version",
        "source_scope",
        "shifted_field",
    }
    if not isinstance(document, dict) or set(document) != expected:
        raise ValueError("deferred shifted-field policy has an unsupported structure")
    if document["schema_version"] != SCHEMA_VERSION or document["policy_version"] != POLICY_VERSION:
        raise ValueError("deferred shifted-field policy identity is invalid")
    if document["report_only"] is not True or document["shifted_field"] != "cuisine_raw":
        raise ValueError("deferred shifted-field policy must remain report-only and field-bound")
    if set(document["diet_values_in_course"]) != DIET_VALUES:
        raise ValueError("deferred shifted-field diet vocabulary drifted")
    direct = {key: tuple(value) for key, value in document["direct_mappings"].items()}
    contextual = {key: tuple(value) for key, value in document["contextual_mappings"].items()}
    if direct != DIRECT_MAPPINGS or contextual != CONTEXTUAL_MAPPINGS:
        raise ValueError("deferred shifted-field meal mapping drifted")
    if document["source_scope"] != {
        "manifest_row_count": 62,
        "route_row_counts": EXPECTED_ROUTES,
    }:
        raise ValueError("deferred shifted-field source scope drifted")
    return hashlib.sha256(raw).hexdigest()


def build_manifest(source_path: Path, policy_path: Path, output_path: Path) -> dict[str, Any]:
    """Write source row number, fingerprint, fixed route and slot key without dish identity."""
    policy_hash = load_policy(policy_path)
    rows: list[tuple[int, str, str, str]] = []
    routes: Counter[str] = Counter()
    seen: set[int] = set()
    for row in load_and_normalize(source_path):
        if row.srno < 0 or row.srno in seen:
            raise ValueError("deferred shifted-field manifest requires unique source row numbers")
        seen.add(row.srno)
        if row.normalized["course_raw"].strip().lower() not in DIET_VALUES:
            continue
        shifted = row.normalized["cuisine_raw"].strip().lower()
        if shifted in DIRECT_MAPPINGS:
            slots = DIRECT_MAPPINGS[shifted]
            route = f"shifted_direct:{','.join(slots)}"
        elif shifted in CONTEXTUAL_MAPPINGS:
            slots = CONTEXTUAL_MAPPINGS[shifted]
            route = f"shifted_contextual:{','.join(slots)}"
        else:
            slots = ()
            route = "unresolved_food_role"
        routes[route] += 1
        rows.append((row.srno, row.fingerprint, route, ",".join(slots)))
    if len(rows) != 62 or dict(sorted(routes.items())) != EXPECTED_ROUTES:
        raise ValueError("deferred shifted-field manifest distribution drifted")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        csv.writer(handle, delimiter="\t", lineterminator="\n").writerows(rows)
    return {
        "schema_version": "deferred-meal-slot-shifted-field-manifest-summary-v1",
        "policy_version": POLICY_VERSION,
        "policy_sha256": policy_hash,
        "manifest_row_count": len(rows),
        "route_row_counts": dict(sorted(routes.items())),
        "report_only": True,
        "identity_exposed": False,
        "raw_source_text_exposed": False,
    }


def main(argv: list[str] | None = None) -> int:
    """Build the protected temporary manifest and print aggregate metadata only."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--policy", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    print(json.dumps(build_manifest(args.source, args.policy, args.output), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
