# REPO-CERT-014 — WP-8D Recommendation Engine Core Execution v1.0

**Status:** ACTIVE — Execution Certificate.
**Version:** v1.0
**Date:** 2026-07-15
**Placement:** docs/project-history/certificates/[ACTIVE]_REPO-CERT-014_WP-8D_Recommendation_Engine_Core_v1.0.md
**Attests:** [ACTIVE]_WP-8D_Recommendation_Engine_Core_v1.0.md
**Dependencies:** DOC-P3-02, DOC-P3-03 §02–16, DOC-P3-03A, DOC-P3-04, DOC-P3-06, DOC-P4-00, DOC-P4-02 (DRAFT), REPO-CERT-008/011/013.

---

## Certification

The **reusable FooFoo Recommendation Engine core** is certified **built and validated**, implementing
the frozen business logic (DOC-P3-03 §02, §06–11) as pure, caller-agnostic domain logic behind
injected ports, with **no schema, migration, seed, canonical-data, validation-SQL, security, or
frozen-document change, and no live database connection.** No recommendation logic exists anywhere
outside `supabase/functions/_shared/services/re/`.

## AD-01 reconciliation (pre-implementation gate)

Before coding, the onboarding↔first-plan boundary was re-reconciled against ACTIVE evidence. **DOC-P3-02
(CDM) Domain Events** name the **RE Engine** as the actor that generates the first plan at OB-08b
(Effect: Week Plan, Plan Slots), with onboarding as orchestrator. This reconciles the apparent
contradiction **without a DCR**; the prior STOP (REPO-CERT-012/013) was too literal about DOC-P3-06
§12/§13 (own-logic vs transitive footprint). Detail in the WP-8D work package §1. **DOC-P4-02 remains
DRAFT** — the Founder's in-session direction is recorded, but the formal AD-01 sign-off is pending
countersignature; no ratification was fabricated. WP-8D does not depend on it (the engine is identical
under every AD-01 option).

## Basis (directly executed this session, Deno 2.1.4)

- **New code (8 files) under `_shared/services/re/`:** `types.ts` (DTOs), `ports.ts` (repository/config
  ports), `constraints.ts` (LF-D02–D06), `scoring.ts` (LF-E01–E08), `variety.ts` (LF-F01–F03),
  `safety.ts` (LF-H01–H04), `resolvers.ts` (LF-A09/B01–B03), `engine.ts` (§02 orchestration:
  `generateSlate`, `generateWeekPlan`), plus `index.ts` barrel.
- **Tests (1 file):** `_tests/re_core.test.ts` — 28 tests (pure functions + 4 fake-repo engine
  integration tests).
- **`deno task verify` (fmt:check → lint → check → test):**
  - `deno fmt --check` → **PASS**
  - `deno lint` → **PASS**
  - `deno check` (incl. `services/re/index.ts`) → **PASS** (47 files)
  - `deno test --allow-env functions/_tests/` → **52 passed / 0 failed** (8 foundation + 16 consent +
    28 RE core).
- **Coverage exercised:** 6 hard constraints incl. ingredient-level allergen union; weight-ladder
  interpolation invariants (tier endpoints exact, weights sum ≈ 1.0); cohort-prior neutral fallback;
  cosine ContentMatch; PersonalHistory decay; Not-Today penalty (decay + threshold + context
  override); FinalScore assembly; bandit α/β update + bounded exploration bonus; MMR diversity;
  variety windows (fried cap + monsoon override + same-dish); safety gates (diet/allergen/jain +
  planning-role); persona Option-B fallback; engine — safe slate, unseeded-prior path, LF-D07
  popular fallback, week-plan assembly.

## Scope & limits

Certifies the **reusable engine only.** Does NOT certify any `/v1/*` endpoint, the onboarding
orchestrator, the nightly CRON, concrete Supabase repository adapters, or live-DB behavioural
validation (deferred to later WPs; consistent with the WP-8B/8C no-DB-in-tests posture). Two honest
limits: (1) **`re_cohort_class_priors` is unseeded** — cold-start CohortPrior is the documented neutral
0.50 fallback (LF-E02) until seeded (MVP limitation, WP-8D §3); (2) **DCR-8D-01** — the DOC-P3-03 §07
weight-ladder worked example is internally inconsistent, so the continuous forward-transition reading
was implemented and tested by invariant, flagged for Founder confirmation (WP-8D §4).

## Consequence

**WP-8D COMPLETE.** The reusable RE core is production-grade and validated. Downstream WPs may wire it
to `/v1/recommendations` (WP-8E), the nightly plan job (WP-8E), and the onboarding orchestrator (per
AD-01, once DOC-P4-02 is countersigned ACTIVE), plus concrete Supabase adapters + live behavioural
validation — none duplicating engine logic. Deploy discipline (Supabase CLI, numbered migrations, CI
safety gates, Founder-approved production) remains in force.

## Critical Self-Review

- **Execution real or claimed?** Real — `deno task verify` ran to completion (52/0) this session.
- **Frozen artifacts touched?** No — zero SQL/schema/security change; no frozen document modified.
- **Business logic invented?** No — every function cites its LF; the one ambiguity (§07 example) is
  DCR-8D-01, implemented by disclosed invariant, not fabricated; the priors fallback is LF-E02.
- **Reusable / no duplication?** Yes — pure logic + ports; recommendation logic lives only in
  `services/re/`.
- **Founder ratification fabricated?** No — DOC-P4-02 stays DRAFT pending countersignature.

## Versioning & Placement

v1.0, docs/project-history/certificates/ per the Placement Rule; naming per WP-5AA. Attests the WP-8D
work package.

## Founder Countersignature

Founder acceptance of WP-8D Recommendation Engine Core: _______________________ Date: ___________
