"""
Phase 13 (+ Phase 6 negative-path) — API security and abuse testing.

Exercises the auth + input boundary of the RE service through the real HTTP stack:

  * unsigned / malformed / stale / tampered signatures -> 401 (fail-closed),
  * signature check runs BEFORE body parsing (raw-byte HMAC),
  * malformed / missing / oversized payloads -> clean 4xx, never a 500,
  * unknown fields tolerated (additive/open contract),
  * rate limiting sheds a flood with 429 + Retry-After, and (per main.py's documented ordering)
    an unsigned over-limit request returns 429, not 401 — the limiter is the outermost layer.

No secret value is ever printed; only the dev test secret (already public in the repo) is used.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time

import pytest

from ghar_re_service import auth

VALID_HH = {
    "q1_household_type": "single", "q2_working_professionals": 1, "q3_home_state": "Delhi",
    "q4_current_city": "New Delhi", "q5_diet": "veg", "q7_veg_days": [], "q8_is_jain": False,
    "q9_allergies": [], "q11_conditions": [], "q12_member_ages": [{"role": "self", "age": 30}], "q13_who_cooks": "self",
    "q14_eat_out_per_week": 2, "q15_objective": "healthy_living",
}
CTX = {"slot": "dinner", "season": "summer", "weather": {"is_raining": False, "temp_c": 33}}
BODY = {"household": VALID_HH, "context": CTX}


def _sig(secret: str, ts: int, raw: bytes) -> str:
    """Compute the X-Ghar-Signature header value for the given timestamp and raw body bytes."""
    mac = hmac.new(secret.encode(), f"{ts}.".encode() + raw, hashlib.sha256).hexdigest()
    return f"t={ts},v1={mac}"


def test_unsigned_request_rejected_401(client):
    r = client.post("/v1/recommendations", json=BODY)
    assert r.status_code == 401
    assert r.json()["error"] == "unauthorized"


def test_missing_signature_header_401(client):
    raw = json.dumps(BODY).encode()
    r = client.post("/v1/recommendations", content=raw,
                    headers={"content-type": "application/json"})
    assert r.status_code == 401
    assert r.json()["detail"] == "missing_signature"


def test_malformed_signature_401(client):
    raw = json.dumps(BODY).encode()
    r = client.post("/v1/recommendations", content=raw,
                    headers={"content-type": "application/json",
                             auth.SIGNATURE_HEADER: "not-a-valid-signature"})
    assert r.status_code == 401
    assert r.json()["detail"] in {"malformed_signature", "invalid_signature"}


def test_stale_signature_rejected_401(client, secret):
    raw = json.dumps(BODY).encode()
    old_ts = int(time.time()) - 10_000  # far outside max_skew
    r = client.post("/v1/recommendations", content=raw,
                    headers={"content-type": "application/json",
                             auth.SIGNATURE_HEADER: _sig(secret, old_ts, raw)})
    assert r.status_code == 401
    assert r.json()["detail"] == "stale_signature"


def test_tampered_body_rejected_401(client, secret):
    raw = json.dumps(BODY).encode()
    ts = int(time.time())
    header = _sig(secret, ts, raw)              # sign the clean bytes
    r = client.post("/v1/recommendations", content=raw + b"  ",  # send altered bytes
                    headers={"content-type": "application/json", auth.SIGNATURE_HEADER: header})
    assert r.status_code == 401
    assert r.json()["detail"] == "invalid_signature"


def test_missing_required_field_is_422_not_500(signed_post):
    bad = {"household": {k: v for k, v in VALID_HH.items() if k != "q5_diet"}, "context": CTX}
    r = signed_post("/v1/recommendations", bad)
    assert r.status_code == 422
    assert r.json()["error"] == "invalid_request"


def test_empty_body_is_clean_4xx_not_500(signed_post):
    r = signed_post("/v1/recommendations", {})
    assert r.status_code in {422}, r.text
    assert r.status_code != 500


def test_unknown_fields_tolerated(signed_post):
    payload = {**BODY, "telemetry": {"client": "qa"}, "future_top": 1}
    payload = {**payload, "household": {**VALID_HH, "q99_future": "x"}}
    r = signed_post("/v1/recommendations", payload)
    assert r.status_code == 200, r.text


def test_large_payload_does_not_500(signed_post):
    """A large but well-formed payload (fat unknown field) must not crash the service."""
    payload = {**BODY, "junk": ["x" * 100 for _ in range(5000)]}
    r = signed_post("/v1/recommendations", payload)
    assert r.status_code in {200, 413, 422}, r.text
    assert r.status_code != 500


def test_meta_requires_no_auth_but_is_reachable(client):
    """/v1/meta is unauthenticated by design (RE-DOC-10 §4) — must be reachable without a signature."""
    r = client.get("/v1/meta")
    assert r.status_code == 200


def test_rate_limit_sheds_flood_with_429(client, secret):
    """A burst beyond the configured allowance is shed with 429 + Retry-After.

    Uses a UNIQUE client IP (Fly-Client-IP) so this flood does not consume the shared limiter
    budget for other tests, and only asserts if a limiter is actually enabled at runtime.
    """
    from ghar_re_service import main, ratelimit

    limiter = main.state.rate_limiter
    if limiter is None or not limiter.enabled:
        pytest.skip("rate limiter not enabled in this configuration")

    ip = "203.0.113.77"  # TEST-NET-3, unique to this test
    max_req = getattr(limiter, "max_requests", 300)
    saw_429 = False
    retry_after_ok = True
    # Hit an unauthenticated but rate-limited path (/v1/meta) so we isolate the limiter, and go
    # comfortably past the budget.
    for _ in range(max_req + 25):
        r = client.get("/v1/meta", headers={ratelimit.CLIENT_IP_HEADER: ip})
        if r.status_code == 429:
            saw_429 = True
            retry_after_ok = retry_after_ok and ("Retry-After" in r.headers)
            break
    assert saw_429, f"limiter (budget {max_req}) never returned 429 under a flood"
    assert retry_after_ok, "429 response missing Retry-After header"


def test_limiter_precedes_auth_unsigned_flood_returns_429(client, secret):
    """Documented invariant (main.py): an unsigned over-limit request is shed with 429, not 401 —
    the limiter is the outermost middleware, so a flood is dropped before any HMAC is computed."""
    from ghar_re_service import main, ratelimit

    limiter = main.state.rate_limiter
    if limiter is None or not limiter.enabled:
        pytest.skip("rate limiter not enabled in this configuration")

    ip = "203.0.113.88"
    max_req = getattr(limiter, "max_requests", 300)
    statuses = set()
    for _ in range(max_req + 25):
        r = client.post("/v1/recommendations", json=BODY,
                        headers={ratelimit.CLIENT_IP_HEADER: ip})
        statuses.add(r.status_code)
        if r.status_code == 429:
            break
    assert 429 in statuses, "unsigned flood was never rate-limited"
