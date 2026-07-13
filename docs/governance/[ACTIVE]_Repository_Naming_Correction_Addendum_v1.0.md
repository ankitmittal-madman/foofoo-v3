# [ACTIVE]_Repository_Naming_Correction_Addendum_v1.0

**Status:** ACTIVE — correction addendum to the WP-5AA normalization
**Version:** v1.0
**Date:** 2026-07-13
**Placement:** docs/governance/[ACTIVE]_Repository_Naming_Correction_Addendum_v1.0.md
**Supersedes:** None (additive addendum; does not edit the original Normalization Report in place, per DOC-P3-09 §06E)
**Dependencies:** [ACTIVE]_Repository_Naming_Standard_v1.0; [ACTIVE]_Repository_Normalization_Report_v1.0; [ACTIVE]_Repository_Naming_Exception_Register_v1.0 (rewritten in this pass).

---

## Executive Summary

After the first WP-5AA normalization pass (commit `8995074`), the Founder issued four correcting directives. This addendum records them verbatim, the evidence-based decisions made in response, and the resulting second rename pass — 58 additional files renamed, bringing total normalized files to 133. It does not edit the original Normalization Report; it supersedes its *conclusions* where they conflict, per the standing "never delete, always add an additive correction" rule.

## 1. Founder Directives (verbatim)

1. "All Draft versions with latest versions are final one hence do not explicit review of founder"
2. "Frozen and Active should be same. Shouldn't create conflicts"
3. "Both APDF documents are important — 1.0 provide complete view of all documents while 1.1 give addendum to it"
4. "Changes are not done in Product, Governance or to some files. Please check name conventions in those files too"

## 2. Interpretation & Evidence

**Directive 1** — a document carrying `DRAFT`/`DESIGNED` status that has no later superseding version is, per the Founder, final: it does not need an "awaiting Founder review" gate reflected in its filename. Applied to: the 22 files already tokened `[DRAFT]`, plus the DESIGNED-status REPO-WP exception set, plus 13 Product/Architecture/Governance/Roadmap/Visuals files that were re-examined this pass (see §4) and found to carry the identical "DRAFT ... pending founder review" pattern while being their only/latest version.

**Directive 2** — `[FROZEN]` and `[ACTIVE]` must not coexist as if they meant different things for the same class of document (both mean "currently in force"). Applied to: the 10 files tokened `[FROZEN]` in the first pass, and — reading the same principle across to the other non-token lifecycle words — `EXECUTED` (REPO-WP-02) and `RESOLVED` (AGR-005/006), which are the same "done/current, not pending" concept as FROZEN.

**Directive 3** — APDF Framework Base v1.0 is not obsolete; it remains the complete reference and the vNext Addendum v2.0 is additive to it, not a replacement. Evidence check: vNext Addendum's own header already says "Supersedes: `APDF_Framework_v1.md` (retained unmodified)" — this phrase describes retention/extension, not the Base being inert. Correction: Base v1.0 reclassified `[SUPERSEDED]→[ACTIVE]`; vNext Addendum was already moving to `[ACTIVE]` under Directive 1.

**Directive 4** — a re-scan found 13 files under `docs/product/`, `docs/architecture/`, `docs/governance/`, `docs/roadmaps/`, `docs/visuals/` still carrying `Copy of _ACTIVE__` names. These had been left as "binary .docx, out of scope" in the first pass. Re-inspection with `file(1)` showed 13 of them are **plain UTF-8 text with a `.docx`/`.html` extension**, not real binaries — so their headers were readable. All 13 carry an explicit `DRAFT ... pending founder review` (or, for the visuals HTML, no status marker at all and no competing version) status and are each the only/latest version of their document. Applied per Directive 1. One file (`Project_Baseline_Register_v1_1_md.docx`) was found to be a genuine older version explicitly superseded by v1.5 — correctly left `[SUPERSEDED]`, not pulled to ACTIVE (Directive 1 only covers the *latest* version).

## 3. What changed in this pass — 58 renames

- **32** files collapsed from `[DRAFT]`/`[FROZEN]`/non-token (`DESIGNED`/`EXECUTED`/`RESOLVED`) → `[ACTIVE]`.
- **1** file (`APDF_Framework_Base_v1.0`) moved `[SUPERSEDED]→[ACTIVE]` (Directive 3).
- **1** file (`REPO-WP-03_v1.0`) newly assigned `[SUPERSEDED]` (it already had a valid token, `SUPERSEDED`, that the first pass had mis-filed as an "exception" instead of applying — corrected here).
- **13** Product/Architecture/Governance/Roadmap/Visuals files renamed from `Copy of _ACTIVE__…` → `[ACTIVE]_…` (Directive 4), using real header evidence.
- **1** file (`Project_Baseline_Register_v1_1_md.docx`) renamed `Copy of _ACTIVE__…` → `[SUPERSEDED]_…` (genuine supersession, confirmed by its own `Supersedes:` chain).

Full list: see the updated Rename Mapping Table (Part 2, this pass).

## 4. What did NOT change (still exceptions)

9 files remain unresolved — 2 with a genuine identity conflict (the two SESSION_HANDOFF files), and 7 with no lifecycle word or version at all (Project_Checkpoint; the 4 DOC-P3-05 completion summaries; the 2 P3-03 readiness/quality-gate docs). Directives 1–4 do not provide evidence to classify these, so per the Naming Standard's "never guess" rule they remain in the Exception Register (rewritten this pass) pending direct Founder classification.

## 5. Totals after both passes

| | Pass 1 | Pass 2 | Cumulative |
|---|---|---|---|
| Files renamed | 75 | 58 | **133** |
| Documents at `[ACTIVE]` | 22 | +45 | **67** |
| Documents at `[SUPERSEDED]` | 1 | net 0 (+1 −1 reclass, +1 new) | **2** |
| Documents at `[DRAFT]`/`[FROZEN]` | 32 | −32 | **0** |
| Remaining exceptions | 42 | −33 | **9** |

## Critical Self-Review

- **Considered** collapsing the 9 remaining exceptions too, reading the Founder's directives broadly. **Rejected** — none of the 9 carry a lifecycle word or version the directives address; doing so would be guessing, which every version of this standard forbids.
- **Considered** editing the original Normalization Report/Exception Register in place rather than adding this addendum + rewriting the Exception Register. **Resolved:** the Exception Register was rewritten (its job is "current state of exceptions," which changed factually) while this addendum preserves the original report's history rather than silently erasing what the first pass believed and why — consistent with DOC-P3-09 §06E's "state what you supersede, don't retroactively edit."
- **Limitation:** the visuals HTML (`DOC-06_Visual_Design_System_Explorer`) had no explicit status marker at all; it was defaulted to `[ACTIVE]` on the strength of being an undisputed, only-version companion artifact to the now-`[ACTIVE]` DOC-06, not on direct textual evidence of its own — the weakest inference in this pass, flagged here for visibility.

## Versioning & Placement

`[ACTIVE]_Repository_Naming_Correction_Addendum_v1.0.md` → docs/governance/. New file.

## Founder Sign-off

Founder acceptance of this correction addendum: _______________________ Date: ___________
