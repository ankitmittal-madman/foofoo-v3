-- Migration: 024_re_dish_regional_affinity.sql
-- ============================================================================
-- RECONSTRUCTED FROM EVIDENCE — WP-5B Migration Recovery, 2026-07-13
-- ============================================================================
-- Original authored/applied 2026-07-06 (Supabase version 20260706092242, name
-- "024_re_dish_regional_affinity"; REPO-WP-02 §7.6, commit 4ed5e91); lost in the
-- repository migration. This is the table whose absent CREATE statement was the
-- Critical finding (RR-01) of the Repository Completeness Audit. Reconstructed
-- to reproduce the exact live state in project slsqtlygeekdppuyiiff, observed
-- read-only 2026-07-13.
--
-- Evidence:
--   * live introspection: re_engine.re_dish_regional_affinity columns
--     dish_id (uuid NOT NULL), state_code (text NOT NULL), affinity_score
--     (numeric NOT NULL); PK (dish_id, state_code); FKs to dishes(id) ON DELETE
--     CASCADE and re_states(state_code); CHECK 0 <= affinity_score <= 1.
--   * migration 028 header note explicitly names this table and its numeric
--     affinity_score as a prior precedent.
--   * REPO-WP-02 §7.6 / Architecture Freeze v1.0 Pack B: "new dedicated table
--     re_engine.re_dish_regional_affinity (dish_id FK, state_code FK,
--     affinity_score numeric)."
-- Confidence: HIGH (table fully introspected; all constraints observed exact).
-- Note: no RLS and no anon/authenticated grants — correct for re_engine, which
--   is locked to service_role by migration 001 (confirmed live).
-- ============================================================================

CREATE TABLE re_engine.re_dish_regional_affinity (
  dish_id        uuid NOT NULL REFERENCES public.dishes(id) ON DELETE CASCADE,
  state_code     text NOT NULL REFERENCES re_engine.re_states(state_code),
  affinity_score numeric NOT NULL CHECK (affinity_score >= 0 AND affinity_score <= 1),
  PRIMARY KEY (dish_id, state_code)
);
