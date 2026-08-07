"""Stream an immutable, user-free recommendation catalogue publication from production.

The database owns eligibility and row composition. This tool keeps one repeatable, read-only
snapshot, writes canonical JSONL without holding the catalogue in memory, and publishes the
directory atomically only after count and hash verification succeed. It does not deploy, alter
serving configuration, or write to either Supabase project.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import tempfile
from collections.abc import Iterator, Mapping
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

DATABASE_ENV_NAMES = ("DATABASE_URL", "SUPABASE_DB_URL", "FOOFOO_SUPABASE_URI")
ROW_SCHEMA_VERSION = "recommendation-catalogue-row-v1"
MANIFEST_SCHEMA_VERSION = "recommendation-catalogue-publication-v1"


@dataclass(frozen=True)
class PublicationCoverage:
    """Aggregate catalogue readiness counts; contains no household or profile information."""

    active_dishes: int
    enriched_dishes: int
    safety_closed_dishes: int
    class_mapped_dishes: int
    publishable_dishes: int

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> PublicationCoverage:
        """Convert one database coverage row into strict integer counters."""
        return cls(**{name: int(row[name]) for name in cls.__dataclass_fields__})


def database_url(environ: Mapping[str, str] | None = None) -> str:
    """Resolve the explicitly configured production read target and fail closed when absent."""
    values = environ or os.environ
    for name in DATABASE_ENV_NAMES:
        value = values.get(name)
        if value:
            return value
    raise RuntimeError(
        "No production database connection configured; set DATABASE_URL, SUPABASE_DB_URL, "
        "or FOOFOO_SUPABASE_URI."
    )


def _mapping(cursor: Any, row: Any) -> Mapping[str, Any]:
    """Return a cursor result as a mapping for both real and lightweight test cursors."""
    if isinstance(row, Mapping):
        return row
    columns = [item[0] for item in cursor.description]
    return dict(zip(columns, row, strict=True))


def fetch_coverage(connection: Any) -> PublicationCoverage:
    """Read aggregate publication coverage from the governed database boundary."""
    with connection.cursor() as cursor:
        cursor.execute("select * from re_engine.catalogue_publication_coverage()")
        row = cursor.fetchone()
        if row is None:
            raise RuntimeError("Catalogue publication coverage returned no row")
        return PublicationCoverage.from_row(_mapping(cursor, row))


def iter_publication_rows(connection: Any, *, page_size: int = 500) -> Iterator[dict[str, Any]]:
    """Yield deterministic UUID-keyset pages without loading the full catalogue into memory."""
    if not 1 <= page_size <= 2000:
        raise ValueError("page_size must be between 1 and 2000")
    after: str | None = None
    while True:
        with connection.cursor() as cursor:
            cursor.execute(
                "select re_engine.catalogue_publication_rows(%s, %s) as publication_row",
                (after, page_size),
            )
            batch = cursor.fetchall()
        if not batch:
            return
        for result in batch:
            mapped = _mapping(cursor, result)
            row = mapped["publication_row"]
            if not isinstance(row, Mapping):
                raise RuntimeError("Catalogue publication row is not an object")
            value = dict(row)
            if value.get("schema_version") != ROW_SCHEMA_VERSION:
                raise RuntimeError("Catalogue publication row has an unsupported schema")
            dish_id = value.get("id")
            if not isinstance(dish_id, str) or not dish_id:
                raise RuntimeError("Catalogue publication row is missing canonical dish id")
            if after is not None and dish_id <= after:
                raise RuntimeError("Catalogue publication rows are not strictly ordered")
            after = dish_id
            yield value
        if len(batch) < page_size:
            return


def publish(connection: Any, output_dir: Path, *, page_size: int = 500) -> dict[str, Any]:
    """Build and atomically expose one checked catalogue directory from a read-only snapshot."""
    if output_dir.exists():
        raise FileExistsError(f"publication target already exists: {output_dir}")
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{output_dir.name}.", dir=output_dir.parent))
    rows_path = stage / "catalogue.jsonl"
    digest = hashlib.sha256()
    count = 0
    first_id: str | None = None
    last_id: str | None = None
    try:
        coverage = fetch_coverage(connection)
        if coverage.publishable_dishes <= 0:
            raise RuntimeError("No safety-closed, class-mapped dishes are publishable")
        with rows_path.open("x", encoding="utf-8") as output:
            for row in iter_publication_rows(connection, page_size=page_size):
                encoded = (json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n").encode()
                output.write(encoded.decode())
                digest.update(encoded)
                dish_id = str(row["id"])
                first_id = first_id or dish_id
                last_id = dish_id
                count += 1

        if count != coverage.publishable_dishes:
            raise RuntimeError(
                "Catalogue coverage/export count mismatch inside the read-only snapshot: "
                f"{coverage.publishable_dishes} != {count}"
            )

        content_sha256 = digest.hexdigest()
        manifest = {
            "schema_version": MANIFEST_SCHEMA_VERSION,
            "publication_version": f"sha256:{content_sha256}",
            "source": "re_engine.catalogue_publication_rows",
            "generated_at": datetime.now(UTC).isoformat(),
            "row_count": count,
            "first_dish_id": first_id,
            "last_dish_id": last_id,
            "catalogue_jsonl_sha256": content_sha256,
            "coverage": asdict(coverage),
        }
        (stage / "manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        os.replace(stage, output_dir)
        return manifest
    finally:
        if stage.exists():
            shutil.rmtree(stage)


def connect_read_only(dsn: str) -> Any:
    """Open a repeatable, read-only production snapshot with a bounded statement timeout."""
    import psycopg2

    connection = psycopg2.connect(
        dsn,
        connect_timeout=15,
        application_name="foofoo-catalogue-publication",
    )
    connection.set_session(readonly=True, autocommit=False, isolation_level="REPEATABLE READ")
    with connection.cursor() as cursor:
        cursor.execute("set local statement_timeout = '5min'")
    return connection


def main(argv: list[str] | None = None) -> int:
    """Run a local publication build; callers deploy or index the result in a separate gate."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--page-size", type=int, default=500)
    args = parser.parse_args(argv)

    connection = connect_read_only(database_url())
    try:
        manifest = publish(connection, args.output_dir, page_size=args.page_size)
        connection.rollback()
    finally:
        connection.close()
    print(json.dumps(manifest, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
