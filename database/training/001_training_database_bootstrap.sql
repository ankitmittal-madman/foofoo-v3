-- Minimal private-schema bootstrap for a dedicated synthetic-training Supabase project.
-- Production tenant, catalogue, planning, auth and event structures are intentionally absent.

CREATE SCHEMA IF NOT EXISTS ml;
CREATE SCHEMA IF NOT EXISTS research;

REVOKE ALL ON SCHEMA ml, research FROM PUBLIC, anon, authenticated;
GRANT USAGE ON SCHEMA ml, research TO service_role;

COMMENT ON SCHEMA ml IS
  'Private model lifecycle and synthetic-training control state; never a client API surface.';
COMMENT ON SCHEMA research IS
  'Private synthetic and research evidence; never production identity or behavioral truth.';
