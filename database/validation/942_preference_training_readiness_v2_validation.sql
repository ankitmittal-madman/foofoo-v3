DO $$
BEGIN
  IF to_regprocedure('ml.preference_training_readiness_v2(integer,integer)') IS NULL THEN
    RAISE EXCEPTION 'ml.preference_training_readiness_v2(integer,integer) is missing';
  END IF;
  IF has_function_privilege(
    'anon', 'ml.preference_training_readiness_v2(integer,integer)', 'EXECUTE'
  ) OR has_function_privilege(
    'authenticated', 'ml.preference_training_readiness_v2(integer,integer)', 'EXECUTE'
  ) THEN
    RAISE EXCEPTION 'preference readiness v2 must remain service-role only';
  END IF;
END $$;

SELECT * FROM ml.preference_training_readiness_v2(10000, 500);
