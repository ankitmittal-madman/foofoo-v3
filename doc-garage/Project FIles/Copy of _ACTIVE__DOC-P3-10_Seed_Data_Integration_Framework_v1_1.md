# [ACTIVE]_DOC-P3-10_Seed_Data_Integration_Framework_v1.1

**Document ID:** DOC-P3-10
**Title:** Seed Data Integration Framework — Phase 3.5, Phase 1
**Version:** 1.1
**Approval Status:** APPROVED — ACTIVE — GOVERNING FRAMEWORK
**Date:** 2026-07-02
**Supersedes:** `[ACTIVE]_DOC-P3-10_Seed_Data_Integration_Framework_v1.0` (targeted refinement only — see Revision Notice below; v1.0 retained as superseded reference, not deleted)
**Owner:** Founder (APVerse Labs)
**Prepared By:** Claude (planning/architecture role)
**Governed by:** `[ACTIVE]_DOC-P3-09_Knowledge_Integration_Governance_v1.0` (APPROVED — ACTIVE — GOVERNING DOCUMENT) — unchanged, not reopened by this revision

---

## Revision Notice — v1.0 → v1.1

This is a **targeted execution-governance refinement**, not a redesign. Existing section numbering is preserved unchanged; four additions are inserted as lettered sub-sections at the point most relevant to the material they extend, so nothing already-approved shifts number:

1. **Section 12A — Knowledge Inventory** (new, after Section 12): distinguishes *what files exist* (Source Inventory) from *what business knowledge exists inside them* (Knowledge Inventory).
2. **Section 15A — Canonical ID Governance** (new, after Section 15): introduces stable `CAN-<DOMAIN>-NNN` governance identifiers for the Canonical Knowledge Dictionary.
3. **Section 20A — Transformation Rules Library** (new, after Section 20): introduces a governed `TR-NNN` rule catalogue so provenance records reference a rule ID instead of repeating transformation logic; Section 20's text is lightly amended to point at it.
4. **Section 11A — Phase 2 Boundary Definition** (new, after Section 11): states explicitly what Phase 2 (Knowledge Acquisition) may and may not do, to prevent scope creep into Discovery/Canonicalization/Mapping.

No other section's substance was altered. No architecture, schema, business logic, API, security, Recommendation Engine, or governance philosophy (DOC-P3-09) was touched.

---

## Baseline Re-Verification (performed before this revision)

| Document | Version Confirmed On Disk | Status |
|---|---|---|
| `[ACTIVE]_Project_Baseline_Register` | v1.5 | ACTIVE — no newer version found |
| `[ACTIVE]_Engineering_Handover_Project_Continuity_Package` | v1.3 | ACTIVE — no newer version found |
| `[ACTIVE]_DOC-P3-05_Architecture_Gap_Register` | v1.1 | ACTIVE — LIVING DOCUMENT, IDR-001 still Open |
| `[ACTIVE]_DOC-P3-09_Knowledge_Integration_Governance` | v1.0 | APPROVED — ACTIVE — GOVERNING DOCUMENT — unchanged |
| `[ACTIVE]_DOC-P3-10_Seed_Data_Integration_Framework` | v1.0 | Prior version — now superseded by this v1.1 |

**Confirmed:** DOC-P3-09 remains the sole governing document for Phase 3.5. DOC-P3-10 continues to operationalize it, unchanged in philosophy. All Phase 3 architecture documents remain frozen and immutable and were not consulted for redesign purposes in this revision.

---

## 1. Purpose

Define the complete operational framework by which Phase 3.5 (Knowledge Integration & Seed Data Engineering) will be executed, so that Phase 2 onward can proceed against a pre-agreed process rather than ad hoc decisions made mid-stream.

## 2. Objectives

- Establish a repeatable, auditable process for turning raw Excel knowledge into approved, provenance-tagged seed data.
- Resolve IDR-001 without touching frozen architecture.
- Ensure every subsequent phase (2 through 11, per DOC-P3-09 Section 15) has clear entry/exit criteria before it starts.

## 3. Scope

**In scope:** process design, intake mechanics, canonicalization strategy, mapping strategy, gap handling, QA/validation strategy, rollback strategy, metrics — for the entirety of Phase 3.5.
**Out of scope:** touching any actual knowledge file; performing any mapping; generating any SQL; any architecture, schema, API, security, or RE logic change.

## 4. Success Criteria

- All required sections of this framework are agreed before Phase 2 begins.
- Every later phase in DOC-P3-09 Section 15 has traceable entry/exit criteria defined here.
- Founder can approve this document without needing to infer any undefined process step.

