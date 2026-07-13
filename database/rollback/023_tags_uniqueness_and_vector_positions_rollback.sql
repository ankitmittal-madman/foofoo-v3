-- Rollback: 023_tags_uniqueness_and_vector_positions_rollback.sql
-- Reverses: 023_tags_uniqueness_and_vector_positions.sql
-- RECONSTRUCTED FROM EVIDENCE (WP-5C Rollback Recovery, 2026-07-13).
--   Source of truth: the forward migration file 023_tags_uniqueness_and_vector_positions.sql (the authoritative record of exactly what
--   this migration created). No original rollback existed for 001-020 (never authored — see
--   REPO-WP-02 discovery); the 021-026 rollbacks were lost in the apverse-labs repository loss
--   and are reconstructed from the WP-5B-recovered forward migrations.
--   APPLY ORDER: rollbacks run in REVERSE (028 -> 001). Each reverses ONLY what its own migration
--   created and assumes later migrations are already rolled back. Plain DROP / RESTRICT are used
--   deliberately so out-of-order or on-populated-data application FAILS LOUDLY rather than
--   cascading silently — matching the 027/028 rollback precedent.
--
-- WARNING: re-adding the ORIGINAL global UNIQUE(tag_name) restores the Batch-3 uniqueness
--   conflict. If tag rows exist where the same tag_name appears under different dimensions
--   (e.g. "light"/"none"), this ADD CONSTRAINT will FAIL LOUDLY — expected and correct. On the
--   currently-unseeded table it reverses cleanly.

DROP FUNCTION public.fn_assign_tag_vector_positions();
ALTER TABLE public.tags DROP CONSTRAINT tags_dimension_tag_name_key;
ALTER TABLE public.tags ADD CONSTRAINT tags_tag_name_key UNIQUE (tag_name);
