-- Rollback: 021_cuisines_reference_rollback.sql
-- Reverses: 021_cuisines_reference.sql
-- RECONSTRUCTED FROM EVIDENCE (WP-5C Rollback Recovery, 2026-07-13).
--   Source of truth: the forward migration file 021_cuisines_reference.sql (the authoritative record of exactly what
--   this migration created). No original rollback existed for 001-020 (never authored — see
--   REPO-WP-02 discovery); the 021-026 rollbacks were lost in the apverse-labs repository loss
--   and are reconstructed from the WP-5B-recovered forward migrations.
--   APPLY ORDER: rollbacks run in REVERSE (028 -> 001). Each reverses ONLY what its own migration
--   created and assumes later migrations are already rolled back. Plain DROP / RESTRICT are used
--   deliberately so out-of-order or on-populated-data application FAILS LOUDLY rather than
--   cascading silently — matching the 027/028 rollback precedent.
--
-- NOTE: dropping public.cuisines also removes its RLS enablement. The cuisine_id FK columns on
--   dishes/dish_combos are dropped before the table they reference.

DROP POLICY cuisines_public_read ON public.cuisines;
ALTER TABLE public.dish_combos DROP COLUMN cuisine_id;
ALTER TABLE public.dishes DROP COLUMN cuisine_id;
DROP TABLE public.cuisines;
