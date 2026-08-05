# Food Intelligence and Meal Episode Architecture

**Status:** ACTIVE
**Version:** 2.0
**Date:** 2026-08-05
**Placement:** `docs/architecture/`
**Supersedes:** Food Ontology and Meal Taxonomy Architecture v1.0; the food/episode implementation portions of DOC-10 Technical Architecture v1.0
**Dependencies:** Comprehensive PRD and Intelligence Bibles v1.1; Database Architecture Review and Target Schema v1.1; migrations 055–064; seeds 146–147

## Executive Summary

Foofoo owns a governed food-intelligence platform; external datasets and APIs are evidence providers, not runtime truth. Every canonical dish is queued for enrichment, every user-added dish enters staging, and only governed class mappings and safety closure can enter recommendations. The final served recommendation is a complete meal episode. Dish/class contracts remain as compatibility surfaces while episode serving, canonical slates, propensities, outcomes, and replay are active.

This document, the comprehensive PRD, and the database target review are the implementation guides. Archived predecessor documents are historical evidence only.

## 1. Production Baseline

The production baseline on 5 August 2026 is migrations 055–064, seed 147, `dish-ontology`, `cron-dish-ontology`, `plan`, `research-panel`, and `research-annotations` Edge Functions. The catalogue contains 802 production dishes plus governed composite episodes. Every production dish has a background enrichment job and a published single-primary episode. The mobile episode client is on by default with a compatibility fallback.

FoodOn returned usable evidence in the controlled evaluation. USDA FoodData Central returned HTTP 403 for the configured key; catalogue nutrition remains available, but USDA-derived assertions will not appear until the credential is activated/replaced and `ops.requeue_external_provider('usda_fdc')` is run.

## 2. Bounded Contexts and Ownership

| Layer | Owned records | Rule |
|---|---|---|
| Source/staging | `dish_submissions`, `food_source_records`, enrichment jobs | Immutable provider/user evidence; never recommendation truth |
| Governed food | dishes, ingredients, aliases, taxonomy assertions/current values, constraints, regions, graph, nutrients, recipes | Confidence, provenance, review state, and safety authority are explicit |
| Episode catalogue | grammars, rules, episodes, components, workload, cadence | Versioned complete-meal objects; published rows only at runtime |
| Runtime decisions | plans, slates/items, propensities, outcomes, replay | Preserve exactly what was eligible, ordered, shown, and later happened |
| Online intelligence | `re_engine`, `ml`, and `ops` | Private state, feature/model registry, lineage, review and publication controls |
| Research | studies, consented participants, diaries, annotation batches/items/labels | Separate consent, leases, reviewer identity tokens, and agreement policy |

## 3. Enrichment Pipeline

`dish change/submission → durable job → lease claim → FoodOn + USDA lookup → raw hashed records → normalized provisional assertions → deterministic safety checks → safe promotion or AI/review → catalogue publication → immutable recommendation bundle`

The worker runs every ten minutes and claims rows with `FOR UPDATE SKIP LOCKED`. Daily reconciliation creates missing jobs, releases expired leases, and reopens due 90-day refreshes. All canonical dishes were reopened once by migration 060 so each receives at least one external pass. Provider repair is explicit and idempotent through `ops.requeue_external_provider`.

Accepted assertions are never overwritten by lower-confidence automation. External matches stay provisional. USDA values are stored as source-linked nutrient assertions rather than replacing catalogue estimates.

## 4. Unknown-Dish Policy

The mobile submission flow captures name, aliases, ingredients, cuisine, region, meal slots, cook time, and notes. It displays enrichment status and never writes directly to `dishes`.

Conservative automatic promotion is active when both conditions hold:

1. FoodOn or USDA produces an exact normalized name match.
2. Every submitted ingredient already exists in the safety-governed ingredient catalogue.

This promotion creates a canonical draft with provisional aliases and derived ingredient safety. It does not invent unknown ingredients, clear allergens, or create unreviewed class mappings. Generative classification remains pending until a model/provider, regional data-processing posture, confidence thresholds, and reviewer/training-consent policy are approved.

## 5. Canonical Ontology

`food.ontology_nodes` represents dishes, variants, ingredients/forms, classes/roles, cuisines, regions, techniques, tags, nutrients, seasons, festivals, equipment, recipes, sources, and external food terms. `food.ontology_edges` represents containment/main ingredient, variant/alias, class membership, origin/popularity, technique/tag, pairing/substitution, suitability/season/festival, and source support.

The graph is relational and bounded. It supports auditable product traversals without introducing a graph database. Dedicated graph infrastructure requires measured traversal/operations evidence.

The catalogue seed populates aliases, ingredient and class links, cuisine/region/slot/sensory features, constraints, nutrition estimates, recipes and steps, plate grammars, single-dish and curated-combo episodes, component rows, workload features, and cadence priors.

