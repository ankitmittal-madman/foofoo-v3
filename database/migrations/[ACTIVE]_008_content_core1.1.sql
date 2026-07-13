-- Migration: 008_content_core.sql
-- Implements: DOC-P3-04 v1.3 §03.6 (dishes), §03.10 (dish_combos) — AGR-001 resolved at v1.3
-- Logical functions: LF-D01-D07/E03/K01-K04 (dishes), CDM Entity 19 (dish_combos — no RE
--   algorithm currently writes to dish_combos at MVP, per P3-04 §03.10 justification)
-- Governance refs: DOC-P3-05 Part (a) Phase 7 (prerequisite: 001 only)
-- CDM entities: Entity 15 (Dish), Entity 19 (Dish Combo)
-- CDM invariants enforced: Invariant 6 (auto-derivation supremacy) — enforced by the REVOKE
--   statement below, which is the declarative half of Invariant 6; the procedural half (the
--   actual trigger that computes these columns) is fn_derive_dish_attributes, deployed in file 010.
-- Note: indexes (idx_dishes_active, idx_dishes_diet_type, idx_dishes_is_jain, idx_dishes_allergen,
-- idx_dishes_meal_occasion, idx_dishes_parent) and RLS policies are NOT created here — see 020/019.

CREATE TABLE public.dishes (
  id                       uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at               timestamptz NOT NULL DEFAULT now(),
  updated_at               timestamptz NOT NULL DEFAULT now(),
  name                     text NOT NULL UNIQUE,
  name_hindi               text,
  name_regional            text,
  description              text,
  meal_occasion            text[] NOT NULL,
  cook_time_minutes        integer NOT NULL,
  difficulty               text NOT NULL CHECK (difficulty IN ('beginner','intermediate','advanced')),

  -- DERIVED-STORED (CDM Invariant 6). Trigger fn_derive_dish_attributes (file 010) is the
  -- ONLY writer of these three columns once the REVOKE below is in force.
  diet_type                text CHECK (diet_type IN ('veg','non_veg','egg','vegan')),
  is_jain                  boolean,
  allergen_flags            integer,

  -- DERIVED-STORED. Trigger fn_update_dish_genome_vector (file 010) is the only writer.
  genome_vector            real[],

  -- DERIVED-STORED. Daily CRON (DOC-P4 scheduling concern) is the only writer; the SQL
  -- function this CRON calls, if any, is a Part (c)/(d) concern, not this file's.
  popularity_score         real NOT NULL DEFAULT 0.5,
  acceptance_rate_7d        real,
  acceptance_rate_30d       real,

  parent_dish_id            uuid REFERENCES public.dishes(id),
  is_active                 boolean NOT NULL DEFAULT true,
  is_indian_only            boolean NOT NULL DEFAULT true,
  photo_url                 text,
  photo_blurhash             text
);

-- Privilege lockdown for derived columns (Invariant 6, declarative half). Kept in this file
-- alongside the table it protects, rather than consolidated with indexes/RLS, since this is a
-- table-scoped integrity statement, not an access-pattern or row-security object.
--
-- AGR-001 RESOLVED (P3-04 v1.3, June 2026): this statement matches the corrected P3-04 text.
-- The role "service_role_app_writer" referenced in the original P3-04 v1.2 text did not exist
-- and has been removed at the architecture level — see DOC-P3-04 v1.3 Enhancement changelog.
-- No other change was made to this file as a result of this resolution.
REVOKE UPDATE (diet_type, is_jain, allergen_flags, genome_vector,
               popularity_score, acceptance_rate_7d, acceptance_rate_30d)
  ON public.dishes FROM authenticated, anon;

CREATE TABLE public.dish_combos (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  combo_name    text NOT NULL,
  combo_type    text NOT NULL CHECK (combo_type IN ('inseparable','base_with_sides','thali')),
  meal_occasion text[] NOT NULL,
  is_active     boolean NOT NULL DEFAULT true
);
