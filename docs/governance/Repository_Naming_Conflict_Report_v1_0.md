# Repository Naming Conflict Report v1.0 (WP-5AA — STOP)

**Status:** ACTIVE — Conflict report (WP-5AA halted at the mandatory STOP clause; NO renames performed)
**Version:** v1.0
**Date:** 2026-07-13
**Placement:** docs/governance/Repository_Naming_Conflict_Report_v1_0.md
**Supersedes:** None — first Naming Conflict Report
**Dependencies:** CLAUDE.md; DOC-P3-09 §06E; Project Baseline Register v1.5; Repository_Completeness_Audit_v1_0; Repository_Recovery_Decision_Log_v1_0 (RD-05). Produced instead of executing normalization, per WP-5AA Step "Authoritative Sources": *"If any standards conflict, STOP and produce a conflict report instead of making changes."*

---

## Executive Summary

WP-5AA directs a repository-wide filename/metadata/version normalization to the canonical form `[ACTIVE]_<ID>_<Name>_v<Major.Minor>`, executed by Claude Code via `git mv`. Before making any change I read the authoritative sources and ran a full read-only scan. **A material conflict exists between WP-5AA's canonical convention and the higher-precedence project documentation (DOC-P3-09 §06E).** Because WP-5AA itself instructs "STOP and produce a conflict report instead of making changes" on any standards conflict, **no file was renamed and no metadata was edited.** This report documents the conflict with evidence, proposes a resolved standard for Founder ratification, and includes the complete DESIGNED rename/status map so that — once the Founder resolves the conflict — execution is a single mechanical step.

**Nothing in the repository was modified except the creation of this report.**

## 1. The Conflict (with evidence)

### Conflict 1 — Claude may not assign/relabel status tokens (the core blocker)
The canonical convention embeds a governance **status token** (`[ACTIVE]`) in the filename. WP-5AA Step 4 requires "every authoritative active document carries [ACTIVE]" while simultaneously "Do NOT incorrectly mark archived or draft documents as ACTIVE" and "superseded documents keep their historical status." Satisfying this requires assigning each file the *correct* token from the five permitted values.

DOC-P3-09 §06E (verified verbatim, lines 17–19) states:
- *"Older versions are never renamed and never deleted by Claude."*
- *"Claude does not retroactively edit or relabel the superseded file."*
- *"The Founder manually manages historical file lifecycle (archiving, deletion, relabeling to `[SUPERSEDED]`/`[FROZEN]`/`[ARCHIVED]`) outside of Claude's actions."*

Assigning `[DRAFT]`/`[FROZEN]`/`[SUPERSEDED]` tokens to the ~30 mis-labeled files below is precisely the relabeling §06E reserves to the Founder. **WP-5AA (a Founder instruction) and §06E (Project Documentation) are in direct conflict**, and the governing precedence order (global CLAUDE.md: 1. Project Documentation → 2. Founder Decisions) places §06E above an ad-hoc instruction that does not itself amend §06E.