## 6. Recommendation and Learning Runtime

The planning hierarchy remains class-first:

`household → constraints → intent/class plan → class-bound dishes → plate grammar/components → episode safety/practicality → episode rank → slate → outcome`.

`POST /plan { surface: "meal_episodes" }` is the default mobile request. The Edge layer persists `slates` and ordered `slate_items` before returning success. Each item stores rank, rule score, rerank score, exact logging propensity, prediction heads, reasons, generator codes, decision trace, runtime episode hash, and, when resolvable, the canonical catalogue episode ID.

Feedback dual-writes typed outcomes for chosen, locked, cooked, ordered, replaced, completed, and regretted actions. `replay_recommendation_slate` returns the immutable slate, ordered items, and linked outcomes. The current production ranker is explicitly registered as an untrained rule baseline; learned promotion requires offline/replay evidence and calibration.

## 7. APIs

| API | Trust boundary | Purpose |
|---|---|---|
| `POST /v1/dish-ontology` | Authenticated user | submit/update/status, classes and governed class candidates |
| `cron-dish-ontology` | Service role only | reconcile, claim, research, normalize and schedule refresh |
| `POST /plan` meal episodes | Authenticated user | serve complete episode slate and persist exposure |
| `POST /v1/feedback` | Authenticated user | record preference/pantry and typed episode outcomes |
| `research-panel` | Authenticated, explicitly enrolled user | participation status and longitudinal meal diaries |
| `research-annotations` | Service role only | create batches, queue/lease items and store annotations |

## 8. External Evidence Strategy

- FoodOn via EMBL-EBI OLS4: active for identifiers and synonyms; no key.
- USDA FoodData Central: adapter and normalization active; production key currently receives HTTP 403 and requires owner action.
- Open Food Facts: reserve for packaged products/barcodes, not household dish truth.
- Recipe websites and academic datasets: import only when licensing and provenance permit; never scrape into runtime truth by default.
- Internal catalogue and research package: deterministic seed evidence with named source versions.

No external API supplies Foofoo's Indian household meal-class or plate-grammar ontology. Foofoo must own those taxonomies.

## 9. Research and Annotation Operations

Studies bind protocol, sampling frame, consent policy and lifecycle. Participants are explicitly enrolled and linked to a user only inside the private research schema. Meal diaries retain planned-versus-actual components, portions, cook effort, pantry, leftovers and satisfaction.

Annotation batches pin corpus and handbook versions, required reviewers and agreement threshold. Items are leased with skip-locked semantics; labels retain annotator token and confidence. Low agreement must be adjudicated or retained as disputed evidence, not silently averaged into truth.

## 10. Compatibility and Legacy Disposition

Compatibility is deliberate: dish/class planning and `recommendation_events` remain because active clients and feedback resolution use them. Episode slates/outcomes are the canonical new facts and are dual-written. Legacy relations may be contracted only after one observed production window proves complete episode exposure/outcome linkage, export/delete coverage, and rollback. This avoids breaking the current recommender while preventing new design work from targeting legacy tables.

## 11. Verification and Rollback

Each migration 060–064 has a paired rollback and validation. Release gates cover queue coverage/leases, schema objects, safe promotion, episode/model/replay activation, research binding and provider requeue. Edge functions use server-held secrets and service-role checks. Raw external payloads never enter the scoring hot path.

The rollback order is clients/functions, schedules, seed/content, then schema. Published catalogue rows are append/supersede oriented; no rollback may delete canonical dishes or historical slates/outcomes.

## 12. Open Decisions

1. Select the generative provider/model and allowed processing region for user-entered food metadata.
2. Ratify auto-promotion thresholds, class multi-label caps, and the human-review SLA.
3. Decide whether corrected user submissions may be retained as model-training data under explicit consent.
4. Replace or activate the USDA credential, then run the provider requeue and labelled match-quality evaluation.
5. Add health-condition suitability only after clinical evidence and governance approval.

## 13. Critical Self-Review

- Comprehensive catalogue values are broad but provisional where source evidence is internal or AI-drafted; population does not equal human certification.
- A recipe row for every dish closes product coverage, but the draft recipe set must not be presented as professionally tested.
- Selection propensity is exact for the current deterministic inclusion policy (`1`); it becomes non-trivial only when randomized/exploration policies are activated.
- The research system is operational infrastructure, not evidence that a representative household panel has been recruited.
- USDA failure is external and visible; the system intentionally does not fabricate USDA nutrition on a 403.

## 14. Versioning and Placement

Version 2.0 is the active food-intelligence and meal-episode implementation architecture. The comprehensive PRD defines product intent; the database review defines physical target and current/transition labels; this document defines deployed subsystem behavior. Any AI safety, promotion, or canonical-event contraction change requires a versioned revision.

## Founder Sign-off

Founder acceptance: _______________________ Date: ___________
