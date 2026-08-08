-- record_external_nutrient_assertion (migration 064) hardcodes source_name='usda_fdc' on both the
-- food.nutrients upsert and the food.nutrient_assertions insert. Migration 128 added IFCT as a
-- second nutrient source (store.ts promoteExternalEvidence); calling the existing function
-- unmodified for an IFCT match would mislabel its provenance as USDA -- a real correctness bug,
-- not a cosmetic one, since source_name is what downstream review/audit trusts for evidence
-- lineage. Fix: add p_source_name, defaulted to 'usda_fdc' so every existing call site (store.ts's
-- normalizeUsda path) keeps its current behavior unchanged.
--
-- Same reason as migration 127's DROP FUNCTION: adding a defaulted trailing parameter to an
-- existing signature makes an 8-positional-arg call ambiguous between the old and new function,
-- so the old one must be dropped first rather than left alongside via CREATE OR REPLACE.

DROP FUNCTION IF EXISTS public.record_external_nutrient_assertion(
  uuid, text, text, text, numeric, text, uuid, numeric
);

CREATE OR REPLACE FUNCTION public.record_external_nutrient_assertion(
  p_dish_id uuid, p_nutrient_code text, p_display_name text, p_unit_code text,
  p_expected_value numeric, p_serving_basis text, p_source_record_id uuid, p_confidence numeric,
  p_source_name text DEFAULT 'usda_fdc'
)
RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER SET search_path=public,food,pg_temp AS $$
DECLARE v_nutrient_id uuid; v_assertion_id uuid;
BEGIN
  INSERT INTO food.nutrients(nutrient_code,display_name,unit_code,source_name)
  VALUES(p_nutrient_code,p_display_name,p_unit_code,p_source_name)
  ON CONFLICT(nutrient_code) DO UPDATE SET display_name=excluded.display_name
  RETURNING id INTO v_nutrient_id;
  INSERT INTO food.nutrient_assertions(dish_id,nutrient_id,expected_value,serving_basis,method_code,
    source_name,source_record_id,confidence,review_status)
  VALUES(p_dish_id,v_nutrient_id,p_expected_value,p_serving_basis,
    CASE WHEN p_source_name = 'ifct' THEN 'ifct_trigram_top_match' ELSE 'usda_search_top_match' END,
    p_source_name,p_source_record_id,p_confidence,'provisional') RETURNING id INTO v_assertion_id;
  RETURN v_assertion_id;
END $$;

COMMENT ON FUNCTION public.record_external_nutrient_assertion(uuid,text,text,text,numeric,text,uuid,numeric,text) IS
  'Records one nutrient assertion from an external source. p_source_name defaults to usda_fdc for '
  'backward compatibility with pre-migration-129 call sites; pass ifct explicitly for IFCT matches '
  '(migration 128) so provenance is not mislabeled.';

REVOKE ALL ON FUNCTION public.record_external_nutrient_assertion(uuid,text,text,text,numeric,text,uuid,numeric,text) FROM PUBLIC,anon,authenticated;
GRANT EXECUTE ON FUNCTION public.record_external_nutrient_assertion(uuid,text,text,text,numeric,text,uuid,numeric,text) TO service_role;
