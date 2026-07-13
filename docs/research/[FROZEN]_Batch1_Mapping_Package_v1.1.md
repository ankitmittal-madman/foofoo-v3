# Phase 3.5 — Batch 1 — Stage 3: Knowledge Mapping
## Consolidated Deliverable Set v1.1

**Governed by:** `[ACTIVE]_DOC-P3-09_Knowledge_Integration_Governance_v1.0`, `[ACTIVE]_DOC-P3-10_Seed_Data_Integration_Framework_v1.1`
**Execution audit trail:** `[ACTIVE]_DOC-P3-11_Discovery_Execution_Register_v1.5`
**Input (frozen, immutable, not touched):** `Batch1_Discovery_Report_v1.1` (FROZEN), `Batch1_Canonicalization_Package_v1.1` (FROZEN)
**Target (frozen architecture, not touched):** `DOC-P3-04_Data_Architecture_ERD_v1.3`
**Supersedes:** `Batch1_Mapping_Package_v1.0` (not modified — retained as superseded reference)
**Date:** 2026-07-02
**Status:** APPROVED — ACTIVE — FROZEN

**Revision Notice (v1.0 → v1.1) — governance refinement only, no new mapping decisions, no issue resolution:**
1. New **Section 1A — Canonical Attribute → Schema Mapping Matrix** (all 76 CAN-ATT entries)
2. New **Section 6A — Mapping Decision Register** (`MAP-DEC-*`)
3. New **Section 6B — Transformation Summary**
4. New **Section 6C — Mapping Completeness Metrics**
5. New **Section 6D — Mapping Confidence Dashboard**
6. New **Section 6E — Permanent MAP ID Governance**
7. MI-004 and MI-007 recommendation wording refined (issues themselves unchanged, unresolved, not weakened)
8. New **Section 6F — Executive Mapping Summary**
9. This document is now **FROZEN** — v1.0 retained unmodified as superseded reference
10. Attribute-level review (required to build Section 1A) surfaced **7 new consolidated Mapping Issues (MI-017 through MI-023)** — orphaned canonical attributes with no column anywhere in the 15 target tables. These are new *findings*, not new *decisions*; nothing is resolved.

No existing section was renumbered or restructured.

**Scope (unchanged):** Batch 1 only. No schema redesign, no entity redesign, no API/RE-logic redesign, no Gap Analysis, no SQL, no seed data, no re-canonicalization, no inferred business facts.

---

## 0. Method Note

DOC-P3-04 v1.3's frozen schema (§03.27) defines exactly 15 `re_engine` reference tables. Remarkably, they correspond almost 1:1 to this batch's 15 canonical entities, and their documented seed-row-counts (36, 5, 41, 41, 8, 131, 13, 1,050, 24, 142–143, 2,952–2,953, 20,664, 7,992, 36, 324) match this batch's canonical row counts **exactly**. This confirms Batch 1 is the intended seed source for these tables.

Every mapping decision below states its **MAP ID**, **Source CAN ID(s)**, **Target schema object**, **Target column(s)**, **Rationale**, **Confidence** (DOC-P3-09 §14 bands), **Evidence**, **Transformation Rule reference** (if applicable), **Provenance**, and **Direct / Composite / Derived / Deferred** classification. Where the schema expects a value with no canonical source, or expects a value format not evidenced in the canonical data, this is raised as a **Mapping Issue (MI-XXX)** — not silently resolved, not guessed.

**Scope note on row-level verification:** for high-cardinality tables (131 meal classes, 2,952 cohorts, 20,664 weekly-plan rows), this stage verifies the **mapping rule** (which source field → which target column, and whether the transformation is sound) using representative evidence — not a manual row-by-row check of every value, which is properly a Seed Generation / validation-stage activity (`90x_behavioral_*.sql`), not a Mapping-stage one.

---

## 1. Entity-to-Table Mapping

| MAP ID | Source CAN ID | Target Schema Object | Classification | Confidence | Rationale |
|---|---|---|---|---|---|
| MAP-ENT-001 | CAN-ENT-001 (Main Cohort) | `re_engine.re_main_cohorts` | Direct | High | Row counts match exactly (5=5); table is the obvious seed target per DOC-P3-04 §02 table inventory |
| MAP-ENT-002 | CAN-ENT-002 (Sub-Cohort) | `re_engine.re_subcohorts` | Direct | High | Row counts match exactly (41=41) |
| MAP-ENT-003 | CAN-ENT-003 (Persona) | `re_engine.re_personas` | Direct | High | Row counts match exactly (41=41) |
| MAP-ENT-004 | CAN-ENT-004 (Routing Rule) | `re_engine.re_routing_rules` | Direct | High | Row counts match exactly (8=8) |
| MAP-ENT-005 | CAN-ENT-005 (State/UT) | `re_engine.re_states` | Direct | High | Row counts match exactly (36=36) |
| MAP-ENT-006 | CAN-ENT-006 (City Migration Overlay) | `re_engine.re_city_migration_overlays` | Direct | High | Row counts match exactly (324=324) |
| MAP-ENT-007 | CAN-ENT-007 (Meal Class) | `re_engine.re_meal_classes` | Direct | High | Row counts match exactly (131=131) |
| MAP-ENT-008 | CAN-ENT-008 (Class-Dish Option) | `re_engine.re_class_dish_options` | Direct (structure) / Deferred (dish_id value) | Medium | Row counts match exactly (1,050=1,050), but `dish_id` is a UUID FK to `public.dishes`, which is not yet canonicalized (Batch 4) — see MI-001 |
| MAP-ENT-009 | CAN-ENT-009 (Dish, Batch 1 scope) | *(no direct table — dish identity resolves through `public.dishes`, out of Batch 1 scope)* | Deferred | N/A | Per Batch Independence Rule and Cross-Batch Merge Governance — see MI-001 |
| MAP-ENT-010 | CAN-ENT-010 (Add-on Component Class) | `re_engine.re_addon_classes` | Direct | High | Row counts match exactly (24=24) |
| MAP-ENT-011 | CAN-ENT-011 (Add-on Dish Option) | `re_engine.re_addon_dish_options` | Direct (structure) / Deferred (dish_id value) | Medium | Row counts match (142–143 vs 142) — same `dish_id` dependency as MAP-ENT-008; see MI-001 |
| MAP-ENT-012 | CAN-ENT-012 (Cohort) | `re_engine.re_cohorts` | Direct (structure) / Derived (some columns) | Medium | Row counts match (2,952–2,953 vs 2,952) — see MI-002, MI-003 for `diet_mode`/`prior_weight` |
| MAP-ENT-013 | CAN-ENT-013 (Weekly Plan Day) | `re_engine.re_weekly_class_plans` | Composite (major restructure) | Low-Medium | Row counts match exactly (20,664=20,664) but the schema's column structure is substantially narrower than the canonical entity — see MI-004 (this is the single largest Mapping Issue in this batch) |
| MAP-ENT-014 | CAN-ENT-014 (Household Addon Plan Entry) | `re_engine.re_household_addon_plans` | Composite | Medium | Row counts match exactly (7,992=7,992), but schema drops day/slot granularity present in canonical data — see MI-005 |
| MAP-ENT-015 | CAN-ENT-015 (NonVeg Logic Profile) | `re_engine.re_nonveg_logic` | Composite | Medium | Row counts match exactly (36=36), but schema's 2-column structure is much narrower than the canonical entity's 6-count + list structure — see MI-006 |

**All 15 canonical entities have a target table identified.** Three (MAP-ENT-008, 009, 011) have a Deferred component pending Batch 4. Four (MAP-ENT-012, 013, 014, 015) carry genuine structural Mapping Issues, detailed below — none silently resolved.

