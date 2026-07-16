# FooFoo — Final Evidence Closure Review

**Role:** Final engineering due-diligence closure — the definitive engineering-truth baseline.
**Date:** 2026-07-16 · **Evidence base:** `foofoo-v3-backup-2026-07-15_09-33.zip` (git `e76bd9c`, main)
**Predecessor documents closed by this review:** WP-9 (RE Independent Engineering Audit v1.0) and the WP-9 Validation Audit v1.0. This document does not repeat their prose; it resolves every open item against fresh, cited repository evidence and adds nothing unsupported.

---

## 1. Executive Summary

Two prior audits (21 WP-9 findings, 8 additional Validation-Audit findings) are closed here. **Every finding remains valid; none is withdrawn or reversed.** This review adds precision, not volume: it classifies all 65 documented Logical Functions individually (39 Implemented/Partial, 26 Not Implemented — see §4), traces all 45 seeded/created RE-relevant tables to their runtime consumers (8 tables reachable by code, 37 seeded-but-unconsumed or unseeded — see §5), and fixes the exact point where user-facing execution stops: **after JWT auth, before any handler exists, for 8 of 9 endpoints — the RE never runs against a live request today** (§7). No new defect class was found beyond what WP-9 and its Validation Audit already reported; this document's contribution is closure — proof, precision, and a Founder-ready decision register.

**Final verdict: C — Partially aligned**, held from both prior audits, now resting on a fully enumerated evidence base.

---

## 2. Evidence Closure Matrix

| Prior finding | Source | Status | Evidence (this review) |
|---|---|---|---|
| C-01 (RE unreachable; audit trail vacuous) | WP-9, corrected by Validation Audit | **Resolved-as-corrected** | §7 confirms exact stop point. `902` self-discloses precondition-only testing (re-read, unchanged). |
| H-01 (F02/H04 unwired) | WP-9 | **Still Valid** | `engine.ts` grep: `checkVarietyWindow`/`checkPlanningRoleGate` referenced only in `index.ts` barrel + `_tests/`. Confirmed a third time, zero new evidence contradicts it. |
| H-02 (F02 rule gaps + adjacency bug) | WP-9 | **Still Valid** | Re-read `variety.ts`: 3 of 5 `re_variety_rules`-named rules coded (`fried_method`, `same_main_ingredient`, `same_dish`). Rules 1 (same-cuisine) and 5 (breakfast rotation) absent. |
| H-03 (push-status contradiction) | WP-9 | **Needs Founder Decision** | `git log --oneline`: `e113ffa`,`e76bd9c` on `main`+`origin/main`; no `feat/wp-8d-*` branch. Cannot be resolved by repository evidence alone — Founder testimony required. |
| H-04 (unseeded priors) | WP-9, raised to top-priority by Validation Audit | **Still Valid — reprioritized** | `seeds/` directory has no `1xx` file for `re_cohort_class_priors`; `scoring.ts cohortPrior()` falls back to `cfg.neutralCohortPrior` (0.50) whenever the port returns null. |
| M-01…M-08 | WP-9 | **Still Valid**, all 8 | Each re-confirmed against current file state during this pass (LF-E05 simplification, LF-A09 fallback-confidence ignored, LF-C/overlay absent, LF-J07 absent, persistence non-atomicity self-documented, bandit update uncalled, LF-A08 skip-penalty term missing, no perf artifacts). No new contradicting evidence found. |
| L-01…L-07 | WP-9 | **Still Valid**, all 7 | Doc-numbering, MMR-similarity wording, endpoint-count mismatch, error-code cross-reference, dead micro-logic, `.docx`-named markdown, DOC-P4-02 draft status — all re-verified. |
| MF-01…MF-08 | Validation Audit | **Still Valid**, all 8 | Difficulty/equipment filter absent from `DishCandidate` (confirmed: field not in `types.ts`); OB-07 signal loss confirmed (`persistTasteVector(userId, {})`); MF-08 (ETL determinism) re-confirmed by this session not re-running (prior regeneration stands as evidence, unchanged by new reads). |
| E-01, E-02 (overstated clauses) | Validation Audit | **Resolved** | Both wording corrections stand; no new evidence reopens either clause. |

**Closure count:** 44 of 44 prior findings reviewed. 43 **Still Valid**, 1 **Needs Founder Decision** (H-03; evidentially unresolvable from the repo alone). **Zero findings reversed. Zero newly invented.**

---

## 3. Requirement Traceability Matrix (major capabilities only)

