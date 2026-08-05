DO $$
BEGIN
  IF (SELECT count(*) FROM food.meal_episodes WHERE catalog_status='published') < (SELECT count(*) FROM public.dishes WHERE is_active) THEN
    RAISE EXCEPTION 'every active dish must have at least one published episode';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM ml.model_registry WHERE model_name='episode_success' AND stage='production') THEN
    RAISE EXCEPTION 'episode success baseline is not registered';
  END IF;
  IF to_regprocedure('public.replay_recommendation_slate(uuid)') IS NULL THEN
    RAISE EXCEPTION 'slate replay function missing';
  END IF;
END $$;
