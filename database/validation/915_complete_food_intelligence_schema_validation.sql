DO $$
BEGIN
  IF to_regclass('food.ontology_nodes') IS NULL OR to_regclass('food.ontology_edges') IS NULL THEN
    RAISE EXCEPTION 'FAIL: ontology graph missing';
  END IF;
  IF to_regclass('food.nutrient_assertions') IS NULL THEN
    RAISE EXCEPTION 'FAIL: nutrient assertion store missing';
  END IF;
  IF to_regclass('ops.content_review_tasks') IS NULL THEN
    RAISE EXCEPTION 'FAIL: governed review queue missing';
  END IF;
  IF to_regclass('research.meal_diaries') IS NULL OR to_regclass('research.annotations') IS NULL THEN
    RAISE EXCEPTION 'FAIL: research evidence foundation missing';
  END IF;
END $$;

SELECT n.nspname AS schema_name, c.relname AS table_name
FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname IN ('food','ops','research')
  AND c.relname IN ('ontology_nodes','ontology_edges','nutrients','nutrient_assertions',
                    'content_review_tasks','catalog_versions','catalog_publish_runs',
                    'studies','participants','meal_diaries','annotation_batches','annotations')
ORDER BY schema_name, table_name;
