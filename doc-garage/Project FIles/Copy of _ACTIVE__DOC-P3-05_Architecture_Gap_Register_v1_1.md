# DOC-P3-05 · Architecture Gap Register
**Version:** 1.1
**Date:** 2026-07-01
**Status:** LIVING DOCUMENT — authoritative tracking mechanism for all architecture gaps raised during DOC-P3-05 implementation, present and future
**Supersedes:** v1.0 (addendum only — see Addendum Notice below; no v1.0 row modified)
**Maintained alongside:** DOC-P3-04 (Data Architecture), DOC-P3-05 Part (a) (Implementation Governance), and now DOC-P3-07 (Security Architecture) as the originating document of this revision's one new entry

---

## Addendum Notice — v1.0 → v1.1

This revision adds exactly one new entry, **AGR-P3-07-001**, in a new Section ("Cross-Document AGR Index") below the original AGR-001–004 register, which is otherwise untouched — every existing row, column, and statistic from v1.0 is preserved verbatim. This register's own "How to use this register" instruction already anticipated exactly this case ("When a new AGR is raised during any future part of DOC-P3-05 **or any later implementation document**, add a row here"). AGR-P3-07-001 is indexed here in a lighter-weight format than AGR-001–004 use, by design: **this register tracks governance status only; the full technical discussion, verification record, and resolution reasoning remain owned exclusively by DOC-P3-07 v1.2 and are not reproduced here.** DOC-P3-07 is not reopened, modified, or reinterpreted by this addendum.

---

## Purpose

Every Architecture Gap Report (AGR) raised during implementation is tracked here, from the moment it is discovered through to its final resolution status. No AGR should exist only inside a single part's completion summary — this register is the one place to check "what gaps have ever been found, and where do they stand."

## How to use this register

When a new AGR is raised during any future part of DOC-P3-05 (or any later implementation document), add a row here using the next sequential AGR ID, and update its status as it moves through the lifecycle: **Open → Resolved | Deferred | Rejected**. Never delete a row, even after resolution — the register's value is its complete history.

---

## Register

| AGR ID | Description | Affected Documents | Root Cause | Resolution Decision | Status | Version Resolved | Remaining Impact |
|---|---|---|---|---|---|---|---|
| **AGR-001** | DOC-P3-04 §03.6 revoked UPDATE privilege on three derived `dishes` columns from a role, `service_role_app_writer`, that was never defined anywhere in the approved architecture or in the Environment Assumptions (three platform roles: `anon`, `authenticated`, `service_role`). | DOC-P3-04 (architecture defect) → propagated to DOC-P3-05 Part (b), file `008` | Architecture-level error: an undefined role referenced in approved DDL text. | Role removed from the REVOKE statement. `service_role` was never intended to be restricted (the SECURITY DEFINER trigger functions run as table owner regardless of invoking role); the two roles always meant to be restricted — `authenticated`, `anon` — are unaffected. | **Resolved** | DOC-P3-04 v1.3 | None. File `008` updated as a direct, minimal consequence; no other object touched. |
| **AGR-002** | Part (a) v1.1's own Phase 7 (Migration Dependency Matrix) and Phase 8.1 (Object-to-Migration Allocation Matrix) contradicted each other on where `public.meal_classes` is created — Phase 7's file-`011` row claimed it existed by file `003`; Phase 8.1 allocated it to file `018`, which comes after `011`. Since `plan_slots.class_code` has an FK to this table, file `011` could not declare that FK as DOC-P3-04 specifies without it failing. | DOC-P3-05 Part (a) (governance defect — not a DOC-P3-04 defect); propagated to Part (c), files `011` and `018` | Planning-layer error: two sections of the same governance document made incompatible claims about a single object's file allocation. | Root-cause fix applied at the planning layer first, per founder instruction: `meal_classes` reallocated to file `003` in both Phase 7 and Phase 8.1 (restoring Phase 7's original, correct intent). File `018` retired as an intentionally empty placeholder — number preserved, not reused, no other file renumbered. Implementation consequence: file `011`'s `plan_slots.class_code` now carries its FK inline exactly as DOC-P3-04 specifies; the previous deferred-`ALTER TABLE` workaround in file `018` was removed as no longer necessary. | **Resolved** | DOC-P3-05 Part (a) v1.2; migration files `003`, `010` (n/a — see AGR-003), `011`, `018` updated in the same pass | None. The fix is structurally identical in outcome to what DOC-P3-04 always specified — only *which file* creates the object changed, not the object itself. |
| **AGR-003** | `fn_derive_dish_attributes()`, deployed in file `010`, writes to `public.derivation_conflicts` on detecting a data conflict — but that table was allocated to file `015`, five files later. PL/pgSQL does not validate referenced-table existence at function-creation time, so this did not block migration *application*, but a genuine conflict detected before file `015` ran would cause the trigger's `INSERT` to fail at runtime, rolling back an otherwise-valid `dish_ingredients` write. | DOC-P3-05 Part (a) (governance defect); propagated to Part (c), files `010` and `015` | Planning-layer error, same class as AGR-002: an object allocated after the file that depends on it, this time inside a function body rather than a declarative FK. | Root-cause fix applied at the planning layer: `derivation_conflicts` reallocated to file `010` (Phase 8.1), co-located with the function that writes to it — the same "group by concern" principle already used to justify keeping all 4 trigger functions in one file. Removed from file `015`'s allocation. Implementation consequence: file `010` now creates this table before defining `fn_derive_dish_attributes()`; file `015` no longer creates it. | **Resolved** | DOC-P3-05 Part (a) v1.2; migration files `010`, `015` updated in the same pass | None. No trigger dependency in the approved sequence now has a forward reference to a table that doesn't yet exist. |
| **AGR-004** | Three minor, non-blocking discrepancies found while implementing file `020` (indexes): (1) DOC-P3-04's stated "37 indexes" count included one self-correcting duplicate (`idx_ingredients_allergen` created, dropped, recreated with a different index type) — the true distinct count is 36. (2) `idx_tags_vector_position` is functionally redundant with the `UNIQUE` column constraint already on `tags.vector_position`. (3) `idx_sl_gate_diet`, as literally described in DOC-P3-04 §03.16, uses a partial-index predicate referencing `now()`, which is not valid Postgres syntax (partial index predicates are evaluated once at creation, not per query) — P3-04's own text acknowledges this and gestures at a "plain composite index" fallback without naming its exact columns. | DOC-P3-04 (minor textual imprecision, not a structural defect); DOC-P3-05 Part (c), file `020` | Documentation imprecision in DOC-P3-04's index inventory — not an architectural defect requiring a design change. | No architecture change required. Findings (1) and (2) are disclosed for transparency; the redundant index in (2) was implemented anyway, exactly as DOC-P3-04 names it, since faithfully reproducing approved text takes precedence over silently optimizing it away. Finding (3)'s "plain composite" fallback was implemented with an explicit column-order choice, flagged as this migration's interpretation pending confirmation against real `EXPLAIN` output once Part (d)'s safety-gate scripts exist. | **Resolved** (informational) | DOC-P3-05 Part (c), file `020`, as originally authored — no further version change needed | One small open item, not a gap: the exact column order of `idx_sl_gate_diet` should be re-validated against real query plans once Part (d)'s safety-gate SQL exists, since the current order is an informed guess, not a measured choice. |

