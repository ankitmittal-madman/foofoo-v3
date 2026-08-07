# Auxiliary recommender production-readiness report

## Current verdict (2026-08-07)

The auxiliary stack is ready for local and production-traffic **shadow validation**, not active
selection. Canonical data, Qdrant artifacts, the feature contract, a trained LightFM hybrid model,
offline comparison, runtime loader, container packaging, and recurring CI gates now exist. The
synthetic-data guard is enforced in code: shadow can score, while compare/active cannot apply this
artifact. LightGCN and KGAT are correctly deferred. See `DATASET_AND_MODEL_REPORT.md` and
`data/reports/quality_gate_v1.json` for measured evidence.

## Implementation audit

Production-safe and exercised:

- Independent FastAPI deployment, Docker image, health/readiness endpoints, and per-request kill
  switches.
- Immutable existing-result boundary and deterministic shadow/compare/active policy gate.
- Local request pool, JSON pool, current Qdrant Query Points adapter, and local food-graph candidate
  expansion. Each optional source fails independently.
- Feature-hash recipe/context embeddings, dietary/allergy/meal-slot rules, household-aware weighted
  ranking, pantry/freshness/region features, popularity debiasing, novelty penalty, and MMR-style
  diversity selection.
- Structured reason codes, model/version/readiness metadata, trace IDs, stage latencies, decision
  logs, and process-local operational metrics.
- Labeled offline replay harness and unit/integration/end-to-end/failure tests.

Partially implemented:

- The versioned Indian food graph contains canonical dishes and typed ingredient, diet, region,
  cuisine, meal-slot, and cooking-technique relations, but ingredient coverage is only 43.0% and
  provenance/reviewer workflows are not yet production-grade.
- The feature-hash embedder is deterministic and useful for Qdrant plumbing, but is not a learned
  Recipe2Vec representation and has no semantic-quality benchmark.
- Household fit blends member preference overlap, but does not model preference strength,
  negotiation roles, child/adult nutrition targets, or time-varying taste.
- Metrics are process-local and reset at restart; logs require an external collector/dashboard.

Explicitly deferred, not claimed as working:

- RecBole LightGCN, KGAT, FairRec, Debias, CDR, and DA remain disabled or `scaffold_only`.
  LightFM is implemented and trained, but is shadow-only until real interaction and online evidence
  replace the synthetic training basis.
- Exploration is reported as `not_implemented`; active output is deterministic exploitation only.
- The product Edge still needs to call this service with the existing engine output. No existing
  recommendation code was edited, which preserves isolation but means deployment alone does not
  route production traffic through the comparator.

## Verification checklist

Automated checks currently prove:

- Qdrant requests use a local-only URL, a 64-dimensional deterministic query vector, meal-slot
  payload filtering, bounded timeout, and structured candidate parsing.
- Request, graph, and Qdrant candidates deduplicate; failure of one source preserves healthy sources.
- Allergy aliases, dietary restrictions, unavailable ingredients, and meal slot reject candidates
  before ranking.
- Region, household preference, pantry contents, and recent meals can change the top-ranked dish.
- Popularity contributes a bounded debias score and overlapping ingredients receive a diversity
  penalty.
- Disabled and shadow modes preserve the existing payload byte-for-data-equivalent; compare/active
  require confidence, improvement, safety, diversity, alignment, and override gates.
- Identical inputs produce identical rankings and policy decisions.

Still needed before active production rollout:

1. Build a time-split, household-disjoint offline dataset from impressions, selections, skips,
   substitutions, completions, repeat cooks, and explicit feedback. Include negative exposure data,
   not only positive interactions.
2. Define promotion gates for Recall@K, NDCG@K, MAP@K, constraint-violation rate, catalogue coverage,
   intra-list diversity, novelty, calibration, regional slices, household slices, and latency p95/p99.
3. Retrain and register LightFM on consented real events using the existing stable household, dish,
   and context contracts. Train LightGCN only after at least 5 positive events exist for a broad
   household cohort; train KGAT only after interaction and ontology gates both pass.
4. Build an ingredient canonicalization service covering Indian-language aliases, transliteration,
   packaged ingredients, derivatives, cross-contact, and quantity-aware substitutions. The current
   alias table is deliberately small.
5. Build a governed Indian dish/ingredient/region/season/occasion/technique ontology with provenance,
   review workflow, graph validation, and snapshot versioning.
6. Add nutrition-aware objectives based on portion size, household-member requirements, conditions,
   weekly nutrient balance, and clinician-reviewed safety policy. Current `nutrition_fit` is an input
   feature, not independently calculated.
7. Add long-term taste state with recency decay, repeated exposure, household-member attribution,
   fatigue windows, novelty tolerance, and cross-slot/week diversity budgets.
8. Add constrained exploration: logged propensities, epsilon/Thompson policy, safety exclusions,
   novelty budgets, and off-policy evaluation. Never evaluate exploration from click-through alone.
9. Wire shadow traffic at the Edge, persist impression-level comparison traces, then run a staged
   interleaving/A/B program with guardrail metrics and automatic rollback. The service must not call
   the existing engine itself.
10. Export OpenTelemetry/Prometheus metrics to durable storage; add dashboards and alerts for fallback,
    constraint violations, source health, feature drift, score drift, win rate, and latency.
11. Add automated replay, drift detection, retraining, artifact validation, canarying, and champion/
    challenger rollback. Current retraining is manual/nonexistent.
12. Add load, soak, chaos, Qdrant outage, corrupt-artifact, high-cardinality, and catalogue-scale tests.

## Risk report

- Comparator quality depends on baseline metrics supplied inside the opaque existing result. Missing
  metrics use conservative defaults, but uncalibrated scores from two systems are not inherently
  comparable. A shared calibration dataset is required.
- Qdrant vector dimension is fixed at 64 and must match the collection schema. The feature hash has
  collisions and weak semantics; it is a safe retrieval baseline, not mature personalization.
- Logs include recommendation payloads when `AUX_REC_LOG_ALL=true`. They exclude request identity but
  still require retention, access-control, and DPDP review because meal choices may reveal sensitive
  dietary information.
- In-process counters reset on restart and are not suitable for SLO enforcement.
- Runtime configuration is re-read per request for fast rollback, but malformed per-model switches
  can cause auxiliary fallback after readiness has passed. Central validated configuration is needed.
- Local JSON artifacts are read on requests and can create latency or consistency issues at scale.
  Production should load immutable, checksummed snapshots at startup and swap atomically.
- The service endpoint currently has no service-to-service authentication or rate limiting. Keep it
  private until it gains the same boundary controls as the main recommender.
- A caller can supply inaccurate candidate safety metadata. Safety should ultimately resolve against
  a governed canonical ingredient/allergen source, not trust candidate payloads.
