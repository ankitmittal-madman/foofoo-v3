-- Rollback: 027_routing_rules_show_question_key_nullable_rollback.sql
-- Reverses: 027_routing_rules_show_question_key_nullable.sql
-- WARNING (parallel to the 025/026 rollback precedent): reversing this restores the ORIGINAL
--   NOT NULL constraint, which will again make "skip rule" rows (show_question_key IS NULL)
--   unrepresentable. If this rollback is ever run AFTER the WP-4B seed load has completed,
--   it will fail against any already-loaded skip-rule rows (the MC_SOLO/MC_COUPLE/MC_PG_HOSTEL/
--   diet_type=jain rows) — this is expected and correct: rolling back a schema-integrity fix
--   while relying data exists should fail loudly, not silently corrupt or drop rows. On the
--   currently-unseeded table (0 rows in re_routing_rules as of this migration's authoring),
--   this reverses cleanly.

ALTER TABLE re_engine.re_routing_rules
  DROP CONSTRAINT re_routing_rules_action_check;

ALTER TABLE re_engine.re_routing_rules
  ALTER COLUMN show_question_key SET NOT NULL;
