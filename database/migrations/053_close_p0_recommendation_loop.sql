-- Close the P0 recommendation loop: explicit intent, persisted plans, experiments and push jobs.
-- All user-owned tables are service-role written and own-row readable through RLS.

ALTER TABLE public.feedback_events DROP CONSTRAINT IF EXISTS feedback_events_event_type_check;
ALTER TABLE public.feedback_events ADD CONSTRAINT feedback_events_event_type_check CHECK (
  event_type IN ('accept','edit','swap','like','dislike','shown_not_tapped','never','not_today','lock','unlock','add_to_date')
);
-- Historical clients could retry the same action without an idempotency guard. Preserve the
-- earliest canonical event and remove only exact later duplicates before enforcing uniqueness.
WITH ranked_feedback AS (
  SELECT id, row_number() OVER (
    PARTITION BY profile_id, recommendation_event_id, dish_id, event_type
    ORDER BY created_at, id
  ) AS duplicate_rank
  FROM public.feedback_events
)
DELETE FROM public.feedback_events
WHERE id IN (SELECT id FROM ranked_feedback WHERE duplicate_rank > 1);
ALTER TABLE public.feedback_events ADD CONSTRAINT feedback_events_idempotency_key
  UNIQUE NULLS NOT DISTINCT (profile_id, recommendation_event_id, dish_id, event_type);

-- Re-homing with LIKE in migration 046 did not recreate external foreign keys.
ALTER TABLE public.never_list
  ADD CONSTRAINT never_list_profile_fkey FOREIGN KEY (profile_id) REFERENCES public.profiles(id) ON DELETE CASCADE,
  ADD CONSTRAINT never_list_dish_fkey FOREIGN KEY (dish_id) REFERENCES public.dishes(id) ON DELETE CASCADE;
ALTER TABLE public.not_today_suppression
  ADD CONSTRAINT not_today_profile_fkey FOREIGN KEY (profile_id) REFERENCES public.profiles(id) ON DELETE CASCADE,
  ADD CONSTRAINT not_today_dish_fkey FOREIGN KEY (dish_id) REFERENCES public.dishes(id) ON DELETE CASCADE;
ALTER TABLE public.user_taste_vectors
  ADD CONSTRAINT user_taste_vectors_profile_fkey FOREIGN KEY (profile_id) REFERENCES public.profiles(id) ON DELETE CASCADE;
ALTER TABLE public.user_taste_vectors ADD COLUMN IF NOT EXISTS dish_affinity jsonb NOT NULL DEFAULT '{}';
ALTER TABLE public.user_re_state
  ADD CONSTRAINT user_re_state_profile_fkey FOREIGN KEY (profile_id) REFERENCES public.profiles(id) ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS idx_never_list_active
  ON public.never_list (profile_id) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_not_today_active
  ON public.not_today_suppression (profile_id, effective_until) WHERE is_active = true;

-- First-party product telemetry is canonical; vendor export is optional and consent-gated.
CREATE TABLE public.product_events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  profile_id uuid NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
  event_name text NOT NULL,
  request_id text,
  dish_id uuid REFERENCES public.dishes(id) ON DELETE SET NULL,
  properties jsonb NOT NULL DEFAULT '{}',
  experiment_assignments jsonb NOT NULL DEFAULT '{}',
  occurred_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_product_events_profile_time ON public.product_events (profile_id, occurred_at DESC);
CREATE INDEX idx_product_events_name_time ON public.product_events (event_name, occurred_at DESC);
ALTER TABLE public.product_events ENABLE ROW LEVEL SECURITY;
CREATE POLICY product_events_select_own ON public.product_events FOR SELECT
  USING ((select auth.uid()) = profile_id);

CREATE VIEW public.recommendation_kpis_daily WITH (security_invoker = true) AS
WITH served AS (
  SELECT created_at::date AS metric_date, count(DISTINCT profile_id) AS active_households,
         sum(plate_count) AS dishes_shown
  FROM public.recommendation_events WHERE re_served = true GROUP BY created_at::date
), actions AS (
  SELECT r.created_at::date AS metric_date,
         count(f.id) FILTER (WHERE f.event_type IN ('accept','like')) AS positive_actions,
         count(f.id) FILTER (WHERE f.event_type = 'never') AS never_actions
  FROM public.recommendation_events r
  JOIN public.feedback_events f ON f.recommendation_event_id = r.id
  GROUP BY r.created_at::date
)
SELECT s.metric_date, s.active_households, s.dishes_shown,
       coalesce(a.positive_actions, 0) AS positive_actions,
       coalesce(a.never_actions, 0) AS never_actions,
       round(coalesce(a.positive_actions, 0)::numeric / NULLIF(s.dishes_shown, 0), 4) AS acceptance_rate,
       round(coalesce(a.never_actions, 0)::numeric / NULLIF(s.dishes_shown, 0), 4) AS never_rate
FROM served s LEFT JOIN actions a USING (metric_date);
REVOKE ALL ON public.recommendation_kpis_daily FROM anon, authenticated;

CREATE TABLE public.experiments (
  experiment_key text PRIMARY KEY,
  variants text[] NOT NULL CHECK (cardinality(variants) >= 2),
  allocation_pct smallint NOT NULL DEFAULT 100 CHECK (allocation_pct BETWEEN 0 AND 100),
  is_active boolean NOT NULL DEFAULT false,
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE public.notification_devices (
  profile_id uuid NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
  provider text NOT NULL DEFAULT 'onesignal',
  device_external_id text NOT NULL,
  timezone text NOT NULL DEFAULT 'Asia/Kolkata',
  is_active boolean NOT NULL DEFAULT true,
  updated_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (profile_id, provider, device_external_id)
);
ALTER TABLE public.notification_devices ENABLE ROW LEVEL SECURITY;

CREATE TABLE public.notification_jobs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  profile_id uuid NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
  job_date date NOT NULL,
  notification_type text NOT NULL DEFAULT 'morning_plan',
  scheduled_for timestamptz NOT NULL,
  payload jsonb NOT NULL DEFAULT '{}',
  status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','processing','sent','failed','cancelled')),
  attempts smallint NOT NULL DEFAULT 0,
  provider_message_id text,
  last_error text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (profile_id, job_date, notification_type)
);
CREATE INDEX idx_notification_jobs_due ON public.notification_jobs (scheduled_for)
  WHERE status IN ('pending','failed');
ALTER TABLE public.notification_jobs ENABLE ROW LEVEL SECURITY;

-- Existing planning tables become the canonical server-side plan store.
ALTER TABLE public.week_plans ADD COLUMN IF NOT EXISTS status text NOT NULL DEFAULT 'draft'
  CHECK (status IN ('draft','finalized'));
ALTER TABLE public.week_plans ADD COLUMN IF NOT EXISTS updated_at timestamptz NOT NULL DEFAULT now();
