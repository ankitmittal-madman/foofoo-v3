DO $$
DECLARE
  constraint_definition text;
BEGIN
  SELECT pg_get_constraintdef(oid) INTO constraint_definition
  FROM pg_constraint
  WHERE conrelid = 'public.outcome_events'::regclass
    AND conname = 'outcome_events_outcome_type_check';

  IF constraint_definition IS NULL
     OR position('liked' IN constraint_definition) = 0
     OR position('disliked' IN constraint_definition) = 0 THEN
    RAISE EXCEPTION 'outcome_events does not accept explicit liked/disliked outcomes';
  END IF;

  IF to_regprocedure('ml.preference_training_readiness(integer,integer)') IS NULL THEN
    RAISE EXCEPTION 'preference training readiness function is missing';
  END IF;

  IF to_regprocedure('ml.preference_training_export_rows()') IS NULL THEN
    RAISE EXCEPTION 'point-in-time preference training export function is missing';
  END IF;

  IF has_function_privilege(
    'authenticated',
    'ml.preference_training_readiness(integer,integer)',
    'EXECUTE'
  ) THEN
    RAISE EXCEPTION 'preference training readiness function is exposed to authenticated clients';
  END IF;

  IF has_function_privilege(
    'authenticated',
    'ml.preference_training_export_rows()',
    'EXECUTE'
  ) THEN
    RAISE EXCEPTION 'preference training export is exposed to authenticated clients';
  END IF;

  IF position(
    'household_snapshot' IN pg_get_functiondef(
      'public.record_episode_recommendation_lineage(jsonb)'::regprocedure
    )
  ) = 0 THEN
    RAISE EXCEPTION 'recommendation lineage does not retain point-in-time household features';
  END IF;
END $$;

SELECT * FROM ml.preference_training_readiness(10000, 500);
