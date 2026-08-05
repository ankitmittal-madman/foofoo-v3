# Food Intelligence and Meal Episode Architecture

**Status:** ACTIVE
**Version:** 2.0
**Date:** 2026-08-05
**Placement:** `docs/architecture/`
**Supersedes:** Food Ontology and Meal Taxonomy Architecture v1.0; the food/episode implementation portions of DOC-10 Technical Architecture v1.0
**Dependencies:** Comprehensive PRD and Intelligence Bibles v1.1; Database Architecture Review and Target Schema v1.1; migrations 055–074; seeds 146–147

## Executive Summary

Foofoo owns a governed food-intelligence platform; external datasets and APIs are evidence providers, not runtime truth. Every canonical dish is queued for enrichment, every user-added dish enters staging, and only governed class mappings and safety closure can enter recommendations. The final served recommendation is a complete meal episode. Dish/class contracts remain as compatibility surfaces while episode serving, canonical slates, propensities, outcomes, and replay are active.

This document, the comprehensive PRD, and the database target review are the implementation guides. Archived predecessor documents are historical evidence only.

## 1. Production Baseline

The production baseline on 5 August 2026 is migrations 055–074, seed 147, `dish-ontology`, `cron-dish-ontology`, `household-access`, `recommendations`, `plan`, `feedback`, `research-panel`, and `research-annotations` Edge Functions. The catalogue contains 802 production dishes plus governed composite episodes. Every production dish has a background enrichment job and a published single-primary episode. The mobile episode client is on by default with a compatibility fallback. Migrations 065 and 070–072 complete relationship/source/AI provenance, controlled provider evaluation, database-enforced AI field policy and normalized recommendation request/run/candidate lineage. Migrations 073–074 make active household membership, rather than profile/household ID equality, the authorization basis for recommendations, plans and feedback and bind cross-user service access to JWT role rather than function-owner identity. The mobile household surface and user/tenant-scoped persistence make that boundary selectable and usable end to end.

The first full external pass completed for all 802 canonical dishes with zero failed or pending jobs. FoodOn returned usable evidence for 104 dishes. USDA's free public demo key was evaluated against 12 Indian dishes: four exact matches, five semantic mismatches and three no-record cases. Only exact normalized names at record confidence `>=0.90` can now retain provisional USDA nutrients; migration 070 records the labelled evaluation and removed mismatched provisional assertions without deleting raw evidence.

## 2. Bounded Contexts and Ownership

| Layer | Owned records | Rule |
|---|---|---|
| Source/staging | `dish_submissions`, `food_source_records`, enrichment jobs | Immutable provider/user evidence; never recommendation truth |
| Governed food | dishes, ingredients, aliases, taxonomy assertions/current values, constraints, regions, graph, nutrients, recipes | Confidence, provenance, review state, and safety authority are explicit |
| Episode catalogue | grammars, rules, episodes, components, workload, cadence | Versioned complete-meal objects; published rows only at runtime |
| Runtime decisions | plans, slates/items, propensities, outcomes, replay | Preserve exactly what was eligible, ordered, shown, and later happened |
| Online intelligence | `re_engine`, `ml`, and `ops` | Private state, feature/model registry, lineage, review and publication controls |
| Research | studies, consented participants, diaries, annotation batches/items/labels | Separate consent, leases, reviewer identity tokens, and agreement policy |
| Household authorization | memberships, membership events, hashed invites, role transitions | Exactly one active owner; API authorization precedes service-role access; dependents remain separate from account permissions |

## 3. Enrichment Pipeline

`dish change/submission → durable job → lease claim → FoodOn + USDA lookup → raw hashed records → normalized provisional assertions → deterministic safety checks → safe promotion or AI/review → catalogue publication → immutable recommendation bundle`

The worker runs every ten minutes and claims rows with `FOR UPDATE SKIP LOCKED`. Daily reconciliation creates missing jobs, releases expired leases, and reopens due 90-day refreshes. All canonical dishes were reopened once by migration 060 so each receives at least one external pass. Provider repair is explicit and idempotent through `ops.requeue_external_provider`.

