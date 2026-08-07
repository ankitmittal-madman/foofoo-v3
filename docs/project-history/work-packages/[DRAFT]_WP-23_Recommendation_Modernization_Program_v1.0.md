# Recommendation Modernization Program

**Status:** DRAFT
**Version:** v1.0
**Date:** 2026-08-07
**Placement:** `docs/project-history/work-packages/`
**Supersedes:** Nothing. WP-14 remains historical evidence and is not rewritten.
**Dependencies:** Canonical Recommendation Engine Architecture Final Review v1.0; Food Intelligence and Meal Episode Architecture v2.0; migrations 071, 079–091; Ghar RE contract v1; Auxiliary Recommender Production Readiness report

## Executive Summary

FooFoo needs one recommendation learning system shared by the app, production database, Ghar RE
and Aux RE. Ghar remains the final deterministic safety and meal-composition authority. Aux becomes
the scalable retrieval and learned-ranking system, initially in shadow and only later eligible for
controlled influence. Both consume the same canonical dish, episode, class, event, temporal and
household-context definitions.

The current repository proves important foundations already exist: class-first planning, semantic
dish/class/tag affinity, complete-meal episodes, immutable slates and typed outcomes, deterministic
Ghar fallback, an Aux LightFM shadow artifact, and catalogue/ontology publication controls. The
remaining work is not a replacement. It closes the serving-catalogue split, direct meal-class
feedback gap, temporal sequence/spacing gap, shallow health/fitness model, missing search and swap
semantics, selected-date loss, sensitive-inference governance, and the absence of an active
Ghar–Aux production integration.

## 1. Verified Baseline and Evidence Classes

Facts below deliberately retain their evidence class. A repository count, an older production
audit and a UI screenshot are not interchangeable.

| Fact | Current evidence | Confidence |
|---|---|---|
| Ghar serving catalogue contains 810 rows | Local bundle count and manifest | High for repository artifact |
| Ghar bundle is approximately 810 KB | Local file size | High for repository artifact |
| Aux local retrieval pool contains 86 candidates | `aux_re_service/data/retrieval/v1/candidates.json` | High for repository artifact |
| Aux LightFM artifact is synthetic-data guarded and shadow-only | Aux readiness report and policy code | High for repository behavior |
| Current architecture document records 802 production dishes on 2026-08-05 | Active architecture v2.0 | High for that dated audit only |
| Founder-provided Supabase view shows 3,409 `public.dishes` rows | Product screenshot | Medium; requires read-only live reconciliation |
| Ghar does not query production Supabase during scoring | Service/container code | High |
| Selected Today date was not forwarded to meal episodes | Mobile request path before this WP | High; fixed in this WP slice |
| Direct dish feedback derives dish, class and semantic-tag affinity | Migration 084 and feedback RPC path | High |
| Direct meal-class selection does not create a durable class preference event | Weekly-plan UI and feedback contract | High |
| Ghar learned `s_pref` contribution is disabled | Scoring/config path | High |
| Aux is not called by the live Edge serving path | Aux readiness report and Edge call graph | High |

Before production changes, a read-only audit must reconcile approved, enriched, class-mapped,
safety-closed, bundle-published and actually served dish counts. Raw DB row count is not the same as
recommendation-ready coverage.

## 2. Non-Negotiable Product Semantics

1. An exposure is not an acceptance.
2. Dish, episode and meal class are separate event targets.
3. The time of the action and intended meal date are separate facts.
4. Breakfast, lunch, dinner and snacks are separate meal moments.
5. Weekday and weekend rhythms are separate; individual-day behavior may refine them after enough
   evidence.
6. Explicit safety facts may hard-filter. Probabilistic inferences may only soft-rerank.
7. Ghar rechecks safety after Aux retrieval; Aux can never make an unsafe item eligible.
8. Production user data remains in production. Synthetic/generated training data remains in the
   training project. No production identities or raw behavior cross that boundary without a
   separately approved consent design.
9. Every served result records catalogue, feature, policy and model versions.
10. Every learned or inferred signal carries provenance, confidence, decay and allowed use.

## 3. Canonical Interaction Contract

The canonical event must support the following fields. Additions are additive and versioned; older
clients remain valid during the dual-write window.

