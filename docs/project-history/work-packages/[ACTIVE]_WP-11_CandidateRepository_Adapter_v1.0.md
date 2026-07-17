# [ACTIVE]_WP-11_CandidateRepository_Adapter_v1.0

**Status:** ACTIVE — first concrete RE read-port adapter BUILT & TEST-VERIFIED (certified REPO-CERT-022). Content-seeding coverage of `re_class_dish_options` and 5 surfaced debt items are enumerated remaining work (§5, §6), not blockers to this Work Package's own completion.
**Version:** v1.0
**Date:** 2026-07-17
**Placement:** docs/project-history/work-packages/[ACTIVE]_WP-11_CandidateRepository_Adapter_v1.0.md
**Builds on:** WP-8E RE integration layer (REPO-CERT-015, left this adapter BLOCKED), WP-8F blocker report (REPO-CERT-018), WP-8FA architecture audit (REPO-CERT-019, resolved 5 of 6 blockers), WP-10 schema evolution (REPO-CERT-021, populated `main_ingredient_class`).
**Governance basis (frozen, consumed not modified):** `[ACTIVE]_DOC-P3-13_Main_Ingredient_Derivation_Heuristic_v1.0.md`, DOC-P3-03 §06/§07/§08 (LF-D01–D07, LF-F01/F02), DOC-P3-04 (schema), `[ACTIVE]_WP-8FA_CandidateRepository_Architecture_Audit_v1.0.md` (verdicts adopted, re-verified against the live schema — not re-derived from memory).

---

## Executive Summary

