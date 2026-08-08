-- Remove only the read-only aggregate report. No source, proposal, dish or serving data changed.

REVOKE EXECUTE ON FUNCTION re_engine.deferred_meal_slot_shifted_field_report(
  text, text, text, text, integer, integer, integer
) FROM service_role;
DROP FUNCTION IF EXISTS re_engine.deferred_meal_slot_shifted_field_report(
  text, text, text, text, integer, integer, integer
);
