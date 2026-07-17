# [ACTIVE]_SER-002_dish_ingredients_main_ingredient_flag_v1.0 — Schema Evolution Request

**Status:** ACTIVE — APPROVED (Founder decision, 2026-07-17, approved as written).
**Version:** v1.0
**Date:** 2026-07-17
**Placement:** docs/governance/[ACTIVE]_SER-002_dish_ingredients_main_ingredient_flag_v1.0.md
**Type:** Schema Evolution Request (structural capability only — no data included).
**Author:** Claude (Engineering session, Wave 2a).
**Implements in:** `database/migrations/031_dish_ingredients_main_ingredient_flag.sql` (+ rollback).

---

## 1. Problem

`CandidateRepository`'s `mainIngredientClass` field (the last of the four original WP-8F blockers, per `[ACTIVE]_REPO-CERT-019_WP-8FA_CandidateRepository_Audit_v1.0.md`) cannot be computed today because `public.dish_ingredients` has no way to record which ingredient(s) in a multi-ingredient dish "dominate" for variety/scoring purposes (LF-D/E). This SER adds the structural capability to record that; it does **not** populate it.

## 2. Evidence

- `public.dish_ingredients` (`migration 009_content_junctions.sql`) is a pure junction: `(dish_id, ingredient_id, is_optional)`, `PRIMARY KEY (dish_id, ingredient_id)` — no column expresses ingredient dominance.
- `[ACTIVE]_Founder_Decision_Register_v1.0.md` FD-11 records three previously-considered derivation approaches (by weight/quantity, by source listing order, via a curated override table) with **no ratified rule** and **no source data** — `ingredients.category` exists in the raw source CSV but was never seeded (per WP-8FA blocker 8F-02).
- Because the derivation rule is still undecided, this SER intentionally proposes only a **boolean flag column**, not a weight/rank/percentage column — a rank or weight column would presuppose a specific rule (e.g., "sort by weight") that hasn't been ratified. A boolean is the minimal structure consistent with *any* eventual rule, including a curated override table that simply flags rows true/false.
- **A dish may have more than one dominant ingredient** (e.g., a mixed dal, a combo-style dish, a dish where two proteins are co-equal) — the column must support multiple `TRUE` rows per `dish_id`, not a single "the one main ingredient" slot.

## 3. Architecture Impact

Add `is_main_ingredient boolean NOT NULL DEFAULT false` to `public.dish_ingredients`. Scope is **one column on one table**. No other table changes. `CandidateRepository`'s `mainIngredientClass` field remains unbuilt until (a) this column exists and (b) the Founder ratifies the actual derivation rule and the data is populated — both explicitly **out of scope for this SER**.

## 4. Backward Compatibility

- Added as `NOT NULL DEFAULT false` — every existing `dish_ingredients` row becomes `false` on migration; no existing row is invalidated, no existing query's result set changes (nothing currently reads this column).
- No uniqueness constraint is added restricting how many `TRUE` rows a dish may have — by design, per §2 (multiple dominant ingredients must remain representable).
- Deterministic and idempotent: `ADD COLUMN IF NOT EXISTS` guard, standard for this repository's migration style.

## 5. Migration Strategy

`031_dish_ingredients_main_ingredient_flag.sql`: `ALTER TABLE public.dish_ingredients ADD COLUMN is_main_ingredient boolean NOT NULL DEFAULT false;`. Structural band, next sequential after `030`. No existing migration edited.

## 6. Rollback Strategy

`031_dish_ingredients_main_ingredient_flag_rollback.sql`: `ALTER TABLE public.dish_ingredients DROP COLUMN is_main_ingredient;`. Safe at any time before downstream code reads the column, since no data or code will yet depend on it.

## 7. Explicitly Out of Scope

- **The actual `is_main_ingredient = true` data is a pending Founder deliverable (FD-11), not part of this SER.** No seed file, no ETL extension, and no backfill are proposed here.
- The derivation *rule* itself (by weight, by listing order, curated override) is still unratified and is not decided by this SER — this SER is deliberately rule-agnostic.
- `CandidateRepository.mainIngredientClass` implementation is not in scope; it depends on both the rule (Founder) and the data (Founder deliverable + ETL work), neither of which this SER provides.

## 8. Recommendation

**Approve the structural column now, independent of the data question.** A boolean flag is minimal, does not presuppose an unratified rule, and unblocks Epic 1's adapter work to proceed on every other field while FD-11's data question is resolved separately and in parallel — the column sitting unpopulated costs nothing (default `false` everywhere) until the Founder deliverable lands.

## 9. Founder Decision

**APPROVED as written** (Founder, 2026-07-17). Migration `031` implements this SER exactly as specified — boolean flag, no uniqueness constraint, no data included.

## 10. Cross-references

- `[ACTIVE]_Founder_Decision_Register_v1.0.md` FD-11 (dominant-ingredient derivation rule — still Pending, unaffected by this SER).
- `docs/project-history/certificates/[ACTIVE]_REPO-CERT-019_WP-8FA_CandidateRepository_Audit_v1.0.md` (origin of the blocker).
- `database/migrations/009_content_junctions.sql` (current `dish_ingredients` definition).
- `[ACTIVE]_SER-001_re_cohorts_city_tier_v1.0.md` (SER format precedent).

Founder Sign-off: Ankit Mittal — Date: 2026-07-17
