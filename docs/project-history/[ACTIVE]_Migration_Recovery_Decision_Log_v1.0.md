# Migration Recovery Decision Log v1.0 (WP-5B)

**Status:** ACTIVE — Decision log
**Version:** v1.0
**Date:** 2026-07-13
**Placement:** docs/project-history/[ACTIVE]_Migration_Recovery_Decision_Log_v1.0.md
**Supersedes:** None
**Dependencies:** Migration_Recovery_Report_v1_0, Migration_Recovery_Evidence_Register_v1_0.

---

## Executive Summary

Every engineering decision taken during WP-5B recovery, its rationale, its reversibility, and its confidence. Decisions made autonomously (MADE) were strictly mechanical/evidence-forced; decisions requiring Founder input remain OPEN. No decision altered the database or any existing file.

## 1. Decision Table

| ID | Decision | Status | Rationale / Evidence | Reversible? |
|---|---|---|---|---|
| MRD-01 | Use the live database as the exact-DDL source (Priority 4) rather than reconstruct from prose | MADE | WP-5B Step 5 authorizes it; the live schema IS the executed result of the lost migrations, so this is recovery, not reconstruction. | Yes — files are deletable; DB untouched. |
| MRD-02 | Head every file "RECONSTRUCTED FROM EVIDENCE"; do not present as original | MADE | WP-5B principle #5; CLAUDE.md anti-fabrication. | N/A |
| MRD-03 | Filename convention = bare `NNN_description.sql` (not `[ACTIVE]_…`) | MADE | Matches sibling 027/028 (same authoring era) and the live migration names exactly. | Yes — `git mv`. |
| MRD-04 | Author 021–026 as ALTER/CREATE diffs against migration-020 base state (read from repo files 002/003/008/009) | MADE | Produces a migration that, applied on 020's state, yields the observed live state; forward-compatible with 027/028. | Yes. |
| MRD-05 | Write constraints as inline/explicitly-named to reproduce observed constraint names | MADE | Live constraint names are Postgres auto-names; inline definitions regenerate identical names (verified against `pg_constraint`). | Yes. |
| MRD-06 | Reconstruct the `slot` `USING` conversion expression in 025/026 | MADE (flagged) | Result observed; original text unknowable. Expression is the unique one consistent with REPO-WP-02 §7.6 `'addon' → ['snack']`. Confidence Medium on text, High on result. | Yes. |
| MRD-07 | Omit explicit anon/authenticated GRANTs on cuisines | MADE | Those grants are Supabase project defaults (migration 001 `ALTER DEFAULT PRIVILEGES`), not set by 021; reproducing them would misattribute provenance. | Yes. |
| MRD-08 | Attribute `cuisine_id` FK columns to 021 (not 022) | MADE | Migration named `021_cuisines_reference`; REPO-WP-02 §7.6 groups cuisine table + FK together. Column ordinals (cuisine_id before calories/serving_size) corroborate 021-before-022 ordering. | Yes. |
| MRD-09 | Record `pf1_security_hardening` + `103_production_*` as out-of-scope findings, do not recover | MADE | WP-5B scope is 021–026 only; scope discipline. | N/A |
| MRD-10 | Whether to accept recovered 021–026 as the canonical repo migrations | **OPEN** | Founder acceptance gate (WP-5B Step 11). | — |
| MRD-11 | Source of truth if the Founder later locates byte-originals via ChatGPT | **OPEN** | If originals surface, compare and supersede these reconstructions per DOC-P3-09 §06E. | — |
| MRD-12 | Verify a clean-room rebuild (001–028) matches production | **OPEN** | Recommended before WP-5E freeze; belongs to validation, not this WP. | — |

## Critical Self-Review

- **Considered** making MRD-06 an OPEN Founder decision rather than MADE-flagged. **Resolved as MADE-flagged** — declining to write any conversion would leave 025/026 non-functional as migrations; the expression is evidence-forced, and the flag + reversibility preserve Founder override.
- **Limitation:** MRD-11 means these files carry a standing "supersede if originals found" clause; they are the best available recovery, not a claim that originals are gone forever.

## Versioning & Placement

`[ACTIVE]_Migration_Recovery_Decision_Log_v1.0.md` → `docs/project-history/`. New file.

## Founder Sign-off

Founder acceptance of the Migration Recovery Decision Log: _______________________ Date: ___________
