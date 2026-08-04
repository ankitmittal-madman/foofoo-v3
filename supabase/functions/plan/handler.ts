/**
 * POST /v1/plan — WP-18 planning surfaces (business handler).
 *
 * THIN orchestration, same frozen boundary as recommendations/handler.ts (Edge owns auth/DB, the RE
 * owns the math). One function multiplexes the five planning surfaces via `body.surface`:
 *   cold_start    -> RE /v1/cold-start     (15 diverse dishes to seed preferences)
 *   calibration   -> RE /v1/calibration    (3 slots x 5 dishes: dish-pick calibration grid)
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

import { loadHouseholdRaw, recordHouseholdContext } from "../recommendations/compose.ts";
import { recordRecommendationEvent } from "../recommendations/events.ts";
import { callRecommendationEngine } from "../recommendations/re-client.ts";

const SERVICE_NAME = "plan";

// surface -> { RE path, whether it needs the composed household }
const SURFACES: Record<string, { path: string; needsHousehold: boolean }> = {
  cold_start: { path: "/v1/cold-start", needsHousehold: true },
  calibration: { path: "/v1/calibration", needsHousehold: true },
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
      ]);
      if (FEEDBACK_ELIGIBLE_SURFACES.has(surface) && resolvedHouseholdId) {
        const body = result.body as Record<string, unknown>;
        const dishes = surface === "calibration"
          ? Object.values((body.slots as Record<string, unknown[]>) ?? {}).flat()
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
      return jsonContract({ ...result.body, request_id: requestId }, ctx.traceId, 200);
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
