DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public'
      AND table_name = 'recommendation_events'
      AND column_name = 'aux_shadow_observation'
      AND data_type = 'jsonb'
  ) THEN
    RAISE EXCEPTION 'recommendation_events.aux_shadow_observation is missing';
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'recommendation_events_aux_shadow_observation_shape'
      AND conrelid = 'public.recommendation_events'::regclass
  ) THEN
    RAISE EXCEPTION 'Aux shadow observation constraint is missing';
  END IF;
END $$;

SELECT
  coalesce(aux_shadow_observation->>'mode', 'not_observed') AS mode,
  coalesce(aux_shadow_observation->>'outcome', 'not_observed') AS outcome,
  count(*) AS events,
  round(avg((aux_shadow_observation->>'aux_latency_ms')::numeric), 2) AS avg_aux_latency_ms,
  round(avg((aux_shadow_observation->>'served_candidate_coverage')::numeric), 4)
    AS avg_served_candidate_coverage
FROM public.recommendation_events
GROUP BY 1, 2
ORDER BY 1, 2;
