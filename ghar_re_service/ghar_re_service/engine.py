"""
engine — composition/translation layer (NO recommendation math here).

Translates a contract request into the shape ghar_re_core expects, calls the ONE tested pipeline
(ghar_re_core.pipeline.recommend — same math the 16 tests cover), then serializes the result into
the Phase A response, populating the open `contributions[]` via the ScoringModule registry.

If a formula appears to be needed here, it belongs in ghar_re_core, not this file.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any

from ghar_re_core import calibration as calib
from ghar_re_core import meal_planner as planner
from ghar_re_core import pipeline as core_pipeline
from ghar_re_core import scoring as S
from ghar_re_service import media
from ghar_re_service.modules import compose_base
from ghar_re_service.version import API_VERSION, ENGINE_VERSION

TARGET_PLATES = 7

# Raw Q1-Q15 keys the core derivation reads (defaults fill anything the caller omits).
_ARRAY_DEFAULTS = ("q6_nonveg_types", "q7_veg_days", "q9_allergies", "q11_conditions")


def build_household_dict(hh: dict[str, Any]) -> dict[str, Any]:
    """Map the contract's raw household (Q1-Q15) to the dict ghar_re_core.derivation expects."""
    out = dict(hh)
    out.setdefault("label", hh.get("label", "request-household"))
    for k in _ARRAY_DEFAULTS:
        out.setdefault(k, [])
    out.setdefault("q8_is_jain", False)
    out.setdefault("q10_allergy_other", None)
    return out


def build_context(ctx: dict[str, Any], exclude_dish_ids: list[str] | None = None) -> dict[str, Any]:
    """Map the contract context to a core context dict.

    Weather is injected by the Edge layer, which owns provider access and caching.

    `exclude_dish_ids` (WP-8G Option A) is a REQUEST-level field, not part of the contract's
    HouseholdContext object, so it's threaded in as a separate argument here rather than read off
    `ctx` — but it still lands in the core ctx dict, since that's what
    ghar_re_core.scoring.pass_exclude_dish_ids/eligible() read. Additive/optional: an
    omitted/empty list is a no-op, matching every existing caller/fixture that predates this field.
    """
    weather = ctx.get("weather") or {}
    core_ctx = core_pipeline.make_context(
        slot=ctx.get("slot", "dinner"),
        season=ctx.get("season", "transitional"),
        weekday=ctx.get("weekday", "Monday"),
        weather_condition=weather.get("weather_condition"),
        temp_c=weather.get("temp_c"),
        is_raining=bool(weather.get("is_raining", False)),
        active_modes=ctx.get("active_modes") or [],
        calorie_target=ctx.get("calorie_target"),
    )
    core_ctx["exclude_dish_ids"] = exclude_dish_ids or []
    # These are online, household-specific features composed by the Edge layer.  Keeping them
    # here is essential: cohort decay and exploration both read the core context, not the raw
    # HTTP request.  Previously the JSON contract accepted interaction_count but this translation
    # silently dropped it, leaving every returning household in cold-start weighting forever.
    core_ctx["interaction_count"] = max(0, int(ctx.get("interaction_count", 0) or 0))
    feedback_counts = ctx.get("dish_feedback_counts")
    core_ctx["dish_feedback_counts"] = feedback_counts if isinstance(feedback_counts, list) else []
    return core_ctx


def _request_rng_seed(household: dict[str, Any], context: dict[str, Any]) -> int:
    """Stable RNG seed for ghar_re_core.exploration's epsilon-greedy swap, derived from the
    request's own content rather than true randomness — so identical requests (same household +
    context) always get the same served plates (RE-DOC-11 persistence/repeatability guarantee),
    while distinct households/contexts still land on independent dice-rolls, matching the
    household-seeded RNG precedent in ghar_re_core.meal_planner.cold_start_top15."""
    payload = json.dumps({"household": household, "context": context}, sort_keys=True, default=str)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return int(digest[:16], 16)


def _principal_hero(plate):
    """The hero whose BASE breakdown represents the plate's contributions.

    For a pair, the higher-scoring of the two heroes; otherwise the sole hero.
    (Documented explainability choice.)
    """
    if plate["form"] == "pair":
        dry, liquid = plate["dry"], plate["liquid"]
        return dry, [dry, liquid]
    h = plate["hero"]
    return h, [h]


