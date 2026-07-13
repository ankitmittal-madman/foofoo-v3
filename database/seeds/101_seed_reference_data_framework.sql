-- Migration: 101_seed_reference_data_framework.sql
-- Implements: DOC-P3-04 v1.3 §03.27 (15 reference/seed tables — structures created in files
--   002, 003, 004)
-- Logical functions: LF-A03/B02 (re_states), LF-A01/A09 (re_main_cohorts), LF-A09/B01
--   (re_personas), LF-A02 (re_subcohorts), BUILD-02 dynamic onboarding (re_routing_rules),
--   LF-B02/D01/H04 (re_meal_classes), LF-H04 (overlap_rules), LF-D01 (class_dish_options),
--   LF-C01/C02 (addon classes/options), LF-B02/E02 (cohorts), LF-B02 (weekly_class_plans),
--   LF-C01 (household_addon_plans), LF-B03 (nonveg_logic), LF-A03/E05 (city_migration_overlays)
-- Governance refs: DOC-P3-05 Part (a) v1.2 §07 (seed gates S-01 through S-15), Contract 14.5
--   ("the system must not serve any recommendation request on partial seed data")
--
-- *** IDR-001 APPLIES TO THIS ENTIRE FILE ***
-- The full ~30,000-row dataset for these 15 tables comes from
-- Indian_Meal_Cohort_Persona_DB_v3.xlsx, which is NOT present in project files (confirmed by
-- direct directory scan during the Project Baseline Verification, [ACTIVE]_Project_Baseline_
-- Register_v1.1). Per the standing governance rule against introducing undocumented business
-- logic, this file does NOT fabricate the missing ~30,000 rows. It instead seeds a small,
-- clearly-marked illustrative dataset per table — enough to exercise every downstream trigger,
-- constraint, and query path described in DOC-P3-03/03A — and leaves every full-volume table
-- explicitly short of its Seed Gate target. Gate validation (file 901) will correctly report
-- these gates as FAILING until the real source file is provided and a follow-up seed migration
-- (102+) supersedes the illustrative rows below. This is the intended, disclosed behavior of
-- this file, not an oversight.

-- S-01: re_states — illustrative subset (target: 36)
INSERT INTO re_engine.re_states (state_code, state_name, region) VALUES
  ('MP', 'Madhya Pradesh', 'central'),
  ('MH', 'Maharashtra', 'west'),
  ('TN', 'Tamil Nadu', 'south'),
  ('WB', 'West Bengal', 'east'),
  ('PB', 'Punjab', 'north'),
  ('KA', 'Karnataka', 'south');
-- AWAITING SOURCE DATA: 30 remaining states/UTs.

-- S-02: re_main_cohorts — COMPLETE (5 of 5 — this is a fixed, fully-specified set per
-- DOC-P3-02/DOC-P3-03, not seed-source data; no IDR applies to this specific table)
INSERT INTO re_engine.re_main_cohorts (cohort_code, display_label, sort_order) VALUES
  ('MC_SOLO', 'Just me', 1),
  ('MC_COUPLE', 'Two of us', 2),
  ('MC_NUCLEAR_FAMILY', 'Family with children', 3),
  ('MC_JOINT_FAMILY', 'Joint family / multi-gen', 4),
  ('MC_PG_HOSTEL', 'PG / hostel / shared', 5);

-- S-05: re_routing_rules — COMPLETE (8 of 8 — fully specified in DOC-P3-03 §03 LF-A02; no IDR)
INSERT INTO re_engine.re_routing_rules (trigger_answer, show_question_key, skip_if_answered, sort_order) VALUES
  ('MC_NUCLEAR_FAMILY', 'children_ages', NULL, 1),
  ('MC_JOINT_FAMILY', 'elder_members_present', NULL, 2),
  ('MC_JOINT_FAMILY', 'elder_health_conditions', NULL, 3),
  ('MC_SOLO', NULL, ARRAY['children_ages','elder_members_present'], 4),
  ('MC_COUPLE', NULL, ARRAY['children_ages','elder_members_present'], 5),
  ('MC_PG_HOSTEL', NULL, ARRAY['children_ages','elder_members_present'], 6),
  ('diet_type=jain', NULL, ARRAY['nonveg_questions'], 7),
  ('infant_declared', 'infant_allergen_questions', NULL, 8);

