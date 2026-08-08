/**
 * POST /v1/recommendations — business handler (Phase C).
 *
 * THIN orchestration handler (frozen architecture: Edge Functions own auth/DB, the RE owns math).
 * Flow (RE-DOC-10 §9): authenticate (middleware) → verify ownership of the target household
 * (DOC-P3-06 §05, same boundary as consent/handler.ts) → fetch household+context → compose +
 * validate the ghar-re-v1 request → signed call to the RE (timeout/retry) → pass the response
 * through as-is (RE-DOC-11 §6) → log the outcome. On any RE failure, return a fallback plate as a
 * valid 200.
 *
 * No recommendation math here. Deps are injectable so the handler is unit-testable without a live
 * RE (default deps use the real client/loader/event-writer).
 */
import { requireAuth } from "../_shared/auth/authorize.ts";
import {
  HOUSEHOLD_READ_ROLES,
  type HouseholdRoleLookup,
  requireHouseholdRole,
} from "../_shared/auth/household.ts";
import { jsonContract } from "../_shared/api/response.ts";
import { AppError } from "../_shared/errors/app-error.ts";
import { API_ERRORS } from "../_shared/errors/api-catalogue.ts";
import { ERROR_CATALOGUE } from "../_shared/errors/catalogue.ts";
import { UserJourney } from "../_shared/logging/userJourney.ts";
import type { Handler } from "../_shared/middleware/types.ts";
import type { RequestContext } from "../_shared/types/context.ts";

import {
  applyFestivalContext,
  buildExcludeDishIds,
  buildRequest,
  type HouseholdRaw,
  loadFestivalContext,
  loadHouseholdRaw,
  loadLatestContext,
  recordHouseholdContext,
} from "./compose.ts";
import {
  loadOnlineRecommendationState,
  type OnlineRecommendationState,
} from "./personalization.ts";
import { validateRequest, validateResponse } from "./contract.ts";
import { callRecommendationEngine, type ReResult } from "./re-client.ts";
import { buildFallbackResponse } from "./fallback.ts";
import { recordRecommendationEvent } from "./events.ts";
import { recordDishRecommendationSlate } from "../plan/episodes.ts";
import { maybeLogSummary, recordRequest } from "./metrics.ts";
import { deriveGovernedContextSignals, mergeGovernedContextSignals } from "./governed-context.ts";
import {
  buildAuxiliaryRequest,
  buildAuxShadowObservation,
  buildProductionGuardrailObservation,
  callAuxiliaryEngine,
} from "./aux-client.ts";

const SERVICE_NAME = "recommendations";

