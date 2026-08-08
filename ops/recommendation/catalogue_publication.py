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
import sqlite3
import tempfile
from collections.abc import Iterator, Mapping
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ops.recommendation.protected_identity import database_identifies_project

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


def production_database_url(environ: Mapping[str, str] | None = None) -> str:
    """Resolve only a connection that cryptographically names the protected production project."""
    values = environ or os.environ
    value = database_url(values)
    project_ref = values.get("PRODUCTION_PROJECT_REF", "")
    if not project_ref or not database_identifies_project(value, project_ref):
        raise RuntimeError("production database identity is missing or ambiguous")
    return value


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


def fetch_identity_count(connection: Any) -> int:
    """Read the governed count of canonical dish identities, independent of eligibility."""
    with connection.cursor() as cursor:
        cursor.execute("select re_engine.catalogue_identity_coverage() as identity_count")
        row = cursor.fetchone()
        if row is None:
            raise RuntimeError("Catalogue identity coverage returned no row")
        return int(_mapping(cursor, row)["identity_count"])


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


def iter_identity_rows(connection: Any, *, page_size: int = 500) -> Iterator[dict[str, str]]:
    """Yield deterministic canonical UUID/name pages without asserting serving eligibility."""
    if not 1 <= page_size <= 2000:
        raise ValueError("page_size must be between 1 and 2000")
    after: str | None = None
    while True:
        with connection.cursor() as cursor:
            cursor.execute(
                "select dish_id::text, name from re_engine.catalogue_identity_rows(%s, %s)",
                (after, page_size),
            )
            batch = cursor.fetchall()
            mapped_batch = [_mapping(cursor, result) for result in batch]
        if not mapped_batch:
            return
        for row in mapped_batch:
            dish_id = str(row.get("dish_id") or "")
            name = str(row.get("name") or "").strip()
            if not dish_id or not name:
                raise RuntimeError("Catalogue identity row is incomplete")
            if after is not None and dish_id <= after:
                raise RuntimeError("Catalogue identity rows are not strictly ordered")
            after = dish_id
            yield {"dish_id": dish_id, "name": name}
        if len(mapped_batch) < page_size:
            return


def _create_hydration_index(path: Path) -> sqlite3.Connection:
    """Create the disk-backed canonical-ID/slot/class index used by bounded engine retrieval."""
    database = sqlite3.connect(path)
    database.executescript(
        """
        PRAGMA journal_mode=OFF;
        PRAGMA synchronous=OFF;
        PRAGMA page_size=4096;
        CREATE TABLE catalogue (
          dish_id TEXT PRIMARY KEY,
          name TEXT NOT NULL,
          payload TEXT NOT NULL
        ) WITHOUT ROWID;
        CREATE TABLE catalogue_identity (
          dish_id TEXT PRIMARY KEY,
          normalized_name TEXT NOT NULL UNIQUE,
          name TEXT NOT NULL
        ) WITHOUT ROWID;
        CREATE TABLE dish_slots (
          slot TEXT NOT NULL,
          dish_id TEXT NOT NULL REFERENCES catalogue(dish_id),
          PRIMARY KEY (slot, dish_id)
        ) WITHOUT ROWID;
        CREATE TABLE dish_classes (
          class_code TEXT NOT NULL,
          dish_id TEXT NOT NULL REFERENCES catalogue(dish_id),
          PRIMARY KEY (class_code, dish_id)
        ) WITHOUT ROWID;
        """
    )
    return database


