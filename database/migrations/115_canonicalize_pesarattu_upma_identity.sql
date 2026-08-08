-- Retire the duplicate "Pesarattu MLC" catalogue row and preserve both the historical typo and
-- the established MLA Pesarattu name as resolvable aliases of canonical Pesarattu Upma.
--
-- This does not rewrite immutable recommendation exposures, outcomes or feedback. Existing rows
-- continue to reference the historical UUID; future name resolution and serving use one canonical
-- identity. The duplicate remains recoverable under a non-user-facing retired name so rollback
-- does not depend on reconstructing deleted data.

DO $canonicalize$
DECLARE
  v_canonical_id uuid;
  v_duplicate_id uuid;
  v_retired_name constant text := 'Pesarattu MLC [retired duplicate]';
BEGIN
  SELECT id INTO v_canonical_id
  FROM public.dishes
  WHERE name = 'Pesarattu Upma';

  SELECT id INTO v_duplicate_id
  FROM public.dishes
  WHERE name = 'Pesarattu MLC';

  IF v_canonical_id IS NULL THEN
    RAISE EXCEPTION 'canonical Pesarattu Upma dish is missing';
  END IF;
  IF EXISTS (
    SELECT 1 FROM public.dishes
    WHERE name = v_retired_name AND id IS DISTINCT FROM v_duplicate_id
  ) THEN
    RAISE EXCEPTION 'retired Pesarattu duplicate name is already occupied';
  END IF;

  IF v_duplicate_id IS NOT NULL THEN
    UPDATE public.dishes
    SET name = v_retired_name,
        is_active = false
    WHERE id = v_duplicate_id;
  END IF;

  INSERT INTO public.dish_aliases (
    dish_id, alias_text, alias_source, import_run_id, confidence
  )
  VALUES (v_canonical_id, 'Pesarattu MLC', 'dedupe_merge', NULL, 1.000)
  ON CONFLICT (dish_id, alias_text) DO UPDATE
  SET alias_source = EXCLUDED.alias_source,
      confidence = EXCLUDED.confidence;

  INSERT INTO public.dish_name_synonyms (
    dish_id, synonym, data_source, alias_type, region, language, source_url, confidence
  )
  VALUES (
    v_canonical_id,
    'MLA Pesarattu',
    'real',
    'common_name',
    'Andhra Pradesh',
    'telugu',
    'https://www.slurrp.com/slurrp360/regional/pesarattu-1665403098313',
    0.950
  )
  ON CONFLICT (dish_id, synonym) DO UPDATE
  SET data_source = EXCLUDED.data_source,
      alias_type = EXCLUDED.alias_type,
      region = EXCLUDED.region,
      language = EXCLUDED.language,
      source_url = EXCLUDED.source_url,
      confidence = EXCLUDED.confidence;
END
$canonicalize$;

COMMENT ON TABLE public.dish_aliases IS
  'ETL-discovered aliases and reviewed dedupe names. Pesarattu MLC resolves to canonical Pesarattu Upma; historical facts retain their original UUID.';
