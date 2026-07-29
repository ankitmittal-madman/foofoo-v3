"""
Rate limiting tests (public-ingress hardening).

Two layers, mirroring test_auth.py's structure:
  * unit tests over ghar_re_service.ratelimit — pure window logic, no HTTP and no sleeps (the
    limiter takes `now` as an argument precisely so time can be driven by the test);
  * HTTP tests through the FastAPI middleware — proving the 429 happens at the boundary AND that it
    happens BEFORE signature verification, which is the property the whole feature rests on.
"""

import json
import time

import pytest
from fastapi.testclient import TestClient
from ghar_re_service.providers import EnvRateLimitConfigProvider, RateLimitConfig
from ghar_re_service.ratelimit import SlidingWindowRateLimiter, client_key

from ghar_re_core import fixtures as F
from ghar_re_service import main, ratelimit

# ---------------------------------------------------------------------------
# unit — the sliding window
# ---------------------------------------------------------------------------


def test_requests_under_the_limit_are_allowed():
    rl = SlidingWindowRateLimiter(max_requests=3, window_seconds=60)
    for _ in range(3):
        assert rl.check("1.2.3.4", now=1000.0).allowed


def test_request_over_the_limit_is_refused():
    rl = SlidingWindowRateLimiter(max_requests=3, window_seconds=60)
    for _ in range(3):
        rl.check("1.2.3.4", now=1000.0)
    decision = rl.check("1.2.3.4", now=1000.0)
    assert not decision.allowed
    assert decision.retry_after == 60  # whole window must pass before the oldest hit ages out


def test_window_slides_rather_than_resetting_in_fixed_buckets():
    """The burst-across-the-boundary case a fixed bucket gets wrong.

    Hits are STAGGERED (t=0,1,2) rather than stacked on one instant, because that is what makes the
    claim testable: allowance must come back one slot at a time as each individual hit ages out, not
    all at once the way a fixed 60s bucket would refill it.
    """
    rl = SlidingWindowRateLimiter(max_requests=3, window_seconds=60)
    for t in (0.0, 1.0, 2.0):
        rl.check("ip", now=t)

    assert not rl.check("ip", now=59.9).allowed  # nothing has aged out yet
    assert rl.check("ip", now=60.5).allowed  # only the t=0 hit expired -> exactly one slot
    assert not rl.check("ip", now=60.6).allowed  # and it was immediately consumed


def test_clients_are_limited_independently():
    rl = SlidingWindowRateLimiter(max_requests=2, window_seconds=60)
    rl.check("a", now=0.0)
    rl.check("a", now=0.0)
    assert not rl.check("a", now=0.0).allowed
    assert rl.check("b", now=0.0).allowed  # b must not inherit a's exhaustion


def test_refused_requests_do_not_extend_the_lockout():
    """A client hammering while blocked must not push its own reset further out — otherwise a brief
    burst becomes an unbounded lockout for a caller that simply retries too eagerly."""
    rl = SlidingWindowRateLimiter(max_requests=1, window_seconds=60)
    rl.check("ip", now=0.0)
    for t in (10.0, 20.0, 30.0, 50.0):
        assert not rl.check("ip", now=t).allowed
    assert rl.check("ip", now=60.1).allowed  # still frees at the ORIGINAL hit + window


def test_zero_disables_the_limiter_rather_than_blocking_everything():
    """An operator setting the limit to 0 is turning a damper off; it must never black-hole traffic."""
    rl = SlidingWindowRateLimiter(max_requests=0)
    assert not rl.enabled
    for _ in range(1000):
        assert rl.check("ip", now=0.0).allowed


def test_tracking_table_is_bounded():
    """Memory must not grow with attacker-controlled source addresses — that would make the
    protection its own denial-of-service vector."""
    rl = SlidingWindowRateLimiter(max_requests=5, window_seconds=60, max_tracked_clients=10)
    for i in range(500):
        rl.check(f"10.0.0.{i}", now=0.0)
    assert rl.tracked_clients <= 10


def test_eviction_drops_least_recently_seen_first():
    rl = SlidingWindowRateLimiter(max_requests=5, window_seconds=60, max_tracked_clients=2)
    rl.check("old", now=0.0)
    rl.check("mid", now=1.0)
    rl.check("new", now=2.0)  # evicts "old"
    # "old" comes back with a clean slate; "new" keeps its tally.
    assert rl.check("old", now=3.0).remaining == 4
    assert rl.check("new", now=3.0).remaining == 3


def test_invalid_construction_is_refused():
    with pytest.raises(ValueError):
        SlidingWindowRateLimiter(max_requests=-1)
    with pytest.raises(ValueError):
        SlidingWindowRateLimiter(max_requests=10, window_seconds=0)
    with pytest.raises(ValueError):
        SlidingWindowRateLimiter(max_requests=10, max_tracked_clients=0)


# ---------------------------------------------------------------------------
# unit — client key selection
# ---------------------------------------------------------------------------


def test_client_key_prefers_the_proxy_supplied_ip():
    assert client_key("203.0.113.7", "172.16.0.1") == "203.0.113.7"


def test_client_key_falls_back_to_socket_peer_then_constant():
    assert client_key(None, "172.16.0.1") == "172.16.0.1"
    assert client_key("", "  ") == "unknown"


# ---------------------------------------------------------------------------
# config provider
# ---------------------------------------------------------------------------