---

## Summary statistics — DOC-P3-05-originated AGRs only (v1.0, unchanged)

| Status | Count | AGR IDs |
|---|---|---|
| Open | 0 | — |
| Resolved | 4 | AGR-001, AGR-002, AGR-003, AGR-004 |
| Deferred | 0 | — |
| Rejected | 0 | — |

**All four gap reports raised to date within DOC-P3-05 are resolved.** Two (AGR-001, AGR-004) were architecture-level findings with no governance-document defect; two (AGR-002, AGR-003) were governance-document defects, both fixed at the root cause (DOC-P3-05 Part (a)) rather than patched only in the implementation layer, per the founder's explicit instruction.

---

## Cross-Document AGR Index `(new in v1.1)`

AGRs originating from documents other than DOC-P3-05 are indexed here in a lighter format. **This index tracks governance status only — the originating document remains the sole authority for technical detail, verification history, and resolution reasoning.**

| AGR ID | Current Status | Originating Document | Short Description | Impact | Current Disposition | Owner | Resolution Path |
|---|---|---|---|---|---|---|---|
| **AGR-P3-07-001** | **OPEN** | DOC-P3-07 v1.2 (Security Architecture), Section 06/19/38/40 | DOC-10 §06 requires an age-verification capability for DPDP minor protection; the frozen P3 architecture (DOC-P3-02/03/04/05) contains no implemented mechanism for it. Classified as an implementation omission relative to DOC-10, not a defect in the frozen architecture. | **High** — DPDP Act 2023 minor-protection compliance is a non-negotiable pre-launch legal requirement (DOC-09 §01/§03); this is launch-blocking, though it does not block Phase 4 start or any document freeze | Open, non-blocking for architecture/document governance; blocking for public launch | Founder | Requires explicit Founder direction through controlled governance (an AGR-approved architecture correction or a Founder-accepted policy-only mitigation) if pursued. No schema change, SER, or onboarding redesign has been proposed by any document to date. |

**Combined summary (all AGRs, all originating documents):** 5 total — 4 Resolved (DOC-P3-05-originated), 1 Open (DOC-P3-07-originated). Zero Deferred, zero Rejected.

**This addendum does not reopen, modify, or reinterpret DOC-P3-07 v1.2**, which remains ACTIVE — APPROVED — FROZEN exactly as it stood before this register was updated. Consult DOC-P3-07 v1.2 Sections 06, 19, 38, and 40 for the full technical discussion, the v1.1 verification record (direct search of DOC-P3-02/03/04/05 confirming no age/DOB/age-category mechanism exists), and the complete reasoning behind this classification.

---

## Cross-document version trail

For full audit traceability, the documents touched by these resolutions, in order:

1. DOC-P3-04 v1.2 → v1.3 (AGR-001)
2. DOC-P3-05 Part (b), file `008` (AGR-001 consequence)
3. DOC-P3-05 Part (a) v1.1 → v1.2 (AGR-002, AGR-003 root-cause corrections, Phase 16 added)
4. DOC-P3-05 Part (c), files `003`, `010`, `011`, `015`, `018` (AGR-002/AGR-003 consequences)
5. This register, created to consolidate all of the above (v1.0)
6. This register, v1.0 → v1.1 — addendum only, indexing AGR-P3-07-001 (originating from DOC-P3-07 v1.2) without reopening or modifying that document
