DROP POLICY IF EXISTS membership_events_select_household ON public.household_membership_events;
DROP POLICY IF EXISTS invites_select_owner ON public.household_invites;
DROP POLICY IF EXISTS memberships_select_household ON public.household_memberships;
DROP POLICY IF EXISTS households_select_member ON public.households;

CREATE POLICY households_select_member ON public.households FOR SELECT USING (
  EXISTS (SELECT 1 FROM public.household_memberships hm
          WHERE hm.household_id = id AND hm.user_id = (SELECT auth.uid()) AND hm.status = 'active')
);
CREATE POLICY memberships_select_self ON public.household_memberships FOR SELECT
  USING (user_id = (SELECT auth.uid()));
CREATE POLICY invites_select_member ON public.household_invites FOR SELECT USING (
  EXISTS (SELECT 1 FROM public.household_memberships hm
          WHERE hm.household_id = household_invites.household_id
            AND hm.user_id = (SELECT auth.uid()) AND hm.status = 'active')
);

DROP TRIGGER IF EXISTS household_memberships_record_event ON public.household_memberships;
DROP TRIGGER IF EXISTS household_memberships_one_owner ON public.household_memberships;
DROP TRIGGER IF EXISTS households_one_owner ON public.households;
DROP FUNCTION IF EXISTS public.accept_household_invite(text,uuid);
DROP FUNCTION IF EXISTS public.create_household_invite(uuid,uuid,text,text,timestamptz);
DROP FUNCTION IF EXISTS public.leave_household(uuid,uuid);
DROP FUNCTION IF EXISTS public.revoke_household_membership(uuid,uuid,uuid);
DROP FUNCTION IF EXISTS public.change_household_member_role(uuid,uuid,uuid,text);
DROP FUNCTION IF EXISTS public.transfer_household_ownership(uuid,uuid,uuid);
DROP FUNCTION IF EXISTS public.has_household_role(uuid,uuid,text[]);
DROP FUNCTION IF EXISTS public.record_household_membership_event();
DROP FUNCTION IF EXISTS public.assert_household_has_one_owner();
DROP INDEX IF EXISTS public.uq_household_one_active_owner;
DROP INDEX IF EXISTS public.idx_household_memberships_user_active;
DROP TABLE IF EXISTS public.household_membership_events;

-- Restore the migration-059 compatibility provisioner. The forward migration
-- adds actor context for membership-event provenance; after the audit trigger
-- is removed the earlier implementation is the correct rollback target.
CREATE OR REPLACE FUNCTION public.provision_profile_household()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public
AS $function$
BEGIN
  INSERT INTO public.households (
    id, name, household_type_code, owner_user_id, created_at, updated_at
  ) VALUES (
    NEW.id,
    coalesce(nullif(NEW.primary_cook_name, ''), 'My household'),
    NULL,
    NEW.id,
    NEW.created_at,
    NEW.updated_at
  )
  ON CONFLICT (id) DO UPDATE
    SET owner_user_id = EXCLUDED.owner_user_id,
        updated_at = greatest(public.households.updated_at, EXCLUDED.updated_at);

  INSERT INTO public.household_memberships (
    household_id, user_id, role_code, status, joined_at, revoked_at
  ) VALUES (
    NEW.id, NEW.id, 'owner', 'active', NEW.created_at, NULL
  )
  ON CONFLICT (household_id, user_id) DO UPDATE
    SET role_code = 'owner', status = 'active', revoked_at = NULL;
  RETURN NEW;
END
$function$;

REVOKE EXECUTE ON FUNCTION public.provision_profile_household()
  FROM PUBLIC, anon, authenticated;
