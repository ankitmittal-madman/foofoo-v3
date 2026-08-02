-- Rollback: 042_onboarding_sessions_profile_id_fk_to_auth_users.sql

ALTER TABLE public.onboarding_sessions
  DROP CONSTRAINT onboarding_sessions_profile_id_fkey;

ALTER TABLE public.onboarding_sessions
  ADD CONSTRAINT onboarding_sessions_profile_id_fkey
  FOREIGN KEY (profile_id) REFERENCES public.profiles(id) ON DELETE CASCADE;
