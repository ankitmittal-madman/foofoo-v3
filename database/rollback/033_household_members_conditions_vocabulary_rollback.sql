-- Rollback: 033_household_members_conditions_vocabulary_rollback.sql
-- Reverses: 033_household_members_conditions_vocabulary.sql
--
-- IMPORTANT — read before executing, this rollback is NOT unconditionally safe:
--   `conditions[1]` (first array element) is only a lossless reverse of the forward migration
--   if no row has been given more than one tag between the forward migration landing and this
--   rollback running. At the time the forward migration was written, household_members held 0
--   live rows, so this was trivially true then. If this rollback is executed later, after real
--   onboarding data exists, RE-VERIFY before running:
--
--     SELECT count(*) FROM public.household_members WHERE cardinality(conditions) > 1;
--
--   If that count is > 0, this rollback SILENTLY DISCARDS every condition tag after the first
--   for those rows (array -> scalar can only keep one value). Do not run this rollback against
--   real multi-condition data without an explicit decision on which tag to keep, or an export
--   of the discarded tags first.
--
-- SECOND CAVEAT, also disclosed rather than silently worked around: the reconstructed scalar
--   values will be the NEW lowercase vocabulary (e.g. 'toddler'), which do NOT satisfy the OLD
--   8-value uppercase CHECK ('TODDLER', etc.) — the two vocabularies are not the same values.
--   This rollback therefore restores the OLD CHECK CONSTRAINT SHAPE for structural/documentation
--   symmetry with the forward migration, but does NOT attempt a value re-mapping (new condition
--   -> old segment enum), since that mapping was never specified anywhere and this rollback will
--   not invent one. On any table with live data, adding the old CHECK back will fail validation
--   until that mapping decision is made — this is expected, not a bug in this script. If you need
--   to unblock quickly with live data present, comment out the final ADD CONSTRAINT statement
--   below and resolve the value mapping as a separate, explicit follow-up decision.

-- 1. Drop the new (15-value, array-based) constraint first — must go before the type changes
--    below, since it references the array-typed column.
ALTER TABLE public.household_members
  DROP CONSTRAINT household_members_conditions_check;

-- 2. Remove the array-era default; the old column was NOT NULL with no default.
ALTER TABLE public.household_members
  ALTER COLUMN conditions DROP DEFAULT;

-- 3. Convert text[] -> text, keeping only the first tag per row (see caveat above).
ALTER TABLE public.household_members
  ALTER COLUMN conditions TYPE text USING conditions[1];

-- 4. Rename back to the original column name.
ALTER TABLE public.household_members
  RENAME COLUMN conditions TO segment;

-- 5. Restore NOT NULL (a row with zero conditions, cardinality 0, produces conditions[1] = NULL
--    after step 3 — this will fail step 5 if any such row exists; that is expected, since the
--    entire point of the new vocabulary's empty-array default was to make "no condition" a valid
--    state, which the old scalar NOT NULL column could never represent as anything other than
--    the placeholder 'ADULT_STANDARD'. Resolve by deciding what such rows should become before
--    running this rollback against real data.
ALTER TABLE public.household_members
  ALTER COLUMN segment SET NOT NULL;

-- 6. Restore the original 8-value CHECK, for structural symmetry — see second caveat above
--    regarding value-mapping, not attempted here.
ALTER TABLE public.household_members
  ADD CONSTRAINT household_members_segment_check
  CHECK (
    segment = ANY (ARRAY[
      'INFANT','TODDLER','SCHOOL_CHILD','DIABETIC_ELDER','POSTPARTUM',
      'FITNESS_OVERLAY','FASTING_MEMBER','ADULT_STANDARD'
    ]::text[])
  );