-- S-03: re_personas — illustrative subset (target: 41)
INSERT INTO re_engine.re_personas (persona_code, main_cohort_code, display_name, primary_diet) VALUES
  ('MC3_NORTH_VEG', 'MC_NUCLEAR_FAMILY', 'Nuclear Family North Veg', 'veg'),
  ('MC3_SOUTH_VEG', 'MC_NUCLEAR_FAMILY', 'Nuclear Family South Veg', 'veg'),
  ('MC1_URBAN_SOLO', 'MC_SOLO', 'Urban Solo', 'non_veg'),
  ('MC2_COUPLE_VEG', 'MC_COUPLE', 'Couple Veg', 'veg'),
  ('MC5_PG_STANDARD', 'MC_PG_HOSTEL', 'PG Hostel Standard', 'egg');
-- AWAITING SOURCE DATA: 36 remaining personas.

-- S-04: re_subcohorts — illustrative subset (target: 41)
INSERT INTO re_engine.re_subcohorts (subcohort_code, main_cohort_code, description) VALUES
  ('SC_WITH_SCHOOL_CHILD', 'MC_NUCLEAR_FAMILY', 'Children aged 4-12'),
  ('SC_WITH_INFANT', 'MC_NUCLEAR_FAMILY', 'Infant 0-12 months present'),
  ('SC_COUPLE_STANDARD', 'MC_COUPLE', 'No branching for couples'),
  ('SC_SOLO_STANDARD', 'MC_SOLO', 'No branching for solo'),
  ('SC_PG_STANDARD', 'MC_PG_HOSTEL', 'No branching for PG/hostel');
-- AWAITING SOURCE DATA: 36 remaining subcohort refinements.

