-- Migration: 006_profile_dependent_public.sql
-- Implements: DOC-P3-04 v1.2 §03.2 (household_members), §03.3 (onboarding_sessions),
--   §03.4 (consent_records)
-- Logical functions: LF-A02/A05/C01/D03 (household_members), LF-A01-A08 (onboarding_sessions),
--   LF-M01 (consent_records)
-- Governance refs: DOC-P3-05 Part (a) Phase 7 (prerequisite: 005)
-- CDM entities: Entity 3 (Household Member), Entity 28 (Onboarding Session), Entity 51 (Consent Record)
-- CDM invariants enforced: Invariant 4 (member allergen propagation — enforced by the
--   fn_sync_profile_allergen_union trigger, which is deployed in file 010, NOT here; this file
--   only creates the table the trigger will later attach to)
-- Note: indexes (idx_household_members_profile, idx_onboarding_sessions_profile,
-- idx_consent_profile_type) and RLS policies are NOT created here — see 020/019.
-- Note: the trigger trg_sync_allergen_union itself is allocated to file 010 per Phase 8.2
-- (all 4 trigger functions grouped in one file), NOT created alongside this table.

CREATE TABLE public.household_members (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  profile_id      uuid NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
  created_at      timestamptz NOT NULL DEFAULT now(),
  member_name     text,
  segment         text NOT NULL CHECK (segment IN
    ('INFANT','TODDLER','SCHOOL_CHILD','DIABETIC_ELDER','POSTPARTUM',
     'FITNESS_OVERLAY','FASTING_MEMBER','ADULT_STANDARD')),
  allergen_flags  integer NOT NULL DEFAULT 0,
  diet_type       text CHECK (diet_type IN ('veg','non_veg','egg','vegan','jain')),
  is_active       boolean NOT NULL DEFAULT true
);

CREATE TABLE public.onboarding_sessions (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  profile_id    uuid NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
  created_at    timestamptz NOT NULL DEFAULT now(),
  screen_id     text NOT NULL,
  question_key  text NOT NULL,
  answer_value  jsonb NOT NULL,
  skipped       boolean NOT NULL DEFAULT false,
  answered_at   timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE public.consent_records (
  id                     uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  profile_id             uuid NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
  consent_type           text NOT NULL CHECK (consent_type IN
    ('personalization','analytics','push_notifications','data_retention')),
  granted                boolean NOT NULL,
  granted_at             timestamptz NOT NULL DEFAULT now(),
  ip_address_hash        text,
  privacy_policy_version text NOT NULL
);
