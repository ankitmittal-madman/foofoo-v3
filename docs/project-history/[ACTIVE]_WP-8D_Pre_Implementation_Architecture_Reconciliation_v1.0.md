# [ACTIVE]_WP-8D_Pre_Implementation_Architecture_Reconciliation_v1.0

**Status:** ACTIVE — Pre-Implementation Reconciliation (read-only; no code, no schema/DB/migration/seed/security change). WP-8D implementation is **HELD** pending the decisions in §6.
**Version:** v1.0
**Date:** 2026-07-15
**Placement:** docs/project-history/[ACTIVE]_WP-8D_Pre_Implementation_Architecture_Reconciliation_v1.0.md
**Supersedes:** none. **Builds on:** [ACTIVE]_WP-8C_Architectural_Reconciliation_Report_v1.0 and REPO-CERT-012 (AD-01), [DRAFT]_DOC-P4-02.
**Companion certificate:** REPO-CERT-013.
**Evidence basis (read this session from source, not chat):** DOC-P3-03 §02–16 (full RE pipeline: §03 onboarding, §04 class plan, §05 addon, §06 candidate+hard constraints, §07 scoring, §08 MMR/variety, §09 suppression, §10 safety gates, §11 context, §14 plan mgmt, §16 config); DOC-P3-03A (execution/R-W matrix, prior session); DOC-P3-04 (schema/tables); DOC-P3-06 v1.2 (contract); DOC-P4-00 (backend arch); DOC-P4-02 DRAFT; database/{migrations,seeds,validation} inspection; REPO-CERT-007/010/011/012.

> **Governance honored:** one-source-of-truth; no invention; no assumption; repository overrides conversation; ACTIVE documents authoritative; frozen documents not modified. The prompt's assertion that onboarding returns the first week plan was treated as a claim to verify — not a fact.

---

## Executive Summary

The **Recommendation Engine algorithm is fully and self-containedly specified** in DOC-P3-03 §06–11 (inline formulas, thresholds, config-table references, and safety-gate SQL) — it is implementable **without** reading the binary RE-DOC `.docx` files and **without invention**. The **RE-ownership architecture is unambiguous**: a single reusable engine, invoked by `/v1/recommendations` (live) and the nightly CRON, sharing one implementation (DOC-P4-00 §5/§14; DCR-P3-06-007). **On both counts, WP-8D is ready to build.**

However, **two evidence-backed blockers prevent starting WP-8D implementation this session**, and both trigger the prompt's own STOP conditions:

1. **AD-01 (weekly-plan persistence/ownership) is unresolved and unratified.** Whether `POST /v1/onboarding` synchronously generates + persists + returns the first week plan is an open decision (REPO-CERT-012; DOC-P4-02 DRAFT). ACTIVE documents disagree, and resolving it toward "onboarding returns the plan" additionally requires a **governed DCR against frozen DOC-P3-06 §12/§13** (§3). This is a Founder decision, not one I may make unilaterally.
2. **A core scoring-input table is unseeded:** `re_cohort_class_priors` (the CohortPrior signal, weight 0.55 at cold start) has **no seed** (§5). `re_segment_addon_rule` is likewise unseeded. WP-8D's ranking can be *built* (fallbacks are specified) but cannot be *meaningfully validated* for cold-start behaviour until this is dispositioned.

**DECISION: STOP before writing WP-8D code.** Produce this reconciliation. Implement WP-8D immediately after §6's two decisions are made.

---

## 1. Complete Runtime Flow — responsible service / API / tables / rules / module / validation

Legend: **data ✅** = seed/schema present & validated; **code ⛔** = runtime not built.

