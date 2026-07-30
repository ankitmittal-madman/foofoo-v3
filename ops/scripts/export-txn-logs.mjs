#!/usr/bin/env node
/**
 * Transaction log export — DB event rows -> plain-English daily log files.
 *
 * Bridges the raw event tables Supabase already persists into the same plain-English narrative
 * style as `supabase/functions/_shared/logging/userJourney.ts`, but for after-the-fact reporting
 * (a day's worth of activity) rather than real-time logging.
 *
 * TABLES EXPORTED (discovered from the actual migration ledger, not assumed):
 *   - public.recommendation_events  (database/migrations/038_household_answers_context_and_events.sql)
 *       one row per SERVED recommendation request — outcome, plate_count, latency_ms.
 *   - public.feedback_events        (038, same file) — accept/edit/swap/like/dislike/shown_not_tapped.
 *   - public.interaction_events     (database/migrations/012_interaction_audit_appendonly.sql)
 *       dish_accepted/locked/cooked/ordered/rated/never/not_today/swiped_past, onboarding
 *       preference events, plan_opened, session_depth.
 *   - public.suggestion_logs        (012, same file) — every dish the RE actually suggested,
 *       ranked, per slate.
 *
 * `public.context_log` (012) and `public.weather_cache` (012) are deliberately NOT exported here:
 * they describe environmental context, not a user or system action, so they don't fit either
 * output shape below (per-user narrative / system daily summary).
 *
 * USAGE
 *   node ops/scripts/export-txn-logs.mjs                  # today, live DB
 *   node ops/scripts/export-txn-logs.mjs --date 2026-07-29
 *   node ops/scripts/export-txn-logs.mjs --dry-run         # fixture data, no network/env required
 *
 * ENV (server-side names already used by supabase/functions/_shared/config/config.ts):
 *   SUPABASE_URL                 — project URL
 *   SUPABASE_SERVICE_ROLE_KEY    — service-role key (read-only usage here; never printed)
 *
 * TIMEZONE: the golden-master household fixtures and dish catalogue are India-market (cities:
 * Bengaluru/Ahmedabad/Pune/Mumbai; RE-DOC references IST-relative "season"/"weekday" derivation).
 * No single documented "project timezone" constant was found in-repo, so this script follows
 * that same market convention: Asia/Kolkata for the "which calendar day does this row belong to"
 * boundary, and states so explicitly rather than silently assuming UTC.
 *
 * PRIVACY (DOC-P3-07 §16 / DPDP): profile ids are truncated to 8 chars in every narrative line.
 * No email, JWT, or free-text answer content is ever written here — only the columns these
 * tables define, which are already non-free-text/enum/numeric per their CHECK constraints.
 *
 * OUTPUT: ops/logs/session-log/users/<date>__<short-profile-id>.txt (per profile) and
 * ops/logs/session-log/system/<date>.txt (platform summary). Append-only: re-running for a date
 * already exported appends a new "export run" section rather than overwriting the file.
 */
import { existsSync, mkdirSync, appendFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const TZ = "Asia/Kolkata";
const REPO_ROOT = dirname(dirname(dirname(fileURLToPath(import.meta.url))));
const OUT_USERS = join(REPO_ROOT, "ops", "logs", "session-log", "users");
const OUT_SYSTEM = join(REPO_ROOT, "ops", "logs", "session-log", "system");

function parseArgs(argv) {
  const args = { date: null, dryRun: false };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === "--date") args.date = argv[++i];
    else if (argv[i] === "--dry-run") args.dryRun = true;
  }
  return args;
}

function todayInTz() {
  // en-CA gives YYYY-MM-DD directly — simplest reliable way to get a TZ-local calendar date
  // without pulling in a date library dependency.
  return new Intl.DateTimeFormat("en-CA", { timeZone: TZ }).format(new Date());
}

function shortId(id) {
  if (!id) return "unknown";
  return id.length > 8 ? `${id.slice(0, 8)}…` : id;
}

function dayRangeUtc(dateStr) {
  // A "day" is defined in Asia/Kolkata (UTC+5:30, no DST) — compute UTC bounds for the
  // PostgREST >=/< range filter without a date library.
  const start = new Date(`${dateStr}T00:00:00+05:30`);
  const end = new Date(start.getTime() + 24 * 60 * 60 * 1000);
  return { startIso: start.toISOString(), endIso: end.toISOString() };
}

