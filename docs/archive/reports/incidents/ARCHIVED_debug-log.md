# STATUS

ARCHIVED

## Reason

Implementation completed.

This document is retained for historical reference only.

It must not be used as the primary implementation guide.

Refer to the active documentation for the current source of truth.

---

# Debug Log

## 2026-08-04 — POST /v1/plan returning 400 on the calibration (cold-start) screen

**Reported symptom:** Browser console showed `POST https://cmkswalqpmmqojwdmqbv.supabase.co/functions/v1/plan 400 (Bad Request)` from `fetchCalibrationGrid()` (mobile/src/api/plan.ts) on the post-onboarding "Select what you like" screen (mobile/app/cold-start.tsx).

**Root cause (confirmed by):** the live `plan` Edge Function (deployed version before this fix) did not contain the `calibration` surface at all — pulled its deployed source via `mcp__supabase__get_edge_function` and its `SURFACES` map only had `cold_start`, `meal_plan`, `weekly_plan`, `class_dishes`, `recipe`. Local `supabase/functions/plan/handler.ts` (committed since `5b0a8b3`, further extended in `188b91a`) added `calibration`, but that code was never deployed. The client's `{surface:"calibration"}` request hit the deployed handler's "unknown surface" branch, throwing `ERR_VALIDATION_FAILED` (400) — confirmed against edge-function logs (`mcp__supabase__get_logs`), which showed the failing calls completing in 150–620ms (too fast to have called the RE at all), versus 1200–2000ms for the successful `/plan` calls nearby that did complete a real RE round trip.

**Layer:** Config/infra (deploy lag) — not a code defect. The committed source was correct; production was simply running an older version of it.

**Fix applied:** Deployed the current `supabase/functions/plan/` source (handler.ts, index.ts, and its full shared-dependency closure) via `mcp__supabase__deploy_edge_function` → version 3, `ACTIVE`. Re-fetched the deployed source afterward and confirmed `calibration` is now present (8 occurrences, matching the surface map entry + the cold_start/calibration event-recording branches).

**Re-verification:** Confirmed statically (deployed source now contains `calibration`). Could not trigger a real authenticated `POST /plan {surface:"calibration"}` end-to-end from this environment (no live user session/browser here) — a real user hitting the cold-start screen, or a manual authenticated curl/Postman call, is the remaining manual check to fully close this out.

**Pattern risk elsewhere:** CONFIRMED, not just theoretical. Audited all 5 non-cron Edge Functions by comparing each function's `updated_at` (from `mcp__supabase__list_edge_functions`) against the last git commit touching its `supabase/functions/<name>/` directory:

| Function | Deployed `updated_at` (UTC) | Last relevant commit (UTC) | Stale? |
|---|---|---|---|
| household | 2026-08-01 14:26:37 | 2026-08-04 02:34:04 (`ea077e7` — sets `onboarding_completed` on profile creation) | **YES — 3 days behind** |
| recommendations | 2026-08-01 14:29:58 | 2026-08-04 02:49:22 (`e487941` — cook_capability ranking bias + household_context wiring) | **YES — 3 days behind** |
| consent | 2026-08-02 02:26:39 | 2026-07-30 13:49:39 | No — deployed after last change |
| feedback | 2026-08-02 10:40:12 | 2026-08-02 10:29:28 | No — deployed after last change |
| plan | now current (this fix) | — | No (just fixed) |

`household` and `recommendations` are both currently serving stale logic in production and are the next fix candidates.