# =====================================================================================
# WP-18 planning surfaces (onboarding → plan → dish). Translation-only, exactly like run():
# map the request → call ghar_re_core.meal_planner (the ONE place the ranking/reconciliation lives)
# → attach media (Cloudinary image URLs; recipe on the detail surface). No math here.
# =====================================================================================
def _with_images(views: list[dict]) -> list[dict]:
    """Attach a Cloudinary image URL to each dish view (in place)."""
    for v in views:
        media.attach_image(v)
    return views


def plan_cold_start(request: dict[str, Any], catalogue, config) -> dict[str, Any]:
    """Surface 1: post-onboarding top-15 preference primer (diverse top dishes)."""
    hh = build_household_dict(request["household"])
    n = int(request.get("count", 15))
    res = planner.cold_start_top15(
        hh,
        catalogue,
        n=n,
        weekday=request.get("weekday", "Monday"),
        household_id=request.get("household_id"),
    )
    _with_images(res["dishes"])
    return res


def plan_calibration(request: dict[str, Any], catalogue, config) -> dict[str, Any]:
    """WP-18 dish-pick surface: 3 slots x 5 dishes (3 expected-positive + 2 planted-mismatch,
    cell_role never surfaced to the client) for the post-onboarding calibration grid."""
    hh = build_household_dict(request["household"])
    res = calib.calibration_grid(
        hh,
        catalogue,
        weekday=request.get("weekday", "Monday"),
        household_id=request.get("household_id"),
    )
    for slot_dishes in res["slots"].values():
        _with_images(slot_dishes)
    return res


def plan_slot(request: dict[str, Any], catalogue, config) -> dict[str, Any]:
    """Surface 2 (and 4 when class_code is set): a slot's 4–5 dish options."""
    hh = build_household_dict(request["household"])
    res = planner.slot_options(
        hh,
        request.get("slot", "dinner"),
        catalogue,
        n=int(request.get("count", 8)),
        weekday=request.get("weekday", "Monday"),
        class_code=request.get("class_code"),
        context=request.get("context") or {},
        exclude_dish_names=request.get("exclude_dish_names") or [],
        preference_by_dish=request.get("preference_by_dish") or {},
    )
    _with_images(res["options"])
    # Deterministic lifecycle add-ons remain separate from the household's primary meal.  These
    # are food-role rules only; health-condition add-ons intentionally require clinical review.
    addon_classes = {
        "infant": {
            "breakfast": "BF_INFANT_6M_SOFT",
            "lunch": "LD_CHILD_MILD_PLATE",
            "dinner": "LD_CHILD_MILD_PLATE",
        },
        "toddler": {"lunch": "LD_CHILD_MILD_PLATE", "dinner": "LD_CHILD_MILD_PLATE"},
        "school_child": {"lunch": "LD_CHILD_MILD_PLATE", "dinner": "LD_CHILD_MILD_PLATE"},
        "elder": {"lunch": "LD_ELDERLY_SOFT_DIGESTIVE", "dinner": "LD_ELDERLY_SOFT_DIGESTIVE"},
    }
    addons = []
    for index, member in enumerate(hh.get("q12_member_ages") or []):
        role = member.get("role") if isinstance(member, dict) else None
        if not isinstance(role, str):
            continue
        class_code = addon_classes.get(role, {}).get(request.get("slot", "dinner"))
        if not class_code:
            continue
        addon = planner.dishes_for_class(
            hh,
            request.get("slot", "dinner"),
            class_code,
            catalogue=catalogue,
            n=1,
            weekday=request.get("weekday", "Monday"),
            context=request.get("context") or {},
            exclude_dish_names=request.get("exclude_dish_names") or [],
            preference_by_dish=request.get("preference_by_dish") or {},
        )
        if addon["options"]:
            view = addon["options"][0]
            media.attach_image(view)
            addons.append(
                {
                    "member_index": index,
                    "member_role": role,
                    "class_code": class_code,
                    "dish": view,
                }
            )
    res["addons"] = addons
    return res


