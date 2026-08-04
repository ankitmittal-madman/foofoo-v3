# STATUS

ARCHIVED

## Reason

Implementation completed.

This document is retained for historical reference only.

It must not be used as the primary implementation guide.

Refer to the active documentation for the current source of truth.

---

# Edge Function Error Boundaries Audit

Report-only run. No fixes applied.

**Date:** 2026-07-30
**Repo state:** branch `claude/foofoo-skills-dotfiles-e93096`, commit `e7bb584`
**Platform detected:** Supabase Edge Functions (`supabase/functions/`)

## Error standard used as baseline

Found and used, in order:
- `docs/architecture/[ACTIVE]_DOC-P3-06_API_Contract_Specification_v1.2.md` — Section 07 (Error
  Model), Section 05.1 (Auth/Authz Failure Matrix), Section 18.4 (Timeout/retry philosophy),
  Section 21 (API Error Catalogue).
- Actual code implementation of that standard: `supabase/functions/_shared/errors/app-error.ts`,
  `catalogue.ts` (foundation codes), `api-catalogue.ts` (contract-frozen client-facing codes),
  `middleware/error-boundary.ts` (catch-all → generic 500, never leaks stack/DB detail),
  `api/response.ts` (`jsonContract` envelope), `api/handler.ts` (`defineHandler` pipeline:
  context → error-boundary → logging → endpoint middleware).

Envelope: `{ error: { code, message, retriable, trace_id, context? } }`. Doc and code agree.

## Functions found (3 deployed; 1 documented-but-not-deployed)

| Function dir | Entry | Handler |
|---|---|---|
| `supabase/functions/consent/` | `index.ts` | `handler.ts` → `makeConsentHandler` |
| `supabase/functions/household/` | `index.ts` | `handler.ts` → `makeHouseholdHandler` |
| `supabase/functions/recommendations/` | `index.ts` | `handler.ts` → `makeRecommendationsHandler` |
| *(none — see Finding 1)* | — | `_shared/services/onboarding/orchestrator.ts` (`OnboardingOrchestrator`) |

## Audit matrix

