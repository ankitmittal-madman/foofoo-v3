DROP INDEX IF EXISTS public.recommendation_events_aux_shadow_version_idx;
ALTER TABLE public.recommendation_events
  DROP CONSTRAINT IF EXISTS recommendation_events_aux_shadow_observation_shape;
ALTER TABLE public.recommendation_events
  DROP COLUMN IF EXISTS aux_shadow_observation;
