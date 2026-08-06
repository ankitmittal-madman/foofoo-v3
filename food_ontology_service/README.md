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
foofoo-ontology-worker
```

The migration runner serializes deploys with an advisory lock, records SHA-256 checksums and fails
if an applied migration was edited. The worker claims bounded batches with `SKIP LOCKED`, uses
five-minute leases, completes or reviews successful jobs, retries failures exponentially and
dead-letters exhausted or unsupported jobs. The default factory performs real FoodOn and Wikidata
enrichment, enables exact-match-only USDA nutrition when `ONTOLOGY_USDA_API_KEY` is present, and
applies reviewed rules from `ONTOLOGY_CLASSIFICATION_RULES_JSON`. Low-confidence and
safety-sensitive results remain review-only, and accepted values are never overwritten. Custom
factories remain supported for similarity, image and publication deployments.

Create a watermarked export, idempotently import it, and produce a reconciliation report:

```bash
foofoo-ontology-cutover export --source-dsn "$LEGACY_DATABASE_URL" --output export.json
foofoo-ontology-cutover import --target-dsn "$ONTOLOGY_DATABASE_URL" --input export.json
foofoo-ontology-cutover reconcile --target-dsn "$ONTOLOGY_DATABASE_URL" \
  --input export.json --report reconciliation.json
```

Reconciliation fails closed on identity/count drift, name collisions, class-role violations,
missing evidence pointers, unresolved submission jobs, and image rows without migratable
Cloudinary identity/checksum metadata. Workers consume durable invalidation events and advance
Redis namespace versions when both Redis REST settings are present.

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

The Supabase gateway supports `FOOD_ONTOLOGY_READ_MODE=legacy|shadow|service`; `legacy` is the safe
default. Shadow mode records parity without changing responses. Production service mode requires
the ontology URL/token and Redis REST URL/token. Metrics cover routing, origin latency, cache
hits/errors and shadow parity. The service exposes authenticated Prometheus metrics at `/metrics`
and propagates `x-request-id` and W3C `traceparent` context.
