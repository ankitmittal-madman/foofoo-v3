-- Activate replay, catalogue episode resolution, ML baseline metadata and annotation operations.

CREATE OR REPLACE FUNCTION public.resolve_catalog_episode_ids(p_dish_ids uuid[])
RETURNS TABLE(dish_id uuid, episode_id uuid, episode_hash text)
LANGUAGE sql STABLE SECURITY DEFINER
SET search_path = public, food, pg_temp
AS $$
  SELECT DISTINCT ON (c.dish_id) c.dish_id, e.id, e.episode_hash
  FROM food.meal_episode_components c
  JOIN food.meal_episodes e ON e.id = c.episode_id
  JOIN food.plate_grammars g ON g.id = e.grammar_id
  WHERE c.dish_id = ANY(p_dish_ids)
    AND c.component_role IN ('primary','hero')
    AND e.catalog_status = 'published'
    AND g.grammar_code = 'SINGLE_PRIMARY'
  ORDER BY c.dish_id, e.version DESC;
$$;
REVOKE ALL ON FUNCTION public.resolve_catalog_episode_ids(uuid[]) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.resolve_catalog_episode_ids(uuid[]) TO service_role;

CREATE OR REPLACE FUNCTION public.replay_recommendation_slate(p_slate_id uuid)
RETURNS jsonb
LANGUAGE sql STABLE SECURITY INVOKER
SET search_path = public, pg_temp
AS $$
  SELECT jsonb_build_object(
    'slate', to_jsonb(s),
    'items', coalesce((SELECT jsonb_agg(to_jsonb(i) ORDER BY i.rank) FROM public.slate_items i WHERE i.slate_id=s.id), '[]'),
    'outcomes', coalesce((SELECT jsonb_agg(to_jsonb(o) ORDER BY o.occurred_at) FROM public.outcome_events o WHERE o.slate_id=s.id), '[]')
  ) FROM public.slates s WHERE s.id=p_slate_id;
$$;
GRANT EXECUTE ON FUNCTION public.replay_recommendation_slate(uuid) TO authenticated, service_role;

CREATE TABLE research.annotation_items (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  batch_id uuid NOT NULL REFERENCES research.annotation_batches(id) ON DELETE CASCADE,
  item_key text NOT NULL,
  subject_type text NOT NULL,
  subject_id text NOT NULL,
  evidence_payload jsonb NOT NULL DEFAULT '{}',
  priority smallint NOT NULL DEFAULT 0,
  item_status text NOT NULL DEFAULT 'pending' CHECK (item_status IN ('pending','in_progress','submitted','adjudicated','cancelled')),
  locked_by text,
  lease_expires_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(batch_id,item_key)
);
ALTER TABLE research.annotations ADD COLUMN annotation_item_id uuid REFERENCES research.annotation_items(id) ON DELETE CASCADE;
CREATE INDEX annotation_items_queue ON research.annotation_items(batch_id,item_status,priority DESC,created_at);

CREATE OR REPLACE FUNCTION research.claim_annotation_items(
  p_batch_id uuid, p_annotator_token text, p_limit integer DEFAULT 10
)
RETURNS SETOF research.annotation_items
LANGUAGE plpgsql SECURITY DEFINER SET search_path = research, pg_temp
AS $$
BEGIN
  RETURN QUERY
  WITH picked AS (
    SELECT i.id FROM research.annotation_items i
    WHERE i.batch_id=p_batch_id
      AND (i.item_status='pending' OR (i.item_status='in_progress' AND i.lease_expires_at<now()))
    ORDER BY i.priority DESC,i.created_at
    FOR UPDATE SKIP LOCKED LIMIT greatest(1,least(coalesce(p_limit,10),50))
  )
  UPDATE research.annotation_items i SET item_status='in_progress',locked_by=p_annotator_token,
    lease_expires_at=now()+interval '30 minutes'
  FROM picked WHERE i.id=picked.id RETURNING i.*;
