# REPO-CERT-015 — WP-8E RE Integration Layer Execution v1.0

**Status:** ACTIVE — Execution Certificate.
**Version:** v1.0
**Date:** 2026-07-15
**Placement:** docs/project-history/certificates/[ACTIVE]_REPO-CERT-015_WP-8E_RE_Integration_Layer_v1.0.md
**Attests:** [ACTIVE]_WP-8E_RE_Integration_Layer_v1.0.md
**Dependencies:** REPO-CERT-014 (WP-8D engine), REPO-CERT-011 (WP-8C), REPO-CERT-008 (WP-8B); DOC-P3-02/03/04/06, DOC-P4-00, DOC-P4-02 (DRAFT).

---

## Certification

The **Recommendation Engine integration orchestration layer** is certified **built and validated**:
onboarding orchestration, the recommendations service, the nightly scheduler, and the
persistence/caller-load Supabase adapters, all reusing the **existing WP-8D engine as the single
source of recommendation logic**, with **no recommendation logic added, and no schema, migration,
seed, validation-SQL, security, or frozen-document change, and no live DB connection.**

## Basis (directly executed this session, Deno 2.1.4)

- **New code (6 files):** `services/planning/persistence.ts`, `services/onboarding/orchestrator.ts`,
  `services/recommendations/service.ts`, `services/scheduler/nightly-plan.ts`,
  `services/adapters/supabase-stores.ts`, `_tests/re_integration.test.ts`.
- **Additive changes:** `services/re/types.ts` + `engine.ts` (surface `Slate.ranked` — the
  already-computed FinalScore, for §06.4; no scoring/ranking logic changed); `errors/api-catalogue.ts`
  (+3 frozen §21.1 codes).
- **`deno task verify`:** `deno fmt --check` PASS · `deno lint` PASS · `deno check` PASS (52 files) ·
  `deno test --allow-env functions/_tests/` → **62 passed / 0 failed** (8 foundation + 16 consent +
  28 RE core + **10 WP-8E integration**).
- **WP-8E test coverage:** onboarding orchestrates→persists→returns §06.2 handle; Jain diet forces
  jain pref; consent-gate → 403; idempotency → 409; confidence Day-0 cap + all-skipped floor;
  city-overlay bands; recommendations reuses engine + persists slate + §06.4 `dishes[].score`;
  missing slot → 404; scheduler processes all eligible users (same engine) + isolates a single
  user's failure.

## Architecture verification

- **One engine, three callers:** onboarding orchestrator, recommendations service, and nightly
  scheduler each invoke the same `RecommendationEngine`; the integration test drives all three off
  one instance. Recommendation logic lives only in `services/re/` (WP-8D) — none in WP-8E.
- **Onboarding = orchestrator:** LF-A01–A09 (its own logic) + engine invocation + persistence + §06.2
  handle; per DOC-P3-02 Domain Events the engine is the plan actor.

## Scope & limits (what is NOT certified)

Certifies the **orchestration layer + verified persistence/load adapters only.** Does NOT certify:
the RE read-port concrete adapters — in particular **`CandidateRepository`, which is BLOCKED** on the
`dish_tags`/`tags` variety-dimension mapping + ingredient-allergen join (unverified schema; not
invented); the remaining read adapters + concrete `ReStateStore` (deferred for scope); the
`/v1/onboarding` + `/v1/recommendations` HTTP endpoints (depend on the full engine wiring); and any
live-DB behaviour (adapters are type-checked only — no live Supabase). Full enumeration in the work
package §6.

## Consequence

**WP-8E orchestration layer COMPLETE and validated.** The integration architecture (one engine,
three callers, onboarding orchestration + persistence) is proven. Production runtime is gated on the
remaining concrete adapters (starting with the `CandidateRepository` dish-genome/tag mapping), the
two endpoints, and live-DB behavioural validation. Deploy discipline unchanged; DOC-P4-02 remains
DRAFT pending Founder countersignature.

## Critical Self-Review

- **Execution real?** Yes — `deno task verify` ran to completion (62/0) this session.
- **Recommendation logic duplicated / invented?** No — engine untouched (except additive `ranked`
  output); DTOs/errors are frozen-contract; the blocked adapter was deferred, not fabricated.
- **Frozen artifacts / DB touched?** No; DOC-P4-02 stays DRAFT.
- **Honest limit:** not end-to-end runnable against a live DB yet — concrete read adapters (esp.
  Candidate), endpoints, and live validation are enumerated debt.

## Versioning & Placement

v1.0, docs/project-history/certificates/ per the Placement Rule; naming per WP-5AA. Attests the WP-8E
work package.

## Founder Countersignature

Founder acceptance of WP-8E RE Integration Layer execution: _______________________ Date: ___________
