/**
 * POST /v1/plan — WP-18 planning surfaces (business handler).
 *
 * THIN orchestration, same frozen boundary as recommendations/handler.ts (Edge owns auth/DB, the RE
 * owns the math). One function multiplexes the five planning surfaces via `body.surface`:
 *   cold_start    -> RE /v1/cold-start     (15 diverse dishes to seed preferences)
 *   calibration   -> RE /v1/calibration    (3 slots x 5 dishes: dish-pick calibration grid)
 *   meal_plan     -> RE /v1/meal-plan      (a slot's 4–5 dish options)
 *   meal_episodes -> RE /v1/meal-episodes  (complete meal episodes + practicality)
 *   weekly_plan   -> RE /v1/weekly-plan    (7 days × slots, top-3 classes each)
 *   class_dishes  -> RE /v1/class-dishes   (reconciliation: dishes of a finalized class)
 *   recipe        -> RE /v1/recipe         (recipe + image for one dish; no household needed)
 *   history       -> (no RE call, P1-3)    (the caller's own recent recommendation_events rows)
 *   profile       -> (no RE call, P1-4)    (the caller's own current diet/allergen/household answers)
 *
 * Flow: authenticate (middleware) → requireHouseholdRole → loadHouseholdRaw (compose from live tables,
 * reused from recommendations/compose.ts) → signed call to the RE surface (re-client, path per
 * surface) → pass the RE body through as-is. No recommendation math here.
 */
import { requireAuth } from "../_shared/auth/authorize.ts";
import {
  HOUSEHOLD_PLAN_WRITE_ROLES,
  HOUSEHOLD_READ_ROLES,
  type HouseholdRoleLookup,
  requireHouseholdRole,
} from "../_shared/auth/household.ts";
import { jsonContract } from "../_shared/api/response.ts";
import { AppError } from "../_shared/errors/app-error.ts";
import { API_ERRORS } from "../_shared/errors/api-catalogue.ts";
import { ERROR_CATALOGUE } from "../_shared/errors/catalogue.ts";
import type { Handler } from "../_shared/middleware/types.ts";

import { loadHouseholdRaw, recordHouseholdContext } from "../recommendations/compose.ts";
import {
  fetchRecentRecommendationEvents,
  fetchRecommendationEvent,
  recordRecommendationEvent,
} from "../recommendations/events.ts";
import { callRecommendationEngine } from "../recommendations/re-client.ts";
import { loadOnlineRecommendationState } from "../recommendations/personalization.ts";
import { addDishToDate, loadSavedWeek, saveWeek, setSlotLock } from "./state.ts";
import { recordProductEvent } from "../_shared/analytics/product-events.ts";
import { loadWeatherContext } from "../_shared/services/weather.ts";
import { recordMealEpisodeSlate } from "./episodes.ts";

const SERVICE_NAME = "plan";

export interface PlanDeps {
  authorizeHousehold?: HouseholdRoleLookup;
}

// surface -> { RE path, whether it needs the composed household }
const SURFACES: Record<string, { path: string; needsHousehold: boolean }> = {
  cold_start: { path: "/v1/cold-start", needsHousehold: true },
  calibration: { path: "/v1/calibration", needsHousehold: true },
  meal_plan: { path: "/v1/meal-plan", needsHousehold: true },
  meal_episodes: { path: "/v1/meal-episodes", needsHousehold: true },
  weekly_plan: { path: "/v1/weekly-plan", needsHousehold: true },
  class_dishes: { path: "/v1/class-dishes", needsHousehold: true },
  recipe: { path: "/v1/recipe", needsHousehold: false },
  search: { path: "/v1/search", needsHousehold: true },
};

