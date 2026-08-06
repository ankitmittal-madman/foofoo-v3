from __future__ import annotations

import threading
import time
from collections import defaultdict
from collections.abc import Callable
from typing import Any

from fastapi import Request, Response


class MetricsRegistry:
    """Small Prometheus text registry with bounded route/status label cardinality."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._counters: dict[tuple[str, ...], float] = defaultdict(float)
        self._latency_sum: dict[tuple[str, ...], float] = defaultdict(float)
        self._latency_count: dict[tuple[str, ...], int] = defaultdict(int)

    def observe(self, method: str, route: str, status: int, seconds: float) -> None:
        labels = (method, route, str(status))
        with self._lock:
            self._counters[labels] += 1
            self._latency_sum[labels] += seconds
            self._latency_count[labels] += 1

    def render(self) -> str:
        lines = [
            "# HELP ontology_http_requests_total HTTP requests handled.",
            "# TYPE ontology_http_requests_total counter",
            "# HELP ontology_http_request_duration_seconds HTTP request latency.",
            "# TYPE ontology_http_request_duration_seconds summary",
        ]
        with self._lock:
            for labels in sorted(self._counters):
                method, route, status = labels
                encoded = f'method="{method}",route="{route}",status="{status}"'
                lines.append(
                    f"ontology_http_requests_total{{{encoded}}} {self._counters[labels]:g}"
                )
                lines.append(
                    "ontology_http_request_duration_seconds_sum"
                    f"{{{encoded}}} {self._latency_sum[labels]:.9f}"
                )
                lines.append(
                    "ontology_http_request_duration_seconds_count"
                    f"{{{encoded}}} {self._latency_count[labels]}"
                )
        return "\n".join(lines) + "\n"


def telemetry_middleware(registry: MetricsRegistry) -> Callable[..., Any]:
    async def middleware(request: Request, call_next: Callable[..., Any]) -> Response:
        started = time.perf_counter()
        response: Response = await call_next(request)
        route = getattr(request.scope.get("route"), "path", "unmatched")
        registry.observe(request.method, route, response.status_code, time.perf_counter() - started)
        trace_id = request.headers.get("x-request-id") or request.headers.get("x-trace-id")
        if trace_id:
            response.headers["x-request-id"] = trace_id[:200]
        return response

    return middleware
