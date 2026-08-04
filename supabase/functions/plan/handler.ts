/**
 * POST /v1/plan — WP-18 planning surfaces (business handler).
 *
 * THIN orchestration, same frozen boundary as recommendations/handler.ts (Edge owns auth/DB, the RE
 * owns the math). One function multiplexes the five planning surfaces via `body.surface`:
 *   cold_start    -> RE /v1/cold-start     (15 diverse dishes to seed preferences)
 *   meal_plan     -> RE /v1/meal-plan      (a slot's 4–5 dish options)
 *   weekly_plan   -> RE /v1/weekly-plan    (7 days × slots, top-3 classes each)
 *   class_dishes  -> RE /v1/class-dishes   (reconciliation: dishes of a finalized class)
 *   recipe        -> RE /v1/recipe         (recipe + image for one dish; no household needed)
 *
 * Flow: authenticate (middleware) → requireOwnership → loadHouseholdRaw (compose from live tables,
 * reused from recommendations/compose.ts) → signed call to the RE surface (re-client, path per
 * surface) → pass the RE body through as-is. No recommendation math here.
 */
import { requireAuth } from "../_shared/auth/authorize.ts";
import { requireOwnership } from "../_shared/auth/authenticate.ts";
import { jsonContract } from "../_shared/api/response.ts";
import { AppError } from "../_shared/errors/app-error.ts";
import { API_ERRORS } from "../_shared/errors/api-catalogue.ts";
import { ERROR_CATALOGUE } from "../_shared/errors/catalogue.ts";
import type { Handler } from "../_shared/middleware/types.ts";

import { loadHouseholdRaw } from "../recommendations/compose.ts";
import { callRecommendationEngine } from "../recommendations/re-client.ts";

const SERVICE_NAME = "plan";

// surface -> { RE path, whether it needs the composed household }
const SURFACES: Record<string, { path: string; needsHousehold: boolean }> = {
  cold_start: { path: "/v1/cold-start", needsHousehold: true },
  meal_plan: { path: "/v1/meal-plan", needsHousehold: true },
  weekly_plan: { path: "/v1/weekly-plan", needsHousehold: true },
  class_dishes: { path: "/v1/class-dishes", needsHousehold: true },
  recipe: { path: "/v1/recipe", needsHousehold: false },
};

/** Build the POST /v1/plan handler. */
export function makePlanHandler(): Handler {
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
    const spec = SURFACES[surface];
    if (!spec) {
      throw new AppError(API_ERRORS.ERR_VALIDATION_FAILED, {
        detail: `unknown surface '${surface}' (expected: ${Object.keys(SURFACES).join(", ")})`,
      });
    }

    const householdId = (typeof body.household_id === "string" ? body.household_id : null) ??
      claims.userId ?? null;
    requireOwnership(claims, householdId);

    const requestId = (typeof body.request_id === "string" && body.request_id)
      ? body.request_id
      : ctx.traceId;
    const log = ctx.logger.child({ request_id: requestId, service: SERVICE_NAME, surface });

    // Build the RE payload for this surface. Planning params (slot/weekday/class_code/count/
    // dish_name/top_classes) pass straight through; the household is composed from the live tables
    // for the surfaces that need it (never trusted from the client).
    const payload: Record<string, unknown> = { request_id: requestId };
    for (const k of ["slot", "weekday", "class_code", "count", "dish_name", "top_classes"]) {
      if (body[k] !== undefined) payload[k] = body[k];
    }
    if (spec.needsHousehold) {
      const { household, householdId: hid, stubbed } = await loadHouseholdRaw(ctx, householdId);
      payload.household = household;
      // Cold-start exploration seed (ghar_re_core.meal_planner.cold_start_top15): a stable
      // per-household RNG seed so two households that land on an identical theta (same cohort
      // answers) don't always converge on the exact same top-n dishes. Harmless for the other
      // surfaces — they don't read household_id from the payload.
      payload.household_id = hid;
      log.info("plan.composed", { household_id: hid, stubbed });
    }

    const reStart = performance.now();
    const result = await callRecommendationEngine(payload, requestId, ctx.config, log, {
      path: spec.path,
    });
    const latencyMs = Math.round(performance.now() - reStart);

    if (result.ok) {
      log.info("plan.re_call_done", { latency_ms: latencyMs });
      // Pass the RE body through as-is (RE-DOC-11 §6), additively stamping the trace id.
      return jsonContract(result.body, ctx.traceId, 200);
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
