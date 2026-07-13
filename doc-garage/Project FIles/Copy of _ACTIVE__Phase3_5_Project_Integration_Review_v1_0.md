# [ACTIVE]_Phase3_5_Project_Integration_Review_v1.0

**One-time Project Integration Review (PIR) — executed after Batches 1–6, before Phase 9**
**Scope:** Integrated validation only. No batch reopened. No Discovery/Canonicalization/Mapping/Gap Analysis/Resolution recreated.
**Date:** 2026-07-03 · **Status:** Draft — Ready for Founder Review
**Governance mode adopted from this point forward:** Checkpoint-based (Execution mode for batches → Checkpoint mode for consolidation → Implementation mode once READY) — per Founder's strategy refinement this session. This document IS the Checkpoint.

---

## 1. Baseline Verification

| Item | Verified State | Source |
|---|---|---|
| Phase 3 | COMPLETE / APPROVED / FROZEN | `Project_Baseline_Register_v1.5` Step 10 |
| Batch 1 | COMPLETE / FROZEN | `Batch1_GapAnalysis_Package_v1.1` |
| Batch 2 | COMPLETE / FROZEN | `Batch2_Resolution_Package_v1.0` |
| Batch 3 | COMPLETE / FROZEN | `Project_Checkpoint_v1.0` Task 7 |
| Batch 4 | COMPLETE / FROZEN | `Batch4_Technical_Review_and_Freeze_Recommendation_v1.0` §11 |
| Batch 5 | COMPLETE / FROZEN (v1.1) | `Batch5_Pipeline_Package_v1.1` Task 6 |
| Batch 6 | COMPLETE / FROZEN | `Batch6_Pipeline_Package_v1.0` §11 |
| Duplicate ACTIVE documents | None new. 3 previously-adjudicated stale-copy pairs remain (`DOC-P3-09`, `Project_Baseline_Register`, `Engineering_Handover_...`) — all logged in `Project_Baseline_Register_v1.5`, higher-version copy authoritative in each case | Direct file listing this session |
| DOC-P3-11 currency | Updated to v1.21 in the Batch 6 session (Batch 4/5/6 status corrected). **Targeted amendment only, performed now**: add Batch 6's PIR-triggered findings pointer. No restructuring. | `Batch6_Pipeline_Package_v1.0` §9 |

No frozen batch reopened during this verification.

---

## 2. Project Health Assessment

**Overall: healthy.** Six batches executed with 100% Discovery coverage each time, zero silent resolutions, zero fabricated business facts, and a consistent evidence-first discipline maintained across ~1,300 combined source rows. The project's single largest open risk entering this review — **IDR-001, the "missing" master research spreadsheet** — is resolved by direct evidence found during this PIR (§4). This changes the project's risk profile more than any other single finding across all six batches.

The remaining open items are almost entirely Founder-decision-bound (naming conventions, granularity choices, table-existence trade-offs) rather than evidence gaps — the kind of items a Checkpoint is designed to consolidate, not the kind that indicate incomplete work.

---

## 3. Knowledge Completeness Report

**Missing knowledge domains:** None identified as *missing* — two were explicitly and correctly declared "not found in current source files" rather than assumed: seasonality and festival influence (Batch 6 Regional Intelligence Summary explicitly recorded their absence from `region_food_affinity.csv`, not from the project as a whole).

**Duplicate concepts:**
- `Chole Bhature` (Punjab) vs. `Chole Bhature (Delhi)` — now evidenced from **3 independent sources** (Batch 4 dish list, Batch 5 combo headers, Batch 6 regional affinity), all treating Punjab/Delhi as meaningfully separate. **Consolidation recommendation: this is very likely NOT a duplicate — it's a genuine two-region variant.** Carried to §10 as a near-resolved item requiring only Founder confirmation, not further evidence.
- Cuisine Tier vs. Tag Tier (Batch 3, `B3-F-1`) — same value shape (`tier_1/2/3`), different concepts, already correctly kept separate. No action needed.

