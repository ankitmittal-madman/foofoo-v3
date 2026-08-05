-- Migration: 070_govern_usda_evaluation_and_exact_match_nutrition.sql
-- Makes external-provider evaluations durable and prevents search-result similarity from being
-- mistaken for dish-level nutrition evidence. Exact USDA matches remain provisional.

CREATE TABLE ops.external_provider_evaluation_runs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  provider text NOT NULL CHECK (provider IN ('foodon_ols','usda_fdc')),
  evaluation_code text NOT NULL UNIQUE CHECK (evaluation_code ~ '^[a-z0-9]+([_-][a-z0-9]+)*$'),
  sample_definition jsonb NOT NULL DEFAULT '{}',
  status text NOT NULL DEFAULT 'queued' CHECK (
    status IN ('queued','running','completed','completed_with_provider_limits','failed')
  ),
  metrics jsonb NOT NULL DEFAULT '{}',
  started_at timestamptz NOT NULL DEFAULT now(),
  completed_at timestamptz,
  created_by text NOT NULL DEFAULT 'service_role'
);

CREATE TABLE ops.external_provider_evaluation_items (
  evaluation_run_id uuid NOT NULL REFERENCES ops.external_provider_evaluation_runs(id) ON DELETE CASCADE,
  dish_id uuid NOT NULL REFERENCES public.dishes(id) ON DELETE CASCADE,
  query_text text NOT NULL,
  source_record_id uuid REFERENCES public.food_source_records(id) ON DELETE SET NULL,
  matched_label text,
  provider_data_type text,
  match_quality text NOT NULL DEFAULT 'pending' CHECK (
    match_quality IN ('pending','exact','non_exact','no_record')
  ),
  nutrient_assertion_count integer NOT NULL DEFAULT 0 CHECK (nutrient_assertion_count >= 0),
  error_code text,
  evaluated_at timestamptz,
  PRIMARY KEY (evaluation_run_id,dish_id)
);
CREATE INDEX external_provider_evaluation_items_quality
  ON ops.external_provider_evaluation_items(evaluation_run_id,match_quality);

CREATE OR REPLACE FUNCTION ops.create_external_provider_evaluation(
  p_provider text,p_evaluation_code text,p_dish_ids uuid[]
)
RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER SET search_path=ops,public,pg_temp AS $$
DECLARE v_run_id uuid; v_requested integer; v_inserted integer;
BEGIN
  IF p_provider NOT IN ('foodon_ols','usda_fdc') THEN RAISE EXCEPTION 'unsupported provider'; END IF;
  v_requested:=coalesce(cardinality(p_dish_ids),0);
  IF v_requested<1 OR v_requested>50 THEN RAISE EXCEPTION 'evaluation sample must contain 1..50 dishes'; END IF;
  INSERT INTO ops.external_provider_evaluation_runs(provider,evaluation_code,sample_definition,status)
  VALUES(p_provider,p_evaluation_code,jsonb_build_object('dish_ids',p_dish_ids,'requested',v_requested),'queued')
  RETURNING id INTO v_run_id;
  INSERT INTO ops.external_provider_evaluation_items(evaluation_run_id,dish_id,query_text)
  SELECT v_run_id,d.id,d.name FROM public.dishes d WHERE d.id=ANY(p_dish_ids)
  ON CONFLICT DO NOTHING;
  GET DIAGNOSTICS v_inserted=ROW_COUNT;
  IF v_inserted<>v_requested THEN RAISE EXCEPTION 'evaluation contains unknown or duplicate dishes'; END IF;
  UPDATE public.dish_enrichment_jobs j SET status='pending_external',attempts=0,next_attempt_at=now(),
    completed_at=NULL,last_error_code=NULL,locked_at=NULL,locked_by=NULL,lease_expires_at=NULL,updated_at=now()
  WHERE j.dish_id=ANY(p_dish_ids);
  UPDATE ops.external_provider_evaluation_runs SET status='running' WHERE id=v_run_id;
  RETURN v_run_id;
END $$;

