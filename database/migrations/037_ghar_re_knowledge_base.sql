-- Migration: 037_ghar_re_knowledge_base.sql
-- Project: Ghar RE v1.0 rebuild (schema `ghar_re`).
-- Implements: TASK 1 Group D — Knowledge Base tables, per ghar_knowledge_base_v0_2.md §0 interface.
--   These are the EDITABLE source-of-truth for the parameters the FROZEN spine reads. KB structure
--   is frozen; cell values are a living dataset. ✓/⚑ markers map to data_source per the Task 1 rule:
--     KB ✓ (verified in catalogue) -> 'real'   ·   KB ⚑ (needs refinement) -> 'stub'.
-- Prerequisite: 034.

-- D.1  zone_map — cuisine_group -> zone  (KB §R1). Authoritative source of a group's zone.
CREATE TABLE ghar_re.zone_map (
  cuisine_group text PRIMARY KEY,                      -- north_indian, mughlai_nawabi, street_food, ...
  zone          text NOT NULL,                         -- North/South/East/West/Central/Northeast/PanIndia/Global
  dish_count    integer,                               -- KB §R1 "dishes" column (informational)
  data_source   ghar_re.data_source_kind NOT NULL
);

-- D.2  comfort_hero_map — the concrete comfort_hero(zone, weather) target set (KB §R3).
--   This is what Core Spine §B7 m_weather resolves INTO. weather_type = rain/summer/winter.
--   verified_flag mirrors the KB ✓/⚑ marker; data_source follows it (✓->real, ⚑->stub).
--   dish_id is nullable: the KB names heroes by dish NAME; it links to a catalogue dish only when
--   one exists (e.g. our golden sample names several KB §R3 heroes by name -> linked).
CREATE TABLE ghar_re.comfort_hero_map (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  zone          text NOT NULL,                          -- North/West-MH/West-GJ/South-TN/South-KL/East-WB/Central/NE...
  weather_type  text NOT NULL CHECK (weather_type IN ('rain','summer','winter')),
  dish_name     text NOT NULL,                          -- KB-named hero (e.g. 'pakora', 'kanda bhaji')
  dish_id       uuid REFERENCES ghar_re.dishes(id),     -- linked when the hero exists in-catalogue
  verified_flag boolean NOT NULL,                       -- KB ✓ = true, KB ⚑ = false
  data_source   ghar_re.data_source_kind NOT NULL,      -- ✓ -> 'real', ⚑ -> 'stub'
  UNIQUE (zone, weather_type, dish_name)
);

-- D.3  negative_priors — authored discouragements (KB §N1). The spine ENFORCES the structural
--   ("in_spine=yes") rows via pairing_rules.yaml hard gates; this table is the editable KB
--   source-of-truth. enforced_via documents WHERE each row is (already) enforced; status marks the
--   two sequence/variety v2 rows as deferred/inactive (do NOT implement those — store only).
CREATE TABLE ghar_re.negative_priors (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  discouragement text NOT NULL,
  context        text,
  action         text,                                 -- penalty (S4 hard-gate) / demote / via weather
  in_spine       boolean NOT NULL,                     -- KB "in-spine?" column
  enforced_via   text,                                 -- 'pairing_rules.yaml' / 'weather' / 'not_yet_active'
  status         text NOT NULL CHECK (status IN ('active','deferred_v2')),
  data_source    ghar_re.data_source_kind NOT NULL
);

-- D.4  sig_score_bands — the 6-band calibration RULE (KB §S1). Distinct from ghar_re.sig_scores
--   (per-dish values). score is the band's canonical value; the pipeline maps a dish's band -> score.
CREATE TABLE ghar_re.sig_score_bands (
  score       real PRIMARY KEY,                         -- 1.00/0.90/0.75/0.60/0.40/0.20
  band_name   text NOT NULL UNIQUE,                     -- national_icon/state_icon/regional_hero/...
  definition  text NOT NULL,
  data_source ghar_re.data_source_kind NOT NULL
);

-- D.5  ingredient_normalization_map — KB §E1. Broader than aliases: surface token -> canonical
--   ingredient -> type. Kept as its OWN table (not forced into ingredient_aliases) precisely
--   because it additionally covers 'expansion' rows (mixed_vegetables -> {potato,carrot,...})
--   that the alias table's 1:1 shape cannot hold — stored in `expansion` text[].
CREATE TABLE ghar_re.ingredient_normalization_map (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  surface_token text NOT NULL,
  canonical     text,                                   -- single canonical ingredient (NULL for pure expansion)
  norm_type     text NOT NULL CHECK (norm_type IN
                  ('alias','synonym','variety','form','equivalence','expansion')),
  expansion     text[],                                 -- only for norm_type='expansion'
  note          text,
  data_source   ghar_re.data_source_kind NOT NULL,
  UNIQUE (surface_token, norm_type)
);

CREATE INDEX idx_ghar_comfort_zone_weather ON ghar_re.comfort_hero_map (zone, weather_type);
