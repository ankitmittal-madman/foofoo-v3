# [ACTIVE]_Batch2_Resolution_Package_v1.0

**Phase 3.5 — Batch 2 — Stage 5: Resolution**
**Methodology:** Identical to `Batch1_Resolution_Package_v1.1` (frozen) — not re-explained here.
**Sole input:** `Batch2_GapAnalysis_Package_v1.0` (FROZEN, not reopened)
**Date:** 2026-07-02
**Status:** Draft — Ready for Founder Review

**Discipline note:** No AGR, SER, or DCR is created here. No schema, migration, or SQL is proposed. "Future AGR/SER Candidate" labels below mirror `Batch1_Resolution_Package_v1.1`'s own established phrasing — a resolution *path*, not an artifact.

---

## Resolution Register

| RES ID | GAP ID | GAP Classification | Resolution Path | Resolution Order | Owner | Confidence |
|---|---|---|---|---|---|---|
| B2-RES-001 | B2-GAP-001 | C1 | Founder Decision (Future AGR Candidate) | **Immediate** | Founder → Architecture | High |
| B2-RES-002 | B2-GAP-002 | C1 | Founder Decision (Future AGR Candidate) — see CBD-001 | **Future Batch** | Founder → Architecture | High |
| B2-RES-003 | B2-GAP-003 | C1 | Founder Decision (Future AGR Candidate) — see CBD-001 | **Future Batch** | Founder → Architecture | Medium |
| B2-RES-004 | B2-GAP-004 | C1 | Founder Decision (Future SER Candidate) | **Parallel** | Founder → Architecture | High |
| B2-RES-005 | B2-GAP-005 | C2 | Founder Decision (business-meaning call; no artifact implied either way) | **Parallel** | Founder/Product | Medium |
| B2-RES-006 | B2-GAP-006 | B | Founder Decision (Documentation Update track — propose a bit-assignment convention for Founder confirmation, no schema change) | **Immediate** | Founder → Architecture | High |
| B2-RES-007 | B2-GAP-007 | C1 | Inherits B2-RES-001 — not independently resolved | **Blocked** (on B2-RES-001) | Architecture | High |

**Why B2-RES-004 is SER-track and B2-RES-001/002/003 are AGR-track, consistent with Batch 1's precedent:** Batch 1 distinguished AGR from SER by severity/criticality, not by "table exists vs. doesn't" — `GC-AGR-001` (Batch 1) involved an existing table with reduced fidelity, same structural shape as B2-GAP-004 here, yet was AGR-track because it blocked core seed generation. B2-GAP-004 (5 descriptive attributes missing from an already-functional `public.ingredients` table) does not block loading the other 10 attributes or any RE function evidenced so far — matching the lower-severity SER pattern instead. B2-GAP-001/002/003, by contrast, involve entire concepts with **no** existing table at all — a more severe absence than reduced fidelity within a working table — placed on the AGR track on that basis.

---

## Cross-Batch Dependency Register

| CBD ID | Source (Batch 2) | Target | Evidence | Status |
|---|---|---|---|---|
| CBD-001 | B2-GAP-002 (Dish Term Synonym), B2-GAP-003 (Disambiguation Records) | Batch 4 (`dishes.xlsx` Canonicalization) | `term_synonyms_v2.canonical_name` values are dish names (Biryani, Pani Puri, Butter Chicken, etc.) — the same identity space Batch 4 will canonicalize independently. Building a synonym-storage table now, before Batch 4's dish ID scheme exists, risks creating an incompatible identity space that would need reconciling later. | **OPEN** — no action taken; recorded per the Batch Independence Rule precedent (same handling as Batch 1's GAP-001) |

**This is the second cross-batch dependency in the project, and the first raised by Batch 2 rather than Batch 1. Both point at Batch 4.**

---

## Impact Chain

| RES ID | Canonical Entity | Target Table | Seed Impact | RE Impact | API Impact | UI Impact |
|---|---|---|---|---|---|---|
| B2-RES-001 | B2-CAN-ENT-002 | None exists | 164 rows blocked | Unknown — no RE-DOC function currently reads alias data | Unknown | Unknown |
| B2-RES-002 | B2-CAN-ENT-003 | None exists | 114 rows blocked | Unknown | Unknown | Unknown |
| B2-RES-003 | B2-CAN-EX-001 | None exists | 7 rows blocked | Unknown | Unknown | Unknown |
| B2-RES-004 | B2-CAN-ENT-001 (partial) | `public.ingredients` (exists; missing 5 columns) | 191 rows partially incomplete (5 of 15 attributes each) | Unknown — no confirmed RE-DOC consumer for these 5 attributes | Unknown | Unknown |
| B2-RES-005 | B2-CAN-ENT-001 | `public.ingredients.is_veg` (exists) | 1 row | Unknown | Unknown | Unknown |
| B2-RES-006 | B2-CAN-ENT-001 / B2-CAN-VOC-003 | `public.ingredients.allergen_flags` (exists) | 45 rows | **Confirmed** — `RE-DOC-02`'s hard-constraint allergen propagation logic depends on this data | Unknown | Unknown |
| B2-RES-007 | B2-CAN-REL-001 | None exists (inherits B2-RES-001) | Not additive — inherits B2-RES-001 | Unknown | Unknown | Unknown |

