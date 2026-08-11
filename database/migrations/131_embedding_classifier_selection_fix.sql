-- cron-embedding-classifier was re-selecting the SAME already-attempted dishes every invocation:
-- its batch query only filtered on cuisine_id IS NULL / no dish_meal_class_mappings row, with no
-- way to know a dish had already been through classify_dish_by_embedding and simply scored below
-- the 0.55 similarity threshold (so it stays cuisine_id=NULL / mapping-less forever). Since
-- meal_classes/cuisines embeddings are static (migration 128, backfilled once), a dish's nearest
-- match never changes -- re-attempting it wastes the batch on dishes that will never publish,
-- instead of advancing to dishes not yet tried at all. Confirmed in production: food_source_records
-- for provider='embedding_classifier' grew from ~2,400 to ~2,700 rows in ~15 minutes while
-- cuisine/meal_class coverage counts did not move at all.
--
-- Fix: one RPC that also excludes dishes with an existing embedding_classifier food_source_records
-- row, replacing the previous two-query (cuisine_id IS NULL + dishes_missing_meal_class) selection
-- in the Edge Function.

CREATE OR REPLACE FUNCTION public.dishes_pending_embedding_classification(p_limit integer DEFAULT 30)
RETURNS TABLE (id uuid, name text)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path=public,pg_temp
AS $$
  SELECT d.id, d.name
  FROM public.dishes d
  WHERE (
    d.cuisine_id IS NULL
    OR NOT EXISTS (SELECT 1 FROM public.dish_meal_class_mappings m WHERE m.dish_id = d.id)
  )
  AND NOT EXISTS (
    SELECT 1 FROM public.food_source_records fsr
    WHERE fsr.dish_id = d.id AND fsr.provider = 'embedding_classifier'
  )
  LIMIT p_limit;
$$;

COMMENT ON FUNCTION public.dishes_pending_embedding_classification(integer) IS
  'Replaces the old dishes_missing_meal_class + cuisine_id IS NULL two-query selection (migration '
  '130) -- also excludes dishes with an existing embedding_classifier food_source_records row, so a '
  'dish that scored below threshold once (and therefore never will change, since the embeddings are '
  'static) is not re-selected every invocation forever.';

REVOKE ALL ON FUNCTION public.dishes_pending_embedding_classification(integer) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.dishes_pending_embedding_classification(integer) TO service_role;