CREATE OR REPLACE FUNCTION ops.finalize_external_provider_evaluation(p_run_id uuid)
RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=ops,public,food,pg_temp AS $$
DECLARE v_run ops.external_provider_evaluation_runs%ROWTYPE; v_metrics jsonb;
BEGIN
  SELECT * INTO v_run FROM ops.external_provider_evaluation_runs WHERE id=p_run_id FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'evaluation run not found'; END IF;
  WITH latest AS (
    SELECT DISTINCT ON (r.dish_id) r.dish_id,r.id,r.source_payload
    FROM public.food_source_records r
    WHERE r.provider=v_run.provider AND r.fetched_at>=v_run.started_at
    ORDER BY r.dish_id,r.fetched_at DESC
  ), nutrient_counts AS (
    SELECT source_record_id,count(*)::integer AS n FROM food.nutrient_assertions
    WHERE source_record_id IS NOT NULL GROUP BY source_record_id
  )
  UPDATE ops.external_provider_evaluation_items i SET
    source_record_id=l.id,
    matched_label=CASE WHEN v_run.provider='usda_fdc' THEN l.source_payload->'foods'->0->>'description'
      ELSE l.source_payload->'response'->'docs'->0->>'label' END,
    provider_data_type=CASE WHEN v_run.provider='usda_fdc'
      THEN l.source_payload->'foods'->0->>'dataType' ELSE NULL END,
    match_quality=CASE WHEN l.id IS NULL THEN 'no_record'
      WHEN lower(regexp_replace(btrim(i.query_text),'\s+',' ','g'))=lower(regexp_replace(btrim(
        CASE WHEN v_run.provider='usda_fdc' THEN l.source_payload->'foods'->0->>'description'
          ELSE l.source_payload->'response'->'docs'->0->>'label' END),'\s+',' ','g')) THEN 'exact'
      ELSE 'non_exact' END,
    nutrient_assertion_count=coalesce(n.n,0),
    error_code=CASE WHEN l.id IS NULL THEN 'no_provider_record' ELSE NULL END,
    evaluated_at=now()
  FROM latest l LEFT JOIN nutrient_counts n ON n.source_record_id=l.id
  WHERE i.evaluation_run_id=p_run_id AND i.dish_id=l.dish_id;

  UPDATE ops.external_provider_evaluation_items SET match_quality='no_record',
    error_code='no_provider_record',evaluated_at=now()
  WHERE evaluation_run_id=p_run_id AND evaluated_at IS NULL;

  SELECT jsonb_build_object(
    'sample_size',count(*),
    'records',count(*) FILTER(WHERE source_record_id IS NOT NULL),
    'exact_matches',count(*) FILTER(WHERE match_quality='exact'),
    'non_exact_matches',count(*) FILTER(WHERE match_quality='non_exact'),
    'no_record',count(*) FILTER(WHERE match_quality='no_record'),
    'nutrient_assertions',sum(nutrient_assertion_count)
  ) INTO v_metrics FROM ops.external_provider_evaluation_items WHERE evaluation_run_id=p_run_id;
  UPDATE ops.external_provider_evaluation_runs SET metrics=v_metrics,
    status=CASE WHEN (v_metrics->>'no_record')::integer=0 THEN 'completed'
      ELSE 'completed_with_provider_limits' END,completed_at=now() WHERE id=p_run_id;
  RETURN v_metrics;
END $$;

-- Remove only provisional nutrition derived from a non-exact USDA search result. Raw source
-- records stay immutable for audit; accepted or human-reviewed assertions are never touched.
DELETE FROM food.nutrient_assertions a USING public.food_source_records r
WHERE a.source_record_id=r.id AND r.provider='usda_fdc' AND a.review_status='provisional'
  AND lower(regexp_replace(btrim(r.query_text),'\s+',' ','g'))<>
      lower(regexp_replace(btrim(r.source_payload->'foods'->0->>'description'),'\s+',' ','g'));

REVOKE ALL ON TABLE ops.external_provider_evaluation_runs,
  ops.external_provider_evaluation_items FROM PUBLIC,anon,authenticated;
GRANT SELECT,INSERT,UPDATE ON ops.external_provider_evaluation_runs,
  ops.external_provider_evaluation_items TO service_role;
REVOKE ALL ON FUNCTION ops.create_external_provider_evaluation(text,text,uuid[]) FROM PUBLIC,anon,authenticated;
REVOKE ALL ON FUNCTION ops.finalize_external_provider_evaluation(uuid) FROM PUBLIC,anon,authenticated;
GRANT EXECUTE ON FUNCTION ops.create_external_provider_evaluation(text,text,uuid[]) TO service_role;
GRANT EXECUTE ON FUNCTION ops.finalize_external_provider_evaluation(uuid) TO service_role;

COMMENT ON TABLE ops.external_provider_evaluation_runs IS
  'Durable labelled evaluation evidence for bounded external food-provider samples.';
COMMENT ON FUNCTION ops.finalize_external_provider_evaluation(uuid) IS
  'Classifies exact/non-exact/no-record results without promoting provider search output to truth.';
