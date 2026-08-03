"""
Phase 12 — Performance benchmark (in-process, real).

Drives the FastAPI app through the TestClient and measures end-to-end latency of the RE's compute
path (/v1/recommendations) plus the cheap /v1/meta, then reports p50/p95/p99/max and a cold-vs-warm
comparison. This is an in-process micro-benchmark, NOT a distributed load test — it measures the
engine's own latency without network, so numbers are a floor, not a production SLA. That limitation
is stated in the emitted metrics so the report never overclaims.

Targets: the repository documents no numeric latency SLA discoverable by this script, so results are
emitted as INFORMATIONAL with a conservative default warn threshold (p99 <= 1500 ms for the
in-process compute path). Override via GHAR_PERF_P99_MS.
"""

from __future__ import annotations

import json
import os
import statistics
import sys
import time
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
for _p in (_REPO_ROOT, _REPO_ROOT / "ghar_re_service"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))


def _percentile(values: list[float], pct: float) -> float:
    """Return the `pct` percentile (0-100) of `values` using nearest-rank on a sorted copy."""
    if not values:
        return 0.0
    s = sorted(values)
    k = max(0, min(len(s) - 1, int(round((pct / 100.0) * (len(s) - 1)))))
    return s[k]


def run(iterations: int = 200) -> dict:
    """Benchmark /v1/meta and /v1/recommendations for `iterations` calls; return a metrics dict."""
    import hashlib
    import hmac

    from fastapi.testclient import TestClient
    from ghar_re_service.providers import DEV_INSECURE_SECRET

    from ghar_re_core import fixtures as fx
    from ghar_re_service import auth, main

    hh = next(h for h in fx.HOUSEHOLDS if h["id_key"] == "couple_mumbai_mh")
    payload = {"household": {k: v for k, v in hh.items() if k != "id_key"},
               "context": {"slot": "dinner", "season": "monsoon",
                           "weather": {"is_raining": True, "temp_c": 27}}}
    raw = json.dumps(payload).encode()

    def _headers() -> dict:
        ts = int(time.time())
        sig = hmac.new(DEV_INSECURE_SECRET.encode(), f"{ts}.".encode() + raw, hashlib.sha256).hexdigest()
        return {"content-type": "application/json", auth.SIGNATURE_HEADER: f"t={ts},v1={sig}"}

    results: dict = {"disclaimer": "in-process TestClient micro-benchmark; not a network/load test",
                     "iterations": iterations, "endpoints": {}}
    with TestClient(main.app) as c:
        # cold call (first compute after startup) vs warm
        t0 = time.perf_counter()
        c.post("/v1/recommendations", content=raw, headers=_headers())
        results["cold_start_ms"] = round((time.perf_counter() - t0) * 1000, 2)

        for name, fn in [
            ("/v1/meta", lambda: c.get("/v1/meta")),
            ("/v1/recommendations", lambda: c.post("/v1/recommendations", content=raw, headers=_headers())),
        ]:
            samples: list[float] = []
            errors = 0
            for _ in range(iterations):
                t = time.perf_counter()
                r = fn()
                samples.append((time.perf_counter() - t) * 1000)
                if r.status_code >= 400:
                    errors += 1
            results["endpoints"][name] = {
                "count": len(samples), "errors": errors,
                "p50_ms": round(_percentile(samples, 50), 2),
                "p95_ms": round(_percentile(samples, 95), 2),
                "p99_ms": round(_percentile(samples, 99), 2),
                "max_ms": round(max(samples), 2),
                "mean_ms": round(statistics.mean(samples), 2),
            }

    warn_p99 = float(os.environ.get("GHAR_PERF_P99_MS", "1500"))
    compute = results["endpoints"].get("/v1/recommendations", {})
    results["warn_threshold_p99_ms"] = warn_p99
    results["within_threshold"] = compute.get("p99_ms", 0) <= warn_p99
    results["status"] = "pass" if results["within_threshold"] else "warn"
    return results


if __name__ == "__main__":
    out = run(int(os.environ.get("GHAR_PERF_ITERS", "200")))
    print(json.dumps(out, indent=2))
