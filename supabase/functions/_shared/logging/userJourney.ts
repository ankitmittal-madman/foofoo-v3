/**
 * User Journey Logger — plain-English, per-profile narrative log (WP-8/install-logging-infra).
 *
 * ONE audience: a non-technical PM or Founder who wants to read, in plain English, what a
 * specific profile did and why the app responded the way it did — without reading code, raw
 * event tables, or the structured JSON logger's field names.
 *
 * Built ON TOP of the existing sanctioned sink (`./logger.ts`) — this module never calls
 * console.* itself. Every entry here is ALSO a structured JSON line (via a bound child logger,
 * `event: "user_journey"`), so nothing is lost from the machine-readable trail; this module only
 * adds a `narrative` string a human can read directly, plus an in-memory per-profile ring buffer
 * so a recent journey can be dumped on demand (e.g. from a debugging endpoint or a REPL) without
 * a database client.
 *
 * Action vocabulary below is discovered from the real handlers/services, not invented:
 *   - consent          <- supabase/functions/consent/handler.ts + consent-service.ts
 *                          (consent_type: personalization | analytics | push_notifications |
 *                          data_retention — public.consent_records CHECK, migration 006)
 *   - onboarding write <- supabase/functions/household/handler.ts (screens logged to
 *                          onboarding_sessions, household_answers upserted, profile created once)
 *   - recommendation   <- supabase/functions/recommendations/handler.ts (outcome vocabulary:
 *                          success | partial | timeout | network | http | bad_body | fallback,
 *                          per public.recommendation_events CHECK, migration 038)
 *   - feedback         <- supabase/functions/feedback/handler.ts (WP-15; event_type vocabulary:
 *                          accept | edit | swap | like | dislike | shown_not_tapped, per
 *                          public.feedback_events CHECK, migration 038)
 *
 * NO PII and NO secrets (DOC-P3-07 §16 / DPDP): profile ids are truncated to 8 chars before being
 * used as either the log key or appearing in a narrative string; no email, JWT, or raw answer
 * free-text is ever interpolated into a narrative.
 */
import { createLogger, type Logger } from "./logger.ts";

const journeyLog: Logger = createLogger("info", { event: "user_journey" });

/** Max narrative entries kept per profile in the in-memory ring buffer (dev/QA aid only — this
 * is NOT a durable store; `ops/scripts/export-txn-logs.mjs` is the durable, DB-backed equivalent). */
const MAX_ENTRIES_PER_PROFILE = 200;

interface JourneyEntry {
  ts: string;
  category: "onboarding" | "consent" | "recommendation" | "feedback";
  narrative: string;
}

const journeys = new Map<string, JourneyEntry[]>();

function shortId(profileId: string): string {
  return profileId.length > 8 ? `${profileId.slice(0, 8)}…` : profileId;
}

function record(profileId: string, category: JourneyEntry["category"], narrative: string): void {
  const key = shortId(profileId);
  const entry: JourneyEntry = { ts: new Date().toISOString(), category, narrative };

  const existing = journeys.get(key) ?? [];
  existing.push(entry);
  if (existing.length > MAX_ENTRIES_PER_PROFILE) existing.shift();
  journeys.set(key, existing);

  journeyLog.info(narrative, { profile: key, category });
}

/** Public API of the user journey logger — see file header for full context. Each method below
 * carries its own trigger/vocabulary doc comment. */
