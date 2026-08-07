-- Canonical recommendation interaction envelope v2.
--
-- This expands the live feedback_events write path instead of creating a third competing event
-- store. Legacy clients remain valid as schema_version=1. New clients provide a retry key,
-- explicit target identity, intended meal moment, evidence source and serving-version lineage.

ALTER TABLE public.feedback_events
  ADD COLUMN IF NOT EXISTS schema_version text NOT NULL DEFAULT '1',
  ADD COLUMN IF NOT EXISTS idempotency_key text,
  ADD COLUMN IF NOT EXISTS target_type text,
  ADD COLUMN IF NOT EXISTS target_id text,
  ADD COLUMN IF NOT EXISTS target_identity_status text,
  ADD COLUMN IF NOT EXISTS target_snapshot jsonb NOT NULL DEFAULT '{}',
  ADD COLUMN IF NOT EXISTS replacement_target_type text,
  ADD COLUMN IF NOT EXISTS replacement_target_id text,
  ADD COLUMN IF NOT EXISTS occurred_at timestamptz NOT NULL DEFAULT now(),
  ADD COLUMN IF NOT EXISTS local_timezone text,
  ADD COLUMN IF NOT EXISTS intended_meal_date date,
  ADD COLUMN IF NOT EXISTS weekday text,
  ADD COLUMN IF NOT EXISTS day_type text,
  ADD COLUMN IF NOT EXISTS source_surface text,
  ADD COLUMN IF NOT EXISTS evidence_kind text NOT NULL DEFAULT 'explicit',
  ADD COLUMN IF NOT EXISTS shown_rank smallint,
  ADD COLUMN IF NOT EXISTS selection_propensity real,
  ADD COLUMN IF NOT EXISTS reason_code text,
  ADD COLUMN IF NOT EXISTS catalog_version text,
  ADD COLUMN IF NOT EXISTS config_version text,
  ADD COLUMN IF NOT EXISTS feature_version text,
  ADD COLUMN IF NOT EXISTS policy_version text,
  ADD COLUMN IF NOT EXISTS model_version text;

ALTER TABLE public.feedback_events DROP CONSTRAINT IF EXISTS feedback_events_event_type_check;
ALTER TABLE public.feedback_events ADD CONSTRAINT feedback_events_event_type_check CHECK (
  event_type IN (
    'accept','edit','swap','like','dislike','shown_not_tapped','never','not_today','lock','unlock',
    'add_to_date','make_this','too_much_work','missing_ingredient','member_objection','cooked',
    'ordered','replaced','completed','regretted','opened','search','selected'
  )
);

ALTER TABLE public.feedback_events
  ADD CONSTRAINT feedback_events_schema_version_check
    CHECK (schema_version IN ('1','2')),
  ADD CONSTRAINT feedback_events_target_type_check
    CHECK (target_type IS NULL OR target_type IN
      ('dish','meal_episode','meal_class','ingredient','query','plan_slot')),
  ADD CONSTRAINT feedback_events_target_identity_status_check
    CHECK (target_identity_status IS NULL OR target_identity_status IN ('resolved','unresolved')),
  ADD CONSTRAINT feedback_events_replacement_target_type_check
    CHECK (replacement_target_type IS NULL OR replacement_target_type IN
      ('dish','meal_episode','meal_class','ingredient','query','plan_slot')),
  ADD CONSTRAINT feedback_events_replacement_pair_check
    CHECK ((replacement_target_type IS NULL) = (replacement_target_id IS NULL)),
  ADD CONSTRAINT feedback_events_day_type_check
    CHECK (day_type IS NULL OR day_type IN ('weekday','weekend')),
  ADD CONSTRAINT feedback_events_weekday_check
    CHECK (weekday IS NULL OR weekday IN
      ('Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday')),
  ADD CONSTRAINT feedback_events_evidence_kind_check
    CHECK (evidence_kind IN ('explicit','inferred','integration','operator')),
  ADD CONSTRAINT feedback_events_shown_rank_check
    CHECK (shown_rank IS NULL OR shown_rank > 0),
  ADD CONSTRAINT feedback_events_propensity_check
    CHECK (selection_propensity IS NULL OR
      (selection_propensity > 0 AND selection_propensity <= 1)),
  ADD CONSTRAINT feedback_events_v2_required_fields_check CHECK (
    schema_version <> '2' OR (
      idempotency_key IS NOT NULL AND nullif(btrim(idempotency_key), '') IS NOT NULL AND
      target_type IS NOT NULL AND target_id IS NOT NULL AND
      target_identity_status IS NOT NULL AND local_timezone IS NOT NULL AND
      source_surface IS NOT NULL AND slot IS NOT NULL
    )
  );

