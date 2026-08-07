DROP FUNCTION IF EXISTS public.get_meal_class_temporal_state(uuid);
DROP FUNCTION IF EXISTS public.record_meal_class_exposure_state(uuid, jsonb);
DROP FUNCTION IF EXISTS public.refresh_meal_class_temporal_state(uuid);
DROP TRIGGER IF EXISTS feedback_events_validate_meal_moment ON public.feedback_events;
DROP FUNCTION IF EXISTS public.validate_recommendation_meal_moment();
DROP TABLE IF EXISTS re_engine.meal_class_temporal_state;
DROP TABLE IF EXISTS re_engine.meal_class_exposures;
