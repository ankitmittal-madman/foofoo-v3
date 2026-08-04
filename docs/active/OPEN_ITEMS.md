# Open Items

This document contains ONLY open/pending work, launch blockers, known bugs, missing
implementation, incomplete datasets, missing ontology, missing APIs, missing tests, missing
deployment work, security issues, and performance issues. Completed work is not listed here —
see `docs/archive/completed-phases/` for history. Source audit:
`docs/archive/audits/re_audit_v2/` (fresh clean-room audit, 2026-08-04).

---

## P0-1: Investigate the recommendation-events vs. plan-persistence gap
- **Priority:** P0
- **Area:** Database / Backend
- **Evidence:** Live query this session: `recommendation_events`=126, `week_plans`=0, `plan_slots`=0, `household_context`=0, `interaction_events`=0.
- **Why it matters:** Either a write path is silently failing for real users, or these 126 events bypass normal persistence. Unknown which — must be resolved before trusting any other production-behavior claim.
- **Current status:** OPEN — not yet investigated.
- **Expected outcome:** A root-cause trace (real request → real DB write, or a discovered failure point) and either a fix or a documented explanation.
- **Files involved:** `supabase/functions/recommendations/`, `supabase/functions/plan/`, `database/migrations/038_household_answers_context_and_events.sql`.
- **Estimated effort:** Small to diagnose.
- **Dependencies:** None.