/** Build the POST /v1/plan handler. */
export function makePlanHandler(deps: PlanDeps = {}): Handler {
  return async (req, ctx) => {
    if (req.method !== "POST") {
      throw new AppError(ERROR_CATALOGUE.METHOD_NOT_ALLOWED);
    }
    const claims = requireAuth(ctx.claims);

    let body: Record<string, unknown> = {};
    try {
      const text = await req.text();
      if (text) body = JSON.parse(text) as Record<string, unknown>;
    } catch {
      throw new AppError(API_ERRORS.ERR_VALIDATION_FAILED, {
        detail: "request body is not valid JSON",
      });
    }

    const surface = typeof body.surface === "string" ? body.surface : "";

    if (["saved_week", "save_week", "lock_slot", "add_to_date"].includes(surface)) {
      const householdId = (typeof body.household_id === "string" ? body.household_id : null) ??
        claims.userId ?? null;
      await requireHouseholdRole(
        ctx,
        claims,
        householdId,
        surface === "saved_week" ? HOUSEHOLD_READ_ROLES : HOUSEHOLD_PLAN_WRITE_ROLES,
        deps.authorizeHousehold,
      );
      if (!householdId) throw new AppError(API_ERRORS.ERR_VALIDATION_FAILED);
      try {
        if (surface === "saved_week") {
          return jsonContract(
            {
              kind: "saved_week",
              plan: await loadSavedWeek(
                ctx,
                householdId,
                typeof body.slot_date === "string" ? body.slot_date : undefined,
              ),
            },
            ctx.traceId,
            200,
          );
        }
        if (surface === "save_week") {
          const selections = body.selections && typeof body.selections === "object"
            ? body.selections as Record<string, Record<string, string>>
            : {};
          const plan = await saveWeek(ctx, householdId, selections, body.finalize === true);
          return jsonContract({ kind: "saved_week", plan }, ctx.traceId, 200);
        }
        if (surface === "add_to_date") {
          const state = await addDishToDate(
            ctx,
            householdId,
            String(body.slot_date ?? ""),
            String(body.slot ?? ""),
            String(body.class_code ?? ""),
            String(body.dish_name ?? ""),
          );
          await recordProductEvent(ctx, {
            profileId: householdId,
            eventName: "recommendation_add_to_date",
            properties: {
              slot_date: body.slot_date,
              slot: body.slot,
              dish_name: body.dish_name,
            },
          });
          return jsonContract({ kind: "add_to_date", slot: state }, ctx.traceId, 200);
        }
        const state = await setSlotLock(
          ctx,
          householdId,
          String(body.weekday ?? ""),
          String(body.slot ?? ""),
          body.locked === true,
          typeof body.slot_date === "string" ? body.slot_date : undefined,
        );
        return jsonContract({ kind: "slot_lock", slot: state }, ctx.traceId, 200);
      } catch (error) {
        throw new AppError(API_ERRORS.ERR_VALIDATION_FAILED, {
          detail: error instanceof Error ? error.message : String(error),
        });
      }
    }

    // "history" (P1-3, 2026-08) is a pure read -- no RE call, no household composition, just the
    // caller's own recommendation_events rows. Handled as a special case rather than added to
    // SURFACES below, since every entry there implies "call the RE"; history never does.
    if (surface === "history") {
      const householdIdForHistory =
        (typeof body.household_id === "string" ? body.household_id : null) ??
          claims.userId ?? null;
      await requireHouseholdRole(
        ctx,
        claims,
        householdIdForHistory,
        HOUSEHOLD_READ_ROLES,
        deps.authorizeHousehold,
      );
      if (!householdIdForHistory) throw new AppError(API_ERRORS.ERR_VALIDATION_FAILED);
      const limit = typeof body.count === "number" && body.count > 0
        ? Math.min(body.count, 50)
        : 20;
      const events = await fetchRecentRecommendationEvents(ctx, householdIdForHistory, limit);
      return jsonContract({ kind: "history", events }, ctx.traceId, 200);
    }

    if (surface === "history_detail") {
      const householdId = (typeof body.household_id === "string" ? body.household_id : null) ??
        claims.userId ?? null;
      await requireHouseholdRole(
        ctx,
        claims,
        householdId,
        HOUSEHOLD_READ_ROLES,
        deps.authorizeHousehold,
      );
      const eventId = typeof body.event_id === "string" ? body.event_id : "";
      if (!householdId || !eventId) {
        throw new AppError(API_ERRORS.ERR_VALIDATION_FAILED, { detail: "event_id is required" });
      }
      const event = await fetchRecommendationEvent(ctx, householdId, eventId);
      if (!event) {
        throw new AppError(API_ERRORS.ERR_RECOMMENDATION_EVENT_NOT_FOUND, {
          detail: "history event not found",
        });
      }
      return jsonContract({ kind: "history_detail", event }, ctx.traceId, 200);
    }

    // "profile" (P1-4, 2026-08) is also a pure read: the same composed household object
    // loadHouseholdRaw already builds for scoring, returned to the caller so a settings/edit
    // screen has something to show. Read-only -- editing still goes through the existing
    // POST /v1/household (this repo's one household-write path); this surface just closes the
    // "there was no way to see current answers before editing them" gap.
    if (surface === "profile") {
      const householdIdForProfile =
        (typeof body.household_id === "string" ? body.household_id : null) ??
          claims.userId ?? null;
      await requireHouseholdRole(
        ctx,
        claims,
        householdIdForProfile,
        HOUSEHOLD_READ_ROLES,
        deps.authorizeHousehold,
      );
      const { household, stubbed } = await loadHouseholdRaw(ctx, householdIdForProfile);
      return jsonContract({ kind: "profile", household, stubbed }, ctx.traceId, 200);
    }

    const spec = SURFACES[surface];
    if (!spec) {
      throw new AppError(API_ERRORS.ERR_VALIDATION_FAILED, {
        detail: `unknown surface '${surface}' (expected: history, ${
          Object.keys(SURFACES).join(", ")
        })`,
      });
    }

    const householdId = (typeof body.household_id === "string" ? body.household_id : null) ??
      claims.userId ?? null;
    await requireHouseholdRole(
      ctx,
      claims,
      householdId,
      HOUSEHOLD_READ_ROLES,
      deps.authorizeHousehold,
    );

    const requestId = (typeof body.request_id === "string" && body.request_id)
      ? body.request_id
      : ctx.traceId;
    const log = ctx.logger.child({ request_id: requestId, service: SERVICE_NAME, surface });

    // Build the RE payload for this surface. Planning params (slot/weekday/class_code/count/
    // dish_name/top_classes) pass straight through; the household is composed from the live tables
    // for the surfaces that need it (never trusted from the client).
    const payload: Record<string, unknown> = { request_id: requestId };
    for (
      const k of [
        "slot",
        "weekday",
        "class_code",
        "count",
        "dish_name",
        "top_classes",
        "query",
        "cuisine",
        "diet",
        "max_total_mins",
        "limit",
        "exclude_dish_names",
      ]
    ) {
      if (body[k] !== undefined) payload[k] = body[k];
    }
    let resolvedHouseholdId: string | undefined;
    let stubbedHousehold = false;
    if (spec.needsHousehold) {
      const { household, householdId: hid, stubbed } = await loadHouseholdRaw(ctx, householdId);
      payload.household = household;
      // Cold-start exploration seed (ghar_re_core.meal_planner.cold_start_top15): a stable
      // per-household RNG seed so two households that land on an identical theta (same cohort
      // answers) don't always converge on the exact same top-n dishes. Harmless for the other
      // surfaces — they don't read household_id from the payload.
      payload.household_id = hid;
      resolvedHouseholdId = hid;
      stubbedHousehold = stubbed;
      const online = await loadOnlineRecommendationState(ctx, hid);
      const weather = await loadWeatherContext(ctx, household.q4_current_city);
      payload.context = {
        slot: body.slot,
        weekday: body.weekday,
        interaction_count: online.interactionCount,
        dish_feedback_counts: online.dishFeedbackCounts,
        weather,
        time_budget_minutes: typeof body.time_budget_minutes === "number"
          ? body.time_budget_minutes
          : undefined,
        pantry_ingredient_names: Array.isArray(body.pantry_ingredient_names)
          ? body.pantry_ingredient_names.filter((value): value is string =>
            typeof value === "string"
          )
          : [],
        leftover_dish_names: Array.isArray(body.leftover_dish_names)
          ? body.leftover_dish_names.filter((value): value is string => typeof value === "string")
          : [],
        discovery_mode: body.discovery_mode === true,
        recovery_mode: body.recovery_mode === true,
      };
      const requestedExclusions = Array.isArray(body.exclude_dish_names)
        ? body.exclude_dish_names
          .filter((name): name is string => typeof name === "string")
          .slice(0, 50)
        : [];
      payload.exclude_dish_names = [
        ...new Set([
          ...online.excludeDishNames,
          ...requestedExclusions,
        ]),
      ];
      payload.preference_by_dish = online.preferenceByDish;
      log.info("plan.composed", { household_id: hid, stubbed });
    }

    const reStart = performance.now();
    const result = await callRecommendationEngine(payload, requestId, ctx.config, log, {
      path: spec.path,
    });
    const latencyMs = Math.round(performance.now() - reStart);

    if (result.ok) {
      log.info("plan.re_call_done", { latency_ms: latencyMs });
      // P0-1 fix (2026-08): every planning surface with a resolved household writes the same
      // household_context row recommendations/handler.ts already writes, via the shared
      // recordHouseholdContext helper. This surface (plan) is the one real traffic actually uses
      // (recommendations/handler.ts has zero live callers) -- household_context had a working
      // writer that was simply never called from here, which is the direct cause of
      // household_context staying at 0 rows despite 126+ served recommendation events. Best-effort
      // (recordHouseholdContext never throws -- see its own try/catch), so this can never turn a
      // successful plan response into a failure. Only slot/weekday are known on this surface (no
      // weather/season resolution happens here, unlike recommendations/compose.ts's buildRequest) --
      // recordHouseholdContext already null-coalesces every other field.
      if (resolvedHouseholdId) {
        await recordHouseholdContext(ctx, resolvedHouseholdId, {
          slot: body.slot,
          weekday: body.weekday,
        });
      }
      // cold_start / calibration / meal_plan / class_dishes: write a recommendation_events row so
      // POST /v1/feedback (which resolves request_id -> recommendation_events, see
      // feedback/events.ts) has something to resolve against. Widened 2026-08 (P0-4) from
      // cold_start/calibration-only to also cover meal_plan/class_dishes -- those are the surfaces
      // the actively-routed Home tab (today.tsx) actually calls, so a like/dislike tap there had
      // nothing to resolve against before this change. weekly_plan/recipe are deliberately excluded:
      // weekly_plan returns classes, not scored dishes, and recipe isn't a recommendation at all.
      // Best-effort (recordRecommendationEvent never throws/never blocks the response, same as
      // recommendations/handler.ts's own call site); skipped for a stubbed (no-profile-yet)
      // household, same guard recordRecommendationEvent already applies itself.
      const FEEDBACK_ELIGIBLE_SURFACES = new Set([
        "cold_start",
        "calibration",
        "meal_plan",
        "class_dishes",
        "meal_episodes",
      ]);
      let slateId: string | undefined;
      if (surface === "meal_episodes" && resolvedHouseholdId) {
        const episodeBody = result.body as Record<string, unknown>;
        slateId = await recordMealEpisodeSlate(ctx, {
          householdId: resolvedHouseholdId,
          requestId,
          slot: typeof body.slot === "string" ? body.slot : undefined,
          weekday: typeof body.weekday === "string" ? body.weekday : undefined,
          classCode: typeof body.class_code === "string" ? body.class_code : undefined,
          modelVersion: String(episodeBody.model_version ?? "unknown"),
          configVersion: String(episodeBody.config_version ?? "unknown"),
          catalogVersion: typeof episodeBody.catalog_version === "string"
            ? episodeBody.catalog_version
            : null,
          policyCode: String(episodeBody.policy_code ?? "episode_success_rule_v1"),
          latencyMs,
          eligibleEpisodeHashes: Array.isArray(episodeBody.eligible_episode_hashes)
            ? episodeBody.eligible_episode_hashes.filter((value): value is string =>
              typeof value === "string"
            )
            : [],
          householdSnapshot: payload.household as Record<string, unknown>,
          requestContext: payload.context && typeof payload.context === "object"
            ? payload.context as Record<string, unknown>
            : {},
          episodes: Array.isArray(episodeBody.episodes)
            ? episodeBody.episodes as Parameters<typeof recordMealEpisodeSlate>[1]["episodes"]
            : [],
        });
      }
      if (FEEDBACK_ELIGIBLE_SURFACES.has(surface) && resolvedHouseholdId) {
        const body = result.body as Record<string, unknown>;
        const dishes = surface === "calibration"
          ? Object.values((body.slots as Record<string, unknown[]>) ?? {}).flat()
          : surface === "meal_episodes"
          ? body.episodes
          : (body.dishes ?? body.options);
        const dishCount = Array.isArray(dishes) ? dishes.length : 0;
        await recordRecommendationEvent(ctx, {
          requestId,
          householdId: resolvedHouseholdId,
          outcome: "success",
          plateCount: dishCount,
          reServed: true,
          plates: dishes,
          latencyMs,
          stubbed: stubbedHousehold,
          slot: typeof body.slot === "string" ? body.slot : undefined,
        });
        await recordProductEvent(ctx, {
          profileId: resolvedHouseholdId,
          eventName: "recommendation_slate_served",
          requestId,
          properties: {
            surface,
            slot: body.slot ?? null,
            dish_count: dishCount,
            latency_ms: latencyMs,
          },
        });
      }
      // Pass the RE body through as-is (RE-DOC-11 §6), additively stamping the trace id AND
      // request_id — unlike /v1/recommendations (engine.py's run() echoes request_id itself),
      // none of the WP-18 planning surfaces (meal_planner.py) take or return request_id, so the
      // client would otherwise have no way to reference this call in a later POST /v1/feedback
      // (feedback/events.ts resolves by request_id + profile_id against recommendation_events —
      // see the cold_start write above). Stamping the SAME requestId used for that write, not
      // ctx.traceId, guarantees they always match even if a caller ever supplies its own
      // request_id in the body.
      return jsonContract(
        { ...result.body, request_id: requestId, slate_id: slateId },
        ctx.traceId,
        200,
      );
    }

    // Planning surfaces have no fallback plate (unlike recommendations) — surface a clean error the
    // app can retry, never a fabricated plan.
    log.warn("plan.re_call_failed", {
      outcome: result.kind,
      detail: result.detail,
      latency_ms: latencyMs,
    });
    return jsonContract(
      { error: "planning_unavailable", detail: result.detail, surface },
      ctx.traceId,
      503,
    );
  };
}
