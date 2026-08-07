"""PII-minimized structured logs and process-local metrics namespace."""

from __future__ import annotations

import json
import logging
import threading
from collections import Counter
from typing import Any

LOGGER = logging.getLogger("foofoo.aux_re")
LOGGER.setLevel(logging.INFO)
_LOCK = threading.Lock()
_COUNTERS: Counter[str] = Counter()
_TOTALS: Counter[str] = Counter()


def record(
    decision: str,
    *,
    enabled: bool,
    selected_auxiliary: bool,
    model_failed: bool,
    constraint_violations: int,
    candidate_count: int,
    diversity_score: float,
    repetition_rate: float,
    rerank_delta: float,
    timings_ms: dict[str, float],
    experiment_variant: str = "not_enrolled",
) -> None:
    with _LOCK:
        _COUNTERS["requests_total"] += 1
        _COUNTERS["auxiliary_enabled_total"] += int(enabled)
        _COUNTERS["auxiliary_selected_total"] += int(selected_auxiliary)
        _COUNTERS["fallback_total"] += int(enabled and not selected_auxiliary)
        _COUNTERS["model_failure_total"] += int(model_failed)
        _COUNTERS["constraint_violation_total"] += constraint_violations
        _COUNTERS["comparison_win_total"] += int(selected_auxiliary)
        _COUNTERS["comparison_loss_total"] += int(enabled and not selected_auxiliary)
        _COUNTERS[f"decision.{decision}"] += 1
        _COUNTERS[f"experiment.{experiment_variant}"] += 1
        _TOTALS["candidate_count_milli"] += round(candidate_count * 1000)
        _TOTALS["diversity_milli"] += round(diversity_score * 1000)
        _TOTALS["repetition_milli"] += round(repetition_rate * 1000)
        _TOTALS["rerank_delta_milli"] += round(rerank_delta * 1000)
        for name, value in timings_ms.items():
            _TOTALS[f"latency.{name}.microseconds"] += round(value * 1000)


def metrics() -> dict[str, int | float]:
    with _LOCK:
        output: dict[str, int | float] = dict(_COUNTERS)
        requests = max(1, _COUNTERS["requests_total"])
        output.update(
            {
                "candidate_recall_size_avg": _TOTALS["candidate_count_milli"] / requests / 1000,
                "diversity_score_avg": _TOTALS["diversity_milli"] / requests / 1000,
                "repetition_rate_avg": _TOTALS["repetition_milli"] / requests / 1000,
                "rerank_delta_avg": _TOTALS["rerank_delta_milli"] / requests / 1000,
                "fallback_rate": _COUNTERS["fallback_total"] / requests,
                "auxiliary_win_rate": _COUNTERS["comparison_win_total"] / requests,
                "model_failure_rate": _COUNTERS["model_failure_total"] / requests,
                "constraint_violations_per_request": _COUNTERS["constraint_violation_total"]
                / requests,
            }
        )
        for key, value in _TOTALS.items():
            if key.startswith("latency."):
                output[key.removesuffix(".microseconds") + "_ms_avg"] = value / requests / 1000
        return output


def log_decision(**fields: Any) -> None:
    LOGGER.info(json.dumps({"namespace": "aux_rec", **fields}, sort_keys=True, default=str))


def record_feedback(*, stored: bool, event_type: str) -> None:
    with _LOCK:
        _COUNTERS["feedback_received_total"] += 1
        _COUNTERS["feedback_stored_total"] += int(stored)
        _COUNTERS["feedback_duplicate_total"] += int(not stored)
        _COUNTERS[f"feedback.{event_type}"] += 1
