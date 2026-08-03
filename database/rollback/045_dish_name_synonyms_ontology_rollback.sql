-- Rollback: 045_dish_name_synonyms_ontology.sql
-- Drops the WP-19 ontology columns/constraint/index. The pre-existing (dish_id, synonym,
-- data_source) rows are unaffected; only the additive WP-19 enrichment is removed.

DROP INDEX IF EXISTS ghar_re.idx_dish_name_synonyms_region;

ALTER TABLE ghar_re.dish_name_synonyms
  DROP CONSTRAINT IF EXISTS dish_name_synonyms_real_needs_source;

ALTER TABLE ghar_re.dish_name_synonyms
  DROP COLUMN IF EXISTS confidence,
  DROP COLUMN IF EXISTS source_url,
  DROP COLUMN IF EXISTS language,
  DROP COLUMN IF EXISTS region,
  DROP COLUMN IF EXISTS alias_type;
