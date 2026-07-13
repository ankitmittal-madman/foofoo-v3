-- Migration: 012_interaction_audit_appendonly.sql
-- Implements: DOC-P3-04 v1.3 §03.15 (interaction_events, partitioned parent),
--   §03.16 (suggestion_logs, partitioned parent), §03.17 (context_log), §03.18 (weather_cache)
-- Logical functions: LF-J01-J09/G01/G02/L04 (interaction_events), LF-F01/H01-H04
--   (suggestion_logs), LF-I01/J07 (context_log), LF-I02 (weather_cache)
-- Governance refs: DOC-P3-05 Part (a) Phase 7 (prerequisite: 005, 008); Phase 8.7 (partition
--   child tables deferred to file 017, NOT created here — only the partitioned parent tables)
-- CDM entities: Entity 29 (Interaction Event), Entity 46 (Weather Cache — note: CDM numbering
--   reuses "46" for both Weather Cache and, in a different context, Class Affinity in earlier
--   project documents; this file follows DOC-P3-04 §03.18's table definition directly, not a
--   CDM entity number, to avoid relying on a numbering ambiguity outside this file's scope)
-- CDM invariants enforced: none directly (these are append-only logs; the safety gates that
--   read suggestion_logs are a Part (d)/DOC-P4 concern, not created here)
-- Note: this file creates the PARTITIONED PARENT tables only (PARTITION BY RANGE). No child
-- partition exists until file 017 runs — these parent tables cannot accept rows until then.

CREATE TABLE public.interaction_events (
  id                    uuid NOT NULL DEFAULT gen_random_uuid(),
  profile_id            uuid NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
  event_type            text NOT NULL CHECK (event_type IN
    ('dish_accepted','dish_locked','dish_cooked','dish_ordered','dish_rated',
     'dish_never','dish_not_today','dish_swiped_past',
     'onboarding_class_preference','plan_opened','session_depth')),
  dish_id               uuid REFERENCES public.dishes(id),
  meal_slot             text,
  slot_date             date,
  rank_at_interaction   smallint,
  time_viewed_ms        integer,
  rating                smallint CHECK (rating BETWEEN 1 AND 5),
  context               jsonb,
  re_version            text,
  confidence_at_time    real,
  occurred_at           timestamptz NOT NULL DEFAULT now(),
  synced_to_re          boolean NOT NULL DEFAULT false,
  PRIMARY KEY (id, occurred_at)
) PARTITION BY RANGE (occurred_at);

CREATE TABLE public.suggestion_logs (
  id                          uuid NOT NULL DEFAULT gen_random_uuid(),
  profile_id                  uuid NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
  dish_id                     uuid NOT NULL REFERENCES public.dishes(id),
  slate_id                    uuid NOT NULL,
  suggested_at                timestamptz NOT NULL DEFAULT now(),
  meal_slot                   text NOT NULL,
  slot_date                   date NOT NULL,
  rank_in_slate                smallint NOT NULL CHECK (rank_in_slate BETWEEN 1 AND 8),
  class_code                   text NOT NULL,
  re_version                   text NOT NULL,
  cold_start_mode               boolean NOT NULL,
  confidence_at_suggestion       real NOT NULL,
  n_candidates_before_filter     integer,
  context_snapshot                jsonb,
  PRIMARY KEY (id, suggested_at)
) PARTITION BY RANGE (suggested_at);

CREATE TABLE public.context_log (
  id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  profile_id          uuid NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
  slate_id            uuid NOT NULL,
  logged_at           timestamptz NOT NULL DEFAULT now(),
  weather_condition   text,
  temp_c              real,
  city                text NOT NULL,
  day_of_week         text NOT NULL,
  is_weekend          boolean NOT NULL,
  season              text NOT NULL,
  time_of_day         text NOT NULL,
  festival_proximity  jsonb,
  re_version          text NOT NULL
);

CREATE TABLE public.weather_cache (
  city          text NOT NULL,
  date          date NOT NULL,
  temp_c        real,
  humidity_pct  smallint,
  condition     text,
  fetched_at    timestamptz NOT NULL DEFAULT now(),
  expires_at    timestamptz NOT NULL,
  PRIMARY KEY (city, date)
);