`SupabaseCandidateRepository` — the concrete adapter for the `CandidateRepository` read-port (`getClassCandidates`, `getPopularFallback`) — is implemented, type-checked, and test-verified against the frozen `DishCandidate` type (17 fields, not 15 as earlier session notes assumed — corrected here) and against the *actual* downstream consumers (`applyHardConstraints`, `scoring.ts`'s `contentMatch`/`contextFit`), not merely assumed compatible. This closes WP-8E debt item 1 and the WP-8F/8FA blocker chain. `deno task verify`: **71 tests, 0 failures** (62 pre-existing + 9 new), `fmt`/`lint`/`check` all clean.

No schema, migration, seed, or frozen-document change. No live-DB connection (adapter is type-checked + fake-tested only, per the existing WP-8E convention).

## 1. What was built

**New:** `supabase/functions/_tests/candidate_repository.test.ts` (9 tests, fake Supabase query-builder chain, no live DB).
**Extended (additive):** `supabase/functions/_shared/services/adapters/supabase-stores.ts` — added `SupabaseCandidateRepository` class plus its private helpers (`loadDishes`, `loadAllergenMarks`, `loadTags`, `loadCuisineGroups`, `assemble`, `pickTag`, `assertNotNull`) and the `MAIN_INGREDIENT_CLASS_PRIORITY` constant. No existing class in this file was modified.

## 2. Field hydration (17 fields — see full table in the session transcript; summarized here)

| Category | Fields | Source |
|---|---|---|
| Direct columns | `dishId`, `baseScore`, `classCode`, `mealOccasions`, `genomeVector`, `cookTimeBandMinutes` | `re_class_dish_options` / `dishes` |
| Type-checked, fail-loud if null | `dietType`, `isJain` | `dishes.diet_type`/`is_jain` — schema allows NULL, 0 nulls observed in 802 rows; adapter throws rather than defaults a safety-relevant field |
| Joined | `ingredientAllergenUnion`, `hasBeef`, `hasPork` | `dish_ingredients` ⨝ `ingredients` (bitwise OR / membership on `name='beef'`/`'pork'`) |
| Joined | `cuisineFamily` | `dishes.cuisine_id` ⨝ `cuisines.cuisine_group` (WP-8FA 8F-01, verdict B) |
| Joined + tie-break | `mainIngredientClass`, `cookingMethod`, `texture` | `dish_tags` ⨝ `tags`, collapsed to one value per dish (§3) |
| Documented deferral | `seasonalAffinity` | always `[]` — WP-8FA 8F-04, no source exists anywhere |
| Documented proxy | `hasNonHalalMeat` | `hasPork OR mainIngredientClass='meat'` — WP-8FA 8F-03 recommendation, updated to use the now-populated tag dimension (WP-8FA predates WP-10) |

## 3. Multi-valued tag dimensions — the tie-break decision

`dish_tags` is inherently multi-valued (802 dishes / 11,297 rows across all dimensions); `DishCandidate`'s `mainIngredientClass`/`cookingMethod`/`texture` are singular strings. Verified counts: 39 dishes have 2 `main_ingredient_class` rows, 164 have 2–3 `cooking_method` rows, 283 have 2–3 `texture` rows — every dish has **at least** one row for each (0 dishes missing).

- **`mainIngredientClass`:** `[ACTIVE]_DOC-P3-13_Main_Ingredient_Derivation_Heuristic_v1.0.md` §1 already documents a priority order for identifying the single dominant ingredient (protein/pulse > grain/flour > vegetable/other). The adapter applies that same order verbatim as the tie-break constant `MAIN_INGREDIENT_CLASS_PRIORITY`.
- **`cookingMethod` / `texture`:** no equivalent spec exists for these two Tier-2 dimensions. The adapter falls back to lowest `tags.vector_position` (the canonical dimension ordering already used elsewhere) — **deterministic, not silent, but not spec-grounded**. Logged as GB-004 (§6 below) rather than left undocumented.

## 4. Downstream compatibility — proven, not assumed

`candidate_repository.test.ts` imports the *real* `applyHardConstraints` (from `constraints.ts`) and the *real* `contentMatch`/`contextFit` (from `scoring.ts`) and runs them directly against the adapter's fake-backed output with zero shimming. This is the literal hexagonal-architecture claim WP-8E left unverified — it is now a passing test, not an assertion in a report.

## 5. Known limitations (surfaced here; full backlog entries in DOC-P3-12, §Task 2 of this session)

1. `cookingMethod`/`texture` tie-break has no documented spec basis (see §3).
2. Pre-existing bug, not introduced or fixed here: `variety.ts:89` checks `cookingMethod === "fried"`, which never matches the real `deep_fried`/`shallow_fried` vocabulary — the fried-count variety rule silently never fires.
3. No FK constraints exist on `dish_ingredients`, `dish_tags`, or `re_class_dish_options` (verified via `pg_constraint` — only `re_class_dish_options.meal_class_code → re_meal_classes` has one). This is why the adapter does NOT use PostgREST relational embedding (`.select("ingredients(name)")` etc.) — it would silently fail to resolve. Flat queries + in-memory joins used instead.
4. `beef`/`pork` `dish_ingredients` linkage is sparse: only 1 dish links `beef`, 13 link `pork` — likely under-links real beef/pork dishes in the seeded data.
5. `hasNonHalalMeat` is a fail-closed proxy, not real halal-certification data (WP-8FA 8F-03, documented MVP limitation, not new to this Work Package).

## 6. The bigger finding: `re_class_dish_options` coverage

Verified directly against the live schema: **50 of 131 `re_meal_classes` (38%) have zero rows in `re_class_dish_options`**; the 81 populated classes average **2.0** dishes each, **7 at most** (165 total rows). `cfg.minCandidates = 3` (LF-D07). Consequence: for the majority of classes, `getClassCandidates` cannot clear the fallback threshold on its own — `getPopularFallback` is the dominant runtime path today, not an edge case. This is a content-seeding gap the adapter faithfully surfaces; it is **not** an adapter defect, and per Task 3 of this session it is logged as an explicit, Founder-ratified interim state in the Decision Register (FD-14) rather than silently accepted.

## 7. Readiness assessment for the next Work Package

- **Architecture: READY** — interface compliance and downstream (HardConstraint/scoring) compatibility are both proven by test, not assumed.
- **Production runtime: PARTIAL** — the adapter is correct, but real-world behavior will be fallback-heavy until `re_class_dish_options` is backfilled for the 50 empty/thin classes (content work, tracked via FD-14, not gating this WP or Wave 3 engineering).
- **Remaining WP-8E debt not touched here:** the other 8 read-port adapters, the two HTTP endpoints, live-DB behavioral validation, `persistWeekPlan` atomicity, and add-on generation (LF-C/FD-06) — unchanged, still open.

## Critical Self-Review

- **Any recommendation logic added to the adapter?** No — hydration and one documented, minimal tie-break only; zero scoring/ranking/filtering logic (that stays in `services/re/`).
- **Anything invented?** No — every field source traces to WP-8FA's verdicts (re-verified live, not trusted from memory) or to a newly-surfaced, explicitly flagged judgment call (tie-break, halal proxy), never silently guessed.
- **Frozen artifacts / DB touched?** No — no migration, seed, or schema change. No live-DB connection.
- **Honest completeness:** the adapter is done and tested; the content-seeding gap it surfaces is real and is handled as a logged decision (FD-14) + backlog items (GB-004–008), not swept under this WP's "complete" status.

## Versioning & Placement

v1.0, `docs/project-history/work-packages/` per the Placement Rule; naming per WP-5AA (`WP-11`, next sequential number — WP-10 is the FD-11/12/13 schema evolution batch). Companion certificate: REPO-CERT-022.

## Founder Sign-off

Founder acceptance of WP-11 (`CandidateRepository` adapter) + acknowledgement of the §5/§6 surfaced limitations and content-seeding gap: _______________________ Date: ___________
