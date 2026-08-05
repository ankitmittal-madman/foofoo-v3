SELECT h.id AS household_without_exactly_one_owner
FROM public.households h
LEFT JOIN public.household_memberships hm
  ON hm.household_id = h.id AND hm.role_code = 'owner' AND hm.status = 'active'
WHERE h.status <> 'deleting'
GROUP BY h.id
HAVING count(hm.user_id) <> 1;

SELECT h.id AS household_owner_projection_mismatch
FROM public.households h
LEFT JOIN public.household_memberships hm
  ON hm.household_id = h.id AND hm.user_id = h.owner_user_id
 AND hm.role_code = 'owner' AND hm.status = 'active'
WHERE h.status <> 'deleting' AND hm.user_id IS NULL;

SELECT hm.household_id, hm.user_id AS membership_without_history
FROM public.household_memberships hm
LEFT JOIN public.household_membership_events e
  ON e.household_id = hm.household_id AND e.user_id = hm.user_id
WHERE e.id IS NULL;

SELECT signature AS client_executable_role_rpc
FROM (VALUES
  ('public.transfer_household_ownership(uuid,uuid,uuid)'),
  ('public.change_household_member_role(uuid,uuid,uuid,text)'),
  ('public.revoke_household_membership(uuid,uuid,uuid)'),
  ('public.leave_household(uuid,uuid)'),
  ('public.create_household_invite(uuid,uuid,text,text,timestamptz)'),
  ('public.accept_household_invite(text,uuid)')
) functions(signature)
WHERE has_function_privilege('anon', signature::regprocedure, 'EXECUTE')
   OR has_function_privilege('authenticated', signature::regprocedure, 'EXECUTE');

SELECT policyname AS missing_role_aware_policy
FROM (VALUES
  ('households_select_member'),
  ('memberships_select_household'),
  ('invites_select_owner'),
  ('membership_events_select_household')
) expected(policyname)
WHERE NOT EXISTS (
  SELECT 1 FROM pg_policies p WHERE p.schemaname = 'public' AND p.policyname = expected.policyname
);
