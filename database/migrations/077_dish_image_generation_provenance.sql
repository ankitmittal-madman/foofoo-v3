-- Migration: 077_dish_image_generation_provenance.sql
-- Adds the genuine schema gap for Stage 5 (real image generation) that migration 076 did not
-- cover: migration 076's public.image_assets records WHAT was fetched (source_url, checksum,
-- fetch_status) but has no column for HOW an ai_generated image was produced — which
-- prompt-generation backend/model supplied the fill-in fields, which image model rendered the
-- pixels, and the exact prompt text sent. Without this, an ai_generated row's provenance would be
-- unrecoverable after the fact (task brief explicitly asks for "full provenance: which
-- model/prompt/adapter generated it").
--
-- Everything else Stage 5 needs (source_url, storage_path, checksum_sha256, content_type,
-- fetch_status, dish_images.source_type/confidence/alt_text/is_primary) already exists in 076 —
-- reused unchanged, no duplication.

ALTER TABLE public.image_assets
  ADD COLUMN prompt_text          text,    -- the fully-assembled standardized prompt sent to the image model
  ADD COLUMN prompt_backend       text CHECK (prompt_backend IN ('groq_api','hf_api','heuristic')),
  ADD COLUMN prompt_model_name    text,    -- e.g. 'llama-3.1-8b-instant', 'mistralai/Mistral-7B-Instruct-v0.3', NULL for heuristic
  ADD COLUMN image_gen_backend    text CHECK (image_gen_backend IN ('pollinations_flux_pro')),
  ADD COLUMN image_gen_seed       integer; -- random seed used for the Pollinations request, for reproducibility/debugging

COMMENT ON COLUMN public.image_assets.prompt_text IS
  'Full standardized prompt text (fixed template + LLM-filled blanks) sent to the image generation backend. NULL for non-ai_generated rows.';
COMMENT ON COLUMN public.image_assets.prompt_backend IS
  'Which backend supplied the prompt fill-in fields (category/vessel_type/description/focal point): groq_api | hf_api | heuristic. Never claims a real model call that did not happen (task brief honesty discipline).';
COMMENT ON COLUMN public.image_assets.image_gen_backend IS
  'Which backend rendered the actual image pixels. Currently only pollinations_flux_pro (flux-pro model via image.pollinations.ai) is implemented.';