/** Minimal PostgREST GET — no @supabase/supabase-js dependency needed for a read-only export. */
async function fetchRows(baseUrl, serviceKey, table, column, startIso, endIso, extraSelect = "*") {
  const url =
    `${baseUrl}/rest/v1/${table}?select=${extraSelect}` +
    `&${column}=gte.${encodeURIComponent(startIso)}&${column}=lt.${encodeURIComponent(endIso)}` +
    `&order=${column}.asc`;
  const res = await fetch(url, {
    headers: {
      apikey: serviceKey,
      Authorization: `Bearer ${serviceKey}`,
    },
  });
  if (!res.ok) {
    throw new Error(`fetch ${table} failed: HTTP ${res.status} ${await res.text()}`);
  }
  return res.json();
}

// --- fixture data for --dry-run (no live DB/env needed) ------------------------------------
function fixtureRows() {
  return {
    recommendation_events: [
      {
        profile_id: "11111111-aaaa-bbbb-cccc-111111111111",
        request_id: "req-1",
        slot: "dinner",
        outcome: "success",
        plate_count: 7,
        latency_ms: 412,
        engine_version: "ghar-re-v1.0",
      },
    ],
    feedback_events: [
      {
        profile_id: "11111111-aaaa-bbbb-cccc-111111111111",
        event_type: "accept",
        slot: "dinner",
        detail: { dish: "Rajma Chawal" },
      },
    ],
    interaction_events: [
      {
        profile_id: "22222222-aaaa-bbbb-cccc-222222222222",
        event_type: "dish_cooked",
        meal_slot: "lunch",
        rating: 4,
      },
    ],
    suggestion_logs: [
      {
        profile_id: "22222222-aaaa-bbbb-cccc-222222222222",
        rank_in_slate: 1,
        class_code: "CLASS-A",
        cold_start_mode: false,
        confidence_at_suggestion: 0.82,
      },
    ],
  };
}

// --- narrative formatting --------------------------------------------------------------------
function narrateRecommendationEvent(r) {
  const parts = [`Served a recommendation request (slot: ${r.slot ?? "unspecified"})`];
  parts.push(`outcome=${r.outcome}, ${r.plate_count ?? 0} plate(s)`);
  if (r.latency_ms != null) parts.push(`${r.latency_ms}ms`);
  if (r.engine_version) parts.push(`engine ${r.engine_version}`);
  return `Recommendation: ${parts.join(", ")}.`;
}

function narrateFeedbackEvent(r) {
  const verbs = {
    accept: "accepted a suggested dish",
    edit: "edited a suggested plate",
    swap: "swapped out a suggested dish",
    like: "liked a dish",
    dislike: "disliked a dish",
    shown_not_tapped: "was shown a dish but did not act on it",
  };
  return `Feedback: ${verbs[r.event_type] ?? r.event_type} (slot: ${r.slot ?? "unspecified"}).`;
}

function narrateInteractionEvent(r) {
  const verbs = {
    dish_accepted: "accepted a dish suggestion",
    dish_locked: "locked in a dish for the day",
    dish_cooked: "marked a dish as cooked",
    dish_ordered: "ordered a dish instead of cooking it",
    dish_rated: `rated a dish${r.rating != null ? ` ${r.rating}/5` : ""}`,
    dish_never: "marked a dish as 'never suggest again'",
    dish_not_today: "declined a dish for today only",
    dish_swiped_past: "swiped past a suggested dish",
    onboarding_class_preference: "recorded an onboarding class preference",
    plan_opened: "opened their meal plan",
    session_depth: "continued browsing the app (session depth event)",
  };
  return `Interaction: ${verbs[r.event_type] ?? r.event_type} (slot: ${r.meal_slot ?? "unspecified"}).`;
}

function narrateSuggestionLog(r) {
  return (
    `Suggestion served: rank ${r.rank_in_slate} in slate, class ${r.class_code}, ` +
    `confidence ${r.confidence_at_suggestion}` +
    `${r.cold_start_mode ? " (cold-start mode)" : ""}.`
  );
}

