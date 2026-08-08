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

import {
  applyFestivalContext,
  loadFestivalContext,
  loadHouseholdRaw,
  recordHouseholdContext,
} from "../recommendations/compose.ts";
import {
  fetchRecentRecommendationEvents,
  fetchRecommendationEvent,
  recordRecommendationEvent,
} from "../recommendations/events.ts";
import { callRecommendationEngine } from "../recommendations/re-client.ts";
import { loadOnlineRecommendationState } from "../recommendations/personalization.ts";
import {
  deriveGovernedContextSignals,
  type GovernedContextSignal,
  mergeGovernedContextSignals,
} from "../recommendations/governed-context.ts";
import {
  type AuxResult,
  buildAuxiliaryRequest,
  buildAuxShadowObservation,
  buildProductionGuardrailObservation,
  callAuxiliaryEngine,
} from "../recommendations/aux-client.ts";
import { addDishToDate, loadSavedWeek, saveWeek, setSlotLock } from "./state.ts";
import { recordProductEvent } from "../_shared/analytics/product-events.ts";
import { loadWeatherContext } from "../_shared/services/weather.ts";
import {
  recordDishRecommendationSlate,
  recordMealEpisodeSlate,
  stripPrivateCandidateLineage,
} from "./episodes.ts";

const SERVICE_NAME = "plan";