| # | Transition | Responsible service | API | DB tables | Business rule | Runtime module (target WP) | Validation |
|---|---|---|---|---|---|---|---|
| 1 | Registration | Supabase Auth (platform) | — | `auth.users` | platform signup | platform | — |
| 2 | Consent | ConsentService | `POST /v1/consent` | `consent_records` | LF-M01 (§15); personalization gates onboarding | WP-8C (built) | 903 RLS |
| 3 | Onboarding capture | OnboardingService | `POST /v1/onboarding` | `profiles`,`household_members`,`onboarding_sessions` | LF-A01–A08 (§03) | WP-8C onboarding (⛔) | 904 (LF-A08) |
| 4 | Profile persistence | OnboardingService | (same) | `profiles` | LF-A03/04/05/06 (§03) | WP-8C onboarding (⛔) | 903 |
| 5 | Persona Resolution | **RE / OnboardingService** | (same) | `re_persona_assignment_rules`→`user_re_state` | LF-A09 DB lookup + Option-B fallback (§03) | **WP-8D (⛔)**; data ✅ | 905 (personas=41) |
| 6 | Cohort Resolution | **RE** | (RE call) | `re_cohorts` (persona×state×diet, city_tier) | LF-B02 (§04); SER-001 | **WP-8D (⛔)**; data ✅ (2,952) | 905 |
| 7 | Recommendation Engine (orchestration) | **RE core** | `POST /v1/recommendations` / CRON | (reads RE + content + config) | §02 9-stage pipeline | **WP-8D (⛔)** | 902 (simulated) |
| 8 | Meal Class Resolution | **RE** | (RE) | `re_weekly_class_plans`,`re_meal_classes`,`re_nonveg_logic` | LF-B02 + nonveg overlay (§04) | **WP-8D (⛔)**; data ✅ (20,664/131/36) | 905 |
| 9 | Candidate Dish Selection | **RE** | (RE) | `re_class_dish_options`,`dishes` | LF-D01 (§06) | **WP-8D (⛔)**; data ✅ (ICD-1: 165) | 905 |
| 10 | ICD Filtering (6 hard constraints) | **RE** | (RE) | `dish_ingredients`,`ingredients`,`re_engine.never_list` | LF-D02–D06 (§06); diet/allergen/religious/occasion/never | **WP-8D (⛔)** | 902 |
| 11 | Safety Gates | **RE** | (RE, pre-serve) | `suggestion_logs`,`plan_slots`,`dishes`,`profiles` | LF-H01–H04 (§10); 0 rows or P0 | **WP-8D (⛔)** | 902 |
| 12 | Regional Affinity | **RE** (scoring input) | (RE) | `re_dish_regional_affinity` | scoring signal (§07) | **WP-8D (⛔)**; data ✅ (ICD-1) | 905 |
| 13 | Ranking | **RE** | (RE) | `re_cohort_class_priors`(⚠ unseeded), `re_context_multipliers`, `user_taste_vectors`, config | LF-E01–E08 FinalScore + weight ladder; LF-F01 MMR; LF-F02 variety (§07/§08) | **WP-8D (⛔)** | 904 (weights) |
| 14 | Weekly Plan Generation | **RE (LF-L01)** | CRON / **AD-01** | `week_plans`,`plan_slots`,`addon_slots`,`suggestion_logs` | LF-L01 (§14) = fetchPersona→classPlan→addons→D–F→H→write | **WP-8E** (⛔); **AD-01 for onboarding** | 904 smoke |
| 15 | Addon Plans | **RE** | (within plan gen) | `re_household_addon_plans`,`re_addon_dish_options`,`re_segment_addon_rule`(⚠ unseeded) | LF-C01/C02 (§05); additive-only (Inv 9) | **WP-8D/8E (⛔)**; data partial | 905 (addon=7,992) |
| 16 | Persistence | **RE / caller** | CRON / **AD-01** | `week_plans`,`plan_slots` | LF-L01 step 7 (§14) | **WP-8E**; **AD-01** for onboarding | 904 |
| 17 | API Response | endpoint handler | `/v1/onboarding` or `/v1/plan` | — | DOC-P3-06 §06.2/§06.5 + trace_id (§22.1) | WP-8C/8E; **AD-01** shapes §06.2 | — |
| 18 | Future Nightly Regeneration | **RE (LF-L01)** | `_cron/nightly-plan` 23:30 UTC | `week_plans`,`plan_slots` | LF-L01 (§14); shared core (DCR-P3-06-007) | **WP-8E (⛔)** | 904 |

**Reading:** the **RE core (WP-8D)** owns transitions 5–13, 15 (resolution + scoring + safety). **Plan generation/persistence (transitions 14, 16, 18)** is LF-L01, a **nightly CRON owned by WP-8E** — and whether onboarding is *also* a synchronous caller of that path is **AD-01**.

---

## 2. Specific Question — "Does POST /v1/onboarding return the user's FIRST WEEK PLAN?"

