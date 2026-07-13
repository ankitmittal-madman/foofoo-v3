-- Rollback: 003_reference_tier1_rollback.sql
-- Reverses: 003_reference_tier1.sql
-- RECONSTRUCTED FROM EVIDENCE (WP-5C Rollback Recovery, 2026-07-13).
--   Source of truth: the forward migration file 003_reference_tier1.sql (the authoritative record of exactly what
--   this migration created). No original rollback existed for 001-020 (never authored — see
--   REPO-WP-02 discovery); the 021-026 rollbacks were lost in the apverse-labs repository loss
--   and are reconstructed from the WP-5B-recovered forward migrations.
--   APPLY ORDER: rollbacks run in REVERSE (028 -> 001). Each reverses ONLY what its own migration
--   created and assumes later migrations are already rolled back. Plain DROP / RESTRICT are used
--   deliberately so out-of-order or on-populated-data application FAILS LOUDLY rather than
--   cascading silently — matching the 027/028 rollback precedent.

DROP TABLE public.meal_classes;
DROP TABLE re_engine.re_meal_classes;
DROP TABLE re_engine.re_routing_rules;
DROP TABLE re_engine.re_subcohorts;
DROP TABLE re_engine.re_personas;
