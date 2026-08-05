BEGIN;

SELECT set_config(
  'request.jwt.claim.sub',
  (SELECT user_id::text FROM public.household_memberships WHERE status = 'active' ORDER BY joined_at LIMIT 1),
  true
);
SELECT set_config('request.jwt.claim.role', 'authenticated', true);
SELECT set_config(
  'app.validation_household_id',
  (SELECT household_id::text FROM public.household_memberships WHERE user_id = auth.uid() AND status = 'active' ORDER BY joined_at LIMIT 1),
  true
);
SELECT set_config(
  'app.validation_other_user_id',
  coalesce((SELECT user_id::text FROM public.household_memberships WHERE user_id <> auth.uid() AND status = 'active' ORDER BY joined_at LIMIT 1), ''),
  true
);
SELECT set_config(
  'app.validation_other_household_id',
  coalesce((SELECT household_id::text FROM public.household_memberships WHERE user_id <> auth.uid() AND status = 'active' ORDER BY joined_at LIMIT 1), ''),
  true
);

SET LOCAL ROLE authenticated;

DO $$
DECLARE
  self_user_id uuid := auth.uid();
  household_id uuid := current_setting('app.validation_household_id')::uuid;
  other_user_text text := current_setting('app.validation_other_user_id');
  other_household_text text := current_setting('app.validation_other_household_id');
BEGIN
  IF NOT public.has_household_role(household_id, self_user_id) THEN
    RAISE EXCEPTION 'authenticated caller cannot resolve own active membership';
  END IF;
  IF other_user_text <> '' AND public.has_household_role(
    other_household_text::uuid, other_user_text::uuid
  ) THEN
    RAISE EXCEPTION 'authenticated caller can probe another user membership';
  END IF;
END $$;

RESET ROLE;
ROLLBACK;
