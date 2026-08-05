# Food Ontology and Meal Taxonomy Architecture

**Status:** ACTIVE
**Version:** 1.0
**Date:** 2026-08-05
**Placement:** `docs/architecture/`
**Supersedes:** None
**Dependencies:** Canonical Planning Model v1.0; migrations 008, 009, 021, 051, 056; seed 146

## Executive Summary

FooFoo now has one database-bound ingestion gate for canonical and user-submitted dishes. Raw
external research remains staging evidence, normalized assertions preserve per-field confidence
and provenance, and only class-bound mappings feed the recommendation candidate view. The
existing class-first plan APIs remain authoritative; this subsystem adds intake, enrichment
status, meal-class discovery and direct candidate lookup without duplicating plan generation.

The existing deterministic `classify_dishes.py` research output is retained and seeded into the
new normalized mapping tables. New unknown dishes use external research first and then stop at
`pending_ai` or `review` until the model policy described in Section 8 is approved.

### Production release status — 2026-08-05

Migrations 054, 055 and 056 and seed 146 are live on Supabase project
`cmkswalqpmmqojwdmqbv`. The production catalogue retained all 802 dishes; every dish has a usable
meal-class mapping, 547 are `enriched`, and 255 are deliberately routed to `review`. The
`dish-ontology` v1, `plan` v9 and `feedback` v6 Edge Functions are active. Fly.io release v124 is
healthy and serves immutable bundle `sha256:3d4cf579d1cf2565`. The compatibility fallback remains
enabled for the monitored rollout window, and unknown-dish AI promotion remains disabled.

## 1. Architecture Plan

The subsystem follows one direction:

`user/research input → staging submission/source records → evidence assertions → reviewed current values → dish/class mappings → candidate view → existing class-first planner`

The database is the enforcement boundary. An insert or taxonomy-relevant update to
`public.dishes` marks that dish pending and creates an enrichment job even when a script or
service bypasses the Edge Function. User-created names first land in `dish_submissions`; they do
not enter recommendation pools until normalized and promoted to `public.dishes` by a trusted
workflow.

Primary classes, add-on classes and combo templates retain explicit planning roles. A constraint
trigger rejects an add-on or combo class mapped with `item_role = 'primary'`.

## 2. Database Schema

### 2.1 Source and staging

- `dish_submissions`: user-entered name and metadata, owner, resolution state and canonical link.
- `food_source_records`: raw FoodOn/USDA responses, provider identity, source URL, SHA-256 and
  fetch time. A row targets exactly one canonical dish or submission.
- `dish_enrichment_jobs`: retryable state machine, missing fields, attempts and worker lease.

### 2.2 Normalized domain

- `meal_class_families` plus additions to `meal_classes`: hierarchy, family, planning role and
  weekday/weekend fit.
- `taxonomy_terms` and `taxonomy_term_aliases`: canonical IDs, parent-child relationships,
  external URIs and regional/language aliases.
- `dish_taxonomy_assertions`: append-only candidate values. Every value carries confidence,
  source name/type, optional source record/URL, review status, timestamp and model identity when
  AI/ML generated it.
- `dish_taxonomy_current`: one selected assertion per dish and field; guards prevent weaker
  evidence or automation from replacing accepted truth.
- `dish_meal_class_mappings`: normalized many-to-many class membership with slot, item role,
  confidence, source and review state.
- `dish_constraints` and `dish_regional_affinities`: filterable, normalized constraints and
  regional evidence.
- `dish_name_synonyms`: the existing sourced regional alias ontology remains in use.

### 2.3 Runtime and generated outputs

- `dish_candidates_by_class`: recommendation-facing read model. It includes only active dishes in
  `enriched` or `review`, preserves classification confidence, and requires callers to select
  `primary` versus `addon` explicitly.
- Existing `week_plans`, `plan_slots`, `recommendation_events` and `feedback_events` remain the
  runtime plan and learning stores. No replacement tables are introduced.

### 2.4 Analytics and debugging

- `dish_ontology_coverage`: selected-field count, class count and most recent taxonomy update.
- `dish_taxonomy_review_queue`: unresolved/failed dishes and their missing fields.

## 3. Enrichment Workflow

1. Capture a canonical dish change or user submission; a database trigger creates the job.
2. Normalize Unicode, whitespace and known aliases. Exact canonical identifiers outrank fuzzy
   matching.
