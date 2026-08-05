-- Rollback for migration 055. This is intentionally explicit because it destroys any data written
-- through the new episode/household surfaces. Take a backup and stop new-contract writers first.

DELETE FROM public.feedback_events WHERE event_type IN (
  'make_this','too_much_work','missing_ingredient','member_objection','cooked','ordered',
  'replaced','completed','regretted'
);
ALTER TABLE public.feedback_events DROP CONSTRAINT IF EXISTS feedback_events_event_type_check;
ALTER TABLE public.feedback_events ADD CONSTRAINT feedback_events_event_type_check CHECK (
  event_type IN ('accept','edit','swap','like','dislike','shown_not_tapped','never','not_today','lock','unlock','add_to_date')
);

DROP POLICY IF EXISTS outcomes_select_member ON public.outcome_events;
DROP POLICY IF EXISTS slate_items_select_member ON public.slate_items;
DROP POLICY IF EXISTS slates_select_member ON public.slates;
DROP POLICY IF EXISTS leftovers_select_member ON public.leftover_lots;
DROP POLICY IF EXISTS pantry_select_member ON public.pantry_beliefs;
DROP POLICY IF EXISTS invites_select_member ON public.household_invites;
DROP POLICY IF EXISTS memberships_select_self ON public.household_memberships;
DROP POLICY IF EXISTS households_select_member ON public.households;

ALTER TABLE public.interaction_events DROP COLUMN IF EXISTS consent_basis;
ALTER TABLE public.interaction_events DROP COLUMN IF EXISTS properties;
ALTER TABLE public.interaction_events DROP COLUMN IF EXISTS schema_version;
ALTER TABLE public.interaction_events DROP COLUMN IF EXISTS received_at;
ALTER TABLE public.interaction_events DROP COLUMN IF EXISTS surface;
ALTER TABLE public.interaction_events DROP COLUMN IF EXISTS event_name;
ALTER TABLE public.interaction_events DROP COLUMN IF EXISTS slate_id;
ALTER TABLE public.interaction_events DROP COLUMN IF EXISTS member_id;
ALTER TABLE public.interaction_events DROP COLUMN IF EXISTS household_id;
ALTER TABLE public.plan_slots DROP COLUMN IF EXISTS selected_episode_hash;
ALTER TABLE public.plan_slots DROP COLUMN IF EXISTS selected_episode_id;

DROP TABLE IF EXISTS ops.safety_gate_log;
DROP TABLE IF EXISTS ops.coverage_gap_log;
DROP TABLE IF EXISTS ops.ai_generation_runs;
DROP TABLE IF EXISTS ml.experiment_assignments;
DROP TABLE IF EXISTS ml.model_registry;
DROP TABLE IF EXISTS ml.feature_definitions;
DROP TABLE IF EXISTS re_engine.member_fairness_state;
DROP TABLE IF EXISTS re_engine.household_cadence_state;
DROP TABLE IF EXISTS re_engine.intent_state;
DROP TABLE IF EXISTS public.outcome_events;
DROP TABLE IF EXISTS public.slate_items;
DROP TABLE IF EXISTS public.slates;
DROP TABLE IF EXISTS public.leftover_lots;
DROP TABLE IF EXISTS public.pantry_beliefs;
DROP TABLE IF EXISTS food.episode_cadence;
DROP TABLE IF EXISTS food.episode_workload_features;
DROP TABLE IF EXISTS food.meal_episode_components;
DROP TABLE IF EXISTS food.meal_episodes;
DROP TABLE IF EXISTS food.recipe_ingredients;
DROP TABLE IF EXISTS food.recipe_steps;
DROP TABLE IF EXISTS food.recipes;
DROP TABLE IF EXISTS food.grammar_component_rules;
DROP TABLE IF EXISTS food.plate_grammars;
DROP TABLE IF EXISTS ops.data_sources;

ALTER TABLE public.household_context DROP COLUMN IF EXISTS household_id;
ALTER TABLE public.product_events DROP COLUMN IF EXISTS household_id;
ALTER TABLE public.feedback_events DROP COLUMN IF EXISTS household_id;
ALTER TABLE public.recommendation_events DROP COLUMN IF EXISTS household_id;
ALTER TABLE public.week_plans DROP COLUMN IF EXISTS household_id;
ALTER TABLE public.household_members DROP COLUMN IF EXISTS effective_to;
ALTER TABLE public.household_members DROP COLUMN IF EXISTS effective_from;
ALTER TABLE public.household_members DROP COLUMN IF EXISTS member_role_code;
ALTER TABLE public.household_members DROP COLUMN IF EXISTS display_name;
ALTER TABLE public.household_members DROP COLUMN IF EXISTS user_id;
ALTER TABLE public.household_members DROP COLUMN IF EXISTS household_id;

DROP TABLE IF EXISTS public.household_invites;
DROP TABLE IF EXISTS public.household_memberships;
DROP TABLE IF EXISTS public.households;

DROP SCHEMA IF EXISTS ml;
DROP SCHEMA IF EXISTS re_engine;
DROP SCHEMA IF EXISTS food;
DROP SCHEMA IF EXISTS ops;