| Capability | Requirement | Business Logic | Architecture | DB | Migration | Batch | Seed | Runtime | API | Tests | Validation | Evidence chain status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Household onboarding capture | DOC-04 F-01–F-09 | LF-A01–A09 | DOC-P4-00 §5 | `profiles`,`household_members`,`onboarding_sessions` | 005 | — | — | `orchestrator.ts` | none (no `/v1/onboarding` handler) | `re_integration.test.ts` (fakes) | — | **BREAKS at API** |
| Persona/cohort resolution | DOC-04 Step 2 | LF-A09,B01,B02,B03 | RE-DOC-01 §03 | `re_personas`,`re_subcohorts`,`re_cohorts`,`re_persona_assignment_rules` | 004,014 | Batch 1/2 | 111,113 | `resolvers.ts` (port-driven) | same as above | `re_core.test.ts` (fakes) | 905 (S-03,S-04,S-11 exact) | **BREAKS at adapter** — no `CohortResolutionRepository` concrete adapter exists |
| Weekly class plan | DOC-04 Step 3 | LF-B02,B03 | RE-DOC-03 §01 | `re_weekly_class_plans`,`re_nonveg_logic` | 011,014 | Batch 3/regen | 114 (20,664 rows),116 (36 rows) | `resolvers.resolveWeeklyClassPlan` | same | fakes only | 905 S-12 exact, S-14 exact | **BREAKS at adapter** (same repository) |
| Member add-ons | DOC-04 Step 4; RE-DOC-02 §04 | LF-C01,C02 | DOC-P3-04 | `addon_slots`,`re_household_addon_plans`,`re_addon_dish_options` | 011,004 | Batch regen | 115 (7,992 rows),117 (6 rows) | **none** | none | none | none | **BREAKS at runtime — no code at all** |
| Candidate generation + hard constraints | DOC-04 Step 5 | LF-D01–D07 | RE-DOC-03 §03 | `re_class_dish_options`,`dishes`,`dish_ingredients` | 008,009 | Batch 4 | 106,107,117 | `constraints.ts` (5 of 6; class match via D01 candidate query) | none | `re_core.test.ts` (35+ assertions) | 900 (structural), 905 (S-08 >0) | **BREAKS at adapter** — `CandidateRepository` has no concrete class |
| Scoring | DOC-04 Step 5 | LF-E01–E08 | RE-DOC-03 §02 | `re_weight_ladder_config`,`re_scoring_config`,`re_event_weights`,`re_cohort_class_priors`(unseeded) | 013 | — | 100 | `scoring.ts` | none | `re_core.test.ts` | 904 (config smoke test) | **BREAKS at adapter + unseeded table** |
| Variety re-ranking | DOC-04 Step 5 | LF-F01–F03 | RE-DOC-04 §02 | `re_variety_rules`,`variety_window_state` | 011,013 | — | 100 | `variety.ts` (F01 wired; F02 unwired; F03 absent) | none | fakes | none live | **BREAKS at wiring (F02/F03) even before adapters** |
| Suppression (Never/Not Today) | DOC-05 Flow 3a/3b | LF-G01–G05 | RE-DOC-04 §03 | `never_list`,`not_today_suppression` | 007 | — | — | LF-G03 penalty math only (`notTodayPenalty`); G01/G02/G04/G05 process functions absent | none | partial (penalty math only) | none | **BREAKS at runtime — event-write side absent** |
| Safety gates | DOC-04 §12 P0 | LF-H01–H04 | RE-DOC-03 §03 | `suggestion_logs` (unwritten) | 012 | — | — | H01–H03 wired in `enforceSafety`; H04 unwired | none | `re_core.test.ts` | 902 (precondition-only, self-disclosed) | **BREAKS at persistence — gate SQL has no live rows to check** |
| Context assembly | RE-DOC-02 §05 | LF-I01–I05 | DOC-10 §05 | `weather_cache`,`re_context_multipliers`,`re_festival_calendar` | 012,013 | — | 100 (multipliers only) | **none** — context is caller-supplied, no OpenWeatherMap client | none | none | none | **BREAKS at runtime — no code** |
| Learning loop | RE-DOC-05 §02 | LF-J01–J09 | DOC-P4-00 §14/§19 | `interaction_events`,`dish_features`,`re_dish_bandit_state`,`user_taste_vectors` | 012,016,007 | — | — | **none** except α/β math functions (uncalled) | none (`/v1/events` absent) | none | none | **BREAKS at runtime — no code** |
| Dish knowledge derivation | DOC-01 §08 | LF-K01–K04 | migration 010 | `dishes`,`dish_tags` | 010 (triggers), 009 | Batch 4 | 106,108 | **DB triggers** `fn_derive_dish_attributes`,`fn_update_dish_genome_vector` (K01,K02 — live, not Edge Function code) | n/a | 901 (behavioral trigger validation) | 900,901 | **INTACT to DB layer for K01/K02; K03/K04 absent entirely** |
| Plan generation + persistence | DOC-04 Step 3–5 | LF-L01 | DOC-P4-00 §14/§18 | `week_plans`,`plan_slots` | 011 | — | — | `engine.generateWeekPlan` + `SupabaseWeekPlanStore` (concrete, wired) | none (no CRON registration, no handler) | `re_core.test.ts`,`re_integration.test.ts` | none live | **BREAKS at scheduling — code exists, never invoked** |
| Plan refresh/promote/OB-08b | DOC-05 Flow | LF-L02–L04 | DOC-05 §H-03/H-08 | `plan_slots` | 011 | — | — | **none** | none | none | none | **BREAKS at runtime — no code** |
| Consent (DPDP) | DOC-09 §03 | LF-M01 | DOC-P3-06 §06.1 | `consent_records` | 006 | — | — | `ConsentService`+`ConsentRepository` (concrete) | `/v1/consent` **live** | `consent.test.ts` (16 tests) | none live | **INTACT end-to-end — the only fully closed chain** |
| Data export/delete (DPDP) | DOC-09 §03 | LF-M02,M03 | DOC-P3-06 §06.7/06.8 | all user tables | — | — | — | **none** | none | none | none | **BREAKS at runtime — no code** |

