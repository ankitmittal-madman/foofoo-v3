# [ACTIVE]_REPO-BOOT-01_Repository_Bootstrap_Execution_Package_v1.0

**Naming note:** This document uses the `REPO-BOOT-` prefix deliberately, distinct from `DOC-`, `RE-DOC-`, `APDF-`, or `Batch`/`PIR` naming. It is a one-time, disposable execution artifact for Phase 6 only. It can be deleted after Repository Gate passes without impacting any APDF, governance, architecture, or product document — nothing outside this file depends on it existing.

**Scope of this session:** Sequencing and readiness package only. No repository created. No SQL generated. No migrations generated. No implementation started. This document ends immediately before Repository Bootstrap implementation begins.

**Precedence followed:** Project Documentation → Founder Decisions → Project APDF → Organization Standards → Organization Skills. Org-standard dotfiles (`.claude/CLAUDE.md`, `.claude/standards/ORG-STD-01_AI_Operating_Model_v1.0.md`) **were not found in project files** — flagged explicitly per Task 5 rather than assumed. This does not block this package since Project Documentation and APDF (both fully available) sit above Org Standards in the required precedence.

**Date:** 2026-07-03 · **Status:** Draft — Ready for Founder Review

---

## Task 1 — Consolidation Check

Repository Bootstrap was previously *described* (purpose, timing, high-level deliverables) across `[ACTIVE]_APDF_Framework_vNext_v2.0.md` (Phase 6 definition) and `[ACTIVE]_FooFoo_Project_Roadmap_v1.0/v1.1.md` (Bootstrap Preview diagram). None of these operationalized it as an executable checklist. This package is the first, consolidating rather than duplicating — every fact carried over from those documents is cited, not restated as new.

---

## 1. Bootstrap Objectives

- Confirm the implementation foundation (`foofoo-v2` repo, `foofoo-mvp` Supabase project, migration tooling) is genuinely ready, not just assumed ready.
- Produce one binary, testable readiness signal (a migration applies and rolls back successfully) rather than a subjective "looks fine."
- Establish exactly what Claude Code receives at handover, so implementation starts with complete, correct context on the first attempt.

## 2. Repository Readiness Criteria

A criterion is "ready" only if directly verified this session or a prior one — not because it was mentioned in an earlier document. Per `APDF_Framework_vNext_v2.0` Phase 6's own primary risk: *"repository existing is not the same as repository verified ready."*

## 3. Bootstrap Scope

- Verify repo folder structure against the migration numbering convention (`DOC-P3-05 Part A v1.2`)
- Verify Supabase project reachability and empty/ready state
- Verify or create `CLAUDE.md`
- Verify validation script (900-series) presence and runnability
- Verify dotfiles/org-standard integration state (flagged NOT VERIFIED this session — see Task 5)
- Run one trivial test migration + rollback as the binary exit test

## 4. Out of Scope

- Writing any real schema migration (the 5 Founder-approved changes from `Phase3_5_Architecture_Freeze_v1.0`)
- Writing any seed SQL
- Any Claude Code execution
- Any change to `DOC-P3-04`, frozen migrations 001–020, or any Batch/PIR/Architecture Freeze document
- Any change to APDF, governance, or product documentation

## 5. Repository Folder Structure

Per `DOC-P3-05 Part A v1.2` (already frozen, not redesigned here):
```
foofoo-v2/
├── supabase/
│   └── migrations/
│       ├── 001-020_*.sql       (structural, FROZEN — do not edit)
│       ├── 100-199_*.sql       (seed — Phase 7 work)
│       └── 900-999_*.sql       (validation — present per project files)
│       └── *_rollback.sql       (paired with every forward migration)
├── CLAUDE.md                    (repo conventions — verify or create)
└── .claude/                     (org dotfiles — presence NOT VERIFIED this session)
```

## 6. Repository Standards

Inherited entirely from `DOC-P3-05 Part A v1.2` — migration numbering, rollback pairing, never editing frozen 001–020 files directly. No new standard introduced here.

## 7. Dotfiles Integration

**NOT VERIFIED.** `.claude/CLAUDE.md` and `.claude/standards/ORG-STD-01_AI_Operating_Model_v1.0.md` were not found among project files during this session's search. This may simply mean they live in the `foofoo-v2` repo itself (a location this Claude.ai session cannot directly browse) rather than being absent — the distinction matters and should be confirmed by direct repo inspection before Repository Gate is scored, not assumed either way.

## 8. CLAUDE.md Integration

