-- Rollback: 090_add_hf_flux_dev_image_backend_rollback.sql
-- Reverts image_assets.image_gen_backend to only allow 'pollinations_flux_pro' and
-- 'hf_flux_schnell' (migration 089 state).
--
-- Any existing rows with image_gen_backend = 'hf_flux_dev' must be reset first (never delete the
-- underlying image/upload provenance) or this will fail with a check violation -- intended.

ALTER TABLE public.image_assets
  DROP CONSTRAINT image_assets_image_gen_backend_check,
  ADD CONSTRAINT image_assets_image_gen_backend_check
    CHECK (image_gen_backend IN ('pollinations_flux_pro', 'hf_flux_schnell'));

COMMENT ON COLUMN public.image_assets.image_gen_backend IS
  'Which backend rendered the actual image pixels: pollinations_flux_pro (flux-pro via image.pollinations.ai, primary) or hf_flux_schnell (Hugging Face Inference Providers router, FLUX.1-schnell, fallback when Pollinations is blocked/unavailable).';
