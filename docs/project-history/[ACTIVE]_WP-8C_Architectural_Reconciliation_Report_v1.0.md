# [ACTIVE]_WP-8C_Architectural_Reconciliation_Report_v1.0

**Status:** ACTIVE — Reconciliation Report (read-only investigation; no code, no schema/DB/migration/seed/security change).
**Version:** v1.0
**Date:** 2026-07-14
**Placement:** docs/project-history/[ACTIVE]_WP-8C_Architectural_Reconciliation_Report_v1.0.md
**Supersedes:** none
**Consolidates:** the three requested reports — Phase 1 = Architecture Traceability, Phase 2 = Cross-Document Reconciliation, Phase 5 = Decision — into one evidence document, to preserve one-source-of-truth (three separate files would duplicate the same evidence base).
**Companion certificate:** REPO-CERT-012.
**Evidence basis (all read this session or cited by path/section):** CLAUDE.md, DOC-P3-03 v1.0 (§02–05, §14, §15, §16), DOC-P3-03A v1.0 (§01, §02, §03, §04, §07, §08 — full read), DOC-P3-04 v1.3 (§03.4 + table/migration map), DOC-P3-06 v1.2 (full), DOC-P4-00 v1.0 (full), WP-8B/REPO-CERT-008, REPO-CERT-007/009/010/011, Engineering Handover v1.3, Baseline Register v1.5 (indexed), and direct inspection of database/{migrations,seeds,rollback,validation,etl} and supabase/functions/.

> **Method note.** Everything below is evidence-backed to a repository file + section/line. Nothing is inferred, and no business logic, algorithm, mapping, or API behaviour is invented. Where documents leave something unstated, this report says "silent / underspecified" rather than filling it.

---

## Executive Summary

The onboarding and recommendation-engine **data and schema are fully in place and independently validated** (905 FULL PASS, REPO-CERT-007/010). The **runtime code does not exist** (backend is WP-8B scaffold only; WP-8C auth/consent lives on an unmerged branch). The frozen specification set (DOC-P3-03/03A/04/06 + DOC-P4-00) is individually consistent, but the **service/edge-function-level runtime sequencing that binds onboarding to first-plan generation is unspecified** — and the document the repository itself designates to own that layer, **DOC-P4-02 (Service/Edge Function Specifications), does not exist.**

No frozen document is internally wrong in a way that requires reopening (no Option-C contradiction was found). The blocker is a genuine **specification gap at the DOC-P4-02 layer.** → **DECISION: OPTION B — author DOC-P4-02 before implementing onboarding** (Phase 5).

---

## PHASE 1 — Architecture Traceability

Each transition of the requested flow, mapped to evidence. **Impl status legend:** ✅ built+validated · ◻ schema/data only (no runtime code) · ⛔ not built · ⚠ specification gap.

