-- Auditable one-way legacy migration and cache-invalidation control plane.
CREATE TABLE ontology.cutover_runs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  source_system text NOT NULL,
  source_watermark timestamptz NOT NULL,
  export_sha256 text NOT NULL CHECK (export_sha256 ~ '^[a-f0-9]{64}$'),
  status text NOT NULL CHECK (status IN ('importing','imported','reconciled','failed')),
  report jsonb NOT NULL DEFAULT '{}',
  created_at timestamptz NOT NULL DEFAULT now(),
  completed_at timestamptz,
  UNIQUE (source_system,export_sha256)
);

CREATE TABLE ontology.legacy_identity_map (
  source_system text NOT NULL,
  entity_type text NOT NULL,
  legacy_id text NOT NULL,
  service_id uuid NOT NULL,
  cutover_run_id uuid NOT NULL REFERENCES ontology.cutover_runs(id) ON DELETE RESTRICT,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (source_system,entity_type,legacy_id),
  UNIQUE (source_system,entity_type,service_id)
);

CREATE TABLE ontology.cache_invalidation_events (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  namespace text NOT NULL,
  resource_key text NOT NULL,
  reason text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX cache_invalidation_events_cursor ON ontology.cache_invalidation_events(id);

CREATE FUNCTION ontology.emit_dish_cache_invalidation() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE target_id uuid;
BEGIN
  target_id := coalesce(NEW.dish_id, OLD.dish_id);
  INSERT INTO ontology.cache_invalidation_events(namespace,resource_key,reason)
  VALUES('dish',target_id::text,TG_TABLE_NAME || ':' || TG_OP),
        ('classes','all',TG_TABLE_NAME || ':' || TG_OP);
  RETURN coalesce(NEW,OLD);
END $$;

CREATE TRIGGER assertions_cache_invalidation AFTER INSERT OR UPDATE ON ontology.current_field_values
FOR EACH ROW EXECUTE FUNCTION ontology.emit_dish_cache_invalidation();
CREATE TRIGGER class_memberships_cache_invalidation AFTER INSERT OR UPDATE OR DELETE ON ontology.dish_class_memberships
FOR EACH ROW EXECUTE FUNCTION ontology.emit_dish_cache_invalidation();
CREATE TRIGGER dish_images_cache_invalidation AFTER INSERT OR UPDATE OR DELETE ON ontology.dish_images
FOR EACH ROW EXECUTE FUNCTION ontology.emit_dish_cache_invalidation();

CREATE FUNCTION ontology.emit_dish_row_cache_invalidation() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  INSERT INTO ontology.cache_invalidation_events(namespace,resource_key,reason)
  VALUES('dish',coalesce(NEW.id,OLD.id)::text,'dishes:' || TG_OP);
  RETURN coalesce(NEW,OLD);
END $$;
CREATE TRIGGER dishes_cache_invalidation AFTER INSERT OR UPDATE OR DELETE ON ontology.dishes
FOR EACH ROW EXECUTE FUNCTION ontology.emit_dish_row_cache_invalidation();