END;
$$;
REVOKE ALL ON FUNCTION research.claim_annotation_items(uuid,text,integer) FROM PUBLIC,anon,authenticated;
GRANT EXECUTE ON FUNCTION research.claim_annotation_items(uuid,text,integer) TO service_role;

INSERT INTO ml.feature_definitions(feature_name,feature_version,value_type,owner_name,expression,null_policy,online_source,offline_source,status) VALUES
('episode_active_minutes','v1','float','recommendation','episode.practicality.active_minutes','use_catalog_prior','response episode','food.episode_workload_features','active'),
('episode_richness','v1','float','recommendation','episode.richness_score','use_zero','response episode','food.episode_cadence','active'),
('household_cadence_debt','v1','float','recommendation','re_engine.household_cadence_state.richness_debt','use_zero','re_engine.household_cadence_state','re_engine.household_cadence_state','active'),
('selection_propensity','v1','float','experimentation','slate_items.selection_propensity','reject_row','public.slate_items','public.slate_items','active')
ON CONFLICT(feature_name,feature_version) DO UPDATE SET status='active';

INSERT INTO ml.model_registry(model_name,model_version,objective,training_dataset_uri,artifact_uri,artifact_checksum,metrics,slice_metrics,stage,approved_by,activated_at)
VALUES('episode_success','episode-practicality-rule-v1','maximize P(choose)*P(execute)*(1-P(regret))','builtin://rule-baseline/no-training-data','repo://ghar_re_core/meal_episode.py','episode-practicality-rule-v1',jsonb_build_object('calibration_status','rule_baseline_untrained'),'{}','production','architecture-baseline',now())
ON CONFLICT(model_name,model_version) DO UPDATE SET stage='production',activated_at=coalesce(ml.model_registry.activated_at,now());

INSERT INTO ops.data_sources(source_code,owner_name,license_code,source_uri,permitted_uses) VALUES
('foofoo_catalogue_v1','Foofoo','proprietary','repo://ghar_re_service/data/bundle/catalogue.json',ARRAY['recommendation','product','evaluation']),
('foofoo_recipes_v1','Foofoo','proprietary','repo://data/source/recipes_v1.json',ARRAY['product','evaluation']),
('foodon_ols','FoodOn / EMBL-EBI OLS','CC-BY-4.0','https://www.ebi.ac.uk/ols4/ontologies/foodon',ARRAY['ontology_matching','evaluation']),
('usda_fdc','USDA FoodData Central','public-domain','https://fdc.nal.usda.gov/',ARRAY['nutrition_matching','evaluation'])
ON CONFLICT(source_code) DO UPDATE SET source_uri=excluded.source_uri,permitted_uses=excluded.permitted_uses;

INSERT INTO ops.catalog_versions(version_code,manifest_checksum,source_versions,row_counts,status,published_at)
SELECT 'food-intelligence-v1','food-intelligence-v1-20260805',
  jsonb_build_object('catalogue','v1','recipes','v1','ontology_schema','061'),
  jsonb_build_object('dishes',(SELECT count(*) FROM public.dishes),'episodes',(SELECT count(*) FROM food.meal_episodes),'recipes',(SELECT count(*) FROM food.recipes)),
  'published',now()
ON CONFLICT(version_code) DO UPDATE SET row_counts=excluded.row_counts,status='published',published_at=now();

CREATE OR REPLACE VIEW ops.enrichment_quality_daily AS
SELECT current_date AS report_date,
  count(*) AS total_jobs,
  count(*) FILTER (WHERE external_enriched_at IS NOT NULL) AS externally_enriched,
  count(*) FILTER (WHERE status='complete') AS complete,
  count(*) FILTER (WHERE status IN ('review','pending_ai')) AS needs_review,
  count(*) FILTER (WHERE last_error_code IS NOT NULL) AS with_provider_or_worker_error
FROM public.dish_enrichment_jobs;

GRANT SELECT,INSERT,UPDATE,DELETE ON research.annotation_items TO service_role;
GRANT SELECT ON ops.enrichment_quality_daily TO service_role;
