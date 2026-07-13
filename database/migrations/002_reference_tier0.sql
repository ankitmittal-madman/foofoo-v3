-- Migration: 002_reference_tier0.sql
-- Implements: DOC-P3-04 v1.2 §03.5 (ingredients), §03.8 (tags), §03.27 (re_states, re_main_cohorts)
-- Logical functions: LF-D03/K01 (ingredients), LF-K02/E03 (tags), LF-A03/B02 (re_states), LF-A01/A09 (re_main_cohorts)
-- Governance refs: DOC-P3-05 Part (a) Phase 7 (prerequisite: 001 only), Phase 8.1 (tier-0 allocation)
-- CDM entities: Entity 18 (Ingredient), Entity 16/17 (Food DNA / Genome Tag), Entity 4 (Regional Identity), Entity 9 (Main Cohort)
-- CDM invariants enforced: none directly in this file (ground-truth/no-dependency tables only)
-- Note: indexes and RLS for these tables are NOT created here — consolidated into 020 and 019
-- per DOC-P3-05 Part (a) Phase 8.3/8.4.

CREATE TABLE public.ingredients (
  id                   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name                 text NOT NULL UNIQUE,
  allergen_flags       integer NOT NULL DEFAULT 0,
  is_veg               boolean NOT NULL,
  is_vegan             boolean NOT NULL DEFAULT false,
  is_jain_excluded     boolean NOT NULL DEFAULT false,
  can_substitute_id    uuid REFERENCES public.ingredients(id),
  seasonal_peak        text[],
  is_active            boolean NOT NULL DEFAULT true
);

CREATE TABLE public.tags (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tag_name        text NOT NULL UNIQUE,
  dimension       text NOT NULL,
  tier            smallint NOT NULL CHECK (tier IN (1,2,3)),
  is_user_facing  boolean NOT NULL DEFAULT false,
  vector_position integer NOT NULL UNIQUE
);

CREATE TABLE re_engine.re_states (
  state_code  text PRIMARY KEY,
  state_name  text NOT NULL,
  region      text NOT NULL
);
-- Seed Gate S-01: expected 36 rows after Part (d) seed load.

CREATE TABLE re_engine.re_main_cohorts (
  cohort_code   text PRIMARY KEY,
  display_label text NOT NULL,
  sort_order    smallint NOT NULL
);
-- Seed Gate S-02: expected 5 rows after Part (d) seed load.