UPDATE public.feedback_events
SET occurred_at = created_at,
    target_type = CASE
      WHEN dish_id IS NOT NULL OR nullif(detail->>'dish_name', '') IS NOT NULL THEN 'dish'
      ELSE target_type
    END,
    target_id = coalesce(target_id, dish_id::text),
    target_identity_status = CASE
      WHEN dish_id IS NOT NULL THEN 'resolved'
      WHEN nullif(detail->>'dish_name', '') IS NOT NULL THEN 'unresolved'
      ELSE target_identity_status
    END,
    target_snapshot = CASE
      WHEN nullif(detail->>'dish_name', '') IS NOT NULL
        THEN jsonb_build_object('display_name', detail->>'dish_name')
      ELSE target_snapshot
    END
WHERE schema_version = '1';

-- v2 clients carry their own stable retry key. Legacy rows retain the former semantic uniqueness
-- rule, now extended with target_id so two meal classes in one weekly slate cannot collide.
ALTER TABLE public.feedback_events
  DROP CONSTRAINT IF EXISTS feedback_events_idempotency_key;
CREATE UNIQUE INDEX feedback_events_v2_idempotency_key
  ON public.feedback_events (household_id, profile_id, idempotency_key)
  WHERE idempotency_key IS NOT NULL;
CREATE UNIQUE INDEX feedback_events_legacy_semantic_key
  ON public.feedback_events (
    profile_id,
    recommendation_event_id,
    event_type,
    coalesce(dish_id::text, target_id, '__none__')
  )
  WHERE idempotency_key IS NULL;

CREATE INDEX feedback_events_target_moment
  ON public.feedback_events (
    household_id, target_type, target_id, slot, day_type, intended_meal_date, occurred_at DESC
  );
CREATE INDEX feedback_events_class_learning
  ON public.feedback_events (household_id, target_id, slot, occurred_at DESC)
  WHERE target_type = 'meal_class' AND data_source = 'real';

CREATE OR REPLACE FUNCTION public.validate_recommendation_interaction_v2_target()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog, public
AS $$
BEGIN
  IF NEW.schema_version <> '2' THEN RETURN NEW; END IF;
  IF NEW.target_type = 'meal_class' AND NOT EXISTS (
    SELECT 1 FROM public.meal_classes c
    WHERE c.class_code = NEW.target_id AND c.is_active
  ) THEN
    RAISE EXCEPTION 'meal_class target is not active: %', NEW.target_id;
  END IF;
  IF NEW.target_type = 'dish' AND NEW.target_identity_status = 'resolved' AND
     (NEW.dish_id IS NULL OR NEW.target_id IS DISTINCT FROM NEW.dish_id::text) THEN
    RAISE EXCEPTION 'resolved dish target must match dish_id';
  END IF;
  RETURN NEW;
END;
$$;

CREATE TRIGGER feedback_events_validate_v2_target
  BEFORE INSERT OR UPDATE OF schema_version,target_type,target_id,target_identity_status,dish_id
  ON public.feedback_events
  FOR EACH ROW EXECUTE FUNCTION public.validate_recommendation_interaction_v2_target();

CREATE OR REPLACE VIEW public.recommendation_interactions_v2
WITH (security_invoker = true) AS
SELECT
  id AS event_id,
  schema_version,
  idempotency_key,
  household_id,
  profile_id AS actor_profile_id,
  recommendation_event_id,
  event_type,
  target_type,
  target_id,
  target_identity_status,
  target_snapshot,
  replacement_target_type,
  replacement_target_id,
  occurred_at,
  created_at AS received_at,
  local_timezone,
  intended_meal_date,
  slot AS meal_slot,
  weekday,
  day_type,
  source_surface,
  evidence_kind,
  shown_rank,
  selection_propensity,
  reason_code,
  catalog_version,
  config_version,
  feature_version,
  policy_version,
  model_version,
  detail,
  data_source
FROM public.feedback_events;

REVOKE ALL ON public.recommendation_interactions_v2 FROM PUBLIC, anon, authenticated;
GRANT SELECT ON public.recommendation_interactions_v2 TO service_role;

-- All behavioral writes must cross the authenticated Edge boundary. RLS alone cannot prevent a
-- direct client from labelling its own row inferred/operator or skipping class identity checks.
REVOKE INSERT, UPDATE, DELETE ON public.feedback_events FROM anon, authenticated;

COMMENT ON VIEW public.recommendation_interactions_v2 IS
  'Service-only canonical event envelope for Ghar feature replay and governed Aux export. Exposure is not acceptance; target and intended meal moment are explicit.';
COMMENT ON COLUMN public.feedback_events.evidence_kind IS
  'Authority class. Authenticated /feedback accepts explicit only; inferred/integration/operator require governed internal writers.';
