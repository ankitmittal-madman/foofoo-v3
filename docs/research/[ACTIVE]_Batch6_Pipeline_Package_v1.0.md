# [ACTIVE]_Batch6_Pipeline_Package_v1.0

**Phase 3.5 — Batch 6 (Regional Intelligence) — Stages 1–5, executed continuously per High-Velocity instruction**
**Asset:** `region_food_affinity.csv` (136 rows, 8 columns)
**Framing:** Regional Intelligence — regional behavior, food availability, migration, state/city hierarchy, seasonality, cuisine influence, diet adaptation. Not merely regional data. Enriches, does not reopen, prior batches.
**Date:** 2026-07-03 · **Status:** Draft — Ready for Founder Review

---

# 0. Baseline Verification

Reconstructed directly from project files, not chat memory:

| Item | Verified State | Source |
|---|---|---|
| Phase 3 | COMPLETE / APPROVED / FROZEN | `Project_Baseline_Register_v1.5` Step 10 |
| Batch 1 | COMPLETE / FROZEN | `Batch1_GapAnalysis_Package_v1.1` |
| Batch 2 | COMPLETE / FROZEN | `Batch2_Resolution_Package_v1.0` |
| Batch 3 | COMPLETE / FROZEN | `Project_Checkpoint_v1.0` Task 7 |
| Batch 4 | COMPLETE / FROZEN | `Batch4_Technical_Review_and_Freeze_Recommendation_v1.0` §11 |
| Batch 5 | COMPLETE / FROZEN (v1.1) | `Batch5_Pipeline_Package_v1.1` Task 6 |
| Duplicate ACTIVE documents | None new — 3 previously-adjudicated stale-copy pairs remain (`DOC-P3-09`, `Project_Baseline_Register`, `Engineering_Handover...`), all already logged, not new conflicts | Direct file listing this session |
| `DOC-P3-11` currency | **Gap found**: still at v1.20, register shows Batch 4 as "pipeline complete, closure not declared" and does not reflect Batch 5 at all. Both freezes are real, documented artifacts — the register is simply stale. Corrected in this execution (§9 below), per this session's own instruction to update DOC-P3-11 in the same pass. | `DOC-P3-11_Discovery_Execution_Register_v1.20` §05 |

No frozen document reopened. Batch 6 proceeds on the basis that Batches 1–5 are genuinely frozen (confirmed via their own freeze artifacts), independent of the register lag.

---

# 1. Batch 6 Discovery

## Source Inventory
| File | Rows | Columns | Confidence |
|---|---|---|---|
| `region_food_affinity.csv` | 136 | 8 | High (100%) |

**136 rows, fully read — no sampling.**

## Entities Observed
| ID | Entity | Key | Rows | Confidence |
|---|---|---|---|---|
| B6-OBS-ENT-001 | Regional Food Affinity (state–dish pairing with strength score) | `(state_code, dish_name)` | 136 (0 exact duplicate keys) | High |

## Relationships Observed
| ID | Relationship | Result | Confidence |
|---|---|---|---|
| B6-OBS-REL-001 | Affinity → State (`state_code`) | 29 distinct state codes; **6 of 29 match Batch 1's currently-seeded `re_states` illustrative subset** (MP, MH, TN, WB, PB, KA — all 6 seeded states are covered); the remaining 23 codes reference states not yet seeded in `re_states` (which is itself only 6-of-36 illustrative per Batch 1's disclosed, intentional incompleteness — not a Batch 6 defect) | High |
| B6-OBS-REL-002 | Affinity → Dish (`dish_name`) | Not independently joined against Batch 4's frozen 810-dish list within this pass (Batch 4 is frozen, not reopened) — **recorded as an open cross-batch relationship**, strengthened by spot-evidence below, not exhaustively resolved | Medium |
| B6-OBS-REL-003 | Affinity dish names ↔ Batch 4's 8 combo-candidate dishes (CBD-004) / Batch 5's unresolved 5 | **Direct hit: `Appam with Stew` appears verbatim in `region_food_affinity.csv`** (state not yet checked against final value — see Canonicalization) — this is one of the 5 dishes Batch 5 found with **no** combo-file match at all (`B5-MI-007`). Regional data does not resolve the combo question, but it confirms `Appam with Stew` is a real, named dish with regional grounding, not a data artifact. | High — exact string match |
| B6-OBS-REL-004 | Affinity dish names ↔ `dish_combos_v2.csv` combo names | Additional overlaps found: `Chole Bhature`, `Sarson Ka Saag` (component of `Sarson Ka Saag Makki Ki Roti`), `Dal Baati` (component of `Dal Baati Churma`), `Bedmi Puri` (component of `Bedmi Puri Aloo`), `Banarasi Chaat` — confirms these dishes/components carry independently-sourced regional identity consistent with their combo/cuisine assignments, not contradicting them | High |
| B6-OBS-REL-005 | Affinity → Cuisine (indirect, via state) | Not directly joined — `region_food_affinity.csv` has no `cuisine` column; any state↔cuisine relationship would route through Batch 3's `cuisines_v4.state_origin` field, itself already flagged Low-confidence/partial in Batch 3 (`B3-OBS-REL-003`) — this batch does not attempt to resolve that pre-existing weak relationship, only notes it as the natural join path | Medium |

