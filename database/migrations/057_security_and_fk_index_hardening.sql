-- Close post-056 advisor findings without widening any client data access.
--
-- 1. Ontology trigger functions are implementation details, not public RPCs. PostgreSQL trigger
--    execution does not require the invoking role to hold EXECUTE on the trigger function.
-- 2. Every non-inherited FK in application schemas receives a non-partial leading index only when
--    no valid covering index already exists. Parent partition indexes propagate to partitions.
-- 3. Two byte-for-byte duplicate indexes reported by the production advisor are removed.

SET lock_timeout = '5s';
SET statement_timeout = '5min';

REVOKE EXECUTE ON FUNCTION public.create_dish_enrichment_job() FROM PUBLIC, anon, authenticated;
REVOKE EXECUTE ON FUNCTION public.create_submission_enrichment_job() FROM PUBLIC, anon, authenticated;
REVOKE EXECUTE ON FUNCTION public.enqueue_dish_enrichment() FROM PUBLIC, anon, authenticated;
REVOKE EXECUTE ON FUNCTION public.protect_reviewed_taxonomy_value() FROM PUBLIC, anon, authenticated;
REVOKE EXECUTE ON FUNCTION public.validate_current_taxonomy_assertion() FROM PUBLIC, anon, authenticated;
REVOKE EXECUTE ON FUNCTION public.validate_dish_class_role() FROM PUBLIC, anon, authenticated;

DO $migration$
DECLARE
  fk record;
  index_name text;
  index_columns text;
BEGIN
  FOR fk IN
    SELECT
      con.oid,
      con.conrelid,
      con.conname,
      ns.nspname AS schema_name,
      rel.relname AS table_name,
      con.conkey,
      array_agg(att.attname ORDER BY key_column.ordinality) AS column_names
    FROM pg_constraint con
    JOIN pg_class rel ON rel.oid = con.conrelid
    JOIN pg_namespace ns ON ns.oid = rel.relnamespace
    CROSS JOIN LATERAL unnest(con.conkey) WITH ORDINALITY AS key_column(attnum, ordinality)
    JOIN pg_attribute att ON att.attrelid = con.conrelid AND att.attnum = key_column.attnum
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
      )
    GROUP BY con.oid, con.conrelid, con.conname, ns.nspname, rel.relname, con.conkey
    ORDER BY ns.nspname, rel.relname, con.conname
  LOOP
    index_name := format(
      'idx_%s_%s_fk',
      fk.table_name,
      array_to_string(fk.column_names, '_')
    );
    IF length(index_name) > 63 THEN
      index_name := left(index_name, 54) || '_' || left(md5(fk.conname), 8);
    END IF;

    SELECT string_agg(format('%I', column_name), ', ')
      INTO index_columns
      FROM unnest(fk.column_names) AS column_name;

    EXECUTE format(
      'CREATE INDEX IF NOT EXISTS %I ON %I.%I (%s)',
      index_name,
      fk.schema_name,
      fk.table_name,
      index_columns
    );
  END LOOP;
END
$migration$;

-- Keep the purpose-specific partial index and the constraint-owned unique index.
DROP INDEX IF EXISTS public.never_list_profile_id_idx;
DROP INDEX IF EXISTS public.idx_tags_vector_position;

RESET statement_timeout;
RESET lock_timeout;
