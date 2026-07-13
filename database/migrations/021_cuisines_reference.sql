-- Migration: 021_cuisines_reference.sql
-- ============================================================================
-- RECONSTRUCTED FROM EVIDENCE — WP-5B Migration Recovery, 2026-07-13
-- ============================================================================
-- This file is NOT the byte-for-byte original. The original was authored and
-- applied on 2026-07-06 (Supabase migration version 20260706092140, name
-- "021_cuisines_reference") per REPO-WP-02 §7.6 addendum (commit 4ed5e91) but
-- was lost during the repository migration off the deleted apverse-labs org.
-- It is reconstructed here to reproduce the EXACT applied schema state observed
-- live (read-only) in Supabase project slsqtlygeekdppuyiiff on 2026-07-13.
--
-- Evidence:
--   * live introspection: information_schema.columns, pg_constraint,
--     pg_policies, pg_class.relrowsecurity (public.cuisines and the two
--     cuisine_id FKs) — WP-5B, 2026-07-13
--   * REPO-WP-02 §7.6: "public.cuisines exists with FK shape; cuisine_id FK on
--     dishes and dish_combos"
--   * Architecture Freeze v1.0 Pack A: cuisine → FK to new public.cuisines
--     (seeded from cuisines_v4.csv)
-- Confidence: HIGH (table, constraints, RLS policy all observed live and exact).
-- Note: anon/authenticated table-level grants are Supabase project defaults
--   (ALTER DEFAULT PRIVILEGES from migration 001), not set by this migration,
--   so no explicit GRANT is reproduced here.
-- ============================================================================

CREATE TABLE public.cuisines (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name           text NOT NULL UNIQUE,
  display_name   text NOT NULL,
  cuisine_group  text NOT NULL,
  parent_cuisine text,
  state_origin   text,
  description    text,
  tier           text,
  is_user_facing boolean NOT NULL DEFAULT true,
  is_active      boolean NOT NULL DEFAULT true
);

-- Cuisine foreign keys on content tables (nullable — assigned at seed time).
ALTER TABLE public.dishes
  ADD COLUMN cuisine_id uuid REFERENCES public.cuisines(id);

ALTER TABLE public.dish_combos
  ADD COLUMN cuisine_id uuid REFERENCES public.cuisines(id);

-- Public-read reference table (created after the 019 RLS pass, so RLS is set here).
ALTER TABLE public.cuisines ENABLE ROW LEVEL SECURITY;

CREATE POLICY cuisines_public_read
  ON public.cuisines
  FOR SELECT
  USING (true);
