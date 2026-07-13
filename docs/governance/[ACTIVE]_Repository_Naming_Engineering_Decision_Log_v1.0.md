# [ACTIVE]_Repository_Naming_Engineering_Decision_Log_v1.0

**Status:** ACTIVE — decision log
**Version:** v1.0
**Date:** 2026-07-13
**Placement:** docs/governance/[ACTIVE]_Repository_Naming_Engineering_Decision_Log_v1.0.md
**Supersedes:** None
**Dependencies:** [ACTIVE]_Repository_Naming_Standard_v1.0; [ACTIVE]_Repository_Naming_Conflict_Report_v1.0 (the STOP this WP resolved).

---

## Executive Summary

Engineering decisions taken during the WP-5AA FINAL normalization, each with rationale and reversibility. The earlier WP-5AA STOP (Naming Conflict Report) was lifted by explicit Founder approval (WP-5AA FINAL Steps 3 & 6, which authorize Claude to rename historical files as "repository normalization, NOT relabelling").

## 1. Decision Table

| ID | Decision | Rationale / Evidence | Reversible? |
|---|---|---|---|
| ND-01 | Proceed with the rename pass | WP-5AA FINAL Step 3 ratifies the standard; Step 6 authorizes Claude to rename historical files — resolving the §06E conflict that caused the prior STOP | Yes — `git mv` back |
| ND-02 | Adopt the five-token form `[STATUS]_Name_vX.Y.md` | §06E defines exactly five statuses; WP-5AA's `[ACTIVE]`-only draft could not represent the mostly-non-ACTIVE corpus | Yes |
| ND-03 | Derive each token from the document's own Status header (priority 1) | Step 5 resolution order; e.g. DOC-P3-06/07/08 headers say FROZEN, DOC-P3-04 says DRAFT | Yes |
| ND-04 | Strip `[ACTIVE]_` + version from SQL migrations 001–020 → bare `NNN_description.sql` | Step 7; aligns repo with the live Supabase migration ledger (verified names) | Yes |
| ND-05 | Drop redundant `_FROZEN` suffix on Batch1 Discovery (token now conveys it) | Avoids double status marking | Yes |
| ND-06 | Reference rewrite by literal old→new basename across all tracked text | Guarantees "no broken references"; safe (exact-string, long unique names) | Yes |
| ND-07 | Do NOT rewrite historical narrative in KNOWLEDGE.html (e.g. "why do filenames still say 'Copy of _ACTIVE__'") | Those describe the past state truthfully; editing them would falsify history (CLAUDE.md lifecycle discipline) | N/A |
| ND-08 | Do NOT rewrite before-state evidence tables in the Conflict Report / Completeness Audit | They quote old names as forensic evidence; must remain verbatim | N/A |
| ND-09 | Exception all non-token lifecycle statuses (DESIGNED/EXECUTED/RESOLVED) | Standard §4 forbids guessing; mapping is a Founder decision | Yes (later) |
| ND-10 | Exception all `.docx`/`.html` | `.md` conversion is out of scope; binary status not header-verifiable | Yes (later) |
| ND-11 | Add a naming-enforcement clause to CLAUDE.md | Step 10 — future sessions must not create violating filenames | Yes |
| ND-12 | Version tokens for filename come from the body where filename disagreed (e.g. DOC-P3-02 → v1.1) | Body is authoritative over a stale filename version | Yes |

## 2. Status prose left untouched

Per "do not rewrite document bodies," the `Status:` prose inside each renamed document was left as-authored (it already matched the derived token). Only filenames, and references to renamed files, changed. Internal `Placement:` lines that named the old basename were corrected by the reference rewrite (ND-06).

## Critical Self-Review

- **Considered** editing every renamed doc's internal `Placement:` header to the new path. **Limited to the reference rewrite** — a broad prose edit across 55 Founder-authored docs risked altering content; the basename rewrite fixes the identity portion without touching surrounding text.
- **Limitation:** some internal `Placement:` lines still carry pre-S1 directory paths (a pre-existing issue noted in the Completeness Audit); correcting full stale paths is out of naming-normalization scope.

## Versioning & Placement

`[ACTIVE]_Repository_Naming_Engineering_Decision_Log_v1.0.md` → docs/governance/. New file.

## Founder Sign-off

Founder acceptance: _______________________ Date: ___________
