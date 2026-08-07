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
import { withTimeout } from "../_shared/utils/timeout.ts";
import {
  buildShownNotTappedRows,
  flattenServedDishes,
  flattenServedMealClasses,
  resolveDishIdsByName,
  toExposureItems,
  toMealAttributeExposureItems,
  toMealClassExposureItems,
} from "./served.ts";
import type { GovernedContextSignal } from "./governed-context.ts";

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
  intendedMealDate?: string;
  dayType?: "weekday" | "weekend";
  plates?: unknown; // the served set, stored as jsonb for audit/replay
  engineVersion?: string;
  configVersion?: string;
  /** New user served neutral defaults — there is no profiles row to reference (see below). */
  stubbed?: boolean;
  /** RE's decision_trace (funnel + winners + near-miss alternatives), stored as-is (jsonb) —
   * present whenever the RE call succeeded, since compose.ts always sets
   * include_decision_trace=true on the outgoing request (WP-12). Absent on fallback/error paths,
   * since there was no RE decision to trace. */
  decisionTrace?: unknown;
  /** Authority-labelled request context used for this serving decision. */
  governedContextSignals?: GovernedContextSignal[];
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

  let insertedId: string | null = null;
  try {
    const db = createServiceRoleClient(ctx.config);
    const { data, error } = await withTimeout(
      db.from("recommendation_events").insert({
        profile_id: ev.householdId,
        household_id: ev.householdId,
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
        decision_trace: ev.decisionTrace ?? null,
        data_source: "real",
      }).select("id").single(),
      "recommendations.events.record",
    );
    if (error) throw error;
    insertedId = (data as { id: string } | null)?.id ?? null;
  } catch (e) {
    ctx.logger.warn("recommendation_event.persist_failed", {
      request_id: ev.requestId,
      household_id: ev.householdId,
      outcome: ev.outcome,
      detail: e instanceof Error ? e.message : String(e),
    });
    return;
  }

  // Store the exact governed context used for this served decision. The RPC preserves any user
  // correction already attached to an inferred feature and returns only active/confirmed state.
  if (ev.governedContextSignals?.length) {
    try {
      const db = createServiceRoleClient(ctx.config);
      const { error } = await withTimeout(
        db.rpc("materialize_governed_context_signals", {
          p_household_id: ev.householdId,
          p_signals: ev.governedContextSignals,
        }),
        "recommendations.events.materialize_governed_context",
      );
      if (error) throw error;
    } catch (e) {
      ctx.logger.warn("governed_context.persist_failed", {
        request_id: ev.requestId,
        household_id: ev.householdId,
        detail: e instanceof Error ? e.message : String(e),
      });
    }
  }

  // §0.1: emit one `shown_not_tapped` feedback_events row per served hero dish, synchronously
  // with the recommendation_events write above — this is the Edge-Function-side "served"
  // denominator Phase 2's bandit later reads (module doc, served.ts). A later real
  // accept/like/dislike/edit/swap row sharing this recommendation_event_id+dish_id supersedes it
  // at READ time; nothing here needs to delete/update it. Best-effort, same as the write above:
  // never turns an otherwise-successful recommendation into an error for the user.
  if (
    (ev.outcome === "success" || ev.outcome === "partial") && insertedId &&
    Array.isArray(ev.plates) && ev.plates.length > 0
  ) {
    const db = createServiceRoleClient(ctx.config);
    const served = flattenServedDishes(ev.plates);
    if (served.length > 0) {
      try {
        const dishIds = await resolveDishIdsByName(ctx, db, served.map((s) => s.dishName));
        const rows = buildShownNotTappedRows(ev.householdId, insertedId, served, dishIds);
        const { error: feError } = await withTimeout(
          db.from("feedback_events").insert(rows),
          "recommendations.events.record_shown_not_tapped",
        );
        if (feError) throw feError;
        ctx.logger.info("shown_not_tapped.recorded", {
          request_id: ev.requestId,
          household_id: ev.householdId,
          row_count: rows.length,
        });
      } catch (e) {
        ctx.logger.warn("shown_not_tapped.persist_failed", {
          request_id: ev.requestId,
          household_id: ev.householdId,
          detail: e instanceof Error ? e.message : String(e),
        });
      }

      // Exposure state is independent of the feedback denominator. Either secondary write may
      // fail during a rolling deployment without preventing the other from being retained.
      try {
        const { error: exposureError } = await withTimeout(
          db.rpc("record_recommendation_exposure_state", {
            p_recommendation_event_id: insertedId,
            p_items: toExposureItems(served),
          }),
          "recommendations.events.record_exposure_state",
        );
        if (exposureError) {
          // Rolling deploys are order-tolerant: a missing/new RPC cannot discard the already
          // recorded recommendation or shown denominator.
          ctx.logger.warn("recommendation_exposure_state.persist_failed", {
            request_id: ev.requestId,
            household_id: ev.householdId,
            detail: exposureError.message,
          });
        }
      } catch (e) {
        ctx.logger.warn("recommendation_exposure_state.persist_failed", {
          request_id: ev.requestId,
          household_id: ev.householdId,
          detail: e instanceof Error ? e.message : String(e),
        });
      }

      // Dated item/attribute impressions remain separate from feedback and from the undated
      // rolling variety model. Only surfaces that know the intended meal moment write this state.
      if (
        (ev.slot === "breakfast" || ev.slot === "lunch" || ev.slot === "dinner") &&
        ev.intendedMealDate && ev.dayType
      ) {
        try {
          const { error: temporalError } = await withTimeout(
            db.rpc("record_meal_attribute_exposure_state", {
              p_recommendation_event_id: insertedId,
              p_items: toMealAttributeExposureItems(served, {
                mealSlot: ev.slot,
                intendedMealDate: ev.intendedMealDate,
                dayType: ev.dayType,
              }),
            }),
            "recommendations.events.record_meal_attribute_exposure_state",
          );
          if (temporalError) throw temporalError;
        } catch (e) {
          ctx.logger.warn("meal_attribute_exposure_state.persist_failed", {
            request_id: ev.requestId,
            household_id: ev.householdId,
            detail: e instanceof Error ? e.message : String(e),
          });
        }
      }
    }
  }

  // Weekly class impressions are stored separately from feedback. Being shown a class can inform
  // repetition pressure, but must never be counted as the household selecting or accepting it.
  if (
    (ev.outcome === "success" || ev.outcome === "partial") && insertedId &&
    Array.isArray(ev.plates)
  ) {
    const servedClasses = flattenServedMealClasses(ev.plates);
    if (servedClasses.length > 0) {
      try {
        const db = createServiceRoleClient(ctx.config);
        const { error } = await withTimeout(
          db.rpc("record_meal_class_exposure_state", {
            p_recommendation_event_id: insertedId,
            p_items: toMealClassExposureItems(servedClasses),
          }),
          "recommendations.events.record_meal_class_exposure_state",
        );
        if (error) throw error;
      } catch (e) {
        ctx.logger.warn("meal_class_exposure_state.persist_failed", {
          request_id: ev.requestId,
          household_id: ev.householdId,
          detail: e instanceof Error ? e.message : String(e),
        });
      }
    }
  }
}

