-- Complete the expand-phase household backfill and prevent new profile/tenant drift.

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

DROP TRIGGER IF EXISTS profiles_provision_household ON public.profiles;
CREATE TRIGGER profiles_provision_household
AFTER INSERT ON public.profiles
FOR EACH ROW EXECUTE FUNCTION public.provision_profile_household();

-- Reconcile profiles created after migration 055 was applied.
INSERT INTO public.households (id, name, household_type_code, owner_user_id, created_at, updated_at)
SELECT p.id, coalesce(nullif(p.primary_cook_name, ''), 'My household'), NULL, p.id,
       p.created_at, p.updated_at
FROM public.profiles p
ON CONFLICT (id) DO NOTHING;

INSERT INTO public.household_memberships (household_id, user_id, role_code, status, joined_at)
SELECT p.id, p.id, 'owner', 'active', p.created_at
FROM public.profiles p
ON CONFLICT (household_id, user_id) DO UPDATE
  SET role_code = 'owner', status = 'active', revoked_at = NULL;

UPDATE public.week_plans SET household_id = profile_id WHERE household_id IS NULL;
UPDATE public.recommendation_events SET household_id = profile_id WHERE household_id IS NULL;
UPDATE public.feedback_events SET household_id = profile_id WHERE household_id IS NULL;
UPDATE public.product_events SET household_id = profile_id WHERE household_id IS NULL;
UPDATE public.household_context SET household_id = profile_id WHERE household_id IS NULL;

ALTER TABLE public.week_plans ALTER COLUMN household_id SET NOT NULL;
ALTER TABLE public.recommendation_events ALTER COLUMN household_id SET NOT NULL;
ALTER TABLE public.feedback_events ALTER COLUMN household_id SET NOT NULL;
ALTER TABLE public.product_events ALTER COLUMN household_id SET NOT NULL;
ALTER TABLE public.household_context ALTER COLUMN household_id SET NOT NULL;
