# [ACTIVE]_WP-8FA_CandidateRepository_Architecture_Audit_v1.0

**Status:** ACTIVE — CPTO-level architectural evidence audit (READ-ONLY). No runtime code, no schema/migration/seed/DB change. Companion certificate: REPO-CERT-019.
**Version:** v1.0
**Date:** 2026-07-15
**Placement:** docs/project-history/work-packages/[ACTIVE]_WP-8FA_CandidateRepository_Architecture_Audit_v1.0.md
**Purpose:** Resolve, from repository evidence alone, whether the four WP-8F `DishCandidate` blockers (+ the fifth cold-start prior blocker) are (A) already solved / (B) derivable / (C) intentional MVP deferral / (D) require a Founder-approved SER — eliminating uncertainty before runtime implementation resumes.
**Evidence basis read this session (from source):** `services/re/types.ts` (`DishCandidate`), `re/constraints.ts`, `re/variety.ts`, `re/scoring.ts`, `adapters/supabase-stores.ts`; **RE-DOC-02 §02 (the 20 genome dimensions — extracted from the `.docx` that WP-8F could not read)**, RE-DOC-03/04/05; DOC-P3-03 §06/§07/§08; migrations 002/003/008/009/021/022/024; seeds 100/103/104; source `cuisines_v4.csv`, `ingredients_v5.csv`, `dishes.xlsx`; WP-8F report (REPO-CERT-018).

> **Headline:** the single most important new fact is that **RE-DOC-02 §02 (the 20 genome dimensions) is now read** (the WP-8F author explicitly could not — "`.docx`/binary, not machine-readable"). It resolves 8F-01 directly and re-frames the others. Combined with a direct check of the ingredient/dish data (which WP-8F did not perform for beef/pork), **three of the four "unprovable" WP-8F blockers are actually derivable with no schema change.** Only main-ingredient-class and halal-certification are genuine gaps; seasonal and cohort-prior are intentional, spec-documented MVP deferrals.

---

## 1. CandidateRepository Traceability Report — every `DishCandidate` field

Legend: ✅ Fully Proven · 🟡 Derived (no schema change) · 🟠 Ambiguous · 🔴 Genuine Gap

