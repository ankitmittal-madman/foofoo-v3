from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from food_ontology_service.worker import FieldFreshness, OntologyWorker, enrichment_priority


class Queue:
    def __init__(self, jobs):
        self.jobs = jobs
        self.finished = []
        self.reconciled = 0

    def reconcile_jobs(self):
        self.reconciled += 1
        return 0

    def claim_jobs(self, worker_id, limit=20):
        return self.jobs[:limit]

    def finish_job(self, job_id, worker_id, outcome, error_code=None):
        self.finished.append((job_id, worker_id, outcome, error_code))


def test_worker_completes_reviews_retries_and_dead_letters():
    jobs = [
        {"id": uuid4(), "kind": "enrich", "attempts": 1, "max_attempts": 3},
        {"id": uuid4(), "kind": "classify", "attempts": 1, "max_attempts": 3},
        {"id": uuid4(), "kind": "image", "attempts": 1, "max_attempts": 3},
        {"id": uuid4(), "kind": "publish", "attempts": 3, "max_attempts": 3},
        {"id": uuid4(), "kind": "unknown", "attempts": 1, "max_attempts": 3},
    ]
    queue = Queue(jobs)

    def fail(_job):
        raise TimeoutError("provider timeout")

    worker = OntologyWorker(
        queue,
        "worker-1",
        {
            "enrich": lambda _job: "complete",
            "classify": lambda _job: "review",
            "image": fail,
            "publish": fail,
        },
    )
    report = worker.run_once()
    assert report.claimed == 5
    assert (report.completed, report.review, report.retried, report.dead, report.unsupported) == (
        1,
        1,
        1,
        2,
        1,
    )
    assert queue.reconciled == 1
    assert [item[2] for item in queue.finished] == ["complete", "review", "retry", "dead", "dead"]


def test_incremental_priority_skips_stable_fields_and_prioritizes_missing_safety():
    now = datetime(2026, 8, 6, tzinfo=UTC)
    stable = FieldFreshness("description", 0.95, now - timedelta(days=20), accepted=True)
    missing_safety = FieldFreshness(
        "allergens", None, None, accepted=False, required_for_page=True, safety_critical=True
    )
    stale = FieldFreshness("nutrition", 0.9, now - timedelta(days=200), accepted=True)
    assert enrichment_priority(stable, now) is None
    assert enrichment_priority(missing_safety, now) == 100
    assert enrichment_priority(stale, now) == 35