## P0-2: Wire DPDP export/delete into the mobile app
- **Priority:** P0
- **Area:** Frontend / Compliance
- **Evidence:** `user-export`/`user-delete` Edge Functions implemented and authorized; zero references to either endpoint anywhere under `mobile/`.
- **Why it matters:** India's DPDP Act requires user-initiated data-subject rights; unreachable = non-compliant.
- **Current status:** OPEN — backend done, frontend not started.
- **Expected outcome:** A reachable UI (standalone screen or part of P1-4's profile screen) calling both endpoints.
- **Files involved:** `supabase/functions/user-export/`, `supabase/functions/user-delete/`, new `mobile/app/` screen.
- **Estimated effort:** Medium.
- **Dependencies:** None (can precede or follow P1-4).

## P0-3: Decide the fate of the two parallel recommendation surfaces
- **Priority:** P0
- **Area:** Frontend / Architecture
- **Evidence:** `mobile/app/recommendations.tsx`'s own header comment states it is unreachable; the active surface (`today.tsx`/`weekly-plan.tsx`) uses a different API family with no feedback/explanation UI.
- **Why it matters:** Root cause of P0-4 and P1-2; a single decision here unblocks both.
- **Current status:** OPEN — decision not made.
- **Expected outcome:** A recorded decision: port the dead screen's UI patterns to the active surface, or rebuild fresh.
- **Files involved:** `mobile/app/recommendations.tsx`, `mobile/app/(tabs)/today.tsx`, `mobile/app/(tabs)/weekly-plan.tsx`.
- **Estimated effort:** Small (decision) + Medium (implementation, tracked separately in P0-4/P1-2).
- **Dependencies:** None. Blocks P0-4, P1-2.

## P0-4: Feedback UI on the actively-routed screens
- **Priority:** P0
- **Area:** Frontend
- **Evidence:** `today.tsx`/`recipe/[dish].tsx` have no like/dislike/accept UI.
- **Why it matters:** Feedback data will never accumulate without this — also permanently blocks `s_pref` personalization.
- **Current status:** OPEN.
- **Expected outcome:** Like/dislike/accept controls on the daily-use screens, wired to the existing `POST /v1/feedback`.
- **Files involved:** `mobile/app/(tabs)/today.tsx`, `mobile/app/recipe/[dish].tsx`, `mobile/src/api/feedback.ts`.
- **Estimated effort:** Medium.
- **Dependencies:** P0-3.

## P1-1: Enable Supabase leaked-password-protection
- **Priority:** P1
- **Area:** Security
- **Evidence:** Live Supabase Auth advisor, this session — currently disabled.
- **Why it matters:** Free, real security improvement.
- **Current status:** OPEN.
- **Expected outcome:** Setting enabled in Supabase dashboard.
- **Files involved:** N/A (dashboard setting).
- **Estimated effort:** Trivial.
- **Dependencies:** None.

## P1-2: Recommendation-explanation UI
- **Priority:** P1
- **Area:** Frontend
- **Evidence:** `contributions`/`decision_trace` flow into the API response and get persisted; zero mobile screens render either.
- **Why it matters:** A real, already-built differentiator (explainable recommendations) is invisible to users.
- **Current status:** OPEN.
- **Expected outcome:** A "why this dish" UI surface on the recommendation/recipe screen.
- **Files involved:** `mobile/src/api/types.ts` (Contribution type already defined), recipe/today screens.
- **Estimated effort:** Medium.
- **Dependencies:** P0-3.

## P1-3: History/past-plans view
- **Priority:** P1
- **Area:** Backend + Frontend
- **Evidence:** No GET endpoint exists for household state; only a device-local, non-synced AsyncStorage cache exists client-side.
- **Why it matters:** Basic expected functionality; current "history" is lost on reinstall.
- **Current status:** OPEN.
- **Expected outcome:** A new read endpoint + a screen showing past recommendation/plan history.
- **Files involved:** New Edge Function or extension of `plan`, `mobile/src/lib/weeklyPlanStore.ts`, new screen.
- **Estimated effort:** Medium.
- **Dependencies:** None.

## P1-4: Profile/preferences-edit screen
- **Priority:** P1
- **Area:** Backend + Frontend
- **Evidence:** No route named profile/settings exists; `household` Edge Function is create-once, never revisited post-onboarding.
- **Why it matters:** Users' circumstances change (diet, allergies, household composition); no way to update today.
- **Current status:** OPEN.
- **Expected outcome:** A GET endpoint to read current household state + a screen to edit and re-save it.
- **Files involved:** `supabase/functions/household/`, new `mobile/app/` screen.
- **Estimated effort:** Medium-large.
- **Dependencies:** None. Natural home for P0-2 if not shipped standalone.

## P1-5: Mobile automated test coverage
- **Priority:** P1
- **Area:** Testing
- **Evidence:** Zero `*.test.ts(x)` files anywhere under `mobile/`, no jest config, no test script.
- **Why it matters:** Every other layer (backend/RE) has 755 passing tests; mobile has none — the one place a regression ships unnoticed.
- **Current status:** OPEN.
- **Expected outcome:** A jest/RN-testing-library setup plus tests for the 8 core journeys.
- **Files involved:** `mobile/` (new test infra).
- **Estimated effort:** Large.
- **Dependencies:** Higher-value after P0-3/P1-2/P1-3/P1-4 stabilize the surfaces being tested.

## P1-6: Wire IDF-cosine distance into pairing/scoring
- **Priority:** P1
- **Area:** Recommendation Engine
- **Evidence:** `ghar_re_core/similarity.py` implements the frozen spec's `d(a,b)` cosine formula; `pairing.py`'s `same_base()` still uses a cruder set-intersection proxy, and the cosine module's own docstring confirms it's used only for a separate discovery helper.
- **Why it matters:** The one real gap between the frozen spec and running code.
- **Current status:** OPEN — needs a Founder-level decision since it changes golden-master scoring output.
- **Expected outcome:** Either a ratified decision to wire it in (with golden-master regeneration), or a ratified decision to leave the proxy as the permanent design.
- **Files involved:** `ghar_re_core/pairing.py`, `ghar_re_core/similarity.py`, `ghar_re_core/tests/golden/`.
- **Estimated effort:** Medium (the hard part is already built).
- **Dependencies:** Founder decision.

## P1-7: Real monitoring/alerting
- **Priority:** P1
- **Area:** Observability
- **Evidence:** Only a log-based shim (`telemetry.ts`) exists; Sentry/PostHog/APM are explicitly "seams only, none wired" per the code's own comments.
- **Why it matters:** If the RE service goes down today, nothing pages anyone.
- **Current status:** OPEN.
- **Expected outcome:** At least one real alerting sink wired to the existing telemetry seam.
- **Files involved:** `supabase/functions/_shared/telemetry/telemetry.ts`.
- **Estimated effort:** Medium.
- **Dependencies:** None.

## P2 items (production improvements, not launch-blocking)
- P2-1: Expand nutrition data beyond 50/810 dishes.
- P2-2: Expand comfort-hero mapping beyond 17/36 resolved heroes.
- P2-3: Populate PRIOR table for PanIndia/Global zones (187/810 dishes get no regional prior boost).
- P2-4: Fix RLS policies re-evaluating `auth.uid()` per-row instead of `(select auth.uid())`.
- P2-5: Add a staging/approval gate before `fly_deploy.yml`'s auto-deploy.
- P2-6: Pin the Docker image by digest, not tag.
- P2-7: Archive dead `re_engine`-era ETL/validation scripts targeting dropped schemas.
- P2-8: Resolve unindexed-FK and duplicate-index advisor findings.

## P3 items (future roadmap)
- P3-1: Festival calendar mapping (currently fully absent).
- P3-2: Disease/health-condition dish suitability (currently fully absent; needs real clinical input).
- P3-3: Activate `s_pref` personalization once feedback volume clears a real training threshold (currently 9 rows).
- P3-4: Build a real multi-hop ingredient/dish knowledge graph (current state is flat lookup tables).
- P3-5: Load-test the RE service at full 810-dish scale and re-size the Fly.io machine.
</content>
