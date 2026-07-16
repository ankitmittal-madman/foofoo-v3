# Engineering Launch Plan v1.0

**Role:** Transitions FooFoo from Review Phase to Engineering Execution. Not an audit — no repository finding from WP-9 / WP-9 Validation Audit / Final Evidence Closure / Engineering Execution Baseline is repeated or re-derived here. This document's own contribution is: (1) a repo-wide sweep for Founder decisions not already captured as FD-01–FD-11, (2) a readiness classification of every Epic, (3) a sprint plan, (4) a repository-preparation checklist.
**Status:** ACTIVE
**Version:** v1.0
**Date:** 2026-07-16
**Placement:** docs/project-history/work-packages/
**No code, schema, or migration changes were made while producing this document — read-only investigation only, per instruction.**
**Predecessor documents (source of truth for all prior findings, not repeated here):**
- `[ACTIVE]_WP-9_Independent_Engineering_Due_Diligence_Audit_v1.0.md`
- `[ACTIVE]_WP-9_Validation_Audit_v1.0.md`
- `[ACTIVE]_Final_Evidence_Closure_v1.0.md`
- `[ACTIVE]_Engineering_Execution_Baseline_v1.0.md` (single source of truth for Epics 1–9, root causes RC1–RC5, and FD-01–FD-11 — this document extends, does not replace, it)

---

## 1. Executive Summary

The Engineering Execution Baseline already defines 9 Epics, 5 root causes, and 11 Founder decisions. This document's Phase 1 sweep searched product, RE, architecture, batch/research, ETL, seed, and code layers specifically for **business rules an engineer would have to silently invent** if implementation started today. It found **2 more genuine, evidence-backed Founder decisions** (FD-12, FD-13 — §2) that no prior document names, plus confirmation that one thing the Baseline's evidence-base predates (the Batch 4/5 "cuisine destination" blocker) is **already half-resolved** by a migration none of the four predecessor documents examined at that level of detail.

