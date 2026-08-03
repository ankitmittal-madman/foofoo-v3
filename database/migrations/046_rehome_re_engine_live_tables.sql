-- Migration: 046_rehome_re_engine_live_tables.sql
-- WP-20 (retire legacy re_engine schema) — STEP 1 of 2.
--
-- Copies the ONLY re_engine tables still referenced by live edge-function code into `public`, so the
-- edge functions can be repointed to public BEFORE re_engine is dropped (047). Additive and safe to
-- run while re_engine still exists — both coexist until cutover. This migration drops nothing except
-- the one external FK it repoints.
--
-- Re-homed (chosen because live code touches them — see WP-20 doc §refs):
--   re_states (36 rows, reference vocabulary)  -> public.re_states  + repoint public.profiles FK
--   never_list, not_today_suppression, user_re_state, user_taste_vectors, re_dish_bandit_state
--     (per-user RE state, all currently 0 rows) -> public.*   (DPDP user-export/hard-delete touch them)
--
-- Everything else in re_engine (the ~30 legacy reference tables: re_cohorts, re_weekly_class_plans,
-- re_personas, re_meal_classes, …) is referenced by NO live code, is backed up under
-- database/archive/re_engine_backup_20260803/, and is dropped wholesale by 047.
--
-- SECURITY POSTURE: re_engine was "service-role only; REVOKED from anon/authenticated" (schemas.ts).
-- The per-user copies below preserve that posture — RLS enabled with NO policies means anon/
-- authenticated get nothing and only service_role (which the edge functions use, and which bypasses
-- RLS) can read/write them. re_states is non-PII reference vocabulary; it is left readable like other
-- public reference data. Review this posture at cutover (audit-rls).

-- 1. re_states (reference vocabulary) — clone structure (incl. PK on state_code) + copy data.
CREATE TABLE IF NOT EXISTS public.re_states (LIKE re_engine.re_states INCLUDING ALL);
INSERT INTO public.re_states SELECT * FROM re_engine.re_states
  ON CONFLICT (state_code) DO NOTHING;

-- 2. Repoint public.profiles.home_state FK: re_engine.re_states -> public.re_states.
--    (constraint name discovered dynamically so this does not depend on an assumed name)
DO $$
DECLARE c text;
BEGIN
  SELECT conname INTO c FROM pg_constraint
   WHERE conrelid = 'public.profiles'::regclass
     AND confrelid = 're_engine.re_states'::regclass
     AND contype = 'f';
  IF c IS NOT NULL THEN
    EXECUTE format('ALTER TABLE public.profiles DROP CONSTRAINT %I', c);
  END IF;
END $$;
ALTER TABLE public.profiles
  ADD CONSTRAINT profiles_home_state_fkey
  FOREIGN KEY (home_state) REFERENCES public.re_states(state_code);

-- 3. Per-user RE-state tables (empty today) recreated in public so the DPDP user-export and
--    hard-delete edge functions keep working after re_engine is dropped.
--    Split into two passes deliberately: the DATA COPY (this loop) must complete for every table
--    regardless of what happens next, since 047 drops the source schema right after — a failure
--    here must never let 047 proceed having silently skipped a table's data.
DO $$
DECLARE t text;
BEGIN
  FOREACH t IN ARRAY ARRAY['never_list','not_today_suppression','user_re_state',
                           'user_taste_vectors','re_dish_bandit_state']
  LOOP
    EXECUTE format('CREATE TABLE IF NOT EXISTS public.%I (LIKE re_engine.%I INCLUDING ALL)', t, t);
    EXECUTE format('INSERT INTO public.%I SELECT * FROM re_engine.%I', t, t);  -- 0 rows today
  END LOOP;
END $$;

-- RLS on, no policies = service-role-only, matching the old re_engine posture ("service-role only;
-- REVOKED from anon/authenticated", schemas.ts). Kept as its own pass, AFTER every table's data is
-- safely copied: the anon/authenticated roles are a Supabase-managed platform concern (absent on a
-- vanilla local Postgres used to test this migration) — a REVOKE failure here must not be able to
-- abort the loop above and leave a table's data uncopied ahead of 047's schema drop.
DO $$
DECLARE t text;
BEGIN
  FOREACH t IN ARRAY ARRAY['never_list','not_today_suppression','user_re_state',
                           'user_taste_vectors','re_dish_bandit_state']
  LOOP
    EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', t);
    BEGIN
      EXECUTE format('REVOKE ALL ON public.%I FROM anon, authenticated', t);
    EXCEPTION WHEN undefined_object THEN
      RAISE NOTICE 'WP-20: role anon/authenticated not present (non-Supabase Postgres) — skipped REVOKE on %; apply this manually on the target platform if it lacks those platform roles.', t;
    END;
  END LOOP;
END $$;
