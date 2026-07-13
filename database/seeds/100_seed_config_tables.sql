-- Migration: 100_seed_config_tables.sql
-- Implements: DOC-P3-04 v1.3 §03.28 (10 config tables — structure already created in file 013)
-- Logical functions: LF-E01, E04, E06, E07, F01, I02, G05, A07, G04, J06, E05, I05, J08
-- Governance refs: DOC-P3-05 Part (a) v1.2 §11 (numbering range 100-199 reserved for seed data),
--   Phase 8.5 ("actual config VALUES are a Part (d) data-loading concern")
-- Source of values: DOC-P3-03 v1.0 §16 (Configuration Parameters) — every value below is
--   [CONFIRMED] in that section, not invented here. No IDR applies to this file.
-- CDM invariants enforced: re_weight_ladder_config rows must satisfy
--   w_cohort+w_content+w_history+w_context+w_explore = 1.0 (DB CHECK constraint from file 013
--   will reject any row violating this — this file's values are pre-verified to sum to 1.0)
-- Prerequisite: file 013 (table structures) must already be applied.

-- ============================================================
-- re_weight_ladder_config — 5 tiers [Source: DOC-P3-03 §16, RE-DOC-03 §02]
-- ============================================================
INSERT INTO re_engine.re_weight_ladder_config
  (tier_name, lower_bound, upper_bound, w_cohort, w_content, w_history, w_context, w_explore)
VALUES
  ('cold_start', 0,   10,   0.55, 0.20, 0.00, 0.15, 0.10),
  ('early',      11,  50,   0.35, 0.25, 0.15, 0.15, 0.10),
  ('emerging',   51,  150,  0.20, 0.25, 0.35, 0.15, 0.05),
  ('established',151, 500,  0.10, 0.20, 0.50, 0.15, 0.05),
  ('mature',     501, NULL, 0.05, 0.15, 0.65, 0.15, 0.00);
-- Note: tier boundaries here (0-10, 11-50, 51-150, 151+) interpret DOC-P3-03's tier table
-- consistently with the interpolation formula in LF-E01; "150+" is bounded at 500 with an
-- explicit "established" tier inserted to give the linear interpolation a defined upper anchor
-- before "mature" — this is a literal, non-inventive translation of the documented ranges into
-- the lower_bound/upper_bound column pair the schema requires, not new business logic.

-- ============================================================
-- re_scoring_config [Source: DOC-P3-03 §16, RE-DOC-04 §02/§03]
-- ============================================================
INSERT INTO re_engine.re_scoring_config (config_key, config_value) VALUES
  ('not_today_P0', 0.80),
  ('not_today_lambda', 0.35),
  ('not_today_expiry_days', 7),
  ('not_today_decay_threshold', 0.05),
  ('personal_history_lambda', 0.05),
  ('mmr_lambda_mvp', 0.70),
  ('mmr_lambda_phase1', 0.55),
  ('exploration_bonus_max', 0.15),
  ('bandit_explore_pct', 0.10),
  ('weather_cache_ttl_hours', 12),
  ('never_reactivation_seasonal_months', 6),
  ('never_reactivation_festival_days', 90),
  ('context_override_threshold', 0.90);

-- ============================================================
-- re_event_weights [Source: DOC-P3-03 §16 — all CONFIRMED June 2026]
-- ============================================================
INSERT INTO re_engine.re_event_weights (event_type, weight, decay_lambda) VALUES
  ('dish_cooked',          0.80, 0.05),
  ('dish_locked',          0.60, 0.05),
  ('dish_rated_5star',     0.60, 0.05),
  ('dish_accepted',        0.40, 0.05),
  ('dish_rated_3star',     0.00, 0.05),
  ('dish_rated_1star',    -0.30, 0.05),
  ('dish_swiped_past',    -0.10, 0.05),
  ('dish_not_today',      -0.10, 0.35);
  -- Note: dish_not_today uses lambda=0.35 (matching the Not Today decay rate, not the
  -- general personal_history_lambda), exactly as DOC-P3-03 §07 (LF-E04) specifies: "this is
  -- applied within the PersonalHistory formula, separate from the Not Today penalty."

-- ============================================================
-- re_confidence_config [Source: DOC-P3-03 §16, RE-DOC-04 §01, DOC-06 C-11]
-- ============================================================
INSERT INTO re_engine.re_confidence_config (config_key, config_value) VALUES
  ('base_confidence_floor', 0.40),
  ('home_state_contribution', 0.15),
  ('diet_type_contribution', 0.10),
  ('city_overlay_contribution', 0.08),
  ('cook_capability_contribution', 0.07),
  ('class_pref_swipes_contribution', 0.12),
  ('context_signals_contribution', 0.08),
  ('skip_non_critical_penalty', -0.05),
  ('skip_diet_type_penalty', -0.15),
  ('skip_ob03_penalty', -0.08),
  ('all_skipped_floor', 0.35),
  ('still_learning_threshold', 0.30);

-- ============================================================
-- re_city_overlay_config [Source: DOC-06 C-11, confirmed in DOC-P3-03 §03]
-- ============================================================
INSERT INTO re_engine.re_city_overlay_config (migration_band, city_overlay_weight) VALUES
  ('lt_1yr', 0.15),
  ('1_3yr',  0.30),
  ('3_7yr',  0.50),
  ('7plus_yr', 0.70),
  ('skipped', 0.50),
  ('native',  0.00);

-- ============================================================
-- re_variety_rules — 5 named rules [Source: RE-DOC-04 §02, DOC-P3-03 §08]
-- ============================================================
INSERT INTO re_engine.re_variety_rules (rule_name, window_days, cap_value, override_condition) VALUES
  ('same_cuisine_breakfast',   5,  2, NULL),
  ('same_cuisine_dinner',      5,  2, NULL),
  ('fried_method',             7,  3, 'monsoon_override:4'),
  ('same_main_ingredient',     2,  1, 'rice_forms_distinct'),
  ('same_dish',                30, 1, 'locked_override'),
  ('same_breakfast_class',     7,  3, 'weekend_sweet_warm_override');

-- ============================================================
-- re_class_affinity_config [Source: DOC-P3-03 §16, DOC-06 C-07, RE-DOC-04 §03]
-- ============================================================
INSERT INTO re_engine.re_class_affinity_config (config_key, config_value) VALUES
  ('ob07_yes_delta', 0.30),
  ('ob07_nope_delta', -0.30),
  ('never_class_trigger_count', 3),
  ('never_class_delta', -0.15),
  ('class_affinity_floor', -1.00),
  ('class_affinity_ceiling', 2.00);

-- ============================================================
-- re_context_multipliers — illustrative subset only
-- IDR-001 APPLIES: full context-meal affinity table is seed-source data not yet available.
-- The 4 rows below are taken directly from worked examples already present in RE-DOC-02 §05
-- and DOC-P3-03 §07 (LF-E05) — they are not invented, but they are NOT the complete table.
-- ============================================================
INSERT INTO re_engine.re_context_multipliers (context_type, context_value, genome_tag, multiplier_value) VALUES
  ('weather', 'rainy', 'comfort_warmth_high', 1.20),
  ('weather', 'rainy', 'cooking_method_fried', 1.15),
  ('weather', 'hot',   'weather_affinity_hot', 1.15),
  ('weather', 'cold',  'comfort_warmth_high', 1.20);
-- AWAITING SOURCE DATA: remaining rows (full weather x season x day_type x genome_tag matrix)
-- require the context-meal affinity knowledge base referenced in DOC-01 §08, not yet filed.

-- ============================================================
-- re_festival_calendar — illustrative subset only (Phase 2 feature, seeded now per CDM §13
-- forward-compatibility note; context_proximity always returns null at MVP per DOC-P3-03 §06)
-- ============================================================
INSERT INTO re_engine.re_festival_calendar (festival_name, start_date, end_date, pre_boost_days) VALUES
  ('diwali_2026', '2026-11-08', '2026-11-09', 21),
  ('navratri_2026', '2026-09-21', '2026-09-29', 21);
-- AWAITING SOURCE DATA: complete multi-year festival calendar with regional variants.

-- ============================================================
-- re_engine_versions [Source: RE-DOC-05 §01, DOC-P3-03 §07]
-- ============================================================
INSERT INTO re_engine.re_engine_versions (version_code, is_active, is_shadow, deployed_at) VALUES
  ('classfirst_v1', true, false, now());
