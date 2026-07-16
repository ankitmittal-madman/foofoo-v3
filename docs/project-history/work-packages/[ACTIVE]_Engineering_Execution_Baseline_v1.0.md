# Engineering Execution Baseline v1.0

**Status:** ACTIVE — Verification Engineer output. Read-only steps 1–2 (live verification); no commits, migrations, or schema changes made. This document converts three prior audits into an executable backlog.
**Version:** v1.0
**Date:** 2026-07-16
**Placement:** docs/project-history/work-packages/
**Role:** Verification Engineer (not an auditor) — every prior finding is treated as a hypothesis, spot-checked where a live tool made that possible, then converted into Epics. No prior finding is re-derived from scratch; none is silently overwritten.
**Predecessor documents (do not repeat their prose; consult directly for full evidence):**
- `docs/project-history/work-packages/[ACTIVE]_WP-9_Validation_Audit_v1.0.md`
- `docs/project-history/work-packages/[ACTIVE]_Final_Evidence_Closure_v1.0.md` (current baseline going into this pass)
- `docs/project-history/work-packages/[ACTIVE]_WP-9_Independent_Engineering_Due_Diligence_Audit_v1.0.md` (this session's own prior audit — different evidence base and scope, see §0 reconciliation below)

---

## 0. Evidence-Base Reconciliation (read this before anything else)

The two pasted documents (Validation Audit, Final Evidence Closure) were built against a repository snapshot frozen at git `e76bd9c` — the commit immediately after WP-8E, **before WP-8F and WP-8FA existed**. Those two work packages (`a30a135`, `d221caa`) are already merged to `main` today and did the exact deep-dive the Closure Review calls an open, wholesale blocker: the `CandidateRepository` / `re_class_dish_options` adapter gap.

**This is not a contradiction of the Closure Review's evidence — it is newer evidence the Closure Review's snapshot could not see.** Per the instruction not to silently overwrite prior conclusions, the Closure Review's §3/§5/§9/§10 language ("no concrete adapter exists," "CandidateRepository … no adapter") is preserved verbatim in this document wherever quoted. But **Epic 1 below (Repository Adapters) is scoped using the newer WP-8F/WP-8FA findings**, because building against the Closure Review's framing alone ("fully blocked, adapter design unknown") would mean redoing already-completed mapping work. Specifically, per `REPO-CERT-018`/`019` (WP-8F/WP-8FA), of the 4 originally-unprovable `DishCandidate` fields:
- `cuisineFamily` and `hasBeef`/`hasPork` — **derivable now, no schema change, no Founder decision needed** (`dishes.cuisine_id → cuisines.cuisine_group`; canonical beef/pork ingredient rows already seeded, joined via `dish_ingredients`).
- `mainIngredientClass` — **still blocked, genuinely needs a Founder ruling** on a "dominant ingredient" rule (`ingredients.category` exists in source data but was never seeded and has no defined derivation rule).
- `hasNonHalalMeat` (halal), `seasonalAffinity`, cohort-average cold-start prior — **documented MVP deferrals**, not blockers (matches Closure Review H-04/M-01 on the cold-start prior specifically).

Everything else in the Closure Review (LF classification table, seed-to-runtime matrix, root causes) is treated as current and authoritative — it was not superseded by WP-8F/8FA, which touched only the `CandidateRepository` mapping question.

---

## 1. Executive Summary

Three audits (WP-9, WP-9 Validation Audit, Final Evidence Closure) agree on a **C — Partially aligned** verdict: an unusually clean, well-tested, hexagonal Recommendation Engine core (62/62 tests passing) sits behind a database and knowledge layer that is fully seeded and structurally validated — but is disconnected from any live request path. 52% of documented business logic (34 of 65 LFs) has zero implementation, zero RE-schema tables have a working read adapter, and 8 of 9 API endpoints do not exist.

This session's live verification (Step 1, via Supabase MCP against project `slsqtlygeekdppuyiiff`) **confirms the Closure Review's central claims with production data** and resolves one of its two disclosed uncertainties (`re_persona_assignment_rules` is in fact seeded — 41 rows). It also surfaces **two genuinely new findings** the prior audits could not have found without live access: a live Supabase security-advisory false-positive on `re_engine` schema RLS (verified non-exploitable — see §2.4), and **two live migrations with no corresponding file in `database/migrations/`** (§2.1) — a real reproducibility gap in the repository's own GREEN-certification guarantee.

Everything not implemented collapses into **four engineering root causes plus one governance track** (§3) — not 34 separate problems. The backlog in §4 sequences nine Epics to close them, starting with repository adapters (now materially de-risked by WP-8F/8FA) and ending with post-MVP context assembly.

---

## 2. Live Verification Results (Step 1)

### 2.1 Migrations 021–026 and 029–030 — **CONFIRMED, with one new finding**
`mcp__supabase__list_migrations` was queried live. All of local `database/migrations/021`–`030` are applied: `021_cuisines_reference`, `022_dish_display_attributes`, `023_tags_uniqueness_and_vector_positions`, `024_re_dish_regional_affinity`, `025_combo_component_type_and_slot_array`, `026_meal_classes_mirror_slot_array`, `027_routing_rules_show_question_key_nullable`, `028_weight_ladder_config_numeric_weights`, `029_pf1_security_hardening`, `030_re_cohorts_city_tier` all appear in the live migration history (027/028 are stored by Supabase without their numeric filename prefix — cosmetic, not a defect, confirmed by matching content-derived names 1:1).

**NEW FINDING (not in either prior document): two live migrations have no corresponding file anywhere in the repository** — `103_production_cuisines` (version `20260710104454`) and `103_production_ingredients` (version `20260710104859`), applied 2026-07-10, between local `029` and `030`. `database/seeds/` contains `103_seed_ingredients.sql` and `105_seed_cuisines.sql`, but no file matches either live migration name exactly. This means the live database schema/content cannot currently be reproduced from the repository alone for this slice — a direct gap against the repo's own GREEN-certification claim (REPO-CERT-006) that migration rebuild is deterministic and complete. **Action required: retrieve the SQL actually applied for these two migrations from Supabase and commit it as a properly-numbered file, or document why it was intentionally applied out-of-band.**

### 2.2 Validation `905_re_knowledge_seed_validation.sql` — **CONFIRMED, all gates pass live**
Ran every gate in the script directly against the live database:

| Gate | Expected | Actual | Pass |
|---|---|---|---|
| S-01 re_states | 36 | 36 | ✅ |
| S-02 re_main_cohorts | 5 | 5 | ✅ |
| S-03 re_personas | 41 | 41 | ✅ |
| S-04 re_subcohorts | 41 | 41 | ✅ |
| S-05 re_routing_rules | 8 | 8 | ✅ |
| S-06 re_meal_classes | 131 | 131 | ✅ |
| S-07 re_meal_class_overlap_rules | 13 | 13 | ✅ |
| S-09 re_addon_classes | 24 | 24 | ✅ |
| S-11 re_cohorts | 2,952 | 2,952 | ✅ |
| S-12 re_weekly_class_plans | 20,664 | 20,664 | ✅ |
| S-13 re_household_addon_plans | 7,992 | 7,992 | ✅ |
| S-14 re_nonveg_logic | 36 | 36 | ✅ |
| S-08 re_class_dish_options (ICD-1, >0) | >0 | 165 | ✅ |
| S-10 re_addon_dish_options (ICD-1) | ≥0 | 6 | ✅ |
| re_dish_regional_affinity (ICD-1, >0) | >0 | 130 | ✅ |
| Planning-role safety gate (0 violations) | 0 | 0 | ✅ |

**`re_cohort_class_priors` = 0 rows live — CONFIRMED** (matches H-04 exactly; the cold-start prior is still inert in production, not just in a static seed file).

**`re_persona_assignment_rules` = 41 rows live — RESOLVES the Closure Review's "Unable to verify" (§5).** The table **is** seeded (matching the 41-persona count), even though no `1xx` seed file targets it by that exact name in a standalone way — it is populated as part of the persona-seeding block, confirming the Closure Review's own speculation ("may be covered inside 111's persona seeding block") was correct. This item moves from "Unable to verify" to **Confirmed Seeded**.

### 2.3 `suggestion_logs` / `context_log` row counts — **CONFIRMED, both 0**
`public.suggestion_logs` = 0 rows, `public.context_log` = 0 rows live. This confirms Final Evidence Closure §7's claim that the safety-gate audit trail is currently vacuous in production, not just in theory.

### 2.4 GRANT check: `profiles.diet_type` / `is_jain` / `allergen_flags` — **CONFIRMED SAFE, with one hygiene note; plus one unrelated new finding**
- `is_jain` **does not exist as a column on `profiles`** — it exists only on `dishes` (a derived, trigger-computed column), where migrations `008`/`029` already correctly `REVOKE UPDATE (diet_type, is_jain, allergen_flags, genome_vector, …) FROM PUBLIC, anon, authenticated` — confirmed by direct grep of `029_pf1_security_hardening.sql` line 49–54. This lockdown is intact and correct.
- On `profiles` (the actual onboarding-writable table), `anon` and `authenticated` both hold `INSERT`/`UPDATE`/`SELECT`/`REFERENCES` on `diet_type` and `allergen_flags`. This is **expected and safe**: `profiles` has RLS policies `profiles_select_own`/`profiles_update_own`, both gated on `auth.uid() = id` (confirmed via live `pg_policy` query) — a user can only ever touch their own row, which is the intended onboarding self-service behavior. **Hygiene note (low severity, new):** `anon` holding an `UPDATE` grant it can never legally use (no authenticated session ⇒ `auth.uid()` is null ⇒ policy always fails for anon) is unnecessary privilege surface. Recommend `REVOKE UPDATE, INSERT ON public.profiles FROM anon` as defense-in-depth; not urgent, since RLS already blocks it.
- **NEW FINDING (live-only, not in either prior document):** Supabase's own security advisor flags all 35 `re_engine` schema tables as having RLS disabled and "fully exposed to anon and authenticated." Live verification (`has_schema_privilege`, `has_table_privilege`) confirms this is a **false positive relative to actual reachability**: neither `anon` nor `authenticated` (nor, interestingly, `service_role` under this check) hold `USAGE` on the `re_engine` schema at all, and `has_table_privilege('anon', 're_engine.re_cohort_class_priors', 'SELECT')` returns `false`. The schema-level lockdown that DOC-P3-07/DOC-10 document as the security design ("re_engine schema unreachable by clients") **is confirmed correctly enforced in production**, contradicting the raw advisory text (which doesn't account for schema-level REVOKE). Recommend enabling RLS on these 35 tables anyway as defense-in-depth against a future accidental `GRANT USAGE`, but this is not a live vulnerability today.

