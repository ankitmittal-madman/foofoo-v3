-- Renamed 2026-08-04 from WP-3D_Check2_Fix_Reference.sql to 999_check2_fix_reference_superseded.sql
-- to conform to the NNN_description.sql validation-band naming standard (WP-5AA) — authorized as
-- part of a Founder-directed backlog closeout session (2026-08-04); 999 chosen deliberately outside
-- the sequential 900-909 real-check band since this file is a historical reference, never executed
-- standalone, not a runnable validation check.
--
-- SUPERSEDED (2026-08-04): Check 2's underlying bug (search-path-sensitive conrelid::regclass::text
-- comparison) was independently fixed a different way, under WP-6E3, in the live file
-- (900_structural_validation.sql's Check 2 now uses conrelid = ANY(ARRAY[...]::regclass[]) — verify
-- there directly rather than trusting this note). The join-based rewrite proposed below was never
-- applied and is now moot. Kept only as a historical record of the originally-proposed approach;
-- do not apply it.
--
-- Reference only — this was the proposed fix for Check 2 in 900_structural_validation.sql,
-- provided for founder review before Claude Code applies it as part of WP-3D.
-- Do NOT run this standalone against production; it is a snippet to replace the existing
-- Check 2 block in the live file, not a new migration.

-- CURRENT (confirmed broken — returns empty despite all 7 target FKs existing):
--
-- \echo '--- Check 2: Safety-critical FKs present ---'
-- SELECT conname, conrelid::regclass AS table_name
-- FROM pg_constraint
-- WHERE contype = 'f'
--   AND conrelid::regclass::text IN ('public.dish_ingredients','public.plan_slots','public.dishes')
-- ORDER BY table_name;

-- PROPOSED FIX — join through pg_class/pg_namespace instead of relying on regclass::text
-- string matching, which is sensitive to search_path and doesn't reliably match a
-- schema-qualified literal:

\echo '--- Check 2: Safety-critical FKs present ---'
SELECT
  con.conname,
  ns.nspname || '.' || cls.relname AS table_name
FROM pg_constraint con
JOIN pg_class cls ON cls.oid = con.conrelid
JOIN pg_namespace ns ON ns.oid = cls.relnamespace
WHERE con.contype = 'f'
  AND ns.nspname = 'public'
  AND cls.relname IN ('dish_ingredients', 'plan_slots', 'dishes')
ORDER BY table_name;

-- Expected result after fix: 7 rows (2 from dish_ingredients, 2 from dishes, 3 from plan_slots)
-- per this session's independent live verification.