function plannedDayType(value: unknown): "weekday" | "weekend" | undefined {
  if (typeof value !== "string" || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return undefined;
  const day = new Date(`${value}T12:00:00Z`).getUTCDay();
  return day === 0 || day === 6 ? "weekend" : "weekday";
}

export interface PlanDeps {
  authorizeHousehold?: HouseholdRoleLookup;
  callAux?: typeof callAuxiliaryEngine;
  loadHousehold?: typeof loadHouseholdRaw;
  loadOnlineState?: typeof loadOnlineRecommendationState;
  loadWeather?: typeof loadWeatherContext;
  loadFestival?: typeof loadFestivalContext;
  callRe?: typeof callRecommendationEngine;
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
  const callAux = deps.callAux ?? callAuxiliaryEngine;
  const loadHousehold = deps.loadHousehold ?? loadHouseholdRaw;
  const loadOnlineState = deps.loadOnlineState ?? loadOnlineRecommendationState;
  const loadWeather = deps.loadWeather ?? loadWeatherContext;
  const loadFestival = deps.loadFestival ?? loadFestivalContext;
  const callRe = deps.callRe ?? callRecommendationEngine;
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
            profileId: claims.userId,
            householdId,
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
      const { household, stubbed } = await loadHousehold(ctx, householdIdForProfile);
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
    let governedContextSignals: GovernedContextSignal[] = [];
    let derivedGovernedContextSignals: GovernedContextSignal[] = [];
    if (spec.needsHousehold) {
      const { household, householdId: hid, stubbed } = await loadHousehold(ctx, householdId);
      payload.household = household;
      // Cold-start exploration seed (ghar_re_core.meal_planner.cold_start_top15): a stable
      // per-household RNG seed so two households that land on an identical theta (same cohort
      // answers) don't always converge on the exact same top-n dishes. Harmless for the other
      // surfaces — they don't read household_id from the payload.
      payload.household_id = hid;
      derivedGovernedContextSignals = deriveGovernedContextSignals(household);
      resolvedHouseholdId = hid;
      stubbedHousehold = stubbed;
      const online = await loadOnlineState(ctx, hid);
      governedContextSignals = mergeGovernedContextSignals(
        derivedGovernedContextSignals,
        online.governedContextSignals,
      );
      const weather = await loadWeather(ctx, household.q4_current_city);
      const festival = await loadFestival(
        ctx,
        typeof body.date === "string" ? body.date : undefined,
      );
      payload.context = applyFestivalContext({
        slot: body.slot,
        weekday: body.weekday,
        date: body.date,
        active_modes: Array.isArray(body.active_modes) ? body.active_modes : [],
        interaction_count: online.interactionCount,
        dish_feedback_counts: online.dishFeedbackCounts,
        recent_class_counts: online.recentClassCounts,
        recent_cuisine_counts: online.recentCuisineCounts,
        novelty_budget: online.noveltyBudget,
        richness_debt: online.richnessDebt,
        temporal_class_state: online.temporalClassState,
        temporal_attribute_state: online.temporalAttributeState,
        governed_context_signals: governedContextSignals,
        // The v1 contract types `weather` as an object when present. Provider configuration is
        // optional, so omit the field when weather is unavailable instead of sending `null`,
        // which the stricter meal-episode request validator correctly rejects with HTTP 422.
        ...(weather ? { weather } : {}),
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
        // The RE mixes this monotonic client value into its deterministic request seed. Without
        // forwarding it, Regenerate issued a real network request but replayed identical ranking.
        refresh_generation: typeof body.refresh_generation === "number"
          ? Math.max(0, Math.trunc(body.refresh_generation))
          : 0,
      }, festival);
      const requestedExclusions = Array.isArray(body.exclude_dish_names)
        ? body.exclude_dish_names
          .filter((name): name is string => typeof name === "string")
          .slice(0, 50)
        : [];
      payload.exclude_dish_names = [
        ...new Set([
          ...online.excludeDishNames,
          ...(body.exclude_recently_served === false ? [] : online.recentExposureDishNames),
          ...requestedExclusions,
        ]),
      ].slice(0, 50);
      payload.preference_by_dish = online.preferenceByDish;
      payload.preference_by_class = online.preferenceByClass;
      payload.preference_by_direct_class = online.preferenceByDirectClass;
      payload.preference_by_projected_class = online.preferenceByProjectedClass;
      payload.preference_by_tag = online.preferenceByTag;
      log.info("plan.composed", { household_id: hid, stubbed });
    }

    // Meal episodes are the user-visible dish-composition surface covered by the bounded Ghar
    // contract. Aux runs only as optional shadow retrieval; all errors preserve bundle serving.
    let auxResult: AuxResult | null = null;
    if (surface === "meal_episodes" && resolvedHouseholdId) {
      const aux = await callAux(
        buildAuxiliaryRequest(payload, claims.userId, resolvedHouseholdId),
        requestId,
        ctx.config,
        log,
      );
      auxResult = aux;
      if (aux.ok) {
        if (ctx.config.auxReMode === "active") payload.candidate_dish_ids = aux.candidateIds;
        log.info("aux_re.candidates_retrieved", {
          candidate_count: aux.candidateIds.length,
          publication_version: aux.publicationVersion,
          latency_ms: aux.latencyMs,
          surface,
          mode: ctx.config.auxReMode,
          applied_to_ghar: ctx.config.auxReMode === "active",
        });
      } else if (aux.reason !== "disabled") {
        log.warn("aux_re.shadow_unavailable", {
          reason: aux.reason,
          latency_ms: aux.latencyMs,
          surface,
        });
      }
    }

    const reStart = performance.now();
    const result = await callRe(payload, requestId, ctx.config, log, {
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
      // nothing to resolve against before this change. weekly_plan is now included so a direct
      // class selection has request lineage; recipe remains excluded because it is content detail.
      // Durable event lineage is required for non-stubbed feedback-capable responses. Stubbed
      // households still have no referentially valid profile row, so the writer skips them.
      const FEEDBACK_ELIGIBLE_SURFACES = new Set([
        "cold_start",
        "calibration",
        "meal_plan",
        "class_dishes",
        "meal_episodes",
        "weekly_plan",
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
            : episodeBody.catalogue_selection &&
                typeof episodeBody.catalogue_selection === "object" &&
                typeof (episodeBody.catalogue_selection as Record<string, unknown>)
                    .publication_version === "string"
            ? String(
              (episodeBody.catalogue_selection as Record<string, unknown>).publication_version,
            )
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
      } else if (
        resolvedHouseholdId &&
        ["cold_start", "calibration", "meal_plan", "class_dishes"].includes(surface)
      ) {
        const dishBody = result.body as Record<string, unknown>;
        slateId = await recordDishRecommendationSlate(ctx, {
          householdId: resolvedHouseholdId,
          requestId,
          surface: surface as "cold_start" | "calibration" | "meal_plan" | "class_dishes",
          modelVersion: String(
            dishBody.model_version ?? dishBody.engine_version ?? "ghar-re-rule-v1",
          ),
          configVersion: String(dishBody.config_version ?? "unknown"),
          catalogVersion: typeof dishBody.catalog_version === "string"
            ? dishBody.catalog_version
            : null,
          policyCode: String(dishBody.policy_code ?? "adaptive-diversity-v1"),
          latencyMs,
          householdSnapshot: payload.household as Record<string, unknown>,
          requestContext: payload.context && typeof payload.context === "object"
            ? payload.context as Record<string, unknown>
            : {},
          response: dishBody,
        });
      }
      if (FEEDBACK_ELIGIBLE_SURFACES.has(surface) && resolvedHouseholdId) {
        const body = result.body as Record<string, unknown>;
        const dishes = surface === "calibration"
          ? Object.values((body.slots as Record<string, unknown[]>) ?? {}).flat()
          : surface === "meal_episodes"
          ? body.episodes
          : surface === "weekly_plan" && Array.isArray(body.days)
          ? (body.days as Array<Record<string, unknown>>).flatMap((day) => {
            const slots = day.slots && typeof day.slots === "object"
              ? day.slots as Record<string, unknown>
              : {};
            return Object.entries(slots).flatMap(([slot, classes]) =>
              Array.isArray(classes)
                ? classes.map((mealClass, index) => ({
                  ...(mealClass as Record<string, unknown>),
                  meal_slot: slot,
                  intended_meal_date: day.date,
                  day_type: ["Saturday", "Sunday"].includes(String(day.weekday))
                    ? "weekend"
                    : "weekday",
                  shown_rank: index + 1,
                }))
                : []
            );
          })
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
          intendedMealDate: typeof body.date === "string" ? body.date : undefined,
          dayType: plannedDayType(body.date),
          engineVersion: typeof body.engine_version === "string"
            ? body.engine_version
            : typeof body.model_version === "string"
            ? body.model_version
            : undefined,
          configVersion: typeof body.config_version === "string" ? body.config_version : undefined,
          catalogueSelection: body.catalogue_selection,
          auxShadowObservation: auxResult
            ? buildAuxShadowObservation(auxResult, ctx.config.auxReMode, body)
            : undefined,
          productionGuardrailObservation: auxResult
            ? buildProductionGuardrailObservation(
              auxResult,
              ctx.config.auxReMode,
              body,
              (payload.context as Record<string, unknown> | undefined)?.date,
            )
            : undefined,
          governedContextSignals: derivedGovernedContextSignals,
          // These surfaces accept explicit feedback by request_id. Do not return a response whose
          // recommendation event is missing, because the subsequent feedback could not be joined
          // to its exact served slate.
          lineageRequired: !stubbedHousehold,
        });
        await recordProductEvent(ctx, {
          profileId: claims.userId,
          householdId: resolvedHouseholdId,
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
        {
          ...stripPrivateCandidateLineage(result.body as Record<string, unknown>),
          request_id: requestId,
          slate_id: slateId,
        },
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
    if (surface === "meal_episodes" && resolvedHouseholdId && auxResult) {
      await recordRecommendationEvent(ctx, {
        requestId,
        householdId: resolvedHouseholdId,
        outcome: result.kind,
        plateCount: 0,
        reServed: false,
        detail: result.detail,
        latencyMs,
        stubbed: stubbedHousehold,
        slot: typeof body.slot === "string" ? body.slot : undefined,
        intendedMealDate: typeof body.date === "string" ? body.date : undefined,
        dayType: plannedDayType(body.date),
        auxShadowObservation: buildAuxShadowObservation(auxResult, ctx.config.auxReMode, {}),
        productionGuardrailObservation: buildProductionGuardrailObservation(
          auxResult,
          ctx.config.auxReMode,
          undefined,
          (payload.context as Record<string, unknown> | undefined)?.date,
        ),
        governedContextSignals: derivedGovernedContextSignals,
      });
    }
    return jsonContract(
      { error: "planning_unavailable", detail: result.detail, surface },
      ctx.traceId,
      503,
    );
  };
}
