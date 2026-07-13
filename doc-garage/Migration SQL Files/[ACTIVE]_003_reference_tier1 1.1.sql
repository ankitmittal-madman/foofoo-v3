-- Migration: 003_reference_tier1.sql
-- Implements: DOC-P3-04 v1.3 §03.27 (re_personas, re_subcohorts, re_routing_rules, re_meal_classes),
--   §03.11 (public.meal_classes — relocated here at v1.2 per AGR-002 resolution; see
--   DOC-P3-05 Part (a) v1.2 Phase 16)
-- Logical functions: LF-A09/B01 (re_personas), LF-A02 (re_subcohorts), LF-A02/BUILD-02 dynamic onboarding (re_routing_rules), LF-B02/D01/H04 (re_meal_classes), LF-D01 (public.meal_classes display read)
-- Governance refs: DOC-P3-05 Part (a) v1.2 Phase 7 (prerequisite: 002), Phase 8.1 (tier-1 allocation, corrected v1.2)
-- CDM entities: Entity 11 (Persona), Entity 10 (Sub-cohort), Entity 20 (Meal Class)
-- CDM invariants enforced: Invariant 5 (planning_role correctness — re_meal_classes.planning_role
--   is the column Safety Gate 4 reads; the gate query itself lives in file 900-series, Part (d))

CREATE TABLE re_engine.re_personas (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  persona_code      text NOT NULL UNIQUE,
  main_cohort_code  text NOT NULL REFERENCES re_engine.re_main_cohorts(cohort_code),
  display_name      text NOT NULL,
  primary_diet      text NOT NULL,
  is_active         boolean NOT NULL DEFAULT true
);
-- Seed Gate S-03: expected 41 rows after Part (d) seed load.

CREATE TABLE re_engine.re_subcohorts (
  subcohort_code    text PRIMARY KEY,
  main_cohort_code  text NOT NULL REFERENCES re_engine.re_main_cohorts(cohort_code),
  description       text
);
-- Seed Gate S-04: expected 41 rows after Part (d) seed load.

CREATE TABLE re_engine.re_routing_rules (
  id                 uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  trigger_answer     text NOT NULL,
  show_question_key  text NOT NULL,
  skip_if_answered   text[],
  sort_order         smallint NOT NULL
);
-- Seed Gate S-05: expected 8 rows after Part (d) seed load.

CREATE TABLE re_engine.re_meal_classes (
  class_code             text PRIMARY KEY,
  slot                   text NOT NULL CHECK (slot IN ('breakfast','lunch','dinner','addon')),
  day_type               text NOT NULL CHECK (day_type IN ('weekday','weekend','any')),
  planning_role          text NOT NULL CHECK (planning_role IN
    ('MAIN_PRIMARY','ADDON_ONLY_NOT_PRIMARY','COMBO_TEMPLATE_NOT_PRIMARY')),
  weekday_fit_1_5        smallint,
  weekend_fit_1_5        smallint,
  variety_cooldown_days  smallint,
  max_per_week           smallint,
  cuisine_family         text,
  diet_type              text
);
-- Seed Gate S-06: expected 131 rows after Part (d) seed load.
-- Note: idx_re_meal_classes_role (the Safety-Gate-4-supporting index on planning_role) is
-- deliberately NOT created here — consolidated into 020 per Phase 8.3. This is a file-location
-- decision only; the column itself and its safety role are unchanged from P3-04.

-- AGR-002 RESOLUTION (v1.2): public.meal_classes relocated here from the now-retired file 018.
-- This is the public read-mirror of re_meal_classes above. Created in the same file as its
-- re_engine counterpart for the exact reason Phase 5.1 always intended — they are the same
-- concept, just visible to two different privilege contexts.
CREATE TABLE public.meal_classes (
  class_code      text PRIMARY KEY,
  slot            text NOT NULL CHECK (slot IN ('breakfast','lunch','dinner','addon')),
  display_name    text NOT NULL,
  is_addon        boolean NOT NULL DEFAULT false,
  is_active       boolean NOT NULL DEFAULT true
);
-- Note: the one-way daily sync job that keeps this table current from re_engine.re_meal_classes
-- (DOC-P3-04 §03.11) is a DOC-P4 scheduling concern and is not created in this migration file.
