# [ACTIVE]_WP-10_FD12_FD11_FD13_Schema_Evolution_Batch_v1.0

**Status:** ACTIVE — Executed and certified (see companion `REPO-CERT-021`).
**Version:** v1.0
**Date:** 2026-07-17
**Placement:** docs/project-history/work-packages/[ACTIVE]_WP-10_FD12_FD11_FD13_Schema_Evolution_Batch_v1.0.md
**Supersedes:** None.
**Dependencies:** `[ACTIVE]_SER-002_dish_ingredients_main_ingredient_flag_v1.0.md`, `[ACTIVE]_SER-003_interaction_events_idempotency_key_v1.0.md`, `[ACTIVE]_Founder_Decision_Register_v1.0.md` (FD-07, FD-11, FD-12, FD-13), prior Wave 1.5 investigation (FD-07 cohort-prior coverage, FD-12 combo-cuisine mix).

---

## Executive Summary

This Work Package executes the first batch of engineering work against the four FD-07/11/12/13 investigations closed out in the prior two sessions: two approved Schema Evolution Requests (SER-002, SER-003) are implemented as migrations `031`/`032` and run against the live database; the FD-12 data fix (a new `Multi-Regional` cuisine, applied to 7 mixed-cuisine `dish_combos` rows) is applied as a plain data change; FD-07 is confirmed to require no seed (documented separately in the Decision Register, not repeated here); and everything is validated against the existing structural/behavioral validation suite plus targeted checks for the new columns and data. Nothing outside this explicit scope was touched.

## 1. Scope

**In scope:**
1. Migration `031` — `public.dish_ingredients.is_main_ingredient boolean NOT NULL DEFAULT false` (SER-002).
2. Migration `032` — `public.interaction_events.dedup_key uuid` (nullable) + partitioned unique index `idx_ie_dedup_key` (SER-003).
3. FD-12 data fix — insert `multi_regional` into `public.cuisines`; point 7 named `dish_combos` rows at it.
4. Validation of all of the above against `900_structural_validation.sql` plus targeted checks.

**Explicitly out of scope (unchanged, still open):**
- FD-07: no seed of `re_cohort_class_priors` — already ratified as "rely on neutral fallback" in the Decision Register; not re-touched here.
- FD-11's actual ingredient data (which rows get `is_main_ingredient = true`) — separate pending Founder deliverable.
- The 7 orphaned `dish_combos` rows with zero linked member dishes (Daal Bafla, Dal Pakwan, Keema Pav, Matar Kulcha, Sadya Thali, Thali Meals (South Indian), Chole Bhature (Delhi)) — pending Founder deliverable, not resolved by this WP.
- The "Kerala Rice Meals" dish-level cuisine mistagging — flagged for human content review, not silently corrected.

## 2. Migration 031 — `dish_ingredients.is_main_ingredient`

Implements SER-002 exactly as approved: `ALTER TABLE public.dish_ingredients ADD COLUMN is_main_ingredient boolean NOT NULL DEFAULT false;`. No uniqueness constraint — multiple `TRUE` rows per dish remain representable, per SER-002 §2. Applied live via `mcp__supabase__apply_migration`; paired rollback written to `database/rollback/031_dish_ingredients_main_ingredient_flag_rollback.sql`.

**Verified post-migration:** column exists, type `boolean`, `is_nullable = NO`, `column_default = false`. All 7,108 existing `dish_ingredients` rows read `false` (0 `true`, 7,108 `false`) — no data fabricated, no existing row altered in meaning.

## 3. Migration 032 — `interaction_events.dedup_key`

Implements SER-003 exactly as approved, including the partition-scoped uniqueness approach (approved as the correct trade-off, not a compromise): `ALTER TABLE public.interaction_events ADD COLUMN dedup_key uuid;` + `CREATE UNIQUE INDEX idx_ie_dedup_key ON public.interaction_events (dedup_key, occurred_at) WHERE dedup_key IS NOT NULL;`. Applied live; paired rollback written to `database/rollback/032_interaction_events_dedup_key_rollback.sql`.

