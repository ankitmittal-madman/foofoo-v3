# Founder Decision Register v1.0

**Status:** ACTIVE — this is the constitutional governance document of FooFoo. Every Founder-level decision, ratified or pending, is discoverable from this single file.
**Version:** v1.0
**Date:** 2026-07-16
**Placement:** docs/governance/
**Supersedes:** `[SUPERSEDED]_Founder_Decision_Book_v1.0.md` (created earlier the same day; this Register absorbs its full FD-01–13 content unchanged and adds product/RE/AI/governance philosophy decisions the Book never attempted).
**Dependencies:** Cites, never copies, its primary sources. Every decision below traces to a document, code file, or live-verified fact — this Register invents no history and no alternatives-considered analysis that was never recorded.

---

## 1. Purpose

Every important decision FooFoo has made — from "the RE is the product, not a feature" to "seed `re_cohort_class_priors` before shipping any endpoint" — currently lives inside whichever document happened to surface it: a concept doc's opening paragraph, a work package's reconciliation notes, an audit's findings table. None of those documents is discoverable from the others, and a future engineer, AI agent, or reviewer has no single place to ask "why does the product work this way, and is that settled or still open?"

This Register answers that question. It is not an audit, not a design document, and not a place where new product behavior gets invented — it is where already-made-or-pending decisions become permanently findable.

## 2. How to use this document

- **Building a feature and unsure if a rule is settled?** Check §7 (Engineering Decisions) and §12 (Deferred) before writing code that assumes an answer.
- **Wondering why the product works a certain way at all — not just an engineering detail, but a philosophy?** Check §8–§11.
- **The Founder, reviewing what needs a signature?** §16 is the complete checklist.
- **Just ratified something?** Move it to the appropriate "Ratified" subsection, assign it an `AGR-NNN` if it's engineering-facing, and log it in §17.
- **Never invent an alternatives-considered analysis that wasn't recorded.** If a frozen document only states its adopted design with no discussion of what else was considered, this Register says so plainly rather than fabricating a debate that never happened.

## 3. Decision Lifecycle

```
Surfaced (found at its point of origin — a concept doc, a WP, an audit)
   │
   ▼
Pending ──────────────► Deferred (explicit, dated, reasoned — never silent)
   │                         │
   ▼                         ▼
Ratified (via document freeze, AGR-NNN, or explicit Founder sign-off)   remains Deferred until revisited
   │
   ▼
Superseded (only when a later ratified decision explicitly replaces it)
```

Two ratification paths exist in this repository and both are valid: (a) **document freeze** — a concept/spec document reaches `APPROVED — FROZEN` status and its content becomes the ratified decision (this is how RE-DOC-01–05 and DOC-P3-06/07/08 work), and (b) **AGR** — a standalone Architecture Governance Record for a narrower, later-surfaced engineering decision (`AGR-005`, `AGR-006`). Both paths terminate in "Ratified" in this Register; neither is more authoritative than the other.

## 4. Governance Principles

These are the rules this Register itself follows, extracted from how the repository has actually behaved (not invented for this document):

1. **Never fabricate execution, history, or an alternatives analysis that wasn't recorded** — per `CLAUDE.md` and demonstrated by `REPO-BOOT-03`'s explicit disclosure of the repository's reconstructed git lineage.
2. **Never delete a superseded document — stamp and keep both** — per `CLAUDE.md`, applied to this Register's own predecessor (see Supersedes, above).
3. **A decision is either Ratified, Pending, Deferred, or Superseded — never silently dropped.**
4. **Cite the primary source; do not copy its prose.** This Register is an index, not an archive.
5. **A pending decision left unresolved for a long time is a signal to escalate, not evidence it no longer matters.**

## 5. Classification Rules

Applied to every item in this Register, per the task's own taxonomy:

- **A — Existing Founder Decision (already covered):** ratified, findable at its primary source, indexed here.
- **B — New Founder Decision:** genuinely first-surfaced, no prior primary source, assigned a new `FD-NN`.
- **C — Engineering Decision:** implementation detail correctly *not* promoted to Founder level (e.g., which similarity metric MMR uses internally).
- **D — Architecture Decision:** an `AGR`-numbered record.
- **E — Research Conclusion:** a Batch/research-package finding, not itself a decision (e.g., a data-quality observation) unless it produced one.
- **F — Deferred Decision:** explicitly, on the record, postponed by the Founder.
- **G — Open Question:** evidence insufficient to state a decision exists at all — left as a question, not converted into a false decision.
- **H — Duplicate:** same decision appearing under two IDs; retired to one.
- **I — Superseded:** a decision replaced by a later ratified one.

## 6. Decision Index

| ID | Title | Category | Section |
|---|---|---|---|
| FD-01 | Ratify/reject WP-8D/8E push to main | Ratified | §7 |
| FD-02 | DCR-8D-01 weight-ladder ambiguity | Ratified | §7 |
| FD-03 | DCR-8E-01 Day-0 confidence cap | Ratified | §7 |
| FD-04 | DOC-P4-02 DRAFT→ACTIVE (AD-01) | Ratified | §7 |
| FD-05 | ACTIVE/DRAFT contradiction across frozen set | Ratified | §7 |
| FD-06 | Member add-ons build-order priority | Pending | §7 |
| FD-07 | Cold-start priors + OB-07 signal priority | Pending | §7 |
| FD-08 | DOC-01 vs DOC-04 MVP scope conflict | Ratified | §7 |
| FD-09 | DOC-10 §10 stale environment map | Ratified | §7 |
| FD-10 | LF-D07 fallback behavior approval | Ratified | §7 |
| FD-11 | `mainIngredientClass` dominant-ingredient rule | Pending | §7 |
| FD-12 | `dish_combos` cuisine-destination column | Pending | §7 |
| FD-13 | `POST /v1/events` idempotency handling | Pending | §7 |
| PD-01 | Class-first architecture | Ratified | §8 |
| PD-02 | RE module isolation ("the RE is the product") | Ratified | §8 |
| PD-03 | Freemium monetization, 90-day habit window | Ratified | §8 |
| PD-04 | Invite-only GTM to 500 DAU | Ratified | §8 |
| PD-05 | DPDP-first legal posture | Ratified | §8 |
| RE-01 | Cold-start philosophy: cohort intelligence over popularity | Ratified | §9 |
| RE-02 | Continuous confidence ladder (Day 0→60+) | Ratified | §9 |
| RE-03 | Probabilistic exploration (Thompson Sampling) | Ratified | §9 |
| RE-04 | Neutral-fallback philosophy | Ratified | §9 |
| RE-05 | Variety via MMR + explicit rule windows | Ratified | §9 |
| RE-06 | Defense-in-depth safety gating (twice, not once) | Ratified | §9 |
| AI-01 | Six Working Principles (no invented values, config not hardcoded) | Ratified | §10 |
| AI-02 | Explainability via reason-tags | Ratified | §10 |
| AI-03 | Deterministic, reproducible seed/ETL pipeline | Ratified | §10 |
| GOV-01 | Repository-history reconstruction disclosure | Ratified | §11 |
| GOV-02 | Never delete a superseded document | Ratified | §11 |
| AGR-005 | `routing_rules.show_question_key` nullable | Ratified | §11 |
| AGR-006 | Weight-ladder config numeric conversion | Ratified | §11 |

## 7. Engineering Decisions (FD-01 onward)

Full 24-field format applied. Where a field has no recorded content in any primary source, this Register states that explicitly rather than inventing one.

