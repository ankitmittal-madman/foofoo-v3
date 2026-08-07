"""Pipeline orchestration with immutable existing output and fail-safe fallback."""

from __future__ import annotations

import copy
import time
import uuid
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .config import Mode, Settings
from .lightfm_runtime import LightFMArtifactError, LightFMScorer, LightFMScoreTrace
from .observability import log_decision, record
from .policy import decide, existing_metrics
from .ranking import LocalReranker
from .registry import ModelRegistry
from .retrieval import CandidateRetriever
from .schemas import ConstraintCheck, RecommendationRequest, RecommendationResponse


def run(request: RecommendationRequest, settings: Settings | None = None) -> RecommendationResponse:
    settings = settings or Settings.from_env()
    trace_id = str(uuid.uuid4())
    started = time.perf_counter()
    existing = copy.deepcopy(request.existing_result)
    registry = ModelRegistry(settings)
    auxiliary = None
    constraints = ConstraintCheck(passed=True)
    debug: dict[str, Any] = {}
    timings = {"retrieval": 0.0, "reranking": 0.0, "selection": 0.0, "total": 0.0}
    retrieval_failures: dict[str, str] = {}
    candidate_count = 0
    model_trace: dict[str, Any] = {"lightfm": {"applied": False, "reason": "disabled"}}

    if settings.enabled:
        try:
            retrieval_started = time.perf_counter()
            retrieval = CandidateRetriever(settings).retrieve(request)
            timings["retrieval"] = (time.perf_counter() - retrieval_started) * 1000
            candidate_count = len(retrieval.candidates)
            retrieval_failures = retrieval.failures
            candidates = retrieval.candidates
            if settings.lightfm_enabled:
                try:
                    if not settings.lightfm_artifact_path:
                        raise LightFMArtifactError("artifact path is not configured")
                    scorer = LightFMScorer.load(
                        Path(settings.lightfm_artifact_path),
                        allow_synthetic=settings.lightfm_allow_synthetic,
                        allow_unpromoted=settings.lightfm_allow_unpromoted,
                    )
                    if scorer.synthetic_only and settings.mode is not Mode.SHADOW:
                        lightfm_trace = LightFMScoreTrace(
                            False,
                            0,
                            scorer.version,
                            "synthetic_artifact_shadow_only",
                        )
                    else:
                        candidates, lightfm_trace = scorer.apply(
                            candidates,
                            request,
                            blend_weight=settings.lightfm_weight,
                        )
                    model_trace["lightfm"] = asdict(lightfm_trace)
                except (LightFMArtifactError, ImportError, ValueError) as exc:
                    model_trace["lightfm"] = {
                        "applied": False,
                        "reason": type(exc).__name__,
                    }
            if not settings.use_local_reranker:
                raise RuntimeError("local reranker disabled and no governed model output available")
            rerank_started = time.perf_counter()
            auxiliary, rejected = LocalReranker().rank(candidates, request)
            timings["reranking"] = (time.perf_counter() - rerank_started) * 1000
            all_rejected = bool(retrieval.candidates) and not auxiliary.items
            constraints = ConstraintCheck(
                passed=not all_rejected,
                reasons=[reason for row in rejected for reason in row["reasons"]]
                if all_rejected
                else [],
            )
            debug = {
                "retrieval_sources": retrieval.sources,
                "retrieval_failures": retrieval.failures,
                "candidate_count": candidate_count,
                "rejected_candidates": rejected,
                "model_trace": model_trace,
            }
        except Exception as exc:  # auxiliary failure must never fail the product response
            constraints = ConstraintCheck(passed=False, reasons=["auxiliary_pipeline_error"])
            debug = {"error_type": type(exc).__name__}

    selection_started = time.perf_counter()
    decision = decide(existing, auxiliary, constraints, settings)
    timings["selection"] = (time.perf_counter() - selection_started) * 1000
    timings["total"] = (time.perf_counter() - started) * 1000
    old_metrics = existing_metrics(existing)
    scores = {
        "existing_quality": old_metrics["quality"],
        "auxiliary_quality": auxiliary.quality_score if auxiliary else 0.0,
        "improvement_delta": (
            auxiliary.quality_score - old_metrics["quality"] if auxiliary else 0.0
        ),
    }
    diversity = auxiliary.diversity_score if auxiliary else 0.0
    repetition_rate = 1.0 - diversity if auxiliary and len(auxiliary.items) > 1 else 0.0
    record(
        decision.reason,
        enabled=settings.enabled,
        selected_auxiliary=decision.code == "auxiliary",
        model_failed=bool(
            debug.get("error_type")
            or retrieval_failures
            or model_trace["lightfm"].get("reason")
            not in {"disabled", "scored", "unknown_household", "no_known_candidates"}
        ),
        constraint_violations=len(constraints.reasons),
        candidate_count=candidate_count,
        diversity_score=diversity,
        repetition_rate=repetition_rate,
        rerank_delta=scores["improvement_delta"],
        timings_ms=timings,
    )
    if settings.log_all:
        log_decision(
            trace_id=trace_id,
            mode=settings.mode,
            decision=decision.code,
            reason=decision.reason,
            scores=scores,
            existing_result=existing,
            auxiliary_result=auxiliary.model_dump() if auxiliary else None,
            timings_ms=timings,
            retrieval_failures=retrieval_failures,
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
        model_metadata={
            "models": registry.metadata(),
            "mode": settings.mode,
            "retrieval_failures": retrieval_failures,
            "model_trace": model_trace,
        },
        timings_ms={name: round(value, 3) for name, value in timings.items()},
        debug_trace=debug if request.debug else None,
    )
