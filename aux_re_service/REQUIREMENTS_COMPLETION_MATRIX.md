# Final requirements completion matrix

Status meanings: **done** is implemented and verified locally; **shadow-ready** is deliberately
blocked from active production; **integration-ready** needs real product traffic or data; **deferred**
failed an explicit readiness gate.

| Ask | Status | Repository evidence / remaining condition |
|---|---|---|
| Separate optional auxiliary service | Done | FastAPI service, independent container, no import from the existing engine |
| Disabled, shadow, compare, active, instant fallback | Done | Config, comparator, immutable existing result, failure tests |
| Real Qdrant dish vectors and filters | Done | 86 v2 dish vectors/payloads; live local upload/query; slot, region, diet, allergy and ingredient filters |
| Canonical Indian food ontology | Done v2 | Dish/alias/ingredient/allergy/diet/cuisine/region/slot/category/spice/nutrition-trait/season/occasion/technique/substitute nodes and typed relations |
| Regional cuisine and home-food research | Done for supplied evidence | `INDIAN_HOME_FOOD_BEHAVIOR.md`; authoritative grounding plus dataset-derived patterns and caveats |
| Dataset inventory/schema/gap audit | Done | Checksummed audit, complete workbook inventory, FK/PK/missing/label/temporal checks, canonical `schema_map.json` |
| Realistic cloned interactions and negatives | Done | 64,842 interactions: recommendation, meal, member, dish-preference and substitution evidence; 17,459 negatives |
| Reusable household feature pipeline | Done | Demography, members, decision model, diet, fasting, spice, region, cooking capacity, equipment, health, exclusions, history and context |
| Weekly planning signals | Done | 10,000 household weekly-signal rows; runtime weekly repetition, schedule, leftover, season and occasion features |
| Household/member food graph | Done | 29,020 `preferred_by`, `avoided_by`, and `consumed_by` edges |
| Real feedback instrumentation | Integration-ready | Idempotent `/v1/feedback`, vote/substitute validation, local durable store and normalization pipeline; needs consented product calls |
| LightFM baseline | Shadow-ready | v2 WARP hybrid, negative-aware, 4,219-household holdout; beats popularity; synthetic artifact blocked in active mode |
| LightGCN | Deferred | RecBole export exists; blocked by zero real interactions and only 4,357 households with five positive synthetic events |
| KGAT | Deferred | KG/links export exists; same interaction blockers plus only 43.0% ingredient coverage |
| Fairness/diversity/debias | Done locally, frameworks deferred | Household aggregation, popularity debias and MMR diversity are active; FairRec/Debias/CDR/DA packages remain scaffold-only until real slice benchmarks justify them |
| Local reranker and calibration | Done baseline | Weighted deterministic household/region/pantry/freshness/nutrition/weekly/spice ranking with confidence and comparator gates |
| Hard safety | Done | Allergy, diet, unavailable ingredient, member restriction and meal-slot filtering before ranking |
| Offline evaluation | Done | Recall, precision, NDCG, coverage, diversity, novelty, repetition, safety, household/region/pantry/freshness fit, latency, fallback and win-rate support |
| Holdout/scenario/before-after/ablation | Done | Train/validation/test tables, replay harness and `compare_scorecards` promotion comparison |
| Monitoring | Done locally | Trace IDs, model versions, stage latency, failures, fallback/win/diversity/repetition/feedback counters and Prometheus text endpoint |
| Shadow testing | Done locally | Live Docker + Qdrant shadow flow keeps the existing result and records model/retrieval evidence |
| A/B framework | Integration-ready | Stable household control/treatment assignment; control cannot override; needs production traffic and outcome logging |
| Recurring code/data/model/weekly/monthly gates | Done | Change-triggered plus weekly/monthly workflow, artifact checks, tests, live container flow and retained reports |
| Active production rollout | Blocked correctly | Requires real training data, online shadow/interleaving evidence, service authentication and operational SLOs |

## Conditional asks

LightGCN and KGAT were requested **after enough data / ontology maturity**. Their input exports and
switches exist, but training or enabling them now would turn random synthetic structure into a false
quality claim. The machine gate records the blockers and keeps both unavailable.

Actual real-user feedback, online shadow comparisons, A/B outcomes, dashboards, alerts, and active
rollout cannot be manufactured inside a local repository. The collection, assignment, metrics, and
fallback paths are implemented; completing those items requires authorized production integration
and consented traffic.