## 5. Inputs

- DOC-P3-09 (governing document, provenance model, confidence framework, execution phases, validation gates — all inherited, not redefined here).
- DOC-P3-04 (frozen schema — the eventual mapping target, referenced only, not touched).
- The Architecture Gap Register (IDR-001 context).

## 6. Outputs

This document itself, plus initial templates referenced within it: Source Inventory Structure (Section 12), Knowledge Inventory (Section 12A), Canonical ID scheme (Section 15A), Transformation Rules Library (Section 20A), Lessons Learned Register template (Section 31), Metrics/Dashboard definitions (Sections 32–33), Artefact Inventory (Section 34) — all templates, no populated content yet.

## 7. Execution Workflow

This framework operationalizes DOC-P3-09 Section 15 (Phases 2–11) as follows, at a process level only:

1. **Intake** (Section 11, bounded per Section 11A) → files logged into Source Inventory (Section 12); business concepts later logged into Knowledge Inventory (Section 12A)
2. **Batching** (Section 14) → files grouped for manageable discovery/canonicalization passes
3. **Discovery** (DOC-P3-09 Phase 3) → per-file findings, no mapping
4. **Canonicalization** (Section 15, with IDs per Section 15A) → Canonical Knowledge Dictionary built incrementally per batch
5. **Mapping** (Section 16, using Transformation Rules per Section 20A) → canonical concepts mapped to frozen schema/domain model
6. **Gap Analysis** (Section 17) → A / B / C1 / C2 / C3 classification
7. **Founder Decision Workflow** (Section 18) for B/C1/C2/C3 items
8. **Mapping Report compiled** → Founder Review gate (hard stop, per DOC-P3-09)
9. **Seed Generation → Validation → Closure**, per DOC-P3-09 Phases 9–11

## 8. Deliverables

Per phase, exactly as listed in DOC-P3-09 Section 09 (Outputs table) — this framework does not redefine that list, only operationalizes how each is produced.

## 9. Required Project Documents

Mandatory reads before any Phase 3.5 work: Project Baseline Register (latest), Engineering Handover (latest), Architecture Gap Register (latest), DOC-P3-09 (governing), DOC-P3-04 (schema target), DOC-P3-02/03/03A (domain model + logic, for mapping context), RE-DOC-01–05 (genome/class/scoring targets).

## 10. Required Research Files

Primary known source: `Indian_Meal_Cohort_Persona_DB_v3.xlsx` (per IDR-001 and Engineering Handover Part 7/9). Any additional Excel files the Founder supplies during Phase 2 are accepted under the same terms (Section 11 of DOC-P3-09) — this framework does not presuppose a closed list.

## 11. Source File Intake Process

1. Founder uploads file(s) as-is — no preprocessing required.
2. Claude logs each file into the Source Inventory (Section 12) immediately on receipt, before any content is read for Discovery.
3. Intake confirms: filename, format, approximate size/sheet count — not content interpretation (that is Discovery, Phase 3).
4. No file is rejected, reformatted, or merged with another at intake. Overlap/contradiction handling happens at Mapping/Gap Analysis, not intake.

## 11A. Phase 2 Boundary Definition *(new in v1.1)*

To prevent scope creep, Phase 2 (Knowledge Acquisition) is explicitly bounded:

**Phase 2 performs ONLY:**
- File intake
- Source Inventory registration (Section 12)
- Storage of the file as supplied
- Integrity verification (file opens correctly, is not corrupted, matches what the Founder describes uploading)

**Phase 2 MUST NOT perform:**
- Interpretation of file content
- Discovery (business domain, entities, concepts — that is Phase 3)
- Canonicalization (that is Phase 4)
- Mapping (that is Phase 5)
- Business analysis of any kind
- Gap analysis (that is Phase 6)
- Assumptions about business facts
- SQL generation of any kind

Any activity beyond the "performs ONLY" list, however small, is treated as a boundary violation and must be logged as such rather than performed quietly. This boundary exists because Phase 3.5's entire discipline (per DOC-P3-09) depends on Discovery, Canonicalization, and Mapping happening as distinct, reviewable steps — collapsing them into intake would defeat the purpose of having separate phases and gates at all.

## 12. Source Inventory Structure

