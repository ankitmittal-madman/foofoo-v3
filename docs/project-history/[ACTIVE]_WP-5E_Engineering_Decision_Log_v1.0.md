# WP-5E Engineering Decision Log v1.0

**Status:** ACTIVE — decision log
**Version:** v1.0
**Date:** 2026-07-13
**Placement:** docs/project-history/[ACTIVE]_WP-5E_Engineering_Decision_Log_v1.0.md
**Supersedes:** None
**Dependencies:** WP-5E Validation Remediation; WP-5F Clean-Room Validation Report; REPO-WP-04B v1.1; REPO-WP-04DA v1.0; migration 025.

---

| ID | Decision | Verdict | Evidence / Reasoning | Reversible? |
|---|---|---|---|---|
| WED-01 | Fix seed 101 `re_meal_classes.slot` to `text[]` arrays | MADE | Migration 025 (in-repo) makes the column `text[]` with `{breakfast,lunch,dinner,snack}` CHECK; scalar form fails on type + value | Yes (git) |
| WED-02 | Map the two `'addon'`-slot rows to `ARRAY['snack']` (not `ARRAY['addon']`, not planning_role remap) | MADE | Migration 025 USING rule `'addon'→ARRAY['snack']`; REPO-WP-02 §7.6; Batch1 MAP-DEC-003 (Snack≠addon at planning_role) | Yes |
| WED-03 | Treat the fix as RECOVERY of a lost applied fix, not new authorship | MADE | REPO-WP-04B v1.1 records all 9 rows were `ARRAY[...]`, `'addon'→ARRAY['snack']` "genuinely on main" (2026-07-09); lost in apverse-labs reconstruction | n/a |
| WED-04 | Leave `re_addon_classes` seed rows scalar | MADE | Migration 004 defines `re_addon_classes.slot text` (unconstrained, never array-converted) — scalar is correct | n/a |
| WED-05 | Correct 900 Check 1 expected 60→62 with repository-derived derivation | MADE | `grep -cE '^\s*CREATE TABLE' database/migrations/*.sql` = 62 = 60 baseline + cuisines(021) + re_dish_regional_affinity(024) | Yes |
| WED-06 | Make Check 1 self-evaluating (`pass` column) and tie the number to the migration set via comment, rather than a bare magic constant | MADE | WP-5E brief Step 4B: "verify reality, not stale documentation; avoid hardcoded historical values" | Yes |
| WED-07 | Do NOT touch 900 Check 3 / Check 5 / 901 Test 1 | MADE (excluded) | These are WP-04DA's approved corrections and depend on LIVE-DB values (33 RLS tables, 24 policies, trigger attachment) not derivable from repository files; touching them violates repository-evidence-only mandate + Step 4C | n/a |
| WED-08 | Do NOT enumerate-and-diff all 62 table names in Check 1 | DEFERRED | Larger than the named finding; count + derivation resolves VALIDATION-01 within minimal-correction scope | n/a |
| WED-09 | Record the WP-04B doc↔file inconsistency but do not expand into a broader audit | MADE | Step 4C: additional inconsistencies → STOP unless directly required; this one IS the seed-fix evidence, so recorded, not expanded | n/a |

## Critical Self-Review

- **Considered** copying WP-04DA's live figure "33 RLS tables" into Check 5 to make 900 fully current. **Rejected** — WP-5E may not rely on live/introspection values; the repository shows ~20 RLS-enabled tables (019 + 021), and reconciling 20-vs-33 needs a database WP-5E does not touch. Correctly left to WP-04DA.
- **Limitation:** WED-03's "recovery" framing rests on REPO-WP-04B's assertion; the byte-original fixed seed file is not itself in-repo. The restored array form is nonetheless independently forced by migration 025's live-applied CHECK, so it is correct regardless of the lost file's exact text.

## Founder Sign-off

Founder acceptance of the WP-5E Engineering Decision Log: _______________________ Date: ___________
