/**
 * Outcome logging (Phase C, RE-DOC-10 §9 step 6/7).
 *
 * Every recommendation attempt is logged with its outcome + request_id + household_id.
 *
 * ⚠️ STUB (TODO — founder decision needed): the live app Postgres has NO recommendation_event /
 * feedback_event table yet (they exist only in the golden-sample `ghar_re` schema, not the live
 * application schema). Rather than invent a live migration silently, this writes a STRUCTURED LOG
 * line now and marks the DB insert as TODO. Wire the real insert once the table + its location are
 * decided (Edge Functions own DB access).
 */
import type { RequestContext } from "../_shared/types/context.ts";

export type RecommendationOutcome =
  | "success"
  | "partial" // RE served plates but warnings[] non-empty — e.g. <7 eligible dishes (Phase D Task 4)
  | "timeout"
  | "network"
  | "http"
  | "bad_body"
  | "fallback";

export interface RecommendationEventInput {
  requestId: string;
  householdId: string;
  outcome: RecommendationOutcome;
  plateCount: number;
  reServed: boolean; // true = plates came from the RE; false = fallback
  detail?: string;
  latencyMs?: number; // RE call latency, measured edge-function-side (Phase D Task 2)
}

/**
 * Record the outcome of a recommendation request.
 * TODO(founder-decision): INSERT into recommendation_event once the live table exists; until then
 * this is log-only (no data is silently dropped — the structured line is the record for now).
 */
export function recordRecommendationEvent(
  ctx: RequestContext,
  ev: RecommendationEventInput,
): Promise<void> {
  ctx.logger.info("recommendation_event", {
    // TODO: persist to recommendation_event table (does not exist in live schema yet).
    stubbed_db_write: true,
    request_id: ev.requestId,
    household_id: ev.householdId,
    outcome: ev.outcome,
    plate_count: ev.plateCount,
    re_served: ev.reServed,
    detail: ev.detail,
    latency_ms: ev.latencyMs,
  });
  return Promise.resolve();
}
