# [ACTIVE]_Batch2_Canonicalization_Package_v1.0

**Phase 3.5 — Batch 2 — Stage 2: Canonicalization**
**Methodology:** Identical to `Batch1_Canonicalization_Package_v1.1` (frozen) — not re-explained here. Reference that document for the general canonicalization discipline, confidence-banding rules, and exclusion philosophy.
**Input:** `Batch2_Discovery_Report_v1.1` (FROZEN)
**Date:** 2026-07-02
**Status:** Draft — Ready for Founder Review

---

## 1. Canonical Entity Dictionary

| ID | Entity | Canonical Key | Source | Confidence |
|---|---|---|---|---|
| B2-CAN-ENT-001 | Ingredient | `name` | B2-OBS-ENT-001 | High (100%) |
| B2-CAN-ENT-002 | Ingredient Alias | `(ingredient_name, alias, language)` | B2-OBS-ENT-002 | High (100%) |
| B2-CAN-ENT-003 | Dish Term Synonym | `(canonical_name, synonym, language)` | B2-OBS-ENT-003, minus 7 rows — see Exclusion Register | High (100%) |

**Critical rule applied, per Founder instruction:** Ingredient, Ingredient Alias, and Dish Term Synonym remain **three independent canonical families**. No merge was performed or considered between them, regardless of structural similarity between the two synonym-shaped files (§B2-F-1 in Discovery already established they don't share scope).

---

## 2. Canonical Attribute Dictionary

Direct 1:1 canonicalization — every source column already carries a clean, unambiguous name and domain (unlike Batch 1's 5-cross-referenced-sheet workbook, no column consolidation or renaming was required). Full attribute list is Discovery §4 (`Batch2_Discovery_Report_v1.1`), unchanged; each becomes a `B2-CAN-ATT-*` with identical name, type, and domain. Not reproduced row-by-row here — no transformation occurred that would justify a separate table (per Task instruction: "if a section has nothing new compared to Batch 1[methodology], reference Batch 1[-style output]; do not duplicate content").

**Exception requiring a decision (see Exclusion Register below):** `term_synonyms_v2.canonical_name` mixes two attribute purposes (dish-name label vs. disambiguation-warning label) — resolved by excluding the 7 warning rows from the main entity rather than forcing them into the same attribute definition as the other 86.

---

## 3. Canonical Vocabulary Dictionary

| ID | Vocabulary | Values | Source |
|---|---|---|---|
| B2-CAN-VOC-001 | Ingredient Category | 17 | B2-OBS-VOC-001 |
| B2-CAN-VOC-002 | Ingredient Diet Type | 3 | B2-OBS-VOC-002 |
| B2-CAN-VOC-003 | Allergen Type | 10 | B2-OBS-VOC-003 |
| B2-CAN-VOC-004 | Common Unit | 7 | B2-OBS-VOC-004 |
| B2-CAN-VOC-005 | Alias Language | 7 | B2-OBS-VOC-005a |
| B2-CAN-VOC-006 | Synonym Language | 20 | B2-OBS-VOC-005b |

**VOC-005 and VOC-006 are kept as two separate canonical vocabularies, not merged** — see Non-Merge Register (§9). Same discipline as the entity-level non-merge above: structural similarity (both are "language" columns) is not evidence of identical scope.

---

## 4. Canonical Relationship Dictionary

| ID | Relationship | Status |
|---|---|---|
| B2-CAN-REL-001 | Ingredient Alias → Ingredient | **Canonicalized** — 100% referential match (B2-OBS-REL-001), high confidence, no exceptions |

**B2-OBS-REL-002 (Dish Term Synonym → future Batch 4 Dish entity) is explicitly NOT canonicalized here.** Per Founder instruction ("Do not infer future Batch 4 relationships... Batch Independence remains absolute"), it remains a recorded Discovery-stage observation only. It carries no CAN ID and will not be assigned one until Batch 4 exists to canonicalize against.

---

## 5. Canonical Business Rules

| ID | Rule | Exceptions |
|---|---|---|
| B2-CAN-RULE-001 | `is_allergen='Y'` ⟺ `allergen_type` populated | 0 of 191 |
| B2-CAN-RULE-002 | `is_vegan='Y'` ⟹ `diet_type='veg'` | 0 of 191 |

Both promoted directly from B2-OBS-RULE-001/002 — full-file verification in Discovery already proved 100% consistency; no further evidence-gathering was needed at Canonicalization.

---

## 6. Canonical Synonym Register

**Ingredient Alias (B2-CAN-ENT-002):** 167 raw rows → **164 canonical entries** after collapsing the 3 Version/Patch duplicates (§7 Merge Register). Canonical form = source form for all non-duplicate rows; no transformation needed beyond the 3 collapses.

**Dish Term Synonym (B2-CAN-ENT-003):** 121 raw rows → **114 canonical synonym entries** (121 minus the 7 disambiguation-marker rows excluded to §8). 0 duplicates found among the remaining 114 — no merge needed.

---

## 7. Canonical Merge Register

| Merge ID | Members | Canonical Result | Reasoning |
|---|---|---|---|
| B2-MERGE-001 | `sesame_oil`/"til ka tel"/hindi (rows 137, 155) | 1 canonical alias entry (row 155 retained as authoritative — later `is_updated=Y` timestamp) | Classified Version/Patch duplicate (`Batch2_Discovery_Report_v1.1` B2-DQ-001) — proven 100% identical except metadata; merging is the correct action for a data-entry re-insertion, not a business fact |
| B2-MERGE-002 | `spring_onion`/"hara pyaaz"/hindi (rows 57, 163) | 1 canonical entry (row 163 retained) | Same reasoning |
| B2-MERGE-003 | `vinegar`/"sirka"/hindi (rows 143, 161) | 1 canonical entry (row 161 retained) | Same reasoning |

**Only these 3 merges performed. No entity-level or vocabulary-level merge was performed anywhere else in this batch.**

---

## 8. Canonical Exclusion Register

| Exclusion ID | Excluded Content | Reason | Disposition |
|---|---|---|---|
| B2-CAN-EX-001 | 7 `term_synonyms_v2.csv` rows carrying a `(disambiguation)`-suffixed `canonical_name` (Bhaji, Halwa, Biryani, Vada, Chutney, Curry, Dosa) | These are ambiguity-warning records, not name→synonym mappings — a structurally different purpose than the other 114 rows sharing the same file/columns | Excluded from B2-CAN-ENT-003 (Dish Term Synonym). Retained, not discarded — logged here with full content preserved for Mapping stage to determine their eventual home (likely a distinct "Disambiguation Note" concept, a Mapping/Gap Analysis question, not decided here) |

Mirrors Batch 1's `CAN-EX` precedent (excluding non-matching-purpose rows from an entity while preserving them in the record) — same discipline, applied here for the first time in Batch 2.

---

## 9. Canonical Non-Merge Register

| Non-Merge ID | Candidates Considered | Reasoning for Keeping Separate |
|---|---|---|
| B2-NOMERGE-001 | Ingredient Alias (B2-CAN-ENT-002) vs. Dish Term Synonym (B2-CAN-ENT-003) | Different entity class entirely (ingredient names vs. dish names) — required by Founder instruction, also independently evidenced in Discovery (§B2-F-1) |
| B2-NOMERGE-002 | Alias Language (B2-CAN-VOC-005) vs. Synonym Language (B2-CAN-VOC-006) | Materially different value domains (7 vs. 20 values, partial overlap only) — same "structural similarity ≠ same scope" principle applied at the vocabulary level |
| B2-NOMERGE-003 | The 4 Language-duplicate alias pairs (baby_corn, broccoli, mozzarella, noodles — english vs. hindi tag) | Each language tag is a distinct, meaningful usage fact, not administrative noise — unlike the 3 Version/Patch duplicates, there is no evidence these are the same record entered twice |

---

## 10. Canonical Attribute Matrix

| Entity | Attributes | Source Columns | Transformation Required |
|---|---|---|---|
| Ingredient | 15 | 15 | None — direct passthrough |
| Ingredient Alias | 7 (6 after merge collapse removes 3 duplicate rows, not columns) | 7 | None — 3 row-level merges only, no column change |
| Dish Term Synonym | 8 | 8 | None on remaining 114 rows; 7 rows excluded (§8), not transformed |

---

## 11. Canonical Completeness Metrics

| Entity | Column Completeness | Row Retention |
|---|---|---|
| Ingredient | 100% on all business columns; `last_update_date` 0% populated (100% null — informational, not a defect) | 191/191 (100%) |
| Ingredient Alias | 100% on business columns | 164/167 canonical rows (98.2% — 3 collapsed via merge, 0% data loss, only redundancy removed) |
| Dish Term Synonym | 100% on business columns | 114/121 canonical rows (94.2% — 7 excluded to a separate register, 0% data loss, fully retained under B2-CAN-EX-001) |

---

## 12. Canonical Provenance Summary

Every canonical ID in this package traces to exactly one Discovery-stage `B2-OBS-*` ID, which traces to exactly one source file and column, per Batch 1's provenance discipline (`Batch1_Canonicalization_Package_v1.1` §Provenance, referenced not repeated). No canonical value in this batch was inferred, assumed, or introduced without a direct Discovery-stage citation.

---

## OBS → CAN Lineage

```
B2-OBS-ENT-001 (Ingredient)          → B2-CAN-ENT-001
B2-OBS-ENT-002 (Ingredient Alias)    → B2-CAN-ENT-002 (167 → 164 rows, 3 merges)
B2-OBS-ENT-003 (Dish Term Synonym)   → B2-CAN-ENT-003 (121 → 114 rows, 7 excluded to B2-CAN-EX-001)
B2-OBS-REL-001                       → B2-CAN-REL-001
B2-OBS-REL-002 (cross-batch)         → NOT canonicalized — remains an observation, awaits Batch 4
B2-OBS-VOC-001…005a/005b             → B2-CAN-VOC-001…006 (005a→005, 005b→006, kept separate)
B2-OBS-RULE-001/002                  → B2-CAN-RULE-001/002 (unchanged, 0 exceptions)
```

---

## 13. Confidence

**High (100%) across every canonical entity, attribute, vocabulary, relationship, and rule in this batch.** Unlike Batch 1 (which required resolving conflicting evidence across 5 cross-referenced sheets), Batch 2's three flat files needed no cross-sheet reconciliation — the only judgment calls were the 7 duplicate classifications (Discovery) and the 1 exclusion decision (§8), both fully evidence-backed with 0 residual ambiguity.

---

## Executive Summary

Batch 2 canonicalizes cleanly: 3 independent entity families (Ingredient, Ingredient Alias, Dish Term Synonym) confirmed and kept separate per Founder instruction; 3 duplicate rows merged (Version/Patch category only); 7 rows excluded to a separate register (disambiguation-warning content, not lost); 1 relationship canonicalized at 100% confidence; 1 cross-batch relationship correctly deferred to Batch 4. No merge, inference, or architecture assumption was made beyond what full-file evidence directly supports.

---

## Regression Review

- ✅ No Batch 1 document reopened
- ✅ No architecture, schema, RE, or API touched
- ✅ Batch Independence maintained — zero Batch 4 inference
- ✅ Duplicates classified, not silently removed (3 merges are evidence-backed exceptions, explicitly logged, not deletions)
- ✅ No governance rule rewritten — only Batch 1's frozen methodology applied

---

## Founder Approval Gate

**Batch 2 Canonicalization is complete. Mapping has NOT begun. Gap Analysis has NOT begun. Architecture Confirmation and Governance Evaluation have NOT been created — not yet required by any new evidence.**

Founder sign-off: _______________________ Date: ___________