### FD-01 — Ratify or reject the `main`-branch push of WP-8D/8E
- **Status:** Ratified (2026-07-16, claude.ai Founder decision-closing session; see `[ACTIVE]_Founder_Ratification_Certificate_2026-07-16_v1.0.md`) · **Date raised:** 2026-07-16 (this audit chain) · **Origin:** `[ACTIVE]_WP-9_Validation_Audit_v1.0.md` §H-03
- **Context:** WP-8D/8E's own work-package text implies the code was not yet pushed; the actual repository shows both merged to `main` and `origin/main`.
- **Problem Statement:** Governance record and repository state disagree on whether this was an authorized push.
- **Alternatives Considered:** Not recorded in any source — this is a factual discrepancy, not a design choice with options.
- **Final Decision:** The WP-8D/8E push to `main` is retroactively ratified as authorized; no governance exception is logged. WP-8D/8E work-package notes corrected accordingly (2026-07-17).
- **Business Rationale / Technical Rationale:** N/A — factual ratification, not a design tradeoff.
- **Engineering Impact:** Blocks clean closure of `REPO-CERT-014`/`015`.
- **AI Impact:** None directly.
- **Recommendation Engine Impact:** None directly — the code itself is unaffected either way.
- **Database Impact:** None. **API Impact:** None. **Batch Impact:** None. **ETL Impact:** None. **Architecture Impact:** None.
- **Affected Documents:** `REPO-CERT-014`, `REPO-CERT-015`.
- **Affected Work Packages:** WP-8D, WP-8E.
- **Affected Tests:** None.
- **Affected Epics:** None directly (governance closure only).
- **Implementation Notes:** None — no code change implied by either outcome.
- **Acceptance Criteria:** A dated Founder statement, either ratifying the push or logging a governance exception.
- **Future Review Trigger:** None — awaits one-time resolution.
- **Source Evidence:** `git log origin/main --oneline` (confirms `e113ffa`/`e76bd9c` present, re-verified this session at `b27ca58`).

### FD-02 — Rule on DCR-8D-01 (weight-ladder worked-example inconsistency)
- **Status:** Ratified (2026-07-16, claude.ai Founder decision-closing session; see `[ACTIVE]_Founder_Ratification_Certificate_2026-07-16_v1.0.md`) · **Origin:** `docs/project-history/[ACTIVE]_WP-8D_Pre_Implementation_Architecture_Reconciliation_v1.0.md`
- **Context:** `DOC-P3-03` §07's own worked example uses inconsistent interpolation references between weight-ladder tiers.
- **Problem Statement:** Two readings of the interpolation rule are both textually defensible.
- **Alternatives Considered:** The two competing readings are described in the primary source; this Register does not restate them, per instruction to cite rather than copy.
- **Final Decision:** The "continuous forward-transition reading" is confirmed as the ratified standard (already implemented in `interpolateWeightLadder`). `DOC-P3-03` §07's worked example corrected to match (2026-07-17).
- **Business Rationale:** Consistent Day-0→Mature scoring behavior is required for the cold-start metric (DOC-01 §07) to mean anything.
- **Technical Rationale:** The continuous reading is the only one that keeps `interpolateWeightLadder`'s partition-of-unity invariant true at every tier boundary (tested).
- **Engineering Impact:** None further — already implemented; only the *documentation* needs to catch up to what shipped.
- **AI Impact:** None. **Recommendation Engine Impact:** Governs LF-E01's tier interpolation directly.
- **Database Impact:** None. **API Impact:** None. **Batch Impact:** None. **ETL Impact:** None.
- **Architecture Impact:** None — implementation already matches one reading; only ratification is pending.
- **Affected Documents:** `DOC-P3-03` §07 (needs its worked example corrected to match the ratified reading).
- **Affected Work Packages:** WP-8D.
- **Affected Tests:** `_tests/re_core.test.ts` (partition-of-unity assertion already exists).
- **Affected Epics:** Epic 1 (Repository Adapters), per `Engineering_Execution_Baseline_v1.0.md`.
- **Implementation Notes:** No code change required regardless of outcome — only whether `DOC-P3-03`'s text is corrected to match.
- **Acceptance Criteria:** Founder signature approving the implemented reading, and a corrected worked example in `DOC-P3-03`.
- **Future Review Trigger:** None.
- **Source Evidence:** `supabase/functions/_shared/services/re/scoring.ts` (`interpolateWeightLadder`); `_tests/re_core.test.ts`.

### FD-03 — Rule on DCR-8E-01 (Day-0 confidence 0.65 cap vs 1.0 schema ceiling)
- **Status:** Ratified (2026-07-16, claude.ai Founder decision-closing session; see `[ACTIVE]_Founder_Ratification_Certificate_2026-07-16_v1.0.md`) · **Origin:** `docs/project-history/work-packages/[ACTIVE]_WP-8E_RE_Integration_Layer_v1.0.md`, line ~53
- **Context:** LF-A08 states additive onboarding-confidence contributions sum to 1.00 for a fully-answered onboarding, but also states "Maximum at Day 0 completion: 0.65."
- **Problem Statement:** The schema's confidence range allows up to 1.0; the Day-0 text caps it at 0.65 — which governs?
- **Alternatives Considered:** Not separately enumerated in the source beyond the two conflicting statements themselves.
- **Final Decision:** Confirmed: clamp to [0.35, 0.65] at Day 0; the 1.0 ceiling applies only to later warm-state evolution. `DOC-P3-03` LF-A08 section now notes the clamp explicitly (2026-07-17).
- **Business Rationale:** Prevents overconfident Day-0 recommendations before any real signal exists.
- **Technical Rationale:** Faithful to the explicit "Maximum at Day 0: 0.65" sentence.
- **Engineering Impact:** Already implemented; ratification is documentation catch-up only.
- **AI Impact:** None. **Recommendation Engine Impact:** Governs LF-A08's clamp directly.
- **Database Impact:** None. **API Impact:** None. **Batch Impact:** None. **ETL Impact:** None. **Architecture Impact:** None.
- **Affected Documents:** `DOC-P3-03` (LF-A08 section should note the clamp explicitly).
- **Affected Work Packages:** WP-8E.
- **Affected Tests:** `_tests/re_integration.test.ts`.
- **Affected Epics:** Epic 1.
- **Implementation Notes:** No code change required.
- **Acceptance Criteria:** Founder signature confirming the clamp as the documented standard.
- **Future Review Trigger:** None.
- **Source Evidence:** `supabase/functions/_shared/services/onboarding/orchestrator.ts` (clamp logic).

