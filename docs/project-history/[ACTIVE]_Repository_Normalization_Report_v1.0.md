# [ACTIVE]_Repository_Normalization_Report_v1.0

**Status:** ACTIVE — normalization execution report
**Version:** v1.0
**Date:** 2026-07-13
**Placement:** docs/project-history/[ACTIVE]_Repository_Normalization_Report_v1.0.md
**Supersedes:** None
**Dependencies:** [ACTIVE]_Repository_Naming_Standard_v1.0; [ACTIVE]_Repository_Rename_Mapping_Table_v1.0; [ACTIVE]_Repository_Naming_Exception_Register_v1.0; [ACTIVE]_Repository_Naming_Validation_Report_v1.0; [ACTIVE]_Repository_Naming_Engineering_Decision_Log_v1.0.

---

## Executive Summary

WP-5AA FINAL applied the ratified Repository Naming Standard in one controlled pass. **75 files were renamed via `git mv` (history preserved); 55 documents received a correct `[STATUS]_…_vX.Y` name and 20 SQL migrations were reduced to the canonical bare `NNN_description.sql` form (aligning the repo with the live Supabase ledger).** References were rewritten so nothing breaks. 19 documents + 23 binaries were deliberately left unchanged (Exception Register), because assigning them a name would have required guessing a status the evidence does not support. CLAUDE.md now enforces the standard for future sessions.

## 1. What changed

| Category | Renamed | Target form |
|---|---|---|
| Documents → `[ACTIVE]` | 22 | governing/living/latest docs (Baseline Register, DOC-P3-09/10/12, Gap Register, roadmaps, recovery/audit set, …) |
| Documents → `[DRAFT]` | 22 | "Ready for Founder Review" docs (DOC-P3-02/03/03A/04/05A, APDF vNext, Freeze/Decision Review, REPO-BOOT-01/02/03, most Batch2–6 packages) |
| Documents → `[FROZEN]` | 10 | "APPROVED — ACTIVE — FROZEN" (DOC-P3-06/07/08, frozen Batch1/2/5 packages) |
| Documents → `[SUPERSEDED]` | 1 | APDF Framework Base (superseded by vNext) |
| SQL migrations → bare | 20 | `001`–`020` `_description.sql` |
| **Total renamed** | **75** | |

Full old→new list: see the Rename Mapping Table. Token derivation and judgment calls: see the Engineering Decision Log.

## 2. References & metadata

- Cross-references to renamed files were rewritten (literal old→new basename) across all tracked `.md`/`.html`/`.sql` — 12 files updated, including KNOWLEDGE.html and the recovery/audit doc set.
- `Status:` prose inside documents was left as authored (already consistent with the derived token); only filenames and references changed.
- CLAUDE.md updated with a naming-enforcement clause pointing at the Naming Standard (Step 10).

## 3. Exceptions (unchanged) — summary

- **11** files with a non-token lifecycle status (`DESIGNED`/`EXECUTED`/`RESOLVED`: the REPO-WP series, AGR-005/006, Recovery WP Plan).
- **8** files with no version and/or no status token (completion summaries, readiness/quality-gate docs, SESSION_HANDOFF-4, Project_Checkpoint).
- **23** binary `.docx`/`.html` (out-of-scope for `.md` conversion).

Reasons + recommended actions: Exception Register. All are resolvable in short follow-ups once the Founder ratifies the `DESIGNED/EXECUTED/RESOLVED` → token mapping and the binary-conversion approach.

## 4. Repository Health Update (before → after)

| Dimension | Before (post-WP-5B) | After (WP-5AA) |
|---|---|---|
| Filename convention | 🔴 3 conflicting styles; `[ACTIVE]` token false on ~30 files | 🟢 single 5-token standard applied to all normalizable docs; SQL matches live ledger |
| Version format | 🟡 mixed `v1_0`/`1.0`/spaced | 🟢 `vX.Y` across renamed set |
| Governance ratification | 🟡 no ratified naming standard | 🟢 standard ratified + CLAUDE.md-enforced |
| Broken references | 🟢 none | 🟢 none (rewritten) |
| Git history | 🟢 intact | 🟢 intact (`git mv` only) |
| Remaining naming debt | — | 🟡 19 docs + 23 binaries pending Founder mapping decision (tracked) |

**Overall: YELLOW → YELLOW-improving.** Naming is no longer a governance conflict; residual items are bounded, tracked, and Founder-gated. (DB-layer items — rollbacks 001–026, WP-4B/4DB certificates, the out-of-scope `pf1`/`103_*` migrations — are unchanged by this WP.)

## Critical Self-Review

- **Considered** forcing every file to conform (including lifecycle-word and binary files). **Rejected** — would have required guessing statuses or content conversion, violating the Naming Standard's own "never guess" rule and WP scope. Bounded exceptions with a clear resolution path are the higher-integrity outcome.
- **Limitation:** ~42 files remain non-canonical (exceptions); this is a deliberate, documented pause, not an oversight.

## Versioning & Placement

`[ACTIVE]_Repository_Normalization_Report_v1.0.md` → docs/project-history/. New file.

## Founder Sign-off

Founder acceptance of the Normalization Report: _______________________ Date: ___________
