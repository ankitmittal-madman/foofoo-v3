# Food Ontology Microservice — Deep Review and Target Architecture

**Status:** ACTIVE  
**Version:** 1.0  
**Date:** 2026-08-06  
**Decision:** Extract food ontology into an independently deployed service and database. Keep
class-first recommendation math in Ghar RE and publish versioned ontology snapshots to it.

## A. Executive assessment

The ontology materially strengthens recommendations. Class membership, Food DNA, region, diet,
ingredients, constraints and similarity improve cold start, candidate recall, variety,
substitution and explanations. It is worth building now, but the deployment boundary needs
redesign before the 6,871-row ingestion is treated as production architecture.

The existing domain model is substantially reusable. The principal problem is ownership: ontology
tables, enrichment workers and provider calls currently live beside the main app data in Supabase.
`POST /v1/dish-ontology` also calls FoodOn/USDA before returning, and the ingestion pipeline may
call prompt generation, Pollinations and Cloudinary inside a database transaction. Both violate
the required failure and latency boundary.

Target outcome:

`Foofoo app -> cached /v1 ontology API -> ontology DB`

`sources -> isolated workers/queues -> evidence -> assertions/review -> published snapshot -> Ghar RE`

This can reach consumer-app dish-page depth, but not from a single free source. Richness comes from
merging licensed/open recipe data, FoodOn/Wikidata aliases, recipe-derived ingredients and methods,
Indian nutrition references, controlled inference, internal research and reviewed image assets.
Safety facts must never be inferred from provider absence or generative output.

## B. Current-state audit

### Reuse

- `public.dishes`, meal classes, class families, class hierarchy and `planning_role` already encode
  class-first planning and explicit add-on/combo separation.
- Migrations 056–072 provide staged source records, per-field assertions/current pointers,
  confidence, provenance, leases, retries, review tasks, Food DNA terms, graph edges, nutrition,
  recipes, catalogue publication and AI lineage.
- `food.ontology_nodes/edges` support aliases, variants, region, substitution, pairing and similar
  dishes without requiring a graph database.
- The 810-dish immutable `food_ontology_snapshot.json` is already consumed by Ghar RE and has
  compatibility tests. This is the correct recommendation integration seam.
- Migration 076 has useful import-run/source-row/result/error audit records. Migration 077 records
  prompt and image-model provenance.

### Replace or consolidate

- Move ontology-owned tables out of the main app database into the service database. During
  migration, a physically isolated `ontology` database/schema is acceptable; the steady state is
  independent credentials, backups, migrations and deployment.
- Replace the action-switched `POST /v1/dish-ontology` with resource-oriented `/v1` endpoints and
  scoped service credentials. The main app must not have ontology database credentials.
- Submission must enqueue and return `202`; external calls must never occur in the request.
- Consolidate `dish_aliases` and `dish_name_synonyms` behind one canonical alias entity with an
  evidence link and alias kind. The current duplication is understandable ingestion history, not
  a desirable final model.
- Consolidate ingestion and taxonomy review into one review-task model with `workflow_type`, while
  retaining distinct reason codes and SLAs.
- Stop writing source course codes into `dishes.meal_occasion`; source-shaped values belong only
  in staging/evidence.
- Move image generation/upload outside ingestion transactions. A successful Cloudinary upload is
  followed by a short idempotent metadata transaction.
- Retire Supabase `cron-dish-ontology` after traffic and data cutover. Until then it is a migration
  bridge, not the target worker.

### Missing

- A standalone ontology deployment, scoped API contract, read cache, explicit correction/feedback
  contract, similarity-builder job, image moderation/licence fields, and measured completeness and
  recommendation-quality gates.
- City/state/country entities should replace free-text region codes. Assertions should target
  stable region IDs and retain the source's original label.
- Field policies need freshness windows in addition to publication confidence/risk.

## C. Target architecture and boundary

| Layer | Responsibility | Store/compute |
|---|---|---|
| API | validation, auth scopes, idempotency, ETags, rate limits | stateless service |
| Source/staging | immutable imports, provider responses, user corrections | ontology DB |
| Canonical domain | dishes, aliases, classes, regions, tags, ingredients, recipes | ontology DB |
| Evidence/governance | assertions, sources, confidence, review decisions, policy | ontology DB |
| Runtime output | published dish detail, class candidates, similarity, image refs | read model + cache |
| Jobs | enrichment, normalization, similarity, image, publish | durable queue/workers |
| Recommendation | class selection/ranking and household policy | Ghar RE, not ontology service |

Workers use leases or a real queue, bounded concurrency, timeouts, exponential backoff with jitter,
circuit breakers and provider-specific token buckets. Raw payloads are encrypted/retained under a
policy and never returned to app clients. OpenTelemetry traces connect request, job, evidence,
assertion, review and snapshot IDs. Metrics cover queue age, provider error/rate, confidence,
review backlog, cache hit rate, publication lag and per-field coverage.

The ontology service emits a content-addressed `catalogue.published` snapshot/event. Ghar RE loads
only a validated immutable snapshot at startup and rolls back by version. It does not call the
ontology API once per candidate during recommendation requests.

