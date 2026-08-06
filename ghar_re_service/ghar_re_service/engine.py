"""
engine — composition/translation layer (NO recommendation math here).

Translates a contract request into the shape ghar_re_core expects, calls the ONE tested pipeline
(ghar_re_core.pipeline.recommend — same math the 16 tests cover), then serializes the result into
the Phase A response, populating the open `contributions[]` via the ScoringModule registry.

If a formula appears to be needed here, it belongs in ghar_re_core, not this file.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import uuid
from typing import Any

from ghar_re_core import calibration as calib
from ghar_re_core import meal_episode, preference, taste
from ghar_re_core import meal_planner as planner
from ghar_re_core import model_provider as preference_models
from ghar_re_core import pipeline as core_pipeline
from ghar_re_core import scoring as S
from ghar_re_core.derivation import derive_theta
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


def build_context(
    ctx: dict[str, Any],
    exclude_dish_ids: list[str] | None = None,
    exclude_dish_names: list[str] | None = None,
    preference_by_dish: dict[str, float] | None = None,
) -> dict[str, Any]:
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
    core_ctx["exclude_dish_names"] = exclude_dish_names or []
    core_ctx["preference_by_dish"] = preference_by_dish or {}
    # These are online, household-specific features composed by the Edge layer.  Keeping them
    # here is essential: cohort decay and exploration both read the core context, not the raw
    # HTTP request.  Previously the JSON contract accepted interaction_count but this translation
    # silently dropped it, leaving every returning household in cold-start weighting forever.
    core_ctx["interaction_count"] = max(0, int(ctx.get("interaction_count", 0) or 0))
    feedback_counts = ctx.get("dish_feedback_counts")
    core_ctx["dish_feedback_counts"] = feedback_counts if isinstance(feedback_counts, list) else []
    # Episode/practicality inputs are additive v1 context. They do not alter hard eligibility;
    # ghar_re_core.meal_episode consumes them only after the safe plate pool has been formed.
    if ctx.get("time_budget_minutes") is not None:
        core_ctx["time_budget_minutes"] = max(0, int(ctx["time_budget_minutes"]))
    core_ctx["pantry_ingredient_names"] = [
        value for value in (ctx.get("pantry_ingredient_names") or []) if isinstance(value, str)
    ][:250]
    core_ctx["leftover_dish_names"] = [
        value for value in (ctx.get("leftover_dish_names") or []) if isinstance(value, str)
    ][:50]
    core_ctx["discovery_mode"] = bool(ctx.get("discovery_mode", False))
    core_ctx["recovery_mode"] = bool(ctx.get("recovery_mode", False))
    core_ctx["refresh_generation"] = max(0, int(ctx.get("refresh_generation", 0) or 0))
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


def _with_shadow_preferences(
    views: list[dict],
    household: dict[str, Any],
    raw_context: dict[str, Any],
    catalogue,
    config,
    *,
    slot: str | None = None,
    name_key: str = "name",
) -> list[dict]:
    """Attach score-only model output to served views without changing their order or score."""
    if getattr(config, "pref_model_mode", "disabled") != "shadow":
        return views
    artifact = preference_models.active_model().artifact
    if artifact is None:
        raise RuntimeError("Shadow preference mode has no loaded artifact")
    metadata = getattr(artifact, "metadata", {})
    model_version = metadata.get("model_version") if isinstance(metadata, dict) else None
    theta = derive_theta(household)
    for view in views:
        dish_name = view.get(name_key)
        dish = catalogue.get(dish_name) if isinstance(dish_name, str) else None
        if dish is None:
            continue
        item_context = dict(raw_context)
        item_context["slot"] = view.get("slot") or slot or raw_context.get("slot", "dinner")
        ctx = build_context(item_context)
        prediction = preference.loaded_preference_score(dish, theta, ctx)
        if prediction is not None:
            view["shadow_preference_score"] = round(prediction, 6)
            view["shadow_preference_model_version"] = model_version
    return views


def _online_taste(request: dict[str, Any], catalogue) -> tuple[list[str], dict[str, float]]:
    """Canonicalize exposure state and derive bounded semantic affinity once per request."""
    excluded = taste.canonicalize_names(request.get("exclude_dish_names") or [], catalogue)
    preferences = taste.expand_preferences(
        request.get("preference_by_dish") or {},
        catalogue,
        preference_by_class=request.get("preference_by_class") or {},
        preference_by_tag=request.get("preference_by_tag") or {},
    )
    return excluded, preferences


def plan_cold_start(request: dict[str, Any], catalogue, config) -> dict[str, Any]:
    """Surface 1: post-onboarding top-15 preference primer (diverse top dishes)."""
    hh = build_household_dict(request["household"])
    n = int(request.get("count", 15))
    excluded, preferences = _online_taste(request, catalogue)
    context = request.get("context") or {}
    refresh_generation = max(0, int(context.get("refresh_generation", 0) or 0))
    date_salt = str(context.get("date") or datetime.date.today().isoformat())
    res = planner.cold_start_top15(
        hh,
        catalogue,
        n=n,
        weekday=request.get("weekday", "Monday"),
        household_id=request.get("household_id"),
        variety_salt=f"{date_salt}:{refresh_generation}",
        exclude_dish_names=excluded,
        preference_by_dish=preferences,
        richness_debt=context.get("richness_debt", 0),
    )
    _with_images(res["dishes"])
    _with_shadow_preferences(
        res["dishes"], hh, {"weekday": request.get("weekday", "Monday")}, catalogue, config
    )
    _with_shadow_preferences(
        res["_candidate_lineage"],
        hh,
        {"weekday": request.get("weekday", "Monday")},
        catalogue,
        config,
    )
    return res


def plan_calibration(request: dict[str, Any], catalogue, config) -> dict[str, Any]:
    """WP-18 dish-pick surface: 3 slots x 5 dishes (3 expected-positive + 2 planted-mismatch,
    cell_role never surfaced to the client) for the post-onboarding calibration grid."""
    hh = build_household_dict(request["household"])
    excluded, preferences = _online_taste(request, catalogue)
    res = calib.calibration_grid(
        hh,
        catalogue,
        weekday=request.get("weekday", "Monday"),
        household_id=request.get("household_id"),
        exclude_dish_names=excluded,
        preference_by_dish=preferences,
    )
    for slot, slot_dishes in res["slots"].items():
        _with_images(slot_dishes)
        _with_shadow_preferences(
            slot_dishes,
            hh,
            {"weekday": request.get("weekday", "Monday")},
            catalogue,
            config,
            slot=slot,
        )
    _with_shadow_preferences(
        res["_candidate_lineage"],
        hh,
        {"weekday": request.get("weekday", "Monday")},
        catalogue,
        config,
    )
    return res


def plan_slot(request: dict[str, Any], catalogue, config) -> dict[str, Any]:
    """Surface 2 (and 4 when class_code is set): a slot's 4–5 dish options."""
    hh = build_household_dict(request["household"])
    excluded, preferences = _online_taste(request, catalogue)
    res = planner.slot_options(
        hh,
        request.get("slot", "dinner"),
        catalogue,
        n=int(request.get("count", 8)),
        weekday=request.get("weekday", "Monday"),
        class_code=request.get("class_code"),
        context=request.get("context") or {},
        exclude_dish_names=excluded,
        preference_by_dish=preferences,
    )
    _with_images(res["options"])
    _with_shadow_preferences(
        res["options"],
        hh,
        request.get("context") or {},
        catalogue,
        config,
        slot=request.get("slot", "dinner"),
    )
    _with_shadow_preferences(
        res["_candidate_lineage"],
        hh,
        request.get("context") or {},
        catalogue,
        config,
        slot=request.get("slot", "dinner"),
    )
    # Deterministic lifecycle add-ons remain separate from the household's primary meal.  These
    # are food-role rules only; health-condition add-ons intentionally require clinical review.
    addon_classes = {
        "infant": {
            "breakfast": "BF_INFANT_6M_SOFT",
            "lunch": "LD_CHILD_MILD_PLATE",
            "dinner": "LD_CHILD_MILD_PLATE",
        },
        # `recommendations/compose.ts` emits the live household-member vocabulary below. Keep the
        # historical core aliases too so fixtures and older callers remain compatible.
        "weaning": {
            "breakfast": "BF_INFANT_6M_SOFT",
            "lunch": "LD_CHILD_MILD_PLATE",
            "dinner": "LD_CHILD_MILD_PLATE",
        },
        "toddler": {"lunch": "LD_CHILD_MILD_PLATE", "dinner": "LD_CHILD_MILD_PLATE"},
        "school_child": {"lunch": "LD_CHILD_MILD_PLATE", "dinner": "LD_CHILD_MILD_PLATE"},
        "child": {"lunch": "LD_CHILD_MILD_PLATE", "dinner": "LD_CHILD_MILD_PLATE"},
        "elder": {"lunch": "LD_ELDERLY_SOFT_DIGESTIVE", "dinner": "LD_ELDERLY_SOFT_DIGESTIVE"},
        "senior": {"lunch": "LD_ELDERLY_SOFT_DIGESTIVE", "dinner": "LD_ELDERLY_SOFT_DIGESTIVE"},
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
            exclude_dish_names=excluded,
            preference_by_dish=preferences,
        )
        if addon["options"]:
            view = addon["options"][0]
            media.attach_image(view)
            _with_shadow_preferences(
                [view],
                hh,
                request.get("context") or {},
                catalogue,
                config,
                slot=request.get("slot", "dinner"),
            )
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
    _, preferences = _online_taste(request, catalogue)
    return planner.weekly_class_plan(
        hh,
        top_classes=int(request.get("top_classes", 3)),
        catalogue=catalogue,
        preference_by_dish=preferences,
    )