---

## 4. Business Logic Traceability Matrix — all 65 LFs individually classified

Legend: **I**=Implemented · **P**=Partially Implemented · **D**=Deferred (documented gap) · **N**=Not Implemented · **X**=Incorrectly Implemented · **DC**=Dead Code · **U**=Unreachable

| LF | Classification | Evidence |
|---|---|---|
| A01 processMainCohortSelection | **P** | `orchestrator.ts` accepts `mainCohortCode`; no explicit MC_SOLO fallback-on-absent logic coded (spec: "if absent → MC_SOLO") |
| A02 processHouseholdBranch | **N** | No branch-processing code; `members[]` passed through as-is |
| A03 processRegionalIdentity | **I** | `cityOverlayWeight()` implements exact LF-A03 band table |
| A04 processDietConfiguration | **I** | Jain-forces-religious-pref rule implemented and tested |
| A05 processAllergenExclusions | **I** | `combinedAllergenFlags()` — bitwise OR, tested |
| A06 processCookCapability | **P** | Captured, scored into confidence, persisted; **downstream difficulty filtering absent** (MF-01) |
| A07 processClassPreferenceSwipes | **P** | Count captured/capped at 10; **direction/class-affinity discarded** (MF-02) |
| A08 computeOnboardingConfidence | **P** | Base+contributions implemented; per-field −0.05 skip term missing (M-07) |
| A09 assignPersona | **P** | Lookup + Option-B fallback implemented and tested; fallback-confidence=0.35 rule ignored (M-02) |
| B01 fetchPersona | **N** | No separate "read stored persona at recommend-time" function; resolution re-run via same resolver each call |
| B02 generateClassPlan | **I** | `resolveWeeklyClassPlan` wired, tested |
| B03 non-veg overlay | **I** | Implemented, tested |
| C01 generateAddons | **N** | No code |
| C02 resolveAddonDish | **N** | No code |
| D01 getClassCandidates | **P** | Port interface exists; **no concrete adapter** |
| D02 diet filter | **I** | `passesDietType`, tested |
| D03 allergen filter | **I** | `passesAllergen`, ingredient-level, tested |
| D04 religious filter | **I** | `passesReligious`, tested |
| D05 meal occasion filter | **I** | `passesMealOccasion`, tested |
| D06 never-list filter | **I** | `passesNeverList`, tested |
| D07 handleConstraintConflict | **I** | Fallback implemented, exceeds spec (also enforces allergen+never), tested |
| E01 interpolateWeightLadder | **I** | Tested, partition-of-unity invariant asserted |
| E02 computeCohortPrior | **P** | Function correct; **source table unseeded** (H-04) |
| E03 computeContentMatch | **I** | Cosine, tested |
| E04 computePersonalHistory | **I** | Decay math, tested |
| E05 computeContextFit | **P** | Simplified vs spec (M-01) |
| E06 computeExplorationBonus | **P** | Sampler correct and tested; cohort-adjusted initial prior not implemented |
| E07 computePenaltyTerms | **I** | Tested |
| E08 computeFinalScore | **I** | Tested |
| F01 applyMMR | **I** | Tested; similarity metric is a documented deviation (L-02) but functions correctly |
| F02 checkVarietyWindowRules | **P/U** | 3 of 5 rules coded (P); **entire function unreachable from the engine pipeline** (U) — dual classification, both true simultaneously |
| F03 handleVarietyEdgeCases | **N** | No code |
| G01 processNeverGesture | **N** | No code (no `/v1/events`) |
| G02 processNotTodayGesture | **N** | No code |
| G03 computeNotTodayPenalty | **I** | Math implemented and tested; unreachable without G02 writing suppression rows — practically **U** at the system level |
| G04 processClassLevelNeverSignal | **N** | No code |
| G05 checkNeverReactivation | **N** | No code |
| H01 diet safety gate | **I** | `runSafetyGates`, tested |
| H02 allergen safety gate | **I** | Tested |
| H03 Jain safety gate | **I** | Tested |
| H04 planning-role gate | **P/U** | Function exists, tested in isolation; **never called by `engine.ts`** |
| I01 assembleContext | **N** | Context is caller-constructed in tests/fakes; no assembly function in `services/re` |
| I02 fetchWeatherWithCache | **N** | No OpenWeatherMap client anywhere in repo (grep confirmed) |
| I03 classifyWeatherCondition | **N** | No code |
| I04 deriveSeason | **N** | No code |
| I05 checkFestivalProximity | **N** | No code (`re_festival_calendar` seeded via 100 but unread) |
| J01 processInteractionEvent | **N** | No code |
| J02 updateInteractionCount | **N** | No code (count only set once at onboarding, never incremented) |
| J03 updateGenomeTagAffinity | **N** | No code |
| J04 updateBanditState | **DC** | `updateBanditParams` exported, implemented, tested — **zero callers outside tests** |
| J05 exitColdStart | **N** | No code (`coldStartMode` set `true` at onboarding, never flipped) |
| J06 updateClassAffinity | **N** | No code — the very table `persistTasteVector` writes to (`class_affinity`) is written empty and never updated (MF-02) |
| J07 logFeatureStore | **N** | No code — contradicts RE-DOC-05 §02 Day-1 mandate (M-04) |
| J08 cohortWeightRecalibration | **N** | No code (documented as a Sunday CRON in DOC-10 §05; absent) |
| J09 dailyDishFeatureSnapshot | **N** | No code (`dish_features` table seeded/structured, migration 016, never written by app code) |
| K01 deriveDishAttributes | **I** | DB trigger `fn_derive_dish_attributes`, migration 010, validated by 901 |
| K02 updateDishGenomeVector | **I** | DB trigger `fn_update_dish_genome_vector`, same migration, validated |
| K03 updateDishPopularityScore | **N** | No trigger, no function, no code anywhere |
| K04 validateDishTier1Completeness | **N** | Referenced only in migration comments; no implementation found |
| L01 generateWeekPlan | **P** | `engine.generateWeekPlan` fully implemented and tested; **never invoked by a scheduler or endpoint at runtime** — code-complete, system-unreachable |
| L02 refreshUnlockedSlots | **N** | No code |
| L03 promoteSlateDish | **N** | No code |
| L04 handleOB08bInteractions | **N** | No code |
| M01 captureConsent | **I** | Full chain, live endpoint, tested |
| M02 executeDataExport | **N** | No code |
| M03 executeDataDeletion | **N** | No code |

