DROP FUNCTION IF EXISTS re_engine.production_guardrail_aggregate(
  timestamptz, timestamptz, text
);

DROP INDEX IF EXISTS public.recommendation_events_guardrail_version_time_idx;

ALTER TABLE public.recommendation_events
  DROP CONSTRAINT IF EXISTS recommendation_events_production_guardrail_observation_shape,
  DROP COLUMN IF EXISTS production_guardrail_observation;
