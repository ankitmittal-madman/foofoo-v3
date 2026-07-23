"""
Service-level e2e tests (FastAPI TestClient): health/readiness endpoints, /v1/meta, and a full
/v1/recommendations round-trip against the golden-sample households.
"""
import pytest
from fastapi.testclient import TestClient

from ghar_re_service import main
from ghar_re_core import fixtures as F


@pytest.fixture(scope="module")
def client():
    # entering the context runs the startup lifecycle (config → catalogue → indices → registry → ready)
    with TestClient(main.app) as c:
        yield c


def _req(hh_key="couple_mumbai_mh", **ctx):
    hh = [h for h in F.HOUSEHOLDS if h["id_key"] == hh_key][0]
    context = {"slot": "dinner", "season": "monsoon", "weather": {"is_raining": True, "temp_c": 27}}
    context.update(ctx)
    return {"household": {k: v for k, v in hh.items() if k != "id_key"}, "context": context}


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
        r = client.post("/v1/recommendations", json=_req())
        assert r.status_code == 503
        assert r.json()["error"] == "service_not_ready"
    finally:
        main.state.ready = True   # restore for the rest of the module


def test_meta_returns_versions(client):
    body = client.get("/v1/meta").json()
    assert body["api_version"] == "v1"
    assert body["engine_version"] == "1.0.0"
    assert body["config_version"].startswith("Config v")


def test_recommendations_end_to_end(client):
    r = client.post("/v1/recommendations", json=_req("couple_mumbai_mh"))
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
    # West-MH rainy household → its KB §R3 comfort hero (Kanda Bhaji) is among the served heroes
    served = {n for p in body["plates"] for n in p["hero_dish_names"]}
    assert "Kanda Bhaji" in served


def test_recommendations_tolerates_unknown_fields(client):
    req = _req()
    req["household"]["q99_future"] = "ignored"
    req["telemetry"] = {"client": "test"}
    r = client.post("/v1/recommendations", json=req)
    assert r.status_code == 200   # additive/open contract holds at the HTTP boundary


def test_request_id_is_echoed(client):
    req = _req()
    req["request_id"] = "fixed-req-id-123"
    body = client.post("/v1/recommendations", json=req).json()
    assert body["request_id"] == "fixed-req-id-123"


def test_invalid_request_returns_422(client):
    bad = _req()
    del bad["household"]["q1_household_type"]   # drop a required field
    r = client.post("/v1/recommendations", json=bad)
    assert r.status_code == 422
    assert r.json()["error"] == "invalid_request"