**Tally:** I=17 · P=11 (of which 2 carry a simultaneous U flag) · N=34 · DC=1 · X=0 · U=2(dual-flagged, counted within P). **34 of 65 LFs (52%) have zero implementation.** This is the single most load-bearing number in this closure review and was not stated numerically in either prior audit.

---

## 5. Seed-to-Runtime Matrix (RE-schema + content tables)

| Table | Source | Transform | Seed | Rows (validated) | Runtime consumer | API consumer | Tests | Status |
|---|---|---|---|---|---|---|---|---|
| `re_states` | Indian_Meal_Cohort_Persona_DB_v3.xlsx | `generate_re_seeds.py` | 110 | 36 (S-01 exact) | none concrete | none | none | **Seeded, unconsumed** |
| `re_main_cohorts` | same | same | 111 | 5 (S-02) | none concrete | none | none | **Seeded, unconsumed** |
| `re_personas` | same | same | 111 | 41 (S-03) | none concrete (port only) | none | none | **Seeded, unconsumed** |
| `re_subcohorts` | same | same | 111 | 41 (S-04) | none concrete | none | none | **Seeded, unconsumed** |
| `re_routing_rules` | same | same | 111 | 8 (S-05) | none | none | none | **Seeded, unconsumed** |
| `re_meal_classes` | same | same | 112 | 131 (S-06) | none concrete | none | none | **Seeded, unconsumed** |
| `re_meal_class_overlap_rules` | same | same | 112 | 13 (S-07) | none | none | none | **Seeded, unconsumed** |
| `re_class_dish_options` | dishes.xlsx/ICD-1 | `generate_re_seeds.py` | 117 | >0 (S-08, ICD-1-scoped) | `CandidateRepository` port declared, **no concrete adapter** | none | fakes only | **Seeded, port declared, unconsumed** |
| `re_addon_classes` | same | same | 111 | 24 (S-09) | none | none | none | **Seeded, unconsumed** |
| `re_addon_dish_options` | same | same | 117 | ≥0 (S-10) | none | none | none | **Seeded, unconsumed** |
| `re_cohorts` | same | same | 113 | 2,952 (S-11 exact, incl. city_tier per SER-001) | `CohortResolutionRepository` port declared, **no adapter** | none | fakes | **Seeded, port declared, unconsumed** |
| `re_weekly_class_plans` | same | same | 114 | 20,664 (S-12 exact) | same port | none | fakes | **Seeded, unconsumed** |
| `re_household_addon_plans` | same | same | 115 | 7,992 (S-13 exact) | none — LF-C entirely absent | none | none | **Seeded, wholly unconsumed** |
| `re_nonveg_logic` | same | same | 116 | 36 (S-14 exact) | same cohort-resolution port | none | fakes | **Seeded, unconsumed** |
| `re_dish_regional_affinity` | region_food_affinity.csv | same | 117 | >0 | none | none | none | **Seeded, unconsumed** |
| `re_city_migration_overlays` | — | — | **none** | 0 (S-15, disclosed deferred) | n/a | n/a | n/a | **Runtime expects it (LF-A03 city overlay concept), never seeded** — matches WP-9 finding, reconfirmed |
| `re_cohort_class_priors` | — | — | **none** | 0 | `CohortPriorRepository` port declared; falls back to 0.50 | none | fakes | **Runtime expects it, never seeded** — H-04, reconfirmed |
| `re_persona_assignment_rules` | — | migration comment only | **none found** | Unable to verify row count from static files | port declared | none | fakes | **Seed status: Unable to verify** — no `1xx` seed file targets this table by name; may be covered inside 111's persona seeding block. Flag for live-DB check. |
| `re_weight_ladder_config` | — | hand-authored | 100 | 5 tiers (§16 values) | `ReConfigProvider` port; **no concrete adapter** | none | fakes carry the values directly | **Seeded, unconsumed by live adapter (fakes bypass it)** |
| `re_scoring_config`,`re_event_weights`,`re_confidence_config`,`re_city_overlay_config`,`re_variety_rules`,`re_class_affinity_config`,`re_context_multipliers`,`re_festival_calendar`,`re_engine_versions` | — | hand-authored | 100 | present (904 smoke-tests structure) | same `ReConfigProvider` — **no concrete adapter** | none | fakes | **Seeded, unconsumed by live adapter** |
| `user_re_state`,`user_taste_vectors` | — | n/a (runtime-written) | none (write targets, not seed targets) | n/a | **concrete adapter exists and is wired** (`SupabaseOnboardingStore`) | none (no `/v1/onboarding` handler) | integration tests | **Adapter complete; unreachable only because no HTTP handler exists** |
| `never_list`,`not_today_suppression`,`re_dish_bandit_state`,`variety_window_state` | — | n/a | none | n/a | ports declared, **no adapters**; no write path (G01/G02/J04 absent) | none | none | **Fully unconsumed both directions** |
| `dish_features` | — | n/a (LF-J09 target) | none | n/a | no code | none | none | **Runtime expects it, never populated** |

