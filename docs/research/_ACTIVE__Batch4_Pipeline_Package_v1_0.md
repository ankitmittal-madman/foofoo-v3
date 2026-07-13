# [ACTIVE]_Batch4_Pipeline_Package_v1.0

**Phase 3.5 — Batch 4 (Core Integration Batch) — Stages 1–5**
**Asset:** `dishes.xlsx`, sheet `dishes_810` (810 rows, 35 columns). **`Sheet1` excluded per standing Founder directive — not read at any point in this analysis.**
**Date:** 2026-07-02 · **Status:** Draft — Ready for Founder Review

---

# STAGE 1 — DISCOVERY

## Source Inventory
810 rows × 35 columns, fully read via direct computation — no sampling. 0 nulls on 29 of 35 columns; `Alternate Names` (615 null), `Notes` (754 null), `Last Update Date` (707 null) are the only sparse columns, all informational, not defects.

## Entities Observed
| ID | Entity | Key | Rows | Confidence |
|---|---|---|---|---|
| B4-OBS-ENT-001 | Dish | `Dish Name` | 810 (0 duplicates — confirmed independently by the sheet's own `Dupli` formula column, all 810 evaluate to 1) | High (100%) |

## Relationships Observed (all checked by full-file cross-reference against the relevant frozen canonical set)

| ID | Relationship | Result | Confidence |
|---|---|---|---|
| B4-OBS-REL-001 | Dish → Cuisine (`Cuisines` column, single-value despite the plural name) | **100% clean — 0 orphans** against `cuisines_v4.name` (57 of 65 canonical cuisines actually used) | High |
| B4-OBS-REL-002 | Dish → Ingredient (comma-separated `Ingredients` tokens) | 169 distinct tokens used; **165 match `ingredients_v5.name` (97.6%); 4 orphans:** `basmati_rice`, `coriander_seeds`, `cumin_powder`, `mixed_vegetables` | High |
| B4-OBS-REL-003 | Dish → Tag, across 11 of Batch 3's 12 categories (all but `allergen`, which is ingredient-driven, consistent with that design) | 10 of 11 categories 100% clean. **`Texture` has 3 orphans: `juicy`, `brothy`, `spongy`** — not present anywhere in `tags_v4.csv`'s 12-value texture set | High |
| B4-OBS-REL-004 | Dish Name ↔ Batch 2's `term_synonyms_v2.canonical_name` | **79 of 93** canonical dish-synonym entries match a `Dish Name` here (case-insensitive) — this is the concrete evidence CBD-001 was raised on, now directly confirmed | High |
| B4-OBS-REL-005 | Dish's own `Alternate Names` column vs. the same 79-dish overlap above | 62 of the 79 matched dishes have **both** mechanisms populated. Spot-check (`Butter Chicken`): Batch 2 records `synonym="Murgh Makhani", language=hindi`; Batch 4 records `Alternate Names="murgh makhani"` — **the two sources agree, not conflict**, in the case checked | Medium-High (one full spot-check confirmed agreement; not exhaustively verified across all 62) |

## Vocabularies / Value Ranges Observed
| ID | Finding |
|---|---|
| B4-OBS-VOC-001 | `Difficulty`: easy/medium/hard (3 values) |
| B4-OBS-VOC-002 | `tier_1` (Food DNA tier): only `tier_1`/`tier_2` present (487/323) — **no `tier_3` dish exists in this batch**, an observation, not a defect |
| B4-OBS-VOC-003 | `Source`: `ai_generated` (807), `manual` (3) |
| B4-OBS-VOC-004 | `Spice Level` 1–4, `Sweetness` 0–3, `Heaviness` 1–3, `Calories` 30–800 — all within plausible ranges, no outliers flagged |

## Business Rules Observed
| ID | Rule | Exceptions |
|---|---|---|
| B4-OBS-RULE-001 | `Prep Mins + Cooks Mins = Total Mins` | **0 of 810** |
| B4-OBS-RULE-002 | `Dish Name` uniqueness | 0 of 810 |

## Data Quality Findings
| ID | Finding | Detail | Severity |
|---|---|---|---|
| B4-DQ-001 | Two distinct patch events | `2026-05-12` (91 rows) — new, Batch-4-specific, larger event; `2026-05-20` (12 rows) — matches the cross-file event already seen in Batch 2/3, corroborating evidence of a shared multi-file upload on that date | Informational |
| B4-DQ-002 | 33 rows carry `"Validation review: <field> changed"` notes | Documents that a QA pass already touched these specific fields (heaviness ×18, weather_affinity ×8, spice_level ×2, texture/mouthfeel/richness ×1 each, 2 combined) | Informational — provenance, not defect |
| B4-DQ-003 | **8 rows carry `"COMBO: model as dish_combo during Supabase import"`** | `Nahari Kulcha`, `Appam with Stew`, `Kombdi Vade (Malvani)`, `Fafda Jalebi`, `Dal Baati`, `Poha Jalebi (Indori)`, `Sheermal with Nihari`, `Aloo Puri` — explicit source-provided instruction that these are not standalone dishes for `public.dishes` but should route to `public.dish_combos`/`dish_combo_items` instead | **High — this is new evidence pointing forward to Batch 5, see CBD-004 below** |
| B4-DQ-004 | 4 orphan `Ingredients` tokens (B4-OBS-REL-002) | Batch 4's own data references ingredients Batch 2's frozen canonical set doesn't contain | Medium — a genuine cross-batch data disagreement, not an architecture gap (see Gap Analysis) |
| B4-DQ-005 | 3 orphan `Texture` values (B4-OBS-REL-003) | Same pattern for Batch 3's Tag vocabulary | Medium |

## Cross-Batch Evidence Check (Batch 5 assets, read-only reference, per Special Integration Rule — strengthening, not resolving)
`dish_combos_v2_20260520.csv`'s 35 combo names were checked against the 8 COMBO-flagged dishes above: **0 exact name matches**, but clear conceptual overlap by inspection (`Dal Baati` ↔ `Dal Baati Churma`; `Poha Jalebi (Indori)` ↔ `Poha Jalebi`). This is real but inexact evidence — recorded as-is, not forced into a match.

---

# STAGE 2 — CANONICALIZATION

## Canonical Entity Dictionary
| ID | Entity | Rows | Confidence |
|---|---|---|---|
| B4-CAN-ENT-001 | Dish (standalone) | 802 (810 minus 8 excluded) | High |
| B4-CAN-EX-001 | Dish (combo-candidate, excluded) | 8 | High — same exclusion discipline as Batch 2's disambiguation-row handling: distinct structural purpose, not discarded |

**0 merges required** — 0 duplicate keys.

## Canonical Relationship Dictionary
B4-CAN-REL-001 (Dish→Cuisine), B4-CAN-REL-002 (Dish→Ingredient), B4-CAN-REL-003 (Dish→Tag, 11 categories) — all canonicalized as observed; orphan counts (§ above) carried forward to Mapping/Gap Analysis, not silently dropped or force-matched.

## Canonical Business Rules
B4-CAN-RULE-001, B4-CAN-RULE-002 — promoted directly, 0 exceptions.

## Confidence
High (100%) on structure; the 4+3 orphan values and the 8 excluded rows are the only non-trivial items, all fully evidenced.

---

# STAGE 3 — MAPPING

## Baseline Confirmation
Full `public.dishes` DDL read (`_ACTIVE__008_content_core1_1.sql`, 17 real columns + 3 audit columns). Confirmed: `diet_type`, `is_jain`, `allergen_flags`, `genome_vector`, `popularity_score`, `acceptance_rate_7d/30d` are explicitly **DERIVED-STORED** (trigger/CRON-only writes, with a `REVOKE UPDATE` enforcing this) — these are correctly **not** seed-mapping targets, by the architecture's own design, not an oversight. `dish_ingredients` and `dish_tags` junction tables confirmed as the correct destinations for Ingredients and the 11 tag-category columns respectively.

## Attribute Mapping Matrix (abbreviated to non-trivial results — trivial direct matches noted, not tabulated at length)

**Mapped, Direct:** `Dish Name→name`, `Short Description→description`, `Meal Types→meal_occasion` (comma-split to array), `Is Active→is_active`, `Difficulty→difficulty` (deterministic value transform: easy→beginner, medium→intermediate, hard→advanced).

**Mapped, via junction, partially blocked:** Ingredients → `dish_ingredients` (blocked for the specific dishes touching the 4 orphan tokens only); the 11 tag-category columns → `dish_tags` (blocked project-wide pending Batch 3's `public.tags` resolution, not a new architecture gap).

**Not Applicable, by design:** `diet_type`, `is_jain`, `allergen_flags`, `genome_vector`, `popularity_score`, `acceptance_rate_7d/30d` (derived/CRON), `Source`/`Notes`/`Is Updated`/`Last Update Date`/`Is Review`/`Dupli`/`#` (annotation/computational).

**Mapping Issues (13 raised):**

| MAP ID | Attribute(s) | Issue | Confidence |
|---|---|---|---|
| B4-MI-001 | `Cuisines` | **No column, junction, or table anywhere on `public.dishes` for cuisine at all** — strengthens B3-RES-001/002 with concrete, 810-row-scale evidence; not an independent new gap | High |
| B4-MI-002 | `Alternate Names` | Cardinality mismatch — target has exactly 2 fixed slots (`name_hindi`, `name_regional`); source is an unbounded comma list; also overlaps CBD-001 | High |
| B4-MI-003 | `Spice Level`, `Sweetness`, `Heaviness` | No destination columns | High |
| B4-MI-004 | `Prep Mins`, `Cooks Mins`, `Total Mins` | Target has one `cook_time_minutes` column; which source field it should hold is not stated anywhere, and `Prep`/`Cooks Mins` individually have no destination regardless | Medium |
| B4-MI-005 | `Calories` | No destination column | High |
| B4-MI-006 | `Serving Size` | No destination column | High |
| B4-MI-007 | `tier_1` | No destination column on `public.dishes` | High |
| B4-MI-008 | (target) `is_indian_only` | No source column; a plausible derivation from `Cuisines`/cuisine-group membership exists but is not stated as a rule anywhere | Medium |
| B4-MI-009 | (target) `photo_url`, `photo_blurhash` | Source has `image_folder` (a folder path), not a URL — construction/transformation logic is undefined | Medium |
| B4-MI-010 | Ingredients (4 orphan tokens) | `basmati_rice`, `coriander_seeds`, `cumin_powder`, `mixed_vegetables` would fail the `dish_ingredients.ingredient_id` FK | High |
| B4-MI-011 | Texture (3 orphan values) | `juicy`, `brothy`, `spongy` would fail the `dish_tags`/`public.tags.tag_name` lookup | High |
| B4-MI-012 | All 11 tag-category columns | `dish_tags` population is blocked project-wide until Batch 3's `public.tags` uniqueness conflict and missing `vector_position` values are resolved (B3-RES-003/004) — inherited, not independent | High |
| B4-MI-013 | The 8 `B4-CAN-EX-001` rows | No established column-level rule for decomposing a flat dish row into a `dish_combos` + `dish_combo_items` structure | Medium |

## Gap Readiness Summary
All 13 issues evidence-complete. Ready for Gap Analysis.

---

# STAGE 4 — GAP ANALYSIS

## Gap Classification Matrix

| Gap ID | MAP ID | Classification | Why |
|---|---|---|---|
| B4-GAP-001 | B4-MI-001 | **C1** | No structure exists at all — same class as B3-GAP-001/002, confirmed at larger scale, not independent |
| B4-GAP-002 | B4-MI-002 | **C1** | Structural cardinality limit (2 slots) genuinely cannot hold an unbounded list — new finding, only visible once real multi-synonym dish data existed |
| B4-GAP-003 | B4-MI-003 | **C1** | No columns exist |
| B4-GAP-004 | B4-MI-004 | **C2** | The core question ("which of 3 time fields does `cook_time_minutes` mean?") is a business/semantic interpretation, not a missing structure — the column exists |
| B4-GAP-005 | B4-MI-005 | **C1** | No column exists |
| B4-GAP-006 | B4-MI-006 | **C1** | No column exists |
| B4-GAP-007 | B4-MI-007 | **C1** | No column exists |
| B4-GAP-008 | B4-MI-008 | **C2** | Column exists; the derivation rule is the open question |
| B4-GAP-009 | B4-MI-009 | **C2** | Columns exist; the transformation convention is the open question |
| B4-GAP-010 | B4-MI-010 | **C3** | The architecture (`dish_ingredients` FK to `public.ingredients`) works correctly — the conflict is between two independently-authored source files (Batch 2's ingredient list vs. Batch 4's dish data), a research conflict, not an architecture gap |
| B4-GAP-011 | B4-MI-011 | **C3** | Same reasoning — `public.tags`/`dish_tags` structure is sound; the source data disagrees across batches |
| B4-GAP-012 | B4-MI-012 | **Inherits B3-GAP-003 (C3) / B3-GAP-004 (B)** | Not an independent gap — cannot be classified fresh without duplicating Batch 3's already-frozen analysis |
| B4-GAP-013 | B4-MI-013 | **C2** | `dish_combos`/`dish_combo_items` already exist structurally — the open question is how to decompose one flat row into that structure, a mapping/business-logic decision |

**0 Category A. 1 Category B (inherited, not fresh). 5 Category C1. 5 Category C2. 2 Category C3.**

## Impact Summary (abbreviated)

| Gap ID | Business Impact | Seed Impact | Cross-Batch Impact |
|---|---|---|---|
| B4-GAP-001 | No dish can show its cuisine anywhere | All 810 rows | Confirms B3-RES-001/002 |
| B4-GAP-002 | Multi-language dish names beyond 2 slots are lossy | Up to 17 dishes with 2+ alternate names (comma-count check not exhaustively re-verified here) | Confirms/extends CBD-001 |
| B4-GAP-003 | No spice/sweetness/heaviness signal available to any feature | All 810 rows | None |
| B4-GAP-004 | Cook-time display may be wrong if the assumed field is incorrect | All 810 rows | None |
| B4-GAP-005 | No calorie display | All 810 rows | None |
| B4-GAP-006 | No serving-size display | All 810 rows | None |
| B4-GAP-007 | Food DNA tier not persisted at dish level despite being computed | All 810 rows | None |
| B4-GAP-008 | Filtering "Indian-only" dishes not possible without this | All 810 rows | None |
| B4-GAP-009 | No dish photos displayable without a defined URL scheme | All 810 rows | None |
| B4-GAP-010 | 4 ingredient references would fail to load | Affects the specific dishes using them (exact dish count not separately tallied) | **New evidence against Batch 2's frozen Ingredient list — does not reopen it** |
| B4-GAP-011 | 3 texture tag references would fail to load | Affects the specific dishes using them | **New evidence against Batch 3's frozen Tag vocabulary — does not reopen it** |
| B4-GAP-012 | All dish-level Food DNA tagging blocked | All 810 rows, all 11 tag categories | Direct dependency on B3-RES-003/004 |
| B4-GAP-013 | 8 dishes would be mis-modeled as standalone if not routed to combos | 8 rows | **New — CBD-004, points to Batch 5** |

## Regression Review (Gap Analysis)
No AGR/SER/DCR recommended. No schema change proposed. No Batch 1/2/3 frozen document reopened — B4-GAP-010/011/012 explicitly reference but do not modify Batch 2/3's frozen Canonicalization or Gap Analysis packages.

## Resolution Readiness Summary
13 of 13 ready. B4-GAP-001 and B4-GAP-012 are not independent — they should be tracked jointly with B3-RES-001/002 and B3-RES-003/004 respectively, not as new parallel decisions.

---

# STAGE 5 — RESOLUTION

## Resolution Register

| RES ID | GAP ID | Path | Order | Owner |
|---|---|---|---|---|
| B4-RES-001 | B4-GAP-001 | Founder Decision — **not independent, adds evidentiary weight to B3-RES-001/002** | Immediate | Founder→Arch |
| B4-RES-002 | B4-GAP-002 | Founder Decision (Future SER Candidate) — tied to CBD-001 | Future/Parallel | Founder→Arch |
| B4-RES-003 | B4-GAP-003 | Founder Decision (Future SER Candidate) | Parallel | Founder→Arch |
| B4-RES-004 | B4-GAP-004 | Founder Decision (business/semantic call — which time field `cook_time_minutes` means) | Parallel | Founder/Product |
| B4-RES-005 | B4-GAP-005 | Founder Decision (Future SER Candidate) | Parallel | Founder→Arch |
| B4-RES-006 | B4-GAP-006 | Founder Decision (Future SER Candidate) | Parallel | Founder→Arch |
| B4-RES-007 | B4-GAP-007 | Founder Decision (Future SER Candidate) | Parallel | Founder→Arch |
| B4-RES-008 | B4-GAP-008 | Founder Decision (derivation rule for `is_indian_only`) | Parallel | Founder/Product |
| B4-RES-009 | B4-GAP-009 | Founder Decision (photo URL/storage convention) | Parallel | Founder/Engineering |
| B4-RES-010 | B4-GAP-010 | Founder Decision (research conflict — whether to extend Batch 2's ingredient list or correct Batch 4's data; does not reopen Batch 2) | Blocked pending decision | Founder→Arch |
| B4-RES-011 | B4-GAP-011 | Founder Decision (same pattern as B4-RES-010, for Texture; does not reopen Batch 3) | Blocked pending decision | Founder→Arch |
| B4-RES-012 | B4-GAP-012 | **Inherits B3-RES-003/004 entirely — not independently resolved** | Blocked on Batch 3 | Arch |
| B4-RES-013 | B4-GAP-013 | Founder Decision (combo-decomposition rule) — grounds **CBD-004** | Future Batch (Batch 5) | Founder→Arch |

## Cross-Batch Integration Summary

| CBD ID | Status Before This Session | New Evidence This Session | Status Now |
|---|---|---|---|
| CBD-001 (Batch 2 Synonyms → Batch 4) | Open, evidence-only (no Batch 4 existed yet) | **Substantially strengthened**: 79/93 canonical dish names confirmed present in Batch 4; 62 of those also independently corroborated by Batch 4's own `Alternate Names` field, with 1 full spot-check showing agreement, not conflict | **Open — strengthened, not closed** (per Special Integration Rule; a real decision on whether/how to merge the two mechanisms is still Resolution/Founder's to make) |
| CBD-002 (Batch 3 Cuisine → Batch 4) | Open, evidence-only | **Fully confirmed**: 100% of 810 dishes' cuisine values match Batch 3's canonical list, 0 orphans; B4-MI-001/GAP-001/RES-001 show the practical cost of leaving this unresolved | **Open — confirmed, higher urgency** |
| CBD-003 (Batch 3 Tags → Batch 4) | Open, evidence-only | **Confirmed and refined**: 10 of 11 tag categories are 100% clean; only Texture has orphans (3 values) — this is more precise than the original CBD-003, which didn't know which category(ies) would actually conflict | **Open — confirmed and narrowed** |
| **CBD-004 (NEW) — Batch 4 Dishes → Batch 5 Dish Combos** | Did not exist | 8 dishes explicitly source-annotated `"COMBO: model as dish_combo during Supabase import"`; checked against Batch 5's `dish_combos_v2.csv` — 0 exact name matches, but clear conceptual overlap on at least 2 (`Dal Baati`↔`Dal Baati Churma`, `Poha Jalebi (Indori)`↔`Poha Jalebi`) | **New — Open** |

**No CBD was closed. All four remain open, three strengthened with new evidence, one newly raised — exactly per the Special Integration Rule.**

## Regression Review (full Batch 4 pipeline)
- ✅ No Batch 1/2/3 frozen document modified — B4-GAP-010/011 and CBD-001/002/003 reference but do not reopen them
- ✅ No architecture, schema, RE, or API document touched
- ✅ No AGR, SER, or DCR created
- ✅ No schema change, migration, or SQL proposed
- ✅ No downstream impact invented beyond what DDL/data directly evidences
- ✅ `Sheet1` never read
- ✅ No stop condition triggered — B4-GAP-010/011 (source-data conflicts) and B4-MI-001 (no-cuisine-column) were evidence-complete and classifiable without an execution halt, consistent with how equally-serious findings were handled in Batches 1–3

---

## Batch 4 Closure Readiness Summary

| Check | Status |
|---|---|
| All 5 stages complete | ✅ |
| 13 of 13 gaps resolved to a path | ✅ |
| Cross-Batch Dependencies logged/strengthened | ✅ 3 strengthened, 1 new |
| Any gap requiring further evidence | ❌ None |
| **Batch 4 ready to close** | Not yet declared — awaiting Founder approval; no blocker identified |

---

## Founder Approval Gate

**Batch 4 pipeline (Discovery through Resolution) is complete. Batch Closure has NOT begun. Batch 5 has NOT begun. No AGR, SER, or DCR has been created.**

Founder sign-off: _______________________ Date: ___________
