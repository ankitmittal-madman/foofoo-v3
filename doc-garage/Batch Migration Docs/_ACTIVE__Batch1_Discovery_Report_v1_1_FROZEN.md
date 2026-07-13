# Phase 3.5 — Phase 3: Knowledge Discovery — Batch 1
## Consolidated Deliverable Set (v1.1)

**Governed by:** `[ACTIVE]_DOC-P3-09_Knowledge_Integration_Governance_v1.0`
**Operationalized by:** `[ACTIVE]_DOC-P3-10_Seed_Data_Integration_Framework_v1.1`
**Execution audit trail:** `[ACTIVE]_DOC-P3-11_Discovery_Execution_Register_v1.1` (companion document)
**Batch scope:** `Indian_Meal_Cohort_Persona_DB_v3.xlsx` **ONLY** — no other dataset participates in this batch.
**Discovery boundary applied:** documents only what is explicitly observable in the workbook (column headers, distinct/enumerated values, explicit textual join-rule statements). **No canonicalization, mapping, normalization, inference, transformation, SQL, or seed data generation performed. No conflicts resolved. No concepts merged.**
**Version:** 1.1 (finalized in place per Founder instruction — Founder Decisions F1/F2 recorded below, document now FROZEN; no further content change)
**Date:** 2026-07-02
**Status:** APPROVED — ACTIVE — FROZEN

**Founder Decision Closure (recorded 2026-07-02):**
- **F1 — CLOSED.** Decision: the omission of `Weekly_Plan_Normalization_Note` and `Weekly_Plan_Join_Rules` from `Data_Dictionary_v3` is a workbook documentation omission only. Both remain valid workbook sheets and participated fully in Discovery per their actual content. No correction to the source workbook is required.
- **F2 — CLOSED.** Decision: maintain **two** canonical vocabularies — Vocabulary A (Core Meal Slot: Breakfast, Lunch/Dinner, Dinner, Snack) and Vocabulary B (Add-on Slot Applicability: the compound values, preserved exactly as authored — not flattened, split, normalized, or expanded into multi-select during Canonicalization). Any transformation needed for database loading belongs to Mapping/Transformation Rules, not Canonicalization.

**Batch 1 Stage 1 (Discovery) is now COMPLETE. This document is FROZEN. It is not reopened except via a Cross-Batch Conflict raised by a later batch, per DOC-P3-11 §22.**

**Revision Notice (v1.0 → v1.1):**
1. **Founder Review Register (Section 8) re-evaluated.** Items F3, F4, and F5 are reclassified from "Founder Review Item" to **"Canonicalization Verification Task"**, each backed by new full-dataset evidence gathered this turn (not present in v1.0, which relied on sampled data). F1 and F2 remain genuine Founder Decisions — neither can be resolved from observable evidence alone.
2. **Language tightened.** All hedging/interpretive terms ("possible," "assumed," "expected" used speculatively) replaced with direct observational statements. No information was removed — only precision was improved.
3. Nothing was silently changed: the original v1.0 conflict/review items are preserved below with a note showing exactly what evidence caused each reclassification.

---

## 1. Batch 1 Discovery Report

**Method:** every one of the 22 worksheets was read in full (all rows, all columns). For each column, distinct-value cardinality was computed; where cardinality was low, the full set of distinct values is recorded as an observed enumeration. Where cardinality was high, a small sample is recorded for identification purposes only — no attempt was made to catalogue every high-cardinality value (that belongs to Canonicalization).

**Per-sheet business purpose (as explicitly stated in the workbook itself — README, Sources_v3, Data_Dictionary_v3 — not inferred by Claude):**

