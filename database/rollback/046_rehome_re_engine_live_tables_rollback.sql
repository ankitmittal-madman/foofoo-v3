-- Rollback: 046_rehome_re_engine_live_tables.sql
-- Repoints public.profiles.home_state back to re_engine.re_states and drops the public copies.
-- Only safe to run while re_engine still exists (i.e. BEFORE 047 has been applied).

ALTER TABLE public.profiles DROP CONSTRAINT IF EXISTS profiles_home_state_fkey;
ALTER TABLE public.profiles
  ADD CONSTRAINT profiles_home_state_fkey
  FOREIGN KEY (home_state) REFERENCES re_engine.re_states(state_code);

DROP TABLE IF EXISTS public.re_states;
DROP TABLE IF EXISTS public.never_list;
DROP TABLE IF EXISTS public.not_today_suppression;
DROP TABLE IF EXISTS public.user_re_state;
DROP TABLE IF EXISTS public.user_taste_vectors;
DROP TABLE IF EXISTS public.re_dish_bandit_state;
