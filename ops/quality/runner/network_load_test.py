"""Dependency-free load probe for signed Ghar or Aux recommendation endpoints.

The probe reports measurements by default. It becomes a pass/fail gate only when operators supply
ratified limits; the repository does not invent latency, error or throughput targets.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import hmac
import json
import statistics
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from collections.abc import Callable
from pathlib import Path
from typing import Any

REPORT_SCHEMA = "recommendation-load-report-v2"
SIGNATURE_HEADERS = {"ghar": "X-Ghar-Signature", "aux": "X-Aux-Signature"}


def percentile(values: list[float], pct: float) -> float:
    if not values:
        raise ValueError("at least one latency sample is required")
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, round((pct / 100) * (len(ordered) - 1)))]


def signed_headers(service: str, secret: str, raw: bytes, timestamp: int) -> dict[str, str]:
    try:
        header = SIGNATURE_HEADERS[service]
    except KeyError as exc:
        raise ValueError("service must be ghar or aux") from exc
    digest = hmac.new(
        secret.encode(), f"{timestamp}.".encode() + raw, hashlib.sha256
    ).hexdigest()
    return {
        "content-type": "application/json",
        header: f"t={timestamp},v1={digest}",
    }


def summarize(samples: list[tuple[float, int]], concurrency: int, elapsed_s: float) -> dict[str, Any]:
    if not samples or concurrency <= 0 or elapsed_s <= 0:
        raise ValueError("samples, positive concurrency and elapsed time are required")
    latencies = [latency for latency, _ in samples]
    statuses = Counter(status for _, status in samples)
    errors = sum(count for status, count in statuses.items() if status == 0 or status >= 400)
    return {
        "requests": len(samples),
        "concurrency": concurrency,
        "errors": errors,
        "error_rate": round(errors / len(samples), 6),
        "status_counts": {str(key): statuses[key] for key in sorted(statuses)},
        "throughput_rps": round(len(samples) / elapsed_s, 3),
        "p50_ms": round(percentile(latencies, 50), 2),
        "p95_ms": round(percentile(latencies, 95), 2),
        "p99_ms": round(percentile(latencies, 99), 2),
        "mean_ms": round(statistics.mean(latencies), 2),
        "max_ms": round(max(latencies), 2),
    }


def run(
    url: str,
    secret: str,
    payload: dict[str, Any],
    requests: int,
    concurrency: int,
    *,
    service: str = "ghar",
    timeout_s: float = 10,
    opener: Callable[..., Any] = urllib.request.urlopen,
) -> dict[str, Any]:
    if requests <= 0 or concurrency <= 0 or timeout_s <= 0:
        raise ValueError("requests, concurrency and timeout must be positive")
    raw = json.dumps(payload, separators=(",", ":")).encode()

    def call(_: int) -> tuple[float, int]:
        timestamp = int(time.time())
        request = urllib.request.Request(
            url,
            data=raw,
            method="POST",
            headers=signed_headers(service, secret, raw, timestamp),
        )
        started = time.perf_counter()
        try:
            with opener(request, timeout=timeout_s) as response:
                status = int(response.status)
                response.read()
        except urllib.error.HTTPError as error:
            status = error.code
        except (urllib.error.URLError, TimeoutError):
            status = 0
        return (time.perf_counter() - started) * 1000, status

    started = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as pool:
        samples = list(pool.map(call, range(requests)))
    metrics = summarize(samples, concurrency, time.perf_counter() - started)
    parsed_url = urllib.parse.urlparse(url)
    origin = parsed_url.hostname or "unknown"
    if parsed_url.port is not None:
        origin = f"{origin}:{parsed_url.port}"
    return {
        "schema_version": REPORT_SCHEMA,
        "service": service,
        "url_origin": origin,
        "metrics": metrics,
    }


def assess(
    report: dict[str, Any],
    *,
    max_p95_ms: float | None = None,
    max_error_rate: float | None = None,
    min_throughput_rps: float | None = None,
    baseline: dict[str, Any] | None = None,
    max_p95_regression_pct: float | None = None,
) -> dict[str, Any]:
    """Apply only explicitly supplied targets and return each measured gate."""
    metrics = report.get("metrics")
    if not isinstance(metrics, dict):
        raise ValueError("report metrics are required")
    gates: dict[str, bool] = {}
    targets: dict[str, float] = {}
    if max_p95_ms is not None:
        targets["max_p95_ms"] = max_p95_ms
        gates["p95_latency"] = float(metrics["p95_ms"]) <= max_p95_ms
    if max_error_rate is not None:
        targets["max_error_rate"] = max_error_rate
        gates["error_rate"] = float(metrics["error_rate"]) <= max_error_rate
    if min_throughput_rps is not None:
        targets["min_throughput_rps"] = min_throughput_rps
        gates["throughput"] = float(metrics["throughput_rps"]) >= min_throughput_rps
    if max_p95_regression_pct is not None:
        if baseline is None or not isinstance(baseline.get("metrics"), dict):
            raise ValueError("a baseline report is required for a regression target")
        baseline_p95 = float(baseline["metrics"]["p95_ms"])
        if baseline_p95 <= 0:
            raise ValueError("baseline p95 must be positive")
        targets["max_p95_regression_pct"] = max_p95_regression_pct
        regression = 100 * (float(metrics["p95_ms"]) - baseline_p95) / baseline_p95
        gates["p95_regression"] = regression <= max_p95_regression_pct
    return {
        **report,
        "evaluation": {
            "mode": "gated" if gates else "measurement_only",
            "targets": targets,
            "gates": gates,
            "passed": all(gates.values()) if gates else None,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8000/v1/recommendations")
    parser.add_argument("--service", choices=sorted(SIGNATURE_HEADERS), default="ghar")
    parser.add_argument("--secret", required=True)
    parser.add_argument("--payload", type=Path, required=True)
    parser.add_argument("--requests", type=int, default=500)
    parser.add_argument("--concurrency", type=int, default=20)
    parser.add_argument("--timeout-seconds", type=float, default=10)
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--max-p95-ms", type=float)
    parser.add_argument("--max-error-rate", type=float)
    parser.add_argument("--min-throughput-rps", type=float)
    parser.add_argument("--max-p95-regression-pct", type=float)
    args = parser.parse_args()
    payload = json.loads(args.payload.read_text(encoding="utf-8"))
    baseline = json.loads(args.baseline.read_text(encoding="utf-8")) if args.baseline else None
    report = assess(
        run(
            args.url,
            args.secret,
            payload,
            args.requests,
            args.concurrency,
            service=args.service,
            timeout_s=args.timeout_seconds,
        ),
        max_p95_ms=args.max_p95_ms,
        max_error_rate=args.max_error_rate,
        min_throughput_rps=args.min_throughput_rps,
        baseline=baseline,
        max_p95_regression_pct=args.max_p95_regression_pct,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    passed = report["evaluation"]["passed"]
    return 0 if passed is not False else 1


if __name__ == "__main__":
    raise SystemExit(main())
