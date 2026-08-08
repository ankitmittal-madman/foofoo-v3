-- Remove only the read-only identity publication boundary; no catalogue or user data changes.

REVOKE EXECUTE ON FUNCTION re_engine.catalogue_identity_rows(uuid, integer) FROM service_role;
REVOKE EXECUTE ON FUNCTION re_engine.catalogue_identity_coverage() FROM service_role;
DROP FUNCTION IF EXISTS re_engine.catalogue_identity_rows(uuid, integer);
DROP FUNCTION IF EXISTS re_engine.catalogue_identity_coverage();