**Every "Unknown" is left Unknown deliberately — no downstream impact is asserted without a citable frozen-document source. Only B2-RES-006's RE Impact is confirmed, and only because `RE-DOC-02` explicitly names allergen propagation as a hard constraint.**

---

## OBS → CAN → MAP → GAP → RES Lineage

```
B2-OBS-ENT-002 → B2-CAN-ENT-002 → B2-MI-001 → B2-GAP-001 → B2-RES-001
B2-OBS-ENT-003 → B2-CAN-ENT-003 → B2-MI-002 → B2-GAP-002 → B2-RES-002 (+ CBD-001)
B2-CAN-EX-001  →                  B2-MI-003 → B2-GAP-003 → B2-RES-003 (+ CBD-001)
B2-OBS-ENT-001 → B2-CAN-ENT-001   → B2-MI-004 → B2-GAP-004 → B2-RES-004
B2-OBS-ENT-001 → B2-CAN-VOC-002   → B2-MI-005 → B2-GAP-005 → B2-RES-005
B2-OBS-ENT-001 → B2-CAN-VOC-003   → B2-MI-006 → B2-GAP-006 → B2-RES-006
B2-OBS-REL-001 → B2-CAN-REL-001   → B2-MI-007 → B2-GAP-007 → B2-RES-007 (inherits RES-001)
```

---

## Resolution Confidence

**Confidence measures certainty of the resolution *path* (Founder Decision vs. Architecture vs. Documentation-track), not certainty of eventual implementation.**

| Confidence | RES IDs | Basis |
|---|---|---|
| High | B2-RES-001, 002, 004, 006, 007 | Classification-to-path mapping is direct and evidence-backed; no ambiguity in which track applies |
| Medium | B2-RES-003, 005 | B2-RES-003 inherits GAP-003's "distinct destination" uncertainty; B2-RES-005 is a genuine open business call with no frozen precedent pointing to one answer |

---

## Governance Backlog Note

Two purely cosmetic/reporting improvements were noticed while building the Impact Chain and Resolution Order tables above (a visual flow-diagram renderer; a Kanban-style view of Immediate/Parallel/Future Batch/Blocked). Neither affects seed quality, lineage, architecture, or reproducibility — both logged to `DOC-P3-12` v1.1 as GB-001/GB-002 instead of pausing this stage. See that document for detail.

---

## Regression Review

- ✅ `Batch2_GapAnalysis_Package_v1.0` not reopened or modified — no GAP record edited
- ✅ `Batch2_Mapping_Package_v1.0` not reopened
- ✅ No architecture, schema, RE, or API document touched
- ✅ No AGR, SER, or DCR created
- ✅ No schema change, migration, or SQL proposed
- ✅ No downstream impact invented — every unconfirmed cell in the Impact Chain reads "Unknown"
- ✅ Cross-batch content (CBD-001) recorded as an open dependency only, no Batch 4 assumption made

---

## Resolution Summary

7 of 7 gaps resolved to a path. 4 Founder-Decision/Future-AGR-Candidate items (2 of which also carry a new Cross-Batch Dependency, CBD-001). 1 Founder-Decision/Future-SER-Candidate item. 1 Founder-Decision/Documentation-Update-track item with a direct structural precedent already in frozen architecture. 1 pure business-meaning call with no schema implication either way. Resolution Order applied for the first time this batch: 2 Immediate, 2 Parallel, 2 Future Batch, 1 Blocked.

---

## Batch 2 Closure Readiness Summary

| Check | Status |
|---|---|
| Discovery, Canonicalization, Mapping, Gap Analysis frozen/approved | ✅ |
| Resolution complete | ✅ (this document) |
| All gaps carry a resolution path | ✅ 7 of 7 |
| Any gap requiring further evidence before Founder can decide | ❌ None — all 7 were already marked Resolution-ready in Gap Analysis |
| Architecture Confirmation required | Not yet — no item here shows the "absence, evidence ambiguous" pattern that triggered it in Batch 1; all 7 gaps have a clear, evidence-backed classification already |
| Governance Evaluation required | Not yet — would restate what this Resolution Register already shows for a 7-gap batch; can be added later if Founder wants the extra layer |
| Cross-Batch Dependencies logged | ✅ CBD-001 |
| **Batch 2 ready to close** | **Not yet declared — awaiting Founder approval per stop condition; no blocker identified** |

---

## Founder Approval Gate

**Batch 2 Resolution is complete. Batch Closure has NOT begun. Batch 3 has NOT begun. No AGR, SER, or DCR has been created.**

Founder sign-off: _______________________ Date: ___________
