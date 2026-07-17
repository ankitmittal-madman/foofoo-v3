# [ACTIVE]_WP-8D_Recommendation_Engine_Core_v1.0

**Status:** ACTIVE — reusable Recommendation Engine core BUILT & VALIDATED (certified REPO-CERT-014). Onboarding wiring and live-DB adapters are explicitly out of scope (see §5).
**Version:** v1.0
**Date:** 2026-07-15
**Placement:** docs/project-history/work-packages/[ACTIVE]_WP-8D_Recommendation_Engine_Core_v1.0.md
**Supersedes:** none. **Builds on:** WP-8B scaffold (REPO-CERT-008), WP-8C auth/consent (REPO-CERT-011), the WP-8D Pre-Implementation Reconciliation (REPO-CERT-013).
**Governance basis (frozen, consumed not modified):** DOC-P3-02 (CDM), DOC-P3-03 v1.0 §02–16 (LF-A09/B01-B03/C01-C02/D01-D07/E01-E08/F01-F03/H01-H04/I01), DOC-P3-03A, DOC-P3-04 v1.3, DOC-P3-06 v1.2, DOC-P4-00 v1.0 (§2/§3/§5/§14/§20), DOC-P4-02 (DRAFT), RE-DOC-01 (isolation), REPO-CERT-007/010.

---

## Executive Summary

WP-8D delivers the **reusable Recommendation Engine core** — the single, caller-agnostic engine that owns every recommendation decision (candidate selection → hard constraints → scoring → diversity → safety) and assembles a week plan in memory. It is pure domain logic behind injected repository/config **ports** (DDD / hexagonal; DOC-P4-00 §4/§20), so it is DB-agnostic and unit-testable, and is invoked identically by all three callers per the frozen design: `/v1/recommendations`, the nightly plan job, and — per the AD-01 reconciliation below — the onboarding orchestrator.

**No frozen document, schema, migration, seed, validation SQL, or security artifact was modified. No live DB connection is made. No recommendation logic is duplicated anywhere else.** Verified: `deno fmt --check`, `deno lint`, `deno check`, `deno test` all pass — **52 tests, 0 failures** (8 foundation + 16 consent + 28 RE core).

---

## 1. AD-01 Architectural Reconciliation — RESOLVED (no DCR)

**Question (CPTO):** does the three-responsibility separation — (1) Recommendation Engine, (2) Plan Assembly, (3) Persistence — with onboarding as an *orchestrator* that invokes the reusable RE, reconcile the apparent onboarding↔first-plan contradiction **without a DCR**?

**Answer: YES.** Decisive evidence is **DOC-P3-02 (Conceptual Domain Model)**, which I had previously only indexed:
- **Entity 28 (Completion):** "Onboarding is considered complete when the user taps 'Looks good'… At this point: assign_persona() has run, **first plan is generated**, onboarding_completed = true."
- **Domain Events table:** `PlanPreviewGenerated` — "First plan generated at OB-08b" — **Actor = RE Engine** — Effect = **Week Plan, Plan Slots**. `PersonaAssigned` — Actor = RE Engine.
- **Entity 11:** the persona is "the bridge between onboarding … and the recommendation engine."

The CDM explicitly assigns first-plan generation to the **RE Engine** as a distinct actor, invoked during onboarding. Therefore:
- **Onboarding logic (LF-A01–A09)** writes only its own tables (`profiles`, `household_members`, `onboarding_sessions`, `user_re_state`, `user_taste_vectors`) — exactly DOC-P3-06 §13.
- **The RE Engine** (a separate module/actor) generates the plan and writes `week_plans`/`plan_slots` — which is why §13 lists those under the RE path, not onboarding.
- Onboarding **orchestrates** the RE Engine; it does not implement recommendation logic. `first_week_plan` in DOC-P3-06 §06.2 is the handle to the plan the RE Engine produced.

**Which prior interpretation was too literal:** REPO-CERT-012/013 read DOC-P3-06 §12/§13 as onboarding's *complete transitive footprint* (concluding "onboarding writes no plan tables ⇒ cannot return a generated plan ⇒ contradiction"). §12/§13 describe each endpoint's **own** direct logic/writes; the CDM Domain Events table (actor = RE Engine) is the authoritative statement that resolves the boundary. Reading DOC-P3-02 in full — not inferring from §12/§13 — supplied the missing evidence.

**Why no DCR:** no documented table, write, rule, or algorithm changes. DOC-P3-02 already specifies first-plan-at-onboarding with the RE Engine as actor; DOC-P3-03A §01 already documents plan generation as multi-trigger ("CRON **OR first app open after gap**"); DOC-P4-00 §5/§14 already establishes the shared reusable core. The orchestration model is the reading that makes the *most* ACTIVE clauses simultaneously true.

**Governance note:** DOC-P4-02 remains **[DRAFT]**. The Founder gave architectural *direction* in-session; the formal AD-01 sign-off line is unsigned. DOC-P4-02 should be promoted to ACTIVE by Founder countersignature — this WP does not fabricate that ratification. WP-8D does **not** depend on it: the reusable engine is identical under every AD-01 option, so building it now is safe.

## 2. What WP-8D Implements (LF coverage)

All under `supabase/functions/_shared/services/re/` (DOC-P4-00 §2), pure logic behind ports:

