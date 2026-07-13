-- Migration: 005_profiles.sql
-- Implements: DOC-P3-04 v1.2 §03.1 (public.profiles)
-- Logical functions: LF-A01-A09 (all onboarding writes), LF-D02/D04/H01/H03 (diet/religious reads)
-- Governance refs: DOC-P3-05 Part (a) Phase 7 (prerequisite: 002, for home_state FK; also
--   requires platform-provided auth.users per Phase 13 Environment Assumptions)
-- CDM entities: Entity 1 (User/Profile), Entity 4 (Regional Identity, partial)
-- CDM invariants enforced: Invariant 7 (city_overlay_weight + home_state_signature_weight = 1.0,
--   enforced by application logic per P3-04 — NOT a DB constraint, since the complement weight
--   is not itself a stored column); Invariant 2 (jain_diet_consistency CHECK below)
-- Note: indexes (idx_profiles_last_active, idx_profiles_home_state) and RLS policies are NOT
-- created here — consolidated into 020 and 019 per Phase 8.3/8.4.

CREATE TABLE public.profiles (
  id                          uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  created_at                  timestamptz NOT NULL DEFAULT now(),
  updated_at                  timestamptz NOT NULL DEFAULT now(),
  onboarding_completed        boolean NOT NULL DEFAULT false,
  primary_cook_name           text NOT NULL,
  home_state                  text NOT NULL REFERENCES re_engine.re_states(state_code),
  current_city                text NOT NULL,
  migration_duration_band     text CHECK (migration_duration_band IN ('native','lt_1yr','1_3yr','3_7yr','7plus_yr','skipped')),
  city_overlay_weight         real NOT NULL DEFAULT 0.50 CHECK (city_overlay_weight BETWEEN 0 AND 1),
  diet_type                   text NOT NULL CHECK (diet_type IN ('veg','non_veg','egg','vegan','jain')),
  religious_pref              text NOT NULL DEFAULT 'all' CHECK (religious_pref IN ('all','hindu_veg','jain','halal','no_beef','no_pork')),
  allergen_flags              integer NOT NULL DEFAULT 0,
  cook_capability              text NOT NULL CHECK (cook_capability IN ('beginner','intermediate','advanced')),
  push_notification_time      time NOT NULL DEFAULT '07:00:00',
  last_active_at               timestamptz,
  deleted_at                   timestamptz,
  CONSTRAINT jain_diet_consistency CHECK (
    NOT (religious_pref = 'jain' AND diet_type NOT IN ('veg','jain'))
  )
);