| Field | Description |
|---|---|
| Source ID | Sequential ID (SRC-001, SRC-002, …) |
| Filename | Exact as uploaded |
| Format | .xlsx / .csv / other |
| Intake Date | Date logged |
| Sheet Count | Number of sheets/tabs |
| Approx. Row Count | Per sheet, order of magnitude |
| Status | Intake Logged → Discovered → Canonicalized → Mapped → Archived |
| Notes | Any founder-supplied context about the file's origin or intent |

## 12A. Knowledge Inventory *(new in v1.1)*

The Source Inventory (Section 12) tracks **what files exist**. The Knowledge Inventory tracks **what business knowledge exists inside those files**, once Discovery (Phase 3) has run. These are deliberately separate: a single file can contribute to several knowledge domains, and a single domain can be scattered across several files.

**This is an inventory only — no discovery or interpretation is performed by defining this structure.** It is populated as Phase 3 (Discovery) proceeds, not at framework-approval time.

| Field | Description |
|---|---|
| Knowledge Domain | e.g. Dishes, Ingredients, Personas, Cohorts, Meal Plans, Nutrition, Festivals, Regions, Dietary Rules, Allergens, Tags, or any other domain discovered |
| Source File(s) | Which Source ID(s) (Section 12) contribute to this domain |
| Approx. Concept Count | Rough count of distinct items found for this domain, per file |
| Discovery Status | Not Started → In Progress → Complete |
| Notes | Overlaps, contradictions, or partial-coverage flags noted during Discovery (not resolved here) |

The domain list above is illustrative, not closed — any business domain genuinely found in the source files is added as its own row.

## 13. File Naming Convention

Source files are **never renamed** on intake — the original filename is preserved verbatim in the Source Inventory as the permanent provenance reference. If a corrected/updated version of a file is supplied later, it is logged as a new Source ID with a "Supersedes: SRC-00X" note, following the same never-overwrite discipline used elsewhere in this project (no-column-drop, no silent version replacement).

## 14. Batch Processing Strategy

Files are processed in **Founder-approved batches**, not all at once, to keep each Discovery/Canonicalization/Mapping pass reviewable:

- Batch size: as many files as share a clear business domain (e.g., all cohort/persona files together, all dish/ingredient files together) — domain coherence takes priority over file count.
- Each batch completes Discovery → Canonicalization → Mapping → Gap Analysis before the next batch starts, unless the Founder explicitly approves parallel batches.
- Rationale: prevents an error in one domain's canonicalization from silently propagating into an unrelated domain's mapping before anyone reviews it.

## 15. Canonicalization Strategy

- One canonical entry per real-world business concept (dish, ingredient, cuisine, festival, persona, cohort, meal classification, dietary tag, allergen, regional term), per DOC-P3-09 Phase 4.
- Canonicalization candidates are proposed by Claude with a confidence score (Section 14 of DOC-P3-09); anything below the Medium band (94%) is flagged for Founder review before being entered into the Canonical Knowledge Dictionary.
- The Dictionary is versioned incrementally per batch — never silently overwritten. Each entry retains links to every source variant it consolidates.
- Canonicalization strictly never creates a new schema-level entity — it only groups source labels into one dictionary term for later mapping.

## 15A. Canonical ID Governance *(new in v1.1)*

Every entry in the Canonical Knowledge Dictionary receives a stable **Canonical ID** at the point it is created, using the pattern:

`CAN-<DOMAIN>-NNN`

Examples: `CAN-DISH-001`, `CAN-INGREDIENT-001`, `CAN-PERSONA-001`, `CAN-COHORT-001`, `CAN-FESTIVAL-001`.

**These IDs are governance identifiers only — they are NOT database primary keys** and must never be mistaken for or mapped directly onto a schema-level ID. Their sole purpose is to provide a stable reference usable across Phase 3.5 documentation, mapping reports, provenance records, and validation, so that "the same canonical concept" can be cited consistently without repeating its full definition each time.

Rules:
- Canonical IDs are assigned sequentially per domain and never reused, even if a canonical entry is later found to be a duplicate and merged (the retired ID is marked "Merged into CAN-x" — never deleted or recycled).
- The domain prefix list starts with the illustrative set above and grows as new domains are discovered (Section 12A) — a new domain gets a new prefix, not an overloaded existing one.

## 16. Mapping Strategy

- Every canonical concept (referenced by its Canonical ID, Section 15A) is mapped to one (or explicitly zero) target in: DOC-P3-02 (Conceptual Domain Model), DOC-P3-03/03A (Business Logic), RE-DOC-01–05 (RE inputs), DOC-P3-04 (schema table/column).
- Mapping is 1:1 wherever possible. Where a canonical concept maps to multiple schema locations (e.g., a dietary tag affecting both a `dishes` attribute and a `re_engine` scoring input), all mappings are recorded, not just the first found.
- Zero mappings found → immediately routed to Gap Analysis (Section 17), never left implicit.

