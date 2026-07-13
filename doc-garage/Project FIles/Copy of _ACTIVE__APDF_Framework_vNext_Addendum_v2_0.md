# [ACTIVE]_APDF_Framework_vNext_v2.0

**Reconstruction of the AI-First Product Development Framework, derived from the complete FooFoo project lifecycle**
**Supersedes:** `APDF_Framework_v1.md` (retained, unmodified, as historical reference — the original 6-phase/33-document model)
**Date:** 2026-07-03 · **Status:** Draft — Ready for Founder Review
**This is a reconstruction of the framework itself, not a new architecture, not a new governance layer, not a redesign of anything already frozen.**

---

## 1. Project Lifecycle Analysis

Analyzing what actually happened across Discovery → Product Definition → UX → Solution Architecture → Phase 3.5 → Architecture Freeze, the real lifecycle that emerged has **7 natural stages**, not the original 6 phases. The difference isn't cosmetic — one entirely new stage (Knowledge Integration) emerged that v1 didn't anticipate at all, and the boundary between "architecture" and "implementation" turned out to need an explicit checkpoint the original framework never named.

| Stage (as it actually happened) | Why it exists | Inputs required | Outputs produced | Why the next transition was safe |
|---|---|---|---|---|
| **1. Discovery & Definition** | Establish problem, market, user, and exact product scope before any design | Founder vision, market context | DOC-P0/P1 series, personas, product brief | Safe once Founder and Claude agree on scope in writing — nothing downstream depends on ambiguous scope |
| **2. UX & Information Architecture** | Define how the product is used before defining how it works internally | Product Definition outputs | DOC-05 (IA), DOC-06 (Design System) | Safe once every screen/flow traces to a product requirement — architecture can now design *for* something concrete |
| **3. Solution Architecture** | Define the complete technical design — schema, logic, API, security, infrastructure — before writing implementation code | UX outputs, business logic understanding | DOC-P3-02 through P3-08 (8 documents), frozen schema, frozen API contract, frozen security model | Safe once every schema object traces to a business-logic function (the "v1 Jain bug" lesson) — this project's single most important discipline, earned the hard way |
| **4. Knowledge Integration** *(new — did not exist in APDF v1)* | Turn raw research/knowledge files into governed, provenance-tagged seed data BEFORE seeding — this stage didn't exist in the original plan because v1 assumed seed data would simply "be available"; in practice it required 6 full batches of Discovery→Canonicalization→Mapping→Gap Analysis→Resolution | Frozen Solution Architecture (schema is the mapping target), raw source files (CSVs, xlsx) | 6 batch packages, Project Integration Review, Architecture Decision Review, Architecture Freeze document | Safe once every source file has been mapped or explicitly gapped against the frozen schema, with zero orphan lineage — verified this project's own Lineage Audit found 0 broken chains across 6 batches |
| **5. Architecture Finalization** *(new — the explicit checkpoint APDF v1 never named)* | Convert the accumulated Knowledge Integration gaps into a final, Founder-approved set of schema amendments, distinct from the original Solution Architecture freeze | Knowledge Integration outputs (blockers, decision packs) | Founder-approved Architecture Approval Packs, final schema delta, Architecture Freeze declaration | Safe once the Founder has explicitly signed off on every remaining schema change — this project learned the hard way (this exact session) that "architecture frozen" and "ready to implement" are NOT the same moment; a freeze can still carry unresolved Founder decisions |
| **6. Repository Bootstrap** *(new — never modeled explicitly in v1)* | Stand up the actual repository, database instance, migration tooling, and CI scaffolding — a distinct, small, mechanical stage between "we know what to build" and "we are building it" | Architecture Finalization sign-off | Live `foofoo-v2` repo structure, live Supabase project, migration folder convention, CI skeleton | Safe once the repo can accept a migration file and run it against a real (even empty) database — this is a testable, binary readiness check, not a judgment call |
| **7. Implementation** | Actual code: seed SQL, Edge Functions, frontend, testing, launch | Repository Bootstrap complete | Working product | N/A — this is the terminal stage until Growth/Evolution begins |

