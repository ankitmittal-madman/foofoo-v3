DO $$
BEGIN
  IF to_regclass('re_engine.recommendation_item_exposures') IS NULL
     OR to_regclass('re_engine.variety_window_state') IS NULL THEN
    RAISE EXCEPTION 'recommendation exposure/variety tables are missing';
  END IF;
  IF to_regprocedure('public.record_recommendation_exposure_state(uuid,jsonb)') IS NULL
     OR to_regprocedure('public.get_recommendation_variety_state(uuid)') IS NULL THEN
    RAISE EXCEPTION 'recommendation variety RPCs are missing';
  END IF;
  IF has_function_privilege('anon',
       'public.record_recommendation_exposure_state(uuid,jsonb)', 'EXECUTE')
     OR has_function_privilege('authenticated',
       'public.record_recommendation_exposure_state(uuid,jsonb)', 'EXECUTE')
     OR has_function_privilege('anon',
       'public.get_recommendation_variety_state(uuid)', 'EXECUTE')
     OR has_function_privilege('authenticated',
       'public.get_recommendation_variety_state(uuid)', 'EXECUTE') THEN
    RAISE EXCEPTION 'recommendation variety RPCs must remain service-role only';
  END IF;
END $$;

SELECT count(*) AS exposure_rows FROM re_engine.recommendation_item_exposures;
SELECT count(*) AS variety_rows FROM re_engine.variety_window_state;
