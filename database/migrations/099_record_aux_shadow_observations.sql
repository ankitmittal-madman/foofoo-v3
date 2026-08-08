-- Privacy-minimized Aux retrieval evidence attached to the existing serving event.

ALTER TABLE public.recommendation_events
  ADD COLUMN IF NOT EXISTS aux_shadow_observation jsonb;

ALTER TABLE public.recommendation_events
  DROP CONSTRAINT IF EXISTS recommendation_events_aux_shadow_observation_shape;

ALTER TABLE public.recommendation_events
  ADD CONSTRAINT recommendation_events_aux_shadow_observation_shape CHECK (
    aux_shadow_observation IS NULL OR (
      jsonb_typeof(aux_shadow_observation) = 'object'
      AND aux_shadow_observation ?& ARRAY[
        'mode', 'outcome', 'candidate_count', 'aux_latency_ms',
        'comparable_served_count', 'served_in_candidates_count', 'served_candidate_coverage'
      ]
      AND (
        aux_shadow_observation - ARRAY[
          'mode', 'outcome', 'failure_reason', 'publication_version', 'candidate_count',
          'aux_latency_ms', 'comparable_served_count', 'served_in_candidates_count',
          'served_candidate_coverage'
        ]
      ) = '{}'::jsonb
      AND aux_shadow_observation->>'mode' IN ('shadow', 'active')
      AND aux_shadow_observation->>'outcome' IN ('retrieved', 'unavailable')
      AND (aux_shadow_observation->>'candidate_count')::integer BETWEEN 0 AND 500
      AND (aux_shadow_observation->>'aux_latency_ms')::integer >= 0
      AND (aux_shadow_observation->>'comparable_served_count')::integer >= 0
      AND (aux_shadow_observation->>'served_in_candidates_count')::integer >= 0
      AND (aux_shadow_observation->>'served_in_candidates_count')::integer
        <= (aux_shadow_observation->>'comparable_served_count')::integer
      AND (
        (
          aux_shadow_observation->>'outcome' = 'retrieved'
          AND aux_shadow_observation->>'publication_version' ~ '^sha256:[0-9a-f]{64}$'
          AND (aux_shadow_observation->>'candidate_count')::integer BETWEEN 1 AND 500
          AND NOT (aux_shadow_observation ? 'failure_reason')
        ) OR (
          aux_shadow_observation->>'outcome' = 'unavailable'
          AND aux_shadow_observation->>'failure_reason' IN ('timeout', 'network', 'http', 'bad_body')
          AND (aux_shadow_observation->>'candidate_count')::integer = 0
          AND NOT (aux_shadow_observation ? 'publication_version')
        )
      )
      AND (
        (
          aux_shadow_observation->>'outcome' = 'unavailable'
          AND jsonb_typeof(aux_shadow_observation->'served_candidate_coverage') = 'null'
        ) OR (
          aux_shadow_observation->>'outcome' = 'retrieved'
          AND (aux_shadow_observation->>'comparable_served_count')::integer = 0
          AND jsonb_typeof(aux_shadow_observation->'served_candidate_coverage') = 'null'
        ) OR (
          aux_shadow_observation->>'outcome' = 'retrieved'
          AND (aux_shadow_observation->>'comparable_served_count')::integer > 0
          AND jsonb_typeof(aux_shadow_observation->'served_candidate_coverage') = 'number'
          AND (aux_shadow_observation->>'served_candidate_coverage')::numeric BETWEEN 0 AND 1
        )
      )
    )
  );

CREATE INDEX IF NOT EXISTS recommendation_events_aux_shadow_version_idx
  ON public.recommendation_events ((aux_shadow_observation->>'publication_version'))
  WHERE aux_shadow_observation->>'publication_version' IS NOT NULL;

COMMENT ON COLUMN public.recommendation_events.aux_shadow_observation IS
  'Privacy-minimized Aux serving evidence: mode, outcome, immutable version, latency and count-only canonical served overlap; never candidate IDs or user history.';