Every Claude Code prompt drafted across this project's prior sessions has assumed `CLAUDE.md` exists and lists it as the first file to read. Its actual presence in the repo has never been directly confirmed within any Claude.ai session — this is one of the concrete verification actions Bootstrap must perform, not assume.

## 9. Organization Skill Registration

Cannot be completed this session — no visibility into what organization skills exist beyond the dotfiles-related skill names surfaced in this Claude.ai session's own available-skills list (`dotfiles-bootstrap`, `docs-sequence`, `repo-structure-setup`, `project-kickoff`). These are **this session's own tool-level skills**, not confirmed to be the same as "organization skills" referenced in `ORG-STD-01` (which itself is unverified — see Task 5/Task 7). Flagged as NOT VERIFIED rather than conflated.

## 10. Skill Activation Matrix

| Skill (as visible to this Claude.ai session) | Classification | Reasoning |
|---|---|---|
| `dotfiles-bootstrap` | **Manual** | Directly relevant to Task 5/7's gap (org dotfiles not found) — should be invoked explicitly once `.claude/` presence is confirmed, not run automatically against unverified assumptions |
| `repo-structure-setup` | **Manual** | Directly relevant to Task verifying/auditing `foofoo-v2` folder structure — matches this package's own Section 5 |
| `docs-sequence` | **Not Applicable** | This project's documentation sequence is already fully established (33+ documents, APDF-governed) — this skill is for projects starting fresh |
| `project-kickoff` | **Not Applicable** | This project is well past kickoff (Phase 6 of 7) |
| Any skill referenced only inside the unverified `ORG-STD-01` | **Deferred** | Cannot classify a skill I cannot read; deferred until dotfiles presence is confirmed by direct repo access |

**Per instruction: skills adapt to the project, not the reverse.** No project workflow was altered to accommodate any skill above.

## 11. Repository Bootstrap Sequence

Reasoned from the project's own dependency structure, not assumed from the example in the prompt:

```
1. Read Project Documentation (Baseline Register, Architecture Freeze, APDF vNext)
        ↓
2. Read Organization Standards (.claude/CLAUDE.md, ORG-STD-01) — IF PRESENT; else flag and proceed under Project Documentation authority alone, per precedence order
        ↓
3. Verify Repository Structure (foofoo-v2 folder layout vs. DOC-P3-05 Part A)
        ↓
4. Verify Migration Layout (001-020 present and untouched, 100-199/900-999 folders exist)
        ↓
5. Verify Supabase Project (foofoo-mvp reachable, schema state matches frozen DDL, no drift)
        ↓
6. Verify Environment (credentials/access configured for Claude Code to actually connect)
        ↓
7. Verify or Create CLAUDE.md
        ↓
8. Verify Validation Scripts (900-904 present and executable against a fresh/empty schema)
        ↓
9. Register/Classify Skills (Task 5/10 above — best-effort given current visibility)
        ↓
10. Run Trivial Test Migration + Rollback (the binary exit test)
        ↓
11. Repository Gate scored
        ↓
12. Claude Code begins (Phase 7)
```

**Deviation from the example sequence given in the prompt:** Environment/credential verification (step 6) is inserted before `CLAUDE.md` and validation-script checks, because a Supabase connection that Claude Code can't actually authenticate against would make every later step's "verification" theoretical rather than real — this ordering was reasoned from the project's own repeated lesson (stated in `APDF_Framework_vNext_v2.0`) that assumed-but-unverified infrastructure state is exactly the failure mode Phase 6 exists to catch.

## 12. Repository Gate Checklist

| Item | Status | Basis |
|---|---|---|
| Repository exists | **NOT VERIFIED** | Referenced in project memory (`apverse-labs/foofoo-v2`) but not directly inspected in any Claude.ai session to date |
| Supabase configured | **NOT VERIFIED** | `foofoo-mvp` referenced in project memory as retained/untouched; not directly queried |
| Migration folders | **NOT VERIFIED** | Convention is fully specified (`DOC-P3-05 Part A v1.2`) but actual folder presence unconfirmed |
| Rollback convention | **NOT VERIFIED** | Same — specified, not confirmed present |
| Validation scripts | **PASS (existence)** | `900_structural_validation.sql`, `901_behavioral_trigger_validation.sql`, `902_behavioral_safety_gates.sql`, `903_behavioral_rls_validation.sql`, `904_behavioral_config_and_smoke_test.sql` all present in project files — **runnability against a live database is NOT VERIFIED**, only file existence |
| CLAUDE.md | **NOT VERIFIED** | Assumed by every prior Claude Code prompt in this project; presence never directly confirmed |
| Dotfiles installed | **NOT VERIFIED** | Per Task 5/7 above |
| Organization standards loaded | **NOT VERIFIED** | Per Task 5/7 above |
| Project documentation loaded | **PASS** | Confirmed this session — Baseline Register, Architecture Freeze, APDF vNext, Roadmap all present and read |
| Required project documents present | **PASS** | All Phase 3/3.5/4/5 documents confirmed present across this project's session history |
| Seed source files available | **PASS** | 12 CSV/XLSX files + master workbook (22 sheets) confirmed present in project files |
| Phase 3.5 frozen | **PASS** | Confirmed via `Phase3_5_Project_Integration_Review_v1.0`, `Phase3_5_Architecture_Freeze_v1.0` |
| Architecture frozen | **PASS** | Confirmed via Founder sign-off, 3rd Jul'26 |

