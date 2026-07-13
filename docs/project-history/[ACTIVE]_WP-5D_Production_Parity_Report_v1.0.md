# WP-5D Production Parity Report v1.0

**Status:** ACTIVE — parity report
**Version:** v1.0
**Date:** 2026-07-13
**Placement:** docs/project-history/[ACTIVE]_WP-5D_Production_Parity_Report_v1.0.md
**Supersedes:** None
**Dependencies:** WP-5D Evidence Register, Decision Log, Validation Report.

---

## 1. Repository vs Production — migration axis

| Category | Count | Detail |
|---|---|---|
| Production tracked migrations | 31 | ledger of `slsqtlygeekdppuyiiff` |
| Present in repo (content) | 28 | 001–028 (027/028 with added ordinals) |
| Missing — canonical (Class A) | 1 | `pf1_security_hardening` |
| Missing — production data (Class B) | 2 | `103_production_cuisines`, `103_production_ingredients` |
| Untracked production objects (no migration) | 2 | `rls_auto_enable()` + `ensure_rls` event trigger |
| Naming divergences | 2 | 027/028 repo ordinals vs bare ledger names |

## 2. Parity percentage

**Canonical engineering migration parity: 28 / 29 = 96.6%.**
(Denominator = the 28 present canonical migrations + the 1 canonical missing migration `pf1`. The two Class-B `103_*` seed-data migrations are environment-specific and correctly excluded from the canonical denominator per the brief.)

**Not 100%.** The single canonical gap (`pf1`) is fully evidenced (exact SQL in hand) but **blocked** on one Founder architecture decision (the status of the `rls_auto_enable`/`ensure_rls` overlay), not on missing information.

## 3. Remaining differences (exhaustive)

1. **`pf1_security_hardening` not in repo** — canonical; recovery blocked (Decision Log D-03/D-05).
2. **`rls_auto_enable()` + `ensure_rls`** — untracked production objects; auto-enable RLS on every public table; **cause a measured +13 RLS-enabled drift** (prod 33 vs repo 20), contradicting frozen migration 019 for the 7 internal audit tables. Canonical status undecided.
3. **`103_production_cuisines` / `103_production_ingredients`** — production seed data; intentionally not in the canonical repo (repo uses illustrative seeds 100–102 under IDR-001). A deliberate, documented environment difference, not an engineering-parity defect.
4. **027/028 filename ordinals** — repo adds `027_`/`028_`; production ledger names are bare. Cosmetic; renaming needs Founder authorization (Naming Standard §6).

## 4. What matches exactly

Base tables (62 = 62), policies (24 = 24), migrations 001–028 content, all 5 canonical `fn_*` functions, and (per WP-5F2) the full build/seed/teardown behavior.

## 5. Is parity 100%?

**No.** Engineering parity is **96.6%** on the canonical migration axis, with the remaining 3.4% (the `pf1` security-hardening migration) blocked behind one architecture decision about the `rls_auto_enable` overlay. Data-layer differences (`103_*`) are intentional and out of canonical scope.

## Critical Self-Review

- **Considered** reporting 100% by excluding `pf1` as "environment-specific". **Rejected** — `pf1` is a genuine engineering/security migration that belongs in the canonical repo; calling it non-canonical to inflate parity would be dishonest.
- **Limitation:** percentage is migration-axis; a full object-level parity (indexes/constraints byte-diff) is a WP-5G activity.

## Founder Sign-off

Founder acceptance of the WP-5D Production Parity Report: _______________________ Date: ___________
