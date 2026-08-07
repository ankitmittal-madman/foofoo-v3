-- Migration: 089_add_hf_image_generation_backend.sql
-- Extends the image_assets.image_gen_backend CHECK constraint (added in migration 077) to allow
-- 'hf_flux_schnell' alongside the existing 'pollinations_flux_pro'.
--
-- Every real Stage 5 generation attempt against Pollinations.ai from the GitHub Actions runner
-- has come back HTTP 403 Forbidden despite a non-default User-Agent already being sent (see
-- database/etl/dish_ingestion/images.py PollinationsClient docstring) -- most consistent with
-- Pollinations blocking GitHub Actions' shared runner IP ranges, not a request-shape problem.
-- The ETL now falls back to Hugging Face's Inference Providers router (text-to-image,
-- black-forest-labs/FLUX.1-schnell) when Pollinations exhausts its retries, so the schema needs a
-- second allowed value to record which backend actually rendered a given image.

ALTER TABLE public.image_assets
  DROP CONSTRAINT image_assets_image_gen_backend_check,
  ADD CONSTRAINT image_assets_image_gen_backend_check
    CHECK (image_gen_backend IN ('pollinations_flux_pro', 'hf_flux_schnell'));

COMMENT ON COLUMN public.image_assets.image_gen_backend IS
  'Which backend rendered the actual image pixels: pollinations_flux_pro (flux-pro via image.pollinations.ai, primary) or hf_flux_schnell (Hugging Face Inference Providers router, FLUX.1-schnell, fallback when Pollinations is blocked/unavailable).';
