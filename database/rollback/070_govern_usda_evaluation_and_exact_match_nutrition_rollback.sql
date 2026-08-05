DROP FUNCTION IF EXISTS ops.finalize_external_provider_evaluation(uuid);
DROP FUNCTION IF EXISTS ops.create_external_provider_evaluation(text,text,uuid[]);
DROP TABLE IF EXISTS ops.external_provider_evaluation_items;
DROP TABLE IF EXISTS ops.external_provider_evaluation_runs;

-- Deliberately do not recreate non-exact provisional nutrition deleted by migration 070. Those
-- assertions pointed at a different food and are unsafe to restore even during schema rollback.
