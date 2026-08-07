-- Resolve feedback names to one canonical public.dishes row without silently choosing among
-- ambiguous aliases. Canonical names are highest priority; only sourced/ingestion-proven aliases
-- participate. Groq-inferred aliases remain review evidence, not identity authority.

CREATE OR REPLACE FUNCTION public.resolve_canonical_dish_identity(p_name text)
RETURNS TABLE(dish_id uuid, canonical_name text, match_source text)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = pg_catalog, public
AS $function$
  WITH input AS (
    SELECT lower(regexp_replace(btrim(p_name), '[[:space:]]+', ' ', 'g')) AS normalized_name
  ), matches AS (
    SELECT d.id AS dish_id, 0 AS priority, 'canonical_name'::text AS match_source
    FROM public.dishes d, input i
    WHERE lower(regexp_replace(btrim(d.name), '[[:space:]]+', ' ', 'g')) = i.normalized_name

    UNION ALL

    SELECT d.id, 1, 'regional_name'
    FROM public.dishes d, input i
    WHERE i.normalized_name IN (
      lower(regexp_replace(btrim(d.name_hindi), '[[:space:]]+', ' ', 'g')),
      lower(regexp_replace(btrim(d.name_regional), '[[:space:]]+', ' ', 'g'))
    )

    UNION ALL

    SELECT s.dish_id, 1, 'curated_synonym'
    FROM public.dish_name_synonyms s, input i
    WHERE s.data_source = 'real'
      AND lower(regexp_replace(btrim(s.synonym), '[[:space:]]+', ' ', 'g')) = i.normalized_name

    UNION ALL

    SELECT a.dish_id, 2, 'ingestion_alias'
    FROM public.dish_aliases a, input i
    WHERE a.alias_source IN ('csv_translated_name', 'csv_original_name', 'dedupe_merge')
      AND lower(regexp_replace(btrim(a.alias_text), '[[:space:]]+', ' ', 'g')) = i.normalized_name
  ), prioritized AS (
    SELECT matches.*, min(priority) OVER () AS best_priority FROM matches
  ), distinct_best AS (
    SELECT dish_id, min(match_source) AS match_source
    FROM prioritized WHERE priority = best_priority GROUP BY dish_id
  ), unambiguous AS (
    SELECT *, count(*) OVER () AS match_count FROM distinct_best
  )
  SELECT u.dish_id, d.name, u.match_source
  FROM unambiguous u
  JOIN public.dishes d ON d.id = u.dish_id
  WHERE u.match_count = 1 AND nullif(btrim(p_name), '') IS NOT NULL;
$function$;

REVOKE ALL ON FUNCTION public.resolve_canonical_dish_identity(text)
  FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.resolve_canonical_dish_identity(text) TO service_role;

COMMENT ON FUNCTION public.resolve_canonical_dish_identity(text) IS
  'Service-role-only canonical dish resolver. Returns no row for unknown or ambiguous aliases; canonical names take precedence.';

-- Repair identity-less historical feedback only where the new resolver proves one canonical row.
-- Preserve the supplied display name and add the resolved canonical name as separate evidence.
WITH resolved AS (
  SELECT f.id, identity.dish_id, identity.canonical_name
  FROM public.feedback_events f
  CROSS JOIN LATERAL public.resolve_canonical_dish_identity(
    coalesce(nullif(f.detail->>'canonical_dish_name', ''), nullif(f.detail->>'dish_name', ''))
  ) identity
  WHERE f.dish_id IS NULL AND f.data_source = 'real'
)
UPDATE public.feedback_events f
SET dish_id = resolved.dish_id,
    detail = jsonb_set(
      coalesce(f.detail, '{}'::jsonb), '{canonical_dish_name}',
      to_jsonb(resolved.canonical_name), true
    )
FROM resolved WHERE f.id = resolved.id;

-- Rebuild generalized taste projections because newly resolved dish IDs can now contribute their
-- class and semantic tags. This is deterministic replay of explicit feedback, not a new signal.
DO $refresh$
DECLARE v_profile_id uuid;
BEGIN
  FOR v_profile_id IN
    SELECT DISTINCT profile_id FROM public.feedback_events
    WHERE data_source = 'real'
      AND event_type IN ('like','accept','make_this','cooked','completed','dislike','never')
  LOOP
    PERFORM public.refresh_user_taste_vector(v_profile_id);
  END LOOP;
END
$refresh$;
