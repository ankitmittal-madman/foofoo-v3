"""Operational report: total/active/eligible/rejected-by-reason, published + fallback counts.

Read-only. Combines:
  - the gap report (ops.recommendation.catalogue_gap_report) for total/bucket counts,
  - the DB-backed publication ledger (public.catalogue_versions) for the latest published
    version/timestamp/checksum/dish_count,
  - the existing 810-dish fallback bundle manifest for the fallback catalogue count,
  - the rollout gate (public.catalogue_rollout_state) for what is actually live.

Contains no user, household, or event data — only dish-count aggregates and catalogue metadata.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ops.recommendation.catalogue_db_publish import read_rollout_state
from ops.recommendation.catalogue_eligibility import evaluate_dish
from ops.recommendation.catalogue_gap_query import iter_dish_records
from ops.recommendation.catalogue_gap_report import build_gap_report

DEFAULT_FALLBACK_MANIFEST = Path("ghar_re_service/data/bundle/manifest.json")


def _fallback_catalogue_info(manifest_path: Path = DEFAULT_FALLBACK_MANIFEST) -> dict[str, Any]:
    """Read the existing, untouched fallback bundle's own manifest for its dish count/version."""
    if not manifest_path.exists():
        return {"available": False, "path": str(manifest_path)}
    manifest = json.loads(manifest_path.read_text())
    return {
        "available": True,
        "path": str(manifest_path),
        "bundle_version": manifest.get("bundle_version"),
        "catalogue_sha256": manifest.get("catalogue_sha256"),
        "catalogue_source": manifest.get("catalogue_source"),
    }


def _latest_catalogue_version(connection: Any) -> dict[str, Any] | None:
    """Latest row in public.catalogue_versions, or None if nothing has ever been published."""
    with connection.cursor() as cursor:
        cursor.execute(
            "select id::text as id, publication_version, created_at, dish_count "
            "from public.catalogue_versions order by created_at desc limit 1"
        )
        row = cursor.fetchone()
    if row is None:
        return None
    if isinstance(row, dict):
        return dict(row)
    columns = ("id", "publication_version", "created_at", "dish_count")
    return dict(zip(columns, row, strict=True))


def build_operational_report(
    connection: Any, *, fallback_manifest_path: Path = DEFAULT_FALLBACK_MANIFEST
) -> dict[str, Any]:
    """Assemble the full operational report from live DB state plus static fallback manifest."""
    dishes = list(iter_dish_records(connection))
    gap = build_gap_report(dishes)
    verdicts = [evaluate_dish(d) for d in dishes]

    rejected_by_reason: dict[str, int] = {}
    for verdict in verdicts:
        for reason in verdict.reasons:
            key = reason.split(":", 1)[0]
            rejected_by_reason[key] = rejected_by_reason.get(key, 0) + 1

    return {
        "total_dishes": len(dishes),
        "active_dishes": sum(1 for d in dishes if d.is_active),
        "eligible_dishes": sum(1 for v in verdicts if v.passed),
        "rejected_by_reason": rejected_by_reason,
        "gap_bucket_counts": gap["counts"],
        "published_catalogue": _latest_catalogue_version(connection),
        "fallback_catalogue": _fallback_catalogue_info(fallback_manifest_path),
        "rollout_state": read_rollout_state(connection),
    }