3. Query external sources concurrently. Store the complete raw response and hash before deriving
   any normalized value.
4. Apply deterministic local research and rules, including the existing 810-dish catalogue and
   meal-class rubric.
5. For fields still missing, invoke the approved structured-output classifier. Store each output
   as an assertion with model name/version, confidence and provenance.
6. Select current values only when policy permits. Never replace an accepted value with
   automation; never replace a current value with lower confidence.
7. Mark confidence below the approved threshold provisional and route it to review.
8. Promote a submission only after required safety fields and at least one valid meal-class
   mapping exist. The canonical dish then passes through the canonical-dish trigger as well.

Recommended required fields are: canonical identity, cuisine, meal class, diet type, cooking
method, spice, heaviness, texture, richness, weather affinity, constraints, slot eligibility and
regional affinity. Fields may be multi-valued through separate assertions/mappings, never a
pipe-separated production string.

## 4. API Contract and Integration Points

### 4.1 Reused APIs

- `POST /v1/plan { surface: "weekly_plan" }`: weekly class-first plan.
- `POST /v1/plan { surface: "class_dishes", class_code, slot, ... }`: finalized class dish pool.
- `POST /v1/plan { surface: "meal_plan", ... }`: ranked slot candidates and explanations.
- Python RE `/v1/weekly-plan`, `/v1/class-dishes`, `/v1/meal-plan`: existing signed compute
  endpoints called by the Edge layer.

These endpoints remain the recommendation source of truth. The new API must not reimplement
ranking or weekly planning.

### 4.2 Recommendation compatibility bridge

The active Python RE remains an immutable, startup-loaded service. Seed generation now also emits
`food_ontology_snapshot.json`, a planning-safe projection containing canonical dish identity,
primary class, all class memberships, planning roles, confidence, review status and provenance.
The bundle exporter includes that file in its content hash, and `ghar_re_core.knowledge` prefers
the snapshot for class lookup.

This is deliberately a build-time promotion boundary, not a per-request database dependency:

`reviewed ontology → generated snapshot → versioned RE bundle → existing class-first scoring`

During rollout, the legacy class CSVs remain a fallback for an older bundle and for the small set
of reference/fixture names outside the 810-dish production catalogue. Compatibility tests prove
the snapshot produces the same primary and multi-class memberships for every current catalogue
dish. Raw external records, AI candidates and rejected assertions are never bundled.

### 4.3 New authenticated API

`POST /v1/dish-ontology` multiplexes:

- `{ action: "submit", name, metadata? }` → `201`, staged submission plus external research
  outcome.
- `{ action: "update", submission_id, name, metadata? }` → `201`, revised submission and a new
  enrichment pass.
- `{ action: "status", submission_id }` → owned submission and job state.
- `{ action: "meal_classes" }` → canonical active classes with hierarchy/planning role.
- `{ action: "candidates", class_code, slot?, role?, diet?, limit? }` → class-bound candidates,
  confidence and explanation-ready tags. `role` defaults to `primary`; add-ons require
  `role: "addon"`.

External failure is partial, not destructive: successful provider evidence is retained, failed
provider count is returned, and unresolved work proceeds to AI/review.

## 5. External API Assessment

### FoodOn through EMBL-EBI OLS4 — integrated

Use `GET https://www.ebi.ac.uk/ols4/api/search?q=...&ontology=foodon`. It is the best available
open ontology identifier/synonym source and needs no product API key. It is evidence only: FoodOn
does not encode FooFoo's household meal classes or Indian weekday/slot semantics.

### USDA FoodData Central — integrated when configured

Use `/fdc/v1/foods/search` with `USDA_FOODDATA_API_KEY`. It is strong for nutrient/food component
data, CC0/public-domain, and currently documents a default 1,000 requests/hour/IP limit. It is
not a meal-taxonomy service and Indian prepared-dish coverage/matching must be measured before
nutrient values are promoted.

### Open Food Facts — adapter deferred

Its current API exposes multilingual category/label/ingredient taxonomy suggestions, but its
core entity is a packaged food product. It is useful later for barcode/product submissions, not
as the canonical source for household dishes or meal classes.

No evaluated external source provides FooFoo's required class-first meal taxonomy. FooFoo should
own that ontology and use external APIs as evidence enrichers, never as the planner's class truth.