def plan_weekly(request: dict[str, Any], catalogue, config) -> dict[str, Any]:
    """Surface 3: the weekly class plan (7 days × slots, top-3 dish-backed classes each)."""
    hh = build_household_dict(request["household"])
    return planner.weekly_class_plan(
        hh, top_classes=int(request.get("top_classes", 3)), catalogue=catalogue
    )


def plan_class_dishes(request: dict[str, Any], catalogue, config) -> dict[str, Any]:
    """Surface 4: RECONCILIATION — only dishes of a finalized class for that day/slot."""
    hh = build_household_dict(request["household"])
    res = planner.dishes_for_class(
        hh,
        request["slot"],
        request["class_code"],
        catalogue,
        n=int(request.get("count", 8)),
        weekday=request.get("weekday", "Monday"),
        context=request.get("context") or {},
        exclude_dish_names=request.get("exclude_dish_names") or [],
        preference_by_dish=request.get("preference_by_dish") or {},
    )
    _with_images(res["options"])
    return res


def plan_search(request: dict[str, Any], catalogue, config) -> dict[str, Any]:
    """Safety-aware full-catalogue search and structured filters."""
    hh = build_household_dict(request["household"])
    res = planner.search_dishes(
        hh,
        catalogue=catalogue,
        query=request.get("query", ""),
        cuisine=request.get("cuisine"),
        diet=request.get("diet"),
        slot=request.get("slot"),
        max_total_mins=request.get("max_total_mins"),
        limit=request.get("limit", 30),
        weekday=request.get("weekday", "Monday"),
        context=request.get("context") or {},
    )
    _with_images(res["options"])
    return res


def recipe_detail(request: dict[str, Any]) -> dict[str, Any]:
    """Surface 5: full recipe + image for one dish (the meal-detail screen)."""
    name = request["dish_name"]
    return {"dish_name": name, "image_url": media.image_url(name), "recipe": media.recipe_for(name)}


def run(request: dict[str, Any], catalogue, config, registry) -> dict[str, Any]:
    """Full request → response.

    `catalogue`/`config`/`registry` come from the providers at startup.
    """
    request_id = request.get("request_id") or str(uuid.uuid4())
    hh = build_household_dict(request["household"])
    ctx = build_context(request["context"], request.get("exclude_dish_ids"))
    ctx["_rng_seed"] = _request_rng_seed(hh, request["context"])
    objective = hh.get("q15_objective") or config.default_objective
    want_trace = bool(request.get("include_decision_trace"))

    # the ONE implementation of the math; with_trace is opt-in and never changes which plates
    # are served (decision_log module's own LOGGING-ONLY invariant, covered by
    # ghar_re_core/tests/test_pipeline.py::
    # test_decision_trace_never_changes_which_plates_are_served)
    result = core_pipeline.recommend(hh, ctx, catalogue, with_trace=want_trace)
    plates_out: list[dict] = []
    warnings: list[str] = []

    for i, p in enumerate(result["plates"]):
        principal, heroes = _principal_hero(p)
        base_total, contributions = compose_base(principal, result["theta"], ctx, config, registry)
        gain = S.gain_q15(principal, objective)
        plates_out.append(
            {
                "plate_id": str(uuid.uuid5(uuid.NAMESPACE_OID, f"{request_id}:{i}")),
                "form": p["form"],
                "hero_dish_ids": [h.id for h in heroes],
                "hero_dish_names": [h.name for h in heroes],
                "support": p.get("support"),
                "is_standalone": p["form"] == "standalone",
                "plate_score": round(p["score"], 6),
                "base_total": round(base_total, 6),  # fixed aggregate
                "gain_multiplier": round(gain, 6),  # fixed aggregate
                "final_score": round(p["score"], 6),  # fixed aggregate
                "contributions": contributions,  # OPEN list (RE-DOC-11 §6)
            }
        )

    if len(plates_out) < TARGET_PLATES:
        warnings.append(
            f"only {len(plates_out)} of {TARGET_PLATES} plates could be formed "
            "for this household/context"
        )

    response = {
        "request_id": request_id,
        "api_version": API_VERSION,
        "engine_version": ENGINE_VERSION,
        "config_version": config.versions["config"],
        "plates": plates_out,
        "warnings": warnings,
    }
    if want_trace and result.get("decision_trace") is not None:
        response["decision_trace"] = result["decision_trace"]
    return response
