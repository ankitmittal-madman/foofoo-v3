# Founder Ratification Certificate — 2026-07-16

**Status:** ACTIVE
**Version:** v1.0
**Date:** 2026-07-16
**Placement:** docs/governance/
**Supersedes:** None.
**Dependencies:** `[ACTIVE]_Founder_Decision_Register_v1.0.md` (the living index this certificate ratifies against — cited, not replaced); each document named in §3's "Affected Documents" column.

---

## Executive Summary

This certificate is the board-minutes-style record of a batch Founder ratification session held on claude.ai on 2026-07-16, in which the Founder (Ankit Mittal) closed 9 of the 13 Founder-level decisions (FD-01 through FD-13) surfaced in the Founder Decision Register. Claude (Sonnet) acted as facilitator only — presenting each decision's context and recorded alternatives from the Register and its primary sources, without selecting an outcome on the Founder's behalf. 4 items (FD-07, FD-11, FD-12, FD-13) remain open Founder deliverables, not resolved in this session, and are tracked separately.

This certificate records that ratification occurred and states each outcome. It is distinct from the Founder Decision Register (the living index of all Founder-level decisions, ratified or pending) and from a `REPO-CERT-NNN` (which certifies that engineering execution actually happened). This certificate certifies a governance event — a decision, not a deployment.

## 1. Session Context

- **Session type:** claude.ai Founder decision-closing session (separate from this Claude Code repository session, in which this certificate was drafted and recorded).
- **Date of ratification:** 2026-07-16.
- **Date of this certificate's drafting:** 2026-07-17 (Claude Code, this repository).
- **Participants:**
  - Founder — Ankit Mittal (decision authority).
  - Claude (Sonnet) — facilitator. Presented each FD's context, problem statement, and recorded alternatives from the Decision Register and its cited primary sources; made no decision itself.
- **Scope:** All 13 Pending items indexed in §6/§7 of `[ACTIVE]_Founder_Decision_Register_v1.0.md` as of its 2026-07-16 creation.

## 2. What This Certificate Does NOT Do

Per explicit Founder instruction, this certificate records Founder ratification of decisions only. It does not:
- modify architecture,
- approve schema,
- approve implementation,
- replace SERs (Schema Evolution Requests),
- replace AGRs (Architecture Governance Records).

Engineering proceeds only through the normal governance process — a ratified FD is a green light to open or continue the affected Work Package(s) per the Register's own Decision Dependency Matrix (§14), not a substitute for one.

## 3. Ratified Decisions (9 of 13)

| ID | Ratified Outcome | Affected Documents |
|---|---|---|
| **FD-01** | The WP-8D/8E push to `main` is retroactively ratified as authorized; no governance exception is logged. | `REPO-CERT-014`, `REPO-CERT-015` |
| **FD-02** | The "continuous forward-transition reading" of DCR-8D-01's weight-ladder interpolation is confirmed as the ratified standard (already implemented in `interpolateWeightLadder`). | `DOC-P3-03` §07 (worked example to be corrected to match) |
| **FD-03** | Day-0 confidence is clamped to [0.35, 0.65]; the 1.0 schema ceiling applies only to later warm-state evolution (already implemented in `orchestrator.ts`). | `DOC-P3-03` (LF-A08 section to note the clamp explicitly) |
| **FD-04** | Ratified as **Option 2** — the first weekly plan is generated live/synchronously at the end of onboarding (not deferred), consistent with the existing OB-08b "aha moment" product decision. `DOC-P4-02` promotes DRAFT → ACTIVE on this basis. | `DOC-P4-02` (DRAFT → ACTIVE) |
| **FD-05** | Ratified as **Option (b)** — the Repository Naming Standard is amended so `[ACTIVE]` status does not require a Founder signature line. The six affected documents (`DOC-P3-02`, `DOC-P3-03`, `DOC-P3-03A`, `DOC-P3-04`, `DOC-P3-05-Part-A`, APDF vNext Addendum) keep their `[ACTIVE]` filenames; their internal "DRAFT — pending Founder sign-off" headers are corrected, not the filenames. | The six documents named above; `docs/governance/[ACTIVE]_Repository_Naming_Standard_v1.0.md` (amendment required) |
| **FD-06** | Member add-ons (Epic 6) are sequenced after the repository adapters (Epic 1), ahead of the learning loop, per the Engineering Execution Baseline's recommendation. | `Engineering_Execution_Baseline_v1.0.md` |
| **FD-08** | Grocery-list auto-generation is confirmed **OUT of MVP scope**. `DOC-04`'s existing Change Notice is correct; `DOC-01` §06 (which reads "Core — cannot defer") is corrected to match `DOC-04`, not the reverse. | `DOC-01` §06 (correction required) |
| **FD-09** | The stale "locked" environment map in `DOC-10` §10 (superseded Supabase project ref / GitHub org) is approved for refresh to the current live values (`ankitmittal-madman/foofoo-v3`, project `slsqtlygeekdppuyiiff`). | `DOC-10` §10 (refresh required) |
| **FD-10** | The shipped `handleConstraintConflict` behavior — enforcing allergen and never-list constraints beyond the original LF-D07 spec — is approved as the official standard. `RE-DOC-01` §05 is updated to match the code; the code is not pulled back. | `RE-DOC-01` §05 (update required) |