### 2.5 `git log origin/main` — **CONFIRMED (fact only, not the decision)**
`e113ffa` (WP-8D) and `e76bd9c` (WP-8E) are present on `origin/main`, confirming H-03's factual premise. **Additional context the Closure Review's snapshot could not have (does not resolve H-03, only sharpens its scope):** `origin/main` has since advanced further, to `b27ca58`, incorporating WP-8F, WP-8FA, and this session's own WP-9/REPO-CERT-020 — meaning the un-ratified "push to main" H-03 refers to has grown since the Closure Review was written. The Founder decision itself (ratify or open a governance exception) is unchanged and still requires Founder testimony, not more repository reading.

---

## 3. Root Cause Analysis (Step 2 — consolidated from Closure Review §4/§5, not re-derived)

The Closure Review's 34 "Not Implemented" LFs and its seed-to-runtime "unconsumed" table list collapse into **four engineering root causes and one governance track**:

**RC1 — Repository Adapter Gap.** No concrete Supabase adapter exists for 9 declared RE-schema ports (candidates, cohort-resolution, cohort-priors, config, taste-vector-read, history, bandit-state, context-multipliers). Explains: D01 (candidate generation), E02 (cohort prior — also compounded by unseeded data), B01 (persona fetch architecture), and ~20 of the "seeded, unconsumed" tables in Closure Review §5. **This is the single largest cause** — most of the "designed but not running" gap traces here. Per §0, this is now materially smaller in practice than the Closure Review's framing implies: 2 of 3 remaining `CandidateRepository` field mappings are already proven derivable (WP-8FA), leaving one Founder decision, not an open-ended design question.

