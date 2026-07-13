# [ACTIVE]_Engineering_Handover_Project_Continuity_Package_v1.3.md
**Status:** ACTIVE
**Version:** v1.3
**Date:** 2026-07-01
**Supersedes:** `[ACTIVE]_Engineering_Handover_Project_Continuity_Package_v1.2` — records APDF Phase 3 formal completion following DOC-P3-08 v1.1 freeze. Targeted update only; Part 14's Phase 3 status and one Part 9 line are corrected to reflect completion, nothing else rewritten.
**Approved By:** Pending Founder sign-off
**Current Phase:** APDF Phase 3 (Solution Architecture) — **now fully complete including DOC-P3-06 and DOC-P3-07, both APPROVED — ACTIVE — FROZEN.** Ready for Phase 3.5 (Technical Implementation / Service Layer), and for the DOC-P3-08 readiness assessment already in progress.
**Source Documents Referenced:** `[ACTIVE]_Project_Baseline_Register_v1.3`, `[ACTIVE]_DOC-P3-06_API_Contract_Specification_v1.2`, `[ACTIVE]_DOC-P3-07_Security_Architecture_v1.2`, plus all documents catalogued in Part 3 of v1.0 (unchanged)
**Downstream Documents Dependent On This Package:** Every future Claude session working on this project, starting with the very next one after this document is filed

