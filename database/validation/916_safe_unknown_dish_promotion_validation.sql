DO $$
BEGIN
  IF to_regprocedure('public.promote_submission_if_safe(uuid)') IS NULL THEN
    RAISE EXCEPTION 'promote_submission_if_safe(uuid) is missing';
  END IF;
END $$;
