DO $$
BEGIN
  IF to_regprocedure('ml.preference_shadow_evaluation()') IS NULL THEN
    RAISE EXCEPTION 'ml.preference_shadow_evaluation() is missing';
  END IF;
  IF has_function_privilege('anon', 'ml.preference_shadow_evaluation()', 'EXECUTE')
     OR has_function_privilege('authenticated', 'ml.preference_shadow_evaluation()', 'EXECUTE') THEN
    RAISE EXCEPTION 'shadow evaluation must not be exposed to client roles';
  END IF;
  IF has_function_privilege('anon', 'ml.preference_training_export_rows()', 'EXECUTE')
     OR has_function_privilege('authenticated', 'ml.preference_training_export_rows()', 'EXECUTE') THEN
    RAISE EXCEPTION 'training export must not be exposed to client roles';
  END IF;
END $$;

SELECT * FROM ml.preference_shadow_evaluation();
