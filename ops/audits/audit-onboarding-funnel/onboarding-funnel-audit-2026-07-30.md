# Onboarding Funnel Audit — 2026-07-30

**Mode:** Report-only. No fixes applied in this round, per explicit task instruction (this
overrides `.claude/skills/audit-onboarding-funnel/SKILL.md`'s own Step 6/7 auto-fix-on-confirmation
behavior for this run only).

Spec found: none. Checked `knowledge-book/product/specs/*/product-spec.md` and
`knowledge-book/qa/specs/*/test-plan.md` (this repo has no `knowledge-book/` directory at all —
its docs live under `docs/`). No onboarding-specific product spec or QA test plan was found under
`docs/product/`, `docs/architecture/`, or `docs/project-history/` either. Gap flagged per Step 1:
a written onboarding spec would make this audit and future QA more reliable. The flow below was
discovered from code only.

## Flow discovered (ordered)

1. `mobile/app/index.tsx` — root gate: loading spinner → `session` check → redirect
2. `mobile/app/splash-2.tsx` — marketing/welcome screen (unauthenticated entry)
3. `mobile/app/(auth)/sign-in.tsx` — sign in / sign up (email + password, Supabase Auth)
4. `mobile/app/create-id.tsx` — capture display name → `POST /v1/household` (post sign-up only)
5. `mobile/app/(onboarding)/_layout.tsx` — onboarding route guard + `OnboardingProvider`
6. `mobile/app/(onboarding)/step-1.tsx` — household type + working professionals
7. `mobile/app/(onboarding)/step-2.tsx` — home state + current city
8. `mobile/app/(onboarding)/step-3.tsx` — diet + conditional follow-ups
9. `mobile/app/(onboarding)/step-4.tsx` — allergens + medical conditions
10. `mobile/app/(onboarding)/step-5.tsx` — age/cooking details → `POST /v1/household` → `router.replace("/recommendations")`
11. `mobile/app/recommendations.tsx` — first real post-onboarding screen