**5 of 13 items PASS. 8 of 13 items NOT VERIFIED.** This is the honest state — not a failure, since none of the 8 NOT VERIFIED items require anything beyond direct inspection that this Claude.ai session doesn't have standing tool access to perform (repo browsing, Supabase querying) without either a connector or a Claude Code session with actual access.

## 13. Repository Exit Criteria

Unchanged from `APDF_Framework_vNext_v2.0` Phase 6: **a trivial migration can be written, applied, and rolled back successfully against the real database.** This single test, once actually run, would resolve most of the NOT VERIFIED items above as a side effect (if the migration applies, the repo/Supabase/folder structure/CLAUDE.md must all have been functional enough to allow it).

## 14. Definition of Done

Repository Bootstrap is done when: all 13 Gate items are PASS or explicitly Founder-waived (not silently skipped), and the trivial test migration + rollback has been run and reported with actual output, not asserted.

## 15. Claude Responsibilities (Claude.ai, this stage)

Verification-first reasoning, gap identification (as done throughout this document), sequencing, and handover package preparation. No code execution.

## 16. Claude Code Responsibilities (once Gate passes)

Actual repo/Supabase inspection, `CLAUDE.md` creation if missing, running the trivial test migration, and reporting real (not assumed) results for every Gate item currently marked NOT VERIFIED.

## 17. Founder Responsibilities

Confirm infrastructure access/credentials exist and are usable; confirm whether `.claude/` dotfiles are genuinely present in `foofoo-v2` or still pending; make the actual go/no-go call using this package's Gate results once they're real.

## 18. Rollback Strategy

Bootstrap itself is low-risk (verification + possibly creating `CLAUDE.md`) — if the trivial test migration fails, its own paired `_rollback.sql` reverses it immediately; no other project state is touched during Bootstrap, so there is nothing else to roll back.

## 19. Risks

- **Primary risk (already named in `APDF_Framework_vNext_v2.0`):** treating "described in a prior document" as equivalent to "verified" — this package deliberately resists that by marking 8 items NOT VERIFIED rather than inferring PASS from context.
- **Secondary risk:** the org-standard dotfiles may exist in the repo but simply weren't visible to this session — if Bootstrap proceeds without checking, a real conflict-resolution rule (Project Docs > Founder > APDF > Org Standards > Org Skills) could go unused because nobody confirmed Org Standards' actual content.

## 20. Dependencies

Repository Bootstrap depends on: Architecture Freeze sign-off (✅ complete), direct repo/Supabase access (a Claude Code session or a connected GitHub/Supabase tool), and Founder confirmation of dotfiles presence.

## 21. Go/No-Go Decision Matrix

