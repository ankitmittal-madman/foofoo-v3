-- Rollback: 101_seed_reference_data_framework_rollback.sql
-- Reverses exactly the illustrative rows 101_seed_reference_data_framework.sql inserted.
-- Scoped by natural key, NOT a blanket DELETE FROM — seeds 110/111/112/116 layer their own
-- (larger, ON CONFLICT DO NOTHING) rows into these same tables and must survive this rollback.
-- Deleted in child-before-parent order (re_city_migration_overlays/re_nonveg_logic reference
-- re_states via home_state/state_code; re_meal_class_overlap_rules and re_addon_classes
-- reference class codes defined alongside them; re_subcohorts/re_personas/re_routing_rules
-- reference re_main_cohorts; re_states is deleted last).
--
-- IMPORTANT — like every rollback in this repo, apply in strict reverse numeric order: seeds
-- 110-121 (the real, non-illustrative seed pipeline) insert into the SAME tables using
-- ON CONFLICT DO NOTHING on these same natural keys, and 112/114/117 add genuine dependent rows
-- (e.g. re_class_dish_options entries FK'd to these meal_class_codes) on top of them. Running this
-- rollback while any seed numbered 102-121 is still applied WILL fail on a foreign-key violation
-- (verified live, 2026-07-30) — that is correct protective behavior, not a bug in this script. Roll
-- back 121 down through 102 first, in that order, before running this file.
BEGIN;

DELETE FROM re_engine.re_city_migration_overlays
WHERE (home_state, current_city, migration_duration_band) IN (
  ('MP', 'Mumbai', '3_7yr'),
  ('TN', 'Bangalore', 'lt_1yr'),
  ('WB', 'Mumbai', '1_3yr'),
  ('MH', 'Mumbai', 'native')
);

DELETE FROM re_engine.re_nonveg_logic WHERE state_code IN ('WB', 'PB', 'MP');

DELETE FROM re_engine.re_addon_classes
WHERE addon_class_code IN ('ADDON_INFANT', 'ADDON_DIABETIC', 'ADDON_POSTPARTUM');

DELETE FROM re_engine.re_meal_class_overlap_rules
WHERE class_code IN ('ADDON_INFANT', 'ADDON_DIABETIC') AND conflicts_with = 'MAIN_PRIMARY_SLOT';

DELETE FROM re_engine.re_meal_classes
WHERE class_code IN (
  'BF_LIGHT_GRAIN', 'BF_STUFFED_FLATBREAD', 'BF_SOUTH_FERMENTED', 'LUNCH_DAL_SABZI_ROTI',
  'DIN_CURRY_ROTI', 'DIN_NON_VEG_MAIN', 'ADDON_INFANT', 'ADDON_DIABETIC', 'COMBO_RICE_DAL_VEG'
);

DELETE FROM re_engine.re_subcohorts
WHERE subcohort_code IN (
  'SC_WITH_SCHOOL_CHILD', 'SC_WITH_INFANT', 'SC_COUPLE_STANDARD', 'SC_SOLO_STANDARD', 'SC_PG_STANDARD'
);

DELETE FROM re_engine.re_personas
WHERE persona_code IN (
  'MC3_NORTH_VEG', 'MC3_SOUTH_VEG', 'MC1_URBAN_SOLO', 'MC2_COUPLE_VEG', 'MC5_PG_STANDARD'
);

DELETE FROM re_engine.re_routing_rules
WHERE (trigger_answer, sort_order) IN (
  ('MC_NUCLEAR_FAMILY', 1), ('MC_JOINT_FAMILY', 2), ('MC_JOINT_FAMILY', 3),
  ('MC_SOLO', 4), ('MC_COUPLE', 5), ('MC_PG_HOSTEL', 6), ('diet_type=jain', 7), ('infant_declared', 8)
);

DELETE FROM re_engine.re_main_cohorts
WHERE cohort_code IN ('MC_SOLO', 'MC_COUPLE', 'MC_NUCLEAR_FAMILY', 'MC_JOINT_FAMILY', 'MC_PG_HOSTEL');

DELETE FROM re_engine.re_states WHERE state_code IN ('MP', 'MH', 'TN', 'WB', 'PB', 'KA');

COMMIT;
