DO $$
BEGIN
  IF to_regprocedure('public.refresh_user_re_state(uuid)') IS NULL THEN
    RAISE EXCEPTION 'public.refresh_user_re_state(uuid) is missing';
  END IF;
  IF has_function_privilege('anon', 'public.refresh_user_re_state(uuid)', 'EXECUTE')
     OR has_function_privilege('authenticated',
       'public.refresh_user_re_state(uuid)', 'EXECUTE') THEN
    RAISE EXCEPTION 'user recommendation state refresh must be service-role only';
  END IF;
  IF EXISTS (
    SELECT 1 FROM public.user_re_state s
    WHERE s.interaction_count < 0
       OR s.cold_start_mode <> (s.interaction_count < 14)
       OR s.weight_tier IS DISTINCT FROM CASE
         WHEN s.interaction_count <= 10 THEN 'cold_start'
         WHEN s.interaction_count <= 50 THEN 'early'
         WHEN s.interaction_count <= 150 THEN 'emerging'
         WHEN s.interaction_count <= 500 THEN 'established'
         ELSE 'mature'
       END
  ) THEN
    RAISE EXCEPTION 'user recommendation state violates lifecycle invariants';
  END IF;
END $$;

SELECT count(*) AS populated_user_re_states FROM public.user_re_state;
