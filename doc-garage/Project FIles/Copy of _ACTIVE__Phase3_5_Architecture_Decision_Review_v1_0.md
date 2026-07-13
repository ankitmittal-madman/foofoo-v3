# [ACTIVE]_Phase3_5_Architecture_Decision_Review_v1.0

**Final architecture checkpoint — executed after the Project Integration Review, before Phase 9**
**Scope:** Evaluation only. No redesign. No new AGR/SER created. No frozen document reopened.
**Date:** 2026-07-03 · **Status:** Draft — Ready for Founder Review

---

## 1. Baseline Verification

| Item | Verified State | Source |
|---|---|---|
| Phase 3 | COMPLETE / APPROVED / FROZEN | `Project_Baseline_Register_v1.5` Step 10 |
| Batches 1–6 | COMPLETE / FROZEN | Each batch's own freeze artifact (confirmed in the PIR, §1) |
| Phase 3.5 Project Integration Review | COMPLETE | `Phase3_5_Project_Integration_Review_v1.0` — present in project files, all 14 sections intact |
| `DOC-P3-09` | Current at v1.3 (§06E Persistence Rule) | Present in project files as `_ACTIVE__DOC-P3-09_Knowledge_Integration_Governance_v1_3.md` |
| `DOC-P3-11` | **Project file is v1.20 — one revision behind.** The v1.21 content (Batch 4/5 freeze correction, Batch 6 addition) was fully specified inside `Batch6_Pipeline_Package_v1.0` §9 but was never filed as its own standalone document. This is a targeted document-status correction, not a new finding — flagged per this session's "stale execution register" correction allowance, not treated as blocking. | Direct file listing this session; `Batch6_Pipeline_Package_v1.0` §9/§10 |

No frozen batch or document reopened during this verification.

---

## 2. Architecture Decision Review

Every remaining architecture-related item from the PIR's Blocker Matrix, reviewed individually with no option selected:

### 2.1 — Cuisine Persistence (`public.dishes`, `public.dish_combos`)
- **Evidence:** 100% of 810 dishes and 100% of 35 combos carry a valid cuisine value (matching Batch 3's canonical 65-cuisine list); zero destination column exists on either table in frozen `DOC-P3-04 v1.3`.
- **Current state:** Cuisine is fully present in source data, completely absent from schema.
- **Options:** (a) add a `cuisine_id` FK column to both `dishes` and `dish_combos`, referencing a new `public.cuisines` table seeded from `cuisines_v4.csv`; (b) add a plain `cuisine text` column to both tables with no FK (looser, faster, no referential integrity); (c) do not persist cuisine as a queryable attribute at all — treat it as informational/derivable from dish name and defer permanently.
- **Trade-offs:** (a) is the most correct long-term (matches the project's existing FK-everywhere discipline, e.g. `re_states`, `tags`) but is the largest single schema change in Phase 3.5 to date, touching two tables at once. (b) is faster to implement but reintroduces exactly the kind of unconstrained text field the project has otherwise avoided. (c) costs nothing architecturally but discards a Genome-relevant signal (`RE-DOC-02`'s regional_origin tag dimension already implies cuisine matters to ContentMatch).
- **Seed impact:** Critical — 845 rows (810+35) across 2 tables affected; this is the single highest-row-count blocker in the project.
- **Business impact:** High — cuisine filtering/display is a basic, expected product feature; its total absence would be immediately visible to users.
- **Cross-batch impact:** Resolves CBD-002, B4-GAP-001, B5-GAP-003, B3-RES-001/002 simultaneously — this is the single decision with the widest consolidation payoff in the entire review.
- **Recommendation:** None offered, per instruction.

### 2.2 — Regional Affinity Persistence
- **Evidence:** `region_food_affinity.csv` — 136 rows, dish-level affinity scores (0.80–0.95) to specific states; no table anywhere in frozen architecture is shaped to hold this.
- **Current state:** Data exists, is well-formed, has no destination.
- **Options:** (a) new table `re_engine.re_dish_regional_affinity(dish_id, state_code, affinity_score)`, feeding RE ContentMatch directly; (b) fold into the existing `dish_tags` mechanism as a new tag dimension (`regional_affinity`) with `confidence` reused as the score; (c) do not persist as a structured signal — leave as reference-only content-team data, not RE input.
- **Trade-offs:** (a) is the cleanest semantic fit but is a net-new table (an SER, not a CHECK-constraint edit). (b) reuses existing infrastructure with zero new tables but overloads `dish_tags.confidence`'s established meaning (tag-assignment certainty, not regional strength — these are different concepts wearing the same column). (c) costs nothing now but permanently discards a signal Batch 6 confirmed is real and non-trivial (2 genuine multi-region cases, clean 0.80–0.95 distribution).
- **Seed impact:** High — 136 rows; also gates whether Batch 1's eventual full `re_states` seeding (now resolved per the PIR's IDR-001 finding) has a second consumer.
- **Business impact:** Medium — improves regional personalization quality but the product functions without it (cohort/state logic already exists independently in `re_engine.re_cohorts`).
- **Cross-batch impact:** Resolves B6-GAP-001; supersedes B6-CBD-001 entirely (per PIR §4).
- **Recommendation:** None offered.

