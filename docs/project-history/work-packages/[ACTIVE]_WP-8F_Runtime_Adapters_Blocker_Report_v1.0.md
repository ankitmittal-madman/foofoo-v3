# [ACTIVE]_WP-8F_Runtime_Adapters_Blocker_Report_v1.0

**Status:** ACTIVE — **BLOCKER REPORT (STOP).** WP-8F implementation is HALTED at the mandatory schema-mapping proof: the engine's `DishCandidate` cannot be materialized from the canonical schema without guessing four mappings. No runtime adapters, endpoints, or live-DB writes were implemented (prompt rule: "Do NOT continue past uncertainty"). Companion certificate: REPO-CERT-018.
**Version:** v1.0
**Date:** 2026-07-15
**Placement:** docs/project-history/work-packages/[ACTIVE]_WP-8F_Runtime_Adapters_Blocker_Report_v1.0.md
**Builds on:** WP-8E (REPO-CERT-015), WP-8D (REPO-CERT-014).
**Evidence basis (read this session from live schema/seeds):** migrations 002 (tags, ingredients), 003 (re_meal_classes), 008 (dishes), 009 (dish_tags, dish_ingredients), 011 (plan tables), 012 (interaction_events), 021 (cuisines + dishes.cuisine_id), 022 (dish display attrs), 024 (re_dish_regional_affinity); seed 104 (tags — canonical dimension vocabulary); WP-8D `services/re/types.ts` (`DishCandidate`); DOC-P3-03 §06/§07/§08 (LF-D04, LF-E03/E05, LF-F01/F02).

---

## Executive Summary

WP-8F's highest-priority deliverable — the concrete **`CandidateRepository`** that materializes the engine's `DishCandidate` from the canonical schema — **cannot be built without inventing schema mappings.** Four fields the WP-8D engine requires have **no provable canonical source**, and one read adapter (taste, cold-start) has a fifth gap. Per the prompt's explicit rule and this repository's "no invention" governance, implementation is **STOPPED**; this report gives the exact schema location, conflicting/absent evidence, and the required decision for each blocker.

**What is provable (2 of 4 variety dimensions + allergen + jain + genome + occasion + cook time + base score):** enough for a *partial* candidate, but **not** the complete object the engine's LF-D04 (religious), LF-F01/F02 (variety), and LF-E05 (season) stages consume. A partial candidate would silently degrade safety-critical filtering — unacceptable.

**Existing verification unaffected:** no code changed this session; `deno task verify` → **62 tests, 0 failures** (re-run confirmed).

---

## What the engine requires vs what the schema provides

The `DishCandidate` (WP-8D `services/re/types.ts`) fields and their canonical sources:

| Field | Engine use (LF) | Canonical source | Status |
|---|---|---|---|
| `dishId`, `baseScore` | LF-D01 | `re_engine.re_class_dish_options` (dish_id, base_score) | ✅ provable |
| `dietType`, `isJain` | LF-D02/D04, safety | `dishes.diet_type`, `dishes.is_jain` (008) | ✅ provable |
| `ingredientAllergenUnion` | LF-D03, Gate 2 | OR of `ingredients.allergen_flags` via `dish_ingredients` (002/009) | ✅ provable |
| `mealOccasions` | LF-D05 | `dishes.meal_occasion[]` (008) | ✅ provable |
| `genomeVector` | LF-E03 | `dishes.genome_vector[]` (008) | ✅ provable |
| `cookTimeBandMinutes` | LF-E05 | `dishes.cook_time_minutes` (008) | ✅ provable |
| `cookingMethod` | LF-F01 variety | `tags.dimension='cooking_method'` via `dish_tags` (002/009/104 — 16 tags) | ✅ provable |
| `texture` | LF-F01 variety | `tags.dimension='texture'` via `dish_tags` (104 — 12 tags) | ✅ provable |
| **`cuisineFamily`** | **LF-F01 variety** | **NONE — see BLOCKER-8F-01** | ⛔ **unprovable** |
| **`mainIngredientClass`** | **LF-F01/F02 variety** | **NONE — see BLOCKER-8F-01** | ⛔ **unprovable** |
| **`hasNonHalalMeat` / `hasBeef` / `hasPork`** | **LF-D04 religious** | **NONE — see BLOCKER-8F-02** | ⛔ **unprovable** |
| **`seasonalAffinity`** | **LF-E05 context** | **NONE — see BLOCKER-8F-03** | ⛔ **unprovable** |

Plus, in the read-adapter layer: `TasteVectorRepository.getCohortAverageVector` (LF-E03 cold-start) has **no canonical source — BLOCKER-8F-04**.

---

