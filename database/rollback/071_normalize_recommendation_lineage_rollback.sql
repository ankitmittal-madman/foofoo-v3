DROP FUNCTION IF EXISTS public.record_episode_recommendation_lineage(jsonb);
ALTER TABLE public.slates DROP COLUMN IF EXISTS recommendation_run_id;
DROP TABLE IF EXISTS public.recommendation_candidate_stages;
DROP TABLE IF EXISTS public.recommendation_candidates;
DROP TABLE IF EXISTS public.recommendation_runs;
DROP TABLE IF EXISTS ml.feature_snapshots;
DROP TABLE IF EXISTS public.context_snapshots;
DROP TABLE IF EXISTS public.recommendation_requests;