### 2.3 — Dish-Level Attributes (spice, sweetness, heaviness, calories, serving size, Food DNA tier)
- **Evidence:** All 6 attributes populated on all 810 dishes in `dishes.xlsx`; none has a destination column in `DOC-P3-04 v1.3`.
- **Current state:** Fully populated source data, fully absent schema.
- **Options:** (a) add all 6 as individual columns on `public.dishes`; (b) add only the ones with confirmed RE relevance (Food DNA `tier_1`, since `RE-DOC-02`/`RE-DOC-03` explicitly reference dish tiers) and defer the other 5 as display-only content; (c) fold spice/sweetness/heaviness into the existing `dish_tags` genome mechanism as new tier-2 dimensions, keep calories/serving_size as plain columns (display-only, not genome-relevant).
- **Trade-offs:** (a) is simplest to reason about but adds 6 columns for attributes of very different character (some are genome-relevant, some are pure display). (b) is minimal-footprint but leaves calorie/serving-size display broken. (c) matches the project's stated genome-via-tags architecture pattern most closely but requires classifying which of the 6 are "genome" vs. "display" — a judgment call, not a pure evidence question.
- **Seed impact:** High — all 810 dishes.
- **Business impact:** Medium-High — calories/serving size are common app-level expectations; spice/sweetness/heaviness likely feed filtering or ContentMatch.
- **Cross-batch impact:** None beyond Batch 4 itself (B4-MI-003/005/006/007).
- **Recommendation:** None offered.

