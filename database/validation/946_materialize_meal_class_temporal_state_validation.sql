DO $$
BEGIN
  IF to_regclass('re_engine.meal_class_exposures') IS NULL OR
     to_regclass('re_engine.meal_class_temporal_state') IS NULL THEN
    RAISE EXCEPTION 'meal-class temporal tables are missing';
  END IF;
  IF to_regprocedure('public.refresh_meal_class_temporal_state(uuid)') IS NULL OR
     to_regprocedure('public.record_meal_class_exposure_state(uuid,jsonb)') IS NULL OR
     to_regprocedure('public.get_meal_class_temporal_state(uuid)') IS NULL THEN
    RAISE EXCEPTION 'meal-class temporal RPCs are missing';
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM pg_trigger
    WHERE tgrelid = 'public.feedback_events'::regclass
      AND tgname = 'feedback_events_validate_meal_moment' AND NOT tgisinternal
  ) THEN
    RAISE EXCEPTION 'meal moment consistency trigger is missing';
  END IF;
  IF has_function_privilege('anon', 'public.get_meal_class_temporal_state(uuid)', 'EXECUTE') OR
     has_function_privilege('authenticated', 'public.get_meal_class_temporal_state(uuid)', 'EXECUTE') THEN
    RAISE EXCEPTION 'meal-class temporal state must remain service-only';
  END IF;
  IF EXISTS (
    SELECT 1 FROM re_engine.meal_class_temporal_state
    WHERE meal_slot NOT IN ('breakfast','lunch','dinner')
       OR day_type NOT IN ('weekday','weekend')
       OR explicit_positive_count_28d < 0
       OR explicit_negative_count_28d < 0
       OR exposure_count_14d < 0
  ) THEN
    RAISE EXCEPTION 'invalid temporal state row';
  END IF;
END $$;

SELECT meal_slot, day_type, count(*) AS state_rows,
  sum(explicit_positive_count_28d) AS explicit_positive_events,
  sum(explicit_negative_count_28d) AS explicit_negative_events,
  sum(exposure_count_14d) AS class_impressions
FROM re_engine.meal_class_temporal_state
GROUP BY meal_slot, day_type
ORDER BY meal_slot, day_type;
