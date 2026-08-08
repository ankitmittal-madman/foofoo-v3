-- Rollback for 129_parameterize_nutrient_assertion_source.sql

DROP FUNCTION IF EXISTS public.record_external_nutrient_assertion(
  uuid, text, text, text, numeric, text, uuid, numeric, text
);

CREATE OR REPLACE FUNCTION public.record_external_nutrient_assertion(
  p_dish_id uuid,p_nutrient_code text,p_display_name text,p_unit_code text,p_expected_value numeric,
  p_serving_basis text,p_source_record_id uuid,p_confidence numeric
)
RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER SET search_path=public,food,pg_temp AS $$
DECLARE v_nutrient_id uuid; v_assertion_id uuid;
BEGIN
  INSERT INTO food.nutrients(nutrient_code,display_name,unit_code,source_name)
  VALUES(p_nutrient_code,p_display_name,p_unit_code,'usda_fdc')
  ON CONFLICT(nutrient_code) DO UPDATE SET display_name=excluded.display_name
  RETURNING id INTO v_nutrient_id;
  INSERT INTO food.nutrient_assertions(dish_id,nutrient_id,expected_value,serving_basis,method_code,
    source_name,source_record_id,confidence,review_status)
  VALUES(p_dish_id,v_nutrient_id,p_expected_value,p_serving_basis,'usda_search_top_match','usda_fdc',
    p_source_record_id,p_confidence,'provisional') RETURNING id INTO v_assertion_id;
  RETURN v_assertion_id;
END $$;
REVOKE ALL ON FUNCTION public.record_external_nutrient_assertion(uuid,text,text,text,numeric,text,uuid,numeric) FROM PUBLIC,anon,authenticated;
GRANT EXECUTE ON FUNCTION public.record_external_nutrient_assertion(uuid,text,text,text,numeric,text,uuid,numeric) TO service_role;