export const UserJourney = {
  /**
   * One onboarding write call (POST /v1/household) — a household submitted answers for one or
   * more screens. `screenIds` mirrors onboarding_sessions.screen_id (migration 006); `profileCreated`
   * flags the one-time event where the 5 required profiles columns finally completed.
   */
  logOnboardingStep(
    profileId: string,
    screenIds: string[],
    opts?: { profileCreated?: boolean; membersWritten?: number },
  ): void {
    const parts = [`Household answered onboarding screen(s): ${screenIds.join(", ")}`];
    if (opts?.profileCreated) parts.push("→ profile created (all required fields now known)");
    if (opts?.membersWritten) parts.push(`→ ${opts.membersWritten} household member(s) saved`);
    record(profileId, "onboarding", parts.join(" "));
  },

  /**
   * One POST /v1/consent call — real consent_type/granted vocabulary from
   * public.consent_records (migration 006). `personalizationGranted` is the resolved flag that
   * gates whether onboarding may proceed (DOC-P3-06 §06.1).
   */
  logConsentDecision(
    profileId: string,
    consents: Array<{ consentType: string; granted: boolean }>,
    personalizationGranted: boolean,
  ): void {
    const summary = consents
      .map((c) => `${c.consentType.replace(/_/g, " ")}: ${c.granted ? "granted" : "declined"}`)
      .join("; ");
    const narrative = `Household recorded consent decisions — ${summary}. ` +
      `Personalization is ${personalizationGranted ? "ON" : "OFF"} for this household.`;
    record(profileId, "consent", narrative);
  },

  /**
   * One POST /v1/recommendations call resolved — real outcome vocabulary from
   * public.recommendation_events (migration 038): success | partial | timeout | network | http |
   * bad_body | fallback. This is the single most useful entry for "why did the app show that" —
   * it names the outcome the Edge Function actually recorded, not an inferred guess.
   */
  logRecommendationOutcome(
    profileId: string,
    outcome: "success" | "partial" | "timeout" | "network" | "http" | "bad_body" | "fallback",
    plateCount: number,
    opts?: { latencyMs?: number; detail?: string; reServed?: boolean },
  ): void {
    let narrative: string;
    switch (outcome) {
      case "success":
        narrative = `App served ${plateCount} recommended plate(s) — the RE responded normally.`;
        break;
      case "partial":
        narrative =
          `App served ${plateCount} plate(s), but the RE raised warnings for this request ` +
          `(fewer eligible dishes than usual for this household/context).`;
        break;
      case "fallback":
        narrative = `App served a fallback plate — the RE's response could not be used ` +
          `(${opts?.detail ?? "reason not recorded"}).`;
        break;
      case "timeout":
        narrative = "App served a fallback plate — the RE did not respond in time.";
        break;
      case "network":
        narrative = "App served a fallback plate — could not reach the RE (network failure).";
        break;
      case "http":
        narrative = `App served a fallback plate — the RE returned an HTTP error.`;
        break;
      case "bad_body":
        narrative =
          "App served a fallback plate — the RE's response did not match the expected contract.";
        break;
    }
    if (opts?.latencyMs !== undefined) narrative += ` (${opts.latencyMs}ms)`;
    record(profileId, "recommendation", narrative);
  },

  /**
   * One POST /v1/feedback call resolved (WP-15) — real event_type vocabulary from
   * public.feedback_events (migration 038): accept | edit | swap | like | dislike |
   * shown_not_tapped plus explicit plan controls. Preference and suppression state is updated by
   * feedback/events.ts; this logger remains narrative-only.
   */
  logFeedbackRecorded(
    profileId: string,
    eventType:
      | "accept"
      | "edit"
      | "swap"
      | "like"
      | "dislike"
      | "shown_not_tapped"
      | "never"
      | "not_today"
      | "lock"
      | "unlock"
      | "add_to_date",
    dishResolved: boolean,
  ): void {
    const verb: Record<typeof eventType, string> = {
      accept: "accepted a served plate as-is",
      edit: "edited a served plate",
      swap: "swapped a dish out of a served plate",
      like: "liked a dish",
      dislike: "disliked a dish",
      shown_not_tapped: "was shown a dish they didn't tap on",
      never: "permanently excluded a dish",
      not_today: "suppressed a dish for today",
      lock: "locked a meal slot",
      unlock: "unlocked a meal slot",
      add_to_date: "added a dish to another date",
    };
    const narrative = `Household ${verb[eventType]}` +
      (dishResolved ? "." : " (dish not yet matched to the catalogue — recorded anyway).");
    record(profileId, "feedback", narrative);
  },

  /** Return the full plain-English journey for one profile, oldest first — for a debugging
   * endpoint, a REPL, or a support conversation. Returns "" if nothing has been logged yet. */
  getFullLog(profileId: string): string {
    const entries = journeys.get(shortId(profileId)) ?? [];
    return entries.map((e) => `[${e.ts}] (${e.category}) ${e.narrative}`).join("\n");
  },

  /** Clear one profile's in-memory journey (does not touch any DB table). */
  clearLog(profileId: string): void {
    journeys.delete(shortId(profileId));
  },
};