## Vocabularies / Value Ranges Observed
| ID | Finding |
|---|---|
| B6-OBS-VOC-001 | `state_code`: 29 distinct 2-letter codes, all valid ISO 3166-2:IN state/UT codes (verified — 0 typos or invalid codes found) |
| B6-OBS-VOC-002 | `affinity_score`: continuous, range 0.80–0.95, 136 populated values, 0 nulls |
| B6-OBS-VOC-003 | `source`: single value, `regional`, 136/136 — no alternate sourcing method observed in this file |
| B6-OBS-VOC-004 | `is_active`/`is_updated`/`is_review`: uniform Y/N/N across all 136 rows — no patch-event signature (unlike Batch 2–4's mixed `is_updated` values), suggesting this file was authored in a single pass, not iteratively revised |

## Business Rules Observed
| ID | Rule | Evidence | Exceptions |
|---|---|---|---|
| B6-OBS-RULE-001 | **Affinity score range is bounded [0.80, 0.95]** — no low-affinity or negative/exclusionary scores exist in this file | Full-column min/max computation | 0 — every row represents a positive/strong regional association, never a weak or excluded one; this file appears to encode "strong regional signature" dishes only, not a full affinity spectrum |
| B6-OBS-RULE-002 | **One dish can carry affinity to more than one state** (multi-region applicability) | 2 confirmed cases: `Chole Bhature` (PB 0.85, DL 0.95), `Litti Chokha` (BR 0.95, JH 0.85) | 2 of 136 rows (1.5%) — genuinely rare, not the norm |
| B6-OBS-RULE-003 | **Multi-region dishes have differentiated, non-identical scores per state** — never the same score duplicated across states | Both B6-OBS-RULE-002 cases show distinct scores (0.85 vs 0.95 in both pairs) | 0 exceptions in the 2 observed cases |
| B6-OBS-RULE-004 | **No dish appears under a state code outside the standard 29-state footprint of this file** — internal consistency | Full cross-tabulation | 0 exceptions |

## Data Quality Findings
| ID | Finding | Detail | Severity |
|---|---|---|---|
| B6-DQ-001 | 8 states/UTs from the full India list have zero rows in this file (`AN`, `CH`, `DD`, `DN`, `HR`, `LA`, `LD`, `PY`) | Mostly small Union Territories, plus Haryana (a populous state) notably absent | Medium — Haryana's absence is more consequential than the UTs, given its size; recorded as evidence, not resolved |
| B6-DQ-002 | `Chole Bhature` multi-region case (B6-OBS-RULE-002) directly parallels Batch 5's own internal finding (`B5-DQ-001`: `Chole Bhature` vs. `Chole Bhature (Delhi)` as separate combo headers, the latter with zero items) | Three independent sources (Batch 4 dishes, Batch 5 combos, Batch 6 regional affinity) all treat Punjab and Delhi as separately meaningful for this exact dish — this cross-batch convergence is itself evidence that the Punjab/Delhi split is a real, intentional distinction in the source data, not an accident | **High — strengthens rather than resolves B5-GAP-005/B5-RES-005; the Founder's open question ("is `Chole Bhature (Delhi)` a duplicate or genuine variant?") now has 3 independent data points all pointing toward "genuine variant," though this batch does not decide that question** |
| B6-DQ-003 | No `cuisine` column exists in this file at all | Same recurring architectural absence already identified for `public.dishes` (B4-GAP-001) and `public.dish_combos` (B5-GAP-003) — this file simply doesn't attempt the join, consistent with those known gaps | Informational — not a new defect, a third data point on an already-known question |
| B6-DQ-004 | `Appam with Stew` present here with no combo-file counterpart (B6-OBS-REL-003) | Directly relevant to CBD-004's unresolved 5 dishes from Batch 5 | High — see Cross-Batch Integration Summary §8 |

## Discovery Readiness Summary
136 rows, 1 entity, 5 relationships, 4 vocabularies, 4 business rules, 4 data quality findings — all at 100%, no sampling. Ready for Canonicalization.

---

# 2. Batch 6 Canonicalization

## Canonical Entity Dictionary
| ID | Entity | Rows | Confidence |
|---|---|---|---|
| B6-CAN-ENT-001 | Regional Food Affinity | 136 (134 single-state dishes + 2 multi-state dishes represented as 2 rows each) | High |

**0 merges required.** The 2 multi-region dishes are retained as 2 distinct rows each (not merged into one dish-level record with multiple states packed in), consistent with the source file's own row-per-(state,dish) granularity — canonicalization respects the source shape rather than restructuring it.

## Canonical Relationship Dictionary
- B6-CAN-REL-001 (Affinity → State): canonicalized as observed; 6-of-29 currently resolvable against seeded `re_states`, 23-of-29 pending `re_states`' own future full seeding (a Batch 1 scope item, not reopened here)
- B6-CAN-REL-002 (Affinity → Dish, cross-batch to Batch 4): canonicalized as an **open cross-batch relationship**, strengthened by direct spot-evidence (B6-OBS-REL-003/004), not exhaustively joined
- B6-CAN-REL-003 (Affinity → Cuisine, indirect via Batch 3): canonicalized as an **open, weak cross-batch relationship**, inheriting Batch 3's own already-disclosed Low-confidence finding on `state_origin`

## Canonical Business Rules
B6-CAN-RULE-001 through 004 promoted directly from Discovery — B6-CAN-RULE-002/003 (multi-region applicability) carry their small sample size (n=2) forward explicitly, not overstated as a general pattern.

## Confidence
High (100%) on structure and the 136-row entity set. Medium on both cross-batch relationships (Dish, Cuisine) since neither Batch 4 nor Batch 3 was reopened to perform an exhaustive join. The state-coverage gap (23 of 29 codes referencing not-yet-seeded `re_states` rows) and the 2 multi-region cases are the only non-trivial canonicalization items, all fully evidenced.

---

# 3. Batch 6 Mapping

## Baseline Confirmation
`re_engine.re_states` DDL confirmed (`002_reference_tier0.sql`): 3 columns (`state_code` PK, `state_name`, `region`), Seed Gate S-01 target 36 rows, currently 6 illustrative rows seeded. **No table in frozen architecture is named for "regional food affinity" specifically** — this is the first Mapping-stage question this batch raises.

## Attribute Mapping Matrix

**Mapped, Partially Blocked:**
- `state_code` → `re_engine.re_states.state_code` (FK target exists, but only 6 of 29 referenced codes currently have a matching seeded row — 23 would fail FK insertion today, though this is a Batch 1 seed-completeness issue, not a Batch 6 architecture gap)

**Not Mapped — No Destination Exists:**
- `dish_name` — no destination column identified; if this data is meant to influence RE scoring (as its filename and content strongly suggest — "affinity" is exactly the kind of signal `RE-DOC-02`'s ContentMatch layer would consume), there is no `re_*` table shaped to hold a per-dish, per-state weighting value
- `affinity_score` — same absence, no destination
- `source` — annotation-shaped, consistent with every prior batch's `Source` column pattern; likely Not Applicable rather than a gap, but flagged rather than assumed

**Not Applicable, by design:** `is_active`/`is_updated`/`last_update_date`/`is_review` (annotation/computational, same pattern as every prior batch).

## Mapping Issues (4 raised)

| MAP ID | Attribute(s) | Issue | Confidence |
|---|---|---|---|
| B6-MI-001 | Entire `region_food_affinity` concept (`dish_name` + `affinity_score` as a pair) | **No table anywhere in frozen architecture (`DOC-P3-04 v1.3`) is shaped to hold a per-dish, per-state affinity weight.** The closest existing structures are `re_engine.re_city_migration_overlays.city_overlay_weight` (a single real-valued weight, but scoped to city-migration context, not dish-level) and `dish_tags.confidence` (a real-valued weight, but scoped to tag confidence, not regional affinity). Neither is a direct match. | High |
| B6-MI-002 | `state_code` (23 of 29 codes) | These 23 codes have no matching row in the currently-seeded `re_states` table — but this is because `re_states` itself is only 6-of-36 seeded by explicit, disclosed design (`101_seed_reference_data_framework.sql`'s own comment: "AWAITING SOURCE DATA: 30 remaining states/UTs"), not because Batch 6's data is wrong | Medium — the *fact* is high-confidence, but whether it constitutes a "gap" at all is genuinely ambiguous, since the destination table's own incompleteness is pre-existing and disclosed |
| B6-MI-003 | Haryana (`HR`) and 7 UTs entirely absent from source data (B6-DQ-001) | Not a mapping problem in the technical sense — there is no HR row to map — but material to any future completeness assessment of regional coverage | Low |
| B6-MI-004 | `Chole Bhature (Delhi)` / `Chole Bhature` split (B6-DQ-002) | Not an independent new gap — this is the same open question as `B5-GAP-005`/`B5-RES-005`, now carrying a third source's worth of corroborating evidence | High — strengthens, does not duplicate |

## Gap Readiness Summary
All 4 issues evidence-complete. Ready for Gap Analysis.

---

# 4. Batch 6 Gap Analysis

| GAP ID | Origin | Category | Reasoning | Priority | Owner |
|---|---|---|---|---|---|
| B6-GAP-001 | B6-MI-001 (no destination table for regional affinity) | **C3 — canonical information has no persistence location in frozen schema** | The concept (dish-level regional weighting) is plausible and directly relevant to `RE-DOC-02`'s ContentMatch layer, but no existing table — not `re_city_migration_overlays`, not `dish_tags` — is shaped to hold it without either overloading an unrelated table's meaning or adding a new one | **High** — if this data is meant to feed RE scoring at all, its absence is a real content-input gap, not cosmetic | Founder→Arch |
| B6-GAP-002 | B6-MI-002 (23 unseeded state codes) | B — architecture supports it (FK structure is correct), data (in the *target* table) is incomplete | `re_states` is disclosed-incomplete by Batch 1's own design; Batch 6 doesn't introduce a new architectural question, it just becomes the first batch whose *own* data depends on that pre-existing incompleteness being resolved | Medium — blocks nothing right now (Batch 6 doesn't need to seed *into* `re_states`), but will block Batch 6's own FK-dependent inserts whenever seed generation is attempted | Founder (source data — same open item as GC-DOC-002/Batch 1's residual state attributes) |
| B6-GAP-003 | B6-MI-003 (Haryana + UTs absent) | Not a schema or mapping gap — a source-data coverage observation | N/A — recorded for completeness, not classified as an architecture/mapping issue | Low | Product/Content |
| B6-GAP-004 | B6-MI-004 (Chole Bhature Delhi corroboration) | **Not independent — inherits B5-GAP-005/B5-RES-005 entirely** | Three sources now agree Punjab/Delhi are meaningfully distinct for this dish; this strengthens the existing open Founder question, it does not create a new one | High (tracked jointly with B5-GAP-005) | Founder |

**Category tally: 1×C3 (independent), 1×B, 1×N/A (informational), 1×inherited/joint. 0×A, 0×C1, 0×C2.**

## Impact Summary
| Gap ID | Business Impact | Seed Impact | Cross-Batch Impact |
|---|---|---|---|
| B6-GAP-001 | If regional affinity is meant to influence recommendations (plausible given RE-DOC-02's ContentMatch design), its absence means the RE cannot use this signal at all until a destination exists | All 136 rows | New — first batch to raise this specific table-shape question |
| B6-GAP-002 | No immediate business impact (Batch 6 doesn't insert into `re_states`) | Blocks Batch 6's own future FK-dependent seed inserts for 23 of 29 state codes, whenever seed generation is attempted | Inherits Batch 1's disclosed `re_states` incompleteness — does not reopen it |
| B6-GAP-003 | Regional coverage gap for Haryana specifically (a large state) may be noticeable if surfaced to users before addressed | 0 rows affected (nothing to seed that doesn't exist) | None |
| B6-GAP-004 | Reinforces the open Chole Bhature/Delhi Founder decision with a third data point | 0 additional rows (already counted under B5-GAP-005) | Strengthens B5-GAP-005/CBD chain |

## Regression Review (Gap Analysis)
No AGR/SER/DCR recommended. No schema change proposed. No Batch 1–5 frozen document reopened — B6-GAP-002/004 explicitly reference but do not modify Batch 1/Batch 5's frozen packages.

## Resolution Readiness Summary
4 of 4 ready. B6-GAP-004 tracked jointly with B5-GAP-005, not as an independent new decision.

---

# 5. Batch 6 Resolution

| RES ID | GAP ID | Path | Order | Owner |
|---|---|---|---|---|
| B6-RES-001 | B6-GAP-001 | Founder/Architecture Decision — confirm whether dish-level regional affinity is intended to feed RE scoring; if yes, this becomes an SER Candidate (new table, shape TBD — not designed here, no option selected, no schema proposed) | Parallel | Founder→Arch |
| B6-RES-002 | B6-GAP-002 | Founder Decision — same open item as Batch 1's residual `re_states` completeness question (GC-DOC-002 lineage); no new decision required beyond what's already pending | Future Batch Dependency (resolves when `re_states` is fully seeded) | Founder |
| B6-RES-003 | B6-GAP-003 | No action required — informational; may inform future source-data acquisition if Haryana/UT coverage is later deemed necessary | N/A | Product/Content |
| B6-RES-004 | B6-GAP-004 | **Inherits B5-RES-005 entirely** — not independently resolved; this session adds corroborating evidence to that existing open Founder question, nothing more | Joint with Batch 5 | Founder |

---

# 6. Regional Intelligence Summary

**Regional behavior:** The file encodes only strong, positive regional associations (0.80–0.95 range) — it is a "signature dish" list per state, not a full preference spectrum including weak or negative associations. This shapes what the data can and cannot be used for: it identifies a state's characteristic dishes, not a complete regional taste profile.

**State/city hierarchy:** No city-level granularity exists in this file at all — everything is state-level. This is a genuine structural boundary: city-level regional nuance (e.g., `Bhutte Ka Kees (Indori)`, `Banarasi Chaat` — both named after specific cities, not states) is captured only in the *dish name itself*, not as a queryable city attribute. This is worth flagging: the data has implicit city-level signal trapped in text that a state-only schema can't structurally exploit.

**Multi-region applicability:** Rare (2 of 136 rows) but real, and in both cases the multi-region dishes carry differentiated (not duplicated) scores — the source data treats "which state associates most strongly" as a real, graded question, not a flat yes/no.

**Migration:** No direct migration-behavior data exists in this file — `re_city_migration_overlays` (Batch 1, frozen architecture) is the correct existing home for migration-pattern logic, and this batch's data doesn't overlap with or extend it.

**Cuisine influence / conflicting cuisine ownership:** The `Chole Bhature` Punjab/Delhi split, corroborated across three independent batches now (Batch 4 dish list, Batch 5 combo headers, Batch 6 regional affinity), is the clearest evidence of "conflicting cuisine ownership" the special review asked about — and it consistently resolves toward "genuinely both are meaningful," not toward one source being wrong.

**Seasonality / festival influence / language variants / diet adaptations:** **None observed.** This file contains no columns or values touching any of these four dimensions. Recorded explicitly as an absence, not silently skipped — the Discovery Focus list asked for evidence on these topics, and the evidence is that this particular source file simply doesn't address them. They may be covered by other project files not yet processed, or may not exist in the project's current source set at all.

---

# 7. Cross-Batch Integration Summary

| CBD / Cross-Batch Item | Status Entering Batch 6 | New Evidence This Session | Status Now |
|---|---|---|---|
| CBD-001 (Batch 2 Synonyms → Batch 4) | Open | Not touched — Batch 6 assets don't bear on dish naming/synonyms | Unchanged — Open |
| CBD-002 (Batch 3 Cuisine → Batch 4) | Open, high urgency | Not directly touched, but B6-OBS-REL-005 confirms the natural join path (state→cuisine) inherits Batch 3's own already-weak `state_origin` relationship — no new strengthening, just confirmation the weakness is real | Unchanged — Open, confirmed still weak |
| CBD-003 (Batch 3 Tags → Batch 4) | Open | Not touched | Unchanged — Open |
| CBD-004 (Batch 4 Dishes → Batch 5 Dish Combos) | Open — 3 of 8 resolved per Batch 5 | **`Appam with Stew` (one of the 5 still-unresolved dishes) confirmed as a real, regionally-grounded dish via B6-OBS-REL-003** — this doesn't resolve the combo question, but it rules out "this might be a data-entry error" as an explanation for why it has no combo match. The dish is real; it simply has no combo definition anywhere in current project files. | **Open — narrowed, not resolved.** The absence of a combo match for `Appam with Stew` is now more clearly a *missing source file* question than a *data quality* question. |
| **New — B6-CBD-001 (Batch 6 Affinity → Batch 1 re_states)** | Did not exist | 23 of 29 state codes in `region_food_affinity.csv` reference `re_states` rows not yet seeded — this is Batch 6 depending on Batch 1's own disclosed-incomplete seed data, not a new architectural finding, but a new formal dependency worth tracking as Batch 1's eventual full seeding now has a second consumer (Batch 6) beyond its original scope | **New — Open** |

**No CBD closed. One new Cross-Batch Dependency raised (B6-CBD-001). CBD-004 narrowed with new evidence, not resolved.**

---

# 8. Regression Review

- ✅ No Batch 1–5 frozen document modified or reopened for edit
- ✅ `Batch4_...`, `Batch5_Pipeline_Package_v1.1`, `101_seed_reference_data_framework.sql` read-only referenced for cross-batch evidence, never altered
- ✅ No architecture, schema, RE, or API document touched
- ✅ No AGR, SER, or DCR actually created — B6-RES-001 identifies an SER *candidate* only, contingent on a Founder confirmation that hasn't happened
- ✅ No SQL, DDL, or migration proposed or run
- ✅ No GAP/RES/CBD ID renumbered, merged, or reused
- ✅ No CBD closed
- ✅ 100% Discovery/Canonicalization/Mapping/Gap Analysis/Resolution — all 136 rows read in full, no sampling
- ✅ No business rule inferred without direct evidence — B6-OBS-RULE-002/003 (multi-region applicability) explicitly stated with their n=2 sample size, not generalized
- ✅ Conflicts found (Chole Bhature multi-region, 23 unseeded states) recorded as evidence only, not resolved, per Special Review instruction

---

# 9. DOC-P3-11 Update (executed in this pass, per instruction)

`DOC-P3-11` is updated from v1.20 to **v1.21** in the same execution, correcting the register to reflect Batch 4's and Batch 5's actual (already-documented) freeze status and adding Batch 6:

**[ACTIVE]_DOC-P3-11_Discovery_Execution_Register_v1.21 — Revision Summary (v1.20 → v1.21):**
1. §05 Discovery Batch Register corrected: Batch 4 status changed from "pipeline complete, closure not yet declared" to **COMPLETE — FROZEN**, citing `Batch4_Technical_Review_and_Freeze_Recommendation_v1.0` §11 as the freeze basis (this register update does not itself freeze Batch 4 — it records a freeze that already happened and was simply never logged here).
2. Batch 5 added to §05 as **COMPLETE — FROZEN**, citing `Batch5_Pipeline_Package_v1.1` Task 6.
3. Batch 6 added to §05 as **Pipeline complete this session (`Batch6_Pipeline_Package_v1.0`) — closure not yet declared**, pending this document's own Founder Approval Gate below.
4. New running-statistics block added for Batch 5 (previously never recorded: 2 source files, 109 rows, 7 gaps, 7 resolutions, 1 ownership reclassification) and Batch 6 (1 file, 136 rows, 4 gaps, 4 resolutions, 1 new CBD).
5. Cumulative Cross-Batch Dependency count updated: 4 (CBD-001–004, inherited) + 1 new (B6-CBD-001) = **5 open**.
6. No other section altered. No renumbering. No frozen batch package reopened.

*(Full replacement text of DOC-P3-11 v1.21 is not reproduced in full here to keep this package lightweight per this session's governance instruction — the revision summary above is authoritative and sufficient to action; a standalone `[ACTIVE]_DOC-P3-11_Discovery_Execution_Register_v1.21.md` should be filed with this content merged into the existing v1.20 structure.)*

---

# 10. Persistence Manifest

**Created:**
- `[ACTIVE]_Batch6_Pipeline_Package_v1.0.md`

**Updated (content specified in §9 above; standalone file to be filed separately per the note there):**
- `[ACTIVE]_DOC-P3-11_Discovery_Execution_Register_v1.21.md` (supersedes v1.20)

**Supersedes:**
- None newly superseded by this document itself — `Batch6_Pipeline_Package_v1.0` is a first issue
- `DOC-P3-11_Discovery_Execution_Register_v1.20.md` — superseded by v1.21 per §9

No historical file renamed. No historical file deleted. Founder manages historical file lifecycle manually, per `DOC-P3-09` §06E.

---

# 11. Batch 6 Closure Readiness Summary

| Check | Status |
|---|---|
| All 5 stages complete | ✅ |
| 4 of 4 gaps resolved to a path | ✅ |
| Cross-Batch Dependencies logged/strengthened | ✅ 1 new (B6-CBD-001), 1 narrowed (CBD-004), 3 unchanged (CBD-001/002/003) |
| Any gap requiring further evidence | ❌ None — all 4 need a Founder *decision*, not more evidence |
| DOC-P3-11 updated in same execution | ✅ v1.20 → v1.21, per §9 |
| **Batch 6 ready to close** | **Recommended COMPLETE — APPROVED — ACTIVE — FROZEN** — no stop condition triggered, no unresolved evidence gap, consistent with how every prior batch froze with open Founder-decision items still outstanding |

---

# 12. Founder Approval Gate

**Batch 6 pipeline (Baseline Verification through Resolution) is complete. `DOC-P3-11` updated to v1.21 in the same execution. Batch 6 is recommended COMPLETE — APPROVED — ACTIVE — FROZEN. No AGR, SER, or DCR has been created — 1 SER Candidate (B6-RES-001) identified, not created. No CBD closed. The Phase 3.5 Integration Review has NOT begun, per instruction.**

**Items requiring Founder attention, ranked by materiality:**
1. **B6-GAP-001:** No table exists to hold dish-level regional affinity weighting. If this signal matters for RE scoring (plausible, not confirmed), an SER is needed — shape not designed here.
2. **B6-DQ-002/B6-GAP-004:** Third independent data source now supports treating `Chole Bhature` (Punjab) and `Chole Bhature (Delhi)` as genuinely distinct — relevant context for the still-open `B5-RES-005` decision.
3. **B6-CBD-001 (new):** 23 of 29 state codes in this batch's data depend on `re_states` rows not yet seeded (Batch 1's own disclosed, intentional gap) — no urgency today, but worth tracking as a second consumer of that eventual full seeding.
4. **`Appam with Stew`:** Confirmed real and regionally grounded, still has no combo-file match anywhere in current project files — narrows, does not resolve, the open CBD-004 question from Batch 5.

Founder sign-off: _______________________ Date: ___________