| # | Transition | Governing doc · section | Business rule | API (DOC-P3-06) | Table(s) (DOC-P3-04) | Migration / Seed | Validation | Impl status |
|---|---|---|---|---|---|---|---|---|
| 1 | User Registration | DOC-P3-06 §19.1 ("Signed Up") | Supabase Auth signup (platform, out of contract) | — (Surface A / infra) | `auth.users` (platform) | platform | — | ◻ platform-provided |
| 2 | Authentication | DOC-P3-06 §04, §05.1; DOC-P4-00 §7 | JWT verify; gateway `verify_jwt=true` | all Surface B except `/v1/health` | — | — | — | ✅ built (WP-8C branch: `authenticate`, REPO-CERT-011) |
| 3 | Consent | DOC-P3-03 §15 LF-M01; DOC-P3-06 §06.1; DOC-09 §03 | Personalization must precede onboarding | `POST /v1/consent` | `consent_records` | mig `006` (no seed — runtime) | 903 (RLS) | ✅ built (WP-8C branch, REPO-CERT-011) |
| 4 | Onboarding | DOC-P3-03 §03 LF-A01–A08; DOC-P3-06 §06.2 | 8 screens → answers; confidence math (§03) | `POST /v1/onboarding` | `profiles`, `household_members`, `onboarding_sessions` | mig `005`,`006` (runtime) | 904 (LF-A08 cited) | ⛔ not built |
| 5 | Profile Completion | DOC-P3-03 §03 LF-A03/A04/A05/A06 | home_state, diet_type, allergen bitfield, cook_capability, city overlay weight | (within `/v1/onboarding`) | `profiles` | mig `005` | 903 | ⛔ not built |
| 6 | Persona Resolution | DOC-P3-03 §03 LF-A09; §02 R/W matrix | DB lookup `(main_cohort, sub_cohort, home_state, diet)` → persona; Option-B fallback | (within `/v1/onboarding`) | `re_persona_assignment_rules` → `re_engine.user_re_state` | mig `014` / seed `111` | 905 (personas=41) | ◻ data ✅ / code ⛔ |
| 7 | State Resolution | DOC-P3-03 §03 LF-A03 | home_state → `re_states` | (within `/v1/onboarding`) | `re_states` | mig `002` / seed `110` | 905 (states=36) | ◻ data ✅ / code ⛔ |
| 8 | Regional Affinity | DOC-P3-03A §02; RE-DOC (scoring) | dish×state affinity used in scoring | (RE pipeline, not onboarding) | `re_dish_regional_affinity` | mig `024` / seed `117` (ICD-1) | 905 (>0) | ◻ data ✅ / code ⛔ |
| 9 | Cohort Resolution | DOC-P3-03 §04 LF-B02; §03 fallback | `(persona × state × diet)` → `re_cohorts`; city_tier (SER-001) | (RE pipeline) | `re_cohorts` (2,952) | mig `004`,`030` / seed `113` | 905 (=2952, GAP-002) | ◻ data ✅ / code ⛔ |
| 10 | Recommendation Engine | DOC-P3-03 §02, §06–11 (9-stage pipeline) | candidate→hard constraints→score→MMR→safety gates | `POST /v1/recommendations` | `re_class_dish_options`, `dishes`, config | mig `004`+ / seed `117` (ICD-1) | 902 (safety, simulated) | ⛔ not built (WP-8D/8E) |
| 11 | Weekly Plan | DOC-P3-03 §04 LF-B02, §14 LF-L01 | 21 class assignments from `re_weekly_class_plans`; nonveg overlay | (CRON / plan endpoints) | `re_weekly_class_plans` (20,664) → `week_plans`,`plan_slots` | mig `004`,`011` / seed `114` | 905 (=20664); 904 smoke | ◻ data ✅ / code ⛔ |
| 12 | Addon Plans | DOC-P3-03 §05 LF-C01/C02 | member segment × class → addon; additive-only (Invariant 9) | (CRON / plan endpoints) | `re_household_addon_plans` (7,992), `re_addon_dish_options` → `addon_slots` | mig `004`,`011` / seed `115`,`117` | 905 (=7992) | ◻ data ✅ / code ⛔ |
| 13 | API Response | DOC-P3-06 §06.2 (onboarding), §06.4/06.5 (plan) | response envelope + `trace_id` (§22.1) | all Surface B | — | — | — | ⚠ onboarding response includes `first_week_plan` — see Phase 3 |

**Phase 1 conclusion:** transitions 6–12 are **data-complete and validated** but have **no runtime code**; transitions 4–5 (onboarding capture) and 10 (RE) are unbuilt; transition 13 carries the one specification gap (Phase 3).

---

## PHASE 2 — Cross-Document Reconciliation

Every issue found is classified with evidence. Categories: **Repository Bug · Documentation Gap · Implementation Gap · Intentional Deferral · Already Implemented · Not Required.**