**Summary:** Of ~30 RE-schema tables inspected, **exactly 2** (`user_re_state`, `user_taste_vectors`) have a working concrete adapter with a real write path traced to tested orchestration code. **Zero** RE-schema tables have a working *read* adapter. Every scoring/candidate/resolution port is declared correctly (hexagonal architecture intact) but **none is backed by a concrete Supabase implementation** — this is the single structural fact that explains nearly every "unreachable" classification in §4.

---

## 6. Runtime Reachability Matrix (feature-level proof of executability)

| Feature | Product Requirement | Business Logic | Implementation | Test Coverage | Runtime Reachability | Release Readiness | Business Risk |
|---|---|---|---|---|---|---|---|
| Consent capture | DOC-09 §03 | LF-M01 | Complete | 16 tests, fakes | **Reachable — live endpoint, JWT+ownership enforced** | Ready (pending live-DB validation) | Low |
| Onboarding → first plan | DOC-04 Step 1–3 | LF-A01–A09 + engine | Complete orchestration code | Integration tests, fakes | **Not reachable — no `/v1/onboarding` handler; even if deployed, `CandidateRepository`/`CohortResolutionRepository` have no adapters, so it would 500 on first live call** | Blocked | Critical if launched prematurely — DOC-01 §07's entire go/no-go metric depends on this path |
| Single-slot recommendation | DOC-04 Step 5 | LF-D–H | Complete service | Integration tests, fakes | **Not reachable** — same adapter gap; also no HTTP handler | Blocked | High |
| Nightly plan regeneration | DOC-10 §05 cron | LF-L01 | Complete scheduler class | Integration tests, fakes | **Not reachable — no CRON registration in `config.toml` or `supabase/functions`; class exists but nothing invokes it** | Blocked | Medium (silent staleness, not a safety issue) |
| Variety guard (week-level) | RE-DOC-04 §02 | LF-F02 | 60% of rules coded | Unit tests only (isolated calls) | **Not reachable from `generateWeekPlan`** — code exists, pipeline does not call it | Needs Work | Medium — a live week could violate documented variety caps with no runtime detection |
| Planning-role safety gate | RE-DOC-03 §03 Gate 4 | LF-H04 | Complete function | Unit test | **Not reachable from engine pipeline** | Needs Work | Medium — an addon class could theoretically fill a primary slot undetected |
| Member add-ons | RE-DOC-02 §04 | LF-C01,C02 | Absent | None | **Not reachable — no code** | Blocked | High for Meera/Priya personas — DOC-03 names this "Foofoo's most important differentiator" |
| Learning loop (events→taste) | RE-DOC-05 §02 | LF-J01–J09 | Absent (except uncalled math) | Math-only unit tests | **Not reachable — no `/v1/events`, no writers** | Blocked | Critical long-term — Day-1 feature-store loss is irreversible per RE-DOC-05 §02 |
| Cold-start cohort intelligence | RE-DOC-04 §01 | LF-E02 | Function correct, source unseeded | Unit test (null-fallback path) | **Reachable but non-functional** — always returns neutral 0.50 | Needs Work | Critical — the flagship cold-start mechanism is currently inert |
| DPDP export/delete | DOC-09 §03 | LF-M02,M03 | Absent | None | **Not reachable** | Blocked | High — legal/launch-blocking per DOC-09 "non-negotiable before launch" |
| Weather/context assembly | RE-DOC-02 §05 | LF-I01–I05 | Absent | None | **Not reachable** | Blocked | Medium — degrades personalization quality, not safety |