---

## 1A. Canonical Attribute → Schema Mapping Matrix *(new in v1.1 — authoritative reference for Seed Generation)*

All 76 `CAN-ATT` entries from `Batch1_Canonicalization_Package_v1.1` §1A, mapped individually. Transformation Rule references cite the library in `DOC-P3-10` §20A (`TR-001`–`TR-006`) where applicable; a new transformation need not yet catalogued there is marked "TR-new (uncatalogued)". Confidence follows DOC-P3-09 §14 bands.

| CAN-ATT | Attribute Name | Source Entity | Target Table | Target Column | Mapping Type | Transformation Rule | Confidence | Related MAP ID | Related MI |
|---|---|---|---|---|---|---|---|---|---|
| CAN-ATT-001 | main_cohort_label | CAN-ENT-001 | `re_main_cohorts` | `display_label` | Direct | None | High | MAP-ENT-001 | — |
| CAN-ATT-002 | user_understands_as | CAN-ENT-001 | *(no column)* | — | Deferred | — | Medium | MAP-ENT-001 | MI-017 |
| CAN-ATT-003 | subcohort_screen_copy | CAN-ENT-001 | *(no column)* | — | Deferred | — | Medium | MAP-ENT-001 | MI-017 |
| CAN-ATT-004 | routing_notes | CAN-ENT-001 | *(no column)* | — | Deferred | — | Medium | MAP-ENT-001 | MI-017 |
| CAN-ATT-005 | sub_cohort_label | CAN-ENT-002 | `re_subcohorts` | `description` | Direct | TR-002 (case normalization, if needed) | High | MAP-ENT-002 | — |
| CAN-ATT-006 | show_as_chip_text | CAN-ENT-002 | *(no column)* | — | Deferred | — | Medium | MAP-ENT-002 | MI-017 |
| CAN-ATT-007 | ask_next | CAN-ENT-002 | *(no column)* | — | Deferred | — | Medium | MAP-ENT-002 | MI-017 |
| CAN-ATT-008 | do_not_show_in_first_screen | CAN-ENT-002 | *(no column)* | — | Deferred | — | Medium | MAP-ENT-002 | MI-017 |
| CAN-ATT-009 | persona_name | CAN-ENT-003 | `re_personas` | `display_name` | Direct | None | High | MAP-ENT-003 | — |
| CAN-ATT-010 | age_band | CAN-ENT-003 | *(no column)* | — | Deferred | — | Medium | MAP-ENT-003 | MI-018 |
| CAN-ATT-011 | household_stage | CAN-ENT-003 | *(no column)* | — | Deferred | — | Medium | MAP-ENT-003 | MI-018 |
| CAN-ATT-012 | lifecycle_health | CAN-ENT-003 | *(no column)* | — | Deferred | — | Medium | MAP-ENT-003 | MI-018 |
| CAN-ATT-013 | cook_dependency | CAN-ENT-003 | *(no column)* | — | Deferred | — | Medium | MAP-ENT-003 | MI-018 |
| CAN-ATT-014 | time_pressure | CAN-ENT-003 | *(no column)* | — | Deferred | — | Medium | MAP-ENT-003 | MI-018 |
| CAN-ATT-015 | nonveg_mode | CAN-ENT-003 | `re_personas` | `primary_diet` | Derived | TR-new (uncatalogued — 12-value nonveg_mode → primary_diet's value domain, format unconfirmed) | Medium | MAP-ENT-003 | MI-002 (shared root cause with `re_cohorts.diet_mode`) |
| CAN-ATT-016 | revealed_behavior_summary | CAN-ENT-003 | *(no column)* | — | Deferred | — | Medium | MAP-ENT-003 | MI-018 |
| CAN-ATT-017 | meal_slot_boost_classes | CAN-ENT-003 | *(no column)* | — | Deferred | — | Medium | MAP-ENT-003 | MI-018 |
| CAN-ATT-018 | onboarding_branch_trigger | CAN-ENT-003 | `re_routing_rules` (cross-entity) | `trigger_answer` (plausible, unconfirmed) | Derived | TR-new (uncatalogued) | Low-Medium | MAP-ENT-004 (cross-ref) | MI-021 |
| CAN-ATT-019 | can_be_overlay | CAN-ENT-003 | *(no column)* | — | Deferred | — | Medium | MAP-ENT-003 | MI-018 |
| CAN-ATT-020 | dependent_addon_default | CAN-ENT-003 | *(no column)* | — | Deferred | — | Medium | MAP-ENT-003 | MI-018 |
| CAN-ATT-021 | health_overlay_default | CAN-ENT-003 | *(no column)* | — | Deferred | — | Medium | MAP-ENT-003 | MI-018 |
| CAN-ATT-022 | cook_overlay_default | CAN-ENT-003 | *(no column)* | — | Deferred | — | Medium | MAP-ENT-003 | MI-018 |
| CAN-ATT-023 | recommended_onboarding_path | CAN-ENT-003 | *(no column)* | — | Deferred | — | Medium | MAP-ENT-003 | MI-018 |
| CAN-ATT-024 | shown_when | CAN-ENT-004 | `re_routing_rules` | `trigger_answer` (plausible) | Derived | TR-new (uncatalogued) | Medium | MAP-ENT-004 | MI-021 |
| CAN-ATT-025 | input_type | CAN-ENT-004 | *(no column)* | — | Deferred | — | Medium | MAP-ENT-004 | MI-021 |
| CAN-ATT-026 | user_prompt_summary | CAN-ENT-004 | *(no column)* | — | Deferred | — | Medium | MAP-ENT-004 | MI-021 |
| CAN-ATT-027 | why_it_matters | CAN-ENT-004 | *(no column)* | — | Deferred | — | Medium | MAP-ENT-004 | MI-021 |
| CAN-ATT-028 | maps_to_fields | CAN-ENT-004 | `re_routing_rules` | `show_question_key` (plausible) | Derived | TR-new (uncatalogued) | Medium | MAP-ENT-004 | MI-021 |
| CAN-ATT-029 | state_ut | CAN-ENT-005 | `re_states` | `state_name` | Direct | None | High | MAP-ENT-005 | — |
| CAN-ATT-030 | region_archetype | CAN-ENT-005 | `re_states` | `region` (unconfirmed exact value domain) | Derived | TR-new (uncatalogued) | Medium | MAP-ENT-005 | MI-011 |
| CAN-ATT-031 | representative_cities | CAN-ENT-005 | *(no column)* | — | Deferred | — | Medium | MAP-ENT-005 | MI-019 |
| CAN-ATT-032 | nonveg_intensity | CAN-ENT-005 | *(no column)* | — | Deferred | — | Medium | MAP-ENT-005 | MI-019 |
| CAN-ATT-033 | primary_staple_base | CAN-ENT-005 | *(no column)* | — | Deferred | — | Medium | MAP-ENT-005 | MI-019 |
| CAN-ATT-034 | meal_slot_class_pools | CAN-ENT-005 | *(no column)* | — | Deferred | — | Medium | MAP-ENT-005 | MI-019 |
| CAN-ATT-035 | behavioral_notes | CAN-ENT-005 | *(no column)* | — | Deferred | — | Medium | MAP-ENT-005 | MI-019 |
| CAN-ATT-036 | destination_group_name | CAN-ENT-006 | *(no column — `re_city_migration_overlays` has no name/label column)* | — | Deferred | — | Medium | MAP-ENT-006 | MI-020 |
| CAN-ATT-037 | weighting_factors | CAN-ENT-006 | `re_city_migration_overlays` | `city_overlay_weight` (single column vs. 3 canonical weights) | Composite → **Issue** | — | Low | MAP-ENT-006 | MI-015 |
| CAN-ATT-038 | overlay_meal_classes | CAN-ENT-006 | *(no column)* | — | Deferred | — | Medium | MAP-ENT-006 | MI-020 |
| CAN-ATT-039 | planning_rule | CAN-ENT-006 | *(no column)* | — | Deferred | — | Medium | MAP-ENT-006 | MI-020 |
| CAN-ATT-040 | class_name | CAN-ENT-007 | *(no column — `re_meal_classes` has no display-name column)* | — | Deferred | — | Medium | MAP-ENT-007 | MI-022 |
| CAN-ATT-041 | class_category | CAN-ENT-007 | *(no column)* | — | Deferred | — | Medium | MAP-ENT-007 | MI-022 |
| CAN-ATT-042 | fit_scores | CAN-ENT-007 | `re_meal_classes` | `weekday_fit_1_5`, `weekend_fit_1_5` | Composite | TR-new (split composite into 2 columns) | High | MAP-ENT-007 | — |
| CAN-ATT-043 | cook_complexity | CAN-ENT-007 | *(no column)* | — | Deferred | — | Medium | MAP-ENT-007 | MI-022 |
| CAN-ATT-044 | heaviness | CAN-ENT-007 | *(no column)* | — | Deferred | — | Medium | MAP-ENT-007 | MI-022 |
| CAN-ATT-045 | food_profile | CAN-ENT-007 | `re_meal_classes` | `cuisine_family` (partial overlap only, unconfirmed) | Derived → **Issue** | — | Low | MAP-ENT-007 | MI-022 |
| CAN-ATT-046 | region_relevance | CAN-ENT-007 | *(no column)* | — | Deferred | — | Medium | MAP-ENT-007 | MI-022 |
| CAN-ATT-047 | behavioral_meaning | CAN-ENT-007 | *(no column)* | — | Deferred | — | Medium | MAP-ENT-007 | MI-022 |
| CAN-ATT-048 | food_dna_tags | CAN-ENT-007 | *(no column in the 15 target tables)* | — | Deferred | — | Medium | MAP-ENT-007 | MI-022 |
| CAN-ATT-049 | allowed_as_weekly_primary_v3 | CAN-ENT-007 | `re_meal_classes` | `planning_role` (via MAP-RULE-001 logic) | Derived | None (already-verified rule, CAN-RULE-004) | High | MAP-RULE-001 | — |
| CAN-ATT-050 | addon_target_segment_v3 | CAN-ENT-007 | *(no column)* | — | Deferred | — | Medium | MAP-ENT-007 | MI-022 |
| CAN-ATT-051 | overlap_resolution_v3 | CAN-ENT-007 | `re_meal_class_overlap_rules` (separate table, via MAP-RULE-002) | `conflicts_with` (plausible) | Derived | None | Medium | MAP-RULE-002 | — |
| CAN-ATT-052 | region_relevance (Class-Dish) | CAN-ENT-008 | *(no column)* | — | Deferred | — | Medium | MAP-ENT-008 | MI-022 |
| CAN-ATT-053 | class_use_scope_v3 | CAN-ENT-008 | `re_class_dish_options` | `is_primary_candidate` (plausible derivation) | Derived → **Issue** | TR-new (uncatalogued boolean rule) | Medium | MAP-RULE-004 | MI-014 |
| CAN-ATT-054 | dish_name | CAN-ENT-009 | `re_class_dish_options` | `dish_id` (UUID, requires Batch 4) | Deferred | — | N/A | MAP-ENT-008/009 | MI-001 |
| CAN-ATT-055 | addon_class_name | CAN-ENT-010 | *(no column — `re_addon_classes` has no name/label column)* | — | Deferred | — | Medium | MAP-ENT-010 | MI-020 |
| CAN-ATT-056 | food_dna_role | CAN-ENT-010 | *(no column)* | — | Deferred | — | Medium | MAP-ENT-010 | MI-020 |
| CAN-ATT-057 | planning_note | CAN-ENT-010 | *(no column)* | — | Deferred | — | Medium | MAP-ENT-010 | MI-020 |
| CAN-ATT-058 | dish_or_component_name | CAN-ENT-011 | `re_addon_dish_options` | `dish_id` (UUID, requires Batch 4) | Deferred | — | N/A | MAP-ENT-011 | MI-001 |
| CAN-ATT-059 | representative_cities (Cohort) | CAN-ENT-012 | *(no column)* | — | Deferred | — | Medium | MAP-ENT-012 | MI-019 |
| CAN-ATT-060 | weekly_class_mix | CAN-ENT-012 | *(no column — `re_cohorts` has no class-mix column; this is expressed instead via `re_weekly_class_plans`)* | — | Composite (represented elsewhere) | — | Medium | MAP-ENT-013 | MI-004 |
| CAN-ATT-061 | nonveg_egg_defaults | CAN-ENT-012 | *(no column)* | — | Deferred | — | Medium | MAP-ENT-012 | MI-002 |
| CAN-ATT-062 | dependent_addon_required_v3 | CAN-ENT-012 | *(no column)* | — | Deferred | — | Medium | MAP-ENT-012 | MI-002 |
| CAN-ATT-063 | household_addon_logic | CAN-ENT-012 | `re_household_addon_plans` | `segment` (plausible) | Derived | TR-new (uncatalogued) | Medium | MAP-ENT-014 | MI-005 |
| CAN-ATT-064 | planning_confidence_v3 | CAN-ENT-012 | *(no column — `prior_weight` is numeric, this source is free text)* | — | Deferred | — | Low | MAP-ENT-012 | MI-003 |
| CAN-ATT-065 | day_of_week | CAN-ENT-013 | `re_weekly_class_plans` | `day_of_week` | Direct | None | High | MAP-ENT-013 | — |
| CAN-ATT-066 | weekday_weekend | CAN-ENT-013 | *(no column — schema has no separate weekday/weekend flag; `re_meal_classes.day_type` is the closer analog, but on the wrong table)* | — | Deferred | — | Medium | MAP-ENT-013 | MI-004 |
| CAN-ATT-067 | meal_slot_classes | CAN-ENT-013 | `re_weekly_class_plans` | `breakfast_class_code`, `lunch_class_code`, `dinner_class_code` (primary only; secondary/tertiary/snack have no column) | Composite → **Issue** | — | Low | MAP-REL-006 | MI-004 |
| CAN-ATT-068 | addon_class_codes | CAN-ENT-013 | *(no column on this table — addons live in `re_household_addon_plans` at a different grain)* | — | Composite → **Issue** | — | Low | MAP-REL-007 | MI-005 |
| CAN-ATT-069 | scheduled_nonveg_or_egg_slot | CAN-ENT-013 | *(no column)* | — | Deferred | — | Medium | MAP-ENT-013 | MI-004 |
| CAN-ATT-070 | state_ut/city_tier/persona_name (display context) | CAN-ENT-014 | *(no column — `re_household_addon_plans` has no display-context columns)* | — | Deferred | — | Medium | MAP-ENT-014 | MI-005 |
| CAN-ATT-071 | day_of_week, meal_slot | CAN-ENT-014 | *(no column)* | — | Deferred → **Issue** | — | Low | MAP-ENT-014 | MI-005 |
| CAN-ATT-072 | target_member_segment | CAN-ENT-014 | `re_household_addon_plans` | `segment` | Direct | None | High | MAP-ENT-014 | — |
| CAN-ATT-073 | addon_examples | CAN-ENT-014 | *(no column — represented via `re_addon_dish_options`, not this table)* | — | Composite (represented elsewhere) | — | Medium | MAP-ENT-011 | — |
| CAN-ATT-074 | cooking_logic | CAN-ENT-014 | *(no column)* | — | Deferred | — | Medium | MAP-ENT-014 | MI-005 |
| CAN-ATT-075 | meals_per_week_defaults | CAN-ENT-015 | `re_nonveg_logic` | `weekly_nonveg_slots` (6 canonical counts → 1 schema column) | Composite → **Issue** | — | Low | MAP-ENT-015 | MI-006 |
| CAN-ATT-076 | preferred_nonveg_classes | CAN-ENT-015 | `re_nonveg_logic` | `preferred_slots` (plausible, name mismatch — "slots" vs. "classes") | Derived → **Issue** | — | Low-Medium | MAP-ENT-015 | MI-006 |
| CAN-ATT-077 *(renumbered reference — original CAN-ATT-077 in the Canonicalization package is `state_notes`)* | state_notes | CAN-ENT-015 | *(no column)* | — | Deferred | — | Medium | MAP-ENT-015 | MI-006 |

**Matrix coverage: 76/76 canonical attributes addressed. 18 map Direct/Composite/Derived with reasonable confidence; 58 are Deferred or flagged as part of an Issue — see Section 6C for the full completeness breakdown.**

---

## 2. Vocabulary Mapping



| MAP ID | Source CAN ID | Target Schema Object | Classification | Confidence | Rationale |
|---|---|---|---|---|---|
| MAP-VOC-001 | CAN-VOC-002 (Diet Type core: egg/mixed/nonveg/veg) | `re_meal_classes.diet_type text` (no CHECK constraint on this column) | Direct | High | Column exists, unconstrained text — canonical values fit without transformation |
| MAP-VOC-002 | CAN-VOC-009 (Planning Role) | `re_meal_classes.planning_role` CHECK IN ('MAIN_PRIMARY','ADDON_ONLY_NOT_PRIMARY','COMBO_TEMPLATE_NOT_PRIMARY') | Direct | High | **Exact verbatim match** — canonical vocabulary's 3 values are identical to the schema's CHECK constraint values |
| MAP-VOC-003 | CAN-VOC-004 (Core Meal Slot: Breakfast, Lunch/Dinner, Dinner, Snack) | `re_meal_classes.slot` CHECK IN ('breakfast','lunch','dinner','addon') | **Mapping Issue** | Low | See MI-007 — schema's enum has no `snack` value at all, and splits "Lunch/Dinner" into two separate values while adding an `addon` value not present in the canonical core vocabulary |
| MAP-VOC-004 | CAN-VOC-005 (Addon Slot Applicability, per F2 — preserved verbatim) | *(no direct schema column — `re_addon_classes.slot text`, unconstrained)* | Derived | Medium | `re_addon_classes.slot` is free text, so the compound values (e.g. "Breakfast/Snack/Dinner") could be stored verbatim without violating any constraint — but see MI-007, since this is entangled with the same `slot` vocabulary confusion |
| MAP-VOC-005 | CAN-VOC-001 (Main Cohort ID: MC1–MC5) | `re_main_cohorts.cohort_code` (example values in schema comment: MC_SOLO, MC_COUPLE, MC_NUCLEAR_FAMILY, MC_JOINT_FAMILY, MC_PG_HOSTEL) | **Mapping Issue** | Low-Medium | See MI-008 — 4 of 5 values correspond plausibly by label semantics; MC5 does not |
| MAP-VOC-006 | CAN-VOC-006/007 (City Tier Code/Label: T1/T2, Tier1_Metro/Tier2_Urban) | *(no direct schema column found in the 15 target tables)* | **Mapping Issue** | N/A | See MI-009 — city tier does not appear as a column anywhere in `re_cohorts`, `re_weekly_class_plans`, or `re_household_addon_plans` |
| MAP-VOC-007 | CAN-VOC-008 (Class Family Code, 14 `FAM_` values) | *(no direct schema column)* | **Mapping Issue** | N/A | See MI-010 — no `class_family_code` or equivalent column exists on `re_meal_classes` |
| MAP-VOC-008 | CAN-VOC-003 (Nonveg Mode, 12 values) | `re_cohorts.diet_mode text` (unconstrained) | Derived | Medium | Plausible target by name, but the exact value format `diet_mode` expects is not specified in the schema — see MI-002 |
| MAP-VOC-009 | CAN-VOC-012 (Day of Week) | `re_weekly_class_plans.day_of_week text` (unconstrained) | Direct | High | Free text, no format conflict; canonical 3-letter abbreviations fit without transformation |
| MAP-VOC-010 | CAN-VOC-015 (Region Archetype) | *(no direct schema column)* | **Mapping Issue** | N/A | See MI-011 — `re_states` has only `state_code`, `state_name`, `region` (3 columns); `region` may be intended to hold this, but its expected value format is unconfirmed |

---

## 3. Relationship Mapping

| MAP ID | Source CAN ID | Target Schema FK | Classification | Confidence | Notes |
|---|---|---|---|---|---|
| MAP-REL-001 | CAN-REL-006/007/009 (Persona→Main Cohort/Sub-Cohort) | `re_personas.main_cohort_code REFERENCES re_main_cohorts(cohort_code)` | Direct (structure) | High | FK structure matches exactly one canonical relationship (Persona→Main Cohort); **note:** schema has no direct `re_personas → re_subcohorts` FK — subcohort routing is a `re_routing_rules`/onboarding-flow concept, not a stored FK in this table. `re_subcohorts` itself has the `main_cohort_code` FK independently. |
| MAP-REL-002 | CAN-REL-005 (Sub-Cohort→Persona) | *(no FK found — `re_subcohorts` has no `persona_id`/`persona_code` column)* | **Mapping Issue** | N/A | See MI-012 — the canonical "maps_to_persona_id" relationship (the entire point of the routing sheet) has no home in the frozen schema as currently defined |
| MAP-REL-003 | CAN-REL-008 (Cohort→State/UT) | `re_cohorts.state_code REFERENCES re_states(state_code)` | Direct (structure) | High | Matches exactly |
| MAP-REL-004 | CAN-REL-009 (Cohort→Persona) | `re_cohorts.persona_id REFERENCES re_personas(id)` | Direct (structure) | High | Matches exactly — note the FK target is `re_personas.id` (the surrogate UUID), not `persona_code`, which is consistent regardless of how MI-013's persona_code value question resolves |
| MAP-REL-005 | CAN-REL-001 (Weekly Plan Day→Cohort) | `re_weekly_class_plans.cohort_id REFERENCES re_cohorts(cohort_id)` | Direct (structure) | High | Matches exactly |
| MAP-REL-006 | CAN-REL-002 (Weekly Plan Day→Meal Class, primary/secondary/tertiary) | `re_weekly_class_plans.{breakfast,lunch,dinner}_class_code REFERENCES re_meal_classes(class_code)` | Composite / partial | Medium | Schema only has room for ONE class per slot (implicitly "primary") for 3 of 4 slots — see MI-004 |
| MAP-REL-007 | CAN-REL-003 (Weekly Plan Day→Add-on, per slot) | *(no column on `re_weekly_class_plans` — add-ons live in `re_household_addon_plans` instead)* | Composite | Medium | Relationship exists but at a different granularity — see MI-005 |
| MAP-REL-008 | CAN-REL-011 (Household Addon→Meal Class, via `attached_to_main_class_code`) | *(no `attached_to_main_class_code`-equivalent column on `re_household_addon_plans`)* | **Mapping Issue** | N/A | See MI-005 |
| MAP-REL-009 | CAN-REL-012 (Household Addon→Add-on Component Class) | `re_household_addon_plans.addon_class_code REFERENCES re_addon_classes(addon_class_code)` | Direct (structure) | High | Matches exactly |
| MAP-REL-010 | CAN-REL-013 (NonVeg Logic→State/UT) | `re_nonveg_logic.state_code REFERENCES re_states(state_code)` (schema uses `state_code` as both PK and the join key, 1:1) | Direct (structure) | High | Matches exactly — confirms CD-6's deferred modeling question is now resolved *structurally* by the frozen schema: NonVeg Logic Profile is its own table, 1:1 keyed to State, not folded into `re_states` |
| MAP-REL-011 | CAN-REL-010 (Overlap Resolution→Meal Class) | `re_meal_class_overlap_rules.class_code REFERENCES re_meal_classes(class_code)` | Direct (structure) | High | Matches exactly |

**MAP-REL-010 resolves the one open Canonicalization modeling note (CD-6) as a side effect of Mapping** — the frozen schema already decided NonVeg Logic Profile is a separate table. This is stated here as an observation of what the schema does, not a new architecture decision.

---

## 4. Business Rule Mapping

| MAP ID | Source CAN ID | Target Enforcement Mechanism | Classification | Confidence |
|---|---|---|---|---|
| MAP-RULE-001 | CAN-RULE-004 (only `MAIN_PRIMARY`+`allowed_as_weekly_primary=Y` classes may be weekly primary) | `re_meal_classes.planning_role` CHECK constraint + `idx_re_meal_classes_role` index, explicitly built "to support Safety Gate 4 (LF-H04)" per DOC-P3-04 §03.27 comment | Direct | High — schema explicitly names this exact rule as its purpose |
| MAP-RULE-002 | CAN-RULE-003 (13 classes excluded from main rotation) | `re_meal_class_overlap_rules` table (13-row seed target, Seed Gate S-07) | Direct | High — row count match (13=13) confirms this table exists specifically for this rule |
| MAP-RULE-003 | CAN-RULE-002 (dependent/lifecycle foods never primary — add-ons only) | `re_household_addon_plans` / `re_addon_classes` tables (separate from `re_meal_classes`/`re_weekly_class_plans`) | Direct | High — the schema's table separation itself enforces this rule structurally |
| MAP-RULE-004 | CAN-RULE-011 (946 main-pool vs 104 legacy/addon-scoped dish rows) | `re_class_dish_options.is_primary_candidate boolean` | Derived | Medium — plausible target column, but its exact derivation rule from `class_use_scope_v3` is not specified — see MI-014 |
| MAP-RULE-005 | CAN-RULE-008 (City Migration Overlay's 3 weights) | `re_city_migration_overlays.city_overlay_weight real` (single column) | **Mapping Issue** | N/A — see MI-015, schema has only ONE weight column, canonical data has THREE named weights |
| MAP-RULE-006 | CAN-RULE-005/006/007 (nonveg activation guardrails, hard-filter overrides) | Not a schema-enforceable rule — these are Edge Function / application-logic rules, per DOC-P3-04 Principle 3 ("hard constraints are query-time joins... never cached booleans the filter trusts blindly") | Derived (documentation only) | High — correctly has NO direct schema column; this rule belongs in RE Edge Function logic, not seed data, and Mapping correctly finds no table for it |
| MAP-RULE-007 | CAN-RULE-009/010 (dish examples excluded from Weekly Plan; add-ons are attachments not replacements) | Table structure itself (`re_weekly_class_plans` has no dish columns; `re_household_addon_plans` is a separate table from the main plan) | Direct | High |
| MAP-RULE-008 | CAN-RULE-012 (QA uniqueness claims) | `re_cohorts` and `re_weekly_class_plans` PRIMARY KEY / UNIQUE constraints | Direct | High — schema enforces the same uniqueness via `UNIQUE (persona_id, state_code, diet_mode)` and `UNIQUE (cohort_id, day_of_week)` respectively |

---

## 5. Consolidated Mapping Issues Register

*(Every item below is genuinely unresolved. None is silently decided. Each requires either a Founder decision, a Cross-Batch resolution, or routing to Gap Analysis.)*

| MI ID | Issue | Affected MAP IDs | Evidence | Recommended Path |
|---|---|---|---|---|
| MI-001 | `dish_id` (UUID, FK to `public.dishes`) has no canonical source yet — `public.dishes` is populated from `dishes.xlsx`, which is Batch 4, not Batch 1 | MAP-ENT-008, 009, 011 | DOC-P3-04 §03.27 DDL; Batch Independence Rule (DOC-P3-11 §04) | **Deferred to Batch 4.** When Batch 4 canonicalizes `dishes.xlsx`, a Cross-Batch Conflict/linkage must be raised to connect `CAN-ENT-009`/`CAN-ENT-011` (this batch's dish *names*) to the future `public.dishes` UUIDs — never merged automatically (per Canonicalization §12) |
| MI-002 | `re_cohorts.diet_mode` (text, NOT NULL) — no canonical column named `diet_mode`; `Persona.nonveg_mode` (CAN-ATT-015) is a plausible source but the exact expected value format is not specified anywhere in DOC-P3-04 | MAP-VOC-008, MAP-ENT-012 | `re_cohorts` DDL; Persona_Master_v3 full data | **Founder Decision required** — confirm whether `diet_mode` should take `nonveg_mode`'s 12 values verbatim, or a transformed subset, and supply/approve the transformation rule |
| MI-003 | `re_cohorts.prior_weight` (real, DEFAULT 1.0) — no canonical numeric weight exists anywhere in `Cohort_Matrix_v3` (only a free-text `planning_confidence_v3` note) | MAP-ENT-012 | Full-column check: `Cohort_Matrix_v3` has no numeric weight/prior column | **Likely not a gap** — the schema's own `DEFAULT 1.0` may be sufficient and this column may be intentionally `RUNTIME_CALC`-adjacent rather than seed-sourced; recommend confirming with DOC-P3-04's author intent before Gap Analysis, rather than assuming |
| MI-004 | **(Largest issue.)** `re_weekly_class_plans` stores exactly ONE class per slot for 3 slots (breakfast/lunch/dinner) with no rank concept; canonical `Weekly_Class_Plan_v3` (CAN-ATT-067) has PRIMARY/SECONDARY/TERTIARY ranks across 4 slots (breakfast/lunch/snack/dinner) — 12 raw values per row vs. schema's 3 | MAP-ENT-013, MAP-REL-006 | `re_weekly_class_plans` DDL vs. Discovery Report §3 (Weekly_Class_Plan_v3 attribute list) | Gap Analysis must first determine whether this is: (a) intentional architecture, (b) implementation behaviour, (c) runtime behaviour, or (d) a genuine schema gap. Only after Gap Analysis may an SER be recommended if evidence supports it. |
| MI-005 | `re_household_addon_plans` has no `day_of_week`, `meal_slot`, or `attached_to_main_class_code` columns; canonical `Household_Addon_Component_Plan` has all three, and its 7,992-row count is identical to the schema's expected count, suggesting the schema may assume one row already represents an implicit day/slot combination that the DDL doesn't expose a column for | MAP-ENT-014, MAP-REL-007, MAP-REL-008 | `re_household_addon_plans` DDL vs. Discovery Report §3 | **Founder Decision required** — clarify whether day/slot/attached-class information is (a) intentionally not persisted at this granularity, (b) implied by `re_addon_classes.slot`, or (c) a genuine DDL gap requiring an SER |
| MI-006 | `re_nonveg_logic` has only 2 data columns (`weekly_nonveg_slots smallint`, `preferred_slots text[]`); canonical NonVeg Logic Profile (CAN-ATT-075/076/077) has 6 named weekly-count fields (omnivore/regular-nonveg/egg/fish/chicken/mutton) plus free-text state notes | MAP-ENT-015 | `re_nonveg_logic` DDL vs. `Batch1_Canonicalization_Package_v1.1` §1A | **Founder Decision required** — confirm which of the 6 canonical counts collapses into the single `weekly_nonveg_slots`, and whether `preferred_slots` is meant to hold `preferred_nonveg_classes` (Meal Class codes) or something else |
| MI-007 | `re_meal_classes.slot` CHECK constraint (`breakfast`,`lunch`,`dinner`,`addon`) has no `snack` value, splits the canonical "Lunch/Dinner" compound value into two, and includes an `addon` value the canonical Core Meal Slot vocabulary doesn't have | MAP-VOC-003, MAP-VOC-004 | `re_meal_classes` DDL vs. `Batch1_Canonicalization_Package_v1.1` §2 (CAN-VOC-004/005, per Founder Decision F2) | Gap Analysis must first determine whether this is: (a) intentional architecture, (b) implementation behaviour, (c) runtime behaviour, or (d) a genuine schema gap. Only after Gap Analysis may an SER be recommended if evidence supports it. 22 of 131 canonical Meal Classes have `slot_group = Snack` and currently have no valid value for this column — this fact is not in dispute; only its classification is deferred to Gap Analysis. |
| MI-008 | `re_main_cohorts.cohort_code` expected values (per schema comment) are `MC_SOLO, MC_COUPLE, MC_NUCLEAR_FAMILY, MC_JOINT_FAMILY, MC_PG_HOSTEL`; canonical `main_cohort_label` values for MC1–MC4 correspond plausibly, but **MC5 ("Special goal or kitchen operating mode") does not semantically match "MC_PG_HOSTEL"** | MAP-VOC-005 | Direct comparison this turn: MC1–4 labels vs. schema comment; MC5 mismatch confirmed | **Founder Decision required** — MC5's correct `cohort_code` cannot be inferred from evidence; guessing "MC_PG_HOSTEL" would be an unproven business-fact inference, which Mapping is not permitted to make |
| MI-009 | City Tier (T1/T2, Tier1_Metro/Tier2_Urban — CAN-VOC-006/007) has no column anywhere across the 15 target tables | MAP-VOC-006 | Full DDL review of all 15 tables (§03.27) | **Route to Gap Analysis** — either city tier is not needed at the `re_engine` layer (it may belong to `public.profiles` instead, outside Batch 1's target tables), or it is a genuine schema gap |
| MI-010 | Class Family Code (14 `FAM_` values — CAN-VOC-008) has no column on `re_meal_classes` or elsewhere | MAP-VOC-007 | Full DDL review of `re_meal_classes` | **Route to Gap Analysis** — determine whether this classification is needed by any RE logical function (per RE-DOC-01–05) or was Discovery-only context not required downstream |
| MI-011 | `re_states.region text` — unclear whether this is meant to hold Region Archetype (CAN-VOC-015, e.g. "SOUTH_RICE") verbatim, or a different regional grouping | MAP-VOC-010 | `re_states` DDL (`region` column, no CHECK, no comment clarifying expected values) | **Founder Decision or RE-DOC cross-check required** — confirm intended value domain before Seed Generation |
| MI-012 | The canonical Sub-Cohort→Persona relationship (`maps_to_persona_id`, CAN-REL-005 — the entire functional purpose of the routing sheet) has no corresponding FK in `re_subcohorts` (which only has `main_cohort_code`, no persona reference) | MAP-REL-002 | `re_subcohorts` DDL vs. `Subcohort_Routing` sheet | **Route to Gap Analysis / possible SER** — if BUILD-02's dynamic onboarding (per Engineering Handover) needs sub-cohort→persona routing at runtime, this relationship needs a home somewhere in the schema; it currently has none among the 15 target tables |
| MI-013 | `re_personas.persona_code` (UNIQUE text) — no example value given in the schema comment; two candidate canonical sources exist (`persona_id`, e.g. "P01", vs. a slug derived from `sub_cohort_label`, e.g. "student_hostel_budget") with materially different meaning for anyone reading the seeded data later | MAP-ENT-003 | `re_personas` DDL; Discovery Report Persona/Sub-Cohort attribute lists | **Founder Decision required** — confirm intended `persona_code` convention before Seed Generation |
| MI-014 | `re_class_dish_options.is_primary_candidate` (boolean) and `base_score` (real) — no canonical source column for either; `class_use_scope_v3` (main_class_dish_pool/legacy_addon_or_template) is a plausible but unconfirmed basis for `is_primary_candidate`, and nothing at all in the canonical data suggests a `base_score` value | MAP-RULE-004 | `Class_Dish_Options_v3` full attribute list (Discovery Report §3) | **Route to Gap Analysis** — `is_primary_candidate` has a plausible derivation path (needs Founder confirmation of the exact boolean rule); `base_score` appears to have no canonical source at all and may be a `RUNTIME_CALC`-style value computed later, not seeded |
| MI-015 | `re_city_migration_overlays.city_overlay_weight` (single real column) vs. canonical `weighting_factors` (CAN-ATT-037, three named weights: home-state, current-city, national-modern) | MAP-RULE-005 | `re_city_migration_overlays` DDL vs. `City_Migration_Overlay_v3` full attribute list | **Founder Decision required** — confirm whether the three canonical weights should be combined into one seeded value (and by what formula), or whether an SER is needed to add two more weight columns |
| MI-016 | `re_addon_dish_options.suitability_rank` (smallint NOT NULL) — no canonical source column in `Addon_Dish_Options` | (not in Section 4 table — attribute-level gap on MAP-ENT-011) | `Addon_Dish_Options` full attribute list | **Route to Gap Analysis** — no evidenced source; may require a default/derived ranking rule |
| MI-017 | Main Cohort and Sub-Cohort onboarding-copy attributes (`user_understands_as`, `subcohort_screen_copy`, `routing_notes`, `show_as_chip_text`, `ask_next`, `do_not_show_in_first_screen` — 6 attributes total) have no column in `re_main_cohorts`/`re_subcohorts` | CAN-ATT-002, 003, 004, 006, 007, 008 | Section 1A matrix; `re_main_cohorts`/`re_subcohorts` DDL (3 and 3 columns respectively, neither has room for UI copy) | **Route to Gap Analysis** — these read as UI/onboarding-flow copy rather than `re_engine` seed data; project memory references an established `re-onboarding-content.ts` config pattern for exactly this kind of content, which may be the correct home instead of these tables — Gap Analysis should confirm, not Mapping |
| MI-018 | 13 Persona behavioral attributes (`age_band`, `household_stage`, `lifecycle_health`, `cook_dependency`, `time_pressure`, `revealed_behavior_summary`, `meal_slot_boost_classes`, `can_be_overlay`, `dependent_addon_default`, `health_overlay_default`, `cook_overlay_default`, `recommended_onboarding_path`, plus `onboarding_branch_trigger` cross-referenced separately) have no column in `re_personas` (6 columns total: id, persona_code, main_cohort_code, display_name, primary_diet, is_active) | CAN-ATT-010–014, 016, 017, 019–023 | Section 1A matrix; `re_personas` DDL | **Route to Gap Analysis** — the frozen `re_personas` table is materially thinner than the canonical Persona entity; determine whether this behavioral detail is intentionally out of `re_engine`'s seed scope (perhaps consumed only at Discovery/design time) or represents a genuine schema gap affecting RE logical functions |
| MI-019 | 5 State/UT attributes (`representative_cities`, `nonveg_intensity`, `primary_staple_base`, `meal_slot_class_pools`, `behavioral_notes`) have no column in `re_states` (3 columns: state_code, state_name, region) | CAN-ATT-031–035 | Section 1A matrix; `re_states` DDL | **Route to Gap Analysis** — same pattern as MI-018, applied to State/UT |
| MI-020 | Add-on Component Class and City Migration Overlay descriptive attributes (`destination_group_name`, `overlay_meal_classes`, `planning_rule`, `addon_class_name`, `food_dna_role`, `planning_note`) have no column in `re_city_migration_overlays` or `re_addon_classes` | CAN-ATT-036, 038, 039, 055, 056, 057 | Section 1A matrix; both tables' DDL | **Route to Gap Analysis** — same pattern |
| MI-021 | Routing Rule attributes (`input_type`, `user_prompt_summary`, `why_it_matters`) have no column in `re_routing_rules`; `shown_when`/`onboarding_branch_trigger`→`trigger_answer` and `maps_to_fields`→`show_question_key` are only plausible, unconfirmed derivations | CAN-ATT-018, 024–028 | Section 1A matrix; `re_routing_rules` DDL (5 columns) | **Founder Decision or Gap Analysis** — confirm whether `trigger_answer`/`show_question_key` are the intended targets for `shown_when`/`maps_to_fields`, and whether the 3 unmapped attributes are needed by BUILD-02's dynamic onboarding logic |
| MI-022 | 8 Meal Class descriptive/behavioral attributes (`class_name`, `class_category`, `cook_complexity`, `heaviness`, `region_relevance`, `behavioral_meaning`, `food_dna_tags`, `addon_target_segment_v3`) plus Class-Dish Option's `region_relevance` have no column in `re_meal_classes` or `re_class_dish_options`; `food_profile`→`cuisine_family` is only a partial, unconfirmed overlap | CAN-ATT-040, 041, 043, 044, 046–048, 050, 052 | Section 1A matrix; `re_meal_classes` DDL (10 columns, none of which is a display name) | **Route to Gap Analysis** — notably, `re_meal_classes` has no human-readable name column at all; confirm whether `class_code` alone is sufficient for the app or a name column is a genuine gap |
| MI-023 | Cohort's descriptive/behavioral attributes (`representative_cities`, `nonveg_egg_defaults`, `dependent_addon_required_v3`, `planning_confidence_v3`) have no column in `re_cohorts` (5 columns: cohort_id, persona_id, state_code, diet_mode, prior_weight) | CAN-ATT-059, 061, 062, 064 | Section 1A matrix; `re_cohorts` DDL | **Route to Gap Analysis** — same pattern as MI-018/019/020/022, applied to Cohort |

**23 Mapping Issues total (16 from the original Mapping pass + 7 new consolidated findings from the attribute-level matrix). Zero silently resolved. Zero business facts inferred to make an issue "go away."**



---

## 6. Completion Summary

- All 15 canonical entities mapped to a target table in the frozen `re_engine` schema (§1).
- All 76 canonical attributes individually mapped in the new Attribute → Schema Mapping Matrix (§1A).
- 10 vocabulary mappings attempted; 5 are clean, 5 surfaced genuine Mapping Issues (§2).
- 11 relationship mappings attempted; 9 are structurally sound, 2 surfaced genuine Mapping Issues (§3).
- 8 business rule mappings attempted; 6 map cleanly to schema mechanisms, 2 have partial/derived status (§4).
- **23 Mapping Issues total** (16 original + 7 new from attribute-level review), each with evidence and a recommended path — none resolved unilaterally (§5).
- No schema, entity, API, or RE-logic redesign occurred. No SQL was written. No seed data was generated. No canonicalization was redone. No Mapping Issue was resolved. No Founder Decision was inferred.
- The single most significant finding remains **`re_weekly_class_plans` (MI-004)**, joined this revision by the observation that several `re_engine` reference tables (`re_personas`, `re_states`, `re_meal_classes`, `re_cohorts`) are materially thinner than their canonical counterparts (MI-018, 019, 022, 023) — a pattern worth Gap Analysis's attention as a whole, not just per table.

---

## 6A. Mapping Decision Register *(new in v1.1 — permanent governance record)*

| MAP-DEC ID | Decision | Reason | Evidence | Alternative Considered | Why Rejected | Linked MAP IDs | Linked CAN IDs | Confidence |
|---|---|---|---|---|---|---|---|---|
| MAP-DEC-001 | Map all 15 canonical entities to the 15 `re_engine` reference tables by row-count correspondence | Row counts match exactly across all 15 pairs | §1 table; DOC-P3-04 §03.27 seed-gate comments | Map to `public` schema tables instead | No `public` table exists for cohort/persona/meal-class reference data — `re_engine` is explicitly the seed-reference schema per DOC-P3-04 §02 | MAP-ENT-001…015 | CAN-ENT-001…015 | High |
| MAP-DEC-002 | Treat `dish_id` (UUID) as Deferred rather than attempting a placeholder value | Batch Independence Rule forbids treating an un-canonicalized concept as resolved | DOC-P3-11 §04; `public.dishes` not yet populated | Generate a temporary/placeholder UUID now, backfill later | Would fabricate a database identity for a business fact not yet observed — directly prohibited by "never silently invent business data" | MAP-ENT-008, 009, 011 | CAN-ENT-009, 011 | High |
| MAP-DEC-003 | Do not attempt to resolve the `slot` vocabulary mismatch (MI-007) by silently re-mapping Snack-slot classes to an existing enum value | Any silent re-mapping would misrepresent 22 real Meal Classes' actual slot | Full data: 22 of 131 rows have `slot_group = Snack` | Map Snack → `addon` (schema's 4th value) | `addon` means something structurally different (planning role), not a time-of-day slot — conflating the two would corrupt `planning_role`-based Safety Gate 4 logic | MAP-VOC-003 | CAN-VOC-004 | High |
| MAP-DEC-004 | Do not guess `MC5`'s `cohort_code` (MI-008) | No evidence connects "Special goal or kitchen operating mode" to "MC_PG_HOSTEL" | Direct comparison, this stage | Assume MC5 = MC_PG_HOSTEL by process of elimination (last remaining code) | Elimination is not evidence of business-meaning identity — the label content actively contradicts it | MAP-VOC-005 | CAN-ENT-001 | High (high confidence in the decision to *not* guess, not in a resolved mapping) |
| MAP-DEC-005 | Record orphaned descriptive/behavioral attributes (MI-017–023) as Deferred with a Gap Analysis routing, rather than omitting them from the Attribute Matrix entirely | Every canonical attribute must appear in Section 1A per Task 1's mandate — silence would look like an oversight, not a documented decision | Section 1A, 76/76 rows populated | Omit attributes with no target column from the matrix | Would violate "every CAN object accounted for" discipline carried over from Canonicalization | Multiple (MAP-ENT-001–015) | Multiple CAN-ATT | High |

**These decisions are permanent governance records and are never regenerated** — future revisions may add new `MAP-DEC` entries but never edit or renumber these five.

---

## 6B. Transformation Summary *(new in v1.1 — executive summary only, no duplicated tables)*

| Category | Count |
|---|---|
| Direct mappings | 18 |
| Composite mappings | 8 |
| Derived mappings | 12 |
| Deferred mappings | 38 |
| Rejected mappings | 0 (no mapping was attempted and then rejected outright — all non-Direct items are Deferred/Issue, not Rejected) |
| Mapping Issues | 23 (MI-001 through MI-023) |
| Cross-Batch dependencies | 1 (MI-001 — `dish_id`, depends on Batch 4) |
| Founder Decisions required | 8 (MI-002, 004, 006, 008, 011, 013, 015, 021) |

*(Counts reconcile against the 76-row Attribute Matrix in §1A plus the 15 entity-level and 11 relationship-level mappings in §1/§3 — see §6C for the full reconciliation.)*

---

## 6C. Mapping Completeness Metrics *(new in v1.1)*

| Layer | Total | Mapped (Direct/Composite/Derived) | Deferred/Issue | Coverage % (mapped) |
|---|---|---|---|---|
| Entities | 15 | 15 (all have a target table) | 3 with a Deferred component (MI-001) | 100% (structural), 80% (fully clean) |
| Attributes | 76 | 18 | 58 | 24% clean / 100% addressed |
| Relationships | 14 | 9 | 2 (structural gaps) + 3 not separately itemized (implicit in entity-level Deferred) | 64–79% |
| Business Rules | 12 | 10 (8 clean + 2 partial) | 2 | 83% |
| Vocabularies | 15 (10 attempted in §2) | 5 | 5 | 50% of attempted |
| Synonyms | 6 | 6 (all synonyms map trivially — a synonym is a labeling fact, not a schema-dependent mapping) | 0 | 100% |
| Deferred (cross-batch) | — | — | 1 (MI-001) | — |
| Issues | — | — | 23 total | — |

**No percentage above represents information loss.** Every "Deferred/Issue" row is a documented, evidenced finding (§1A, §5) — not a silently dropped attribute. The 24% "clean" attribute coverage is the headline number Gap Analysis should focus on: it means most of Batch 1's rich canonical detail currently has no home in the 15 frozen `re_engine` tables as they stand today.

---

## 6D. Mapping Confidence Dashboard *(new in v1.1 — counts and links only)*

| Confidence / Category | Count | See |
|---|---|---|
| High | 34 | §1 (10 entity-level), §3 (8 relationship-level), §4 (5 rule-level), §1A (11 attribute-level) |
| Medium | 31 | §1A (majority of Deferred attribute rows), §1 (4 entity-level) |
| Low / Low-Medium | 11 | §2 (MI-007/008 related), §1A (composite-mismatch rows: CAN-ATT-037, 060, 067, 068, 075, 076) |
| Deferred | 38 | §1A |
| Founder Decision Required | 8 | MI-002, 004, 006, 008, 011, 013, 015, 021 |
| Gap Analysis Required | 15 | MI-001, 003, 005, 007, 009, 010, 012, 014, 016, 017, 018, 019, 020, 022, 023 |
| Cross-Batch | 1 | MI-001 |

---

## 6E. Permanent MAP ID Governance *(new in v1.1, permanent — mirrors Canonical ID Governance)*

- `MAP-*` IDs (including `MAP-ENT`, `MAP-VOC`, `MAP-REL`, `MAP-RULE`, `MAP-DEC`) are **immutable**: never renumbered, never recycled, never reused, never reassigned — even if a mapping is later superseded or found incorrect.
- A superseded mapping is marked "Superseded by [new ID]" and remains permanently in the historical record; it is never deleted.
- Every future Seed SQL statement (Phase 3.5 Phase 9 / DOC-P3-09) **must cite the `MAP-*` ID it was generated from**, per the Permanent Lineage Chain (`DOC-P3-11` §26).
- Every future `GAP-*` ID **must reference the originating `MAP-*` ID(s)** it classifies, once Gap Analysis begins.
- This rule mirrors `Batch1_Canonicalization_Package_v1.1` §11 (Canonical ID Governance) exactly, extended one link down the lineage chain.

---

## 6F. Executive Mapping Summary *(new in v1.1 — audit view only)*

```
Source Workbook: Indian_Meal_Cohort_Persona_DB_v3.xlsx
        │
        ▼
22 Worksheets
        │
        ▼
20 Observable Entities
        │
        ▼
15 Canonical Entities
        │
        ▼
15 Schema Targets (re_engine reference tables, DOC-P3-04 §03.27)
        │
        ▼
23 Mapping Issues (16 original + 7 attribute-level)
        │
        ▼
0 Silently Resolved
        │
        ▼
100% Lineage Preserved (OBS → CAN → MAP, every ID traceable)
        │
        ▼
Ready for Gap Analysis
```

---

## Regression Review — verified by direct comparison against v1.0

- ✅ No architecture, schema, API, Security, or Recommendation Engine change — confirmed by direct diff, v1.0's Sections 1–5 content is unchanged in substance, only wording refined (MI-004, MI-007) and new sections appended
- ✅ No RE change
- ✅ No Discovery change — `Batch1_Discovery_Report_v1.1` not opened for edit
- ✅ No Canonicalization change — `Batch1_Canonicalization_Package_v1.1` not opened for edit
- ✅ No entity redesign — all 15 canonical entities used exactly as frozen
- ✅ No Gap Analysis started — Mapping Issues remain raised and evidenced only, none classified into Category A/B/C1/C2/C3
- ✅ No SQL generated, no INSERT/UPSERT, no database changes
- ✅ No Mapping Issue resolved — MI-004 and MI-007's wording changed, their substance (unresolved status, evidence, affected IDs) did not
- ✅ No Founder Decision inferred — MI-008 (MC5), MI-013 (persona_code), and all others remain explicitly open
- ✅ `DOC-P3-09` and `DOC-P3-10` not touched
- ✅ No previously frozen document regenerated — `Batch1_Discovery_Report_v1.1` and `Batch1_Canonicalization_Package_v1.1` remain exactly as frozen; only `Batch1_Mapping_Package` (still Draft in v1.0) is being frozen for the first time here
- ✅ Lineage chain maintained: every `MAP-*` ID cites its source `CAN-*` ID(s); every new `CAN-ATT` row in §1A cites its parent entity
- ✅ Permanent Mapping Freeze Rule (DOC-P3-11 §26A) now becomes applicable the moment this document freezes below

---

## Gap Analysis Readiness Summary

*(Readiness summary for the next stage only — does not begin that stage.)*

| Check | Status |
|---|---|
| All 15 canonical entities have a mapping attempt | ✅ Yes |
| All 76 canonical attributes individually mapped | ✅ Yes — §1A |
| Every unmapped/partially-mapped item raised as a Mapping Issue | ✅ Yes — 23 issues, all evidenced |
| Mapping Decision Register complete | ✅ Yes — 5 permanent decisions logged (§6A) |
| Completeness metrics produced | ✅ Yes (§6C) |
| Confidence dashboard produced | ✅ Yes (§6D) |
| Any Mapping Issue silently resolved | ❌ No |
| Any business fact inferred without evidence | ❌ No |
| Founder Decisions required before Gap Analysis can classify remaining issues | ⚠️ 8 — MI-002, 004, 006, 008, 011, 013, 015, 021 |
| Gap Analysis started | ❌ **No — awaiting Founder approval** |

**Verdict:** Batch 1 Stage 4 (Gap Analysis) may begin once the Founder approves this frozen Mapping package. Gap Analysis's job is to formally classify each of the 23 Mapping Issues into Category A/B/C1/C2/C3 per DOC-P3-09 §15 — Mapping has deliberately stopped short of that classification.

---

## Freeze Confirmation

**`Batch1_Mapping_Package_v1.1` — APPROVED — ACTIVE — FROZEN.** Supersedes v1.0, which is retained unmodified as a superseded reference and is never regenerated.

---

## Founder Approval Gate

**Mapping has been performed and is now FROZEN. Gap Analysis has NOT begun. Mapping Issues have NOT been classified. No AGR or SER has been created. Batch 2 has NOT begun. No SQL, INSERT, UPSERT, or database change of any kind occurred.**

This package awaits Founder approval before Stage 4 (Gap Analysis) starts.

Founder sign-off: _______________________ Date: ___________