| # | Field | Business meaning | Research (RE-DOC) | Business logic (DOC-P3-03) | DB source / seed | Derivation | Current impl | Status |
|---|---|---|---|---|---|---|---|---|
| 1 | `dishId` | candidate identity | RE-DOC-03 §01 class→dish | LF-D01 | `re_engine.re_class_dish_options.dish_id` (mig 004) / seed 117 | direct | consumed in engine; repo unbuilt | ✅ |
| 2 | `baseScore` | class-fit base | RE-DOC-03 | LF-D01 | `re_class_dish_options.base_score` / seed 117 | direct | " | ✅ |
| 3 | `dietType` | diet class | RE-DOC-02 dim 12 | LF-D02/K01 | `dishes.diet_type` (mig 008, **trigger-derived**) | direct read | " | ✅ |
| 4 | `isJain` | jain safety | RE-DOC-02 dim 17 (Jain) | LF-D04/K01, Gate 3 | `dishes.is_jain` (trigger-derived) | direct read | " | ✅ |
| 5 | `ingredientAllergenUnion` | allergen safety | RE-DOC-02 dim 13 | LF-D03, Gate 2 (GR-06) | OR of `ingredients.allergen_flags` via `dish_ingredients` (mig 002/009) | bitwise OR join | " | ✅ |
| 6 | `mealOccasions` | slot eligibility | RE-DOC-02 dim 1 | LF-D05 | `dishes.meal_occasion[]` (mig 008) | direct | " | ✅ |
| 7 | `classCode` | class membership | RE-DOC-02 dim 19 | LF-D01 | `re_class_dish_options.meal_class_code` | direct | " | ✅ |
| 8 | `genomeVector` | ContentMatch | RE-DOC-02 §02 | LF-E03/K02 | `dishes.genome_vector[]` (trigger) | direct | " | ✅ |
| 9 | `cookTimeBandMinutes` | context/quick filter | RE-DOC-02 dim 7 | LF-E05 | `dishes.cook_time_minutes` (mig 008) | direct | " | ✅ |
| 10 | `cookingMethod` | variety dim | RE-DOC-02 dim 5 | LF-F01 | `tags.dimension='cooking_method'` via `dish_tags` (seed 104, 16 tags) | tag lookup | " | ✅ |
| 11 | `texture` | variety dim | RE-DOC-02 dim 4 | LF-F01 | `tags.dimension='texture'` via `dish_tags` (seed 104, 12 tags) | tag lookup | " | ✅ |
| 12 | `cuisineFamily` | variety dim (regional origin) | **RE-DOC-02 dim 2 "Regional origin"** {North/South Indian, Bengali, Gujarati, Mughlai, Pan-Indian} | LF-F01 | `dishes.cuisine_id → public.cuisines.cuisine_group` (mig 021) | **join** dish→cuisine→cuisine_group | not yet built | 🟡 → **B** |
| 13 | `mainIngredientClass` | variety dim 11 | RE-DOC-02 dim 11 {rice,wheat,lentil,dairy,egg,poultry,fish,seafood,vegetable,fruit} | LF-F01/F02 | **none seeded** (`ingredients.category` exists in `ingredients_v5.csv` but was NOT seeded; no `tags` dim; `food_dna_tier_1` = "tier_1"/"tier_2", useless) | needs category + a "dominant ingredient" rule | not built | 🔴 → **D** |
| 14 | `hasBeef` | religious (no_beef) | RE-DOC-02 dim 17 (no-beef) | LF-D04 | **`ingredients` row `beef`** (category=meat, seeded) via `dish_ingredients` | membership join | not built | 🟡 → **B** |
| 15 | `hasPork` | religious (no_pork) | RE-DOC-02 dim 17 (no-pork) | LF-D04 | **`ingredients` row `pork`** (category=meat, seeded) via `dish_ingredients` | membership join | not built | 🟡 → **B** |
| 16 | `hasNonHalalMeat` | religious (halal) | RE-DOC-02 dim 17 (Halal) | LF-D04 | pork ⇒ true (derivable); **halal certification of other meats: unmodelled anywhere** | partial derive; halal genuinely absent | not built | 🟠 → **B (pork) + C (halal limitation)** |
| 17 | `seasonalAffinity` | season boost | RE-DOC-02 dim 14 {summer,monsoon,winter,post-monsoon,all-season} | LF-E05 | **none** (dish season absent — Batch6 "declared absent"; dishes carry `weather_affinity` dim 15, not season) | not sourced | ContextFit runs on weather/day/cook-time | 🔴 → **C** |

**14 of 17 fields are ✅ fully proven** against the seeded canonical schema. The 3 non-green fields are the blockers below (plus the read-adapter cold-start priors, §Blocker 8F-05).

---

## 2. Architecture Audit — blocker-by-blocker (evidence exhausted)

### BLOCKER 8F-01 — Cuisine Family → **B. Can be derived. No schema evolution required.**
- **RE-DOC-02 dim 2 "Regional origin"** is exactly this dimension; example values (North Indian, South Indian, Bengali, Gujarati, Mughlai, Pan-Indian) are the **`cuisine_group`** vocabulary.
- `cuisines_v4.csv` `cuisine_group` holds precisely this family taxonomy: `north_indian`(10), `south_indian`(10), `west_indian`(9), `northeast_indian`(7), `east_indian`(4), `mughlai_nawabi`(3), `central_indian`(3), plus non-Indian families. `public.cuisines.cuisine_group` (mig 021) is seeded from it (seed 105); `dishes.cuisine_id → cuisines` (mig 021).
- **Resolution of the WP-8F ambiguity ("cuisine_group vs parent_cuisine?"):** the *family* is `cuisine_group` (matches RE-DOC-02 dim 2). `parent_cuisine` is intra-group lineage, not the family. Corroborated by `re_meal_classes.cuisine_family` using the same taxonomy (`pan_indian`, `north_indian`, …).
- **Derivation (no schema change):** `DishCandidate.cuisineFamily = SELECT c.cuisine_group FROM dishes d JOIN cuisines c ON c.id = d.cuisine_id`.

