from __future__ import annotations

import contextvars
import hashlib
import json
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Callable, Iterator
from uuid import UUID

import psycopg
from psycopg import Connection
from psycopg.errors import ForeignKeyViolation, UniqueViolation
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from .models import (
    AliasInput,
    ClassMembershipInput,
    DishCreate,
    DishPatch,
    DishRecord,
    FeedbackInput,
    FieldValue,
    ImageRef,
    SimilarityInput,
)
from .repository import ConflictError, IdempotentResult, NotFoundError, normalize_name


_ACTIVE_CONNECTION: contextvars.ContextVar[Connection | None] = contextvars.ContextVar(
    "ontology_postgres_connection", default=None
)


def _json(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, UUID | datetime):
        return str(value)
    return value


def _request_digest(value: Any) -> str:
    def scrub(item: Any) -> Any:
        if isinstance(item, dict):
            return {key: scrub(child) for key, child in item.items() if key != "last_verified_at"}
        if isinstance(item, list):
            return [scrub(child) for child in item]
        return item

    encoded = json.dumps(scrub(value), sort_keys=True, default=_json, separators=(",", ":"))
    return hashlib.sha256(encoded.encode()).hexdigest()


class PostgresRepository:
    """Normalized PostgreSQL adapter. Idempotent commands share one database transaction."""

    def __init__(self, dsn: str):
        if not dsn:
            raise RuntimeError("ontology PostgreSQL DSN required")
        self.dsn = dsn

    def _connect(self) -> Connection:
        return psycopg.connect(self.dsn, row_factory=dict_row)

    @contextmanager
    def _connection(self) -> Iterator[Connection]:
        active = _ACTIVE_CONNECTION.get()
        if active is not None:
            yield active
            return
        with self._connect() as connection:
            yield connection

    def ping(self) -> None:
        with self._connection() as connection:
            connection.execute("SELECT 1")

    def idempotent(
        self,
        principal: str,
        operation: str,
        key: str,
        body: Any,
        action: Callable[[], tuple[int, dict[str, Any]]],
    ) -> IdempotentResult:
        digest = _request_digest(body)
        with self._connect() as connection:
            # Serializes only contenders for this logical key and avoids an action/idempotency gap.
            connection.execute(
                "SELECT pg_advisory_xact_lock(hashtextextended(%s,0))",
                (f"{principal}:{operation}:{key}",),
            )
            prior = connection.execute(
                """SELECT request_sha256,response_status,response_body
                   FROM ontology.idempotency_records
                   WHERE principal=%s AND operation=%s AND idempotency_key=%s AND expires_at>now()""",
                (principal, operation, key),
            ).fetchone()
            if prior:
                if prior["request_sha256"] != digest:
                    raise ConflictError("idempotency_key_reused_with_different_payload")
                return IdempotentResult(prior["response_status"], prior["response_body"], True)
            token = _ACTIVE_CONNECTION.set(connection)
            try:
                status, payload = action()
                connection.execute(
                    """INSERT INTO ontology.idempotency_records
                       (principal,operation,idempotency_key,request_sha256,response_status,response_body)
                       VALUES(%s,%s,%s,%s,%s,%s)""",
                    (principal, operation, key, digest, status, Jsonb(payload)),
                )
            finally:
                _ACTIVE_CONNECTION.reset(token)
            return IdempotentResult(status, payload, False)

    def _source_record(self, connection: Connection, dish_id: UUID, evidence: dict[str, Any]) -> UUID:
        source = connection.execute(
            """INSERT INTO ontology.data_sources(source_code,source_type)
               VALUES(%s,'declared_evidence') ON CONFLICT(source_code) DO UPDATE SET enabled=true
               RETURNING id""",
            (evidence["source_code"],),
        ).fetchone()
        payload = json.dumps(
            {"dish_id": str(dish_id), "evidence": evidence},
            sort_keys=True,
            separators=(",", ":"),
        )
        checksum = hashlib.sha256(payload.encode()).hexdigest()
        record = connection.execute(
            """INSERT INTO ontology.source_records
               (source_id,provider_record_id,subject_dish_id,source_url,payload,payload_sha256)
               VALUES(%s,%s,%s,%s,%s,%s)
               ON CONFLICT(source_id,payload_sha256) DO UPDATE SET fetched_at=now()
               RETURNING id""",
            (source["id"], evidence.get("source_record_id"), dish_id,
             evidence.get("source_url"), Jsonb({"dish_id": str(dish_id), "evidence": evidence}), checksum),
        ).fetchone()
        return record["id"]

    def _assert(self, connection: Connection, dish_id: UUID, field_path: str,
                field: FieldValue | AliasInput | ClassMembershipInput | SimilarityInput) -> UUID:
        payload = field.model_dump(mode="json")
        assertion = connection.execute(
            """INSERT INTO ontology.assertions
               (dish_id,field_path,value,confidence,review_status,extraction_method,last_verified_at)
               VALUES(%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
            (dish_id, field_path, Jsonb(payload), field.confidence,
             str(getattr(field, "review_status", "provisional")),
             field.evidence[0].extraction_method,
             getattr(field, "last_verified_at", datetime.now().astimezone())),
        ).fetchone()
        for item in field.evidence:
            record_id = self._source_record(connection, dish_id, item.model_dump(mode="json"))
            connection.execute(
                "INSERT INTO ontology.assertion_evidence(assertion_id,source_record_id) VALUES(%s,%s)",
                (assertion["id"], record_id),
            )
        return assertion["id"]

    def _select_field(self, connection: Connection, dish_id: UUID, path: str,
                      field: FieldValue) -> UUID:
        assertion_id = self._assert(connection, dish_id, path, field)
        connection.execute(
            """INSERT INTO ontology.current_field_values(dish_id,field_path,assertion_id,selected_by)
               VALUES(%s,%s,%s,'api_write') ON CONFLICT(dish_id,field_path) DO UPDATE
               SET assertion_id=excluded.assertion_id,selected_by=excluded.selected_by,selected_at=now()""",
            (dish_id, path, assertion_id),
        )
        return assertion_id

    def _replace_aliases(self, connection: Connection, dish_id: UUID,
                         aliases: list[AliasInput]) -> None:
        connection.execute("DELETE FROM ontology.dish_aliases WHERE dish_id=%s", (dish_id,))
        for alias in aliases:
            path = f"aliases/{normalize_name(alias.name)}:{alias.language}:{alias.region_code or ''}"
            assertion_id = self._assert(connection, dish_id, path, alias)
            connection.execute(
                """INSERT INTO ontology.dish_aliases
                   (dish_id,alias_text,normalized_alias,language,region_code,alias_type,assertion_id)
                   VALUES(%s,%s,%s,%s,%s,%s,%s)""",
                (dish_id, alias.name, normalize_name(alias.name), alias.language,
                 alias.region_code, alias.alias_type, assertion_id),
            )

    def _replace_classes(self, connection: Connection, dish_id: UUID,
                         memberships: list[ClassMembershipInput]) -> None:
        connection.execute("DELETE FROM ontology.dish_class_memberships WHERE dish_id=%s", (dish_id,))
        for membership in memberships:
            path = f"class_memberships/{membership.class_code}:{membership.slot}:{membership.role}"
            assertion_id = self._assert(connection, dish_id, path, membership)
            connection.execute(
                """INSERT INTO ontology.dish_class_memberships
                   (dish_id,class_code,slot,role,assertion_id) VALUES(%s,%s,%s,%s,%s)""",
                (dish_id, membership.class_code, membership.slot, str(membership.role), assertion_id),
            )

    def create_dish(self, data: DishCreate) -> DishRecord:
        try:
            with self._connection() as connection:
                row = connection.execute(
                    """INSERT INTO ontology.dishes(canonical_name,normalized_name,locale)
                       VALUES(%s,%s,%s) RETURNING id""",
                    (data.canonical_name, normalize_name(data.canonical_name), data.locale),
                ).fetchone()
                dish_id = row["id"]
                if data.description:
                    self._select_field(connection, dish_id, "description", data.description)
                for path, field in data.fields.items():
                    self._select_field(connection, dish_id, path, field)
                self._replace_aliases(connection, dish_id, data.aliases)
                self._replace_classes(connection, dish_id, data.class_memberships)
                return self.get_dish(dish_id)
        except UniqueViolation as exc:
            raise ConflictError("canonical_name_exists") from exc
        except ForeignKeyViolation as exc:
            raise ConflictError("unknown_meal_class") from exc

    def update_dish(self, dish_id: UUID, patch: DishPatch) -> DishRecord:
        try:
            with self._connection() as connection:
                if not connection.execute("SELECT 1 FROM ontology.dishes WHERE id=%s", (dish_id,)).fetchone():
                    raise NotFoundError("dish_not_found")
                changes = patch.model_dump(exclude_unset=True)
                if "canonical_name" in changes:
                    connection.execute(
                        "UPDATE ontology.dishes SET canonical_name=%s,normalized_name=%s,updated_at=now() WHERE id=%s",
                        (patch.canonical_name, normalize_name(patch.canonical_name or ""), dish_id),
                    )
                if patch.description is not None:
                    self._select_field(connection, dish_id, "description", patch.description)
                if patch.fields is not None:
                    for path, field in patch.fields.items():
                        self._select_field(connection, dish_id, path, field)
                if patch.aliases is not None:
                    self._replace_aliases(connection, dish_id, patch.aliases)
                if patch.class_memberships is not None:
                    self._replace_classes(connection, dish_id, patch.class_memberships)
                connection.execute("UPDATE ontology.dishes SET updated_at=now() WHERE id=%s", (dish_id,))
                return self.get_dish(dish_id)
        except UniqueViolation as exc:
            raise ConflictError("canonical_name_exists") from exc
        except ForeignKeyViolation as exc:
            raise ConflictError("unknown_meal_class") from exc

    def _evidence(self, connection: Connection, assertion_id: UUID) -> list[dict[str, Any]]:
        rows = connection.execute(
            """SELECT ds.source_code,sr.provider_record_id AS source_record_id,sr.source_url,
                      a.extraction_method,ds.checked_at
               FROM ontology.assertions a
               JOIN ontology.assertion_evidence ae ON ae.assertion_id=a.id
               JOIN ontology.source_records sr ON sr.id=ae.source_record_id
               JOIN ontology.data_sources ds ON ds.id=sr.source_id WHERE a.id=%s""",
            (assertion_id,),
        ).fetchall()
        return [{k: value for k, value in row.items() if k != "checked_at" and value is not None}
                for row in rows]

    def get_dish(self, dish_id: UUID) -> DishRecord:
        with self._connection() as connection:
            dish = connection.execute("SELECT * FROM ontology.dishes WHERE id=%s", (dish_id,)).fetchone()
            if not dish:
                raise NotFoundError("dish_not_found")
            current = connection.execute(
                """SELECT c.field_path,a.id,a.value,a.confidence,a.review_status,a.last_verified_at
                   FROM ontology.current_field_values c JOIN ontology.assertions a ON a.id=c.assertion_id
                   WHERE c.dish_id=%s""",
                (dish_id,),
            ).fetchall()
            fields: dict[str, FieldValue] = {}
            description = None
            for item in current:
                field = FieldValue(value=item["value"].get("value", item["value"]),
                                   confidence=float(item["confidence"]),
                                   review_status=item["review_status"],
                                   evidence=self._evidence(connection, item["id"]),
                                   last_verified_at=item["last_verified_at"])
                if item["field_path"] == "description":
                    description = field
                else:
                    fields[item["field_path"]] = field
            alias_rows = connection.execute(
                """SELECT a.value FROM ontology.dish_aliases d
                   JOIN ontology.assertions a ON a.id=d.assertion_id WHERE d.dish_id=%s ORDER BY d.alias_text""",
                (dish_id,),
            ).fetchall()
            class_rows = connection.execute(
                """SELECT a.value FROM ontology.dish_class_memberships d
                   JOIN ontology.assertions a ON a.id=d.assertion_id WHERE d.dish_id=%s ORDER BY d.class_code,d.slot""",
                (dish_id,),
            ).fetchall()
            relation_rows = connection.execute(
                """SELECT a.value FROM ontology.dish_relationships r
                   JOIN ontology.assertions a ON a.id=r.assertion_id
                   WHERE r.subject_dish_id=%s ORDER BY r.score DESC""",
                (dish_id,),
            ).fetchall()
            image_rows = connection.execute(
                """SELECT i.cloudinary_public_id,i.cloudinary_asset_id,i.cloudinary_version,i.secure_url,
                          i.checksum_sha256,i.source_type,i.licence_code,i.attribution,d.review_status,d.is_primary
                   FROM ontology.dish_images d JOIN ontology.image_assets i ON i.id=d.image_asset_id
                   WHERE d.dish_id=%s ORDER BY d.is_primary DESC,i.created_at""",
                (dish_id,),
            ).fetchall()
            return DishRecord(
                id=dish["id"], canonical_name=dish["canonical_name"],
                normalized_name=dish["normalized_name"], locale=dish["locale"], status=dish["status"],
                description=description, aliases=[AliasInput.model_validate(row["value"]) for row in alias_rows],
                class_memberships=[ClassMembershipInput.model_validate(row["value"]) for row in class_rows],
                fields=fields, relationships=[SimilarityInput.model_validate(row["value"]) for row in relation_rows],
                images=[ImageRef.model_validate(row) for row in image_rows],
                created_at=dish["created_at"], updated_at=dish["updated_at"],
            )

    def get_by_name(self, name: str) -> DishRecord:
        normalized = normalize_name(name)
        with self._connection() as connection:
            row = connection.execute(
                """SELECT id FROM ontology.dishes WHERE normalized_name=%s
                   UNION ALL SELECT dish_id FROM ontology.dish_aliases WHERE normalized_alias=%s
                   LIMIT 1""", (normalized, normalized),
            ).fetchone()
            if not row:
                raise NotFoundError("dish_not_found")
            return self.get_dish(row["id"])

    def list_classes(self) -> list[dict[str, Any]]:
        with self._connection() as connection:
            return connection.execute(
                """SELECT class_code,display_name,slot,planning_role,parent_class_code,family_code
                   FROM ontology.meal_classes WHERE is_active ORDER BY slot,class_code"""
            ).fetchall()

    def dishes_by_class(self, class_code: str, role: str, limit: int) -> list[DishRecord]:
        with self._connection() as connection:
            rows = connection.execute(
                """SELECT d.id FROM ontology.dishes d JOIN ontology.dish_class_memberships m ON m.dish_id=d.id
                   JOIN ontology.assertions a ON a.id=m.assertion_id
                   WHERE m.class_code=%s AND m.role=%s AND a.review_status<>'rejected' AND d.status<>'retired'
                   ORDER BY a.confidence DESC,d.canonical_name LIMIT %s""",
                (class_code, role, limit),
            ).fetchall()
            return [self.get_dish(row["id"]) for row in rows]

    def enqueue(self, dish_id: UUID, kind: str, fields: list[str], priority: int, force: bool) -> dict[str, Any]:
        self.get_dish(dish_id)
        field_key = ",".join(sorted(set(fields))) or "all"
        dedupe = f"{kind}:{dish_id}:{field_key}"
        with self._connection() as connection:
            if force:
                connection.execute(
                    "UPDATE ontology.jobs SET status='dead',last_error_code='superseded_by_force',updated_at=now() "
                    "WHERE deduplication_key=%s AND status IN ('queued','running','retry')", (dedupe,)
                )
            row = connection.execute(
                """INSERT INTO ontology.jobs(dish_id,kind,deduplication_key,requested_fields,priority)
                   VALUES(%s,%s,%s,%s,%s)
                   ON CONFLICT(deduplication_key) WHERE status IN ('queued','running','retry')
                   DO UPDATE SET priority=greatest(ontology.jobs.priority,excluded.priority),updated_at=now()
                   RETURNING *""", (dish_id, kind, dedupe, list(sorted(set(fields))), priority),
            ).fetchone()
            return row

    def job_status(self, job_id: UUID) -> dict[str, Any]:
        with self._connection() as connection:
            row = connection.execute("SELECT * FROM ontology.jobs WHERE id=%s", (job_id,)).fetchone()
            if not row:
                raise NotFoundError("job_not_found")
            return row

    def enrichment_status(self, dish_id: UUID) -> dict[str, Any]:
        dish = self.get_dish(dish_id)
        with self._connection() as connection:
            jobs = connection.execute(
                "SELECT * FROM ontology.jobs WHERE dish_id=%s ORDER BY created_at DESC LIMIT 25", (dish_id,)
            ).fetchall()
        required = {"cuisine", "diet_type", "cooking_method", "texture", "region"}
        return {"dish_id": dish_id, "missing_fields": sorted(required-set(dish.fields)), "jobs": jobs}

    def save_relationship(self, dish_id: UUID, relation: SimilarityInput) -> DishRecord:
        if dish_id == relation.target_dish_id:
            raise ConflictError("self_relationship_not_allowed")
        self.get_dish(dish_id)
        self.get_dish(relation.target_dish_id)
        with self._connection() as connection:
            assertion_id = self._assert(connection, dish_id,
                                        f"relationships/{relation.relationship}:{relation.target_dish_id}", relation)
            connection.execute(
                """INSERT INTO ontology.dish_relationships
                   (subject_dish_id,predicate,object_dish_id,score,explanation_features,assertion_id)
                   VALUES(%s,%s,%s,%s,%s,%s) ON CONFLICT(subject_dish_id,predicate,object_dish_id)
                   DO UPDATE SET score=excluded.score,explanation_features=excluded.explanation_features,
                                 assertion_id=excluded.assertion_id""",
                (dish_id, str(relation.relationship), relation.target_dish_id, relation.score,
                 relation.explanation_features, assertion_id),
            )
            return self.get_dish(dish_id)

    def add_image(self, dish_id: UUID, image: ImageRef) -> DishRecord:
        self.get_dish(dish_id)
        with self._connection() as connection:
            asset = connection.execute(
                """INSERT INTO ontology.image_assets
                   (cloudinary_public_id,cloudinary_asset_id,cloudinary_version,secure_url,checksum_sha256,
                    source_type,licence_code,attribution,moderation_status)
                   VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)
                   ON CONFLICT(cloudinary_public_id) DO UPDATE SET cloudinary_asset_id=excluded.cloudinary_asset_id,
                    cloudinary_version=excluded.cloudinary_version,secure_url=excluded.secure_url,
                    moderation_status=excluded.moderation_status RETURNING id""",
                (image.cloudinary_public_id, image.cloudinary_asset_id, image.cloudinary_version,
                 image.secure_url, image.checksum_sha256, image.source_type, image.licence_code,
                 image.attribution, str(image.review_status)),
            ).fetchone()
            if image.is_primary:
                connection.execute("UPDATE ontology.dish_images SET is_primary=false WHERE dish_id=%s", (dish_id,))
            connection.execute(
                """INSERT INTO ontology.dish_images(dish_id,image_asset_id,is_primary,review_status)
                   VALUES(%s,%s,%s,%s) ON CONFLICT(dish_id,image_asset_id) DO UPDATE
                   SET is_primary=excluded.is_primary,review_status=excluded.review_status""",
                (dish_id, asset["id"], image.is_primary, str(image.review_status)),
            )
            return self.get_dish(dish_id)

    def submit_feedback(self, dish_id: UUID, feedback: FeedbackInput, principal: str) -> dict[str, Any]:
        self.get_dish(dish_id)
        with self._connection() as connection:
            return connection.execute(
                """INSERT INTO ontology.correction_submissions
                   (dish_id,field_path,proposed_value,reason,actor_reference,submitted_by_principal)
                   VALUES(%s,%s,%s,%s,%s,%s) RETURNING *""",
                (dish_id, feedback.field_path, Jsonb(feedback.proposed_value), feedback.reason,
                 feedback.actor_reference, principal),
            ).fetchone()

    def claim_jobs(self, worker_id: str, limit: int = 20) -> list[dict[str, Any]]:
        with self._connection() as connection:
            return connection.execute("SELECT * FROM ontology.claim_jobs(%s,%s)", (worker_id, limit)).fetchall()

    def finish_job(self, job_id: UUID, worker_id: str, outcome: str,
                   error_code: str | None = None) -> None:
        with self._connection() as connection:
            connection.execute("SELECT ontology.finish_job(%s,%s,%s,%s)",
                               (job_id, worker_id, outcome, error_code))

    def reconcile_jobs(self) -> int:
        with self._connection() as connection:
            row = connection.execute("SELECT ontology.reconcile_jobs() AS count").fetchone()
            return row["count"]
