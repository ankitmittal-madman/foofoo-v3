# REPO-CERT-022 — WP-11 CandidateRepository Adapter Execution v1.0

**Status:** ACTIVE — Execution Certificate.
**Version:** v1.0
**Date:** 2026-07-17
**Placement:** docs/project-history/certificates/[ACTIVE]_REPO-CERT-022_WP-11_CandidateRepository_Adapter_v1.0.md
**Attests:** [ACTIVE]_WP-11_CandidateRepository_Adapter_v1.0.md
**Dependencies:** REPO-CERT-015 (WP-8E, left this adapter blocked), REPO-CERT-018 (WP-8F blocker), REPO-CERT-019 (WP-8FA audit, verdicts adopted), REPO-CERT-021 (WP-10, populated `main_ingredient_class`).

---

## Certification

The **`CandidateRepository` concrete Supabase adapter** (`SupabaseCandidateRepository`) is certified **built and test-verified**: both port methods (`getClassCandidates`, `getPopularFallback`) implemented, all 17 `DishCandidate` fields hydrated with a traced source or an explicitly documented deferral/proxy, and — the specific claim WP-8E left unverified — **downstream compatibility with `applyHardConstraints` and `scoring.ts` proven by a passing test that imports the real functions**, not asserted from the adapter's shape alone.

## Basis (directly executed this session, Deno 2.1.4)

- **New code:** `supabase/functions/_tests/candidate_repository.test.ts` (9 tests).
- **Additive changes:** `supabase/functions/_shared/services/adapters/supabase-stores.ts` (`SupabaseCandidateRepository` + private helpers; no existing class modified).
- **`deno task verify`:** `deno fmt --check` PASS · `deno lint` PASS · `deno check` PASS (54 files) · `deno test --allow-env functions/_tests/` → **71 passed / 0 failed** (62 pre-existing + **9 new WP-11 adapter tests**).
- **WP-11 test coverage:** full 17-field hydration against a 3-dish fixture; multi-class dish (grain+meat) collapses to `meat` per the documented DOC-P3-13 priority, not DB-return order; single-valued dish passes through unchanged; pork dish sets `hasPork`/`hasNonHalalMeat`; unknown class code returns `[]` (not an error); diet-filtered fallback (exact match, not the broadened hard-constraint rule); `classCode=""` for fallback candidates (LF-D07: no class constraint, never fabricated); **`applyHardConstraints` and `contentMatch`/`contextFit` run directly against the adapter's output with no shim.**

## Architecture verification

- **Interface compliance:** `SupabaseCandidateRepository implements CandidateRepository` — `deno check` confirms structural conformance to the frozen port.
- **No PostgREST relational embedding used** — verified via `pg_constraint` that no FK exists on `dish_ingredients.ingredient_id`, `dish_tags.tag_id`, or `re_class_dish_options.dish_id`; embedding syntax would silently fail. Flat queries + in-memory joins used instead, and this reasoning is recorded in the adapter's own code comment, not only in this certificate.
- **No recommendation logic added:** hydration + one minimal, documented tie-break rule only; `services/re/` (scoring, constraints, variety, safety, engine) untouched.

## Scope & limits (what is NOT certified)

Certifies the **`CandidateRepository` adapter and its test coverage only**. Does NOT certify: the remaining 8 read-port adapters (`CohortResolutionRepository`, `CohortPriorRepository`, `TasteVectorRepository`, `PersonalHistoryRepository`, `BanditStateRepository`, `ContextMultiplierRepository`, `NeverListRepository`, `SuppressionRepository`); the `/v1/onboarding`/`/v1/recommendations` HTTP endpoints; any live-DB behavioral validation (this adapter is type-checked + fake-tested only, no live Supabase connection made this session); or resolution of the `re_class_dish_options` content-seeding gap (WP-11 §6; tracked as FD-14, not gating this certificate).

## Consequence

**WP-11 `CandidateRepository` adapter COMPLETE and test-verified.** The WP-8E debt item this closes ("`CandidateRepository` concrete adapter — BLOCKED") is resolved. Production runtime for Wave 3 remains gated on the other read adapters, the two endpoints, live-DB validation, and — separately, as a content rather than engineering task — backfilling `re_class_dish_options` for the 50 empty/thin classes.

## Critical Self-Review

- **Execution real?** Yes — `deno task verify` ran to completion (71/0) this session, output captured in the session transcript.
- **Recommendation logic duplicated / invented?** No — the adapter hydrates and applies one documented tie-break; all scoring/filtering logic remains solely in `services/re/`.
- **Frozen artifacts / DB touched?** No — no migration, seed, schema, or live-DB change.
- **Honest limit:** the content-seeding gap this adapter surfaces (§6 of the WP) is real, disclosed, and separately tracked (FD-14) — not something this certificate's "complete" status glosses over.

## Versioning & Placement

v1.0, `docs/project-history/certificates/` per the Placement Rule; naming per WP-5AA. Attests the WP-11 work package.

## Founder Countersignature

Founder acceptance of WP-11 `CandidateRepository` adapter execution: _______________________ Date: ___________
