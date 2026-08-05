-- Validation for migration 056 + seed 146. Run after both; the behavioral probes roll back.

-- Structural inventory and RLS posture.
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public' AND table_name IN (
  'meal_class_families','taxonomy_terms','taxonomy_term_aliases','dish_submissions',
  'food_source_records','dish_enrichment_jobs','dish_taxonomy_assertions',
  'dish_taxonomy_current','dish_meal_class_mappings','dish_constraints',
  'dish_regional_affinities'
)
ORDER BY table_name;

SELECT tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public' AND tablename IN (
  'dish_submissions','food_source_records','dish_enrichment_jobs',
  'dish_taxonomy_assertions','dish_taxonomy_current','dish_meal_class_mappings'
)
ORDER BY tablename;

DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM public.dishes d
    WHERE d.ontology_status IN ('enriched','review')
      AND NOT EXISTS (
        SELECT 1 FROM public.dish_meal_class_mappings m
        WHERE m.dish_id = d.id AND m.review_status <> 'rejected'
      )
  ) THEN
    RAISE EXCEPTION 'FAIL: enriched/review dish exists without a usable meal-class mapping';
  END IF;

  IF EXISTS (
    SELECT 1 FROM public.dish_meal_class_mappings m
    JOIN public.meal_classes c ON c.class_code = m.class_code
    WHERE m.item_role = 'primary'
      AND (c.is_addon OR c.planning_role <> 'MAIN_PRIMARY')
  ) THEN
    RAISE EXCEPTION 'FAIL: add-on/combo class leaked into a primary dish pool';
  END IF;

  IF EXISTS (
    SELECT 1 FROM public.dish_meal_class_mappings
    WHERE classification_method = ''
  ) THEN
    RAISE EXCEPTION 'FAIL: meal-class mapping lacks classification method provenance';
  END IF;

  IF EXISTS (
    SELECT 1 FROM public.dish_taxonomy_current cur
    JOIN public.dish_taxonomy_assertions a ON a.id = cur.assertion_id
    WHERE a.dish_id <> cur.dish_id OR a.field_key <> cur.field_key OR a.review_status = 'rejected'
  ) THEN
    RAISE EXCEPTION 'FAIL: current taxonomy pointer does not match its assertion';
  END IF;
END $$;

BEGIN;

DO $$
DECLARE probe_id uuid;
BEGIN
  INSERT INTO public.dishes (
    name, meal_occasion, cook_time_minutes, difficulty, is_active
  ) VALUES (
    'Ontology Queue Probe ' || gen_random_uuid()::text,
    ARRAY['dinner'], 10, 'beginner', false
  ) RETURNING id INTO probe_id;

  IF NOT EXISTS (
    SELECT 1 FROM public.dish_enrichment_jobs
    WHERE dish_id = probe_id AND status = 'pending_external'
  ) THEN
    RAISE EXCEPTION 'FAIL: canonical dish insert bypassed enrichment queue';
  END IF;

  IF (SELECT ontology_status FROM public.dishes WHERE id = probe_id) <> 'pending' THEN
    RAISE EXCEPTION 'FAIL: new canonical dish was not marked pending';
  END IF;
END $$;

ROLLBACK;

SELECT ontology_status, count(*) AS dish_count
FROM public.dishes
GROUP BY ontology_status
ORDER BY ontology_status;

SELECT review_status, count(*) AS mapping_count
FROM public.dish_meal_class_mappings
GROUP BY review_status
ORDER BY review_status;