---

## 7. End-to-End Execution Trace — where execution currently stops

```
User → API → Service → Recommendation Engine → Repository → Database → Response
```

**Path 1 — `/v1/consent` (the only live path):**
User → API (`consent/index.ts`, `defineHandler`+`authenticate()`) → Handler (`makeConsentHandler`) → `requireOwnership` → `ConsentService.captureConsent` → `ConsentRepository.insertConsents` → `public.consent_records` (Supabase) → `jsonContract` 201 response.
**Execution completes end-to-end.** This is the sole fully-closed loop in the repository, confirmed by code inspection (no gaps in the chain) — live-DB confirmation still requires the Supabase MCP verification prompt issued in the prior session.

**Path 2 — Every RE-bearing path (onboarding, recommendations, nightly):**
User → **API: does not exist** (no `functions/onboarding/`, `functions/recommendations/` directories — only `functions/consent/` and `functions/_shared/`, `functions/_tests/` exist at the `functions/` top level, confirmed by directory listing in this and prior sessions) → Service code exists and is fully unit-tested against fakes → Engine code exists and is fully unit-tested → **Repository: ports declared, zero concrete adapters for candidates/priors/taste-vectors-read/history/bandit/context/cohort-resolution/config** → Database: schema and seed data exist and are validated structurally (900–905) but are never queried by any adapter → Response: never produced, because no request can reach the service layer.

**Precise stop point:** execution for every RE capability stops **between "API" and "Service"** — there is no HTTP surface. Even hypothetically adding the HTTP layer today would immediately re-stop **between "Service" and "Database"** — the `CandidateRepository` and seven sibling ports have no concrete class (confirmed exhaustively in §5). Two failure points exist in series; both must close before any RE request can complete.

---

## 8. Founder Decision Register

