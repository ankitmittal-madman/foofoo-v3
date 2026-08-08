-- Disable further contextual proposal generation while preserving every proposal and evidence row.
-- Existing pending/review decisions remain auditable and no public dish fact is changed.

REVOKE EXECUTE ON FUNCTION ops.generate_contextual_meal_slot_set_proposals(
  text, integer, integer, text, text, text, text
) FROM service_role;
REVOKE EXECUTE ON FUNCTION re_engine.contextual_meal_slot_set_candidate_evidence()
  FROM service_role;
REVOKE EXECUTE ON FUNCTION re_engine.contextual_slot_set_from_import_course(text)
  FROM service_role;
REVOKE EXECUTE ON FUNCTION re_engine.contextual_course_evidence_category(text)
  FROM service_role;

DROP FUNCTION IF EXISTS ops.generate_contextual_meal_slot_set_proposals(
  text, integer, integer, text, text, text, text
);
DROP FUNCTION IF EXISTS re_engine.contextual_meal_slot_set_candidate_evidence();

COMMENT ON TABLE ops.dish_meal_slot_set_proposals IS
  'Retained contextual multi-slot proposal history; generation disabled by rollback 118.';