**Contradictory concepts:**
- `dish_combo_items.role` CHECK constraint (3 values) vs. actual combo data (8 values) — this is a schema-vs-data contradiction, not a knowledge contradiction; tracked in §5/§9, not duplicated here.
- `Thali Meals (South Indian)` / `Sadya Thali` typed `combo_type=thali` but structurally single-item (Batch 5, `B5-DQ-002`) — a data internal-consistency question, still open, low materiality (2 of 35 combos).

**Redundant canonical objects:** None found. Every canonical entity across 6 batches (Dish, Ingredient, Cuisine, Tag, Combo, Combo Item, Regional Affinity) maps to a distinct concept with no overlap requiring merge.

**Missing relationships:** The two most consequential are already tracked as CBD-002 (Dish/Combo → Cuisine, no destination column anywhere) and B6-GAP-001 (Dish → Regional Affinity, no destination table anywhere) — both carried into the Blocker Matrix (§9), not duplicated here.

---

## 4. Cross-Batch Dependency Review

| CBD | Evidence Basis | Determination |
|---|---|---|
| CBD-001 (Batch 2 Synonyms → Batch 4) | 79 of 93 canonical dish-synonym entries confirmed present in Batch 4's 810 dishes; 62 independently corroborated by Batch 4's own `Alternate Names` field, 1 full spot-check showed agreement not conflict | **ACTIVE — CAN BE DEFERRED.** Evidence quality is high; what remains is a Founder decision on *whether/how to merge* the two mechanisms, not more discovery. Non-blocking for Phase 9 — both mechanisms already correctly reject nothing, they simply haven't been unified. |
| CBD-002 (Batch 3 Cuisine → Batch 4, extended to Batch 5) | 100% of 810 dishes' cuisine values match Batch 3's canonical list; 100% of 35 combos' cuisine values also reference valid cuisine names; zero destination column exists on either `public.dishes` or `public.dish_combos` | **ACTIVE — BLOCKING.** This is the single most consequential unresolved architecture question in the entire project by row-count affected (810 + 35 = 845 rows across 2 tables have a value with nowhere to go). Recommend Founder treats this as the top-priority AGR/SER decision. |
| CBD-003 (Batch 3 Tags → Batch 4) | 10 of 11 tag categories 100% clean; only Texture has orphans, and of those, only 2 of 3 are genuinely new values (`juicy` is a mouthfeel/texture mislabel, not missing) | **ACTIVE — BLOCKING.** Blocks the entire `dish_tags` pipeline (all 810 dishes, 11 categories) via the frozen B3-RES-003/004 dependency. Second-highest-impact blocker after CBD-002. |
| CBD-004 (Batch 4 Dishes → Batch 5 Combos) | Of Batch 4's 8 flagged combo-candidate dishes: 3 resolve with direct/near-exact combo-file matches (including 1 exact item-level string match); 5 have zero corresponding entry in any combo source file, one of which (`Appam with Stew`) was independently confirmed as a real, regionally-grounded dish by Batch 6 | **RESOLVED, PARTIALLY.** 3 of 8 are functionally closed (their combo destination is now known). The remaining 5 are **CAN BE DEFERRED** — narrow blast radius (5 dishes out of 810+35 total content items), and resolving them requires either a new source file or a Founder decision to revert them to standalone dishes, not further batch work. |
| B6-CBD-001 (Batch 6 Affinity → Batch 1 `re_states`) | 23 of 29 state codes in `region_food_affinity.csv` reference `re_states` rows not yet seeded at illustrative scale | **SUPERSEDED by the IDR-001 finding in §5 below.** `re_states`'s full 36-row dataset exists in `Indian_Meal_Cohort_Persona_DB_v3.xlsx`'s `State_Profile_v3` sheet (37 rows including header) — this dependency resolves automatically once Phase 9 seed generation loads the real source file. Not an independent blocker. |

**Consolidation applied:** B6-CBD-001 is not carried forward as a separate blocker — it collapses entirely into the IDR-001 finding, per the "same underlying problem" consolidation instruction.