## D. Canonical data model

- `dish`: stable ID, canonical name, locale, description, lifecycle and merge target.
- `dish_alias`: normalized text, language/script, alias kind, region scope; uniqueness on
  normalized alias + locale, with ambiguity represented explicitly.
- `meal_class`, `meal_class_edge`, `dish_class_membership`: slot, role
  (`primary|addon|combo_component`), strength, confidence and evidence.
- `region`, `cuisine`, `dish_region_affinity`: typed hierarchy and affinity.
- `ingredient`, `ingredient_form`, `recipe`, `recipe_ingredient`, `recipe_step`.
- `taxonomy_term`, `dish_term_assertion`: Food DNA dimensions including diet, method, spice,
  richness, heaviness, texture, slot, season, weather, occasion and festival.
- `dish_relationship`: `same_as|variant_of|parent_of|sibling_of|similar_to|substitute_for`, directed
  where appropriate, score, explanation features, confidence and evidence.
- `nutrient_assertion`: value/range, unit, serving basis and method. No dish-level nutrition may be
  copied from a merely similar external food.
- `source_record`, `assertion`, `assertion_evidence`, `current_field_value`: field-level lineage.
- `review_task`, append-only `review_decision`, `field_policy`.
- `image_asset`, `dish_image`: Cloudinary public ID/version, source/licence/attribution, checksum,
  perceptual hash, moderation state, prompt/model/seed, dimensions, primary role and confidence.
- `job`, `job_attempt`, `provider_checkpoint`, `catalogue_version`, `idempotency_record`.

Accepted human values are never overwritten. New evidence creates a new assertion; policy or a
review decision moves the current pointer. Merges preserve redirect IDs and all historical edges.

## E. Free-source evaluation