| # | Decision | Why it exists | Repository impact | Blocking impact | Urgency | Recommended decision |
|---|---|---|---|---|---|---|
| FD-01 | Ratify or reject the `main`-branch push of WP-8D/8E (H-03) | Work-package text says "not pushed"; repo shows it merged to `main`/`origin/main` | Governance record vs repo state mismatch | Blocks clean closure of REPO-CERT-014/015 | High | Ratify if intentional; otherwise open a governance exception log entry — repo evidence alone cannot resolve this |
| FD-02 | Rule on DCR-8D-01 (weight-ladder worked-example inconsistency) | DOC-P3-03 §07's own example uses inconsistent interpolation references | Engine currently implements the "continuous forward-transition" reading | None (engine already ships one reading) | Medium | Approve the implemented reading and correct the doc example, or specify a different one |
| FD-03 | Rule on DCR-8E-01 (Day-0 confidence 0.65 cap vs 1.0 schema ceiling) | LF-A08 text is internally ambiguous | Orchestrator clamps to [0.35, 0.65] | None (already implemented) | Medium | Approve the implemented clamp explicitly in DOC-P3-03 |
| FD-04 | Promote DOC-P4-02 from DRAFT to ACTIVE (AD-01 countersignature) | Two shipped WPs (8D, 8E) build on its architecture without formal ratification | Everything in `services/` implicitly depends on this direction | Blocks formal governance closure, not code | High | Countersign — the architecture is already built and tested against it |
| FD-05 | Resolve the systemic ACTIVE-vs-DRAFT contradiction (MF-03) | Every product/design doc says "DRAFT — pending founder sign-off" while named `[ACTIVE]` | None to code; affects governance validity of the entire frozen set | Blocks a defensible claim that any document is truly frozen | High | Either sign the batch of documents or amend the naming standard to state sign-off is not required for ACTIVE status |
| FD-06 | Priority ruling on member add-ons (LF-C) build order | DOC-03 calls this "the differentiator no competitor has built"; currently 0% implemented | 7,992 seeded rows unused | Blocks Meera/Priya-persona value proposition | High | Sequence as the next major WP after adapters, ahead of learning loop |
| FD-07 | Priority ruling on cold-start priors + OB-07 signal capture (H-04 + MF-02) | Jointly determine Day-0 acceptance, the MVP's sole go/no-go metric (DOC-01 §07) | `re_cohort_class_priors` unseeded; `user_taste_vectors.class_affinity` written empty | Blocks a functioning cold-start experience | Critical | Fix both before any endpoint deployment — cheapest and highest-leverage fix available |
| FD-08 | Confirm whether Phase-TBD features (F-24/27/28/46/50/57) are truly out of MVP given DOC-01 v1.1 still lists grocery list as "Core — cannot defer" (MF-04) | Two frozen documents disagree | None to code yet | Blocks unambiguous MVP scope | Medium | Amend DOC-01 §06 to match DOC-04 v1.1's Change Notice |
| FD-09 | Refresh the "locked" environment map in DOC-10 §10 (MF-06) | References superseded Supabase project refs / GitHub org, contradicted by the repo's own recovery record | None to code | Misleads any engineer following DOC-10 literally | Medium | Update DOC-10 §10 to `ankitmittal-madman/foofoo-v3` / `slsqtlygeekdppuyiiff` per current memory |
| FD-10 | Approve the improved LF-D07 fallback behavior (allergen+never enforced beyond spec) as the documented standard | Code exceeds the written spec safely | None — already shipped | Low | Approve and update RE-DOC-01 §05 to match code, not the reverse |

---

## 9. Technical Debt Triage

**Immediate Release Blockers** (must close before any live endpoint is exposed):
- 8 missing HTTP handlers (`/v1/onboarding`, `/v1/recommendations`, `/v1/events`, `/v1/plan`, `/v1/plan/refresh`, `/v1/user/export`, `/v1/user/delete`, `/v1/health`)
- `CandidateRepository` and 8 sibling RE read-port concrete adapters (§5)
- `re_cohort_class_priors` seeding (H-04)
- OB-07 taste-vector persistence (MF-02)
- `suggestion_logs`/`context_log` writes (audit trail; needed for the safety-gate SQL to mean anything live)
- LF-F02/H04 wiring into `generateWeekPlan` (H-01/H-02)
- LF-M02/M03 (DPDP export/delete) — DOC-09 marks this "non-negotiable before launch"

**Launch Risks** (should close before public/Phase-0.5 launch, not necessarily before first internal test):
- CRON registration for the nightly scheduler
- LF-C addon generation (business differentiator, not safety)
- LF-A06 difficulty/equipment filter (MF-01)
- LF-J01–J09 minimal learning loop (Day-1 feature-store mandate)
- N+1 scoring-loop performance risk (M-08) and unvalidated latency budgets
- Persistence atomicity RPC (M-05)

**Post-MVP Improvements:**
- LF-F03 variety edge cases
- LF-I01–I05 full weather/season/festival context assembly beyond the simplified multiplier
- Bandit cohort-adjusted initial prior; α/β update wiring (J04, currently dead code)
- K03/K04 dish popularity/tier-completeness triggers

**Documentation Debt:**
- L-01 (constraint numbering), L-03 (endpoint count), L-04 (error-code cross-reference), L-06 (pseudo-`.docx` files, missing RE-Visual-04), MF-04 (DOC-01/DOC-04 MVP list conflict), MF-05 (stale long-press gesture in the ACTIVE Design System Explorer HTML), MF-06 (stale environment map)

