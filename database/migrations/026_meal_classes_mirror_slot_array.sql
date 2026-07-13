-- Migration: 026_meal_classes_mirror_slot_array.sql
-- ============================================================================
-- RECONSTRUCTED FROM EVIDENCE — WP-5B Migration Recovery, 2026-07-13
-- ============================================================================
-- Original authored/applied 2026-07-08 (Supabase version 20260708141613, name
-- "026_meal_classes_mirror_slot_array"); lost in the repository migration.
-- Reconstructed to reproduce the exact live state in project
-- slsqtlygeekdppuyiiff, observed read-only 2026-07-13.
--
-- Context / identity: migration 026 was authored AFTER the WP-02 freeze batch
-- (021-025) to answer REPO-WP-02 follow-up decision #3 — "Should
-- public.meal_classes (the read-mirror) receive the same multi-slot conversion
-- as re_engine.re_meal_classes?" The live migration name confirms the answer was
-- YES and it was applied 2026-07-08. It applies to the public.meal_classes
-- MIRROR exactly the slot conversion migration 025 applied to re_meal_classes.
--
-- Evidence:
--   * live introspection: public.meal_classes.slot is text[] with CHECK (slot
--     <@ ARRAY['breakfast','lunch','dinner','snack'] AND cardinality(slot) >= 1).
--     Base 003 defined it as scalar text CHECK IN
--     ('breakfast','lunch','dinner','addon').
--   * Supabase migration history: version 20260708141613, name
--     "026_meal_classes_mirror_slot_array".
-- Confidence: HIGH on resulting shape (observed live). The USING conversion
--   expression is RECONSTRUCTED (result observed, original text not), mirroring
--   migration 025's cited 'addon' -> ['snack'] rule for consistency of the
--   read-mirror with re_meal_classes.
-- ============================================================================

ALTER TABLE public.meal_classes DROP CONSTRAINT meal_classes_slot_check;

ALTER TABLE public.meal_classes
  ALTER COLUMN slot TYPE text[]
  USING (CASE WHEN slot = 'addon' THEN ARRAY['snack'] ELSE ARRAY[slot] END);

ALTER TABLE public.meal_classes
  ADD CONSTRAINT meal_classes_slot_check
  CHECK (slot <@ ARRAY['breakfast','lunch','dinner','snack'] AND cardinality(slot) >= 1);
