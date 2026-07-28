-- Rollback: 038_household_answers_context_and_events_rollback.sql
-- Reverses 038_household_answers_context_and_events.sql exactly.
--
-- Order matters: feedback_events references recommendation_events, so it drops first. The
-- household_members.age column is dropped last because it is an ALTER on a pre-existing table
-- (006/033) that this migration only added to — the table itself must survive this rollback.
--
-- DATA LOSS WARNING: dropping recommendation_events / feedback_events discards served-recommendation
-- and behavioural history, which cannot be reconstructed (the RE is stateless and keeps none of it).
-- Only run this against an environment where that history is known to be disposable.

DROP TABLE IF EXISTS public.feedback_events;
DROP TABLE IF EXISTS public.recommendation_events;
DROP TABLE IF EXISTS public.household_context;
DROP TABLE IF EXISTS public.household_answers;

ALTER TABLE public.household_members
  DROP COLUMN IF EXISTS age;