## 17. Gap Analysis Strategy

Applies DOC-P3-09 Section 15 / Phase 6 classification exactly:
- **Category A** — perfect mapping, high confidence → auto-loadable.
- **Category B** — architecture supports it, data incomplete → proposed value + confidence, Founder approval required per the confidence band.
- **Category C1** — architecture gap → AGR raised against the specific frozen document.
- **Category C2** — business ambiguity → Founder Decision requested.
- **Category C3** — research conflict (contradicting source files) → Manual Resolution requested, with both conflicting values shown side by side, never auto-picked.

## 18. Founder Decision Workflow

1. Claude surfaces the item (B / C1 / C2 / C3) with full context: source(s), proposed value(s) if any, confidence, and why it needs a decision.
2. Founder responds with one of: Approve / Adjust / Reject / Defer.
3. Decision is recorded in the provenance record (Decision Authority = "Founder") and in the Knowledge Mapping Report.
4. Deferred items are tracked openly in the Gap Analysis output — they do not silently block the rest of the batch unless they are a hard dependency for another mapping.

## 19. AI Decision Workflow

1. Claude may finalize Category A mappings (≥95% confidence, architecture fully supports it) without a per-item Founder round-trip, but all such mappings are still listed in the Knowledge Mapping Report for visibility.
2. Claude may propose (never finalize) Category B values — these always wait for Founder Decision Workflow (Section 18).
3. Claude never resolves Category C items unilaterally under any confidence level — C-items always route to Section 18, without exception.
4. Any point where Claude would need to "assume" a business fact not present in any source file is treated as a Category C2, not as an AI Suggestion — assumptions about facts (as opposed to suggested best-fit mappings) are not permitted.

## 20. Provenance Capture Strategy

Captured at the point of mapping, using the exact 10-field model defined in DOC-P3-09 Section 13 (Original Source File, Sheet, Row, Original Value, Canonical Value, **Transformation Rule ID — per the Transformation Rules Library, Section 20A**, Target Entity, Target Attribute, Confidence Score, Decision Authority). Captured incrementally per batch, not retrofitted at the end — a mapping without a complete provenance record is not considered complete.

## 20A. Transformation Rules Library *(new in v1.1)*

Rather than repeating transformation logic in every provenance record, transformation logic is defined once per rule and referenced by ID:

| Rule ID | Rule Name |
|---|---|
| TR-001 | Whitespace normalization |
| TR-002 | Case normalization |
| TR-003 | Hindi ↔ English synonym mapping |
| TR-004 | Regional naming normalization |
| TR-005 | Plural/Singular normalization |
| TR-006 | Known business synonym merge |

- Every provenance record's "Transformation Rule" field (Section 20 / DOC-P3-09 Section 13) cites a Rule ID from this library rather than restating the rule's logic.
- If a transformation genuinely does not fit any existing rule, a new Rule ID is proposed (next sequential `TR-NNN`) with a plain-language description — it is added to this library, not invented ad hoc inside a single provenance record.
- This library is additive-only: existing Rule IDs are never redefined once used in a provenance record, to preserve historical traceability. A correction to a rule's definition is filed as a new Rule ID with a note superseding the old one for future use, exactly as source files are versioned (Section 13).

## 21. Quality Assurance Strategy

- Every batch's Canonicalization output is spot-checked against its source files before Mapping begins (sample-based, not exhaustive, given data-first discipline already governs deeper checks downstream).
- Every Category A auto-mapping is still listed for Founder visibility (Section 19.1) — QA is never fully silent even where approval isn't required.
- Cross-batch consistency check before Phase 7 report compilation: no canonical concept should have been defined two different ways across two batches.

## 22. Validation Strategy

Reuses, does not reinvent, the existing project validation assets:
- Three mandatory safety gates (diet violations, never-list violations, Jain violations — must return 0 rows), per standing project practice.
- Existing scripts `901_behavioral_trigger_validation.sql`, `902_behavioral_safety_gates.sql`, `903_behavioral_rls_validation.sql`, `904_behavioral_config_and_smoke_test.sql`, and `900_structural_validation.sql` are re-run against seeded data at DOC-P3-09 Phase 10 — no new validation scripts are authored unless a genuine coverage gap is found (which would itself be an AGR against DOC-P3-05, not a Phase 3.5 decision).