**The single biggest lesson driving this reconstruction:** APDF v1 treated "Solution Architecture" and "Technical Implementation" as adjacent phases (3 → 4) with nothing between them. In practice, this project needed **three** stages in between — Knowledge Integration, Architecture Finalization, and Repository Bootstrap — none of which existed in the original plan, and their absence is exactly why "Claude repeatedly suggested Claude Code too early," per the Founder's own stated background for this session. Every premature Claude Code suggestion in this project's history happened at a moment that, in hindsight, was still inside Knowledge Integration or Architecture Finalization, not yet at Repository Bootstrap.

---

## 2. APDF vNext — Phase-by-Phase Breakdown

### Phase 1 — Discovery & Definition
*(Consolidates original Phases 0–1; no material change — this part of v1 worked correctly)*

| Field | Detail |
|---|---|
| **Purpose** | Establish the problem, market, user, and exact product scope |
| **Objectives** | Business model clarity; validated market opportunity; complete product requirements |
| **Inputs** | Founder vision, market research access |
| **Outputs** | DOC-P0-01–04, DOC-P1-01–04 (business model, market research, personas, PRD) |
| **Entry Criteria** | Founder has a product idea worth formal scoping |
| **Exit Criteria** | PRD approved; personas validated; no open scope ambiguity |
| **Deliverables** | Product Brief, Market Research, User Personas, PRD |
| **Primary Risks** | Building the wrong thing for the wrong user — the classic "impressive technology, wrong problem" failure v1 warned against |
| **Owner** | Founder |
| **Expected AI Role** | Research synthesis, persona drafting, structured questioning to surface unstated assumptions |
| **Founder Role** | Final authority on business model, market positioning, product scope |
| **Expected Claude Role** | Full engagement — this is pure Claude.ai document work |
| **Expected Claude Code Role** | None — no code exists to write yet |

### Phase 2 — UX & Information Architecture
*(Consolidates original Phase 2; no material change)*

| Field | Detail |
|---|---|
| **Purpose** | Define how the product is used before defining how it works internally |
| **Objectives** | Complete screen/flow inventory; design system established |
| **Inputs** | Approved PRD, personas |
| **Outputs** | DOC-05 (Information Architecture), DOC-06 (UX Design System) |
| **Entry Criteria** | Phase 1 complete and Founder-approved |
| **Exit Criteria** | Every screen traces to a product requirement; design system covers all identified screen types |
| **Deliverables** | IA document, Design System, HTML visual explorers |
| **Primary Risks** | Designing screens architecture can't efficiently support (caught by running UX and Architecture close together, not in strict sequence) |
| **Owner** | Founder / Product |
| **Expected AI Role** | IA structuring, design system authoring, visual prototype generation |
| **Founder Role** | UX approval, visual direction confirmation |
| **Expected Claude Role** | Full engagement |
| **Expected Claude Code Role** | None |

