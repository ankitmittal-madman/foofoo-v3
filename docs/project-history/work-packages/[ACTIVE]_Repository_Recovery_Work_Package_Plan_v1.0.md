# Repository Recovery Work Package Plan v1.0

**Status:** DESIGNED — awaiting Founder approval to execute (no WP executed)
**Version:** v1.0
**Date:** 2026-07-13
**Placement:** docs/project-history/work-packages/[ACTIVE]_Repository_Recovery_Work_Package_Plan_v1.0.md
**Supersedes:** None — first Repository Recovery Work Package Plan
**Dependencies:** Repository_Completeness_Audit_v1_0 (evidence), Repository_Recovery_Roadmap_v1_0 (sequence), Repository_Recovery_Backlog_v1_0 (items), Repository_Recovery_Risk_Register_v1_0 (risk), Repository_Recovery_Decision_Log_v1_0 (decisions). WP format derived from REPO-BOOT-02 Task 8.

---

## Executive Summary

Six work packages (WP-5A → WP-5F) carry the repository from its current YELLOW state to a GREEN, frozen baseline. Each follows the repository's established Work Package format. All are DESIGNED only; none is executed by this document. Effort is expressed in relative Claude Code session-units (S = 1 focused session, M = 2–3, L = 4+), never fabricated hours. Every WP requires explicit Founder approval to begin, and each must STOP for approval before the next.

Standing constraints for all WPs: no fabricated SQL, execution, or certificates; frozen architecture untouched; the live database is a read/introspection source for recovery but production (`foofoo-mvp`) is never targeted for seed/validation — Phase-3.5 staging discipline (DOC-P3-10 §23) applies.

---

## WP-5A — Repository Audit  ✅ (this deliverable set)

- **Objective:** Establish exact repository state; produce the six recovery documents.
- **Dependencies:** none.
- **Inputs:** repository @ `4148ce3`.
- **Outputs:** Repository_Completeness_Audit_v1_0 + Backlog + Roadmap + Decision Log + Risk Register + this Plan.
- **Risks:** low — read-only + new docs only.
- **Acceptance:** every gap evidenced with a citation; nothing fabricated/modified.
- **Exit:** Founder accepts the audit.
- **Effort:** S (complete).
- **Founder approval required:** acceptance of findings.

## WP-5B — Migration Recovery

- **Objective:** Restore forward migration files `021`–`026` (including `re_engine.re_dish_regional_affinity`, migration 024) so the repository can rebuild the live schema.
- **Dependencies:** WP-5A accepted; RD-01, RD-02, RD-08.
- **Inputs:** live-DB schema introspection (permitted here, not in the audit); `REPO-WP-02:113` §7.6 descriptions; Architecture Freeze Packs A/B/C; Batch 3–6 specs; ChatGPT originals if RD-01 = YES.
- **Outputs:** six migration files in `database/migrations/`, each verified to match the applied live DDL; a reconciliation note (recovered-vs-applied) — no schema change to the live DB.
- **Risks:** **High** (RR-01) — reconstructed DDL must be byte-faithful to what is applied, or a future rebuild diverges silently. Mitigation: diff reconstructed DDL against live `pg_dump`/`information_schema`; do not invent columns.
- **Acceptance:** a clean-environment apply of `001`–`026` reproduces the live schema object-for-object.
- **Exit:** files committed; reconciliation report filed; STOP.
- **Effort:** M–L.
- **Founder approval required:** to begin, and to accept the source-of-truth path (RD-02).

## WP-5C — Rollback Recovery

- **Objective:** Provide paired, tested rollbacks for migrations `001`–`026`.
- **Dependencies:** WP-5B (for the `020`–`026` sub-track); RD-03. Sub-track `001`–`019` depends only on the already-present forward files and may run in parallel.
- **Inputs:** present forward migrations `001`–`020`; recovered `021`–`026` (WP-5B); DOC-P3-05 §5.3 rollback-pairing rule; the `027`/`028` rollback style (loud-fail-on-seeded-data warning) as the pattern.
- **Outputs:** rollback files for `001`–`026` in `database/rollback/`.
- **Risks:** **High/Medium** (RR-02, RR-03) — a rollback that does not truly reverse its migration fails when needed most. Mitigation: prove each on an empty/staging DB (apply → rollback → re-apply), per REPO-WP-02 §7.4 precedent.
- **Acceptance:** 26/26 forward files have a rollback; at least the highest-risk ones proven by live apply/rollback cycle on staging.
- **Exit:** files committed; rollback-proof report filed; STOP.
- **Effort:** L (19 never-authored + 7 lost = 26 files, each needing correctness proof).
- **Founder approval required:** to begin; RD-03.

