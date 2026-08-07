"""Idempotent storage adapters for auto-training runs and research staging."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from typing import Any

from .auto_engine_types import (
    InspectionReport,
    ResearchRecord,
    TableSeedCount,
)


def payload_sha256(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


class MemoryTrainingStore:
    """Transaction-free test/dry-run store with the same idempotency semantics as PostgreSQL."""

    def __init__(self) -> None:
        self.runs: dict[str, dict[str, Any]] = {}
        self.records: dict[tuple[str, str], dict[str, Any]] = {}
        self.model_runs: list[dict[str, Any]] = []

    def begin_run(
        self, batch_id: str, engine_version: str, run_mode: str, config: dict[str, Any]
    ) -> tuple[str, bool]:
        run_id = f"{batch_id}:run-{len(self.runs) + 1}"
        self.runs[run_id] = {
            "id": run_id,
            "batch_id": batch_id,
            "engine_version": engine_version,
            "run_mode": run_mode,
            "status": "running",
            "config": config,
        }
        return run_id, False

    def write_inspection(self, run_id: str, inspection: InspectionReport) -> None:
        self.runs[run_id]["inspection_summary"] = inspection.as_report()

    def seed_records(
        self,
        run_id: str,
        batch_id: str,
        records: list[ResearchRecord],
        minimum_confidence: float,
    ) -> dict[str, TableSeedCount]:
        counts: dict[str, TableSeedCount] = defaultdict(TableSeedCount)
        for record in records:
            count = counts[record.target_table]
            if (
                record.confidence < minimum_confidence
                or record.ontology_mapping_status == "rejected"
            ):
                count.rejected += 1
                continue
            count.confidences.append(record.confidence)
            count.confidence_bands[record.confidence_band] += 1
            key = (record.target_table, record.record_key)
            digest = payload_sha256(record.payload)
            existing = self.records.get(key)
            value = {
                "target_table": record.target_table,
                "record_key": record.record_key,
                "payload": record.payload,
                "payload_sha256": digest,
                "confidence": record.confidence,
                "confidence_band": record.confidence_band,
                "ontology_mapping_status": record.ontology_mapping_status,
                "ontology_version": record.ontology_version,
                "source_type": record.source_type,
                "generation_method": record.generation_method,
                "provenance_tags": list(record.provenance_tags),
                "explanation": record.explanation,
                "first_batch_id": batch_id if existing is None else existing["first_batch_id"],
                "last_batch_id": batch_id,
                "version": 1 if existing is None else existing["version"] + 1,
            }
            if existing is None:
                self.records[key] = value
                count.inserted += 1
            elif existing["payload_sha256"] == digest:
                count.skipped += 1
            elif record.confidence >= existing["confidence"]:
                self.records[key] = value
                count.updated += 1
            else:
                count.skipped += 1
        self.runs[run_id]["seed_summary"] = {
            table: count.as_report() for table, count in sorted(counts.items())
        }
        return dict(counts)

    def fetch_research_records(self, target_table: str) -> list[dict[str, Any]]:
        return [
            value
            for (table, _), value in sorted(self.records.items())
            if table == target_table and value["ontology_mapping_status"] != "rejected"
        ]

    def write_model_run(self, run_id: str, model: dict[str, Any]) -> None:
        self.model_runs.append({"run_id": run_id, **model})

    def finish_run(self, run_id: str, report: dict[str, Any], status: str) -> None:
        self.runs[run_id].update(report)
        self.runs[run_id]["status"] = status


class PostgresTrainingStore:
    """Service-role PostgreSQL adapter; the caller owns commit/rollback."""

    def __init__(self, connection: Any):
        self.connection = connection

    def begin_run(
        self, batch_id: str, engine_version: str, run_mode: str, config: dict[str, Any]
    ) -> tuple[str, bool]:
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s,0))", (batch_id,))
            cursor.execute(
                """INSERT INTO ml.auto_training_runs(batch_id,engine_version,run_mode,config)
                   VALUES(%s,%s,%s,%s::jsonb) RETURNING id::text""",
                (batch_id, engine_version, run_mode, json.dumps(config, sort_keys=True)),
            )
            row = cursor.fetchone()
            if row is None:
                raise RuntimeError("database did not return auto-training run id")
            return str(row[0] if not isinstance(row, dict) else row["id"]), False

    def write_inspection(self, run_id: str, inspection: InspectionReport) -> None:
        with self.connection.cursor() as cursor:
            cursor.execute(
                "UPDATE ml.auto_training_runs SET inspection_summary=%s::jsonb WHERE id=%s",
                (json.dumps(inspection.as_report(), sort_keys=True), run_id),
            )
            for row in inspection.rows:
                cursor.execute(
                    """INSERT INTO ml.auto_training_table_audits(
                         run_id,entity_type,source_table,total_records,usable_records,missing_fields,
                         duplicate_records,orphan_records,low_confidence_records,coverage_score,details)
                       VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb)
                       ON CONFLICT(run_id,entity_type) DO UPDATE SET
                         total_records=excluded.total_records,usable_records=excluded.usable_records,
                         missing_fields=excluded.missing_fields,duplicate_records=excluded.duplicate_records,
                         orphan_records=excluded.orphan_records,
                         low_confidence_records=excluded.low_confidence_records,
                         coverage_score=excluded.coverage_score,details=excluded.details""",
                    (
                        run_id,
                        row.entity_type,
                        row.source_table,
                        row.total_records,
                        row.usable_records,
                        row.missing_fields,
                        row.duplicate_records,
                        row.orphan_records,
                        row.low_confidence_records,
                        row.coverage_score,
                        json.dumps(row.details, sort_keys=True),
                    ),
                )

    def seed_records(
        self,
        run_id: str,
        batch_id: str,
        records: list[ResearchRecord],
        minimum_confidence: float,
    ) -> dict[str, TableSeedCount]:
        counts: dict[str, TableSeedCount] = defaultdict(TableSeedCount)
        with self.connection.cursor() as cursor:
            for record in records:
                count = counts[record.target_table]
                if (
                    record.confidence < minimum_confidence
                    or record.ontology_mapping_status == "rejected"
                ):
                    count.rejected += 1
                    continue
                count.confidences.append(record.confidence)
                count.confidence_bands[record.confidence_band] += 1
                digest = payload_sha256(record.payload)
                cursor.execute(
                    """SELECT payload_sha256,confidence FROM research.auto_training_records
                       WHERE target_table=%s AND record_key=%s FOR UPDATE""",
                    (record.target_table, record.record_key),
                )
                prior = cursor.fetchone()
                if prior:
                    old_hash = prior[0] if not isinstance(prior, dict) else prior["payload_sha256"]
                    old_confidence = float(
                        prior[1] if not isinstance(prior, dict) else prior["confidence"]
                    )
                    if old_hash == digest or record.confidence < old_confidence:
                        count.skipped += 1
                        continue
                    cursor.execute(
                        """UPDATE research.auto_training_records SET payload=%s::jsonb,
                           payload_sha256=%s,source_type=%s,generation_method=%s,confidence=%s,
                           confidence_band=%s,ontology_mapping_status=%s,ontology_version=%s,
                           provenance_tags=%s,explanation=%s,last_batch_id=%s,version=version+1,
                           updated_at=now() WHERE target_table=%s AND record_key=%s""",
                        (
                            json.dumps(record.payload, sort_keys=True),
                            digest,
                            record.source_type,
                            record.generation_method,
                            record.confidence,
                            record.confidence_band,
                            record.ontology_mapping_status,
                            record.ontology_version,
                            list(record.provenance_tags),
                            record.explanation,
                            batch_id,
                            record.target_table,
                            record.record_key,
                        ),
                    )
                    count.updated += 1
                else:
                    cursor.execute(
                        """INSERT INTO research.auto_training_records(
                           target_table,record_key,payload,payload_sha256,source_type,generation_method,
                           confidence,confidence_band,ontology_mapping_status,ontology_version,
                           provenance_tags,explanation,first_batch_id,last_batch_id)
                           VALUES(%s,%s,%s::jsonb,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                        (
                            record.target_table,
                            record.record_key,
                            json.dumps(record.payload, sort_keys=True),
                            digest,
                            record.source_type,
                            record.generation_method,
                            record.confidence,
                            record.confidence_band,
                            record.ontology_mapping_status,
                            record.ontology_version,
                            list(record.provenance_tags),
                            record.explanation,
                            batch_id,
                            batch_id,
                        ),
                    )
                    count.inserted += 1

            for table, count in counts.items():
                report = count.as_report()
                bands = report["confidence_bands"]
                cursor.execute(
                    """INSERT INTO ml.auto_training_seed_counts(
                       run_id,target_table,inserted_count,updated_count,skipped_count,rejected_count,
                       average_confidence,high_confidence_count,medium_confidence_count,low_confidence_count)
                       VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                       ON CONFLICT(run_id,target_table) DO UPDATE SET
                         inserted_count=excluded.inserted_count,updated_count=excluded.updated_count,
                         skipped_count=excluded.skipped_count,rejected_count=excluded.rejected_count,
                         average_confidence=excluded.average_confidence,
                         high_confidence_count=excluded.high_confidence_count,
                         medium_confidence_count=excluded.medium_confidence_count,
                         low_confidence_count=excluded.low_confidence_count""",
                    (
                        run_id,
                        table,
                        count.inserted,
                        count.updated,
                        count.skipped,
                        count.rejected,
                        report["average_confidence"],
                        bands["high"],
                        bands["medium"],
                        bands["low"],
                    ),
                )
            cursor.execute(
                "UPDATE ml.auto_training_runs SET seed_summary=%s::jsonb WHERE id=%s",
                (
                    json.dumps(
                        {table: count.as_report() for table, count in sorted(counts.items())},
                        sort_keys=True,
                    ),
                    run_id,
                ),
            )
        return dict(counts)

    def fetch_research_records(self, target_table: str) -> list[dict[str, Any]]:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """SELECT target_table,record_key,payload,payload_sha256,confidence,confidence_band,
                   ontology_mapping_status,ontology_version,source_type,generation_method,
                   provenance_tags,explanation,first_batch_id,last_batch_id,version
                   FROM research.auto_training_records
                   WHERE target_table=%s AND ontology_mapping_status<>'rejected'
                   ORDER BY record_key""",
                (target_table,),
            )
            columns = [item[0] for item in cursor.description]
            return [
                dict(row) if isinstance(row, dict) else dict(zip(columns, row, strict=True))
                for row in cursor.fetchall()
            ]

    def write_model_run(self, run_id: str, model: dict[str, Any]) -> None:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """INSERT INTO ml.auto_training_model_runs(
                   run_id,model_name,status,input_source_split,input_record_count,artifact_uri,
                   artifact_checksum,metrics,gate_checks,reason)
                   VALUES(%s,%s,%s,%s::jsonb,%s,%s,%s,%s::jsonb,%s::jsonb,%s)
                   ON CONFLICT(run_id,model_name) DO UPDATE SET status=excluded.status,
                     input_source_split=excluded.input_source_split,
                     input_record_count=excluded.input_record_count,artifact_uri=excluded.artifact_uri,
                     artifact_checksum=excluded.artifact_checksum,metrics=excluded.metrics,
                     gate_checks=excluded.gate_checks,reason=excluded.reason""",
                (
                    run_id,
                    model["model_name"],
                    model["status"],
                    json.dumps(model.get("input_source_split", {}), sort_keys=True),
                    model.get("input_record_count", 0),
                    model.get("artifact_uri"),
                    model.get("artifact_checksum"),
                    json.dumps(model.get("metrics", {}), sort_keys=True),
                    json.dumps(model.get("gate_checks", {}), sort_keys=True),
                    model.get("reason"),
                ),
            )

    def finish_run(self, run_id: str, report: dict[str, Any], status: str) -> None:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """UPDATE ml.auto_training_runs SET status=%s,batch_confidence=%s,
                   batch_confidence_band=%s,research_summary=%s::jsonb,
                   ontology_summary=%s::jsonb,training_summary=%s::jsonb,
                   evaluation_summary=%s::jsonb,readiness_summary=%s::jsonb,
                   next_actions=%s::jsonb,completed_at=now() WHERE id=%s""",
                (
                    status,
                    report["research_generation"]["batch_confidence"],
                    report["research_generation"]["batch_confidence_band"],
                    json.dumps(report["research_generation"], sort_keys=True),
                    json.dumps(report["ontology"], sort_keys=True),
                    json.dumps(report["training"], sort_keys=True),
                    json.dumps(report["evaluation"], sort_keys=True),
                    json.dumps(report["readiness"], sort_keys=True),
                    json.dumps(report["next_actions"], sort_keys=True),
                    run_id,
                ),
            )


class DryRunTrainingStore(MemoryTrainingStore):
    """Simulate writes while reading already-staged research from PostgreSQL."""

    def __init__(self, connection: Any):
        super().__init__()
        self.source = PostgresTrainingStore(connection)
        self._loaded_tables: set[str] = set()

    def _load(self, target_table: str) -> None:
        if target_table in self._loaded_tables:
            return
        for value in self.source.fetch_research_records(target_table):
            self.records[(target_table, value["record_key"])] = value
        self._loaded_tables.add(target_table)

    def seed_records(
        self,
        run_id: str,
        batch_id: str,
        records: list[ResearchRecord],
        minimum_confidence: float,
    ) -> dict[str, TableSeedCount]:
        for target_table in {record.target_table for record in records}:
            self._load(target_table)
        return super().seed_records(run_id, batch_id, records, minimum_confidence)

    def fetch_research_records(self, target_table: str) -> list[dict[str, Any]]:
        self._load(target_table)
        return super().fetch_research_records(target_table)
