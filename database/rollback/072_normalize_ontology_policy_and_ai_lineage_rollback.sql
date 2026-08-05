DROP TRIGGER IF EXISTS dish_taxonomy_assertions_groq_field_policy ON public.dish_taxonomy_assertions;
DROP FUNCTION IF EXISTS public.enforce_groq_ontology_field_policy();
DROP TRIGGER IF EXISTS ontology_review_decisions_immutable ON food.ontology_review_decisions;
DROP FUNCTION IF EXISTS food.prevent_ontology_review_decision_mutation();
DROP TABLE IF EXISTS food.ontology_review_decisions;
DROP TABLE IF EXISTS food.ontology_field_policies;
DROP TABLE IF EXISTS ops.assertion_ai_runs;
DROP TABLE IF EXISTS ops.assertion_sources;
DROP TABLE IF EXISTS ops.ai_generation_run_inputs;
