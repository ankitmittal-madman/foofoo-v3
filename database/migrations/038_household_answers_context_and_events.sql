-- Migration: 038_household_answers_context_and_events.sql
-- Implements: Ghar RE v1.0 Phase C.5 — application data ownership. Adds the APPLICATION-side
--   tables the recommendations Edge Function needs to build a real ghar-re-v1 request, replacing
--   the hardcoded stub in supabase/functions/recommendations/compose.ts.
-- Governance refs: RE-DOC-10 §1 (frozen architecture: "Edge Functions own 100% of database access
--   and all user identity"; "RE owns zero DB connections") and §9 (composition flow step 2:
--   "fetch household + raw Q1-Q15 + household_context from Postgres").
--
-- SCHEMA DECISION (the reason this file targets `public` and creates only FOUR tables):
--   These are APPLICATION tables. They deliberately do NOT get a ghar_re-namespaced schema —
--   `ghar_re.*` (034-037) is the GOLDEN-SAMPLE / offline-reference schema for the engine's own
--   fixtures, and `re_engine.*` (001-004) is the retired reference tier. Neither is the live
--   application schema. The live application schema is `public` (005 profiles, 006
--   household_members / onboarding_sessions / consent_records, 008+ content, 011 planning).
--
--   Verified before writing this migration, by reading the migration ledger rather than assuming:
--     * public.profiles (005) IS the household root — it holds primary_cook_name, home_state,
--       current_city, diet_type, religious_pref, allergen_flags, and is what
--       public.household_members.profile_id already references. A separate `households` table is
--       therefore NOT created here: it would fork household identity in two, and every existing
--       public-schema table that scopes data to a household already keys on profile_id.
--     * public.household_members (006, altered by 033) already exists and already carries the
--       condition vocabulary (conditions text[]) the RE needs for weaning/senior detection. It is
--       reused, not duplicated — this file only ADDS the one column it lacks (age, see B below).
--     * public.onboarding_sessions (006) is an append-only LOG of answering events
--       (screen_id, question_key, answer_value, skipped, answered_at) whose live question_key
--       vocabulary (children_ages, elder_members_present, ... per seeds 101/111) is the app's own
--       onboarding vocabulary, NOT the RE's Q1-Q15. It is not the current-state answer record the
--       RE needs, so household_answers below is a genuinely new table rather than a duplicate.
--
--   Net: 3 of the 6 tables named in the Phase C.5 brief already exist under the live schema's own
--   names (households -> profiles, household_members -> household_members, and the answer LOG ->
--   onboarding_sessions); this file adds the 4 that genuinely do not exist.
--
-- Q1-Q15 SOURCE MAP (what the Edge Function joins to build the RE payload — no field is stored
--   twice; anything already on profiles is read from profiles, never re-declared here):
--     q1_household_type        -> public.household_answers.q1_household_type
--     q2_working_professionals -> public.household_answers.q2_working_professionals
--     q3_home_state            -> public.profiles.home_state
--     q4_current_city          -> public.profiles.current_city
--     q5_diet                  -> public.profiles.diet_type
--     q6_nonveg_types          -> public.household_answers.q6_nonveg_types
--     q7_veg_days              -> public.household_answers.q7_veg_days
--     q8_is_jain               -> derived: profiles.religious_pref='jain' OR diet_type='jain'
--     q9_allergies             -> derived: profiles.allergen_flags bitfield -> tokens
--                                 (7-bit model, DOC-P3-02 §Allergen: 1 nuts, 2 dairy, 4 gluten,
--                                  8 shellfish, 16 egg, 32 soy, 64 sesame)
--     q10_allergy_other        -> public.household_answers.q10_allergy_other
--     q11_conditions           -> public.household_answers.q11_conditions
--     q12_member_ages          -> public.household_members (age + conditions-derived role)
--     q13_who_cooks            -> public.household_answers.q13_who_cooks
--     q14_eat_out_per_week     -> public.household_answers.q14_eat_out_per_week
--     q15_objective            -> public.household_answers.q15_objective
--
-- data_source: carried by every new table per the standing project-wide rule. Note this uses
--   `text NOT NULL CHECK (... IN (...))` and NOT the ghar_re.data_source_kind ENUM from 034 —
--   the enum is scoped to the ghar_re schema, and the public schema's own established convention
--   for constrained vocabularies is text + CHECK (see profiles.diet_type, profiles.religious_pref,
--   household_members.conditions). Same three values, this schema's idiom.
--
-- RLS: enabled per table below rather than deferred to a consolidated file. 019 consolidated RLS
--   for the 005-018 band as a one-off; migrations added after it (e.g. 030) carry their own, since
--   public-schema tables are reachable through PostgREST the moment they exist and a table that
--   ships without RLS is exposed in the window before a follow-up migration lands.
-- Prerequisite: 005 (profiles), 006 (household_members), 033 (conditions vocabulary).

