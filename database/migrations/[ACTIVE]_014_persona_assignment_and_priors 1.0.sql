-- Migration: 014_persona_assignment_and_priors.sql
-- Implements: DOC-P3-04 v1.3 §03.28 (re_persona_assignment_rules, re_cohort_class_priors)
-- Logical functions: LF-A09 (assignPersona — DB lookup table), LF-E02/J08 (computeCohortPrior /
--   cohortWeightRecalibration target table)
-- Governance refs: DOC-P3-05 Part (a) Phase 7 (prerequisite: 003, 004)
-- CDM entities: Entity 11 (Persona, via assignment rules), Entity 35 (Scoring Signal CohortPrior)
-- CDM invariants enforced: none directly; this table pair is what closes DOC-P3-03 gap G-002
--   (assign_persona mapping logic) and G-005 (CohortPrior table structure) at the structural level

CREATE TABLE re_engine.re_persona_assignment_rules (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  main_cohort_code   text NOT NULL REFERENCES re_engine.re_main_cohorts(cohort_code),
  subcohort_code      text REFERENCES re_engine.re_subcohorts(subcohort_code),
  state_code           text REFERENCES re_engine.re_states(state_code),
  diet_type             text,
  persona_id            uuid NOT NULL REFERENCES re_engine.re_personas(id),
  UNIQUE (main_cohort_code, subcohort_code, state_code, diet_type)
);

CREATE TABLE re_engine.re_cohort_class_priors (
  cohort_id     uuid NOT NULL REFERENCES re_engine.re_cohorts(cohort_id),
  class_code     text NOT NULL REFERENCES re_engine.re_meal_classes(class_code),
  acceptance_rate_prior real NOT NULL DEFAULT 0.5,
  updated_at      timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (cohort_id, class_code)
);
