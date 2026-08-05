-- Run inside an explicit transaction and roll it back. Uses existing identities but leaves no data.
DO $test$
DECLARE
  target_household uuid;
  original_owner uuid;
  temporary_owner uuid;
  matching_event_count integer;
BEGIN
  -- Management-API validation has no JWT by default; exercise the service-role
  -- branch used by Edge for cross-user owner transitions.
  PERFORM set_config('request.jwt.claim.role', 'service_role', true);
  SELECT h.id, h.owner_user_id INTO target_household, original_owner
  FROM public.households h WHERE h.status = 'active' ORDER BY h.created_at LIMIT 1;
  SELECT u.id INTO temporary_owner
  FROM auth.users u
  WHERE u.id <> original_owner
    AND NOT EXISTS (
      SELECT 1 FROM public.household_memberships hm
      WHERE hm.household_id = target_household AND hm.user_id = u.id
    )
  ORDER BY u.created_at LIMIT 1;
  IF target_household IS NULL OR temporary_owner IS NULL THEN
    RAISE EXCEPTION 'household role smoke fixture identities unavailable';
  END IF;

  INSERT INTO public.household_memberships (household_id, user_id, role_code, status)
  VALUES (target_household, temporary_owner, 'member', 'active');
  PERFORM public.transfer_household_ownership(
    target_household, original_owner, temporary_owner
  );
  IF NOT public.has_household_role(
    target_household, temporary_owner, ARRAY['owner']::text[]
  ) THEN
    RAISE EXCEPTION 'owner transfer did not activate the target owner';
  END IF;

  PERFORM public.transfer_household_ownership(
    target_household, temporary_owner, original_owner
  );
  PERFORM public.revoke_household_membership(
    target_household, original_owner, temporary_owner
  );
  IF public.has_household_role(target_household, temporary_owner) THEN
    RAISE EXCEPTION 'revoked membership still has household access';
  END IF;

  SELECT count(*) INTO matching_event_count
  FROM public.household_membership_events e
  WHERE e.household_id = target_household AND e.user_id = temporary_owner
    AND e.event_type IN ('activated','owner_transferred','revoked');
  IF matching_event_count < 3 THEN
    RAISE EXCEPTION 'membership event history incomplete: %', matching_event_count;
  END IF;
END
$test$;

SET CONSTRAINTS ALL IMMEDIATE;