## 23. Rollback Strategy

- Seed migrations follow the existing `NNN_description.sql` numbering convention — a failed or rejected seed batch is rolled back by not advancing the migration sequence past its number, never by editing an already-applied file in place.
- `foofoo-staging` (currently deleted, to be recreated per standing project state) is the required environment for all Phase 3.5 seed loading and validation — production (`foofoo-mvp`) is never touched during Phase 3.5.
- If validation (Section 22) fails after loading, the affected seed migration file(s) are reverted via a new down-migration, not a manual data delete — preserving the audit trail.

## 24. Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Source files conflict on core cohort/persona definitions | Medium | High | Category C3 routing — no silent resolution |
| Canonicalization drifts across batches (same concept, two dictionary entries) | Medium | Medium | Cross-batch consistency check (Section 21) before Phase 7; Canonical IDs (Section 15A) make duplicates easier to spot |
| Founder approval backlog stalls Phase 3.5 | Medium | Medium | Batching (Section 14) limits size of any single approval round-trip |
| Seed generation deviates from frozen DOC-P3-04 column names/types | Low | High | Phase 9 generation only from Phase 8-approved mapping, cross-checked literally against DOC-P3-04 v1.3 |
| `foofoo-staging` not yet recreated when Phase 9 arrives | Medium | Low | Flagged now; recreation is a pre-Phase-9 checkpoint, not a Phase 3.5 blocker today |
| Phase 2 scope creep into Discovery/Mapping | Low (newly mitigated) | Medium | Explicit Phase 2 Boundary Definition (Section 11A) |

## 25. Issue Classification

Reuses the project's existing four-type classification, now supplemented by DOC-P3-09's C1/C2/C3 sub-typing for Category C specifically:
- **IDR** — Issue/Data Request (e.g., IDR-001 itself)
- **DCR** — Document Correction Request
- **AGR** — Architecture Gap Report (= Category C1)
- **SER** — Schema Evolution Request
- Category C2 (Business Ambiguity) and C3 (Research Conflict) are Phase-3.5-specific sub-types that resolve via Founder Decision, not via a formal architecture-change artifact.

## 26. Checkpoints

Identical to the Validation Gates already defined in DOC-P3-09 (Gate 1→2 through Gate 11→Closure) — this framework does not add new checkpoints, it confirms those gates will be operated exactly as specified there.

## 27. Entry Criteria for Each Subsequent Phase

| Phase | Entry Criteria |
|---|---|
| 2 (Acquisition) | This framework approved by Founder; Phase 2 Boundary Definition (Section 11A) understood and respected |
| 3 (Discovery) | At least one file batch fully intake-logged (Section 11–12) |
| 4 (Canonicalization) | Discovery findings complete for the batch in progress; Knowledge Inventory (Section 12A) populated for that batch |
| 5 (Mapping) | Canonical Knowledge Dictionary entries (with Canonical IDs, Section 15A) exist for the batch's concepts |
| 6 (Gap Analysis) | Every canonical concept in the batch has a mapping outcome (found or not found) |
| 7 (Mapping Report) | Every Gap Analysis record has a classification (A/B/C1/C2/C3) |
| 8 (Founder Review) | Mapping Report compiled and complete |
| 9 (Seed Generation) | Founder approval received at Gate 7→8 |
| 10 (Validation) | Seed artifacts generated from approved mapping only |
| 11 (Closure) | Validation passed (all safety gates 0 rows, FK/constraint/trigger/RE checks pass) |

## 28. Exit Criteria for Each Subsequent Phase

Mirrors Section 27 one phase ahead — i.e., a phase's exit criteria are the next phase's entry criteria, per DOC-P3-09's Validation Gates table (already the authoritative source; not duplicated in full here to avoid two documents diverging over time).

## 29. Deliverable Acceptance Criteria

A deliverable (per Section 8/DOC-P3-09 Section 09) is accepted only if: (a) it matches its defined output type exactly, (b) every value in it carries provenance where applicable (Section 20, citing a Transformation Rule ID per Section 20A), (c) it has been through the QA check for its phase (Section 21), and (d) any C-category item it contains has a recorded routing, not a silent gap.

## 30. Completion Criteria

Phase 3.5 is complete when all Section 27–28 phases have cleared their exit criteria through Phase 11, IDR-001 is closed, and the Phase 3.5 Completion Report (DOC-P3-09 Phase 11 output) is signed off by the Founder.

