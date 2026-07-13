-- Rollback: 025_combo_component_type_and_slot_array_rollback.sql
-- Reverses: 025_combo_component_type_and_slot_array.sql
-- RECONSTRUCTED FROM EVIDENCE (WP-5C Rollback Recovery, 2026-07-13).
--   Source of truth: the forward migration file 025_combo_component_type_and_slot_array.sql (the authoritative record of exactly what
--   this migration created). No original rollback existed for 001-020 (never authored — see
--   REPO-WP-02 discovery); the 021-026 rollbacks were lost in the apverse-labs repository loss
--   and are reconstructed from the WP-5B-recovered forward migrations.
--   APPLY ORDER: rollbacks run in REVERSE (028 -> 001). Each reverses ONLY what its own migration
--   created and assumes later migrations are already rolled back. Plain DROP / RESTRICT are used
--   deliberately so out-of-order or on-populated-data application FAILS LOUDLY rather than
--   cascading silently — matching the 027/028 rollback precedent.
--
-- WARNING (LOSSY REVERSAL — parallel to the 027/028 precedent): converting slot from text[]
--   back to scalar text cannot represent any row with more than one slot. The reversal maps
--   ARRAY['snack'] -> 'addon' and otherwise takes slot[1]; any genuinely multi-slot row
--   (cardinality > 1, e.g. ARRAY['lunch','dinner']) SILENTLY LOSES its extra slots. On the
--   currently-unseeded table this reverses cleanly. Do NOT run after multi-slot data is loaded.

ALTER TABLE re_engine.re_meal_classes DROP CONSTRAINT re_meal_classes_slot_check;
ALTER TABLE re_engine.re_meal_classes
  ALTER COLUMN slot TYPE text
  USING (CASE WHEN slot = ARRAY['snack'] THEN 'addon' ELSE slot[1] END);
ALTER TABLE re_engine.re_meal_classes
  ADD CONSTRAINT re_meal_classes_slot_check CHECK (slot IN ('breakfast','lunch','dinner','addon'));
ALTER TABLE public.dish_combo_items DROP COLUMN component_type;
