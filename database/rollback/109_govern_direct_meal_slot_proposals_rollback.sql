-- Preserve any generated proposal/evidence rows for audit and recovery. Disable further writes and
-- remove only the generator surface; retained evidence validation still depends on the exact-course
-- helper. Installation failure itself rolls back atomically.
REVOKE INSERT, UPDATE ON ops.dish_meal_slot_proposals FROM service_role;
REVOKE INSERT ON ops.dish_meal_slot_proposal_evidence FROM service_role;
REVOKE EXECUTE ON FUNCTION re_engine.direct_slot_from_import_course(text)
  FROM service_role;
REVOKE EXECUTE ON FUNCTION re_engine.direct_meal_slot_proposal_candidates()
  FROM service_role;
DROP FUNCTION IF EXISTS ops.generate_direct_meal_slot_proposals(text, integer);
DROP FUNCTION IF EXISTS re_engine.direct_meal_slot_proposal_candidates();
