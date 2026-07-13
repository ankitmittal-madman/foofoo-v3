# [ACTIVE]_Batch2_GapAnalysis_Package_v1.0

**Phase 3.5 — Batch 2 — Stage 4: Gap Analysis**
**Methodology:** Identical to `Batch1_GapAnalysis_Package_v1.1` (frozen) — not re-explained here.
**Sole input:** `Batch2_Mapping_Package_v1.0` (APPROVED INPUT, not reopened)
**Classification authority:** `DOC-P3-09_Knowledge_Integration_Governance_v1.1` §15 Phase 6 (Category A/B/C1/C2/C3)
**Date:** 2026-07-02
**Status:** Draft — Ready for Founder Review

**Discipline note:** Every classification below states only what the evidence proves. No resolution type (AGR/SER/DCR), schema change, or implementation is recommended anywhere in this document — that is Resolution's decision, not this stage's.

---

## Executive Summary

All 7 Mapping Issues from `Batch2_Mapping_Package_v1.0` are classified. **4 are Category C1** (architecture does not currently support the concept at all — no candidate table or column exists). **2 are Category B** (a destination column exists; what's incomplete is the value-population rule, not the structure). **1 is Category C2** (a genuine business-meaning question, not a structural or data-completeness gap). **0 are Category A** (nothing here was a clean/automatic mapping — those weren't raised as issues) and **0 are Category C3** (no conflicting source-data evidence was found anywhere in this batch — Batch 2's three files agreed with each other and with the frozen architecture on every fact checked; the gaps are all absences or undefined rules, not conflicts).

---

## Gap Classification Matrix

| Gap ID | Originating MAP ID | Classification | Why |
|---|---|---|---|
| B2-GAP-001 | B2-MI-001 | **C1** | No table for Ingredient Alias exists anywhere in frozen architecture — architecture does not support the concept at all, not a data-completeness or business-meaning question |
| B2-GAP-002 | B2-MI-002 | **C1** | Same reasoning — no table for Dish Term Synonym |
| B2-GAP-003 | B2-MI-003 | **C1** | Same reasoning — no table for the 7 disambiguation records, and no evidence that MI-002's eventual destination (if one is created) would also suit this different content type |
| B2-GAP-004 | B2-MI-004 | **C1** | 5 Ingredient attributes have no matching column anywhere in `public.ingredients` — a structural absence, not incomplete data within an existing column |
| B2-GAP-005 | B2-MI-005 | **C2** | The destination column (`is_veg`, boolean) exists and is structurally sufficient for 190 of 191 rows; the 1 `diet_type='egg'` row is not a missing-architecture problem, it is a question of what "egg" should mean for `is_veg` — a business-meaning decision, evidenced by `public.profiles.diet_type` already treating `'egg'` as a category distinct from both `'veg'` and `'non_veg'` elsewhere in the frozen schema |
| B2-GAP-006 | B2-MI-006 | **B** | The destination column (`allergen_flags`, integer bitmask) already exists and architecturally supports the concept; what is incomplete is the bit-position-to-allergen-type assignment — this is missing/incomplete data within a supported structure, not an absent structure |
| B2-GAP-007 | B2-MI-007 | **C1** | Directly and entirely dependent on B2-GAP-001 — the relationship cannot exist independently of its source entity's table |

**0 Category A. 2 Category B. 4 Category C1. 1 Category C2. 0 Category C3.**

---

## Gap Register

### B2-GAP-001
- **Originating MAP ID:** B2-MI-001
- **OBS lineage:** B2-OBS-ENT-002 (Ingredient Alias, `ingredient_aliases_v2.csv`, 167 rows)
- **CAN lineage:** B2-CAN-ENT-002 (164 canonical rows after 3 Version/Patch merges)
- **Evidence:** Full-text search of every frozen `.sql` migration file (`002`–`020`) and `DOC-P3-04` v1.3 for "alias" — 0 matches
- **Gap Classification:** C1
- **Why this classification is correct:** The search was exhaustive and returned zero candidate tables or columns. This is not a case of an existing structure lacking a value — no structure exists to evaluate.
- **Business Impact:** Regional-language ingredient names (167 rows across 7 languages) cannot be surfaced to users or used for search/matching if not persisted
- **Technical Impact:** No consuming logical function in `RE-DOC-01–05` currently reads alias data, so no RE pipeline is broken today — but nothing prevents a future one from needing it
- **Seed Impact:** 164 canonical rows have nowhere to load
- **Cross-Batch Impact:** None identified — this concept is Batch-2-scoped only, no other batch's canonical data references it
- **Owner:** Architecture
- **Priority:** High
- **Confidence:** High (100% — exhaustive negative search)
- **Resolution Readiness:** Ready

### B2-GAP-002
- **Originating MAP ID:** B2-MI-002
- **OBS lineage:** B2-OBS-ENT-003 (Dish Term Synonym, `term_synonyms_v2.csv`, 121 rows)
- **CAN lineage:** B2-CAN-ENT-003 (114 canonical rows after excluding 7 disambiguation records)
- **Evidence:** Full-text search of every frozen `.sql` migration file and `DOC-P3-04` for "synonym" — 0 matches
- **Gap Classification:** C1
- **Why this classification is correct:** Same exhaustive-negative-search basis as B2-GAP-001; no candidate table exists.
- **Business Impact:** Regional dish-name variants (Gol Gappa/Puchka/Gupchup for Pani Puri, etc.) cannot be matched to a canonical dish if a user searches by a regional name
- **Technical Impact:** No RE-DOC function currently reads synonym data
- **Seed Impact:** 114 canonical rows have nowhere to load
- **Cross-Batch Impact:** This entity's `canonical_name` values are dish names — the same names Batch 4 will canonicalize from `dishes.xlsx`. Whatever destination is eventually created must reconcile with Batch 4's dish catalogue rather than assume a separate, disconnected identity space. This is a genuine cross-batch consideration, evidenced by the content itself, not inferred.
- **Owner:** Architecture
- **Priority:** High
- **Confidence:** High (100%)
- **Resolution Readiness:** Ready

### B2-GAP-003
- **Originating MAP ID:** B2-MI-003
- **OBS lineage:** B2-OBS-ENT-003 (the 7 rows within `term_synonyms_v2.csv` carrying a `(disambiguation)` marker)
- **CAN lineage:** B2-CAN-EX-001 (excluded from B2-CAN-ENT-003)
- **Evidence:** Same search as B2-GAP-002 — 0 matches; content review confirms these 7 rows serve a different purpose (ambiguity warning, not name mapping) than the other 114
- **Gap Classification:** C1
- **Why this classification is correct:** No table exists for this content either; classified independently from B2-GAP-002 because the content type differs and no evidence proves the two would share a future destination
- **Business Impact:** Generic/ambiguous dish terms (Biryani, Chutney, Curry, etc.) have no persisted warning to guide disambiguation logic if the app ever needs to prompt a user for clarification
- **Technical Impact:** None identified in current RE-DOC scope
- **Seed Impact:** 7 rows have nowhere to load
- **Cross-Batch Impact:** Same dish-name-space consideration as B2-GAP-002 — these 7 terms overlap with generic dish-family names Batch 4 will also encounter
- **Owner:** Architecture
- **Priority:** Low
- **Confidence:** High (100% on the gap; the "distinct destination" premise is Medium — noted, not overstated)
- **Resolution Readiness:** Ready

### B2-GAP-004
- **Originating MAP ID:** B2-MI-004
- **OBS lineage:** B2-OBS-ENT-001 (`display_name`, `category`, `common_unit`, `is_common`, `description` columns of `ingredients_v5.csv`)
- **CAN lineage:** B2-CAN-ENT-001 (partial)
- **Evidence:** Full DDL read of `public.ingredients` (`_ACTIVE__002_reference_tier0.sql` lines 10–20) — 9 columns total, none of these 5 names present
- **Gap Classification:** C1
- **Why this classification is correct:** These are structural absences in an existing table, not values missing from an existing column — the columns themselves don't exist.
- **Business Impact:** No human-readable ingredient name, category grouping, unit-of-measure, "common ingredient" flag, or description would be available to any downstream feature that reads `public.ingredients` directly
- **Technical Impact:** `RE-DOC-01–05`'s Food DNA / genome scoring reads `public.tags`/`dish_tags`, not these 5 attributes directly — no evidence this blocks RE scoring specifically
- **Seed Impact:** All 191 ingredient rows are affected for these 5 attributes specifically (the other 10 attributes are unaffected)
- **Cross-Batch Impact:** None identified
- **Owner:** Architecture
- **Priority:** Medium
- **Confidence:** High (100%)
- **Resolution Readiness:** Ready

### B2-GAP-005
- **Originating MAP ID:** B2-MI-005
- **OBS lineage:** B2-OBS-ENT-001 (`diet_type` column, value `'egg'`, 1 of 191 rows)
- **CAN lineage:** B2-CAN-VOC-002 (Ingredient Diet Type, 3 values)
- **Evidence:** `public.ingredients.is_veg` is `boolean NOT NULL` (2-state only); `public.profiles.diet_type` (a different, already-frozen table) independently enumerates `'egg'` as a category distinct from `'veg'`/`'non_veg'` — showing the project's own frozen schema elsewhere already treats "egg" as its own thing, not a subtype of veg or non-veg
- **Gap Classification:** C2
- **Why this classification is correct:** The column exists and is structurally adequate for the other 190 rows; what's missing is not structure but a decision about meaning — whether an egg-containing ingredient should be treated as `is_veg=true` or `false` for the ingredient-level record, given the project already keeps "egg" conceptually separate at the profile level
- **Business Impact:** Affects diet-safety correctness for exactly 1 ingredient row if defaulted incorrectly (e.g., a strict-vegetarian household seeing an egg-derived ingredient marked `is_veg=true`)
- **Technical Impact:** Any RE logic that filters on `is_veg` inherits whatever default is chosen
- **Seed Impact:** 1 of 191 rows
- **Cross-Batch Impact:** None identified
- **Owner:** Founder/Product
- **Priority:** Low
- **Confidence:** Medium (the gap is clearly evidenced; "low priority" reflects the 1-row blast radius, not any uncertainty about the finding itself)
- **Resolution Readiness:** Ready

### B2-GAP-006
- **Originating MAP ID:** B2-MI-006
- **OBS lineage:** B2-OBS-ENT-001 (`allergen_type`, 10-value vocabulary, populated on 45 of 191 rows)
- **CAN lineage:** B2-CAN-VOC-003 (Allergen Type)
- **Evidence:** `public.ingredients.allergen_flags` is `integer NOT NULL DEFAULT 0` (bitmask-shaped, consistent with `public.profiles.allergen_flags` using the identical pattern elsewhere in frozen architecture); no section of `DOC-P3-04` defines which bit position corresponds to which of the 10 allergen types
- **Gap Classification:** B
- **Why this classification is correct:** The architecture already supports storing this concept structurally (the column exists, and the bitmask pattern is an established, precedented convention in this schema, not a new idea). What's incomplete is a value-assignment table (bit ↔ allergen type), which is data/configuration, not a missing structure — matching Category B's definition exactly ("architecture supports it, data missing/incomplete").
- **Business Impact:** All 45 allergen-flagged ingredients are affected until an encoding exists — allergen-avoidance logic (a stated safety-critical function per `RE-DOC-02`) cannot be seeded correctly without it
- **Technical Impact:** `RE-DOC-02`'s hard-constraint allergen propagation logic depends on this data being loadable
- **Seed Impact:** 45 of 191 rows carry allergen data awaiting this encoding
- **Cross-Batch Impact:** None identified — allergen encoding is a Batch-2-introduced concept; no other batch has raised it yet
- **Owner:** Architecture
- **Priority:** Medium-High
- **Confidence:** High (100% on the gap; Category B assignment itself is High confidence given the direct structural precedent from `public.profiles.allergen_flags`)
- **Resolution Readiness:** Ready

### B2-GAP-007
- **Originating MAP ID:** B2-MI-007
- **OBS lineage:** B2-OBS-REL-001 (Ingredient Alias → Ingredient)
- **CAN lineage:** B2-CAN-REL-001
- **Evidence:** Entirely dependent on B2-GAP-001 — no independent evidence beyond that
- **Gap Classification:** C1
- **Why this classification is correct:** A relationship cannot be structurally supported when its source-side entity has no table; this is not an independent architecture gap, it inherits B2-GAP-001's classification
- **Business Impact:** None beyond what B2-GAP-001 already describes
- **Technical Impact:** None beyond B2-GAP-001
- **Seed Impact:** None beyond B2-GAP-001 — do not double-count row impact
- **Cross-Batch Impact:** None identified
- **Owner:** Architecture
- **Priority:** High (matches B2-GAP-001 — tracked jointly, not scored independently)
- **Confidence:** High
- **Resolution Readiness:** Ready (resolves automatically once B2-GAP-001 resolves)

---

## Evidence Register

| Gap ID | Evidence Source | Type |
|---|---|---|
| B2-GAP-001 | Full-text search, all frozen `.sql` files + `DOC-P3-04` v1.3, term "alias" | Negative search (exhaustive) |
| B2-GAP-002 | Full-text search, same scope, term "synonym" | Negative search (exhaustive) |
| B2-GAP-003 | Same search + `Batch2_Canonicalization_Package_v1.0` §8 (`B2-CAN-EX-001`) | Negative search + canonical record |
| B2-GAP-004 | `_ACTIVE__002_reference_tier0.sql` lines 10–20, `public.ingredients` full DDL | Direct DDL read |
| B2-GAP-005 | `_ACTIVE__002_reference_tier0.sql` (`is_veg` boolean); `_ACTIVE__005_profiles.sql` (`diet_type` enum including `'egg'`) | Direct DDL read, cross-referenced |
| B2-GAP-006 | `_ACTIVE__002_reference_tier0.sql` (`allergen_flags` integer); `_ACTIVE__005_profiles.sql` (same pattern) | Direct DDL read, cross-referenced |
| B2-GAP-007 | B2-GAP-001 (inherited) | Derived, not independent |

**No source outside the frozen architecture and the frozen Batch 2 Mapping package was used.**

---

## Impact Matrix

| Gap ID | Business | Technical | Seed | Cross-Batch |
|---|---|---|---|---|
| B2-GAP-001 | Medium-High | Low (no current RE consumer) | 164 rows blocked | None |
| B2-GAP-002 | Medium-High | Low | 114 rows blocked | None |
| B2-GAP-003 | Low | None identified | 7 rows blocked | None |
| B2-GAP-004 | Medium | Low | 191 rows partially blocked (5 of 15 attributes) | None |
| B2-GAP-005 | Low (1-row blast radius) | Low | 1 row | None |
| B2-GAP-006 | High (safety-relevant) | Medium (RE-DOC-02 dependency) | 45 rows | None |
| B2-GAP-007 | (inherits B2-GAP-001) | (inherits) | (inherits, not additive) | None |

---

## Priority Matrix

| Priority | Gaps |
|---|---|
| High | B2-GAP-001, B2-GAP-002, B2-GAP-007 |
| Medium-High | B2-GAP-006 |
| Medium | B2-GAP-004 |
| Low | B2-GAP-003, B2-GAP-005 |

---

## Ownership Matrix

| Owner | Gaps |
|---|---|
| Architecture | B2-GAP-001, B2-GAP-002, B2-GAP-003, B2-GAP-004, B2-GAP-006, B2-GAP-007 |
| Founder/Product | B2-GAP-005 |

---

## Confidence Matrix

| Confidence | Gaps |
|---|---|
| High | B2-GAP-001, B2-GAP-002, B2-GAP-004, B2-GAP-006, B2-GAP-007 |
| Medium | B2-GAP-003, B2-GAP-005 |
| Low | None |

---

## Resolution Readiness Matrix

| Gap ID | Ready for Resolution? | Note |
|---|---|---|
| B2-GAP-001 | ✅ Ready | Evidence complete |
| B2-GAP-002 | ✅ Ready | Evidence complete; cross-batch note carried forward for Resolution's awareness, not resolved here |
| B2-GAP-003 | ✅ Ready | Evidence complete |
| B2-GAP-004 | ✅ Ready | Evidence complete |
| B2-GAP-005 | ✅ Ready | Evidence complete; Founder input is what Resolution will need to seek, not additional evidence-gathering |
| B2-GAP-006 | ✅ Ready | Evidence complete |
| B2-GAP-007 | ✅ Ready | Resolves jointly with B2-GAP-001 |

**7 of 7 gaps ready for Resolution. 0 require further Discovery, Canonicalization, or Mapping work before Resolution can proceed.**

---

## Regression Review

- ✅ `Batch2_Mapping_Package_v1.0` not reopened or modified
- ✅ No architecture, schema, RE, or API document touched
- ✅ No AGR, SER, or DCR recommended anywhere in this document
- ✅ No schema change, implementation, or SQL proposed
- ✅ No new entity or relationship invented
- ✅ No Batch 1 document touched
- ✅ `DOC-P3-12` left untouched — no governance-only (non-data/architecture-affecting) improvement was discovered during this stage; everything found here is squarely a data/architecture/lineage matter, correctly kept in-line rather than deferred

---

## Stage Completion Summary

7 of 7 Mapping Issues classified: 4 Category C1, 2 Category B, 1 Category C2, 0 Category A, 0 Category C3. Every gap carries complete OBS→CAN lineage, evidence, impact, ownership, priority, confidence, and resolution readiness. No resolution type recommended for any gap.

---

## Resolution Readiness Summary

All 7 gaps are evidence-complete and ready for Stage 5 (Resolution). B2-GAP-001/002/007 form one interconnected cluster (Architecture owner). B2-GAP-003 is a smaller, related cluster sharing the same missing-table root cause but a distinct content type. B2-GAP-004 is a standalone Architecture item. B2-GAP-005 needs Founder/Product input specifically (not Architecture). B2-GAP-006 has the clearest path of all seven — Category B with a direct structural precedent already in the frozen schema (`public.profiles.allergen_flags`).

---

## Founder Approval Gate

**Batch 2 Gap Analysis is complete. Resolution has NOT begun. No AGR, SER, or DCR has been created. No implementation has been prepared.**

Founder sign-off: _______________________ Date: ___________
