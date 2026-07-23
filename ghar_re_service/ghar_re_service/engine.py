"""
engine — composition/translation layer (NO recommendation math here).

Translates a contract request into the shape ghar_re_core expects, calls the ONE tested pipeline
(ghar_re_core.pipeline.recommend — same math the 16 tests cover), then serializes the result into
the Phase A response, populating the open `contributions[]` via the ScoringModule registry.

If a formula appears to be needed here, it belongs in ghar_re_core, not this file.
"""
from __future__ import annotations

import uuid
from typing import Any, Dict, List

from ghar_re_core import pipeline as core_pipeline
from ghar_re_core import scoring as S
from ghar_re_service.modules import compose_base
from ghar_re_service.version import API_VERSION, ENGINE_VERSION

TARGET_PLATES = 7

# Raw Q1-Q15 keys the core derivation reads (defaults fill anything the caller omits).
_ARRAY_DEFAULTS = ("q6_nonveg_types", "q7_veg_days", "q9_allergies", "q11_conditions")


def build_household_dict(hh: Dict[str, Any]) -> Dict[str, Any]:
    """Map the contract's raw household (Q1-Q15) to the dict ghar_re_core.derivation expects."""
    out = dict(hh)
    out.setdefault("label", hh.get("label", "request-household"))
    for k in _ARRAY_DEFAULTS:
        out.setdefault(k, [])
    out.setdefault("q8_is_jain", False)
    out.setdefault("q10_allergy_other", None)
    return out


def build_context(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Map the contract context to a core context dict (weather is mocked/injected — no live API)."""
    weather = ctx.get("weather") or {}
    return core_pipeline.make_context(
        slot=ctx.get("slot", "dinner"),
        season=ctx.get("season", "transitional"),
        weekday=ctx.get("weekday", "Monday"),
        weather_condition=weather.get("weather_condition"),
        temp_c=weather.get("temp_c"),
        is_raining=bool(weather.get("is_raining", False)),
        active_modes=ctx.get("active_modes") or [],
        calorie_target=ctx.get("calorie_target"),
    )


def _principal_hero(plate):
    """The hero whose BASE breakdown represents the plate's contributions. For a pair, the
    higher-scoring of the two heroes; otherwise the sole hero. (Documented explainability choice.)"""
    if plate["form"] == "pair":
        d, l = plate["dry"], plate["liquid"]
        return d, [d, l]
    h = plate["hero"]
    return h, [h]


def run(request: Dict[str, Any], catalogue, config, registry) -> Dict[str, Any]:
    """Full request → response. `catalogue`/`config`/`registry` come from the providers at startup."""
    request_id = request.get("request_id") or str(uuid.uuid4())
    hh = build_household_dict(request["household"])
    ctx = build_context(request["context"])
    objective = hh.get("q15_objective") or config.default_objective

    result = core_pipeline.recommend(hh, ctx, catalogue)   # the ONE implementation of the math
    plates_out: List[dict] = []
    warnings: List[str] = []

    for i, p in enumerate(result["plates"]):
        principal, heroes = _principal_hero(p)
        base_total, contributions = compose_base(principal, result["theta"], ctx, config, registry)
        gain = S.gain_q15(principal, objective)
        plates_out.append({
            "plate_id": str(uuid.uuid5(uuid.NAMESPACE_OID, f"{request_id}:{i}")),
            "form": p["form"],
            "hero_dish_ids": [h.id for h in heroes],
            "hero_dish_names": [h.name for h in heroes],
            "support": p.get("support"),
            "is_standalone": p["form"] == "standalone",
            "plate_score": round(p["score"], 6),
            "base_total": round(base_total, 6),          # fixed aggregate
            "gain_multiplier": round(gain, 6),           # fixed aggregate
            "final_score": round(p["score"], 6),         # fixed aggregate
            "contributions": contributions,              # OPEN list (RE-DOC-11 §6)
        })

    if len(plates_out) < TARGET_PLATES:
        warnings.append(
            f"only {len(plates_out)} of {TARGET_PLATES} plates could be formed for this household/context"
        )

    return {
        "request_id": request_id,
        "api_version": API_VERSION,
        "engine_version": ENGINE_VERSION,
        "config_version": config.versions["config"],
        "plates": plates_out,
        "warnings": warnings,
    }
