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

The S100–S124 rows preserve the deployment status at the time each checkpoint was written. They
are historical checkpoint evidence, not the current production state. S130 supersedes those
pre-deployment status cells: migrations 092–101, the 642-dish publication, matching Qdrant/Ghar/Aux
foundations and Edge code are deployed with production Aux routing off. Run 31256081581 later
closed the independent Aux model-quality CI gate. Authenticated test-household smoke, catalogue
gap closure, ratified load/shadow evidence and any canary remain open. Later protected aggregate
runs `31257431526` and `31257875325` measured 3,410 stored/3,402 active dishes, 646
presence-eligible, 547 strict-quality-ready and 255 low-confidence class mappings. All 255 are
provisional internal-research outputs with no curated, human-reviewed or accepted evidence.

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
| S108 — signed staged Edge orchestration | Edge can call Aux with raw-body HMAC authentication in explicit `off`, `shadow` or `active` mode for Today recommendations and meal episodes; the request carries household, history, governed context and direct/projected meal-class affinity, while only active mode passes a bounded canonical-ID shortlist to Ghar; Ghar remains final safety and response catalogue lineage is recorded | Code checkpoint only; migration 098, Edge configuration, Aux secret, publication index and service releases are not deployed; default mode is `off` and shadow mode cannot change user-visible Ghar candidates |
| S109 — governed offline Aux gate | A privacy-minimized evaluator compares a frozen candidate baseline with one immutable Aux publication using consented real outcomes, household-disjoint time splits, canonical identity, zero hard-safety violations, recall/MRR, slice non-regression and deterministic Ghar failover evidence; synthetic evidence is structurally barred from active eligibility | Code checkpoint only; the evaluator is tested with fixtures but no real holdout dataset has been supplied or evaluated, so Aux is not eligible for active promotion |
| S110 — measured load and Aux chaos gates | The network probe signs either Ghar or Aux requests, records aggregate status/latency/throughput, treats transport failures as errors, strips payloads and secrets from reports, and remains measurement-only unless ratified absolute or baseline-relative targets are supplied; Edge tests prove the 800 ms Aux timeout and network failure each make one attempt and fail open | Code checkpoint only; deterministic tests pass, but no deployed service load/soak run or ratified production threshold evidence exists yet |
| S111 — durable privacy-minimized shadow evidence | Migration 099 adds a strictly allowlisted count-only Aux observation to the existing recommendation event; Today and meal episodes record mode, retrieval/failure outcome, publication hash, Aux latency, candidate count and canonical served overlap after Ghar responds, while candidate/served IDs, names, preferences and user history are structurally excluded | Code checkpoint only; migration 099 and Edge changes are not deployed, so no real shadow observations exist; legacy non-UUID Ghar results are explicitly recorded as non-comparable rather than false zero overlap |
| S112 — service-only shadow health aggregation | Migration 100 exposes a security-definer aggregate function over a caller-supplied half-open window capped at 31 days; it groups by UTC day, rollout mode and immutable publication, returning only availability, timeout, candidate-count, latency and canonical-overlap metrics with all public/authenticated access revoked | Code checkpoint only; migrations 099–100 are not deployed and therefore the function has no real observations to summarize |
| S113 — explicit promotion and kill-switch decision | A privacy-safe evaluator binds one publication across the real-outcome offline gate, explicitly gated Aux load report, aggregate shadow/canary health and zero hard-guardrail counters; all product targets are mandatory inputs, shadow cannot promote unless every gate passes, and an active operational/safety breach emits `disable_aux`, `set AUX_RE_MODE=off` and exit code 2 | Code checkpoint only; deterministic fixtures pass, but no ratified targets or real offline/load/shadow evidence have been supplied, and no deployment automation consumes the decision yet |
| S114 — protected fail-safe rollout workflow | A production-environment workflow downloads exactly one privacy-minimized evidence file from a successful same-repository run, executes the S113 evaluator, uploads only the decision, and may set the Supabase `AUX_RE_MODE` secret to `off` only on exit code 2; it explicitly contains no active-mode mutation path | Code checkpoint only; the workflow has static/YAML tests but has not run, no evidence producer is connected, and production environment approval/credentials remain external controls |
| S115 — governed rollout evidence composition | The load probe now records publication hashes returned by successful Aux responses; a new atomic, no-overwrite composer accepts only the governed offline/load/health/guardrail/target schemas, requires measured production guardrails, matching observation windows, ratified target approval, one publication across every source, and embeds SHA-256 source lineage before validating the assembled decision input | Code checkpoint only; fixtures pass, but no real reports, approved targets or evidence artifact have been composed and no producer workflow is connected |
| S116 — measured final-serving guardrails | Ghar independently rechecks the final served dish IDs against canonical catalogue identity and its authoritative hard eligibility predicate; Edge binds that count-only audit to the requested date and exact Aux publication, persists active catalogue fallback/version failures, and migration 101 exposes a service-only aggregate that becomes unavailable when any audit is missing instead of substituting zero | Code checkpoint only; migration 101 and service/Edge changes are not deployed, so no real production guardrail report exists and Aux remains off |
| S117 — protected rollout evidence production | A production-environment workflow accepts exactly three independently supplied offline/load/ratified-target reports from one successful same-repository run, opens a project-verified read-only production connection, exports only service-only health/guardrail aggregates, derives rather than trusts the observed rollout mode, composes one immutable evidence file, and uploads no source report | Code checkpoint only; the workflow has not run, the source reports and approved targets do not exist, and production environment approval/credentials remain external controls |
| S118 — governed rollout input packaging | A separate protected workflow downloads exactly one aggregate offline report and one gated Aux load report from successful same-repository runs, builds the six required product targets only from protected environment variables with approval reference/time, rejects raw cases, identity fields, extra keys, mixed catalogue generations and measurement-only load results, and publishes the exact three-file artifact accepted by S117 | Code checkpoint only; no real offline/load artifact or product-ratified environment target has been supplied, and upstream report-producing workflows/runs remain required |
| S119 — deployed Aux load-report production | A production-environment workflow verifies an HTTPS Aux endpoint is enabled on the exact requested catalogue publication, signs a fixed non-user load persona through an environment-only secret lookup, applies only protected request/concurrency/timeout/latency/error/throughput targets, and grants the accepted `aux-load-report` artifact name only to a passing version-bound run; breached runs finish failed with separately named aggregate diagnostics | Code checkpoint only; no deployed endpoint or protected load variables were supplied and no live load traffic was generated |
| S120 — governed offline-report boundary | A protected workflow accepts exactly one privacy-minimized replay file only from the named successful consented-holdout workflow, emits the accepted offline artifact name only for an eligible exact-publication comparison, never re-uploads cases, and constrains case shapes, bounds, opaque IDs and aggregate slice labels; the rollout packager now also pins the exact offline/load producer workflow names and refuses reuse of one run as both sources | Code checkpoint only; the separately approved consent design and real `Aux RE consented holdout replay` producer do not yet exist, so no real offline report can be produced and Aux remains ineligible for promotion |
| S121 — shadow-only Aux deployment boundary | Aux now has a no-scale-to-zero Fly topology and protected production workflow that requires a pre-provisioned governed HTTPS Qdrant host, API-key authentication, an exact hash-derived immutable collection and manifest row count, secret-safe Fly injection, and post-deploy shadow/publication metadata; public/ambiguous Qdrant URLs are rejected and neither Aux override nor Edge active mode can be enabled | Code checkpoint only; no Fly app, Qdrant endpoint, collection, secrets or production approval was supplied, the workflow has not run, and catalogue publication/upload plus Ghar publication delivery remain separate unmet deployment steps |
| S122 — one immutable catalogue across both engines | A project-verified read-only production workflow builds one user-free three-file publication; a lineage-bound Qdrant workflow creates and exact-count verifies the new hash-named collection using an environment-only API key; Aux deployment now requires that exact upload report; and a separate lineage-bound Ghar workflow bakes the same manifest/JSONL/SQLite publication into its image, fails the build when required files are absent, and verifies live metadata after deployment | Code checkpoint only; migration 097, production credentials, approved Qdrant, Fly targets and environment approvals were not supplied, none of the workflows ran, and the live approved/publishable count remains unknown |
| S123 — atomic modernization deployment and operator sequence | A main-only, protected production workflow verifies exact database identity and prerequisite state, refuses a partially applied 092–101 schema, applies all ten migrations plus validations 944–953 in one serialized transaction or revalidates a complete schema read-only, and emits identity-free evidence; the ACTIVE runbook defines the exact off → publish → dual-engine deploy → shadow → approved canary sequence plus user-first and exceptional database rollback | Code checkpoint only; no workflow ran, Edge has no dedicated protected off-to-shadow/canary mode-control workflow, the consented real-outcome producer and ratified targets remain absent, and no production migration/publication/deployment is claimed |
| S124 — protected off/shadow transition and main-branch lineage | One production workflow always forces Edge to `off` before evaluating a requested transition, permits only `off` or evidence-only `shadow`, requires exact successful main-branch Aux/Ghar/load runs plus matching live publication/version/count before shadow, writes identity-free transition evidence, and serializes with the automatic kill switch; every catalogue/engine/Edge workflow in that trusted chain is now main-only and downstream consumers verify source branch | Code checkpoint only; no workflow ran or secret changed, live Ghar still reports the legacy 810-dish bundle, no Aux Fly app/publication/Qdrant upload is deployed, and user-visible canary activation remains intentionally absent pending consented evidence, ratified targets and explicit approval |
| S130 — Phase A deployed with Aux routing off | Protected runs applied migrations 092–101, published and indexed one immutable 642-dish generation, deployed the same generation to Ghar and an isolated one-Machine Aux service, deployed the updated Edge functions after 151 tests, passed boundary smoke, and reasserted the production Edge switch as `off` with all shadow-only steps skipped | Orders 1–9 deployed; Ghar remains user-authoritative and no request is routed to Aux. Authenticated cold-start/experienced-user smoke still requires an explicitly selected test household. Phase B load, shadow, offline evidence and canary remain unexecuted and unauthorized |
| S139 — meal-class remediation evidence audit | Migration 105 and validation 957 expose a service-only aggregate provenance report; protected run `31257875325` reconciled all 255 low-confidence otherwise-ready mappings as 238 primary and 17 secondary chef-rubric outputs, all provisional internal research, with zero curated-exact, human-reviewed or accepted evidence | Aggregate audit deployed and passed; no mapping, dish, catalogue, engine or Aux routing changed. Independent proposal validation and human-review routing remain required before confidence or publication can change |
| S140 — governed primary/component serving-role foundation | Migration 106 separates accepted slot-aware staple/side/accompaniment compatibility facts from non-serving proposals, validates published grammar/slot/role consistency, normalizes `snack` to canonical `snacks`, exposes a service-only aggregate readiness report, and provides exact validation/rollback plus a protected workflow | Protected run `31258906340` installed and validated the foundation, measuring 603 primary-ready, 262 primary-review and 537 component-review dish-slot routes with zero proposals/facts. Publication and both engines remain unchanged; Aux stays OFF |
| S141 — complete active-inventory serving-role audit | Additive migration 107 preserves v1 evidence and adds dish-level routes, explicit missing/unrecognized canonical-slot counts and exact reconciliation of every active dish plus every valid dish-slot | Protected run `31259220512` installed and validated v2: 802 active dishes have canonical slots, 2,600 do not, 2,596 lack hero roles and 918 carry unrecognized slot labels. No serving change; Aux stays OFF |
| S142 — fixed-category meal-slot source audit | Migration 108 joins only production catalogue import lineage for slotless dishes, converts raw course values inside the database to fixed direct/contextual/conflict/missing categories, and emits reconciled aggregates with raw text and identities structurally excluded | Protected run `31267459809` installed and validated it: 1,802 single-direct candidates, 797 contextual review cases and one conflict. No proposal or serving change; Aux stays OFF |
| S145 — governed direct meal-slot proposal foundation | Migration 109 creates service-only pending proposals with immutable source-row evidence, exact-count and idempotency gates, a forward-only reviewed lifecycle, evidence-preserving rollback and a protected production generator that cannot alter dishes, publication or serving | Protected run `31269668506` installed and validated the foundation, creating exactly 1,802 pending proposals with 7,222 evidence links: 667 lunch, 566 snacks, 294 dinner and 275 breakfast. No proposal was approved/applied, no serving/publication changed and Aux stays OFF |
| S147 — bounded direct meal-slot proposal review | Migration 110 exposes a service-only read-only report with exact status/evidence/freshness reconciliation and a deterministic 1–25-name sample per slot; identifiers, raw source text and all user data remain excluded, with exact validation/rollback and a protected review workflow | Protected run `31270121136` installed and ran it: all 1,802 proposals remain pending/fresh, all 7,222 links reconcile at 4–8 per proposal and a 40-name sample confirms slots span both heroes and components. No proposal decision, dish/publication/serving change or Aux routing occurred |
