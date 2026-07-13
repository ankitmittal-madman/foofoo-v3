# [ACTIVE]_Rollback_Decision_Log_v1.0

**Status:** ACTIVE — decision log
**Version:** v1.0
**Date:** 2026-07-13
**Placement:** docs/governance/[ACTIVE]_Rollback_Decision_Log_v1.0.md
**Supersedes:** None
**Dependencies:** [ACTIVE]_WP-5C_Rollback_Recovery_Report_v1.0.

---

## Executive Summary

Engineering decisions taken during WP-5C rollback recovery, with rationale and reversibility. Every decision was constrained by the forward-migration evidence and the 027/028 precedent; none modified a forward migration, architecture, or the live database.

## 1. Decision Table

| ID | Decision | Rationale / Evidence | Reversible? |
|---|---|---|---|
| RBD-01 | Reconstruct each rollback from its forward migration file | The DDL a migration creates is exactly what its rollback drops; the forward file is the authoritative source (session-resume: documentation over memory) | Yes — delete/rewrite the rollback |
| RBD-02 | Use plain `DROP` / `DROP SCHEMA … RESTRICT`, not `CASCADE` | Loud failure on out-of-order or populated-data application is safer than silent cascade; matches 027/028 precedent | Yes |
| RBD-03 | Design for reverse-order application (028→001), documented in the Dependency Graph | A migration can depend on any earlier one; only reverse order guarantees clean teardown | N/A (documentation) |
| RBD-04 | 018 rollback is a deliberate no-op (`SELECT 1`) | Migration 018 is an empty retired placeholder (AGR-002); a rollback that dropped anything would be wrong | Yes |
| RBD-05 | 017 rollback uses a dynamic `pg_inherits` `DO` block | Partition names are generated from `CURRENT_DATE` at deploy; a static name list would miss real partitions | Yes |
| RBD-06 | 001 rollback drops the extension with `IF EXISTS` and warns it may be a PG13+ core function | Faithful reversal of `CREATE EXTENSION` without breaking on a core-provided `gen_random_uuid` | Yes |
| RBD-07 | 023/025/026 reversals authored as lossy/loud-failing, with explicit WARNING headers | Restoring the original global unique / scalar `slot` cannot represent post-migration data; failing loudly beats silent corruption — 027/028 precedent | Yes |
| RBD-08 | Reuse WP-5B live-introspection evidence (trigger bindings, constraint names) read-only; do NOT re-query the DB | WP-5C is repository reconstruction, not a DB audit; the forward files + prior evidence suffice | N/A |
| RBD-09 | Name files `NNN_description_rollback.sql` (canonical SQL form) | `[ACTIVE]_Repository_Naming_Standard_v1.0` §SQL: no status token, no version, match migration basename | Yes |
| RBD-10 | Defer live teardown execution to WP-5F | Executing a full teardown is higher blast-radius than authoring SQL; belongs to its own approved WP | N/A |

## 2. Non-decisions (explicitly out of scope)

No forward migration authored/edited; no schema/architecture change; no live database modification; no seed/validation change; the 9 WP-5AA naming exceptions untouched; the out-of-scope applied-but-missing migrations (`pf1_security_hardening`, `103_production_*`) not recovered (they are forward migrations, not rollbacks — flagged for a future WP).

## Critical Self-Review

- **Considered** authoring rollbacks for the three out-of-scope applied migrations (pf1, 103_*) while "in the rollback layer." **Rejected** — they have no forward file in the repo, so a rollback would have nothing authoritative to reverse; recovering the forward files first is a separate WP.
- **Limitation:** RBD-08 means correctness rests on the forward files matching the live DB for 001–020; this is asserted by REPO-WP-02's certified execution, not re-proven here.

## Versioning & Placement

`[ACTIVE]_Rollback_Decision_Log_v1.0.md` → docs/governance/. New file.

## Founder Sign-off

Founder acceptance: _______________________ Date: ___________
