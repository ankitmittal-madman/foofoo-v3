# [ACTIVE]_Batch2_Mapping_Package_v1.0

**Phase 3.5 — Batch 2 — Stage 3: Knowledge Mapping**
**Methodology:** Identical to `Batch1_Mapping_Package_v1.1` (frozen) — not re-explained here.
**Input:** `Batch2_Canonicalization_Package_v1.0` (FROZEN)
**Target:** Frozen architecture only — `DOC-P3-04` v1.3, all frozen DDL (`002`–`020`)
**Date:** 2026-07-02
**Status:** Draft — Ready for Founder Review

---

## 0. Baseline Confirmation

`Batch2_Discovery_Report_v1.1` and `Batch2_Canonicalization_Package_v1.0` both confirmed APPROVED — ACTIVE — FROZEN. Full-text search of every frozen `.sql` migration file (`002`–`020`) and `DOC-P3-04` for "alias" or "synonym" returned **zero matches anywhere in the frozen architecture** — this single fact drives most of this package's findings and was verified directly, not assumed.

---

## 1. Entity Mapping Matrix

| CAN ID | Entity | Destination | Status |
|---|---|---|---|
| B2-CAN-ENT-001 | Ingredient | `public.ingredients` | **Mapped** — destination exists, partial column coverage (see §2) |
| B2-CAN-ENT-002 | Ingredient Alias | *(none found)* | **Mapping Issue — B2-MI-001** |
| B2-CAN-ENT-003 | Dish Term Synonym | *(none found)* | **Mapping Issue — B2-MI-002** |
| B2-CAN-EX-001 | 7 disambiguation records | *(none found)* | **Mapping Issue — B2-MI-003** |

---

## 2. Attribute Mapping Matrix

### Ingredient (B2-CAN-ENT-001 → `public.ingredients`)

| Attribute | Destination Column | Mapping Type | Status |
|---|---|---|---|
| `name` | `name` | Direct | Mapped |
| `is_vegan` | `is_vegan` | Direct | Mapped |
| `is_jain_compatible` | `is_jain_excluded` | Direct, polarity inverted (`'Y'→false`, `'N'→true`) — deterministic, no ambiguity | Mapped |
| `is_active` | `is_active` | Direct | Mapped |
| `diet_type` ('veg'/'non_veg'/'egg') | `is_veg` (boolean) | Transformation — **ambiguous for `'egg'`** | **Mapping Issue — B2-MI-005** |
| `is_allergen` + `allergen_type` (10 values) | `allergen_flags` (integer bitmask) | Destination column exists; **no bit-position encoding scheme found anywhere in frozen architecture** | **Mapping Issue — B2-MI-006** |
| `display_name`, `category`, `common_unit`, `is_common`, `description` | *(none)* | No matching column | **Mapping Issue — B2-MI-004** |
| `is_updated`, `last_update_date`, `is_review` | *(none)* | Source-side annotation/administrative flags — same category as Batch 1's `_FounderInfoOnly` columns | Not Applicable — no destination needed |

