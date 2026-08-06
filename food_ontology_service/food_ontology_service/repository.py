from __future__ import annotations

import hashlib
import json
import threading
import unicodedata
from copy import deepcopy
from dataclasses import dataclass
from datetime import timedelta
from typing import Any
from uuid import UUID, uuid4

from .models import DishCreate, DishPatch, DishRecord, FeedbackInput, ImageRef, SimilarityInput, utcnow


class ConflictError(ValueError):
    pass


class NotFoundError(LookupError):
    pass


def normalize_name(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


@dataclass
class IdempotentResult:
    status_code: int
    payload: dict[str, Any]
    replayed: bool


class MemoryRepository:
    """Reference adapter used by tests/local dev; production uses the matching SQL schema."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self.dishes: dict[UUID, DishRecord] = {}
        self.name_index: dict[str, UUID] = {}
        self.jobs: dict[UUID, dict[str, Any]] = {}
        self.feedback: list[dict[str, Any]] = []
        self.idempotency: dict[tuple[str, str, str], tuple[str, int, dict[str, Any]]] = {}

    def idempotent(self, principal: str, operation: str, key: str, body: Any, action) -> IdempotentResult:
        def request_shape(value: Any) -> Any:
            if isinstance(value, dict):
                return {k: request_shape(v) for k, v in value.items() if k != "last_verified_at"}
            if isinstance(value, list):
                return [request_shape(v) for v in value]
            return value

        digest = hashlib.sha256(
            json.dumps(request_shape(body), sort_keys=True, default=str).encode()
        ).hexdigest()
        identity = (principal, operation, key)
        with self._lock:
            prior = self.idempotency.get(identity)
            if prior:
                if prior[0] != digest:
                    raise ConflictError("idempotency_key_reused_with_different_payload")
                return IdempotentResult(prior[1], deepcopy(prior[2]), True)
            status_code, payload = action()
            self.idempotency[identity] = (digest, status_code, deepcopy(payload))
            return IdempotentResult(status_code, payload, False)

    def create_dish(self, data: DishCreate) -> DishRecord:
        with self._lock:
            normalized = normalize_name(data.canonical_name)
            if normalized in self.name_index:
                raise ConflictError("canonical_name_exists")
            now = utcnow()
            dish = DishRecord(
                id=uuid4(), canonical_name=data.canonical_name, normalized_name=normalized,
                locale=data.locale, description=data.description, aliases=data.aliases,
                class_memberships=data.class_memberships, fields=data.fields,
                created_at=now, updated_at=now,
            )
            self.dishes[dish.id] = dish
            self.name_index[normalized] = dish.id
            return deepcopy(dish)

    def update_dish(self, dish_id: UUID, patch: DishPatch) -> DishRecord:
        with self._lock:
            dish = self.dishes.get(dish_id)
            if not dish:
                raise NotFoundError("dish_not_found")
            changes = patch.model_dump(exclude_unset=True)
            if "canonical_name" in changes:
                new_name = changes["canonical_name"]
                normalized = normalize_name(new_name)
                owner = self.name_index.get(normalized)
                if owner and owner != dish_id:
                    raise ConflictError("canonical_name_exists")
                self.name_index.pop(dish.normalized_name, None)
                self.name_index[normalized] = dish_id
                changes["normalized_name"] = normalized
            updated = dish.model_copy(update={**changes, "updated_at": utcnow()})
            self.dishes[dish_id] = updated
            return deepcopy(updated)

    def get_dish(self, dish_id: UUID) -> DishRecord:
        dish = self.dishes.get(dish_id)
        if not dish:
            raise NotFoundError("dish_not_found")
        return deepcopy(dish)

    def get_by_name(self, name: str) -> DishRecord:
        dish_id = self.name_index.get(normalize_name(name))
        if not dish_id:
            for dish in self.dishes.values():
                if any(normalize_name(alias.name) == normalize_name(name) for alias in dish.aliases):
                    dish_id = dish.id
                    break
        if not dish_id:
            raise NotFoundError("dish_not_found")
        return self.get_dish(dish_id)

    def list_classes(self) -> list[dict[str, Any]]:
        rows: dict[tuple[str, str, str], dict[str, Any]] = {}
        for dish in self.dishes.values():
            for item in dish.class_memberships:
                rows[(item.class_code, item.slot, item.role)] = {
                    "class_code": item.class_code, "slot": item.slot, "planning_role": item.role
                }
        return sorted(rows.values(), key=lambda row: (row["slot"], row["class_code"]))

    def dishes_by_class(self, class_code: str, role: str, limit: int) -> list[DishRecord]:
        found = []
        for dish in self.dishes.values():
            if any(m.class_code == class_code and m.role == role and m.review_status != "rejected"
                   for m in dish.class_memberships):
                found.append(dish)
        found.sort(key=lambda dish: dish.canonical_name)
        return deepcopy(found[:limit])

    def enqueue(self, dish_id: UUID, kind: str, fields: list[str], priority: int, force: bool) -> dict[str, Any]:
        self.get_dish(dish_id)
        with self._lock:
            if not force:
                for job in self.jobs.values():
                    if job["dish_id"] == dish_id and job["kind"] == kind and job["status"] in {"queued", "running"}:
                        return deepcopy(job)
            job_id = uuid4()
            now = utcnow()
            job = {"id": job_id, "dish_id": dish_id, "kind": kind, "fields": fields,
                   "priority": priority, "status": "queued", "attempts": 0,
                   "next_attempt_at": now, "lease_expires_at": None, "created_at": now}
            self.jobs[job_id] = job
            return deepcopy(job)

    def job_status(self, job_id: UUID) -> dict[str, Any]:
        if job_id not in self.jobs:
            raise NotFoundError("job_not_found")
        return deepcopy(self.jobs[job_id])

    def enrichment_status(self, dish_id: UUID) -> dict[str, Any]:
        dish = self.get_dish(dish_id)
        jobs = [deepcopy(j) for j in self.jobs.values() if j["dish_id"] == dish_id]
        missing = [k for k in ("cuisine", "diet_type", "cooking_method", "texture", "region") if k not in dish.fields]
        return {"dish_id": dish_id, "missing_fields": missing, "jobs": jobs}

    def add_relationship(self, dish_id: UUID, relation: SimilarityInput) -> DishRecord:
        self.get_dish(relation.target_dish_id)
        dish = self.get_dish(dish_id)
        if dish_id == relation.target_dish_id:
            raise ConflictError("self_relationship_not_allowed")
        relationships = [r for r in dish.relationships if not (
            r.target_dish_id == relation.target_dish_id and r.relationship == relation.relationship
        )]
        relationships.append(relation)
        return self.update_dish(dish_id, DishPatch()).model_copy(update={"relationships": relationships})

    def save_relationship(self, dish_id: UUID, relation: SimilarityInput) -> DishRecord:
        dish = self.add_relationship(dish_id, relation)
        with self._lock:
            self.dishes[dish_id] = dish
        return deepcopy(dish)

    def add_image(self, dish_id: UUID, image: ImageRef) -> DishRecord:
        dish = self.get_dish(dish_id)
        images = [item.model_copy(update={"is_primary": False}) if image.is_primary else item
                  for item in dish.images if item.cloudinary_public_id != image.cloudinary_public_id]
        images.append(image)
        updated = dish.model_copy(update={"images": images, "updated_at": utcnow()})
        with self._lock:
            self.dishes[dish_id] = updated
        return deepcopy(updated)

    def submit_feedback(self, dish_id: UUID, feedback: FeedbackInput, principal: str) -> dict[str, Any]:
        self.get_dish(dish_id)
        item = {"id": uuid4(), "dish_id": dish_id, "principal": principal,
                **feedback.model_dump(), "status": "pending", "created_at": utcnow()}
        self.feedback.append(item)
        return deepcopy(item)