### BLOCKER 8F-02 — Main Ingredient Class → **D. Requires a Founder-approved decision/SER.**
- **RE-DOC-02 dim 11** defines it: enum {rice, wheat, lentil, dairy, egg, poultry, fish, seafood, vegetable, fruit}; use = the `same_main_ingredient` variety guard (seeded in `re_variety_rules`, seed 100).
- **No seeded source:** `public.ingredients` has **no `category`** (seed 103 loaded only name/is_veg/is_vegan/is_jain_excluded/allergen_flags); no `tags` dimension for it; `food_dna_tier_1` is literally "tier_1"/"tier_2" (not an ingredient class).
- **Data partially recoverable but insufficient alone:** `ingredients_v5.csv` HAS `category` {spice, vegetable, grain_flour, lentil_legume, dairy, seafood, meat, fruit, egg, …} — but (a) it isn't in the DB, (b) it doesn't map 1:1 to dim 11 (e.g. `grain_flour` → rice? wheat? — ambiguous), and (c) selecting the **"main/dominant" ingredient** from an unordered, quantity-less `Ingredients` list is **not specified anywhere**.
- **Why D:** realizing dim 11 needs a genuine specification decision (dominant-ingredient rule + category→enum map) plus either a new `ingredients.category` column (schema evolution) or a new `main_ingredient_class` tag dimension seeded from a ratified derivation. This is beyond pure derivation. (MMR degrades to 3 dims meanwhile, but the seeded `same_main_ingredient` rule depends on this field, so silent omission is not acceptable.)

### BLOCKER 8F-03 — Religious Safety (beef / pork / halal) → **B for beef/pork (derivable, no schema change); halal = C (documented MVP limitation).**
- **RE-DOC-02 dim 17 "Religious compatibility"** {all, Hindu-veg, Jain, Halal, no-beef, no-pork} defines the dimension; `constraints.ts passesReligious` already implements `no_beef→!hasBeef`, `no_pork→!hasPork`, `halal→!hasNonHalalMeat`, `jain→isJain`.
- **Decisive correction to WP-8F:** the report called these "unprovable" and leaned SER — but it did not inspect the ingredient data. **`ingredients_v5.csv` contains canonical rows `beef` and `pork`** (both `category=meat`, seeded into `public.ingredients` by seed 103; descriptions: "Kerala beef fry / Goan beef curry", "Goan vindaloo … Naga smoked pork"). Dish text confirms real beef/pork dishes exist (pork ×36, beef ×6 in `dishes.xlsx`).
- **Derivation (no schema change, NOT fragile):** `hasBeef = dish_ingredients contains ingredient 'beef'`; `hasPork = contains 'pork'`. This is a clean membership join on canonical ingredient identities — not substring name-matching. `no_beef`/`no_pork` religious filtering is therefore **fully enforceable at MVP → B.**
- **Halal is the genuine residue:** halal is a *slaughter/certification* attribute, not an ingredient identity — a chicken dish may be halal or not, and **nothing in the schema or source models it.** Recommendation: at MVP, `hasNonHalalMeat` is set conservatively (`hasPork` OR any meat-category ingredient) OR onboarding does not offer `halal`; either way **halal is a documented, Founder-accepted limitation (C)** pending a future halal-certification data SER. `profiles.religious_pref` CHECK still permits the value; the limitation must be surfaced in onboarding UX so users are not misled (safety-relevant).

### BLOCKER 8F-04 — Seasonal Affinity → **C. Intentional MVP deferral.**
- **RE-DOC-02 dim 14** defines it, but its uses are **non-MVP**: RE-DOC-04 uses `seasonal_affinity` only in a **reactivation** trigger ("re-surfaced if seasonal_affinity matches current season AND > 6 months elapsed") and as one optional ContextFit/override signal alongside weather/festival.
- **No sourced dish data:** Batch6 explicitly **declared seasonality absent** from the source files; `dishes.xlsx` carries **`Weather Affinity`** (RE-DOC-02 dim 15 — hot/rainy/cold/all_weather), **not** seasonal. `grep seasonal` on schema → 0 dish columns. `ingredients.seasonal_peak[]` exists (ingredient-level, different concept).
- **Graceful:** `scoring.ts contextFit` runs on weather/day-type/cook-time; `RecommendationContext.season` is optional. The season *boost* and season *reactivation* are deferred with no MVP behavior loss beyond the (unsourced) seasonal nuance. Document as an MVP limitation; realize dim 14 when a seasonal dataset or a `season` tag dimension is sourced.