def plan_class_dishes(request: dict[str, Any], catalogue, config) -> dict[str, Any]:
    """Surface 4: RECONCILIATION — only dishes of a finalized class for that day/slot."""
    hh = build_household_dict(request["household"])
    excluded, preferences = _online_taste(request, catalogue)
    res = planner.dishes_for_class(
        hh,
        request["slot"],
        request["class_code"],
        catalogue,
        n=int(request.get("count", 8)),
        weekday=request.get("weekday", "Monday"),
        context=request.get("context") or {},
        exclude_dish_names=excluded,
        preference_by_dish=preferences,
    )
    _with_images(res["options"])
    _with_shadow_preferences(
        res["options"],
        hh,
        request.get("context") or {},
        catalogue,
        config,
        slot=request["slot"],
    )
    _with_shadow_preferences(
        res["_candidate_lineage"],
        hh,
        request.get("context") or {},
        catalogue,
        config,
        slot=request["slot"],
    )
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
    _with_shadow_preferences(
        res["options"],
        hh,
        request.get("context") or {},
        catalogue,
        config,
        slot=request.get("slot", "dinner"),
    )
    _with_shadow_preferences(
        res["_candidate_lineage"],
        hh,
        request.get("context") or {},
        catalogue,
        config,
        slot=request.get("slot", "dinner"),
    )
    return res


