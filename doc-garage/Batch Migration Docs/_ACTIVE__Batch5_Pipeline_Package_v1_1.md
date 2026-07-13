# [ACTIVE]_Batch5_Pipeline_Package_v1.1

**Supersedes:** `Batch5_Pipeline_Package_v1.0` (retained unmodified as superseded reference — never regenerated)
**Scope:** Governance refinement only. No Discovery, Canonicalization, Mapping, or Gap Analysis rerun. No evidence, ID, lineage, classification, confidence, or statistic changed.
**Date:** 2026-07-03 · **Status:** APPROVED — ACTIVE — FROZEN (pending Founder sign-off below)

---

## Persistence Manifest

**Created:**
- `[ACTIVE]_Batch5_Pipeline_Package_v1.1.md`
- `[ACTIVE]_DOC-P3-09_Knowledge_Integration_Governance_v1.3.md`

**Updated (referenced, not rewritten — this manifest itself is the record of the update):**
- `DOC-P3-11` should log Batch 5 closure at its next revision (v1.21) — not performed as a separate document in this pass since the Founder instruction scoped this session to Batch 5 + DOC-P3-09 only; flagged here so it isn't silently missed.

**Supersedes:**
- `Batch5_Pipeline_Package_v1.0.md` — retained, untouched, historical
- `DOC-P3-09_Knowledge_Integration_Governance_v1.2.md` — retained, untouched, historical

No historical file renamed. No historical file deleted. Founder manages historical file lifecycle manually, per `DOC-P3-09` §06E.

---

## Task 1 — Permanent Document Persistence Rule

Confirmed **not already present** in `DOC-P3-09 v1.2` (verified by direct search before amending — the general naming convention existed only in `Engineering_Handover...v1.3` §6.1 and `Project_Baseline_Register_v1.2` Step 9, not in DOC-P3-09 itself). Added as `DOC-P3-09 v1.3` §06E, targeted amendment, no other content touched. See separate file.

---

## Task 3 — B5-RES-001 Refined: Architecture Option Pack

**Evidence, Classification, Priority, Lineage, and Confidence below are unchanged verbatim from `Batch5_Pipeline_Package_v1.0` §6–7.** Only the Resolution wording is refined — from an implementation-suggesting statement to a decision-neutral option pack.

### Problem
`public.dish_combo_items.role` carries a live CHECK constraint (`DOC-P3-04 v1.3` §03.10; migration `009_content_junctions.sql`) restricting values to `('primary','side','accompaniment')`. The actual Batch 5 seed source (`dish_combo_items_v2_20260520.csv`) uses 8 distinct role values. 31 of 74 rows (41.9%) fall outside the 3 schema-permitted values and would fail at insert time.

### Evidence *(unchanged from v1.0)*
- Exact role tabulation: `primary` (30, allowed), `accompaniment` (13, allowed), `bread` (12, blocked), `carb_base` (5, blocked), `condiment` (5, blocked), `dessert` (2, blocked), `beverage` (1, blocked), `standalone` (6, blocked).
- `side` — the one schema-permitted value beyond `primary`/`accompaniment` — is used in **0 of 74 rows**.
- Relationship-Intelligence evidence (B5-OBS-RULE-002/005/006): substitution occurs only within a role; bread is the dominant substitution axis; dessert/condiment are never substitution targets. This behavioral evidence is relevant context for any option below, not a basis for selecting one.

### Option A — Expand the CHECK constraint to match observed data
Add the 6 missing values to the existing constraint (`bread`, `carb_base`, `condiment`, `dessert`, `beverage`, `standalone`), retaining `side` for any future data that uses it.
- **Trade-off:** Preserves full relationship-semantic granularity found in Discovery (bread vs. carb_base as distinct substitution classes, etc.) at the cost of a wider enum that future combo data must also conform to exactly.

### Option B — Collapse the 6 unsupported values onto the existing 3-value set
Define a mapping (e.g., `bread`→`accompaniment`, `carb_base`→`accompaniment`, `condiment`→`accompaniment`, `dessert`→`accompaniment`, `beverage`→`accompaniment`, `standalone`→`primary`) and transform data at seed time rather than changing the schema.
- **Trade-off:** No schema change required, but destroys the substitution-axis distinction the Relationship Intelligence findings depend on (B5-OBS-RULE-002/005) — bread-vs-carb_base swap logic and dessert/condiment non-swap behavior would no longer be queryable from `role` alone.

### Option C — Introduce a two-tier model (retain `role`'s 3 values, add a new `component_type` column for the finer-grained 8-value semantic)
Keep `role` as-is (satisfies the current CHECK, unchanged), add a second column carrying the richer vocabulary for RE/UI consumption.
- **Trade-off:** Preserves both the frozen constraint and the full relationship-semantic detail, at the cost of a net-new column (an SER, not a CHECK-constraint edit) and a small denormalization (two columns describing related but distinct facets of the same row).

### Recommendation
None offered. Per instruction, no option is selected here — this is presented as a decision-neutral pack for Founder/Architecture review.

### Seed Impact *(unchanged classification from v1.0's Critical rating, restated in this pack's terms)*
**Critical** — 31 of 74 rows (41.9%) cannot be seeded under the current constraint regardless of which option is chosen; the impact is identical across all three options in that all three would unblock the same 31 rows. The options differ in what they preserve or discard, not in whether they resolve the blocking condition.

### Decision Deferred
This Architecture Option Pack does not select an option, does not redesign the schema, and does not create an AGR. It is evidence-driven input for a Founder/Architecture decision, per instruction.

