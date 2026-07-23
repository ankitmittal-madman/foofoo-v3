-- Migration: 034_ghar_re_schema_and_catalogue.sql
-- Project: Ghar RE v1.0 rebuild (the OLD persona/cohort/weight-ladder RE is retired; this is
--   a NEW, isolated schema `ghar_re` and does NOT touch public.dishes / re_engine.* or the
--   real 810-dish catalogue).
-- Implements: TASK 1 Group A — Catalogue / Knowledge tables.
-- Source specs: Core Spine FROZEN §1 (feature space) + §S2 (BASE); KB v0.2 §R1/§S1/§E1.
--   dish-level fields added per Core Spine §S1 GROUP D (hero_role, diet) + §S2 A2/A5
--   (jain_compatible, farali_compatible) + §B1 (scope_tier).
-- HARD SCHEMA REQUIREMENT: every table carries a NOT NULL `data_source` column constrained to
--   ('real','ai_generated','stub') with NO default (nothing silently picks 'real').

CREATE SCHEMA IF NOT EXISTS ghar_re;

-- Privilege boundary mirrors migration 001's treatment of re_engine: service_role only.
REVOKE ALL ON SCHEMA ghar_re FROM PUBLIC, anon, authenticated;
GRANT USAGE ON SCHEMA ghar_re TO service_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA ghar_re GRANT ALL ON TABLES TO service_role;

-- The single provenance enum reused by EVERY table in groups A-D.
--   real         = transcribed verbatim from a real authored source (frozen doc / KB ✓ cell /
--                  real catalogue value).
--   ai_generated = invented by this build to fill a gap (golden sample rows, computed fills).
--   stub         = present but flagged low-confidence (KB ⚑ "needs refinement" cell).
DO $$ BEGIN
  CREATE TYPE ghar_re.data_source_kind AS ENUM ('real','ai_generated','stub');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- =====================================================================================
-- GROUP A — CATALOGUE / KNOWLEDGE
-- =====================================================================================

-- A.1  cuisine_groups  (KB §R1 groups; zone itself lives in ghar_re.zone_map, group D)
CREATE TABLE ghar_re.cuisine_groups (
  name          text PRIMARY KEY,                    -- e.g. north_indian, south_indian
  display_name  text NOT NULL,
  display_order integer,
  description   text,
  data_source   ghar_re.data_source_kind NOT NULL
);

-- A.2  cuisines  (mirrors data/source/cuisines_v4.csv shape; parent_cuisine = self-hierarchy)
CREATE TABLE ghar_re.cuisines (
  name           text PRIMARY KEY,                   -- e.g. punjabi, tamil, chettinad
  display_name   text NOT NULL,
  cuisine_group  text NOT NULL REFERENCES ghar_re.cuisine_groups(name),
  parent_cuisine text REFERENCES ghar_re.cuisines(name),   -- chettinad -> tamil
  state_origin   text,                               -- feeds m_palette cuis(x, state)
  tier           text,                               -- tier_1 / tier_2 / tier_3
  is_user_facing boolean NOT NULL DEFAULT true,
  data_source    ghar_re.data_source_kind NOT NULL
);

-- A.3  dishes  (dishes.xlsx `dishes_810` STRUCTURE + the doc-required fields the xlsx lacks)
--   Multi-valued sensory/structure attributes are text[] matching the tags vocabulary
--   (ghar_re.tags). Scalars follow the Core Spine §1 encodings (spice (spice-1)/3, etc.).
CREATE TABLE ghar_re.dishes (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name              text NOT NULL UNIQUE,
  short_description text,
  alternate_names   text[],
  cuisine           text REFERENCES ghar_re.cuisines(name),   -- primary cuisine
  -- Sensory scalars (§1 GROUP A)
  spice_level       integer CHECK (spice_level BETWEEN 0 AND 4),
  sweetness         integer CHECK (sweetness   BETWEEN 0 AND 3),
  heaviness         integer CHECK (heaviness   BETWEEN 1 AND 3),
  difficulty        text CHECK (difficulty IN ('easy','medium','hard')),
  prep_mins         integer,
  cook_mins         integer,
  total_mins        integer,
  calories          integer,
  serving_size      text,
  -- Multi-valued attributes (§1 groups A/B/D/E). Validated against ghar_re.tags in the pipeline.
  meal_type         text[] NOT NULL,                 -- breakfast/lunch/dinner/snacks (m_slot §B2)
  dish_category     text[],
  cooking_method    text[],
  primary_taste     text[],
  texture           text[],
  richness          text[],
  mouthfeel         text[],
  aroma_profile     text[],
  fermentation      text CHECK (fermentation IN ('none','light','medium','heavy')),
  serving_temp      text CHECK (serving_temp IN ('hot','warm','room_temp','chilled','frozen')),
  weather_affinity  text[],                          -- all_weather/cold_weather/hot_weather/rainy (WE, §B7)

  -- ---- Fields the docs REQUIRE that dishes.xlsx does NOT carry (Task 1) ----
  -- diet: graded diet §S1 3.5 + hard filter A1
  diet              text NOT NULL CHECK (diet IN ('veg','egg','non_veg')),
  -- hero_role: plate structure §S1 GROUP D + §S4 pool assignment
  hero_role         text NOT NULL CHECK (hero_role IN
                       ('liquid','dry','single','standalone','support','snack','accompaniment')),
  -- jain_compatible: hard filter A2 (Y/N; derived from ingredient flags in the pipeline)
  jain_compatible   text NOT NULL CHECK (jain_compatible IN ('Y','N')),
  -- scope_tier: §B1 palette gate (experimental * rho_disc)
  scope_tier        text NOT NULL CHECK (scope_tier IN
                       ('indian_core','indianised_daily','experimental')),
  -- farali_compatible: fasting-mode hard filter A5 (vrat-compatible)
  farali_compatible boolean NOT NULL DEFAULT false,

  is_active         boolean NOT NULL DEFAULT true,
  data_source       ghar_re.data_source_kind NOT NULL
);

