-- Migration: 043_household_answers_profile_id_fk_to_auth_users.sql
-- Same bug as 042, on the second table household/handler.ts writes before a profiles row can
-- exist. Step 2 (upsertHouseholdAnswers) upserts into public.household_answers on every call,
-- including the very first one for a brand-new signup — but household_answers.profile_id
-- REFERENCEd public.profiles(id), which does not exist yet at that point (profile creation is
-- step 3, gated on 5 required fields accumulated across calls). Confirmed via live Postgres logs
-- AFTER 042 was applied: "insert or update on table \"household_answers\" violates foreign key
-- constraint \"household_answers_profile_id_fkey\"" — 042 only repointed onboarding_sessions,
-- missing this second table with the identical shape of problem.
--
-- Same fix, same reasoning as 042: profile_id here also really means "the authenticated user id",
-- guaranteed to exist in auth.users the moment the caller is authenticated, regardless of whether
-- public.profiles has been created yet. Repointing the FK to auth.users(id) — profile_id remains
-- the PRIMARY KEY of this table, only the REFERENCES target changes. No orphaned rows to
-- reconcile: every prior insert against the old FK failed and rolled back.

ALTER TABLE public.household_answers
  DROP CONSTRAINT household_answers_profile_id_fkey;

ALTER TABLE public.household_answers
  ADD CONSTRAINT household_answers_profile_id_fkey
  FOREIGN KEY (profile_id) REFERENCES auth.users(id) ON DELETE CASCADE;
