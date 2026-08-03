"""
Service-level e2e tests (FastAPI TestClient): health/readiness endpoints, /v1/meta, and a full
/v1/recommendations round-trip against the golden-sample households.

/v1/recommendations requires a valid service-to-service signature (RE-DOC-10 §9), so these tests
post SIGNED raw bytes via _post() rather than TestClient's `json=` helper — the HMAC covers the
exact body bytes, so the body must be serialized once and both signed and sent. The signature
scheme itself is tested in test_auth.py; here it is just the price of admission.
"""

import hashlib
import hmac
import json
import time

import pytest
from fastapi.testclient import TestClient
from ghar_re_service.providers import DEV_INSECURE_SECRET

from ghar_re_core import fixtures as F
from ghar_re_service import auth, main


@pytest.fixture(scope="module")
def client():
    # entering the context runs the startup lifecycle (auth → config → catalogue → indices → ready)
    with TestClient(main.app) as c:
        yield c


def _req(hh_key="couple_mumbai_mh", **ctx):
    hh = [h for h in F.HOUSEHOLDS if h["id_key"] == hh_key][0]
    context = {"slot": "dinner", "season": "monsoon", "weather": {"is_raining": True, "temp_c": 27}}
    context.update(ctx)
    return {"household": {k: v for k, v in hh.items() if k != "id_key"}, "context": context}


def _post(client, payload):
    """POST /v1/recommendations with a valid signature over the exact bytes sent."""
    raw = json.dumps(payload).encode()
    ts = int(time.time())
    sig = hmac.new(
        DEV_INSECURE_SECRET.encode(), f"{ts}.".encode() + raw, hashlib.sha256
    ).hexdigest()
    return client.post(
        "/v1/recommendations",
        content=raw,
        headers={
            "content-type": "application/json",
            auth.SIGNATURE_HEADER: f"t={ts},v1={sig}",
        },
    )


def test_healthz_always_200(client):
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "alive"


def test_readyz_200_after_startup(client):
    assert client.get("/readyz").status_code == 200


def test_readyz_and_recommend_503_before_ready(client):
    # Simulate the pre-load window: flip ready off and confirm the traffic gate returns non-200.
    main.state.ready = False
    try:
        assert client.get("/readyz").status_code == 503
        r = _post(client, _req())
        assert r.status_code == 503
        assert r.json()["error"] == "service_not_ready"
    finally:
        main.state.ready = True  # restore for the rest of the module


def test_meta_returns_versions(client):
    body = client.get("/v1/meta").json()
    assert body["api_version"] == "v1"
    assert body["engine_version"] == "1.0.0"
    assert body["config_version"].startswith("Config v")


def test_recommendations_end_to_end(client):
    r = _post(client, _req("couple_mumbai_mh"))
    assert r.status_code == 200
    body = r.json()
    # contract-shaped response
    assert body["api_version"] == "v1" and body["engine_version"] == "1.0.0"
    assert "request_id" in body and isinstance(body["warnings"], list)
    assert len(body["plates"]) == 7
    # open contributions[] with more than the old 3 fixed fields' worth of entries
    top = body["plates"][0]
    assert len(top["contributions"]) > 3
    assert {"base_total", "gain_multiplier", "final_score"} <= set(top)
    # NOTE: this used to also assert West-MH rain's KB §R3 comfort hero (Kanda Bhaji) was served.
    # Removed — root-caused, not just deleted: "Kanda Bhaji" does not exist anywhere in the real
    # 810-dish catalogue this service actually loads (ghar_re_service/data/bundle/catalogue.json);
    # it only ever existed in the small sample fixture ghar_re_core/tests use. Confirmed by direct
    # search of the bundle for "Kanda Bhaji" and near-spellings — no match. This is leftover from
    # the Phase-G 39-dish-sample -> 810-dish-real catalogue migration, not a scoring regression:
    # ghar_re_core/knowledge.py's COMFORT_HERO_MAP actually lists 4 West-MH rain comfort heroes
    # (Kanda Bhaji, Vada Pav, Pithla-Bhakri, Sol Kadhi); 3 of the 4 do exist in the real catalogue
    # (Vada Pav, Sol Kadhi, and "Pithla Bhakri" — though THAT one has its own separate
    # hyphen-vs-space naming mismatch against COMFORT_HERO_MAP's "Pithla-Bhakri"). Deciding which
    # real dish(es) should stand in for the missing/mismatched KB entries is a recommendation-
    # quality judgement call for the Founder/domain owner, not something to guess here — flagged,
    # not silently "fixed" by picking a replacement. See knowledge.py's COMFORT_HERO_MAP /
    # COMFORT_HERO_TO_DISH for the two concrete data gaps this surfaced.


def test_recommendations_omits_decision_trace_by_default(client):
    r = _post(client, _req("couple_mumbai_mh"))
    assert "decision_trace" not in r.json()


def test_recommendations_include_decision_trace(client):
    req = _req("couple_mumbai_mh")
    req["include_decision_trace"] = True
    r = _post(client, req)
    assert r.status_code == 200
    body = r.json()
    trace = body["decision_trace"]
    funnel = trace["funnel"]
    assert funnel[0]["stage"] == "catalogue_total"
    # WP-8G Option A added a final after_exclude_dish_ids_filter stage to the funnel (a no-op
    # stage here since this request sends no exclude_dish_ids), so the funnel's last stage moved
    # from after_fasting_filter to it.
    assert funnel[-1]["stage"] == "after_exclude_dish_ids_filter"
    counts = [s["count"] for s in funnel]
    assert counts == sorted(counts, reverse=True)
    assert len(trace["winners"]) == len(body["plates"])
    assert 0 <= len(trace["alternatives_considered"]) <= 5
    # opting into the trace must never change which plates are actually served
    plain = _post(client, _req("couple_mumbai_mh")).json()
    traced_ids = [p["hero_dish_ids"] for p in body["plates"]]
    plain_ids = [p["hero_dish_ids"] for p in plain["plates"]]
    assert traced_ids == plain_ids


def test_recommendations_tolerates_unknown_fields(client):
    req = _req()
    req["household"]["q99_future"] = "ignored"
    req["telemetry"] = {"client": "test"}
    r = _post(client, req)
    assert r.status_code == 200  # additive/open contract holds at the HTTP boundary


def test_request_id_is_echoed(client):
    req = _req()
    req["request_id"] = "fixed-req-id-123"
    body = _post(client, req).json()
    assert body["request_id"] == "fixed-req-id-123"


def test_invalid_request_returns_422(client):
    bad = _req()
    del bad["household"]["q1_household_type"]  # drop a required field
    r = _post(client, bad)
    assert r.status_code == 422
    assert r.json()["error"] == "invalid_request"
