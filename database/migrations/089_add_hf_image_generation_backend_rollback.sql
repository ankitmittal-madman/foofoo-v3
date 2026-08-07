-- Rollback: 089_add_hf_image_generation_backend_rollback.sql
-- Reverts image_assets.image_gen_backend to only allow 'pollinations_flux_pro'.
--
-- Any existing rows with image_gen_backend = 'hf_flux_schnell' must be reset first (rather than
-- deleted -- the underlying image/upload is still real and valid) or this will fail with a check
-- violation, which is the intended safety behavior: never silently drop provenance data.

ALTER TABLE public.image_assets
  DROP CONSTRAINT image_assets_image_gen_backend_check,
  ADD CONSTRAINT image_assets_image_gen_backend_check
    CHECK (image_gen_backend IN ('pollinations_flux_pro'));

COMMENT ON COLUMN public.image_assets.image_gen_backend IS
  'Which backend rendered the actual image pixels. Currently only pollinations_flux_pro (flux-pro model via image.pollinations.ai) is implemented.';