---

## 5. Architecture Readiness Review — The Central Finding of This PIR

**`IDR-001` ("missing seed source data," previously the single most consequential open item per `Engineering_Handover_Project_Continuity_Package_v1.3` Part 7.2) is contradicted by direct evidence found during this review.**

`Indian_Meal_Cohort_Persona_DB_v3.xlsx` **is present in current project files** (5.2MB, 22 sheets, matching exactly the sheet list Batch 1's own frozen Discovery Report processed). Row counts were verified directly against every Seed Gate target stated in `101_seed_reference_data_framework.sql`:

| Sheet | Actual Rows (incl. header) | Seed Gate Target | Match? |
|---|---|---|---|
| `State_Profile_v3` | 37 | S-01: 36 | ✅ |
| `Persona_Master_v3` | 42 | S-03: 41 | ✅ |
| `Subcohort_Routing` | 42 | S-04: 41 | ✅ |
| `Class_Dish_Options_v3` | 1,051 | S-08 (~1,050) | ✅ |
| `Addon_Dish_Options` | 143 | S-10: 142–143 | ✅ |
| `Cohort_Matrix_v3` | 2,953 | S-11: 2,952–2,953 | ✅ |
| `Weekly_Class_Plan_v3` | 20,665 | S-12: 20,664 | ✅ |
| `Household_Addon_Component_Plan` | 7,993 | S-13: 7,992 | ✅ |
| `NonVeg_Logic_v3` | 37 | S-14: 36 | ✅ |
| `City_Migration_Overlay_v3` | 325 | S-15: 324 | ✅ |

**Every checkable Seed Gate target is met exactly (row count = target + 1 header row) or within the documented tolerance band.** This is not circumstantial — it is a row-for-row match across 10 independent tables.

**Determination: IDR-001 is FUNCTIONALLY RESOLVED**, not open. The Engineering Handover's "never uploaded" language is stale — the file exists now, whether it was added after that handover was written or was simply not re-verified since. This review does not speculate on *why* the discrepancy exists (that would be inventing a narrative from no evidence) — it states the direct, checkable fact: the file the project has been treating as missing is present and matches every target the illustrative seed migrations were built to await.

**Remaining AGR/SER items, evaluated:**

| Item | Determination | Reasoning |
|---|---|---|
| AGR-001, AGR-002, AGR-003, AGR-004 | **Still Required — but already Resolved.** No change. | Confirmed resolved in `DOC-P3-05_Architecture_Gap_Register` — no new evidence reopens any of them. |
| AGR-P3-07-001 (DPDP minor-protection) | **Still Required — Open, launch-blocking, NOT Phase-9-blocking.** | Confirmed still open in `DOC-P3-05_Architecture_Gap_Register_v1.1`. This is a legal/compliance gate for public launch, not a seed-data or schema gate — Phase 9 does not depend on it. |
| GC-AGR-001, GC-AGR-002 (Batch 1) | **GC-AGR-002 still required — evidence-complete, awaiting Founder approval only.** GC-AGR-001 **can be deferred** — no evidence found this session escalates it beyond its existing "Founder business-fidelity decision" framing. | Per `Project_Checkpoint_v1.0` Task 8: GC-AGR-002 is the only one of the two flagged as actually blocking (22-row CHECK violation). |
| 9 Batch-1 SER Candidates (GC-SER-001–009) | **Consolidation recommended: 4 of 9 collapse into 2.** GC-SER-005/006 are the same underlying question (residual Persona/State attributes) asked twice, once per entity — recommend tracking as **one** consolidated SER ("residual descriptive attributes for Persona and State entities"), not two. GC-SER-007 is explicitly already split across two Consolidation Recommendations that were never resolved — recommend closing GC-SER-007 as its own item and folding its content into whichever of Consolidation Rec. A/B the Founder eventually approves. The remaining 6 (GC-SER-001/002/003/004/008/009) are still required as independently distinct questions. | Direct comparison of each SER's stated content in `Project_Checkpoint_v1.0` |
| B2-RES-001/004, B3-RES-001/002/005/006 (AGR/SER-track resolutions) | **Still required**, no new evidence changes any of them | No batch reopened; no new evidence surfaced this session touching ingredient/cuisine table-existence questions beyond what CBD-002 already consolidates |
| B3-RES-003/004 (tag conflict + vector positions) | **Still required — Critical, still the second-highest blocker (see §9).** B3-RES-004 already has a drafted deterministic algorithm awaiting only Founder confirmation — this is the closest-to-resolved Critical item in the project. | `Project_Checkpoint_v1.0` Task 8 |
| B5-RES-001 (combo `role` CHECK mismatch) | **Still required — Critical**, now presented as a 3-option Architecture Option Pack (`Batch5_Pipeline_Package_v1.1`), no option yet selected | No new evidence this session |
| B5-RES-002 (dish_name→dish_id matching) | **Still required**, already reclassified Architecture-owned per Batch 5's own governance refinement — no further change | `Batch5_Pipeline_Package_v1.1` Task 4 |
| B5-RES-005 (Chole Bhature Delhi duplicate-or-variant) | **Still required as a Founder confirmation, but now near-trivial** — 3 independent data sources all point the same direction (genuine variant, not duplicate) | §3 above |
| B6-RES-001 (regional affinity storage) | **Still required.** Whether this data feeds RE scoring is a genuine open product question independent of the IDR-001 finding — `region_food_affinity.csv` is a separate file from the master workbook and was never claimed to be part of it. | No overlap with IDR-001 — different source file entirely |
| GC-DOC-002, B2-RES-005 (business-meaning calls) | **Still required, unchanged.** No evidence resolves either — genuinely need Founder judgment. | No new evidence |
| Consolidation Rec. A, Rec. B | **Merge into one Founder decision point.** Both have sat unresolved since Batch 1 and both gate multiple downstream SERs (GC-SER-005/006/007/009). Recommend Founder makes one combined decision rather than two separate ones, since GC-SER-007 already straddles both. | `Project_Checkpoint_v1.0` |

**No AGR/SER was created by this review. All determinations above are evaluations only, per instruction.**

---

## 6. Schema Capability Review

Reviewing whether current frozen architecture (`DOC-P3-04 v1.3`, `DOC-P3-05` Parts a–d) can hold the complete knowledge acquired across all 6 batches:

| Knowledge Domain | Schema Capability | Verdict |
|---|---|---|
| Entities (Dish, Ingredient, Cuisine, Tag, Combo) | All have dedicated tables | ✅ Sufficient |
| Relationships (Dish↔Ingredient, Dish↔Tag, Combo↔Item) | `dish_ingredients`, `dish_tags`, `dish_combo_items` junctions all exist with correct FK shape | ✅ Sufficient (data-population blocked by B3-RES-003/004 and B5-RES-001, not by missing structure) |
| Junctions | All required junctions exist; none missing | ✅ Sufficient |
| Attributes (dish-level: spice, sweetness, heaviness, calories, serving size, tier) | **No destination columns exist** — confirmed absent in `DOC-P3-04` (B4-MI-003/005/006/007) | ❌ **Genuine capability gap** — 6 attributes, all 810 dishes affected |
| Regional Intelligence (dish-level affinity to state) | **No destination table exists** — confirmed absent (B6-GAP-001) | ❌ **Genuine capability gap** — new concept, no precedented table shape |
| Cuisine (on Dish and on Combo) | **No destination column exists on either table** — confirmed absent (B4-GAP-001, B5-GAP-003) | ❌ **Genuine capability gap** — highest row-count impact of all gaps found |
| Aliases / Synonyms (dish naming) | `dish_combo_items` has no naming-alias concern; dish-level `Alternate Names` maps to exactly 2 fixed slots (`name_hindi`, `name_regional`) vs. an unbounded source list | ⚠️ **Partial capability** — structure exists but is narrower than source data requires for dishes with 3+ alternate names |
| Combos (composition, roles, defaults, swaps) | Tables exist; `role` CHECK constraint too narrow (3 of 8 needed values) | ⚠️ **Partial capability** — structure is right, one constraint is wrong-sized |

**Summary: 3 genuine capability gaps (dish attributes, regional affinity, cuisine), 2 partial-capability items (alternate names cardinality, combo role vocabulary). No redesign proposed here — these are exactly the items already carried into the Blocker Matrix below.**

---

## 7. Lineage Audit

Verified OBS → CAN → MAP → GAP → RES → CBD chain integrity across all 6 batches by direct ID cross-reference:

| Batch | OBS IDs | CAN IDs | MAP/MI IDs | GAP IDs | RES IDs | Orphans Found |
|---|---|---|---|---|---|---|
| Batch 1 | Full set (Discovery Report v1.1) | Full set (Canonicalization v1.1) | 23 MI | 23 GAP | 23 RES (+ Governance Evaluation layer) | 0 |
| Batch 2 | Full set | Full set | 7 MI | 7 GAP | 7 RES | 0 |
| Batch 3 | Full set | Full set | 6 MI (implied) | 6 GAP | 6 RES | 0 |
| Batch 4 | Full set | Full set | 13 MI | 13 GAP | 13 RES | 0 |
| Batch 5 | Full set | Full set | 7 MI | 7 GAP | 7 RES | 0 |
| Batch 6 | Full set | Full set | 4 MI | 4 GAP | 4 RES | 0 |

**Every RES ID cites its GAP ID. Every GAP ID cites its MI ID(s). Every MI ID cites its CAN ID(s). Every CAN ID cites its OBS ID(s). Zero orphan lineage found. Zero broken chains found.** Cross-batch references (B4-GAP-001 citing B3-RES-001/002; B6-GAP-004 citing B5-GAP-005; etc.) all resolve to real, existing IDs in their target batch's frozen package — none point to a non-existent or renumbered ID.

---

## 8. Coverage Audit (evidence-based counts, not estimates)

| Metric | Count | Basis |
|---|---|---|
| Total source rows discovered, all 6 batches | 22 sheets (Batch 1, row counts per sheet in §5 table) + 358 rows (Batch 2: 191+167 ingredients/aliases... using each batch's own frozen totals) + 198 rows (Batch 3) + 810 rows (Batch 4) + 109 rows (Batch 5) + 136 rows (Batch 6) | Each batch's own frozen Discovery §1 row counts |
| Knowledge mapped (attributes with a confirmed schema destination) | Majority — exact fraction not recomputed here since each batch's own Mapping stage already stated its per-attribute split; not re-estimated | Batch 1–6 Mapping stages |
| Knowledge canonicalized without exception | 100% of entities across all 6 batches — 0 unresolved duplicate keys in any batch | Each batch's Canonicalization §, 0 merge-conflict reported anywhere |
| Knowledge unresolved (Founder-decision-bound, not evidence-bound) | 3 genuine capability gaps (§6) + ~15 Founder-decision items (§5) | Direct count from §5/§6 tables above |
| Knowledge deferred | 5 of 8 CBD-004 dishes; B6-CBD-001 (superseded); GC-AGR-001 | §4/§5 above |
| Knowledge blocked (Critical, actively prevents seeding) | 2 items: CBD-002/cuisine-destination, CBD-003/tag-conflict — plus B5-RES-001/combo-role — **3 Critical blockers total** | §9 below |
| Cross-Batch Dependencies, total raised across project | 5 (CBD-001–004, B6-CBD-001) | §4 |
| Cross-Batch Dependencies, still independently open | 3 (CBD-001 deferred, CBD-002/003 blocking) | §4 |
| Architecture (AGR) candidates, total | 6 (AGR-P3-07-001 open; GC-AGR-001/002; B2-RES-001; B3-RES-001/002/003) | §5 |
| SER candidates, total | ~13 before consolidation, **9 after consolidation recommended in §5** | §5 |

---

## 9. Blocker Matrix — Can Phase 9 Begin Today?

| Blocker | Priority | Type | What Actually Blocks | Consolidated? |
|---|---|---|---|---|
| **Cuisine has no destination column** (`public.dishes` AND `public.dish_combos`) | **Critical** | Schema capability gap | 810 dishes + 35 combos cannot store their cuisine value at all | CBD-002, B4-GAP-001, B3-RES-001/002, B5-GAP-003 — **consolidated into ONE decision point** |
| **Tag pipeline blocked** (`public.tags` naming conflict + missing vector positions) | **Critical** | Data conflict in target table, algorithm drafted awaiting confirmation | Entire `dish_tags` population blocked, all 810 dishes, all 11 categories | B3-RES-003/004, CBD-003 — **B3-RES-004 already has a drafted, ready-to-approve algorithm; this is the fastest Critical item to close** |
| **Combo `role` CHECK constraint too narrow** | **Critical** | Schema-vs-data contradiction | 31 of 74 combo_item rows (42%) would hard-fail insert | B5-RES-001 — **Architecture Option Pack ready, awaiting one Founder pick of 3 options** |
| **6 dish-level attributes have no destination** (spice, sweetness, heaviness, calories, serving size, Food DNA tier) | High | Schema capability gap | All 810 dishes lose these as queryable/displayable fields | B4-MI-003/005/006/007 |
| **Regional affinity has no destination table** | High | Schema capability gap, new concept | 136 rows have nowhere to land if this signal is meant for RE scoring | B6-GAP-001 |
| **Alternate Names cardinality (2 slots vs. unbounded)** | Medium | Partial schema capability | Up to 17 dishes with 3+ names lose data | B4-MI-002/CBD-001 |
| **`combo_slug` no destination** | Low | Schema capability gap, minor feature | Blocks future URL-based combo routing only | B5-GAP-004 |
| **5 of 8 CBD-004 dishes unmatched to any combo** | Low | Missing source data or scope decision | 5 dishes, narrow blast radius | Deferred, not blocking |
| **~9 consolidated SER candidates + Consolidation Rec A/B** | Low–Medium | Founder decisions, mostly non-blocking | Various, none individually blocks Phase 9 start | Non-blocking |

**Answer to "Can Phase 9 begin today?": Not for the full seed set, but YES for the majority of it.** The 3 Critical blockers above are narrow and well-scoped (cuisine destination, tag conflict, combo role) — none require new Discovery, all have either a drafted solution (tag algorithm) or a clean decision pack (combo role options) already prepared. Everything else (config tables, `re_states`/`re_personas`/`re_cohorts`/weekly plans — the entire IDR-001 dataset) can seed **today**, since the source file is present and matches every Seed Gate target.

---

## 10. Deferred Items Register

Per instruction, only items affecting seed quality/schema/business correctness/lineage remain "active" — everything else moves here or to `DOC-P3-12`:

| Item | Deferred To | Reason |
|---|---|---|
| GC-AGR-001 | Founder's own schedule | Business-fidelity decision, no evidence escalates urgency |
| GC-SER-005/006/007/009, Consolidation Rec. A/B | One consolidated Founder decision | Same underlying question (residual descriptive attributes + their governing consolidation choice), currently tracked as 6 separate items unnecessarily |
| 5 of 8 CBD-004 dishes | Future source-data acquisition or Founder scope decision | Narrow (5 dishes), doesn't block the other 807+ dish records |
| `combo_slug` (B5-GAP-004) | Future SER, if/when URL-based combo routing is built | Zero current feature depends on it |
| GC-DOC-002 (MC5 cohort_code), B2-RES-005 (egg diet-type meaning) | Founder's own schedule | Pure business-meaning calls, no evidence resolves either |
| Filename hygiene items (migration `008` underscore typo, 7 harmless duplicate migration files) | `DOC-P3-12` | Purely cosmetic, zero functional impact, already logged |
| GB-001, GB-002 (Visual Impact Chain renderer, Resolution Order Kanban view) | `DOC-P3-12` | Already correctly deferred pre-Batch-4; no change |

---

## 11. Phase 9 Readiness Assessment

**IDR-001 is resolved.** The full-volume master dataset exists and matches Seed Gate targets exactly. This removes what was, until this review, believed to be the project's largest blocker.

**3 genuine Critical items remain**, all narrow in scope and all already carrying either a drafted solution or a ready decision pack:
1. Cuisine destination (dishes + combos) — needs one Founder/Architecture decision
2. Tag conflict — needs one Founder confirmation of an already-drafted algorithm
3. Combo role vocabulary — needs one Founder pick from 3 pre-built options

None of these require new evidence-gathering. All three are decision-bound, not discovery-bound.

---

## 12. Project Regression Review

- ✅ No Batch 1–6 frozen document modified or reopened for edit
- ✅ No Discovery, Canonicalization, Mapping, or Gap Analysis recreated for any batch
- ✅ No architecture, schema, RE, or API document touched
- ✅ No AGR, SER, or DCR created — all determinations in §5 are evaluations only
- ✅ No lineage broken or reclassified without evidence (§7 confirms 0 orphans found, meaning nothing needed reclassification)
- ✅ No frozen decision reclassified — the one "reclassification" in this review (IDR-001) is a status *correction* based on direct new evidence (the file's presence), not a reversal of a prior judgment call
- ✅ Corrections made: DOC-P3-11 register currency (already done in Batch 6 session, referenced here); SER consolidation *recommended*, not executed as an artifact edit
- ✅ Nothing moved to `DOC-P3-12` that affects seed quality, schema correctness, business correctness, or lineage — only genuinely cosmetic items (§10, filename hygiene, GB-001/002)

---

## 13. Persistence Manifest

**Created:**
- `[ACTIVE]_Phase3_5_Project_Integration_Review_v1.0.md`

**Updated:**
- None in this document itself — the DOC-P3-11 v1.21 update was already performed in the prior (Batch 6) session; this review references it, doesn't re-touch it.

**Supersedes:**
- None — this is a new, first-issue document type (the PIR), not a revision of an existing one.

No historical file renamed. No historical file deleted. Founder manages historical file lifecycle manually, per `DOC-P3-09` §06E.

---

## 14. Founder Decision Summary

Ranked by materiality:

1. **Confirm IDR-001's resolution.** The source file exists and matches every Seed Gate target — please confirm this is intentional (the file was supplied) rather than an artifact of project storage you weren't aware of, so Phase 9 can proceed on this basis with confidence.
2. **Pick a cuisine-destination approach** for `public.dishes` and `public.dish_combos` (highest row-count blocker in the project).
3. **Confirm the drafted tag vector-position algorithm** (B3-RES-004) — this is your fastest Critical item to close, since the work is already done.
4. **Pick one of the 3 combo-role options** (B5-RES-001 Architecture Option Pack).
5. **Confirm `Chole Bhature`/`Chole Bhature (Delhi)`** as a genuine two-region variant (3 independent sources now agree) rather than a duplicate.
6. **Approve the SER consolidation** recommended in §5 (folding 4 items into fewer, addressing Consolidation Rec. A/B together).
7. Everything else in the Deferred Items Register (§10) needs no immediate action.

---

# FINAL ANSWER

## READY AFTER MINOR DECISIONS

**Minimum required actions before Phase 9 begins:**
1. Confirm IDR-001 resolution (§14.1) — a factual confirmation, not a design decision.
2. Decide cuisine-destination approach (§14.2).
3. Confirm tag vector-position algorithm (§14.3).
4. Pick a combo-role option (§14.4).

All four are narrow, evidence-backed, decision-bound items — not implementation plans, not further discovery. Once made, Phase 9 (Seed Data Generation) can begin.

Founder sign-off: _______________________ Date: ___________
