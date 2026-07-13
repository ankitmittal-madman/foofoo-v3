# WP-5E Evidence Register v1.0

**Status:** ACTIVE — evidence register
**Version:** v1.0
**Date:** 2026-07-13
**Placement:** docs/project-history/[ACTIVE]_WP-5E_Evidence_Register_v1.0.md
**Supersedes:** None
**Dependencies:** WP-5E Validation Remediation; WP-5E Decision Log & Validation Report.

---

Every correction traces to explicit repository evidence. No live database was queried; all evidence is in-repo (or a prior in-repo record of a live observation).

## 1. SEED-01 evidence

| # | Evidence | Location | What it establishes |
|---|---|---|---|
| E-01 | `slot` is `text[]`, CHECK `slot <@ ARRAY['breakfast','lunch','dinner','snack'] AND cardinality(slot) >= 1` | `database/migrations/025_combo_component_type_and_slot_array.sql:39-45` | Target column type + allowed values |
| E-02 | `USING (CASE WHEN slot = 'addon' THEN ARRAY['snack'] ELSE ARRAY[slot] END)` | `025:41` | Legacy `'addon'` → `ARRAY['snack']` mapping rule |
| E-03 | "All 9 `re_meal_classes` rows now `ARRAY[...]`; `'addon'` → `ARRAY['snack']` confirmed correct" | `docs/project-history/work-packages/[ACTIVE]_REPO-WP-04B_Seed_Loading_v1.1.md:25` | The fix previously existed and was verified on the old main |
| E-04 | Statement inventory: `re_meal_classes` = 9 rows, "The WP-4A-fixed statement" | `REPO-WP-04B_..._v1.1.md:47` | The fix targeted exactly these 9 rows |
| E-05 | "legacy `'addon'` maps to `ARRAY['snack']`"; "ADDON row with `['snack']` inserted cleanly … legacy `'addon'` rejected" | `REPO-WP-02_Schema_Baseline_Establishment_v1.0.md:113-114` | Behavioral confirmation of the array form / rejection of scalar |
| E-06 | "Do not map Snack → `addon`; `addon` means a planning role, not a time-of-day slot" | Batch1 Mapping Package MAP-DEC-003 | `ARRAY['snack']` correct; must not touch planning_role |
| E-07 | Pre-fix scalar rows present on current main (the regression) | `database/seeds/101_...sql` re_meal_classes INSERT (pre-edit) | SEED-01 was still live before this WP |
| E-08 | `re_addon_classes.slot text NOT NULL` (unconstrained) | `database/migrations/004_reference_tier2.sql:36-40` | Its seed rows correctly stay scalar (not changed) |

## 2. VALIDATION-01 evidence

| # | Evidence | Location | What it establishes |
|---|---|---|---|
| E-09 | 62 `CREATE TABLE` statements across migrations | `grep -cE '^\s*CREATE TABLE' database/migrations/*.sql` = 62 | Repository-derived true base-table count |
| E-10 | `CREATE TABLE public.cuisines` | `021_cuisines_reference.sql:26` | +1 over the 60 baseline |
| E-11 | `CREATE TABLE re_engine.re_dish_regional_affinity` | `024_re_dish_regional_affinity.sql:27` | +1 over the 60 baseline |
| E-12 | "DOC-P3-04 §02 states 60 tables total" (the stale source) | `900_structural_validation.sql:11` (pre-edit) | Origin of the outdated 60 |
| E-13 | No migration contains `DROP TABLE`/`RENAME TO` | `grep -niE 'DROP TABLE|RENAME TO' database/migrations/*.sql` = none | 62 is a pure sum of CREATEs, nothing removed |

## 3. Scope-exclusion evidence (why Check 3/5, 901 left alone)

| # | Evidence | Location | What it establishes |
|---|---|---|---|
| E-14 | WP-04DA owns Check 3/Check 5/901 Test 1 corrections, derived from LIVE introspection (5 fns, 4 triggers, 33 RLS tables, 24 policies, diet_type='vegan') | `REPO-WP-04DA_..._v1.0.md:16-24, 50-55` | Those fixes need a database; out of a repo-evidence-only package |
| E-15 | WP-04DA status: DESIGNED, awaiting approval; no execution certificate | `REPO-WP-04DA_..._v1.0.md:6`; Recovery Backlog RB-09 | Those corrections are unexecuted and separately gated |

## Critical Self-Review

- **Considered** citing live-DB introspection to strengthen E-09. **Rejected** — WP-5E is repository-authoritative; the `grep` over checked-in migration files is stronger and reproducible without a database.
- **Limitation:** E-03/E-04 are a prior *record* of a live observation, not the byte-original fixed file. E-01/E-02 (the live-applied migration 025 CHECK) independently force the same array form, so the correction stands on in-repo DDL alone.

## Founder Sign-off

Founder acceptance of the WP-5E Evidence Register: _______________________ Date: ___________
