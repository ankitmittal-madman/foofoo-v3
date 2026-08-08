-- Disable further cohort mutation while preserving every before/after and approval record.
-- Use ops.rollback_direct_meal_slot_mapping_policy first when dish facts themselves must be
-- restored. This schema rollback deliberately retains the service-only ledger for audit.

REVOKE EXECUTE ON FUNCTION ops.apply_direct_meal_slot_mapping_policy(
  text, integer, integer, integer, text, text, text, text, text, text, text
) FROM service_role;
REVOKE EXECUTE ON FUNCTION ops.rollback_direct_meal_slot_mapping_policy(
  text, integer, text, text, text, text
) FROM service_role;
DROP FUNCTION IF EXISTS ops.apply_direct_meal_slot_mapping_policy(
  text, integer, integer, integer, text, text, text, text, text, text, text
);
DROP FUNCTION IF EXISTS ops.rollback_direct_meal_slot_mapping_policy(
  text, integer, text, text, text, text
);