| Condition | Go / No-Go |
|---|---|
| All 13 Gate items PASS | **GO** — proceed to Claude Code handover |
| Some NOT VERIFIED items remain, but Founder confirms infrastructure access is available for direct verification | **GO, conditionally** — hand this package to a Claude Code session whose first job is to resolve every NOT VERIFIED item with real evidence, then re-score before touching any real migration |
| Any Gate item is a confirmed FAIL (e.g., repo genuinely doesn't exist, Supabase unreachable) | **NO-GO** — resolve the specific failure before proceeding |
| Dotfiles/org standards remain unconfirmed indefinitely | **GO anyway**, per the stated precedence order — Project Documentation and APDF outrank Org Standards, so their absence doesn't block Bootstrap, it just means Org Standards contribute nothing until located |

---

## Task 4 — Sequencing Rationale (recap)

Already covered in Section 11 — the one deliberate deviation from the prompt's example sequence (environment/credential check moved earlier) is justified there.

## Task 7 — Implementation Handover Package (definition only, no prompt)

Once Repository Gate scores GO, Claude Code should receive, at minimum:
- **Project documents:** `Phase3_5_Architecture_Freeze_v1.0`, `Batch5_Pipeline_Package_v1.1`, `DOC-P3-04 v1.3`, `DOC-P3-05 Part A v1.2`
- **Architecture:** the 5 Founder-approved changes (cuisine persistence, dish attributes, tag vectors, combo roles, `slot` array conversion) with the addon-safety requirement explicitly restated
- **DDL:** `003_reference_tier1_1_1.sql`, `009_content_junctions_1_0.sql`, `002_reference_tier0_1_0.sql` (the three files to extend)
- **Seed files:** the master workbook + 9 remaining CSV/XLSX sources
- **Standards:** `CLAUDE.md` (once verified/created), any org standards once located
- **Validation:** the 900–904 script set
- **Founder decisions:** the full sign-off record (Ankit, 3rd Jul'26) including the exact addon-safety verification query result already run
- **Repository conventions:** the migration numbering/rollback-pairing rule from `DOC-P3-05 Part A`

---

## Executive Dashboard (Task 8)

```
Current Phase:        Phase 6 — Repository Bootstrap
Next Phase:            Phase 7 — Implementation
Current Gate:          🟡 Repository Gate — SCORED THIS SESSION: 5/13 PASS, 8/13 NOT VERIFIED
Next Gate:              ⚪ Data Gate
Repository Status:     Existence assumed from memory, NOT directly verified this session
Implementation Status: Not started
Overall Completion:    83% (unchanged — this session produced a readiness package, not new completed work)
```

```
Architecture Freeze ──▶ 🟢 PASSED
        │
        ▼
Repository Bootstrap ──▶ 🟡 IN PROGRESS (this package)
        │
        ▼
Repository Gate ──▶ ⚪ NOT YET SCORED FOR REAL (5/13 confirmed, 8/13 pending direct inspection)
        │
        ▼
Claude Code Begins ──▶ ⚪ NOT YET
```

---

## Task 9 — Regression Review

- ✅ No architecture changed
- ✅ No governance changed
- ✅ No APDF changed
- ✅ No project workflow changed
- ✅ No SQL generated
- ✅ No migrations generated
- ✅ No repository created
- ✅ No implementation started
- ✅ Named `REPO-BOOT-01` specifically to remain separable from `DOC-`/`APDF-`/`RE-DOC-`/governance naming — deletable post-Gate with zero impact elsewhere

---

# Final Output

## 1. Repository Bootstrap Summary
Repository Bootstrap has been fully *sequenced and scoped* this session, but **not executed** — 8 of 13 Gate items require direct repo/Supabase inspection this Claude.ai session cannot perform without either a connected tool or a Claude Code session tasked specifically with verification-only work first.

## 2. Repository Bootstrap Execution Sequence
See Section 11 — 12-step sequence, one deliberate deviation from the prompt's example (credential/environment check moved earlier), justified by this project's own recurring "verified vs. assumed" lesson.

## 3. Repository Gate
5 of 13 items PASS (all document/file-existence checks completable from project knowledge). 8 of 13 NOT VERIFIED (all requiring live repo/Supabase access). Zero FAIL.

## 4. Implementation Readiness Score
**62% Gate-verifiable from current session context (5/13 hard-confirmed); true readiness cannot be scored above that until the 8 NOT VERIFIED items are resolved with real evidence.** This is deliberately not rounded up to "basically ready" — per this package's own stated primary risk.

## 5. Remaining Work Before Claude Code
- Direct confirmation of `foofoo-v2` folder structure and `CLAUDE.md` presence
- Direct confirmation of `foofoo-mvp` Supabase reachability and schema state
- Confirmation of whether `.claude/` org dotfiles exist in the repo
- The actual trivial migration + rollback test, run and reported

## 6. Recommended Next Action
Hand this package to a session with direct repo/Supabase access (Claude Code, or Claude.ai with a connected GitHub/Supabase tool) whose **only** job is to resolve the 8 NOT VERIFIED Gate items and run the trivial migration test — then return here for a real Gate score before any actual schema/seed work begins.

---

**I'm proposing that "resolve the 8 NOT VERIFIED items" as the next step. Would you like me to proceed with drafting the verification-only Claude Code prompt for that, or hold?**

Founder sign-off: _______________________ Date: ___________
