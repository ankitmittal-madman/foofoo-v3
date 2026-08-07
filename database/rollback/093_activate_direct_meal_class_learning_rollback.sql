-- Stop serving the new direct/projected fields before applying this rollback.
DROP FUNCTION IF EXISTS public.refresh_user_taste_vector(uuid);
ALTER FUNCTION public.refresh_user_taste_vector_without_direct_class(uuid)
  RENAME TO refresh_user_taste_vector;
REVOKE ALL ON FUNCTION public.refresh_user_taste_vector(uuid) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.refresh_user_taste_vector(uuid) TO service_role;

ALTER TABLE public.user_taste_vectors
  DROP COLUMN IF EXISTS projected_class_affinity,
  DROP COLUMN IF EXISTS direct_class_affinity;