**RC2 — Invocation Layer Gap.** No HTTP handler exists beyond `/v1/consent`, and no CRON registration exists for the nightly scheduler. Explains why fully-coded, fully-tested modules (`engine.generateWeekPlan`, `OnboardingOrchestrator`, `RecommendationService`, `NightlyPlanScheduler`) never execute against a real request — this is a separate, later-stage blocker from RC1: fixing RC1 alone does not make anything reachable without this layer too.

**RC3 — Event Ingestion Gap.** No `/v1/events` endpoint and no event-writer functions exist. Explains the entire learning loop (J01–J09) and the suppression-gesture layer (G01, G02, G04, G05) — `computeNotTodayPenalty` (G03) and `updateBanditParams` (J04) are themselves correctly implemented and tested, but structurally unreachable without something to write the events they read.

**RC4 — Pipeline Wiring Gap.** `checkVarietyWindowRules` (F02) and `checkPlanningRoleGate` (H04) are implemented and unit-tested in isolation but never called from `engine.ts`'s actual generation pipeline. Distinct from RC1–RC3: no adapter, endpoint, or event path is missing here — this is a pure omitted-function-call defect inside code that already exists, and is the cheapest of the four to close.

**RC5 (not an engineering root cause — governance track, see §6).** The systemic ACTIVE/DRAFT status contradiction across the frozen document set (MF-03) and the unratified push of WP-8D/8E to main (H-03) are Founder decisions, not code defects. No LF traces here.