// --- assembly ----------------------------------------------------------------------------------
function groupByProfile(rows, narrate) {
  const byProfile = new Map();
  for (const r of rows) {
    const key = shortId(r.profile_id);
    const lines = byProfile.get(key) ?? [];
    lines.push(narrate(r));
    byProfile.set(key, lines);
  }
  return byProfile;
}

function writeAppendSafe(path, header, lines) {
  const dir = dirname(path);
  if (!existsSync(dir)) mkdirSync(dir, { recursive: true });
  const stamp = new Date().toISOString();
  const block = [`\n=== export run @ ${stamp} ===`, header, ...lines, ""].join("\n");
  appendFileSync(path, block, "utf8");
}

async function main() {
  const { date: dateArg, dryRun } = parseArgs(process.argv.slice(2));
  const date = dateArg ?? todayInTz();

  let rowsByTable;
  if (dryRun) {
    console.log(`[export-txn-logs] --dry-run: using fixture data for ${date} (${TZ})`);
    rowsByTable = fixtureRows();
  } else {
    const baseUrl = process.env.SUPABASE_URL;
    const serviceKey = process.env.SUPABASE_SERVICE_ROLE_KEY;
    if (!baseUrl || !serviceKey) {
      console.error(
        "[export-txn-logs] SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY are not set. " +
          "Set both, or re-run with --dry-run to exercise the script against fixture data.",
      );
      process.exit(1);
    }
    const { startIso, endIso } = dayRangeUtc(date);
    console.log(`[export-txn-logs] exporting ${date} (${TZ}) — window ${startIso} .. ${endIso}`);

    const [recEvents, fbEvents, interactionEvents, suggestionLogs] = await Promise.all([
      fetchRows(baseUrl, serviceKey, "recommendation_events", "created_at", startIso, endIso),
      fetchRows(baseUrl, serviceKey, "feedback_events", "created_at", startIso, endIso),
      fetchRows(baseUrl, serviceKey, "interaction_events", "occurred_at", startIso, endIso),
      fetchRows(baseUrl, serviceKey, "suggestion_logs", "suggested_at", startIso, endIso),
    ]);
    rowsByTable = {
      recommendation_events: recEvents,
      feedback_events: fbEvents,
      interaction_events: interactionEvents,
      suggestion_logs: suggestionLogs,
    };
  }

  // --- per-user output -------------------------------------------------------------------------
  const perProfile = new Map();
  const merge = (map) => {
    for (const [profile, lines] of map) {
      const existing = perProfile.get(profile) ?? [];
      perProfile.set(profile, existing.concat(lines));
    }
  };
  merge(groupByProfile(rowsByTable.recommendation_events, narrateRecommendationEvent));
  merge(groupByProfile(rowsByTable.feedback_events, narrateFeedbackEvent));
  merge(groupByProfile(rowsByTable.interaction_events, narrateInteractionEvent));
  merge(groupByProfile(rowsByTable.suggestion_logs, narrateSuggestionLog));

  for (const [profile, lines] of perProfile) {
    const path = join(OUT_USERS, `${date}__${profile}.txt`);
    writeAppendSafe(path, `Household ${profile} — ${date} (${TZ})`, lines);
  }

  // --- system/platform summary -------------------------------------------------------------------
  const summaryLines = [
    `recommendation_events: ${rowsByTable.recommendation_events.length}`,
    `feedback_events: ${rowsByTable.feedback_events.length}`,
    `interaction_events: ${rowsByTable.interaction_events.length}`,
    `suggestion_logs: ${rowsByTable.suggestion_logs.length}`,
    `distinct households active: ${perProfile.size}`,
  ];
  const outcomeCounts = {};
  for (const r of rowsByTable.recommendation_events) {
    outcomeCounts[r.outcome] = (outcomeCounts[r.outcome] ?? 0) + 1;
  }
  for (const [outcome, count] of Object.entries(outcomeCounts)) {
    summaryLines.push(`  recommendation outcome "${outcome}": ${count}`);
  }
  const systemPath = join(OUT_SYSTEM, `${date}.txt`);
  writeAppendSafe(systemPath, `Platform summary — ${date} (${TZ})`, summaryLines);

  console.log(`[export-txn-logs] wrote ${perProfile.size} per-user file(s) + 1 system file.`);
}

main().catch((err) => {
  console.error("[export-txn-logs] failed:", err.message);
  process.exit(1);
});
