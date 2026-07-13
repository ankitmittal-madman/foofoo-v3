# [ACTIVE]_Repository_Naming_Standard_v1.0

**Status:** ACTIVE — ratified standard (Founder-approved via WP-5AA FINAL)
**Version:** v1.0
**Date:** 2026-07-13
**Placement:** docs/governance/[ACTIVE]_Repository_Naming_Standard_v1.0.md
**Supersedes:** None — first ratified Repository Naming Standard. Extends DOC-P3-09 §06E (which it does not contradict: §06E fixes the five status values and the persistence discipline; this standard fixes the filename form and, per WP-5AA Step 6, authorizes Claude to apply it via `git mv`).
**Dependencies:** DOC-P3-09 §06E; CLAUDE.md; Project Baseline Register.

---

## Executive Summary

This is the single canonical naming standard for the FooFoo repository, ratified by the Founder in WP-5AA FINAL. All future files must conform; future Claude Code sessions must never create a file that violates it (enforced via CLAUDE.md). This document states the rules only; the one-time normalization that applied them is recorded in the Repository Normalization Report.

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

## 5. Extensions

`.docx` and `.html` documents are out of scope for `.md`-form normalization (conversion is content rewriting, not renaming). They remain as-is until a dedicated conversion work package; see the Exception Register.

## 6. Enforcement (future sessions)

CLAUDE.md references this standard. Every new authoritative document, migration, rollback, seed, validation script, certificate, runbook, or template MUST be created in the form above. Renaming an existing file remains a Founder-authorized action (WP-5AA established the precedent; a future bulk rename needs the same explicit authorization).

## Critical Self-Review

- **Considered** an `[ACTIVE]`-only convention (as WP-5AA's non-final draft implied). **Rejected** — the corpus is mostly non-ACTIVE; a single token would force false status. The five-token form is the only one consistent with both §06E and reality.
- **Limitation:** lifecycle words used by the REPO-WP series (`DESIGNED`/`EXECUTED`) and AGRs (`RESOLVED`) are not among the five tokens; mapping them is deferred to a Founder decision rather than guessed (see Exception Register).

## Versioning & Placement

`[ACTIVE]_Repository_Naming_Standard_v1.0.md` → docs/governance/. New file; supersedes nothing.

## Founder Sign-off

Founder ratification of the Repository Naming Standard: _______________________ Date: ___________
