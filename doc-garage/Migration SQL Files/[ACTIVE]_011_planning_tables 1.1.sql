-- Migration: 011_planning_tables.sql
-- Implements: DOC-P3-04 v1.3 §03.12 (week_plans), §03.13 (plan_slots), §03.14 (addon_slots)
-- Logical functions: LF-B02/L01/L02 (week_plans), LF-B02/D01-D07/E01-E08/F01-F03/L01-L03
--   (plan_slots), LF-C01/C02 (addon_slots)
-- Governance refs: DOC-P3-05 Part (a) v1.2 Phase 7 (prerequisite: 003 for meal_classes FK,
--   005 for profiles, 006 for household_members, 008 for dishes)
-- CDM entities: Entity 23 (Week Plan), Entity 24 (Plan Slot), Entity 26 (Add-on Slot)
-- CDM invariants enforced: Invariant 11 (one plan per week — UNIQUE(profile_id, week_start_date)
--   below), Invariant 9 (add-on never replaces primary — UNIQUE(plan_slot_id, household_member_id)
--   on addon_slots, enforced structurally by addon_slots being a distinct table from plan_slots)
-- AGR-002 RESOLVED (v1.2, at the planning layer): public.meal_classes was relocated to file 003
-- (it was a planning-allocation defect in Part (a), not a P3-04 issue). plan_slots.class_code
-- below now carries its FK directly, exactly as DOC-P3-04 §03.13 specifies, with no workaround.

CREATE TABLE public.week_plans (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  profile_id       uuid NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
  week_start_date  date NOT NULL,
  created_at       timestamptz NOT NULL DEFAULT now(),
  re_version       text NOT NULL,
  is_locked        boolean NOT NULL DEFAULT false,
  UNIQUE (profile_id, week_start_date)
);

CREATE TABLE public.plan_slots (
  id                       uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  week_plan_id             uuid NOT NULL REFERENCES public.week_plans(id) ON DELETE CASCADE,
  slot_date                date NOT NULL,
  meal_slot                text NOT NULL CHECK (meal_slot IN ('breakfast','lunch','dinner')),
  class_code               text NOT NULL REFERENCES public.meal_classes(class_code),
  selected_dish_id          uuid REFERENCES public.dishes(id),
  is_locked                boolean NOT NULL DEFAULT false,
  locked_at                timestamptz,
  slate_dish_ids            uuid[] NOT NULL DEFAULT '{}',
  slate_reasons             jsonb NOT NULL DEFAULT '{}',
  slate_confidence          real,
  slate_generated_at        timestamptz,
  cold_start_mode           boolean NOT NULL DEFAULT true,
  UNIQUE (week_plan_id, slot_date, meal_slot)
);

CREATE TABLE public.addon_slots (
  id                   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  plan_slot_id         uuid NOT NULL REFERENCES public.plan_slots(id) ON DELETE CASCADE,
  household_member_id  uuid NOT NULL REFERENCES public.household_members(id) ON DELETE CASCADE,
  addon_class_code     text NOT NULL,
  dish_id              uuid REFERENCES public.dishes(id),
  UNIQUE (plan_slot_id, household_member_id)
);