function dayTypeForDate(value: unknown): "weekday" | "weekend" | undefined {
  if (typeof value !== "string" || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return undefined;
  const day = new Date(`${value}T12:00:00Z`).getUTCDay();
  return day === 0 || day === 6 ? "weekend" : "weekday";
}

export interface RecommendationDeps {
  authorizeHousehold?: HouseholdRoleLookup;
  loadHousehold?: (
    ctx: RequestContext,
    householdId: string | null,
  ) => Promise<{ household: HouseholdRaw; householdId: string; stubbed: boolean }>;
  callRe?: (
    payload: Record<string, unknown>,
    requestId: string,
    cfg: RequestContext["config"],
    logger: RequestContext["logger"],
  ) => Promise<ReResult>;
  recordEvent?: typeof recordRecommendationEvent;
  recordSlate?: typeof recordDishRecommendationSlate;
  /** §0.2 — injectable so tests never need a live household_context table. */
  recordContext?: typeof recordHouseholdContext;
  /** Shared online learning state, injectable so tests never need live personalization tables. */
  loadOnlineStateFn?: (
    ctx: RequestContext,
    profileId: string,
  ) => Promise<OnlineRecommendationState>;
  /** WP-8G Option A — injectable so tests never need a live recommendation_events table. */
  buildExcludeDishIdsFn?: typeof buildExcludeDishIds;
  /** WP-14 §3 — injectable so tests never need a live household_context table. */
  loadLatestContextFn?: typeof loadLatestContext;
  /** Governed date-to-festival mapping, injectable for deterministic tests. */
  loadFestivalContextFn?: typeof loadFestivalContext;
  callAux?: typeof callAuxiliaryEngine;
}

function plateCount(body: Record<string, unknown>): number {
  const plates = body.plates;
  return Array.isArray(plates) ? plates.length : 0;
}

/** Build the POST /v1/recommendations handler. */
export function makeRecommendationsHandler(deps: RecommendationDeps = {}): Handler {
  const loadHousehold = deps.loadHousehold ?? loadHouseholdRaw;
  const callRe = deps.callRe ??
    ((payload, requestId, cfg, logger) =>
      callRecommendationEngine(payload, requestId, cfg, logger));
  const recordEvent = deps.recordEvent ?? recordRecommendationEvent;
  const recordSlate = deps.recordSlate ?? recordDishRecommendationSlate;
  const recordContext = deps.recordContext ?? recordHouseholdContext;
  const loadOnlineStateFn = deps.loadOnlineStateFn ?? loadOnlineRecommendationState;
  const buildExcludeDishIdsFn = deps.buildExcludeDishIdsFn ?? buildExcludeDishIds;
  const loadLatestContextFn = deps.loadLatestContextFn ?? loadLatestContext;
  const loadFestivalContextFn = deps.loadFestivalContextFn ?? loadFestivalContext;
  const callAux = deps.callAux ?? callAuxiliaryEngine;
  const authorizeHousehold = deps.authorizeHousehold;

  return async (req, ctx) => {
    if (req.method !== "POST") {
      throw new AppError(ERROR_CATALOGUE.METHOD_NOT_ALLOWED);
    }

    // Auth middleware populated claims; requireAuth is the defensive backstop.
    const claims = requireAuth(ctx.claims);

    // Body is optional (a bare "recommend for me" call is valid); if present it may carry
    // request_id / household_id / context overrides.
    let body: Record<string, unknown> = {};
    try {
      const text = await req.text();
      if (text) body = JSON.parse(text) as Record<string, unknown>;
    } catch {
      throw new AppError(API_ERRORS.ERR_VALIDATION_FAILED, {
        detail: "request body is not valid JSON",
      });
    }

    const householdId = (typeof body.household_id === "string" ? body.household_id : null) ??
      claims.userId ?? null;

    // Role-aware Surface-B authorization runs before any service-role read. Compatibility
    // households already have an active owner membership; shared households may additionally
    // grant planner/cook/member/viewer read access without equating household id to JWT subject.
    await requireHouseholdRole(
      ctx,
      claims,
      householdId,
      HOUSEHOLD_READ_ROLES,
      authorizeHousehold,
    );

    // request_id: use the caller's if supplied, else the request's trace id (already a UUIDv4).
    // Bound onto a child logger NOW so every log line for the rest of this request — auth already
    // resolved above, compose/RE-call/response-handling below — carries the SAME id without each
    // call site having to remember to pass it (Phase D Task 1).
    const requestId = (typeof body.request_id === "string" && body.request_id)
      ? body.request_id
      : ctx.traceId;
    const log = ctx.logger.child({ request_id: requestId, service: SERVICE_NAME });
    const eventCtx = { ...ctx, logger: log };

    log.info("recommendation.auth_ok", { user_id: claims.userId });

    // Fetch household + context from the live `public` tables (compose.ts) — ownership already
    // verified above.
    const { household, householdId: hid, stubbed } = await loadHousehold(ctx, householdId);
    const derivedGovernedContextSignals = deriveGovernedContextSignals(household);
    log.info("recommendation.composed", { household_id: hid, stubbed });

    const contextOverride = (body.context && typeof body.context === "object")
      ? body.context as Record<string, unknown>
      : undefined;

    // Load all independent serving state concurrently. Online state is shared with the plan
    // surface, so this endpoint cannot silently fall back to a less-personalized ranking path.
    const [online, excludeDishIds, storedContext] = await Promise.all([
      loadOnlineStateFn(ctx, hid),
      // Retain id exclusions for compatibility with older recommendation events whose plates did
      // not persist canonical names.
      buildExcludeDishIdsFn(ctx, hid),
      loadLatestContextFn(ctx, hid),
    ]);
    const festival = await loadFestivalContextFn(
      ctx,
      typeof contextOverride?.date === "string" ? contextOverride.date : undefined,
    );
    const governedContextSignals = mergeGovernedContextSignals(
      derivedGovernedContextSignals,
      online.governedContextSignals,
    );
    const requestedRefreshGeneration = typeof body.refresh_generation === "number"
      ? body.refresh_generation
      : contextOverride?.refresh_generation;
    const enrichedContext = {
      ...(contextOverride ?? {}),
      dish_feedback_counts: online.dishFeedbackCounts,
      recent_class_counts: online.recentClassCounts,
      recent_cuisine_counts: online.recentCuisineCounts,
      novelty_budget: online.noveltyBudget,
      richness_debt: online.richnessDebt,
      ...(typeof requestedRefreshGeneration === "number" &&
          Number.isFinite(requestedRefreshGeneration)
        ? { refresh_generation: Math.max(0, Math.trunc(requestedRefreshGeneration)) }
        : {}),
    };
    const payload = buildRequest(
      household,
      applyFestivalContext(enrichedContext, festival),
      requestId,
      online.interactionCount,
      excludeDishIds,
      storedContext,
    );
    payload.context = applyFestivalContext(payload.context as Record<string, unknown>, festival);
    const requestedExclusions = Array.isArray(body.exclude_dish_names)
      ? body.exclude_dish_names.filter((name): name is string =>
        typeof name === "string" && name.trim().length > 0
      ).slice(0, 50)
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
    (payload.context as Record<string, unknown>).temporal_class_state = online.temporalClassState;
    (payload.context as Record<string, unknown>).temporal_attribute_state =
      online.temporalAttributeState;
    (payload.context as Record<string, unknown>).governed_context_signals = governedContextSignals;

    // Optional shadow retrieval narrows the scalable publication before Ghar math. Failure is
    // deliberately fail-open to the unchanged immutable bundle; Aux never becomes final safety.
    const aux = await callAux(
      buildAuxiliaryRequest(payload, claims.userId, hid),
      requestId,
      ctx.config,
      log,
    );
    if (aux.ok) {
      if (ctx.config.auxReMode === "active") payload.candidate_dish_ids = aux.candidateIds;
      log.info("aux_re.candidates_retrieved", {
        candidate_count: aux.candidateIds.length,
        publication_version: aux.publicationVersion,
        latency_ms: aux.latencyMs,
        mode: ctx.config.auxReMode,
        applied_to_ghar: ctx.config.auxReMode === "active",
      });
    } else if (aux.reason !== "disabled") {
      log.warn("aux_re.shadow_unavailable", { reason: aux.reason, latency_ms: aux.latencyMs });
    }

    // §0.2: persist the RESOLVED context (same object buildRequest just sent) into
    // household_context, so the household's NEXT call finds real history via loadLatestContext
    // instead of always falling through to DEFAULT_CONTEXT. Best-effort telemetry, same
    // "don't let a secondary write fail an otherwise-successful request" pattern as
    // recordRecommendationEvent below — recordHouseholdContext itself never throws, but this is
    // wrapped defensively anyway so a future change to that contract can't regress the request.
    try {
      await recordContext(ctx, hid, payload.context as Record<string, unknown>);
    } catch (e) {
      log.warn("household_context.record_call_failed", {
        household_id: hid,
        detail: e instanceof Error ? e.message : String(e),
      });
    }

    // Validate the OUTGOING payload against the shared contract BEFORE calling the RE (RE-DOC-10 §15).
    const reqCheck = validateRequest(payload);
    if (!reqCheck.valid) {
      recordRequest("error");
      maybeLogSummary(log);
      throw new AppError(API_ERRORS.ERR_VALIDATION_FAILED, {
        detail: `composed payload failed ghar-re-v1 contract: ${reqCheck.errors.join("; ")}`,
      });
    }

    // Latency measured HERE (edge-function-side clock) — this is the real user-facing wait for
    // the RE call, per Task 2 ("the one with the real user-facing clock").
    const reStart = performance.now();
    const result = await callRe(payload, requestId, ctx.config, log);
    const latencyMs = Math.round(performance.now() - reStart);

    if (result.ok) {
      // Defensive fail-closed check: pass through only if the RE's body is contract-conformant.
      const respCheck = validateResponse(result.body);
      if (respCheck.valid) {
        const warnings = Array.isArray(result.body.warnings) ? result.body.warnings : [];
        // Task 4: zero/partial-eligible-dishes is a distinct outcome, never lumped into "error".
        const outcome = warnings.length > 0 ? "partial" : "success";
        log.info("recommendation.re_call_done", {
          outcome,
          latency_ms: latencyMs,
          warnings: warnings.length,
        });
        let slateId: string | undefined;
        if (!stubbed) {
          slateId = await recordSlate(eventCtx, {
            householdId: hid,
            requestId,
            surface: "recommendations",
            modelVersion: typeof result.body.engine_version === "string"
              ? result.body.engine_version
              : "unknown",
            configVersion: typeof result.body.config_version === "string"
              ? result.body.config_version
              : "unknown",
            catalogVersion: typeof result.body.catalog_version === "string"
              ? result.body.catalog_version
              : null,
            policyCode: "home-diversity-v2",
            latencyMs,
            householdSnapshot: payload.household as Record<string, unknown>,
            requestContext: payload.context as Record<string, unknown>,
            response: {
              ...result.body,
              slot: (payload.context as Record<string, unknown>).slot,
            },
          });
        }
        await recordEvent(eventCtx, {
          requestId,
          householdId: hid,
          outcome,
          plateCount: plateCount(result.body),
          reServed: true,
          latencyMs,
          stubbed,
          plates: result.body.plates,
          slot: typeof (payload.context as Record<string, unknown>).slot === "string"
            ? String((payload.context as Record<string, unknown>).slot)
            : undefined,
          intendedMealDate: typeof (payload.context as Record<string, unknown>).date === "string"
            ? String((payload.context as Record<string, unknown>).date)
            : undefined,
          dayType: dayTypeForDate((payload.context as Record<string, unknown>).date),
          engineVersion: typeof result.body.engine_version === "string"
            ? result.body.engine_version
            : undefined,
          configVersion: typeof result.body.config_version === "string"
            ? result.body.config_version
            : undefined,
          decisionTrace: result.body.decision_trace,
          catalogueSelection: result.body.catalogue_selection,
          auxShadowObservation: buildAuxShadowObservation(aux, ctx.config.auxReMode, result.body),
          productionGuardrailObservation: buildProductionGuardrailObservation(
            aux,
            ctx.config.auxReMode,
            result.body,
            (payload.context as Record<string, unknown>).date,
          ),
          governedContextSignals: derivedGovernedContextSignals,
          lineageRequired: !stubbed,
        });
        recordRequest(outcome);
        maybeLogSummary(log);
        UserJourney.logRecommendationOutcome(hid, outcome, plateCount(result.body), {
          latencyMs,
          reServed: true,
        });
        // Pass through plates[]/contributions[] AS-IS (RE-DOC-11 §6 — no second translation layer),
        // additively stamping the trace id.
        return jsonContract({ ...result.body, slate_id: slateId }, ctx.traceId, 200);
      }
      log.warn("re_response.invalid", { latency_ms: latencyMs, errors: respCheck.errors });
      const fb = buildFallbackResponse(requestId, "invalid RE response");
      await recordEvent(eventCtx, {
        requestId,
        householdId: hid,
        outcome: "bad_body",
        plateCount: plateCount(fb),
        reServed: false,
        detail: respCheck.errors.join("; "),
        latencyMs,
        stubbed,
        productionGuardrailObservation: buildProductionGuardrailObservation(
          aux,
          ctx.config.auxReMode,
          result.body,
          (payload.context as Record<string, unknown>).date,
        ),
        governedContextSignals: derivedGovernedContextSignals,
      });
      recordRequest("fallback");
      maybeLogSummary(log);
      UserJourney.logRecommendationOutcome(hid, "bad_body", plateCount(fb), {
        latencyMs,
        detail: respCheck.errors.join("; "),
        reServed: false,
      });
      return jsonContract(fb, ctx.traceId, 503);
    }

    // RE failure (timeout/network/http/bad_body) → surface as a retryable error, not a guessed
    // plate (WP-21): a hardcoded dish ignores this household's actual allergies/diet.
    log.warn("recommendation.re_call_failed", {
      outcome: result.kind,
      latency_ms: latencyMs,
      detail: result.detail,
    });
    const fb = buildFallbackResponse(requestId, result.kind);
    await recordEvent(eventCtx, {
      requestId,
      householdId: hid,
      outcome: result.kind,
      plateCount: plateCount(fb),
      reServed: false,
      detail: result.detail,
      latencyMs,
      stubbed,
      productionGuardrailObservation: buildProductionGuardrailObservation(
        aux,
        ctx.config.auxReMode,
        undefined,
        (payload.context as Record<string, unknown>).date,
      ),
      governedContextSignals: derivedGovernedContextSignals,
    });
    recordRequest(result.kind === "timeout" ? "timeout_fallback" : "fallback");
    maybeLogSummary(log);
    UserJourney.logRecommendationOutcome(hid, result.kind, plateCount(fb), {
      latencyMs,
      detail: result.detail,
      reServed: false,
    });
    return jsonContract(fb, ctx.traceId, 503);
  };
}
