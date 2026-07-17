# [ACTIVE]_WP-8E_RE_Integration_Layer_v1.0

**Status:** ACTIVE — RE integration orchestration layer BUILT & VALIDATED (certified REPO-CERT-015). Concrete RE read-port adapters (incl. CandidateRepository) + HTTP endpoints + live-DB validation are enumerated remaining debt (§6).
**Version:** v1.0
**Date:** 2026-07-15
**Placement:** docs/project-history/work-packages/[ACTIVE]_WP-8E_RE_Integration_Layer_v1.0.md
**Builds on:** WP-8D RE core (REPO-CERT-014), WP-8C auth/consent (REPO-CERT-011), WP-8B scaffold (REPO-CERT-008).
**Governance basis (frozen, consumed not modified):** DOC-P3-02 (CDM Domain Events), DOC-P3-03 v1.0 §03/§04/§05/§14, DOC-P3-04 v1.3 §03.1–03.13 (migrations 005/006/007/011), DOC-P3-06 v1.2 §06.2/§06.4/§21, DOC-P4-00 §4/§5/§14/§16, DOC-P4-02 (DRAFT).

---

## Executive Summary

WP-8E integrates callers with the **existing** WP-8D Recommendation Engine — it adds **no** recommendation logic (scoring, ranking, safety, variety, constraints are untouched in `services/re/`). It delivers, fully implemented and test-verified with fakes:

1. **Onboarding orchestration** — `OnboardingOrchestrator` runs onboarding's OWN logic (LF-A01–A09: answer capture, confidence, city-overlay, persona/cohort resolution, consent gate), then **invokes the reusable engine**, **persists** the generated week plan, and **returns the §06.2 handle**. The engine owns every recommendation decision.
2. **Recommendations service** — `RecommendationService` (POST /v1/recommendations, §06.4) loads inputs, invokes the **same** engine for a single slot, persists the fresh slate, returns the §06.4 DTO.
3. **Nightly scheduler** — `NightlyPlanScheduler` (LF-L01, §14) iterates eligible users and invokes the **same** engine, persisting each plan; per-user failures are isolated.
4. **Persistence + caller-load Supabase adapters** — verified-column repository adapters for `week_plans`/`plan_slots`, the onboarding writes, plan-slot class reads, and eligible users.

**All three callers share the one engine (single source of recommendation logic).** Verified: `deno fmt --check`, `deno lint`, `deno check`, `deno test` → **62 tests, 0 failures** (8 foundation + 16 consent + 28 RE core + **10 WP-8E integration**). No schema/migration/seed/validation-SQL/security or frozen-document change; DOC-P4-02 remains DRAFT.

---

## 1. Architecture verification (the mission)

