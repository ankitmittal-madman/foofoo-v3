"""
Phase 6 — API contract testing at the HTTP boundary.

These tests independently validate the LIVE HTTP responses against the published JSON-Schema
contract (contracts/ghar-re-v1.schema.json) using jsonschema directly — deliberately NOT trusting
the service's own `schemas.validate_response`, so a bug in that validator cannot hide a contract
break. Covers /healthz, /readyz, /v1/meta, and /v1/recommendations.
"""

from __future__ import annotations

from jsonschema import Draft202012Validator


def _validator(schema: dict, def_name: str) -> Draft202012Validator:
    """Build a Draft2020-12 validator for one named `$defs` entry of the contract schema."""
    sub = dict(schema["$defs"][def_name])
    sub["$defs"] = schema["$defs"]  # keep sibling $ref targets resolvable
    return Draft202012Validator(sub)


def test_healthz_contract(client):
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json() == {"status": "alive"}


def test_readyz_ready_after_startup(client):
    r = client.get("/readyz")
    assert r.status_code == 200
    assert r.json()["status"] == "ready"


def test_meta_conforms_to_contract(client, contract_schema):
    r = client.get("/v1/meta")
    assert r.status_code == 200
    errors = sorted(_validator(contract_schema, "MetaResponse").iter_errors(r.json()),
                    key=lambda e: e.path)
    assert not errors, "MetaResponse contract violations: " + "; ".join(
        f"{list(e.path)}: {e.message}" for e in errors)


def test_recommendation_response_conforms_to_contract(signed_post, contract_schema):
    from ghar_re_core import fixtures as fx

    hh = next(h for h in fx.HOUSEHOLDS if h["id_key"] == "couple_mumbai_mh")
    payload = {
        "household": {k: v for k, v in hh.items() if k != "id_key"},
        "context": {"slot": "dinner", "season": "monsoon",
                    "weather": {"is_raining": True, "temp_c": 27}},
    }
    r = signed_post("/v1/recommendations", payload)
    assert r.status_code == 200, r.text
    body = r.json()
    errors = sorted(_validator(contract_schema, "RecommendationResponse").iter_errors(body),
                    key=lambda e: e.path)
    assert not errors, "RecommendationResponse contract violations: " + "; ".join(
        f"{list(e.path)}: {e.message}" for e in errors)
    # contract invariants the schema alone may not pin
    assert body["api_version"] == "v1"
    assert len(body["plates"]) == 7
    assert isinstance(body["warnings"], list)


def test_response_request_id_is_echoed(signed_post):
    payload = {
        "request_id": "qa-fixed-id-001",
        "household": {"q1_household_type": "single", "q2_working_professionals": 1,
                      "q3_home_state": "Delhi", "q4_current_city": "New Delhi",
                      "q5_diet": "veg", "q7_veg_days": [], "q8_is_jain": False,
                      "q9_allergies": [], "q11_conditions": [], "q12_member_ages": [{"role": "self", "age": 30}],
                      "q13_who_cooks": "self", "q14_eat_out_per_week": 2,
                      "q15_objective": "healthy_living"},
        "context": {"slot": "dinner", "season": "summer",
                    "weather": {"is_raining": False, "temp_c": 35}},
    }
    r = signed_post("/v1/recommendations", payload)
    assert r.status_code == 200, r.text
    assert r.json()["request_id"] == "qa-fixed-id-001"
