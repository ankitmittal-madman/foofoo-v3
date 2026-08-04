ALTER TABLE public.week_plans DROP COLUMN IF EXISTS updated_at;
ALTER TABLE public.week_plans DROP COLUMN IF EXISTS status;
DROP TABLE IF EXISTS public.notification_jobs;
DROP TABLE IF EXISTS public.notification_devices;
DROP TABLE IF EXISTS public.experiments;
DROP VIEW IF EXISTS public.recommendation_kpis_daily;
DROP TABLE IF EXISTS public.product_events;
DROP INDEX IF EXISTS public.idx_not_today_active;
DROP INDEX IF EXISTS public.idx_never_list_active;
ALTER TABLE public.user_re_state DROP CONSTRAINT IF EXISTS user_re_state_profile_fkey;
ALTER TABLE public.user_taste_vectors DROP CONSTRAINT IF EXISTS user_taste_vectors_profile_fkey;
ALTER TABLE public.user_taste_vectors DROP COLUMN IF EXISTS dish_affinity;
ALTER TABLE public.not_today_suppression DROP CONSTRAINT IF EXISTS not_today_dish_fkey;
ALTER TABLE public.not_today_suppression DROP CONSTRAINT IF EXISTS not_today_profile_fkey;
ALTER TABLE public.never_list DROP CONSTRAINT IF EXISTS never_list_dish_fkey;
ALTER TABLE public.never_list DROP CONSTRAINT IF EXISTS never_list_profile_fkey;
ALTER TABLE public.feedback_events DROP CONSTRAINT IF EXISTS feedback_events_event_type_check;
ALTER TABLE public.feedback_events DROP CONSTRAINT IF EXISTS feedback_events_idempotency_key;
ALTER TABLE public.feedback_events ADD CONSTRAINT feedback_events_event_type_check CHECK (
  event_type IN ('accept','edit','swap','like','dislike','shown_not_tapped')
);
