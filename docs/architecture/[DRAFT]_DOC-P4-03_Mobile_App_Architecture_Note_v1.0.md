Status: DRAFT
Version: 1.0
Date: 2026-07-30
Placement: docs/architecture/ (P4 series — application layer, companion to DOC-P4-00/DOC-P4-02)
Supersedes: none
Dependencies: DOC-P3-06 (API Contract Specification v1.2), contracts/ghar-re-v1.schema.json,
supabase/functions/household, supabase/functions/recommendations, docs/architecture/DOC-05
(Information Architecture v1.2), docs/architecture/DOC-06 (UX Design System v1.1)

# DOC-P4-03 — Mobile App Architecture Note v1.0

## Executive Summary
No frontend/mobile client exists anywhere in this repository's history (confirmed by direct git
history audit at session start — no `package.json`, `app.json`, or Expo trace on any branch). This
note proposes the client as a new top-level component, `mobile/`, and scaffolds it against the two
real endpoints that exist today (`POST /v1/household`, `POST /v1/recommendations`). It stops short
of the full 35-screen onboarding flow in DOC-05 — Phase 1 wires four onboarding screens plus one
recommendation screen against the real backend, proving the contract rather than the UI.

**Governance note:** `mobile/` is a new top-level folder. CLAUDE.md's Placement Rule requires an
approved RACR for this. It is added here because the Founder's own task instruction explicitly
requested this exact top-level component, scoped identically to how `ghar_re_service/` and
`supabase/` were added in prior work — but no RACR document exists yet. Flagged for Founder
follow-up, not silently bypassed.

## 1. Stack confirmation
`package.json`/`app.json` do not exist anywhere in git history, so there is no prior stack
decision to confirm against — proceeding with the stack given in the task: React Native + Expo SDK
52+, Supabase JS client, TanStack Query, Expo Router for navigation. Deploy targets (Vercel web /
EAS mobile) are out of scope for Phase 1 (no build/deploy config beyond what Expo scaffolds by
default).

## 2. Directory structure (`mobile/`)
```
mobile/
  app/                      Expo Router routes (file-based)
    _layout.tsx             Root layout: SessionProvider + QueryClientProvider
    index.tsx               Redirect: signed-in+onboarded -> recommendations, else -> auth/onboarding
    (auth)/
      sign-in.tsx
      sign-up.tsx
    (onboarding)/
      _layout.tsx           Guards: redirects to sign-in if no session
      profile-basics.tsx    Screen 1 — the 5 profiles-required fields (gates everything else)
      household.tsx         Screen 2 — Q1/Q2 + household_members
      food-and-health.tsx   Screen 3 — Q6/Q7/Q10/Q11
      lifestyle.tsx         Screen 4 — Q13/Q14/Q15 -> navigates to recommendations
    recommendations.tsx     Calls POST /v1/recommendations, renders the 7 plates plainly
  src/
    auth/
      supabaseClient.ts     Supabase client (GoTrue against the existing live Auth)
      SessionContext.tsx    Session state + bearer token accessor
    api/
      client.ts             Thin fetch wrapper: base URL + Authorization: Bearer <jwt>
      household.ts           postHousehold() — typed to schema.ts's request/response shape
      recommendations.ts     postRecommendations() — typed to contract.ts's response shape
      types.ts               Shared request/response types, hand-mirrored from the Edge Function
                              source (schema.ts, contract.ts) since no OpenAPI/generated client
                              exists yet
    lib/
      queryClient.ts         TanStack QueryClient instance
  app.json, package.json, tsconfig.json, .env.example
```

## 3. Onboarding screen ordering — deliberately NOT DOC-05's order
DOC-05 v1.2's onboarding sequence (OB-01 cohort -> OB-02 household/members -> OB-03 state/city ->
OB-04 diet -> ... -> OB-08 profile name) collects household composition **before** the five
`profiles` NOT NULL columns are complete. `household/handler.ts` hard-rejects `household_members`
writes until a `profiles` row exists (FK constraint) — confirmed by direct read of
`household/handler.ts` step 4 and `schema.ts`'s `PROFILE_REQUIRED_FIELDS`. Following DOC-05's literal
order in Phase 1 would 422 on the very first household-composition screen for every new user.

