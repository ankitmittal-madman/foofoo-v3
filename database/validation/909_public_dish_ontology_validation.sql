-- Validation: 909_public_dish_ontology_validation.sql
-- WP-19 Dish Ontology (retargeted onto public.dishes post-WP-21). Structural + evidence-integrity
-- checks over public.dish_name_synonyms. Run AFTER migration 051 and its seed(s). Each block
-- RAISES on violation (fail-loud).

-- 1. The table and its expected columns exist.
DO $$
DECLARE missing text;
BEGIN
  SELECT string_agg(col, ', ') INTO missing FROM (
    SELECT unnest(ARRAY['dish_id','synonym','data_source','alias_type','region','language','source_url','confidence']) AS col
    EXCEPT
    SELECT column_name FROM information_schema.columns
    WHERE table_schema='public' AND table_name='dish_name_synonyms'
  ) q;
  IF missing IS NOT NULL THEN
    RAISE EXCEPTION 'public.dish_name_synonyms missing columns: %', missing;
  END IF;
END $$;

-- 2. Evidence integrity: every web-researched ('real') alias carries a citation and a confidence.
DO $$
DECLARE n int;
BEGIN
  SELECT count(*) INTO n FROM public.dish_name_synonyms
  WHERE data_source='real' AND (source_url IS NULL OR confidence IS NULL);
  IF n > 0 THEN
    RAISE EXCEPTION '% real aliases missing source_url or confidence (cited evidence required)', n;
  END IF;
END $$;

-- 3. alias_type, when set, is one of the allowed kinds (belt-and-braces vs the CHECK constraint).
DO $$
DECLARE n int;
BEGIN
  SELECT count(*) INTO n FROM public.dish_name_synonyms
  WHERE alias_type IS NOT NULL
    AND alias_type NOT IN
      ('regional_name','common_name','transliteration','english_gloss','spelling_variant');
  IF n > 0 THEN
    RAISE EXCEPTION '% aliases have an invalid alias_type', n;
  END IF;
END $$;

-- 4. Every seeded alias points at a dish that exists in public.dishes (no orphan aliases).
DO $$
DECLARE n int;
BEGIN
  SELECT count(*) INTO n FROM public.dish_name_synonyms s
  WHERE NOT EXISTS (SELECT 1 FROM public.dishes d WHERE d.id = s.dish_id);
  IF n > 0 THEN
    RAISE EXCEPTION '% orphan aliases reference a non-existent dish_id', n;
  END IF;
END $$;

-- 5. No alias string equals another dish's own canonical name (the WP-19 safety filter,
--    checked structurally here as a second line of defense against a conflated alias).
DO $$
DECLARE n int;
BEGIN
  SELECT count(*) INTO n FROM public.dish_name_synonyms s
  JOIN public.dishes d2 ON d2.name = s.synonym AND d2.id <> s.dish_id;
  IF n > 0 THEN
    RAISE EXCEPTION '% aliases collide with a DIFFERENT dish''s own canonical name', n;
  END IF;
END $$;
