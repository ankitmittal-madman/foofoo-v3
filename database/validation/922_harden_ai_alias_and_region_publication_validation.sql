DO $$ BEGIN
  IF EXISTS (
    SELECT 1 FROM public.dish_name_synonyms s JOIN public.dishes d ON d.id=s.dish_id
    WHERE s.data_source='ai_generated' AND lower(regexp_replace(btrim(s.synonym),'\s+',' ','g'))=
      lower(regexp_replace(btrim(d.name),'\s+',' ','g'))
  ) THEN RAISE EXCEPTION 'AI canonical-name alias escaped guard'; END IF;
  IF EXISTS (SELECT 1 FROM public.dish_regional_affinities
    WHERE source_name='groq' AND region_code IN ('in_rajasthan','in_punjab','in_maharashtra','it')) THEN
    RAISE EXCEPTION 'Groq regional shorthand escaped normalization';
  END IF;
END $$;
