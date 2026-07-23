-- Validation: 906_ghar_re_validation.sql
-- Ghar RE v1.0 rebuild — structural + data_source integrity checks over the ghar_re schema.
-- Run AFTER migrations 034-037 and seeds 120-121. Each block RAISES on violation (fail-loud).

-- 1. Every ghar_re table carries a NOT NULL data_source of the enum type (HARD SCHEMA REQUIREMENT).
DO $$
DECLARE bad text;
BEGIN
  SELECT string_agg(t.table_name, ', ') INTO bad
  FROM information_schema.tables t
  WHERE t.table_schema='ghar_re' AND t.table_type='BASE TABLE'
    AND NOT EXISTS (
      SELECT 1 FROM information_schema.columns c
      WHERE c.table_schema='ghar_re' AND c.table_name=t.table_name
        AND c.column_name='data_source' AND c.is_nullable='NO' AND c.udt_name='data_source_kind');
  IF bad IS NOT NULL THEN
    RAISE EXCEPTION 'Tables missing NOT NULL data_source enum: %', bad;
  END IF;
END $$;

-- 2. No data_source column may have a DEFAULT (no silent 'real').
DO $$
DECLARE bad text;
BEGIN
  SELECT string_agg(table_name, ', ') INTO bad FROM information_schema.columns
  WHERE table_schema='ghar_re' AND column_name='data_source' AND column_default IS NOT NULL;
  IF bad IS NOT NULL THEN
    RAISE EXCEPTION 'data_source columns with a default (forbidden): %', bad;
  END IF;
END $$;

-- 3. The golden SAMPLE tables must contain ZERO 'real' rows (Task 2/Task 4 integrity).
DO $$
DECLARE n int;
BEGIN
  SELECT count(*) INTO n FROM (
    SELECT data_source FROM ghar_re.dishes
    UNION ALL SELECT data_source FROM ghar_re.dish_ingredients
    UNION ALL SELECT data_source FROM ghar_re.dish_macro
    UNION ALL SELECT data_source FROM ghar_re.sig_scores
    UNION ALL SELECT data_source FROM ghar_re.households
    UNION ALL SELECT data_source FROM ghar_re.region_food_affinity
    UNION ALL SELECT data_source FROM ghar_re.dish_variants
  ) s WHERE data_source='real';
  IF n > 0 THEN RAISE EXCEPTION 'Golden sample has % rows tagged real (must be 0)', n; END IF;
END $$;

-- 4. comfort_hero_map: verified_flag TRUE <-> data_source 'real'; FALSE <-> 'stub' (KB ✓/⚑).
DO $$
DECLARE n int;
BEGIN
  SELECT count(*) INTO n FROM ghar_re.comfort_hero_map
  WHERE (verified_flag AND data_source <> 'real') OR (NOT verified_flag AND data_source <> 'stub');
  IF n > 0 THEN RAISE EXCEPTION '% comfort_hero_map rows break the ✓->real / ⚑->stub mapping', n; END IF;
END $$;

-- 5. Every dish carries the doc-required added fields (NOT NULL columns already enforce this;
--    this asserts the enums are populated with valid tokens).
DO $$
DECLARE n int;
BEGIN
  SELECT count(*) INTO n FROM ghar_re.dishes
  WHERE diet NOT IN ('veg','egg','non_veg')
     OR hero_role NOT IN ('liquid','dry','single','standalone','support','snack','accompaniment')
     OR jain_compatible NOT IN ('Y','N')
     OR scope_tier NOT IN ('indian_core','indianised_daily','experimental');
  IF n > 0 THEN RAISE EXCEPTION '% dishes have invalid diet/hero_role/jain/scope_tier', n; END IF;
END $$;

-- 6. Referential smoke: every dish_ingredients ingredient resolves to a real ingredient master row.
DO $$
DECLARE n int;
BEGIN
  SELECT count(*) INTO n FROM ghar_re.dish_ingredients di
  LEFT JOIN ghar_re.ingredients i ON i.name = di.ingredient_name
  WHERE i.name IS NULL;
  IF n > 0 THEN RAISE EXCEPTION '% dish_ingredients rows reference a missing ingredient', n; END IF;
END $$;

\echo 'ghar_re validation 906: ALL CHECKS PASSED'
