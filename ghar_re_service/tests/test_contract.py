"""
Contract tests (Phase A + RE-DOC-11 §5/§6): the response conforms to the JSON Schema, the
additive/open compatibility rule is actually ENFORCED (not just documented), and the service's
registry-composed BASE matches ghar_re_core's BASE exactly (no math duplication / no drift).
"""
import copy

import pytest

from ghar_re_service import schemas, engine
from ghar_re_service.modules import build_registry, compose_base
from ghar_re_service.providers import LocalSnapshotCatalogueProvider, YamlFileConfigProvider
from ghar_re_core import scoring as S
from ghar_re_core.derivation import derive_theta
from ghar_re_core import fixtures as F
from ghar_re_core.pipeline import make_context

CONFIG = YamlFileConfigProvider().load()
CATALOGUE = LocalSnapshotCatalogueProvider().load()
REGISTRY = build_registry()


def _sample_request(hh_key="couple_delhi_north"):
    hh = [h for h in F.HOUSEHOLDS if h["id_key"] == hh_key][0]
    return {
        "household": {k: v for k, v in hh.items() if k != "id_key"},
        "context": {"slot": "dinner", "season": "monsoon", "weather": {"is_raining": True, "temp_c": 27}},
    }


# ---------------------------------------------------------------------------
# response conforms to the Phase A JSON Schema
# ---------------------------------------------------------------------------
def test_response_conforms_to_schema():
    resp = engine.run(_sample_request(), CATALOGUE, CONFIG, REGISTRY)
    schemas.validate_response(resp)   # raises ContractError if non-conformant
    assert resp["api_version"] == "v1"
    assert len(resp["plates"]) == 7


def test_request_sample_conforms_to_schema():
    schemas.validate_request(_sample_request())   # a well-formed request validates


# ---------------------------------------------------------------------------
# ADDITIVE/OPEN compatibility (RE-DOC-11 §5 rule 1) — enforced, not just a comment
# ---------------------------------------------------------------------------
def test_unknown_request_field_is_tolerated():
    req = _sample_request()
    req["some_future_field"] = {"anything": 123}         # unknown top-level field
    req["household"]["q16_future_question"] = "surprise"  # unknown nested field
    req["context"]["experimental_flag"] = True
    # must NOT raise — unknown fields are ignored, never rejected
    schemas.validate_request(req)


def test_unknown_response_field_is_tolerated():
    resp = engine.run(_sample_request(), CATALOGUE, CONFIG, REGISTRY)
    resp["future_top_level"] = "ok"
    resp["plates"][0]["future_plate_field"] = 42
    resp["plates"][0]["contributions"][0]["future_module_field"] = "x"
    schemas.validate_response(resp)   # additive tolerance on the response side too


def test_missing_required_field_still_fails():
    # additive-open must NOT mean "anything goes" — required fields are still required.
    req = _sample_request()
    del req["household"]["q5_diet"]
    with pytest.raises(schemas.ContractError):
        schemas.validate_request(req)


# ---------------------------------------------------------------------------
# contributions[] is OPEN and richer than the old fixed 3-field struct (RE-DOC-11 §6)
# ---------------------------------------------------------------------------
def test_contributions_array_is_open_and_populated():
    resp = engine.run(_sample_request(), CATALOGUE, CONFIG, REGISTRY)
    for plate in resp["plates"]:
        contribs = plate["contributions"]
        assert len(contribs) > 3, "contributions must exceed the old {base,gain_q15,pairing_compat} 3-field struct"
        for c in contribs:
            assert set(c) >= {"module", "value", "weight", "confidence"}
        # fixed aggregates coexist with the open list
        assert {"base_total", "gain_multiplier", "final_score"} <= set(plate)


# ---------------------------------------------------------------------------
# NO MATH DUPLICATION: the service registry's BASE == ghar_re_core.scoring.base() exactly
# ---------------------------------------------------------------------------
def test_registry_base_matches_core_base():
    hh = [h for h in F.HOUSEHOLDS if h["id_key"] == "couple_delhi_north"][0]
    theta = derive_theta({k: v for k, v in hh.items() if k != "id_key"})
    ctx = make_context(slot="dinner", season="monsoon", is_raining=True)
    checked = 0
    for dish in CATALOGUE:
        if S.m_slot(dish, ctx) == 0:
            continue
        base_total, _ = compose_base(dish, theta, ctx, CONFIG, REGISTRY)
        assert base_total == pytest.approx(S.base(dish, theta, ctx), rel=1e-9, abs=1e-9), \
            f"registry BASE drifted from core BASE for {dish.name}"
        checked += 1
    assert checked > 10
