ALTER TABLE public.household_context ALTER COLUMN household_id DROP NOT NULL;
ALTER TABLE public.product_events ALTER COLUMN household_id DROP NOT NULL;
ALTER TABLE public.feedback_events ALTER COLUMN household_id DROP NOT NULL;
ALTER TABLE public.recommendation_events ALTER COLUMN household_id DROP NOT NULL;
ALTER TABLE public.week_plans ALTER COLUMN household_id DROP NOT NULL;

DROP TRIGGER IF EXISTS profiles_provision_household ON public.profiles;
DROP FUNCTION IF EXISTS public.provision_profile_household();

-- Backfilled tenant records are retained: deleting them could cascade real post-migration data.
