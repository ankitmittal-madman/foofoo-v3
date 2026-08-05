-- Restore the exact privilege and duplicate-index state that preceded migration 057.

GRANT EXECUTE ON FUNCTION public.create_dish_enrichment_job() TO PUBLIC;
GRANT EXECUTE ON FUNCTION public.create_submission_enrichment_job() TO PUBLIC;
GRANT EXECUTE ON FUNCTION public.enqueue_dish_enrichment() TO PUBLIC;
GRANT EXECUTE ON FUNCTION public.protect_reviewed_taxonomy_value() TO PUBLIC;
GRANT EXECUTE ON FUNCTION public.validate_current_taxonomy_assertion() TO PUBLIC;
GRANT EXECUTE ON FUNCTION public.validate_dish_class_role() TO PUBLIC;

DO $rollback$
DECLARE
  fk record;
  index_name text;
BEGIN
  FOR fk IN
    SELECT
      con.conname,
      ns.nspname AS schema_name,
      rel.relname AS table_name,
      array_agg(att.attname ORDER BY key_column.ordinality) AS column_names
    FROM pg_constraint con
    JOIN pg_class rel ON rel.oid = con.conrelid
    JOIN pg_namespace ns ON ns.oid = rel.relnamespace
    CROSS JOIN LATERAL unnest(con.conkey) WITH ORDINALITY AS key_column(attnum, ordinality)
    JOIN pg_attribute att ON att.attrelid = con.conrelid AND att.attnum = key_column.attnum
    WHERE con.contype = 'f'
      AND con.conparentid = 0
      AND ns.nspname IN ('public', 'food', 're_engine', 'ml', 'ops')
    GROUP BY con.oid, con.conname, ns.nspname, rel.relname
  LOOP
    index_name := format(
      'idx_%s_%s_fk',
      fk.table_name,
      array_to_string(fk.column_names, '_')
    );
    IF length(index_name) > 63 THEN
      index_name := left(index_name, 54) || '_' || left(md5(fk.conname), 8);
    END IF;
    EXECUTE format('DROP INDEX IF EXISTS %I.%I', fk.schema_name, index_name);
  END LOOP;
END
$rollback$;

CREATE INDEX IF NOT EXISTS never_list_profile_id_idx
  ON public.never_list (profile_id) WHERE is_active = true;
CREATE UNIQUE INDEX IF NOT EXISTS idx_tags_vector_position
  ON public.tags (vector_position);