### BLOCKER 8F-05 — Cold-start Cohort Prior (`re_cohort_class_priors` empty) → **C. Intentional MVP deferral; neutral fallback by design.**
- **DOC-P3-03 §07 LF-E02** specifies the behavior verbatim: "If no matching row: use 0.50 (neutral prior). Log as seed data gap." `scoring.ts` implements it: `cohortPrior(rawPrior, cfg) = rawPrior ?? cfg.neutralCohortPrior` with `neutralCohortPrior = 0.50` (types.ts / seed 100 config).
- **Why empty is correct:** `re_cohort_class_priors` holds `(cohort_id, class_code) → acceptance_rate_prior` — an **empirical acceptance rate** that only exists **after** real user interactions. Pre-launch there is no data (no invention permitted). **RE-DOC-04 confirms the plan:** "calibrated against actual Day-0 acceptance rates after MVP launch … adjust cohort priors first." Populated post-launch by LF-J08 (cohortWeightRecalibration).
- **Action:** none for MVP — the neutral 0.50 fallback is the designed cold-start behavior; keep it. (Related read-adapter gap — cohort **average taste vector** for LF-E03 cold-start ContentMatch — is the same class of cold-start deferral: use a neutral/zero taste vector at cold start so cohort prior + context drive ranking; documented limitation, C.)

---

## 3. Repository Evidence Matrix

| Blocker | Defined in research? | Data in source? | In seeded DB? | Schema change needed? | Verdict |
|---|---|---|---|---|---|
| 8F-01 cuisine_family | ✅ RE-DOC-02 dim 2 | ✅ cuisines_v4.cuisine_group | ✅ cuisines.cuisine_group + dishes.cuisine_id | ❌ none | **B** |
| 8F-02 main_ingredient_class | ✅ RE-DOC-02 dim 11 | 🟡 ingredients_v5.category (not 1:1) | ❌ category not seeded | ⚠️ column or tag-dim + rule | **D** |
| 8F-03 beef/pork | ✅ RE-DOC-02 dim 17 | ✅ ingredients 'beef'/'pork' | ✅ seeded + dish_ingredients | ❌ none (join) | **B** |
| 8F-03 halal | ✅ RE-DOC-02 dim 17 | 🔴 none (certification) | 🔴 none | ⚠️ future halal-data SER | **C** (limitation) |
| 8F-04 seasonal_affinity | ✅ RE-DOC-02 dim 14 | 🔴 none (Batch6 absent) | 🔴 none (weather≠season) | defer | **C** |
| 8F-05 cohort_class_priors | ✅ DOC-P3-03 LF-E02 | 🔴 none pre-launch (empirical) | ✅ table exists, empty by design | ❌ none (neutral fallback) | **C** |

---

## 4. Secondary Audit — other findings (not among the five)

1. **`CandidateRepository` is not yet implemented** — confirmed: `adapters/supabase-stores.ts` has persistence/onboarding/re-state/eligible-users stores but no CandidateRepository (the WP-8F-blocked deliverable). Building it needs only 8F-01/8F-03(beef/pork) resolved + decisions on 8F-02/halal.
2. **Transaction atomicity (implementation risk):** `SupabaseWeekPlanStore.persistWeekPlan` does sequential upserts (Supabase JS has no multi-statement txn); DOC-P4-00 §16 wants an atomic slate write. Already flagged as debt in the adapter — should become a Postgres RPC before production.
3. **`ingredients.category` not seeded (root enabler for 8F-02):** the source column exists; seeding it (a bounded, evidence-backed reseed) would also give `main_ingredient_class` a real basis.
4. **Documentation-drift / UX-safety risk:** `profiles.religious_pref` CHECK permits `halal`/`no_beef`/`no_pork`, and the engine handles them, but MVP will enforce only beef/pork+jain. Onboarding must not imply halal is enforced — otherwise a halal user is silently mis-served (safety).
5. **Safety-gate coverage:** validation `902` tests diet/jain/allergen — **not** beef/pork/halal. If beef/pork religious filtering ships (8F-03=B), a 4th safety-gate check (no_beef/no_pork → 0 violations) should be added (WP-04DA-style validation extension, not a schema change).