### Phase 3 — Solution Architecture
*(Consolidates original Phase 3; the discipline here — "every schema object traces to a business-logic function" — is validated by this entire project's experience and is kept unchanged)*

| Field | Detail |
|---|---|
| **Purpose** | Define the complete technical design before any implementation code is written |
| **Objectives** | Conceptual domain model, business logic spec, ERD, API contract, security architecture, integration architecture — all internally consistent and cross-referenced |
| **Inputs** | Approved UX/IA, business logic understanding |
| **Outputs** | DOC-P3-02 through P3-08 (8 documents), frozen schema, frozen API contract |
| **Entry Criteria** | Phase 2 complete |
| **Exit Criteria** | All 8 mandatory Phase 3 documents APPROVED — ACTIVE — FROZEN; zero unresolved architecture contradictions |
| **Deliverables** | The 8-document Phase 3 set, migration files 001-020 |
| **Primary Risks** | Repeating the "v1 Jain bug" — implementing business logic that was never formally specified |
| **Owner** | Founder → Architecture |
| **Expected AI Role** | Full architecture design, schema authoring, cross-document consistency checking |
| **Founder Role** | Approval gate for every frozen document |
| **Expected Claude Role** | Full engagement — heaviest Claude.ai document-production phase in the framework |
| **Expected Claude Code Role** | None yet — schema exists only as specification (`.md`), not as executable migrations |

### Phase 4 — Knowledge Integration *(NEW — did not exist in APDF v1)*

| Field | Detail |
|---|---|
| **Purpose** | Turn raw research/knowledge files into governed, provenance-tagged, schema-mapped seed data |
| **Objectives** | 100% Discovery coverage of every source file; canonicalization with zero unresolved duplicates; every attribute mapped or explicitly gapped; zero orphan lineage |
| **Inputs** | Frozen Phase 3 schema (the mapping target), raw source files |
| **Outputs** | Batch packages (Discovery → Canonicalization → Mapping → Gap Analysis → Resolution, per batch), Cross-Batch Dependency register, Project Integration Review |
| **Entry Criteria** | Phase 3 fully frozen |
| **Exit Criteria** | Every source file batched and closed; Project Integration Review confirms 100% lineage integrity and a bounded, evidence-complete blocker list |
| **Deliverables** | Per-batch pipeline packages, PIR document |
| **Primary Risks** | The risk this project actually encountered repeatedly: treating "missing evidence" and "Founder hasn't decided yet" as the same thing, or silently resolving ambiguity instead of classifying it. Also: **not recognizing when a "missing" source file has actually already been supplied** — this project's own IDR-001 finding (the master workbook was present all along) shows how a stale assumption can persist across many sessions if nothing re-checks it |
| **Owner** | Founder → Architecture, batch-by-batch |
| **Expected AI Role** | Full Discovery/Canonicalization/Mapping/Gap Analysis execution; evidence-first discipline; never inferring business facts |
| **Founder Role** | Batch freeze approvals; resolving Founder-decision-bound gaps as they accumulate (not required to resolve all of them before the next batch — Batch Independence) |
| **Expected Claude Role** | Full engagement — this is the second-heaviest Claude.ai phase, entirely document/evidence work |
| **Expected Claude Code Role** | **None.** This is the phase where premature Claude Code engagement happened historically in this project. No repository exists yet; there is nothing for Claude Code to operate on. |

### Phase 5 — Architecture Finalization *(NEW — the explicit checkpoint APDF v1 never named)*

| Field | Detail |
|---|---|
| **Purpose** | Convert the accumulated Knowledge Integration blockers into a final, Founder-approved schema delta — distinct from and subsequent to the original Solution Architecture freeze |
| **Objectives** | Consolidate duplicate/overlapping decisions into the smallest set of genuine Founder choices; verify every recommendation against real (not illustrative) data before it's acted on; produce a Chief-Architect-level recommendation, not just neutral options |
| **Inputs** | Knowledge Integration outputs (PIR, blocker matrix) |
| **Outputs** | Architecture Decision Review, Architecture Approval Packs, Architecture Freeze document, Founder sign-off |
| **Entry Criteria** | Knowledge Integration's Project Integration Review is complete |
| **Exit Criteria** | Founder has explicitly signed off on every remaining schema change; zero open Phase-9-blocking decisions remain |
| **Deliverables** | Signed Architecture Freeze document |
| **Primary Risks** | This project's own experience is the cautionary tale: a "freeze" recommendation was nearly acted on with a scope error (the GC-AGR-002 `slot` finding was originally 22 rows; direct re-verification against real data found 90). **The lesson: never let a Founder sign an architecture decision based on illustrative or partially-verified evidence** — always re-check against the real source before the sign-off, not after |
| **Owner** | Founder (final authority) |
| **Expected AI Role** | Direct, non-neutral recommendations where evidence supports one clearly; explicit verification against real data before any Founder ask; catching self-inconsistencies (like the addon-safety check this project just performed) before they become bugs |
| **Founder Role** | Final decision-maker; explicitly asking "does this break anything else" is exactly the right question at this stage, as demonstrated this session |
| **Expected Claude Role** | Full engagement, now explicitly in an "advisor with a recommendation" mode rather than a neutral-options mode |
| **Expected Claude Code Role** | **None.** Still no repository. This is a pure decision-making stage. |

### Phase 6 — Repository Bootstrap *(NEW — never modeled explicitly in v1)*

| Field | Detail |
|---|---|
| **Purpose** | Stand up the actual repository, database instance, and tooling — a small, mechanical, testable stage between "we know what to build" and "we are building it" |
| **Objectives** | Live repo with correct folder structure; live Supabase project; migration convention operational; CI skeleton in place |
| **Inputs** | Signed Architecture Freeze document |
| **Outputs** | `foofoo-v2` repo (already exists per project memory — this stage formalizes and verifies it), initialized Supabase project, `CLAUDE.md`, migration folder structure |
| **Entry Criteria** | Phase 5 sign-off received |
| **Exit Criteria** | A trivial test migration can be written, applied, and rolled back successfully against a real (even empty) database — a binary, testable readiness check |
| **Deliverables** | Bootstrap verification report |
| **Primary Risks** | Skipping this as "obviously already done" — repository *existing* is not the same as repository *verified ready*; this project's `Batch6`/`PIR` sessions found stale document states more than once, and the same discipline applies to infrastructure state |
| **Owner** | Founder → Engineering |
| **Expected AI Role** | Verification-first: confirm repo/Supabase state directly rather than assuming it matches what was last discussed |
| **Founder Role** | Confirms infrastructure access/credentials are in place |
| **Expected Claude Role** | Verification and folder/file scaffolding via Claude.ai's computer-use tools where applicable |
| **Expected Claude Code Role** | **This is the first phase where Claude Code becomes appropriate** — see Task 3 below for the precise reasoning |

### Phase 7 — Implementation
*(Consolidates original Phases 4–6: Technical Implementation, Quality/Operations, Growth/Evolution — collapsed into one phase with internal sub-stages, since this project's evidence shows the original 3-way split added document overhead without changing what actually happens sequentially: backend → frontend → test → launch → iterate)*

| Field | Detail |
|---|---|
| **Purpose** | Build, test, and ship the actual product against the frozen, bootstrapped foundation |
| **Sub-stages** | Seed SQL → Backend (Edge Functions) → Frontend (React Native/Expo) → Testing → Launch → Growth/Evolution (post-launch, iterative) |
| **Inputs** | Verified Repository Bootstrap |
| **Outputs** | Working product, deployed and operating |
| **Entry Criteria** | Phase 6 exit criteria met |
| **Exit Criteria** | Per sub-stage — seed data matches Seed Gate targets; Edge Functions pass behavioral validation; frontend implements the frozen IA; launch criteria (DOC-09/DOC-08) met |
| **Deliverables** | Seed migrations, Edge Function code, mobile app, test suites |
| **Primary Risks** | AGR-P3-07-001 (DPDP minor-protection) is a real launch-blocking item already identified — Phase 7 must not treat "seed data ready" as "ready to launch" |
| **Owner** | Founder → Engineering |
| **Expected AI Role** | Claude Code does the majority of execution here; Claude.ai handles any new specification needs that arise (DOC-P4 documents) |
| **Founder Role** | Launch approval, ongoing product direction |
| **Expected Claude Role** | Reduced relative to Phases 1–5 — mainly new-spec authoring and cross-checking Claude Code's output against frozen architecture |
| **Expected Claude Code Role** | **Primary executor** for this entire phase |

---

## 3. Implementation Transition — Reasoned, Not Assumed

Reasoning directly from this project's own evidence (not from general best practice):

- **Repository creation:** Should happen at Phase 6 entry — i.e., only after Architecture Finalization sign-off. Evidence: every time this project's sessions discussed "should Claude Code do X," the honest answer was "not yet" until an actual Founder-signed decision existed to implement. The repository already exists (`apverse-labs/foofoo-v2` per project memory) — this doesn't contradict the model, it means Phase 6 for this project is a **verification** stage, not a from-scratch creation stage.
- **Supabase existence:** Same timing as repository creation — Phase 6. A database instance with no confirmed schema to load is inert; creating it earlier adds no value and risks drift between "what's designed" and "what's provisioned."
- **Git initialization:** Phase 6, alongside repository verification.
- **Migration folder structure:** Phase 6 — this project's own `DOC-P3-05 Part A` (migration numbering strategy) is itself a Phase 5→6 artifact: it was written *after* architecture froze, specifically to prepare for implementation, which is exactly the Phase 6 purpose this reconstruction assigns it.
- **Validation framework:** Phase 6 for the *framework* (900-series script structure); Phase 7 for actually *running* it against real seed data.
- **When Claude Code first becomes appropriate:** **The moment Phase 6's exit criterion is met** — a trivial migration can be written and applied against a real database. Every earlier suggestion of Claude Code in this project's history (and there's an explicit Founder observation that this happened "too early" multiple times) occurred during Phase 4 or Phase 5, when no such database existed yet to apply anything to. This reconstruction makes that timing explicit and testable instead of a judgment call.
- **When real SQL should begin:** Phase 7, immediately after Phase 6 verification — this is the actual Seed SQL sub-stage.
- **When backend development begins:** Phase 7, after Seed SQL is loaded and validated (Edge Functions need real data to test against meaningfully, per this project's own `904_behavioral_config_and_smoke_test.sql` reasoning).
- **When frontend begins:** Phase 7, can start in parallel with backend once the API contract (`DOC-P3-06`, already frozen since Phase 3) is stable — frontend does not need to wait for backend *code*, only for the frozen *contract*, which already exists.

---

## 4. AI Responsibility Matrix

| Phase | Claude.ai Responsibilities | Claude Code Responsibilities | Founder Responsibilities | Human Review Checkpoint | Evidence Gate | Decision Gate | Implementation Gate |
|---|---|---|---|---|---|---|---|
| 1. Discovery & Definition | Full document authoring | None | Business model authority | PRD sign-off | Market research validity | Scope approval | N/A |
| 2. UX & IA | Full document authoring | None | UX/visual approval | IA sign-off | Screen-to-requirement traceability | Design system approval | N/A |
| 3. Solution Architecture | Full schema/API/security design | None | Freeze approval per document | Each of 8 documents | Business-logic traceability per schema object | Phase 3 freeze | N/A |
| 4. Knowledge Integration | Full Discovery/Canonicalization/Mapping/Gap Analysis | None | Batch freeze approvals, gap decisions | Each batch's Founder Approval Gate | Lineage integrity (0 orphans) | Batch freeze | N/A |
| 5. Architecture Finalization | Recommendation authoring, real-data re-verification | None | Final schema-delta sign-off | This exact stage (as demonstrated this session) | Real-data verification (not illustrative) | Architecture Freeze | N/A |
| 6. Repository Bootstrap | Verification, scaffolding via computer-use tools | **First appropriate use** — folder/config scaffolding, migration file creation | Infrastructure access confirmation | Bootstrap verification report | Trivial-migration-applies-successfully test | Bootstrap complete | Repository Gate |
| 7. Implementation | New-spec authoring, cross-checking Claude Code output | **Primary executor** — seed SQL, Edge Functions, frontend, tests | Launch approval | Per sub-stage deliverable | Seed Gate targets met; behavioral validation passes | Launch approval | Production Gate |

---

## 5. Current Project State (per APDF vNext)

| Status | Item |
|---|---|
| **Completed** | Phase 1 (Discovery & Definition) · Phase 2 (UX & IA) · Phase 3 (Solution Architecture, all 8 documents frozen) · Phase 4 (Knowledge Integration, all 6 batches + PIR complete) · Phase 5 (Architecture Finalization — Founder signed off this session, 3rd Jul'26) |
| **Current** | Transitioning into Phase 6 (Repository Bootstrap) |
| **Next** | Verify `foofoo-v2` repo structure, confirm Supabase project state, confirm migration folder convention is ready — then issue the first legitimate Claude Code prompt (already drafted in the prior session, now correctly timed) |
| **Remaining** | Phase 6 exit verification → Phase 7 (Seed SQL → Backend → Frontend → Testing → Launch → Growth) |

---

## 6. Repository Bootstrap Framework

**Purpose:** Confirm — not assume — that the implementation foundation is genuinely ready, via one binary test rather than a checklist of assumptions.

**Timing:** Immediately following Phase 5 sign-off. Should take a single session, not a multi-batch process — this is a mechanical verification stage, not a design stage.

**Deliverables:** A short Bootstrap Verification Report confirming each item below, with direct evidence (not "should be fine").

**Folder structure:** Confirm `foofoo-v2` matches the structure already implied by this project's migration numbering convention (`001-020` structural, `100-199` seed, `900-999` validation) — a `supabase/migrations/` directory or equivalent, with rollback pairing enforced.

**Supabase initialization:** Confirm `foofoo-mvp` (the retained production project, per prior memory) is reachable and empty/ready for the frozen schema — not re-created, verified.

**Migration strategy:** Confirmed already fully specified in `DOC-P3-05 Part A v1.2` — Phase 6 applies it, doesn't redesign it.

**Validation strategy:** Confirm the 900-series validation scripts exist and are runnable against a fresh schema load — this is the literal exit-criteria test.

**Developer workflow:** Confirm `CLAUDE.md` exists and states the repo conventions Claude Code needs (per every prior Claude Code prompt in this project referencing it) — if it doesn't exist yet, creating it is itself a Phase 6 deliverable, not a Phase 7 afterthought.

**Claude integration:** Claude.ai continues to hold architecture authority; Phase 6's Claude.ai role is verification, not design.

**Claude Code integration:** This is the phase where Claude Code is first invoked — for scaffolding and verification tasks, not yet for business-logic implementation (that's Phase 7).

---

## 7. Implementation Planning Framework

```
Architecture Freeze (Phase 5, DONE — signed 3rd Jul'26)
        ↓
Repository Bootstrap (Phase 6, NEXT — one verification session)
        ↓
Claude Code first engaged (folder/migration scaffolding only)
        ↓
Seed SQL (Phase 7 sub-stage 1 — load real data, run 900-series validation)
        ↓
Backend (Phase 7 sub-stage 2 — Edge Functions against validated seed data)
        ↓
Frontend (Phase 7 sub-stage 3 — can start in parallel once API contract confirmed stable, no need to wait for Backend code)
        ↓
Testing (Phase 7 sub-stage 4 — full behavioral + integration testing)
        ↓
Launch (Phase 7 sub-stage 5 — gated on AGR-P3-07-001 DPDP resolution + DOC-09/DOC-08 criteria)
```

---

## 8. Execution Gate Model

| Gate | Entry | Exit | Approval | Evidence Required |
|---|---|---|---|---|
| **Architecture Gate** (end of Phase 3) | All 8 Phase 3 documents drafted | Zero unresolved architecture contradictions | Founder, per document | Cross-document consistency check |
| **Knowledge Gate** (end of Phase 4) | All source files batched | Zero orphan lineage, all gaps classified | Founder, PIR sign-off | Lineage Audit (0 broken chains) |
| **Decision Gate** (end of Phase 5) | PIR blockers packaged into approval packs | Founder has signed every remaining schema delta | Founder, explicit sign-off (as happened this session) | Real-data re-verification of every recommendation before ask |
| **Repository Gate** (end of Phase 6) | Architecture Freeze signed | Trivial migration applies and rolls back successfully | Engineering/Founder | Direct test execution, not assumption |
| **Implementation Gate** (within Phase 7, per sub-stage) | Repository Gate passed | Seed Gate targets met; behavioral validation passes | Founder/Engineering | 900-series script pass/fail results |
| **Production Gate** (end of Phase 7) | All sub-stages complete | Launch criteria (DOC-09/DOC-08) met, AGR-P3-07-001 resolved | Founder | Legal/compliance sign-off, load testing evidence |

---

## 9. Project Health — Is APDF vNext Better Than v1?

**Yes, and the phase numbering should change.** Justification:

- v1's Phase 3→4 boundary was the single point where this project's actual experience diverged most sharply from the plan — three real, necessary stages (Knowledge Integration, Architecture Finalization, Repository Bootstrap) had to be invented mid-project because v1 didn't model them. Keeping v1's numbering would mean either mislabeling these as "Phase 3.5" forever (which is literally what happened — note the project's own document naming) or awkwardly cramming them into "Phase 4."
- v1's Phases 4/5/6 (Technical Implementation / Quality & Operations / Growth & Evolution) never got tested against real project experience yet, so there's no evidence forcing a 3-way split there — collapsing them into one Phase 7 with sub-stages matches how implementation phases actually flow in every software project of this shape (sequential, not independently gated).
- The renumbering directly fixes the root cause the Founder named for this session: "Claude repeatedly suggested Claude Code too early because the implementation transition was never explicitly modelled." APDF vNext makes that transition a named, testable gate (Repository Gate) instead of an implicit judgment call.

---

## 10. Recommendations

1. Adopt APDF vNext (this document) as the governing framework for all future FooFoo phases.
2. Retain `APDF_Framework_v1.md` unmodified as historical reference — do not delete or edit it, per the project's own persistence discipline.
3. Immediately proceed to Phase 6 (Repository Bootstrap) as a short, single-session verification pass — not a redesign, not a new governance layer.
4. Do not issue any Claude Code prompt until Phase 6's exit criterion (trivial migration applies and rolls back successfully) is directly demonstrated, not assumed.
5. Treat the already-drafted Claude Code prompt from the prior session as a **Phase 7** artifact — hold it until Phase 6 passes, then reuse it as-is (it doesn't need rewriting, only correct sequencing).

---

## 11. Migration Strategy from Old APDF to APDF vNext

| Old APDF v1 element | APDF vNext treatment |
|---|---|
| Phase 0 (Discovery) | Merged into vNext Phase 1 |
| Phase 1 (Product Definition) | Merged into vNext Phase 1 |
| Phase 2 (User Experience) | Becomes vNext Phase 2, unchanged |
| Phase 3 (Solution Architecture) | Becomes vNext Phase 3, unchanged in content, discipline fully retained |
| "Phase 3.5" (ad hoc, never formally in v1) | Formalized as vNext Phase 4 (Knowledge Integration) |
| (unnamed gap between architecture and implementation) | Formalized as vNext Phase 5 (Architecture Finalization) |
| (unnamed gap before Claude Code) | Formalized as vNext Phase 6 (Repository Bootstrap) |
| Phase 4 (Technical Implementation) | Becomes vNext Phase 7, sub-stage 1–3 |
| Phase 5 (Quality and Operations) | Becomes vNext Phase 7, sub-stage 4 |
| Phase 6 (Growth and Evolution) | Becomes vNext Phase 7, sub-stage 5 (post-launch, iterative) |

**All 33 original documents remain valid and are not renamed or renumbered** — this migration changes the *phase* structure surrounding them, not the documents themselves. `DOC-P3-XX` numbering, `RE-DOC-XX` numbering, and all frozen content are entirely unaffected.

**No document was reopened, redesigned, or reclassified without evidence in producing this reconstruction** — every claim above traces to a specific artifact already in project files (cited inline throughout).

Founder sign-off: _______________________ Date: ___________