-- ---------------------------------------------------------------------------
-- A. household_answers — current-state Q1-Q15 onboarding answers, one row per household.
--    Only the answers that are NOT already columns on public.profiles live here (see source map).
-- ---------------------------------------------------------------------------
CREATE TABLE public.household_answers (
  profile_id               uuid PRIMARY KEY REFERENCES public.profiles(id) ON DELETE CASCADE,
  created_at               timestamptz NOT NULL DEFAULT now(),
  updated_at               timestamptz NOT NULL DEFAULT now(),
  q1_household_type        text CHECK (q1_household_type IN
                             ('single','couple','couple_kids','couple_kids_parents','joint','flatmates')),
  q2_working_professionals integer CHECK (q2_working_professionals >= 0),
  q6_nonveg_types          text[] NOT NULL DEFAULT '{}',
  q7_veg_days              text[] NOT NULL DEFAULT '{}',
  q10_allergy_other        text,
  q11_conditions           text[] NOT NULL DEFAULT '{}',
  q13_who_cooks            text CHECK (q13_who_cooks IN
                             ('self','family','hired_cook','order_tiffin')),
  q14_eat_out_per_week     integer CHECK (q14_eat_out_per_week >= 0),
  q15_objective            text CHECK (q15_objective IN
                             ('awesome_taste','healthy_living','into_fitness','protein_calculator')),
  data_source              text NOT NULL DEFAULT 'real'
                             CHECK (data_source IN ('real','ai_generated','stub'))
);

-- ---------------------------------------------------------------------------
-- B. household_members.age — the one column the RE needs that this table lacks.
--    contracts/ghar-re-v1.schema.json marks MemberAge.age REQUIRED (role is optional), and
--    ghar_re_core/derivation.py reads it numerically for the weaning (<2) and senior (>=65)
--    thresholds. NULLABLE on purpose: age is not collected by the current onboarding flow, and
--    backfilling a fabricated number into every existing row would be inventing user data. The
--    Edge Function supplies a documented role-derived default when this is NULL (see compose.ts);
--    the safety-critical filters key off the role, which conditions[] already supplies exactly.
-- ---------------------------------------------------------------------------
ALTER TABLE public.household_members
  ADD COLUMN age integer CHECK (age IS NULL OR (age >= 0 AND age <= 120));

-- ---------------------------------------------------------------------------
-- C. household_context — the per-request context the RE scores against (θ Context class).
--    One row per recommendation request, not per household: context is dynamic by definition
--    (slot/season/weather change every call), so this is an append-only history, and the Edge
--    Function reads the most recent row per household when the caller supplies no override.
--    Weather is a MOCKED injected input in v1 (no live weather API) — Core Spine B7.
-- ---------------------------------------------------------------------------
CREATE TABLE public.household_context (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  profile_id        uuid NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
  created_at        timestamptz NOT NULL DEFAULT now(),
  slot              text CHECK (slot IN ('breakfast','lunch','dinner','snacks')),
  season            text CHECK (season IN
                      ('summer','monsoon','winter','transitional','post_monsoon')),
  weekday           text,
  weather_condition text,
  temp_c            real,
  is_raining        boolean,
  humidity          real,
  active_modes      text[] NOT NULL DEFAULT '{}',
  calorie_target    integer CHECK (calorie_target IS NULL OR calorie_target > 0),
  data_source       text NOT NULL DEFAULT 'real'
                      CHECK (data_source IN ('real','ai_generated','stub'))
);