def _sha256_file(path: Path) -> str:
    """Hash a finished artifact in bounded chunks so large indexes stay memory-safe."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def publish(connection: Any, output_dir: Path, *, page_size: int = 500) -> dict[str, Any]:
    """Build and atomically expose one checked catalogue directory from a read-only snapshot."""
    if output_dir.exists():
        raise FileExistsError(f"publication target already exists: {output_dir}")
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{output_dir.name}.", dir=output_dir.parent))
    rows_path = stage / "catalogue.jsonl"
    index_path = stage / "catalogue.sqlite3"
    rows_digest = hashlib.sha256()
    publication_digest = hashlib.sha256()
    count = 0
    identity_count = 0
    first_id: str | None = None
    last_id: str | None = None
    try:
        coverage = fetch_coverage(connection)
        expected_identity_count = fetch_identity_count(connection)
        if coverage.publishable_dishes <= 0:
            raise RuntimeError("No safety-closed, class-mapped dishes are publishable")
        if expected_identity_count <= 0:
            raise RuntimeError("No canonical dish identities are publishable")
        with (
            rows_path.open("x", encoding="utf-8") as output,
            _create_hydration_index(index_path) as index,
        ):
            for row in iter_publication_rows(connection, page_size=page_size):
                canonical = json.dumps(row, sort_keys=True, separators=(",", ":"))
                encoded = (canonical + "\n").encode()
                output.write(encoded.decode())
                rows_digest.update(encoded)
                publication_digest.update(b"catalogue:")
                publication_digest.update(encoded)
                dish_id = str(row["id"])
                index.execute(
                    "INSERT INTO catalogue(dish_id, name, payload) VALUES (?, ?, ?)",
                    (dish_id, str(row["name"]), canonical),
                )
                index.executemany(
                    "INSERT OR IGNORE INTO dish_slots(slot, dish_id) VALUES (?, ?)",
                    ((str(slot), dish_id) for slot in row.get("meal_slots", [])),
                )
                index.executemany(
                    "INSERT OR IGNORE INTO dish_classes(class_code, dish_id) VALUES (?, ?)",
                    (
                        (str(item["class_code"]), dish_id)
                        for item in row.get("meal_classes", [])
                        if isinstance(item, Mapping) and item.get("class_code")
                    ),
                )
                first_id = first_id or dish_id
                last_id = dish_id
                count += 1
            for identity in iter_identity_rows(connection, page_size=page_size):
                dish_id = identity["dish_id"]
                name = identity["name"]
                normalized_name = " ".join(name.casefold().split())
                try:
                    index.execute(
                        "INSERT INTO catalogue_identity(dish_id, normalized_name, name) "
                        "VALUES (?, ?, ?)",
                        (dish_id, normalized_name, name),
                    )
                except sqlite3.IntegrityError as exc:
                    raise RuntimeError("Canonical catalogue identity is not unique") from exc
                identity_encoded = f"{dish_id}\t{normalized_name}\t{name}\n".encode()
                publication_digest.update(b"identity:")
                publication_digest.update(identity_encoded)
                identity_count += 1
            index.commit()
            mismatch_count = index.execute(
                """
                SELECT count(*)
                FROM catalogue c
                LEFT JOIN catalogue_identity i ON i.dish_id = c.dish_id AND i.name = c.name
                WHERE i.dish_id IS NULL
                """
            ).fetchone()[0]
            if mismatch_count:
                raise RuntimeError("Safety-closed catalogue identity is incomplete")
            index.execute("VACUUM")

        if count != coverage.publishable_dishes:
            raise RuntimeError(
                "Catalogue coverage/export count mismatch inside the read-only snapshot: "
                f"{coverage.publishable_dishes} != {count}"
            )
        if identity_count != expected_identity_count:
            raise RuntimeError(
                "Catalogue identity coverage/export count mismatch inside the read-only snapshot: "
                f"{expected_identity_count} != {identity_count}"
            )

        content_sha256 = rows_digest.hexdigest()
        publication_sha256 = publication_digest.hexdigest()
        index_sha256 = _sha256_file(index_path)
        manifest = {
            "schema_version": MANIFEST_SCHEMA_VERSION,
            "publication_version": f"sha256:{publication_sha256}",
            "source": {
                "catalogue": "re_engine.catalogue_publication_rows",
                "identity": "re_engine.catalogue_identity_rows",
            },
            "generated_at": datetime.now(UTC).isoformat(),
            "row_count": count,
            "identity_row_count": identity_count,
            "first_dish_id": first_id,
            "last_dish_id": last_id,
            "catalogue_jsonl_sha256": content_sha256,
            "catalogue_sqlite_sha256": index_sha256,
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


def connect_read_only(dsn: str, *, application_name: str = "foofoo-catalogue-publication") -> Any:
    """Open a repeatable, read-only production snapshot with a bounded statement timeout."""
    import psycopg2

    connection = psycopg2.connect(
        dsn,
        connect_timeout=15,
        application_name=application_name[:63],
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

    application_name = f"foofoo-catalogue-{os.environ.get('GITHUB_RUN_ID', 'local')}"
    connection = connect_read_only(production_database_url(), application_name=application_name)
    try:
        manifest = publish(connection, args.output_dir, page_size=args.page_size)
        connection.rollback()
    finally:
        connection.close()
    print(json.dumps(manifest, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