**Reverse observation (not a Mapping Issue — target has data Batch 2 doesn't supply, not the other way round):** `public.ingredients.can_substitute_id` and `.seasonal_peak` have no corresponding source column in `ingredients_v5.csv`. Recorded for completeness; does not block loading Batch 2's actual data.

### Ingredient Alias / Dish Term Synonym / Disambiguation Records
No attribute-level mapping is possible — the entities themselves have no destination table (B2-MI-001/002/003). Attributes are not evaluated column-by-column against a table that doesn't exist.

---

## 3. Vocabulary Mapping Matrix

| CAN ID | Vocabulary | Destination | Status |
|---|---|---|---|
| B2-CAN-VOC-001 | Ingredient Category | *(none — tied to B2-MI-004)* | Mapping Issue |
| B2-CAN-VOC-002 | Ingredient Diet Type | `is_veg` (tied to B2-MI-005) | Mapping Issue |
| B2-CAN-VOC-003 | Allergen Type | `allergen_flags` (tied to B2-MI-006) | Mapping Issue |
| B2-CAN-VOC-004 | Common Unit | *(none — tied to B2-MI-004)* | Mapping Issue |
| B2-CAN-VOC-005 | Alias Language | *(none — tied to B2-MI-001)* | Mapping Issue |
| B2-CAN-VOC-006 | Synonym Language | *(none — tied to B2-MI-002)* | Mapping Issue |

---

## 4. Relationship Mapping Matrix

| CAN ID | Relationship | Status |
|---|---|---|
| B2-CAN-REL-001 | Ingredient Alias → Ingredient | **Mapping Issue — B2-MI-007** (cannot map a relationship whose source-side entity has no destination table; dependent on B2-MI-001) |

**Cross-batch observation (B2-OBS-REL-002, Dish Term Synonym → future Batch 4 Dish entity) is NOT mapped here** — per instruction, it is not projected into Batch 4 at all. It remains exactly what Discovery recorded it as: an observation.

---

## 5. Business Rule Mapping Matrix

| CAN ID | Rule | Destination | Status |
|---|---|---|---|
| B2-CAN-RULE-001 | `is_allergen='Y'` ⟺ `allergen_type` populated | `allergen_flags` | Enforcement blocked pending the same encoding decision as **B2-MI-006** — not a separate issue |
| B2-CAN-RULE-002 | `is_vegan='Y'` ⟹ `diet_type='veg'` | `is_vegan` / `is_veg` | **Mapped — Direct.** Both destination columns already exist; the rule restates cleanly as `is_vegan=true ⟹ is_veg=true`, a direct corollary of existing columns. No issue. |

---

## 6. Persistence Destination Matrix (summary)

| Canonical Object | Destination Exists? | Clean Mapping? |
|---|---|---|
| Ingredient (9 of 15 attributes) | ✅ Yes | ✅ 4 direct, 2 with deterministic transformation, 3 annotation-only (N/A) |
| Ingredient (6 of 15 attributes) | ❌ No / ⚠️ Ambiguous | ❌ 5 no column, 1 ambiguous value-transform, 1 undefined encoding |
| Ingredient Alias (whole entity, 164 rows) | ❌ No | ❌ No table anywhere |
| Dish Term Synonym (whole entity, 114 rows) | ❌ No | ❌ No table anywhere |
| Disambiguation Records (7 rows) | ❌ No | ❌ No table anywhere |
| Ingredient Alias → Ingredient relationship | ❌ No | ❌ Blocked by entity gap |

---

## 7. Mapping Issues Register

| MAP ID | Reason | Evidence | Target Object | Expected Destination | Confidence | Owner | Recommended Next Stage |
|---|---|---|---|---|---|---|---|
| B2-MI-001 | Ingredient Alias entity (164 canonical rows) has no table anywhere in frozen architecture | Full-text search of all frozen `.sql` files and `DOC-P3-04` for "alias" — 0 matches | B2-CAN-ENT-002 | Unknown — no candidate table exists | High (100% — search is exhaustive and negative) | Architecture | Gap Analysis (likely Category C1 → AGR path, since this isn't a Founder wording question, it's a structural absence) |
| B2-MI-002 | Dish Term Synonym entity (114 canonical rows) has no table anywhere in frozen architecture | Same search, "synonym" — 0 matches | B2-CAN-ENT-003 | Unknown — no candidate table exists; conceptually adjacent to the future `public.dishes` (Batch 4) but that table doesn't yet exist in canonicalized form for this batch to target | High | Architecture | Gap Analysis |
| B2-MI-003 | The 7 excluded disambiguation records have no table (same root cause as B2-MI-002, distinct because the content type — an ambiguity warning, not a name-to-name mapping — may warrant a different destination even if one is created for B2-MI-002) | `Batch2_Canonicalization_Package_v1.0` §8, `B2-CAN-EX-001` | 7 rows under B2-CAN-EX-001 | Unknown — do not assume it shares B2-MI-002's eventual destination | Medium (the gap itself is High confidence; the assumption that it's a *different* destination than MI-002 is a judgment call, not proven) | Architecture | Gap Analysis |
| B2-MI-004 | 5 Ingredient attributes (`display_name`, `category`, `common_unit`, `is_common`, `description`) have no matching column in `public.ingredients` | Full DDL read, `_ACTIVE__002_reference_tier0.sql` lines 10–20 | B2-CAN-ENT-001 (partial) | Unknown — `public.ingredients` would need new columns, or these are intentionally not persisted (Discovery-only context) | High (absence confirmed); intent unknown | Architecture | Gap Analysis |
| B2-MI-005 | `diet_type='egg'` has no deterministic mapping to boolean `is_veg` | `_ACTIVE__002_reference_tier0.sql` (`is_veg boolean NOT NULL`, no third state); 1 of 191 ingredients carries `diet_type='egg'` | B2-CAN-ENT-001.diet_type | `is_veg` column exists, but a business decision is needed on how egg-category ingredients are represented | Medium | Founder/Product | Gap Analysis (Founder Decision, not architecture) |
| B2-MI-006 | `allergen_type` (10-value vocabulary) has a destination column (`allergen_flags`, integer) but no bit-position encoding scheme is defined anywhere in frozen architecture | `_ACTIVE__002_reference_tier0.sql` (`allergen_flags integer NOT NULL DEFAULT 0`); no `DOC-P3-04` section defines which bit = which allergen | B2-CAN-ENT-001.allergen_type, B2-CAN-VOC-003 | Column exists; encoding table/mapping does not | Medium-High (gap confirmed; likely resolvable as a Documentation Update once the 10-value vocabulary is bit-assigned, not necessarily a schema change) | Architecture | Gap Analysis |
| B2-MI-007 | Ingredient Alias → Ingredient relationship cannot be persisted because its source-side entity has no table | Dependent on B2-MI-001 | B2-CAN-REL-001 | Resolves automatically once B2-MI-001 resolves — not independent | High | Architecture | Gap Analysis (track jointly with B2-MI-001, do not double-count) |

