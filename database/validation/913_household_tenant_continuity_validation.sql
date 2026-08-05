SELECT p.id AS profile_without_household
FROM public.profiles p
LEFT JOIN public.households h ON h.id = p.id
WHERE h.id IS NULL;

SELECT p.id AS profile_without_active_owner_membership
FROM public.profiles p
LEFT JOIN public.household_memberships membership
  ON membership.household_id = p.id
 AND membership.user_id = p.id
 AND membership.role_code = 'owner'
 AND membership.status = 'active'
WHERE membership.user_id IS NULL;

SELECT table_name, is_nullable
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name IN (
    'week_plans', 'recommendation_events', 'feedback_events',
    'product_events', 'household_context'
  )
  AND column_name = 'household_id'
  AND is_nullable <> 'NO';

SELECT count(*) AS public_profile_provision_execute_grants
FROM (VALUES ('anon'), ('authenticated')) AS roles(role_name)
WHERE has_function_privilege(
  role_name,
  'public.provision_profile_household()'::regprocedure,
  'EXECUTE'
);
