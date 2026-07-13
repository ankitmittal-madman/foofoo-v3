# Repository Recovery Decision Log v1.0

**Status:** ACTIVE — Decision log (open decisions awaiting Founder; no decision executed)
**Version:** v1.0
**Date:** 2026-07-13
**Placement:** docs/governance/[ACTIVE]_Repository_Recovery_Decision_Log_v1.0.md
**Supersedes:** None — first Repository Recovery Decision Log
**Dependencies:** Repository_Completeness_Audit_v1_0, Repository_Recovery_Backlog_v1_0, Repository_Recovery_Risk_Register_v1_0.

---

## Executive Summary

This log records every decision the recovery effort requires, who owns it, its current status, and the evidence framing it. It follows the never-delete-a-row discipline of the Architecture Gap Register. No decision below has been made or executed by this audit; all are **OPEN** pending Founder (and, where noted, a ChatGPT gap-audit answer). Each row states the options without pre-selecting one, matching the Architecture Decision Review precedent.

## 1. Decision Table

| ID | Decision required | Owner | Status | Options / Evidence |
|---|---|---|---|---|
| RD-01 | Answer the single ChatGPT gap-audit question: *does ChatGPT hold the original 021–026 migration/rollback files and/or the WP-4B/4C/4DB run outputs?* | Founder → ChatGPT | OPEN | YES → supply them (fastest, R4). NO → recover via live-DB introspection + re-run-with-certification (R3). Gate for RD-02/RD-05. |
| RD-02 | Source of truth for recovering 021–026 DDL | Founder | OPEN | (a) Live-DB introspection reconciled to WP-02 §7.6 + Freeze Packs [recommended if RD-01=NO]; (b) ChatGPT originals [if RD-01=YES]. |
| RD-03 | Author the 19 never-existent rollbacks (001–019)? | Founder | OPEN | (a) Yes, as part of recovery (closes RR-03, needed for an honest Repository Gate); (b) defer. Forward files are in-repo, so authorship is unblocked either way. |
| RD-04 | Re-run vs. reconstruct-from-logs for WP-4B/4C/4DB certificates | Founder | OPEN | (a) Re-run against DB and certify [most defensible]; (b) accept recovered ChatGPT logs as the certificate evidence [faster, weaker]. |
| RD-05 | Naming normalization to `[ACTIVE]_…_vX_Y` (DOC-P3-09 §06E) | Founder | OPEN | §06E reserves renaming to the Founder. (a) Approve a history-preserving `git mv` batch; (b) leave as-is. No rename performed without this. |
| RD-06 | Create `engineering/` top-level folder for templates/runbooks | Founder (RACR) | OPEN | New top-level folder ⇒ requires a Repository Architecture Change Request per CLAUDE.md "Placement Rule". Alternative: place under `docs/`. |
| RD-07 | Correct REPO-BOOT-03 §6 via additive errata before signing | Founder | OPEN | (a) Add dated errata (original text untouched, per §06E); (b) sign as-is [not recommended — see RR-09]. |
| RD-08 | Verify live-DB state (introspection) as a recovery input | Founder | OPEN | Permitted in recovery (not in this audit). Confirms the 28-migration / 143-row / 27-table claims before certification. |
| RD-09 | Sequence: recover DB first vs. governance (templates/naming) first | Founder | OPEN | Dependency graph (Recovery Roadmap §3) recommends DB-first (WP-5B) because RR-01 is the only Critical risk. |

## 2. Decisions explicitly NOT in recovery scope

The three PIR architecture decisions (cuisine persistence, tag-vector confirmation, combo-role vocabulary), the DPDP age-verification gate, and IDR-001 master data are pre-existing product/architecture decisions tracked elsewhere (Architecture Freeze; Gap Register; DOC-P3-10). They are noted here only so the recovery effort does not silently absorb them.

## Critical Self-Review

- **Considered** recommending a single option per decision. **Followed the Architecture Decision Review precedent instead** — options are laid out, recommendations are flagged as such, but none is selected. Pre-selecting a Founder decision would exceed this audit's report-only mandate.
- **Considered** treating RD-01 as answerable now. **Rejected** — this is a non-interactive session with no ChatGPT access; RD-01 must be relayed to the Founder.

## Versioning & Placement

`[ACTIVE]_Repository_Recovery_Decision_Log_v1.0.md` → `docs/governance/`. New file; supersedes nothing. Rows are appended and status-updated in future versions, never deleted.

## Founder Sign-off

Founder acceptance of the Repository Recovery Decision Log: _______________________ Date: ___________
