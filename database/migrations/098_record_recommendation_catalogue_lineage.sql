-- Additive serving lineage for bundle fallback and versioned published candidates.

ALTER TABLE public.recommendation_events
  ADD COLUMN IF NOT EXISTS catalogue_selection jsonb;

ALTER TABLE public.recommendation_events
  DROP CONSTRAINT IF EXISTS recommendation_events_catalogue_selection_shape;

ALTER TABLE public.recommendation_events
  ADD CONSTRAINT recommendation_events_catalogue_selection_shape CHECK (
    catalogue_selection IS NULL OR (
      jsonb_typeof(catalogue_selection) = 'object'
      AND catalogue_selection->>'source' IN ('fallback_bundle', 'published_candidates')
      AND (
        catalogue_selection->>'source' = 'fallback_bundle'
        OR (
          catalogue_selection->>'publication_version' ~ '^sha256:[0-9a-f]{64}$'
          AND (catalogue_selection->>'candidate_count')::integer BETWEEN 1 AND 500
        )
      )
    )
  );

CREATE INDEX IF NOT EXISTS recommendation_events_catalogue_version_idx
  ON public.recommendation_events ((catalogue_selection->>'publication_version'))
  WHERE catalogue_selection->>'publication_version' IS NOT NULL;

COMMENT ON COLUMN public.recommendation_events.catalogue_selection IS
  'Count-only serving lineage: deterministic bundle fallback or immutable published-candidate version; contains no user history or dish payloads.';
