-- Rollback: 008_content_core_rollback.sql
-- Reverses: 008_content_core.sql
-- RECONSTRUCTED FROM EVIDENCE (WP-5C Rollback Recovery, 2026-07-13).
--   Source of truth: the forward migration file 008_content_core.sql (the authoritative record of exactly what
--   this migration created). No original rollback existed for 001-020 (never authored — see
--   REPO-WP-02 discovery); the 021-026 rollbacks were lost in the apverse-labs repository loss
--   and are reconstructed from the WP-5B-recovered forward migrations.
--   APPLY ORDER: rollbacks run in REVERSE (028 -> 001). Each reverses ONLY what its own migration
--   created and assumes later migrations are already rolled back. Plain DROP / RESTRICT are used
--   deliberately so out-of-order or on-populated-data application FAILS LOUDLY rather than
--   cascading silently — matching the 027/028 rollback precedent.
--
-- NOTE: migration 008 also issued a REVOKE UPDATE on derived dish columns (Invariant 6).
--   That grant state is moot once public.dishes is dropped, so no explicit re-GRANT is reversed.

DROP TABLE public.dish_combos;
DROP TABLE public.dishes;