| Sheet | Stated Purpose (verbatim or near-verbatim from source) |
|---|---|
| README | Workbook overview: "Class-first, cohort-hierarchy and add-on-aware cold-start database for Indian meal planning." |
| Main_Cohort_Hierarchy | 5 user-facing onboarding cards (per `Data_Dictionary_v3`) |
| Subcohort_Routing | Sub-cohort chips mapping to detailed personas (per `Data_Dictionary_v3`) |
| Persona_Master_v3 | Detailed persona priors after routing (per `Data_Dictionary_v3`) |
| Routing_Rules_v3 | Onboarding question sequencing (observed: `rule_id`, `shown_when`, `input_type`, `user_prompt_summary`) |
| State_Profile_v3 | Home-state signature class pools (per `Data_Dictionary_v3`) |
| City_Migration_Overlay_v3 | Blend home food and current city lifestyle (per `Data_Dictionary_v3`) |
| Meal_Class_Master_v3 | Class-first planning taxonomy (per `Data_Dictionary_v3`) |
| Meal_Class_Overlap_Resolution | Explicit cleanup list — classes moved out of main weekly rotation |
| Class_Dish_Options_v3 | Exhaustive dishes under each meal class (per `Data_Dictionary_v3`) |
| Addon_Component_Class_Master | Member-specific add-ons/sides/swaps (per `Data_Dictionary_v3`) |
| Addon_Dish_Options | Dish-level detail under each add-on class |
| Cohort_Matrix_v3 | State/persona protein frequency priors + full cohort cross-product (per `Data_Dictionary_v3`) |
| Weekly_Class_Plan_v3 | One-week class plan per cohort (per `Data_Dictionary_v3`) |
| Weekly_Plan_Normalization_Note | Explains why dish examples were deliberately removed from the weekly plan sheet |
| Weekly_Plan_Join_Rules | Explicit join instructions for consumers of the weekly plan |
| Household_Addon_Component_Plan | Normalized add-on schedule (per `Data_Dictionary_v3`) |
| NonVeg_Logic_v3 | State/persona protein frequency priors and guardrails |
| DB_Implementation_v3 | Proposed table/primary-key mapping guidance (documentation, per Founder's Special Rules) |
| Sources_v3 | External research sources used to build the workbook (provenance) |
| QA_Checks_v3 | Self-reported QA pass/fail results (QA/Validation) |
| Data_Dictionary_v3 | Sheet-by-sheet index of the workbook itself (documentation) |

---

## 2. Observable Entity Inventory

Entities are recorded **per sheet of occurrence** — recurrence of the same identifier pattern across sheets is noted as an **observation**, not asserted as confirmed identity (that determination belongs to Canonicalization).

| Candidate Entity | Primary Identifying Column(s) | Sheets Where Observed | Occurrences |
|---|---|---|---|
| Main Cohort | `main_cohort_id` | Main_Cohort_Hierarchy, Subcohort_Routing, Persona_Master_v3, Cohort_Matrix_v3 | 4 sheets |
| Sub-Cohort | `sub_cohort_id` | Subcohort_Routing, Persona_Master_v3, Cohort_Matrix_v3 | 3 sheets |
| Persona | `persona_id` | Subcohort_Routing (`maps_to_persona_id`), Persona_Master_v3, Cohort_Matrix_v3, Weekly_Class_Plan_v3, Household_Addon_Component_Plan | 5 sheets |
| Routing Rule | `rule_id` | Routing_Rules_v3 | 1 sheet |
| State/UT | `state_id` / `state_ut` | State_Profile_v3, Cohort_Matrix_v3, NonVeg_Logic_v3, City_Migration_Overlay_v3 (`origin_state_ut`) | 4 sheets |
| City Migration Overlay | `origin_state_ut` + `destination_group_code` | City_Migration_Overlay_v3 | 1 sheet |
| Meal Class | `meal_class_code` | Meal_Class_Master_v3, Meal_Class_Overlap_Resolution, Class_Dish_Options_v3, State_Profile_v3 (embedded in pool strings), Weekly_Class_Plan_v3 (embedded in primary/secondary/tertiary columns), Cohort_Matrix_v3 (embedded), Household_Addon_Component_Plan (`attached_to_main_class_code`) | 7 sheets (3 as primary key, 4 as embedded reference) |
| Meal Class Family | `class_family_code` | Meal_Class_Master_v3 | 1 sheet |
| Class-Dish Option | `dish_option_id` | Class_Dish_Options_v3 | 1 sheet |
| Dish (name only, in this workbook) | `dish_name` | Class_Dish_Options_v3, Meal_Class_Master_v3 (`example_dishes`, semicolon-delimited list) | 2 sheets |
| Add-on Component Class | `addon_class_code` | Addon_Component_Class_Master, Addon_Dish_Options, Weekly_Class_Plan_v3 (4 slot-specific addon-code columns), Household_Addon_Component_Plan | 4 sheets |
| Add-on Dish Option | `addon_dish_option_id` | Addon_Dish_Options | 1 sheet |
| Cohort (state × tier × persona) | `cohort_id` | Cohort_Matrix_v3, Weekly_Class_Plan_v3 (referenced), Household_Addon_Component_Plan (referenced) | 3 sheets |
| Weekly Plan Day | `plan_day_id` | Weekly_Class_Plan_v3 | 1 sheet |
| Household Addon Plan Entry | `addon_plan_id` | Household_Addon_Component_Plan | 1 sheet |
| NonVeg Logic Profile | `state_ut` (as key) | NonVeg_Logic_v3 | 1 sheet |
| DB Implementation Note | `table_name` | DB_Implementation_v3 | 1 sheet (documentation/mapping guidance only) |
| Source Reference | `source_id` | Sources_v3 | 1 sheet (provenance only) |
| QA Check | `check_id` | QA_Checks_v3 | 1 sheet (QA/validation only) |
| Data Dictionary Entry | `sheet_name` | Data_Dictionary_v3 | 1 sheet (documentation only — see Discovery Conflict Register, item 1) |

---

## 3. Observable Attribute Inventory

Full column lists per sheet (already captured structurally in the Phase 2 Worksheet Inventory) are reproduced here with cardinality class, since attribute-level cardinality is a Discovery-stage observation, not a Phase 2 structural fact.

| Sheet | Attribute Count | Low-Cardinality (enumerated) Attributes | High-Cardinality Attributes |
|---|---|---|---|
| README | 2 | item, details | — |
| Main_Cohort_Hierarchy | 5 | main_cohort_id, main_cohort_label, user_understands_as, subcohort_screen_copy, routing_notes | — |
| Subcohort_Routing | 9 | main_cohort_id, main_cohort_label, ask_next, do_not_show_in_first_screen | sub_cohort_id, sub_cohort_label, maps_to_persona_id, persona_name, show_as_chip_text |
| Persona_Master_v3 | 22 | time_pressure, nonveg_mode, main_cohort_id, can_be_overlay, health_overlay_default, cook_overlay_default | persona_id, persona_name, age_band, household_stage, lifecycle_health, cook_dependency, revealed_behavior_summary, bf/ld/sn/dn_boost_classes, onboarding_branch_trigger, sub_cohort_id, sub_cohort_label, dependent_addon_default, recommended_onboarding_path |
| Routing_Rules_v3 | 6 | rule_id, shown_when, input_type, user_prompt_summary, why_it_matters, maps_to_fields | — |
| State_Profile_v3 | 15 | region_archetype, nonveg_intensity, primary_staple_base, breakfast/lunch/dinner/weekend/snack/nonveg_class_pool, planning_note_v3 | state_id, state_ut, tier1/tier2 city columns, behavioral_notes |
| City_Migration_Overlay_v3 | 11 | destination_group_code, destination_group_name, home_state/current_city/national_modern weight columns, overlay_meal_classes, planning_rule, v3_usage_note, example_mp_in_mumbai | origin_state_ut, example_readout |
| Meal_Class_Master_v3 | 23 | slot_group, diet_type, weekday/weekend_fit, cook_complexity, heaviness, primary_base, cooking_methods, texture, richness, class_family_code, planning_role_v3, allowed_as_weekly_primary_v3, addon_target_segment_v3, overlap_resolution_v3, db_use_note_v3 | meal_class_code, class_name, class_category, example_dishes, region_relevance, behavioral_meaning, food_dna_tags |
| Meal_Class_Overlap_Resolution | 7 | old_issue, v3_resolution, allowed_as_weekly_primary_v3 | meal_class_code, class_name, replacement_logic, addon_target_segment |
| Class_Dish_Options_v3 | 11 | diet_type, slot_group, usage_note, source_logic, class_use_scope_v3, join_rule_v3 | dish_option_id, meal_class_code, meal_class_name, dish_name, region_relevance |
| Addon_Component_Class_Master | 8 | slot_group, diet_type | addon_class_code, target_member_segment, addon_class_name, food_dna_role, example_dishes, planning_note |
| Addon_Dish_Options | 8 | slot_group, diet_type, usage_note | addon_dish_option_id, addon_class_code, addon_class_name, dish_or_component_name, target_member_segment |
| Cohort_Matrix_v3 | 38 | city_tier_code, city_tier, main_cohort_id, time_pressure, nonveg_mode, nonveg/egg_meals_per_week_default, dependent_addon_required_v3, health/cook_overlay_default, household_addon_logic, main_meal_vs_addon_rule_v3, planning_confidence_v3, join_to_dish_options | cohort_id, state_id, state_ut, representative_cities, sub_cohort_id, persona_id, age_band, household_stage, lifecycle_health, cook_dependency, all *_class_mix columns, dependent_member_segments_v3, state_signature_notes, join_to_weekly_plan, cohort_display_name_v3 |
| Weekly_Class_Plan_v3 | 23 | day_of_week, weekday_weekend, all 4 *_addon_class_code columns, qa_mapping_status | plan_day_id, cohort_id, persona_id, all primary/secondary/tertiary class columns, scheduled_nonveg_or_egg_slot |
| Weekly_Plan_Normalization_Note | 1 | note | — |
| Weekly_Plan_Join_Rules | 2 | need, join_rule | — |
| Household_Addon_Component_Plan | 15 | city_tier, day_of_week, meal_slot, component_not_replacement_note | addon_plan_id, cohort_id, state_ut, persona_id, persona_name, target_member_segment, addon_class_code, addon_class_name, addon_examples, attached_to_main_class_code, cooking_logic |
| NonVeg_Logic_v3 | 13 | nonveg_intensity, default_omnivore/regular_nonveg/egg/fish/chicken/mutton meals-per-week columns, guardrail, v3_planning_change, weekly_schedule_note | state_ut, preferred_nonveg_classes, state_notes |
| DB_Implementation_v3 | 5 | table_name, primary_key, purpose, important_columns, notes | — (all 10 rows enumerated, documentation) |
| Sources_v3 | 5 | source_id, source_name, url, used_for, confidence_note | — (all 7 rows enumerated, provenance) |
| QA_Checks_v3 | 4 | check_id, check_name, status, details | — (all 7 rows enumerated, QA) |
| Data_Dictionary_v3 | 3 | — | sheet_name, row_count_or_scope, description (20 rows) |

---

## 4. Observable Relationship Inventory

Only relationships **explicitly stated in the workbook's own text or directly matching column names** are recorded. No relationship was inferred from naming similarity alone.

| # | Source | Target | Basis (explicit statement / matching column) |
|---|---|---|---|
| R1 | `Weekly_Class_Plan_v3.cohort_id` | `Cohort_Matrix_v3.cohort_id` | Explicit — stated in `Weekly_Plan_Join_Rules` and `Cohort_Matrix_v3.join_to_weekly_plan` |
| R2 | `Weekly_Class_Plan_v3.*_primary_class` / `*_secondary_class` / `*_tertiary_class` | `Class_Dish_Options_v3.meal_class_code` | Explicit — stated in `Weekly_Plan_Join_Rules` and `Class_Dish_Options_v3.join_rule_v3` |
| R3 | `Weekly_Class_Plan_v3.*_addon_class_code` | `Addon_Dish_Options.addon_class_code` | Explicit — stated in `Weekly_Plan_Join_Rules` |
| R4 | `Cohort_Matrix_v3.join_to_dish_options` | `Class_Dish_Options_v3.meal_class_code` / `Addon_Dish_Options.addon_class_code` | Explicit — stated verbatim in the column's own values |
| R5 | `Subcohort_Routing.maps_to_persona_id` | `Persona_Master_v3.persona_id` | Explicit — column name states the mapping directly |
| R6 | `Persona_Master_v3.main_cohort_id` | `Main_Cohort_Hierarchy.main_cohort_id` | Matching column name and value domain (MC1–MC5) |
| R7 | `Persona_Master_v3.sub_cohort_id` | `Subcohort_Routing.sub_cohort_id` | Matching column name and value domain |
| R8 | `Cohort_Matrix_v3.state_id` | `State_Profile_v3.state_id` | Matching column name and value domain (S01–S36) |
| R9 | `Cohort_Matrix_v3.main_cohort_id` / `sub_cohort_id` / `persona_id` | `Main_Cohort_Hierarchy` / `Subcohort_Routing` / `Persona_Master_v3` respectively | Matching column names and value domains |
| R10 | `Meal_Class_Overlap_Resolution.meal_class_code` | `Meal_Class_Master_v3.meal_class_code` | Same code namespace (`BF_`/`LD_`/`DN_`/`SN_` prefixes) — **not independently confirmed as a verbatim row match; flagged in Conflict Register item 3** |
| R11 | `Household_Addon_Component_Plan.attached_to_main_class_code` | `Meal_Class_Master_v3.meal_class_code` | Same code namespace observed in sample values (e.g. `SN_SOUTH_TIFFIN_SNACK`) |
| R12 | `Household_Addon_Component_Plan.addon_class_code` | `Addon_Component_Class_Master.addon_class_code` / `Addon_Dish_Options.addon_class_code` | Matching column name and value domain (`ADD_` prefix) |
| R13 | `NonVeg_Logic_v3.state_ut` | `State_Profile_v3.state_ut` | Matching column name and value domain |
| R14 | `DB_Implementation_v3.table_name` | (proposed) each corresponding sheet | Explicit — this sheet's stated purpose is to propose table/primary-key mapping guidance |

---

## 5. Observable Business Rule Inventory

Rules recorded **verbatim or near-verbatim** from source cells — none inferred.

| # | Rule (as stated in source) | Source |
|---|---|---|
| BR1 | "Weekly plan columns store main family meal classes only. Dishes are fetched from Class_Dish_Options_v3." | README |
| BR2 | "Dependent/lifecycle foods are not primary meal classes. They appear in add-on columns and Household_Addon_Component_Plan." | README; `Cohort_Matrix_v3.main_meal_vs_addon_rule_v3` |
| BR3 | 13 meal classes are explicitly moved out of main weekly rotation ("Moved out of main weekly rotation. Use only in Household_Addon_Component_Plan or as combo template; not a replacement for family main meal.") | `Meal_Class_Overlap_Resolution.v3_resolution` |
| BR4 | Only classes with `planning_role_v3 = MAIN_PRIMARY` and `allowed_as_weekly_primary_v3 = Y` may appear as a weekly primary/secondary/tertiary class | `Meal_Class_Master_v3` (enumerated columns); confirmed by `QA_Checks_v3` check "Weekly primary/secondary/tertiary classes are MAIN_PRIMARY only" (status PASS) |
| BR5 | "Ask explicit diet, protein types and no-meat days before activation." | `NonVeg_Logic_v3.guardrail` |
| BR6 | "Nonveg can be a primary class only for egg/nonveg personas or state-high omnivore priors; family dependent add-ons do not change diet hard constraints." | `NonVeg_Logic_v3.v3_planning_change` |
| BR7 | "User diet/religion/allergy hard filters override." | `NonVeg_Logic_v3.weekly_schedule_note`; echoed in `DB_Implementation_v3` notes |
| BR8 | City migration overlay applies three weights (`home_state_signature_weight`, `current_city_lifestyle_weight`, `national_modern_weight`) per origin-state/destination-city-group pair, and "modifies class weights, not hard filters" | `City_Migration_Overlay_v3` |
| BR9 | Weekly plan dish examples were deliberately excluded from the 20k-row sheet "to avoid class/dish mismatch and keep DB normalized" | `Weekly_Plan_Normalization_Note` |
| BR10 | Add-on components are explicitly "not a meal replacement" — attached to a main class while the main class remains as planned | `Household_Addon_Component_Plan.component_not_replacement_note`; `Addon_Dish_Options.usage_note` |
| BR11 | Two rows in `Class_Dish_Options_v3` carry a distinct `class_use_scope_v3` value (`legacy_addon_or_template` vs `main_class_dish_pool`) with different join instructions in `join_rule_v3` for each | `Class_Dish_Options_v3` |
| BR12 | QA self-checks report PASS on: cohort ID uniqueness (2,952/2,952), plan day ID uniqueness (20,664/20,664), and zero invalid references — **as stated by the source, not independently re-verified in this Discovery pass** | `QA_Checks_v3` |

---

## 6. Observable Controlled Vocabulary Inventory

| Vocabulary | Values Observed | Source Column(s) |
|---|---|---|
| Main Cohort ID | MC1, MC2, MC3, MC4, MC5 (5) | `main_cohort_id` (4 sheets) |
| Diet Type (core) | egg, mixed, nonveg, veg (4) | `Meal_Class_Master_v3.diet_type`, `Class_Dish_Options_v3.diet_type`, `Addon_Component_Class_Master.diet_type` (2 values only: mixed, veg), `Addon_Dish_Options.diet_type` (2 values only: mixed, veg) — **note: addon sheets show only 2 of the 4 core values; flagged as an observation, not a conflict** |
| Nonveg Mode | budget_default, default, egg_only, health_veg_or_default, jain, outside_nonveg, protein_nonveg, regular_nonveg, seafood, sunday_mutton, veg_default, veg_only (12) | `Persona_Master_v3.nonveg_mode`, `Cohort_Matrix_v3.nonveg_mode` |
| Region Archetype | CENTRAL_MIXED, EAST_RICE_FISH, HIMALAYAN, ISLAND_COASTAL, NORTHEAST_RICE_MEAT, NORTH_WHEAT, SOUTH_RICE, WEST_COASTAL, WEST_VEG (9) | `State_Profile_v3.region_archetype` |
| Slot Group (core, 4-value) | Breakfast, Dinner, Lunch/Dinner, Snack | `Meal_Class_Master_v3.slot_group`, `Class_Dish_Options_v3.slot_group` |
| Slot Group (compound, 7-value) | All, Breakfast/Lunch/Dinner, Breakfast/Snack, Breakfast/Snack/Dinner, Dinner, Lunch/Dinner, Lunch/Dinner/Snack | `Addon_Component_Class_Master.slot_group`, `Addon_Dish_Options.slot_group` — **flagged as a second, structurally different vocabulary; see Conflict Register item 2** |
| City Tier Code | T1, T2 | `Cohort_Matrix_v3.city_tier_code` |
| City Tier (label) | Tier1_Metro, Tier2_Urban | `Cohort_Matrix_v3.city_tier`, `Household_Addon_Component_Plan.city_tier` |
| Class Family Code | 14 values, all prefixed `FAM_` (e.g. FAM_BREAKFAST_HEALTH_PROTEIN, FAM_DAILY_DAL_SABZI_RICE_ROTI, FAM_NONVEG_PROTEIN …) | `Meal_Class_Master_v3.class_family_code` |
| Planning Role | ADDON_ONLY_NOT_PRIMARY, COMBO_TEMPLATE_NOT_PRIMARY, MAIN_PRIMARY (3) | `Meal_Class_Master_v3.planning_role_v3` |
| Destination Group Code | AHMEDABAD_SURAT, BENGALURU_HYD_CHENNAI, DELHI_NCR, GOA_COASTAL, HOME_STATE_TIER1, HOME_STATE_TIER2, KOLKATA_EAST, MUMBAI_PUNE, PAN_INDIA_PG_HOSTEL (9) | `City_Migration_Overlay_v3.destination_group_code` |
| Time Pressure | high, low, medium, very high (4) | `Persona_Master_v3.time_pressure`, `Cohort_Matrix_v3.time_pressure` |
| Day of Week | Fri, Mon, Sat, Sun, Thu, Tue, Wed (7, three-letter abbreviations) | `Weekly_Class_Plan_v3.day_of_week`, `Household_Addon_Component_Plan.day_of_week` |
| Add-on Class Code | ~24 values, all prefixed `ADD_` | `Addon_Component_Class_Master.addon_class_code` and 3 other sheets |
| Weekday/Weekend flag | Weekday, Weekend (2) | `Weekly_Class_Plan_v3.weekday_weekend` |

---

## 7. Discovery Conflict Register

*(Recorded, not resolved — resolution belongs to later stages/Founder decision.)*

| # | Conflict / Discrepancy Observed | Detail |
|---|---|---|
| C1 | `Data_Dictionary_v3` lists only **20** sheet entries, but the workbook contains **22** sheets | The two sheets absent from the dictionary listing are identified: `Weekly_Plan_Normalization_Note` and `Weekly_Plan_Join_Rules`. Whether this omission is by design or an oversight is not determinable from the data itself. Routed to Founder Review Register, item F1 (remains a Founder Decision). |
| C2 | Two distinct `slot_group` vocabularies exist in the same workbook: a 4-value set (core meal classes) and a 7-value compound set (add-on classes, including combined values like "Breakfast/Lunch/Dinner") | Every compound value's component tokens are confirmed to be members of the 4-value core set (full decomposition check performed). Whether this warrants one canonical vocabulary with multi-select representation or two separate vocabularies is a modeling decision. Routed to Founder Review Register, item F2 (remains a Founder Decision). |
| C3 | `Meal_Class_Overlap_Resolution` lists 13 `meal_class_code` values sharing the same code-prefix pattern as codes in `Meal_Class_Master_v3` | A full-set comparison (all 13 codes against all 131 Master rows, not a sample) confirms all 13 codes are present in `Meal_Class_Master_v3`. Zero codes are missing. Reclassified to Canonicalization Verification Task, item F3 (see Section 8). |
| C4 | `Class_Dish_Options_v3` (classified Master Data in Phase 2) contains a `class_use_scope_v3` column with a `legacy_addon_or_template` value alongside `main_class_dish_pool` | Full-column tally: 946 rows are `main_class_dish_pool`, 104 rows are `legacy_addon_or_template` (out of 1,050 total). The split is fully quantified and internally consistent with `join_rule_v3`'s two stated join instructions. Reclassified to Canonicalization Verification Task, item F4 (see Section 8). |
| C5 | `diet_type` shows 4 enumerated values in core sheets (egg, mixed, nonveg, veg) but only 2 (mixed, veg) in the two Addon sheets | Full-column check (all rows, not a sample) confirms `egg` and `nonveg` occur **zero** times in `Addon_Component_Class_Master.diet_type` (14 veg / 10 mixed) or `Addon_Dish_Options.diet_type` (82 veg / 60 mixed). No genuine ambiguity remains — the narrower vocabulary is a consistent, fully observed fact of this dataset. Reclassified to Canonicalization Verification Task, item F5 (see Section 8). |

---

## 8. Founder Review Register (revised)

Each item below was re-evaluated against full-dataset evidence (not sampled data). Items resolvable through observable evidence and governance rules are reclassified as **Canonicalization Verification Tasks** — they still require an explicit confirmation step during Canonicalization, but not a Founder business/governance decision. Items requiring genuine business or modeling judgment remain **Founder Decisions**.

### 8A. Founder Decisions — CLOSED (2026-07-02)

| Item | Description | Decision | Status |
|---|---|---|---|
| F1 | `Data_Dictionary_v3` omits `Weekly_Plan_Normalization_Note` and `Weekly_Plan_Join_Rules` | Documentation omission only; both sheets remain valid and participated in Discovery; no workbook correction required | ✅ CLOSED |
| F2 | Two `slot_group` vocabularies (4-value core vs 7-value compound) | Maintain as two separate canonical vocabularies (Vocabulary A: Core Meal Slot; Vocabulary B: Addon Slot Applicability); compound values preserved verbatim, never flattened/split/normalized during Canonicalization | ✅ CLOSED |

### 8B. Canonicalization Verification Tasks (reclassified from Founder Review this turn)

| Item | Description | Evidence Resolving It | Verification Task for Canonicalization Stage |
|---|---|---|---|
| F3 | 13 `Meal_Class_Overlap_Resolution` codes vs. `Meal_Class_Master_v3` | Full-set comparison: all 13 codes are present in the 131-row Master list; zero missing | Confirm the 13 codes map 1:1 to the corresponding Master rows when the canonical meal-class entity is built |
| F4 | `Class_Dish_Options_v3` contains 946 `main_class_dish_pool` rows and 104 `legacy_addon_or_template` rows | Full-column tally confirms exact split, consistent with the sheet's own `join_rule_v3` instructions | Confirm the 104 legacy/addon-scoped rows are tagged and routed per `join_rule_v3`, not merged into the primary dish-pool canonical set |
| F5 | `diet_type` in Addon sheets shows only `veg`/`mixed`, never `egg`/`nonveg` | Full-column check across both Addon sheets (196 rows total) confirms zero occurrences of `egg` or `nonveg` | Confirm the Addon-class canonical `diet_type` vocabulary is scoped to `{veg, mixed}` only, distinct from the 4-value core `diet_type` vocabulary |

**No item was silently deleted. All five original items remain fully traceable — F1 and F2 as open Founder Decisions, F3–F5 as Canonicalization Verification Tasks with their resolving evidence attached.**

---

## 9. Discovery Completion Summary

- All 22 worksheets of `Indian_Meal_Cohort_Persona_DB_v3.xlsx` read in full.
- No other file participated in this batch (Founder's strict scope requirement honored).
- 20 candidate entities, ~230 total attribute occurrences across 22 sheets, 14 explicit/near-explicit relationships, 12 explicit business rules, and 14 controlled vocabularies observed and recorded.
- 5 discrepancies identified. On re-evaluation with full-dataset evidence (v1.1): **2 remain genuine Founder Decisions (F1, F2)**; **3 are reclassified as Canonicalization Verification Tasks (F3, F4, F5)**, each fully evidenced and requiring only a confirmation step, not a business judgment, during Canonicalization.
- No canonicalization, mapping, normalization, inference, transformation, SQL, or seed generation was performed at any point.

---

## 10. Canonicalization Readiness Summary

*(This is a readiness summary for the next stage only — it does not begin that stage.)*

| Check | Status |
|---|---|
| Batch 1 Discovery complete | ✅ Yes — all 22 sheets covered |
| Entity/Attribute/Relationship/Business Rule/Vocabulary inventories produced | ✅ Yes |
| Discovery conflicts identified and routed | ✅ Yes — 5 items; 2 remain Founder Decisions (F1, F2), 3 reclassified as Canonicalization Verification Tasks (F3, F4, F5) |
| Any silent merge, discard, or correction performed | ❌ No |
| Canonicalization started | ❌ **No — awaiting Founder approval** |

**Verdict:** Canonicalization (Stage 2 of Batch 1's lifecycle) may begin once the Founder resolves **F1 and F2 only** — the two genuine Founder Decisions. F3, F4, and F5 no longer require Founder input before Canonicalization starts; they carry their resolving evidence directly and will be verified as routine confirmation steps during Canonicalization itself. **Canonicalization has not begun.**

---

## Regression Review

- ✅ No architecture, schema, API, Security, or Recommendation Engine change
- ✅ No business logic change
- ✅ No governance philosophy change
- ✅ No transformation, canonicalization, mapping, or SQL performed
- ✅ No seed data generated
- ✅ Source file (`Indian_Meal_Cohort_Persona_DB_v3.xlsx`) opened read-only throughout; not modified
- ✅ No item silently merged, discarded, transformed, mapped, ignored, or corrected — F1–F5 fully traceable, none deleted
- ✅ Reclassification of F3–F5 is evidence-based (full-dataset checks shown inline), not a judgment call performed in place of the Founder

**Only Batch 1 Discovery governance was refined this turn (evidence gathering + language precision). Canonicalization has not begun. Batch 2 has not begun.**

Founder sign-off: _______________________ Date: ___________
