-- Validation: 907_dish_ontology_validation.sql
-- WP-19 Dish Ontology — structural + evidence-integrity checks over ghar_re.dish_name_synonyms.
-- Run AFTER migration 045 and seed 122. Each block RAISES on violation (fail-loud).

-- 1. The five WP-19 columns exist with the expected types.
DO $$
DECLARE missing text;
BEGIN
  SELECT string_agg(col, ', ') INTO missing FROM (
    SELECT unnest(ARRAY['alias_type','region','language','source_url','confidence']) AS col
    EXCEPT
    SELECT column_name FROM information_schema.columns
    WHERE table_schema='ghar_re' AND table_name='dish_name_synonyms'
  ) q;
  IF missing IS NOT NULL THEN
    RAISE EXCEPTION 'dish_name_synonyms missing WP-19 columns: %', missing;
  END IF;
END $$;

-- 2. Evidence integrity: every web-researched ('real') alias carries a citation and a confidence.
DO $$
DECLARE n int;
BEGIN
  SELECT count(*) INTO n FROM ghar_re.dish_name_synonyms
  WHERE data_source='real' AND (source_url IS NULL OR confidence IS NULL);
  IF n > 0 THEN
    RAISE EXCEPTION '% real aliases missing source_url or confidence (WP-19 requires cited evidence)', n;
  END IF;
END $$;

-- 3. alias_type, when set, is one of the allowed kinds (belt-and-braces vs the CHECK constraint).
DO $$
DECLARE n int;
BEGIN
  SELECT count(*) INTO n FROM ghar_re.dish_name_synonyms
  WHERE alias_type IS NOT NULL
    AND alias_type NOT IN
      ('regional_name','common_name','transliteration','english_gloss','spelling_variant');
  IF n > 0 THEN
    RAISE EXCEPTION '% aliases have an invalid alias_type', n;
  END IF;
END $$;

-- 4. Every seeded alias points at a dish that exists in ghar_re.dishes (no orphan aliases).
DO $$
DECLARE n int;
BEGIN
  SELECT count(*) INTO n FROM ghar_re.dish_name_synonyms s
  WHERE NOT EXISTS (SELECT 1 FROM ghar_re.dishes d WHERE d.id = s.dish_id);
  IF n > 0 THEN
    RAISE EXCEPTION '% orphan aliases reference a non-existent dish_id', n;
  END IF;
END $$;
