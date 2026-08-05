-- Migration: 067_expose_ai_worker_rpc_facade.sql
-- PostgREST exposes public, not private ops; service-only facades retain the ops implementation.

CREATE OR REPLACE FUNCTION public.claim_ai_dish_enrichment(p_worker_id text,p_batch_size integer DEFAULT 2)
RETURNS TABLE(dish_id uuid,query_text text,attempts smallint)
LANGUAGE sql SECURITY DEFINER SET search_path=public,ops,pg_temp AS $$
  SELECT * FROM ops.claim_ai_dish_enrichment(p_worker_id,p_batch_size);
$$;

CREATE OR REPLACE FUNCTION public.reserve_ai_provider_budget(
  p_provider text,p_request_limit integer,p_token_limit bigint,p_reserve_tokens bigint
)
RETURNS boolean LANGUAGE sql SECURITY DEFINER SET search_path=public,ops,pg_temp AS $$
  SELECT ops.reserve_ai_provider_budget(p_provider,p_request_limit,p_token_limit,p_reserve_tokens);
$$;

CREATE OR REPLACE FUNCTION public.settle_ai_provider_budget(
  p_provider text,p_reserved_tokens bigint,p_actual_tokens bigint
)
RETURNS void LANGUAGE sql SECURITY DEFINER SET search_path=public,ops,pg_temp AS $$
  SELECT ops.settle_ai_provider_budget(p_provider,p_reserved_tokens,p_actual_tokens);
$$;

CREATE OR REPLACE FUNCTION public.finish_ai_dish_enrichment(
  p_dish_id uuid,p_worker_id text,p_model_name text,p_status text,p_error text DEFAULT NULL
)
RETURNS void LANGUAGE sql SECURITY DEFINER SET search_path=public,ops,pg_temp AS $$
  SELECT ops.finish_ai_dish_enrichment(p_dish_id,p_worker_id,p_model_name,p_status,p_error);
$$;

REVOKE ALL ON FUNCTION public.claim_ai_dish_enrichment(text,integer) FROM PUBLIC,anon,authenticated;
REVOKE ALL ON FUNCTION public.reserve_ai_provider_budget(text,integer,bigint,bigint) FROM PUBLIC,anon,authenticated;
REVOKE ALL ON FUNCTION public.settle_ai_provider_budget(text,bigint,bigint) FROM PUBLIC,anon,authenticated;
REVOKE ALL ON FUNCTION public.finish_ai_dish_enrichment(uuid,text,text,text,text) FROM PUBLIC,anon,authenticated;
GRANT EXECUTE ON FUNCTION public.claim_ai_dish_enrichment(text,integer) TO service_role;
GRANT EXECUTE ON FUNCTION public.reserve_ai_provider_budget(text,integer,bigint,bigint) TO service_role;
GRANT EXECUTE ON FUNCTION public.settle_ai_provider_budget(text,bigint,bigint) TO service_role;
GRANT EXECUTE ON FUNCTION public.finish_ai_dish_enrichment(uuid,text,text,text,text) TO service_role;

COMMENT ON FUNCTION public.claim_ai_dish_enrichment(text,integer) IS
  'Service-only PostgREST facade for the private ops AI queue.';
