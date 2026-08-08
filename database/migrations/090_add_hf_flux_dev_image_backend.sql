-- Migration: 090_add_hf_flux_dev_image_backend.sql
-- Extends image_assets.image_gen_backend's CHECK constraint (069/089) to allow 'hf_flux_dev'.
--
-- Founder decision: test Hugging Face's FLUX.1-dev directly against Pollinations for image
-- quality (both flux-pro and flux-realism on Pollinations produced wrong shapes/compositions for
-- unfamiliar regional dishes despite accurate prompt text -- see database/etl/dish_ingestion/
-- images.py module docstring). 'hf_flux_schnell' (migration 089) is kept in the allowed set for
-- historical rows already using it; new HF-backed rows now use 'hf_flux_dev'.

ALTER TABLE public.image_assets
  DROP CONSTRAINT image_assets_image_gen_backend_check,
  ADD CONSTRAINT image_assets_image_gen_backend_check
    CHECK (image_gen_backend IN ('pollinations_flux_pro', 'hf_flux_schnell', 'hf_flux_dev'));

COMMENT ON COLUMN public.image_assets.image_gen_backend IS
  'Which backend rendered the actual image pixels: pollinations_flux_pro (flux-pro/flux-realism via image.pollinations.ai), hf_flux_dev (Hugging Face Inference Providers router, FLUX.1-dev -- current HF default), or hf_flux_schnell (historical rows only, superseded by hf_flux_dev).';
