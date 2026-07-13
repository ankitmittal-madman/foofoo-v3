-- Migration: 025_combo_component_type_and_slot_array.sql
-- ============================================================================
-- RECONSTRUCTED FROM EVIDENCE — WP-5B Migration Recovery, 2026-07-13
-- ============================================================================
-- Original authored/applied 2026-07-06 (Supabase version 20260706092303, name
-- "025_combo_component_type_and_slot_array"; REPO-WP-02 §7.6, commit 4ed5e91);
-- lost in the repository migration. Reconstructed to reproduce the exact live
-- state in project slsqtlygeekdppuyiiff, observed read-only 2026-07-13.
--
-- Evidence:
--   * live introspection: public.dish_combo_items.component_type (text,
--     nullable) with CHECK over 8 values; re_engine.re_meal_classes.slot is now
--     text[] with CHECK (slot <@ ARRAY['breakfast','lunch','dinner','snack']
--     AND cardinality(slot) >= 1). Base 003 defined slot as scalar text with
--     CHECK IN ('breakfast','lunch','dinner','addon').
--   * REPO-WP-02 §7.6: "dish_combo_items.component_type exists with 8-value
--     CHECK; role's original CHECK byte-identical; re_meal_classes.slot is
--     text[] with 4-value CHECK; legacy 'addon' maps to ARRAY['snack']."
--   * Architecture Freeze v1.0 Pack C: add component_type, leave role unchanged.
-- Confidence: HIGH on the resulting shape (component_type CHECK, slot type +
--   CHECK all observed live). The ALTER ... USING conversion expression is
--   RECONSTRUCTED (its result is observed; the original text is not) — it is the
--   only expression consistent with the cited 'addon' -> ['snack'] rule.
-- Note: role's CHECK is untouched here (confirmed byte-identical live:
--   role IN ('primary','side','accompaniment')).
-- ============================================================================

-- New combo component classification (nullable; role is left unchanged).
ALTER TABLE public.dish_combo_items
  ADD COLUMN component_type text
  CHECK (component_type IN
    ('primary','bread','carb_base','accompaniment','condiment','dessert','beverage','standalone'));

-- Convert re_meal_classes.slot from scalar text to text[] (multi-slot support).
-- Legacy scalar 'addon' becomes ARRAY['snack']; every other scalar becomes a
-- single-element array of itself.
ALTER TABLE re_engine.re_meal_classes DROP CONSTRAINT re_meal_classes_slot_check;

ALTER TABLE re_engine.re_meal_classes
  ALTER COLUMN slot TYPE text[]
  USING (CASE WHEN slot = 'addon' THEN ARRAY['snack'] ELSE ARRAY[slot] END);

ALTER TABLE re_engine.re_meal_classes
  ADD CONSTRAINT re_meal_classes_slot_check
  CHECK (slot <@ ARRAY['breakfast','lunch','dinner','snack'] AND cardinality(slot) >= 1);
