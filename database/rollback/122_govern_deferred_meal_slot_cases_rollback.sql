-- Disable further final-cohort generation while retaining private cases and immutable evidence.
-- Existing review history must survive rollback; this does not touch public.dishes or serving.

REVOKE ALL ON FUNCTION ops.generate_deferred_meal_slot_cases(
  text,text,text,text,text,integer,integer,integer
) FROM PUBLIC, anon, authenticated, service_role;

DROP FUNCTION IF EXISTS ops.generate_deferred_meal_slot_cases(
  text,text,text,text,text,integer,integer,integer
);

COMMENT ON TABLE ops.deferred_meal_slot_cases IS
  'Retained private deferred meal-slot case ledger; generation disabled by rollback 122.';
