# [ACTIVE]_SER-001_re_cohorts_city_tier_v1.0 — Schema Evolution Request

**Status:** ACTIVE — APPROVED (Founder decision, 2026-07-14, GAP-002 = Option A).
**Version:** v1.0
**Date:** 2026-07-14
**Placement:** docs/governance/[ACTIVE]_SER-001_re_cohorts_city_tier_v1.0.md
**Type:** Schema Evolution Request (first governed SER post-Architecture-Freeze).
**Author:** Principal Data / RE Architect (WP-6RE-DEC).
**Implements in:** `database/migrations/030_re_cohorts_city_tier.sql` (+ rollback).

---

## 1. Problem

The frozen `re_engine.re_cohorts` table declares `UNIQUE (persona_id, state_code, diet_mode)` (`migration 004`). The canonical cohort source `Cohort_Matrix_v3` (`Indian_Meal_Cohort_Persona_DB_v3.xlsx`) carries **2,952 cohort rows** that vary across **persona × state × city_tier**. Because `diet_mode`/`nonveg_mode` is **persona-determined** (constant per persona), the frozen unique key collapses the two city tiers of each (persona, state) pair to a single key — admitting at most **1,476** rows. This makes **Seed Gate S-11 (target 2,952) unsatisfiable** against the frozen schema and, transitively, blocks S-12 (`re_weekly_class_plans`, 20,664) and S-13 (`re_household_addon_plans`, 7,992). This is the GAP-002 conflict (`Batch1_Resolution_Package` RES-004), confirmed OPEN by the WP-6RE audit.

## 2. Evidence (all re-derived from live repository this session)

- `Cohort_Matrix_v3` = **2,952 rows** = **1,476** distinct `(persona_id, state_id)` × **2** `city_tier_code` values (`T1`=1,476, `T2`=1,476). *[direct workbook introspection]*
- For all 1,476 `(persona, state)` pairs, the T1/T2 rows **share every persona/diet field** (`persona_id, nonveg_mode, main_cohort_id, sub_cohort_id, household_stage, lifecycle_health, cook_dependency, time_pressure`) — **0 exceptions**. → they differ **only** by city tier. *[STEP-1A proof, WP-6RE-DEC]*
- `nonveg_mode` is persona-determined: distinct `(persona, nonveg_mode)` = **41** → distinct `(persona, state, diet_mode)` = **1,476**. *[verified]*
- No existing `re_cohorts` column encodes tier (`{cohort_id uuid, persona_id, state_code, diet_mode, prior_weight}`). *[migration 004]*
- `Weekly_Class_Plan_v3` = **20,664 = 2,952 × 7** (exactly 7.00 days per distinct source cohort_id) → weekly plans are **tier-specific**; S-12 is only satisfiable if cohorts are the 2,952 tier-distinct set. *[STEP-5 math]*
- Frozen RE read path (`DOC-P3-03 LF-B02`, "21 class assignments" = 7 days × 3 primary slots) is unaffected — it reads per (cohort, day); adding a discriminator to the cohort identity does not change the read shape.

## 3. Architecture Impact

Add `city_tier` to `re_engine.re_cohorts` and evolve the uniqueness key to `(persona_id, state_code, diet_mode, city_tier)`. Scope is **one table**; no other table's columns change. `re_weekly_class_plans` and `re_household_addon_plans` already reference cohorts by `cohort_id` (FK), so they are unaffected structurally — they simply now resolve to tier-distinct cohort rows. No RE algorithm, API contract, or security policy changes (`re_engine` remains service-role-only). DOC-P3-04 §03.27 is evolved by this SER (recorded as an architecture-evolution note, not a rewrite of the frozen ERD).

## 4. Backward Compatibility

- `city_tier` is added **nullable** with `CHECK (city_tier IN ('T1','T2'))` (NULL passes CHECK), so the two pre-existing illustrative `re_cohorts` rows (`seed 102`) are **preserved** unchanged (city_tier = NULL) — no data loss.
- The new composite `UNIQUE` is a **superset** of the old key columns; it never rejects a row the old key would have accepted once `city_tier` is populated distinctly. NULL city_tier rows remain distinct under Postgres NULL-in-UNIQUE semantics.
- Deterministic and idempotent: the ALTER is guarded so re-application is a no-op.

## 5. Migration Strategy

Forward migration `030_re_cohorts_city_tier.sql`: `ADD COLUMN city_tier text` + `CHECK`, `DROP CONSTRAINT re_cohorts_persona_id_state_code_diet_mode_key`, `ADD CONSTRAINT re_cohorts_persona_state_diet_tier_key UNIQUE (persona_id, state_code, diet_mode, city_tier)`. Structural band (next sequential after 029). No existing migration edited.

## 6. Rollback Strategy

`030_re_cohorts_city_tier_rollback.sql`: drop the composite unique, restore the original `UNIQUE (persona_id, state_code, diet_mode)`, drop the CHECK, drop the column. Note: rollback must run **after** the RE cohort seeds (113+) are rolled back, since restoring the 3-column unique would otherwise conflict with tier-distinct rows — standard reverse-order teardown (documented in the rollback header).

## 7. Recommendation

**Approve.** `city_tier` is the **minimal** (single column), **correct** (proven the only differentiator), **non-redundant** (no existing column holds it), and **future-safe** (tier is a stable, low-cardinality discriminator; enables tier-aware planning without further schema change) resolution. The alternatives — redefining `diet_mode` to carry tier (semantically wrong) or revising S-11 to 1,476 (loses the tier signal that S-12's 20,664 plans depend on) — are inferior and evidence-contradicted.

## 8. Founder Decision

**APPROVED — Option A** (Founder, 2026-07-14): "The Recommendation Engine SHALL distinguish cohorts by City Tier … include `city_tier` inside `re_cohorts`."

## 9. Implementation Approval

Approved for implementation in `migration 030` under this SER. Repository remains GREEN-gated: migration 030 + rollback are added to the deterministic rebuild/teardown set (contiguous numbering, paired rollback), preserving the GREEN invariants.

## 10. Cross-references

- Architecture Freeze: `[ACTIVE]_Phase3_5_Architecture_Freeze_v1.0` (this is the first governed evolution *after* freeze).
- Schema: `DOC-P3-04 §03.27` (`re_cohorts`); implemented by `migration 004`.
- RE docs: `RE-DOC-03` (class taxonomy), `DOC-P3-03 LF-B02` (weekly plan read).
- Research: `Batch1_Resolution_Package` RES-004 / GAP-002; `Cohort_Matrix_v3`, `Weekly_Class_Plan_v3`.
- Audit: `[ACTIVE]_WP-6RE_Recommendation_Engine_Knowledge_Audit_v1.0` (§Step-3 GAP-002 proof).

Founder Sign-off: _______________________ Date: ___________