**Addendum Notice (v1.0 → v1.1):** v1.0 was written before DOC-P3-06 and DOC-P3-07 existed, and correctly described Phase 3 as complete only through DOC-P3-05. Both documents have since been drafted, revised, and approved/frozen (DOC-P3-06 v1.2, session #028; DOC-P3-07 v1.2, session #030). **This is a targeted addendum, not a rewrite** — only Part 1 (Executive Overview), Part 3.3 (document catalogue), and Part 9 (Current Project Status) are updated below. Parts 2, 4–8, 10–13 are carried forward from v1.0 unchanged and are not reproduced in full here; consult v1.0 (superseded but not deleted, per standard practice) if their full text is needed, or treat every citation below as pointing to the same unchanged content v1.0 already established.

**Purpose of this document:** This is not a summary. This is the complete onboarding package for a brand-new Claude session with zero conversational memory. If something mattered during this project's history and is not written down here or in an ACTIVE project file, it is treated as lost — so nothing important is left unwritten. A new session should be able to read this document plus the ACTIVE files it references and continue work with the same discipline, the same governance, and the same understanding of *why* things are the way they are, without ever opening this chat again.

---

# Part 1 — Project Executive Overview

## Project vision
FooFoo is an AI-powered meal decision assistant for Indian households, built to solve the daily "aaj kya banaye?" (what do I cook today?) problem. The founding framing: *"Zomato solved how to get food. FooFoo solves what to eat."* The product is not a recipe app or a food-ordering app — it is a recommendation engine that understands a household's food culture, dietary constraints, regional identity, and evolving taste, and turns that understanding into a concrete 7-day meal plan.

## Product objective
Give an Indian household (the primary persona, "Meera," a 32-year-old family meal planner) a personalized weekly meal plan that:
- Respects hard dietary constraints (diet type, religion, allergens) with zero tolerance for violation
- Reflects the household's regional food culture, blended with their current city's influence based on how long they've lived there
- Accommodates special household members (infants, diabetic elders, postpartum mothers, etc.) via additive add-ons, never by changing the primary family meal
- Learns from behavior over time, shifting from research-cohort-based recommendations (cold start) to genuinely personalized ones
- Runs entirely on free-tier infrastructure until the product proves itself at 500 DAU within 90 days

## Product scope (MVP)
- React Native + Expo mobile app, ~35 screens
- Supabase (PostgreSQL) backend, two schemas: `public` (client-visible) and `re_engine` (recommendation-engine-private, service-role only)
- A "class-first" recommendation architecture: the engine picks a *meal class* (e.g., "light grain breakfast") before it picks a specific dish
- Onboarding that silently assigns one of 41 backend personas to a household without ever exposing that complexity to the user
- A 4-layer scientific model (Genome → Food Graph → Household Intelligence → Context) governing every recommendation

## Current implementation phase
**APDF Phase 3 (Solution Architecture) is complete, including the API Contract and Security Architecture layers added after this document's v1.0.** This covers: Conceptual Domain Model (DOC-P3-02) → Business Logic Specification (DOC-P3-03) → Logic Governance & Execution Matrix (DOC-P3-03A) → Data Architecture & ERD (DOC-P3-04) → full database implementation across DOC-P3-05 Parts (a) through (d), including seed data framework, structural validation, and behavioral validation → **API Contract Specification (DOC-P3-06 v1.2, APPROVED — ACTIVE — FROZEN) → Security Architecture (DOC-P3-07 v1.2, APPROVED — ACTIVE — FROZEN).**

**The database schema and migration layer remain permanently FROZEN** (Project Baseline Register v1.2, Step 10), and **DOC-P3-06 and DOC-P3-07 are now frozen under the identical discipline** — no future service may modify any of these three without an approved AGR/DCR/IDR/SER.

**Next phase is APDF Phase 4 (Technical Implementation)** — Edge Functions, and the actual recommendation engine runtime code, consuming the frozen database, the frozen API contract, and the frozen integration/infrastructure architecture exactly as defined. **DOC-P3-08 (Integration & Infrastructure Architecture) v1.1 is now ACTIVE — APPROVED — FROZEN**, completing all 8 mandatory Phase 3 documents. **APDF Phase 3 is formally complete.**

## Overall architecture philosophy
This project follows the **AI-First Product Development Framework (APDF)** — a 33-document, 6-phase methodology (`[ACTIVE]_APDF_Framework_v1.md`) adopted after an early "v1 Jain bug" where dietary/religious safety logic was implemented incorrectly because business logic was never formally specified before schema design. The philosophy: **you cannot design what you have not understood; you cannot build what you have not designed.** Every schema object, trigger, and index traces back to a specific business-logic function and document section.

A second philosophy adopted partway through: **never silently fix, never silently assume.** Any inconsistency discovered during implementation is classified (AGR / IDR / DCR — Part 6) and surfaced explicitly before any action is taken. This caught and correctly resolved five real issues (AGR-001 through AGR-004, IDR-001).

## Current maturity
- Product/UX documentation (Phases 0–2): mature, stable
- RE conceptual documentation (RE-DOC-01 through 05): mature, stable, **v1.0 only** — there is no "v1.1"; an earlier session mistakenly believed one existed, later corrected (see Part 7 Correction Notice)
- Solution architecture (DOC-P3-02 through P3-05): **complete and frozen**
- Service/implementation layer (Phase 4): **not started**
- Seed/reference data: **structurally complete, substantively incomplete** — see IDR-001, the single most important open item in this package

## Remaining roadmap (detail in Part 10)
1. Obtain or reconstruct the real seed source data (`Indian_Meal_Cohort_Persona_DB_v3.xlsx`) — resolves IDR-001
2. **Resolve AGR-P3-07-001** (age-verification implementation omission relative to DOC-10 §06) — Founder decision required; does not block Phase 4 start, but is launch-blocking per DOC-09 §01
3. ~~DOC-P3-08 (Integration & Infrastructure Architecture)~~ — **Done, v1.1, ACTIVE — APPROVED — FROZEN (session #033). APDF Phase 3 formally complete.**
4. DOC-P4-01/02 — Frontend Implementation Spec and Service/Edge Function Specifications (both now have DOC-P3-06's frozen contract and DOC-P3-07's frozen security architecture as direct inputs)
5. Build the RE pipeline as Edge Functions, consuming the frozen schema and the frozen API contract
6. DOC-P5-01/02 — Test Strategy and QA Specification
7. Deployment, smoke testing, launch readiness

---

# Part 2 — Project Baseline

**The authoritative source for this section is `[ACTIVE]_Project_Baseline_Register_v1.2.md`.** This handover does not replace it — it points to it and summarizes its conclusion.

## Baseline status
**✅ Baseline Approved** (established in v1.1, carried forward unchanged into v1.2). Every Critical/High-severity version conflict from the original 8-step verification is resolved. Two findings (M-2, M-4) were later found to be **false findings** and formally withdrawn with the error explained in the register's own Correction Notice.

## Current authority
The **single authoritative list of ACTIVE documents** is the Step 2 table inside `[ACTIVE]_Project_Baseline_Register_v1.2.md`. This handover's Part 3 catalogue is built from that table with added implementation-status detail — but the register wins on any disagreement, and such a disagreement should itself be raised as a DCR.

## Governance frozen as of Baseline Register v1.2, Step 10
DOC-P3-04 (latest ACTIVE version) and DOC-P3-05 Parts (a)–(d) (latest ACTIVE versions) are permanently frozen. Full detail in Part 6 — this is essential reading before touching anything.

---

# Part 3 — Complete Document Catalogue

**Legend:** Mandatory (M) = must be read before related implementation work begins. Informational (I) = useful context, not a hard prerequisite.

## 3.1 — Phase 0–2 documents (Product, UX)

| Doc ID | Filename | Version | Status | Purpose | Downstream Deps | M/I |
|---|---|---|---|---|---|---|
| DOC-01 | `_ACTIVE__DOC-01_Product_Brief_v1_1.docx` | v1.1 | ACTIVE | Founding vision, 4-layer model overview | DOC-P3-02, DOC-P3-03 | I |
| DOC-02 | `_ACTIVE__DOC-02_Market_Research_v1_0.docx` | v1.0 | ACTIVE | Market sizing, competitive landscape | DOC-01 | I |
| DOC-03 | `_ACTIVE__DOC-03_User_Personas_v1_0.docx` | v1.0 | ACTIVE | Meera/Priya/Vikram personas, cohort mapping examples | DOC-P3-02, DOC-P3-03 | M (Phase 4 UX) |
| DOC-04 | `_ACTIVE__DOC-04_PRD_v1_1.docx` | v1.1 | ACTIVE | Feature registry, 6-step pipeline, NFRs, success metrics | DOC-P3-03 | M |
| DOC-05 | `_ACTIVE__DOC-05_Information_Architecture_v1_2.docx` | v1.2 | ACTIVE | 35 MVP screens, navigation, gestures | DOC-P3-03 | M (Phase 4 frontend) |
| DOC-06 | `_ACTIVE__DOC-06_UX_Design_System_v1_1.docx` | v1.1 | ACTIVE | Design tokens, OB-07 signaling, C-11 city-overlay weight values (load-bearing numeric source) | DOC-P3-03 (cites exact weight values) | **M — real numeric config values used in seed data** |
| DOC-06-Visual | `_ACTIVE__DOC-06-Visual_Design_System_Explorer.html` | unversioned | ACTIVE | Interactive companion to DOC-06 | — | I |
| DOC-07 | `_ACTIVE__DOC-07_GTM_v1_0.docx` | v1.0 | ACTIVE | Go-to-market strategy | — | I |
| DOC-08 | `_ACTIVE__DOC-08_Revenue_v1_0.docx` | v1.0 | ACTIVE | Monetisation model | — | I |
| DOC-09 | `_ACTIVE__DOC-09_Legal_v1_0.docx` | v1.0 | ACTIVE | DPDP Act 2023 compliance, consent/retention rules | DOC-P3-03, DOC-P3-04 (consent_records table) | **M — legal compliance is non-negotiable** |
| DOC-10 | `_ACTIVE__DOC-10_Technical_Architecture_v1_0.docx` | v1.0 | ACTIVE, **known open documentation gap** | Original tech stack, early RE pipeline sketch, Edge Function endpoint list | DOC-P3-04 (superseded on schema specifics) | I — **do not use its `re_engine` table-naming scheme; DOC-P3-04 supersedes it, but the amendment note was never added (open gap G-4)** |
| PM-SUPP-01 | `_ACTIVE__PM-SUPP-01_Roadmap_v1_0.docx` (or `.md`, identical) | v1.0 | ACTIVE | Phase sequencing / roadmap | — | I |
| PM-SUPP-02 | `_ACTIVE__PM-SUPP-02_Risk_Register_v1_0.docx` (or `.md`, identical) | v1.0 | ACTIVE | Risk identification | — | I |

## 3.2 — Recommendation Engine concept layer

| Doc ID | Filename | Version | Status | Purpose | M/I |
|---|---|---|---|---|---|
| RE-DOC-01 | `_ACTIVE__RE-DOC-01_Architecture.docx` | v1.0 — **only version that has ever existed** | ACTIVE | Module boundary (RE sovereign, server-side only), API contract, fallback behavior | **M** |
| RE-DOC-02 | `_ACTIVE__RE-DOC-02_Four_Layers.docx` | v1.0 | ACTIVE | 20 genome dimensions, Food Graph, household two-level model, city-overlay math, weather-to-food mapping | **M — the scientific core of the product** |
| RE-DOC-03 | `_ACTIVE__RE-DOC-03_Class_Taxonomy_Scoring.docx` | v1.0 | ACTIVE | 26 class codes, FinalScore formula (5 signals), weight ladder (5 tiers), 6 hard constraints | **M** |
| RE-DOC-04 | `_ACTIVE__RE-DOC-04_ColdStart_Variety_Suppression.docx` | v1.0 | ACTIVE | Confidence ladder, MMR variety algorithm, Not Today decay formula, Never-list reactivation | **M** |
| RE-DOC-05 | `_ACTIVE__RE-DOC-05_Evolution_Roadmap.docx` | v1.0 | ACTIVE | 4-state ML evolution model, feature store requirements, shadow-mode deployment | **M — governs Phase 4+ ML evolution** |
| RE-Visual-01/02/03 | `_ACTIVE__RE-Visual-01/02/03_*.html` | unversioned | ACTIVE | Interactive companions to RE-DOC-01/04/05 | I — **complete, correct set of 3; no 4th visual has ever existed** |

## 3.3 — Solution Architecture layer (Phase 3)

| Doc ID | Filename | Version | Status | Purpose | M/I |
|---|---|---|---|---|---|
| DOC-P3-02 | `_ACTIVE__DOC-P3-02_Conceptual_Domain_Model_v1_md.docx` | v1.1 | ACTIVE | 51 domain entities, 7 aggregate roots, 14 invariants, 52 events, 8-layer dependency map | **M — conceptual foundation** |
| DOC-P3-03 | `_ACTIVE__DOC-P3-03_Business_Logic_Specification_v1.md` | v1.0 | ACTIVE | 61 logical functions fully specified with formulas/thresholds/citations | **M — every algorithm the RE runs** |
| P3-03 Context Baseline | `_ACTIVE__P3-03_Context_Baseline_Readiness.md` | v1.0 | ACTIVE (supporting) | Pre-write validation for DOC-P3-03 (5 conflicts found/resolved) | I |
| P3-03 Logic Inventory | `_ACTIVE__P3-03_Logic_Inventory_QualityGate.md` | v1.0 | ACTIVE (supporting) | Full 61-function inventory, source coverage matrix, quality gate verdict | I |
| DOC-P3-03A | `_ACTIVE__DOC-P3-03A_Logic_Governance_Matrix_v1_md.docx` | v1.0 | ACTIVE | Dependency graph, read/write matrix, config classification, traceability, data lineage, execution classification, auditability, validation matrix | **M — governs HOW logic executes** |
| DOC-P3-04 | `_ACTIVE__DOC-P3-04_Data_Architecture_ERD_v1_3.md` | **v1.3** | ACTIVE, **FROZEN** | Complete physical schema: 60 tables, full DDL, indexing, partitioning, RLS, derived-data strategy, concurrency, auditability, ERD, data dictionary, data contracts, quality framework, master data governance | **M — the single most important technical document** |
| DOC-P3-05 Part (a) | `_ACTIVE__DOC-P3-05_Part_A_Readiness_Migration_Strategy_v1_2.md` | **v1.2** | ACTIVE, **FROZEN** | Readiness assessment, 20-file dependency/allocation matrices, transaction/failure/naming/verification/environment rules, Phase 16 (AGR-002/003 fix) | **M — governs the migration file structure** |
| DOC-P3-05 Part (b) Summary | `_ACTIVE__DOC-P3-05_Part_B_Completion_Summary_1_0.md` | v1.0-equivalent | ACTIVE, **FROZEN** | Completion record for files 001-009; AGR-001 discovery/resolution | M (historical/audit) |
| DOC-P3-05 Part (c) Summary | `_ACTIVE__DOC-P3-05_Part_C_Completion_Summary.md` | v1.0 | ACTIVE, **FROZEN** | Completion record for files 010-020; AGR-002/003/004 | M (historical/audit) |
| DOC-P3-05 Regression Validation | `_ACTIVE__DOC-P3-05_Regression_Validation_AGR002_003.md` | v1.0 | ACTIVE | Formal 5-point regression check post AGR-002/003 fix | M (historical/audit) |
| DOC-P3-05 Part (d) Summary | `_ACTIVE__DOC-P3-05_Part_D_Completion_Summary.md` | v1.0 | ACTIVE, **FROZEN** | Completion record for seed framework (100-102) and validation (900-904); raises/resolves IDR-001 | **M — full detail of the project's biggest open item** |
| **DOC-P3-06** *(new in v1.1)* | `_ACTIVE__DOC-P3-06_API_Contract_Specification_v1_2.md` | **v1.2** | **ACTIVE — APPROVED — FROZEN** (session #028) | 10 Surface B endpoints, full request/response contracts, auth/authz model, error catalogue, versioning strategy, event contract, consumer matrix | **M — the complete API contract Phase 4 must implement against** |
| **DOC-P3-07** *(new in v1.1)* | `_ACTIVE__DOC-P3-07_Security_Architecture_v1_2.md` | **v1.2** | **ACTIVE — APPROVED — FROZEN** (session #030) | Consolidated security architecture: trust boundaries, threat model, auth/authz, RLS/service-role model, DPDP compliance, incident detection, security traceability matrix | **M — carries AGR-P3-07-001 (open, launch-blocking, does not block this freeze)** |
| **DOC-P3-08** *(new in v1.3)* | `_ACTIVE__DOC-P3-08_Integration_and_Infrastructure_Architecture_v1_1.md` | **v1.1** | **ACTIVE — APPROVED — FROZEN** (session #033) | Integration inventory (8 integrations), infrastructure topology, CI/CD, environment strategy, failure handling, integration validation matrix, operational runbook summary, integration lifecycle governance | **M — completes all 8 mandatory Phase 3 documents; APDF Phase 3 formally complete** |
| Architecture Gap Register | `_ACTIVE__DOC-P3-05_Architecture_Gap_Register_v1_1.md` | **v1.1** | ACTIVE, living document | Tracks AGR-001 through 004 (all Resolved, DOC-P3-05-originated) plus a Cross-Document AGR Index for AGR-P3-07-001 (Open, DOC-P3-07-originated) | **M — check before assuming any past issue is open** |
| Project Baseline Register | `_ACTIVE__Project_Baseline_Register_v1_5.md` | **v1.5** | ACTIVE, control tower | Document inventory, ACTIVE checklist, conflict detection, Step 10 schema-freeze rule, Step 11 Frozen/Mutable distinction table, Step 12 Phase 3 completion record, **catalogues all 8 mandatory Phase 3 documents** | **M — read FIRST, always** |
| APDF Framework | `_ACTIVE__APDF_Framework_v1.md` | v1.0 | ACTIVE | The 33-document, 6-phase methodology | M (methodology understanding) |

## 3.4 — SQL Migration and Validation Files

**Migration files follow their own frozen numbering convention and do NOT receive the `[ACTIVE]` markdown prefix** (Part 13 standardization rule reserves that prefix for governance/specification documents only).

| Range | Purpose | Status |
|---|---|---|
| `001`–`009` | Core schema: extensions, schema setup, reference tiers 0/1/2, profiles, household-dependent tables, RE identity tables, content core, content junctions | ACTIVE, FROZEN |
| `010`–`020` | Operational: trigger functions/triggers (incl. `derivation_conflicts`, AGR-003 fix), planning tables (incl. inline `meal_classes` FK, AGR-002 fix), interaction/audit tables, config table structures, persona assignment/priors, operational audit tables, dish_features, initial partitions, retired `meal_classes` mirror placeholder, RLS (42 statements), indexes (36 statements) | ACTIVE, FROZEN |
| `100`–`102` | Seed data: config tables (fully real, `[CONFIRMED]` values), reference data framework (illustrative only, **IDR-001 applies**), illustrative dish content + dependents (illustrative only, **IDR-001 applies**) | ACTIVE, FROZEN in structure; **substantively incomplete pending real source data** |
| `900`–`904` | Validation: structural checks, behavioral trigger validation (live mutation test proving AGR-003's fix works end-to-end), behavioral safety-gate validation (live violation-detection test), behavioral RLS validation (two-user impersonation), behavioral config/smoke test | ACTIVE — re-runnable verification scripts |

**Known filename hygiene issue (still open, non-blocking, Part 7 G-3):** file `008`'s corrected version is named `_ACTIVE__008_content_core1_1.sql` — **missing the underscore** before `1_1` that every other file has. Any future tooling globbing `*_1_1.sql` will miss it. Content is correct and safe to use as-is; only the filename needs fixing.

## 3.5 — Files explicitly out of current scope / status unknown

| Item | Status |
|---|---|
| `12_MVP_Sprint_Plan_Phase1_v3`, `15_Pitch_Deck`, `Complete_Feature_Inventory`, `04_Budget_Financial_Projections` | Confirmed **absent from project storage** as of the last Baseline re-scan. Must be re-uploaded and freshly classified if needed. |
| `_ACTIVE__SESSION_HANDOFF-4.md` and `_ACTIVE__SESSION_HANDOFF_v1_0-1.docx` | Two files, unrelated naming/numbering schemes, relationship never disambiguated (open item G-6). **This handover package supersedes both in practical terms** — read this document instead. |
| `Indian_Meal_Cohort_Persona_DB_v3.xlsx` | **Never uploaded to project storage at any point.** The single most consequential missing artifact — see IDR-001 (Parts 4.9, 7, 8). |

---

# Part 4 — Architecture Evolution History

## 4.1 — The founding decision: class-first, not dish-first
**Decision:** The RE always selects a *meal class* before selecting a specific dish. Dish selection is always an expansion within an already-chosen class.
**Why:** Ensures nutritional/cultural balance across a week — a household gets a structured plan, not just "popular dishes."
**Alternative rejected:** Direct dish ranking with no class layer — rejected for producing no structural balance guarantee.

## 4.2 — The pivot from "schema-first" to "docs-first, no exceptions"
**Context:** An early schema draft written directly from RE concept documents, skipping formal business-logic specification, produced the "v1 Jain bug" — Jain dietary-safety logic implemented incorrectly because its exact derivation rule was never precisely written down first.
**Decision:** Adopt the full APDF framework — no code/schema until CDM → Business Logic Spec → Governance Matrix → Data Architecture → Database Schema, strictly in order.
**Alternative rejected:** Continue patching the existing schema draft — rejected as treating symptoms while leaving the root "no formal specification" problem unaddressed.

## 4.3 — Dish genome vector: pre-computed and stored, not assembled at query time
**Decision:** `dishes.genome_vector` is a trigger-maintained, stored `real[]`.
**Alternatives rejected:** (1) query-time assembly — too slow against the 800ms pipeline budget; (2) immediate `pgvector` adoption — premature at MVP candidate-pool sizes (~8-60 dishes/class), with a documented single-step upgrade path left open instead.

## 4.4 — Add-ons are always additive, never substitutive
**Decision:** Household members with special needs get a separate Add-on Slot; the primary family meal is never modified.
**Why:** Core differentiator vs. "medical diet converter" apps. Enforced structurally via a `UNIQUE(plan_slot_id, household_member_id)` constraint on a distinct `addon_slots` table.

## 4.5 — Ingredient-level allergen safety, never dish-level shortcuts
**Decision:** Safety-critical allergen checks always join through `dish_ingredients → ingredients.allergen_flags`; `dishes.allergen_flags` is a display cache only, explicitly never trusted for the safety path ("GR-06").
**Why:** A dish-level cache can go stale between derivation-trigger runs; ingredient-level ground truth removes that risk entirely.

## 4.6 — AGR-001: the `service_role_app_writer` phantom role
**What happened:** DOC-P3-04's original REVOKE statement protecting derived dish columns named a role, `service_role_app_writer`, that was never defined anywhere.
**Resolution:** Architecture corrected first (DOC-P3-04 → v1.3, role removed since `service_role` never needed restriction), migration file updated as a direct, minimal consequence.
**Lesson institutionalized:** "Raise an AGR, fix the architecture first, then propagate the minimum implementation change" — the origin case for this project's core discipline.

## 4.7 — AGR-002 and AGR-003: planning-layer ordering defects, fixed at the root
**What happened:** DOC-P3-05 Part (a)'s own migration-allocation matrix contradicted itself twice — once about which file creates `public.meal_classes` (needed by file `011`'s FK before it existed under the original allocation), and once about `derivation_conflicts` (needed by a trigger in file `010` but allocated to file `015`, five files later).
**Resolution — the key precedent:** Fixed at the root (Part (a) itself, → v1.2) rather than patched only in the implementation layer, per explicit founder instruction. `meal_classes` reallocated to file `003`; `derivation_conflicts` reallocated to file `010`; file `018` retired as an empty placeholder (number preserved, not reused).
**Lesson institutionalized:** When the true cause is a defect in the plan, fix the plan.

## 4.8 — AGR-004: minor documentation-precision findings, informational only
Three small items (an index-count inflation, one redundant-but-faithfully-reproduced index, one syntax-impossible index resolved via P3-04's own documented fallback). No architecture change required.

## 4.9 — IDR-001: the missing source dataset (the project's current single biggest open item)
**What happened:** 15 reference tables (~30,000 rows) and a 500+ dish catalogue are specified to come from `Indian_Meal_Cohort_Persona_DB_v3.xlsx` — never uploaded to project storage.
**Why IDR, not AGR:** The architecture correctly specifies shape/structure/volume; the design is not wrong. The blocker is a missing external input.
**Resolution so far:** A full seed-loading framework was built and proven correct with small, real, clearly-marked illustrative rows (never fabricated business data). Every gap explicitly marked `AWAITING SOURCE DATA`.
**This remains open.** See Parts 7 and 10.

---

# Part 5 — Decision Register

| ID | Context | Decision | Reasoning | Alternatives Considered | Outcome | Documents Affected |
|---|---|---|---|---|---|---|
| D-001 | RE architecture foundation | Class-first, not dish-first | Structural variety/balance guarantees | Direct dish ranking | Adopted, never revisited | RE-DOC-03, DOC-P3-03 |
| D-002 | Post "v1 Jain bug" | Adopt full APDF docs-first methodology | Prevent recurrence of underspecified-logic bugs | Continue patching existing schema | Adopted; governs whole project | APDF_Framework, all P3-0x |
| D-003 | ContentMatch implementation | Pre-computed trigger-maintained `real[]` genome vector | 800ms budget; pgvector premature at MVP scale | Query-time assembly; immediate pgvector | Adopted; documented upgrade path | DOC-P3-03 §07, DOC-P3-04 §03.6/03.9/12 |
| D-004 | Household add-on handling | Strictly additive, never substitutive | Core product differentiator | Modify primary meal in place | Adopted; enforced via UNIQUE constraint | CDM Invariant 9, DOC-P3-04 §03.14 |
| D-005 | Allergen safety | Ingredient-level ground truth always, never dish-level cache | Cache can go stale between derivations | Trust dish-level flags directly | Adopted; codified "GR-06" | DOC-P3-04, migrations 009/010 |
| D-006 (AGR-001) | Undefined REVOKE role | Remove `service_role_app_writer`; restrict only `authenticated, anon` | Role never existed; service_role never needed restriction | Define the phantom role; guess its intent | Architecture corrected (P3-04→v1.3); migration 008 updated | DOC-P3-04, migration 008 |
| D-007 (AGR-002/003) | Two self-inconsistencies in Part (a) | Fix the governance plan itself, then propagate minimum implementation change | Explicit founder instruction: root-cause fix, not symptom patch | Patch implementation only | Both resolved at planning layer; regression confirmed zero drift | Part (a) v1.2, migrations 003/010/011/015/018 |
| D-008 (IDR-001) | Missing source spreadsheet | Build seed framework with illustrative data only; never fabricate | Fabricating data would itself be an undocumented assumption | Invent plausible full data; skip seeding entirely | Framework proven; full load deferred, disclosed | Migrations 100-102, Part (d) Summary |
| D-009 | Post-Part(c) governance | Permanently freeze DOC-P3-04 + Part (a)-(d); require AGR/SER for any future change | Protect the discipline just built from erosion by future service-layer shortcuts | Leave schema open to ad hoc changes | Adopted (Baseline Register v1.2, Step 10) | Project Baseline Register v1.2 |
| D-010 | Baseline re-verification | Withdraw findings M-2/M-4 as false | Zero genuine file evidence found for either; based on misremembered chat context | Leave findings standing | Withdrawn, error explained in-register | Baseline Register v1.1→v1.2 |
| D-011 | Naming consistency | `[ACTIVE]_...vX.Y` for governance/spec docs; migrations keep `NNN_description.sql`, no prefix | Two artifact types need two non-conflicting conventions | Force one convention on both | Adopted; this handover follows it | Baseline Register v1.0 Step 9, this document |

---

# Part 6 — Governance Rules (permanent, binding — do not rely on conversation history for any of these)

## 6.1 — Document versioning and naming
- ACTIVE governance/spec/report docs: `[ACTIVE]_Document_ID_Document_Name_vX.Y` (`.md` per Part 13).
- Mandatory header: Status, Version, Date, Supersedes, Approved By, Current Phase, Source Documents Referenced, Downstream Documents Dependent On.
- Only one ACTIVE version of any document at a time. On revision: increment version, update header, mark prior superseded — never silently overwrite.
- All cross-references must cite an explicit version, never "latest X."
- **Version Conflict Policy:** if more than one candidate ACTIVE file is ever found for the same Document ID, stop, make no assumption, produce a Version Conflict Report before continuing.

## 6.2 — SQL migration convention (frozen)
- `NNN_description.sql` sequencing: `001`–`020` structural, `100`–`199` seed data, `900`–`999` validation.
- Every forward migration paired with a `_rollback.sql` file, written at the same time.
- Every file's header must cite the DOC-P3-04 section, DOC-P3-03 logical function(s), DOC-P3-03A governance reference, and relevant CDM entity/invariant.
- Idempotent patterns mandatory (`IF NOT EXISTS`, `CREATE OR REPLACE`, `duplicate_object` exception guards).
- Migration files never receive the `[ACTIVE]` markdown prefix.

## 6.3 — Architecture freeze (newest rule, one of the most important)
- DOC-P3-04 and DOC-P3-05 Parts (a)-(d), latest ACTIVE versions, are **permanently frozen**.
- Every future service must consume the database exactly as defined — no undocumented assumptions, no silent redefinition (no ad hoc columns, type changes, bypassed derived-column protections, or relaxed RLS for convenience).
- A genuine need for schema change requires either an **AGR** (existing architecture found incomplete/incorrect) or a **Schema Evolution Request (SER)** — new artifact type — (architecture correct, new capability requires growth). Either must be approved before any modification.
- Any approved change produces a new document version, becomes the new ACTIVE Baseline entry, prior version marked superseded.

## 6.4 — Issue classification discipline
Every issue discovered must be classified as exactly one of:
- **AGR** — approved architecture itself incomplete/inconsistent/incorrect; requires review/correction first.
- **IDR** — implementation cannot faithfully reproduce approved architecture due to a technical/practical constraint; architecture is NOT modified to resolve it.
- **DCR** — architecture correct, documentation needs clarification without changing meaning.
Never silently resolve. Classify first, explain the recommended course, act only within that classification's scope.

## 6.5 — Regression validation requirement
After any approved architectural correction: confirm no unintended architecture change, no migration allocation drift, no SQL objects added/removed beyond approved scope, all trigger dependencies remain safe, full traceability preserved. `DOC-P3-05_Regression_Validation_AGR002_003.md` is the reusable template.

## 6.6 — Behavioral validation requirement (permanent for all future phases)
Structural verification alone is insufficient. Must also verify: business rules execute correctly under live data, trigger behavior matches architecture under live mutation, derived attributes remain correct after changes, constraints actively reject bad data, RLS actually isolates different users, configuration-driven behavior functions correctly, data quality rules are enforced, audit/lineage behavior matches design. Migration files `901`–`904` are the template pattern (live mutation tests with `ASSERT`, two-user impersonation, planted-violation detection).

## 6.7 — Traceability requirement
Nothing may be validated, implemented, or documented without citing: the DOC-P3-04 section, the DOC-P3-03 logical function, the DOC-P3-03A governance reference, and (for migrations) the Part (a) allocation.

## 6.8 — Definition of Ready
A task is ready only when: prerequisite ACTIVE documents are identified with no version conflicts; any schema/architecture dependency already exists in the frozen baseline or has an approved AGR/SER; no open AGR/IDR blocks it; the task's scope has been checked against Part 7 of this document.

## 6.9 — Definition of Done
A task is done only when: every object created traces to an approved architectural source; structural AND behavioral validation both pass; any issue found was classified (never silently resolved); the Baseline Register and/or Gap Register are updated if governance-tracked artifacts were touched; a completion summary exists as a filed ACTIVE document, not only as chat output.

## 6.10 — File format standardization
Every governance/spec/register/report/architecture/implementation/reference/research/handover document must be Markdown (`.md`). Only exception: SQL migration files remain `.sql`. Non-Markdown source assets (DOCX/XLSX/PDF/HTML) are reference-only going forward.

---

# Part 7 — Known Assumptions, Constraints and Open Items

## 7.1 — Resolved
- AGR-001 (phantom REVOKE role) — Resolved, DOC-P3-04 v1.3
- AGR-002 (meal_classes allocation self-contradiction) — Resolved, Part (a) v1.2
- AGR-003 (derivation_conflicts forward-reference) — Resolved, Part (a) v1.2
- AGR-004 (minor index precision issues) — Resolved (informational)
- M-2 / M-4 (false findings re: nonexistent "RE v1.1" and 4th HTML visual) — Withdrawn, Baseline Register v1.2

## 7.2 — Open, Awaiting Founder / Blocked

| Item | Status | What's needed to unblock |
|---|---|---|
| **IDR-001 — missing seed source data** | **Open, the single most important item in this package** | Founder must either (a) locate/upload `Indian_Meal_Cohort_Persona_DB_v3.xlsx`, (b) commission its reconstruction (41 personas, ~2,952 cohort rows, ~20,664 weekly-plan rows, ~1,050 class-dish rows, 500+ tagged dishes), or (c) formally accept illustrative-scale data for an extended pilot with re-scoped launch criteria. Edge Function *code* can still be written against illustrative data meanwhile; end-to-end RE quality cannot be meaningfully tested until resolved. |
| G-3 — `008` filename typo + 7 harmless duplicate migration files | Open, non-blocking | Rename to include missing underscore; delete confirmed-identical duplicates whenever convenient |
| G-4 — DOC-10 never received its amendment note | Open, non-blocking | Add short note deferring schema authority to DOC-P3-04 |
| G-5 — Part (a)'s own header still says "v1.2" of P3-04 despite body discussing v1.3 | Open, non-blocking | One-line correction next time Part (a) is opened |
| G-6 — SESSION_HANDOFF-4 vs SESSION_HANDOFF_v1_0-1 relationship never disambiguated | Open, non-blocking | Dedicated comparison pass; treat this handover as superseding both meanwhile |
| Sprint plan, pitch deck, feature inventory, budget files | Confirmed absent from storage | Re-upload and freshly classify if needed for future GTM work |

## 7.3 — Deferred (by design, not oversight)
- Sunday cohort-weight recalibration algorithm (LF-J08) — explicitly a safe no-op until 30+ days of live data exist
- Festival-aware boosting — seeded now, activation behind a feature flag, Phase 2 scope
- Mood Selector — Phase 1 scope, schema already anticipates it additively
- Multi-profile households — Phase 1.5 scope, current Household=User collapse is a documented simplification
- pgvector adoption — deferred until candidate pools exceed ~200 dishes/class

## 7.4 — Technical constraints carried into Phase 4
- 800ms Edge Function budget for the full recommendation pipeline
- Weather API free-tier limit (1,000 calls/day), mitigated by `weather_cache` (12h TTL)
- No per-signal FinalScore logging at MVP — documented, accepted limitation with a named Phase 1 fix path (`recommendation_debug_log`, 5% sampled)
- Config value change history not versioned per-row at MVP — documented, accepted

---

# Part 8 — Knowledge Sources

| Source | Purpose | Authority | Mandatory? | Current Usage | Future Usage |
|---|---|---|---|---|---|
| `Indian_Meal_Cohort_Persona_DB_v3.xlsx` | Canonical research dataset behind all 15 seed/reference tables | **Highest — ground truth for cold-start quality** | Yes, but currently unavailable (IDR-001) | Only illustrative substitute rows exist | Must become versioned seed SQL migrations (`100`-series) once available — never hand-typed, never loaded outside the numbered convention |
| Dish/ingredient content set (500+ dishes) | Content source for `dishes`/`ingredients`/`dish_tags` at real scale | High | Yes, for launch readiness | Only 3 illustrative dishes + 8 ingredients seeded | Must pass the Tier-1 completeness gate (LF-K04) before linking to `re_class_dish_options` |
| DOC-06 C-11 city-overlay table | Numeric source for `re_city_overlay_config` | High, confirmed | Yes | Fully loaded (file `100`) | Stable; revisit only if research suggests band adjustments |
| DOC-P3-03 §16 config tables | Numeric source for all 10 `re_engine` config tables | High, `[CONFIRMED]` | Yes | Fully loaded (file `100`) | Expect revision from live production data; any change must update DOC-P3-03 and the seed migration together |

**Clarification:** none of the above are live/streaming database imports. They are seed sources — spreadsheets/specs transformed into versioned SQL `INSERT` statements. No live external connection exists into the running database.

---

# Part 9 — Current Project Status

## Completed
- **DOC-P3-02** v1.1 ✅
- **DOC-P3-03** v1.0 ✅ (plus supporting Context Baseline and Logic Inventory docs)
- **DOC-P3-03A** v1.0 ✅
- **DOC-P3-04** v1.3 ✅ (3 revision cycles: v1.0 → v1.1/1.2 enhancements → v1.3 AGR-001 fix)
- **DOC-P3-05 Part (a)** v1.2 ✅ (2 cycles: v1.1 → v1.2 AGR-002/003 fix)
- **DOC-P3-05 Part (b)** ✅ (files 001-009; AGR-001 found/resolved)
- **DOC-P3-05 Part (c)** ✅ (files 010-020; AGR-002/003/004 found/resolved)
- **DOC-P3-05 Part (d)** ✅ (files 100-102 seed framework, 900-904 validation; IDR-001 raised/disclosed)
- **DOC-P3-06** v1.2 ✅ **APPROVED — ACTIVE — FROZEN** (session #028; 3 revision cycles v1.0→v1.1→v1.2; 8 DCRs raised, 3 resolved by precedence, 5 open non-blocking)
- **DOC-P3-07** v1.2 ✅ **APPROVED — ACTIVE — FROZEN** (session #030; 3 revision cycles v1.0→v1.1→v1.2; 1 AGR raised — AGR-P3-07-001 — OPEN and does not block this freeze; 6 DOC-P3-07-owned DCRs, 5 inherited from DOC-P3-06)
- **DOC-P3-08** v1.1 ✅ **APPROVED — ACTIVE — FROZEN** (session #033; 2 revision cycles v1.0→v1.1; 0 AGRs raised; 4 DCRs, 3 resolved, 1 open non-blocking). **Completes all 8 mandatory APDF Phase 3 documents — Phase 3 formally complete.**
- **Project Baseline Register** v1.0 → v1.1 → v1.2 → v1.3 → v1.4 → **v1.5** ✅ (v1.5 catalogues DOC-P3-08 v1.1 and formally records Phase 3 completion, Step 12; none of v1.3/v1.4/v1.5 is a full re-scan)
- **Architecture Gap Register** v1.0 → **v1.1** ✅ (v1.1 adds a Cross-Document AGR Index entry for AGR-P3-07-001; DOC-P3-05-originated AGR-001–004 rows unchanged)

## What remains
1. **Resolve IDR-001** — biggest open item, missing seed source data
2. **Resolve AGR-P3-07-001** — age-verification implementation omission relative to DOC-10 §06; Founder decision required; launch-blocking per DOC-09 §01 but does not block Phase 4 start
3. ~~Mirror AGR-P3-07-001 into the Architecture Gap Register~~ — **Done, v1.1 (this session)**. Governance-status index only; full detail remains owned by DOC-P3-07
4. ~~**DOC-P3-08 (Integration & Infrastructure Architecture)**~~ — **Done, v1.1, ACTIVE — APPROVED — FROZEN (session #033).**
5. **DOC-P4-01/02** — not started
6. **Edge Function / RE runtime code** — not started; must respect the frozen schema and the frozen API contract
7. **DOC-P5-01/02** — not started
8. **Deployment/launch readiness** — not started

---

# Part 10 — Next Recommended Steps

1. **Decide IDR-001's resolution path** (founder decision, no prerequisite) — upload/reconstruct source data, or formally re-scope launch criteria for illustrative-scale pilot.
2. **New session reads this handover + Baseline Register v1.2 in full** before any substantive work (Part 11 gate).
3. **DOC-P4-01 (Frontend Implementation Spec)** — prerequisite: DOC-05, DOC-06, RE-DOC-01's API contract. Parallelizable with step 4.
4. **DOC-P4-02 (Service/Edge Function Specifications)** — prerequisite: DOC-P3-03 (61 functions to turn into contracts), DOC-P3-03A (execution classification), DOC-P3-04 (frozen schema).
5. **Build RE Edge Functions** — prerequisite: DOC-P4-02 approved, frozen schema; any schema gap found must be AGR/SER, never silently patched.
6. **DOC-P5-01/02** — prerequisite: DOC-P4-02; extend the behavioral-validation pattern from files `901`-`904` rather than reinventing it.
7. **Housekeeping (G-3 through G-6)** — no prerequisite, non-blocking, anytime.

---

# Part 11 — New Session Startup Checklist (mandatory)

1. ☐ Read `[ACTIVE]_Project_Baseline_Register_v1.2.md` in full.
2. ☐ Read this handover package in full.
3. ☐ Confirm no newer version of either exists in project files than what was just read.
4. ☐ Load only documents marked ACTIVE per the Baseline Register's Step 2 table.
5. ☐ Verify no version conflict exists for any document about to be relied on.
6. ☐ Check `[ACTIVE]_DOC-P3-05_Architecture_Gap_Register.md` for open AGRs/IDRs before starting related work. As of this handover: 4 AGRs Resolved, IDR-001 Open.
7. ☐ Confirm current phase: Phase 3 complete, Phase 4 not started.
8. ☐ Confirm frozen governance will be respected: no schema modification without approved AGR/SER.
9. ☐ Confirm latest versions before citing: DOC-P3-04 = v1.3, DOC-P3-05 Part (a) = v1.2. Never write "latest P3-04."
10. ☐ Only after all above, begin requested work — classify (AGR/IDR/DCR) any inconsistency found before acting on it.

---

# Part 12 — Context Preservation Audit

| Category | Where it lives now | Still trapped in chat? |
|---|---|---|
| Product vision/scope/philosophy | Part 1 + DOC-01/04 | No |
| ACTIVE document identity/version/purpose | Part 3 + Baseline Register v1.2 | No |
| Why architecture looks as it does | Parts 4 + 5 | No |
| Permanent governance rules | Part 6 + Baseline Register v1.0/v1.2 | No |
| Open items, assumptions, constraints | Part 7 | No |
| Knowledge source boundaries | Part 8 | No |
| Completion status | Part 9 | No |
| Next steps and dependencies | Part 10 | No |
| Full AGR-001-004 detail | Summarized here (4.6-4.8) + full detail in Gap Register / Part (b)/(c) summaries (primary source, ACTIVE, not chat-only) | Partially — by deliberate summarization choice, not a gap |
| Full IDR-001 detail | Parts 4.9/7.2/9 + full detail in Part (d) Summary | No — fully filed |
| Reasoning for M-2/M-4 withdrawal | Part 5 (D-010) + Baseline Register's own Correction Notice | No — fully filed |

**Conclusion: no critical project knowledge remains trapped exclusively inside conversation history.** The one "Partially" entry is intentional — this document points to full primary sources rather than duplicating hundreds of lines of SQL-level detail; a new session can retrieve that detail from the cited ACTIVE files if needed.

---

# Part 13 — Project File Standardization (action record)

- This document is filed as `[ACTIVE]_Engineering_Handover_Project_Continuity_Package_v1.0.md` — correctly prefixed, correctly versioned, Markdown.
- All future governance/spec/register/report/architecture/implementation/reference/research/handover documents follow the same convention.
- SQL migration files retain `NNN_description.sql`, **no** `[ACTIVE]` prefix — a permanent, intentional exception (Rule 6.1/6.2), not an oversight to "fix" later.
- Existing DOCX/XLSX/PDF/HTML files (RE-DOC-01–05, DOC-01–10, PM-SUPP-01/02, HTML visuals) remain in native format as reference assets. This package does not convert them — that is recommended as a separate, discrete future task if a new session's efficiency would benefit, particularly for the RE-DOC files given how heavily they are cited.

---

## Final sign-off

| Field | Value |
|---|---|
| Document | `[ACTIVE]_Engineering_Handover_Project_Continuity_Package_v1.1.md` |
| Status | ACTIVE — pending Founder sign-off |
| Supersedes | v1.0 — targeted addendum only (Parts 1, 3.3, 9 updated; all other Parts unchanged) |
| Confirms | **APDF Phase 3 formally complete** — all 8 mandatory documents ACTIVE; DOC-P3-04 through DOC-P3-08 all APPROVED — ACTIVE — FROZEN; Phase 4 not started; 4 AGRs on the Gap Register resolved, 1 open (AGR-P3-07-001) indexed in Architecture Gap Register v1.1 (governance-status only; full detail owned by DOC-P3-07); 1 IDR open (resolves via Phase 3.5); Baseline Register v1.5 current; schema/migration layer, API contract, security architecture, and integration/infrastructure architecture all frozen |
| Required before use | New session must complete Part 11's checklist before beginning any implementation work; Part 11 itself is unchanged from v1.0 but should now be read as also covering DOC-P3-06/DOC-P3-07 |

---

# Part 14 — Project Progress Snapshot (new in v1.2)

Using the APDF 6-phase lifecycle:

| Phase | Status |
|---|---|
| Phase 0 — Discovery | Complete |
| Phase 1 — Product Definition | Complete |
| Phase 2 — User Experience | Complete |
| Phase 3 — Solution Architecture | **Complete** |
| Phase 3.5 — Knowledge Integration & Seed Data Engineering | Pending (blocked on IDR-001 — real seed source data) |
| Phase 4 — Technical Implementation | Not Started |
| Phase 5 — Quality and Operations | Not Started |
| Phase 6 — Growth and Evolution | Not Started |

*(Asterisk removed in v1.3 — previously "Subject to completion of DOC-P3-08." DOC-P3-08 v1.1 is now ACTIVE — APPROVED — FROZEN (session #033). All 8 mandatory Phase 3 documents are complete.)*

---

# Part 15 — Current Frozen Architecture (new in v1.2)

- DOC-P3-04 (Data Architecture & ERD v1.3)
- DOC-P3-05 Parts (a)–(d)
- DOC-P3-06 (API Contract Specification v1.2)
- DOC-P3-07 (Security Architecture v1.2)

No future work may modify any of the four documents above unless an approved AGR, DCR, SER, IDR, or explicit Founder instruction reopens them.

---

Founder sign-off (v1.3 — Phase 3 status corrected to fully Complete in Part 14; DOC-P3-08 completion recorded in Parts 3.3 and 9; Baseline Register/Gap Register version references updated; no other content modified): ___________________________ Date: _______________
