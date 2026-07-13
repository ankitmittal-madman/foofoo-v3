# Batch 4 Technical Review & Freeze Recommendation v1.0

**Phase 3.5 — Batch 4 (Core Integration Batch) — Refinement Pass on `Batch4_Pipeline_Package_v1.0`**
**Baseline reconstructed from project files (not chat memory):** `DOC-P3-11 v1.20`, `DOC-P3-12`, `Batch4_Pipeline_Package_v1.0`, `Project_Checkpoint_v1.0`, `Batch1/2/3` frozen packages, all frozen Phase 3 documents.
**Date:** 2026-07-03 · **Status:** Draft — Ready for Founder Review

**Confirmed state (per instruction, not assumed):**

| Item | Status |
|---|---|
| Phase 3 | COMPLETE / APPROVED / FROZEN |
| Batch 1, 2, 3 | COMPLETE / FROZEN |
| Batch 4 | Pipeline complete (`Batch4_Pipeline_Package_v1.0`) — Founder Review pending, closure not declared |
| Batch 5 | NOT STARTED |

No stage of Batch 4 was rerun. No document was regenerated. This pass is a refinement layer only, per instruction.

---

## 1. Batch 4 Technical Review

**Architecture.** `dishes_810` maps to `public.dishes` (17 real + 3 audit columns, `_ACTIVE__008_content_core1_1.sql`). The derived-stored columns (`diet_type`, `is_jain`, `allergen_flags`, `genome_vector`, `popularity_score`, `acceptance_rate_7d/30d`) are correctly excluded from every mapping target — confirmed by the `REVOKE UPDATE` pattern already in frozen DDL. This is good architecture discipline holding under a much larger dataset (810 rows vs. Batch 1–3's 22–198). Cuisine has 0 data-level orphans (100% of 810 dishes match `cuisines_v4`) but **no destination column, table, or junction exists on `public.dishes` for cuisine at all** — this isn't a new finding, it's Batch 4 supplying the largest evidence sample yet for B3-RES-001/002.

**Integration.** `dish_ingredients` and `dish_tags` are the structurally correct junction targets. `dish_ingredients` is blocked only for the rows touching the 4 orphan ingredient tokens — narrow blast radius. `dish_tags` is blocked project-wide, inherited entirely from Batch 3's unresolved `public.tags` conflict (B3-RES-003/004) — Batch 4 did not create this block, it just makes it visible at dish-grain for the first time.

**Seed quality.** Internal consistency is strong: 0 duplicate dish names across 810 rows, `Prep + Cooks = Total` holds with 0 exceptions, all numeric ranges (spice, sweetness, heaviness, calories) are plausible with no outliers. 802 of 810 rows are clean standalone seed candidates; 8 are explicitly source-flagged as combo candidates and correctly excluded from the standalone canonical set (`B4-CAN-EX-001`) rather than force-fit.

**Future implementation.** Six attributes (`Spice Level`, `Sweetness`, `Heaviness`, `Calories`, `Serving Size`, `tier_1`) have no destination column anywhere in frozen architecture — a cluster of SER candidates, not urgent individually but collectively material to Food DNA completeness at launch. Photo URL construction is undefined (`image_folder` is a path, not a URL — see §6). Cook-time mapping is a genuine semantic ambiguity: three source fields (`Prep Mins`, `Cooks Mins`, `Total Mins`) map to one destination column (`cook_time_minutes`), and nothing in frozen architecture states which one it should hold.

---

## 2. Root Cause Report

### A. Ingredient Orphans — verified against `ingredients_v5.csv` and `ingredient_aliases_v2.csv` directly (not assumed)

| Orphan | Root Cause | Evidence |
|---|---|---|
| `basmati_rice` | **Naming/tokenization mismatch, not a missing entity.** Canonical row is `rice_basmati` (word-order convention: `<type>_<variety>`), with alias `basmati chawal` (hindi) already registered. Batch 4 used the reverse order. | `ingredients_v5.csv` row: `rice_basmati,Basmati Rice,grain_flour,...`; `ingredient_aliases_v2.csv`: `rice_basmati,basmati chawal,hindi` |
| `coriander_seeds` | **Genuine canonicalization omission.** Canonical set has `coriander_powder` (ground) and `coriander_leaves` (fresh herb) — but whole dried coriander seed is a culinarily distinct ingredient (used for tempering, different from powder or leaf) and has no row at all. | Full-text check of `ingredients_v5.csv`: no `coriander_seed*` row exists in any form |
| `cumin_powder` | **Canonicalization granularity decision, not an omission.** The single canonical row `cumin_seeds` explicitly states "Whole **or ground**" in its description — Batch 2 deliberately collapsed both physical forms into one ingredient. Batch 4's source distinguishes the ground form by a different name, orphaning it against that earlier granularity decision. | `ingredients_v5.csv`: `cumin_seeds,Cumin Seeds (Jeera),spice,...,Whole or ground. Tempering staple.` |
| `mixed_vegetables` | **Tokenization/genuine compound issue — not a single ingredient at all.** It's a collective/bundle term (e.g., "mixed vegetable curry" using multiple discrete vegetables), not an atomic ingredient, so it cannot and should not resolve to one canonical row. | No `mixed_vegetable*` row exists; all other vegetable rows in `ingredients_v5.csv` are single-item (onion, potato, cauliflower, etc.) |

**Conclusion:** 1 of 4 is a pure naming-convention mismatch (trivially fixable via alias registration), 1 is a genuine missing ingredient, 1 is a granularity decision already made by Batch 2 that Batch 4's data doesn't honor, and 1 is not an ingredient-shaped token in the first place. These are four different problems wearing the same "orphan" label — they should not be resolved with one blanket rule.

### B. Texture Orphans — verified against full `tags_v4.csv` (all 12 categories, 111 rows), not just the Texture category

| Orphan | Root Cause | Evidence |
|---|---|---|
| `juicy` | **Not a texture orphan at all — it's a cross-category mismatch.** `juicy` already exists as a canonical value, but under category `mouthfeel` (tier_3), not `texture`: `mouthfeel,juicy,Juicy,tier_3,Y,Releases liquid on bite. Kebabs`. Batch 4's `Texture` column is tagging a mouthfeel concept. | Direct grep of `tags_v4.csv` |
| `brothy` | **Genuinely new value — confirmed absent from all 111 rows, all 12 categories.** Conceptually closest to `mouthfeel` (which already has `moist`, `juicy`, `gelatinous` — all liquid-content descriptors), not `texture`. | Full-file search returned 0 matches |
| `spongy` | **Genuinely new value — confirmed absent from all 111 rows, all 12 categories.** Conceptually closest to existing `texture` values `fluffy` and `soft` but distinct (describes dhokla/rasgulla-type structure, not idli-type softness). | Full-file search returned 0 matches |

**Conclusion:** This is not "3 new texture values" as the orphan label suggests. It's 1 miscategorized value (belongs in `mouthfeel`, already exists) and 2 genuinely new values that likely belong in `mouthfeel`, not `texture`, based on conceptual proximity to that category's existing members. Routing all 3 into "add to texture vocabulary" would be the wrong fix for 2 of them.

---

## 3. Alternate Name Strategy

Investigated `term_synonyms_v2.csv`'s 93 rows (language field + `disambiguation_note` free text) for natural categories. Three — and only three — are evidenced; no additional categories (marketing name, historical name, abbreviation) appear anywhere in the data, so none are proposed:

| Category | Evidence | Example |
|---|---|---|
| **Regional/Language Alias** (majority — ~85 of 93 rows) | `disambiguation_note` explicitly names a region or language identity: "Delhi/North India name", "Kolkata name", "Karnataka name", "Andhra/Telangana name" | Pani Puri → Gol Gappa (hindi, Delhi), Puchka (bengali, Kolkata), Gupchup (hindi, Jharkhand/Odisha) |
| **Spelling Variation** (same language, different transliteration) | `disambiguation_note` literally says "Alternate spelling" / "Alternate English spelling" | Idli → Idly (english); Sambar → Sambhar (english); Paratha → Parantha (hindi) |
| **Word-Order Variation** | `disambiguation_note` literally says "Alternate word order" | Chaat Papdi → Papdi Chaat (hindi) |

**Data quality finding surfaced by this task (new, not previously logged):** one row — `Paratha → Parotta (tamil)` — carries `disambiguation_note = "South Indian layered bread - different dish"`. This row is *structurally* a synonym entry but its own note says the two are **not** the same dish. This is a self-contradicting row: either it should not be in `term_synonyms_v2` at all, or the note is doing double duty as a "false-friend" warning. Recommend flagging for Founder clarification — logging as **B4-DQ-006** rather than silently reinterpreting it.

**Relevance to Batch 4:** `dishes.xlsx`'s own `Alternate Names` column (B4-OBS-REL-005) doesn't carry a language tag the way `term_synonyms_v2` does — it's a flat comma list. If the two mechanisms are ever merged (still an open Founder decision per B4-RES-002/CBD-001), these three categories are the natural classification scheme to carry over, since they're the only ones with actual evidentiary support.

---

## 4. Cuisine Architecture — Evidence Threshold Assessment

**Not redesigning. Assessing only whether the evidence bar has moved.**

Batch 3 evidence (frozen): cuisine has 0 orphans in the abstract vocabulary sense (65 clean cuisine rows, hierarchy intact).
Batch 4 evidence (new): **100% of 810 real dish rows** — the largest content sample in the project so far — reference a cuisine value, all 810 matching Batch 3's canonical list, and **zero destination exists anywhere in frozen architecture** to store any of them.

This changes the evidence *scale*, not the evidence *nature*. B3-RES-001/002 already correctly identified the gap; Batch 4 supplies the concrete cost of leaving it open (every single dish row is affected, not a hypothetical). Recommend: cuisine should move to the top of the AGR/SER priority queue on **impact size**, not because a new architectural question was discovered. This is a prioritization signal, not a new finding.

---

## 5. Combo Intelligence Notes (evidence only — no modeling, no decomposition)

Extracted from `dish_combo_items_v2_20260520.csv` (74 rows) and cross-referenced against Batch 4's 8 COMBO-flagged dishes:

- **Role vocabulary observed (8 distinct values):** `primary`, `bread`, `carb_base`, `accompaniment`, `condiment`, `dessert`, `beverage`, `standalone`. This is a real, bounded vocabulary already in use across 35 combos — useful as a starting enum if/when `dish_combo_items.role` is formalized.
- **Naming convention observed:** combo names follow one of three patterns: (a) `DishA DishB` concatenation (`Chole Bhature`, `Rajma Chawal`), (b) a descriptive suffix (`Kerala Rice Meals`, `Hyderabadi Biryani Set`), or (c) identical to the sole member dish, tagged `role=standalone` (`Matar Kulcha`, `Sadya Thali`, `Keema Pav`). This third pattern is directly relevant to Batch 4's 8 flagged rows — several (`Nahari Kulcha`, `Aloo Puri`) look structurally like standalone-role combos, not multi-item combos.
- **Pairing convention observed:** `is_default=Y` marks the canonical pairing; `is_swappable=Y` marks alternates (e.g., `Rajma Chawal` accepts `Jeera Rice` as default carb, `Phulka` as a swappable alternate) — a real substitution pattern already encoded, not something Batch 5 needs to invent from scratch.
- **Direct name overlap with Batch 4's 8 flagged dishes:** confirmed conceptual (not exact-string) overlap on at least 2 — `Dal Baati` ↔ `Dal Baati Churma`, `Poha Jalebi (Indori)` ↔ `Poha Jalebi` — consistent with what `Batch4_Pipeline_Package_v1.0` already found. `Nahari Kulcha` appears in the combo-items file as `Nihari Kulcha → Nahari Kulcha (role: standalone)`, a near-exact match not previously surfaced — **new evidence strengthening CBD-004**.

No component decomposition or combo modeling was performed — this is inventory only, for Batch 5's use.

---

## 6. Image Convention Findings

`Batch4_Pipeline_Package_v1.0` (B4-MI-009) already establishes that `dishes.xlsx` carries an `image_folder` **path** column, not a URL, and that URL/blurhash construction logic is undefined. No additional deterministic naming convention (slug pattern, UUID scheme, folder hierarchy) is evidenced anywhere in the reviewed project files beyond this single path column. This task does not add new evidence beyond what B4-MI-009 already recorded — flagging that explicitly rather than inventing a convention that isn't there.

---

## 7. Food DNA Observation — Tier 3 Absence

**B4-OBS-VOC-002:** Batch 4's 810 rows carry only `tier_1` (487) and `tier_2` (323) Food DNA values — **no `tier_3` dish exists in this batch.**

Cross-referenced against `RE-DOC-02`'s tier definitions (frozen): Tier 3 is explicitly documented as **"future ML," "not required at MVP"** (combo_pairing_affinity, regional_microvariant, festival_relevance, dietary_subcategory). Given Tier 3 is scoped as a post-MVP enrichment layer rather than a per-dish classification every dish is expected to carry at seed time, its absence across all 810 Batch 4 rows is **consistent with intentional design**, not an unexpected gap. No dish in the frozen tier framework is required to reach Tier 3 before launch — this reads as expected, not a defect.

---

## 8. Seed Impact Matrix — Batch 4 Open Resolutions

Added as an explicit field on every currently open Batch 4 Resolution, classified **only** by effect on Phase 9 Seed Generation:

| RES ID | Gap | Seed Impact | Basis |
|---|---|---|---|
| B4-RES-001 | Cuisine has no destination | **Critical** | Blocks seeding cuisine for all 810 rows — no row can carry this attribute at all until resolved |
| B4-RES-002 | Alternate Names cardinality (2 slots vs. unbounded) | **Medium** | Affects only dishes with 2+ alternate names (bounded subset, not all 810) |
| B4-RES-003 | Spice/Sweetness/Heaviness — no destination | **High** | All 810 rows lose a Food DNA input dimension if unresolved before seed generation |
| B4-RES-004 | Cook-time field ambiguity | **High** | Wrong field choice seeds an incorrect value silently across all 810 rows — high risk precisely because it wouldn't throw an error |
| B4-RES-005 | Calories — no destination | **Medium** | Display-only attribute; not consumed by frozen RE scoring per current documents |
| B4-RES-006 | Serving Size — no destination | **Low** | Display-only, narrow feature surface |
| B4-RES-007 | tier_1 (Food DNA tier) not persisted at dish level | **High** | Tier is computed but has nowhere to land — affects downstream RE tier-based logic for all 810 rows |
| B4-RES-008 | is_indian_only derivation undefined | **Medium** | Affects a filtering feature, not core plan generation |
| B4-RES-009 | Photo URL scheme undefined | **Medium** | Blocks a user-facing feature (dish photos) but not seed correctness of core fields |
| B4-RES-010 | 4 ingredient orphans | **Critical** (for touched rows) | These specific dish→ingredient FK inserts will hard-fail without resolution — not a display gap, a load-time failure |
| B4-RES-011 | 3 texture orphans | **High** (for touched rows) | Same FK-failure mechanism as above, narrower category |
| B4-RES-012 | Tag pipeline blocked (inherits B3-RES-003/004) | **Critical** | Blocks `dish_tags` for all 810 rows, all 11 categories — the single largest seed-blocking item in Batch 4 by row×column surface area |
| B4-RES-013 | 8 combo-candidate rows need decomposition rule | **Medium** | Narrow (8 rows), but wrong handling means these dishes either seed incorrectly as standalone or don't seed at all |

**Primary prioritization signal for Founder:** B4-RES-001, B4-RES-010, and B4-RES-012 are the three **Critical** items — two are FK-failure risks (hard stops at seed-load time, not soft display gaps), and one (cuisine) affects literally every row. These should be resolved first regardless of how the remaining High/Medium/Low items are sequenced.

---

## 9. Cross-Batch Dependency (CBD) Priority Review

Per instruction: priority only, no CBD is closed.

| CBD | Prior Priority | New Evidence This Session | Revised Priority |
|---|---|---|---|
| CBD-001 (Batch 2 Synonyms → Batch 4) | Open, evidence-only | Unchanged this session (already fully strengthened in `Batch4_Pipeline_Package_v1.0` — 79/93 confirmed, 62 corroborated) | **No change — remains Open, high-confidence, unresolved by Founder** |
| CBD-002 (Batch 3 Cuisine → Batch 4) | Open, confirmed, higher urgency | §4 above confirms scale (100% of 810 rows affected) but no new *nature* of evidence | **Priority raised to highest of the four** — largest confirmed blast radius of any open CBD |
| CBD-003 (Batch 3 Tags → Batch 4) | Open, confirmed and narrowed | §2B above refines it further: of the 3 texture orphans, only 2 are genuinely new values — the 3rd is a mouthfeel/texture cross-category error, not a vocabulary gap | **Priority unchanged, but scope narrowed** — the actual new-value burden is smaller than previously stated (2 new values, not 3) |
| CBD-004 (Batch 4 Dishes → Batch 5 Combos, NEW) | New this batch | §5 above adds a third near-match (`Nahari Kulcha`/`Nihari Kulcha`) to the 2 already found, and surfaces the `role=standalone` pattern as a likely fit for several of the 8 flagged dishes | **Priority raised** — evidence base for a clean resolution path is now stronger (3 of 8 have concrete combo-file matches, not 2) |

---

## 10. Regression Review

- ✅ No Batch 1/2/3 frozen document reopened or modified
- ✅ No architecture, schema, RE, or API document touched
- ✅ No AGR, SER, or DCR created
- ✅ No SQL, DDL, or migration proposed or run
- ✅ `Batch4_Pipeline_Package_v1.0` referenced, not regenerated — Discovery/Canonicalization/Mapping/Gap Analysis/Resolution stages were not rerun
- ✅ No GAP ID, RES ID, or CBD ID renumbered, merged, or reused
- ✅ No CBD closed — all four remain Open per §9
- ✅ New findings (B4-DQ-006 self-contradicting synonym row; the `juicy` cross-category miscategorization; the `Nahari Kulcha` combo-file match) are additive evidence layered onto the frozen pipeline, not edits to it
- ✅ `Sheet1` of `dishes.xlsx` not read at any point in this session

---

## 11. Batch 4 Freeze Recommendation

**Recommend: FREEZE `Batch4_Pipeline_Package_v1.0`.**

Basis: all 5 stages complete, all 13 gaps carry a resolution path, all 4 CBDs are logged and now more precisely evidenced than at pipeline-completion time, and this refinement pass found no architecture, schema, lineage, or business-correctness contradiction — the two findings that came closest (the `juicy` mouthfeel/texture mismatch, and the self-contradicting Paratha/Parotta synonym row) are both **data-precision corrections that sharpen existing gaps**, not new stop-condition-triggering defects. Per the Permanent Execution Rule, neither interrupts execution; both are recorded here and should also be logged to `DOC-P3-12` as governance-backlog-adjacent precision notes, not treated as new GAPs requiring their own Resolution Register entries.

Freezing Batch 4 does **not** mean all open items are resolved — consistent with how Batch 1, 2, and 3 were each frozen with open GC/RES/CBD items still outstanding. It means Batch 4's own pipeline is internally complete, consistent, and ready to be relied upon by Batch 5.

**Recommend: do NOT begin Batch 5** until this freeze is Founder-approved, per instruction.

---

## 12. Founder Approval Gate

**Batch 4 Technical Review, Root Cause Analysis, Alternate Name Strategy, Cuisine Evidence Review, Combo Intelligence Notes, Image Convention Findings, Food DNA Observation, Seed Impact Matrix, and CBD Priority Review are complete. No AGR, SER, or DCR has been created. No GAP has been resolved, closed, or reclassified. No frozen document has been modified. Batch 4 is recommended for freeze but is NOT yet frozen by this document — that requires Founder sign-off. Batch 5 has NOT begun.**

New items surfaced this session requiring Founder attention before/alongside freeze:
- **B4-DQ-006** (new): self-contradicting `Paratha → Parotta` synonym row in `term_synonyms_v2.csv`
- Refined understanding of B4-GAP-011 (texture orphans): only 2 of 3 are genuinely new values; `juicy` is a category-placement error, already present under `mouthfeel`

Founder sign-off: _______________________ Date: ___________