## 4. Open Founder Deliverables — Not Resolved by This Certificate

The following 4 items were discussed in the same Register but explicitly **not** closed in this ratification session. They remain Pending in the Decision Register and are tracked separately — this certificate does not block on them and does not state an outcome for them:

- **FD-07** — Cold-start priors (`re_cohort_class_priors`) + OB-07 signal capture: cohort-prior data coverage still needs verification before this can be ratified.
- **FD-11** — `mainIngredientClass` dominant-ingredient derivation rule: main-ingredient data/rule not yet supplied.
- **FD-12** — `dish_combos` cuisine-destination column: combo-cuisine tie-break rule not yet decided.
- **FD-13** — `POST /v1/events` idempotency handling: idempotency-key mechanics (client vs. server ownership) not yet decided.

## 5. Effective Date

All 9 ratifications in §3 are effective **2026-07-16**, the date of the claude.ai session in which the Founder made them — not the date of this certificate's drafting.

## 6. Superseded Decisions

None. All 9 ratified items were previously status **Pending** in the Decision Register; none supersedes a prior **Ratified** decision.

## 7. Reference Documents

- `docs/governance/[ACTIVE]_Founder_Decision_Register_v1.0.md` — the living index this certificate ratifies against (§6 Decision Index, §7 Engineering Decisions FD-01–13).
- Per-decision primary sources, as cited in the Register and repeated in §3 above.

## 8. Required Follow-up (Documentation Catch-up, Not New Engineering)

The following documents are now stated by the Register/primary sources as needing a text correction to match the ratified outcome above. None requires new code; each is a documentation-catch-up action:

- `DOC-P3-03` §07 (FD-02 worked example; FD-03 clamp note)
- `DOC-P4-02` (FD-04: DRAFT → ACTIVE status change)
- `docs/governance/[ACTIVE]_Repository_Naming_Standard_v1.0.md` (FD-05 amendment) and the six documents named in §3
- `DOC-01` §06 (FD-08 correction)
- `DOC-10` §10 (FD-09 refresh)
- `RE-DOC-01` §05 (FD-10 update)
- `[ACTIVE]_Founder_Decision_Register_v1.0.md` — should be updated next (Wave 1, not yet run as of this certificate) to move FD-01–06, 08–10 from Pending to Ratified, and to log this certificate in its §17 Version History.

## Critical Self-Review

This certificate's 9 ratified outcomes were supplied directly by the Founder in this session, not inferred from the Register's own "recommended" language except where the Founder confirmed that recommendation as the ratified outcome (FD-01, FD-02, FD-03, FD-06, FD-09 — each of which the Register already recorded as "already implemented" or "recommended," and the Founder confirmed rather than overrode). FD-04, FD-05, FD-08, and FD-10 involved genuine unresolved alternatives with no prior recorded pick; their outcomes here are stated exactly as the Founder supplied them, not fabricated or inferred. The 4 items in §4 are deliberately left without a stated outcome — this certificate does not guess at them. This certificate does not itself update the Decision Register (see §8) — that is separate follow-up work, not yet performed, and is not claimed as done here.

## Versioning & Placement

v1.0, filed under `docs/governance/`, per the repository's Naming Standard (certificate-style token, dated). No prior version exists; nothing is superseded.

Founder sign-off: _______________________ Date: ___________
