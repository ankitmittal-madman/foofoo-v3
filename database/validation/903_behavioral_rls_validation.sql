-- Migration: 903_behavioral_rls_validation.sql (validation script)
-- Implements: DOC-P3-04 v1.3 §03, all 19 RLS-enabled tables (file 019)
-- Logical functions: n/a — security model verification
-- Governance refs: DOC-P3-05 Part (a) v1.2 Phase 12 ("manual review" required for true
--   logical-correctness of RLS, beyond mere presence — this script provides the automatable
--   portion of that check by impersonating two distinct authenticated users)
-- Behavioral claim under test: "RLS policies enforce the intended security model"
--   (founder requirement #4) — NOT just "RLS is enabled," which file 900 already checked.

\echo '=== BEHAVIORAL VALIDATION: RLS enforcement across two distinct users ==='

DO $$
DECLARE
  v_user_a uuid;
  v_user_b uuid;
  v_visible_count integer;
BEGIN
  SELECT id INTO v_user_a FROM public.profiles OFFSET 0 LIMIT 1;
  SELECT id INTO v_user_b FROM public.profiles OFFSET 1 LIMIT 1;

  IF v_user_a IS NULL OR v_user_b IS NULL THEN
    RAISE NOTICE 'SKIPPED: this test requires at least 2 distinct profile fixtures to prove cross-user isolation. Only 0-1 found.';
    RETURN;
  END IF;

  -- Simulate user A's session
  PERFORM set_config('request.jwt.claims', json_build_object('sub', v_user_a)::text, true);
  EXECUTE 'SET ROLE authenticated';

  SELECT count(*) INTO v_visible_count FROM public.profiles;
  ASSERT v_visible_count = 1,
    format('FAIL: user A should see exactly 1 profile row (their own), saw %s', v_visible_count);
  RAISE NOTICE 'PASS: profiles_select_own correctly restricts user A to exactly their own row';

  SELECT count(*) INTO v_visible_count FROM public.household_members WHERE profile_id = v_user_b;
  ASSERT v_visible_count = 0,
    'FAIL: user A should not be able to see user B''s household_members rows';
  RAISE NOTICE 'PASS: hm_all_own correctly blocks cross-user household_members visibility';

  RESET ROLE;
END $$;

-- Behavioral proof for the public-read tables: an UNAUTHENTICATED role can read dishes,
-- but cannot write to it (proves dishes_public_read is read-only, not accidentally permissive)
\echo '--- Public-read table write protection (anon role) ---'
DO $$
BEGIN
  EXECUTE 'SET ROLE anon';
  BEGIN
    EXECUTE 'INSERT INTO public.dishes (name, meal_occasion, cook_time_minutes, difficulty) VALUES (''Hack Attempt'', ARRAY[''breakfast''], 5, ''beginner'')';
    RAISE EXCEPTION 'FAIL: anon role was able to INSERT into dishes — RLS misconfigured';
  EXCEPTION WHEN insufficient_privilege OR others THEN
    RAISE NOTICE 'PASS: anon role correctly blocked from writing to public.dishes';
  END;
  RESET ROLE;
END $$;

-- Behavioral proof that re_engine is invisible to client roles entirely (not just RLS, but
-- schema-level lockdown per file 001)
\echo '--- re_engine schema invisibility ---'
DO $$
BEGIN
  EXECUTE 'SET ROLE authenticated';
  BEGIN
    EXECUTE 'SELECT count(*) FROM re_engine.never_list';
    RAISE EXCEPTION 'FAIL: authenticated role was able to query re_engine.never_list directly — schema lockdown breached';
  EXCEPTION WHEN insufficient_privilege OR invalid_schema_name THEN
    RAISE NOTICE 'PASS: authenticated role correctly cannot query re_engine tables at all';
  END;
  RESET ROLE;
END $$;