## BLOCKER-8F-01 — dish variety dimensions `cuisine_family` and `main_ingredient_class` (LF-F01 MMR)

**Engine need:** LF-F01 (DOC-P3-03 §08) computes slate diversity via similarity across the four variety-relevant dimensions it names verbatim: **cuisine_family, cooking_method, main_ingredient_class, texture.** `DishCandidate.cuisineFamily` / `.mainIngredientClass` are dish-level.

**Evidence (exact locations):**
- Canonical `tags.dimension` vocabulary (seed `104_seed_tags.sql`, from `tags_v4.csv`, 111 rows): `dish_category`(20), `cooking_method`(16), `texture`(12), `aroma_profile`(11), `allergen`(11), `mouthfeel`(10), `richness`(7), `primary_taste`(7), `serving_temp`(5), `weather_affinity`(4), `meal_type`(4), `fermentation`(4). **No `cuisine_family` and no `main_ingredient`/`main_ingredient_class` dimension.**
- `cuisine_family` exists as a column ONLY on `re_engine.re_meal_classes` (`003_reference_tier1.sql:47`) — a **class-level** attribute, not dish-level.
- A dish→cuisine link exists: `dishes.cuisine_id → public.cuisines` (`021_cuisines_reference.sql:41`). `cuisines` (021:26) has `cuisine_group` **and** `parent_cuisine` — **neither is named "family".**
- `022_dish_display_attributes.sql` adds only `calories, serving_size, food_dna_tier_1` — not these dimensions.

**Conflict / uncertainty:** LF-F01 names `cuisine_family` and `main_ingredient_class` as dish variety dimensions, but the canonical schema has (a) no dish-level `cuisine_family` — only `cuisines.cuisine_group`/`parent_cuisine` (ambiguous which is "family"), and (b) no `main_ingredient_class` at all (`dish_category` is a category taxonomy, semantically distinct from "main ingredient").

**Required decision:**
1. Is dish `cuisine_family` = `cuisines.cuisine_group`, `cuisines.parent_cuisine`, or a new column? (RE-DOC-02 §02 genome dimensions may define this — it is `.docx`/binary and not machine-readable; a Founder/architect ruling or a readable spec excerpt is required.)
2. Is `main_ingredient_class` = `tags.dimension='dish_category'`, a new tag dimension, or a new dish column? (LF-F02 rule 3 references "main ingredient (dimension 11)" — a genome dimension not present in the canonical `tags` vocabulary.)

---

## BLOCKER-8F-02 — religious meat markers for LF-D04 (halal / no_beef / no_pork)

**Engine need:** LF-D04 (DOC-P3-03 §06) is an **ingredient-level** hard constraint: `halal` → exclude non-halal meat; `no_beef` → exclude beef-derived; `no_pork` → exclude pork-derived. `DishCandidate.hasNonHalalMeat/hasBeef/hasPork`.

**Evidence:** `public.ingredients` (`002_reference_tier0.sql`) columns: `allergen_flags, is_veg, is_vegan, is_jain_excluded, can_substitute_id, seasonal_peak[], is_active`. **No beef/pork/halal/meat-type marker.** No `tags.dimension` for meat/religious type. `jain` IS supported (`dishes.is_jain` / `ingredients.is_jain_excluded`).

**Conflict / uncertainty:** LF-D04 requires ingredient-level halal/beef/pork identification; the schema provides none. Deriving from ingredient names (e.g., name contains "beef") would be fabricated/fragile — forbidden.

**Required decision:** How are non-halal / beef / pork ingredients identified? Options: (a) add ingredient columns/flags (schema evolution → SER); (b) a new `tags.dimension` (e.g., `meat_type`) + seed; (c) declare `halal`/`no_beef`/`no_pork` out of MVP scope and degrade those `religious_pref` values to no-op with a documented, Founder-accepted limitation (note: `profiles.religious_pref` CHECK still permits these values, so onboarding can set them). **Safety-relevant — must not be guessed.**

---

## BLOCKER-8F-03 — dish `seasonal_affinity` for LF-E05 ContextFit season adjustment

**Engine need:** LF-E05 (DOC-P3-03 §07): "Boost dishes where `dish.seasonal_affinity` contains `current_season`." `DishCandidate.seasonalAffinity`.

**Evidence:** No `seasonal_affinity` column exists on `dishes` (008 + 022 confirmed) or anywhere (`grep` → 0 hits). `ingredients.seasonal_peak[]` exists (ingredient-level, would need an undocumented aggregation). `tags.dimension='weather_affinity'` exists (weather ≠ season).

