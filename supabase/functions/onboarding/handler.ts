/**
 * POST /v1/onboarding — business handler (DOC-P3-06 §06.2).
 *
 * CRITICAL audit fix (ops/audits/audit-edge-functions/edge-function-audit.md): the fully-built
 * `OnboardingOrchestrator` (`_shared/services/onboarding/orchestrator.ts`) was never wired to a
 * deployed Edge Function — this file + index.ts is that wiring. THIN handler, same discipline as
 * consent/handler.ts and household/handler.ts: parse → authorize (ownership) → delegate → envelope.
 *
 * The consent gate (HIGH audit finding — DPDP personalization-consent enforcement had no live
 * enforcement point) and the idempotency 409 (DOC-P3-06 §06.2/§08) are BOTH already implemented
 * inside the orchestrator itself (`isPersonalizationGranted` / `isOnboardingComplete` checks at the
 * top of `completeOnboarding`) — this handler does not duplicate them, it only has to actually call
 * the orchestrator for those checks to run at all.
 */
import { requireAuth } from "../_shared/auth/authorize.ts";
import { requireOwnership } from "../_shared/auth/authenticate.ts";
import { jsonContract } from "../_shared/api/response.ts";
import { AppError } from "../_shared/errors/app-error.ts";
import { API_ERRORS } from "../_shared/errors/api-catalogue.ts";
import { ERROR_CATALOGUE } from "../_shared/errors/catalogue.ts";
import { createContainer } from "../_shared/di/container.ts";
import { UserJourney } from "../_shared/logging/userJourney.ts";
import type { OnboardingOrchestrator } from "../_shared/services/onboarding/orchestrator.ts";
import type { MealSlot, RecommendationContext } from "../_shared/services/re/types.ts";
import type { Handler } from "../_shared/middleware/types.ts";
import type { RequestContext } from "../_shared/types/context.ts";
import { parseOnboardingRequest } from "./schema.ts";

const SERVICE_NAME = "onboarding";

export type OnboardingOrchestratorResolver = (ctx: RequestContext) => OnboardingOrchestrator;

const defaultResolver: OnboardingOrchestratorResolver = (ctx) =>
  createContainer(ctx).onboardingOrchestrator;

/** Monday of the current week (UTC) — the first week plan starts immediately at signup, matching
 * the nightly scheduler's own week-boundary convention (`nextMonday()` in supabase-stores.ts),
 * except here we want the week already under way, not strictly "next" week. */
function currentWeekMonday(): string {
  const d = new Date();
  const day = d.getUTCDay(); // 0=Sun..6=Sat
  const back = day === 0 ? 6 : day - 1; // days since Monday
  d.setUTCDate(d.getUTCDate() - back);
  return d.toISOString().slice(0, 10);
}

/**
 * Default per-slot context builder for the first-week plan. Deliberately minimal (weekday/weekend
 * only, no weather/season) — matching the same "neutral default context" spirit as
 * recommendations/compose.ts's own DEFAULT_CONTEXT; real per-slot weather/season assembly (LF-I01)
 * is a `/v1/recommendations`-time concern, not onboarding's.
 */
function contextForSlot(slotDate: string, mealSlot: MealSlot): RecommendationContext {
  const day = new Date(`${slotDate}T00:00:00Z`).getUTCDay();
  return {
    mealSlot,
    slotDate,
    dayType: day === 0 || day === 6 ? "weekend" : "weekday",
    isMonsoon: false,
  };
}

/** Build the POST /v1/onboarding handler. */
export function makeOnboardingHandler(resolve: OnboardingOrchestratorResolver = defaultResolver): Handler {
  return async (req, ctx) => {
    if (req.method !== "POST") {
      throw new AppError(ERROR_CATALOGUE.METHOD_NOT_ALLOWED);
    }

    // Auth middleware populated claims; requireAuth is the defensive backstop.
    const claims = requireAuth(ctx.claims);

    let body: unknown;
    try {
      body = await req.json();
    } catch {
      throw new AppError(API_ERRORS.ERR_VALIDATION_FAILED, {
        detail: "request body is not valid JSON",
      });
    }

    const { userId, answers } = parseOnboardingRequest(body);

    // Sole Surface-B authorization boundary (DOC-P3-06 §05): JWT user_id == body user_id. Runs
    // BEFORE the orchestrator (and therefore before its consent check) ever sees this request.
    requireOwnership(claims, userId);

    const log = ctx.logger.child({ profile_id: userId, service: SERVICE_NAME });
    const orchestrator = resolve(ctx);

    // ERR_CONSENT_REQUIRED (403) and ERR_ONBOARDING_ALREADY_COMPLETE (409) are both thrown FROM
    // INSIDE completeOnboarding() (orchestrator.ts) — propagate as-is, the error-boundary
    // middleware maps them to their AppError's own httpStatus/code, same as every other endpoint.
    const result = await orchestrator.completeOnboarding(
      userId,
      answers,
      currentWeekMonday(),
      contextForSlot,
    );

    log.info("onboarding.completed", {
      persona_id: result.persona_id,
      cold_start_mode: result.cold_start_mode,
      confidence_score: result.confidence_score,
    });
    UserJourney.logOnboardingStep(userId, answers.skippedScreens, {
      profileCreated: true,
      membersWritten: answers.members.length || undefined,
    });

    // 201 Created per DOC-P3-06 §06.2.
    return jsonContract({ ...result }, ctx.traceId, 201);
  };
}