## WP-5D — Execution Recovery

- **Objective:** Produce the missing execution certificates for the seed/validation chain (WP-4B, WP-4C, WP-4DB) with real output.
- **Dependencies:** WP-5B + WP-5C complete; RD-01, RD-04.
- **Inputs:** recovered migration set; seeds `100`–`102`; validation `900`–`904` (+ the `WP-3D_Check2_Fix_Reference.sql` fix for 900 Check 2); WP-4B v1.1 / WP-04DB / WP-04DC designs; staging DB.
- **Outputs:** Seed-load Execution Certificate, Validation Execution Certificate (900–904), and resolution of the 901 Test 5 halt (per WP-04DC options) — each with verbatim counts/timestamps, filed in `docs/project-history/certificates/`.
- **Risks:** **Medium** (RR-04) — must record observed output, never expected values; must not silently "pass" the known 901 Test 5 / GRANT-level finding.
- **Acceptance:** every certificate carries real run evidence; WP-4B/4C/4DB statuses become COMPLETED only with the companion certificate (CLAUDE.md rule).
- **Exit:** certificates committed; STOP.
- **Effort:** M.
- **Founder approval required:** to begin; RD-04 (re-run vs. reconstruct-from-logs).

## WP-5E — Repository Freeze

- **Objective:** Close the governance gaps and freeze the repository operating baseline.
- **Dependencies:** WP-5B/5C/5D closed; RD-05, RD-06, RD-07.
- **Inputs:** REPO-BOOT-02 Task 8 (WP template), REPO-BOOT-03 (certificate template), AGR-005/006 (AGR template); CLAUDE.md; DOC-P3-09 §06E.
- **Outputs:** 3 engineering templates + 4 runbooks (location per RD-06); Repository Naming Standard; RACR process definition; approved naming `git mv` normalization (RD-05); README known-gaps update; REPO-BOOT-03 §6 additive errata (RD-07); Repository Freeze Certificate (DRAFT).
- **Risks:** **Low** — additive/documentation; the `git mv` batch is the only non-trivial item (history-preserving, reversible).
- **Acceptance:** every governance backlog item (RB-11..RB-15) closed; freeze rules documented.
- **Exit:** committed; Freeze Certificate drafted for signature; STOP.
- **Effort:** M.
- **Founder approval required:** to begin; RD-05/06/07 (RD-06 is a RACR).

## WP-5F — Repository Green Certification

- **Objective:** Independently re-audit and certify the repository GREEN.
- **Dependencies:** WP-5E closed.
- **Inputs:** the full recovered repository; this audit as the re-run baseline.
- **Outputs:** Repository Health Certificate (GREEN) with a fresh, non-inherited evidence pass.
- **Risks:** **Low** — verification only.
- **Acceptance:** clean-room DB rebuild matches production; 26/26 rollbacks proven; all certificates present; no fabricated/assumed content; naming consistent.
- **Exit:** GREEN certificate signed by Founder.
- **Effort:** S.
- **Founder approval required:** final sign-off.

## Critical Self-Review

- **Considered** folding WP-5A into a preamble rather than a numbered WP. **Kept it numbered** to match the Founder-specified WP-5A..5F structure and to make the audit itself an accountable, acceptance-gated step.
- **Considered** giving concrete hour estimates. **Rejected** — no repository evidence supports hour-level estimates; relative session-units avoid fabricated precision.
- **Considered** letting WP-5D reuse recovered ChatGPT logs as certificates without re-running. **Left as an explicit Founder decision (RD-04)** rather than pre-deciding — re-running is more defensible but costlier, and that trade-off is the Founder's.

## Versioning & Placement

`[ACTIVE]_Repository_Recovery_Work_Package_Plan_v1.0.md` → `docs/project-history/work-packages/`. New file; supersedes nothing. Individual WPs, when authored for execution, become their own `REPO-WP-5x` documents citing this plan.

## Founder Sign-off

Founder approval of the Repository Recovery Work Package Plan: _______________________ Date: ___________