| ID | Finding | Evidence | Classification |
|---|---|---|---|
| R-01 | Onboarding response includes `first_week_plan`, but onboarding's own LF coverage and table writes exclude plan generation | DOC-P3-06 §06.2 (response has `first_week_plan`) vs §12 (onboarding = LF-A01–A09 only) + §13 (writes exclude `week_plans`/`plan_slots`); DOC-P3-03A §02 R/W matrix (A01–A09 write `user_re_state`/`user_taste_vectors`, not plan tables); DOC-P3-03 §14 LF-L01 is the plan generator | **Documentation Gap** — the onboarding→plan handoff (mechanism + timing) is unspecified. Reconcilable (see Phase 3), not a contradiction. Owned by DOC-P4-02. |
| R-02 | Plan-generation trigger stated three ways across docs | DOC-P3-03 §14 LF-L01 "23:30 UTC CRON"; DOC-P3-03A §01 Layer-2 header "CRON (23:30 UTC daily) **OR first app open after gap**"; DOC-P3-06 §06.2 onboarding returns a `first_week_plan` handle | **Documentation Gap** — runtime trigger ownership unspecified; DOC-P4-02 territory. |
| R-03 | DOC-P4-02 (Service/Edge Function Specs) referenced as downstream owner but absent | DOC-P3-06 header "Downstream Documents … DOC-P4-02"; DOC-P4-00 §8 "umbrella beneath … DOC-P4-02"; grep: no `*P4-0[12]*` file, no `DOC-P4-02` string except in DOC-P4-00 | **Documentation Gap (the primary one)** |
| R-04 | DOC-P4-01 (Frontend Spec) absent | grep: no file | **Intentional Deferral** — DOC-P4-00 §322 sequences frontend after the API Gate; not needed for backend onboarding. |
| R-05 | `re_class_dish_options` (165) / `re_addon_dish_options` (6) far below original targets (1,050 / 142) | REPO-CERT-007/010; 900 Check 7; 905 ICD-1-aware | **Intentional Deferral** — Founder-approved Option C / ICD-1; remainder in Deferred Knowledge Register. |
| R-06 | `re_city_migration_overlays` (S-15) canonically 0 | REPO-CERT-010 §7 | **Intentional Deferral** — needs `migration_duration_band` source field. |
| R-07 | AGR-P3-07-001 (DPDP under-13 age gate) open, launch-blocking | DOC-P4-00 §295; Gap Register v1.1 | **Intentional Deferral** — Founder decision; does not block onboarding *build*, blocks launch. |
| R-08 | Table naming: docs/queries reference `re_sub_cohorts`; schema object is `re_subcohorts` | mig `003` (`re_subcohorts`), FK mig `014`, validated in 905 as `re_subcohorts`; ETL uses `sub_cohort_id` | **Documentation Gap (minor, verify)** — schema is internally consistent; low priority, non-blocking. |
| R-09 | Consent/auth already implemented; not on main | WP-8C work package + REPO-CERT-011; branch `feat/wp-8c-auth-onboarding-consent` commit `6906dd5` | **Already Implemented** (pending merge/Founder acceptance). |
| R-10 | Onboarding accepts events before completion (OB-08b) | DOC-P3-03 §14 LF-L04; DOC-P3-06 §19.1 | **Already Specified** (frozen); an implementation requirement, not a gap. |
| R-11 | Per-signal FinalScore + config-version audit absent at MVP | DOC-P3-03A §08 (known limitation); DOC-P3-06 §22.1 (`trace_id` not on log tables) | **Intentional Deferral** — documented Phase-1 enhancement (`re_recommendation_debug_log`). |

**No finding classified as Repository Bug or hard Contradiction.** Every disagreement is either an intentional, documented deferral or a specification gap at the DOC-P4-02 layer.

---

## PHASE 3 — WP-8C Onboarding Boundary Validation

**Question:** should onboarding (a) stop after profile/persona capture, (b) return the first generated weekly plan, or (c) create a cohort and defer planning?

**Where the documents point — evidence, not resolution:**

