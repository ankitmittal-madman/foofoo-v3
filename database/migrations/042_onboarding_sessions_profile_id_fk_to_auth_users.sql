-- Migration: 042_onboarding_sessions_profile_id_fk_to_auth_users.sql
-- Fixes a live production bug: every first-time onboarding call 500s. public.onboarding_sessions.
-- profile_id previously REFERENCEd public.profiles(id), but household/handler.ts's step 1 (log
-- every screen to onboarding_sessions, the append-only source of truth) runs BEFORE step 3 (create
-- the profiles row) can possibly succeed — profile creation is gated on 5 required fields that are
-- themselves accumulated by reading back from onboarding_sessions. On a brand-new signup's very
-- first call there is no profiles row yet, so the INSERT unconditionally violated the FK. Confirmed
-- via live Postgres logs: "insert or update on table \"onboarding_sessions\" violates foreign key
-- constraint \"onboarding_sessions_profile_id_fkey\"".
--
-- profile_id has always actually meant "the authenticated household/user id" — the existing RLS
-- policy already treats it that way (ob_sessions_own ... USING (auth.uid() = profile_id), migration
-- 019), and that id is guaranteed to exist in auth.users the moment the caller is authenticated,
-- regardless of whether public.profiles has been created yet. Repointing the FK to auth.users(id)
-- fixes the ordering bug without changing any application code or any stored value. No orphaned
-- rows exist to reconcile: every prior insert against the old FK failed and rolled back.

ALTER TABLE public.onboarding_sessions
  DROP CONSTRAINT onboarding_sessions_profile_id_fkey;

ALTER TABLE public.onboarding_sessions
  ADD CONSTRAINT onboarding_sessions_profile_id_fkey
  FOREIGN KEY (profile_id) REFERENCES auth.users(id) ON DELETE CASCADE;
