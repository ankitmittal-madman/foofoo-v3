# [ACTIVE]_DOC-P3-09_Knowledge_Integration_Governance_v1.3

**Version:** 1.3 (supersedes v1.2)
**Date:** 2026-07-03

## Revision Summary (v1.2 → v1.3) — Targeted Amendment Only

Added **§06E — Permanent Document Persistence Rule**, per Founder instruction. Verified first that this exact rule (specifically: the "never rename," "never delete," and "Founder manually manages historical files" clauses) was **not** already present anywhere in v1.2 — the existing naming/versioning convention lived only in `Engineering_Handover_Project_Continuity_Package_v1.3` §6.1 and `Project_Baseline_Register_v1.2` Step 9, neither of which is DOC-P3-09 itself. This amendment consolidates that rule into its proper home (DOC-P3-09, the governance document), stated explicitly rather than by cross-reference. No other section altered. No renumbering. §00–§06D and §07–Completion inherited unchanged from v1.2.

---

## 06E. Permanent Document Persistence Rule *(new in v1.3)*

- Every newly created authoritative project document is named `[ACTIVE]_Document_Name_vX.Y.ext`.
- Version numbers follow semantic versioning (v1.0, v1.1, v1.2, v2.0, etc.).
- At any point in time, only ONE `[ACTIVE]` version of a given document may exist.
- Older versions are never renamed and never deleted by Claude.
- When a new ACTIVE version is generated, Claude states explicitly which previous version it supersedes; Claude does not retroactively edit or relabel the superseded file.
- The Founder manually manages historical file lifecycle (archiving, deletion, relabeling to `[SUPERSEDED]`/`[FROZEN]`/`[ARCHIVED]`) outside of Claude's actions.
- This rule governs all five permitted status values already in use across the project (`[ACTIVE]`, `[FROZEN]`, `[SUPERSEDED]`, `[DRAFT]`, `[ARCHIVED]`) — it does not introduce new statuses, it states the persistence discipline that applies to documents carrying them.

---

## Regression Review (v1.3 addendum)

- ✅ No content altered beyond the single new subsection — §06E is additive only
- ✅ No section renumbered
- ✅ §00–§06D and §07–Completion inherited unchanged from v1.2
- ✅ No Batch 1/2/3/4/5 frozen package touched
- ✅ No schema, architecture, RE, or API content affected — governance-only, consistent with every prior DOC-P3-09 revision

Founder sign-off: _______________________ Date: ___________
