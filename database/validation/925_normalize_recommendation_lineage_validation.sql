DO $$ BEGIN
  IF to_regclass('public.recommendation_requests') IS NULL OR
     to_regclass('public.context_snapshots') IS NULL OR
     to_regclass('ml.feature_snapshots') IS NULL OR
     to_regclass('public.recommendation_runs') IS NULL OR
     to_regclass('public.recommendation_candidates') IS NULL OR
     to_regclass('public.recommendation_candidate_stages') IS NULL THEN
    RAISE EXCEPTION 'normalized recommendation lineage tables missing';
  END IF;
  IF to_regprocedure('public.record_episode_recommendation_lineage(jsonb)') IS NULL THEN
    RAISE EXCEPTION 'normalized lineage writer missing';
  END IF;
  IF EXISTS (SELECT 1 FROM public.slates WHERE recommendation_run_id IS NULL) THEN
    RAISE EXCEPTION 'slate without normalized recommendation run';
  END IF;
  IF EXISTS (
    SELECT 1 FROM public.slate_items i JOIN public.slates s ON s.id=i.slate_id
    JOIN public.recommendation_runs r ON r.id=s.recommendation_run_id
    WHERE NOT EXISTS (SELECT 1 FROM public.recommendation_candidates c
      WHERE c.recommendation_run_id=r.id AND c.candidate_item_hash=i.episode_hash)
  ) THEN RAISE EXCEPTION 'served slate item missing normalized candidate'; END IF;
  IF has_table_privilege('authenticated','public.recommendation_runs','SELECT') OR
     has_function_privilege('authenticated','public.record_episode_recommendation_lineage(jsonb)','EXECUTE') THEN
    RAISE EXCEPTION 'normalized lineage leaked to authenticated role';
  END IF;
END $$;
