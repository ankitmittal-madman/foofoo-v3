# [ACTIVE]_WP-12_Planning_Semantics_Architecture_Batch_v1.0

**Status:** ACTIVE — docs-only commit, Founder-approved 2026-07-17, certified REPO-CERT-023. Final Architecture Baseline Review performed and passed (§5): READY WITH MINOR DOCUMENTATION NOTES. No implementation, no schema, no code, no data changes.
**Version:** v1.0
**Date:** 2026-07-17
**Placement:** docs/project-history/work-packages/[ACTIVE]_WP-12_Planning_Semantics_Architecture_Batch_v1.0.md
**Builds on:** the Persona/Cohort Domain sections of `[ACTIVE]_DOC-P3-02_Conceptual_Domain_Model_v1.1.md`; the WP-8E finding (item 6) that `re_segment_addon_rule` does not exist as a table and the LF-C add-on path needs reconciling; FD-06 (member add-on build-order priority, still separately Pending).
**Governance basis (ratified this batch):** `[ACTIVE]_Founder_Decision_Register_v1.0.md` FD-15.

---

## Executive Summary

Four Founder-approved design documents from the claude.ai Planning Semantics track are committed to `docs/architecture/`, and the Founder Decision Register is updated with FD-15 ratifying the two-layer persona/segment redesign they describe. This is a **documentation-only batch**: no code, schema, or data was written or changed. The batch closes the design phase for the condition/overlay layer redesign and hands off a concrete Phase 2 scope (the `household_members.segment` vocabulary fix) as the next engineering Work Package.

## 1. What was committed

| Document | Placement | Summary |
|---|---|---|
| `[ACTIVE]_Canonical_Planning_Semantics_Architecture_v1.0.md` | `docs/architecture/` | The two-layer persona redesign: composition catalog (kept, ~5 archetypes) + planning-semantics layer (conditions → genome-space attributes → three-channel routing: absorb/swap/add). Revises the prior investigation's "preserve the 41-row catalog as-is" position. |
| `[ACTIVE]_Phase1_Persona_Decomposition_Catalog_v1.0.md` | `docs/architecture/` | All 41 `Persona_Master_v3` rows classified: ~8 composition rows, ~22 condition-driven rows, ~7 diet-dimension rows, 2 region-axis rows, 1 compound patch (`P41`, dissolves entirely). Answers the architecture doc's open composition-count and cooking-capability-attachment questions. |
| `[ACTIVE]_Phase1B_Attribute_to_Class_Rule_Extraction_v1.0.md` | `docs/architecture/` | The 92 boost classes across all 41 personas collapsed into 8 shared attribute→class rules (Rules A–H) + ~12 condition specializations, replacing 41 hand-attached lists with no research knowledge lost. |
| `[ACTIVE]_Canonical_Planning_Model_v1.0.md` | `docs/architecture/` | The reasoning model — "how FooFoo thinks before it recommends": safety-first ordering, the shared-meal-preservation principle (recovered from a previously-unread free-text column), three-channel routing, an explainability chain, four stress-test households, and an honestly-scoped missing-thinking inventory (§8). |

## 2. Governance updates made alongside

1. **`[ACTIVE]_Founder_Decision_Register_v1.0.md`:** new entry **FD-15** (§7) recording the Founder's 2026-07-17 ratification of the Planning Semantics Architecture direction, citing all four documents above. FD-15 explicitly supersedes the flat 41-persona/8-segment vocabulary approach for the add-on layer and marks the `household_members.segment` vocabulary blocker (noted in WP-8E item 6) **resolved-by-direction**: Phase 2 (the vocabulary fix) is now the specified path. Decision Index (§6), Founder Sign-off Register (§16), and Version History (§17) updated accordingly.
2. **`[ACTIVE]_DOC-P3-02_Conceptual_Domain_Model_v1.1.md`:** one-line "See also" added under Entity 3's Member Segments vocabulary, pointing to the Phase1 Decomposition Catalog and noting the CDM's persona/segment sections are superseded on this topic pending the CDM's own future revision. The CDM itself is **not** rewritten — this is a pointer, not a content change.

## 3. What this batch does NOT do