| Source | Contribution | Limits | Role |
|---|---|---|---|
| Foofoo research/catalogue | class taxonomy, Food DNA, Indian household semantics | must be governed/versioned | canonical for Foofoo classes |
| [FoodOn via EBI OLS](https://foodon.org/) | food concepts, IDs, synonyms (CC BY 4.0) | weak prepared-dish and regional coverage | supporting identity evidence |
| [Wikidata](https://www.wikidata.org/wiki/Wikidata:Licensing)/Wikipedia APIs | CC0 structured aliases, multilingual names and origin; separately licensed text/media | community quality; text/media licences vary | supporting/fallback, field cited |
| [USDA FoodData Central](https://fdc.nal.usda.gov/api-guide/) | CC0 nutrients and ingredients; free keyed API | weak Indian dish matching; serving mismatch | supporting, exact/recipe match only |
| Indian Food Composition Tables | Indian ingredient nutrition | licensing/distribution must be confirmed | canonical ingredient evidence when permitted |
| [Open Food Facts](https://openfoodfacts.github.io/documentation/docs/Product-Opener/api/) | ODbL packaged-food/barcode facts and images | not household prepared-dish truth; ODbL obligations need architectural review | packaged-food fallback only |
| Recipe1M+/RecipeNLG/open recipe corpora | ingredient/method priors | licence and Indian coverage vary | offline supporting evidence only |
| Published academic Indian recipe datasets | regional recipes/classification evaluation | inconsistent licences/schemas | offline evaluation/support only |
| [Wikimedia Commons](https://commons.wikimedia.org/wiki/Commons:Reusing_content_outside_Wikimedia/en) | openly licensed images | each file's licence/attribution and dish match must be checked | preferred sourced image pool |

Do not scrape Tasty, Zomato, Swiggy or recipe sites merely because pages are public. Accessibility
is not a reuse licence. Keep a source registry with licence, allowed uses, attribution, rate policy
and retention policy; disable an adapter when those facts are unknown.

## F. Daily incremental enrichment

Compute priority per field, not just per dish:

`priority = new-item + safety-gap + required-page-gap + low-confidence + stale + user-correction - stability`

- New submissions enqueue immediately; the API returns `202` and a status URL.
- Daily scheduler selects due work with a global cap and provider caps. It first handles safety
  review gaps, then newly published dishes, low-confidence required fields, stale evidence and
  optional richness fields.
- Example freshness: aliases/regions 180 days, recipe/description 365 days, provider nutrition 180
  days, images 365 days or on moderation failure. Internal accepted taxonomy is event-refreshed,
  not blindly time-expired.
- Confidence `<0.65` stays evidence-only; `0.65–0.84` queues review for product-visible fields;
  `>=0.85` may auto-publish only for low-risk allowlisted fields. Diet/allergen/medical/religious
  safety requires deterministic evidence policy or human acceptance regardless of model score.
- Skip a field when its accepted assertion is unexpired and no newer source/correction exists.
- Claim with `SKIP LOCKED`, 5-minute leases, deterministic idempotency keys and max attempts.
  Provider outage opens a circuit and reschedules; it never fails app reads.
- Similarity recomputes only for changed embeddings/features and affected neighbours. Catalogue
  publication follows schema, coverage, add-on, allergen and regression gates.

## G. Recommendation connection

The ontology does not replace Ghar RE. It publishes class membership and ranking features:

1. Ghar RE selects eligible primary classes from household, slot and plan policy.
2. The snapshot expands only reviewed class-bound dishes; add-on roles are a separate query/pool.
3. Hard diet/allergy/Jain constraints run before ranking.
4. Ranker uses region, cuisine, Food DNA, weather/season, effort, nutrition overlay, recent variety
   and feedback-derived affinity.
5. Explanations cite selected features (for example class fit + regional affinity), not opaque AI
   prose.
6. If a candidate is unavailable, reviewed `substitute_for`/`similar_to` neighbours from another
   region are filtered through the same hard constraints before ranking.

Evaluate offline on class recall@K, hard-filter violations (target zero), regional NDCG, diversity,
substitution acceptance, cold-start saves and explanation coverage; then use a guarded A/B test on
save/cook/replace/regret outcomes. Ontology version must be logged with every recommendation.

## H. Image and Cloudinary flow

`image-needed event -> licensed-source search -> validate licence/content -> optional generation ->
moderation/dedupe -> Cloudinary upload -> metadata commit -> cache invalidation`

Workers validate MIME, dimensions, size, checksum, perceptual duplicates and dish relevance.
Cloudinary credentials belong only to the image worker. Use deterministic public IDs such as
`dishes/{dish_id}/{content_hash}`, signed uploads, versioned delivery URLs and eager transforms.
Persist public ID, asset ID, version, secure URL, checksum, attribution/licence, prompt/model/seed,
moderation/review and timestamps. Never store only a mutable URL. A failed upload leaves the job
retryable and does not create a live dish link. The API returns an approved primary, then approved
fallback, then a class/cuisine placeholder or `null`.

## I. Risks and controls

- Free sources do not provide authoritative Indian meal-class semantics: Foofoo owns and reviews it.
- Transliteration and regional names create false merges: conservative thresholds and ambiguous
  alias sets route to review.
- Generated images can misrepresent a dish: labelled provenance, relevance/moderation checks and
  human review for primary imagery.
- Provider and free-tier instability: cache, caps, circuits, checkpoints and source diversity.
- Recommendation drift: immutable snapshots, shadow evaluation, outcome monitoring and rollback.
- Rich metadata can look more certain than it is: surface confidence internally and only publish
  fields meeting policy.
- Dual writes during extraction can diverge: outbox/change-data capture, reconciliation and a
  time-bounded cutover; do not maintain permanent bidirectional truth.

## J. Prioritized implementation and validation

### Phase 0 — boundary and safety (now)

1. Stand up `food_ontology_service` with its own credentials/schema, versioned API, scoped tokens,
   idempotent writes and async job records.
2. Change app dish submission to enqueue only. Disable synchronous provider calls.
3. Move image/provider work out of ingestion transactions.
4. Pin existing Ghar RE snapshot behaviour and add contract tests for primary/add-on separation.

### Phase 1 — migrate and publish

Export/copy canonical records and evidence, reconcile counts/checksums, switch reads to the service,
then revoke app access to ontology tables. Build snapshot publication with schema, safety,
referential-integrity and golden-recommendation gates.

### Phase 2 — richness and similarity

Add licensed source adapters, multilingual identity, structured recipes, field completeness scoring,
similarity feature generation and review tooling. Start with ingredient/class/region similarity;
add embeddings only after a labelled related-dish set exists.

### Phase 3 — images and measured learning

Run the independent image queue, moderation and Cloudinary linkage. A/B test ontology snapshot
versions and use explicit save/cook/replace/regret outcomes to calibrate affinity and similarity.

### Tests and release gates

- Unit: normalization/transliteration, confidence merge, field policy, similarity symmetry,
  add-on invariant, staleness and priority.
- Contract: every endpoint, scope, validation, idempotency replay/conflict, ETag/cache behaviour and
  error envelope.
- Integration: PostgreSQL migrations, lease races, retry/dead-letter, provider timeout/circuit,
  review immutability, Cloudinary success/failure and outbox publication.
- Data: duplicate rate, alias ambiguity, referential integrity, provenance coverage, field coverage,
  exact nutrition match and zero unsafe automatic publications.
- Recommendation regression: current 810-dish snapshot, class membership, primary/add-on pools,
  hard-filter zero violations and golden slates.
- Operational: load, queue backlog recovery, backup/restore, key rotation, snapshot rollback and
  external-provider total outage.

## Acceptance answers

1. **Recommendation quality:** yes, if integrated by reviewed snapshots and measured outcomes.
2. **Consumer-app depth:** yes through multi-source aggregation; not from FoodOn/USDA alone.
3. **Cross-region links:** yes through typed, evidence-bearing dish relationships.
4. **Free sources:** yes for an MVP, with coverage/licence gaps and Foofoo-owned taxonomy.
5. **Daily isolation:** yes with priority queues, caps and the service's own DB/workers.
6. **Cloudinary:** yes through an independent image queue and immutable asset metadata.
7. **Auditability:** yes with append-only evidence/assertions/reviews and field policies.
8. **Build first:** service boundary, async intake, canonical identity/class safety and snapshot
   publication. Defer embeddings, broad generated imagery and learned ranking until labelled quality
   gates exist.
