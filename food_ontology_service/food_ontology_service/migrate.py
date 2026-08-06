from __future__ import annotations

import hashlib
import os
from pathlib import Path

import psycopg

DEFAULT_MIGRATIONS = Path(__file__).resolve().parents[1] / "migrations"


def apply_migrations(dsn: str, directory: Path = DEFAULT_MIGRATIONS) -> list[str]:
    """Apply each immutable SQL migration once under a database advisory lock."""
    applied_now: list[str] = []
    files = sorted(directory.glob("[0-9][0-9][0-9]_*.sql"))
    if not files:
        raise RuntimeError(f"no ontology migrations found in {directory}")
    with psycopg.connect(dsn) as connection:
        connection.execute(
            "SELECT pg_advisory_xact_lock(hashtextextended('foofoo-ontology-migrations',0))"
        )
        connection.execute("CREATE SCHEMA IF NOT EXISTS ontology")
        connection.execute(
            """CREATE TABLE IF NOT EXISTS ontology.schema_migrations(
                 version text PRIMARY KEY,
                 checksum_sha256 text NOT NULL,
                 applied_at timestamptz NOT NULL DEFAULT now()
               )"""
        )
        existing = {
            row[0]: row[1]
            for row in connection.execute(
                "SELECT version,checksum_sha256 FROM ontology.schema_migrations"
            ).fetchall()
        }
        for path in files:
            version = path.name.split("_", 1)[0]
            sql = path.read_text(encoding="utf-8")
            checksum = hashlib.sha256(sql.encode()).hexdigest()
            if version in existing:
                if existing[version] != checksum:
                    raise RuntimeError(f"applied migration checksum changed: {path.name}")
                continue
            connection.execute(sql)
            connection.execute(
                "INSERT INTO ontology.schema_migrations(version,checksum_sha256) VALUES(%s,%s)",
                (version, checksum),
            )
            applied_now.append(path.name)
    return applied_now


def main() -> None:
    database_url = os.getenv("ONTOLOGY_DATABASE_URL")
    if not database_url:
        raise RuntimeError("ONTOLOGY_DATABASE_URL is required for migrations")
    for name in apply_migrations(database_url):
        print(f"applied {name}")


if __name__ == "__main__":
    main()
