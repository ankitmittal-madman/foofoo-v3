-- Migration: 022_dish_display_attributes.sql
-- ============================================================================
-- RECONSTRUCTED FROM EVIDENCE — WP-5B Migration Recovery, 2026-07-13
-- ============================================================================
-- Original authored/applied 2026-07-06 (Supabase version 20260706092156, name
-- "022_dish_display_attributes"; REPO-WP-02 §7.6, commit 4ed5e91); lost in the
-- repository migration. Reconstructed to reproduce the exact live state in
-- project slsqtlygeekdppuyiiff, observed read-only on 2026-07-13.
--
-- Evidence:
--   * live introspection: public.dishes columns 24-26 are calories (integer,
--     nullable), serving_size (text, nullable), food_dna_tier_1 (text, nullable)
--   * REPO-WP-02 §7.6: "calories/serving_size/food_dna_tier_1 columns on dishes;
--     spice/sweetness/heaviness as tier-2 tag dimensions (seed-time rows, no DDL)"
--   * Architecture Freeze v1.0 Pack A: dish attributes split — calories/
--     serving_size/tier_1 as plain columns.
-- Confidence: HIGH (all three columns and their types observed live).
-- Note: spice/sweetness/heaviness are seed-time tier-2 tag rows, NOT columns —
--   no DDL for them here, by design.
-- ============================================================================

ALTER TABLE public.dishes ADD COLUMN calories        integer;
ALTER TABLE public.dishes ADD COLUMN serving_size    text;
ALTER TABLE public.dishes ADD COLUMN food_dna_tier_1 text;
