-- Publish canonical dish identity independently from recommendation eligibility.
--
-- The safety-closed catalogue publication intentionally excludes incomplete dishes. Ghar's
-- immutable fallback can still rank those dishes, so it needs an exact name -> UUID boundary for
-- feedback lineage without treating an incomplete dish as database-eligible. These functions are
-- read-only, contain no user data and remain service-role only.

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
RETURNS TABLE (dish_id uuid, name text)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public, re_engine, pg_temp
AS $$
  SELECT d.id, d.name
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
  'Streams canonical dish UUID/name pairs for identity reconciliation only; does not assert serving eligibility and contains no user data.';
