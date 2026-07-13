# Migration Recovery Evidence Register v1.0 (WP-5B)

**Status:** ACTIVE — Evidence register, report only
**Version:** v1.0
**Date:** 2026-07-13
**Placement:** docs/project-history/Migration_Recovery_Evidence_Register_v1_0.md
**Supersedes:** None
**Dependencies:** Migration_Recovery_Report_v1_0.

---

## Executive Summary

The per-migration evidence matrix (Step 3) and recovery classification (Step 4) for `021`–`026`. Every recovered element traces to (a) live read-only introspection of `slsqtlygeekdppuyiiff` on 2026-07-13 and/or (b) a repository document. Recovery classes: **A** exact (resulting state fully observed/reproducible), **B** partial (structure exact, one element reconstructed), **C** reconstruction required (no faithful source). Result: 021–024 = A; 025–026 = B (state A, one `USING` expression reconstructed). No item is class C.

## 1. Evidence Matrix

### 021_cuisines_reference — Class A
- **Purpose:** create `public.cuisines`; add cuisine FK to content tables. Evidence: REPO-WP-02 §7.6; Architecture Freeze Pack A; Batch3/Batch4 cuisine gap (B4-RES-001).
- **Tables:** `public.cuisines` (10 cols, observed). **Columns:** id/name/display_name/cuisine_group/parent_cuisine/state_origin/description/tier/is_user_facing/is_active (types observed live).
- **Constraints:** PK(id); UNIQUE(name); + FK `dishes.cuisine_id`→cuisines(id), `dish_combos.cuisine_id`→cuisines(id) (observed).
- **Indexes:** cuisines_pkey, cuisines_name_key (observed). **Functions/Triggers:** none.
- **RLS:** enabled + `cuisines_public_read` SELECT USING(true) (observed).
- **Seed dependency:** `103_production_cuisines` (out of scope). **Rollback dependency:** WP-5C must drop policy, RLS, FKs, table.

### 022_dish_display_attributes — Class A
- **Purpose:** add display attributes to dishes. Evidence: REPO-WP-02 §7.6; Freeze Pack A.
- **Columns:** `dishes.calories` (integer), `serving_size` (text), `food_dna_tier_1` (text), all nullable (observed ordinals 24-26).
- **Constraints/Indexes/Triggers:** none added. **Rollback dependency:** drop 3 columns.

### 023_tags_uniqueness_and_vector_positions — Class A
- **Purpose:** resolve Batch3 tag uniqueness conflict; codify vector-position mechanism. Evidence: Batch3 (CBD-003); REPO-WP-02 §7.6; base migration 002 (had global UNIQUE tag_name).
- **Constraints:** DROP `tags_tag_name_key`; ADD `tags_dimension_tag_name_key` UNIQUE(dimension,tag_name) (observed present/absent respectively).
- **Functions:** `public.fn_assign_tag_vector_positions()` — recovered VERBATIM (`pg_get_functiondef`). **Triggers:** none (confirmed).
- **Note:** `vector_position` column + its UNIQUE pre-existed in base 002 (unchanged). **Rollback dependency:** drop function; swap unique back to global tag_name.

### 024_re_dish_regional_affinity — Class A
- **Purpose:** create dish-level regional affinity table (Batch6 B6-GAP-001; Freeze Pack B). This is the RR-01 Critical table.
- **Tables:** `re_engine.re_dish_regional_affinity`. **Columns:** dish_id(uuid NOT NULL), state_code(text NOT NULL), affinity_score(numeric NOT NULL) (observed).
- **Constraints:** PK(dish_id,state_code); FK→dishes(id) ON DELETE CASCADE; FK→re_states(state_code); CHECK 0≤affinity_score≤1 (observed). **RLS:** none (re_engine locked). **Rollback dependency:** drop table.

### 025_combo_component_type_and_slot_array — Class B
- **Purpose:** add combo component classification; convert re_meal_classes.slot to array. Evidence: Freeze Pack C; Batch5 (role vocabulary); REPO-WP-02 §7.6 ('addon'→['snack']); base 003 (scalar slot) / 009 (dish_combo_items).
- **Columns:** `dish_combo_items.component_type` (text, nullable, 8-value CHECK — observed). `re_meal_classes.slot` text→text[] (observed).
- **Constraints:** `dish_combo_items_component_type_check` (8 values, observed); `re_meal_classes_slot_check` (`<@` 4-value + cardinality≥1, observed). `role` CHECK unchanged (observed).
- **Reconstructed element:** the `ALTER … USING (CASE WHEN slot='addon' THEN ARRAY['snack'] ELSE ARRAY[slot] END)` conversion expression (result observed; original text not). **Rollback dependency:** WP-5C — reversing an array→scalar conversion is lossy for any multi-slot row (documented for WP-5C).

### 026_meal_classes_mirror_slot_array — Class B
- **Purpose:** apply 025's slot conversion to the `public.meal_classes` read-mirror (REPO-WP-02 follow-up #3). Evidence: live migration name/version `20260708141613`; base 003; symmetry with 025.
- **Columns/Constraints:** `public.meal_classes.slot` text→text[]; `meal_classes_slot_check` (observed). **Reconstructed element:** same `USING` expression as 025. **Rollback dependency:** same lossy note as 025.

## 2. Referenced documents / WPs / AGRs / validations consulted
REPO-WP-02 (§7.6 addendum, commit 4ed5e91); REPO-WP-03 v1.0/v1.1 (26/26 count, 026 references); Architecture Freeze v1.0 (Packs A/B/C); AGR-005 (027, unrelated table), AGR-006 (028, cites 024 precedent); base migrations 002/003/008/009; validation 900 (structural expectations). Live: `list_migrations`, catalog introspection (2026-07-13).

## Critical Self-Review

- **Considered** classifying 025/026 as Class C (reconstruction). **Rejected** — only one bounded expression is reconstructed; the entire resulting state and all constraints are observed exact, which is materially stronger than "reconstruction required." Class B with an explicit flag is the honest rating.
- **Limitation:** classification reflects fidelity to the *applied result*, not to the lost *original text*, which is unknowable; this distinction is stated rather than blurred.

## Versioning & Placement

`Migration_Recovery_Evidence_Register_v1_0.md` → `docs/project-history/`. New file.

## Founder Sign-off

Founder acceptance of the Migration Recovery Evidence Register: _______________________ Date: ___________