| Function | Auth check | DB errors caught | External API fallback | Empty/null handled | Timeout handled | Standard format | Missing coverage |
|---|---|---|---|---|---|---|---|
| **consent** | Yes — `authenticate()` middleware (index.ts) + `requireOwnership` in handler before any write (JWT `user_id` == `profile_id`) | Yes, well — `consent-repository.ts` wraps the insert, logs `pg_code` only (no PII), throws a clean `AppError(INTERNAL)` — the one function that does this explicitly rather than relying solely on the catch-all boundary | N/A — no external API | Partial — malformed JSON body → 400; unknown `consent_type` → 422 `ERR_CONSENT_TYPE_INVALID`; but nothing distinguishes "no rows returned from insert" (always at least 1 due to `.min(1)` validation, so effectively fine) | No — no timeout wraps the Supabase insert call; relies entirely on the platform's function execution ceiling | Yes | None significant |
| **household** | Yes — same pattern (`authenticate()` + `requireOwnership` before any store.ts call) | **No** — every `store.ts` function does `if (error) throw error;` with the raw Postgres error object, relying on the generic error-boundary catch-all (which does convert it to a safe `AppError(INTERNAL)` before it reaches the client, but skips the "log `pg_code`, throw typed error" step `consent-repository.ts` uses) | N/A — no external API | Good — missing-profile-before-members case is explicitly caught → 422 `ERR_HOUSEHOLD_INCOMPLETE`; unknown `question_key` / out-of-vocabulary `answer_value` → 422 `ERR_HOUSEHOLD_FIELD_INVALID` | No — same gap as consent; also no guard against the classic profile-creation **race**: `profileExists()` then `createProfileRow()` are two separate round-trips with no lock/upsert, so two concurrent onboarding calls for the same household could both pass the `!exists` check and both attempt `INSERT INTO profiles`, producing a raw unique-violation on the second one, surfacing only as a generic 500 instead of a documented state | Yes | See Finding 1/2 below — this function is standing in for the documented `/v1/onboarding` contract endpoint but does not implement its consent gate or idempotency rule |
| **recommendations** | Yes — same pattern, checked before `loadHouseholdRaw` runs | Partial — `loadHouseholdRaw`/`loadLatestContext` (compose.ts) do bare `if (error) throw error` (same gap as household); `events.ts`'s `recordRecommendationEvent` is explicitly **best-effort** (wrapped in try/catch, logs a warning, never fails the request) — correctly reasoned as "history-write failure must not break a successful recommendation" | **Excellent** — `re-client.ts` distinguishes timeout (abort, never retried) vs. network error (retried once) vs. non-2xx HTTP vs. non-JSON body, all four routed to `buildFallbackResponse()` and still returned as a valid 200 (matches DOC-P3-06 §07 fallback table and RE-DOC-01 §05 exactly) | Excellent — RE returning `warnings[]` (e.g. <7 eligible dishes) is a distinct `"partial"` outcome, never conflated with error; a response that fails the outgoing/incoming Ajv contract check is also caught (`bad_body`) and downgraded to a fallback plate rather than passed through or 500'd | Explicit and correct for the **external** call only — `RE_TIMEOUT_MS = 2500` (matches contract's "server-fetched, 2.5s" budget) via `AbortController`. **No timeout on the three internal Supabase reads** in `loadHouseholdRaw`/`loadLatestContext` — if the DB itself hangs, the RE-side 2.5s budget never engages and the request can run past the documented <800ms Edge-Function budget (Section 18.2) with only the platform's own hard ceiling as a backstop | Yes | The one internal-DB-hang gap noted above |

## Findings, by severity

**CRITICAL — Finding 1: `/v1/onboarding` (DOC-P3-06 §06.2) is documented and has a fully-built
orchestrator, but is never wired to a deployed Edge Function.**
`supabase/functions/_shared/services/onboarding/orchestrator.ts` implements the complete,
correctly-error-handled `OnboardingOrchestrator.completeOnboarding()` — consent gate
(`ERR_CONSENT_REQUIRED`), idempotency (`ERR_ONBOARDING_ALREADY_COMPLETE` → 409), persona/cohort
resolution, and RE engine invocation for the first week plan. `grep -rl "OnboardingOrchestrator"
supabase/` shows it is referenced **nowhere else** outside its own file (and presumably its unit
test) — there is no `supabase/functions/onboarding/index.ts`. The only actual onboarding-adjacent
write path deployed today is `household/`, which is a different, simpler contract (raw per-screen
`household_answers`/`profiles` upserts) that implements **none** of orchestrator's documented
rules:
- No personalization-consent gate before accepting onboarding writes (DOC-09 §03 / §06.1's stated
  hard dependency is not enforced anywhere in the deployed path).
- No 409 idempotency on a re-submitted, already-complete household (`profiles.onboarding_completed`
  isn't even a concept `household/store.ts` reads or writes).
- No first-week-plan generation — `/v1/recommendations` is a separate on-demand call, so nothing
  currently reproduces LF-A09/first_week_plan from the documented `/v1/onboarding` response.

This is either (a) an intentional MVP simplification that the API contract doc has not been
updated to reflect, or (b) an orphaned implementation that should be wired up. Either way it's a
real drift between documented behavior and what's deployed — flagged for a Founder decision, not
silently resolved here.

**HIGH — Finding 2: the personalization-consent hard dependency is unenforced end-to-end.**
Consequence of Finding 1: since `household/` never checks consent, and (per the API-contract audit
below) the mobile client never calls `/v1/consent` at all, a user can currently complete onboarding
without ever granting or being asked about personalization consent — the DPDP rule in DOC-09 §03 /
DOC-P3-06 §06.1 ("personalization consent must be granted before any onboarding data collection")
has no enforcement point anywhere in the live request path.

**MEDIUM — Finding 3: no timeout guard on internal Supabase calls in any of the 3 functions.**
Every DB read/write in `consent`, `household`, and `recommendations` is an un-timed `await`. The
external RE call in `recommendations` is the only place with an explicit `AbortController` +
timeout. A slow/hanging Postgres connection has no function-level backstop short of the platform's
own hard execution ceiling, which conflicts with the documented per-endpoint latency budgets
(Section 18.2: `<200ms/step` onboarding, `<800ms` recommendations Edge Function execution).

**MEDIUM — Finding 4: profile-creation race in `household/store.ts`.**
`profileExists()` → (gap) → `createProfile()` is check-then-act across two round-trips with no
transaction, advisory lock, or `ON CONFLICT DO NOTHING`. Two concurrent calls for the same
household during onboarding (plausible with a flaky network causing a client retry) can both pass
the existence check and race on the `profiles` INSERT; the loser gets a raw unique-violation
surfaced only as a generic 500, not a documented, actionable error.

**LOW — Finding 5: inconsistent DB-error handling style.**
`consent-repository.ts` deliberately logs `error.code` and throws a typed `AppError(INTERNAL)`
before propagating. `household/store.ts` and `recommendations/compose.ts` both just do
`if (error) throw error`, relying entirely on the generic error-boundary catch-all to convert it
safely. The end client-facing behavior is equivalent (both end up as a generic 500 with no leaked
detail), but the inconsistency means a future engineer copying the "obvious" pattern from
household/recommendations won't get the `pg_code`-only structured log line consent's path gets —
a debuggability gap, not a correctness one.

## Summary

```
Functions audited: 3 deployed (consent, household, recommendations)
                    + 1 documented-contract endpoint with no deployed function (onboarding)
Functions with real gaps found: 3 of 3 deployed, plus the missing onboarding deployment
CRITICAL: 1 (Finding 1)
HIGH: 1 (Finding 2)
MEDIUM: 2 (Findings 3, 4)
LOW: 1 (Finding 5)
Functions fixed: 0 — report-only run, no fixes applied per instruction
```

No code was changed as part of this audit.
