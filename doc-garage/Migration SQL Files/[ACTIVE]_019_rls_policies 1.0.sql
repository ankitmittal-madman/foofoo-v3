-- Migration: 019_rls_policies.sql
-- Implements: DOC-P3-04 v1.3, all RLS ENABLE/CREATE POLICY statements across §03.1-03.18,
--   §03.25, §03.27's note on re_engine lockdown (already handled in file 001, not repeated here)
-- Logical functions: every LF-number that reads/writes a public-schema personal-data table
--   (effectively the entire LF-A through LF-M range, indirectly, via the access boundary)
-- Governance refs: DOC-P3-05 Part (a) Phase 7 (prerequisite: every public table file —
--   005,006,007 n/a (re_engine, no RLS needed),008,009,011,012,015,016 n/a (re_engine),018);
--   Phase 8.4 (consolidation rationale); this file's position LAST among structural files is
--   itself a validation step per Part (a)'s own stated reasoning
-- CDM entities: all Aggregates with client-facing tables (Household, Meal Plan, Interaction
--   History's public-facing portion)
-- CDM invariants enforced: none new — RLS implements the access-boundary half of CDM Aggregate
--   ownership; it does not introduce new business rules

ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
CREATE POLICY profiles_select_own ON public.profiles FOR SELECT USING (auth.uid() = id);
CREATE POLICY profiles_update_own ON public.profiles FOR UPDATE USING (auth.uid() = id);

ALTER TABLE public.household_members ENABLE ROW LEVEL SECURITY;
CREATE POLICY hm_all_own ON public.household_members FOR ALL USING (auth.uid() = profile_id);

ALTER TABLE public.onboarding_sessions ENABLE ROW LEVEL SECURITY;
CREATE POLICY ob_sessions_own ON public.onboarding_sessions FOR SELECT USING (auth.uid() = profile_id);

ALTER TABLE public.consent_records ENABLE ROW LEVEL SECURITY;
CREATE POLICY consent_select_own ON public.consent_records FOR SELECT USING (auth.uid() = profile_id);

ALTER TABLE public.ingredients ENABLE ROW LEVEL SECURITY;
CREATE POLICY ingredients_public_read ON public.ingredients FOR SELECT USING (true);

ALTER TABLE public.dishes ENABLE ROW LEVEL SECURITY;
CREATE POLICY dishes_public_read ON public.dishes FOR SELECT USING (true);

ALTER TABLE public.dish_ingredients ENABLE ROW LEVEL SECURITY;
CREATE POLICY di_public_read ON public.dish_ingredients FOR SELECT USING (true);

ALTER TABLE public.tags ENABLE ROW LEVEL SECURITY;
CREATE POLICY tags_public_read ON public.tags FOR SELECT USING (true);

ALTER TABLE public.dish_tags ENABLE ROW LEVEL SECURITY;
CREATE POLICY dish_tags_public_read ON public.dish_tags FOR SELECT USING (true);

ALTER TABLE public.dish_combos ENABLE ROW LEVEL SECURITY;
CREATE POLICY combos_public_read ON public.dish_combos FOR SELECT USING (true);

ALTER TABLE public.dish_combo_items ENABLE ROW LEVEL SECURITY;
CREATE POLICY combo_items_public_read ON public.dish_combo_items FOR SELECT USING (true);

ALTER TABLE public.meal_classes ENABLE ROW LEVEL SECURITY;
CREATE POLICY meal_classes_public_read ON public.meal_classes FOR SELECT USING (true);

ALTER TABLE public.week_plans ENABLE ROW LEVEL SECURITY;
CREATE POLICY week_plans_select_own ON public.week_plans FOR SELECT USING (auth.uid() = profile_id);
CREATE POLICY week_plans_update_own ON public.week_plans FOR UPDATE USING (auth.uid() = profile_id);

ALTER TABLE public.plan_slots ENABLE ROW LEVEL SECURITY;
CREATE POLICY plan_slots_select_own ON public.plan_slots FOR SELECT USING (
  EXISTS (SELECT 1 FROM public.week_plans wp WHERE wp.id = week_plan_id AND wp.profile_id = auth.uid())
);
CREATE POLICY plan_slots_update_own ON public.plan_slots FOR UPDATE USING (
  EXISTS (SELECT 1 FROM public.week_plans wp WHERE wp.id = week_plan_id AND wp.profile_id = auth.uid())
);

ALTER TABLE public.addon_slots ENABLE ROW LEVEL SECURITY;
CREATE POLICY addon_slots_select_own ON public.addon_slots FOR SELECT USING (
  EXISTS (SELECT 1 FROM public.plan_slots ps JOIN public.week_plans wp ON wp.id = ps.week_plan_id
          WHERE ps.id = plan_slot_id AND wp.profile_id = auth.uid())
);

ALTER TABLE public.interaction_events ENABLE ROW LEVEL SECURITY;
CREATE POLICY ie_insert_own ON public.interaction_events FOR INSERT WITH CHECK (auth.uid() = profile_id);
CREATE POLICY ie_select_own ON public.interaction_events FOR SELECT USING (auth.uid() = profile_id);

ALTER TABLE public.suggestion_logs ENABLE ROW LEVEL SECURITY;
CREATE POLICY sl_select_own ON public.suggestion_logs FOR SELECT USING (auth.uid() = profile_id);

ALTER TABLE public.context_log ENABLE ROW LEVEL SECURITY;
CREATE POLICY context_log_select_own ON public.context_log FOR SELECT USING (auth.uid() = profile_id);

ALTER TABLE public.weather_cache ENABLE ROW LEVEL SECURITY;
CREATE POLICY weather_cache_public_read ON public.weather_cache FOR SELECT USING (true);

-- audit_log, derivation_conflicts, coverage_gap_log, safety_gate_log, push_notification_logs,
-- feature_flags, etl_job_runs: per DOC-P3-04 §03.19-03.25, these are internal-only tables with
-- NO client SELECT policy — they are read via privileged service-role access only. RLS is
-- intentionally NOT enabled on these per P3-04's own text ("No RLS SELECT policy for client
-- roles — internal-only table"), which itself means leaving RLS disabled is correct, not an
-- omission. Stated explicitly here so this absence is never mistaken for an oversight.
