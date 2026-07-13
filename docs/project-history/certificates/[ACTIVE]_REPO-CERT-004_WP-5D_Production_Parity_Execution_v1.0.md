# REPO-CERT-004 — WP-5D Production Parity Execution Certificate v1.0

**Status:** ACTIVE — execution certificate
**Version:** v1.0
**Date:** 2026-07-13
**Placement:** docs/project-history/certificates/[ACTIVE]_REPO-CERT-004_WP-5D_Production_Parity_Execution_v1.0.md
**Supersedes:** None
**Dependencies:** WP-5D Work Package, Evidence Register, Engineering Decision Log, Validation Report, Production Parity Report.

---

## 1. Actual execution

On 2026-07-13, WP-5D compared the repository against the **production** Supabase project `slsqtlygeekdppuyiiff` using **read-only** queries only:
- `list_migrations` (ledger diff) — 31 tracked migrations vs 28 repo files.
- `supabase_migrations.schema_migrations.statements` — recovered exact SQL of `pf1_security_hardening`; characterized `103_*` as pure INSERT seed data.
- catalog introspection (`pg_proc`, `pg_event_trigger`, `pg_tables`, `pg_policies`, `information_schema`) — identified the untracked `rls_auto_enable()`/`ensure_rls` objects and measured the +13 RLS drift.

**No production object was modified. No repository `database/` file was modified. No migration was authored or committed.**

## 2. Files created

- `docs/project-history/work-packages/[ACTIVE]_WP-5D_Production_Parity_Recovery_v1.0.md`
- `docs/project-history/[ACTIVE]_WP-5D_Evidence_Register_v1.0.md`
- `docs/project-history/[ACTIVE]_WP-5D_Engineering_Decision_Log_v1.0.md`
- `docs/project-history/[ACTIVE]_WP-5D_Validation_Report_v1.0.md`
- `docs/project-history/[ACTIVE]_WP-5D_Production_Parity_Report_v1.0.md`
- `docs/project-history/certificates/[ACTIVE]_REPO-CERT-004_WP-5D_Production_Parity_Execution_v1.0.md` (this file)

## 3. Files modified

- `KNOWLEDGE.html` — Session 8 appended (markers preserved).
- **No `database/` file modified.**

## 4. Findings

- 3 production migrations absent from repo: `pf1_security_hardening` (Class A canonical), `103_production_cuisines` + `103_production_ingredients` (Class B production seed data).
- `pf1` exact SQL recovered as evidence (HIGH confidence); **commit blocked** by a dangling dependency on the untracked `rls_auto_enable()`/`ensure_rls` objects, whose canonical status conflicts with frozen migration 019 and is a Founder decision.
- Measured drift: production RLS-enabled public tables = 33 vs repo build 20 (+13 from `ensure_rls`), explaining WP-04DA's "33".
- Confirmed WP-5F2's SEC-901T5 defense-in-depth gap is exactly what `pf1` Finding 2 fixes.

## 5. Validation performed

No repo SQL changed → numbering/dependency/rollback/rebuildability all preserved (WP-5F2 baseline intact). `pf1`-as-verbatim would fail a repo-only clean-room on the `rls_auto_enable` line (deterministic; not committed).

## 6. Git commit

Commit `<see git log — WP-5D documentation commit>` (parent `92a717c`). Documentation only: 6 new `docs/` files + `KNOWLEDGE.html`. No `database/` change (verified via `git diff --cached`).

## 7. Deviations

- STEP 5/6 canonical recovery of `pf1` was **not committed** — a deliberate STEP-6 STOP pending the Founder's `rls_auto_enable` decision (committing verbatim breaks rebuildability; modifying breaks parity; adopting the overlay changes frozen architecture). This is the honest outcome, not an omission.

## 8. Confidence

**HIGH** — migration diff is exhaustive and verified; `pf1` text is verbatim from the ledger; the drift is directly measured; the blocker is a well-characterized architecture decision, not an information gap.

## 9. Repository state after execution

Repository SQL unchanged; production untouched. Canonical migration parity **96.6% (28/29)** — one canonical migration (`pf1`) pending a Founder decision. Repository is **not yet** the complete engineering source of truth.

## Critical Self-Review

- **Considered** titling this an "execution certificate" despite committing no SQL. **Kept, reframed** — it certifies the read-only production-parity execution and evidence recovery, and explicitly records that no canonical migration was committed and why.
- **Limitation:** attests to migration-axis parity + surfaced objects; full byte-level schema parity is WP-5G.

## Founder Sign-off

Founder acceptance of the WP-5D Execution Certificate: _______________________ Date: ___________
