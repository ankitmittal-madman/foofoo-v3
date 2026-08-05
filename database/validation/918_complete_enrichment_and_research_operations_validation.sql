DO $$ BEGIN
  IF to_regprocedure('ops.requeue_external_provider(text)') IS NULL THEN RAISE EXCEPTION 'provider requeue missing'; END IF;
  IF to_regprocedure('public.record_external_nutrient_assertion(uuid,text,text,text,numeric,text,uuid,numeric)') IS NULL THEN RAISE EXCEPTION 'external nutrient writer missing'; END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='research' AND table_name='participants' AND column_name='user_id') THEN
    RAISE EXCEPTION 'participant user binding missing';
  END IF;
END $$;