-- A.4  ingredients  (mirrors ingredients_v5.csv; is_jain_compatible/allergen feed A2/A3 + farali)
CREATE TABLE ghar_re.ingredients (
  name               text PRIMARY KEY,
  display_name       text,
  category           text,                           -- spice/vegetable/lentil_legume/dairy/...
  diet_type          text CHECK (diet_type IN ('veg','egg','non_veg')),
  is_allergen        boolean NOT NULL DEFAULT false,
  allergen_type      text,                           -- gluten/dairy/tree_nuts/... (tags: allergen)
  is_jain_compatible boolean,                         -- false for onion/garlic/root veg
  is_vegan           boolean,
  data_source        ghar_re.data_source_kind NOT NULL
);

-- A.5  dish_ingredients  (join; is_main_ingredient mirrors migration 031 flag; feeds ING block)
CREATE TABLE ghar_re.dish_ingredients (
  dish_id            uuid NOT NULL REFERENCES ghar_re.dishes(id) ON DELETE CASCADE,
  ingredient_name    text NOT NULL REFERENCES ghar_re.ingredients(name),
  is_main_ingredient boolean NOT NULL DEFAULT false,
  data_source        ghar_re.data_source_kind NOT NULL,
  PRIMARY KEY (dish_id, ingredient_name)
);

-- A.6  ingredient_aliases  (ingredient_aliases_v2.csv; surface->canonical, alias class only)
CREATE TABLE ghar_re.ingredient_aliases (
  alias                text PRIMARY KEY,
  canonical_ingredient text NOT NULL REFERENCES ghar_re.ingredients(name),
  data_source          ghar_re.data_source_kind NOT NULL
);

-- A.7  dish_name_synonyms  (term_synonyms_v2.csv at the dish level)
CREATE TABLE ghar_re.dish_name_synonyms (
  dish_id     uuid NOT NULL REFERENCES ghar_re.dishes(id) ON DELETE CASCADE,
  synonym     text NOT NULL,
  data_source ghar_re.data_source_kind NOT NULL,
  PRIMARY KEY (dish_id, synonym)
);

-- A.8  tags  (tags_v4.csv controlled vocabulary; category+value composite key)
CREATE TABLE ghar_re.tags (
  category       text NOT NULL,                       -- weather_affinity/richness/texture/...
  value          text NOT NULL,
  display_value  text,
  tier           text,
  is_user_facing boolean NOT NULL DEFAULT true,
  data_source    ghar_re.data_source_kind NOT NULL,
  PRIMARY KEY (category, value)
);

-- A.9  dish_combos  (dish_combos_v2_20260520.csv)
CREATE TABLE ghar_re.dish_combos (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name        text NOT NULL UNIQUE,
  combo_type  text,
  description text,
  data_source ghar_re.data_source_kind NOT NULL
);

-- A.10  dish_combo_items  (dish_combo_items_v2_20260520.csv; role = hero/support/etc.)
CREATE TABLE ghar_re.dish_combo_items (
  combo_id    uuid NOT NULL REFERENCES ghar_re.dish_combos(id) ON DELETE CASCADE,
  dish_id     uuid REFERENCES ghar_re.dishes(id),
  dish_name   text,                                   -- kept for rows whose dish is not in catalogue
  role        text,
  data_source ghar_re.data_source_kind NOT NULL,
  PRIMARY KEY (combo_id, dish_name)
);

-- A.11  region_food_affinity  (region_food_affinity.csv; state_code x dish affinity)
CREATE TABLE ghar_re.region_food_affinity (
  state_code     text NOT NULL,
  dish_name      text NOT NULL,
  affinity_score real NOT NULL CHECK (affinity_score BETWEEN 0 AND 1),
  source         text,
  data_source    ghar_re.data_source_kind NOT NULL,
  PRIMARY KEY (state_code, dish_name)
);

-- A.12  community_priors  (community_priors.csv; KB §C1 — D6 SOFT diet-default, always
--   overridden by explicit Q5-Q8; decays to behaviour in v2)
CREATE TABLE ghar_re.community_priors (
  state                   text PRIMARY KEY,
  zone                    text NOT NULL,
  diet_lean               text NOT NULL,             -- strongly_veg/veg_leaning/mixed/strongly_non_veg
  default_non_veg_cadence text NOT NULL,             -- rare/weekend/frequent/daily
  data_source             ghar_re.data_source_kind NOT NULL
);

COMMENT ON SCHEMA ghar_re IS
  'Ghar RE v1.0 rebuild (isolated). Governs the rebuilt recommendation engine only; the retired persona/cohort/weight-ladder RE in re_engine/public is untouched.';
