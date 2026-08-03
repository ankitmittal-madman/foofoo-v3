# [ACTIVE]_REPO-CERT-030_WP-21_Ghar_Re_Schema_Retirement_v1.0

**Status:** ACTIVE
**Version:** v1.0
**Date:** 2026-08-03
**Placement:** docs/project-history/certificates/[ACTIVE]_REPO-CERT-030_WP-21_Ghar_Re_Schema_Retirement_v1.0.md
**Certifies:** WP-21's `ghar_re` Postgres schema retirement (migration `050_drop_unused_ghar_re_schema.sql`) — FULL execution against production. WP-21 v1.0 had prepared this migration and its rollback but could not apply it ("no DB write credentials available this session"); this session had Founder-supplied credentials and executed it.
**Supersedes:** N/A
**Dependencies:** `docs/project-history/work-packages/[DRAFT]_WP-21_Production_Hardening_Audit_v1.0.md` §2 (the Founder decision and pre-migration verification this certificate executes)

---

## What this certifies

### Pre-execution verification (this session, not assumed from WP-21's write-up)
- Re-confirmed live, via direct `psql` query against the production database
  (`cmkswalqpmmqojwdmqbv`), that the `ghar_re` schema still existed with all 28 tables
  immediately before this session's action — i.e. migration 050 had been written but never
  actually run.
- Independently re-derived (in an earlier part of this same session, before finding WP-21's
  own write-up) that no currently-deployed runtime code path reads `ghar_re.*`: the
  `recommendations` Edge Function and the live Fly.io RE service (`ghar_re_service`) both
  read from `public.*` / a build-time JSON bundle respectively, never from this schema.
  This matches WP-21's own independent verification — two separate checks, same conclusion.
- An earlier plan in this session to drop only `ghar_re.dishes` (not the whole schema) was
  reversed after finding real FK-dependent tables inside `ghar_re` itself
  (`dish_pairing_penalties`, `dish_safety_flags`, `dish_name_synonyms`). WP-21's decision to
  retire the *entire* schema in one `DROP SCHEMA ... CASCADE`, rather than individual tables,
  is the correct approach given those internal dependencies — confirmed, not just accepted.

### Backup taken before any destructive action
`pg_dump` (Postgres 17.10 client, required — the CLI's bundled 15.6/16.14 clients refused with
a server-version-mismatch guard against the live server's Postgres 17.6) against the live
project, schema-scoped to `ghar_re`, schema **and data**:
`database/archive/ghar_re_backup_20260803/ghar_re_schema_and_data.sql` — verified 2,217 lines,
28 `CREATE TABLE` statements, 28 matching `COPY` (data) blocks, one per table. This is a real
data snapshot, not a structure-only dump — if recovery is ever needed, this file (not
migration 050's rollback, which is intentionally a no-op pointing here) is the actual recovery
path.

### Execution
Migration `050_drop_unused_ghar_re_schema.sql` (`DROP SCHEMA IF EXISTS ghar_re CASCADE`, inside
`BEGIN`/`COMMIT`) run by the Founder directly via the Supabase Dashboard SQL Editor against the
live project, after this session prepared and verified everything else. Confirmed post-run, via
this session's own direct `psql` query: `SELECT nspname FROM pg_namespace WHERE
nspname='ghar_re'` → **0 rows.** The schema and all 28 tables are gone from production.

### Scope not touched by this action
- `public.dishes` (802 rows) — untouched, unrelated schema, still the app's content-layer table.
- The live RE's actual catalogue source (`ghar_re_service/data/bundle/catalogue.json`, 810
  dishes from `dishes.xlsx`) — untouched, was never in Postgres to begin with.
- `database/validation/906_ghar_re_validation.sql` / `907_dish_ontology_validation.sql` and
  `supabase/config.toml`'s `schemas` list — already handled by the session that wrote WP-21 and
  migration 050; re-confirmed present/correct in this session, not re-done.

## Critical Self-Review
- **This was a real, irreversible production action.** The Founder supplied the database
  password directly in this conversation to enable it; used only as an environment variable for
  the exact `pg_dump`/`psql` commands that needed it, never echoed, logged, or written to any
  file.
- **The actual `DROP SCHEMA` was run by the Founder, not by this session directly** — an earlier
  attempt to run it via an agent-issued `psql` command was blocked by the harness's own
  permission classifier (a production DDL statement), and rather than seek a workaround, this
  session handed the exact command to the Founder to execute and independently re-verified the
  result afterward via a separate read-only query. That verification (0 rows) is this
  certificate's actual evidence, not the Founder's own report of success.
- **The backup's completeness was checked by line/table count, not by a restore test.** A
  from-backup restore into a scratch database was not performed this session — if this backup is
  ever needed, its first real use will be that restore, unverified until then.

## Versioning & Placement
v1.0, first issue. Companion: `[DRAFT]_WP-21_Production_Hardening_Audit_v1.0.md` §2 (the
decision and pre-migration prep this certifies the execution of); `database/migrations/
050_drop_unused_ghar_re_schema.sql` + its rollback; `database/archive/
ghar_re_backup_20260803/ghar_re_schema_and_data.sql` (the real recovery path).

## Founder Sign-off

