# Foofoo Food Ontology Service

Independent API boundary for canonical dishes, meal taxonomy, enrichment, similarity, provenance,
review and Cloudinary references. It does not contain household/recommendation logic and the main
Foofoo app must not connect to its database.

The checked-in `MemoryRepository` makes contract tests and local API exploration deterministic.
The production schema is [migrations/001_create_ontology_schema.sql](migrations/001_create_ontology_schema.sql);
the next cutover increment wires its PostgreSQL repository and queue consumer before traffic moves.

Run locally:

```bash
pip install -e 'food_ontology_service[test]'
uvicorn food_ontology_service.main:app --app-dir food_ontology_service
```

Local bearer token: `local-ontology-token`. Production startup fails unless
`ONTOLOGY_SERVICE_TOKENS` supplies named tokens and scopes. Write-triggering endpoints require an
`Idempotency-Key`. All enrichment/classification routes return `202`; workers, not HTTP requests,
call external providers.

Production scopes are `ontology:read` (app reads), `ontology:write` (controlled intake/feedback),
and `ontology:admin` (review, relationships and image publication). Prefer short-lived OAuth2
client-credential tokens at the gateway; the opaque token implementation is the deployable first
step and retains the same scope boundary.