- **Toward "does NOT generate the plan" (b→no):**
  - DOC-P3-06 §12: `/v1/onboarding` maps to **LF-A01–A09 only** (no LF-B01/B02/L01).
  - DOC-P3-06 §13: `/v1/onboarding` writes `profiles`, `household_members`, `onboarding_sessions`, `user_re_state`, `user_taste_vectors` — **not** `week_plans`/`plan_slots`.
  - DOC-P3-03A §02 R/W matrix: A01–A09 write `user_re_state`/`user_taste_vectors`; **B02 and L01** are the functions that write `week_plans`/`plan_slots`, and they sit in a **separate layer**.
  - DOC-P3-03 §14: **LF-L01 `generateWeekPlan` is a 23:30 UTC nightly CRON**; DOC-P3-03A §07 classifies it "Scheduled CRON".
  - DOC-P4-00 §302/§310–322: build order puts onboarding (WP-8C, "persona/cohort resolution") **before** the RE core (WP-8D) and `/v1/recommendations` + nightly-plan (WP-8E).
- **Toward "DOES return a plan" (b→yes):**
  - DOC-P3-06 §06.2: onboarding **201 response includes `first_week_plan: { week_plan_id, week_start_date }`**.
  - DOC-P3-06 §14.1 sequence: onboarding returns `{persona_id, confidence, first_week_plan}` in one call.
  - DOC-P3-03 §03 header: onboarding "Output: … **first week plan**."
  - DOC-P3-03 §14 LF-L04: onboarding shows an **OB-08b plan preview** (before `onboarding_completed=true`) — which requires the RE pipeline to have produced candidates.
- **Toward "first app open after gap":**
  - DOC-P3-03A §01 Layer-2 header: plan trigger = "CRON (23:30 UTC daily) **OR first app open after gap**."

**Exactly where they disagree:** DOC-P3-06 §06.2/§14.1 present a first-plan artifact in the onboarding response, while DOC-P3-06 §12/§13, DOC-P3-03A §02, and DOC-P3-03 §14 place *actual plan generation* outside onboarding (a separate CRON / RE pipeline). The **mechanism and timing** by which a `first_week_plan` handle appears in onboarding's response — synchronous call to the shared RE service (DCR-P3-06-007), a trigger on onboarding completion, the OB-08b preview, the nightly CRON, or "first app open" — **is stated by no frozen document.**

**Per instruction, this report does not resolve the conflict.** It records that the boundary is genuinely underspecified at the service/edge-function layer, and that the response artifact is a *handle* (`week_plan_id` + `week_start_date`), which is reconcilable with generation happening elsewhere — hence a gap, not a contradiction. **Resolution is a Founder-ratified architectural decision, and DOC-P4-02 is its designated home.**

---

## PHASE 4 — Recommendation Engine Dependency Graph

```
consent (personalization=true) ──┐
auth (JWT verify)  ───────────────┤
                                  ▼
        onboarding capture (LF-A01–A08) → profiles, household_members, onboarding_sessions
                                  │
                                  ▼
        persona resolution (LF-A09) ── re_persona_assignment_rules ──▶ user_re_state (persona_id, overlays)
                                  │                                     user_taste_vectors (OB-07 affinity)
                                  ▼
        cohort resolution (LF-B01/B02) ── re_cohorts (persona×state×diet, city_tier)
                                  │
                                  ├── class plan ── re_weekly_class_plans (21 slots)
                                  ├── nonveg overlay ── re_nonveg_logic
                                  ├── addons ── re_household_addon_plans / re_addon_dish_options
                                  ▼
        candidate + score + MMR + safety (LF-D/E/F/H) ── re_class_dish_options, dishes,
                                  │                        dish_ingredients, dish_tags, genome_vector,
                                  │                        re_dish_regional_affinity, config tables
                                  ▼
        weekly plan write (LF-L01) ──▶ week_plans, plan_slots, addon_slots, suggestion_logs
```

**Prerequisite existence check (evidence: agents + 905 + REPO-CERT-007/010):**

