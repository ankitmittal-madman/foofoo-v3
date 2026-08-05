-- SECURITY DEFINER changes current_user to the function owner. Use session/JWT identity so an
-- authenticated caller cannot probe another user's household membership through the helper.
-- Only JWT identity is authoritative; function-owner identity would defeat the boundary.

CREATE OR REPLACE FUNCTION public.has_household_role(
  p_household_id uuid,
  p_user_id uuid,
  p_allowed_roles text[] DEFAULT ARRAY['owner','planner','cook','member','viewer']::text[]
)
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = pg_catalog, public
AS $function$
  SELECT EXISTS (
    SELECT 1 FROM public.household_memberships hm
    WHERE hm.household_id = p_household_id
      AND hm.user_id = p_user_id
      AND hm.status = 'active'
      AND hm.role_code = ANY (p_allowed_roles)
      AND (
        (SELECT auth.role()) = 'service_role'
        OR p_user_id = (SELECT auth.uid())
      )
  )
$function$;

REVOKE ALL ON FUNCTION public.has_household_role(uuid, uuid, text[]) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.has_household_role(uuid, uuid, text[])
  TO authenticated, service_role;
