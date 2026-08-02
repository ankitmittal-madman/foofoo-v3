# [DRAFT]_WP-12_Per_User_Recommendation_Decision_Trace_v1.0

**Status:** DRAFT — designed and implemented in `ghar_re_core`, `ghar_re_service`, the shared contract, and the Edge Function/DB side this session; NOT yet live, because the updated `ghar_re_service` has not been redeployed to Fly.io from this session (no `flyctl`/Fly credentials available here). The DB migration and Edge Function changes ARE live. See §3 for the exact deploy/verify gap.
**Version:** v1.0
**Date:** 2026-08-02
**Placement:** docs/project-history/work-packages/[DRAFT]_WP-12_Per_User_Recommendation_Decision_Trace_v1.0.md
**Builds on:** WP-8D RE Core, WP-8E RE Integration Layer, migration 038 (recommendation_events).
**Governance basis:** RE-DOC-11 §6 (open/additive contract fields, "pass through as-is"), `ghar_re_core/decision_log.py`'s own LOGGING-ONLY invariant (never influences scoring/ranking/filtering).

---

## Executive Summary

The Founder asked whether per-user recommendation decisions are logged with the funnel of how many catalogue meals survive each filtering stage. The honest answer, established by direct code inspection: **no.** `ghar_re_core/decision_log.py` already contained the right idea — a "why these 7 plates, why not these others" record — but it is Python `logging`, a no-op unless a handler is attached, and this session confirmed by grep that the deployed `ghar_re_service` never attaches one and never calls it directly. It was dead weight in production. Nothing captured the earlier funnel stages (catalogue → after diet filter → after jain/allergen/weaning/fasting filters) at all, anywhere.

This WP makes it real: the RE now computes and can return a `decision_trace` per request (funnel counts + served plates + top-5 near-miss alternatives with a concrete reason each lost), and the Edge Function persists it into a new `recommendation_events.decision_trace` column — so every recommendation event has a durable, queryable, per-user record of how the catalogue narrowed down to what was shown, not just the final plates and their score contributions (which is all that existed before).