## 6. Migration, ETL and Rollout Runbook

1. Apply migration `056_food_ontology_enrichment.sql` after the concurrent `055` migration.
2. Run `database/etl/generate_food_ontology_seed.py`; CI should fail if its checked-in seed diff
   is non-empty.
3. Apply `146_seed_food_ontology.sql` after existing reference/content seeds.
4. Run validation `910_food_ontology_enrichment_validation.sql`.
5. Inspect `dish_ontology_coverage` and `dish_taxonomy_review_queue`; resolve low-confidence
   classes before expanding candidate-view use.
6. Deploy the `dish-ontology` Edge Function and configure a server-only USDA key if desired.
7. Generate and verify `food_ontology_snapshot.json`; the bundle version changes whenever this
   promoted projection changes.
8. Deploy the rebuilt immutable RE bundle. Do not add live database calls inside scoring math.
9. Retain the legacy CSV fallback for one rollout window; remove it only after deployed parity and
   rollback verification.

Rollback uses `056_food_ontology_enrichment_rollback.sql`. It removes only the new enrichment
structures and columns; canonical dish rows survive. Roll back the Edge Function before the
schema so old code never calls missing tables.

## 7. Test Plan

- Missing tags: insert a canonical dish with minimal fields; verify status `pending`, one active
  job and required missing-field list.
- User-added dish: submit a Unicode/regional name; verify owner-scoped staging, raw provider
  evidence and `pending_ai`/`review` without premature candidate eligibility.
- Low-confidence inference: insert a 0.60 assertion/mapping; verify provisional review state and
  that it cannot replace stronger accepted truth.
- Class-bound retrieval: query a class and verify every result has the requested class/slot/role,
  with confidence and ontology state.
- Add-on-only handling: attempt a primary mapping to an add-on class; the transaction must fail.
- Recommendation filtering: verify diet, Jain/allergen/fasting/cook-capability filters are applied
  before ranking and that an empty safe pool returns a named empty state.
- External failure: timeout FoodOn while USDA succeeds; preserve USDA evidence and return partial.
- ETL determinism: run the generator twice and compare the seed hash.
- Recommendation compatibility: prove snapshot and legacy primary/multi-class lookup parity for
  all 810 dishes, golden-master outputs remain unchanged, and catalogue-specific class-count
  caches cannot leak across bundle versions.
- RLS: user A can read their submission/job; user B cannot. Raw submissions are never public.

## 8. ML/AI Decisions Required

Implementation is intentionally paused at `pending_ai` for unknown dishes until these product
decisions are approved:

1. Model/provider and data residency: which structured-output model may receive user-entered dish
   names/metadata, and in which region?
2. Promotion thresholds: proposed `≥0.90` auto-select, `0.70–0.899` provisional/recommendable with
   explanation, `<0.70` human review and not primary-eligible. The existing seed preserves its
   actual rubric confidence rather than pretending every mapping meets this policy.
3. Safety fields: diet, allergens and religious/fasting constraints should require deterministic
   ingredient evidence or human review; an LLM alone should never clear a safety exclusion.
4. Multi-label policy: maximum primary classes per slot and whether secondary classes can be
   auto-selected.
5. Review operations: reviewer identity, SLA and whether corrected examples may become training
   data under the user's consent posture.

## 9. Critical Self-Review

- The API currently stages external evidence but does not auto-promote unknown dishes; this is a
  deliberate safety boundary pending Section 8 decisions.
- FoodOn and USDA matching quality for Indian regional dish names is unknown and needs an offline
  labelled evaluation. Exact-name confidence is capped below canonical/human confidence.
- Seed 146 is large because it contains an auditable snapshot of all per-field source assertions.
  A future bulk loader may compress deployment transport, but must preserve deterministic hashes.
- The Python RE consumes the planning-safe ontology projection through its immutable bundle;
  external evidence and database review state stay outside request-time scoring. The checked-in
  legacy fallback remains intentionally active for rollback and non-production fixture names.
- Clinical health-condition suitability remains outside this subsystem until appropriate clinical
  governance exists.

## 10. Versioning and Placement

Version 1.0 establishes the normalized schema, ingestion gate, research adapters, seed and API.
Changes to confidence/promotion policy or safety semantics require a versioned architecture
revision and explicit review.

## Founder Sign-off