| Module | LF coverage | Notes |
|---|---|---|
| `constraints.ts` | LF-D02–D06 (6 hard constraints) + LF-A05 allergen union | ingredient-level allergen (GR-06); pure filters |
| `scoring.ts` | LF-E01 weight-ladder interpolation, E02 CohortPrior (+neutral fallback), E03 cosine ContentMatch, E04 PersonalHistory decay, E05 ContextFit, E06 Thompson-sampling ExplorationBonus (+α/β update), E07 Not-Today penalty, E08 FinalScore | numeric params via config port (§16), never hardcoded |
| `variety.ts` | LF-F01 MMR, LF-F02 variety-window rules (fried cap + monsoon override, same-dish, same-ingredient) | |
| `safety.ts` | LF-H01–H04 (diet/allergen/jain/planning-role) | pure predicates over the proposed slate (defense in depth before serve) |
| `resolvers.ts` | LF-A09 persona (+Option-B fallback), LF-B02 cohort + weekly class plan, LF-B03 non-veg overlay | thin, over the resolution port |
| `engine.ts` | §02 pipeline orchestration: `generateSlate` (D→E→F→H) and `generateWeekPlan` (B→C→per-slot) | RE Engine; returns an in-memory plan (persistence is the caller's) |
| `types.ts`, `ports.ts`, `index.ts` | DTOs, repository/config ports, barrel | |

**Tests:** `functions/_tests/re_core.test.ts` — 28 tests: hard constraints, weight-ladder invariants, cohort-prior fallback, cosine, personal-history decay, not-today penalty, final score, MMR diversity, variety windows, safety gates, planning-role gate, persona Option-B fallback, and 4 engine integration tests (safe slate, unseeded-prior path, LF-D07 fallback, week-plan assembly) — all with in-memory fakes.

## 3. Cohort-prior neutral fallback (MVP limitation, documented)

Per CPTO direction: WP-8D is **not** blocked by the unseeded `re_cohort_class_priors` table. LF-E02 specifies a neutral fallback (0.50), which the engine applies via `ScoringConfig.neutralCohortPrior` when the prior lookup returns null. **MVP limitation:** until `re_cohort_class_priors` is seeded, cold-start CohortPrior is uniform 0.50 for all dishes, so cold-start ranking is driven by the other signals (content/context/exploration). This is documented, not silent; seeding the table (a WP-6-class task) restores the research prior with no engine change.

## 4. Deviations / classifications (surfaced, not invented)

- **DCR-8D-01 — §07 weight-ladder worked example is internally inconsistent.** The example (DOC-P3-03 §07 line 539) computes `w_cohort = 0.20 + 0.487×(0.20−0.20)` (references the current tier) while `w_history = 0.15 + 0.487×(0.35−0.15)` (references the previous tier). These use different reference points and cannot both follow one rule. WP-8D implements the **continuous forward-transition** reading of the stated formula (each tier's weights interpolate toward the next tier's across the tier span), which preserves partition-of-unity (all tiers sum to 1.0) and C0 continuity. Tests assert those invariants, not the contradictory example. **Flagged for Founder confirmation; no behaviour invented.**
- **Reason tags (DOC-P3-06 §06.4)** are derived from the dominant scoring signals (an implementation convention summarising which signal drove a pick) — a faithful summary, not new business logic.
- **ExplorationBonus** uses a Marsaglia–Tsang Beta/Gamma sampler with an **injected** RNG (deterministic in tests), realising LF-E06 Thompson sampling; Beta(1,1) = Uniform at cold start.

## 5. Scope boundary (what WP-8D deliberately does NOT do)

- **No onboarding wiring / no `/v1/*` handlers / no CRON** — the engine is the reusable core only; callers are later WPs. Onboarding will be a thin orchestrator (per §1), never duplicating engine logic.
- **No concrete DB adapters / no live connection** — only port interfaces; Supabase-backed adapters + live behavioural validation (extending `902`/`905`) are a later WP.
- **No schema/seed/migration/frozen-doc change.**

## 6. Verification & Governance

`cd supabase && deno task verify` → fmt:check PASS · lint PASS · `deno check functions/_shared/services/re/index.ts` PASS · `deno test` **52 passed / 0 failed**. Branch `feat/wp-8d-re-core-reconciliation`; not pushed as of this Work Package's own execution (committed locally after tests passed, per instruction). No frozen artifact touched at that time; DOC-P4-02 remained DRAFT.

**[FD-01 update, 2026-07-16]** This branch's later push to `main` (`e113ffa`/`e76bd9c`) is retroactively ratified as authorized — see `[ACTIVE]_Founder_Decision_Register_v1.0.md` FD-01 and `[ACTIVE]_Founder_Ratification_Certificate_2026-07-16_v1.0.md`. This Work Package's own text above is left unchanged as the historical record at time of execution, per `CLAUDE.md`'s never-delete-history rule.

## Critical Self-Review

- **Recommendation logic duplicated anywhere?** No — it lives only in `services/re/`; callers will orchestrate, not reimplement.
- **Anything invented?** No — every function cites an LF; the one genuine ambiguity (§07 example) is flagged as DCR-8D-01 with a disclosed, invariant-preserving reading; the priors fallback is the documented LF-E02 behaviour.
- **Is it reusable/caller-agnostic?** Yes — pure logic + injected ports; the engine reads no HTTP and no DB.
- **Did I fabricate Founder ratification of AD-01?** No — DOC-P4-02 stays DRAFT; the reconciliation is evidence-backed (DOC-P3-02) and recorded as Founder-directed, pending countersignature.
- **Limits:** cold-start CohortPrior is neutral until the priors table is seeded; live-DB behavioural validation is deferred; `.docx` RE-DOC sources consumed via their DOC-P3-03 formalization.

## Versioning & Placement

v1.0, docs/project-history/work-packages/ per the Placement Rule; naming per WP-5AA. Companion certificate: REPO-CERT-014.

## Founder Sign-off

Founder acceptance of WP-8D (RE core) + confirmation of DCR-8D-01 (weight-ladder interpolation) + `re_cohort_class_priors` disposition + AD-01 countersignature to promote DOC-P4-02 to ACTIVE: _______________________ Date: ___________
