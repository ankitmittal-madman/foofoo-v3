-- Rollback for 125_dish_safety_field_correctness_audit.sql.
-- Drops the audit/autocorrect functions only. Does NOT revert the is_jain/diet_type/allergen_flags
-- corrections already applied to production on 2026-08-08 (1,040 is_jain, 220 diet_type->non_veg,
-- 97 diet_type->egg, 395 nuts + 47 fish allergen_flags rows) — those corrections fixed real,
-- spot-verified data errors (e.g. dishes containing chicken/prawns marked veg/jain) and reverting
-- them would reintroduce a known food-safety defect. If a genuine revert of the data itself is
-- ever required, it must be a separate, explicitly-reviewed migration, not this rollback.

DROP FUNCTION IF EXISTS public.dish_safety_field_autocorrect();
DROP FUNCTION IF EXISTS re_engine.dish_safety_field_autocorrect();
DROP FUNCTION IF EXISTS re_engine.dish_safety_field_violations();
