-- Immutable, DB-backed catalogue publication versions and the explicit human rollout gate.
--
-- Additive only. Does not touch public.dishes, the 810-dish fallback bundle, or any existing
-- serving path. re_engine.catalogue_publication_rows()/coverage() (097) remain the sole
-- eligibility source of truth this table copies from; this migration only gives publication a
-- durable, insert-only DB record instead of (or alongside) the file-based artifact already
-- produced by ops/recommendation/catalogue_publication.py, and a single governed switch that
-- decides whether any published version may ever reach live traffic.

CREATE SCHEMA IF NOT EXISTS re_engine;

-- One immutable row per published snapshot. Never UPDATEd or DELETEd once inserted — a new
-- publish always creates a new version row, never mutates an existing one (enforced below).
CREATE TABLE public.catalogue_versions (
  id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  publication_version text NOT NULL UNIQUE CHECK (publication_version ~ '^sha256:[0-9a-f]{64}$'),
  created_at          timestamptz NOT NULL DEFAULT now(),
  dish_count          integer NOT NULL CHECK (dish_count > 0),
  source_query        text NOT NULL DEFAULT 're_engine.catalogue_publication_rows',
  generated_by        text NOT NULL,
  notes               text
);

COMMENT ON TABLE public.catalogue_versions IS
  'Insert-only ledger of immutable catalogue publication snapshots. Never serves traffic by '
  'itself — see catalogue_rollout_state for the explicit human-controlled serving gate.';

-- One row per dish in a given published version. Insert-only, keyed by (version_id, dish_id).
CREATE TABLE public.catalogue_dishes (
  version_id uuid NOT NULL REFERENCES public.catalogue_versions(id),
  dish_id    uuid NOT NULL REFERENCES public.dishes(id),
  payload    jsonb NOT NULL,
  PRIMARY KEY (version_id, dish_id)
);

COMMENT ON TABLE public.catalogue_dishes IS
  'Immutable per-dish payload for one published catalogue_versions row. schema_version inside '
  'payload matches re_engine.catalogue_publication_rows() output (recommendation-catalogue-row-v1).';

CREATE INDEX IF NOT EXISTS catalogue_dishes_version_idx ON public.catalogue_dishes (version_id);

-- Immutability guard: block UPDATE and DELETE at the table level so "never mutate a published
-- version" is enforced by the database, not just by application discipline.
CREATE OR REPLACE FUNCTION re_engine.reject_catalogue_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  RAISE EXCEPTION 'catalogue publication rows are immutable; % is not permitted on %',
    TG_OP, TG_TABLE_NAME;
END;
$$;

CREATE TRIGGER catalogue_versions_immutable
  BEFORE UPDATE OR DELETE ON public.catalogue_versions
  FOR EACH ROW EXECUTE FUNCTION re_engine.reject_catalogue_mutation();

CREATE TRIGGER catalogue_dishes_immutable
  BEFORE UPDATE OR DELETE ON public.catalogue_dishes
  FOR EACH ROW EXECUTE FUNCTION re_engine.reject_catalogue_mutation();

REVOKE ALL ON public.catalogue_versions FROM PUBLIC, anon, authenticated;
REVOKE ALL ON public.catalogue_dishes FROM PUBLIC, anon, authenticated;
GRANT SELECT, INSERT ON public.catalogue_versions TO service_role;
GRANT SELECT, INSERT ON public.catalogue_dishes TO service_role;

-- Single-row explicit human rollout gate. Defaults to OFF: compute and store every published
-- version, but the existing 810-dish fallback bundle stays the only thing that ever serves
-- live traffic until a human flips this row to SHADOW, CANARY, or LIVE.
CREATE TABLE public.catalogue_rollout_state (
  id               boolean PRIMARY KEY DEFAULT true CHECK (id),
  mode             text NOT NULL DEFAULT 'OFF' CHECK (mode IN ('OFF', 'SHADOW', 'CANARY', 'LIVE')),
  active_version_id uuid REFERENCES public.catalogue_versions(id),
  updated_at       timestamptz NOT NULL DEFAULT now(),
  updated_by       text NOT NULL DEFAULT 'system_default',
  CHECK (mode = 'OFF' OR active_version_id IS NOT NULL)
);

COMMENT ON TABLE public.catalogue_rollout_state IS
  'Single-row explicit rollout gate for the DB-backed catalogue. OFF (default) = compute and '
  'store published versions but never serve them; the 810-dish fallback bundle keeps serving. '
  'A human (Founder/on-call) must explicitly move this to SHADOW/CANARY/LIVE and name an '
  'active_version_id before any published version can influence Ghar, Aux, or Qdrant serving.';

INSERT INTO public.catalogue_rollout_state (id, mode, active_version_id, updated_by)
VALUES (true, 'OFF', NULL, 'migration_102_default')
ON CONFLICT (id) DO NOTHING;

REVOKE ALL ON public.catalogue_rollout_state FROM PUBLIC, anon, authenticated;
GRANT SELECT ON public.catalogue_rollout_state TO authenticated;
GRANT SELECT, UPDATE ON public.catalogue_rollout_state TO service_role;