Accepted assertions are never overwritten by lower-confidence automation. External matches stay provisional. Exact-only USDA values are stored as source-linked nutrient assertions rather than replacing catalogue estimates; non-exact results remain raw evidence only.

## 4. Unknown-Dish Policy

The mobile submission flow captures name, aliases, ingredients, cuisine, region, meal slots, cook time, and notes. It displays enrichment status and never writes directly to `dishes`.

Conservative automatic promotion is active when both conditions hold:

1. FoodOn or USDA produces an exact normalized name match.
2. Every submitted ingredient already exists in the safety-governed ingredient catalogue.

This promotion creates a canonical draft with provisional aliases and derived ingredient safety. It does not invent unknown ingredients, clear allergens, or create unreviewed class mappings.

Groq `openai/gpt-oss-120b` is active for canonical-dish enrichment only. Output at confidence
`>=0.65` is retained as traceable evidence; aliases, allowlisted low-risk taxonomy dimensions and
regional affinity may publish at `>=0.80`. The model contract cannot express ingredients,
nutrition, allergens, medical or religious suitability, vegetarian status or alcohol claims.
Database guards independently reject canonical/component aliases and normalize known regional
codes. Atomic UTC-day limits are 800 requests and 160,000 tokens; exhausted work becomes
`budget_deferred` and resumes automatically. The stored Hugging Face token is an unused fallback,
not a second production provider.

## 5. Canonical Ontology

`food.ontology_nodes` represents dishes, variants, ingredients/forms, classes/roles, cuisines, regions, techniques, tags, nutrients, seasons, festivals, equipment, recipes, sources, and external food terms. `food.ontology_edges` represents containment/main ingredient, variant/alias, class membership, origin/popularity, technique/tag, pairing/substitution, suitability/season/festival, and source support.

The graph is relational and bounded. It supports auditable product traversals without introducing a graph database. Dedicated graph infrastructure requires measured traversal/operations evidence.

The catalogue seed populates aliases, ingredient and class links, cuisine/region/slot/sensory features, constraints, nutrition estimates, recipes and steps, plate grammars, single-dish and curated-combo episodes, component rows, workload features, and cadence priors.

## 6. Recommendation and Learning Runtime

The planning hierarchy remains class-first:

`household → constraints → intent/class plan → class-bound dishes → plate grammar/components → episode safety/practicality → episode rank → slate → outcome`.

`POST /plan { surface: "meal_episodes" }` is the default mobile request. The Edge layer persists `slates` and ordered `slate_items` before returning success. It also atomically records normalized recommendation requests, context/feature snapshots, runs, all eligible candidates and per-candidate stage evidence. Each shown item stores rank, scores, propensity, prediction heads, reasons, generator codes, decision trace, runtime episode hash, and, when resolvable, the canonical catalogue episode ID.

Feedback dual-writes typed outcomes for chosen, locked, cooked, ordered, replaced, completed, and regretted actions. `replay_recommendation_slate` returns the immutable slate, ordered items, and linked outcomes. The current production ranker is explicitly registered as an untrained rule baseline; learned promotion requires offline/replay evidence and calibration.

## 7. APIs

| API | Trust boundary | Purpose |
|---|---|---|
| `POST /v1/dish-ontology` | Authenticated user | submit/update/status, classes, governed class candidates, and a complete provenance-bearing `ontology_record` by canonical ID or name |
| `cron-dish-ontology` | Service role only | reconcile, claim, research, normalize and schedule refresh |
| `POST /plan` meal episodes | Authenticated user | serve complete episode slate and persist exposure |
| `POST /v1/feedback` | Authenticated user | record preference/pantry and typed episode outcomes |
| `research-panel` | Authenticated, explicitly enrolled user | participation status and longitudinal meal diaries |
| `research-annotations` | Service role only | create batches, queue/lease items and store annotations |
| `POST /household-access` | Authenticated user or one-time invite token | list memberships, invite, accept, change role, revoke, transfer owner or leave through service-only RPCs |

### 7.1 Household permission boundary

