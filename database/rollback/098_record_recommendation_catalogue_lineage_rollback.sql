DROP INDEX IF EXISTS public.recommendation_events_catalogue_version_idx;
ALTER TABLE public.recommendation_events
  DROP CONSTRAINT IF EXISTS recommendation_events_catalogue_selection_shape;
ALTER TABLE public.recommendation_events
  DROP COLUMN IF EXISTS catalogue_selection;