- Does not touch `household_members.segment`, any table, or any migration — Phase 2 (the schema fix) is future work, opened as its own Work Package when scheduled.
- Does not resolve FD-06 (LF-C build-order sequencing) — that ordering question is independent of which vocabulary LF-C is eventually built against, and remains Pending.
- Does not rewrite `DOC-P3-02` — only a cross-reference pointer was added; the CDM's own persona/segment content revision is deferred to a future pass, per the document's own placement rules (never delete/rewrite a still-`ACTIVE` document's substance without its own versioned revision).
- Does not fix the mojibake/encoding issues silently — the four source documents, as drafted in the claude.ai session, contained broken em-dash/section-symbol/arrow character encoding (UTF-8 mis-decoded as Latin-1). This was corrected during commit so the files render correctly in the repository; no wording, structure, or substantive content was altered in the process.

## 4. Readiness assessment for the next Work Package

- **Design: READY.** The condition/attribute vocabulary (Phase1 Catalog §3), the shared attribute→class rules (Phase1B §2), the three-channel routing model (Canonical Planning Model §1/§5), and the explainability chain (Canonical Planning Model §6) are all Founder-ratified (FD-15) and available as the specified target for Phase 2.
- **Next engineering step (separate WP, not this one):** Phase 2 — the `household_members.segment` vocabulary fix — resolving the current 8-hardcoded-value column to the real, combinable condition vocabulary documented in Phase1 Catalog §3, built directly against these four documents.
- **Open questions carried forward, not resolved here** (per the architecture doc §8, partially narrowed by the Phase1 Catalog): exact final composition-archetype count (Catalog gives ~5 as an initial answer, flagged as needing one more confirmatory pass through all 41 rows); condition-rule priority/conflict resolution beyond the same-attribute-same-scope case already resolved in §9c of the architecture doc.

## 5. Final Architecture Baseline Review (2026-07-17, prior to commit)

Before this batch was committed, the four Planning Semantics documents were reviewed together as one integrated architecture — a coherence/sign-off pass, not further research — against one question: *can a new engineer understand how FooFoo thinks and implement Phase 2 without referring back to `Persona_Master` or the original research workbook?*

- **Verdict: READY WITH MINOR DOCUMENTATION NOTES.**
- **Story flow (Research → Architecture → Rule Extraction → Planning Model → RE):** confirmed coherent. Each document cites and builds on the ones before it (the Architecture doc's §9b/§9b-supplement explicitly incorporate the Planning Model's three-channel and rhythm-attribute findings; the Phase1 Catalog and Phase1B both frame themselves as extensions of the Architecture doc's condition-dimension catalog).
- **Terminology:** Composition, Condition, Semantic Attribute, Genome Space, Absorb/Swap/Add, and Shared-Meal Preservation are used consistently across all four documents. "Planning Intent" is introduced and scoped as optional in the Planning Model only (§3) — not a contradiction, since the Architecture doc's own diagram is a higher-level abstraction that doesn't need to show the optional layer to remain correct.
- **Genuine cross-document inconsistency found and corrected (the one substantive fix this review made):** the Architecture document's own §8/closing-§9 note stated that the composition-archetype-count and cooking-capability-attachment open questions "remain open," while the Phase1 Persona Decomposition Catalog (dated the same day) explicitly answers both. This was a real contradiction a new engineer would hit reading the Architecture doc in isolation. **Fixed** by updating Architecture §8's two bullets and the closing italic note to point to the Phase1 Catalog's answers, preserving the Catalog's own hedge that the exact archetype count still merits one confirmatory pass. No new conclusion was invented — the fix only makes the Architecture doc consistent with its own already-ratified companion document.
- **Minor typographical artifacts corrected** (leftover from this repository's earlier mojibake-repair pass, not original session content): `Rule: —` → `Rule: →` in six places across Phase1B (Rules A–D wording was previously ambiguous, reading as a broken colon+dash); `MC1→MC4` → `MC1–MC4` and `P30→P34` → `P30–P34` in the Phase1 Catalog (these are row-range references, not causal arrows). No wording, claims, or conclusions changed by these corrections.
- **Architectural completeness:** confirmed. What enters the system (household member data), how planning knowledge is derived (condition rules → shared attributes), how member needs are handled (three-channel routing), how conflicts resolve (§9c dominance rule), and how planning becomes recommendation (§9a genome-space bridge into ContentMatch) are each answered, cross-referenced, and non-contradictory after the fix above.
- **Phase 2 readiness:** confirmed sufficient. The real condition vocabulary (Phase1 Catalog §3), the schema-change direction (Architecture §5/§7), and the multi-tag-per-member requirement are all explicit. No genuine blocker was found; the concrete schema shape (e.g., single column vs. join table) is correctly left as Phase 2's own engineering decision, not something the architecture needed to pre-decide.

**The Planning Semantics Architecture is accepted as the repository baseline for subsequent engineering work.**

## Critical Self-Review

- **Anything invented?** No — all four documents are committed as Founder-approved, with only mechanical text-encoding corrections (broken em-dashes, section symbols, arrows) applied for readability, plus the one cross-reference fix and two typographical corrections identified in the final baseline review (§5) — none of which changed wording, claims, or conclusions. Where this Work Package cites a "segment vocabulary blocker," it cites the actual prior record (`WP-8E` item 6's `re_segment_addon_rule` mismatch note) rather than a document that does not exist in this repository.
- **Frozen artifacts / DB touched?** No — zero schema, migration, seed, or code changes. This is the docs-only commit the task requested.
- **Honest completeness:** this batch closes the design phase only. Phase 2–4 (vocabulary fix, LF-C build, catalog shrink) are explicitly future work, not claimed complete here.

## Versioning & Placement

v1.0, `docs/project-history/work-packages/` per the Placement Rule; naming per WP-5AA (`WP-12`, next sequential number after `WP-11`). Companion certificate: REPO-CERT-023.

## Founder Sign-off

Founder acceptance of WP-12 (Planning Semantics Architecture batch commit) and FD-15's ratification record: _______________________ Date: ___________