**7 Mapping Issues raised. 0 resolved. 0 schema changes proposed. 0 new entities invented.**

---

## 8. Mapping Confidence

| Finding Type | Confidence |
|---|---|
| "No table exists" findings (B2-MI-001, 002, 004) | High — exhaustive full-text search, negative result |
| "Column exists but transformation/encoding undefined" (B2-MI-005, 006) | Medium-High on the gap; the eventual resolution path is a judgment call, correctly deferred |
| Direct/clean mappings (name, is_vegan, is_jain_compatible→is_jain_excluded, is_active, RULE-002) | High (100%) |
| B2-MI-003 (distinct-destination assumption) | Medium — flagged as the one judgment call in this package |

---

## OBS → CAN → MAP Lineage

```
B2-OBS-ENT-001 → B2-CAN-ENT-001 → B2-MAP-ENT-001 (public.ingredients, partial)
B2-OBS-ENT-002 → B2-CAN-ENT-002 → B2-MI-001 (no destination)
B2-OBS-ENT-003 → B2-CAN-ENT-003 → B2-MI-002 (no destination)
B2-CAN-EX-001  →                  B2-MI-003 (no destination, distinct from MI-002)
B2-OBS-REL-001 → B2-CAN-REL-001 → B2-MI-007 (blocked by MI-001)
B2-OBS-REL-002 → (not canonicalized) → (not mapped — remains observation, Batch 4)
B2-OBS-RULE-001/002 → B2-CAN-RULE-001/002 → RULE-001 blocked by MI-006; RULE-002 Mapped Direct
```

---

## Executive Summary

Batch 2's Ingredient entity maps cleanly for 4 of 15 attributes, deterministically transforms for 2 more, and correctly excludes 3 as annotation-only — a majority workable outcome. The larger finding is structural: **the entire Ingredient Alias and Dish Term Synonym concepts have no persistence destination anywhere in the frozen architecture** — this was not visible until Batch 2's own canonical entities were mapped against it, since Batch 1 never touched multilingual alias/synonym data. This is a materially different situation from Batch 1's Architecture Confirmation items (which were mostly "absence, intent unknown") — here, there isn't even a candidate table to evaluate. 7 Mapping Issues raised, all evidence-backed, none resolved, none silently worked around.

---

## Regression Review

- ✅ No architecture, schema, RE, or API document touched
- ✅ No Batch 1 or Batch 2 frozen document reopened
- ✅ No entity invented, no relationship invented, no schema redesigned
- ✅ No Batch 4 persistence inferred — B2-OBS-REL-002 untouched, not mapped
- ✅ Every Mapping Issue cites direct evidence (a completed search or a direct DDL read), not assumption

---

## Gap Readiness Summary

All 7 Mapping Issues are cleanly evidenced and ready for Gap Analysis classification (Category A/B/C1/C2/C3 per `DOC-P3-09` §15 Phase 6). Likely early read, not a Gap Analysis decision: B2-MI-001/002/003/004 look like **C1 (Architecture Gap)** candidates (no destination exists at all); B2-MI-005 looks like **C2 (Business Ambiguity)** (Founder call on egg-diet representation); B2-MI-006 looks like **C3 or a Documentation Update** (encoding scheme, not a missing column). B2-MI-007 is not independent — it resolves with B2-MI-001. No blocker prevents proceeding to Gap Analysis.

---

## Founder Approval Gate

**Batch 2 Mapping is complete. Gap Analysis has NOT begun. Resolution has NOT begun. Architecture Confirmation and Governance Evaluation have NOT been created — not yet required.**

Founder sign-off: _______________________ Date: ___________