def test_rate_limit_defaults_are_applied_when_unset():
    cfg = EnvRateLimitConfigProvider(environ={}).load()
    assert cfg.max_requests == ratelimit.DEFAULT_MAX_REQUESTS_PER_MINUTE
    assert cfg.window_seconds == ratelimit.DEFAULT_WINDOW_SECONDS


def test_rate_limit_is_configurable_by_environment():
    cfg = EnvRateLimitConfigProvider(
        environ={"GHAR_RE_RATE_LIMIT_PER_MINUTE": "42", "GHAR_RE_RATE_LIMIT_WINDOW_SECONDS": "10"}
    ).load()
    assert (cfg.max_requests, cfg.window_seconds) == (42, 10)


def test_malformed_rate_limit_fails_at_startup():
    """A typo'd limit must be loud now, not discovered during the incident it failed to prevent."""
    with pytest.raises(RuntimeError, match="GHAR_RE_RATE_LIMIT_PER_MINUTE"):
        EnvRateLimitConfigProvider(environ={"GHAR_RE_RATE_LIMIT_PER_MINUTE": "many"}).load()


# ---------------------------------------------------------------------------
# HTTP — the middleware boundary
# ---------------------------------------------------------------------------


@pytest.fixture
def limited_client(monkeypatch):
    """A live app whose limiter is tightened to 2 requests/minute for the duration of one test.

    Patched via the provider (not by reaching into the running app) so this exercises the same
    startup path production uses.
    """
    monkeypatch.setenv("GHAR_RE_RATE_LIMIT_PER_MINUTE", "2")
    with TestClient(main.app) as c:
        yield c


def _unsigned_post(client, ip="198.51.100.5"):
    return client.post(
        "/v1/recommendations",
        content=json.dumps({"household": {}}).encode(),
        headers={"content-type": "application/json", ratelimit.CLIENT_IP_HEADER: ip},
    )


def test_http_over_limit_returns_429_before_signature_check(limited_client):
    """THE ordering test. These requests are unsigned, so the signature middleware would answer 401.
    Once the allowance is spent the answer must become 429 instead — which is only possible if the
    limiter runs first, i.e. no HMAC was computed for the shed request."""
    assert _unsigned_post(limited_client).status_code == 401
    assert _unsigned_post(limited_client).status_code == 401
    third = _unsigned_post(limited_client)
    assert third.status_code == 429
    assert third.json()["error"] == "rate_limited"


def test_http_429_carries_retry_after(limited_client):
    for _ in range(3):
        r = _unsigned_post(limited_client, ip="198.51.100.9")
    assert r.status_code == 429
    assert int(r.headers["Retry-After"]) >= 1


def test_http_limit_is_per_client_ip(limited_client):
    """One noisy source must not shed a different caller's traffic."""
    for _ in range(3):
        _unsigned_post(limited_client, ip="198.51.100.20")
    # A different address still gets its own allowance (401 = reached the signature check).
    assert _unsigned_post(limited_client, ip="198.51.100.21").status_code == 401


def test_http_health_probes_are_never_rate_limited(limited_client):
    """Shedding a platform health check would get the machine restarted — the outage this exists to
    prevent. Well past the 2/min allowance, both probes must still answer 200."""
    for _ in range(25):
        assert limited_client.get("/healthz").status_code == 200
        assert limited_client.get("/readyz").status_code == 200


def test_http_rate_limited_requests_are_counted_separately(limited_client):
    """A 429 is the service working, not failing — it must not inflate errors_total."""
    before = limited_client.get("/v1/meta").json()["metrics"]
    for _ in range(4):
        _unsigned_post(limited_client, ip="198.51.100.30")
    after = limited_client.get("/v1/meta").json()["metrics"]

    assert after["rate_limited_total"] > before["rate_limited_total"]
    # The two 401s counted as errors; the shed ones did not add to that.
    assert after["errors_total"] - before["errors_total"] == 2


# ---------------------------------------------------------------------------
# HTTP — default configuration must not disturb normal traffic
# ---------------------------------------------------------------------------


def test_signed_traffic_is_unaffected_at_default_limits():
    """The default ceiling exists to damp floods, not to interfere with real use. A normal signed
    request must still succeed with the limiter fully armed."""
    import hashlib
    import hmac

    from ghar_re_service.providers import DEV_INSECURE_SECRET

    hh = [h for h in F.HOUSEHOLDS if h["id_key"] == "couple_mumbai_mh"][0]
    raw = json.dumps(
        {
            "household": {k: v for k, v in hh.items() if k != "id_key"},
            "context": {"slot": "dinner", "season": "monsoon"},
        }
    ).encode()
    ts = int(time.time())
    sig = hmac.new(
        DEV_INSECURE_SECRET.encode(), f"{ts}.".encode() + raw, hashlib.sha256
    ).hexdigest()

    with TestClient(main.app) as c:
        r = c.post(
            "/v1/recommendations",
            content=raw,
            headers={
                "content-type": "application/json",
                "X-Ghar-Signature": f"t={ts},v1={sig}",
            },
        )
    assert r.status_code == 200
    assert len(r.json()["plates"]) == 7


def test_rate_limit_config_builds_a_working_limiter():
    rl = RateLimitConfig(max_requests=1, window_seconds=30).build()
    assert rl.check("x", now=0.0).allowed
    assert not rl.check("x", now=0.0).allowed
