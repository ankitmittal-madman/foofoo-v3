/**
 * Outcome recording (Phase C, wired to the live table in Phase C.5 — RE-DOC-10 §9 step 6/7).
 *
 * Every recommendation attempt is written to public.recommendation_events (migration 038) AND
 * logged as a structured line. Both, deliberately: the DB row is the queryable history that v2's
 * learned preference signal reads, and the log line is what stays available when the DB write
 * itself is what failed.
 *
 * Data ownership: this is an APPLICATION table in the live `public` schema, written by the Edge
 * Function's service-role client. The RE never sees it and gains no database dependency from it.
 */
import { createServiceRoleClient } from "../_shared/db/client.ts";
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
  slot?: string;
  plates?: unknown; // the served set, stored as jsonb for audit/replay
  engineVersion?: string;
  configVersion?: string;
  /** New user served neutral defaults — there is no profiles row to reference (see below). */
  stubbed?: boolean;
}

/**
 * Record the outcome of a recommendation request.
 *
 * The DB write is best-effort BY DESIGN: failing to record history must never turn an otherwise
 * successful recommendation into an error for the user. A failed write is logged at warn with the
 * event's identifying fields, so nothing is silently lost — the log line remains a full record.
 */
export async function recordRecommendationEvent(
  ctx: RequestContext,
  ev: RecommendationEventInput,
): Promise<void> {
  ctx.logger.info("recommendation_event", {
    request_id: ev.requestId,
    household_id: ev.householdId,
    outcome: ev.outcome,
    plate_count: ev.plateCount,
    re_served: ev.reServed,
    detail: ev.detail,
    latency_ms: ev.latencyMs,
    stubbed_household: ev.stubbed ?? false,
  });

  // A new user with no profiles row has no id to reference, and recommendation_events.profile_id
  // is a NOT NULL FK to profiles — there is nothing valid to insert. The log line above is the
  // complete record for that case.
  if (ev.stubbed) return;

  try {
    const db = createServiceRoleClient(ctx.config);
    const { error } = await db.from("recommendation_events").insert({
      profile_id: ev.householdId,
      request_id: ev.requestId,
      slot: ev.slot ?? null,
      outcome: ev.outcome,
      re_served: ev.reServed,
      plate_count: ev.plateCount,
      plates: ev.plates ?? null,
      latency_ms: ev.latencyMs ?? null,
      detail: ev.detail ?? null,
      engine_version: ev.engineVersion ?? null,
      config_version: ev.configVersion ?? null,
      data_source: "real",
    });
    if (error) throw error;
  } catch (e) {
    ctx.logger.warn("recommendation_event.persist_failed", {
      request_id: ev.requestId,
      household_id: ev.householdId,
      outcome: ev.outcome,
      detail: e instanceof Error ? e.message : String(e),
    });
  }
}
