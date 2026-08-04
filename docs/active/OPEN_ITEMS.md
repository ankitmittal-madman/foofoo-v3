# Open Items

This document contains ONLY open/pending work, launch blockers, known bugs, missing
implementation, incomplete datasets, missing ontology, missing APIs, missing tests, missing
deployment work, security issues, and performance issues. Completed work is not listed here —
see `docs/archive/completed-phases/` for history. Source audit:
`docs/archive/audits/re_audit_v2/` (fresh clean-room audit, 2026-08-04).

---

## P0-1: Investigate the recommendation-events vs. plan-persistence gap
- **Priority:** P0
- **Status:** Completed 2026-08-04. Root cause: live edge-function logs showed `plan` is the sole
  active traffic surface (zero `/v1/recommendations` requests) and `plan/handler.ts` simply never
  called the already-correct, already-tested `recordHouseholdContext`. Fixed by wiring that call
  into `plan/handler.ts` for every surface with a resolved household. Deployed to production
  (`plan` function, v4, 2026-08-04).
- **Files involved:** `supabase/functions/plan/handler.ts`.

## P0-2: Wire DPDP export/delete into the mobile app
- **Priority:** P0
- **Status:** Completed 2026-08-04. New `mobile/src/api/account.ts` (export request/poll,
  delete-account with exact-phrase confirmation) wired into a new `mobile/app/(tabs)/settings.tsx`
  screen, added to the tab layout.
- **Files involved:** `mobile/src/api/account.ts`, `mobile/app/(tabs)/settings.tsx`, `mobile/app/(tabs)/_layout.tsx`.

## P0-3: Decide the fate of the two parallel recommendation surfaces
- **Priority:** P0
- **Status:** Completed 2026-08-04. Decision: retired the dead surface — live logs confirmed zero
  traffic to `mobile/app/recommendations.tsx`/`mobile/src/api/recommendations.ts`; both deleted.
  `today.tsx` (the actually-routed screen) got the feedback/explanation UI instead (see P0-4/P1-2).
- **Files involved:** `mobile/app/recommendations.tsx` (deleted), `mobile/src/api/recommendations.ts` (deleted).

## P0-4: Feedback UI on the actively-routed screens
- **Priority:** P0
- **Status:** Completed 2026-08-04. `today.tsx` rewritten with a `DishCard` component: like/dislike
  buttons wired to `POST /v1/feedback`, plus a "Why this?" toggle showing the match score and
  cuisine/class explanation. Backend `FEEDBACK_ELIGIBLE_SURFACES` widened to include
  `meal_plan`/`class_dishes` so feedback on these surfaces is actually accepted.
- **Files involved:** `mobile/app/(tabs)/today.tsx`, `supabase/functions/plan/handler.ts`.

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
- **Status:** Completed 2026-08-04, bundled with P0-4. `DishCard`'s "Why this?" toggle on
  `today.tsx` renders the match score and cuisine/class explanation using the RE's existing
  `contributions`/score fields.
- **Files involved:** `mobile/app/(tabs)/today.tsx`.

## P1-3: History/past-plans view
- **Priority:** P1
- **Status:** Completed 2026-08-04. New `"history"` surface on `plan/handler.ts` (pure read via
  `fetchRecentRecommendationEvents`) plus a new `mobile/app/history.tsx` reverse-chronological
  list screen, reachable from Settings.
- **Files involved:** `supabase/functions/plan/handler.ts`, `supabase/functions/recommendations/events.ts`, `mobile/app/history.tsx`, `mobile/src/api/plan.ts`.

## P1-4: Profile/preferences-edit screen
- **Priority:** P1
- **Status:** Completed 2026-08-04. New `"profile"` GET surface on `plan/handler.ts` and a real
  UPDATE path added to `household/handler.ts` (previously the handler only ever created a
  household once and silently no-op'd on repeat calls — genuine bug found and fixed while
  building this, with regression tests added). New `mobile/app/profile-edit.tsx` screen. Also
  fixed a stale validation cap on `allergen_flags` (7-bit max, should have been 9-bit per the
  WP-21 fish/mustard extension — found while wiring this screen).
- **Files involved:** `supabase/functions/plan/handler.ts`, `supabase/functions/household/handler.ts`, `supabase/functions/household/store.ts`, `supabase/functions/household/schema.ts`, `mobile/app/profile-edit.tsx`.

## P1-5: Mobile automated test coverage
- **Priority:** P1
- **Status:** Partially completed 2026-08-04 — honest scoping, not full 8-journey coverage. Jest +
  jest-expo + @testing-library/react-native infra stood up from scratch (previously zero test
  files, no jest config). 9 passing tests: pure-logic coverage for allergen-bit encoding and API
  error-message mapping. No RN component-render tests yet (e.g. Settings' confirmation-phrase
  gating). **Remaining:** component-render tests for the new P0-2/P0-4/P1-3/P1-4 screens.
- **Files involved:** `mobile/package.json`, `mobile/jest.config.js`, `mobile/jest.setup.js`, `mobile/src/onboarding/__tests__/`, `mobile/src/api/__tests__/`.

## P1-6: Wire IDF-cosine distance into pairing/scoring
- **Priority:** P1
- **Status:** Completed. Archived — see `docs/archive/completed-phases/[ACTIVE]_RE_Compliance_Review_2026-08-04_v1.0.md` (Item 2).
- `same_base()` now computes `cosine(base-ingredient vectors) > theta_base` exactly per the frozen spec (theta_base=0.6, taken from the spec, not invented); golden-master verified unaffected on the 39-dish sample. Also fixed in the same review: `_cuis()`'s missing 0.70 "same parent cuisine" tier, and an `m_season` monsoon-branch bug (returned 0.5 instead of the spec's required 0).

## P1-7: Real monitoring/alerting
- **Priority:** P1
- **Status:** Completed 2026-08-04. `webhookSink()` (fire-and-forget POST, 3s timeout, never
  suppresses the fallback log) plus `resolveTelemetrySink()` wired directly into
  `error-boundary.ts` — the one place every request across every Edge Function already flows
  through unconditionally — rather than via the never-instantiated `Container`. Activates when
  `TELEMETRY_WEBHOOK_URL` is configured (not fabricated — no real webhook URL was provided this
  session, so it currently falls back to log-only until Founder supplies one); log-only otherwise.
- **Files involved:** `supabase/functions/_shared/telemetry/telemetry.ts`, `supabase/functions/_shared/middleware/error-boundary.ts`, `supabase/functions/_shared/config/env.ts`, `supabase/functions/_shared/config/config.ts`.

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