Of the 9 Epics, **3 are ready to implement immediately with zero Founder input** (Epic 4, and the housekeeping items), **4 are ready to start with only a narrow, already-scoped Founder input** (Epics 1, 2, 5, 6), and **2 have a hard, total Founder block on part of their scope** (Epic 6's build-order per FD-06, Epic 1's `mainIngredientClass` field per FD-11). Nothing is blocked by missing infrastructure — the Supabase project, CI, and test harness are all live and working (62/62 tests passing, confirmed via live Supabase access in the Baseline's Step 1).

The recommended first sprint (§8) is Epic 4 + the migration-drift housekeeping item — both are fully unblocked today, both close a real correctness/reproducibility gap, and both cost less than two days combined.

---

## 2. Founder Decision Register (Complete)

FD-01 through FD-11 are carried forward **verbatim** from the Engineering Execution Baseline §6 (which itself carried FD-01–FD-10 verbatim from the Final Evidence Closure Review §8, adding only FD-11). They are not reproduced in full table form again here to avoid drift between two copies of the same text — see Baseline §6 for the complete FD-01–FD-11 table. **Below are only the net-new items this session's repository sweep found**, each built to the same Decision Pack structure the task requires.

### FD-12 — Cuisine destination column for `dish_combos` (partially resolved, one side still open)

- **Title:** Does `public.dish_combos` need a `cuisine_id`/cuisine-destination column, and if so, what value goes in it for each of the 35 combo rows?
- **Why engineering is blocked:** The original Batch 4/5 finding (`B4-GAP-001`, `B5-GAP-003`, consolidated in `[ACTIVE]_Phase3_5_Project_Integration_Review_v1.0.md` §9/§14) was: **"Cuisine has no destination column — `public.dishes` AND `public.dish_combos` — confirmed absent... highest row-count impact of all gaps found."** Live verification this session shows this is now **half true**: `public.dishes.cuisine_id` **exists** (added by migration `021_cuisines_reference.sql`, confirmed live via `information_schema.columns`) and is exactly the field WP-8FA's `CandidateRepository` reconciliation relies on (`dishes.cuisine_id → cuisines.cuisine_group`). But `public.dish_combos` **still has no cuisine column at all** — confirmed by the same live query returning zero rows for `dish_combos`. No prior document (WP-9, its Validation Audit, the Closure Review, or the Baseline) checked this at the column level; all four assumed the "cuisine mapping problem" was closed by WP-8FA, but WP-8FA only proved the `dishes`-level mapping.
- **Current evidence:** `docs/research/[ACTIVE]_Phase3_5_Project_Integration_Review_v1.0.md` §9/§14 (original finding); live `information_schema.columns` query (this session) confirming `dishes.cuisine_id` exists, `dish_combos` has no cuisine column; migration `021_cuisines_reference.sql` (resolved the `dishes` side only).
- **Possible implementation impact:** If any Epic 1 adapter or future combo-scoring logic needs a combo's cuisine (e.g., for variety/MMR diversity across combo-based dishes, RE-DOC-04 §02), it cannot be computed today — there is no column to read.
- **Recommended decision:** Add `dish_combos.cuisine_id` (nullable FK to `cuisines`, same pattern as `dishes.cuisine_id`) and backfill from combo-member dishes' dominant cuisine (a deterministic derivation, not a Founder judgment call, once the column exists) — or explicitly rule combo-level cuisine out of scope for MVP scoring if no Epic currently needs it (need to confirm against Epic 1/9 designs before treating this as urgent).
- **Default if Founder does not decide:** Leave unresolved; combo-level cuisine remains unavailable to any scoring/variety logic that might want it. Low risk today since no current Epic explicitly reads combo cuisine — this is a latent gap, not an active blocker, until an Epic needs it.
- **Risk:** Low today, Medium if Epic 9 (Context Assembly) or a future combo-variety feature is scoped without checking this first.
- **Affected files:** `database/migrations/` (new migration if approved), `docs/research/[ACTIVE]_Phase3_5_Project_Integration_Review_v1.0.md` (should be marked resolved-on-dishes/open-on-combos at next revision).
- **Affected APIs:** None directly (no endpoint currently exposes combo cuisine).
- **Affected tables:** `public.dish_combos`.
- **Affected ETL:** `database/etl/generate_re_seeds.py` if a combo-cuisine backfill is added.
- **Affected tests:** None yet (no code depends on this today).

### FD-13 — `POST /v1/events` idempotency/dedup-key handling (already drafted, never confirmed)

- **Title:** Should the client or the server be responsible for preventing double-counted events on retry?
- **Why engineering is blocked:** `docs/architecture/[ACTIVE]_DOC-P3-06_API_Contract_Specification_v1.2.md` §08 (line ~544) already states the problem precisely and in full: *"No `Idempotency-Key` field exists in `interaction_events` today. A network retry of a `dish_cooked` event, for example, would double-count in LF-J02's `interaction_count++`."* It offers two options and a recommendation (Option a: client-side responsibility, no schema change — "recommended for MVP") but is explicitly phrased as **"Recommendation for Founder confirmation"** — i.e., drafted, not ratified. This is directly load-bearing for **Epic 5 (Event Ingestion)** in the Baseline: implementing G01/G02/J01/J02 today without this ruling means building against an unconfirmed assumption.
- **Current evidence:** `DOC-P3-06 v1.2` §08, the exact `[DCR]` line quoted above.
- **Possible implementation impact:** If left unconfirmed and Epic 5 proceeds on the "client responsible" default, a client bug or bad network retry silently inflates `interaction_count`, which feeds directly into `computeOnboardingConfidence`/cold-start-exit logic (J02, J05) — a correctness risk in exactly the metric DOC-01 §07 treats as the MVP's go/no-go signal.
- **Recommended decision:** Approve Option (a) as written (client-side responsibility, no schema change) — it is already the document's own recommendation and requires no new engineering work, only a signature.
- **Default if Founder does not decide:** Engineering should treat Option (a) as the working assumption **only if explicitly told to proceed without sign-off**; per this task's own instruction ("do not guess"), Epic 5 should not silently adopt Option (a) without at least a documented interim decision, since a wrong guess here compounds into the cold-start metric.
- **Risk:** Medium — cheap to fix now (a one-line documentation sign-off), expensive to fix later (would require a schema change + backfill if Option (b) is chosen after Epic 5 ships).
- **Affected files:** `docs/architecture/[ACTIVE]_DOC-P3-06_API_Contract_Specification_v1.2.md` (sign-off only, no content change needed).
- **Affected APIs:** `POST /v1/events`.
- **Affected tables:** `public.interaction_events` (only if Option (b) is chosen instead).
- **Affected ETL:** None.
- **Affected tests:** Epic 5's new `_tests/events_endpoint.test.ts` should include a retry/dedup test case either way — write it now, parameterized on whichever option is confirmed.

**Nothing else met this document's bar for a new Founder decision.** The repo-wide sweep (grep across `docs/architecture`, `docs/product`, `docs/governance`, `docs/research`, and `supabase/functions/_shared/services` for TBD/undecided/arbitrary/assumption markers) turned up two other candidates that, on inspection, are **already resolved** and are noted here only to show they were checked, not silently skipped:
- **B5-RES-001** (`dish_combo_items.role` CHECK constraint vs. an 8-value source file) — **resolved** by migration `025_combo_component_type_and_slot_array.sql`, which added a parallel `component_type` column (8-value CHECK) and deliberately left `role` unchanged, per "Architecture Freeze v1.0 Pack C." Confirmed live: `component_type` column exists with the documented CHECK. No Founder action needed.
- **B5-RES-002** (deterministic string-matching for a dish FK) — was reclassified Architecture-owned, not Founder-owned, by the Batch 5 package's own Task 4 review (`docs/research/[ACTIVE]_Batch5_Pipeline_Package_v1.1.md` §Task 4). Not a Founder decision at all.

---

## 3. Engineering Ready Register

Epics/items that can start **today**, with zero Founder input required:

| Item | Why it's ready | Blocking status |
|---|---|---|
| **Epic 4 — Pipeline Wiring Fixes** | Pure code change inside existing, already-tested modules (`engine.ts`, `variety.ts`). No new adapter, endpoint, schema, or business-rule decision needed. | **Ready immediately.** |
| **Housekeeping — migration-drift remediation** (Baseline §2.1: `103_production_cuisines`/`103_production_ingredients`) | Requires only retrieving the already-applied SQL from the live project and committing it as a numbered file — no new design decision. | **Ready immediately.** |
| **Epic 1 — Repository Adapters, 2 of 3 remaining `CandidateRepository` fields + all 8 sibling ports** | `cuisineFamily` and `hasBeef`/`hasPork` mappings are already proven (WP-8FA); the other 8 ports (cohort-resolution, config, priors, etc.) have no known mapping blocker — they simply haven't been built yet. | **Ready for 8 of 9 ports; the 9th (`CandidateRepository`'s `mainIngredientClass` field) needs FD-11.** |
| **Epic 2 — Cold-Start Integrity Package, seeding half** | `re_cohort_class_priors` seeding needs no new decision — the config values (weight ladder tiers, neutral fallback) are already ratified and implemented in `scoring.ts`. | **Ready immediately** (independent of Epic 1's adapter work for the seeding half specifically). |
| **Epic 3 — HTTP Handler Layer, contract level** | `DOC-P3-06` §06.3 and its endpoint table (line 582) confirm `/v1/onboarding`, `/v1/recommendations`, `/v1/events`, `/v1/plan/{user_id}/{week}`, `/v1/health` are **"already active-by-design per RE-DOC-01 — no further approval needed to proceed to Phase 4 implementation."** The contracts are not blocked; only Epic 1's adapters gate a *working* deployment. | **Contract-ready now; functionally blocked on Epic 1 (not a Founder block).** |
| **Epic 7 — DPDP Export/Delete** | Pattern already proven end-to-end by the live `ConsentService`/`ConsentRepository` chain; DOC-09 already mandates this with no open design question. | **Ready immediately, fully parallelizable with everything else.** |
| **Epic 8 — Nightly CRON Registration** | Scheduler class (`NightlyPlanScheduler`) is already built and tested; only registration mechanics remain. | **Ready once Epic 1 lands** (needs real data to act on) — no Founder input. |

---

## 4. Blocked Register

| Item | Blocked by | Detail |
|---|---|---|
| Epic 1 — `CandidateRepository.mainIngredientClass` field only | **Founder decision (FD-11)** | Dominant-ingredient derivation rule undefined; do not fabricate a default (WP-8F's own STOP discipline). |
| Epic 6 — Member Add-ons, build-order/priority | **Founder decision (FD-06)** | DOC-03 calls this "the differentiator no competitor has built," but its position in the sequence relative to the learning loop is a Founder prioritization call, not an engineering one — the Baseline's own recommended sequence (§5) is a *recommendation*, not a ratified order. |
| Epic 5 — Event Ingestion, idempotency design | **Founder decision (FD-13, new this session)** | See §2 — do not build the event-write path assuming Option (a) is silently approved; get the sign-off first (it is cheap). |
| Epic 6 — Member Add-ons, addon-repository field mappings | **Missing data / undefined mapping** — not yet investigated at WP-8F/8FA's level of rigor | No WP-8F-style mapping-proof exercise has been run for the addon-side ports (`re_addon_dish_options`, `re_household_addon_plans` reads) the way it was for `CandidateRepository`. This is a **missing-analysis blocker**, not a Founder blocker — recommend a WP-8F-style mapping audit for Epic 6's ports before implementation, not a guess. |
| FD-12 (`dish_combos` cuisine) | **Blocked by missing documents** — no Epic currently reads combo-level cuisine, so this cannot be resolved by "just building it"; it needs a scoping decision first (does any planned feature need it?). | See §2 FD-12. |
| Nothing is blocked by missing infrastructure. | — | Supabase project (`slsqtlygeekdppuyiiff`) is live, migrations apply cleanly, CI passes, 62/62 tests green — confirmed via this session's own live verification (Baseline §2). |

---

## 5. Sprint Plan

Four sprints, each roughly Epic-sized, sequenced per the Baseline's §5 recommended order with the two zero-dependency items pulled into Sprint 0.

### Sprint 0 — Unblock & De-risk (no Founder input needed)
- **Objectives:** Close the pipeline wiring gap (Epic 4); close the migration-drift reproducibility gap (housekeeping item); get FD-13 signed off (cheap, high-leverage ask).
- **Dependencies:** None.
- **Deliverables:** `engine.ts`/`variety.ts` wiring fix + new 21-slot regression test; committed `031_production_cuisines.sql`/`032_production_ingredients.sql` (or documented exception) + paired rollbacks; a one-line Founder sign-off on FD-13.
- **Validation:** New 21-slot test green; `905` + a rebuild-from-migrations check confirms the two new migration files reproduce the live schema exactly.
- **Migration:** 2 new numbered migration files (retrieved from live `pg_dump`/introspection of the two orphan migrations).
- **Rollback:** Paired rollback files for both new migrations, following the existing `NNN_description_rollback.sql` convention.
- **Documentation updates:** `docs/README.md` migration count refresh (already flagged in WP-9); note the FD-13 sign-off in `DOC-P3-06`'s changelog.
- **Testing:** New 21-slot `generateWeekPlan` test; existing 62 tests must remain green.
- **Definition of Done:** Zero orphan migrations; variety/safety-gate wiring verified by a realistic test; FD-13 resolved.

### Sprint 1 — Repository Adapters (Epic 1)
- **Objectives:** Build all 9 concrete adapters; resolve FD-11 or explicitly scope `mainIngredientClass` out with a documented fallback.
- **Dependencies:** Sprint 0's wiring fixes should land first so adapters are tested against a pipeline that already calls everything it's supposed to.
- **Deliverables:** `SupabaseCandidateRepository` + 8 siblings in `supabase-stores.ts`.
- **Validation:** Live-adapter integration test producing a real, non-empty, constraint-passing slate for ≥3 real cohorts.
- **Migration:** None expected (schema already supports all 9 ports per the ERD) unless FD-11's resolution requires a new derivation column/rule.
- **Rollback:** N/A unless a schema change is added for FD-11.
- **Documentation updates:** `DOC-P4-02` should move from DRAFT toward ratification once adapters prove the architecture works end-to-end (feeds FD-04).
- **Testing:** One integration test per adapter; extend `re_integration.test.ts`.
- **Definition of Done:** Per Baseline Epic 1's DoD/Acceptance Criteria verbatim.

### Sprint 2 — Cold Start + HTTP Surface (Epics 2 & 3)
- **Objectives:** Seed cold-start priors, fix taste-vector persistence, deploy the 5 core HTTP endpoints.
- **Dependencies:** Sprint 1 (adapters must exist for endpoints to do anything real).
- **Deliverables:** Seeded `re_cohort_class_priors`; fixed `persistTasteVector`; 5 deployed endpoints (`/v1/onboarding`, `/v1/recommendations`, `/v1/plan`, `/v1/plan/refresh`, `/v1/health`).
- **Validation:** End-to-end onboarding→recommendation call against live data, no fakes.
- **Migration:** New seed file for cohort priors + paired rollback.
- **Rollback:** Seed rollback; endpoints can be un-deployed by removing the function directories.
- **Documentation updates:** `docs/README.md` "Repository status" section should note the first live-reachable RE path.
- **Testing:** New endpoint test suites mirroring `consent.test.ts`.
- **Definition of Done:** Per Baseline Epics 2/3's DoD verbatim.

### Sprint 3 — Learning Loop, Add-ons, DPDP, CRON (Epics 5, 6, 7, 8 — parallelizable across engineers)
- **Objectives:** Close the remaining Release Blocker Register items.
- **Dependencies:** Sprint 2 (HTTP layer must exist).
- **Deliverables:** `/v1/events` + gesture processing; add-on generation (pending FD-06 priority ruling and the Epic 6 mapping-audit blocker in §4); DPDP export/delete; CRON registration.
- **Validation:** Per-Epic acceptance criteria in the Baseline §4.
- **Migration:** None expected for events/DPDP/CRON; Epic 6 may need one pending its mapping audit.
- **Rollback:** N/A unless Epic 6's audit surfaces a schema need.
- **Documentation updates:** Close FD-06 by recording the Founder's actual build-order ruling; update the Release Blocker Register status.
- **Testing:** New suites per Epic as specified in the Baseline.
- **Definition of Done:** All items in the Baseline's inherited Release Blocker Register (Final Evidence Closure §10) are closed.

---

## 6. Repository Preparation Checklist

| Category | Item | Recommended action |
|---|---|---|
| **Temporary/reference code** | `database/validation/WP-3D_Check2_Fix_Reference.sql` | Naming-standard violation (no `NNN_` prefix); already flagged in WP-9. Rename or move to a non-numbered reference location before Sprint 0 touches `database/validation/`. |
| **Technical debt** | `updateBanditParams` (J04) implemented but uncalled; `updateSlotSlate` doesn't refresh `cold_start_mode` on slot refresh (MF-07, Validation Audit) | Both are one-line fixes; fold into Sprint 1 (bandit wiring) and Sprint 2 (slot refresh) respectively rather than opening separate tickets. |
| **Stale documents** | `docs/README.md` (migration count "29" vs actual 30+2 orphans; validation-staleness claim already fixed by REPO-CERT-010 but not reflected) | Refresh in Sprint 0 alongside the migration-drift fix — same PR, same review. |
| **Stale documents** | `docs/architecture/[ACTIVE]_DOC-10_Technical_Architecture_v1.0.docx` §10 environment map (superseded Supabase refs/org, FD-09) | Refresh — low effort, high trust value; do in Sprint 0 or as a standalone doc-only PR, not gated on any Epic. |
| **Stale documents** | `docs/visuals/[ACTIVE]_DOC-06_Visual_Design_System_Explorer_v1.0.html` (teaches a removed long-press gesture per Validation Audit MF-05) | Regenerate against DOC-05 v1.2/DOC-06 v1.1's swipe-reveal model. Not urgent for backend Epics but will mislead frontend work if left. |
| **Duplicate documents** | `docs/governance/[ACTIVE]_PM-SUPP-02_Risk_Register_v1.0.md` exists as both `.docx` and `.md` with no declared source of truth | Pick one, mark the other superseded, per the Baseline Register's own Version Conflict Policy. Low priority, no Epic depends on it. |
| **Identifier collision** | `DOC-P3-05` claimed by two unrelated documents (`docs/architecture/…Part_A_Readiness_Migration_Strategy` and `docs/governance/…Architecture_Gap_Register`) — flagged in WP-9 §4a | No Epic is blocked by this today, but it should be resolved before any future document cites "DOC-P3-05" ambiguously. Recommend during Sprint 0's documentation pass. |
| **Obsolete work packages, never executed** | `REPO-WP-03`, `REPO-WP-03D`, `REPO-WP-04B`, `REPO-WP-04DA`, `REPO-WP-04DB`, `REPO-WP-04DC`, `Repository_Recovery_Work_Package_Plan` — all still carry header status **"DESIGNED — awaiting Founder approval to execute"** while filed under the `[ACTIVE]` naming token, with no companion certificate anywhere in `docs/project-history/certificates/` | This is a long-standing, self-disclosed gap (flagged as far back as `REPO-BOOT-03`, 2026-07-13) unrelated to the current RE work. Does not block any Epic in this plan. Recommend a single Founder ruling (execute, formally abandon, or re-file as `[SUPERSEDED]`) as its own small governance item, not folded into any Sprint above. |
| **Documentation needing updates after implementation** | `DOC-P4-02` (DRAFT → ACTIVE pending FD-04); the ACTIVE/DRAFT contradiction across `DOC-P3-02/03/03A/04/05-Part-A` and the vNext Addendum (FD-05); `docs/research/[ACTIVE]_Phase3_5_Project_Integration_Review_v1.0.md` (should record FD-12's dishes-side resolution at next revision) | Each is already a named Founder decision (FD-04/FD-05) or this session's new FD-12 — listed here only so nobody forgets to *close the loop* in documentation once the Founder rules, not as new work. |
| **Reproducibility gap** | 2 live migrations with no repo file (`103_production_cuisines`, `103_production_ingredients`) | Already the Sprint 0 deliverable — listed here too since it is simultaneously a repo-hygiene item and an engineering task. |

---

## 7. Risks

1. **Silent-assumption risk (the risk this entire task exists to prevent):** the highest risk is not a missing feature, it's an engineer proceeding on Epic 5 or Epic 6 without FD-13 or the addon mapping audit, and quietly picking a default. Mitigation: this document's own Blocked Register (§4) exists precisely so a sprint cannot start those two items without a visible open item first.
2. **Sequencing risk:** Epic 1 is the dependency root for almost everything (Sprint 1 gates Sprint 2 and half of Sprint 3). If Epic 1 slips, the entire plan slips — recommend starting Epic 1 the moment Sprint 0 closes, not waiting for a "quiet period."
3. **Cold-start metric risk (inherited from Baseline FD-07, restated because it compounds with FD-13):** if Epic 5's event path ships with an unconfirmed idempotency assumption AND Epic 2's cold-start fixes are delayed, the MVP's single go/no-go metric (DOC-01 §07) could be corrupted by double-counted events on top of an already-thin signal. Recommend Sprint 2 and Sprint 3's event work not overlap without FD-13 resolved first.
4. **Reproducibility risk (new, this session):** until the two orphan migrations are committed, a clean-room rebuild from `database/migrations/` will not match production exactly — a real gap in the GREEN certification's guarantee that should not be allowed to persist into a second sprint.
5. **Scope-creep risk on FD-12:** because no current Epic reads combo-level cuisine, there's a temptation to either silently ignore it (creates a hidden gap once someone needs it) or over-engineer a fix now (wasted work if nothing ever needs it). Recommend explicitly deferring it with a dated note, not silently dropping it.

---

## 8. Recommended First Sprint

**Sprint 0, as specified in §5**, for three reasons: (a) every item in it is unblocked today — no Founder decision, no missing data, no missing infrastructure; (b) it closes the only two items in the entire program that are actively *regressing* trust in the repository's own certifications (the migration-drift reproducibility gap, and the wiring gap that makes WP-8D's coverage claims ambiguous); (c) its cost (a wiring fix, two migration files, and one sign-off ask) is the smallest of any sprint in this plan, making it the fastest possible proof that the program is moving from documents into working software.

---

## Critical Self-Review

This document adds exactly two new Founder decisions (FD-12, FD-13) after checking two other candidates (B5-RES-001, B5-RES-002) and confirming both are already resolved rather than reporting them as open. No Epic, root cause, or FD-01–FD-11 item from the Engineering Execution Baseline is restated with different content — where this document references them, it points to the Baseline rather than duplicating its text, per the task's explicit instruction not to repeat previous findings. The Founder Decision Audit (Phase 1) was a targeted grep-and-verify sweep of markers (`TBD`, `undecided`, `unspecified`, `arbitrary`) across `docs/` and `supabase/functions/_shared/services`, followed by direct schema/live verification of every candidate found — it was not an exhaustive re-read of every document in the repository, consistent with the instruction that this is not a fourth audit.

## Versioning & Placement
v1.0, filed under `docs/project-history/work-packages/` alongside its four predecessor documents. This is the Engineering Launch Plan — the next session should start implementation directly from §5/§8, consulting the Baseline only for Epic detail and this document only for the Founder-decision/readiness/sprint framing.

Founder sign-off: _______________________ Date: ___________
