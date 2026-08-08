"""Publish a validator-passed catalogue snapshot into the DB-backed, insert-only version tables.

Complements (does not replace) the existing file-based publisher in
``ops/recommendation/catalogue_publication.py``: that module streams the same eligible rows to
a content-addressed JSONL/sqlite directory for the Ghar/Qdrant GitHub Actions pipelines; this
module additionally records the identical version as durable rows in
``public.catalogue_versions`` / ``public.catalogue_dishes`` (database/migrations/102), so the
publication history is queryable from the database itself, not only from workflow artifacts.

Publishing here NEVER serves traffic and NEVER touches the 810-dish fallback bundle. Whether a
published version may reach Ghar, Aux, or Qdrant is controlled exclusively by the single-row
``public.catalogue_rollout_state`` gate, which a human must move off ``OFF`` explicitly
(see database/migrations/102_catalogue_version_control_plane.sql).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ops.recommendation.catalogue_publication import (
    PublicationCoverage,
    fetch_coverage,
    iter_publication_rows,
)

# Mirrors the CHECK constraint on public.catalogue_rollout_state.mode.
ROLLOUT_MODES: tuple[str, ...] = ("OFF", "SHADOW", "CANARY", "LIVE")


@dataclass(frozen=True)
class DbPublicationResult:
    """What was written to the DB-backed catalogue tables for one publish call."""

    version_id: str
    publication_version: str
    dish_count: int
    coverage: PublicationCoverage


def publish_to_db(
    connection: Any,
    *,
    generated_by: str,
    page_size: int = 500,
    notes: str | None = None,
) -> DbPublicationResult:
    """Insert one new immutable catalogue_versions row plus its catalogue_dishes rows.

    Reuses the exact same eligible-row source (``re_engine.catalogue_publication_rows()``) and
    the same content hash convention (``sha256:<hex>``) as the file-based publisher, computed
    independently here over the DB-inserted payload so the two publish paths can be cross-checked
    for the same input snapshot. Always creates a new version row — never updates an existing
    one; the immutability triggers in migration 102 enforce this at the database level too.
    """
    import hashlib
    import json

    coverage = fetch_coverage(connection)
    if coverage.publishable_dishes <= 0:
        raise RuntimeError("No publishable dishes; refusing to create an empty catalogue version")

    digest = hashlib.sha256()
    rows: list[dict[str, Any]] = []
    for row in iter_publication_rows(connection, page_size=page_size):
        canonical = json.dumps(row, sort_keys=True, separators=(",", ":"))
        digest.update((canonical + "\n").encode())
        rows.append(row)

    if len(rows) != coverage.publishable_dishes:
        raise RuntimeError(
            "DB publish count mismatch inside the read-only snapshot: "
            f"{coverage.publishable_dishes} != {len(rows)}"
        )

    publication_version = f"sha256:{digest.hexdigest()}"

    with connection.cursor() as cursor:
        cursor.execute(
            "insert into public.catalogue_versions "
            "(publication_version, dish_count, generated_by, notes) "
            "values (%s, %s, %s, %s) returning id::text",
            (publication_version, len(rows), generated_by, notes),
        )
        version_id = cursor.fetchone()
        version_id = version_id[0] if not isinstance(version_id, dict) else version_id["id"]
        for row in rows:
            cursor.execute(
                "insert into public.catalogue_dishes (version_id, dish_id, payload) "
                "values (%s, %s, %s)",
                (version_id, row["id"], json.dumps(row, sort_keys=True)),
            )
    connection.commit()

    return DbPublicationResult(
        version_id=str(version_id),
        publication_version=publication_version,
        dish_count=len(rows),
        coverage=coverage,
    )


def read_rollout_state(connection: Any) -> dict[str, Any]:
    """Read the single-row human rollout gate. Defaults to OFF if the row is somehow absent."""
    with connection.cursor() as cursor:
        cursor.execute(
            "select mode, active_version_id::text as active_version_id, updated_at, updated_by "
            "from public.catalogue_rollout_state where id = true"
        )
        row = cursor.fetchone()
    if row is None:
        return {"mode": "OFF", "active_version_id": None, "updated_at": None, "updated_by": None}
    if isinstance(row, dict):
        return dict(row)
    columns = ("mode", "active_version_id", "updated_at", "updated_by")
    return dict(zip(columns, row, strict=True))


def set_rollout_state(
    connection: Any, *, mode: str, active_version_id: str | None, updated_by: str
) -> None:
    """Explicitly move the human rollout gate. This is the ONLY function that may change it.

    Refuses any mode other than OFF without an active_version_id, matching the CHECK constraint
    on public.catalogue_rollout_state (``mode = 'OFF' OR active_version_id IS NOT NULL``).
    """
    if mode not in ROLLOUT_MODES:
        raise ValueError(f"invalid rollout mode: {mode!r}; must be one of {ROLLOUT_MODES}")
    if mode != "OFF" and active_version_id is None:
        raise ValueError("active_version_id is required for any mode other than OFF")
    with connection.cursor() as cursor:
        cursor.execute(
            "update public.catalogue_rollout_state "
            "set mode = %s, active_version_id = %s, updated_at = now(), updated_by = %s "
            "where id = true",
            (mode, active_version_id, updated_by),
        )
    connection.commit()