| Prerequisite | Exists as data/schema? | Exists as runtime code? |
|---|---|---|
| persona / persona_assignment_rules | ✅ mig 003/014, seed 111 (41) | ⛔ |
| cohort (re_cohorts, city_tier) | ✅ mig 004/030, seed 113 (2,952) | ⛔ |
| regional affinity | ✅ mig 024, seed 117 (ICD-1) | ⛔ |
| class_dish_options | ✅ mig 004, seed 117 (165, ICD-1) | ⛔ |
| addon_dish_options | ✅ mig 004, seed 117 (6, ICD-1) | ⛔ |
| weekly_class_plans | ✅ mig 004, seed 114 (20,664) | ⛔ |
| nonveg logic | ✅ mig (tier2), seed 116 (36) | ⛔ |
| genome vectors / dish_tags / derived columns | ✅ triggers proven (REPO-CERT-007/010; 901) | ⛔ (trigger-owned, not backend) |
| meal classes | ✅ seed 112 (131) | ⛔ |
| consent | ✅ schema mig 006; ✅ **code** (WP-8C branch) | ✅ (branch) |
| auth | n/a (platform) | ✅ **code** (WP-8C branch) |
| RLS | ✅ enabled all tables (900/903) | n/a |

**Phase 4 conclusion:** **every RE data/schema prerequisite exists and is validated.** The single missing category is **runtime code** (the RE pipeline itself = WP-8D/8E, and onboarding capture = WP-8C). ICD-1 coverage (R-05) and S-15 (R-06) are documented deferrals that bound candidate coverage but do not block building the runtime. No prerequisite is *undocumented* or *missing by mistake*.

---

## PHASE 5 — Decision

### OPTION B — Current documents are insufficient. Author DOC-P4-02 first.

**Justification (evidence):**

1. **The specification gap is real and specific** (R-01, R-02, R-03; Phase 3): no frozen document specifies the onboarding→first-plan runtime sequencing — the exact question that must be answered before onboarding can be implemented to its frozen contract (`first_week_plan` in DOC-P3-06 §06.2).
2. **The repository itself designates DOC-P4-02 as the owner of this layer** (DOC-P3-06 "Downstream … DOC-P4-02"; DOC-P4-00 §8), and **DOC-P4-02 does not exist** (R-03). This is a missing artifact the architecture already anticipated — not a defect in a frozen document.
3. **It is NOT Option C:** no frozen document is internally self-contradictory in a way requiring reopening. R-01/R-02 are reconcilable (a returned *handle* vs generation-elsewhere); every other disagreement is an intentional, documented deferral (R-04–R-07, R-11). No AGR against a frozen doc is warranted by this investigation.
4. **It is NOT Option A:** implementing onboarding now would force an *invented* resolution of the plan-timing boundary (silently choosing whether onboarding generates, triggers, or defers the plan), violating "never invent business logic / never fabricate API behaviour."

**Consequence:** author DOC-P4-02 (done as a DRAFT this session, pending Founder sign-off), surfacing the onboarding-plan boundary as a governed decision rather than resolving it unilaterally. **Do not implement onboarding until DOC-P4-02 is Founder-approved.**

---

## Critical Self-Review

- **Evidence-only?** Yes — every row cites a file+section; `.docx` sources (DOC-04/05/06/10, RE-DOC-01–05) were cited by filename only (binary), flagged, never quoted-as-if-read.
- **Did I resolve the Phase-3 conflict?** No — identified exactly where docs diverge; resolution deferred to DOC-P4-02 + Founder.
- **Did I invent anything?** No mappings, algorithms, or API behaviours invented.
- **Could this be Option A or C?** Argued against both with evidence (Phase 5 §3–4).
- **Limits:** validation "PASS" is per REPO-CERT-007/010 (not re-executed this session); `.docx` internals not re-read; WP-8C code assessed on its branch, not main.

## Versioning & Placement

v1.0, docs/project-history/ (report peer to the migration/validation recovery reports). Naming per WP-5AA. Companion: REPO-CERT-012; output spec: DOC-P4-02 (DRAFT).

## Founder Sign-off

Founder acknowledgement of the reconciliation findings and the Option-B decision: _______________________ Date: ___________