### Conflict 2 — The current `[ACTIVE]` token is already false for most files
The filename token cannot simply be preserved, because the scan proves it is wrong. Evidence (filename claim vs. the document's own Status header):

| File (current) | Filename claims | Header actually says | Correct token |
|---|---|---|---|
| `Copy of _ACTIVE__DOC-P3-04_..._v1_3.md` | ACTIVE | "DRAFT — pending founder sign-off" | [DRAFT] |
| `Copy of _ACTIVE__DOC-P3-02_..._v1.0.md` | ACTIVE, v1.0 | "DRAFT v1.1 — pending sign-off" | [DRAFT], v1.1 |
| `Copy of _ACTIVE__DOC-P3-06_..._v1_2.md` | ACTIVE | "APPROVED — ACTIVE — FROZEN" | [FROZEN] |
| `Copy of _ACTIVE__DOC-P3-07_..._v1_2.md` | ACTIVE | "ACTIVE — APPROVED — FROZEN" | [FROZEN] |
| `Copy of _ACTIVE__DOC-P3-08_..._v1_1.md` | ACTIVE | "ACTIVE — APPROVED AND FROZEN" | [FROZEN] |
| `REPO-WP-03_..._v1.0.md` | (none) | "⚠️ SUPERSEDED BY v1.1" | [SUPERSEDED] |
| `Copy of _ACTIVE__APDF_Framework_Base_v1.md` | ACTIVE | superseded by vNext Addendum | [SUPERSEDED]? |
| `Copy of _ACTIVE__APDF_..._vNext_Addendum_v2_0.md` | ACTIVE | "Draft — Ready for Founder Review" | [DRAFT] |
| `_ACTIVE__Batch1_Discovery_..._FROZEN.md` | ACTIVE + FROZEN suffix | "APPROVED — ACTIVE — FROZEN" | [FROZEN] |
| `_ACTIVE__Batch2_Mapping_..._v1_0.md` | ACTIVE | "Draft — Ready for Founder Review" | [DRAFT] |
| …(≈30 files total exhibit a token/header mismatch) | | | |

Determining each correct token is a per-document governance judgment (e.g., *is a base framework "superseded" by a still-DRAFT replacement? Is "READY FOR FOUNDER REVIEW" ACTIVE or DRAFT? Are the DOC-P3-05 completion summaries a certificate class?*). These are Founder lifecycle decisions under §06E, not mechanical string edits.

### Conflict 3 — The cited "Repository Naming Standard" does not exist
WP-5AA lists "Repository Naming Standard (if present)" as an authoritative source. It is **not present** (it was only *designed* in an earlier governance proposal, never ratified/committed). There is therefore no ratified standard to normalize *against* — only WP-5AA's inline proposal, which is what conflicts with §06E.

### Conflict 4 — Convention under-specified + version/format collisions
- The canonical pattern only shows `[ACTIVE]_…`; it defines no filename form for `[DRAFT]`/`[FROZEN]`/`[SUPERSEDED]`/`[ARCHIVED]`, yet those dominate the corpus.
- Version rule `v1_0 → v1.0` collides with existing committed precedent: 66 tracked files use `v1_0`, including documents committed days ago under WP-5A/WP-5B; applying it re-touches recently-committed files and mixes with `.` already used elsewhere.
- 19 `.docx` files cannot meet a `.md`-based convention without content conversion — explicitly out of scope ("NOT documentation rewriting").
- Filename-vs-body version mismatches (e.g., DOC-P3-02 filename `v1.0` vs body `v1.1`) require picking a version — a Founder decision.

## 2. Scan Results (Step 2, read-only)

| Convention bucket | Count | Canonical target |
|---|---|---|
| `Copy of _ACTIVE__…` | 48 | strip "Copy of "; token per §06E status |
| `_ACTIVE__…` (no "Copy of") | 19 | `[ACTIVE]_`/correct token |
| `[ACTIVE]_…` (bracket, incl. SQL 001-020 + RE docs) | 28 | keep bracket for docs; **strip entirely for migration SQL** |
| `.docx` | 19 | out of scope (no `.md` conversion) |
| version `v1_0`-style | 66 | `v1.0` (disputed — see Conflict 4) |
| migration SQL `… 1.0.sql` (spaced) | 19 | `NNN_description.sql` (no token/version) |

## 3. Proposed Resolved Standard (for Founder ratification — NOT yet applied)

To make the convention executable, §06E's five status values must each get a filename form:

```
Documents:    [<STATUS>]_<ID>_<Name>_v<Major.Minor>.md
              <STATUS> ∈ { ACTIVE, DRAFT, FROZEN, SUPERSEDED, ARCHIVED }
Certificates: [ACTIVE]_REPO-CERT-<NNN>_<Name>_v<Major.Minor>.md
Runbooks:     [ACTIVE]_RUNBOOK_<Name>_v<Major.Minor>.md
Templates:    [ACTIVE]_TEMPLATE_<Name>_v<Major.Minor>.md
Migrations:   NNN_description.sql            (no token, no version — matches live ledger + 021-028)
Rollbacks:    NNN_description_rollback.sql
Seeds:        1NN_description.sql
Validation:   9NN_description.sql
Version:      v<Major>.<Minor>  (single dot; e.g. v1.0, v1.3)
```
This extends WP-5AA's `[ACTIVE]`-only pattern to the four other §06E statuses so that Step 4's "don't mark draft/superseded as ACTIVE" can actually be honored.

## 4. Founder Resolutions Required (to lift the STOP)

1. **Authorize Claude to assign status tokens from each document's own Status header** (a one-time, evidence-based amendment to §06E), OR supply the token for each file in the Appendix map yourself.
2. **Ratify the expanded standard in §3** (or amend it).
3. **Decide the version-format question** (`v1_0` → `v1.0` repo-wide, including files just committed?).
4. **Confirm `.docx` handling** (leave as-is / defer conversion to a separate WP).
5. **Confirm the version to stamp** where filename and body disagree (e.g., DOC-P3-02).

## 5. Clean, Zero-Conflict Subset (executable immediately on narrow approval)

**Migration SQL `001`–`020`** carry an `[ACTIVE]_` prefix and a spaced ` 1.x` version that the canonical SQL convention forbids and that mismatches the live migration ledger (which names them bare, e.g. `001_extensions_and_schema_setup`). Renaming `"[ACTIVE]_001_extensions_and_schema_setup 1.0.sql"` → `"001_extensions_and_schema_setup.sql"` (via `git mv`) involves **no status token** and aligns the repo with `list_migrations`. This bucket alone has zero §06E conflict and can proceed the moment the Founder approves it — recommended as WP-5AA's first executed step. (Also fixes the `008_content_core1.1.sql` missing-underscore typo → `008_content_core.sql`.)

## 6. Appendix — Full DESIGNED Rename/Status Map

*(Provided so approval → execution is mechanical. Status tokens below are DERIVED FROM EACH DOCUMENT'S OWN HEADER and are PROPOSED, not applied — assigning them is the §06E Founder action this report is blocked on.)*

- **→ [FROZEN]:** DOC-P3-06, DOC-P3-07, DOC-P3-08 (`.docx` — token in filename only if converted); Batch1 {Discovery, Canonicalization, Mapping, GapAnalysis, Architecture Confirmation} v1.1; Batch2 Discovery v1.1; Batch5 Pipeline v1.1.
- **→ [DRAFT]:** DOC-P3-02, DOC-P3-03, DOC-P3-03A, DOC-P3-04, DOC-P3-05 Part A; APDF vNext Addendum v2.0; REPO-BOOT-01, REPO-BOOT-02; Phase3_5 Architecture Decision Review, Architecture Freeze; Batch1 {Governance Evaluation, Resolution}; Batch2 {Canonicalization, GapAnalysis, Mapping, Resolution}; Batch3/Batch4/Batch6 pipelines; Batch4 Technical Review.
- **→ [ACTIVE]:** Project Baseline Register v1.5; DOC-P3-09 v1.3; DOC-P3-10 v1.1; Architecture Gap Register v1.1; Governance Improvement Backlog v1.2; Phase2 Knowledge Acquisition v1.2; Engineering Handover v1.3; FooFoo Roadmap v1.1; PM-SUPP-01/02.
- **→ [SUPERSEDED]:** REPO-WP-03 v1.0 (by v1.1); APDF Base v1 (by vNext); Project_Baseline_Register_v1_1.docx (by v1.5).
- **→ status TBD by Founder:** DOC-P3-05 Part B/C/D + Regression completion summaries (certificate class?); DOC-P3-08 Readiness Report ("READY FOR FOUNDER REVIEW").
- **→ bare SQL (no token):** migrations 001–020 (§5).

## 7. Exception Register (files that must remain unchanged regardless)

| File(s) | Why left unchanged |
|---|---|
| 19 `.docx` files | `.md`-based convention needs content conversion — out of scope |
| `REPO-WP-03 v1.0`, `APDF Base v1`, `Baseline Register v1_1.docx` | superseded older versions — §06E forbids Claude renaming them |
| migrations `021`–`028`, seeds `100`–`102`, validation `900`–`904` | already canonical (`NNN_description.sql`) |
| My WP-5A/5B docs (`Repository_*`, `Migration_*` `_v1_0`) | pending the version-format decision (Conflict 4.2) to avoid churn |
| `CLAUDE.md`, `docs/README.md`, `KNOWLEDGE.html`, `.claude/skills/*` | not versioned project documents under this convention |

## Critical Self-Review

- **Considered** proceeding with the full normalization by inferring status tokens from headers (I have the evidence). **Rejected** — §06E explicitly forbids Claude relabeling historical files, it outranks an ad-hoc instruction per the precedence order, and WP-5AA's own STOP-on-conflict clause is unambiguous. Proceeding would be the exact unilateral overreach this project's governance was built to prevent.
- **Considered** executing the clean SQL subset (§5) now. **Held** — WP-5AA says "produce a conflict report *instead of making changes*"; I surface the subset as ready-to-go rather than acting unilaterally.
- **Considered** producing the three exact documents Step 8 names. **Adapted** — those presume normalization occurred; producing them now would misrepresent an execution that did not happen. This single report carries their intended content (map = Normalization Report; §6 status = Metadata Report; §7 = Exception Register), honestly labeled PROPOSED.
- **Limitation:** status tokens in §6 are derived from headers as of `12213b5`; the Founder may reclassify any of them.

## Versioning & Placement

`Repository_Naming_Conflict_Report_v1_0.md` → `docs/governance/`. New, additive file; supersedes nothing; renames nothing.

## Founder Sign-off

Founder resolution of the naming conflict (authorize token assignment + ratify standard, or direct otherwise): _______________________ Date: ___________
