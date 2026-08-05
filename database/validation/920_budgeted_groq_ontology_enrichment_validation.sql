DO $$
BEGIN
  IF (SELECT count(*) FROM ops.ai_dish_enrichment_state) <> (SELECT count(*) FROM public.dishes) THEN
    RAISE EXCEPTION 'every canonical dish must have an AI enrichment state';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM ml.model_registry WHERE model_name='dish_ontology'
    AND model_version='openai/gpt-oss-120b' AND stage='production') THEN
    RAISE EXCEPTION 'Groq ontology model registry row missing';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM ops.data_sources WHERE source_code='groq_free') THEN
    RAISE EXCEPTION 'Groq source registry row missing';
  END IF;
  IF position('data_source=''ai_generated''' IN pg_get_functiondef(
    'public.record_ai_low_risk_enrichment(uuid,uuid,text,jsonb,numeric,numeric)'::regprocedure
  ))=0 THEN
    RAISE EXCEPTION 'AI promotion may overwrite a non-AI alias';
  END IF;
  IF position('ON CONFLICT(dimension,code) DO NOTHING' IN pg_get_functiondef(
    'public.record_ai_low_risk_enrichment(uuid,uuid,text,jsonb,numeric,numeric)'::regprocedure
  ))=0 THEN
    RAISE EXCEPTION 'AI promotion may overwrite a governed taxonomy label';
  END IF;
END $$;

BEGIN;
SELECT ops.reserve_ai_provider_budget('validation',1,100,50);
SELECT ops.settle_ai_provider_budget('validation',50,25);
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM ops.ai_provider_usage_daily WHERE provider='validation'
    AND requests_used=1 AND tokens_used=25 AND tokens_reserved=0) THEN
    RAISE EXCEPTION 'AI budget reservation/settlement failed';
  END IF;
END $$;
ROLLBACK;
