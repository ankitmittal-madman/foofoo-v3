-- Migration: 051_public_dish_name_synonyms.sql
-- WP-19 Dish Ontology, retargeted: WP-21 (migration 050) dropped the entire ghar_re schema in
-- production (REPO-CERT-030) — verified 0 rows in pg_namespace afterward — and its own audit
-- independently confirmed no live code path ever read ghar_re.* (the real RE reads public.dishes
-- / a build-time JSON bundle). All of WP-19's alias research (13 batches, seeds 122-134) was
-- therefore targeting a schema that no longer exists and was never actually wired to production.
--
-- This migration recreates the alias ontology against public.dishes (802 rows, the real live
-- content-layer table) instead. public.dishes already carries single-value name_hindi/
-- name_regional columns (migration 008), but a real dish can have MANY cited regional/common
-- names (a Marathi name, a Telugu name, an English gloss, ...) — a one-to-many table is required,
-- exactly as it was in the retired ghar_re.dish_name_synonyms, just pointed at the real table.

CREATE TABLE public.dish_name_synonyms (
  dish_id     uuid NOT NULL REFERENCES public.dishes(id) ON DELETE CASCADE,
  synonym     text NOT NULL,
  data_source text NOT NULL CHECK (data_source IN ('real', 'ai_generated', 'stub')),
  alias_type  text CHECK (alias_type IN
                ('regional_name', 'common_name', 'transliteration', 'english_gloss', 'spelling_variant')),
  region      text,   -- state/region the alias is used in (NULL = pan-Indian / general)
  language    text,   -- language of the alias, lowercase (marathi, hindi, telugu, tamil…)
  source_url  text,   -- citation for a web-researched alias (required when data_source='real')
  confidence  real CHECK (confidence BETWEEN 0 AND 1),
  PRIMARY KEY (dish_id, synonym)
);

-- Every web-researched ('real') alias must carry its citation.
ALTER TABLE public.dish_name_synonyms
  ADD CONSTRAINT dish_name_synonyms_real_needs_source
    CHECK (data_source <> 'real' OR source_url IS NOT NULL);

CREATE INDEX idx_dish_name_synonyms_region ON public.dish_name_synonyms(region);

COMMENT ON TABLE public.dish_name_synonyms IS
  'WP-19 (retargeted post-WP-21): sourced, regionalised dish alias ontology against the live public.dishes table.';
COMMENT ON COLUMN public.dish_name_synonyms.alias_type IS
  'kind of alias — regional_name/common_name/transliteration/english_gloss/spelling_variant';
COMMENT ON COLUMN public.dish_name_synonyms.region IS
  'region/state where this alias is the used name; NULL = pan-Indian';
COMMENT ON COLUMN public.dish_name_synonyms.language IS 'language of the alias, lowercase';
COMMENT ON COLUMN public.dish_name_synonyms.source_url IS
  'citation for a web-researched (real) alias — Wikipedia or an established recipe/food-history site';
COMMENT ON COLUMN public.dish_name_synonyms.confidence IS
  'researcher-assigned confidence in [0,1] that this alias is correct and in active use';

-- Privilege posture matching public.dishes' own RLS pattern (019: dishes_public_read) — this is
-- reference/content data, publicly readable, not user-writable; writes come only from
-- seeds/service_role.
ALTER TABLE public.dish_name_synonyms ENABLE ROW LEVEL SECURITY;
CREATE POLICY dish_name_synonyms_public_read ON public.dish_name_synonyms FOR SELECT USING (true);
REVOKE INSERT, UPDATE, DELETE ON public.dish_name_synonyms FROM authenticated, anon;
