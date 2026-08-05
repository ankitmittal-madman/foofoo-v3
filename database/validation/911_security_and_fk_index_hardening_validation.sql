-- Migration 057 acceptance contract. Every query must return zero rows (or zero count).

-- Trigger-only SECURITY DEFINER functions must not be callable through PostgREST roles.
SELECT proc.oid::regprocedure AS unexpectedly_executable_function, role_name
FROM pg_proc proc
CROSS JOIN (VALUES ('anon'), ('authenticated')) AS roles(role_name)
WHERE proc.oid IN (
  'public.create_dish_enrichment_job()'::regprocedure,
  'public.create_submission_enrichment_job()'::regprocedure,
  'public.enqueue_dish_enrichment()'::regprocedure,
  'public.protect_reviewed_taxonomy_value()'::regprocedure,
  'public.validate_current_taxonomy_assertion()'::regprocedure,
  'public.validate_dish_class_role()'::regprocedure
)
AND has_function_privilege(role_name, proc.oid, 'EXECUTE');

-- All application-schema, non-inherited foreign keys must have a valid non-partial leading index.
SELECT ns.nspname AS schema_name, rel.relname AS table_name, con.conname AS unindexed_fk
FROM pg_constraint con
JOIN pg_class rel ON rel.oid = con.conrelid
JOIN pg_namespace ns ON ns.oid = rel.relnamespace
WHERE con.contype = 'f'
  AND con.conparentid = 0
  AND ns.nspname IN ('public', 'food', 're_engine', 'ml', 'ops')
  AND NOT EXISTS (
    SELECT 1
    FROM pg_index existing_index
    WHERE existing_index.indrelid = con.conrelid
      AND existing_index.indisvalid
      AND existing_index.indisready
      AND existing_index.indpred IS NULL
      AND ARRAY(
        SELECT (existing_index.indkey::smallint[])[position]
        FROM generate_series(0, cardinality(con.conkey) - 1) AS position
      ) = con.conkey
  );

SELECT count(*) AS duplicate_indexes_remaining
FROM pg_indexes
WHERE schemaname = 'public'
  AND indexname IN ('never_list_profile_id_idx', 'idx_tags_vector_position');
