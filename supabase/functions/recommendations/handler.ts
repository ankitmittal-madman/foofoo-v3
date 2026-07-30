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
import { requireOwnership } from "../_shared/auth/authenticate.ts";
import { jsonContract } from "../_shared/api/response.ts";
import { AppError } from "../_shared/errors/app-error.ts";
import { API_ERRORS } from "../_shared/errors/api-catalogue.ts";
import { ERROR_CATALOGUE } from "../_shared/errors/catalogue.ts";
import type { Handler } from "../_shared/middleware/types.ts";
import type { RequestContext } from "../_shared/types/context.ts";

import { buildRequest, type HouseholdRaw, loadHouseholdRaw } from "./compose.ts";
import { validateRequest, validateResponse } from "./contract.ts";
import { callRecommendationEngine, type ReResult } from "./re-client.ts";
import { buildFallbackResponse } from "./fallback.ts";
import { recordRecommendationEvent } from "./events.ts";
import { maybeLogSummary, recordRequest } from "./metrics.ts";

const SERVICE_NAME = "recommendations";

export interface RecommendationDeps {
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

    // Sole Surface-B authorization boundary (DOC-P3-06 §05), same as consent/handler.ts: JWT
    // user_id must equal the target household id. Runs BEFORE any household/context data is
    // fetched, so an unauthorized caller supplying someone else's household_id never reaches
    // compose.ts at all.
    requireOwnership(claims, householdId);

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
    log.info("recommendation.composed", { household_id: hid, stubbed });

    const contextOverride = (body.context && typeof body.context === "object")
      ? body.context as Record<string, unknown>
      : undefined;
    const payload = buildRequest(household, contextOverride, requestId);

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
        await recordEvent(eventCtx, {
          requestId,
          householdId: hid,
          outcome,
          plateCount: plateCount(result.body),
          reServed: true,
          latencyMs,
          stubbed,
          plates: result.body.plates,
          engineVersion: typeof result.body.engine_version === "string"
            ? result.body.engine_version
            : undefined,
          configVersion: typeof result.body.config_version === "string"
            ? result.body.config_version
            : undefined,
        });
        recordRequest(outcome);
        maybeLogSummary(log);
        // Pass through plates[]/contributions[] AS-IS (RE-DOC-11 §6 — no second translation layer),
        // additively stamping the trace id.
        return jsonContract(result.body, ctx.traceId, 200);
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
      });
      recordRequest("fallback");
      maybeLogSummary(log);
      return jsonContract(fb, ctx.traceId, 200);
    }

    // RE failure (timeout/network/http/bad_body) → fallback plate, still a valid 200 (RE-DOC-10 §11).
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
    });
    recordRequest(result.kind === "timeout" ? "timeout_fallback" : "fallback");
    maybeLogSummary(log);
    return jsonContract(fb, ctx.traceId, 200);
  };
}
