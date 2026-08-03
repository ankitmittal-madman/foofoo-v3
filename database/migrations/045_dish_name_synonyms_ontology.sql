-- Migration: 045_dish_name_synonyms_ontology.sql
-- WP-19 (Dish Ontology & Regional Names): enriches ghar_re.dish_name_synonyms from a flat
-- synonym list into a SOURCED, REGIONALISED alias ontology. The catalogue's canonical dish names
-- are often the regionally-marked form (e.g. "Bharli Vangi", the Marathi name) which a user from a
-- different state does not recognise even though they cook the identical dish under another name
-- ("Bharwa Baingan" in Hindi, "Gutti Vankaya" in Telugu, "Ennegayi" in Kannada). This migration
-- gives every alias its kind, the region/language it belongs to, a citation, and a confidence — so
-- (a) a dish can be shown/searched in the vocabulary the user actually uses, and (b) the offline
-- classifier (classify_dishes.py, which already reads a dish's synonyms) matches on more real
-- vocabulary, improving dish->class precision.
--
-- Additive & backward-compatible: the existing (dish_id, synonym, data_source) rows are untouched;
-- every new column is nullable. data_source stays the authored-vs-derived provenance enum
-- ('real' = web-researched & cited, 'ai_generated', 'stub'); source_url + confidence carry the
-- per-row evidence for the 'real' rows WP-19 adds.

ALTER TABLE ghar_re.dish_name_synonyms
  ADD COLUMN alias_type text
    CHECK (alias_type IN
      ('regional_name', 'common_name', 'transliteration', 'english_gloss', 'spelling_variant')),
  ADD COLUMN region     text,   -- state/region the alias is used in (NULL = pan-Indian / general)
  ADD COLUMN language    text,   -- language of the alias, lowercase (marathi, hindi, telugu, tamil…)
  ADD COLUMN source_url  text,   -- citation for a web-researched alias (required when data_source='real')
  ADD COLUMN confidence  real CHECK (confidence BETWEEN 0 AND 1);

-- A 'real' (web-researched) alias must carry its citation; derived/stub rows need not. Added
-- NOT VALID: the rule is enforced on every INSERT/UPDATE from here on (so all WP-19 cited rows must
-- carry a source), but pre-existing legacy rows are not retroactively validated — a legacy 'real'
-- row lacking a source_url must not make this schema migration fail on first apply. Backfill legacy
-- sources separately, then `VALIDATE CONSTRAINT` in a later migration if/when full validation is wanted.
ALTER TABLE ghar_re.dish_name_synonyms
  ADD CONSTRAINT dish_name_synonyms_real_needs_source
    CHECK (data_source <> 'real' OR source_url IS NOT NULL) NOT VALID;

COMMENT ON COLUMN ghar_re.dish_name_synonyms.alias_type IS
  'WP-19: kind of alias — regional_name/common_name/transliteration/english_gloss/spelling_variant';
COMMENT ON COLUMN ghar_re.dish_name_synonyms.region IS
  'WP-19: region/state where this alias is the used name; NULL = pan-Indian';
COMMENT ON COLUMN ghar_re.dish_name_synonyms.language IS 'WP-19: language of the alias, lowercase';
COMMENT ON COLUMN ghar_re.dish_name_synonyms.source_url IS
  'WP-19: citation URL for a web-researched (data_source=real) alias';
COMMENT ON COLUMN ghar_re.dish_name_synonyms.confidence IS
  'WP-19: researcher/model confidence in [0,1] that this alias names the same dish';

-- Region lookups: "which aliases are used in Maharashtra" for display localisation.
CREATE INDEX IF NOT EXISTS idx_dish_name_synonyms_region
  ON ghar_re.dish_name_synonyms (region);
