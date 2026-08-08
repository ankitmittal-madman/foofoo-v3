-- Publish canonical dish identity independently from recommendation eligibility.
--
-- The safety-closed catalogue publication intentionally excludes incomplete dishes. Ghar's
-- immutable fallback can still rank those dishes, so it needs an exact name -> UUID boundary for
-- feedback lineage plus governed regional soft-ranking metadata, without treating an incomplete
-- dish as database-eligible. These functions are read-only, contain no user data and remain
-- service-role only.

CREATE OR REPLACE FUNCTION re_engine.catalogue_identity_coverage()
RETURNS bigint
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public, re_engine, pg_temp
AS $$
  SELECT count(*) FROM public.dishes;
$$;

CREATE OR REPLACE FUNCTION re_engine.catalogue_identity_rows(
  p_after uuid DEFAULT NULL,
  p_limit integer DEFAULT 500
)
RETURNS TABLE (dish_id uuid, name text, regional_affinities jsonb)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public, re_engine, pg_temp
AS $$
  SELECT
    d.id,
    d.name,
    coalesce((
      SELECT jsonb_agg(jsonb_build_object(
        'region_code', r.region_code,
        'affinity_score', r.affinity_score,
        'confidence', r.confidence,
        'review_status', r.review_status
      ) ORDER BY r.affinity_score DESC, r.region_code)
      FROM public.dish_regional_affinities r
      WHERE r.dish_id = d.id
        AND r.review_status <> 'rejected'
    ), '[]'::jsonb)
  FROM public.dishes d
  WHERE p_after IS NULL OR d.id > p_after
  ORDER BY d.id
  LIMIT least(greatest(coalesce(p_limit, 500), 1), 2000);
$$;

REVOKE ALL ON FUNCTION re_engine.catalogue_identity_coverage()
  FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION re_engine.catalogue_identity_rows(uuid, integer)
  FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION re_engine.catalogue_identity_coverage() TO service_role;
GRANT EXECUTE ON FUNCTION re_engine.catalogue_identity_rows(uuid, integer) TO service_role;

COMMENT ON FUNCTION re_engine.catalogue_identity_rows(uuid, integer) IS
  'Streams canonical dish UUID/name pairs plus governed regional soft-ranking metadata; does not assert serving eligibility and contains no user data.';
