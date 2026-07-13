-- Migration: 004_reference_tier2.sql
-- Implements: DOC-P3-04 v1.2 §03.27 (re_meal_class_overlap_rules, re_class_dish_options,
--   re_addon_classes, re_addon_dish_options, re_cohorts, re_weekly_class_plans,
--   re_household_addon_plans, re_nonveg_logic, re_city_migration_overlays)
-- Logical functions: LF-H04 (overlap_rules), LF-D01 (class_dish_options), LF-C01 (addon_classes),
--   LF-C02 (addon_dish_options), LF-B02/E02 (cohorts), LF-B02 (weekly_class_plans),
--   LF-C01 (household_addon_plans), LF-B03 (nonveg_logic), LF-A03/E05 (city_migration_overlays)
-- Governance refs: DOC-P3-05 Part (a) Phase 7 (prerequisite: 003), Phase 8.1 (tier-2 allocation)
-- CDM entities: Entity 20 (Meal Class, overlap rules), Entity 21 (Class-Dish Option),
--   Entity 11 (Persona, via cohorts), Entity 23 (Week Plan, via weekly_class_plans)
-- CDM invariants enforced: none directly (reference data); these tables are what Safety Gate 4
--   and the hard-constraint filters (LF-D01-D07) read from at runtime.
-- Internal ordering within this file follows FK dependency: overlap_rules and class_dish_options
-- (reference tier-1 only) -> addon_classes -> addon_dish_options (references addon_classes,
-- same file) -> cohorts (references tier-1 only) -> weekly_class_plans (references cohorts,
-- same file) -> household_addon_plans (references both cohorts and addon_classes, same file) ->
-- nonveg_logic and city_migration_overlays (reference tier-0 re_states only).

CREATE TABLE re_engine.re_meal_class_overlap_rules (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  class_code     text NOT NULL REFERENCES re_engine.re_meal_classes(class_code),
  conflicts_with text NOT NULL
);
-- Seed Gate S-07: expected 13 rows after Part (d) seed load.

CREATE TABLE re_engine.re_class_dish_options (
  id                   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  meal_class_code      text NOT NULL REFERENCES re_engine.re_meal_classes(class_code),
  dish_id              uuid NOT NULL,  -- soft reference to public.dishes(id); see DOC-P3-04 §03.27 note
  base_score           real NOT NULL,
  is_primary_candidate boolean NOT NULL DEFAULT false,
  UNIQUE (meal_class_code, dish_id)
);
-- Seed Gate S-08: expected 1,050 rows after Part (d) seed load.

CREATE TABLE re_engine.re_addon_classes (
  addon_class_code text PRIMARY KEY,
  segment          text NOT NULL,
  slot             text NOT NULL
);
-- Seed Gate S-09: expected 24 rows after Part (d) seed load.

CREATE TABLE re_engine.re_addon_dish_options (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  addon_class_code  text NOT NULL REFERENCES re_engine.re_addon_classes(addon_class_code),
  dish_id           uuid NOT NULL,  -- soft reference to public.dishes(id)
  suitability_rank  smallint NOT NULL
);
-- Seed Gate S-10: expected 142-143 rows after Part (d) seed load.

CREATE TABLE re_engine.re_cohorts (
  cohort_id    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  persona_id   uuid NOT NULL REFERENCES re_engine.re_personas(id),
  state_code   text NOT NULL REFERENCES re_engine.re_states(state_code),
  diet_mode    text NOT NULL,
  prior_weight real NOT NULL DEFAULT 1.0,
  UNIQUE (persona_id, state_code, diet_mode)
);
-- Seed Gate S-11: expected 2,952-2,953 rows after Part (d) seed load.

CREATE TABLE re_engine.re_weekly_class_plans (
  id                    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  cohort_id             uuid NOT NULL REFERENCES re_engine.re_cohorts(cohort_id),
  day_of_week           text NOT NULL,
  breakfast_class_code  text NOT NULL REFERENCES re_engine.re_meal_classes(class_code),
  lunch_class_code      text NOT NULL REFERENCES re_engine.re_meal_classes(class_code),
  dinner_class_code     text NOT NULL REFERENCES re_engine.re_meal_classes(class_code),
  UNIQUE (cohort_id, day_of_week)
);
-- Seed Gate S-12: expected 20,664 rows after Part (d) seed load.

CREATE TABLE re_engine.re_household_addon_plans (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  segment          text NOT NULL,
  cohort_id        uuid NOT NULL REFERENCES re_engine.re_cohorts(cohort_id),
  addon_class_code text NOT NULL REFERENCES re_engine.re_addon_classes(addon_class_code)
);
-- Seed Gate S-13: expected 7,992 rows after Part (d) seed load.

CREATE TABLE re_engine.re_nonveg_logic (
  state_code         text PRIMARY KEY REFERENCES re_engine.re_states(state_code),
  weekly_nonveg_slots smallint NOT NULL,
  preferred_slots     text[] NOT NULL
);
-- Seed Gate S-14: expected 36 rows after Part (d) seed load.

CREATE TABLE re_engine.re_city_migration_overlays (
  id                       uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  home_state               text NOT NULL REFERENCES re_engine.re_states(state_code),
  current_city             text NOT NULL,
  migration_duration_band  text NOT NULL,
  city_overlay_weight      real NOT NULL,
  UNIQUE (home_state, current_city, migration_duration_band)
);
-- Seed Gate S-15: expected 324 rows after Part (d) seed load.