---

## Task 4 — Founder vs. Architecture Ownership Review

Reviewed all 7 Batch 5 Resolution items (`B5-RES-001` through `B5-RES-007`) against the test: *is this item's answer already fully determined by evidence already in hand, such that no new business/product judgment is required — only an architectural implementation choice?*

| RES ID | v1.0 Ownership | Reviewed | Reclassified? | Reasoning |
|---|---|---|---|---|
| B5-RES-001 | Founder→Arch (AGR Candidate) | Yes | **No change** | All three options in the pack above require a genuine trade-off judgment (semantic richness vs. schema simplicity vs. denormalization) — this is a product/architecture judgment call, not a fact evidence alone resolves. Correctly Founder-involved. |
| B5-RES-002 | Founder→Arch | Yes | **Reclassified to Architecture-owned** | The FK target (`dishes.id`) already exists; the only open question is *which deterministic string-matching procedure* to use (exact match, normalized-case match, etc.) — this is a data-engineering implementation method, not a business-judgment call, and Batch 1–4 precedent (e.g., B3-RES-004's deterministic tag-ordering algorithm) already treats "define a deterministic matching/ordering algorithm" as Architecture-track. Reclassifying to **Architecture**, no Founder input required beyond final sign-off. |
| B5-RES-003 | Founder→Arch (joint with B4-GAP-001) | Yes | **No change** | Correctly joint — this is the same open cuisine-destination question already properly escalated to Founder at the Batch 3/4 level; Batch 5 doesn't change that ownership. |
| B5-RES-004 | Founder/Product | Yes | **No change** | Whether `combo_slug` is needed for MVP is a product-scope question with no evidence resolving it either way — correctly Founder/Product. |
| B5-RES-005 | Founder | Yes | **No change** | Whether `Chole Bhature (Delhi)` is a duplicate or a genuine unpopulated variant requires knowledge of source-data intent that no file in the project answers — correctly a Founder fact-check, not an architecture question. |
| B5-RES-006 | Founder/Product | Yes | **No change** | Same reasoning as B5-RES-005 — a data-intent question, not resolvable from evidence alone. |
| B5-RES-007 | Founder→Arch | Yes | **No change** | Whether a missing combo source file exists, or whether the 5 unmatched dishes revert to standalone, requires Founder knowledge of what source material exists outside the project files already reviewed — correctly Founder-involved. |

**1 of 7 reclassified** (B5-RES-002: Founder→Arch → Architecture). No evidence, lineage, or GAP/RES ID changed as a result — only the ownership field.

---

## Task 5 — Regression Review

Verified by direct comparison against `Batch5_Pipeline_Package_v1.0`:

| Check | Result |
|---|---|
| Discovery (§3, all OBS/VOC/RULE/DQ IDs and content) | ✅ Unchanged, byte-for-byte identical in substance |
| Canonicalization (§4) | ✅ Unchanged |
| Mapping (§5, including the 43/31 exact role-count table) | ✅ Unchanged |
| Gap Analysis (§6, all 7 GAP IDs, Categories, Priorities, Owners as originally assigned) | ✅ Unchanged |
| Resolution evidence (§7) | ✅ Unchanged — B5-RES-001's Evidence/Classification/Priority/Lineage/Confidence are verbatim; only its *wording* (now the Option Pack format) changed, per Task 3 |
| IDs | ✅ 0 renumbered, merged, or reused — all `B5-OBS-*`, `B5-CAN-*`, `B5-MI-*`, `B5-GAP-*`, `B5-RES-*`, `B5-DQ-*` identical to v1.0 |
| Lineage | ✅ Every RES still cites its GAP ID; every GAP still cites its MI ID; unchanged |
| Statistics (109 rows, 35 combos, 74 items, 8 roles, 41.9%/58.1% split) | ✅ Identical |
| Cross-Batch Integration Summary (§9), Relationship Intelligence Summary (§8) | ✅ Unchanged |

**Only governance refinements differ**: B5-RES-001's presentation format (Task 3), one ownership reclassification (Task 4), and this document's own header/manifest apparatus (Tasks 1–2). Regression is clean.

---

## Task 6 — Batch 5 Freeze

Regression confirmed clean. Recommending Batch 5 as:

**`Batch5_Pipeline_Package_v1.1` — COMPLETE — APPROVED — ACTIVE — FROZEN.**

This freeze covers the full Batch 5 pipeline (Discovery → Resolution, inherited unchanged from v1.0) plus this session's governance refinements (Option Pack reframing, ownership correction, persistence manifest). `Batch5_Pipeline_Package_v1.0` is retained, unmodified, as the superseded reference.

**`DOC-P3-11` should be updated at its next revision** to record: Batch 5 closed this session; B5-RES-002 ownership corrected to Architecture; B5-RES-001 reframed as an Option Pack awaiting Founder/Architecture decision, not yet an AGR. Not performed as a standalone document edit in this pass — flagged in the Persistence Manifest above rather than silently deferred.

**Batch 6 has NOT begun**, per instruction.

---

## Founder Approval Gate

**Batch 5 governance refinement is complete. No Discovery, Canonicalization, Mapping, or Gap Analysis was rerun. No evidence, ID, lineage, classification, confidence, or statistic was changed. B5-RES-001 remains an unselected Architecture Option Pack — no option was chosen, no AGR was created. B5-RES-002 was reclassified from Founder→Arch to Architecture-owned, on evidence-based justification only. Batch 5 is recommended FROZEN. Batch 6 has NOT begun.**

Founder sign-off: _______________________ Date: ___________