-- ---------------------------------------------------------------------------
-- D. recommendation_events — one row per SERVED recommendation request (not per plate).
--    This is the table events.ts currently only logs to. `plates` holds the served set as jsonb
--    so the audit record survives independently of any later catalogue change, and the version
--    stamps make a past recommendation reproducible/explainable after the engine moves on.
--    `outcome` mirrors the Edge Function's own outcome vocabulary (Phase D), including 'partial'.
-- ---------------------------------------------------------------------------
CREATE TABLE public.recommendation_events (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  profile_id     uuid NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
  request_id     text NOT NULL,
  created_at     timestamptz NOT NULL DEFAULT now(),
  slot           text,
  outcome        text NOT NULL CHECK (outcome IN
                   ('success','partial','timeout','network','http','bad_body','fallback')),
  re_served      boolean NOT NULL,
  plate_count    integer NOT NULL DEFAULT 0 CHECK (plate_count >= 0),
  plates         jsonb,
  latency_ms     integer CHECK (latency_ms IS NULL OR latency_ms >= 0),
  detail         text,
  engine_version text,
  config_version text,
  data_source    text NOT NULL DEFAULT 'real'
                   CHECK (data_source IN ('real','ai_generated','stub'))
);

-- ---------------------------------------------------------------------------
-- E. feedback_events — the behavioural logging substrate. Inert pre-launch (zero rows), but
--    required to EXIST from day one per Core Spine appendix A / D7, because v2's learned
--    preference signal reads its history and history cannot be back-filled retroactively.
-- ---------------------------------------------------------------------------
CREATE TABLE public.feedback_events (
  id                      uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  profile_id              uuid NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
  recommendation_event_id uuid REFERENCES public.recommendation_events(id) ON DELETE SET NULL,
  dish_id                 uuid REFERENCES public.dishes(id),
  created_at              timestamptz NOT NULL DEFAULT now(),
  event_type              text NOT NULL CHECK (event_type IN
                            ('accept','edit','swap','like','dislike','shown_not_tapped')),
  slot                    text,
  detail                  jsonb,
  data_source             text NOT NULL DEFAULT 'real'
                            CHECK (data_source IN ('real','ai_generated','stub'))
);

-- ---------------------------------------------------------------------------
-- Indexes — the access paths the Edge Function actually uses.
-- ---------------------------------------------------------------------------
CREATE INDEX idx_household_context_profile ON public.household_context (profile_id, created_at DESC);
CREATE INDEX idx_rec_events_profile        ON public.recommendation_events (profile_id, created_at DESC);
CREATE INDEX idx_rec_events_request        ON public.recommendation_events (request_id);
CREATE INDEX idx_feedback_events_profile   ON public.feedback_events (profile_id, created_at DESC);

-- ---------------------------------------------------------------------------
-- RLS — same own-row pattern as 019 (auth.uid() = profile_id). Writes go through the Edge
-- Function's service_role connection, which bypasses RLS; these policies exist so a direct
-- PostgREST call with a user JWT can only ever see that user's own rows.
-- ---------------------------------------------------------------------------
ALTER TABLE public.household_answers ENABLE ROW LEVEL SECURITY;
CREATE POLICY household_answers_all_own ON public.household_answers
  FOR ALL USING (auth.uid() = profile_id);

ALTER TABLE public.household_context ENABLE ROW LEVEL SECURITY;
CREATE POLICY household_context_all_own ON public.household_context
  FOR ALL USING (auth.uid() = profile_id);

ALTER TABLE public.recommendation_events ENABLE ROW LEVEL SECURITY;
CREATE POLICY rec_events_select_own ON public.recommendation_events
  FOR SELECT USING (auth.uid() = profile_id);

ALTER TABLE public.feedback_events ENABLE ROW LEVEL SECURITY;
CREATE POLICY feedback_events_all_own ON public.feedback_events
  FOR ALL USING (auth.uid() = profile_id);