**What was implemented and verified this session:**
- `ghar_re_core/scoring.py::eligibility_funnel()` — new, additive function that replays `eligible()`'s exact filter order (A1 diet → A2 jain → A3 allergen → A4 weaning → A5 fasting) over the full catalogue and reports the dish count surviving each stage. Reuses `eligible()`'s own `pass_*` functions so the two can never silently drift apart.
- `ghar_re_core/decision_log.py::build_decision_trace()` — extracted from the existing logging function so the trace can be returned directly (winners, top-5 alternatives with `why_it_lost`, plain-English reasoning, and now the funnel) regardless of whether any logging handler is attached. `log_assemble7_decision()` is now a thin wrapper around it — behavior for existing callers is unchanged.
- `ghar_re_core/pairing.py::assemble_7()` / `ghar_re_core/pipeline.py::recommend()` — new opt-in `with_trace=True` parameter returns `(chosen, decision_trace)` / includes `result["decision_trace"]`. Default behavior (no `with_trace`) is byte-for-byte unchanged.
- `contracts/ghar-re-v1.schema.json` — added optional `include_decision_trace` (request) and `decision_trace` (response) fields. Both schemas already had `additionalProperties: true`, so this is a documentation-level addition, not a breaking change — verified: neither the Python (`jsonschema`) nor TypeScript (Ajv) validator rejects the new fields, and no existing test asserts an exact request/response shape that would break.
- `ghar_re_service/ghar_re_service/engine.py` — reads `request.get("include_decision_trace")`, threads `with_trace` through to `core_pipeline.recommend()`, includes `decision_trace` in the response only when requested.
- `database/migrations/044_recommendation_events_decision_trace.sql` — adds `recommendation_events.decision_trace jsonb` (nullable). **Applied to the live Supabase project and verified.**
- `supabase/functions/recommendations/compose.ts` — `buildRequest()` now always sets `include_decision_trace: true` on the outgoing RE request (every event gets traced, per the Founder's "every event" framing).
- `supabase/functions/recommendations/events.ts` / `handler.ts` — `recordRecommendationEvent()` now accepts and persists `decisionTrace`, wired from `result.body.decision_trace` on the success path.
- Tests: 4 new `ghar_re_core` tests (funnel monotonicity, funnel agrees exactly with `eligible()`'s own count, trace never changes served plates, winners match served plates) + 2 new `ghar_re_service` tests (trace omitted by default, trace present and internally consistent when requested, plates unchanged either way). **All verified locally**: `python3 -m pytest ghar_re_core/tests/ ghar_re_service/tests/` → 84 passed, 1 pre-existing unrelated failure (confirmed pre-existing by running the identical test against an unmodified checkout — `test_recommendations_end_to_end`'s West-MH rainy "Kanda Bhaji" assertion, not touched by this work).

## 1. What the trace actually contains, per request

```
decision_trace: {
  funnel: [
    {"stage": "catalogue_total",        "count": 802},
    {"stage": "after_diet_filter",      "count": 253},
    {"stage": "after_jain_filter",      "count": 253},
    {"stage": "after_allergen_filter",  "count": 253},
    {"stage": "after_weaning_filter",   "count": 253},
    {"stage": "after_fasting_filter",   "count": 253}
  ],
  winners: [ {"rank": 1, "plate": "Bharli Vangi + Dal Dhokli  (+ Roti)", "score": 4.8882}, ... ],
  alternatives_considered: [
    {"plate": "...", "score": ..., "why_it_lost": "hero dish already used in a served plate (no-duplicate guard, §S4.6)"},
    ...
  ],
  reasoning: "Served 7 plate(s) for ... ranked by plate_score (BASE x GAIN_Q15, pairing-adjusted). Top choice: ..."
}
```
This directly answers "from total meals available, how many are shortlisted and finally presented" per individual request, durably, per user — the exact gap identified before this WP.

## 2. What was deliberately NOT done

- **No mobile UI.** This is a backend/observability feature — a queryable log, not a user-facing screen. Building a "why was this recommended" UI is a separate, future product decision.
- **No change to which plates are served.** `eligibility_funnel()` and `build_decision_trace()` are read-only over already-decided results — covered by a dedicated test (`test_decision_trace_never_changes_which_plates_are_served`) and consistent with `decision_log.py`'s own pre-existing, non-negotiable LOGGING-ONLY invariant.
- **No always-on request-side default beyond `compose.ts`.** The RE only computes the funnel/alternatives payload when `include_decision_trace=true` is set — bounded, opt-in cost at the contract level, even though this repo's Edge Function currently always asks for it.
- **`ghar_re_service/tests/test_service.py::test_recommendations_end_to_end`'s pre-existing failure** (West-MH "Kanda Bhaji" not served) was found, confirmed pre-existing via a clean-checkout run, and left alone — out of scope for this WP, flagged here rather than silently bundled in or silently ignored.

## 3. What is NOT yet live — the one real gap

Everything above is implemented and locally test-verified. Two things are also already live:
- The DB migration (`recommendation_events.decision_trace` column exists on the live project, verified via `pg_constraint`-equivalent column check after `apply_migration`).
- The Edge Function code changes are written and committed to `main`.

**What is NOT live:** the updated `ghar_re_service` (the actual Fly.io-deployed Python service) has not been redeployed. This session has no `flyctl` binary and no Fly.io credentials/network access — the same constraint already documented in WP-8G. Until `ghar_re_service` is redeployed:
- The live RE will silently ignore the new `include_decision_trace` request field (contract is additive/open by design, so this doesn't error — it just won't produce a `decision_trace` yet).
- `recommendation_events.decision_trace` will stay `NULL` for every real request, because `result.body.decision_trace` will be `undefined` from the still-old deployed service.
- The Edge Function code is safe to be live ahead of the RE redeploy — it only ever writes `decisionTrace` when the RE actually returns one (`ev.decisionTrace ?? null`), so there is no error state, just an inert field until the RE catches up.

**Required next step, outside this session's reach:** redeploy `ghar_re_service` to Fly.io from the updated `main`. Once done, every new `recommendation_events` row will carry a real `decision_trace`, and the answer to "how many meals were shortlisted for test_05" becomes a live `SELECT decision_trace->'funnel' FROM recommendation_events WHERE ...` query instead of a one-off reconstruction from code + response contributions (as this session did to answer the original question by hand).

## 4. Critical Self-Review

- The core claim this WP responds to — "no funnel logging exists, decision_log.py is dead code in production" — was established by direct grep evidence (`ghar_re_service` never imports/calls `decision_log`), not assumption; re-confirm this after the Fly.io redeploy actually lands, since a redeploy could in principle wire the module differently than this WP assumes.
- All Python-side changes were verified with a real local pytest run (84 passed), including a same-file confirmation that the one failure is pre-existing and unrelated. The Deno/TypeScript-side changes (`compose.ts`, `events.ts`, `handler.ts`) could NOT be run through `deno test`/`deno check` in this sandbox (no `deno` binary, consistent with earlier sessions' same limitation) — verified instead by careful manual reading of the contract validator's `additionalProperties` handling and confirming no existing test asserts an exact request/response shape that the new field would break. This is a real gap versus the Python-side verification and should be re-run through actual `deno test`/`deno check` in CI before merging with full confidence.
- The Fly.io redeploy gap means this WP's headline feature is not actually observable yet for any real user, including `test_05` — the funnel numbers given in chat for `test_05` were reconstructed by hand from code + the existing `contributions[]` data, not read from a live `decision_trace`. That reconstruction is accurate but is exactly the manual process this WP exists to make unnecessary going forward.

## 5. Versioning & Placement

v1.0 — initial implementation, pending Fly.io redeploy to go fully live. Builds on WP-8D/8E; unrelated to WP-8G (recommendation variety) and WP-11 (launch readiness), though WP-11's "reconcile the migration ledger" item now also covers this WP's migration 044 landing cleanly in sequence.

## Founder Sign-off