| Group | Required meaning |
|---|---|
| Identity | Event ID, idempotency key, household, actor, request/slate linkage |
| Target | `dish`, `meal_episode`, `meal_class`, `ingredient`, `query` or `plan_slot`; canonical ID plus display snapshot |
| Replacement | Previous and replacement target IDs for swap/edit events |
| Moment | Event timestamp, local timezone, intended meal date, meal slot, weekday and weekday/weekend type |
| Action | Shown, searched, opened, selected, liked, disliked, locked, swapped, cooked, ordered, completed, regretted, never, not-today |
| Reason | Too much work, missing ingredient, member objection, mood, repetition, health goal or explicit free-choice code |
| Evidence | Explicit/inferred, real/synthetic, source surface, shown rank and propensity |
| Versioning | Schema, catalogue, feature, policy and model versions |

Compound meals resolve to an episode and component identities. `Bhindi + Roti` must not become an
unresolved pseudo-dish when the system already knows Bhindi and Roti as components.

## 4. Signal Value and Learning Rules

The standing differentiated event-weight decision remains authoritative. This program adds target,
moment and outcome semantics; it does not flatten events into one weight.

| Evidence | Learning treatment |
|---|---|
| Shown | Exposure/fatigue only; never positive preference |
| Search | Weak, short-lived query/tag intent |
| Open/details | Weak interest |
| Select/accept/make-this | Strong positive choice |
| Lock | Strong plan-fit signal |
| Cook/complete/repeat cook | Strongest execution/success outcome |
| Dislike/never | Strong negative; `never` also hard suppression |
| Not today | Temporary suppression with expiry |
| Swap without reason | Weak ambiguous signal |
| Reasoned swap | Targeted dish/class/effort/pantry/member-context signal |
| Regret | Strong negative post-choice outcome |

Long-term explicit preference, recent context and temporal cadence remain separate features so a
recent mood cannot erase a durable like and an old like cannot force weekly repetition.

## 5. Temporal Sequence and Spacing Model

The state grain is `household × meal slot × day type`, with optional day-of-week refinement once
minimum evidence is reached. Weekday lunch does not share full-strength evidence with weekday
dinner; weekend behavior does not dominate weekday planning.

For dish, class, cuisine, ingredient family and richness tier, compute:

- days since last shown, selected, cooked and completed;
- 7-, 14- and 28-day exposure and outcome counts;
- consecutive repeats and longest recent run;
- accepted spacing distribution and next-spacing readiness;
- previous-one and previous-two transition features;
- weekday/weekend and slot affinity;
- rich/light and cuisine rotation debt;
- explicit novelty tolerance and observed exploration success.

The rule-serving interpretation is bounded and explainable:

`score = long-term preference + moment fit + spacing readiness + sequence fit - repetition debt`

Aux may learn nonlinear interactions over the same features. Ghar consumes bounded normalized
outputs and remains authoritative for constraints, caps, repair and final composition.

## 6. Meal-Class Learning

Meal class participates at three distinct points:

1. weekly class candidate generation;
2. direct class selection/lock/rejection learning;
3. class-bound dish and episode selection on Today.

Required durable state includes direct class affinity, dish-derived class affinity, class
suppression, class cadence and class transition affinity. Direct class evidence remains separately
inspectable from projected dish evidence. A saved class stays highlighted for its plan slot, while
the evidence from selecting it influences later weekly plans.

## 7. Household, Health, Fitness and Profession Context

### 7.1 Authority ladder

| Tier | Example | Permitted effect |
|---|---|---|
| Explicit verified safety | Allergy, diet, Jain | Hard eligibility |
| Explicit goal/target | Healthy living, protein target, time budget | Strong bounded constraint/rank |
| Observed behavior | Repeated quick weekday dinners | Medium soft rank |
| Low-risk structural inference | Teen present, larger household | Small soft prior |
| Sensitive speculation | Profession/income from state/city | Prohibited as fact or rank feature |
| Medical speculation | Disease or macro restriction inferred from age | Prohibited |

A couple from MP living in Mumbai must not be labelled “working class” without direct evidence.
The product may hold a low-confidence `weekday_time_pressure` hypothesis when supported by explicit
working-professional answers or repeated quick-meal behavior. A household with a 16-year-old may
receive a neutral balanced-family prior, but not an inferred low-carb or medical diet.

Every inferred feature stores value, confidence, sources, allowed use, created time, expiry and
user-correction state. Inferred features never enter logs or third-party payloads with household
identity. Health data and sensitive inferences require DPDP/legal review before production use.