Each step submits its own answer slice immediately via `postHousehold()` (incremental
accumulation against `household/handler.ts`, per `OnboardingContext.tsx`'s own header comment),
rather than one final submit at the end.

## Spec vs code gaps
N/A — no spec exists to compare against (see above).

## Drop-off risks found

| Screen | Risk type | Description | Severity | Suggested fix |
|---|---|---|---|---|
| `mobile/app/index.tsx` (root gate) vs `mobile/app/(auth)/sign-in.tsx` | Broken/inconsistent resume logic | Two different, contradictory routing rules exist for the same "already has a session" state. `index.tsx` (app cold start / reopen with a persisted session) **always** redirects to `/(onboarding)/step-1` — the code's own comment says this is deliberate: *"Phase 1 always routes a signed-in user back into onboarding's first screen... Phase 1 has no 'onboarding complete' flag to branch on yet."* But `sign-in.tsx`'s explicit "Sign In" action routes straight to `/recommendations`, bypassing onboarding and `create-id` entirely. A user who signs up, needs email confirmation, then signs in without ever completing onboarding lands on `/recommendations` with no household profile at all. `recommendations.tsx` has no completeness check — it silently calls `postRecommendations()`, and per its own comment the backend "always returns a valid 200 (RE failure -> fallback plate)", so the user silently gets a generic/fallback recommendation forever with no indication their profile is incomplete, unless they notice and tap the small "Back to onboarding" link. | **HIGH** | Introduce a real "onboarding complete" flag (e.g. on `profiles`) and make both entry points (`index.tsx` cold start AND `sign-in.tsx`'s sign-in branch) branch on the same signal, instead of two independently-reasoned redirect rules. |
| Every reopen of the app by an already-onboarded user | Broken resume logic (forced restart, not persisted) | `OnboardingContext.tsx` holds answers in `useState` only — no `AsyncStorage`/persistence anywhere (confirmed: repo-wide grep for `onboarding_step`, `onboardingStep`, `resume` returns zero hits outside unrelated `AsyncStorage` usage in `logger.ts`/`supabaseClient.ts`). Combined with the routing above: a signed-in user reopening the app is sent to step-1 with a **blank** form every time — no pre-fill from the profile data already saved server-side in prior sessions, no memory of previous answers. If `household/handler.ts` is genuinely idempotent (per the code comment) this is "just" annoying re-entry, not data corruption, but it means onboarding can never actually be marked "done," and a returning user is asked to redo all 5 screens on every cold start. | **HIGH** | Persist an onboarding-step/complete flag client-side (or better, read it from the profile on load) so a returning user with a complete profile skips straight to `/recommendations`, and a returning user mid-flow resumes at their last completed step, pre-filled from already-submitted data. |
| All 6 mutation call sites (`create-id.tsx`, `step-1`..`step-5.tsx`) | Infinite loader / no timeout | `apiPost()` in `mobile/src/api/client.ts` calls raw `fetch()` with no `AbortController`/timeout of any kind. If the network stalls (bad connectivity, backend hang), `mutation.isPending` never resolves — the Continue/Finish button is stuck reading "Saving..."/"Finishing..." indefinitely, with no timeout, no cancel affordance, and no error shown (since nothing ever rejects). Not a hard dead-end on steps 2–5 (the header Back button remains tappable — it isn't gated on `mutation.isPending`), but forward progress can hang forever with zero feedback. | **HIGH** | Add a request timeout (`AbortController` + a sane ms budget, e.g. 15–20s) in `apiPost`, surface a distinct "Request timed out — check your connection" state, and gate/disable Back too, or explicitly allow it, rather than leaving the state undefined. |
| All 6 mutation call sites | Error-state ambiguity | Every screen shows the same fallback: `mutation.error instanceof ApiError ? message : "Something went wrong"`. A genuine offline/network failure (a rejected `fetch()`, not an HTTP error) is indistinguishable from a validation/server error — same generic text, no explicit "Retry" affordance distinct from re-pressing Continue (functionally works, since `mutation.isPending` resets, but there's no visual cue this is a retry). Contrast with `recommendations.tsx`, which does have an explicit "Retry" button and a clearer isError branch — the onboarding screens are less mature than the post-onboarding screen in this respect. | **MEDIUM** | Distinguish network failures from `ApiError` HTTP failures with a clearer message, and add an explicit "Retry" button matching `recommendations.tsx`'s pattern. |
| `step-1.tsx`, `step-2.tsx`, `step-3.tsx`, `step-5.tsx` | Validation trap (disabled button, no explanation) | `canContinue` gates the button on required fields, but nothing tells the user *why* Continue is disabled beyond the (mostly single-field) screen context. Step 5 is the widest case — 5 sections, but only `cookCapability` gates the button; the "Required" hint text on that one section is the only cue. A user who fills every other section and misses "Cooking Skill" gets a disabled button with no highlight pointing at the actual blocker. | **MEDIUM** | Add a shared "why is this disabled" affordance (e.g. shake/highlight the unmet required section on a Continue tap while disabled), matching the explicit inline-error pattern step-4 already uses for its "Others" fields. |
| `step-1.tsx` | One-way door by design | `showBack={false}` on step 1 is reasonable (first screen, nothing to go back to within onboarding), but combined with the no-resume finding above, any household-type selection made and then interrupted (app killed) before pressing Continue is lost with no recovery path other than starting over — acceptable today only because nothing has been submitted yet. | **LOW** | No action needed unless resume/pre-fill (see above) is built — then this stops mattering. |
| `step-4.tsx` "Others" free-text fields | Silent-failure risk, low | `toHouseholdWrite.ts`'s `allergenFlags()` silently drops any allergen value not in the frozen 7-bit `ALLERGEN_BITS` map (only "others" free text is preserved via `allergensOther`) — not a UI drop-off risk today since the chip set matches the bit map exactly, but worth noting as a latent silent-data-loss risk if the chip list and bit map ever drift independently. | **LOW** | No onboarding UX change needed; flag for whoever owns `ALLERGEN_BITS`/chip-list parity. |

## Resume logic
**Status: verified NOT SAFE / does not exist.** There is no `onboarding_step` (or equivalent)
persistence anywhere in the mobile app — repo-wide grep for `onboarding_step`, `onboardingStep`,
`resume` inside `mobile/src` and `mobile/app` returns zero relevant hits. `OnboardingContext`'s
answer bag is in-memory (`useState`) only and is reset to `INITIAL_ANSWERS` on every provider
mount. The only "resume" behavior that exists is the routing decision in `index.tsx`, which
unconditionally sends every signed-in user back to step 1 — which is itself flagged above as a
HIGH finding, both for the forced-restart UX and for its inconsistency with `sign-in.tsx`'s
separate redirect rule.

## Severity summary
- CRITICAL: 0
- HIGH: 3 (inconsistent/missing "onboarding complete" signal across two entry points; no
  persisted resume — forced restart every reopen; no network timeout on any onboarding
  API call — infinite loader risk)
- MEDIUM: 2 (error-state ambiguity; validation trap on step 5's silent gating)
- LOW: 2 (step-1 one-way-door interacts with no-resume; allergen chip/bit-map drift risk)

None of the findings above are a true hard dead-end (every screen retains a way forward or a way
back), but the HIGH items compound into a real, systemic risk: a project whose own architecture
docs (Final Evidence Closure §11) already self-rate onboarding-adjacent runtime work as "Needs
Work"/"Blocked" in several dimensions. The two entry-point/resume findings are the ones most
likely to cause real user confusion or silent data incompleteness in production; lead with those
if only one fix can be prioritized.

## Manual verification still needed
This skill read code only — it did not run the app. A manual click-through of: (a) sign-up →
required email confirmation → sign-in → landing screen, and (b) kill-app-mid-onboarding →
reopen, is recommended to confirm these code-level findings match actual runtime behavior before
considering this audit fully verified.

## Completion summary
```
## Audit completed 2026-07-30
Spec found: No (gap flagged)
Screens audited: 11 (index, splash-2, sign-in, create-id, onboarding layout, steps 1-5, recommendations)
Spec vs code gaps: N/A (no spec)
CRITICAL drop-off risks: 0 (fixed: 0 — report-only round)
HIGH risks: 3 (fixed: 0 — report-only round)
Resume logic: NOT SAFE / does not exist
```
