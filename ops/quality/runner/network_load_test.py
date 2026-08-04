"""Dependency-free concurrent HTTP load test for the signed recommendation service."""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import hmac
import json
import statistics
import time
import urllib.error
import urllib.request


def percentile(values: list[float], pct: float) -> float:
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, round((pct / 100) * (len(ordered) - 1)))]


def run(url: str, secret: str, payload: dict, requests: int, concurrency: int) -> dict:
    raw = json.dumps(payload, separators=(",", ":")).encode()

    def call(_: int) -> tuple[float, int]:
        timestamp = int(time.time())
        signature = hmac.new(
            secret.encode(), f"{timestamp}.".encode() + raw, hashlib.sha256
        ).hexdigest()
        request = urllib.request.Request(
            url,
            data=raw,
            method="POST",
            headers={
                "content-type": "application/json",
                "X-Ghar-Signature": f"t={timestamp},v1={signature}",
            },
        )
        started = time.perf_counter()
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                status = response.status
                response.read()
        except urllib.error.HTTPError as error:
            status = error.code
        return (time.perf_counter() - started) * 1000, status

    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as pool:
        samples = list(pool.map(call, range(requests)))
    latencies = [latency for latency, _ in samples]
    errors = sum(1 for _, status in samples if status >= 400)
    return {
        "requests": requests,
        "concurrency": concurrency,
        "errors": errors,
        "error_rate": round(errors / requests, 6),
        "p50_ms": round(percentile(latencies, 50), 2),
        "p95_ms": round(percentile(latencies, 95), 2),
        "p99_ms": round(percentile(latencies, 99), 2),
        "mean_ms": round(statistics.mean(latencies), 2),
        "max_ms": round(max(latencies), 2),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8000/v1/recommendations")
    parser.add_argument("--secret", required=True)
    parser.add_argument("--payload", required=True, help="request JSON file")
    parser.add_argument("--requests", type=int, default=500)
    parser.add_argument("--concurrency", type=int, default=20)
    parser.add_argument("--max-p95-ms", type=float, default=3000)
    parser.add_argument("--max-error-rate", type=float, default=0.01)
    args = parser.parse_args()
    with open(args.payload) as handle:
        payload = json.load(handle)
    result = run(args.url, args.secret, payload, args.requests, args.concurrency)
    print(json.dumps(result, indent=2))
    return (
        0
        if result["p95_ms"] <= args.max_p95_ms and result["error_rate"] <= args.max_error_rate
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
