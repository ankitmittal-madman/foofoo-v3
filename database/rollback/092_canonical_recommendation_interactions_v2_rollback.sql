-- Application rollback must stop emitting schema v2 before this destructive schema rollback.
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM public.feedback_events WHERE schema_version = '2') THEN
    RAISE EXCEPTION 'schema v2 interaction rows exist; retain additive columns and roll back application reads only';
  END IF;
END $$;

DROP VIEW IF EXISTS public.recommendation_interactions_v2;
GRANT INSERT, UPDATE, DELETE ON public.feedback_events TO anon, authenticated;
DROP TRIGGER IF EXISTS feedback_events_validate_v2_target ON public.feedback_events;
DROP FUNCTION IF EXISTS public.validate_recommendation_interaction_v2_target();
DROP INDEX IF EXISTS public.feedback_events_class_learning;
DROP INDEX IF EXISTS public.feedback_events_target_moment;
DROP INDEX IF EXISTS public.feedback_events_legacy_semantic_key;
DROP INDEX IF EXISTS public.feedback_events_v2_idempotency_key;

ALTER TABLE public.feedback_events DROP CONSTRAINT IF EXISTS feedback_events_v2_required_fields_check;
ALTER TABLE public.feedback_events DROP CONSTRAINT IF EXISTS feedback_events_propensity_check;
ALTER TABLE public.feedback_events DROP CONSTRAINT IF EXISTS feedback_events_shown_rank_check;
ALTER TABLE public.feedback_events DROP CONSTRAINT IF EXISTS feedback_events_evidence_kind_check;
ALTER TABLE public.feedback_events DROP CONSTRAINT IF EXISTS feedback_events_weekday_check;
ALTER TABLE public.feedback_events DROP CONSTRAINT IF EXISTS feedback_events_day_type_check;
ALTER TABLE public.feedback_events DROP CONSTRAINT IF EXISTS feedback_events_replacement_pair_check;
ALTER TABLE public.feedback_events DROP CONSTRAINT IF EXISTS feedback_events_replacement_target_type_check;
ALTER TABLE public.feedback_events DROP CONSTRAINT IF EXISTS feedback_events_target_identity_status_check;
ALTER TABLE public.feedback_events DROP CONSTRAINT IF EXISTS feedback_events_target_type_check;
ALTER TABLE public.feedback_events DROP CONSTRAINT IF EXISTS feedback_events_schema_version_check;

ALTER TABLE public.feedback_events DROP CONSTRAINT IF EXISTS feedback_events_event_type_check;
ALTER TABLE public.feedback_events ADD CONSTRAINT feedback_events_event_type_check CHECK (
  event_type IN (
    'accept','edit','swap','like','dislike','shown_not_tapped','never','not_today','lock','unlock',
    'add_to_date','make_this','too_much_work','missing_ingredient','member_objection','cooked',
    'ordered','replaced','completed','regretted'
  )
);
ALTER TABLE public.feedback_events ADD CONSTRAINT feedback_events_idempotency_key
  UNIQUE NULLS NOT DISTINCT (profile_id, recommendation_event_id, dish_id, event_type);

ALTER TABLE public.feedback_events
  DROP COLUMN IF EXISTS model_version,
  DROP COLUMN IF EXISTS policy_version,
  DROP COLUMN IF EXISTS feature_version,
  DROP COLUMN IF EXISTS config_version,
  DROP COLUMN IF EXISTS catalog_version,
  DROP COLUMN IF EXISTS reason_code,
  DROP COLUMN IF EXISTS selection_propensity,
  DROP COLUMN IF EXISTS shown_rank,
  DROP COLUMN IF EXISTS evidence_kind,
  DROP COLUMN IF EXISTS source_surface,
  DROP COLUMN IF EXISTS day_type,
  DROP COLUMN IF EXISTS weekday,
  DROP COLUMN IF EXISTS intended_meal_date,
  DROP COLUMN IF EXISTS local_timezone,
  DROP COLUMN IF EXISTS occurred_at,
  DROP COLUMN IF EXISTS replacement_target_id,
  DROP COLUMN IF EXISTS replacement_target_type,
  DROP COLUMN IF EXISTS target_snapshot,
  DROP COLUMN IF EXISTS target_identity_status,
  DROP COLUMN IF EXISTS target_id,
  DROP COLUMN IF EXISTS target_type,
  DROP COLUMN IF EXISTS idempotency_key,
  DROP COLUMN IF EXISTS schema_version;