**Required decision:** Source for dish seasonal affinity: (a) aggregate `ingredients.seasonal_peak[]` per dish (needs a documented rule); (b) a new `tags.dimension='season'` + seed; (c) a new `dishes.seasonal_affinity` column (SER); or (d) defer the LF-E05 season adjustment (documented limitation — ContextFit still works on weather/day-type). Non-safety, but must not be guessed.

---

## BLOCKER-8F-04 — cohort average taste vector for LF-E03 cold-start ContentMatch

**Engine need:** LF-E03 (DOC-P3-03 §07): at cold start (interaction_count=0), the user taste vector "defaults to the cohort's average taste profile." `TasteVectorRepository.getCohortAverageVector(cohortId)`.

**Evidence:** `re_engine.user_taste_vectors` (`007`) is **per-user** (`genome_tag_affinity real[]`, `class_affinity jsonb`). There is **no cohort-level taste-vector table**, and a cold-start cohort may have zero users to average.

**Required decision:** Source for the cohort average taste profile: (a) a new `re_cohort_taste_vector` seed/table (schema evolution); (b) a documented cold-start fallback (e.g., zero/neutral vector → ContentMatch ≈ 0 at cold start, with cohort prior + context driving ranking); or (c) another documented derivation. Determines cold-start recommendation quality.

---

## Why this is a hard STOP (not a proceed-with-fallback)

- The prompt is explicit: *"If ANY mapping cannot be proven from repository documents + schema, STOP. Present evidence. Do not guess."* and *"Do NOT continue past uncertainty."*
- Governance: this repo forbids invented schema mappings and fabricated defaults.
- **Safety:** BLOCKER-8F-02 (religious filter) and BLOCKER-8F-01 (variety) feed the safety-critical hard-constraint and diversity stages. Guessing here would silently mis-filter dishes for halal/no-beef/no-pork households and mis-compute variety — exactly the class of error the whole APDF discipline exists to prevent.
- A "partial" `CandidateRepository` (filling the 4 fields with defaults) is a **fabricated default**, forbidden, and would make the engine's output wrong-but-plausible.

## What was NOT done (blocked, by rule)

`CandidateRepository`, the remaining read adapters (blocked-adjacent: taste/cohort-average per 8F-04), the `/v1/onboarding` + `/v1/recommendations` HTTP endpoints (depend on the full engine), and all live-DB validation. **No code was written this session** — the mapping proof failed the gate before implementation.

> **Note on live-DB validation:** even absent the mapping blockers, the prompt's "verify week/slot/score persistence against the real canonical database" needs care — `profiles.id` FKs `auth.users`, so write-path validation requires a **disposable/staging** project (the WP-6E clean-room pattern), never test writes into the canonical **production** dataset. Recommend staging for WP-8F write validation.

## Required decisions to unblock WP-8F (summary for Founder/architect)

| # | Decision | Type | Safety |
|---|---|---|---|
| 8F-01a | dish `cuisine_family` = cuisines.cuisine_group / parent_cuisine / new | DCR or SER | variety |
| 8F-01b | `main_ingredient_class` source (dish_category / new tag dim / new column) | DCR or SER | variety |
| 8F-02 | halal/beef/pork ingredient markers (add flags / tag dim / defer-as-limitation) | **SER or scoped limitation** | **safety** |
| 8F-03 | dish `seasonal_affinity` source (aggregate seasonal_peak / new tag dim / new column / defer) | DCR/SER or limitation | context |
| 8F-04 | cohort average taste vector source (new table / neutral fallback / derivation) | SER or documented fallback | cold-start quality |

Several of these (8F-02, 8F-04, possibly 8F-01b/8F-03) imply **schema evolution (SER)** — which is Founder-gated and outside WP-8F's "no migration change" scope. That is itself the reason WP-8F cannot proceed as scoped without a prior decision.

## Critical Self-Review

- **Did I guess any mapping?** No — every unprovable field is documented with its exact absent/ambiguous schema location.
- **Did I read the actual schema (not memory)?** Yes — migrations 002/003/008/009/011/012/021/022/024 and seed 104 this session.
- **Could a readable spec resolve these?** Partially — RE-DOC-02 (20 genome dimensions) may define cuisine_family/main_ingredient, but it is `.docx` (binary, unreadable here); a Founder ruling or a Markdown excerpt is required. Flagged, not guessed.
- **Existing system harmed?** No — zero code change; 62 tests still pass.

## Versioning & Placement

v1.0, docs/project-history/work-packages/ per the Placement Rule; naming per WP-5AA. Companion: REPO-CERT-018.

## Founder Sign-off (decisions 8F-01…8F-04 required to unblock)

Founder/architect rulings: ___________________________ Date: _______________