## 31. Lessons Learned Register (initial template)

| Date | Phase | Observation | Action Taken / Recommended |
|---|---|---|---|
| 2026-07-02 | Framework (v1.0→v1.1) | Governance gaps found before execution began: no distinction between file-level and knowledge-level inventory; no stable reference IDs for canonical concepts or transformation logic; Phase 2 boundary not explicit | Addressed via Sections 12A, 15A, 20A, 11A in this revision, before any data was processed |

## 32. Metrics Collected Throughout Phase 3.5

- Files processed / total files logged
- Canonical concepts identified per domain (tracked by Canonical ID, Section 15A)
- Mapping outcome distribution (A / B / C1 / C2 / C3 counts and %)
- Founder decision turnaround time per item
- Provenance completeness rate (% of seed values with all 10 fields populated, including a valid Transformation Rule ID)
- Transformation Rule usage frequency (which TR-IDs are most common, and how often a new one is proposed)
- Safety gate pass/fail count per validation run

## 33. Phase 3.5 Dashboard (planned metrics only)

A simple running table (not a live tool) tracked across sessions:

| Metric | Value |
|---|---|
| Batches completed | 0 |
| Files intake-logged | 0 |
| Knowledge domains identified | 0 |
| Canonical concepts defined | 0 |
| Transformation Rules in library | 6 (TR-001–TR-006, initial set) |
| Category A / B / C1 / C2 / C3 counts | 0 / 0 / 0 / 0 / 0 |
| Open Founder Decisions | 0 |
| Safety gates passing | Not yet run |

## 34. Phase 3.5 Artefact Inventory

| Artefact | Status |
|---|---|
| DOC-P3-09 (Governance) | Approved — Active |
| This Framework (DOC-P3-10 v1.1) | Approved — Active — Governing Framework |
| Source Inventory | Not yet created (Phase 2) |
| Knowledge Inventory | Not yet created (Phase 3) |
| Canonical Knowledge Dictionary (with Canonical IDs) | Not yet created (Phase 4) |
| Transformation Rules Library | Initialized with TR-001–TR-006; grows as needed |
| Knowledge Mapping Report | Not yet created (Phase 7) |
| Seed migration files | Not yet created (Phase 9) |
| Phase 3.5 Completion Report | Not yet created (Phase 11) |

## 35. Cross-document Traceability

This framework traces to: DOC-P3-09 (governing rules), DOC-P3-04 (schema target), DOC-P3-02/03/03A (domain/logic targets), RE-DOC-01–05 (RE targets), Architecture Gap Register (IDR-001 origin). Canonical IDs (Section 15A) and Transformation Rule IDs (Section 20A) are new traceability aids layered on top of the provenance model already defined in DOC-P3-09 Section 13 — they do not replace or alter that model, they make it easier to reference consistently.

## 36. Regression Review

- ✅ No architecture changed
- ✅ No schema changed
- ✅ No API changed
- ✅ No Recommendation Engine logic changed
- ✅ No Security Architecture changed
- ✅ No governance philosophy changed — DOC-P3-09 not reopened, reinterpreted, or modified
- ✅ No SQL generated
- ✅ No knowledge file ingested, read, or analyzed
- ✅ No mapping performed
- ✅ Existing section numbering preserved; all four additions are lettered sub-sections, not renumbers

**Only execution governance was strengthened.**

---

## Completion

### 1. Revision Summary
v1.1 adds four targeted governance strengtheners ahead of Phase 2: Knowledge Inventory (12A), Canonical ID Governance (15A), Transformation Rules Library (20A), and an explicit Phase 2 Boundary Definition (11A). No other section's substance changed. Document status updated to APPROVED — ACTIVE — GOVERNING FRAMEWORK, intentionally not FROZEN, since execution governance may continue to evolve through controlled versioning during Phase 3.5 as genuine improvements are found.

### 2. Regression Summary
All regression checks pass (Section 36). No architecture, schema, business logic, API, security, Recommendation Engine, or governance-philosophy change occurred at any point in this revision.

### 3. Readiness Assessment
Framework is strengthened and complete. All entry/exit criteria (Sections 27–28) now reflect the new artefacts (Knowledge Inventory, Canonical IDs, Transformation Rules) at the points where they first become relevant.

### 4. Recommendation
**Proceed directly to Phase 3.5 – Phase 2 (Knowledge Acquisition)**, bounded strictly per Section 11A.

Founder sign-off: _______________________ Date: ___________

---

**Phase 2 is not started. Awaiting Founder instruction.**
