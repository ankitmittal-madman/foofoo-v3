"""
Service-to-service signature verification tests (RE-DOC-10 §9).

Two layers, deliberately:
  * unit tests over ghar_re_service.auth — the pure verification logic, no HTTP involved;
  * HTTP tests through the FastAPI middleware — proving the 401 happens at the boundary, before
    the request is parsed or the engine is called.

The signature these tests construct is built the SAME way the Edge Function's re-client.ts builds
it (`hex(HMAC-SHA256(secret, f"{t}.{rawBody}"))`), so a passing test here is evidence the two
implementations actually agree — not just that this side is self-consistent.
"""

import hashlib
import hmac
import json
import time

import pytest
from fastapi.testclient import TestClient
from ghar_re_service.providers import DEV_INSECURE_SECRET, EnvAuthConfigProvider

from ghar_re_core import fixtures as F
from ghar_re_service import auth, main

SECRET = DEV_INSECURE_SECRET


def _sign(secret: str, timestamp: int, raw: bytes) -> str:
    """Independent re-implementation of the edge function's signing, used as the test oracle."""
    msg = f"{timestamp}.".encode() + raw
    return hmac.new(secret.encode(), msg, hashlib.sha256).hexdigest()


def _headers(raw: bytes, secret: str = SECRET, timestamp: int | None = None) -> dict:
    ts = int(time.time()) if timestamp is None else timestamp
    return {
        "content-type": "application/json",
        auth.SIGNATURE_HEADER: f"t={ts},v1={_sign(secret, ts, raw)}",
        auth.REQUEST_ID_HEADER: "test-req-id",
    }


def _body(hh_key="couple_mumbai_mh") -> bytes:
    hh = [h for h in F.HOUSEHOLDS if h["id_key"] == hh_key][0]
    payload = {
        "household": {k: v for k, v in hh.items() if k != "id_key"},
        "context": {
            "slot": "dinner",
            "season": "monsoon",
            "weather": {"is_raining": True, "temp_c": 27},
        },
    }
    return json.dumps(payload).encode()


# ---------------------------------------------------------------------------
# unit — pure verification logic
# ---------------------------------------------------------------------------
def test_valid_signature_verifies():
    raw = b'{"hello":"world"}'
    ts = int(time.time())
    auth.verify_request(raw, f"t={ts},v1={_sign(SECRET, ts, raw)}", SECRET, now=ts)


def test_missing_signature_rejected():
    with pytest.raises(auth.AuthError) as e:
        auth.verify_request(b"{}", None, SECRET, now=time.time())
    assert e.value.reason == "missing_signature"


def test_malformed_signature_rejected():
    for bad in ("garbage", "t=abc,v1=deadbeef", "v1=deadbeef", "t=123", "t=123,v1="):
        with pytest.raises(auth.AuthError) as e:
            auth.verify_request(b"{}", bad, SECRET, now=time.time())
        assert e.value.reason == "malformed_signature", bad


def test_tampered_body_rejected():
    """The signature is over the body, so changing one byte must invalidate it."""
    raw = b'{"amount":1}'
    ts = int(time.time())
    header = f"t={ts},v1={_sign(SECRET, ts, raw)}"
    with pytest.raises(auth.AuthError) as e:
        auth.verify_request(b'{"amount":9}', header, SECRET, now=ts)
    assert e.value.reason == "invalid_signature"


def test_wrong_secret_rejected():
    raw = b"{}"
    ts = int(time.time())
    header = f"t={ts},v1={_sign('not-the-real-secret', ts, raw)}"
    with pytest.raises(auth.AuthError) as e:
        auth.verify_request(raw, header, SECRET, now=ts)
    assert e.value.reason == "invalid_signature"


def test_stale_timestamp_rejected():
    """Replay guard: a correctly-signed request from 10 minutes ago is still refused."""
    raw = b"{}"
    old = int(time.time()) - 600
    header = f"t={old},v1={_sign(SECRET, old, raw)}"
    with pytest.raises(auth.AuthError) as e:
        auth.verify_request(raw, header, SECRET, now=time.time(), max_skew_seconds=300)
    assert e.value.reason == "stale_signature"


def test_future_dated_timestamp_rejected():
    """Skew is absolute — a future-dated signature is as suspect as a stale one."""
    raw = b"{}"
    future = int(time.time()) + 600
    header = f"t={future},v1={_sign(SECRET, future, raw)}"
    with pytest.raises(auth.AuthError) as e:
        auth.verify_request(raw, header, SECRET, now=time.time(), max_skew_seconds=300)
    assert e.value.reason == "stale_signature"


def test_timestamp_inside_skew_window_accepted():
    raw = b"{}"
    recent = int(time.time()) - 120
    header = f"t={recent},v1={_sign(SECRET, recent, raw)}"
    auth.verify_request(raw, header, SECRET, now=time.time(), max_skew_seconds=300)


# ---------------------------------------------------------------------------
# provider — fail-closed in production
# ---------------------------------------------------------------------------
def test_missing_secret_falls_back_to_dev_secret_locally():
    cfg = EnvAuthConfigProvider(environ={}).load()
    assert cfg.secret == DEV_INSECURE_SECRET


def test_missing_secret_raises_in_production():
    """The dev secret is published in this repo — production must refuse to start without a real one."""
    with pytest.raises(RuntimeError, match="GHAR_RE_SERVICE_SECRET"):
        EnvAuthConfigProvider(environ={"FOOFOO_ENV": "production"}).load()


def test_production_with_secret_loads():
    cfg = EnvAuthConfigProvider(
        environ={"FOOFOO_ENV": "production", "GHAR_RE_SERVICE_SECRET": "real-secret"}
    ).load()
    assert cfg.secret == "real-secret"


# ---------------------------------------------------------------------------
# HTTP — the middleware boundary
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def client():
    with TestClient(main.app) as c:
        yield c


def test_http_signed_request_succeeds(client):
    raw = _body()
    r = client.post("/v1/recommendations", content=raw, headers=_headers(raw))
    assert r.status_code == 200
    assert len(r.json()["plates"]) == 7


def test_http_unsigned_request_is_401(client):
    raw = _body()
    r = client.post(
        "/v1/recommendations", content=raw, headers={"content-type": "application/json"}
    )
    assert r.status_code == 401
    assert r.json()["detail"] == "missing_signature"


def test_http_tampered_body_is_401(client):
    """Sign one body, send another — the classic MITM case."""
    signed = _body("couple_mumbai_mh")
    tampered = _body("jain_couple_ahmedabad")
    r = client.post("/v1/recommendations", content=tampered, headers=_headers(signed))
    assert r.status_code == 401
    assert r.json()["detail"] == "invalid_signature"


def test_http_stale_signature_is_401(client):
    raw = _body()
    r = client.post(
        "/v1/recommendations", content=raw, headers=_headers(raw, timestamp=int(time.time()) - 600)
    )
    assert r.status_code == 401
    assert r.json()["detail"] == "stale_signature"


def test_http_401_happens_before_validation(client):
    """An unsigned request with a structurally INVALID body must still be 401, not 422 — proof the
    signature gate runs before parsing rather than after."""
    r = client.post(
        "/v1/recommendations",
        content=b'{"household":{}}',
        headers={"content-type": "application/json"},
    )
    assert r.status_code == 401


def test_health_and_meta_remain_unauthenticated(client):
    """Probes and the meta endpoint must not require a signature (RE-DOC-10 §4/§12)."""
    assert client.get("/healthz").status_code == 200
    assert client.get("/readyz").status_code == 200
    assert client.get("/v1/meta").status_code == 200
