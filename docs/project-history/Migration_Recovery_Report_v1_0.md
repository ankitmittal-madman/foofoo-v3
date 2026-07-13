# Migration Recovery Report v1.0 (WP-5B)

**Status:** ACTIVE — Recovery executed (repository artifacts only; database NOT modified)
**Version:** v1.0
**Date:** 2026-07-13
**Placement:** docs/project-history/Migration_Recovery_Report_v1_0.md
**Supersedes:** None — first Migration Recovery Report
**Dependencies:** Repository_Completeness_Audit_v1_0 (identified the gap, RR-01), Repository_Recovery_Work_Package_Plan_v1_0 (defines WP-5B). Companions: Migration_Recovery_Evidence_Register_v1_0, Migration_Recovery_Decision_Log_v1_0, Migration_Recovery_Validation_Report_v1_0.

---

## Executive Summary

WP-5B recovered the six forward migration files (`021`–`026`) that the Repository Completeness Audit found missing (Critical risk RR-01: the repository could not rebuild its own live schema). Recovery — not invention — was possible because the live Supabase database (`slsqtlygeekdppuyiiff`) still holds the exact applied result of these migrations, and repository documents (REPO-WP-02 §7.6, Architecture Freeze v1.0, AGR-005/006) independently corroborate each object's purpose. Every recovered file is explicitly headed **RECONSTRUCTED FROM EVIDENCE**; none is presented as the byte-original. The live database was inspected read-only and **not modified**. No rollback SQL was written (that is WP-5C). Overall recovery confidence: **HIGH**.

## 1. What was recovered

| File | Object(s) | Live version | Confidence |
|---|---|---|---|
| `021_cuisines_reference.sql` | `public.cuisines` table; `cuisine_id` FK on `dishes` & `dish_combos`; RLS + `cuisines_public_read` policy | 20260706092140 | High |
| `022_dish_display_attributes.sql` | `dishes.calories`, `dishes.serving_size`, `dishes.food_dna_tier_1` | 20260706092156 | High |
| `023_tags_uniqueness_and_vector_positions.sql` | drop global `tags` unique → `UNIQUE(dimension,tag_name)`; `fn_assign_tag_vector_positions()` (verbatim) | 20260706092216 | High |
| `024_re_dish_regional_affinity.sql` | `re_engine.re_dish_regional_affinity` table (the RR-01 table) | 20260706092242 | High |
| `025_combo_component_type_and_slot_array.sql` | `dish_combo_items.component_type` (8-value CHECK); `re_meal_classes.slot` → `text[]` | 20260706092303 | High* |
| `026_meal_classes_mirror_slot_array.sql` | `public.meal_classes.slot` → `text[]` (read-mirror) | 20260708141613 | High* |

\* Resulting schema state is exact (observed live). The `ALTER … USING` type-conversion expression is reconstructed (result observed, original text not) — flagged in-file and in the Decision Log.

## 2. Evidence hierarchy applied (per WP-5B principles)

Repository documents established *what each migration was for* and *that it existed and ran* (Priority 1–3); the live schema provided the *exact DDL shape* (Priority 4). Reconstruction (Priority 5) was confined to two `USING` conversion expressions in 025/026, both constrained by the cited `'addon' → ['snack']` rule (REPO-WP-02 §7.6). No business logic was invented; the one recovered function body is verbatim from `pg_get_functiondef()`.

## 3. Method (read-only DB inspection)

`list_migrations` (confirmed 021–026 exist by name/version); `information_schema.columns`; `pg_constraint` + `pg_get_constraintdef`; `pg_indexes`; `pg_get_functiondef`; `pg_policies`; `pg_class.relrowsecurity`; `role_table_grants`; `pg_trigger`. Base (pre-021) definitions read from repository files `002`, `003`, `009` to author faithful, order-correct ALTERs. **No DDL/DML was executed against the database.**

## 4. Findings beyond WP-5B scope (recorded, NOT recovered here)

`list_migrations` revealed three further applied migrations absent from the repository, outside WP-5B's `021`–`026` mandate:

| Applied version | Name | Nature |
|---|---|---|
| 20260710101630 | `pf1_security_hardening` | Almost certainly the GRANT-level fix for the `authenticated`/`anon` direct-UPDATE gap flagged in REPO-WP-04DA "Sixth Finding" / WP-04DC. Missing from repo. |
| 20260710104454 | `103_production_cuisines` | Production seed (repo has only seeds 100–102). Missing. |
| 20260710104859 | `103_production_ingredients` | Production seed. Missing. |

These are **new gaps** not named in the Completeness Audit. They should be added to the Recovery Backlog and are candidate scope for a follow-on package (they are neither 021–026 nor rollbacks, so they belong to neither WP-5B nor WP-5C as currently defined). Recorded here for traceability; no action taken.

## 5. Repository health impact

RR-01 moves from **Critical/open** to **resolved-pending-validation**: the repository now contains a contiguous migration set `001`–`028`. Remaining DB-layer gaps: rollbacks `001`–`026` (WP-5C), the three out-of-scope migrations in §4, and independent live-DB verification of a clean-room rebuild.

## 6. What was explicitly NOT done

No rollback files authored (WP-5C). WP-4B / WP-4DB not re-run. Architecture unchanged. Database unmodified. Existing migrations `001`–`020`, `027`, `028` untouched.

## Critical Self-Review

- **Considered** presenting recovered files as originals (dropping the RECONSTRUCTED header) since their applied result is exact. **Rejected** — WP-5B principle #5 and CLAUDE.md forbid pretending; provenance honesty outranks cosmetic cleanliness.
- **Considered** widening scope to recover `pf1_security_hardening` and the `103_*` seeds while connected. **Rejected** — scope discipline; they are recorded (§4) for a properly-approved follow-on, not silently absorbed.
- **Limitation:** table-level grants and any comments in the originals are not reproduced (grants derive from migration 001 default privileges; comments are cosmetic). This does not affect structural rebuild fidelity.

## Versioning & Placement

`Migration_Recovery_Report_v1_0.md` → `docs/project-history/`. New file; supersedes nothing.

## Founder Sign-off

Founder acceptance of the Migration Recovery Report: _______________________ Date: ___________