-- S-06: re_meal_classes — illustrative subset (target: 131)
-- ---------------------------------------------------------------------------
-- WP-5E CORRECTION (2026-07-13) — SEED-01: slot column is text[], not scalar text.
-- Migration 025 converted re_engine.re_meal_classes.slot from scalar text
-- (CHECK IN 'breakfast','lunch','dinner','addon') to text[] with
-- CHECK (slot <@ ARRAY['breakfast','lunch','dinner','snack'] AND cardinality>=1),
-- mapping the legacy scalar 'addon' to ARRAY['snack']. The scalar values below
-- were the PRE-025 form; against the migrated schema they failed on BOTH type
-- (scalar into text[]) and value ('addon' no longer permitted). This block
-- RESTORES the array form that REPO-WP-04B v1.1 (§Pre-Design row "WP-4A fix
-- genuinely on main": "All 9 re_meal_classes rows now ARRAY[...]; 'addon' →
-- ARRAY['snack'] confirmed correct") records as previously loaded and correct,
-- and that was lost in the apverse-labs repository reconstruction. This is
-- recovery of a documented, applied fix — not new business logic.
-- Per-row change: every prior scalar wrapped as a single-element array; the two
-- 'addon'-slot rows become ARRAY['snack'] per the migration-025 / REPO-WP-02
-- §7.6 rule (NOT re-mapped to planning_role — Batch1 MAP-DEC-003). planning_role,
-- day_type, fits, cuisine_family, diet_type are UNCHANGED.
-- ---------------------------------------------------------------------------
INSERT INTO re_engine.re_meal_classes
  (class_code, slot, day_type, planning_role, weekday_fit_1_5, weekend_fit_1_5,
   variety_cooldown_days, max_per_week, cuisine_family, diet_type)
VALUES
  ('BF_LIGHT_GRAIN', ARRAY['breakfast'], 'any', 'MAIN_PRIMARY', 5, 4, 2, 3, 'pan_indian', 'veg'),
  ('BF_STUFFED_FLATBREAD', ARRAY['breakfast'], 'weekend', 'MAIN_PRIMARY', 2, 5, 3, 2, 'north_indian', 'veg'),
  ('BF_SOUTH_FERMENTED', ARRAY['breakfast'], 'any', 'MAIN_PRIMARY', 4, 4, 2, 3, 'south_indian', 'veg'),
  ('LUNCH_DAL_SABZI_ROTI', ARRAY['lunch'], 'any', 'MAIN_PRIMARY', 5, 4, 2, 3, 'north_indian', 'veg'),
  ('DIN_CURRY_ROTI', ARRAY['dinner'], 'any', 'MAIN_PRIMARY', 5, 4, 2, 3, 'north_indian', 'veg'),
  ('DIN_NON_VEG_MAIN', ARRAY['dinner'], 'any', 'MAIN_PRIMARY', 2, 4, 3, 2, 'mughlai', 'non_veg'),
  ('ADDON_INFANT', ARRAY['snack'], 'any', 'ADDON_ONLY_NOT_PRIMARY', NULL, NULL, NULL, NULL, NULL, 'veg'),
  ('ADDON_DIABETIC', ARRAY['snack'], 'any', 'ADDON_ONLY_NOT_PRIMARY', NULL, NULL, NULL, NULL, NULL, NULL),
  ('COMBO_RICE_DAL_VEG', ARRAY['lunch'], 'any', 'COMBO_TEMPLATE_NOT_PRIMARY', 4, 4, 3, 2, 'pan_indian', 'veg');
-- AWAITING SOURCE DATA: 122 remaining class codes (full 131-row taxonomy incl. all 24 addon
-- classes and remaining MAIN_PRIMARY/COMBO_TEMPLATE rows).

-- S-07: re_meal_class_overlap_rules — illustrative subset (target: 13)
INSERT INTO re_engine.re_meal_class_overlap_rules (class_code, conflicts_with) VALUES
  ('ADDON_INFANT', 'MAIN_PRIMARY_SLOT'),
  ('ADDON_DIABETIC', 'MAIN_PRIMARY_SLOT');
-- AWAITING SOURCE DATA: 11 remaining overlap rules.

-- S-09: re_addon_classes — illustrative subset (target: 24)
INSERT INTO re_engine.re_addon_classes (addon_class_code, segment, slot) VALUES
  ('ADDON_INFANT', 'INFANT', 'breakfast'),
  ('ADDON_DIABETIC', 'DIABETIC_ELDER', 'lunch'),
  ('ADDON_POSTPARTUM', 'POSTPARTUM', 'breakfast');
-- AWAITING SOURCE DATA: 21 remaining addon classes.

-- S-14: re_nonveg_logic — illustrative subset (target: 36, one per state)
INSERT INTO re_engine.re_nonveg_logic (state_code, weekly_nonveg_slots, preferred_slots) VALUES
  ('WB', 5, ARRAY['lunch','dinner']),
  ('PB', 3, ARRAY['dinner','weekend_lunch']),
  ('MP', 2, ARRAY['weekend_dinner']);
-- AWAITING SOURCE DATA: 33 remaining states.

-- S-15: re_city_migration_overlays — illustrative subset (target: 324)
INSERT INTO re_engine.re_city_migration_overlays
  (home_state, current_city, migration_duration_band, city_overlay_weight) VALUES
  ('MP', 'Mumbai', '3_7yr', 0.50),
  ('TN', 'Bangalore', 'lt_1yr', 0.15),
  ('WB', 'Mumbai', '1_3yr', 0.30),
  ('MH', 'Mumbai', 'native', 0.00);
-- AWAITING SOURCE DATA: 320 remaining home-state x city x duration-band combinations.
