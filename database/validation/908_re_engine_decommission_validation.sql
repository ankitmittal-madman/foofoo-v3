-- Validation: 908_re_engine_decommission_validation.sql
-- WP-20 — run AFTER migration 046 (re-home) to confirm the cutover is safe BEFORE running 047 (drop).
-- Each block RAISES on violation (fail-loud). This does not check code/deploy state — only the DB.

-- 1. Every re-homed table exists in public with at least as many rows as its re_engine source.
DO $$
DECLARE t text; src int; dst int; bad text[] := '{}';
BEGIN
  FOREACH t IN ARRAY ARRAY['re_states','never_list','not_today_suppression','user_re_state',
                           'user_taste_vectors','re_dish_bandit_state']
  LOOP
    EXECUTE format('SELECT count(*) FROM re_engine.%I', t) INTO src;
    EXECUTE format('SELECT count(*) FROM public.%I', t) INTO dst;
    IF dst < src THEN
      bad := array_append(bad, format('%s (re_engine=%s public=%s)', t, src, dst));
    END IF;
  END LOOP;
  IF array_length(bad,1) > 0 THEN
    RAISE EXCEPTION 'WP-20: public copy missing rows for: %', array_to_string(bad, ', ');
  END IF;
END $$;

-- 2. public.profiles.home_state now has its FK pointed at public.re_states, not re_engine.re_states.
DO $$
DECLARE n int;
BEGIN
  SELECT count(*) INTO n FROM pg_constraint
   WHERE conrelid = 'public.profiles'::regclass AND contype = 'f'
     AND confrelid = 're_engine.re_states'::regclass;
  IF n > 0 THEN
    RAISE EXCEPTION 'WP-20: profiles.home_state still FK''d to re_engine.re_states — repoint before dropping';
  END IF;
END $$;

-- 3. No FK anywhere in the database still points INTO re_engine (would break on DROP SCHEMA CASCADE
--    by silently deleting more than intended, or leave an orphaned reference).
DO $$
DECLARE bad text;
BEGIN
  SELECT string_agg(conrelid::regclass::text || ' -> ' || confrelid::regclass::text, ', ')
    INTO bad
  FROM pg_constraint
  WHERE contype = 'f' AND confrelid::regclass::text LIKE 're_engine.%'
    AND conrelid::regclass::text NOT LIKE 're_engine.%';
  IF bad IS NOT NULL THEN
    RAISE EXCEPTION 'WP-20: external FK(s) still reference re_engine: %', bad;
  END IF;
END $$;
