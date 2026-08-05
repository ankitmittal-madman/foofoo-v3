DO $$ BEGIN
  IF to_regprocedure('public.claim_ai_dish_enrichment(text,integer)') IS NULL OR
     to_regprocedure('public.reserve_ai_provider_budget(text,integer,bigint,bigint)') IS NULL OR
     to_regprocedure('public.settle_ai_provider_budget(text,bigint,bigint)') IS NULL OR
     to_regprocedure('public.finish_ai_dish_enrichment(uuid,text,text,text,text)') IS NULL THEN
    RAISE EXCEPTION 'AI worker PostgREST facade incomplete';
  END IF;
END $$;
