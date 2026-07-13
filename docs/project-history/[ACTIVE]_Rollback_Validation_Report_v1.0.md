# [ACTIVE]_Rollback_Validation_Report_v1.0

**Status:** ACTIVE — validation report (structural validation; live apply deferred to WP-5F)
**Version:** v1.0
**Date:** 2026-07-13
**Placement:** docs/project-history/[ACTIVE]_Rollback_Validation_Report_v1.0.md
**Supersedes:** None
**Dependencies:** [ACTIVE]_WP-5C_Rollback_Recovery_Report_v1.0; [ACTIVE]_Rollback_Evidence_Register_v1.0; [ACTIVE]_Rollback_Dependency_Graph_v1.0.

---

## Executive Summary

Validation of the 26 recovered rollbacks (001–026) by structural reasoning against the forward migrations, per WP-5C Step 6. **All checks PASS.** Validation was performed by reading each forward migration and confirming its rollback drops exactly its created objects, in an order that returns the schema to a clean pre-migration state. Rollbacks were **not** executed against a database (WP-5C is inspect/author-only); a live apply+rollback cycle is recommended as WP-5F.

## 1. Automated checks (this session)

| # | Check | Result | Evidence |
|---|---|---|---|
| 1 | Every migration 001–028 has a paired rollback | ✅ PASS | 28 migrations, 28 rollbacks; basename pairing 28/28 |
| 2 | Every rollback's `Reverses:` names an existing migration | ✅ PASS | 0 broken references |
| 3 | 019 rollback drops all real policies | ✅ PASS | 23 `DROP POLICY` = 23 `CREATE POLICY` in forward (the "24th" grep hit is a comment) |
| 4 | 019 rollback disables RLS on all enabled tables | ✅ PASS | 19 `DISABLE` = 19 `ENABLE` in forward |
| 5 | 020 rollback drops all explicit indexes | ✅ PASS | 36 `DROP INDEX` = 36 `CREATE INDEX` in forward |
| 6 | 010 rollback drops all triggers + functions + table | ✅ PASS | 4 triggers, 4 functions, 1 table = forward counts |
| 7 | New files follow canonical SQL naming | ✅ PASS | all `NNN_description_rollback.sql`, no status token/version |
| 8 | No forward migration / architecture / DB modified | ✅ PASS | only `database/rollback/` + docs added |

## 2. Mental teardown validation (per Step 6)

Applying rollbacks in reverse order (Dependency Graph §1), each returns the schema to its pre-migration state:

- `028→021` (constraint/column/table reversals) → back to post-020 state. ✔
- `020` drop 36 indexes → post-019 state. ✔
- `019` drop policies + disable RLS → post-018 state. ✔
- `018` no-op → post-017. ✔
- `017` drop partitions → parents (012) now childless and droppable. ✔
- `016→011` drop tables (reverse dep order) → post-010. ✔
- `010` drop triggers/functions/table (targets in 009/006/002 still present at this point). ✔
- `009→002` drop tables reverse dep order → only schema re_engine + extension remain. ✔
- `001` `DROP SCHEMA re_engine RESTRICT` (now empty ✔) + drop extension → pre-migration empty DB. ✔

No step drops an object another still-present migration depends on; every FK/inheritance dependency is respected by the reverse order.

## 3. Special-care reversals (025/026/027/028 + 023, 001, 017)

Confirmed each carries the required loud warning and behaves correctly on the current unseeded state (Confidence Matrix §3, Dependency Graph §3). The 025/026 array→scalar and 023 unique-restore are lossy/loud-failing on populated data **by design**, following the 027/028 precedent.

## 4. Not performed (out of scope, → WP-5F)

Live execution of the teardown against a database branch. Structural validation cannot catch a runtime-only error (e.g. an unforeseen dependent object created outside the migration sequence). WP-5F (clean-room rebuild + teardown) is recommended to upgrade this to executed proof.

## Critical Self-Review

- **Considered** running the teardown on a Supabase preview branch to prove it. **Deferred** — WP-5C's mandate is author-and-validate rollback SQL, not execute; a live teardown is a distinct, higher-blast-radius activity better scoped to its own approved WP (5F).
- **Limitation:** "PASS" here means structurally correct against the forward files, not "executed successfully against a live database."

## Versioning & Placement

`[ACTIVE]_Rollback_Validation_Report_v1.0.md` → docs/project-history/. New file.

## Founder Sign-off

Founder acceptance: _______________________ Date: ___________
