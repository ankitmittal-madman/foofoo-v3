DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM information_schema.columns
    WHERE table_schema = 'public'
      AND table_name = 'recommendation_events'
      AND column_name = 'catalogue_selection'
      AND data_type = 'jsonb'
  ) THEN
    RAISE EXCEPTION 'recommendation_events.catalogue_selection is missing';
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'recommendation_events_catalogue_selection_shape'
      AND conrelid = 'public.recommendation_events'::regclass
  ) THEN
    RAISE EXCEPTION 'catalogue lineage constraint is missing';
  END IF;
END $$;

SELECT
  coalesce(catalogue_selection->>'source', 'legacy_unrecorded') AS source,
  count(*) AS events
FROM public.recommendation_events
GROUP BY 1
ORDER BY 1;
