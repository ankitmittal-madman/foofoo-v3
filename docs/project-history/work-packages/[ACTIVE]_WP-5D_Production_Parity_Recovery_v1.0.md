# WP-5D — Production Parity Recovery v1.0

**Status:** ACTIVE — executed (analysis + read-only production introspection; STEP-6 STOP on the one canonical recovery, pending a Founder architecture decision)
**Version:** v1.0
**Date:** 2026-07-13
**Placement:** docs/project-history/work-packages/[ACTIVE]_WP-5D_Production_Parity_Recovery_v1.0.md
**Supersedes:** None
**Dependencies:** WP-5B/5C/5E/5F/5F2; production project `slsqtlygeekdppuyiiff`. Companions: WP-5D Evidence Register, Engineering Decision Log, Validation Report, Production Parity Report, REPO-CERT-004.

---

## Objective

Make the repository the complete engineering source of truth by recovering production-only engineering migrations. Parity only — no backend, no production seeds, no schema redesign, no frozen-architecture change.

## Scope

**In scope:** compare repository vs production migration history; characterize and classify every production migration absent from the repo; recover canonical migrations from production evidence; assess parity; recommend next step.

**Out of scope (per brief):** backend, production seed generation, APIs, frozen-architecture change, schema redesign, optimization, RE work. Also: modifying repository SQL beyond a Founder-approved canonical recovery (none committed this session).

## Repository state before execution

HEAD `92a717c`, clean tree. 28 migration files + 28 rollbacks + 3 seeds. Migration/rollback/seed core execution-proven by WP-5F2.

## Execution strategy

Read the production migration ledger and catalog **read-only** (never modify production); recover the exact applied SQL of any canonical missing migration from `supabase_migrations.schema_migrations`; classify each; validate rebuildability impact; document; report parity.

## Repository evidence produced

Full detail in the Evidence Register. Summary:
- Production has **31 tracked migrations**; repo has **28** files. Missing (3): `pf1_security_hardening`, `103_production_cuisines`, `103_production_ingredients` — candidate list confirmed complete.
- `pf1` exact SQL recovered verbatim (HIGH confidence).
- `103_*` are pure `INSERT` production seed data → Class B, not recovered.
- `pf1` depends on `public.rls_auto_enable()` (+ `ensure_rls` event trigger) — untracked production objects with **no migration provenance**, absent from the repo, that auto-enable RLS on every public table (a measured +13 RLS drift vs the repo build, contradicting frozen migration 019).

## Classifications (STEP 4)

- `pf1_security_hardening` → **A (canonical)** — recover; **blocked** on the `rls_auto_enable` decision.
- `103_production_cuisines` → **B (production data)** — not recovered.
- `103_production_ingredients` → **B (production data)** — not recovered.

## Corrections performed

**None to `database/`.** The one canonical recovery (`pf1`) is a STEP-6 STOP: committing it verbatim breaks self-rebuildability (dangling `rls_auto_enable`); modifying it breaks parity; adopting the RLS overlay changes frozen architecture. Its exact SQL is preserved as evidence pending the Founder decision (Decision Log D-05).

## Validation

No repository SQL changed → migration numbering, dependency chain, rollback chain, and WP-5F2-proven rebuildability are all **unaffected**. Detail in the WP-5D Validation Report.

## Risks

Recovering `pf1` incorrectly (forcing the RLS overlay into canonical schema) would silently change RLS behavior on internal audit tables — mitigated by escalating rather than deciding. Leaving `pf1` unrecovered means the repo is not yet 100% parity — mitigated by a precise, evidence-backed decision request.

## Acceptance criteria

Every production migration classified with evidence ✅; canonical vs environment-specific separated ✅; parity established and quantified ✅; single blocker isolated to a Founder decision ✅; nothing fabricated, no production modified, no frozen architecture changed ✅.

## Exit criteria

Six WP-5D documents + KNOWLEDGE Session 8 committed (docs only); STOP after the readiness answer; do not begin WP-5G.

## Critical Self-Review

- **Considered** declaring WP-5D "complete, parity achieved" by committing a recovered `pf1`. **Rejected** — honest parity requires resolving the `rls_auto_enable` overlay first; a `pf1` that can't rebuild or that diverges from production would be a false completion.
- **Limitation:** WP-5D reconciled the migration axis and the objects surfaced by `pf1`; a full byte-level schema diff is deferred to WP-5G's live certification.

## Founder Sign-off

Founder acceptance of WP-5D: _______________________ Date: ___________