Canonical authorization roles are `owner`, `planner`, `cook`, `member`, and `viewer`. Migration
073 records membership lifecycle events and uses a deferred invariant plus an atomic transfer RPC
to guarantee exactly one active owner. Invite secrets are returned once and only their SHA-256
hashes are stored. RLS permits active members to read household/membership data; owner-only server
paths manage invitations and roles. Recommendations are readable by every active role. Plan
controls require owner/planner; cooked and missing-ingredient evidence permits owner/planner/cook;
ordinary attributable feedback permits owner/planner/cook/member; viewer is read-only. The API
always derives the actor from the JWT and authorizes the separately selected household before any
service-role write. The mobile client exposes membership discovery/selection, invite acceptance,
owner administration and member leave and scopes plan/feedback persistence to user and household.

## 8. External Evidence Strategy

- FoodOn via EMBL-EBI OLS4: active for identifiers and synonyms; no key.
- USDA FoodData Central: free demo-key adapter active for controlled exact-only provisional evidence; broad Indian-dish coverage and free-tier rate limits are inadequate for canonical authority.
- Open Food Facts: reserve for packaged products/barcodes, not household dish truth.
- Recipe websites and academic datasets: import only when licensing and provenance permit; never scrape into runtime truth by default.
- Internal catalogue and research package: deterministic seed evidence with named source versions.

No external API supplies Foofoo's Indian household meal-class or plate-grammar ontology. Foofoo must own those taxonomies.

## 9. Research and Annotation Operations

Studies bind protocol, sampling frame, consent policy and lifecycle. Participants are explicitly enrolled and linked to a user only inside the private research schema. Meal diaries retain planned-versus-actual components, portions, cook effort, pantry, leftovers and satisfaction.

Annotation batches pin corpus and handbook versions, required reviewers and agreement threshold. Items are leased with skip-locked semantics; labels retain annotator token and confidence. Low agreement must be adjudicated or retained as disputed evidence, not silently averaged into truth.

## 10. Compatibility and Legacy Disposition

Compatibility is deliberate: dish/class planning and `recommendation_events` remain because active clients and feedback resolution use them. Episode slates/outcomes and normalized request/run/candidate lineage are the canonical new facts and are dual-written. Runtime class lookup has moved to snapshot v2, which embeds all 1,599 canonical and compatibility names; production bundle `sha256:ffad5c55384244e3` omits both legacy mapping CSVs, which remain offline ETL inputs only. Event-table contraction still waits for exposure/outcome, export/delete and rollback parity.

## 11. Verification and Rollback

Each migration 060–074 has a paired rollback and validation. Release gates cover queue coverage/leases, schema objects, safe promotion, episode/model/replay activation, research binding, provider requeue, complete relationship provenance, the governed ontology read model, household owner/role transitions and authenticated cross-user anti-probing. Edge functions use server-held secrets and service-role checks. Raw external payloads never enter the scoring hot path.

The rollback order is clients/functions, schedules, seed/content, then schema. Published catalogue rows are append/supersede oriented; no rollback may delete canonical dishes or historical slates/outcomes.

## 12. Open Decisions

1. Decide whether corrected user submissions may be retained as model-training data under explicit consent; current Groq processing is limited to canonical catalogue names.
2. Obtain a personal free USDA key only if higher controlled-evaluation throughput is required; never relax the exact-match guard.
3. Add health-condition suitability only after clinical evidence and governance approval.

## 13. Critical Self-Review

- Comprehensive catalogue values are broad but provisional where source evidence is internal or AI-drafted; population does not equal human certification.
- A recipe row for every dish closes product coverage, but the draft recipe set must not be presented as professionally tested.
- Selection propensity is exact for the current deterministic inclusion policy (`1`); it becomes non-trivial only when randomized/exploration policies are activated.
- The research system is operational infrastructure, not evidence that a representative household panel has been recruited.
- USDA coverage limitations are measured and visible; the system rejects semantic near-matches and never treats provider absence as fabricated nutrition.

## 14. Versioning and Placement

Version 2.0 is the active food-intelligence and meal-episode implementation architecture. The comprehensive PRD defines product intent; the database review defines physical target and current/transition labels; this document defines deployed subsystem behavior. Any AI safety, promotion, or canonical-event contraction change requires a versioned revision.

## Founder Sign-off

Founder acceptance: _______________________ Date: ___________
