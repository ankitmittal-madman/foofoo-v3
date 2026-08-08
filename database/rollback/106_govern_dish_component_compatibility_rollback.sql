DROP FUNCTION IF EXISTS re_engine.catalogue_serving_role_readiness_report();
DROP TRIGGER IF EXISTS dish_component_proposal_application_guard
  ON ops.dish_component_compatibility_proposals;
DROP FUNCTION IF EXISTS ops.validate_component_proposal_application();
DROP TRIGGER IF EXISTS dish_component_proposal_lifecycle_guard
  ON ops.dish_component_compatibility_proposals;
DROP FUNCTION IF EXISTS ops.protect_component_proposal_lifecycle();
DROP TRIGGER IF EXISTS dish_component_proposal_grammar_guard
  ON ops.dish_component_compatibility_proposals;
DROP TRIGGER IF EXISTS dish_component_compatibility_immutability_guard
  ON food.dish_component_compatibility;
DROP FUNCTION IF EXISTS food.protect_dish_component_compatibility();
DROP TRIGGER IF EXISTS dish_component_compatibility_grammar_guard
  ON food.dish_component_compatibility;
DROP TABLE IF EXISTS ops.dish_component_compatibility_proposals;
DROP TABLE IF EXISTS food.dish_component_compatibility;
DROP FUNCTION IF EXISTS food.validate_dish_component_grammar();
DROP FUNCTION IF EXISTS re_engine.canonical_meal_slot(text);
