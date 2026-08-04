# Onboarding Orchestrator — Two-Engines Decision — 2026-07-30

Addendum to `edge-function-audit.md`'s CRITICAL finding ("`OnboardingOrchestrator` fully built but
never wired to a deployed Edge Function"). Original finding not modified, per this repo's
versioning rule — this records what was discovered while fixing it and the resulting decision.

## What was found

Fixing the CRITICAL finding meant deploying `_shared/services/onboarding/orchestrator.ts` as a
real `POST /v1/onboarding` Edge Function, which required building live-database adapters for the
`RecommendationEngine`'s 11 ports (`_shared/services/adapters/re-engine-full-adapters.ts`, ~600
lines, schema-verified against the live project).

While doing this, `docs/archive/reports/architecture/ARCHIVED_RE-DOC-12_Ghar_RE_Status_and_Roadmap_v1_0.md` was found to
already document — before this session, unrelated to this audit — that this repository contains
**two independent recommendation engines**:

1. The TypeScript engine (`_shared/services/re/*.ts`, backed by `re_engine.*` /
   `re_meal_classes` / `re_cohort_class_priors`) — the one `OnboardingOrchestrator` and the new
   adapters target. Migration `034_ghar_re_schema_and_catalogue.sql` itself calls this "the OLD
   persona/cohort/weight-ladder RE" and states it is "retired."
2. The Python `ghar_re_core`/`ghar_re_service` pair (RE-DOC-10/11) — the actual live path.
   `recommendations/compose.ts` reads `public` directly and calls this engine over HTTP; it never
   touches `re_engine.*`.

RE-DOC-12 found the legacy engine "not imported by any live edge function... reachable only from
its own three test files," and explicitly flagged that **no Founder Decision Register entry
records this retirement as a ratified decision** — it's a fact about which code executes, not a
governed choice.

This means the original CRITICAL finding's framing ("the fully-built orchestrator should be
wired up") was itself built on an incomplete picture — it didn't know the engine underneath the
orchestrator was already understood to be off the live path.

## Decision (Founder, 2026-07-30)

**Keep the new code, mark it clearly as not-live, do not wire it into the mobile app.**

- `supabase/functions/onboarding/handler.ts`, `index.ts`, and
  `_shared/services/adapters/re-engine-full-adapters.ts` now each carry a prominent header warning
  stating they implement DOC-P3-06 §06.2 against the legacy/retired engine, are not on the live
  request path, and exist as a real, tested reference implementation in case that engine is ever
  revived.
- The mobile app's actual onboarding write path remains `household/handler.ts` (unchanged by this
  decision), which now also carries the race-condition fix and timeout guards from this session's
  backend work — those are independent of which RE engine is live and remain valid fixes.
- The DPDP personalization-consent gate (`isPersonalizationGranted` check) that motivated the
  original HIGH finding is real, tested logic inside the orchestrator — but since the orchestrator
  isn't on the live path, **the live `household/handler.ts` path still has no consent-gate
  enforcement of its own**. This is now a distinct, still-open gap from the original finding and
  should be tracked separately (the mobile app's consent screen enforces the decision client-side
  per this session's mobile fixes, but there is no live server-side 403 equivalent to
  `ERR_CONSENT_REQUIRED` on `household/handler.ts` today).
- Whether to formally retire, archive, or revive the legacy TypeScript engine and its schema
  remains an open Founder decision (RE-DOC-12 §4's own framing) — this addendum does not resolve
  it, only records that today's fix did not require resolving it.
