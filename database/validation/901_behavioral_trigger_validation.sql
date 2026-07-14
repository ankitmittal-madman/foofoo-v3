-- Migration: 901_behavioral_trigger_validation.sql (validation script)
-- Implements: DOC-P3-04 v1.3 §03.6A (fn_derive_dish_attributes, fn_propagate_ingredient_change)
-- Logical functions: LF-K01 deriveDishAttributes() — DOC-P3-03 v1.0 §13, all 5 numbered rules
-- Governance refs: DOC-P3-05 Part (a) v1.2 Phase 12 (trigger behavioral validation)
-- Behavioral claim under test: "derived attributes remain correct" (founder requirement #4)
-- Traceability: each test below cites the exact DOC-P3-03 rule it proves, not just "the
-- trigger ran without error."

\echo '=== BEHAVIORAL VALIDATION: fn_derive_dish_attributes() ==='

-- TEST 1: Rule 2 — a dish with NO non-veg ingredient and NOT all-vegan -> diet_type = 'veg'
\echo '--- Test 1: Poha (canonical: onion, mustard, turmeric, rice) should derive diet_type=vegan, is_jain=false (onion is jain-excluded) ---'
SELECT name, diet_type, is_jain, allergen_flags
FROM public.dishes WHERE name = 'Poha';
-- EXPECTED (WP-6E.2 canonical seeds 103/106/107): diet_type='vegan' (all ingredients vegan;
-- 'vegan' is the stricter case of Rule 2's "no non-veg ingredient"), is_jain=false because
-- canonical ingredient 'onion'.is_jain_excluded=true (seed 103) — proving LF-K01 Rule 3:
-- is_jain requires ALL ingredients jain-safe; onion is not, so Poha comes out is_jain=false.
-- (Modernized WP-6E3: canonical Poha derives 'vegan' — was 'veg' against the removed file-102 row.)

-- TEST 2: Rule 1 — allergen_flags is the UNION of ingredient allergens
\echo '--- Test 2: Bharli Vangi (canonical, contains peanut) should derive allergen_flags including bit 0 (nuts, value 1) ---'
SELECT name, allergen_flags, (allergen_flags & 1) > 0 AS has_nut_allergen_bit
FROM public.dishes WHERE name = 'Bharli Vangi';
-- EXPECTED: has_nut_allergen_bit = true, proving the UNION logic in LF-K01 Rule 1 actually
-- executed via the trigger. Canonical seed 106/107 insert dish + dish_ingredients with the
-- derived columns left unset; fn_derive_dish_attributes populates allergen_flags from the
-- union of ingredient allergens (peanut carries the nut bit).
-- (Modernized WP-6E3: canonical dish 'Bharli Vangi' replaces the removed illustrative
-- 'Aloo Poha with Peanuts'; both exercise the same nut-bit union path.)

-- TEST 3: Rule 2 — ANY non-veg ingredient -> diet_type = 'non_veg'
\echo '--- Test 3: Butter Chicken (chicken, ghee, onion) should derive diet_type=non_veg ---'
SELECT name, diet_type, is_jain FROM public.dishes WHERE name = 'Butter Chicken';
-- EXPECTED: diet_type='non_veg' (Chicken.is_veg=false), is_jain=false (diet_type != veg,
-- Rule 3's precondition fails regardless of ingredient jain-safety).

-- TEST 4 (live mutation test): Rule 5 — UPDATE-time re-derivation via fn_propagate_ingredient_change
\echo '--- Test 4: changing peanut.allergen_flags should immediately re-derive Bharli Vangi (AGR-003 behavioral proof) ---'
DO $$
DECLARE
  v_before integer;
  v_after integer;
BEGIN
  SELECT allergen_flags INTO v_before FROM public.dishes WHERE name = 'Bharli Vangi';
  -- Simulate a content-ops correction: peanut gains the soy bit too (value 32) for this test
  UPDATE public.ingredients SET allergen_flags = allergen_flags | 32 WHERE name = 'peanut';
  SELECT allergen_flags INTO v_after FROM public.dishes WHERE name = 'Bharli Vangi';
  ASSERT v_after = (v_before | 32),
    'FAIL: fn_propagate_ingredient_change did not re-derive the dish after ingredient change';
  RAISE NOTICE 'PASS: dish allergen_flags updated from % to % immediately after ingredient edit, with no manual re-derivation step', v_before, v_after;
  -- Revert for idempotent re-running of this test script
  UPDATE public.ingredients SET allergen_flags = allergen_flags & ~32 WHERE name = 'peanut';
END $$;
-- (Modernized WP-6E3: canonical dish 'Bharli Vangi' + canonical ingredient slug 'peanut'
--  replace the removed illustrative 'Aloo Poha with Peanuts' / 'Peanuts' — same propagate path.)
-- This is the single most important behavioral test in this file: it proves the exact
-- mechanism that closed AGR-003 actually works end-to-end, not just that the SQL applied
-- without a Postgres error.

-- TEST 5: privilege enforcement — application role genuinely cannot override the trigger
\echo '--- Test 5: authenticated role cannot directly set diet_type (AGR-001 + Invariant 6 proof) ---'
DO $$
BEGIN
  BEGIN
    EXECUTE 'SET ROLE authenticated';
    EXECUTE 'UPDATE public.dishes SET diet_type = ''vegan'' WHERE name = ''Poha''';
    RAISE EXCEPTION 'FAIL: authenticated role was able to write diet_type directly — Invariant 6 violated';
  EXCEPTION WHEN insufficient_privilege THEN
    RAISE NOTICE 'PASS: authenticated role correctly blocked from writing derived column';
  END;
  RESET ROLE;
END $$;
