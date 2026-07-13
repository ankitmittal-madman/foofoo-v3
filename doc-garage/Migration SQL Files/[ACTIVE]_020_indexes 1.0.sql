-- Migration: 020_indexes.sql
-- Implements: DOC-P3-04 v1.3, all 37 indexes across §03 (per-table) and §05/§06 (justification)
-- Logical functions: every hot-path LF-number named in DOC-P3-04 §05's Read/Write Optimisation
--   table (LF-D01, D03, D06, E02, F01, H01-H04, B02, L02, etc. — see inline comments per index)
-- Governance refs: DOC-P3-05 Part (a) Phase 7 (prerequisite: all of 002-019); Phase 8.3
--   (consolidation rationale — same reasoning as RLS in file 019)
-- CDM entities: n/a (indexes are access-pattern objects, not domain entities)
-- CDM invariants enforced: none new

-- profiles
CREATE INDEX idx_profiles_last_active ON public.profiles (last_active_at) WHERE deleted_at IS NULL;
CREATE INDEX idx_profiles_home_state ON public.profiles (home_state);

-- household_members / onboarding_sessions / consent_records
CREATE INDEX idx_household_members_profile ON public.household_members (profile_id) WHERE is_active = true;
CREATE INDEX idx_onboarding_sessions_profile ON public.onboarding_sessions (profile_id, screen_id);
CREATE INDEX idx_consent_profile_type ON public.consent_records (profile_id, consent_type, granted_at DESC);

-- ingredients — supports LF-D03 allergen filter join
CREATE INDEX idx_ingredients_allergen ON public.ingredients (allergen_flags);

-- dishes — supports LF-D01-D07 candidate filtering
CREATE INDEX idx_dishes_active ON public.dishes (is_active) WHERE is_active = true;
CREATE INDEX idx_dishes_diet_type ON public.dishes (diet_type);
CREATE INDEX idx_dishes_is_jain ON public.dishes (is_jain) WHERE is_jain = true;
CREATE INDEX idx_dishes_allergen ON public.dishes (allergen_flags);
CREATE INDEX idx_dishes_meal_occasion ON public.dishes USING gin (meal_occasion);
CREATE INDEX idx_dishes_parent ON public.dishes (parent_dish_id) WHERE parent_dish_id IS NOT NULL;

-- dish_ingredients / dish_tags — supports LF-D03 safety-critical join and LF-K02 reverse lookup
CREATE INDEX idx_dish_ingredients_ingredient ON public.dish_ingredients (ingredient_id);
CREATE INDEX idx_dish_tags_tag ON public.dish_tags (tag_id);

-- plan_slots — supports LF-L02 refreshUnlockedSlots, the highest-frequency write-triggering read
CREATE INDEX idx_plan_slots_week_plan ON public.plan_slots (week_plan_id);
CREATE INDEX idx_plan_slots_locked ON public.plan_slots (week_plan_id) WHERE is_locked = false;

-- addon_slots
CREATE INDEX idx_addon_slots_plan_slot ON public.addon_slots (plan_slot_id);

-- week_plans
CREATE INDEX idx_week_plans_profile_date ON public.week_plans (profile_id, week_start_date DESC);

-- interaction_events — supports LF-J01's 15-minute batch processor
CREATE INDEX idx_ie_profile_dish ON public.interaction_events (profile_id, dish_id, occurred_at DESC);
CREATE INDEX idx_ie_unsynced ON public.interaction_events (synced_to_re) WHERE synced_to_re = false;

-- suggestion_logs — supports Safety Gates 1-4 and Section 10 auditability
CREATE INDEX idx_sl_profile_dish_date ON public.suggestion_logs (profile_id, dish_id, slot_date);
CREATE INDEX idx_sl_slate ON public.suggestion_logs (slate_id);

-- context_log
CREATE INDEX idx_context_log_slate ON public.context_log (slate_id);

-- re_engine: re_meal_classes — supports Safety Gate 4 (LF-H04), the single most safety-critical
-- lookup in re_engine
CREATE INDEX idx_re_meal_classes_role ON re_engine.re_meal_classes (planning_role);

-- re_engine: re_class_dish_options — supports LF-D01, first query of every recommendation request
CREATE INDEX idx_re_class_dish_class ON re_engine.re_class_dish_options (meal_class_code);

-- re_engine: re_addon_dish_options
CREATE INDEX idx_re_addon_dish_class ON re_engine.re_addon_dish_options (addon_class_code, suitability_rank);

-- re_engine: re_cohorts — supports LF-B02's cohort lookup, exact composite match to its WHERE clause
CREATE INDEX idx_re_cohorts_lookup ON re_engine.re_cohorts (persona_id, state_code, diet_mode);

-- re_engine: re_weekly_class_plans
CREATE INDEX idx_re_weekly_plans_cohort ON re_engine.re_weekly_class_plans (cohort_id);

-- re_engine: user_re_state
CREATE INDEX idx_user_re_state_cold_start ON re_engine.user_re_state (cold_start_mode) WHERE cold_start_mode = true;

-- re_engine: never_list — the single most frequently executed filter in the entire system (LF-D06)
CREATE INDEX idx_never_list_active ON re_engine.never_list (profile_id) WHERE is_active = true;
CREATE INDEX idx_never_list_reactivation ON re_engine.never_list (nevered_at)
  WHERE is_active = true AND (seasonal_reactivation_eligible OR festival_reactivation_eligible);

-- re_engine: not_today_suppression
CREATE INDEX idx_not_today_active ON re_engine.not_today_suppression (profile_id) WHERE is_active = true;

-- tags — explicit unique index per P3-04 §03.8. NOTE (AGR-004, informational only): this index
-- is functionally redundant with the UNIQUE constraint already declared on tags.vector_position
-- in file 002's CREATE TABLE (a UNIQUE column constraint auto-creates its own index in Postgres).
-- P3-04 v1.3 §03.8 states this CREATE UNIQUE INDEX explicitly anyway. Reproduced here verbatim
-- for traceability completeness rather than silently omitted as "already covered" — the
-- redundancy itself is flagged for the architecture owner's awareness, not silently resolved.
CREATE UNIQUE INDEX idx_tags_vector_position ON public.tags (vector_position);

-- audit_log / etl_job_runs — present in P3-04 §03 inline text; added here on direct
-- re-verification against the approved document after an initial count mismatch was caught.
CREATE INDEX idx_audit_log_actor ON public.audit_log (actor_id, occurred_at DESC);
CREATE INDEX idx_etl_job_runs_name ON public.etl_job_runs (job_name, started_at DESC);

-- suggestion_logs — AGR-004 (informational): P3-04 §03.16 names this index "idx_sl_gate_diet"
-- with an explicit caveat in its own text: "in practice this is implemented as a plain composite
-- index" rather than the literal time-relative partial-index syntax shown, since a partial index
-- predicate using now() is not valid in Postgres (the predicate is evaluated once at index
-- creation, not per-query). The index below is that "plain composite" fallback P3-04 itself
-- describes. The exact column order is this migration's interpretation of P3-04's own hedge,
-- not a literal reproduction, and should be confirmed against actual gate-query EXPLAIN output
-- once Part (d)'s gate scripts exist.
CREATE INDEX idx_sl_gate_diet ON public.suggestion_logs (suggested_at, profile_id, dish_id);