### 7.2 Nutrition maturity

`healthy_living`, `into_fitness` and `protein_calculator` currently rely on lightness/protein
proxies. Promotion to quantitative nutrition requires portioned calories, protein, carbohydrate,
fat, fibre, sodium and source confidence. Clinically governed conditions remain out of scope until
approved evidence and policy exist.

## 8. Scalable Catalogue and Serving Architecture

A single in-memory JSON file is acceptable for hundreds or low thousands of dishes but is not the
million-dish target. Production evolves to two-stage retrieval:

`governed DB → versioned publication → metadata/text/vector indexes → Aux retrieves 100–500 → Ghar safety/rerank → 4–8 served`

Publication includes only approved, safety-closed, class/slot-mapped rows. Ghar keeps a small
versioned fallback catalogue and bounded safety dictionaries, not every dish. Indexes partition by
market/availability and support diet, allergen, slot and class prefilters. Catalogue publication is
atomic, checksummed and rollbackable.

## 9. Engine Responsibilities

| Capability | Aux RE | Ghar RE |
|---|---|---|
| Million-scale candidate retrieval | Primary | No full scan |
| Collaborative/content model | Primary, gated | Optional bounded input |
| Temporal sequence model | Learn and score | Apply bounded state/rules |
| Meal-class prediction | Candidate score | Final plan and repair |
| Hard dietary/allergen safety | Preliminary | Authoritative and repeated |
| Complete episode grammar | Features | Authoritative composition |
| Deterministic fallback | No | Required |
| Final explanation | Feature reasons | User-visible final reason |

Aux begins shadow-only. Synthetic artifacts can validate plumbing but can never earn active
promotion. Active influence requires consented real outcomes, household-disjoint time-split
evaluation, safety parity, calibration and controlled online evidence.

## 10. Delivery Workstreams

| Order | Workstream | Exit evidence |
|---:|---|---|
| 1 | Reconcile live/repository catalogue and behavior baselines | Signed aggregate report; no credentials or identities |
| 2 | Version canonical target/moment/outcome contract | Contract tests across mobile, Edge, Ghar and Aux |
| 3 | Capture selected date, direct class actions, search funnel and reasoned replacement | Replayable real events with canonical identity |
| 4 | Materialize temporal/cadence state | Deterministic replay and window validation |
| 5 | Govern explicit and inferred context | Provenance/confidence/expiry and policy tests |
| 6 | Build versioned DB-to-index catalogue publisher | Count/hash/coverage and rollback parity |
| 7 | Upgrade Ghar rule serving | Golden parity for unchanged cases; new feature tests |
| 8 | Upgrade Aux dataset/model/retrieval | Real-data quality gates and shadow report |
| 9 | Wire Edge shadow integration | Opaque baseline preserved; comparison persisted |
| 10 | Load, soak, chaos, safety, privacy and fairness validation | Ratified gate report |
| 11 | Canary/A-B rollout | Automatic kill switch and rollback evidence |
| 12 | Contract compatibility facts after monitored parity window | Export/delete/replay/rollback proof |

## 11. Acceptance Metrics

Targets requiring a product baseline are expressed as gates, not invented numbers.

| Dimension | Acceptance gate |
|---|---|
| Safety | Zero hard-constraint violations in replay, shadow and canary |
| Identity | Every served/actionable item has canonical target identity or an explicit unresolved state |
| Date | Intended meal date and local event time survive app → DB → feature pipeline |
| Class learning | Direct class action changes a subsequent eligible class ranking in deterministic tests |
| Temporal behavior | Slot/day-type spacing changes replayed ordering without treating exposure as acceptance |
| Catalogue | Approved-to-index and approved-to-served coverage measured by immutable version |
| Ghar resilience | Safe deterministic output when Aux is unavailable or rejected |
| Aux quality | Beats the frozen baseline on ratified offline metrics and all required slices |
| Latency/cost | Meets documented targets established by baseline; no invented threshold |
| Privacy | No production identity/raw event copied to training without approved consent path |
| Explainability | Final result names explicit, temporal, context and safety reasons with provenance |
| Fairness | No sensitive stereotype feature; slice metrics and user correction available |

## 12. Rollout and Rollback

Each behavior is feature-flagged independently: canonical-event dual write, temporal-state read,
class-learning read, inferred-context read, Aux shadow, Aux candidate input and Aux score input.
Database migrations are additive through the dual-write window and have paired rollback scripts.
Rollback disables reads before removing writes; historical events and slates are never deleted.

