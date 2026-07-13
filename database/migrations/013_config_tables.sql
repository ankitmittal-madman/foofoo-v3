-- Migration: 013_config_tables.sql
-- Implements: DOC-P3-04 v1.3 §03.28 (all 10 re_engine configuration tables)
-- Logical functions: LF-E01 (weight_ladder_config), LF-E04/E06/E07/F01/I02/G05 (scoring_config),
--   LF-E04/J03 (event_weights), LF-A08 (confidence_config), LF-A03 (city_overlay_config),
--   LF-F02 (variety_rules), LF-A07/G04/J06 (class_affinity_config), LF-E05 (context_multipliers),
--   LF-I05/G05 (festival_calendar), LF-J08/shadow-mode (engine_versions)
-- Governance refs: DOC-P3-05 Part (a) Phase 7 (prerequisite: 001 only — standalone tables);
--   Phase 8.5 (structure only; actual config VALUES are a Part (d) data-loading concern,
--   explicitly not created here)
-- CDM entities: Aggregate 6 (Reference Data, config subset); maps to the CONFIG_TABLE
--   classification throughout DOC-P3-03A §03
-- CDM invariants enforced: none structural; the weight-sum CHECK below is the one declarative
--   business rule among these tables (re_weight_ladder_config weights must sum to 1.0)

CREATE TABLE re_engine.re_weight_ladder_config (
  tier_name   text PRIMARY KEY,
  lower_bound  integer NOT NULL,
  upper_bound  integer,
  w_cohort     real NOT NULL,
  w_content    real NOT NULL,
  w_history    real NOT NULL,
  w_context    real NOT NULL,
  w_explore    real NOT NULL,
  CHECK (w_cohort + w_content + w_history + w_context + w_explore = 1.0)
);

CREATE TABLE re_engine.re_scoring_config (
  config_key   text PRIMARY KEY,
  config_value real NOT NULL
);

CREATE TABLE re_engine.re_event_weights (
  event_type   text PRIMARY KEY,
  weight       real NOT NULL,
  decay_lambda real
);

CREATE TABLE re_engine.re_confidence_config (
  config_key   text PRIMARY KEY,
  config_value real NOT NULL
);

CREATE TABLE re_engine.re_city_overlay_config (
  migration_band       text PRIMARY KEY,
  city_overlay_weight   real NOT NULL
);

CREATE TABLE re_engine.re_variety_rules (
  rule_name           text PRIMARY KEY,
  window_days          smallint NOT NULL,
  cap_value             smallint NOT NULL,
  override_condition    text
);

CREATE TABLE re_engine.re_class_affinity_config (
  config_key   text PRIMARY KEY,
  config_value real NOT NULL
);

CREATE TABLE re_engine.re_context_multipliers (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  context_type   text NOT NULL,
  context_value   text NOT NULL,
  genome_tag       text NOT NULL,
  multiplier_value  real NOT NULL,
  UNIQUE (context_type, context_value, genome_tag)
);

CREATE TABLE re_engine.re_festival_calendar (
  festival_name     text PRIMARY KEY,
  start_date         date NOT NULL,
  end_date           date NOT NULL,
  pre_boost_days     smallint NOT NULL DEFAULT 21
);

CREATE TABLE re_engine.re_engine_versions (
  version_code   text PRIMARY KEY,
  is_active       boolean NOT NULL DEFAULT false,
  is_shadow        boolean NOT NULL DEFAULT false,
  deployed_at       timestamptz,
  metrics_json       jsonb
);
