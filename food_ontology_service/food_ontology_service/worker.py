from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol
from uuid import UUID

logger = logging.getLogger("food_ontology.worker")


class JobRepository(Protocol):
    def claim_jobs(self, worker_id: str, limit: int = 20) -> list[dict[str, Any]]: ...
    def finish_job(
        self, job_id: UUID, worker_id: str, outcome: str, error_code: str | None = None
    ) -> None: ...
    def reconcile_jobs(self) -> int: ...


JobHandler = Callable[[dict[str, Any]], str | None]


@dataclass(frozen=True)
class WorkerReport:
    claimed: int = 0
    completed: int = 0
    review: int = 0
    retried: int = 0
    dead: int = 0
    unsupported: int = 0


class OntologyWorker:
    """One bounded queue iteration. Provider/network work is supplied as injected handlers."""

    def __init__(
        self,
        repository: JobRepository,
        worker_id: str,
        handlers: dict[str, JobHandler],
        batch_size: int = 20,
    ):
        if len(worker_id.strip()) < 3:
            raise ValueError("worker_id_required")
        self.repository = repository
        self.worker_id = worker_id
        self.handlers = handlers
        self.batch_size = max(1, min(batch_size, 100))

    def run_once(self, reconcile: bool = True) -> WorkerReport:
        if reconcile:
            self.repository.reconcile_jobs()
        jobs = self.repository.claim_jobs(self.worker_id, self.batch_size)
        counts = {"completed": 0, "review": 0, "retried": 0, "dead": 0, "unsupported": 0}
        for job in jobs:
            handler = self.handlers.get(str(job["kind"]))
            if handler is None:
                self.repository.finish_job(
                    job["id"], self.worker_id, "dead", "unsupported_job_kind"
                )
                counts["dead"] += 1
                counts["unsupported"] += 1
                continue
            try:
                outcome = handler(job) or "complete"
                if outcome not in {"complete", "review"}:
                    raise ValueError("handler_invalid_outcome")
                self.repository.finish_job(job["id"], self.worker_id, outcome)
                counts["completed" if outcome == "complete" else "review"] += 1
            except Exception as exc:
                attempts = int(job.get("attempts", 1))
                max_attempts = int(job.get("max_attempts", 8))
                terminal = attempts >= max_attempts
                outcome = "dead" if terminal else "retry"
                error_code = type(exc).__name__.lower()[:120]
                self.repository.finish_job(job["id"], self.worker_id, outcome, error_code)
                counts["dead" if terminal else "retried"] += 1
                logger.warning(
                    "ontology_job_failed",
                    extra={
                        "job_id": str(job["id"]),
                        "kind": str(job["kind"]),
                        "outcome": outcome,
                        "error_code": error_code,
                    },
                )
        return WorkerReport(claimed=len(jobs), **counts)


@dataclass(frozen=True)
class FieldFreshness:
    field_path: str
    confidence: float | None
    last_verified_at: datetime | None
    accepted: bool
    required_for_page: bool = False
    safety_critical: bool = False


DEFAULT_FRESHNESS_DAYS = {
    "aliases": 180,
    "region": 180,
    "nutrition": 180,
    "description": 365,
    "recipe": 365,
    "image": 365,
}


def enrichment_priority(field: FieldFreshness, now: datetime | None = None) -> int | None:
    """Return 0–100 when a field is due, or None when stable work should be skipped."""
    current = now or datetime.now(UTC)
    root = field.field_path.split("/", 1)[0]
    max_age = DEFAULT_FRESHNESS_DAYS.get(root, 365)
    age_days = (
        (current - field.last_verified_at).days
        if field.last_verified_at is not None
        else max_age + 1
    )
    stale = age_days >= max_age
    low_confidence = field.confidence is None or field.confidence < 0.85
    if field.accepted and not stale and not low_confidence:
        return None
    score = 20
    if field.last_verified_at is None:
        score += 25
    if low_confidence:
        score += 20
    if stale:
        score += 15
    if field.required_for_page:
        score += 10
    if field.safety_critical:
        score += 10
    return min(100, score)
