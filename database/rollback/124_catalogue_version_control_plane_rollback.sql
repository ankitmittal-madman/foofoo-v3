DROP TABLE IF EXISTS public.catalogue_rollout_state;
DROP TRIGGER IF EXISTS catalogue_dishes_immutable ON public.catalogue_dishes;
DROP TRIGGER IF EXISTS catalogue_versions_immutable ON public.catalogue_versions;
DROP FUNCTION IF EXISTS re_engine.reject_catalogue_mutation();
DROP TABLE IF EXISTS public.catalogue_dishes;
DROP TABLE IF EXISTS public.catalogue_versions;
