-- Migration: 007_re_identity_interaction_history.sql
-- Implements: DOC-P3-04 v1.2 §03.29 (user_re_state, user_taste_vectors, never_list,
--   not_today_suppression, variety_window_state, re_dish_bandit_state)
-- Logical functions: LF-A08/A09/B01/E01/J02/J05 (user_re_state), LF-E03/E04/J03/J06
--   (user_taste_vectors), LF-D06/G01/G04/G05 (never_list), LF-E07/G02/G03 (not_today_suppression),
--   LF-F02/F03 (variety_window_state), LF-E06/J04 (re_dish_bandit_state)
-- Governance refs: DOC-P3-05 Part (a) Phase 7 (prerequisite: 003 for persona_id FK, 005 for the
--   app-enforced profile_id link). Phase 4 of the founder's P3-05 brief / DOC-P3-04 §04: these six
--   tables deliberately have NO literal FK to public.profiles.id (cross-schema FK trade-off,
--   documented in P3-04 §04) — integrity for that link is enforced procedurally by LF-M03
--   (the DPDP erasure job), not declaratively here. This is a carried-forward architectural
--   decision from P3-04, not introduced in this migration file.
-- CDM entities: Aggregate 2 (RE Identity) — user_re_state, user_taste_vectors;
--   Aggregate 5 (Interaction History) — never_list, not_today_suppression, variety_window_state,
--   re_dish_bandit_state
-- CDM invariants enforced: Invariant 10 (never_list permanence — enforced by is_active semantics
--   and the absence of any automatic-expiry mechanism in this schema)
-- Note: indexes (idx_user_re_state_cold_start, idx_never_list_active,
-- idx_never_list_reactivation, idx_not_today_active) are NOT created here — see 020.
-- Note: this schema is locked to service_role only per file 001 — no RLS needed or created
-- for these tables, consistent with P3-04 §03.26.

CREATE TABLE re_engine.user_re_state (
  profile_id            uuid PRIMARY KEY,
  persona_id             uuid REFERENCES re_engine.re_personas(id),
  overlay_persona_ids     uuid[] NOT NULL DEFAULT '{}',
  confidence_score        real NOT NULL DEFAULT 0.40 CHECK (confidence_score BETWEEN 0.35 AND 1.0),
  interaction_count        integer NOT NULL DEFAULT 0,
  cold_start_mode           boolean NOT NULL DEFAULT true,
  re_engine_version          text,
  weight_tier                text,
  city_overlay_weight         real,
  updated_at                   timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE re_engine.user_taste_vectors (
  profile_id            uuid PRIMARY KEY,
  updated_at             timestamptz NOT NULL DEFAULT now(),
  genome_tag_affinity     real[],
  class_affinity            jsonb NOT NULL DEFAULT '{}'
);

CREATE TABLE re_engine.never_list (
  profile_id                       uuid NOT NULL,
  dish_id                           uuid NOT NULL,
  nevered_at                         timestamptz NOT NULL DEFAULT now(),
  seasonal_reactivation_eligible       boolean NOT NULL DEFAULT false,
  festival_reactivation_eligible       boolean NOT NULL DEFAULT false,
  last_reactivation_check               timestamptz,
  reactivated_count                      integer NOT NULL DEFAULT 0,
  is_active                              boolean NOT NULL DEFAULT true,
  PRIMARY KEY (profile_id, dish_id)
);

CREATE TABLE re_engine.not_today_suppression (
  profile_id     uuid NOT NULL,
  dish_id        uuid NOT NULL,
  suppressed_at  timestamptz NOT NULL DEFAULT now(),
  p0             real NOT NULL DEFAULT 0.80,
  lambda         real NOT NULL DEFAULT 0.35,
  effective_until timestamptz NOT NULL,
  is_active      boolean NOT NULL DEFAULT true,
  PRIMARY KEY (profile_id, dish_id)
);

CREATE TABLE re_engine.variety_window_state (
  profile_id              uuid PRIMARY KEY,
  updated_at                timestamptz NOT NULL DEFAULT now(),
  last_7_class_codes          text[] NOT NULL DEFAULT '{}',
  last_7_cuisine_families      text[] NOT NULL DEFAULT '{}',
  last_7_cooking_methods         text[] NOT NULL DEFAULT '{}',
  last_30_dish_ids                 uuid[] NOT NULL DEFAULT '{}',
  fried_count_this_week              smallint NOT NULL DEFAULT 0,
  monsoon_override_active             boolean NOT NULL DEFAULT false
);

CREATE TABLE re_engine.re_dish_bandit_state (
  profile_id  uuid NOT NULL,
  dish_id     uuid NOT NULL,
  alpha       real NOT NULL DEFAULT 1.0,
  beta        real NOT NULL DEFAULT 1.0,
  updated_at  timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (profile_id, dish_id)
);