### 2.4 — Alias / Alternate Names Handling
- **Evidence:** `dishes.xlsx`'s own `Alternate Names` column supports exactly 2 fixed destination slots (`name_hindi`, `name_regional`) but source data is an unbounded comma list; separately, `term_synonyms_v2.csv` (Batch 2, 93 rows) provides an independently-sourced, language-tagged synonym mechanism with 79-of-93 confirmed overlap against Batch 4's dish names, 62 of those corroborated in both mechanisms without conflict (1 full spot-check).
- **Current state:** Two partially-overlapping alias mechanisms exist; neither is unified; the 2-slot destination is narrower than the source data for dishes with 3+ names.
- **Options:** (a) unify into one mechanism — retire the fixed 2-slot columns, move all alias data into a `dish_aliases` junction table using the 3 evidenced categories from Batch 4's Alternate Name Strategy (regional/language, spelling variation, word-order variation); (b) keep both mechanisms separate and simply widen the fixed-slot approach (add `name_alt_3`, `name_alt_4` columns as needed); (c) keep both mechanisms as-is, accept the narrower 2-slot cardinality as a known, disclosed limitation.
- **Trade-offs:** (a) is the most correct long-term and directly reuses the Alternate Name Strategy categories already evidenced (no new discovery needed) but is a genuine schema change (new table) plus a data-migration decision for the 62 already-populated overlapping dishes. (b) is a smaller change but doesn't address the two-mechanism duplication. (c) costs nothing but permanently caps alias richness at 2 per dish.
- **Seed impact:** Medium — up to 17 dishes (per B4-GAP-002's estimate) with 3+ alternate names lose data under the status quo.
- **Business impact:** Low-Medium — affects search/discovery quality for dishes with many regional names, not core functionality.
- **Cross-batch impact:** Resolves CBD-001 entirely.
- **Recommendation:** None offered.

### 2.5 — Tag Vectors / Food DNA Genome Mechanism
- **Evidence:** `public.tags` has a naming/uniqueness conflict and missing `vector_position` values for some rows (B3-RES-003/004, both Critical, both blocking `RE-DOC-01–05`'s entire genome-vector mechanism); a deterministic vector-position assignment algorithm is **already drafted** (order by tier ascending, then category, then value, alphabetically; sequential integers 0–110) and awaiting only Founder confirmation, not further design.
- **Current state:** Closest-to-resolved Critical item in the project — the hard design work is done.
- **Options:** Not applicable in the usual sense — there is effectively one drafted path (the algorithm) and the only real "option" is whether the Founder confirms it as-is or requests a different deterministic ordering rule.
- **Trade-offs:** Confirming as-drafted costs nothing further; requesting a different ordering rule would require redrafting but not rediscovering evidence.
- **Seed impact:** Critical — blocks all `dish_tags` population, all 810 dishes, all 11 tag categories, and by extension the entire genome-vector trigger mechanism (`fn_update_dish_genome_vector`).
- **Business impact:** Critical — the RE's core ContentMatch scoring cannot function without this.
- **Cross-batch impact:** Resolves CBD-003 entirely; unblocks B4-GAP-012/B4-MI-012 (dish-level tag population, currently blocked project-wide).
- **Recommendation:** None offered, though this is flagged as the fastest of the three Critical items to close given the drafted state.

### 2.6 — Combo Roles (`dish_combo_items.role` CHECK constraint)
- **Evidence:** Live CHECK allows `('primary','side','accompaniment')`; actual data uses 8 values; 31 of 74 rows (41.9%) would hard-fail insert; `side` (schema-allowed) is used in 0 rows. A 3-option Architecture Option Pack already exists (`Batch5_Pipeline_Package_v1.1` Task 3: expand CHECK to 8 values / collapse 6 extra values onto the existing 3 / add a second `component_type` column alongside the unchanged `role`).
- **Current state:** Decision pack fully prepared, awaiting one Founder pick.
- **Options:** Already enumerated in the cited Option Pack — not re-derived here, per the "don't recreate frozen work" instruction.
- **Trade-offs:** Already stated in the Option Pack.
- **Seed impact:** Critical — 31 of 74 combo_item rows.
- **Business impact:** High — combo composition/swap UI depends on `role` being queryable correctly.
- **Cross-batch impact:** None beyond Batch 5 itself.
- **Recommendation:** None offered (consistent with the Option Pack's own original discipline).

### 2.7 — Combo Relationships (dish_name → dish_id resolution)
- **Evidence:** Already reclassified Architecture-owned in `Batch5_Pipeline_Package_v1.1` Task 4 — the FK target exists, only a deterministic string-matching method is undecided.
- **Current state:** Not a Founder decision at all anymore — an Architecture implementation choice.
- **Options/Trade-offs:** Not re-litigated here — this item does not need Founder attention per the PIR and this review's own confirmation.
- **Seed impact:** High (all 74 combo_item rows need this to seed at all) but **not Founder-blocking**.
- **Recommendation:** None needed — Architecture proceeds once Phase 9 begins.

### 2.8 — Remaining Schema Capability Gaps (`combo_slug`)
- **Evidence:** No destination column identified anywhere for a URL-friendly combo slug.
- **Current state:** Low-impact, deferred per PIR §10.
- **Options:** Add now (SER) vs. add later if/when URL-based combo routing is actually built.
- **Seed impact:** Low — 0 rows blocked, purely a future feature gap.
- **Recommendation:** None offered; already correctly deferred, not re-elevated here.

---

## 3. Decision Consolidation Matrix

| Original Items | Consolidated Into | Justification |
|---|---|---|
| CBD-002, B4-GAP-001, B5-GAP-003, B3-RES-001, B3-RES-002 | **Decision 1 — Cuisine Persistence** (§2.1) | All five are the identical underlying question — "where does cuisine live" — asked once per affected table/batch. Genuinely the same architectural question, not five separate ones. |
| B3-RES-003, B3-RES-004, CBD-003 | **Decision 2 — Tag Vector Confirmation** (§2.5) | B3-RES-004's algorithm resolves B3-RES-003's structural conflict as a side effect (assigning positions requires first resolving the naming collision) — these were always one decision wearing two GAP numbers, and CBD-003 is the downstream consequence of the same root cause. |
| B5-RES-001 (already an Option Pack, not re-split) | **Decision 3 — Combo Role Vocabulary** (§2.6) | Already single-item; no further consolidation possible or needed. |
| B6-GAP-001, B6-CBD-001 | **Decision 4 — Regional Affinity Persistence** (§2.2) | B6-CBD-001 was already noted in the PIR (§4) as fully superseded by the IDR-001 finding for its `re_states`-dependency half; what remains is purely the "where does affinity live" question, i.e., B6-GAP-001 alone. Confirmed here, not re-derived. |
| B4-MI-003, B4-MI-005, B4-MI-006, B4-MI-007 | **Decision 5 — Dish Attribute Persistence** (§2.3) | Four missing-column findings on the same table (`public.dishes`), same root cause (six attributes, no destination) — one decision, not four. |
| B4-MI-002, CBD-001 | **Decision 6 — Alias Unification** (§2.4) | Same underlying concept (dish naming variants) approached from two source files — one decision. |
| GC-SER-005, GC-SER-006, GC-SER-007, GC-SER-009, Consolidation Rec. A, Consolidation Rec. B | **Not re-consolidated here** — already fully addressed in PIR §5/§10; this review does not duplicate that consolidation, only confirms it stands | Avoiding double-consolidation of the same items across two review documents |

**Net result: what the PIR's Blocker Matrix presented as ~9 distinct tracked items collapses here into exactly 6 architecture decisions** (cuisine, regional affinity, dish attributes, alias unification, tag vector confirmation, combo roles) — 3 of which (tag vectors, combo roles, cuisine) are Critical/Phase-9-blocking, 3 of which (regional affinity, dish attributes, alias unification) are High-value but not blocking.

---

## 4. Coverage Audit (quantitative, no estimates)

| Metric | Value |
|---|---|
| Knowledge domains discovered | 6 / 6 (Persona/Cohort, Ingredients, Cuisine/Tags, Dishes, Combos, Regional Affinity) |
| Canonical entities established | 15 (Batch 1) + 2 (Batch 2: Ingredient, Ingredient Alias) + 3 (Batch 3: Cuisine Group, Cuisine, Tag) + 2 (Batch 4: Dish, excluded Dish) + 2 (Batch 5: Combo, Combo Item) + 1 (Batch 6: Regional Affinity) = **25 canonical entities total** |
| Relationships evidenced | 5 (Batch 1, implied by CAN-REL entries) + 1 (Batch 2) + 3 (Batch 3) + 5 (Batch 4) + 4 (Batch 5) + 5 (Batch 6) = **23 relationships total**, 0 with broken lineage |
| Business rules captured | 2 (Batch 1 core rules, e.g. uniqueness) + 6 (Batch 4) + 6 (Batch 5) + 4 (Batch 6) = **18 business rules total** (Batch 2/3 rules folded into their vocabulary/relationship counts per those batches' own framing, not double-counted here) |
| Lineage integrity | **100%** — 0 orphan OBS/CAN/MAP/GAP/RES IDs found across all 6 batches (confirmed directly in PIR §7) |
| Cross-Batch Dependencies — Resolved | 1 of 5 (CBD-004, partially: 3 of 8 dishes) — **not counted as fully resolved**, tracked as Deferred (see below) |
| Cross-Batch Dependencies — Deferred | 2 of 5 (CBD-001 via Decision 6; CBD-004's remaining 5 dishes) |
| Cross-Batch Dependencies — Blocking | 2 of 5 (CBD-002 via Decision 1; CBD-003 via Decision 2) |
| Cross-Batch Dependencies — Superseded | 1 of 5 (B6-CBD-001, fully absorbed by the IDR-001 finding) |
| Architecture (AGR) candidates — Still Required | 6 (AGR-P3-07-001 open/launch-only; GC-AGR-002; B3-RES-001/002/003 folded into Decision 1/2) |
| Architecture (AGR) candidates — Resolved | 4 (AGR-001–004) |
| Architecture (AGR) candidates — Deferred | 1 (GC-AGR-001) |
| SER candidates — Before this review's consolidation | 13 (per PIR §8) |
| SER candidates — After PIR + this review's consolidation | **9** (PIR's own consolidation, §5, confirmed unchanged here — not re-litigated) |
| Decisions requiring Founder input before Phase 9 | **3** (Decisions 1, 2, 3 — cuisine, tag vectors, combo roles) — down from the PIR's own count of "4 minimum required actions," since Action 1 (confirm IDR-001) is addressed as a factual finding in this baseline verification's inherited context, not a design decision |

---

## 5. Blocker Reclassification

### Group A — Phase 9 Blockers (genuinely prevent seed generation)
1. **Decision 1 — Cuisine Persistence** (§2.1) — 845 rows across 2 tables cannot store cuisine at all
2. **Decision 2 — Tag Vector Confirmation** (§2.5) — blocks all `dish_tags` population, all 810 dishes
3. **Decision 3 — Combo Role Vocabulary** (§2.6) — blocks 31 of 74 combo_item rows from inserting

### Group B — Launch Blockers (required before production, not before Phase 9)
1. **AGR-P3-07-001** (DPDP minor-protection, no implemented age-verification mechanism) — legal compliance gate, confirmed in the PIR as not Phase-9-blocking
2. **Decision 4 — Regional Affinity Persistence** (§2.2) — improves RE quality but the product functions without it at MVP
3. **Decision 5 — Dish Attribute Persistence** (§2.3) — calorie/serving-size display is an expected feature but not a seed-blocking one (dishes still seed correctly without these 6 columns, just with less content)

### Group C — Future Enhancements (do not affect seed quality)
1. **Decision 6 — Alias Unification** (§2.4) — status quo (2-slot cardinality) is a known limitation, not a defect; seeding proceeds correctly either way
2. **`combo_slug`** (§2.8)
3. All 9 consolidated SER candidates from the PIR not otherwise elevated above (business-meaning calls like GC-DOC-002, B2-RES-005; residual attribute SERs)

**No item was over-classified.** Notably, GC-AGR-002 (Batch 1's 22-row CHECK violation, previously flagged "blocks Phase 9 for Batch 1" in `Project_Checkpoint_v1.0`) is re-examined here: per the PIR's IDR-001 finding, Batch 1's full seed dataset (`Indian_Meal_Cohort_Persona_DB_v3.xlsx`) is now confirmed present and matching every Seed Gate target — meaning GC-AGR-002's specific 22-row violation should be re-verified against the *real* data, not the illustrative subset it was originally found against. This is flagged as a **Group A item pending re-verification**, not assumed resolved or assumed still-blocking without evidence.

---

## 6. Architecture Health Report

| Dimension | Assessment |
|---|---|
| **Schema completeness** | 3 genuine capability gaps remain (cuisine, regional affinity, dish attributes) out of the full knowledge scope discovered — the vast majority of discovered knowledge (ingredients, tags structurally, combos structurally, all core dish fields) has a correct destination |
| **Knowledge completeness** | 6 of 6 domains discovered; 0 domains found entirely missing; 2 sub-dimensions (seasonality, festival influence) explicitly confirmed absent from current source files, not silently assumed present |
| **Cross-batch consistency** | High — every cross-batch relationship checked resolves cleanly or is explicitly flagged Medium-confidence where a full join wasn't performed (never silently assumed) |
| **Architecture consistency** | High — no internal contradiction found in frozen `DOC-P3-04`/`DOC-P3-05` itself; every gap found is an *absence* (missing column/table) or a *narrowness* (CHECK constraint), never a contradiction within the schema's own logic |
| **Seed readiness** | High for the majority of content (config tables, `re_states`/`re_personas`/`re_cohorts`/weekly plans via the now-confirmed-present master workbook, ingredients, cuisines, tags-as-vocabulary, dishes' core fields, combos' core structure); blocked specifically and only on the 3 Group A items |
| **Implementation readiness** | High — all 3 Group A decisions have either a drafted solution (tag vectors) or a fully-built decision pack (combo roles, cuisine consolidation across 5 prior items into 1 clean question) |

---

## 7. Architecture Freeze Assessment

**READY TO FREEZE, conditional on the 3 Group A decisions being made.** The architecture itself (table shapes, relationships, junctions, constraints) shows no internal inconsistency anywhere across 6 batches of evidence — every finding across the entire project has been an absence or a narrowness, never a contradiction requiring redesign. The 3 remaining Critical items are additive (new column/table) or corrective-narrow (widen one CHECK constraint) — none require touching or redesigning any already-frozen structural element. Once Decisions 1–3 are made, no further architectural evolution is anticipated before Phase 9, satisfying the definition of Architecture Freeze stated in the instruction.

---

## 8. Regression Review

- ✅ No Batch 1–6 frozen document modified or reopened for edit
- ✅ No Discovery, Canonicalization, Mapping, Gap Analysis, or Resolution recreated for any batch
- ✅ No lineage changed — §4's Coverage Audit recomputes counts from already-frozen figures, changes no ID or link
- ✅ No schema changed — all 6 architecture decisions in §2 remain unselected options
- ✅ No architecture changed
- ✅ No new AGR or SER created — Decision 1–6 are evaluations; the "6 decisions from ~9 items" consolidation in §3 is a tracking simplification, not an architectural change
- ✅ Only evaluations performed — every recommendation field in §2 is explicitly "None offered"
- ✅ GC-AGR-002 re-verification flag (§5) is a targeted, evidence-based correction (new information: the real dataset is now confirmed present) — not a reclassification of a frozen decision without evidence

---

## 9. Persistence Manifest

**Created:**
- `[ACTIVE]_Phase3_5_Architecture_Decision_Review_v1.0.md`

**Updated (flagged, not executed in this document — per this session's lightweight-documentation instruction):**
- `[ACTIVE]_DOC-P3-11_Discovery_Execution_Register_v1.21.md` should be filed as its own document — content already fully specified in `Batch6_Pipeline_Package_v1.0` §9, simply never materialized as a standalone file. Recommend filing this before Phase 9 begins so the register accurately reflects Batch 6's frozen status, but this is a document-hygiene action, not an architecture blocker.

**Supersedes:**
- None — first-issue document.

No historical file renamed. No historical file deleted. Founder manages historical file lifecycle manually, per `DOC-P3-09` §06E. No new permanent governance framework introduced — this document is a one-time checkpoint artifact, not a recurring process definition.

---

## 10. Founder Decision Summary

Exactly 3 decisions required before Phase 9:

1. **Cuisine Persistence** (§2.1) — pick (a) FK to new `cuisines` table, (b) plain text column, or (c) don't persist. Resolves 5 previously-separate tracked items at once.
2. **Tag Vector Confirmation** (§2.5) — confirm the already-drafted deterministic algorithm, or specify a different ordering rule. Fastest of the three to close.
3. **Combo Role Vocabulary** (§2.6) — pick Option A/B/C from the existing `Batch5_Pipeline_Package_v1.1` Task 3 pack.

One additional evidence-triggered item, not a design decision:
4. **Re-verify GC-AGR-002's 22-row CHECK violation against the real (now-confirmed-present) master dataset**, since it was originally evaluated against illustrative data only.

Everything else (Group B, Group C, and the PIR's own already-consolidated SER list) requires no action before Phase 9.

---

# FINAL ANSWER

## READY FOR PHASE 9 AFTER MINOR DECISIONS

**Minimum required decisions:**
1. Cuisine persistence approach (§2.1 / §10.1)
2. Tag vector algorithm confirmation (§2.5 / §10.2)
3. Combo role vocabulary option (§2.6 / §10.3)

(Item 4 in §10 is a re-verification step, not a decision — it can run in parallel with Phase 9 kickoff.)

No implementation plan is provided, per instruction — these are the decision points only.

Founder sign-off: _______________________ Date: ___________
