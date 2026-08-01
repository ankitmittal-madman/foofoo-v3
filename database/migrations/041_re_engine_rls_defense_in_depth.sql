-- Migration: 041_re_engine_rls_defense_in_depth.sql
-- Responds to the live Supabase advisor's rls_disabled CRITICAL finding on all 34 re_engine.*
-- tables. Verified live before writing this: anon/authenticated hold no SCHEMA USAGE on
-- re_engine (migration 001's original REVOKE ALL is intact), so these tables are not reachable
-- via PostgREST today regardless of RLS state. Enabling RLS is therefore pure defense-in-depth —
-- service_role bypasses RLS unconditionally, so nothing the app does changes — and closes the
-- residual risk of a future accidental GRANT USAGE on the schema reopening all 34 tables at once.

ALTER TABLE re_engine.dish_features ENABLE ROW LEVEL SECURITY;
ALTER TABLE re_engine.never_list ENABLE ROW LEVEL SECURITY;
ALTER TABLE re_engine.not_today_suppression ENABLE ROW LEVEL SECURITY;
ALTER TABLE re_engine.re_addon_classes ENABLE ROW LEVEL SECURITY;
ALTER TABLE re_engine.re_addon_dish_options ENABLE ROW LEVEL SECURITY;
ALTER TABLE re_engine.re_city_migration_overlays ENABLE ROW LEVEL SECURITY;
ALTER TABLE re_engine.re_city_overlay_config ENABLE ROW LEVEL SECURITY;
ALTER TABLE re_engine.re_class_affinity_config ENABLE ROW LEVEL SECURITY;
ALTER TABLE re_engine.re_class_dish_options ENABLE ROW LEVEL SECURITY;
ALTER TABLE re_engine.re_cohort_class_priors ENABLE ROW LEVEL SECURITY;
ALTER TABLE re_engine.re_cohorts ENABLE ROW LEVEL SECURITY;
ALTER TABLE re_engine.re_confidence_config ENABLE ROW LEVEL SECURITY;
ALTER TABLE re_engine.re_context_multipliers ENABLE ROW LEVEL SECURITY;
ALTER TABLE re_engine.re_dish_bandit_state ENABLE ROW LEVEL SECURITY;
ALTER TABLE re_engine.re_dish_regional_affinity ENABLE ROW LEVEL SECURITY;
ALTER TABLE re_engine.re_engine_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE re_engine.re_event_weights ENABLE ROW LEVEL SECURITY;
ALTER TABLE re_engine.re_festival_calendar ENABLE ROW LEVEL SECURITY;
ALTER TABLE re_engine.re_household_addon_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE re_engine.re_main_cohorts ENABLE ROW LEVEL SECURITY;
ALTER TABLE re_engine.re_meal_class_overlap_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE re_engine.re_meal_classes ENABLE ROW LEVEL SECURITY;
ALTER TABLE re_engine.re_nonveg_logic ENABLE ROW LEVEL SECURITY;
ALTER TABLE re_engine.re_persona_assignment_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE re_engine.re_personas ENABLE ROW LEVEL SECURITY;
ALTER TABLE re_engine.re_routing_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE re_engine.re_scoring_config ENABLE ROW LEVEL SECURITY;
ALTER TABLE re_engine.re_states ENABLE ROW LEVEL SECURITY;
ALTER TABLE re_engine.re_subcohorts ENABLE ROW LEVEL SECURITY;
ALTER TABLE re_engine.re_variety_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE re_engine.re_weekly_class_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE re_engine.re_weight_ladder_config ENABLE ROW LEVEL SECURITY;
ALTER TABLE re_engine.user_re_state ENABLE ROW LEVEL SECURITY;
ALTER TABLE re_engine.user_taste_vectors ENABLE ROW LEVEL SECURITY;
ALTER TABLE re_engine.variety_window_state ENABLE ROW LEVEL SECURITY;

-- rls_auto_enable() is an event-trigger function (RETURNS event_trigger); direct RPC invocation
-- by anon/authenticated serves no purpose (pg_event_trigger_ddl_commands() only works inside an
-- actual event trigger) and only widens the exposed surface flagged by the advisor.
REVOKE EXECUTE ON FUNCTION public.rls_auto_enable() FROM PUBLIC, anon, authenticated;
