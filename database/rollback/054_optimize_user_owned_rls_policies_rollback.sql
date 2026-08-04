-- Restore the pre-054 policy expressions. Ownership semantics remain identical.

DROP POLICY IF EXISTS profiles_select_own ON public.profiles;
CREATE POLICY profiles_select_own ON public.profiles FOR SELECT USING (auth.uid() = id);
DROP POLICY IF EXISTS profiles_update_own ON public.profiles;
CREATE POLICY profiles_update_own ON public.profiles FOR UPDATE USING (auth.uid() = id);
DROP POLICY IF EXISTS hm_all_own ON public.household_members;
CREATE POLICY hm_all_own ON public.household_members FOR ALL USING (auth.uid() = profile_id);
DROP POLICY IF EXISTS ob_sessions_own ON public.onboarding_sessions;
CREATE POLICY ob_sessions_own ON public.onboarding_sessions FOR SELECT USING (auth.uid() = profile_id);
DROP POLICY IF EXISTS consent_select_own ON public.consent_records;
CREATE POLICY consent_select_own ON public.consent_records FOR SELECT USING (auth.uid() = profile_id);
DROP POLICY IF EXISTS week_plans_select_own ON public.week_plans;
CREATE POLICY week_plans_select_own ON public.week_plans FOR SELECT USING (auth.uid() = profile_id);
DROP POLICY IF EXISTS week_plans_update_own ON public.week_plans;
CREATE POLICY week_plans_update_own ON public.week_plans FOR UPDATE USING (auth.uid() = profile_id);
DROP POLICY IF EXISTS plan_slots_select_own ON public.plan_slots;
CREATE POLICY plan_slots_select_own ON public.plan_slots FOR SELECT USING (
  EXISTS (SELECT 1 FROM public.week_plans wp WHERE wp.id = week_plan_id AND wp.profile_id = auth.uid())
);
DROP POLICY IF EXISTS plan_slots_update_own ON public.plan_slots;
CREATE POLICY plan_slots_update_own ON public.plan_slots FOR UPDATE USING (
  EXISTS (SELECT 1 FROM public.week_plans wp WHERE wp.id = week_plan_id AND wp.profile_id = auth.uid())
);
DROP POLICY IF EXISTS addon_slots_select_own ON public.addon_slots;
CREATE POLICY addon_slots_select_own ON public.addon_slots FOR SELECT USING (
  EXISTS (SELECT 1 FROM public.plan_slots ps JOIN public.week_plans wp ON wp.id = ps.week_plan_id
          WHERE ps.id = plan_slot_id AND wp.profile_id = auth.uid())
);
DROP POLICY IF EXISTS ie_insert_own ON public.interaction_events;
CREATE POLICY ie_insert_own ON public.interaction_events FOR INSERT WITH CHECK (auth.uid() = profile_id);
DROP POLICY IF EXISTS ie_select_own ON public.interaction_events;
CREATE POLICY ie_select_own ON public.interaction_events FOR SELECT USING (auth.uid() = profile_id);
DROP POLICY IF EXISTS sl_select_own ON public.suggestion_logs;
CREATE POLICY sl_select_own ON public.suggestion_logs FOR SELECT USING (auth.uid() = profile_id);
DROP POLICY IF EXISTS context_log_select_own ON public.context_log;
CREATE POLICY context_log_select_own ON public.context_log FOR SELECT USING (auth.uid() = profile_id);
DROP POLICY IF EXISTS household_answers_all_own ON public.household_answers;
CREATE POLICY household_answers_all_own ON public.household_answers FOR ALL USING (auth.uid() = profile_id);
DROP POLICY IF EXISTS household_context_all_own ON public.household_context;
CREATE POLICY household_context_all_own ON public.household_context FOR ALL USING (auth.uid() = profile_id);
DROP POLICY IF EXISTS rec_events_select_own ON public.recommendation_events;
CREATE POLICY rec_events_select_own ON public.recommendation_events FOR SELECT USING (auth.uid() = profile_id);
DROP POLICY IF EXISTS feedback_events_all_own ON public.feedback_events;
CREATE POLICY feedback_events_all_own ON public.feedback_events FOR ALL USING (auth.uid() = profile_id);