Phase 1 reorders to: profile-basics (Q3/Q4 + diet_type + cook_capability + primary_cook_name) FIRST,
then household/members, then remaining household_answers. This is flagged as a real API-contract
surprise, not silently worked around — the UX sequence and the backend's write-ordering constraint
are currently in tension and DOC-05 should be reconciled with this before Phase 2 polish.

## 4. Screen copy
`ghar_re_v1_0_derivation_D1_D7_FROZEN.md` (read in full) defines Q1–Q15 **semantics** (D1–D7 math),
not UI copy — it has no screen wireframes or wording. Actual onboarding wireframe copy lives in
DOC-06 (`OB-00`, `OB-03`, `OB-07`, `OB-08b`) and the screen map in DOC-05, but neither covers all
four Phase-1 screens' copy, and DOC-06's actual on-screen text is written around a cohort-first flow
that Phase 1 deliberately reorders (§3). Rather than inventing polished copy that isn't backed by an
approved wireframe, Phase 1 labels every field with its plain-English question paired with its
`question_key`/schema name in the code as the source of truth, and does not attempt DOC-06's visual
design (photos, swipe cards, stat bubbles) — this matches the task's explicit "no design polish yet"
scope for the recommendation screen, extended here to onboarding for the same reason: no signed-off
copy to use verbatim.

## 5. API client
Both endpoints are called with the Supabase session's JWT as `Authorization: Bearer <token>` —
`authenticate.ts`'s `supabaseJwtVerifier` calls `GoTrue`'s `auth.getUser()`, so any valid Supabase
Auth session token is accepted. `POST /v1/household` and `POST /v1/recommendations` both apply
`requireOwnership(claims, householdId)`: when `household_id` is omitted from the body, the handler
defaults it to `claims.userId`, so the client can simply omit `household_id` on every call and rely
on this default rather than tracking/sending its own id.

## 6. Verification performed this session (no live Supabase project exists to test against)
`npm install` succeeded; `tsc --noEmit` passes; `npx expo export --platform web` bundles and
serves correctly (verified with a headless Chromium screenshot of the sign-in, onboarding-redirect,
and recommendations screens — the latter correctly shows a "No active session" error+retry state
when called unauthenticated, proving the client's own error handling, not just its happy path).
Two real fixes were needed to get a clean web bundle, both worth flagging as genuine surprises:
- `app.json`'s `web.output` had to be `"single"`, not `"static"` — Expo Router's static-rendering
  (SSG) pre-render step runs in Node with no `window`, and `@supabase/supabase-js`'s GoTrue client
  touches `AsyncStorage`/`window` at construction time, crashing the prerender. Not an issue for
  `expo start` dev mode or for native (RN has no such prerender step) — only static web export.
- The installed `@supabase/supabase-js` (2.45+) does a dynamic `import("@opentelemetry/api")` for
  optional tracing that Metro's bundler tries to statically resolve despite the package's own
  webpack/vite bundler-ignore hints (Metro doesn't honor them). Installing `@opentelemetry/api` as
  a real (unused) dependency satisfies the resolution; no code change needed. Also needed but
  simply missing from the initial dependency list (not a compatibility surprise, just an omission
  caught by `expo export` refusing to run without them): `expo-asset`, `expo-font`, `react-native-web`,
  `react-dom`, `@expo/metro-runtime`.

## Critical Self-Review — dependency pinning gap
`npx expo install` (which resolves each package to the exact version Expo's own compatibility
table pairs with SDK 52) could not run — this environment's outbound proxy blocks Expo's
version-metadata API (`Host not identified` from the proxy, confirmed both via `expo-doctor` and
`expo install --fix`). `expo-asset` and `expo-font` were therefore left to `npm install`'s own
"latest" resolution rather than an SDK-52-pinned version, unlike every other Expo package in this
scaffold which was hand-pinned to its documented SDK 52 range. This is a real gap, not silently
smoothed over: re-run `npx expo install --fix` from an unrestricted network before Phase 2 to
correct these two.

## Critical Self-Review
- The `mobile/` top-level folder placement is not RACR-approved; flagged in §Executive Summary, not
  hidden.
- Screen copy is placeholder/functional, not DOC-06-compliant visual design — explicitly scoped out
  of Phase 1, consistent with the task's own "no design polish yet" instruction.
- `home_state`/`current_city` are free-text inputs in Phase 1, not the 36-state searchable dropdown
  DOC-06 specifies (no state list was located in-repo to source it from without fabricating one).
- No offline/retry/error-state handling beyond TanStack Query defaults — acceptable for Phase 1's
  "prove the wire" goal, not for ship-readiness.

## Addendum — visual design ported from scareme21-create/NewFoo (post-Phase-1)
The Founder pointed at `github.com/scareme21-create/NewFoo` twice, asking to "pick the entire
front end." Two separate visits found two very different states of that repo:

1. **First visit**: `ghar_api/app` (the linked path) is backend Python (FastAPI), not frontend.
   That repo's actual frontend (`foofoo/`) was unmodified `create-expo-app` boilerplate — no real
   screens. Only its light/dark theme tokens were worth porting (done then, unchanged now).
2. **Second visit** (this addendum): the same repo had gained a real, well-designed onboarding
   flow — sign-in, create-id (name capture), a 5-screen onboarding flow, and a "Ghar" warm
   terracotta/cream visual system (Fraunces + Mukta fonts). Still built against the same
   incompatible FastAPI backend (`/v1/onboarding`, different field names, GPS location capture,
   Cloudinary dish photos, a `/v1/analytics` endpoint) as visit 1 — none of that backend surface
   exists in foofoo-v3.

Per Founder direction ("port screens, rewire to our backend, dropping GPS/Cloudinary/analytics"),
this session replaced Phase 1's 4 plain onboarding screens with a straight visual/UX port of
NewFoo's 5-screen flow (`mobile/src/theme/index.tsx`'s Ghar theme, `mobile/src/onboarding/`'s
chip/header components, `mobile/app/(onboarding)/step-1..5.tsx`, plus `splash-2.tsx` and
`create-id.tsx`), with every submit rewired to this repo's real `POST /v1/household` via a new
`mobile/src/onboarding/toHouseholdWrite.ts` mapping layer — not the source repo's own
`toProfile.ts`, which targets a payload shape that does not exist here.

**Two required fields NewFoo's flow never asked for, added here:** `current_city` (source only
had an optional GPS-derived city; dropped GPS, so Screen 2 now asks directly) and
`cook_capability` (source never collected this at all; added to Screen 5 as the one required
question on an otherwise fully-skippable screen — flagged as a deliberate deviation from source's
"everything optional" design intent for that screen, forced by `PROFILE_REQUIRED_FIELDS`).

