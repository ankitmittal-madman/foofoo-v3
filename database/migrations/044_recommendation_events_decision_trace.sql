-- Migration: 044_recommendation_events_decision_trace.sql
-- WP-12 (per-user recommendation explainability): adds public.recommendation_events.decision_trace
-- so every served recommendation carries a durable, queryable record of how the catalogue narrowed
-- down to the plates actually shown — the funnel of dish counts through each hard filter
-- (diet/jain/allergen/weaning/fasting), the winning plates ranked, and the top near-miss
-- alternatives with a concrete reason each lost. Previously this reasoning existed only as Python
-- `logging` output in ghar_re_core/decision_log.py, which is a no-op unless a handler is attached
-- — confirmed this session that the deployed ghar_re_service never attaches one, so it was
-- completely inert in production. This migration is the DB half of making it real: the RE now
-- returns the trace in its response when asked (include_decision_trace=true, contract-additive,
-- see contracts/ghar-re-v1.schema.json), and recommendations/events.ts stores it as-is.
--
-- Nullable, no default: absent on fallback/timeout/error outcomes (there was no RE decision to
-- trace) and on any recommendation_events row written before this column existed.

ALTER TABLE public.recommendation_events
  ADD COLUMN decision_trace jsonb;