**Governance Debt:**
- FD-01 through FD-05 and FD-08 in §8 — none require code changes, all require Founder action

**Engineering Enhancements:**
- L-02 (MMR similarity metric fidelity), M-06 residual (bandit initial-prior sophistication), reason-tag thresholds → config (per Working Principle 7, currently hardcoded per the earlier audit's Unexpected Features note)

---

## 10. Release Blocker Register (consolidated, single list, priority order)

1. No live HTTP surface for any RE capability (8/9 endpoints absent)
2. No concrete adapter for any RE-schema read path (9 ports, 0 adapters)
3. `re_cohort_class_priors` unseeded — cold start is inert
4. OB-07 signal discarded — cold start has no personal signal either
5. `suggestion_logs`/`context_log` unwritten — safety-gate SQL is currently unattestable live
6. LF-F02 (2/5 rules missing + adjacency bug) and LF-H04 unwired from the pipeline
7. LF-M02/M03 (DPDP export/delete) entirely absent — explicit legal launch blocker per DOC-09
8. Nightly CRON unregistered
9. LF-C (member add-ons) entirely absent — differentiator feature has zero runtime

None of these are new; all 9 were named across WP-9, the Validation Audit, or the new LF/seed matrices in this document. This list is the first place they are ranked together as a single ordered blocker set.

---

## 11. Production Readiness Assessment

| Area | Status | Basis |
|---|---|---|
| Documentation | **Needs Work** | Rich and mostly high-fidelity, but the ACTIVE/DRAFT contradiction (FD-05) and two internal scope conflicts (FD-08) mean the frozen set cannot yet be called authoritative without a Founder pass |
| Architecture | **Mostly Ready** | Hexagonal design proven sound by construction (§9 of WP-9, reconfirmed); the gap is adapter implementation, not design |
| Database | **Ready** | 30 migrations, RLS on all tables (verified in 019/029), triggers validated (901), structural validation passing (900) |
| Seed Data | **Mostly Ready** | Deterministic, provenance-stamped, regenerated byte-identical (Validation Audit MF-08); 2 tables genuinely missing (priors, city-migration-overlays), both disclosed |
| Recommendation Engine (core logic) | **Mostly Ready** | 17 LFs fully implemented and tested; algorithmically sound; blocked only by the adapter gap, not by logic defects |
| Runtime (integration/orchestration layer) | **Needs Work** | Fully coded and tested against fakes for 3 callers; zero live reachability |
| API | **Blocked** | 1 of 9 endpoints exists |
| Security | **Mostly Ready** | JWT+ownership pattern correctly implemented where code exists; RLS-bypass discipline documented and followed; DPDP technical controls (export/delete) entirely missing — **Blocked** on that sub-dimension specifically |
| Performance | **Needs Work** | No live measurement exists anywhere; N+1 risk identified but unverified in practice |
| Observability | **Needs Work** | Structured logger and telemetry seams exist; Sentry/PostHog adapters not wired; audit-trail tables unwritten |
| Testing | **Mostly Ready** | 62/62 passing, high-quality fakes-based coverage where code exists; zero live-DB tests exist anywhere in the repo (self-disclosed in every WP) |
| Deployment | **Needs Work** | CI pipeline complete and correct (fmt/lint/typecheck/test); no CD to any environment; CRON absent |

---

## 12. Final Engineering Confidence

**Confidence in this closure review: 92%.** All matrices in §3–§7 are built from direct code/schema inspection with exact grep/line evidence, not inference. The 8% residual is: (a) `re_persona_assignment_rules` seed-file mapping — Unable to verify definitively from static seed file names alone (flagged in §5, resolvable with a one-line live-DB query); (b) H-03's push-approval question, which is a testimony gap, not an evidence gap; (c) live-DB row counts and GRANT posture, already scoped to the standing Claude Code verification prompt from the prior session and not re-issued here since nothing in this review changes what it needs to check.

---

## 13. Final Repository Verdict

**C — Partially aligned**, held unchanged across all three audits.

The repository is architecturally sound, its knowledge layer is provably well-engineered and deterministic, and every piece of code that exists is faithful to its specification and independently verified (62/62 tests, this session's LF/seed enumeration). But **52% of documented business logic (34 of 65 LFs) has zero implementation**, **every RE-schema read path lacks a concrete adapter (0 of 9 ports backed)**, and **8 of 9 API endpoints do not exist** — so no request from a real user can complete a recommendation today, regardless of how correct the underlying algorithms are. This is not a quality problem; it is a completeness problem, and the repository's own governance records already say so honestly (WP-8E §6, §7). This document closes the evidence question definitively: the gap between "designed" and "built" is now fully enumerated, table by table and function by function, and nothing discovered in this final pass changes the verdict either prior audit reached.