### FD-04 — Promote DOC-P4-02 from DRAFT to ACTIVE (AD-01 countersignature)
- **Status:** Ratified (2026-07-16, claude.ai Founder decision-closing session; see `[ACTIVE]_Founder_Ratification_Certificate_2026-07-16_v1.0.md`) · **Origin:** `docs/architecture/[DRAFT]_DOC-P4-02_Service_and_Edge_Function_Specifications_v1.0.md` §3
- **Context:** DOC-P4-02 itself states: *"Status: DRAFT — pending Founder sign-off. Contains one open architectural decision (AD-01) that GATES onboarding implementation."*
- **Problem Statement:** What happens to a user's first weekly plan at the end of onboarding — three options are laid out in DOC-P4-02 §3 itself (capture-only/deferred generation; synchronous first-plan generation; cohort-only deferral), with a non-binding recommendation for Option 1.
- **Alternatives Considered:** The three options are fully specified in DOC-P4-02 §3 — cited, not copied, per this Register's own rule.
- **Final Decision:** Ratified as **Option 2** — the first weekly plan is generated live/synchronously at the end of onboarding, consistent with the existing OB-08b "aha moment" product decision (overriding this Register's own non-binding Option 1 recommendation). `DOC-P4-02` re-issued as `[ACTIVE]_DOC-P4-02_..._v1.1.md` (2026-07-17); `[DRAFT]_..._v1.0.md` retained, stamped SUPERSEDED.
- **Business Rationale:** Directly determines the onboarding→first-plan user experience.
- **Technical Rationale:** Option 2 requires the RE core (WP-8D) to exist before onboarding ships — accepted as the mandatory build order, per DOC-P4-02 §3.
- **Engineering Impact:** WP-8D and WP-8E were already built on an implicit direction without this ratification.
- **AI Impact:** None directly. **Recommendation Engine Impact:** Determines whether `generateWeekPlan` runs synchronously during onboarding or is deferred.
- **Database Impact:** None. **API Impact:** Determines `/v1/onboarding`'s exact response contract. **Batch Impact:** None. **ETL Impact:** None.
- **Architecture Impact:** Everything in `services/` implicitly depends on this direction, per `Final_Evidence_Closure_v1.0.md` §8 FD-04.
- **Affected Documents:** `DOC-P4-02` (moves DRAFT→ACTIVE on ratification).
- **Affected Work Packages:** WP-8C, WP-8D, WP-8E.
- **Affected Tests:** `_tests/re_integration.test.ts`.
- **Affected Epics:** Epic 2, Epic 3 (`Engineering_Execution_Baseline_v1.0.md`).
- **Implementation Notes:** Architecture is already built and tested against Option 1's implication — countersigning ratifies existing work rather than requiring new work.
- **Acceptance Criteria:** Founder selects one of the three AD-01 options in writing.
- **Future Review Trigger:** None.
- **Source Evidence:** `docs/architecture/[DRAFT]_DOC-P4-02_Service_and_Edge_Function_Specifications_v1.0.md` §3.

### FD-05 — Resolve the systemic ACTIVE-vs-DRAFT status contradiction across the frozen document set
- **Status:** Ratified (2026-07-16, claude.ai Founder decision-closing session; see `[ACTIVE]_Founder_Ratification_Certificate_2026-07-16_v1.0.md`) · **Origin:** `docs/governance/[ACTIVE]_Repository_Naming_Conflict_Report_v1.0.md` (2026-07-13)
- **Context:** `DOC-P3-02`, `DOC-P3-03`, `DOC-P3-03A`, `DOC-P3-04`, `DOC-P3-05-Part-A`, and the vNext Addendum all carry the `[ACTIVE]` filename token while their own internal headers read "DRAFT — pending Founder sign-off," with blank signature lines.
- **Problem Statement:** Is a document "frozen" because its filename says ACTIVE, or only once actually signed? The naming standard and the documents' own headers disagree.
- **Alternatives Considered:** (a) sign the batch of documents; (b) amend the naming standard to state sign-off is not required for ACTIVE status. Both stated in `Final_Evidence_Closure_v1.0.md` §8 FD-05, sourced from the Conflict Report's own framing.
- **Final Decision:** Ratified as **Option (b)** — the naming standard is amended (`[ACTIVE]_Repository_Naming_Standard_v1.1.md`, new §4A) so that `[ACTIVE]` status does not require a Founder signature line. The six affected documents keep their `[ACTIVE]` filenames; their "DRAFT — pending Founder sign-off" headers are corrected, not the filenames (2026-07-17).
- **Business Rationale:** Determines whether any "frozen" claim in the repository is currently defensible.
- **Technical Rationale:** Runtime code (WP-8D/8E) has already been built against these documents' content regardless of their signature status.
- **Engineering Impact:** None to code either way — governance validity only.
- **AI Impact:** None. **Recommendation Engine Impact:** None directly (content unaffected; only its formal status).
- **Database Impact:** None. **API Impact:** None. **Batch Impact:** None. **ETL Impact:** None. **Architecture Impact:** None.
- **Affected Documents:** All five named above, plus the vNext Addendum.
- **Affected Work Packages:** All RE-related WPs (8C–8FA) implicitly.
- **Affected Tests:** None.
- **Affected Epics:** None directly.
- **Implementation Notes:** None — pure governance action.
- **Acceptance Criteria:** Either a batch Founder signature, or a naming-standard amendment.
- **Future Review Trigger:** None.
- **Source Evidence:** `docs/governance/[ACTIVE]_Repository_Naming_Conflict_Report_v1.0.md`.

### FD-06 — Priority ruling on member add-ons (LF-C) build order
- **Status:** Pending · **Origin:** synthesized in `Final_Evidence_Closure_v1.0.md` §8 (no pre-existing primary source — stated plainly, not invented provenance)
- **Context:** `docs/product/[ACTIVE]_DOC-03_User_Personas_v1.0.docx` calls member add-ons "the differentiator no competitor has built"; 0% implemented as of this Register's date.
- **Problem Statement:** Where does add-on work sit relative to the learning loop and other post-adapter Epics?
- **Alternatives Considered:** Not recorded anywhere prior to this audit chain's own recommendation.
- **Final Decision:** Not yet ratified — `Engineering_Execution_Baseline_v1.0.md` §5 recommends sequencing it after adapters, ahead of the learning loop, as a recommendation only.
- **Business Rationale:** DOC-03's persona work (Meera/Priya) treats this as high-value differentiation.
- **Technical Rationale:** 7,992 rows of `re_household_addon_plans` already seeded and confirmed live, unconsumed.
- **Engineering Impact:** Determines Epic 6's position in the sequence.
- **AI Impact:** None. **Recommendation Engine Impact:** LF-C01/C02 entirely.
- **Database Impact:** None (schema already supports it). **API Impact:** Addon response shape already exists in `DOC-P3-06`'s `/v1/plan` contract. **Batch Impact:** None. **ETL Impact:** None. **Architecture Impact:** None.
- **Affected Documents:** None requiring update beyond this Register.
- **Affected Work Packages:** None yet — this would open a new WP.
- **Affected Tests:** New addon-generation test suite (not yet written).
- **Affected Epics:** Epic 6, `Engineering_Execution_Baseline_v1.0.md`.
- **Implementation Notes:** See Epic 6's full spec in the Baseline.
- **Acceptance Criteria:** Founder confirms sequencing.
- **Future Review Trigger:** None.
- **Source Evidence:** live Supabase confirmation, `re_household_addon_plans` = 7,992 rows (this audit chain, Step 1 verification).

### FD-07 — Priority ruling on cold-start priors + OB-07 signal capture (bundled)
- **Status:** Pending · **Origin:** synthesized in `Final_Evidence_Closure_v1.0.md` §8 — the underlying technical findings (H-04, MF-02) exist separately in the WP-9 lineage; bundling them as one decision is this audit chain's own synthesis, stated explicitly.
- **Context:** `re_cohort_class_priors` = 0 rows live (confirmed); `persistTasteVector` writes an empty `class_affinity` (confirmed in code).
- **Problem Statement:** Both jointly determine Day-0 recommendation quality, and DOC-01 §07 names Day-0/Day-90 acceptance as the MVP's sole go/no-go metric.
- **Alternatives Considered:** Not separately enumerated — this is a "fix both, they compound" recommendation, not a multi-option choice.
- **Final Decision:** Not yet ratified — recommended as highest-priority engineering work regardless.
- **Business Rationale:** DOC-01 §07's go/no-go metric is at risk if both remain broken simultaneously.
- **Technical Rationale:** `scoring.ts`'s neutral-0.50 fallback (RE-04, §9) already prevents outright failure; this decision is about restoring signal, not preventing a crash.
- **Engineering Impact:** Epic 2 (`Engineering_Execution_Baseline_v1.0.md`).
- **AI Impact:** None directly. **Recommendation Engine Impact:** LF-E02, LF-A07/A09 (taste-vector persistence).
- **Database Impact:** New seed file for `re_cohort_class_priors`. **API Impact:** None directly. **Batch Impact:** None. **ETL Impact:** `database/etl/generate_re_seeds.py` may need extension. **Architecture Impact:** None.
- **Affected Documents:** None beyond this Register.
- **Affected Work Packages:** None yet.
- **Affected Tests:** `905_re_knowledge_seed_validation.sql`, `_tests/re_integration.test.ts`.
- **Affected Epics:** Epic 2, `Engineering_Execution_Baseline_v1.0.md`.
- **Implementation Notes:** See Epic 2's full spec in the Baseline.
- **Acceptance Criteria:** Founder confirms priority; engineering delivers per Epic 2's DoD.
- **Future Review Trigger:** None.
- **Source Evidence:** live Supabase, `re_cohort_class_priors` = 0 rows (this audit chain's Step 1).

### FD-08 — Reconcile DOC-01 vs DOC-04 MVP scope (grocery list)
- **Status:** Ratified (2026-07-16, claude.ai Founder decision-closing session; see `[ACTIVE]_Founder_Ratification_Certificate_2026-07-16_v1.0.md`) · **Origin:** `docs/product/[ACTIVE]_DOC-01_Product_Brief_v1.1.docx` line 107, vs. `docs/architecture/[ACTIVE]_DOC-04_PRD_v1.1.docx` Change Notice
- **Context:** DOC-01 line 107 reads, verbatim (confirmed by direct grep this session): *"Grocery list auto-generated from plan | – | Core — cannot defer."* DOC-04 v1.1's Change Notice moves this feature out of MVP scope.
- **Problem Statement:** Two frozen documents disagree on whether this is in-scope for MVP.
- **Alternatives Considered:** Not separately enumerated — this is a direct factual conflict between two documents, not a menu of options.
- **Final Decision:** Ratified — grocery list is **out of MVP scope**. DOC-04's existing Change Notice is correct; DOC-01 §06 (which wrongly said "Core — cannot defer") corrected to match DOC-04, not the reverse (2026-07-17).
- **Business Rationale:** A reader starting from the founding brief (DOC-01) gets a different MVP than a reader starting from the PRD (DOC-04).
- **Technical Rationale:** N/A.
- **Engineering Impact:** None directly today — no Epic currently builds grocery-list generation.
- **AI Impact:** None. **Recommendation Engine Impact:** None. **Database Impact:** None. **API Impact:** None. **Batch Impact:** None. **ETL Impact:** None. **Architecture Impact:** None.
- **Affected Documents:** `DOC-01` §06 (needs amendment to match `DOC-04`'s Change Notice, per the recommendation already on record).
- **Affected Work Packages:** None.
- **Affected Tests:** None. **Affected Epics:** None currently.
- **Implementation Notes:** None.
- **Acceptance Criteria:** DOC-01 §06 amended to match DOC-04 v1.1, or vice versa, per Founder ruling.
- **Future Review Trigger:** None.
- **Source Evidence:** `grep -a -n -i "grocery" "docs/product/[ACTIVE]_DOC-01_Product_Brief_v1.1.docx"` (this session, line 107).

### FD-09 — Refresh the stale "locked" environment map in DOC-10 §10
- **Status:** Ratified (2026-07-16, claude.ai Founder decision-closing session; see `[ACTIVE]_Founder_Ratification_Certificate_2026-07-16_v1.0.md`) · **Origin:** `docs/architecture/[ACTIVE]_DOC-10_Technical_Architecture_v1.0.docx` §10
- **Context:** DOC-10 §10 references a superseded Supabase project ref and GitHub org, contradicted by the repository's own recovery record.
- **Problem Statement:** An engineer following DOC-10 literally would connect to the wrong infrastructure.
- **Alternatives Considered:** Not applicable — this is a factual refresh, not a design choice.
- **Final Decision:** Ratified — DOC-10 §10 corrected to repo `ankitmittal-madman/foofoo-v3`, Supabase production project `cmkswalqpmmqojwdmqbv` (2026-07-17). **Note:** this supersedes the project ref `slsqtlygeekdppuyiiff` previously stated as "confirmed live" below in this same entry — the Founder supplied `cmkswalqpmmqojwdmqbv` as the correct value in the 2026-07-16 session; the earlier ref is understood to have been superseded or misidentified and should not be used going forward.
- **Business Rationale:** None directly — pure documentation accuracy.
- **Technical Rationale:** Current true values are `ankitmittal-madman/foofoo-v3` / Supabase project `cmkswalqpmmqojwdmqbv`, per Founder confirmation 2026-07-16 (supersedes the `slsqtlygeekdppuyiiff` ref this Register previously cited as live-confirmed).
- **Engineering Impact:** Misleads any engineer following DOC-10 literally.
- **AI Impact:** None. **Recommendation Engine Impact:** None. **Database Impact:** None. **API Impact:** None. **Batch Impact:** None. **ETL Impact:** None. **Architecture Impact:** None.
- **Affected Documents:** `DOC-10` §10.
- **Affected Work Packages:** None. **Affected Tests:** None. **Affected Epics:** Epic 9 (`Engineering_Execution_Baseline_v1.0.md`, "Documentation Debt").
- **Implementation Notes:** Cheap, one-time text update.
- **Acceptance Criteria:** DOC-10 §10 updated and re-verified against live Supabase project settings.
- **Future Review Trigger:** None.
- **Source Evidence:** `docs/project-history/certificates/[ACTIVE]_REPO-CERT-009_WP-6E2_Canonical_Production_Sync_v1.0.md`; live Supabase project ref confirmed this audit chain.

### FD-10 — Approve the improved LF-D07 fallback behavior as the documented standard
- **Status:** Ratified (2026-07-16, claude.ai Founder decision-closing session; see `[ACTIVE]_Founder_Ratification_Certificate_2026-07-16_v1.0.md`) · **Origin:** `docs/architecture/[ACTIVE]_RE-DOC-01_Architecture.docx` §05 vs. `supabase/functions/_shared/services/re/constraints.ts`
- **Context:** The shipped `handleConstraintConflict` implementation also enforces allergen and never-list constraints beyond what RE-DOC-01 §05's spec strictly requires.
- **Problem Statement:** Code is safer than spec — should the spec be updated to match the safer behavior, or should code be pulled back to match spec exactly?
- **Alternatives Considered:** Not separately enumerated — the code's extra safety margin is the only behavior that exists; the only real choice is whether to ratify it or revert it.
- **Final Decision:** Ratified — the shipped code's behavior is approved as the official standard; the code is not pulled back. `RE-DOC-01` §05 updated to match (2026-07-17).
- **Business Rationale:** The extra enforcement (allergen+never beyond spec) reduces safety risk, not increases it.
- **Technical Rationale:** Already implemented and tested; reverting would remove a safety margin for no documented benefit.
- **Engineering Impact:** None further if approved as-is.
- **AI Impact:** None. **Recommendation Engine Impact:** LF-D07 directly. **Database Impact:** None. **API Impact:** None. **Batch Impact:** None. **ETL Impact:** None. **Architecture Impact:** None.
- **Affected Documents:** `RE-DOC-01` §05 (update to match shipped behavior).
- **Affected Work Packages:** None. **Affected Tests:** `_tests/re_core.test.ts`. **Affected Epics:** None currently blocked by this.
- **Implementation Notes:** None — documentation catch-up only.
- **Acceptance Criteria:** Founder signature; `RE-DOC-01` §05 updated to match.
- **Future Review Trigger:** None.
- **Source Evidence:** `supabase/functions/_shared/services/re/constraints.ts` (`handleConstraintConflict`).

### FD-11 — Rule on the `mainIngredientClass` "dominant ingredient" derivation rule
- **Status:** Pending · **Origin:** `docs/project-history/work-packages/[ACTIVE]_WP-8FA_CandidateRepository_Architecture_Audit_v1.0.md`, blocker 8F-02
- **Context:** `ingredients.category` exists in the raw source CSV but was never seeded; no rule defines which ingredient "dominates" a multi-ingredient dish.
- **Problem Statement:** `CandidateRepository`'s `mainIngredientClass` field cannot be computed without this rule, and WP-8F's own STOP discipline forbids fabricating a default.
- **Alternatives Considered:** By weight/quantity; by listing order in source data; via a curated override table — enumerated in `Engineering_Execution_Baseline_v1.0.md` §6 FD-11, sourced from the WP-8FA audit's own framing.
- **Final Decision:** Not yet ratified — this is the single remaining genuine blocker of the four originally identified in WP-8F.
- **Business Rationale:** Directly affects variety/scoring correctness for any dish with multiple significant ingredients.
- **Technical Rationale:** The other three original WP-8F blockers (cuisine_family, beef/pork, halal/seasonal) were resolved or reclassified as documented deferrals by WP-8FA; this is the one that could not be.
- **Engineering Impact:** Blocks the final field of `CandidateRepository` in Epic 1.
- **AI Impact:** None. **Recommendation Engine Impact:** `DishCandidate.mainIngredientClass`, feeding LF-D/E variety and scoring.
- **Database Impact:** Would require seeding `ingredients.category` if a rule is ratified. **API Impact:** None directly. **Batch Impact:** `database/etl/generate_re_seeds.py` would need extension. **ETL Impact:** Same. **Architecture Impact:** None — `CandidateRepository`'s interface already accommodates the field.
- **Affected Documents:** `WP-8FA`, `REPO-CERT-019`.
- **Affected Work Packages:** WP-8F, WP-8FA, and whichever WP implements Epic 1.
- **Affected Tests:** New adapter test (Epic 1, per `Engineering_Execution_Baseline_v1.0.md`).
- **Affected Epics:** Epic 1.
- **Implementation Notes:** Do not implement a default in the meantime — per WP-8F's own explicit rule against fabricated defaults.
- **Acceptance Criteria:** Founder specifies the dominant-ingredient rule; `CandidateRepository` implements it; a new adapter test asserts correct behavior on a multi-ingredient dish.
- **Future Review Trigger:** None.
- **Source Evidence:** `docs/project-history/certificates/[ACTIVE]_REPO-CERT-019_WP-8FA_CandidateRepository_Audit_v1.0.md`.

### FD-12 — `dish_combos` cuisine-destination column
- **Status:** Pending (half-closed) · **Origin:** `docs/research/[ACTIVE]_Phase3_5_Project_Integration_Review_v1.0.md` §9/§14 (`B4-GAP-001`, `B5-GAP-003`), `docs/research/[ACTIVE]_Batch5_Pipeline_Package_v1.1.md` (`B5-RES-003`)
- **Context:** The original finding said neither `dishes` nor `dish_combos` had a cuisine-destination column. Live verification this audit chain confirms `dishes.cuisine_id` now exists (migration `021_cuisines_reference.sql`) — resolved on that side — but `dish_combos` still has **no** cuisine column at all, confirmed via direct `information_schema.columns` query.
- **Problem Statement:** Does `dish_combos` need the same fix, and if so, what value goes in it for each of the 35 rows?
- **Alternatives Considered:** Add `dish_combos.cuisine_id` (nullable FK, same pattern as `dishes`) with a deterministic backfill from combo-member dishes' dominant cuisine; or explicitly rule combo-level cuisine out of scope for MVP if no feature needs it — both stated in last session's Founder Decision Book, sourced from direct schema comparison.
- **Final Decision:** Not yet ratified.
- **Business Rationale:** Only matters if a future feature (e.g., combo-level variety scoring) needs to read a combo's cuisine.
- **Technical Rationale:** The `dishes`-side fix (migration 021) is exactly the pattern that would be replicated.
- **Engineering Impact:** Low today — no current Epic reads combo-level cuisine.
- **AI Impact:** None currently. **Recommendation Engine Impact:** None currently — would matter only if Epic 9 (Context Assembly) or a future combo-variety feature needs it.
- **Database Impact:** `public.dish_combos` (new column, if ratified). **API Impact:** None. **Batch Impact:** Combo-cuisine backfill logic, if ratified. **ETL Impact:** `generate_re_seeds.py`, if ratified. **Architecture Impact:** None.
- **Affected Documents:** `Phase3_5_Project_Integration_Review_v1.0.md` (should record the dishes-side resolution at next revision).
- **Affected Work Packages:** None currently open.
- **Affected Tests:** None currently. **Affected Epics:** None currently — flagged as latent, not urgent.
- **Implementation Notes:** Do not silently drop this — defer explicitly with a dated note if no feature needs it soon.
- **Acceptance Criteria:** Either the column is added and backfilled, or a Founder statement explicitly scopes it out of MVP.
- **Future Review Trigger:** Re-evaluate the moment any Epic proposes combo-level cuisine/variety logic.
- **Source Evidence:** live `information_schema.columns` query, this audit chain, confirming `dishes.cuisine_id` exists and `dish_combos` has no cuisine column.

### FD-13 — `POST /v1/events` idempotency/dedup-key handling
- **Status:** Pending · **Origin:** `docs/architecture/[ACTIVE]_DOC-P3-06_API_Contract_Specification_v1.2.md` §08
- **Context:** DOC-P3-06 §08 states, verbatim: *"No `Idempotency-Key` field exists in `interaction_events` today. A network retry of a `dish_cooked` event, for example, would double-count in LF-J02's `interaction_count++`."*
- **Problem Statement:** Should the client (no schema change) or the server (new dedup-key column) own retry-safety?
- **Alternatives Considered:** Option (a) client-side responsibility, no schema impact — "recommended for MVP" per DOC-P3-06 itself; Option (b) a future Schema Evolution Request adding a client-generated dedup key column. Both stated verbatim in the primary source.
- **Final Decision:** Not yet ratified — DOC-P3-06 explicitly frames this as "Recommendation for Founder confirmation," not yet signed.
- **Business Rationale:** A wrong guess here compounds directly into `interaction_count`, which feeds cold-start-exit logic (J02, J05) and the MVP's Day-0/Day-90 acceptance metric.
- **Technical Rationale:** Option (a) requires zero schema change and is consistent with the current freeze.
- **Engineering Impact:** Directly load-bearing for Epic 5 (Event Ingestion) — should not be silently assumed.
- **AI Impact:** None directly. **Recommendation Engine Impact:** LF-J01/J02 (interaction-count integrity).
- **Database Impact:** None if Option (a); `interaction_events` gets a new column if Option (b). **API Impact:** `POST /v1/events` retry semantics. **Batch Impact:** None. **ETL Impact:** None. **Architecture Impact:** None.
- **Affected Documents:** `DOC-P3-06` §08 (sign-off only, no content change needed for Option (a)).
- **Affected Work Packages:** None yet open. **Affected Tests:** New `_tests/events_endpoint.test.ts` retry/dedup test case (Epic 5, not yet written).
- **Affected Epics:** Epic 5.
- **Implementation Notes:** Write the retry test parameterized on whichever option is confirmed — do not hardcode Option (a) into the test before it's signed.
- **Acceptance Criteria:** A one-line Founder sign-off on Option (a) (or a ruling for Option (b) plus its schema change).
- **Future Review Trigger:** None.
- **Source Evidence:** `docs/architecture/[ACTIVE]_DOC-P3-06_API_Contract_Specification_v1.2.md` §08, the `[DCR]` line quoted above.

---

## 8. Product Philosophy Decisions

### PD-01 — Class-first architecture
- **Status:** Ratified (document freeze, RE-DOC-03) · **Date:** June 2026 · **Origin:** RE-DOC-03 §01
- **Context / Problem Statement:** A dish-first recommender defaults to popularity and gives every new user the same plan regardless of region or cohort.
- **Final Decision, verbatim:** *"The class system is the architectural fix for cold-start failure... The rule: Cohort + context → class. Class → dish candidates. Scoring only within class candidates. A dish from class BF_LIGHT_GRAIN can never appear in a LUNCH_CURRY_RICE slot, regardless of its genome score."*
- **Alternatives Considered:** Not recorded — the source states only the adopted design, not a rejected alternative.
- **Business/Technical Rationale:** Prevents "every new user from Madurai gets the same plan as every new user from Amritsar" (RE-DOC-03's own stated failure mode of the rejected dish-first approach).
- **Engineering/AI/RE Impact:** Governs the entire candidate-generation and scoring pipeline; is the reason `re_meal_classes` exists as a schema layer distinct from `dishes`.
- **Database/API/Batch/ETL Impact:** `re_engine.re_meal_classes`, `re_class_dish_options`; Batch 3 pipeline package.
- **Affected Documents:** RE-DOC-03, DOC-P3-03 §04, DOC-P3-04 ERD.
- **Affected Epics:** Underlies Epic 1's `CandidateRepository` design entirely.
- **Source Evidence:** direct `.docx` extraction this session, `docs/architecture/[ACTIVE]_RE-DOC-03_Class_Taxonomy_Scoring.docx`.

### PD-02 — RE module isolation ("the RE is the product")
- **Status:** Ratified (document freeze, RE-DOC-01) · **Origin:** RE-DOC-01 §01
- **Final Decision, verbatim:** *"The RE is not a feature — it is the product... Every change must deploy without touching the main app codebase or risking regression in auth, plan display, or user profile management."*
- **Alternatives Considered:** Not recorded — RE-DOC-01 states the rejected default ("Most apps embed recommendation logic directly into the application layer") and calls it "a product-destroying mistake" for FooFoo, but does not enumerate a formal alternatives analysis beyond that.
- **Business/Technical Rationale:** Isolation permits scoring/ML changes, A/B tests, and RE failure without app-wide regression or outage (RE-DOC-01's own concern/isolation table).
- **Engineering Impact:** This is why `supabase/functions/_shared/services/re/` exists as pure, DB-agnostic domain logic behind injected ports — confirmed by direct code inspection across this audit chain.
- **Affected Documents:** RE-DOC-01, DOC-P3-06 (API contract), DOC-P4-00.
- **Affected Epics:** Foundational to all RE-related Epics.
- **Source Evidence:** direct `.docx` extraction this session, `docs/architecture/[ACTIVE]_RE-DOC-01_Architecture.docx`.

### PD-03 — Freemium monetization with a 90-day habit window
- **Status:** Ratified (ACTIVE product document) · **Origin:** `docs/product/[ACTIVE]_DOC-08_Revenue_v1.0.docx`
- **Final Decision:** Freemium (₹0 base) with a paid tier (₹99/₹149) introduced only after a 90-day habit-formation window, per the Validation Audit's independent reconstruction of DOC-08 (§A.1).
- **Alternatives Considered:** Not re-read in full this session — cited from the Validation Audit's own reconstruction, not re-derived.
- **Business Rationale:** Habit formation before monetization, consistent with DOC-01's retention-first philosophy.
- **Affected Documents:** DOC-08. **Affected Epics:** None directly (business-model layer, not an engineering Epic).
- **Source Evidence:** `docs/project-history/work-packages/[ACTIVE]_WP-9_Validation_Audit_v1.0.md` §A.1 (not re-verified independently this session — flagged as citing a secondary reconstruction, not the primary `.docx`, for time reasons).

### PD-04 — Invite-only GTM to 500 DAU
- **Status:** Ratified · **Origin:** `docs/product/[ACTIVE]_DOC-07_GTM_v1.0.docx`, per Validation Audit §A.1
- **Final Decision:** Invite-only launch channel targeting 500 DAU as the first milestone.
- **Source Evidence:** Same secondary-reconstruction caveat as PD-03.

### PD-05 — DPDP-first legal posture
- **Status:** Ratified · **Origin:** `docs/product/[ACTIVE]_DOC-09_Legal_v1.0.docx`
- **Final Decision:** Consent capture, data export, and data deletion are explicitly marked "non-negotiable before launch" (per DOC-09, cited across WP-9/Closure Review's LF-M01–M03 treatment).
- **Engineering Impact:** Directly produces FD-13's stakes and Epic 7/8's DPDP work in the Baseline/Launch Plan.
- **Source Evidence:** `docs/product/[ACTIVE]_DOC-09_Legal_v1.0.docx`, cited consistently across all three predecessor audits.

## 9. Recommendation Engine Decisions

### RE-01 — Cold-start philosophy: cohort intelligence over generic popularity
- **Status:** Ratified (document freeze, RE-DOC-04) · **Origin:** RE-DOC-04 §01
- **Final Decision, verbatim:** *"The cold start problem is the most critical RE challenge... The wrong answer is generic popularity. The right answer is cohort intelligence — using secondary research about what households like this one typically enjoy, supplemented by contextual signals."*
- **Alternatives Considered:** Generic popularity — explicitly named and rejected in the source, not merely omitted.
- **Engineering Impact:** Directly produces the `re_cohorts`/`re_cohort_class_priors` schema layer and FD-07's stakes.
- **Source Evidence:** direct `.docx` extraction this session, `docs/architecture/[ACTIVE]_RE-DOC-04_ColdStart_Variety_Suppression.docx`.

### RE-02 — Continuous confidence ladder (Day 0 → Day 60+)
- **Status:** Ratified · **Origin:** RE-DOC-04 §01 confidence-ladder table; `DOC-P3-03` §07 LF-E01
- **Final Decision:** Five confidence bands (Day 0: 0.40–0.65; Day 1–3: 0.55–0.72; Day 3–14: 0.68–0.82; Day 14–60: 0.80–0.91; Day 60+: 0.88–0.96), interpolated continuously, not switched at fixed thresholds.
- **Engineering Impact:** `interpolateWeightLadder` (LF-E01), tested for partition-of-unity at every tier boundary.
- **Source Evidence:** direct `.docx` extraction this session.

### RE-03 — Probabilistic exploration (Thompson Sampling Beta-bandit)
- **Status:** Ratified · **Origin:** `DOC-P3-03` §07 LF-E06 (already documented in the WP-9 lineage, not re-derived this session)
- **Final Decision:** Exploration is a Beta-bandit sampler targeting ~10% slate exploration, not a fixed rule-based rotation.
- **Engineering Impact:** `computeExplorationBonus`, tested; `updateBanditParams` implemented but currently dead code (per `Final_Evidence_Closure_v1.0.md` §4, J04) pending Epic 5.
- **Source Evidence:** cited from prior audit chain, not re-verified this session for time reasons.

### RE-04 — Neutral-fallback philosophy
- **Status:** Ratified · **Origin:** `DOC-P3-03` LF-E02
- **Final Decision:** When cohort or personal data is unavailable, default to a neutral 0.50 score rather than a biased guess or a hard failure.
- **Engineering Impact:** Directly confirmed live this audit chain: `re_cohort_class_priors` = 0 rows, and `scoring.ts`'s `cohortPrior()` correctly falls back to 0.50 rather than erroring.
- **Source Evidence:** live Supabase query, this audit chain.

### RE-05 — Variety via MMR + explicit rule windows
- **Status:** Ratified · **Origin:** `DOC-P3-03` §08
- **Final Decision:** Maximal Marginal Relevance (λ=0.70 MVP) plus five explicit rule windows (cuisine-family cap, fried-dish cap, ingredient-repeat cap, dish-repeat cap, breakfast-class cap) — not pure novelty-maximization.
- **Engineering Impact:** `variety.ts`; 3 of 5 rules currently wired per `Final_Evidence_Closure_v1.0.md` §4 (F02), Epic 4 in the Baseline closes the gap.
- **Source Evidence:** cited from prior audit chain.

### RE-06 — Defense-in-depth safety gating (run twice, not once)
- **Status:** Ratified · **Origin:** `DOC-P3-03` §06/§10, RE-DOC-03 §03
- **Final Decision:** Hard constraints run before scoring (§06); safety gates run again after ranking (§10) — a deliberate second pass, not a single filtering step.
- **Engineering Impact:** `constraints.ts` + `safety.ts`, both tested independently; the second pass is why `suggestion_logs`/safety-gate SQL exist as a distinct validation layer (`902`).
- **Source Evidence:** cited from prior audit chain; migration/validation cross-reference confirmed this audit chain (`019_rls_policies.sql`, `902` script behavior).

## 10. AI Behaviour Decisions

### AI-01 — Six Working Principles (no invented values; config not hardcoded)
- **Status:** Ratified (document freeze, DOC-P3-03) · **Origin:** `DOC-P3-03` lines 25–31
- **Final Decision, verbatim:** *"1. Every specification traces to source document(s). 2. No assumptions — gaps flagged explicitly. 3. Hard constraints always run before scoring. 4. Config values stored in config tables, not hardcoded. 5. Failure behaviors specified with same precision as success paths. 6. All CDM entities referenced by name and number."*
- **Business/Technical Rationale:** These six principles are the governing discipline behind every other Ratified decision in §9 and behind WP-8F's own STOP behavior (refusing to fabricate `CandidateRepository` field mappings) — the single clearest throughline in the entire repository's engineering history.
- **Engineering Impact:** Directly produced the `[UNRESOLVED]`/`[PROPOSED]` tagging convention used throughout `DOC-P3-03`, and the STOP discipline in WP-8F/WP-8FA.
- **Source Evidence:** direct extraction this session, `docs/architecture/[ACTIVE]_DOC-P3-03_Business_Logic_Specification_v1.0.md` lines 20–31.

### AI-02 — Explainability via reason-tags
- **Status:** Ratified · **Origin:** RE-DOC-01 §03 (API response contract)
- **Final Decision:** Every ranked dish in a slate response carries `reason_tags` (e.g., `["regional","weather"]`) alongside its score — not a black-box score only.
- **Engineering Impact:** `re/scoring.ts`/`re/engine.ts` DTOs already carry this field structurally (per RE-DOC-01's own sample response, confirmed this session).
- **Source Evidence:** direct `.docx` extraction this session (RE-DOC-01 §03 sample response body).

### AI-03 — Deterministic, reproducible seed/ETL pipeline
- **Status:** Ratified (demonstrated, not merely stated) · **Origin:** `[ACTIVE]_WP-9_Validation_Audit_v1.0.md` MF-08
- **Final Decision:** The CSV/xlsx→ETL→seed chain must be deterministic — proven by independently re-executing both ETL generators and confirming all committed seed migrations regenerate byte-identical (excluding timestamps).
- **Engineering Impact:** Underlies the trust basis for every Seed Gate (`905`) check re-confirmed live in this audit chain.
- **Source Evidence:** `[ACTIVE]_WP-9_Validation_Audit_v1.0.md` §A.2, MF-08 (not independently re-executed this session — cited, not re-verified, for time reasons).

## 11. Governance Decisions

### GOV-01 — Repository-history reconstruction is disclosed, not concealed
- **Status:** Ratified · **Origin:** `REPO-BOOT-03` (already fully evidenced in `[ACTIVE]_WP-9_Independent_Engineering_Due_Diligence_Audit_v1.0.md` §22 — not re-derived here)
- **Final Decision:** The current git history is an explicitly-disclosed fresh lineage (starting 2026-07-13), not a continuation of the original lost `apverse-labs` repository — stated openly in `CLAUDE.md` and `REPO-BOOT-03` rather than concealed or silently worked around.
- **Source Evidence:** `CLAUDE.md` header, `REPO-BOOT-03`.

### GOV-02 — Never delete a superseded document
- **Status:** Ratified · **Origin:** `CLAUDE.md`
- **Final Decision:** A superseded document is stamped `SUPERSEDED BY vX.Y` with a changelog note and retained, never deleted — applied to this Register's own predecessor (`[SUPERSEDED]_Founder_Decision_Book_v1.0.md`) as a live demonstration, not just a stated rule.
- **Source Evidence:** `CLAUDE.md`; this Register's own Supersedes field.

### AGR-005 / AGR-006 — Ratified Architecture Governance Records
- **Status:** Ratified · **Origin:** `docs/governance/[ACTIVE]_AGR-005_routing_rules_nullable_show_key_v1.0.md`, `[ACTIVE]_AGR-006_weight_ladder_numeric_conversion_v1.0.md`
- **Final Decision:** Not restated here — see each source document directly. Indexed so a future `AGR-007` has a discoverable precedent set.

## 12. Deferred Decisions

*None. No item in §7 has received an explicit, dated Founder deferral statement as of this Register's creation. Nothing is moved here on the basis of having simply gone unanswered for a while — that would violate Governance Principle 5 (§4).*

## 13. Superseded Decisions

| Decision | Superseded by | Reason |
|---|---|---|
| `[SUPERSEDED]_Founder_Decision_Book_v1.0.md` (as a whole document) | This Register | Scope expansion (product/RE/AI/governance philosophy decisions) and structural expansion (17 sections vs. 10, 24-field format vs. a shorter one) required a new canonical file per the naming standard's supersession process — content is carried forward unchanged, not altered. |

## 14. Decision Dependency Matrix

Carried forward unchanged from the superseded Book, extended with the new §8–§11 items where they touch an Epic. See `[ACTIVE]_Engineering_Execution_Baseline_v1.0.md` and `[ACTIVE]_Engineering_Launch_Plan_v1.0.md` for full Epic detail.

| Decision | Epic(s) | Code module(s) | Test(s) |
|---|---|---|---|
| FD-01 | None | — | — |
| FD-02 | Epic 1 | `re/scoring.ts` | `_tests/re_core.test.ts` |
| FD-03 | Epic 1 | `onboarding/orchestrator.ts` | `_tests/re_integration.test.ts` |
| FD-04 | Epic 2/3 | `services/` (all) | all existing suites |
| FD-05 | None | — | — |
| FD-06 | Epic 6 | `re/addons.ts` (new) | new addon suite |
| FD-07 | Epic 2 | `database/seeds/` (new), `orchestrator.ts` | `905...sql`, `_tests/re_integration.test.ts` |
| FD-08 | None | `DOC-01`, `DOC-04` | — |
| FD-09 | None | `DOC-10` §10 | — |
| FD-10 | None | `re/constraints.ts` | `_tests/re_core.test.ts` |
| FD-11 | Epic 1 | `adapters/supabase-stores.ts` | new adapter test |
| FD-12 | None currently | `public.dish_combos` | — |
| FD-13 | Epic 5 | `functions/events/` (new) | `_tests/events_endpoint.test.ts` (new) |
| PD-01/RE-01–06 | Epic 1 (foundational) | `re/` (entire module) | `_tests/re_core.test.ts` |
| PD-02 | All RE Epics (foundational) | `services/re/` module boundary | — |
| AI-01 | All Epics (governing discipline) | all `services/` code | all suites |
| AI-02 | Epic 3 | `re/scoring.ts`/`engine.ts` DTOs | `_tests/re_core.test.ts` |
| AI-03 | Epic 9 (Reproducibility) | `database/etl/` | `905...sql` |

## 15. Decision Traceability Matrix

Requirement → Architecture → RE Document → Implementation → Database → API → Batch → ETL → Tests → Work Packages → Epics → Acceptance Criteria, for the decisions with the fullest chains:

| Decision | Requirement | Architecture | RE Doc | Implementation | Database | API | Batch/ETL | Tests | WPs | Epics | Acceptance |
|---|---|---|---|---|---|---|---|---|---|---|---|
| PD-01 (class-first) | DOC-04 Step 3 | DOC-P3-03 §04 | RE-DOC-03 §01 | `resolvers.ts` | `re_meal_classes`, `re_class_dish_options` | none live | Batch 3 | `re_core.test.ts` | WP-8D | Epic 1 | class never crosses slot boundary (tested) |
| RE-02 (confidence ladder) | DOC-01 §07 | DOC-P3-03 §07 | RE-DOC-04 §01 | `scoring.ts interpolateWeightLadder` | `re_weight_ladder_config` | none live | seed 100 | `re_core.test.ts` | WP-8D | Epic 1/2 | partition-of-unity invariant holds at all tiers |
| RE-04 (neutral fallback) | DOC-01 §07 | DOC-P3-03 LF-E02 | RE-DOC-04 §01 | `scoring.ts cohortPrior` | `re_cohort_class_priors` (0 rows, confirmed live) | none live | — | `re_core.test.ts` | WP-8D | Epic 2 | non-neutral score once seeded (FD-07) |
| FD-11 (mainIngredientClass) | RE-DOC-02 dim 11 | DOC-P3-03 §06 | RE-DOC-02 | `CandidateRepository` (unbuilt) | `ingredients.category` (unseeded) | none | `generate_re_seeds.py` (would extend) | new adapter test (Epic 1) | WP-8F, WP-8FA | Epic 1 | Founder rule specified; adapter test passes |
| FD-13 (events idempotency) | DOC-01 §07 (data integrity) | DOC-P3-06 §08 | RE-DOC-01 §03 | none yet | `interaction_events` | `POST /v1/events` | — | new retry test (Epic 5) | none open | Epic 5 | sign-off recorded; retry test passes per ratified option |

## 16. Founder Sign-off Register

| Decision | Signed? | Date |
|---|---|---|
| AGR-005 | ✅ (per source document) | see source |
| AGR-006 | ✅ (per source document) | see source |
| PD-01–05, RE-01–06, AI-01–03, GOV-01–02 | ✅ (ratified via document freeze — no separate signature line exists for these; freeze status is the ratification mechanism) | see each source document's own freeze date |
| FD-01, FD-02, FD-03, FD-04, FD-05, FD-08, FD-09, FD-10 | ✅ (ratified in a claude.ai Founder decision-closing session; formalized in `[ACTIVE]_Founder_Ratification_Certificate_2026-07-16_v1.0.md`) | 2026-07-16 |
| FD-06, FD-07, FD-11, FD-12, FD-13 | ☐ Not yet signed — out of scope for this wave, tracked separately | — |

## 17. Version History

| Date | Change |
|---|---|
| 2026-07-16 (earlier same day) | `Founder_Decision_Book_v1.0.md` created — first canonical index, FD-01–13 only. |
| 2026-07-16 (this consolidation) | Book superseded by this Register. Scope expanded to product/RE/AI/governance philosophy decisions (PD-01–05, RE-01–06, AI-01–03, GOV-01–02), each cited to a directly-verified primary source (several `.docx` concept documents decoded and quoted directly for the first time this session). Structure expanded from 10 to 17 sections per the Final Governance Consolidation mandate. No FD-01–13 content altered — carried forward exactly. |
| 2026-07-16 (Wave 0 — Founder Ratification Certificate) | 8 of the 13 Pending FDs (FD-01, FD-02, FD-03, FD-04, FD-05, FD-08, FD-09, FD-10) ratified by the Founder in a claude.ai decision-closing session, formalized in `[ACTIVE]_Founder_Ratification_Certificate_2026-07-16_v1.0.md`. FD-06, FD-07, FD-11, FD-12, FD-13 remain Pending, explicitly out of scope for this wave. |
| 2026-07-17 (Wave 1 — document corrections) | §6 and §16 updated to reflect the 8 Wave-0 ratifications (Pending → Ratified). Corresponding document corrections applied: WP-8D/8E notes (FD-01), `DOC-P3-03` §07 worked example + LF-A08 clamp note (FD-02/FD-03), `DOC-P4-02` promoted DRAFT→ACTIVE as v1.1 with AD-01 resolved as Option 2 (FD-04), naming standard amended to v1.1 + six document headers corrected (FD-05), `DOC-01` §06 grocery-list scope corrected (FD-08), `DOC-10` §10 environment map corrected — **note:** the corrected Supabase project ref (`cmkswalqpmmqojwdmqbv`, per Founder confirmation) differs from the ref this Register previously described as "confirmed live" (`slsqtlygeekdppuyiiff`) — flagged, not silently reconciled (FD-09), `RE-DOC-01` §05 updated with the ratified LF-D07 behavior (FD-10). No schema, code, or migration changes made — documentation corrections only. |

---

## Critical Self-Review

Every Ratified entry in §8–§11 is backed by a direct quotation extracted this session from the actual frozen source file (RE-DOC-01, RE-DOC-03, RE-DOC-04 `.docx` files were decoded via their internal XML this session, not recalled from an earlier subagent's paraphrase) or, where a document was not re-read in full (PD-03, PD-04, RE-03, RE-05, RE-06, AI-03), that is stated explicitly as citing a prior audit's reconstruction rather than a fresh primary-source read. No alternatives-considered analysis was invented anywhere it was not already recorded — several entries say plainly "not recorded" rather than fabricate one. FD-01–13 are carried forward from the superseded Book with zero content changes. The one new engineering judgment in this document is the classification decision itself (which items are Ratified-via-freeze vs. still-Pending) — applied consistently using the rule "a FROZEN or ACTIVE-with-matching-header document's content is ratified; a DRAFT-headword or explicitly-flagged-open item is pending," not by any other criterion.

## Versioning & Placement
v1.0, filed under `docs/governance/` — supersedes `[SUPERSEDED]_Founder_Decision_Book_v1.0.md` at the same path, per the repository's naming standard (both retained).

Founder sign-off: _______________________ Date: ___________