**Answer from repository evidence: NOT CONFIRMED. The ACTIVE documents disagree. This is the open, unratified AD-01.**

**Evidence FOR (supports the prompt's flow):**
- DOC-P3-03 §03 header: onboarding "**Output:** persona_id, overlay_persona_ids[], confidence_score, **first week plan**."
- DOC-P3-06 §06.2: onboarding 201 response includes `first_week_plan: { week_plan_id, week_start_date }`; §14.1 sequence shows it returned in the call.
- CDM (per prompt): "initial recommendations generated from onboarding interactions."

**Evidence AGAINST (onboarding does NOT itself generate/persist the plan):**
- DOC-P3-06 §12: `/v1/onboarding` traces to **LF-A01–A09 only** — not LF-B01/B02/L01 (the plan generators).
- DOC-P3-06 §13: `/v1/onboarding` **writes** `profiles`,`household_members`,`onboarding_sessions`,`user_re_state`,`user_taste_vectors` — **NOT** `week_plans`/`plan_slots`.
- DOC-P3-03A §02 (R/W matrix): A01–A09 write `user_re_state`/`user_taste_vectors`; **LF-B02 and LF-L01** write `week_plans`/`plan_slots`, in a separate layer.
- DOC-P3-03 §14: **LF-L01 `generateWeekPlan` is a 23:30 UTC nightly CRON**; DOC-P3-03A §07 "Scheduled CRON"; §01 Layer-2 header: trigger = "CRON … **OR first app open after gap**."
- DOC-P4-00 §302/§310–322: onboarding (WP-8C) is built **before** the RE core (WP-8D) and `/v1/recommendations`+nightly-plan (WP-8E).

**Per the prompt's instruction ("If ANY ACTIVE document contradicts this flow: STOP"), this is a STOP.** The `first_week_plan` object is a *handle* (`week_plan_id`+`week_start_date`), reconcilable with generation happening in LF-L01/WP-8E and being *referenced* by onboarding — but no frozen document states the mechanism or timing. **This report does not resolve the conflict** (consistent with REPO-CERT-012 Option-B and DOC-P4-02 AD-01, both on main).

---

## 3. Governance consequence of choosing "onboarding returns the plan"

If AD-01 is ratified as **Option 2** (onboarding synchronously invokes RE → persists → returns Week 1), then onboarding **writes `week_plans`/`plan_slots`**, which **contradicts frozen DOC-P3-06 §12/§13** (APPROVED-ACTIVE-FROZEN). Per DOC-P3-06 §16.2, any contract change requires **AGR/SER/DCR discipline**. Therefore Option 2 requires a **Founder-authorized DCR against frozen DOC-P3-06 §12/§13**. **Option 1** (onboarding resolves persona/cohort/state and returns a `plan_pending` handle; first plan produced by LF-L01/WP-8E) is the **only option consistent with the frozen contract without reopening it** (the recommendation already recorded in DOC-P4-02 AD-01).

---

## 4. Recommendation-Engine Ownership — RESOLVED from evidence

- **Single reusable engine, multiple callers** — confirmed: DOC-P4-00 §5 ("the recommendation service is the shared core invoked by both `POST /v1/recommendations` and `_cron/nightly-plan` — a single implementation, per DCR-P3-06-007"); §14 ("Same core, two callers"). DCR-P3-06-007 (Resolved): scheduled generation and the live endpoint share a common internal service; the CRON never calls the public HTTP endpoint.
- **RE owns all recommendation decisions** — RE-DOC-01 isolation (DOC-P4-00 §3): candidate→score→MMR→safety is RE-internal; callers never duplicate it.
- **Third caller (onboarding)?** = AD-01. If ratified, onboarding must be a **thin orchestrator** invoking the same shared engine (never duplicating logic) — exactly the prompt's stated principle, enforced by the WP-8D module boundary.

**Conclusion:** all callers (live endpoint, nightly CRON, and — if AD-01 permits — onboarding) reuse the **same** WP-8D engine. WP-8D must be built **caller-agnostic**.

---

## 5. RE build-readiness & data-coverage findings

**Algorithm: READY (no invention required).** DOC-P3-03 §06–11 specify inline: 6 hard constraints (§06), 5-signal FinalScore + weight-ladder interpolation + cosine ContentMatch + PersonalHistory decay (λ=0.05) + ContextFit + Thompson-sampling ExplorationBonus + Not-Today penalty (§07), MMR (λ=0.70) + 5 variety rules (§08), Never/Not-Today suppression (§09), 4 safety-gate SQL queries (§10), context assembly (§11). Config values are in §16 and seeded (100).

**Data-coverage gaps (new findings, evidence-backed):**
| Table | Used by | Seeded? | Impact |
|---|---|---|---|
| `re_cohort_class_priors` | LF-E02 CohortPrior (w=0.55 cold start) | **NO** (created mig 014; no seed) | Cold-start ranking's dominant signal falls back to neutral 0.50 for all dishes → collapses CohortPrior. **Must be dispositioned before WP-8D cold-start validation.** |
| `re_segment_addon_rule` | LF-C01 addon generation (§05) | **NO** | Addon class resolution has no rules; note `re_household_addon_plans` (seed 115) is a different mechanism — a source ambiguity to confirm. |
| `re_context_multipliers` | LF-E05 ContextFit | **YES** (seed 100) | OK |
| `re_dish_bandit_state` | LF-E06 exploration | NO (runtime table — expected) | OK — initialized at runtime (Beta(1,1)) |
| `re_festival_calendar` | LF-G05 reactivation, LF-F03 | (Phase-2 deferred) | OK — festival is Phase-2 scope |

Classification: `re_cohort_class_priors` gap = **Implementation/Data Gap** (blocks meaningful cold-start validation); `re_segment_addon_rule` = **Documentation/Data ambiguity** (verify intended addon mechanism). Neither is invented behaviour; both are surfaced for Founder/data disposition.

---

## 6. Decision & Required Actions (STOP)

**DECISION: STOP — do not write WP-8D code this session.** Triggered STOP conditions (all evidence-backed): *"weekly plan persistence ownership is unclear"* (AD-01), *"any ACTIVE document contradicts another ACTIVE document"* (§06.2 vs §12/§13), and *"proceed only after architecture is proven."*

**To unblock WP-8D, two decisions are required:**
1. **Founder ratifies AD-01** (DOC-P4-02): **Option 1** (recommended — onboarding returns a `plan_pending` handle; LF-L01/WP-8E generates the plan; no frozen-contract change) **or Option 2** (onboarding returns the plan synchronously — requires an authorized **DCR against frozen DOC-P3-06 §12/§13** and sequences WP-8D before onboarding).
2. **Disposition the `re_cohort_class_priors` seed gap** (and confirm the addon mechanism): seed it (a WP-6-class seed task), or Founder-accept the ICD-1 neutral-prior fallback for cold start with a documented limitation.

**After both:** WP-8D implements the caller-agnostic RE core (Persona/Cohort/MealClass/Candidate/RegionalAffinity resolvers, ICD/Eligibility rule engine, Ranking engine incl. weight-ladder/MMR/variety/suppression, Safety gates, DTOs, services, unit + fake-integration tests, docs, certificate) — **no onboarding wiring** (that stays WP-8C/8E per AD-01).

---

## Critical Self-Review

- **Did I invent RE behaviour?** No — every algorithm cited to DOC-P3-03 §06–11 with inline formulas; nothing fabricated.
- **Did I resolve AD-01?** No — surfaced it, recommended Option 1 with rationale, left ratification to the Founder; noted Option 2's frozen-contract DCR requirement.
- **Is the RE algorithm actually implementable?** Yes — §06–11 are self-contained; binary RE-DOC files were not required.
- **New vs REPO-CERT-012?** Adds the full 18-transition runtime map, the RE-algorithm-readiness confirmation, and the `re_cohort_class_priors`/`re_segment_addon_rule` seed-gap findings.
- **Limits:** validation "PASS" per REPO-CERT-007/010 (not re-run); `.docx` RE-DOC sources cited via their DOC-P3-03 formalization, not re-read (binary).

## Versioning & Placement

v1.0, docs/project-history/ (peer to the WP-8C reconciliation report). Naming per WP-5AA. Companion: REPO-CERT-013.

## Founder Sign-off

Founder direction on AD-01 (Option 1 / Option 2+DCR) and on the `re_cohort_class_priors` disposition: _______________________ Date: ___________
