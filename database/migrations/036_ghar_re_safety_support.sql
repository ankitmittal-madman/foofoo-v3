-- Migration: 036_ghar_re_safety_support.sql
-- Project: Ghar RE v1.0 rebuild (schema `ghar_re`).
-- Implements: TASK 1 Group C — Safety / support / deferred-but-schema-now tables.
-- Source specs: Final_RE Deferred register + Core Spine appendix D/E:
--   allergen hidden-derivative table [SP-F13 SAFETY, pre-launch], substitution/variant graph
--   [SP-F14 DB-designed], per-dish macro/nutrition vector [SP-F11 DATA/v2], signature scores
--   (per-dish VALUES applying KB §S1), and the PRIOR[zone][slot(x season)] boost table (§B8).
-- These are SCHEMA-NOW even where logic is deferred, so v2 slots in with no migration.
-- Prerequisite: 034.

-- C.1  allergen_hidden_derivatives — SAFETY-CRITICAL lookup, e.g. hing -> wheat/gluten.
--   Schema now; population + folding into filter A3 is a PRE-LAUNCH deferred item (out of scope
--   for this task's pipeline, per the Task 3 note "Do NOT attempt the allergen hidden-derivative
--   table"). Rows here are inert until wired.
CREATE TABLE ghar_re.allergen_hidden_derivatives (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  surface_token  text NOT NULL,                        -- ingredient/additive that hides an allergen
  hidden_allergen text NOT NULL,                       -- allergen tag it derives to (e.g. gluten)
  note           text,
  is_active      boolean NOT NULL DEFAULT false,        -- inert until safety-verified pre-launch
  data_source    ghar_re.data_source_kind NOT NULL
);

-- C.2  dish_variants — the substitution graph (butter chicken -> butter paneer -> jain -> vegan).
--   Powers the explicit veg-day 1:1 swap in v2; v1 just refills from the veg pool.
CREATE TABLE ghar_re.dish_variants (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  from_dish_id uuid NOT NULL REFERENCES ghar_re.dishes(id) ON DELETE CASCADE,
  to_dish_id   uuid NOT NULL REFERENCES ghar_re.dishes(id) ON DELETE CASCADE,
  variant_type text NOT NULL CHECK (variant_type IN
                 ('veg_swap','jain','vegan','no_onion_garlic','farali','lighter','protein_swap')),
  note         text,
  data_source  ghar_re.data_source_kind NOT NULL,
  UNIQUE (from_dish_id, to_dish_id, variant_type)
);

-- C.3  dish_macro — per-dish nutrition vector (calories/protein/fibre/fat/carbs/sugar/sodium).
--   Unblocks Q15 Protein Calculator + macro-accurate calorie targeting in v2; v1 uses calories only.
CREATE TABLE ghar_re.dish_macro (
  dish_id     uuid PRIMARY KEY REFERENCES ghar_re.dishes(id) ON DELETE CASCADE,
  calories    integer,
  protein_g   real,
  fibre_g     real,
  fat_g       real,
  carbs_g     real,
  sugar_g     real,
  sodium_mg   real,
  data_source ghar_re.data_source_kind NOT NULL
);

-- C.4  sig_scores — per-dish signature VALUES (applies the KB §S1 band RULE; see sig_score_bands).
--   Distinct from ghar_re.sig_score_bands (group D), which is the rule; this is x -> sig(x).
CREATE TABLE ghar_re.sig_scores (
  dish_id             uuid PRIMARY KEY REFERENCES ghar_re.dishes(id) ON DELETE CASCADE,
  sig_score           real NOT NULL CHECK (sig_score BETWEEN 0 AND 1),
  band                text NOT NULL,                   -- national_icon/state_icon/.../utility
  evidence_confidence text,                            -- High/Medium/Low
  coverage_confidence text,
  owner               text,
  method              text,                            -- curated / auto_draft
  version             text,
  data_source         ghar_re.data_source_kind NOT NULL
);

-- C.5  prior_zone_slot_season — the authored PRIOR[zone][slot](x season) boost table (§B8),
--   seeded from KB §R2. season is NULLable: v1 authored 2-D (zone x slot); the 3-D season axis
--   is KB-F4 (deferred), so NULL season = "applies to all seasons".
CREATE TABLE ghar_re.prior_zone_slot_season (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  zone            text NOT NULL,                       -- North/South/East/West/Central/Northeast/PanIndia/Global
  slot            text NOT NULL CHECK (slot IN ('breakfast','lunch','dinner')),
  season          text,                                -- NULL in v1 (2-D); KB-F4 adds the 3rd axis
  match_kind      text NOT NULL CHECK (match_kind IN
                    ('dish_name','dish_category','cuisine','hero_role','structure','attribute')),
  match_value     text NOT NULL,                       -- e.g. 'paratha', 'dosa_idli', 'roti+sabzi+dal'
  boost           real NOT NULL,                       -- additive BASE boost
  usage_tags      text[],                              -- Daily/Weekend/Festival/Weather/Comfort/Recovery
  data_source     ghar_re.data_source_kind NOT NULL
);

CREATE INDEX idx_ghar_prior_zone_slot ON ghar_re.prior_zone_slot_season (zone, slot);
CREATE INDEX idx_ghar_variants_from   ON ghar_re.dish_variants (from_dish_id);
