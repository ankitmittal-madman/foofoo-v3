/**
 * feedback_events writer (WP-15 — POST /v1/feedback, wired to migration 038's table).
 *
 * Unlike recommendations/events.ts's recordRecommendationEvent (best-effort telemetry alongside
 * an already-successful response), a failed write HERE is the entire point of the request failing
 * — the caller needs to know their feedback wasn't recorded so a client can retry, since (per
 * migration 038's own comment) this history "cannot be back-filled retroactively" once the
 * moment passes.
 *
 * Two lookups happen before the insert, both deliberate:
 *   1. The caller supplies `request_id` (RecommendationsResponse.request_id — the ONLY
 *      recommendation identifier the mobile client is ever given; recommendation_events.id, the
 *      DB row's own uuid PK, is never echoed to the client). This is resolved server-side to that
 *      recommendation_events row, scoped to the calling profile (defense-in-depth ownership check
 *      — RLS is bypassed under the service-role client used here, same as every other Edge
 *      Function; see auth/authenticate.ts's own module doc).
 *   2. dish_name (what the mobile client actually has — plate.hero_dish_names, not a
 *      public.dishes uuid) is resolved to dish_id by exact name lookup. A miss is NOT an error:
 *      public.dishes and the RE's own catalogue are two separately-synced data sources (the same
 *      class of gap this session's WP-15 already found and disclosed for the KB comfort-hero
 *      table) — the feedback row is still recorded, with dish_id left null and the miss logged,
 *      rather than rejecting a user's real feedback over a data-sync gap.
 */
import { createServiceRoleClient } from "../_shared/db/client.ts";
import { AppError } from "../_shared/errors/app-error.ts";
import { API_ERRORS } from "../_shared/errors/api-catalogue.ts";
import { ERROR_CATALOGUE } from "../_shared/errors/catalogue.ts";
import type { RequestContext } from "../_shared/types/context.ts";
import { withTimeout } from "../_shared/utils/timeout.ts";
import type { FeedbackEventType } from "../_shared/validation/feedback-schema.ts";

export interface FeedbackEventInput {
  profileId: string;
  /** RecommendationsResponse.request_id — see module doc for why this, not the DB row's uuid PK. */
  requestId: string;
  eventType: FeedbackEventType;
  dishName?: string;
  slot?: string;
  detail?: Record<string, unknown>;
}

export interface FeedbackEventResult {
  id: string;
  createdAt: string;
  dishResolved: boolean;
}

/**
 * Record one feedback event, after resolving the caller's `request_id` to its
 * recommendation_events row and verifying that row belongs to the calling profile.
 * @throws AppError ERR_RECOMMENDATION_EVENT_NOT_FOUND (404) if request_id matches no row for this profile.
 * @throws AppError ERROR_CATALOGUE.INTERNAL (500) if a lookup/the insert itself fails (the caller should retry).
 */
export async function recordFeedbackEvent(
  ctx: RequestContext,
  ev: FeedbackEventInput,
): Promise<FeedbackEventResult> {
  const db = createServiceRoleClient(ctx.config);

  // Scoped to profile_id in the query itself (not just checked after the fact): a request_id
  // belonging to another profile then looks IDENTICAL to "no such request_id" — no information
  // disclosure about another profile's recommendation history (DOC-P3-06 §05.1 precedent).
  const { data: recRows, error: recErr } = await withTimeout(
    db
      .from("recommendation_events")
      .select("id, profile_id")
      .eq("request_id", ev.requestId)
      .eq("profile_id", ev.profileId)
      .order("created_at", { ascending: false })
      .limit(1),
    "feedback.events.lookup_recommendation_event",
  );
  if (recErr) {
    ctx.logger.warn("feedback_event.lookup_recommendation_event_failed", {
      request_id: ev.requestId,
      detail: recErr.message,
    });
    throw new AppError(ERROR_CATALOGUE.INTERNAL, { detail: recErr.message });
  }
  const recRow = recRows?.[0];
  if (!recRow) {
    throw new AppError(API_ERRORS.ERR_RECOMMENDATION_EVENT_NOT_FOUND, {
      context: { request_id: ev.requestId },
    });
  }

  let dishId: string | null = null;
  let dishResolved = false;
  if (ev.dishName) {
    const { data: dishRow, error: dishErr } = await withTimeout(
      db.from("dishes").select("id").eq("name", ev.dishName).maybeSingle(),
      "feedback.events.lookup_dish",
    );
    if (dishErr) {
      // A dish-lookup failure must not block recording the feedback itself — log and continue
      // with dish_id=null, same "don't lose real signal over a secondary lookup" principle as
      // the miss case below.
      ctx.logger.warn("feedback_event.dish_lookup_failed", {
        dish_name: ev.dishName,
        detail: dishErr.message,
      });
    } else if (dishRow) {
      dishId = dishRow.id as string;
      dishResolved = true;
    } else {
      ctx.logger.warn("feedback_event.dish_not_found_in_public_dishes", { dish_name: ev.dishName });
    }
  }

  const { data: inserted, error } = await withTimeout(
    db
      .from("feedback_events")
      .insert({
        profile_id: ev.profileId,
        recommendation_event_id: recRow.id,
        dish_id: dishId,
        event_type: ev.eventType,
        slot: ev.slot ?? null,
        detail: ev.detail ?? null,
        data_source: "real",
      })
      .select("id, created_at")
      .single(),
    "feedback.events.insert",
  );
  if (error) {
    ctx.logger.warn("feedback_event.insert_failed", {
      profile_id: ev.profileId,
      request_id: ev.requestId,
      event_type: ev.eventType,
      detail: error.message,
    });
    throw new AppError(ERROR_CATALOGUE.INTERNAL, { detail: error.message });
  }

  ctx.logger.info("feedback_event.recorded", {
    id: inserted.id,
    profile_id: ev.profileId,
    request_id: ev.requestId,
    event_type: ev.eventType,
    dish_resolved: dishResolved,
  });

  return { id: inserted.id as string, createdAt: inserted.created_at as string, dishResolved };
}
