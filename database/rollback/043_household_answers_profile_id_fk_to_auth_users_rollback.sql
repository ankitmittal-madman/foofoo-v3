-- Rollback: 043_household_answers_profile_id_fk_to_auth_users.sql

ALTER TABLE public.household_answers
  DROP CONSTRAINT household_answers_profile_id_fkey;

ALTER TABLE public.household_answers
  ADD CONSTRAINT household_answers_profile_id_fkey
  FOREIGN KEY (profile_id) REFERENCES public.profiles(id) ON DELETE CASCADE;
