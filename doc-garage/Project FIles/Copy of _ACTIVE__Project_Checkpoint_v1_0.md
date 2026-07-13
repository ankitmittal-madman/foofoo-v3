# [ACTIVE]_Project_Checkpoint_v1.0

**Project Checkpoint — Governance Consolidation Before Batch 4**
**Date:** 2026-07-02
**Baseline confirmed:** All frozen Phase 3 documents, Batch 1/2/3 frozen packages, `DOC-P3-09` v1.1→v1.2, `DOC-P3-11` v1.18→v1.19, `DOC-P3-12` v1.1→v1.2 — no duplicate ACTIVE content found beyond the already-known stale-file housekeeping items from earlier sessions (unchanged, non-blocking).

---

## TASK 2 — Pending Resolution Matrix

*(Task 1's per-item A/B/C/D determination is embedded in the "Recommended Action" and "Reason" columns below — one matrix, no duplicate entries, per instruction.)*

**Legend:** A = Resolve Now · B = Remain Intentionally Open · C = Move to Future Batch · D = Move to Governance Backlog

| ID | Origin | Type | Current Status | Action | Reason | Owner | Blocking? | Future Dep? |
|---|---|---|---|---|---|---|---|---|
| GC-AGR-001 | Batch 1 | AGR Candidate | Open | **B** | Requires Founder business-fidelity decision + eventual implementation; neither has occurred | Founder→Arch | No | No |
| GC-AGR-002 | Batch 1 | AGR Candidate | Open, evidence-complete | **B** | Finding fully evidenced (22-row CHECK violation); only remaining step is Founder approval to create the AGR + implement — implementation excluded from today's closure scope | Founder→Arch | **Yes — blocks Phase 9 for Batch 1** | No |
| GC-SER-001 | Batch 1 | SER Candidate | Open | **B** | Founder decision on addon-plan granularity pending | Founder→Arch | No | No |
| GC-SER-002 | Batch 1 | SER Candidate | Open | **B** | Founder decision on nonveg-logic granularity pending | Founder→Arch | No | No |
| GC-SER-003 | Batch 1 | SER Candidate | Open | **B** | Founder/Product confirmation of City Tier need pending; no evidence resolves it either way | Founder/Product | No | No |
| GC-SER-004 | Batch 1 | SER Candidate | Open | **B** | Founder decision on 3-weights-vs-1-column pending | Founder→Arch | No | No |
| GC-SER-005 | Batch 1 | SER Candidate | Open | **B** | Founder/Arch confirmation of need pending (Persona residual attrs); also subject to unresolved Consolidation Rec. B | Founder→Arch | No | No |
| GC-SER-006 | Batch 1 | SER Candidate | Open | **B** | Same as GC-SER-005 (State residual attrs); also subject to Consolidation Rec. B | Founder→Arch | No | No |
| GC-SER-007 | Batch 1 | SER Candidate | Open | **B** | Split across Consolidation Recs. A & B, neither approved/rejected yet | Founder→Arch | No | No |
| GC-SER-008 | Batch 1 | SER Candidate | Open | **B** | Founder/Arch confirmation pending; tied to BUILD-02 priority | Arch | No | No |
| GC-SER-009 | Batch 1 | SER Candidate | Open | **B** | Subject to unresolved Consolidation Rec. A | Product/Arch | No | No |
| GC-DOC-001 | Batch 1 | Doc Update | Open | **A — RESOLVED THIS CHECKPOINT** | `prior_weight DEFAULT 1.0` documented as a neutral starting prior, consistent with `re_cohort_class_priors.acceptance_rate_prior DEFAULT 0.5`'s identical "start neutral" pattern already in frozen DDL | Documentation | No | No |
| GC-DOC-002 | Batch 1 | Doc Update | Open | **B** | MC5's correct `cohort_code` requires Founder/source confirmation — no accessible evidence picks one value over another | Founder | No | No |
| GC-DOC-003 | Batch 1 | Doc Update | Open | **A — RESOLVED THIS CHECKPOINT** | `re_states.region` domain confirmed as exactly 5 values (north/south/east/west/central), directly observed in `101_seed_reference_data_framework.sql` | Documentation | No | No |
| GC-DOC-004 | Batch 1 | Doc Update | Open | **A — RESOLVED THIS CHECKPOINT** | `persona_code` convention confirmed as `<MAIN_COHORT_PREFIX>_<CONTEXT>_<DIET>` UPPER_SNAKE_CASE (e.g. `MC3_NORTH_VEG`), directly observed in seed INSERTs | Documentation | No | No |
| GC-DOC-005 | Batch 1 | Doc Update | Open | **A — RESOLVED THIS CHECKPOINT** | Per established project convention (UI-copy extraction pattern), onboarding-copy belongs in app config, not a DB column — applying precedent, not a fresh Founder statement on this exact item; Founder may override | Documentation | No | No |
| GC-IMP-001 | Batch 1 | Impl. Note | Open | **B** | Requires Founder/Product methodology decision, then implementation | Founder→Eng | No | No |
| GC-IMP-002 | Batch 1 | Impl. Note | Open | **B** | Same — scoring methodology undecided | Founder→Eng | No | No |
| GC-IMP-003 | Batch 1 | Impl. Note | Open | **B** | Same — ranking methodology undecided | Founder→Eng | No | No |
| GC-FBD-001 | Batch 1 | Future Batch Dep. | Open | **C** | By definition resolves at Batch 4 | Cross-Batch | No | **Yes — Batch 4** |
| Consolidation Rec. A | Batch 1 (Stage 8) | Recommendation | Open | **B** | Never approved or rejected by Founder | Founder | No | No |
| Consolidation Rec. B | Batch 1 (Stage 8) | Recommendation | Open | **B** | Same | Founder | No | No |
| B2-RES-001 | Batch 2 | Resolution (AGR-track) | Open | **B** | Founder/Arch decision on building an Alias table pending | Founder→Arch | No | No |
| B2-RES-002 | Batch 2 | Resolution (AGR-track) | Open | **C** | Tied to CBD-001 — genuinely depends on Batch 4 existing first | Founder→Arch | No | **Yes — Batch 4** |
| B2-RES-003 | Batch 2 | Resolution (AGR-track) | Open | **C** | Same as B2-RES-002 | Founder→Arch | No | **Yes — Batch 4** |
| B2-RES-004 | Batch 2 | Resolution (SER-track) | Open | **B** | Founder/Arch decision on adding 5 columns pending | Founder→Arch | No | No |
| B2-RES-005 | Batch 2 | Resolution (business call) | Open | **B** | Pure business-meaning decision; no evidence favors one answer, cannot be resolved by inference | Founder/Product | No | No |
| B2-RES-006 | Batch 2 | Resolution (Doc-track) | Open | **A — PROPOSAL DRAFTED** | Frequency-ordered bit-assignment proposed (dairy=0, gluten=1, fish=2, tree_nuts=3, mustard=4, peanuts=5, sesame=6, shellfish=7, soy=8, egg_allergen=9); remains Open pending Founder confirmation since it becomes a permanent encoding | Founder→Arch | No | No |
| B2-RES-007 | Batch 2 | Resolution (dependent) | Open | **B** | Inherits B2-RES-001 | Arch | No | No |
| CBD-001 | Batch 2 | Cross-Batch Dep. | Open | **C** | Sequencing NOT satisfied — Batch 4 hasn't run | Cross-Batch | No | **Yes — Batch 4** |
| B3-RES-001 | Batch 3 | Resolution (AGR-track) | Open | **B** | Founder/Arch decision on building a Cuisine Group table pending | Founder→Arch | No | No |
| B3-RES-002 | Batch 3 | Resolution (AGR-track) | Open | **B** | Same for Cuisine | Founder→Arch | No | No |
| B3-RES-003 | Batch 3 | Resolution (AGR-track, Critical) | Open | **B** | Founder/Arch must decide how to rename/restructure the 2 colliding tag values before `public.tags` can seed correctly | Founder→Arch | **Yes — blocks RE-DOC-01–05 genome mechanism** | No |
| B3-RES-004 | Batch 3 | Resolution (Doc-track, Critical) | Open | **A — ALGORITHM DRAFTED** | Deterministic assignment algorithm proposed (order by tier ascending, then category, then value, alphabetically; sequential integers 0–110); full 111-row table not enumerated here, generatable on request; remains Open pending Founder confirmation | Founder→Arch | **Yes — blocks RE-DOC-01–05 genome mechanism** | No |
| B3-RES-005 | Batch 3 | Resolution (SER-track) | Open | **B** | Founder/Arch decision on adding 2 columns pending | Founder→Arch | No | No |
| B3-RES-006 | Batch 3 | Resolution (SER-track) | Open | **B** | Founder/Arch decision on `re_states` scope extension pending | Founder→Arch | No | No |
| CBD-002 | Batch 3 | Cross-Batch Dep. | Open | **B (corrected from a pure "Future Batch" framing)** | Direction is reversed from CBD-001: Batch 4 depends on Batch 3, not vice versa. Cannot close — B3-RES-001/002 (which it depends on) are still open. Should resolve **before** Batch 4 ideally, not "at" Batch 4 | Founder→Arch | No | Partial — affects Batch 4 quality, doesn't block Batch 4 from starting |
| CBD-003 | Batch 3 | Cross-Batch Dep. | Open | **B (same correction as CBD-002)** | Same reasoning — depends on B3-RES-003/004 | Founder→Arch | No | Partial |
| GB-001 | Backlog | Cosmetic | Open | **D (confirmed, already there)** | Visual Impact Chain renderer — Keep | — | No | No |
| GB-002 | Backlog | Cosmetic | Open | **D (confirmed, already there)** | Resolution Order Kanban view — Keep | — | No | No |

**Totals: 40 items reviewed. 5 Resolved/Proposed this checkpoint (A). 30 remain intentionally Open (B) — including 2 CBD reclassifications. 3 moved/confirmed Future Batch (C). 2 confirmed in Governance Backlog (D). 0 closed without evidence.**

---

## TASK 7 — Batch 3 Freeze Summary

`Batch3_Pipeline_Package_v1.0` reviewed for internal consistency: all 5 stages complete, all 6 gaps carry a resolution path, both Cross-Batch Dependencies (CBD-002, CBD-003) properly logged with direct evidence, no contradiction found. **Batch 3 is now marked COMPLETE — APPROVED — ACTIVE — FROZEN**, consistent with how Batch 1 and Batch 2 were frozen with open GC/RES items still outstanding — freezing a batch means its own pipeline is internally complete and consistent, not that every downstream question is answered.

---

## TASK 8 — Project Health Report

### Current Batch Status
Batch 1: FROZEN (20 GC items, 4 resolved this checkpoint, 16 open). Batch 2: FROZEN (7 RES + 1 CBD, all open/deferred). Batch 3: **FROZEN this checkpoint** (6 RES + 2 CBD, 1 RES proposal drafted, rest open).

### Remaining Open Items — by type
- 2 AGR Candidates (GC-AGR-001/002) + 3 AGR-track Batch 2/3 Resolutions (B2-RES-001, B3-RES-001/002) + 1 Critical AGR-track (B3-RES-003)
- 9 SER Candidates (Batch 1) + 4 SER-track Resolutions (B2-RES-004, B3-RES-005/006, and B2-RES-007 dependent)
- 1 Doc Update still open (GC-DOC-002)
- 2 Doc-track proposals drafted, awaiting confirmation (B2-RES-006, B3-RES-004)
- 3 Implementation Notes (methodology decisions pending)
- 2 unresolved Consolidation Recommendations

### Remaining Founder Decisions
GC-DOC-002 (MC5 code), B2-RES-005 (egg diet-type meaning), all 9 Batch-1 SER confirmations, Consolidation Recs A/B, and — highest priority — **confirming the two proposed encodings** (allergen bits, tag vector-positions) so Phase 9 isn't blocked later.

### Remaining Architecture Decisions
Whether to build: an Ingredient Alias table, a Dish Term Synonym table, a Cuisine/Cuisine Group table structure, and how to restructure the 2 colliding `public.tags` values.

### Remaining Cross-Batch Dependencies
CBD-001 (genuinely waits for Batch 4), CBD-002 and CBD-003 (should resolve **before** Batch 4 for best quality, corrected framing this checkpoint).

### Remaining Governance Backlog
GB-001, GB-002 — both Keep, both deferred to post-Batch-6.

### Outstanding Blocking Items
**Only 3 items in the entire project currently block something concrete:** GC-AGR-002 (blocks Batch 1 Phase 9), B3-RES-003 and B3-RES-004 (both block `RE-DOC-01–05`'s genome-vector mechanism — the single most consequential open pair in the project).

### Expected Batch 4 Inputs
`dishes.xlsx` (`dishes_810` sheet, 812 rows; `Sheet1` excluded per Founder directive), plus awareness of CBD-001/002/003 as consuming context — not blocking Batch 4's own Discovery.

### Batch 4 Risks
1. `dishes_810`'s `Cuisines` and 11 tag-category columns will reference Batch 3 concepts that don't yet have destination tables or, in the tag case, have an unresolved naming conflict — Batch 4 Mapping will inherit these same gaps, not new ones.
2. 812 rows is the largest single-file batch yet (vs. Batch 1's largest sheet at 38 rows, Batch 2/3's ~100–190-row files) — proportionally more Discovery-stage effort expected.

### Batch 4 Recommendations
Resolve B3-RES-003/004 (the tag conflict + vector positions) **before** Batch 4 Mapping, since Batch 4 will produce dish-level tag references that would otherwise inherit an already-known-broken target. This is a recommendation, not a directive — Batch 4 can still begin Discovery/Canonicalization independently in the meantime, per Batch Independence.

---

## Project Clean Baseline Summary

**Closed this checkpoint:** 4 Batch 1 Documentation Updates (GC-DOC-001/003/004/005), fully evidence-backed. 2 governance-normalization relocations (Architecture Confirmation Rule, Governance Evaluation Rule, Resolution Execution Rule → `DOC-P3-09`). Batch 3 formally frozen.

**Drafted but intentionally left open:** 2 documentation-track proposals (allergen bit-assignment, tag vector-position algorithm) — both are consequential permanent encodings and are being surfaced for Founder confirmation rather than silently finalized.

**Remains intentionally open, with reasons:** 30 items — the overwhelming majority require a Founder or Architecture decision this checkpoint cannot manufacture on its own (per "never close an item merely to reduce the list"). 3 Cross-Batch Dependencies remain open; 2 of them (CBD-002/003) had their framing corrected from "waits for Batch 4" to "should resolve before Batch 4 for quality, but doesn't block it."

**What Batch 4 inherits:** A clean, internally-consistent Batch 1–3 baseline; 3 open Cross-Batch Dependencies it should be aware of but isn't blocked by; and 2 known, well-evidenced pre-existing gaps (Cuisine/Tag destinations) that its own Mapping stage will re-encounter, not rediscover.

---

## Founder Approval Gate

**Batch 4 has NOT begun.** 5 items resolved/proposed this checkpoint; 30 remain open by design, each with a stated reason; 3 confirmed Future-Batch; 2 confirmed Backlog. Awaiting Founder review before Batch 4 starts.

Founder sign-off: _______________________ Date: ___________