**Value-vocabulary mismatches resolved in `toHouseholdWrite.ts`, not silently passed through:**
`eggetarian` → `egg`, `order_in` → `order_tiffin`, fractional eat-out cadence → integer (our
`q14_eat_out_per_week` is `z.number().int()`), allergen chip tokens → `allergen_flags` bitmask
(compose.ts's frozen 7-bit model) instead of the source's own allergen-slug array. Age-range chips
map onto `household_members.conditions` (MEMBER_CONDITIONS vocab) only where a clear equivalent
exists (`0-2`→`baby_6_18m`, `60+`→`elderly_member`, etc.) — a lossy, disclosed approximation, not a
precise model.

**Dependency-pinning bug actually surfaced, not just theoretical this time:** adding
`expo-splash-screen` via plain `npm install` (same proxy-blocked-`expo install` constraint as the
earlier `expo-asset`/`expo-font` gap) resolved to v57.x — built for a much newer Expo SDK — and
broke web rendering outright (`Error: Module implementation must be a class`). Diagnosed via a
headless-browser console-log check, then fixed by hand-pinning `expo-font` (`~13.0.3`),
`expo-splash-screen` (`~0.29.13`), and `expo-asset` (`~11.0.1`) to their actual SDK 52 versions.
Re-verified working via headless-browser screenshots of splash, sign-in, and create-id after the
fix. This confirms the earlier-flagged pinning gap is a real, active risk, not a hypothetical one —
re-running `npx expo install --fix` from an unrestricted network remains the correct permanent fix.

**Not ported:** NewFoo's `final-dish-intro`/`final-dish`/`final-dish-style2`/`plan.tsx` screens
(Cloudinary dish photos, feedback/analytics calls) — out of scope per Founder direction. This
repo's existing plain `recommendations.tsx` screen is unchanged.

## Versioning & Placement
Placed under `docs/architecture/` per the P4 series (application-layer architecture, companion to
DOC-P4-00/DOC-P4-02). DRAFT until Founder reviews; STOP CONDITION per task instructions — no further
phases begin until this is reviewed.

Founder Sign-off: ___________________________     Date: _______________
