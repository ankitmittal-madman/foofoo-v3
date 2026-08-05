DO $$ BEGIN
  IF EXISTS (
    SELECT 1 FROM public.dish_regional_affinities g
    WHERE g.source_name='groq' AND g.region_code~'^(in|india)_' AND EXISTS (
      SELECT 1 FROM public.dish_regional_affinities canonical
      WHERE canonical.region_code=regexp_replace(g.region_code,'^(in|india)_','')
        AND canonical.source_name<>'groq'
    )
  ) THEN RAISE EXCEPTION 'known Foofoo region still has a Groq prefix'; END IF;
END $$;
