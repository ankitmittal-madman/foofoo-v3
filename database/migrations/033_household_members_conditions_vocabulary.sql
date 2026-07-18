-- Migration: 033_household_members_conditions_vocabulary.sql
-- Implements: SER-004 (Founder-approved) — FD-15 Phase 2. Replaces household_members.segment
--   (scalar text, 8-value CHECK) with household_members.conditions (text[], 15-value CHECK),
--   so a member can carry multiple independent condition tags simultaneously, per the Canonical
--   Planning Semantics Architecture's requirement that conditions "combine freely."
-- Governance refs: [ACTIVE]_SER-004_household_members_conditions_vocabulary_v1.0.md (approved
--   as finalized, including the vocabulary exclusions/collapses and the derive-don't-persist
--   routing decision). [ACTIVE]_Founder_Decision_Register_v1.0.md FD-15.
--
-- Precedent followed exactly: 025_combo_component_type_and_slot_array.sql /
--   026_meal_classes_mirror_slot_array.sql (re_meal_classes.slot / meal_classes.slot scalar text
--   -> text[] conversion, same ALTER COLUMN ... TYPE ... USING + CHECK-containment shape).
--
-- Verified live before writing this migration (this session, direct psql introspection, not
--   assumed from documentation):
--   * Exact constraint name: household_members_segment_check (confirmed via pg_constraint,
--     not guessed) — CHECK (segment = ANY (ARRAY['INFANT','TODDLER','SCHOOL_CHILD',
--     'DIABETIC_ELDER','POSTPARTUM','FITNESS_OVERLAY','FASTING_MEMBER','ADULT_STANDARD'])).
--   * household_members holds 0 live rows — the USING conversion below is verified lossless
--     with no data to lose, and is written to also be correct in general (ARRAY[segment] wraps
--     any single existing value as a one-element array).
--   * No view, rule, or function body anywhere in the live database references
--     household_members.segment (checked via pg_depend / pg_proc.prosrc, not grep alone).
--   * addon_slots.household_member_id FK confirmed live and unaffected — it references
--     household_members.id only, never segment/conditions.
--
-- Vocabulary provenance (single authoritative source, not hand-retyped): the 15 values in the
--   CHECK below are the live-queried UNION of re_engine.re_addon_classes.segment and
--   re_engine.re_household_addon_plans.segment (20 distinct values, confirmed this session),
--   minus exactly 5 Founder-directed exclusions/collapses (SER-004 §6):
--     - allergy_member            (redundant with household_members.allergen_flags bitfield)
--     - cook_needs_instruction    (household-scoped -> profiles.cook_capability, not here)
--     - working_kitchen_manager   (household-scoped -> profiles.cook_capability, not here)
--     - child_or_picky_child      (duplicate pair 1 -> collapsed into picky_child)
--     - postpartum_mother         (duplicate pair 2 -> collapsed into lactating_or_postpartum_mother)
--   20 - 5 = 15. (An earlier estimate of "~17-18" was arithmetically incorrect against the
--   actual exclusion list and is superseded by this derivation — see SER-004 §6.)
--
-- Default: '{}' (empty array) replaces ADULT_STANDARD as the "no condition" representation —
--   the common, valid case for most members, per SER-004 §7. Note cardinality(conditions) >= 0
--   in the CHECK below, NOT >= 1 (unlike the slot precedent, where every meal class must always
--   occupy at least one slot) — zero conditions is expected and valid here.
--
-- Routing (Absorb/Swap/Add) is explicitly NOT persisted anywhere by this migration — per
--   SER-004 §8/Architecture §9b, routing is derived dynamically by the future Planning Engine,
--   not a static property of a condition. No schema surface for it exists here or is implied.

ALTER TABLE public.household_members
  ALTER COLUMN segment TYPE text[] USING ARRAY[segment];

ALTER TABLE public.household_members
  RENAME COLUMN segment TO conditions;

ALTER TABLE public.household_members
  ALTER COLUMN conditions SET DEFAULT '{}';

ALTER TABLE public.household_members
  DROP CONSTRAINT household_members_segment_check;

ALTER TABLE public.household_members
  ADD CONSTRAINT household_members_conditions_check
  CHECK (
    conditions <@ ARRAY[
      'baby_6_18m', 'diabetic_member', 'elderly_member', 'fasting_member',
      'gym_high_protein_member', 'hypertension_heart_member', 'jain_member',
      'lactating_or_postpartum_mother', 'picky_child', 'pregnant_member',
      'recovery_member', 'school_child', 'teen_high_appetite', 'toddler',
      'weight_loss_member'
    ]::text[]
    AND cardinality(conditions) >= 0
  );
