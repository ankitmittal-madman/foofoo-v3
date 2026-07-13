# [ACTIVE]_Batch3_Pipeline_Package_v1.0

**Phase 3.5 — Batch 3 — Stages 1–5: Discovery → Canonicalization → Mapping → Gap Analysis → Resolution**
**Assets (frozen roadmap):** `cuisine_groups_v4.csv`, `cuisines_v4.csv`, `tags_v4.csv`
**Methodology:** Identical to Batch 1/Batch 2 (frozen) — not re-explained. Executed continuously per Founder's High-Velocity execution model; no stop condition (architecture/schema/business-rule/lineage contradiction, seed correctness risk, data loss risk, unisolable cross-batch conflict) was triggered — findings below are raised and carried forward, not blockers.
**Date:** 2026-07-02
**Status:** Draft — Ready for Founder Review

---

# STAGE 1 — DISCOVERY

## Source Inventory

| File | Rows | Columns | Confidence |
|---|---|---|---|
| `cuisine_groups_v4.csv` | 22 | 8 | High (100%) |
| `cuisines_v4.csv` | 65 | 12 | High (100%) |
| `tags_v4.csv` | 111 | 9 | High (100%) |

**198 rows across 3 files, fully read — no sampling.**

## Entities Observed

| ID | Entity | Key | Rows |
|---|---|---|---|
| B3-OBS-ENT-001 | Cuisine Group | `name` | 22 (0 duplicates) |
| B3-OBS-ENT-002 | Cuisine | `name` | 65 (0 duplicates) |
| B3-OBS-ENT-003 | Tag | `(category, value)` | 111 (0 duplicate pairs) |

## Relationships Observed

| ID | Relationship | Evidence | Confidence |
|---|---|---|---|
| B3-OBS-REL-001 | Cuisine → Cuisine Group | `cuisines.cuisine_group` — 65/65 match `cuisine_groups.name`, 0 orphans | High (100%) |
| B3-OBS-REL-002 | Cuisine → Cuisine (self, parent hierarchy) | 12 of 65 rows carry `parent_cuisine`; 12/12 match another `cuisines.name` row, 0 orphans, confirmed single-level (no parent is itself a child) | High (100%) |
| B3-OBS-REL-003 | Cuisine.`state_origin` → `re_states` (Batch 1 frozen architecture) | **Weak/partial only** — `state_origin` has 63 unique values including non-Indian entities (China, Bhutan, Burma, Europe (generic)) that cannot match `re_states`' 36 India-only state codes even in principle | Low — recorded as a real but unresolvable-as-is relationship attempt |

## Vocabularies Observed

| ID | Vocabulary | Values |
|---|---|---|
| B3-OBS-VOC-001 | Cuisine Tier | 3 (tier_1: 17, tier_2: 26, tier_3: 22) |
| B3-OBS-VOC-002 | Tag Category | 12 (dish_category, cooking_method, texture, aroma_profile, allergen, mouthfeel, primary_taste, richness, serving_temp, meal_type, fermentation, weather_affinity) |
| B3-OBS-VOC-003 | Tag Tier | 3 (tier_1: 35, tier_2: 46, tier_3: 30) |

