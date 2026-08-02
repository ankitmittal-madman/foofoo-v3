-- Rollback: 044_recommendation_events_decision_trace.sql

ALTER TABLE public.recommendation_events
  DROP COLUMN decision_trace;
