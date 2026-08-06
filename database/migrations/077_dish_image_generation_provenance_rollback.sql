-- Rollback: 077_dish_image_generation_provenance.sql
ALTER TABLE public.image_assets
  DROP COLUMN IF EXISTS prompt_text,
  DROP COLUMN IF EXISTS prompt_backend,
  DROP COLUMN IF EXISTS prompt_model_name,
  DROP COLUMN IF EXISTS image_gen_backend,
  DROP COLUMN IF EXISTS image_gen_seed;
