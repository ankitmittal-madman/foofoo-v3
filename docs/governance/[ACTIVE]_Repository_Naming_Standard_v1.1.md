# [ACTIVE]_Repository_Naming_Standard_v1.1

**Status:** ACTIVE — ratified standard (Founder-approved via WP-5AA FINAL; amended 2026-07-16 per FD-05)
**Version:** v1.1
**Date:** 2026-07-16
**Placement:** docs/governance/[ACTIVE]_Repository_Naming_Standard_v1.1.md
**Supersedes:** `[ACTIVE]_Repository_Naming_Standard_v1.0.md` (retained unchanged, stamped SUPERSEDED, per `CLAUDE.md`'s never-delete rule). All content below is carried forward from v1.0 unchanged except §4A (new) and this header.
**Dependencies:** DOC-P3-09 §06E; CLAUDE.md; Project Baseline Register; `[ACTIVE]_Founder_Decision_Register_v1.0.md` FD-05; `[ACTIVE]_Founder_Ratification_Certificate_2026-07-16_v1.0.md`.

---

## Executive Summary

This is the single canonical naming standard for the FooFoo repository, ratified by the Founder in WP-5AA FINAL. All future files must conform; future Claude Code sessions must never create a file that violates it (enforced via CLAUDE.md). This document states the rules only; the one-time normalization that applied them is recorded in the Repository Normalization Report. **This v1.1 revision resolves FD-05**, the systemic contradiction between `[ACTIVE]`-filename documents and internal "DRAFT — pending Founder sign-off" headers, by clarifying that the two are not the same thing.

## 1. Documents

```
[STATUS]_Document_Name_vMAJOR.MINOR.md
```
- **STATUS** is exactly one of the five DOC-P3-09 §06E values: `ACTIVE`, `DRAFT`, `FROZEN`, `SUPERSEDED`, `ARCHIVED`. No other prefixes.
- **Version** format is `vMAJOR.MINOR` with a single dot: `v1.0`, `v1.1`, `v1.20`, `v2.0`. Never `v1_0`, `1.0`, `v1`, `v01.00`.
- Remove all filename noise: `Copy of `, doubled underscores, stray spaces, redundant status words in the body of the name (e.g. a trailing `_FROZEN`).

## 2. SQL

```
Migrations:  NNN_description.sql          e.g. 001_extensions_and_schema_setup.sql
Rollbacks:   NNN_description_rollback.sql
Seeds:       1NN_description.sql          (100–199)
Validation:  9NN_description.sql          (900–999)
```
SQL carries **no** `[STATUS]` prefix and **no** version suffix. Migration filenames must match the applied Supabase migration ledger name exactly.

## 3. Certificates / Runbooks / Templates

```
Certificates: [ACTIVE]_REPO-CERT-NNN_Name_vMAJOR.MINOR.md
Runbooks:     [ACTIVE]_RUNBOOK_Name_vMAJOR.MINOR.md
Templates:    [ACTIVE]_TEMPLATE_Name_vMAJOR.MINOR.md
```

## 4. Status Resolution (how the token is chosen — no guessing)

Determine the token from repository evidence, in priority order (per WP-5AA Step 5):
1. The document's own explicit **Status** header, mapped to one of the five values.
2. Project Baseline Register.
3. Supersedes relationship (a version superseded by a later one → `SUPERSEDED`).
4. Certificate relationship.
5. Repository history.

**If still ambiguous — or the header uses a lifecycle word that is not one of the five tokens (e.g. `DESIGNED`, `EXECUTED`, `RESOLVED`) — do NOT rename. Record the file in the Exception Register. Never guess.**

## 4A. `[ACTIVE]` Status Does Not Require a Founder Signature Line (FD-05, ratified 2026-07-16)

**Ruling:** A document's `[ACTIVE]` filename token certifies that its content is the currently governing version of that artifact — it does **not** by itself assert that a blank "Founder Sign-off" line at the bottom of the document has been physically countersigned. Several frozen documents (`DOC-P3-02`, `DOC-P3-03`, `DOC-P3-03A`, `DOC-P3-04`, `DOC-P3-05-Part-A`, the APDF vNext Addendum) carried the `[ACTIVE]` filename token while their own internal headers read "DRAFT — pending Founder sign-off," with blank signature lines — a direct contradiction this standard's v1.0 did not resolve.

**Resolution:** `[ACTIVE]` status is conferred by **content freeze** — the document is the artifact the repository actually builds against, cited by downstream Work Packages and code as authoritative — not by a separately executed signature. This is the same ratification mechanism already used elsewhere in the repository (see `[ACTIVE]_Founder_Decision_Register_v1.0.md` §3, "two ratification paths... both valid: document freeze... or AGR"). A document's internal header may still carry historical "pending sign-off" language describing its state *at the time it was authored*; that language does not retroactively make its `[ACTIVE]` filename false. Each of the six documents named above has had its internal header corrected to reflect this ruling (FD-05 execution, 2026-07-16) — see each document's own Founder Ratification Certificate cross-reference.

**Consequence:** No blanket re-signature project is required for documents already carrying `[ACTIVE]`. A document that is genuinely still under active design (not yet built against, not yet cited as authoritative anywhere) should carry `[DRAFT]` in its filename, not `[ACTIVE]` — the filename token and the internal header must agree going forward; this ruling closes the gap for the existing six by correcting their headers, not by relaxing the standard for future documents.

## 5. Extensions

`.docx` and `.html` documents are out of scope for `.md`-form normalization (conversion is content rewriting, not renaming). They remain as-is until a dedicated conversion work package; see the Exception Register.

## 6. Enforcement (future sessions)

CLAUDE.md references this standard. Every new authoritative document, migration, rollback, seed, validation script, certificate, runbook, or template MUST be created in the form above. Renaming an existing file remains a Founder-authorized action (WP-5AA established the precedent; a future bulk rename needs the same explicit authorization).

## Critical Self-Review

- **Considered** an `[ACTIVE]`-only convention (as WP-5AA's non-final draft implied). **Rejected** — the corpus is mostly non-ACTIVE; a single token would force false status. The five-token form is the only one consistent with both §06E and reality.
- **Limitation:** lifecycle words used by the REPO-WP series (`DESIGNED`/`EXECUTED`) and AGRs (`RESOLVED`) are not among the five tokens; mapping them is deferred to a Founder decision rather than guessed (see Exception Register).
- **FD-05 resolution scope:** this amendment resolves the sign-off-vs-filename contradiction only; it does not relax any other requirement of this standard, and does not itself re-ratify the content of the six affected documents beyond their status header.

## Versioning & Placement

`[ACTIVE]_Repository_Naming_Standard_v1.1.md` → docs/governance/. Supersedes `[ACTIVE]_Repository_Naming_Standard_v1.0.md` (retained, stamped, not deleted).

## Founder Sign-off

Founder ratification of this v1.1 amendment (FD-05): Ankit Mittal — 2026-07-16 (per the claude.ai Founder decision-closing session; formalized in `[ACTIVE]_Founder_Ratification_Certificate_2026-07-16_v1.0.md`).
