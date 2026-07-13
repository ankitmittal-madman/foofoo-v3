-- Rollback: 026_meal_classes_mirror_slot_array_rollback.sql
-- Reverses: 026_meal_classes_mirror_slot_array.sql
-- RECONSTRUCTED FROM EVIDENCE (WP-5C Rollback Recovery, 2026-07-13).
--   Source of truth: the forward migration file 026_meal_classes_mirror_slot_array.sql (the authoritative record of exactly what
--   this migration created). No original rollback existed for 001-020 (never authored — see
--   REPO-WP-02 discovery); the 021-026 rollbacks were lost in the apverse-labs repository loss
--   and are reconstructed from the WP-5B-recovered forward migrations.
--   APPLY ORDER: rollbacks run in REVERSE (028 -> 001). Each reverses ONLY what its own migration
--   created and assumes later migrations are already rolled back. Plain DROP / RESTRICT are used
--   deliberately so out-of-order or on-populated-data application FAILS LOUDLY rather than
--   cascading silently — matching the 027/028 rollback precedent.
--
-- WARNING (LOSSY REVERSAL): same text[] -> text concern as the 025 rollback, applied to the
--   public.meal_classes read-mirror. Multi-slot rows lose data. Clean on the unseeded table.

ALTER TABLE public.meal_classes DROP CONSTRAINT meal_classes_slot_check;
ALTER TABLE public.meal_classes
  ALTER COLUMN slot TYPE text
  USING (CASE WHEN slot = ARRAY['snack'] THEN 'addon' ELSE slot[1] END);
ALTER TABLE public.meal_classes
  ADD CONSTRAINT meal_classes_slot_check CHECK (slot IN ('breakfast','lunch','dinner','addon'));
