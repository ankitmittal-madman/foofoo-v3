-- Disable future contextual cohort mutation while preserving approval, before/after and rollback
-- evidence. Use ops.rollback_contextual_meal_slot_set_policy first when applied dish facts must be
-- restored. The private ledger and extended lifecycle remain because removing either would erase
-- or invalidate audit history.

REVOKE EXECUTE ON FUNCTION ops.apply_contextual_meal_slot_set_policy(
  text, integer, integer, integer, text, text, text, text, text, text, text
) FROM service_role;
REVOKE EXECUTE ON FUNCTION ops.rollback_contextual_meal_slot_set_policy(
  text, integer, text, text, text, text
) FROM service_role;
DROP FUNCTION IF EXISTS ops.apply_contextual_meal_slot_set_policy(
  text, integer, integer, integer, text, text, text, text, text, text, text
);
DROP FUNCTION IF EXISTS ops.rollback_contextual_meal_slot_set_policy(
  text, integer, text, text, text, text
);

COMMENT ON TABLE ops.dish_meal_slot_set_applications IS
  'Retained contextual slot-set application and rollback history; further cohort mutation disabled by rollback 120.';
