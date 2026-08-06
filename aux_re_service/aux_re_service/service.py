"""Pipeline orchestration with immutable existing output and fail-safe fallback."""

from __future__ import annotations

import copy
import uuid
from typing import Any

from .config import Settings
from .observability import log_decision, record
from .policy import decide, existing_metrics
from .ranking import LocalReranker
from .registry import ModelRegistry
from .retrieval import CandidateRetriever
from .schemas import ConstraintCheck, RecommendationRequest, RecommendationResponse


def run(request: RecommendationRequest, settings: Settings | None = None) -> RecommendationResponse:
    settings = settings or Settings.from_env()
    trace_id = str(uuid.uuid4())
    existing = copy.deepcopy(request.existing_result)
    registry = ModelRegistry(settings)
    auxiliary = None
    constraints = ConstraintCheck(passed=True)
    debug: dict[str, Any] = {}

    if settings.enabled:
        try:
            candidates, sources = CandidateRetriever(settings).retrieve(request)
            if not settings.use_local_reranker:
                raise RuntimeError("local reranker disabled and no governed model output available")
            auxiliary, rejected = LocalReranker().rank(candidates, request)
            all_rejected = bool(candidates) and not auxiliary.items
            constraints = ConstraintCheck(
                passed=not all_rejected,
                reasons=[reason for row in rejected for reason in row["reasons"]]
                if all_rejected
                else [],
            )
            debug = {
                "retrieval_sources": sources,
                "candidate_count": len(candidates),
                "rejected_candidates": rejected,
            }
        except Exception as exc:  # auxiliary failure must never fail the product response
            constraints = ConstraintCheck(passed=False, reasons=["auxiliary_pipeline_error"])
            debug = {"error_type": type(exc).__name__}

    decision = decide(existing, auxiliary, constraints, settings)
    old_metrics = existing_metrics(existing)
    scores = {
        "existing_quality": old_metrics["quality"],
        "auxiliary_quality": auxiliary.quality_score if auxiliary else 0.0,
        "improvement_delta": (
            auxiliary.quality_score - old_metrics["quality"] if auxiliary else 0.0
        ),
    }
    record(decision.reason)
    if settings.log_all:
        log_decision(
            trace_id=trace_id,
            mode=settings.mode,
            decision=decision.code,
            reason=decision.reason,
            scores=scores,
            existing_result=existing,
            auxiliary_result=auxiliary.model_dump() if auxiliary else None,
        )
    return RecommendationResponse(
        trace_id=trace_id,
        existing_result=existing,
        auxiliary_result=auxiliary,
        selected_result=decision.selected,
        decision=decision.code,
        decision_reason=decision.reason,
        scores=scores,
        constraint_checks=constraints,
        model_metadata={"models": registry.metadata(), "mode": settings.mode},
        debug_trace=debug if request.debug else None,
    )
