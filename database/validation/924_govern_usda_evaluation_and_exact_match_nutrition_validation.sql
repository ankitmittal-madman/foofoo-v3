DO $$ BEGIN
  IF to_regclass('ops.external_provider_evaluation_runs') IS NULL OR
     to_regclass('ops.external_provider_evaluation_items') IS NULL THEN
    RAISE EXCEPTION 'external provider evaluation ledger missing';
  END IF;
  IF to_regprocedure('ops.create_external_provider_evaluation(text,text,uuid[])') IS NULL OR
     to_regprocedure('ops.finalize_external_provider_evaluation(uuid)') IS NULL THEN
    RAISE EXCEPTION 'external provider evaluation functions missing';
  END IF;
  IF EXISTS (
    SELECT 1 FROM food.nutrient_assertions a JOIN public.food_source_records r ON r.id=a.source_record_id
    WHERE r.provider='usda_fdc' AND a.review_status='provisional'
      AND lower(regexp_replace(btrim(r.query_text),'\s+',' ','g'))<>
          lower(regexp_replace(btrim(r.source_payload->'foods'->0->>'description'),'\s+',' ','g'))
  ) THEN RAISE EXCEPTION 'non-exact USDA nutrition remains publishable'; END IF;
  IF has_function_privilege('authenticated','ops.create_external_provider_evaluation(text,text,uuid[])','EXECUTE') THEN
    RAISE EXCEPTION 'authenticated role can create provider evaluations'; END IF;
END $$;
