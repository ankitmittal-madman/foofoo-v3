DROP FUNCTION IF EXISTS public.claim_ai_dish_enrichment(text,integer);
DROP FUNCTION IF EXISTS public.reserve_ai_provider_budget(text,integer,bigint,bigint);
DROP FUNCTION IF EXISTS public.settle_ai_provider_budget(text,bigint,bigint);
DROP FUNCTION IF EXISTS public.finish_ai_dish_enrichment(uuid,text,text,text,text);