Promotion sequence is offline replay → shadow → internal canary → household-stable experiment →
controlled ramp. A safety, latency, error, fallback or drift breach disables Aux influence and
returns to Ghar-only serving without requiring catalogue/event rollback.

## 13. Critical Self-Review

- This document does not claim the founder-observed 3,409 rows are all approved or serving-ready;
  that requires aggregate live reconciliation.
- It does not treat synthetic Aux metrics as evidence of production preference quality.
- It does not infer profession, income, disease or dietary restriction from geography, age or
  household composition.
- It does not claim a million-dish JSON benchmark was run; catalogue-scale performance remains a
  required workstream.
- It preserves Ghar’s hard safety authority and the production/training database boundary.
- Performance targets remain unset until authoritative product targets or a ratified baseline
  exists.

## 14. Versioning and Placement

Version 1.0 establishes the modernization program and requirement/acceptance baseline. It remains
DRAFT until Founder review. Implementation evidence belongs in companion validations and
certificates; this file must not be marked complete without them.

## Founder Sign-off

Founder acceptance: _______________________ Date: ___________

## Implementation Checkpoints

| Checkpoint | Repository evidence | Deployment status |
|---|---|---|
| S99 — program start | Selected Today date reaches the Plan request; this work package defines the shared program | Committed; no DB change |
| S100 — interaction contract v2 | Versioned JSON contract, additive migration 092/validation 944, Edge validation/writer support, canonical service-only view, weekly meal-class selected/replaced/lock events, and focused mobile/Deno tests | Code checkpoint only; migration and Edge/mobile release not yet deployed |
| S101 — direct meal-class learning | Migration 093 separates direct class affinity from dish-projected class affinity; Edge sends both; Ghar weekly planning weights direct evidence more strongly and explains both contributions; deterministic core/service tests prove ranking movement | Code checkpoint only; migrations 092–093 and serving changes not yet deployed |
| S102 — temporal meal rhythm | Migration 094 materializes dated class impressions separately from explicit selection/rejection, keyed by breakfast/lunch/dinner and weekday/weekend; Edge composes the private state and Ghar applies bounded, separately explained spacing pressure to dated weekly plans | Code checkpoint only; migrations 092–094 and serving/mobile changes not yet deployed |
| S103 — dish and attribute rhythm | Migration 095 materializes point-in-time dish, cuisine, richness and cooking-method outcomes/impressions by dated meal moment; Today sends canonical episode events; Ghar applies bounded recent-spacing and learned-due adjustments with separate explicit/exposure explanations | Code checkpoint only; migrations 092–095 and serving/mobile changes not yet deployed |
| S104 — governed household context | A shared contract and migration 096 distinguish explicit health goals and working-household facts from a low-confidence, expiring, correctable weekday-time-pressure inference; Edge composes it and both Ghar and Aux apply only bounded, explained reranking to meal classes and eligible dishes | Code checkpoint only; migrations 092–096 and serving/mobile changes not yet deployed |
| S105 — scalable catalogue publication | Migration 097 exposes count-only coverage plus bounded, service-only keyset pages containing safety-closed, class-mapped canonical dish facts; a read-only publisher streams immutable JSONL and refuses count drift or partial overwrite | Code checkpoint only; migration 097 is not deployed and live serving still uses the 810-dish fallback |
| S106 — bounded Ghar catalogue hydration | The publisher also builds a checksummed SQLite hydration index; Ghar accepts at most 500 canonical candidate IDs, loads only those rows, strictly validates Ghar-critical taxonomy, preserves database UUIDs and allergen flags, reruns hard eligibility, and reports the selected source or explicit fallback reason | Code checkpoint only; migration 097, publication artifact and Edge/Aux candidate integration are not deployed; the 810-dish bundle remains the deterministic fallback |
| S107 — version-bound Aux catalogue retrieval | A constant-memory importer validates every published row, streams canonical UUID candidates into a new hash-named Qdrant collection, verifies exact indexed count, and exposes rollback-safe collection/version settings; Aux filters every query to that publication, applies household-wide diet/allergen prefilters, reruns hard safety and returns canonical IDs for later Ghar hydration | Code checkpoint only; no publication was generated or uploaded, Aux remains unconfigured, and Edge does not yet orchestrate the Aux-to-Ghar shortlist |
