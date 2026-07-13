# WP-5F2 Validation Report v1.0

**Status:** ACTIVE — execution-based validation report
**Version:** v1.0
**Date:** 2026-07-13
**Placement:** docs/project-history/[ACTIVE]_WP-5F2_Validation_Report_v1.0.md
**Supersedes:** None
**Dependencies:** WP-5F2 Execution Report; WP-5F Clean-Room Validation Report; WP-5E Validation Report.

---

## 1. Regression Check vs WP-5F / WP-5E (STEP 7)

| Prior conclusion | Source | Execution verdict |
|---|---|---|
| Migrations 001–028 contiguous & applicable | WP-5F §2 (simulation) | ✅ **CONFIRMED** — 28/28 applied, in order |
| 62 base tables | WP-5F §2 / WP-5E VALIDATION-01 | ✅ **CONFIRMED** — counted live = 62 |
| 28/28 rollbacks reverse to empty | WP-5F §4 (simulation) | ✅ **CONFIRMED** — teardown to 0 tables, no re_engine |
| Loud-fail rollback on seeded data | WP-5C Confidence Matrix | ✅ **CONFIRMED** — 027/028 fail loudly |
| SEED-01 fixed (seed 101 slot text[]) | WP-5E | ✅ **CONFIRMED** — seed 101 loads; slots `{…}` |
| VALIDATION-01 fixed (Check 1 = 62) | WP-5E | ✅ **CONFIRMED** — Check 1 pass |
| Numeric weight ladder sums exactly 1.0 | AGR-006 / mig 028 | ✅ **CONFIRMED** — 904 shows 1.00 ×5 |
| Trigger derivation correct | WP-5F | ✅ **CONFIRMED** — 901 Tests 1–4 |
| SEC-901T5 (authenticated UPDATE) unresolved | WP-5F risk / WP-04DC | ✅ **RESOLVED** — UPDATE 0 rows: RLS safe; Test 5 is test-design defect; GRANT gap real (WP-5D) |
| GRANT-level gap (authenticated holds col UPDATE) | WP-04DA "Sixth Finding" (live) | ✅ **CONFIRMED** in clean room |
| 901 Test 1 expects `veg` (should be `vegan`) | WP-04DA #3 | ✅ **CONFIRMED** stale — trigger derives `vegan` |
| 900 Check 3 counts fn by name (5 not 4) | WP-04DA #1 | ✅ **CONFIRMED** — 5 fns / 4 triggers |
| 900 Check 5 expects 19 | WP-04DA #5 (live 33) | ⚠️ **REFINED** — clean-room = 20 (19 + cuisines); "19" stale regardless |
| 900 Check 2 "consistent" | WP-5F §6 (read-only) | ❌ **CORRECTED** — Check 2 is vacuous (VAL2-01); read-only review over-read it |

**No prior engineering conclusion about the migration/rollback/seed layers was rejected; all were confirmed.** One read-only validation observation (Check 2 "consistent") was corrected by execution.

## 2. New findings surfaced by execution

| ID | Finding | Severity | Owner |
|---|---|---|---|
| VAL2-01 | 900 Check 2 is vacuous — `conrelid::regclass::text` is unqualified in search_path, so the `IN ('public.…')` filter returns 0 rows; the check verifies nothing and does not error | MEDIUM (false assurance) | validation-script fix (WP-04DA / WP-5E-follow) |
| VAL2-02 | 900 Check 5 expects 19; actual 20 (cuisines from mig 021 not counted) | LOW | same |
| VAL2-03 | 900 Check 3 (fn-by-name) and 901 Test 1 (`veg` vs `vegan`) stale — already WP-04DA-owned, now execution-confirmed | LOW | WP-04DA |
| SEC-901T5-R | GRANT-level gap confirmed real (defense-in-depth); RLS currently protects data (0 rows) | MEDIUM | WP-5D (pf1_security_hardening) |

These are **validation-script** and **production-parity** items, not schema defects. WP-5F2 reports them; it does not fix them (out of scope).

## 3. Repository Health — Execution-Based (STEP 8)

| Layer | Rating | Execution evidence |
|---|---|---|
| Migration Health | 🟢 GREEN | 28/28 apply clean, in order, no warnings; 62 tables + 6 partitions |
| Rollback Health | 🟢 GREEN | 28/28 reverse to empty; loud-fail-on-seeded works as designed |
| Seed Health | 🟢 GREEN | 100/101/102 load; SEED-01 fix live-verified; triggers derive correctly (illustrative volume gap is IDR-001, not a defect) |
| Validation Health | 🟡 YELLOW | schema-under-test is sound; but Check 2 vacuous, Check 3/5 stale, 901 Test 5 test-design defect → the validation *scripts* need the WP-04DA corrections |
| Execution Health | 🟢 GREEN | build+seed+teardown all execute cleanly; the one security-relevant item is data-safe via RLS, GRANT gap deferred to WP-5D |
| **Repository Health** | 🟡 **YELLOW (improved)** | core layers execution-GREEN; YELLOW drivers: validation-script staleness (WP-04DA), production parity incl. confirmed-needed pf1_security_hardening (WP-5D), illustrative seed volume (IDR-001) |

Movement since WP-5E: seed & integrity now **execution-proven GREEN** (not just simulated); SEC-901T5 moved from "unknown/open" to "resolved (data-safe) + defense-in-depth item routed to WP-5D".

## 4. Why not GREEN overall

Three honest blockers remain, none in the migration/rollback/seed core: (a) validation scripts carry stale/vacuous checks (WP-04DA); (b) production parity — the applied-but-missing `pf1_security_hardening` (now execution-justified) plus the two `103_production_*` seeds (WP-5D); (c) illustrative-only seed volume (IDR-001). GREEN certification (WP-5G) should follow WP-5D and the validation-script cleanup.

## Critical Self-Review

- **Considered** downgrading Validation Health to RED because Test 5 "failed". **Rejected** — the schema and data are safe (RLS held, 0 rows); the failure is in the *test's* expectation, not the system. YELLOW (scripts need cleanup) is the honest rating.
- **Limitation:** health for privilege/RLS layers is as faithful as the compatibility bootstrap; the SEC-901T5 direction is nonetheless certain (converges with live WP-04DA).

## Founder Sign-off

Founder acceptance of the WP-5F2 Validation Report: _______________________ Date: ___________
