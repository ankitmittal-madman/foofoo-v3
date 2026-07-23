-- Migration: 035_ghar_re_household_runtime.sql
-- Project: Ghar RE v1.0 rebuild (schema `ghar_re`).
-- Implements: TASK 1 Group B — Household / Onboarding / Runtime tables.
-- Source specs: D1-D7 FROZEN §1.1 (per-field θ metadata schema), §1.2/§1.3 (θ classes/stability);
--   Core Spine appendix + D7 require feedback_event / recommendation_event to EXIST from day one
--   (the logging substrate) even with zero rows pre-launch.
-- Prerequisite: 034 (schema + data_source enum).

-- B.1  households  — the RAW Q1-Q15 onboarding answers, before any derivation.
CREATE TABLE ghar_re.households (
  id                     uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  label                  text,                        -- human label for the golden sample
  -- Q1-Q15 verbatim (D1-D7 onboarding map)
  q1_household_type      text,                        -- single/couple/couple_kids/couple_kids_parents/joint/flatmates
  q2_working_professionals integer,
  q3_home_state          text,
  q4_current_city        text,
  q5_diet                text,                        -- veg/eggetarian/non_veg
  q6_nonveg_types        text[],                      -- chicken/mutton/fish/... + exclusions (no_beef,...)
  q7_veg_days            text[],                      -- weekday names, if any
  q8_is_jain             boolean NOT NULL DEFAULT false,
  q9_allergies           text[],                      -- allergen tokens (gluten/peanuts/...)
  q10_allergy_other      text,
  q11_conditions         text[],                      -- BP/diabetes/... (secondary demote, PARKED)
  q12_member_ages        jsonb,                       -- [{role, age}] so weaning/senior detection works
  q13_who_cooks          text,                        -- self/family/hired_cook/order_tiffin
  q14_eat_out_per_week   integer,
  q15_objective          text,                        -- awesome_taste/healthy_living/into_fitness/protein_calculator
  created_at             timestamptz NOT NULL DEFAULT now(),
  data_source            ghar_re.data_source_kind NOT NULL
);

-- B.2  household_profile — the derived θ object.  ONE ROW PER (household, derived field),
--   each carrying the full D1-D7 §1.1 provenance record. Modelled tall/EAV-style precisely so
--   every field gets value + confidence + source + kind + stability + version + timestamp
--   without a 40-column wide table. `value` is jsonb to hold scalars, strings, arrays, or objects.
CREATE TABLE ghar_re.household_profile (
  household_id uuid NOT NULL REFERENCES ghar_re.households(id) ON DELETE CASCADE,
  field_name   text NOT NULL,                         -- e.g. blend, income_band, spice_ceiling, region
  value        jsonb NOT NULL,                        -- §1.1 value
  confidence   real NOT NULL DEFAULT 1.0 CHECK (confidence BETWEEN 0 AND 1),  -- v1: 1.0 everywhere
  source       text NOT NULL,                         -- §1.1 source: "D4" / "explicit" / "context"
  kind         text NOT NULL CHECK (kind IN ('explicit','derived','learned')),
  stability    text NOT NULL CHECK (stability IN ('stable','dynamic')),
  version      text NOT NULL,                          -- logic version, e.g. "D-layer v1.0"
  computed_at  timestamptz NOT NULL DEFAULT now(),
  data_source  ghar_re.data_source_kind NOT NULL,
  PRIMARY KEY (household_id, field_name)
);

-- B.3  household_context — DYNAMIC per-session context (θ Context class, recomputed each request).
CREATE TABLE ghar_re.household_context (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  household_id      uuid NOT NULL REFERENCES ghar_re.households(id) ON DELETE CASCADE,
  session_id        text,
  slot              text CHECK (slot IN ('breakfast','lunch','dinner','snacks')),
  season            text CHECK (season IN ('summer','monsoon','winter','transitional','post_monsoon')),
  weekday           text,
  -- weather is a MOCKED injected input in v1 (no live API) — Core Spine B7 / Task 3 point 3.
  weather_condition text,                             -- e.g. rain/heatwave/cold_snap/clear
  temp_c            real,
  is_raining        boolean,
  humidity          real,                             -- optional; humidity_modifier only if present
  active_modes      text[],                           -- fasting/festival/veg_egg
  calorie_target    integer,                          -- A6 opt-in
  created_at        timestamptz NOT NULL DEFAULT now(),
  data_source       ghar_re.data_source_kind NOT NULL
);

-- B.4  household_modes — the v1 user-toggled MODES (Final_RE Section A): fasting/festival/veg_egg.
CREATE TABLE ghar_re.household_modes (
  household_id uuid NOT NULL REFERENCES ghar_re.households(id) ON DELETE CASCADE,
  mode         text NOT NULL CHECK (mode IN ('fasting','festival','veg_egg')),
  is_on        boolean NOT NULL DEFAULT false,
  params       jsonb,                                 -- e.g. festival name, veg_egg -> veg|egg
  data_source  ghar_re.data_source_kind NOT NULL,
  PRIMARY KEY (household_id, mode)
);

-- B.5  feedback_event — the behavioural logging substrate (inert pre-launch; v2 S_pref reads it).
--   Required to EXIST from day one per Core Spine appendix A / D7 / Final_RE Deferred register.
CREATE TABLE ghar_re.feedback_event (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  household_id uuid NOT NULL REFERENCES ghar_re.households(id) ON DELETE CASCADE,
  dish_id      uuid REFERENCES ghar_re.dishes(id),
  event_type   text NOT NULL CHECK (event_type IN
                 ('accept','edit','swap','like','dislike','shown_not_tapped')),
  plate_ref    uuid,                                  -- -> recommendation_event.id
  slot         text,
  detail       jsonb,
  created_at   timestamptz NOT NULL DEFAULT now(),
  data_source  ghar_re.data_source_kind NOT NULL
);

-- B.6  recommendation_event — every served plate stamped with Spine/KB/Config versions (audit).
CREATE TABLE ghar_re.recommendation_event (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  household_id   uuid NOT NULL REFERENCES ghar_re.households(id) ON DELETE CASCADE,
  session_id     text,
  slot           text,
  rank           integer,                             -- 1..7 within the served set
  plate          jsonb NOT NULL,                      -- {hero(s), support, form, components}
  plate_score    real,
  spine_version  text,                                -- "Spine v1.0"
  kb_version     text,                                -- "KB v0.2"
  config_version text,                                -- "Config v1.0"
  created_at     timestamptz NOT NULL DEFAULT now(),
  data_source    ghar_re.data_source_kind NOT NULL
);

CREATE INDEX idx_ghar_hh_profile_field  ON ghar_re.household_profile (field_name);
CREATE INDEX idx_ghar_context_household ON ghar_re.household_context (household_id, created_at);
CREATE INDEX idx_ghar_feedback_hh       ON ghar_re.feedback_event (household_id, created_at);
CREATE INDEX idx_ghar_recevent_hh       ON ghar_re.recommendation_event (household_id, created_at);
