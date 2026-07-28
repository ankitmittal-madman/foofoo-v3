/**
 * POST /v1/recommendations — business handler (Phase C).
 *
 * THIN orchestration handler (frozen architecture: Edge Functions own auth/DB, the RE owns math).
 * Flow (RE-DOC-10 §9): authenticate (middleware) → fetch household+context → compose + validate the
 * ghar-re-v1 request → signed call to the RE (timeout/retry) → pass the response through as-is
 * (RE-DOC-11 §6) → log the outcome. On any RE failure, return a fallback plate as a valid 200.
 *
 * No recommendation math here. Deps are injectable so the handler is unit-testable without a live
 * RE (default deps use the real client/loader/event-writer).
 */
import { requireAuth } from "../_shared/auth/authorize.ts";
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

    // Fetch household + context (STUB until the live table exists — see compose.ts).
    const { household, householdId: hid } = await loadHousehold(ctx, householdId);
    // TODO(founder-decision): once the live households table exists, enforce ownership here:
    //   requireOwnership(claims, household.profile_id)  — Edge Functions are the auth boundary.

    // request_id: use the caller's if supplied, else the request's trace id (already a UUIDv4).
    const requestId = (typeof body.request_id === "string" && body.request_id)
      ? body.request_id
      : ctx.traceId;

    const contextOverride = (body.context && typeof body.context === "object")
      ? body.context as Record<string, unknown>
      : undefined;
    const payload = buildRequest(household, contextOverride, requestId);

    // Validate the OUTGOING payload against the shared contract BEFORE calling the RE (RE-DOC-10 §15).
    const reqCheck = validateRequest(payload);
    if (!reqCheck.valid) {
      throw new AppError(API_ERRORS.ERR_VALIDATION_FAILED, {
        detail: `composed payload failed ghar-re-v1 contract: ${reqCheck.errors.join("; ")}`,
      });
    }

    const result = await callRe(payload, requestId, ctx.config, ctx.logger);

    if (result.ok) {
      // Defensive fail-closed check: pass through only if the RE's body is contract-conformant.
      const respCheck = validateResponse(result.body);
      if (respCheck.valid) {
        await recordEvent(ctx, {
          requestId,
          householdId: hid,
          outcome: "success",
          plateCount: plateCount(result.body),
          reServed: true,
        });
        // Pass through plates[]/contributions[] AS-IS (RE-DOC-11 §6 — no second translation layer),
        // additively stamping the trace id.
        return jsonContract(result.body, ctx.traceId, 200);
      }
      ctx.logger.warn("re_response.invalid", { request_id: requestId, errors: respCheck.errors });
      const fb = buildFallbackResponse(requestId, "invalid RE response");
      await recordEvent(ctx, {
        requestId,
        householdId: hid,
        outcome: "bad_body",
        plateCount: plateCount(fb),
        reServed: false,
        detail: respCheck.errors.join("; "),
      });
      return jsonContract(fb, ctx.traceId, 200);
    }

    // RE failure (timeout/network/http/bad_body) → fallback plate, still a valid 200 (RE-DOC-10 §11).
    const fb = buildFallbackResponse(requestId, result.kind);
    await recordEvent(ctx, {
      requestId,
      householdId: hid,
      outcome: result.kind,
      plateCount: plateCount(fb),
      reServed: false,
      detail: result.detail,
    });
    return jsonContract(fb, ctx.traceId, 200);
  };
}
