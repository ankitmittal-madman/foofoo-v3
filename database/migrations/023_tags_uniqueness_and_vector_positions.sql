-- Migration: 023_tags_uniqueness_and_vector_positions.sql
-- ============================================================================
-- RECONSTRUCTED FROM EVIDENCE — WP-5B Migration Recovery, 2026-07-13
-- ============================================================================
-- Original authored/applied 2026-07-06 (Supabase version 20260706092216, name
-- "023_tags_uniqueness_and_vector_positions"; REPO-WP-02 §7.6, commit 4ed5e91);
-- lost in the repository migration. Reconstructed to reproduce the exact live
-- state in project slsqtlygeekdppuyiiff, observed read-only 2026-07-13.
--
-- Evidence:
--   * base migration 002 created public.tags with tag_name globally UNIQUE
--     (constraint tags_tag_name_key) — the Batch-3 uniqueness conflict
--     ("light"/"none" collide across dimensions).
--   * live introspection now shows: NO tags_tag_name_key; a UNIQUE(dimension,
--     tag_name) constraint (tags_dimension_tag_name_key); vector_position still
--     NOT NULL UNIQUE (from base 002). => 023 dropped the global unique and
--     added the composite unique.
--   * function public.fn_assign_tag_vector_positions() body below is recovered
--     VERBATIM via pg_get_functiondef() (WP-5B, 2026-07-13).
--   * REPO-WP-02 §7.6: "tags uniqueness conflict resolved; vector_position
--     mechanism codified (tier ascending, dimension, tag_name A-Z)."
-- Confidence: HIGH. The function body is verbatim; the two constraint changes
--   are exact. vector_position column itself pre-existed in base 002 (unchanged).
-- ============================================================================

-- Resolve the Batch-3 uniqueness conflict: tag names are unique per dimension,
-- not globally.
ALTER TABLE public.tags DROP CONSTRAINT tags_tag_name_key;
ALTER TABLE public.tags ADD CONSTRAINT tags_dimension_tag_name_key UNIQUE (dimension, tag_name);

-- Deterministic tag genome-vector position assignment, called at seed time
-- (no trigger — confirmed no trigger exists on public.tags).
CREATE OR REPLACE FUNCTION public.fn_assign_tag_vector_positions()
 RETURNS integer
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public', 'pg_catalog'
AS $function$
DECLARE
  v_updated integer;
BEGIN
  WITH ordered AS (
    SELECT id, row_number() OVER (ORDER BY tier ASC, dimension ASC, tag_name ASC) - 1 AS pos
    FROM public.tags
  )
  UPDATE public.tags t
     SET vector_position = o.pos + 100000
  FROM ordered o WHERE o.id = t.id;

  WITH ordered AS (
    SELECT id, row_number() OVER (ORDER BY tier ASC, dimension ASC, tag_name ASC) - 1 AS pos
    FROM public.tags
  )
  UPDATE public.tags t
     SET vector_position = o.pos
  FROM ordered o WHERE o.id = t.id;

  GET DIAGNOSTICS v_updated = ROW_COUNT;
  RETURN v_updated;
END;
$function$;
