DO $$
BEGIN
  IF to_regprocedure(
    're_engine.deferred_meal_slot_shifted_field_report(text,text,text,text,integer,integer,integer)'
  ) IS NULL THEN
    RAISE EXCEPTION 'deferred shifted-field audit function is missing';
  END IF;
  IF has_function_privilege(
       'anon',
       're_engine.deferred_meal_slot_shifted_field_report(text,text,text,text,integer,integer,integer)',
       'EXECUTE'
     ) OR has_function_privilege(
       'authenticated',
       're_engine.deferred_meal_slot_shifted_field_report(text,text,text,text,integer,integer,integer)',
       'EXECUTE'
     ) OR NOT has_function_privilege(
       'service_role',
       're_engine.deferred_meal_slot_shifted_field_report(text,text,text,text,integer,integer,integer)',
       'EXECUTE'
     ) THEN
    RAISE EXCEPTION 'deferred shifted-field report must remain service-only';
  END IF;
END $$;
