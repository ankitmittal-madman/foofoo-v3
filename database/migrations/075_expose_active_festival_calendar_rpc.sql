-- Keep the governed festival calendar private while allowing Edge Functions to resolve the
-- festivals active on one date. PostgREST does not expose re_engine, so callers must use this
-- narrowly scoped, service-role-only facade instead of querying the schema directly.

CREATE OR REPLACE FUNCTION public.active_festivals_on(p_date date)
RETURNS TABLE (
  festival_name text,
  start_date date,
  end_date date
)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = pg_catalog, re_engine
AS $function$
  SELECT f.festival_name, f.start_date, f.end_date
  FROM re_engine.re_festival_calendar AS f
  WHERE p_date BETWEEN f.start_date AND f.end_date
  ORDER BY f.festival_name
$function$;

REVOKE ALL ON FUNCTION public.active_festivals_on(date) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.active_festivals_on(date) TO service_role;
