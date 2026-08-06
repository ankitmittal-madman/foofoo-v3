# Food Ontology Service Cutover Runbook

**Status:** ACTIVE
**Version:** 1.1
**Date:** 2026-08-06

## Current verified milestone

The service boundary, normalized PostgreSQL repository, checksum-pinned migration runner,
production enrichment/classification handlers, one-way cutover tooling, distributed cache
invalidation, gateway routing modes and telemetry are implemented. The legacy intake returns `202` after its
durable database trigger queues work; it no longer calls external providers in the request path.
Ghar RE still consumes the immutable ontology snapshot and preserves class-first planning.

This milestone does **not** authorize production traffic cutover. Existing ontology truth remains
in Supabase until the copy/reconciliation and shadow-read gates below pass.

## Deployment order

1. Provision an independent PostgreSQL database and separate API, worker and migration roles.
2. Store `ONTOLOGY_DATABASE_URL` and scoped service tokens in the deployment secret manager.
3. Run `foofoo-ontology-migrate` with the migration role. Re-running must apply zero migrations;
   a checksum mismatch is a release failure.
4. Start the API and require `/readyz` to report `database=postgres`.
5. Deploy workers with reviewed `ONTOLOGY_CLASSIFICATION_RULES_JSON`, provider credentials and,
   when distributed caching is enabled, both Redis REST settings. Start with one small batch. No
   main-app credential may be present in the worker environment.
6. Run `foofoo-ontology-cutover export` against Supabase. Preserve its SHA-256 bundle.
7. Run `foofoo-ontology-cutover import` against the independent database. A repeat must report
   `replayed=true` and import zero additional dishes.
8. Run `foofoo-ontology-cutover reconcile`; archive the JSON report beside the export. `passed`
   must be true before enabling shadow reads.
9. Configure the Edge gateway first with `FOOD_ONTOLOGY_READ_MODE=shadow`, the scoped service
   URL/token, and Redis REST URL/token. `legacy` remains the default and rollback value.

## Mandatory reconciliation gates

- Every active legacy dish maps to exactly one service dish or an explicit reviewed merge.
- Canonical normalized-name collisions are zero or explicitly adjudicated.
- Accepted alias, class, constraint and regional assertion counts/checksums match the export.
- Every class mapping references an active class and passes the database planning-role trigger.
- Primary reads never return add-on or combo-component memberships; add-on reads never return
  primary memberships.
- Every current field pointer references an assertion for the same dish and has evidence.
- Every approved primary image has a Cloudinary public ID, checksum and accepted moderation state.
- Queue leases, retry counts and dead-letter rows reconcile without duplicating active work.
- A generated catalogue snapshot passes the existing 810-dish compatibility and golden Ghar RE
  tests before publication.

## Traffic cutover

1. Shadow the service reads from the app boundary and compare canonical IDs, class candidates,
   provenance and image references. Record mismatch metrics; do not silently fall back on writes.
2. Dual-publish changes through an outbox/CDC bridge for a bounded migration window. Supabase stays
   authoritative during this window; never establish permanent bidirectional truth.
3. Freeze ontology admin writes briefly, drain the bridge, repeat reconciliation and publish one
   content-addressed snapshot.
4. Switch app reads and submissions to the ontology API. Keep Ghar RE on the validated snapshot,
   not per-candidate live API calls.
5. Observe API errors/latency, cache hits, queue age, provider failures, review backlog and class
   candidate parity for at least one full enrichment cycle.
6. Revoke main-app access to ontology tables and disable `cron-dish-ontology` only after the
   rollback window closes.

Gateway transitions are one-way gates per rehearsal: `legacy -> shadow -> service`. Never skip
shadow mode. `service` fails closed on origin errors; only shadow mode contains failures and returns
the authoritative legacy response. Redis failures are cache misses, not ontology failures.
Database mutations emit durable events; workers advance `dish` and `classes` namespace versions,
making old cache entries unreachable without unsafe wildcard deletion.

## Rollback

- Route app reads/submissions back to the legacy boundary.
- Stop new ontology workers without deleting jobs; leases expire and remain auditable.
- Repoint Ghar RE to the previous content-addressed snapshot.
- Keep the independent database for diagnosis. Never delete migrated evidence, assertions,
  decisions or job attempts during rollback.

## Remaining implementation before cutover

- Build similarity, image/Cloudinary and catalogue-publication handlers.
- Replace opaque service tokens with OAuth2 client credentials and add gateway-specific rate limits.
- Wire trace propagation and Prometheus/log metrics to the production collector and alert policies;
  validate dashboards for cache, provider, queue, review and parity signals.
- Adjudicate every export image blocker and active submission job reported by reconciliation.
- Run backup/restore, key rotation, provider-outage and snapshot rollback exercises.