/** One row of a household's own recommendation history. `plates` is loaded only for the detail
 * surface; no other household's rows are reachable because every query is profile-scoped. */
export interface RecommendationHistoryRow {
  id: string;
  request_id: string;
  created_at: string;
  slot: string | null;
  outcome: string;
  plate_count: number;
  plates?: unknown;
}

/**
 * Read-only: the caller's own most recent recommendation_events rows, newest first. Used by the
 * plan Edge Function's "history" surface (P1-3) — the first read path this table has ever had;
 * previously recommendation_events accumulated real rows with no way for a user to see their own
 * history (docs/active/OPEN_ITEMS.md P1-3). Never throws: an empty array on any DB error, same
 * fail-open posture the write-side functions in this file already use, since a history screen
 * should degrade to "no history yet" rather than a hard error.
 */
export async function fetchRecentRecommendationEvents(
  ctx: RequestContext,
  householdId: string,
  limit = 20,
): Promise<RecommendationHistoryRow[]> {
  try {
    const db = createServiceRoleClient(ctx.config);
    const { data, error } = await withTimeout(
      db
        .from("recommendation_events")
        .select("id, request_id, created_at, slot, outcome, plate_count")
        .eq("profile_id", householdId)
        .order("created_at", { ascending: false })
        .limit(limit),
      "recommendations.events.fetchRecentRecommendationEvents",
    );
    if (error) throw error;
    return (data ?? []) as RecommendationHistoryRow[];
  } catch (e) {
    ctx.logger.warn("recommendation_history.fetch_failed", {
      household_id: householdId,
      detail: e instanceof Error ? e.message : String(e),
    });
    return [];
  }
}

/** Fetch one recommendation event, always scoped to the authenticated caller's profile. */
export async function fetchRecommendationEvent(
  ctx: RequestContext,
  householdId: string,
  eventId: string,
): Promise<RecommendationHistoryRow | null> {
  try {
    const db = createServiceRoleClient(ctx.config);
    const { data, error } = await withTimeout(
      db
        .from("recommendation_events")
        .select("id, request_id, created_at, slot, outcome, plate_count, plates")
        .eq("profile_id", householdId)
        .eq("id", eventId)
        .maybeSingle(),
      "recommendations.events.fetchRecommendationEvent",
    );
    if (error) throw error;
    return data as RecommendationHistoryRow | null;
  } catch (e) {
    ctx.logger.warn("recommendation_history.detail_fetch_failed", {
      household_id: householdId,
      event_id: eventId,
      detail: e instanceof Error ? e.message : String(e),
    });
    return null;
  }
}