**Finding B3-F-1:** Cuisine Tier and Tag Tier share the same value shape (`tier_1/2/3`) but are different concepts (cuisine prominence vs. Food DNA scoring tier, per `public.tags.tier`'s established purpose in frozen architecture) — kept as separate vocabularies, same non-merge discipline as Batch 2's language vocabularies.

## Business Rules Observed

| ID | Rule | Exceptions |
|---|---|---|
| B3-OBS-RULE-001 | Every `cuisines.cuisine_group` value exists in `cuisine_groups.name` | 0 of 65 |
| B3-OBS-RULE-002 | Every `cuisines.parent_cuisine` value (where populated) exists in `cuisines.name`, single-level only | 0 of 12 |

## Data Quality Findings

| ID | Finding | Detail | Severity |
|---|---|---|---|
| B3-DQ-001 | 2 cross-category value collisions in `tags_v4.csv` | `"light"` appears under both `richness` and `fermentation`; `"none"` appears under both `fermentation` and `allergen`. **Not** a duplicate row (`(category, value)` pairs are 100% unique) — this is a distinct finding type: a **Target Constraint Conflict**, not a source-side duplicate, because the frozen target schema (`public.tags.tag_name`) requires **global** uniqueness across all categories, which the source data's per-category value choices don't respect | **High — this is the batch's headline finding, carried through Mapping and Gap Analysis below** |
| B3-DQ-002 | 22 of 65 cuisines marked `is_active='N'` | Real business data (niche/regional Indian cuisines plus several non-Indian cuisines currently deactivated: himachali, naga, manipuri, thai, japanese, korean, etc.) — not an administrative artifact | Informational |
| B3-DQ-003 | 4 cuisines (`bhutanese`, `burmese`, `mexican`, `vietnamese`) show `is_updated='Y'`, `last_update_date='20-05-2026'` | Same patch-event date pattern already observed in Batch 2 (`ingredient_aliases_v2.csv`) — corroborating, not new, evidence of a shared multi-file upload event on that date | Informational |

## Cross-Batch Evidence (checked directly against `dishes.xlsx`, the real `dishes_810` data sheet — the Founder-excluded `Sheet1` was not consulted)

| ID | Finding | Evidence |
|---|---|---|
| B3-XREF-001 | `dishes_810`'s header row includes a `Cuisines` column; row 2's sample value is `"punjabi"` — directly matching a `cuisines_v4.name` value | Direct read, `dishes.xlsx`, sheet `dishes_810`, header + row 2 |
| B3-XREF-002 | `dishes_810`'s header also includes `Meal Types`, `Dish Category`, `Cooking Method`, `Primary Taste`, `Texture`, `Richness`, `Mouthfeel`, `Aroma Profile`, `Fermentation`, `Serving Temp`, `Weather Affinity` — 11 of Batch 3's 12 Tag categories (only `allergen` absent, consistent with allergen being ingredient-driven) | Same source |

**These are the basis for CBD-002 and CBD-003 in the Resolution section below — genuine, directly-observed cross-batch dependencies, not inferred.**

---

# STAGE 2 — CANONICALIZATION

## Canonical Entity Dictionary

| ID | Entity | Confidence |
|---|---|---|
| B3-CAN-ENT-001 | Cuisine Group | High (100%) |
| B3-CAN-ENT-002 | Cuisine | High (100%) |
| B3-CAN-ENT-003 | Tag | High (100%) |

**0 merges required — 0 duplicate keys found within any entity.** (B3-DQ-001's 2 collisions are cross-category, not same-key — they don't collapse to a single canonical Tag row; both remain distinct canonical tags.)

## Canonical Relationship Dictionary

| ID | Relationship | Status |
|---|---|---|
| B3-CAN-REL-001 | Cuisine → Cuisine Group | Canonicalized, 100% |
| B3-CAN-REL-002 | Cuisine → Cuisine (self) | Canonicalized, 100% |
| — | Cuisine → `re_states` | **Not canonicalized** — insufficient scope match (B3-OBS-REL-003); forwarded to Mapping as-is, not forced |

## Canonical Vocabulary Dictionary

B3-CAN-VOC-001 (Cuisine Tier), B3-CAN-VOC-002 (Tag Category), B3-CAN-VOC-003 (Tag Tier) — direct promotions, no transformation.

## Canonical Non-Merge Register

| ID | Candidates | Reasoning |
|---|---|---|
| B3-NOMERGE-001 | Cuisine Tier vs. Tag Tier | Same value shape, different concept — see B3-F-1 |
| B3-NOMERGE-002 | The 2 cross-category tag value collisions (`"light"`, `"none"`) | Each retains its own distinct canonical Tag identity (different `category`) — not merged into one tag despite the literal string match |

## Canonical Business Rules

B3-CAN-RULE-001, B3-CAN-RULE-002 — promoted directly, 0 exceptions.

## Confidence

High (100%) throughout — no cross-sheet ambiguity, no exclusions needed this batch (unlike Batch 2's disambiguation-row exclusion).

---

# STAGE 3 — MAPPING

## Baseline Confirmation

Full-text search of every frozen `.sql` file and `DOC-P3-04` for "cuisine" (as a table/entity, not the existing free-text `cuisine_family` column) and "cuisine_group" returned **zero candidate tables**. `public.tags` **does exist** and is the direct target for B3-CAN-ENT-003.

## Entity Mapping Matrix

| CAN ID | Entity | Destination | Status |
|---|---|---|---|
| B3-CAN-ENT-001 | Cuisine Group | *(none)* | **Mapping Issue — B3-MI-001** |
| B3-CAN-ENT-002 | Cuisine | *(none)* | **Mapping Issue — B3-MI-002** |
| B3-CAN-ENT-003 | Tag | `public.tags` | Mapped — partial (see attribute matrix) |

## Attribute Mapping Matrix (Tag → `public.tags`)

| Attribute | Destination | Mapping Type | Status |
|---|---|---|---|
| `category` | `dimension` | Direct passthrough (target unconstrained text) | Mapped |
| `tier` (`tier_1/2/3`) | `tier` (smallint, CHECK 1/2/3) | Direct, deterministic value transform | Mapped |
| `is_user_facing` (Y/N) | `is_user_facing` (boolean) | Direct, deterministic value transform | Mapped |
| `value` | `tag_name` (`text NOT NULL UNIQUE` — **global** uniqueness) | Direct in 109 of 111 cases; **conflicts in 2** | **Mapping Issue — B3-MI-003** |
| — | `vector_position` (`integer NOT NULL UNIQUE`) | **No source column provides this at all** | **Mapping Issue — B3-MI-004** |
| `display_value`, `description` | *(none)* | No matching column | **Mapping Issue — B3-MI-005** |
| `is_updated`, `last_update_date`, `is_review` | *(none)* | Annotation-only | Not Applicable |

## Relationship Mapping Matrix

| CAN ID | Status |
|---|---|
| B3-CAN-REL-001, B3-CAN-REL-002 | **Mapping Issue — inherit B3-MI-002** (Cuisine has no destination table for either relationship to attach to) |
| Cuisine → `re_states` (unresolved) | **Mapping Issue — B3-MI-006** (scope mismatch: even a hypothetical future Cuisine table couldn't cleanly FK 63 origin values, many non-Indian, to a 36-row India-only reference table) |

## Business Rule Mapping Matrix

| CAN ID | Status |
|---|---|
| B3-CAN-RULE-001, B3-CAN-RULE-002 | Both inherit B3-MI-002 — cannot be enforced without a Cuisine destination table |

## Mapping Issues Register

| MAP ID | Reason | Evidence | Confidence | Owner | Recommended Next Stage |
|---|---|---|---|---|---|
| B3-MI-001 | Cuisine Group has no destination table | Exhaustive negative search, all frozen `.sql` + `DOC-P3-04` | High | Architecture | Gap Analysis |
| B3-MI-002 | Cuisine has no destination table (also blocks both relationships and both business rules) | Same search | High | Architecture | Gap Analysis |
| B3-MI-003 | `tag_name` global uniqueness conflict — 2 value collisions across categories | `_ACTIVE__002_reference_tier0.sql` (`tag_name text NOT NULL UNIQUE`); `tags_v4.csv` full-file check (`"light"`: richness+fermentation; `"none"`: fermentation+allergen) | High | Architecture | Gap Analysis — **this is a data-proven constraint conflict, the most significant single finding in Batch 3** |
| B3-MI-004 | `vector_position` required by target schema, zero source values exist | `_ACTIVE__002_reference_tier0.sql` (`vector_position integer NOT NULL UNIQUE`); `tags_v4.csv` full-file check — no such column anywhere | High | Architecture | Gap Analysis — blocks insertion of all 111 rows, not a partial gap |
| B3-MI-005 | `display_value`, `description` have no destination column | DDL read | High | Architecture | Gap Analysis |
| B3-MI-006 | `state_origin` cannot cleanly FK to `re_states` (scope mismatch, not just absence) | Full value-domain comparison, 63 vs. 36 values, non-overlapping categories (countries vs. Indian states) | High | Architecture | Gap Analysis |

**6 Mapping Issues raised. 0 resolved. 0 schema changes proposed.**

## Gap Readiness Summary (Mapping → Gap Analysis)

All 6 issues are evidence-complete. No blocker prevents proceeding.

---

# STAGE 4 — GAP ANALYSIS

## Gap Classification Matrix

| Gap ID | MAP ID | Classification | Why |
|---|---|---|---|
| B3-GAP-001 | B3-MI-001 | **C1** | No table exists at all for Cuisine Group — architecture does not support the concept |
| B3-GAP-002 | B3-MI-002 | **C1** | Same — no table for Cuisine; both relationships and both business rules inherit this |
| B3-GAP-003 | B3-MI-003 | **C3** | Architecture (the `UNIQUE` constraint) is fully capable of supporting distinct tags — the conflict originates in the **source data**, where two different concepts happen to share a literal string across categories. This is a research/source-data conflict, not an architecture gap or a business-meaning ambiguity — the meaning of each "light"/"none" is already clear in context; they simply collide in a flat namespace |
| B3-GAP-004 | B3-MI-004 | **B** | The destination column (`vector_position`) already exists and is well-defined; what's missing is the actual value assignment for each of 111 tags — data missing/incomplete within a supported structure, matching Category B exactly, same pattern as Batch 2's B2-GAP-006 |
| B3-GAP-005 | B3-MI-005 | **C1** | Structural absence of 2 columns on an existing table — mirrors Batch 2's B2-GAP-004 pattern exactly |
| B3-GAP-006 | B3-MI-006 | **C1** | `re_states` is structurally scoped to India-only codes; it cannot represent "China" or "Bhutan" as currently designed — a genuine architecture-scope gap, not an absence of data within an otherwise-adequate structure |

**0 Category A. 1 Category B. 4 Category C1. 0 Category C2. 1 Category C3.**

## Gap Register (abbreviated — full lineage inherited from Discovery/Canonicalization/Mapping above)

| Gap ID | Business Impact | Technical Impact | Seed Impact | Cross-Batch Impact | Owner | Priority | Confidence | Resolution Readiness |
|---|---|---|---|---|---|---|---|---|
| B3-GAP-001 | Cuisine groupings (North/South/East Indian, etc.) unavailable to any feature | Low (no confirmed RE-DOC consumer today) | 22 rows blocked | **Confirmed** — Batch 4's `dishes_810.Cuisines` column will need a canonical cuisine to reference (B3-XREF-001) | Architecture | High | High | Ready |
| B3-GAP-002 | Cuisine-level detail (65 cuisines, hierarchy, tier, description) unavailable | Low | 65 rows blocked | **Confirmed**, same as B3-GAP-001 | Architecture | High | High | Ready |
| B3-GAP-003 | Two Food DNA tag concepts cannot both be seeded as currently valued without one silently overwriting or rejecting the other at load time | **High** — `RE-DOC-01–05`'s entire genome-vector mechanism depends on `public.tags` loading correctly | 2 of 111 rows in direct conflict | Confirmed — Batch 4's dish-level tag columns (B3-XREF-002) will reference these same tag values | Architecture | **Critical** | High | Ready |
| B3-GAP-004 | Food DNA scoring (which reads `vector_position` per `DOC-P3-04` Principle 6) cannot function for any tag until positions are assigned | High — blocks the genome-vector mechanism entirely, for all 111 tags, until resolved | All 111 rows | Confirmed, same as B3-GAP-003 | Architecture | Critical | High | Ready |
| B3-GAP-005 | No display label or description available for any of 111 tags in any UI | Low | 111 rows partially incomplete | None identified | Architecture | Medium | High | Ready |
| B3-GAP-006 | Non-Indian cuisine origins (12+ cuisines: Chinese, Thai, Japanese, Korean, Mexican, etc.) cannot be geographically anchored | Low | Affects `state_origin` for the non-Indian subset of 65 cuisines | None identified beyond B3-GAP-002 (inherits) | Architecture | Low | High | Ready |

## Impact / Priority / Ownership / Confidence Matrices

| Priority | Gaps |
|---|---|
| Critical | B3-GAP-003, B3-GAP-004 |
| High | B3-GAP-001, B3-GAP-002 |
| Medium | B3-GAP-005 |
| Low | B3-GAP-006 |

All 6 gaps: Owner = Architecture. Confidence = High across all 6 (no Medium/Low confidence items this batch — a first for the project).

## Regression Review (Gap Analysis)

- ✅ Mapping not reopened
- ✅ No AGR/SER/DCR recommended
- ✅ No schema change proposed
- ✅ No "likely AGR"/"probably" language used — every classification states only what the evidence proves

## Resolution Readiness Summary (Gap Analysis → Resolution)

6 of 6 gaps ready. B3-GAP-003 and B3-GAP-004 are the most consequential findings in the project to date — both sit directly on the Food DNA / genome-vector mechanism that `RE-DOC-01–05` depends on, unlike any prior Batch 1 or Batch 2 gap.

---

# STAGE 5 — RESOLUTION

## Resolution Register

| RES ID | GAP ID | Classification | Resolution Path | Resolution Order | Owner | Confidence |
|---|---|---|---|---|---|---|
| B3-RES-001 | B3-GAP-001 | C1 | Founder Decision (Future AGR Candidate) | **Immediate** — see CBD-002 | Founder → Architecture | High |
| B3-RES-002 | B3-GAP-002 | C1 | Founder Decision (Future AGR Candidate) | **Immediate** — see CBD-002 | Founder → Architecture | High |
| B3-RES-003 | B3-GAP-003 | C3 | Founder Decision (Future AGR Candidate — this is a data-proven constraint conflict, the same evidentiary class as Batch 1's GAP-007) | **Immediate** — see CBD-003; blocks correct `public.tags` seeding entirely | Founder → Architecture | High |
| B3-RES-004 | B3-GAP-004 | B | Founder Decision (Documentation Update track — a bit/position-assignment scheme must be proposed for Founder confirmation for all 111 tags before any load) | **Immediate** — see CBD-003 | Founder → Architecture | High |
| B3-RES-005 | B3-GAP-005 | C1 | Founder Decision (Future SER Candidate — matches Batch 2's B2-GAP-004/B2-RES-004 pattern: existing table, missing descriptive columns, non-blocking) | Parallel | Founder → Architecture | High |
| B3-RES-006 | B3-GAP-006 | C1 | Founder Decision (Future SER Candidate — extending `re_states` scope, or an alternative non-blocking representation, is a lower-severity structural question than B3-RES-001/002) | Parallel | Founder → Architecture | High |

**Why B3-RES-003/004 outrank B3-RES-001/002/005/006 despite all being "Immediate" or high-severity:** B3-RES-003 and B3-RES-004 block `public.tags` — the literal table the entire Food DNA / genome-vector scoring mechanism (`RE-DOC-01–05`) depends on — from loading correctly at all. B3-RES-001/002 block a *new* concept (Cuisine) that nothing yet consumes structurally; B3-RES-005/006 are descriptive/scope refinements on top of tables that already work. This ordering follows directly from the Impact Matrix above, not from a new judgment introduced at Resolution.

## Cross-Batch Dependency Register

| CBD ID | Source (Batch 3) | Target | Evidence | Status |
|---|---|---|---|---|
| CBD-002 | B3-GAP-001, B3-GAP-002 (Cuisine Group, Cuisine) | Batch 4 (`dishes.xlsx`) | `dishes_810.Cuisines` column, sample value `"punjabi"` directly matching `cuisines_v4.name` (B3-XREF-001) | **OPEN** |
| CBD-003 | B3-GAP-003, B3-GAP-004 (Tag conflicts, vector_position) | Batch 4 (`dishes.xlsx`) | `dishes_810` header includes 11 of Batch 3's 12 tag categories as dish-level columns (B3-XREF-002) | **OPEN** — higher urgency than CBD-001/002 because Batch 4 cannot seed dish-level tags correctly while `public.tags` itself has an unresolved uniqueness conflict and no `vector_position` values |

**Unlike Batch 2's CBD-001 (where waiting for Batch 4 was the safer order), CBD-002 and CBD-003 point the other way: Batch 3's own gaps should resolve *before* Batch 4 begins, because Batch 4 depends on Batch 3's output, not vice versa. This is stated as a sequencing observation, not a directive — Resolution does not schedule batches.**

## Impact Chain

| RES ID | Canonical Entity | Target Table | Seed Impact | RE Impact | API Impact | UI Impact |
|---|---|---|---|---|---|---|
| B3-RES-001 | B3-CAN-ENT-001 | None | 22 rows blocked | Unknown | Unknown | Unknown |
| B3-RES-002 | B3-CAN-ENT-002 | None | 65 rows blocked | Unknown | Unknown | Unknown |
| B3-RES-003 | B3-CAN-ENT-003 | `public.tags` (exists) | 2 of 111 rows in direct conflict | **Confirmed** — genome-vector mechanism (`DOC-P3-04` Principle 6) | Unknown | Unknown |
| B3-RES-004 | B3-CAN-ENT-003 | `public.tags` (exists) | 111 of 111 rows blocked pending position assignment | **Confirmed** — same mechanism | Unknown | Unknown |
| B3-RES-005 | B3-CAN-ENT-003 | `public.tags` (exists, missing columns) | 111 rows partially incomplete | Unknown | Unknown | Likely, unconfirmed — left Unknown |
| B3-RES-006 | B3-CAN-ENT-002 (inherits) | None | Inherits B3-RES-002 | Unknown | Unknown | Unknown |

## OBS → CAN → MAP → GAP → RES Lineage

```
B3-OBS-ENT-001 → B3-CAN-ENT-001 → B3-MI-001 → B3-GAP-001 → B3-RES-001 (+ CBD-002)
B3-OBS-ENT-002 → B3-CAN-ENT-002 → B3-MI-002 → B3-GAP-002 → B3-RES-002 (+ CBD-002)
B3-OBS-ENT-003 → B3-CAN-ENT-003 → B3-MI-003 → B3-GAP-003 → B3-RES-003 (+ CBD-003)
B3-OBS-ENT-003 →                  B3-MI-004 → B3-GAP-004 → B3-RES-004 (+ CBD-003)
B3-OBS-ENT-003 →                  B3-MI-005 → B3-GAP-005 → B3-RES-005
B3-OBS-REL-003 →                  B3-MI-006 → B3-GAP-006 → B3-RES-006
```

## Resolution Confidence

High across all 6 — every classification-to-path mapping followed directly from precedent already established in Batch 1 (GAP-007's data-proven-conflict handling) and Batch 2 (B2-GAP-004/006's structural patterns). No genuinely novel judgment call this batch.

## Regression Review (full pipeline)

- ✅ No Batch 1 or Batch 2 frozen document touched
- ✅ No architecture, schema, RE, or API document modified
- ✅ No AGR, SER, or DCR created
- ✅ No schema change, migration, or SQL proposed
- ✅ No downstream impact invented — every unconfirmed Impact Chain cell reads "Unknown"
- ✅ Cross-batch evidence (B3-XREF-001/002) came from directly reading `dishes.xlsx`'s real data sheet (`dishes_810`) — the Founder-excluded `Sheet1` was never consulted
- ✅ No stop condition was triggered — B3-GAP-003 (the closest candidate, a genuine schema-adjacent conflict) was evidence-complete and classifiable without requiring an execution halt, consistent with how Batch 1's equally-serious GAP-007 was handled

---

## Resolution Summary

6 of 6 gaps resolved to a path: 3 Founder-Decision/Future-AGR-Candidate (Cuisine Group, Cuisine, and the tag-name conflict), 1 Founder-Decision/Documentation-Update-track (vector_position assignment), 2 Founder-Decision/Future-SER-Candidate (descriptive columns, state_origin scope). 2 new Cross-Batch Dependencies raised (CBD-002, CBD-003), both grounded in direct evidence from `dishes.xlsx`'s real data sheet. This batch's headline finding — the `tag_name` global-uniqueness conflict plus the fully-unpopulated `vector_position` column — sits directly on the project's core Food DNA scoring mechanism, making it the most consequential Gap Analysis outcome since Batch 1's GAP-007.

## Batch 3 Closure Readiness Summary

| Check | Status |
|---|---|
| Discovery, Canonicalization, Mapping, Gap Analysis, Resolution all complete this session | ✅ |
| All 6 gaps carry a resolution path | ✅ |
| Any gap requiring further evidence | ❌ None |
| Cross-Batch Dependencies logged | ✅ CBD-002, CBD-003 |
| **Batch 3 ready to close** | Not yet declared — awaiting Founder approval; no blocker identified |

---

## Founder Approval Gate

**Batch 3 pipeline (Discovery through Resolution) is complete. Batch Closure has NOT begun. No AGR, SER, or DCR has been created.**

Founder sign-off: _______________________ Date: ___________