**Items not explained by RC1–RC4 (genuinely net-new logic, not adapter/wiring work):** LF-C (member add-ons, zero code at any layer), LF-M02/M03 (DPDP export/delete, zero code), LF-I01–I05 (context assembly beyond the simplified fallback, no external weather client), K03/K04 (dish popularity/tier-completeness triggers, never written). These are grouped as Epic 6/7/9 in §4 rather than forced into RC1–RC4, since building an adapter or an endpoint for them would not make them work — the business logic itself doesn't exist yet.

---

## 4. Implementation Backlog — Epics (Step 3)

### Epic 1 — Repository Adapters (closes RC1)
**Objective:** Implement concrete Supabase-backed classes for the 9 declared-but-unbacked RE-schema ports in `supabase/functions/_shared/services/re/ports.ts`, starting with `CandidateRepository`.
**Business Value:** Unblocks every downstream capability (recommendations, onboarding-driven plans, cold start) — the single highest-leverage Epic in the backlog.
**Dependencies:** None upstream; blocks Epics 2, 3, 5, 6, 8.
**Risk:** Medium. The `mainIngredientClass` field mapping is genuinely unresolved (needs Founder ruling, FD-11 — see §6) — do not fabricate a default for it (per WP-8F's own STOP discipline). `cuisineFamily`/`hasBeef`/`hasPork` mappings are already proven (WP-8FA) and carry low risk.
**Complexity:** L.
**Files to modify:** `supabase/functions/_shared/services/adapters/supabase-stores.ts` (add `SupabaseCandidateRepository`, `SupabaseCohortResolutionRepository`, `SupabaseCohortPriorRepository`, `SupabaseReConfigProvider`); `supabase/functions/_shared/services/re/ports.ts` (no interface changes expected, verify signatures); `supabase/functions/_shared/services/re/engine.ts` (wire real adapters into `EngineDeps` at construction sites in the three callers).
**Tests required:** New adapter-level tests against a live/staging Supabase instance (not fakes) for each of the 4 adapters; extend `_tests/re_integration.test.ts` to exercise the engine with real adapters end-to-end for at least one full week-plan generation.
**Definition of Done:** All 4 adapters implemented, `mainIngredientClass` either uses a Founder-ratified rule or is explicitly out of scope with a documented fallback; `CandidateRepository.getClassCandidates` returns real rows from `re_engine.re_class_dish_options`/`public.dishes` for a live cohort/class pair.
**Acceptance Criteria:** A `generateWeekPlan` call using only real adapters (no fakes) returns a non-empty, constraint-satisfying slate for at least 3 distinct real cohorts, verified against live data, not fixtures.

### Epic 2 — Cold-Start Integrity Package (closes H-04 + MF-02 + M-02; FD-07)
**Objective:** Seed `re_cohort_class_priors` (currently confirmed 0 rows live, §2.2), persist OB-07 swipe directions into `user_taste_vectors.class_affinity` (currently written empty), and implement the LF-A09 fallback-confidence=0.35 rule.
**Business Value:** This is the single metric the MVP is judged on (DOC-01 §07's Day-0/Day-90 acceptance gate) — currently inert.
**Dependencies:** Independent of Epic 1 for the seeding half; the taste-vector-persistence half touches `onboarding/orchestrator.ts` only.
**Risk:** Low (seeding), Low (orchestrator fix).
**Complexity:** M.
**Files to modify:** `database/etl/generate_re_seeds.py` + a new `database/seeds/1xx_seed_cohort_class_priors.sql` (numbered per convention); `supabase/functions/_shared/services/onboarding/orchestrator.ts` (fix `persistTasteVector` call to carry swipe direction, apply the 0.35 fallback-confidence clamp when `fallbackApplied` is true).
**Tests required:** Seed-count validation added to `905_re_knowledge_seed_validation.sql`; new orchestrator unit test asserting `class_affinity` is non-empty after swipes and that fallback confidence is exactly 0.35.
**Definition of Done:** `re_cohort_class_priors` has one row per (cohort, class) pair with non-null prior; `persistTasteVector` writes real swipe-derived values; fallback path sets confidence 0.35 exactly.
**Acceptance Criteria:** A fresh cold-start onboarding run followed by a recommendation call shows the cohort prior score component as non-neutral (≠0.50) for at least one class.

### Epic 3 — HTTP Handler Layer (closes RC2, endpoints only)
**Objective:** Implement `/v1/onboarding`, `/v1/recommendations`, `/v1/plan`, `/v1/plan/refresh`, `/v1/health` following the `consent/index.ts`+`handler.ts` pattern (JWT auth, ownership check, service delegation, `jsonContract` response).
**Business Value:** Without this, no other Epic is reachable by a real user regardless of correctness.
**Dependencies:** Epic 1 (adapters) must land first, or new handlers will 500 on first real call.
**Risk:** Medium — first real live-traffic surface for the RE; needs the latency/N+1 risk (M-08) checked before exposing publicly.
**Complexity:** L.
**Files to modify:** New `supabase/functions/onboarding/{index.ts,handler.ts}`, `supabase/functions/recommendations/{index.ts,handler.ts}`, `supabase/functions/plan/{index.ts,handler.ts}`; `supabase/config.toml` (route registration, `verify_jwt` settings per endpoint).
**Tests required:** New `_tests/onboarding_endpoint.test.ts`, `_tests/recommendations_endpoint.test.ts` mirroring `consent.test.ts`'s 16-test pattern (auth failure, ownership failure, happy path, malformed input).
**Definition of Done:** All listed endpoints deployed and reachable; error codes match DOC-P3-06 exactly (closes L-04's cross-reference gap as a side effect).
**Acceptance Criteria:** An authenticated end-to-end call to `/v1/onboarding` followed by `/v1/recommendations` returns a real slate for a real user, no fakes involved.

### Epic 4 — Pipeline Wiring Fixes (closes RC4 / H-01 / H-02)
**Objective:** Wire `checkVarietyWindowRules` and `checkPlanningRoleGate` into `engine.ts`'s actual generation pipeline; fix the F02 same-ingredient adjacency bug (per-slot grouping instead of raw array-adjacency); add the two missing variety rules (same-cuisine, breakfast rotation).
**Business Value:** Cheapest fix in the backlog for real correctness risk — a live week could currently violate documented variety caps with no detection.
**Dependencies:** None — pure in-repo code change, can run in parallel with Epic 1.
**Risk:** Low.
**Complexity:** S.
**Files to modify:** `supabase/functions/_shared/services/re/engine.ts` (add the two missing calls to the pipeline), `supabase/functions/_shared/services/re/variety.ts` (fix adjacency grouping, add 2 rules).
**Tests required:** New test in `_tests/re_core.test.ts` using a realistic **21-slot** week (not the existing 1-slot fixture) that would fail today under the adjacency bug and pass after the fix.
**Definition of Done:** `generateWeekPlan` output for a full week never violates any of the 5 documented variety rules or the planning-role gate; existing 62 tests still pass.
**Acceptance Criteria:** A regression test asserting all 5 variety rules fire correctly across a realistic multi-slot week is green.

### Epic 5 — Event Ingestion + Minimal Learning Loop (closes RC3)
**Objective:** Implement `/v1/events`, event-writer functions for G01/G02/G04/G05, and wire the already-implemented J04 (`updateBanditParams`) and J07 (feature-store logging) to actually fire on real events.
**Business Value:** RE-DOC-05 §02 names Day-1 feature-store logging as a mandate — every day without it is unrecoverable learning-signal loss (M-04).
**Dependencies:** Epic 3 (HTTP layer) and Epic 1 (bandit/history adapters).
**Risk:** Medium — first write-heavy, high-frequency endpoint.
**Complexity:** L.
**Files to modify:** New `supabase/functions/events/{index.ts,handler.ts}`; new `supabase/functions/_shared/services/events/processor.ts` implementing G01/G02/G04/G05/J01/J02/J03/J06; wire `updateBanditParams` call site into the processor.
**Tests required:** New `_tests/events_endpoint.test.ts`; extend `re_core.test.ts` bandit tests to assert real invocation from the processor, not just direct unit calls.
**Definition of Done:** A Never/Not-Today gesture from a real client updates `never_list`/`not_today_suppression`, increments `re_dish_bandit_state`, and appears in `dish_features` on the next nightly snapshot.
**Acceptance Criteria:** End-to-end: send event → observe row in `interaction_events` → observe bandit state change → observe it reflected in the next `generateSlate` call's exploration bonus.

### Epic 6 — Member Add-ons (closes LF-C, net-new logic)
**Objective:** Implement `generateAddons`/`resolveAddonDish` (LF-C01/C02), consuming the already-seeded `re_household_addon_plans` (7,992 rows) and `re_addon_dish_options` (6 rows).
**Business Value:** DOC-03 names this "the differentiator no competitor has built" for the Meera/Priya personas — currently 0% implemented despite full seed data existing.
**Dependencies:** Epic 1 (needs an addon-equivalent of `CandidateRepository`), Epic 3 (needs an endpoint to expose it, likely folded into `/v1/plan`).
**Risk:** Medium — net-new business logic, not just wiring.
**Complexity:** M.
**Files to modify:** New `supabase/functions/_shared/services/re/addons.ts`; `supabase/functions/_shared/services/adapters/supabase-stores.ts` (addon repository); `engine.ts` (integrate addon slots into `generateWeekPlan`'s output).
**Tests required:** New addon-generation test suite mirroring `re_core.test.ts`'s constraint/scoring pattern.
**Definition of Done:** A household with addon-eligible members receives populated `addon_slots` alongside their primary week plan.
**Acceptance Criteria:** For a real household with a documented member-addon persona, the plan response includes correctly-resolved addon dishes matching `re_household_addon_plans`.

### Epic 7 — DPDP Export/Delete (closes LF-M02/M03 — legal launch blocker)
**Objective:** Implement data export and deletion following the `ConsentService`/`ConsentRepository` pattern already proven in the one fully-closed chain in the repo.
**Business Value:** DOC-09 marks this "non-negotiable before launch" — currently zero code.
**Dependencies:** Epic 3 (handler layer pattern).
**Risk:** Low — pattern is already proven end-to-end for consent; this is largely replication across more tables.
**Complexity:** M.
**Files to modify:** New `supabase/functions/user-export/{index.ts,handler.ts}`, `supabase/functions/user-delete/{index.ts,handler.ts}`; new `ExportService`/`DeletionService` alongside `ConsentService`.
**Tests required:** New test suites mirroring `consent.test.ts`'s 16-test structure exactly.
**Definition of Done:** A real user can request and receive a complete export of their data across every user-scoped table; a deletion request removes/anonymizes the same set per DOC-09's retention rules.
**Acceptance Criteria:** Export output is verified complete against the full user-scoped table list in DOC-P3-04's ERD; deletion is verified irreversible and RLS-consistent.

### Epic 8 — Nightly CRON Registration (closes the L01 "code-complete, system-unreachable" gap)
**Objective:** Register `NightlyPlanScheduler` as a scheduled job (23:30 UTC per DOC-10 §05).
**Business Value:** Prevents silent plan staleness; low safety risk but real quality-of-life gap.
**Dependencies:** Epic 1 (adapters) — the scheduler needs real data to act on.
**Risk:** Low.
**Complexity:** S.
**Files to modify:** `supabase/config.toml` (or the project's CRON registration mechanism — confirm exact mechanism used for Supabase `pg_cron` vs. Edge Function scheduled invocation); `supabase/functions/_shared/services/scheduler/nightly-plan.ts` (verify `nextMonday` date logic under test, per Validation Audit A.5's flagged untested area).
**Tests required:** New scheduler-date-logic test (`nextMonday` across month/year boundaries); manual staging verification of one real scheduled run.
**Definition of Done:** The scheduler runs automatically at the documented time and regenerates plans for eligible users without manual invocation.
**Acceptance Criteria:** A staging-environment CRON firing produces updated `week_plans` rows for at least one real eligible user without manual triggering.

### Epic 9 — Context Assembly (closes LF-I01–I05, post-MVP per Closure Review §9 triage)
**Objective:** Implement full weather/season/festival context assembly (OpenWeatherMap client, season derivation, festival-proximity check) beyond today's simplified cooking-method-keyed fallback.
**Business Value:** Improves personalization quality; explicitly triaged as post-MVP, not safety-critical.
**Dependencies:** Epic 1 (context-multiplier adapter).
**Risk:** Low — additive, does not change existing correct behavior (M-01's simplification remains a safe fallback if the external API fails).
**Complexity:** M.
**Files to modify:** New `supabase/functions/_shared/services/context/weather-client.ts`; `supabase/functions/_shared/services/re/scoring.ts` (`gatherContextMultipliers`, extend beyond the current simplification).
**Tests required:** New context-assembly test suite with mocked weather API responses covering all documented weather/season/festival branches.
**Definition of Done:** `computeContextFit` uses real weather/season/festival signals when available, falling back to today's simplified multiplier when the external API is unavailable.
**Acceptance Criteria:** A live call during a documented festival window shows the festival-proximity boost applied; a live call during a cached-weather-miss falls back cleanly with no error.

---

## 5. Recommended Implementation Sequence

Sequenced to minimize rework, per the dependency chain already traced in Closure Review §3 and the instruction's own ordering (adapters → endpoints → cold-start → learning loop → addons), with the two cheap/independent Epics (4, migration-drift remediation) slotted early:

1. **Epic 4** — Pipeline Wiring Fixes (no dependencies, cheapest, closes a live correctness gap immediately)
2. **[Housekeeping]** — Resolve the §2.1 migration-drift finding (retrieve/commit the two orphaned live migrations) — independent, should not be deferred since it's a reproducibility gap
3. **Epic 1** — Repository Adapters (unblocks everything downstream)
4. **Epic 2** — Cold-Start Integrity Package (can start in parallel with Epic 1's later half once `CohortPriorRepository` lands)
5. **Epic 3** — HTTP Handler Layer (depends on Epic 1)
6. **Epic 8** — Nightly CRON Registration (depends on Epic 1; cheap, can slot in alongside Epic 3)
7. **Epic 5** — Event Ingestion + Minimal Learning Loop (depends on Epics 1 and 3)
8. **Epic 7** — DPDP Export/Delete (depends on Epic 3; legal blocker, do not defer past first external user)
9. **Epic 6** — Member Add-ons (depends on Epics 1 and 3)
10. **Epic 9** — Context Assembly (post-MVP; last)

---

## 6. Founder Decision Register (verbatim passthrough from Final Evidence Closure Review §8 — not modified, not converted to engineering tasks)

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

**One new item this session adds (not a modification of the above — a distinct decision this pass's evidence surfaced):**

| # | Decision | Why it exists | Repository impact | Blocking impact | Urgency | Recommended decision |
|---|---|---|---|---|---|---|
| FD-11 | Rule on the `mainIngredientClass` "dominant ingredient" derivation rule (WP-8FA's one remaining open item, §0 above) | `ingredients.category` exists in source data but was never seeded, and no rule defines which ingredient "dominates" a multi-ingredient dish | Blocks the final third of Epic 1 (Repository Adapters) | Blocks full `CandidateRepository` completion — 2 of 3 remaining mappings are already unblocked | High | Specify the dominant-ingredient rule (e.g., by weight, by listing order, by a curated override table) so Epic 1 can close completely |

---

## 7. Production Readiness Dashboard

Copied from Final Evidence Closure Review §11 verbatim, with **two lines updated** based on Step 1 live verification (both marked below — no other line is changed):

| Area | Status | Basis |
|---|---|---|
| Documentation | **Needs Work** | Rich and mostly high-fidelity, but the ACTIVE/DRAFT contradiction (FD-05) and two internal scope conflicts (FD-08) mean the frozen set cannot yet be called authoritative without a Founder pass |
| Architecture | **Mostly Ready** | Hexagonal design proven sound by construction (§9 of WP-9, reconfirmed); the gap is adapter implementation, not design |
| Database | **Ready — UPDATED NOTE:** live migration history contains 2 migrations (`103_production_cuisines`, `103_production_ingredients`) with no corresponding committed file (§2.1) — reproducibility is not fully intact until this is resolved; schema/RLS/triggers themselves remain confirmed correct live | 30 migrations confirmed applied live, RLS on all `public`-schema tables (verified in 019/029 + live query), triggers validated (901), structural validation passing (900); **new gap**: 2 unaccounted-for live migrations |
| Seed Data | **Mostly Ready — UPDATED NOTE:** `re_persona_assignment_rules` is now CONFIRMED seeded (41 rows live), resolving the prior "Unable to verify" status | Deterministic, provenance-stamped, regenerated byte-identical (Validation Audit MF-08); only 2 tables genuinely missing (`re_cohort_class_priors` confirmed 0 rows live, `re_city_migration_overlays`), both disclosed and confirmed |
| Recommendation Engine (core logic) | **Mostly Ready** | 17 LFs fully implemented and tested; algorithmically sound; blocked only by the adapter gap (now partially de-risked, §0), not by logic defects |
| Runtime (integration/orchestration layer) | **Needs Work** | Fully coded and tested against fakes for 3 callers; zero live reachability |
| API | **Blocked** | 1 of 9 endpoints exists |
| Security | **Mostly Ready** | JWT+ownership pattern correctly implemented where code exists; RLS-bypass discipline documented and followed; DPDP technical controls (export/delete) entirely missing — **Blocked** on that sub-dimension specifically. Live check this session found the `re_engine` RLS-disabled advisory to be a false positive (schema USAGE is revoked), and the `profiles` anon-UPDATE grant to be safely gated by RLS — no change to the overall rating, but both are now confirmed rather than assumed. |
| Performance | **Needs Work** | No live measurement exists anywhere; N+1 risk identified but unverified in practice |
| Observability | **Needs Work** | Structured logger and telemetry seams exist; Sentry/PostHog adapters not wired; audit-trail tables unwritten (confirmed 0 rows live, §2.3) |
| Testing | **Mostly Ready** | 62/62 passing, high-quality fakes-based coverage where code exists; zero live-DB tests exist anywhere in the repo (self-disclosed in every WP) |
| Deployment | **Needs Work** | CI pipeline complete and correct (fmt/lint/typecheck/test); no CD to any environment; CRON absent |

---

## Critical Self-Review

This document's Step 1 verification used live Supabase MCP tools the two source documents did not have access to (their evidence base was a static zip). Two items remain outside what any of the three predecessor audits or this pass could resolve from repository/live-DB evidence alone: H-03 (Founder ratification of the WP-8D/8E push) and FD-11 (the new dominant-ingredient rule) — both require Founder decisions, correctly kept out of the engineering backlog per the task's own instruction not to convert governance decisions into engineering tasks.

## Versioning & Placement
v1.0, filed under `docs/project-history/work-packages/` alongside its three predecessor documents. This document is the Engineering Execution Baseline — the next engineering session should start here, consult predecessor documents only for evidence detail, and should not require another audit pass.

Founder sign-off: _______________________ Date: ___________
