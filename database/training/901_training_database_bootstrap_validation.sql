-- Verifies the minimal dedicated training boundary without creating production data surfaces.

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_namespace WHERE nspname = 'ml')
     OR NOT EXISTS (SELECT 1 FROM pg_namespace WHERE nspname = 'research') THEN
    RAISE EXCEPTION 'dedicated training schemas are incomplete';
  END IF;

  IF has_schema_privilege('anon', 'ml', 'USAGE')
     OR has_schema_privilege('authenticated', 'ml', 'USAGE')
     OR has_schema_privilege('anon', 'research', 'USAGE')
     OR has_schema_privilege('authenticated', 'research', 'USAGE') THEN
    RAISE EXCEPTION 'dedicated training schemas are exposed to client roles';
  END IF;
END $$;