def plan_meal_episodes(request: dict[str, Any], catalogue, config) -> dict[str, Any]:
    """Return complete, safe meal episodes ranked by choose × execute × no-regret.

    The core meal-episode module owns all intent/practicality mathematics. This service function
    only translates request context, attaches media, and serializes the result.
    """
    household = build_household_dict(request["household"])
    raw_context = request.get("context") or {
        "slot": request.get("slot", "dinner"),
        "weekday": request.get("weekday", "Monday"),
    }
    excluded, preferences = _online_taste(request, catalogue)
    context = build_context(
        raw_context,
        exclude_dish_names=excluded,
        preference_by_dish=preferences,
    )
    context["diversity_policy"] = "home_v2"
    context["_rng_seed"] = _request_rng_seed(household, raw_context)
    count = max(1, min(int(request.get("count", 4)), 8))
    class_code = request.get("class_code")
    if isinstance(class_code, str) and class_code:
        all_episodes = meal_episode.build_class_meal_episodes(
            household,
            context,
            class_code,
            catalogue,
            count=8,
            exclude_dish_names=excluded,
            preference_by_dish=preferences,
        )
    else:
        result = core_pipeline.recommend(household, context, catalogue)
        all_episodes = meal_episode.build_meal_episodes(result["plates"], household, context)
    # Final visible-prefix guard: the plate pool is already diverse, but episode success ranking
    # can otherwise pull every rich plate (or several soups) back into the top four.
    episodes = _select_visible_episode_diversity(all_episodes, count)
    for rank, episode in enumerate(episodes, 1):
        episode["rank"] = rank
        for component in episode["components"]:
            if component["dish_id"] is not None:
                component["image_url"] = media.image_url(component["dish_name"])
        _with_shadow_preferences(
            episode["components"],
            household,
            raw_context,
            catalogue,
            config,
            slot=context["slot"],
            name_key="dish_name",
        )
        shadow_scores = [
            component["shadow_preference_score"]
            for component in episode["components"]
            if "shadow_preference_score" in component
        ]
        if shadow_scores:
            episode["shadow_preference_mean"] = round(sum(shadow_scores) / len(shadow_scores), 6)
    return {
        "kind": "meal_episode_slate",
        "slot": context["slot"],
        "episodes": episodes,
        # This is the complete deterministic episode set considered before the response-size cut.
        # The Edge layer hashes it into the immutable exposure record for exact replay semantics.
        "eligible_episode_hashes": [item["episode_hash"] for item in all_episodes],
        "policy_code": "episode_success_rule_v1",
        "model_version": meal_episode.EPISODE_MODEL_VERSION,
        "warnings": [] if episodes else ["no safe meal episode could be formed"],
    }


def _select_visible_episode_diversity(episodes: list[dict], count: int) -> list[dict]:
    selected, deferred = [], []
    rich_count = soup_count = 0
    rich_cap = max(1, (count + 1) // 2)
    for episode in episodes:
        is_rich = float(episode.get("richness_score", 0.0) or 0.0) >= 0.6
        is_soup = any(
            "soup" in str(component.get("dish_name", "")).casefold()
            for component in episode.get("components", [])
        )
        if (is_rich and rich_count >= rich_cap) or (is_soup and soup_count >= 1):
            deferred.append(episode)
            continue
        selected.append(episode)
        rich_count += int(is_rich)
        soup_count += int(is_soup)
        if len(selected) >= count:
            return selected
    for episode in deferred:
        selected.append(episode)
        if len(selected) >= count:
            break
    return selected


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
    excluded, preferences = _online_taste(request, catalogue)
    ctx = build_context(
        request["context"],
        request.get("exclude_dish_ids"),
        exclude_dish_names=excluded,
        preference_by_dish=preferences,
    )
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
        shadow_view = {"name": principal.name}
        _with_shadow_preferences(
            [shadow_view],
            hh,
            request["context"],
            catalogue,
            config,
            slot=ctx["slot"],
        )
        if "shadow_preference_score" in shadow_view:
            plates_out[-1]["shadow_preference_score"] = shadow_view["shadow_preference_score"]
            plates_out[-1]["shadow_preference_model_version"] = shadow_view[
                "shadow_preference_model_version"
            ]

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