| Requirement | Evidence |
|---|---|
| RE Engine is the single source of recommendation logic | All recommendation code lives only in `services/re/` (WP-8D). WP-8E services import & invoke it; grep shows no scoring/ranking/safety/variety/constraint logic outside `services/re/`. |
| Onboarding only orchestrates | `OnboardingOrchestrator` contains LF-A01–A09 (onboarding's own logic) + calls `engine.generateWeekPlan`; it has zero candidate/score/rank/safety code. |
| RE reused by all 3 callers | `OnboardingOrchestrator`, `RecommendationService`, `NightlyPlanScheduler` each take a `RecommendationEngine` and call it. Integration test constructs one engine and drives all three. |
| Onboarding persists + returns first plan | Per DOC-P3-02 Domain Events (`PlanPreviewGenerated`, actor = RE Engine): engine generates → `WeekPlanStore` persists → §06.2 handle returned. Test asserts persistence + handle. |
| No duplicated RE logic | Confirmed by construction + review (§Governance). |

## 2. Files (all under `supabase/functions/`)

**New:**
- `_shared/services/planning/persistence.ts` — `WeekPlanStore` port + `GeneratedWeekPlan → week_plans/plan_slots` mapping (primary slots only; `plan_slots.meal_slot` CHECK excludes snack).
- `_shared/services/onboarding/orchestrator.ts` — `OnboardingOrchestrator` + `OnboardingStore` port + LF-A03 city-overlay + LF-A08 confidence + consent gate + §06.2 DTO.
- `_shared/services/recommendations/service.ts` — `RecommendationService` + `ReStateStore`/`PlanSlotStore` ports + §06.4 DTO.
- `_shared/services/scheduler/nightly-plan.ts` — `NightlyPlanScheduler` + `EligibleUsersStore` port.
- `_shared/services/adapters/supabase-stores.ts` — concrete adapters: `SupabaseWeekPlanStore`, `SupabaseOnboardingStore`, `SupabasePlanSlotStore`, `SupabaseEligibleUsersStore` (verified columns).
- `_tests/re_integration.test.ts` — 10 tests (fakes only).

**Extended (additive, no logic change):** `_shared/services/re/types.ts` (+`RankedDish`/`Slate.ranked` — surfaces the already-computed FinalScore for §06.4), `_shared/services/re/engine.ts` (builds `ranked`), `_shared/errors/api-catalogue.ts` (+3 frozen §21.1 codes: `ERR_CONSENT_REQUIRED` 403, `ERR_PLAN_NOT_FOUND` 404, `ERR_ONBOARDING_ALREADY_COMPLETE` 409).

## 3. Error handling (frozen contract, no invented errors)

All errors use DOC-P3-06 §21.1 codes: onboarding consent gate → `ERR_CONSENT_REQUIRED` (403); duplicate onboarding → `ERR_ONBOARDING_ALREADY_COMPLETE` (409); missing plan for a recommendation slot → `ERR_PLAN_NOT_FOUND` (404); validation → `ERR_VALIDATION_FAILED`. No generic strings, no invented codes.

## 4. Spec-fidelity decisions (surfaced, not invented)

- **DCR-8E-01 — onboarding confidence Day-0 cap.** DOC-P3-03 §03 LF-A08's additive contributions sum to 1.00 for a fully-answered onboarding, but the same section states **"Maximum at Day 0 completion: 0.65"** (Range Day 0: 0.40–0.65). `computeOnboardingConfidence` clamps to [0.35, 0.65]; the 1.0 schema ceiling is for later warm-state evolution. Faithful to the stated Day-0 maximum.
- **`Slate.ranked` is additive** — surfaces the FinalScore the engine already computed so §06.4 `dishes[].score` is exact; no scoring/ranking logic changed in WP-8D.
- **Persistence atomicity** — the Supabase JS client cannot wrap multi-statement transactions; `persistWeekPlan` does sequential upserts. Production should move it into a Postgres RPC for the atomic slate write (DOC-P4-00 §16). Flagged (§6).

## 5. Governance compliance

No `CREATE`/`ALTER`/`DROP`; no migration, seed, canonical data, validation SQL, RLS/privilege, or frozen-document change (verified: change set touched only `supabase/functions/` + docs). Recommendation logic exists only in `services/re/`. DOC-P4-02 stayed **DRAFT** at time of this Work Package's execution (AD-01 not re-ratified here; the orchestration model was reconciled in WP-8D and Founder-directed, formal countersignature still pending then). Branch `feat/wp-8d-re-core-reconciliation`; not pushed as of this Work Package's own execution.

**[FD-01 update, 2026-07-16]** This branch's later push to `main` is retroactively ratified as authorized — see `[ACTIVE]_Founder_Decision_Register_v1.0.md` FD-01 and `[ACTIVE]_Founder_Ratification_Certificate_2026-07-16_v1.0.md`. **[FD-04 update, 2026-07-16]** DOC-P4-02's AD-01 is now ratified as Option 2 (synchronous first-plan generation) and DOC-P4-02 has been promoted DRAFT → ACTIVE — see FD-04. This Work Package's own text above is left unchanged as the historical record at time of execution, per `CLAUDE.md`'s never-delete-history rule.

## 6. Remaining Technical Debt (precise, for WP-8E completion / next WP)

1. **`CandidateRepository` concrete adapter — BLOCKED (schema-mapping).** The `dishes` table stores the variety dimensions (cuisine_family, cooking_method, main_ingredient_class, texture) as **genome tags** (`dish_tags`→`tags`), not scalar columns, and the ingredient-level allergen union comes from `dish_ingredients`→`ingredients`. Materializing a `DishCandidate` faithfully requires verifying the `tags` taxonomy + genome_vector ordering + the allergen join. Deferred rather than invent the mapping.
2. **Remaining RE read-port concrete adapters** (columns verified, mechanical, deferred for scope): `CohortResolutionRepository`, `CohortPriorRepository`, `TasteVectorRepository`, `PersonalHistoryRepository`, `BanditStateRepository`, `ContextMultiplierRepository`, `NeverListRepository`, `SuppressionRepository`, and a concrete `ReStateStore` (needs the cohort-resolution lookup, since `user_re_state` has no `cohort_id` — cohort is resolved from persona×state×diet_mode via `re_cohorts`).
3. **HTTP endpoints** `/v1/onboarding` + `/v1/recommendations` — the thin handlers (auth via WP-8C middleware → parse §06.2/§06.4 → ownership → call orchestrator/service → envelope) + request parsing. Deferred because a runnable endpoint needs the full engine wiring (item 1). The orchestrators they call are done and tested.
4. **Live-DB behavioural validation** — extend validation `902`/`905` to exercise the runtime engine against a disposable Supabase (the WP-6E clean-room pattern); nothing in WP-8E has been run against a live DB (adapters are type-checked only).
5. **`persistWeekPlan` atomicity** via a Postgres RPC (DCR-8E-01 note; DOC-P4-00 §16).
6. **Addon-slot generation (LF-C01/C02)** — `re_segment_addon_rule` (named in DOC-P3-03 §05) **does not exist as a table**; the real path is `re_household_addon_plans` + `re_addon_classes` + `re_addon_dish_options`. Documentation/schema mismatch to reconcile before addon slots are generated.
7. **`re_cohort_class_priors` unseeded** (carried from WP-8D) — cold-start CohortPrior uses the LF-E02 neutral 0.50 fallback until seeded.

## 7. Readiness assessment for the next work package

- **Architecture: READY** — the one-engine/three-callers integration is proven and tested; onboarding orchestration + persistence + return is verified.
- **Production runtime: NOT YET** — gated on debt items 1–3 (candidate adapter → endpoints) and 4 (live-DB validation). Recommended next WP: implement the RE read-port adapters (starting with the `CandidateRepository` dish-genome/tag mapping — a schema-verification task), wire the two endpoints, then run live-DB behavioural validation on a disposable Supabase.
- **Governance: READY pending** DOC-P4-02 Founder countersignature (AD-01) to make the orchestration model formally ACTIVE.

## Critical Self-Review

- **Any recommendation logic outside the engine?** No — WP-8E is orchestration/persistence/mapping only; `services/re/` (WP-8D) is untouched except the additive `ranked` output surfacing.
- **Anything invented?** No — DTOs match §06.2/§06.4; error codes are §21.1; the one clamp (confidence 0.65) is the stated Day-0 max; the blocked `CandidateRepository` was deferred, not fabricated.
- **Frozen artifacts / DB touched?** No; DOC-P4-02 stays DRAFT.
- **Honest completeness:** the orchestration mission is complete and tested; concrete read adapters (esp. Candidate), endpoints, and live-DB validation are transparently enumerated debt — the system is not yet end-to-end runnable against a real database.

## Versioning & Placement

v1.0, docs/project-history/work-packages/ per the Placement Rule; naming per WP-5AA. Companion certificate: REPO-CERT-015.

## Founder Sign-off

Founder acceptance of WP-8E (RE integration orchestration layer) + acknowledgement of the §6 remaining-debt scope: _______________________ Date: ___________