**Verified post-migration:** column exists, type `uuid`, nullable. The unique index propagated automatically to all 3 existing monthly partitions (`interaction_events_2026_07/08/09`), each `indisvalid = true` — confirmed via `pg_inherits`/`pg_index`, not assumed from the parent index definition alone. `interaction_events` currently holds 0 rows (no `POST /v1/events` handler exists yet, per WP-8E's carried tech debt), so no existing data was at risk.

## 4. FD-12 Data Fix

- Inserted one new row into `public.cuisines`: `name='multi_regional'`, `display_name='Multi-Regional'`, `cuisine_group='multi_regional'`, `state_origin='Pan-India'` (following the `street_food_generic` precedent for pan-Indian entries), `tier='tier_1'`, `is_user_facing=true`, `is_active=true`. No column requirement violated (`name` unique, `display_name`/`cuisine_group` NOT NULL, both satisfied).
- Updated `cuisine_id` on exactly the 7 named `dish_combos` rows (Kerala Rice Meals, Biryani Raita, Chole Bhature, Dosa Sambar, Masala Dosa Set, Poha Jalebi, Puri Aloo) to the new cuisine's `id`.
- This is a plain `INSERT`/`UPDATE` on existing columns — no migration file, per the task instruction and consistent with this being a data change, not a schema change.

**Verified post-change:** exactly those 7 combos now show `cuisine_name = 'multi_regional'`; total `dish_combos` = 35 (unchanged), `with_cuisine = 7`, `without_cuisine = 28` (the 21 trivial same-cuisine combos plus the 7 orphaned combos, both untouched, sum to 28 correctly); `cuisines` count went from 65 to 66 (exactly one new row, nothing else added or removed).

## 5. Validation

Ran `900_structural_validation.sql`'s Check 1 (base-table count, expect 62 — unaffected, since only columns were added, not tables: **62/62 pass**), Check 5 (RLS on every public table, expect 0 without RLS: **0/33 pass**), and re-confirmed two Seed Gate counts unaffected by this batch (S-06 `re_meal_classes` = 131, S-11 `re_cohorts` = 2,952, both pass). Re-ran the two derived-column trigger checks from `901_behavioral_trigger_validation.sql` (Bharli Vangi nut-allergen bit, Butter Chicken non-veg derivation) to confirm the `dish_ingredients` ALTER did not disturb `fn_derive_dish_attributes` — both produced identical results to their documented expectation.

No validation check regressed. No table count changed. No RLS policy changed. No trigger behavior changed.

## 6. What Was Deliberately Not Done

- No seed file for `re_cohort_class_priors` (FD-07 — ratified as out of scope, documented separately).
- No `is_main_ingredient = true` data written for any dish (FD-11 — pending Founder deliverable).
- No linking of the 7 orphaned `dish_combos` to any dishes (pending Founder deliverable).
- No correction to the "Kerala Rice Meals" dish cuisine mistagging (flagged for human review, not auto-corrected).
- No code (Edge Functions, adapters) written or modified — this WP is schema + reference-data only.

## Critical Self-Review

- **Did this WP do anything beyond its approved SERs and data-fix plan?** No — both migrations implement their SERs exactly as approved (verbatim column/index shapes, no additions); the data fix touches exactly the 7 named combos and inserts exactly one new cuisine row.
- **Was anything assumed rather than verified?** No — every claim in §2–§5 is backed by a live query result recorded in this session (column existence/type/default, partition index propagation, row counts before/after, unaffected trigger behavior), not inferred from the migration text alone.
- **Frozen artifacts touched?** No — no existing migration, seed, or validation file was edited; only new migration/rollback files were added and one new data row was inserted.
- **Honest limits:** `dedup_key`'s cross-partition dedup guarantee still depends on the not-yet-built `POST /v1/events` app-level 24h lookback check (Epic 5) — the DB constraint alone only guarantees uniqueness within a partition, as disclosed in SER-003 and accepted by the Founder.

## Versioning & Placement

v1.0, `docs/project-history/work-packages/`, per the Placement Rule; naming per WP-5AA (`WP-10`, next sequential top-level Work Package number after `WP-9`).

Founder sign-off: _______________________ Date: ___________
