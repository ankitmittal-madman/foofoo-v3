from __future__ import annotations

import hashlib
import hmac

import pytest

from ops.quality.runner.network_load_test import assess, signed_headers, summarize


def report(*, p95: float = 100, errors: float = 0, throughput: float = 50) -> dict:
    return {
        "metrics": {
            "p95_ms": p95,
            "error_rate": errors,
            "throughput_rps": throughput,
        }
    }


def test_signer_uses_service_specific_header_and_exact_raw_body():
    raw = b'{"dish":"Poha"}'
    headers = signed_headers("aux", "secret", raw, 100)
    expected = hmac.new(b"secret", b"100." + raw, hashlib.sha256).hexdigest()

    assert headers["X-Aux-Signature"] == f"t=100,v1={expected}"
    assert "X-Ghar-Signature" not in headers


def test_summary_counts_transport_failures_and_http_errors():
    metrics = summarize([(10, 200), (20, 503), (30, 0), (40, 200)], 2, 1)

    assert metrics["errors"] == 2
    assert metrics["error_rate"] == 0.5
    assert metrics["status_counts"] == {"0": 1, "200": 2, "503": 1}
    assert metrics["throughput_rps"] == 4


def test_measurement_only_mode_never_invents_a_pass_threshold():
    result = assess(report())

    assert result["evaluation"] == {
        "mode": "measurement_only",
        "targets": {},
        "gates": {},
        "passed": None,
    }


def test_explicit_absolute_and_baseline_relative_targets_are_enforced():
    result = assess(
        report(p95=125, errors=0.01, throughput=40),
        max_p95_ms=130,
        max_error_rate=0.005,
        min_throughput_rps=35,
        baseline=report(p95=100),
        max_p95_regression_pct=20,
    )

    assert result["evaluation"]["gates"] == {
        "p95_latency": True,
        "error_rate": False,
        "throughput": True,
        "p95_regression": False,
    }
    assert result["evaluation"]["passed"] is False


def test_relative_target_requires_a_real_baseline():
    with pytest.raises(ValueError, match="baseline report"):
        assess(report(), max_p95_regression_pct=10)


@pytest.mark.parametrize("service", ["unknown", "edge"])
def test_unknown_signature_service_fails_closed(service):
    with pytest.raises(ValueError, match="ghar or aux"):
        signed_headers(service, "secret", b"{}", 100)
