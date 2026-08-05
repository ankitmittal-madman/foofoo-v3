-- Migration: 068_harden_ai_alias_and_region_publication.sql
-- Deterministic gates catch errors confidence cannot: canonical repeats, compound fragments and
-- provider-specific regional shorthand. They also clean the controlled production probe.

CREATE OR REPLACE FUNCTION public.guard_ai_dish_synonym()
RETURNS trigger LANGUAGE plpgsql SET search_path=public,pg_temp AS $$
DECLARE canonical text; normalized_alias text; canonical_words text[];
BEGIN
  IF NEW.data_source<>'ai_generated' THEN RETURN NEW; END IF;
  SELECT lower(regexp_replace(btrim(name),'\s+',' ','g')) INTO canonical
  FROM public.dishes WHERE id=NEW.dish_id;
  normalized_alias:=lower(regexp_replace(btrim(NEW.synonym),'\s+',' ','g'));
  IF normalized_alias=canonical THEN RETURN NULL; END IF;
  canonical_words:=regexp_split_to_array(canonical,'\s+');
  IF cardinality(canonical_words)>1 AND normalized_alias !~ '\s'
    AND normalized_alias=ANY(canonical_words) THEN RETURN NULL; END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER dish_name_synonyms_ai_quality_guard
BEFORE INSERT OR UPDATE ON public.dish_name_synonyms
FOR EACH ROW EXECUTE FUNCTION public.guard_ai_dish_synonym();

CREATE OR REPLACE FUNCTION public.normalize_groq_region_code()
RETURNS trigger LANGUAGE plpgsql SET search_path=public,pg_temp AS $$
BEGIN
  IF NEW.source_name='groq' THEN
    NEW.region_code:=CASE NEW.region_code
      WHEN 'in_rajasthan' THEN 'rajasthan' WHEN 'in_punjab' THEN 'punjab'
      WHEN 'in_maharashtra' THEN 'maharashtra' WHEN 'in_gujarat' THEN 'gujarat'
      WHEN 'in_kerala' THEN 'kerala' WHEN 'in_karnataka' THEN 'karnataka'
      WHEN 'in_tamil_nadu' THEN 'tamil_nadu' WHEN 'in_west_bengal' THEN 'west_bengal'
      WHEN 'in_uttar_pradesh' THEN 'uttar_pradesh' WHEN 'in_north_india' THEN 'north_india'
      WHEN 'in_south_india' THEN 'south_india' WHEN 'in_east_india' THEN 'east_india'
      WHEN 'in_west_india' THEN 'west_india' WHEN 'it' THEN 'italy'
      ELSE NEW.region_code END;
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER dish_regional_affinities_groq_code_normalizer
BEFORE INSERT OR UPDATE ON public.dish_regional_affinities
FOR EACH ROW EXECUTE FUNCTION public.normalize_groq_region_code();

DELETE FROM public.dish_name_synonyms s USING public.dishes d
WHERE s.dish_id=d.id AND s.data_source='ai_generated' AND s.source_version='openai/gpt-oss-120b'
  AND (
    lower(regexp_replace(btrim(s.synonym),'\s+',' ','g'))=lower(regexp_replace(btrim(d.name),'\s+',' ','g'))
    OR (
      cardinality(regexp_split_to_array(lower(regexp_replace(btrim(d.name),'\s+',' ','g')),'\s+'))>1
      AND lower(btrim(s.synonym)) !~ '\s'
      AND lower(btrim(s.synonym))=ANY(regexp_split_to_array(lower(regexp_replace(btrim(d.name),'\s+',' ','g')),'\s+'))
    )
  );

DELETE FROM public.dish_regional_affinities g
USING public.dish_regional_affinities canonical
WHERE g.source_name='groq' AND g.dish_id=canonical.dish_id
  AND canonical.region_code=CASE g.region_code WHEN 'in_rajasthan' THEN 'rajasthan'
    WHEN 'in_punjab' THEN 'punjab' WHEN 'in_maharashtra' THEN 'maharashtra'
    WHEN 'in_gujarat' THEN 'gujarat' WHEN 'in_kerala' THEN 'kerala'
    WHEN 'in_karnataka' THEN 'karnataka' WHEN 'in_tamil_nadu' THEN 'tamil_nadu'
    WHEN 'in_west_bengal' THEN 'west_bengal' WHEN 'in_uttar_pradesh' THEN 'uttar_pradesh'
    WHEN 'in_north_india' THEN 'north_india' WHEN 'in_south_india' THEN 'south_india'
    WHEN 'in_east_india' THEN 'east_india' WHEN 'in_west_india' THEN 'west_india'
    WHEN 'it' THEN 'italy' ELSE g.region_code END
  AND canonical.region_code<>g.region_code;

UPDATE public.dish_regional_affinities SET region_code=CASE region_code
  WHEN 'in_rajasthan' THEN 'rajasthan' WHEN 'in_punjab' THEN 'punjab'
  WHEN 'in_maharashtra' THEN 'maharashtra' WHEN 'in_gujarat' THEN 'gujarat'
  WHEN 'in_kerala' THEN 'kerala' WHEN 'in_karnataka' THEN 'karnataka'
  WHEN 'in_tamil_nadu' THEN 'tamil_nadu' WHEN 'in_west_bengal' THEN 'west_bengal'
  WHEN 'in_uttar_pradesh' THEN 'uttar_pradesh' WHEN 'in_north_india' THEN 'north_india'
  WHEN 'in_south_india' THEN 'south_india' WHEN 'in_east_india' THEN 'east_india'
  WHEN 'in_west_india' THEN 'west_india' WHEN 'it' THEN 'italy' ELSE region_code END
WHERE source_name='groq';

COMMENT ON FUNCTION public.guard_ai_dish_synonym() IS
  'Cancels deterministic AI alias errors without creating a human review queue.';