---

## 5. Final Recommendation (one verdict per blocker)

| Blocker | Verdict | One-line action |
|---|---|---|
| **8F-01 Cuisine Family** | **B — derivable** | `cuisineFamily = cuisines.cuisine_group` via `dishes.cuisine_id`; RE-DOC-02 dim 2. No schema change. Implement in CandidateRepository. |
| **8F-02 Main Ingredient Class** | **D — Founder SER/decision** | Ratify a "dominant ingredient" rule + realize dim 11 as a `main_ingredient_class` tag dimension (data-only) **or** seed `ingredients.category` (schema evolution) + category→enum map. Data is recoverable (`ingredients_v5.category`). |
| **8F-03 Religious (beef/pork)** | **B — derivable** | `hasBeef/hasPork = dish_ingredients ∋ ingredient 'beef'/'pork'` (clean join). Enforce `no_beef`/`no_pork` at MVP. Add a beef/pork safety-gate check. |
| **8F-03 Religious (halal)** | **C — documented MVP limitation** | Halal certification is unmodelled; scope out at MVP (conservative default or onboarding does not offer it) pending a future halal-data SER. |
| **8F-04 Seasonal Affinity** | **C — intentional MVP deferral** | Dish season unsourced (Batch6). ContextFit uses weather (dim 15). Defer seasonal boost + season-reactivation; realize dim 14 when a seasonal dataset is sourced. |
| **8F-05 Cold-start Cohort Prior** | **C — intentional MVP deferral** | `re_cohort_class_priors` empty is by design (LF-E02 → 0.50 neutral; implemented). Populate post-launch from real Day-0 acceptance (RE-DOC-04 / LF-J08). No MVP action. |

**Net effect on WP-8F:** of the four fields WP-8F called "unprovable," **8F-01 (cuisine_family) and 8F-03 beef/pork are now proven-derivable with no schema change** — the CandidateRepository can be built for them immediately. **Only 8F-02 (main_ingredient_class) requires a Founder decision/SER**; **halal, seasonal, and cohort-priors are intentional, spec-documented MVP deferrals** requiring documentation (and, for halal, an onboarding-UX safety note), not schema work. This reduces the true blocker set from "4 unprovable + 1" to **exactly one decision (8F-02) + three documented deferrals + one UX-safety note.**

---

## Critical Self-Review
- **Did I exhaust evidence before any "gap" verdict?** Yes — read RE-DOC-02 §02 (the dimension the WP-8F author could not), the ingredient/cuisine/dish source data directly, the RE consumer code, and DOC-P3-03 LFs.
- **Did I correct prior reports where evidence warranted?** Yes — 8F-01 and 8F-03(beef/pork) were mis-classified as unprovable in WP-8F; the missing evidence was RE-DOC-02 (unreadable to that author) and the ingredient rows (unchecked).
- **Any invention?** None. Where a source is genuinely absent (halal, seasonal dish data, empirical priors) it is classified as deferral/gap, not filled.
- **Read-only honored?** Yes — no runtime code, no schema/migration/seed/DB change; existing 62 tests untouched.
- **Is any "B" actually a hidden schema change?** No — 8F-01 and beef/pork are pure joins over already-seeded tables.

## Versioning & Placement
v1.0, docs/project-history/work-packages/, naming per WP-5AA. Consolidates the four required report artifacts (Traceability, Architecture Audit, Evidence Matrix, Final Recommendation) into one document per the repo's lean-governance rule. Companion: REPO-CERT-019.

---

## Founder Sign-off (one decision required: 8F-02 main_ingredient_class realization + dominant-ingredient rule)
Founder/architect ruling: ___________________________ Date: _______________
