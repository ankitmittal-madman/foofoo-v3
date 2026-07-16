# WP-9 — Independent Engineering Due Diligence Audit

**Status:** ACTIVE — Independent audit, READ-ONLY, completed. No code, schema, migration, seed, or documentation content was modified during this audit. This document is itself the deliverable.
**Version:** v1.0
**Date:** 2026-07-16
**Placement:** docs/project-history/work-packages/ (per Placement Rule — this is engineering-history record of a review activity, analogous to WP-6RE and WP-8FA, both of which are audits filed as Work Packages)
**Supersedes:** None
**Dependencies:** All documents and code cited inline; companion certificate REPO-CERT-020
**Audit base:** branch `feat/wp-8f-runtime-blocker` @ `d221caa` (Founder-selected base — see §0)
**Auditor role:** Independent Principal Software Architect / Technical Due Diligence Reviewer (AI-assisted, evidence-gated per repo's own APDF/debug-root-cause discipline)

---

## Executive Summary

FooFoo is a documentation-first, class-first household meal recommendation engine (RE) product. This audit traces the full chain — vision → APDF → product docs → technical docs → database → seed/batch → migrations → validation → application code → RE runtime — using only repository evidence, on the branch the Founder designated as authoritative (`feat/wp-8f-runtime-blocker`, which diverges from `origin/main`; see §0).

**Headline finding: the repository's own STOP discipline is working as designed.** The most recent engineering work (WP-8D → WP-8E → WP-8F → WP-8FA) shows a team that built a real, tested Recommendation Engine core and integration layer, then **correctly refused to fabricate four schema mappings** needed to complete the `CandidateRepository` component, and then did the deeper archival work to resolve three of those four gaps with real evidence — leaving exactly one open Founder decision. This is the single most reassuring signal in the audit: when the evidence ran out, the team stopped, rather than guessing on a safety-critical filter (halal/no-beef/no-pork).

Set against that, three structural weaknesses recur throughout:
1. **Unratified critical-path documents.** The Business Logic Specification (DOC-P3-03), its governance matrix (DOC-P3-03A), and the ERD (DOC-P3-04) — the three documents the APDF framework itself calls the most consequential in the entire 33-document set — are filed under the `[ACTIVE]` naming token but carry internal headers reading "DRAFT — pending founder sign-off," with blank signature lines. Runtime code (WP-8D/8E) has been built against this unratified spec.
2. **Documentation drift.** `docs/README.md` (the repo's own entry point) makes at least two claims that are now stale and contradicted by evidence found elsewhere in the repo: the migration count ("29") and the state of validation-script staleness (already fixed by REPO-CERT-010 but not reflected in the README).
3. **Identifier hygiene gaps.** `DOC-P3-05` is claimed by two unrelated documents, and no document in the repo currently carries the title "Database Schema Specification" that the framework's own definition requires for that ID.

None of these three weaknesses represents fabricated work or hidden failure — every gap found was either self-disclosed in-repo (evidence of a working governance process) or is a low-severity hygiene item. The RE core algorithm is unusually well-specified for an early-stage product (18 sections, explicit formulas, an unresolved-decisions register) and the database schema is execution-proven against a live Supabase project, not just designed on paper.

**Verdict: B — Mostly Implemented with Minor Gaps** (full scoring in §35).

---

## 0. Audit Base and Branch Divergence (mandatory disclosure)

Per CLAUDE.md's Session Start Protocol, HEAD must equal `origin/main` with a clean tree; this repository fails that check. `origin/main` is at `3002b16` (WP-K01, a documentation-only knowledge-platform refactor); the current branch `feat/wp-8f-runtime-blocker` forked earlier and diverged with its own WP-8F/WP-8FA work. **The Founder explicitly selected the current branch as the audit base** (recorded decision, this session). This audit therefore does not cover WP-K01 (main-only) in the Application/RE review, though it is described in §22 for completeness since it affects certificate numbering.

**Correction of an internal research error, verified directly against the filesystem:** the commit messages for `a30a135` and `d221caa` reference "(REPO-CERT-016)" and "(REPO-CERT-017)" respectively, but the actual committed files are `[ACTIVE]_REPO-CERT-018_WP-8F_Runtime_Mapping_Blocker_v1.0.md` and `[ACTIVE]_REPO-CERT-019_WP-8FA_CandidateRepository_Audit_v1.0.md` — confirmed by reading both the certificate files and the WP-8F/WP-8FA documents themselves, which internally and consistently cite REPO-CERT-018/019. **There is no on-disk certificate-numbering collision with main's `REPO-CERT-016` (WP-K01)** — numbers 016–017 are simply unused/skipped on this branch, most likely a deliberate reservation to avoid exactly this collision. This is a minor commit-message hygiene defect (stale parenthetical), not a repository integrity fault.

---

## 1. Executive Summary
See above.

## 2. Repository Scope
Reviewed in full: `docs/governance/`, `docs/product/`, `docs/architecture/`, `docs/project-history/work-packages/`, `docs/project-history/certificates/`, `docs/README.md`, `CLAUDE.md`, `database/migrations/` (001–030), `database/rollback/` (001–030 + seed rollbacks), `database/seeds/` (100–117), `database/validation/` (900–905 + one reference script), `database/etl/` (2 Python generators), `data/source/` (11 raw files), `supabase/functions/` (all Edge Functions and `_shared/services/`), git history and both branch tips (`feat/wp-8f-runtime-blocker`, `origin/main`).

## 3. Documents Reviewed
33 APDF-mapped documents assessed for existence/status (§4 table); all Work Packages and Certificates in `docs/project-history/` (§13); RE-DOC-01–04 (converted from `.docx`); all migration/seed/validation SQL files; all RE-related TypeScript source under `supabase/functions/_shared/services/`.

## 4. APDF Compliance

| # | Document | Status | Evidence |
|---|---|---|---|
| P0-01 Business Model | ✅ ACTIVE | `docs/product/[ACTIVE]_DOC-01_Product_Brief_v1.1.docx` |
| P0-02 Market Research | ✅ ACTIVE | `docs/product/[ACTIVE]_DOC-02_Market_Research_v1.0.docx` |
| P0-03 User Personas | ✅ ACTIVE | `docs/product/[ACTIVE]_DOC-03_User_Personas_v1.0.docx` |
| P0-04 Problem Statement | ✅ Adequate (embedded in DOC-01) | as above |
| P1-01 PRD | ✅ ACTIVE | `docs/architecture/[ACTIVE]_DOC-04_PRD_v1.1.docx` |
| P1-02 User Journey Maps | ⚠️ Partial (flows only) | within DOC-05 |
| P1-03 Roadmap | ✅ ACTIVE | `docs/roadmaps/` |
| P1-04 Legal & Risk | ✅ ACTIVE | `docs/product/[ACTIVE]_DOC-09_Legal_v1.0.docx`, `PM-SUPP-02_Risk_Register` |
| P2-01 Information Architecture | ✅ ACTIVE | `docs/architecture/[ACTIVE]_DOC-05_Information_Architecture_v1.2.docx` |
| P2-02 Design System | ✅ ACTIVE | `docs/architecture/[ACTIVE]_DOC-06_UX_Design_System_v1.1.docx` |
| P2-03 Content Strategy | ⚠️ Partial | embedded in DOC-06, no standalone doc |
| P3-01 System Architecture | ✅ ACTIVE | `docs/architecture/[ACTIVE]_DOC-10_Technical_Architecture_v1.0.docx` |
| P3-02 Conceptual Domain Model | ⚠️ **Filename ACTIVE / header DRAFT, unsigned** | `[ACTIVE]_DOC-P3-02_Conceptual_Domain_Model_v1.1.md` L5 |
| P3-03 Business Logic Spec (critical doc) | ⚠️ **Filename ACTIVE / header DRAFT, unsigned — content complete** | `[ACTIVE]_DOC-P3-03_Business_Logic_Specification_v1.0.md` L5 |
| P3-03A Logic Governance Matrix (companion) | ⚠️ Same DRAFT/filename mismatch | `[ACTIVE]_DOC-P3-03A_Logic_Governance_Matrix_v1.0.md` L5 |
| P3-04 Data Architecture/ERD | ⚠️ **Filename ACTIVE / header DRAFT, unsigned — content complete** | `[ACTIVE]_DOC-P3-04_Data_Architecture_ERD_v1.3.md` L4 |
| P3-05 Database Schema Spec | ❌ **ID collision, no canonical schema-spec doc exists** | two unrelated docs both claim `DOC-P3-05` (see §4a) |
| P3-06 API Contract Spec | ✅ FROZEN (header) / filename token ACTIVE | `[ACTIVE]_DOC-P3-06_API_Contract_Specification_v1.2.md` |
| P3-07 Security Architecture | ✅ FROZEN (header) / filename token ACTIVE | `[ACTIVE]_DOC-P3-07_Security_Architecture_v1.2.md` |
| P3-08 Integration/Infra Architecture | ✅ FROZEN (header) / filename token ACTIVE | `[ACTIVE]_DOC-P3-08_Integration_and_Infrastructure_Architecture_v1.1.md` |
| P4-01 Frontend Spec | ❌ Missing | no file found |
| P4-02 Service/Edge Function Spec | ⚠️ **Correctly labeled DRAFT**; gated by open decision AD-01 | `[DRAFT]_DOC-P4-02_Service_and_Edge_Function_Specifications_v1.0.md` |
| P4-03 Seeding/Migration Plan | ⚠️ Partial, spread across DOC-P3-05-Part-A + WP-6 series | no single canonical artifact |
| P4-04 Performance/Scalability | ❌ Missing (NFRs only, in DOC-04) | — |
| P4-05 Observability | ❌ Missing | — |
| P5-01 Test Strategy | ❌ Missing | — |
| P5-02 QA Spec | ❌ Missing | — |
| P5-03 Deployment Runbook | ❌ Missing | — |
| P5-04 Analytics Framework | ⚠️ Partial (DOC-04 metrics only) | — |
| P5-05 Incident Runbook | ❌ Missing | — |
| P6-01 GTM | ✅ ACTIVE | `docs/product/[ACTIVE]_DOC-07_GTM_v1.0.docx` |
| P6-02 Revenue | ✅ ACTIVE | `docs/product/[ACTIVE]_DOC-08_Revenue_v1.0.docx` |
| P6-03 Evolution Roadmap | ⚠️ RE-DOC-05 claimed complete by APDF Base doc but **not found on disk** — only RE-DOC-01–04 exist | `docs/architecture/` listing |
| P6-04 Session Continuity | ✅ ACTIVE (CLAUDE.md) / ⚠️ `KNOWLEDGE.html` referenced by CLAUDE.md session protocol does **not exist** in repo root | — |

**§4a — DOC-P3-05 identifier collision:** `docs/architecture/[ACTIVE]_DOC-P3-05_Part_A_Readiness_Migration_Strategy_v1.2.md` and `docs/governance/[ACTIVE]_DOC-P3-05_Architecture_Gap_Register_v1.1.md` both claim the `DOC-P3-05` ID for unrelated content; neither is the "Database Schema Specification" the APDF Base document (line 317) defines DOC-P3-05 to be. No document in the repo currently carries that title. This is a genuine identifier-governance gap, not fabricated completeness — the schema itself is fully implemented in migrations (§7) and described piecemeal across the ERD and Migration Strategy docs, but no single ratified "schema spec" artifact exists.

**§4b — The vNext Addendum does not fix the stale gap table.** `docs/governance/[ACTIVE]_APDF_Framework_vNext_Addendum_v2.0.md` is itself filed `[ACTIVE]` while its own header reads "Draft — Ready for Founder Review" with a blank sign-off line — the same defect it exists to prevent. It renumbers the phase model but never updates the original Base-doc gap table (lines 648–680), which is why that table now reads as obsolete rather than corrected. This exact conflict was already self-identified in `docs/governance/[ACTIVE]_Repository_Naming_Conflict_Report_v1.0.md` (2026-07-13) and remains unresolved as of 2026-07-16 pending a Founder ruling — a legitimate process pause under WP-5AA's STOP clause, not an oversight, but still a live filesystem inconsistency today.

## 5. Product Reconstruction (from documentation only)

FooFoo assigns every household to a **cohort** (region/diet/persona) at onboarding, derives a **class plan** (which meal-class — e.g. `BF_SOUTH_FERMENTED`, `LD_CHICKEN_HOME_CURRY` — fills each slot of the week) before any dish is chosen, then fills each class with a scored, variety-aware **dish pool**. This class-first design (RE-DOC-03) is the product's core differentiator versus dish-first recommenders.

The scoring pipeline (DOC-P3-03 §07, LF-E01–E08), reconstructed purely from documentation:
1. **Hard constraints first** (§06, LF-D01–D07): diet type, allergens, religious restrictions (halal/no-beef/no-pork), meal-occasion fit, never-list, conflict handling. Dishes failing these are removed before scoring, not penalized.
2. **Five-signal weighted score**, weights interpolated across a 5-tier confidence ladder (Cold Start → Mature, keyed on interaction count): cohort prior (config table, 0.50 neutral fallback), content match (cosine similarity, dish genome vs. taste vector), personal history (exponential decay, λ=0.05), context fit (weather/season/day-type/cook-time multipliers), exploration bonus (Thompson Sampling Beta-bandit, ~10% slate target) — minus penalty terms (Not-Today exponential decay, P0=0.80, λ=0.35).
3. **Variety re-ranking** (§08): Maximal Marginal Relevance (λ=0.70 MVP) plus five explicit windows (5-day cuisine-family cap, 7-day fried-dish cap with monsoon override, no-repeat-ingredient on consecutive days, 30-day no-repeat-dish, weekly breakfast-class cap).
4. **Suppression** (§09): Never/Not-Today gesture handling with reactivation checks.
5. **Safety gates** (§10): diet/allergen/Jain/planning-role — hard blocking, run again after ranking as a second line of defense.

Cold start (RE-DOC-04): Day 0 plan is cohort-dominant (confidence 0.40–0.65, high exploration), transitioning smoothly to personal-history-dominant by Day 60+ (confidence 0.88–0.96) via the same weight-ladder interpolation used at runtime.

Compliance functions (§15): consent capture, data export, data deletion — the only ones with a deployed HTTP endpoint today (`/v1/consent`, §21).

## 6. Technical Architecture Review

`DOC-P3-06/07/08` (API Contract, Security, Integration/Infra) are the three most mature Phase-3 documents in the repo — genuinely `FROZEN` per their own headers (though filed under an `[ACTIVE]` token, §4). RE-DOC-01 defines the RE as a deliberately isolated module behind `POST /v1/recommendations` (plus `/v1/events`, `/v1/plan/{user_id}/{week}`, `/v1/onboarding`) so scoring changes never touch the main app — this isolation is reflected in the actual code layout (`_shared/services/re/` as pure domain logic behind injected ports, §21).

## 7. Database Review

30 structural migrations (`001`–`030`), all correctly named `NNN_description.sql`, all paired with rollbacks (no gap in the structural band). Confirmed real, execution-verified tables matching the ERD (`DOC-P3-04 v1.3`) almost exactly by name and grouping: `profiles`, `household_members`, `onboarding_sessions`, `consent_records`, `dishes`, `ingredients`, `dish_ingredients`, `tags`/`dish_tags`, `dish_combos`, `meal_classes`, `week_plans`/`plan_slots`/`addon_slots`, `interaction_events`/`suggestion_logs` (both partitioned, `017_initial_partitions.sql`), `context_log`, `weather_cache`, `audit_log`, `derivation_conflicts`, `feature_flags`, `dish_features`, `etl_job_runs`, plus the full `re_engine` schema (config + RE-identity tables, service-role only).

Four derivation triggers (`fn_derive_dish_attributes`, `fn_propagate_ingredient_change`, `fn_sync_profile_allergen_union`, `fn_update_dish_genome_vector`) match the ERD exactly (`010_trigger_functions_and_triggers.sql`). RLS is structural (`019_rls_policies.sql`) and independently hardened (`029_pf1_security_hardening.sql` — REVOKEs derived-column write access, locks trigger EXECUTE to `service_role`, pins `search_path`), with behavioral proof scripts (`902`/`903`) that actually impersonate `authenticated`/`anon` roles rather than just checking policy existence.

**No `candidate`/`recommendation` scoring tables exist anywhere in the schema** — correctly consistent with WP-8F's documented halt before `CandidateRepository`; this is evidence the STOP was real, not merely claimed.

**Findings:**
- Seed files `101` and `102` have no paired rollback (real, unaddressed gap — likely explained by "illustrative seeds" later removed per REPO-CERT-007/009/010, but the gap itself is undocumented).
- `docs/README.md` states migrations run "001-029" — stale; 30 files exist (`030_re_cohorts_city_tier.sql` added 2026-07-14).
- `docs/README.md`'s claim that validation checks "900 Check 2… 901 Test 1… stale" is itself stale — `REPO-CERT-010` (WP-6E.3) already fixed these; the README was never updated to cite that certificate.
- `database/validation/WP-3D_Check2_Fix_Reference.sql` violates the `NNN_description.sql` naming convention (no numeric prefix); explicitly marked reference-only, low severity.

## 8. Batch Processing Review

`database/etl/generate_re_seeds.py` and `generate_icd1_seeds.py` transform raw spreadsheets in `data/source/` (`Indian_Meal_Cohort_Persona_DB_v3.xlsx`, `dishes.xlsx`, `ingredients_v5.csv`, `tags_v4.csv`, `cuisines_v4.csv`, combo CSVs) into the numbered seed SQL (`100`–`117`). This ETL→seed pipeline is intact and traceable end-to-end: raw source → generator script → seed file → live table, with row counts certified in `REPO-CERT-007`/`009`. No orphan reference data or unused batch scripts were found; both generator scripts have a corresponding seed output.

## 9. Seed Strategy Review

No standalone DOC-P4-03 exists; the seed strategy is distributed across `DOC-P3-05-Part-A` (Phase 5.4/11) and the certificate trail (`REPO-CERT-007` disposable clean-room ICD-1 pass → `REPO-CERT-009` live Supabase 18/18 table parity → `REPO-CERT-010` closes a derived-column privilege-drift finding surfaced by 009). This is a documented, executed, and independently re-verified seed pipeline — genuinely stronger evidence than most of the audit's other document gaps, just missing the single canonical planning artifact the framework calls for.

## 10. Data Mapping Review

See §21 (CandidateRepository blocker) for the most consequential mapping-evidence work in the repo: the WP-8F→WP-8FA sequence is, in substance, exactly this phase's mandate — mapping documented business-logic fields to actual schema columns and refusing to proceed where the mapping can't be proven.

## 11. Validation Review

`900`–`905` structural/behavioral/RE-knowledge validation scripts exist and, per direct SQL inspection, are modernized (canonical dish/class names, OID-based joins, invariant-based checks) — contradicting the stale caveat still printed in `docs/README.md` (§7). This is a documentation-freshness defect, not a validation-coverage defect.

## 12. Application Review

Only **one deployed Edge Function exists**: `supabase/functions/consent/` (`index.ts` + `handler.ts`), implementing `POST /v1/consent` per WP-8C (LF-M01) — a thin auth/ownership/delegate handler. **No `/v1/recommendations`, `/v1/onboarding`, `/v1/events`, or `/v1/plan` endpoint is deployed.** All RE logic lives in `_shared/services/`, called only by three in-process orchestrators, not yet exposed over HTTP (§21). This is consistent with, not contradictory to, the documented WP-8E debt register and the WP-8F halt.

## 13. Recommendation Engine Review (WP-8D → WP-8FA narrative, fully verified against code)

- **WP-8D (`e113ffa`, REPO-CERT-014):** Built and test-certified. `supabase/functions/_shared/services/re/{types,ports,constraints,scoring,variety,safety,resolvers,engine,index}.ts` — a pure, DB-agnostic domain engine (`RecommendationEngine.generateSlate`/`generateWeekPlan`) behind injected ports (hexagonal architecture). 52 tests passing (`_tests/re_core.test.ts`). Two disclosed limits: `re_cohort_class_priors` unseeded (0.50 fallback used) and one internally-inconsistent worked example in the spec (DCR-8D-01), resolved by a documented reading rather than silently ignored.
- **WP-8E (`e76bd9c`, REPO-CERT-015):** Built and certified. Three real callers confirmed by direct file read — `OnboardingOrchestrator`, `RecommendationService`, `NightlyPlanScheduler` — each constructing one shared engine instance. Concrete Supabase adapters exist for persistence/onboarding/plan-slot/eligible-users (`adapters/supabase-stores.ts`) but **not** for candidates. 62 tests total (10 new integration tests). WP-8E's own §6 explicitly flagged `CandidateRepository` as "BLOCKED (schema-mapping)" — the seed of the WP-8F stop.
- **WP-8F (`a30a135`, REPO-CERT-018 — commit message stale, says "016"; see §0):** A legitimate, evidence-backed STOP. Before writing `CandidateRepository`, four of seventeen `DishCandidate` fields could not be traced to a canonical schema source: `cuisineFamily`/`mainIngredientClass` (no matching tag dimension), `hasNonHalalMeat`/`hasBeef`/`hasPork` (no ingredient-level religious marker), `seasonalAffinity` (only `weather_affinity` exists, which is not the same axis), and cohort-average taste vector for cold start (only per-user vectors exist). Quoted reasoning: *"A 'partial' CandidateRepository (filling the 4 fields with defaults) is a fabricated default, forbidden, and would make the engine's output wrong-but-plausible."* No code was written; 62 existing tests re-verified green.
- **WP-8FA (`d221caa`, REPO-CERT-019 — commit message stale, says "017"):** Read-only architecture audit that did the deeper archival work WP-8F had not — converting the previously-unreadable RE-DOC-02 `.docx` and inspecting raw seed CSVs directly. Resolved 3 of 4 blockers as derivable without schema change (cuisine_family via `dishes.cuisine_id → cuisines.cuisine_group`; beef/pork via existing seeded ingredient rows joined through `dish_ingredients`), reclassified two as documented MVP deferrals (halal certification — genuinely unmodelled anywhere; seasonal affinity — source data never collected), and left **exactly one open Founder decision**: `main_ingredient_class` — the raw source CSV has an `ingredients.category` column that was never seeded, and no "dominant ingredient" rule has been specified.

`CandidateRepository`: confirmed by full-repo grep — interface only (`ports.ts:19`), referenced by `engine.ts` constructor injection, **no implementing class anywhere**. The engine literally cannot run against the live database until this is built, which cannot happen until the one open decision is ratified.

## 14. API Review
One live contract: `POST /v1/consent` (WP-8C). The full RE API surface (§6) is specified in RE-DOC-01/DOC-P3-06 but not yet implemented as HTTP endpoints.

## 15. Security Review
RLS structural + hardened (§7); auth framework built in WP-8C (REPO-CERT-011); Security Architecture doc (DOC-P3-07) is content-FROZEN. No penetration-test evidence found in-repo (expected — pre-launch).

## 16. Performance Review
No DOC-P4-04 exists; NFRs only within DOC-04. Partitioning exists for high-volume event tables (`017_initial_partitions.sql`) as a forward-looking scalability measure, but no load-test or benchmark evidence was found.

## 17. Scalability Review
Partitioning and RLS-locked `re_engine` schema separation support horizontal growth; the RE core's port-based design (§13) means swapping in a real `CandidateRepository` or a future ML-backed scorer requires no change to `engine.ts` callers — a genuine architectural strength for future evolution, evidenced by the WP-8D/8E design itself, not asserted from documentation alone.

## 18. Maintainability Review
Strength: hexagonal RE core with 62 passing tests and three isolated callers. Weakness: the business-logic spec those tests validate against is itself unratified (§4), meaning "tests pass" currently proves internal consistency, not Founder-approved correctness.

## 19. Documentation Quality
High signal-to-noise on the critical documents (DOC-P3-03/03A/04 are unusually rigorous for their unratified state) but real drift in the repo's own index (`docs/README.md`, §7/§11) and an unresolved identifier collision (§4a). The repo's own naming-conflict self-report (2026-07-13) shows active governance discipline; the gap is that the ruling it awaits hasn't landed in three days.

## 20. Feature Coverage Matrix
| Feature | Product doc | Business logic doc | Schema | Seed | Code | Status |
|---|---|---|---|---|---|---|
| Onboarding/cohort assignment | DOC-04 | DOC-P3-03 §03 | `onboarding_sessions`, `re_main_cohorts` | 110–113 | `OnboardingOrchestrator` | Implemented, no HTTP endpoint |
| Class plan generation | RE-DOC-03 | DOC-P3-03 §04 | `re_meal_classes`, `week_plans` | 114–115 | `engine.ts generateWeekPlan` | Implemented, no HTTP endpoint |
| Hard-constraint filtering | DOC-P3-03 §06 | same | `dish_tags`, `ingredients` | 103–104 | `constraints.ts` | Implemented, tested |
| Scoring (5-signal) | DOC-P3-03 §07 | same | config tables (`re_engine`) | 100 | `scoring.ts` | Implemented, tested; cohort priors unseeded |
| Variety re-ranking | DOC-P3-03 §08 | same | n/a | n/a | `variety.ts` | Implemented, tested |
| Safety gates | DOC-P3-03 §10 | same | n/a | n/a | `safety.ts` | Implemented, tested |
| **Candidate generation from live DB** | DOC-P3-03 §04–06 (implied) | RE-DOC-02 | genome dims partially unseeded | partial | **`CandidateRepository` — not implemented** | **Blocked pending 1 Founder decision** |
| Consent/export/deletion | DOC-09, DOC-P3-03 §15 | same | `consent_records` | n/a | `consent/handler.ts` | **Fully implemented, deployed** |
| `/v1/recommendations` endpoint | RE-DOC-01 | DOC-P3-06 | n/a | n/a | **not built** | Missing |

## 21. Product vs Implementation Matrix
Covered inline in §13/§20 with evidence per row; no additional table needed — every claim above already carries file:line evidence.

## 22. Critical Findings
1. **DOC-P3-03/03A/04 (the three most consequential Phase-3 documents) are unratified** (filename/header status mismatch, blank sign-off), yet runtime code has been built against them. *Risk:* if the Founder's eventual sign-off changes a formula (e.g., the weight ladder or MMR λ), 62 tests and two shipped services would need rework. *Evidence:* headers cited in §4.
2. **`CandidateRepository` — the component that lets the RE run against real data — does not exist**, blocked on one open decision (`main_ingredient_class` dominant-ingredient rule). *Evidence:* §13, full-repo grep.
3. **No document in the repo satisfies the framework's own definition of "Database Schema Specification" (DOC-P3-05)** — the ID is claimed by two unrelated documents. *Evidence:* §4a.

## 23. High Findings
1. `docs/README.md` has two stale claims (migration count, validation-script staleness) that could mislead a fast-moving contributor into re-fixing already-fixed work. §7/§11.
2. RE-DOC-05 (Evolution Roadmap) is claimed complete by the APDF Base doc's gap table but was not found on disk. §4.
3. `KNOWLEDGE.html`, required by CLAUDE.md's own session-start protocol, does not exist in the repo root.

## 24. Medium Findings
1. Seed files 101/102 have no paired rollback (§7).
2. Commit messages for `a30a135`/`d221caa` cite stale certificate numbers (§0) — low-severity but could mislead someone grepping commit log for a cert number.
3. `database/validation/WP-3D_Check2_Fix_Reference.sql` violates the numbered-file naming convention (§7).

## 25. Low Findings
1. `PM-SUPP-02_Risk_Register` exists in both `.docx` and `.md` with no declared source of truth.
2. DOC-P3-06/07/08 are content-FROZEN but filed under the `[ACTIVE]` filename token rather than `[FROZEN]`.

## 26. Technical Debt
Explicitly self-disclosed by the repo itself (not discovered): WP-8E §6 debt register (CandidateRepository, `/v1/recommendations` and `/v1/onboarding` HTTP endpoints not yet built); WP-8FA's single open Founder decision; the pre-2026-07-13 documentary layer's unverifiable execution claims (e.g., `REPO-WP-02`'s addendum cites commit hashes `4ed5e91`/`63c8ce2` that do not exist in the current reconstructed git history — a direct consequence of the disclosed repository-history reconstruction event, `REPO-BOOT-03`).

## 27. Missing Features
Frontend implementation spec (P4-01), performance/scalability plan (P4-04), observability plan (P4-05), full test strategy/QA spec (P5-01/02), deployment runbook (P5-03), incident runbook (P5-05) — all ❌ in §4, consistent with a pre-launch, backend/RE-focused stage of the product.

## 28. Unexpected Features (positive)
The Logic Governance Matrix (DOC-P3-03A) — an 8-layer dependency graph, full read/write matrix, and explicit auditability section describing how to reconstruct "why was dish X ranked #1 for user Y on date Z" — exceeds what the APDF framework's original 33-document list asked for. The WP-8FA architecture-audit discipline (refusing partial implementations, re-deriving evidence from raw CSVs rather than trusting prior documentation) is a stronger evidentiary standard than most production codebases apply.

## 29. Recommendations
1. Bring DOC-P3-02/03/03A/04 and the vNext Addendum to actual Founder sign-off — they are the load-bearing documents for everything built in WP-8D onward, and treating them as unratified drafts while shipping code against them is the single highest-leverage governance action available.
2. Resolve the `main_ingredient_class` decision (WP-8FA's one open item) so `CandidateRepository` can be built for the two-thirds of mappings already proven safe.
3. Refresh `docs/README.md` against `REPO-CERT-010` and the current 30-migration count.
4. Resolve the `DOC-P3-05` identifier collision — either retitle one of the two colliding documents or produce the canonical schema-spec artifact the framework calls for.
5. Create `KNOWLEDGE.html` per CLAUDE.md's own mandatory session-start protocol.

## 30. Overall Engineering Score
**7.5/10.** Real, tested, well-architected core logic; disciplined STOP behavior under uncertainty; let down by governance-document ratification lag rather than by code quality.

## 31. Product Completeness %
**~55%** — core scoring/variety/safety logic complete and tested; candidate generation, runtime HTTP surface, and most Phase 4/5 operational documents missing.

## 32. Implementation Completeness %
**~40%** — one live endpoint (`/v1/consent`); RE core and integration layer built and tested but not runnable end-to-end without `CandidateRepository`.

## 33. Documentation Accuracy %
**~75%** — the critical algorithm/data documents are unusually accurate and detailed; accuracy is pulled down specifically by `docs/README.md` staleness and the DOC-P3-05 identifier collision, not by the core specs themselves.

## 34. Recommendation Engine Completeness %
**~50%** — pure-logic layers (constraints, scoring, variety, safety) are complete and test-certified; the data-access layer that would let the engine run against production is the one missing link, and it is missing for one specific, named, resolvable reason.

## 35. Final Verdict

**B — Mostly Implemented with Minor Gaps.**

The gaps found are real but are, almost without exception, gaps the repository already knew about and had documented before this audit began (WP-8E's debt register, WP-8F's blocker report, the 2026-07-13 naming-conflict report). That is the strongest possible evidence available to an outside auditor: a team whose own paper trail catches its own gaps does not need an auditor to discover them for the first time — it needs the discipline to close them. The one thing this audit adds beyond what the repository already knew is the DOC-P3-05 identifier collision and the README staleness, both low-severity and both fixable in an afternoon.

---

## Critical Self-Review

This audit is based entirely on repository evidence gathered read-only via parallel research agents plus direct verification by the lead auditor (who caught and corrected one research error: the WP-8F/WP-8FA certificate numbers). No production Supabase instance was queried directly (`mcp__supabase__*` tools were available but not used, since the mandate was repository evidence, not live-system inspection) — so §7's database claims rest on migration/seed/validation SQL and prior certificates (REPO-CERT-007/009/010), not a fresh live query. If a stronger guarantee is needed, a live `list_tables`/`get_advisors` pass against the production Supabase project would close that gap. RE-DOC-01–04 were read via `.docx` XML extraction, not native rendering — low risk of misreading but not zero.

## Versioning & Placement
v1.0, filed under `docs/project-history/work-packages/` per the Placement Rule, following the WP-6RE/WP-8FA precedent of filing independent audits as Work Packages. Companion certificate: REPO-CERT-020.

Founder sign-off: _______________________ Date: ___________
