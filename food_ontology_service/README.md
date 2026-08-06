# Foofoo Food Ontology Service

Independent API boundary for canonical dishes, meal taxonomy, enrichment, similarity, provenance,
review and Cloudinary references. It does not contain household/recommendation logic and the main
Foofoo app must not connect to its database.

The checked-in `MemoryRepository` makes contract tests and local API exploration deterministic.
When `ONTOLOGY_DATABASE_URL` is set, the API selects `PostgresRepository`; production fails closed
without that setting. The normalized schema, atomic idempotency records, lease queue and immutable
review decisions are in
[food_ontology_service/migrations/001_create_ontology_schema.sql](food_ontology_service/migrations/001_create_ontology_schema.sql).

Run locally:

```bash
pip install -e 'food_ontology_service[test]'
uvicorn food_ontology_service.main:app --app-dir food_ontology_service
```

Apply migrations and run a worker deployment independently:

```bash
foofoo-ontology-migrate
ONTOLOGY_WORKER_HANDLER_FACTORY='your_package.handlers:build_handlers' foofoo-ontology-worker
```

The migration runner serializes deploys with an advisory lock, records SHA-256 checksums and fails
if an applied migration was edited. The worker claims bounded batches with `SKIP LOCKED`, uses
five-minute leases, completes or reviews successful jobs, retries failures exponentially and
dead-letters exhausted or unsupported jobs. Provider, similarity, image and publication handlers
are injected by the worker deployment; startup fails rather than silently completing jobs when no
handler factory is configured.

Local bearer token: `local-ontology-token`. Production startup fails unless
`ONTOLOGY_SERVICE_TOKENS` supplies named tokens and scopes. Write-triggering endpoints require an
`Idempotency-Key`. All enrichment/classification routes return `202`; workers, not HTTP requests,
call external providers.

Real PostgreSQL tests are opt-in and apply the migration to a disposable database:

```bash
ONTOLOGY_TEST_DSN='postgresql://...' PYTHONPATH=food_ontology_service \
  python -m pytest food_ontology_service/tests -q
```

Production scopes are `ontology:read` (app reads), `ontology:write` (controlled intake/feedback),
and `ontology:admin` (review, relationships and image publication). Prefer short-lived OAuth2
client-credential tokens at the gateway; the opaque token implementation is the deployable first
step and retains the same scope boundary.
