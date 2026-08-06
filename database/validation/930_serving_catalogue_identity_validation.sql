-- Every previously unresolved item from the active RE bundle now has one canonical database ID,
-- remains non-serving until enriched, and can receive feedback without dish_id=NULL.

DO $$
DECLARE
  expected_names constant text[] := ARRAY[
    'Chholar Dal with Luchi',
    'Daal Bafla',
    'Dal Pakwan',
    'Pithla Bhakri',
    'Poha Jalebi (Indori)',
    'Sadya Thali',
    'Thali Meals (South Indian)',
    'Zunka Bhakri'
  ];
  resolved_count integer;
  unsafe_active_count integer;
BEGIN
  SELECT count(*) INTO resolved_count
  FROM public.dishes
  WHERE name = ANY(expected_names);
  IF resolved_count <> cardinality(expected_names) THEN
    RAISE EXCEPTION 'serving catalogue identity incomplete: expected %, found %',
      cardinality(expected_names), resolved_count;
  END IF;

  SELECT count(*) INTO unsafe_active_count
  FROM public.dishes
  WHERE name = ANY(expected_names)
    AND ontology_status <> 'enriched'
    AND is_active;
  IF unsafe_active_count <> 0 THEN
    RAISE EXCEPTION '% unverified identity-only dishes are active', unsafe_active_count;
  END IF;
END $$;
