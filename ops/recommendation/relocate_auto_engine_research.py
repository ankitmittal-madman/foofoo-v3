"""Copy verified Auto Engine research rows to training storage, then remove the source copy."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import re
import tempfile
from collections import Counter
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

FORMAT = "foofoo-auto-engine-research-transfer-v1"
SOURCE_TYPE = "expert_research_synthetic"
BATCH_ID_PATTERN = re.compile(r"sha256:[0-9a-f]{24,64}\Z")
ALLOWED_TARGETS = {
    "research.constraint_examples",
    "research.household_personas",
    "research.interactions",
    "research.meal_examples",
    "research.substitution_examples",
    "research.user_personas",
    "research.weekly_plans",
}
TRANSFER_COLUMNS = (
    "id",
    "target_table",
    "record_key",
    "payload",
    "payload_sha256",
    "source_type",
    "generation_method",
    "confidence",
    "confidence_band",
    "ontology_mapping_status",
    "ontology_version",
    "provenance_tags",
    "explanation",
    "first_batch_id",
    "last_batch_id",
    "version",
    "created_at",
    "updated_at",
    "synthetic_only",
    "source_dataset_version",
    "generation_version",
    "transformation_version",
    "source_lineage",
)


def _connect(dsn: str, *, read_only: bool, application_name: str) -> Any:
    import psycopg2

    connection = psycopg2.connect(
        dsn,
        connect_timeout=15,
        application_name=application_name,
    )
    connection.set_session(readonly=read_only, autocommit=False)
    return connection


def _required_database_url(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Required database connection {name} is not configured")
    return value


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False
    ) as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        temporary = handle.name
    os.replace(temporary, path)


def _validate_record(record: Mapping[str, Any]) -> None:
    if set(record) != set(TRANSFER_COLUMNS):
        raise RuntimeError("transfer record columns do not match the governed format")
    if record["target_table"] not in ALLOWED_TARGETS:
        raise RuntimeError(f"unsafe transfer target: {record['target_table']}")
    if record["source_type"] != SOURCE_TYPE or not record["synthetic_only"]:
        raise RuntimeError("only synthetic Auto Engine research records may be transferred")
    digest = hashlib.sha256(_canonical(record["payload"])).hexdigest()
    if digest != record["payload_sha256"]:
        raise RuntimeError(f"payload checksum mismatch for {record['record_key']}")


def _validate_batch_id(batch_id: str) -> None:
    if not BATCH_ID_PATTERN.fullmatch(batch_id):
        raise RuntimeError("batch ID must be a bounded sha256 provenance identifier")


def _manifest_batch_id(manifest: Mapping[str, Any]) -> str:
    selector = manifest.get("source_selector")
    if not isinstance(selector, Mapping):
        raise RuntimeError("transfer manifest is missing its source selector")
    batch_id = selector.get("batch_id")
    if not isinstance(batch_id, str):
        raise RuntimeError("transfer manifest is missing its batch ID")
    _validate_batch_id(batch_id)
    if selector != {
        "batch_id": batch_id,
        "source_type": SOURCE_TYPE,
        "synthetic_only": True,
    }:
        raise RuntimeError("transfer manifest source selector is not governed")
    return batch_id


def _read_transfer(path: Path, manifest_path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("format") != FORMAT:
        raise RuntimeError("unsupported transfer manifest format")
    batch_id = _manifest_batch_id(manifest)
    records: list[dict[str, Any]] = []
    digest = hashlib.sha256()
    with gzip.open(path, "rb") as source:
        for line in source:
            digest.update(line)
            record = json.loads(line)
            _validate_record(record)
            if record["first_batch_id"] != batch_id or record["last_batch_id"] != batch_id:
                raise RuntimeError("transfer record falls outside the selected batch")
            records.append(record)
            if len(records) > 10_000:
                raise RuntimeError("transfer record limit exceeded")
    if len(records) != int(manifest["record_count"]):
        raise RuntimeError("transfer record count does not match manifest")
    if digest.hexdigest() != manifest["content_sha256"]:
        raise RuntimeError("transfer content checksum does not match manifest")
    targets = dict(sorted(Counter(row["target_table"] for row in records).items()))
    if targets != manifest["target_counts"]:
        raise RuntimeError("transfer target counts do not match manifest")
    return records, manifest


def export_records(
    connection: Any,
    path: Path,
    manifest_path: Path,
    expected_count: int,
    batch_id: str,
) -> dict[str, Any]:
    """Export the bounded synthetic research set without including any production identity row."""
    _validate_batch_id(batch_id)
    select_fields = ",".join(
        (
            "id::text AS id",
            "target_table",
            "record_key",
            "payload",
            "payload_sha256",
            "source_type",
            "generation_method",
            "confidence::text AS confidence",
            "confidence_band",
            "ontology_mapping_status",
            "ontology_version",
            "provenance_tags",
            "explanation",
            "first_batch_id",
            "last_batch_id",
            "version",
            "created_at::text AS created_at",
            "updated_at::text AS updated_at",
            "synthetic_only",
            "source_dataset_version",
            "generation_version",
            "transformation_version",
            "source_lineage",
        )
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    target_counts: Counter[str] = Counter()
    count = 0
    with connection.cursor() as cursor, gzip.open(path, "wb", compresslevel=9) as output:
        cursor.execute(
            f"""SELECT {select_fields}
                FROM research.auto_training_records
                WHERE synthetic_only AND source_type=%s
                  AND first_batch_id=%s AND last_batch_id=%s
                ORDER BY target_table,record_key""",
            (SOURCE_TYPE, batch_id, batch_id),
        )
        columns = [item[0] for item in cursor.description]
        for row in cursor:
            record = dict(row) if isinstance(row, Mapping) else dict(zip(columns, row, strict=True))
            _validate_record(record)
            encoded = _canonical(record) + b"\n"
            output.write(encoded)
            digest.update(encoded)
            target_counts[record["target_table"]] += 1
            count += 1
    if count != expected_count:
        raise RuntimeError(f"expected {expected_count} research records, found {count}")
    manifest = {
        "format": FORMAT,
        "record_count": count,
        "content_sha256": digest.hexdigest(),
        "target_counts": dict(sorted(target_counts.items())),
        "source_selector": {
            "batch_id": batch_id,
            "source_type": SOURCE_TYPE,
            "synthetic_only": True,
        },
    }
    _atomic_json(manifest_path, manifest)
    return manifest


def _same_record(existing: Mapping[str, Any], incoming: Mapping[str, Any]) -> bool:
    compared = set(TRANSFER_COLUMNS) - {"id", "created_at", "updated_at"}
    return all(existing[name] == incoming[name] for name in compared)


def import_records(
    connection: Any, records: Iterable[dict[str, Any]], expected_count: int
) -> dict[str, int]:
    """Insert missing records into training storage and reject divergent natural-key conflicts."""
    inserted = 0
    skipped = 0
    values = list(records)
    if len(values) != expected_count:
        raise RuntimeError("import input count changed after manifest verification")
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s,0))", (FORMAT,))
        for record in values:
            cursor.execute(
                """SELECT target_table,record_key,payload,payload_sha256,source_type,
                          generation_method,confidence::text AS confidence,confidence_band,
                          ontology_mapping_status,ontology_version,provenance_tags,explanation,
                          first_batch_id,last_batch_id,version,synthetic_only,
                          source_dataset_version,generation_version,transformation_version,source_lineage
                   FROM research.auto_training_records
                   WHERE target_table=%s AND record_key=%s FOR UPDATE""",
                (record["target_table"], record["record_key"]),
            )
            prior = cursor.fetchone()
            if prior is not None:
                columns = [item[0] for item in cursor.description]
                existing = (
                    dict(prior)
                    if isinstance(prior, Mapping)
                    else dict(zip(columns, prior, strict=True))
                )
                if not _same_record(existing, record):
                    raise RuntimeError(
                        "training target contains a divergent record for "
                        f"{record['target_table']}:{record['record_key']}"
                    )
                skipped += 1
                continue
            cursor.execute(
                """INSERT INTO research.auto_training_records(
                       id,target_table,record_key,payload,payload_sha256,source_type,
                       generation_method,confidence,confidence_band,ontology_mapping_status,
                       ontology_version,provenance_tags,explanation,first_batch_id,last_batch_id,
                       version,created_at,updated_at,synthetic_only,source_dataset_version,
                       generation_version,transformation_version,source_lineage)
                   VALUES(%s,%s,%s,%s::jsonb,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                          %s,%s,%s,%s,%s::jsonb)""",
                tuple(
                    json.dumps(record[name], sort_keys=True)
                    if name in {"payload", "source_lineage"}
                    else record[name]
                    for name in TRANSFER_COLUMNS
                ),
            )
            inserted += 1
        cursor.execute(
            """SELECT count(*) FROM research.auto_training_records
               WHERE synthetic_only AND source_type='expert_research_synthetic'
                 AND (target_table,record_key) IN (
                   SELECT * FROM unnest(%s::text[],%s::text[])
                 )""",
            (
                [row["target_table"] for row in values],
                [row["record_key"] for row in values],
            ),
        )
        verified = int(cursor.fetchone()[0])
        if verified != expected_count:
            raise RuntimeError(f"training verification expected {expected_count}, found {verified}")
    return {"inserted": inserted, "skipped": skipped, "verified": expected_count}


def delete_source_records(
    connection: Any, records: Iterable[dict[str, Any]], expected_count: int
) -> dict[str, Any]:
    """Delete only source rows whose natural key, payload hash, batch and version are unchanged."""
    values = list(records)
    if len(values) != expected_count:
        raise RuntimeError("cleanup input count changed after manifest verification")
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s,0))", (FORMAT,))
        for record in values:
            cursor.execute(
                """SELECT payload_sha256,last_batch_id,version
                   FROM research.auto_training_records
                   WHERE target_table=%s AND record_key=%s FOR UPDATE""",
                (record["target_table"], record["record_key"]),
            )
            current = cursor.fetchone()
            expected = (
                record["payload_sha256"],
                record["last_batch_id"],
                int(record["version"]),
            )
            if current is None or tuple(current) != expected:
                raise RuntimeError(
                    "production research record changed after export; refusing cleanup for "
                    f"{record['target_table']}:{record['record_key']}"
                )
        cursor.execute(
            """DELETE FROM research.auto_training_records
               WHERE (target_table,record_key) IN (
                 SELECT * FROM unnest(%s::text[],%s::text[])
               )""",
            (
                [row["target_table"] for row in values],
                [row["record_key"] for row in values],
            ),
        )
        if cursor.rowcount != expected_count:
            raise RuntimeError(f"cleanup expected {expected_count} deletes, got {cursor.rowcount}")
    return {"deleted": expected_count}


def storage_report(connection: Any) -> dict[str, int]:
    """Return database and relation fork sizes without exposing row content."""
    with connection.cursor() as cursor:
        cursor.execute(
            """SELECT pg_database_size(current_database()),
                      pg_relation_size('research.auto_training_records'),
                      pg_indexes_size('research.auto_training_records'),
                      COALESCE(pg_total_relation_size(reltoastrelid),0)
               FROM pg_class WHERE oid='research.auto_training_records'::regclass"""
        )
        row = cursor.fetchone()
        if row is None:
            raise RuntimeError("auto_training_records storage audit returned no row")
    return {
        "database_bytes": int(row[0]),
        "table_heap_bytes": int(row[1]),
        "index_bytes": int(row[2]),
        "toast_total_bytes": int(row[3]),
        "relation_total_bytes": int(row[1]) + int(row[2]) + int(row[3]),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("export", "import", "delete", "audit"))
    parser.add_argument("--transfer", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--expected-count", type=int, default=461)
    parser.add_argument("--batch-id")
    args = parser.parse_args(argv)

    if args.mode in {"export", "import", "delete"} and (not args.transfer or not args.manifest):
        parser.error("--transfer and --manifest are required for export, import, and delete")
    if args.mode in {"export", "import", "delete"} and not args.batch_id:
        parser.error("--batch-id is required for export, import, and delete")
    environment = "TRAINING_DATABASE_URL" if args.mode == "import" else "FOOFOO_SUPABASE_URI"
    connection = _connect(
        _required_database_url(environment),
        read_only=args.mode in {"export", "audit"},
        application_name=f"foofoo-auto-engine-research-{args.mode}",
    )
    try:
        before = storage_report(connection)
        if args.mode == "export":
            result = export_records(
                connection,
                args.transfer,
                args.manifest,
                args.expected_count,
                args.batch_id,
            )
            connection.rollback()
        elif args.mode == "import":
            records, manifest = _read_transfer(args.transfer, args.manifest)
            if _manifest_batch_id(manifest) != args.batch_id:
                raise RuntimeError("requested batch does not match the transfer manifest")
            result = import_records(connection, records, args.expected_count)
            connection.commit()
        elif args.mode == "delete":
            records, manifest = _read_transfer(args.transfer, args.manifest)
            if _manifest_batch_id(manifest) != args.batch_id:
                raise RuntimeError("requested batch does not match the transfer manifest")
            result = delete_source_records(connection, records, args.expected_count)
            connection.commit()
        else:
            result = {"status": "audited"}
            connection.rollback()
        after = storage_report(connection)
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
    report = {"mode": args.mode, "result": result, "before": before, "after": after}
    _atomic_json(args.report, report)
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
