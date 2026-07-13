# Phase 3.5 — Batch 1 — Stage 4: Gap Analysis
## Consolidated Deliverable Set v1.1

**Governed by:** `[ACTIVE]_DOC-P3-09_Knowledge_Integration_Governance_v1.0`, `[ACTIVE]_DOC-P3-10_Seed_Data_Integration_Framework_v1.1`
**Execution audit trail:** `[ACTIVE]_DOC-P3-11_Discovery_Execution_Register_v1.7`
**Inputs (frozen, immutable, used read-only):** `Batch1_Discovery_Report_v1.1` (FROZEN), `Batch1_Canonicalization_Package_v1.1` (FROZEN), `Batch1_Mapping_Package_v1.1` (FROZEN), `DOC-P3-04_Data_Architecture_ERD_v1.3`
**Supersedes:** `Batch1_GapAnalysis_Package_v1.0` (not modified — retained as superseded reference)
**Scope:** Governance refinement only. No classification, GAP ID, evidence, ownership, or priority changed.
**Date:** 2026-07-02
**Status:** APPROVED — ACTIVE — FROZEN

**Revision Notice (v1.0 → v1.1) — governance enhancement only:**
1. New **Section 4A — Gap Resolution Matrix**
2. New **Section 4B — Gap Dependency Graph**
3. New **Section 4C — Resolution Order (Execution Waves)**
4. New **Section 4D — Gap Closure Criteria (permanent lifecycle)**
5. New **Section 4E — Executive Traceability Dashboard**
6. New **Section 4F — Structural vs. Semantic Gap View**
7. New **Section 4G — Batch Independence Confirmation**
8. New **Section 4H — Gap Statistics Dashboard**
9. New **Section 4I — Permanent Gap Resolution Rule**
10. New **Section 4J — Why Category C2 = 0**
11. **Wording precision pass:** "Architecture inconsistency" language is now reserved for the 2 GAPs where evidence genuinely proves a hard contradiction (GAP-004, GAP-007 — both demonstrated against real data: 12-vs-3 column mismatch against frozen business rules, and 22 literally unseedable rows against a CHECK constraint). The remaining 11 Category C3 GAPs (005, 006, 009, 010, 012, 015, 018, 019, 020, 022, 023) are reworded to **"canonical information currently has no persistence location in the frozen schema"** — a more precise description of what the evidence actually shows for those items. **No classification changed** — all 11 remain Category C3; only the descriptive language changed.
12. This document is now **FROZEN** — v1.0 retained unmodified as superseded reference.

**Nothing in Sections 1–3 changed in substance.** Section 4's Detailed GAP Register retains every original Category, Confidence, Owner, and Priority exactly as v1.0 — only the "Why This Evidence Supports the Classification" and "Recommended Next Governance Path" prose was refined per item 11 above, and even then only for the 11 GAPs named.

---

## 1. Executive Summary

All 23 Mapping Issues carried forward from `Batch1_Mapping_Package_v1.1` were independently evaluated against the Permanent Evidence Rule (DOC-P3-11 §26C): a classification was only assigned where existing evidence supports it; where no qualifying evidence exists, the issue is classified but explicitly flagged as requiring further evidence before it can move toward closure.

**Result:** 1 Category A, 6 Category B, 3 Category C1, 0 Category C2, 13 Category C3. The dominant pattern is **Category C3 (Architecture inconsistency)** — the frozen `re_engine` reference tables (DOC-P3-04 §03.27) are consistently narrower than the canonical business knowledge extracted from `Indian_Meal_Cohort_Persona_DB_v3.xlsx`, across Meal Class, Persona, State, Cohort, Weekly Plan, Household Addon, NonVeg Logic, and City Migration Overlay alike. No single table is an isolated anomaly — this is a structural pattern worth Founder attention as a whole.

**No issue was closed.** Six issues remain open specifically because no admissible evidence (per §26C) exists yet to classify their eventual resolution path with confidence — they are classified by *type* of inconsistency, not resolved.

---

## 2. Gap Analysis Methodology

1. Each MI's original evidence (from `Batch1_Mapping_Package_v1.1` §5) was re-read in full.
2. Each MI was tested against the Permanent Evidence Rule (§26C) — classification proceeds only where evidence exists; where it doesn't, the issue is classified by its apparent type but flagged as evidence-pending.
3. Category definitions applied exactly as instructed:
   - **A** — No Gap; mapping clarification only (the frozen architecture already supports it; no decision needed)
   - **B** — Business/Founder Decision required (a product/business choice, not an architecture defect)
   - **C1** — Documentation inconsistency (the frozen document is unclear or silent, not wrong)
   - **C2** — Implementation inconsistency (migration/SQL vs. design document mismatch — none found this batch, since no seed SQL yet exists to be inconsistent with)
   - **C3** — Architecture inconsistency (the frozen schema itself does not accommodate documented, evidenced canonical business knowledge)
4. No redesign was proposed. No SQL was written. No issue was merged or renumbered.

---

## 3. Classification Matrix

| MI ID | One-line Issue | Category | Confidence | Owner (§8) | Priority (§7) |
|---|---|---|---|---|---|
| MI-001 | `dish_id` UUID depends on Batch 4 | **A** | High | Cross Batch | Low |
| MI-002 | `re_cohorts.diet_mode` value format unconfirmed | **B** | Medium | Founder | Medium |
| MI-003 | `re_cohorts.prior_weight` has no canonical source | **B** | Medium | Founder | Low |
| MI-004 | Weekly Plan: 12 ranked values vs. 3 schema columns, no snack | **C3** | High | Architecture | Critical |
| MI-005 | Household Addon: missing day/slot/attached-class columns | **C3** | High | Architecture | High |
| MI-006 | NonVeg Logic: 6 counts vs. 1 schema column | **C3** | High | Architecture | High |
| MI-007 | `slot` CHECK constraint has no `snack` value | **C3** | High | Architecture | Critical |
| MI-008 | MC5 label does not match `MC_PG_HOSTEL` | **B** | High | Founder | Medium |
| MI-009 | City Tier has no column anywhere | **C3** | Medium | Architecture | Medium |
| MI-010 | Class Family Code has no column | **C3** | Medium | Architecture | Low |
| MI-011 | `re_states.region` expected value domain unconfirmed | **C1** | Medium | Documentation | Low |
| MI-012 | Sub-Cohort→Persona relationship has no FK anywhere | **C3** | High | Architecture | High |
| MI-013 | `persona_code` convention unconfirmed | **C1** | Medium | Documentation | Medium |
| MI-014 | `is_primary_candidate`/`base_score` have no source | **B** | Medium | Founder | High |
| MI-015 | 3 canonical weights vs. 1 schema column | **C3** | High | Architecture | High |
| MI-016 | `suitability_rank` has no source | **B** | Medium | Founder | Medium |
| MI-017 | Onboarding-copy attributes have no column | **C1** | Low-Medium | Documentation | Low |
| MI-018 | 13 Persona behavioral attributes have no column | **C3** | High | Architecture | High |
| MI-019 | 5 State/UT attributes have no column | **C3** | High | Architecture | Medium |
| MI-020 | Add-on/City-overlay descriptive attributes have no column | **C3** | Medium | Architecture | Low |
| MI-021 | Routing Rule attributes partially unmapped | **B** | Medium | Founder | Medium |
| MI-022 | 8 Meal Class descriptive attributes have no column (incl. no name column at all) | **C3** | High | Architecture | High |
| MI-023 | Cohort descriptive attributes have no column | **C3** | Medium | Architecture | Low |

---

## 4. Detailed GAP Register

*(One register entry per MI. Every `GAP-*` ID permanently references its originating `MAP-*` ID(s), per DOC-P3-11 §26B.)*

| GAP ID | Originating MAP ID(s) | MI Reference | Category | Evidence Reviewed | Why This Evidence Supports the Classification | Confidence | Impact Area(s) | Recommended Next Governance Path |
|---|---|---|---|---|---|---|---|---|
| GAP-001 | MAP-ENT-008, 009, 011 | MI-001 | A | DOC-P3-11 §04 (Batch Independence Rule) — approved project documentation | The rule already establishes the correct handling (defer, never merge automatically); no further decision is needed, this is a correctly sequenced dependency, not an open question | High | Seed Generation (blocks until Batch 4) | No action needed now — re-surface as a Cross-Batch Conflict when Batch 4 canonicalizes `dishes.xlsx` |
| GAP-002 | MAP-VOC-008, MAP-ENT-012 | MI-002 | B | `re_cohorts` DDL (frozen); Persona `nonveg_mode` full data (12 values) | No frozen document specifies `diet_mode`'s expected value domain; only the Founder (or whoever owns RE-DOC's diet-mode semantics) can supply it | Medium | Seed Generation, Recommendation Engine | Founder Decision — supply or approve the `nonveg_mode → diet_mode` transformation rule |
| GAP-003 | MAP-ENT-012 | MI-003 | B | `re_cohorts` DDL (`DEFAULT 1.0`); full-column check of `Cohort_Matrix_v3` (no weight column found) | The schema's own default may be sufficient, but no approved documentation confirms this is intentional rather than an oversight | Medium | Seed Generation | Founder Decision — confirm whether `DEFAULT 1.0` is intentional for all rows or whether a real weight is expected |
| GAP-004 | MAP-ENT-013, MAP-REL-006 | MI-004 | C3 | `re_weekly_class_plans` DDL (3 columns, no rank); `Weekly_Class_Plan_v3` full attribute list (12 columns, 3-tier rank, 4 slots) — both frozen/canonical sources | The frozen schema (DOC-P3-04, itself an architecture document) structurally cannot represent the full canonical business rule already evidenced (BR2, BR4) — this is an inconsistency between two frozen artefacts, not a business choice | High | Seed Generation, Runtime, Architecture, Recommendation Engine | Founder Decision first, on whether reduced fidelity is intentional; if not, SER consideration (see §10) |
| GAP-005 | MAP-ENT-014, MAP-REL-007/008 | MI-005 | C3 | `re_household_addon_plans` DDL (4 columns); `Household_Addon_Component_Plan` full attribute list (15 columns, including day/slot) | The canonical day/slot/attached-class information currently has no persistence location in the frozen schema — the evidence shows an absence, not a proven contradiction (the exact 7,992-row match suggests the schema's coarser grain may be intentional) | High | Seed Generation, Runtime | Founder Decision first; SER consideration if evidence supports |
| GAP-006 | MAP-ENT-015 | MI-006 | C3 | `re_nonveg_logic` DDL (2 columns); NonVeg Logic full attribute list (6 named counts + notes) | The 6 canonical weekly-count values currently have no persistence location beyond the single `weekly_nonveg_slots` column — an absence of structure, not a demonstrated contradiction | High | Seed Generation, Recommendation Engine | Founder Decision first; SER consideration if evidence supports |
| GAP-007 | MAP-VOC-003/004 | MI-007 | C3 | `re_meal_classes.slot` CHECK constraint (4 values, no `snack`); full-column tally (22/131 rows are Snack-slot) | Directly demonstrable: 22 real, evidenced rows cannot be inserted into this column as it stands — an architecture inconsistency, not a data-quality issue | High | Seed Generation, Runtime, Architecture, API | Founder Decision first, per the refined MI-007 wording; SER consideration if evidence supports |
| GAP-008 | MAP-VOC-005 | MI-008 | B | `re_main_cohorts` DDL comment (5 example codes); `Main_Cohort_Hierarchy` full label data | This is not an architecture defect — the column and its 5-value shape are fine; only the specific *value* for MC5 is unknown, which only the Founder or the schema's original author can supply | High | Seed Generation | Founder Decision — supply or confirm MC5's correct `cohort_code` |
| GAP-009 | MAP-VOC-006 | MI-009 | C3 | Full DDL review, all 15 target tables — no tier-related column found anywhere | City Tier is canonical, evidenced data (CAN-VOC-006/007) that currently has no persistence location among the 15 reviewed tables — this describes an absence within the reviewed scope, not a proven architectural contradiction | Medium — it remains possible this belongs to `public.profiles`, outside this batch's 15-table review scope | Runtime, Architecture | Route to Architecture owner to confirm whether `public.profiles` (out of Batch 1's Mapping scope) is the intended home; if not, SER consideration |
| GAP-010 | MAP-VOC-007 | MI-010 | C3 | Full DDL review of `re_meal_classes` — no family/grouping column | Class Family Code currently has no persistence location in the reviewed schema — an absence, not a demonstrated contradiction; same reasoning as GAP-009 | Medium | Architecture, Recommendation Engine | Confirm with Architecture owner whether Class Family Code is needed by any RE-DOC logical function; if yes, SER consideration |
| GAP-011 | MAP-VOC-010 | MI-011 | C1 | `re_states.region text`, no CHECK, no comment | The column exists — this is a documentation gap (DOC-P3-04 doesn't state the expected value domain), not a missing column | Medium | Seed Generation | Documentation owner to clarify intended `region` value domain in DOC-P3-04 or a companion document, or Founder to confirm |
| GAP-012 | MAP-REL-002 | MI-012 | C3 | `re_subcohorts` DDL (no persona reference column); `Subcohort_Routing.maps_to_persona_id`, the entire functional point of the routing sheet | A canonical, evidenced, functionally-central relationship currently has no persistence location anywhere in the frozen schema — this is a notable structural absence, potentially affecting BUILD-02, though not a demonstrated data-level contradiction the way GAP-004/GAP-007 are | High | Architecture, API, Runtime | Architecture owner review, referencing Engineering Handover's BUILD-02 requirement; SER consideration if confirmed |
| GAP-013 | MAP-ENT-003 | MI-013 | C1 | `re_personas.persona_code` (UNIQUE text, no example given) | The column exists and is unambiguous in structure — only its intended *value convention* is undocumented | Medium | Seed Generation | Documentation owner or Founder to confirm intended `persona_code` convention |
| GAP-014 | MAP-RULE-004 | MI-014 | B | `re_class_dish_options` DDL (`base_score real NOT NULL`, `is_primary_candidate boolean`); full `Class_Dish_Options_v3` attribute list (no score column) | `is_primary_candidate` has a plausible derivation (from `class_use_scope_v3`), but `base_score` is a scoring/ranking methodology question — inherently a product decision, not an architecture defect | Medium | Seed Generation, Recommendation Engine | Founder/Product Decision — define or approve the `base_score` methodology; confirm `is_primary_candidate` derivation rule |
| GAP-015 | MAP-RULE-005 | MI-015 | C3 | `re_city_migration_overlays.city_overlay_weight` (1 column); `City_Migration_Overlay_v3` (3 named weights, explicitly used per BR8) | The 3 canonical named weights currently have no separate persistence location — they collapse into 1 column with no documented combination formula; this is an absence of structure/documentation, not a proven contradiction, since a single combined weight may have been the intended design | High | Runtime, Recommendation Engine | Founder Decision first, on whether a combination formula exists or is needed; SER consideration if evidence supports |
| GAP-016 | (attribute-level, MAP-ENT-011) | MI-016 | B | `re_addon_dish_options.suitability_rank smallint NOT NULL`; `Addon_Dish_Options` full attribute list (no rank column) | Same reasoning as GAP-014's `base_score` — a ranking-methodology product decision | Medium | Seed Generation, Recommendation Engine | Founder/Product Decision — define or approve the ranking methodology |
| GAP-017 | MAP-ENT-001/002 | MI-017 | C1 | `re_main_cohorts`/`re_subcohorts` DDL (no copy columns); 6 onboarding-copy canonical attributes | No frozen document confirms where onboarding UI copy is meant to live — plausibly a config file per established project practice, but that practice is not itself a frozen document reviewed in this stage, so it cannot be cited as qualifying evidence under §26C | Low-Medium | UI, Knowledge Quality | Documentation owner to confirm intended storage location for onboarding copy (DB column vs. app config) |
| GAP-018 | MAP-ENT-003 | MI-018 | C3 | `re_personas` DDL (6 columns); canonical Persona (23 attributes) | This canonical behavioral detail currently has no persistence location in the seed-reference table — a structural absence, not a proven contradiction, since the detail may be intentionally scoped to Discovery-time context only | High | Recommendation Engine, Runtime, Architecture | Architecture owner review — determine whether this detail is needed by any RE-DOC logical function or is intentionally Discovery-only context |
| GAP-019 | MAP-ENT-005 | MI-019 | C3 | `re_states` DDL (3 columns); canonical State/UT (13 attributes) | Same reasoning as GAP-018 — no persistence location currently exists for this canonical detail | High | Recommendation Engine, Runtime | Same as GAP-018 |
| GAP-020 | MAP-ENT-006, MAP-ENT-010 | MI-020 | C3 | `re_city_migration_overlays`/`re_addon_classes` DDL; canonical attribute lists | Same reasoning as GAP-018 | Medium | Recommendation Engine, UI | Same as GAP-018 |
| GAP-021 | MAP-ENT-004 | MI-021 | B | `re_routing_rules` DDL (5 columns); canonical Routing Rule (5 attributes, partial name overlap) | Whether `trigger_answer`/`show_question_key` are the intended targets for `shown_when`/`maps_to_fields` is a product/onboarding-flow-owner confirmation, not an architecture defect (the columns plausibly exist for this exact purpose) | Medium | UI, Runtime | Founder/BUILD-02 owner Decision — confirm column-to-attribute correspondence |
| GAP-022 | MAP-ENT-007 | MI-022 | C3 | `re_meal_classes` DDL (10 columns, no display name); canonical Meal Class (16 attributes) | Notably, no human-readable name column exists at all for the primary taxonomy table — this canonical detail currently has no persistence location; whether that absence is a genuine problem depends on whether the app needs a name beyond `class_code`, which is not yet evidenced either way | High | UI, Runtime, Architecture | Architecture owner review — confirm whether `class_code` alone suffices for the app or a name column is a genuine gap |
| GAP-023 | MAP-ENT-012 | MI-023 | C3 | `re_cohorts` DDL (5 columns); canonical Cohort (9 attributes) | Same reasoning as GAP-018 | Medium | Recommendation Engine | Same as GAP-018 |

**23 GAP entries. Every one references its originating MAP ID(s). None closed. None merged. None renumbered.**

---

## 4A. Gap Resolution Matrix *(new in v1.1)*

| GAP ID | Current Status | Required Resolution Type | Owner | Next Governance Step | Final Resolution Target |
|---|---|---|---|---|---|
| GAP-001 | Open (correctly sequenced) | Cross Batch | Cross Batch | Re-surface at Batch 4 | Cross-Batch Resolution |
| GAP-002 | Open | Founder Decision | Founder | Supply/approve transformation rule | Founder Decision |
| GAP-003 | Open | Founder Decision | Founder | Confirm default sufficiency | Founder Decision |
| GAP-004 | Open | Founder Decision → Potential AGR | Founder | Founder review, then Architecture | Potential AGR |
| GAP-005 | Open | Founder Decision → Potential SER | Founder | Founder review, then Architecture | Potential SER |
| GAP-006 | Open | Founder Decision → Potential SER | Founder | Founder review, then Architecture | Potential SER |
| GAP-007 | Open | Founder Decision → Potential AGR | Founder | Founder review, then Architecture | Potential AGR |
| GAP-008 | Open | Founder Decision | Founder | Supply MC5 code | Founder Decision |
| GAP-009 | Open | Documentation Update / Potential SER | Architecture | Confirm `public.profiles` scope | Documentation Update (likely) |
| GAP-010 | Open | Documentation Update / Potential SER | Architecture | Confirm RE-DOC need | Documentation Update (likely) |
| GAP-011 | Open | Documentation Update | Documentation | Clarify `region` value domain | Documentation Update |
| GAP-012 | Open | Potential SER / Potential AGR | Architecture | Review against BUILD-02 | Potential SER |
| GAP-013 | Open | Documentation Update | Documentation | Clarify `persona_code` convention | Documentation Update |
| GAP-014 | Open | Founder Decision | Founder | Define scoring methodology | Founder Decision |
| GAP-015 | Open | Founder Decision → Potential SER | Founder | Founder review, then Architecture | Potential SER |
| GAP-016 | Open | Founder Decision | Founder | Define ranking methodology | Founder Decision |
| GAP-017 | Open | Documentation Update | Documentation | Confirm UI-copy storage location | Documentation Update |
| GAP-018 | Open | Documentation Update / Potential SER | Architecture | Confirm RE-DOC need | No Action (likely) |
| GAP-019 | Open | Documentation Update / Potential SER | Architecture | Confirm RE-DOC need | No Action (likely) |
| GAP-020 | Open | Documentation Update / Potential SER | Architecture | Confirm RE-DOC need | No Action (likely) |
| GAP-021 | Open | Founder Decision | Founder | Confirm column correspondence | Founder Decision |
| GAP-022 | Open | Documentation Update / Potential SER | Architecture | Confirm name-column need | Potential SER (possible) |
| GAP-023 | Open | Documentation Update / Potential SER | Architecture | Confirm RE-DOC need | No Action (likely) |

**No GAP disappears. All 23 remain listed, each with a distinct current status and target — including the several marked "No Action (likely)," which remain open findings, not closures, until Architecture actually confirms no action is needed.**

---

## 4B. Gap Dependency Graph *(new in v1.1 — dependency only, not resolution)*

```
GAP-004 (Weekly Plan structure)
   │
   ▼
GAP-005 (Household Addon grain) ── shares the same "plan-grain" root cause
   │
   ▼
GAP-015 (City Overlay weighting) ── consumed downstream of weekly plan generation

GAP-007 (slot CHECK constraint)
   │
   ▼
Meal Classes (re_meal_classes, GAP-022 descriptive gap on the same table)
   │
   ▼
Weekly Plans (GAP-004 — meal classes feed directly into weekly plan class codes)
   │
   ▼
Recommendation Engine (GAP-006, GAP-014, GAP-015, GAP-016 — all RE-scoring-adjacent gaps depend on clean meal-class and weekly-plan data first)

GAP-012 (Sub-Cohort→Persona relationship)
   │
   ▼
Onboarding / BUILD-02 (independent of the Meal-Class chain above — a separate dependency thread)

GAP-002, GAP-003 (Cohort diet_mode / prior_weight)
   │
   ▼
GAP-014, GAP-016 (RE scoring — cohort-level fields feed into dish-level scoring, so ambiguity compounds downstream)
```

**This graph shows sequencing dependency only — it does not resolve, merge, or prioritize any GAP; that is done separately in §4C (Resolution Order) and §7 (Priority Matrix).**

---

## 4C. Resolution Order — Recommended Execution Waves *(new in v1.1)*

| Wave | GAPs | Rationale |
|---|---|---|
| **Wave 1 — Critical Architecture** | GAP-004, GAP-007 | These block the core weekly-planning pipeline with demonstrated, evidenced contradictions. Resolving architecture questions first prevents every downstream wave from building on an unstable foundation — per the dependency graph (§4B), GAP-007 feeds directly into GAP-004's chain. |
| **Wave 2 — Founder Decisions** | GAP-002, GAP-003, GAP-005, GAP-006, GAP-008, GAP-014, GAP-015, GAP-016, GAP-021 | Once the Wave 1 architecture questions are answered, the remaining Founder Decisions can be resolved in parallel — none of them block each other, and resolving them together avoids repeated back-and-forth Founder review rounds. |
| **Wave 3 — Documentation** | GAP-011, GAP-013, GAP-017 | Pure documentation clarifications carry no architectural risk and can be resolved independently of Waves 1–2, but are sequenced after them so any Wave-1/2 outcome that touches the same tables doesn't require re-clarifying documentation twice. |
| **Wave 4 — Cross Batch / Architecture Confirmation** | GAP-001, GAP-009, GAP-010, GAP-012, GAP-018, GAP-019, GAP-020, GAP-022, GAP-023 | GAP-001 genuinely cannot resolve before Batch 4. The remaining Architecture-confirmation items (whether orphaned attributes are needed by any RE-DOC function) are lowest urgency — confirming "no action needed" is cheaper to do last, once Waves 1–3 may have already changed what's needed. |

**Why this order minimizes project risk:** resolving unstable architecture (Wave 1) before Founder Decisions (Wave 2) prevents a Founder from deciding a seed value for a column that might not exist in its current form once GAP-004/GAP-007 are settled. Documentation (Wave 3) is cheap and low-risk but sequenced after substantive decisions so it doesn't need revisiting. Cross-Batch and open-ended Architecture confirmations (Wave 4) are last because they are the least time-sensitive and, in GAP-001's case, are gated by a different batch entirely.

---

## 4D. Gap Closure Criteria — Permanent Lifecycle *(new in v1.1, permanent)*

```
OPEN
  │
  ▼
Evidence Added   (per the Permanent Evidence Rule, DOC-P3-11 §26C)
  │
  ▼
Founder Approval
  │
  ▼
Resolution
  │
  ▼
Frozen
```

**GAP records themselves are never edited after freezing.** When a GAP moves toward resolution, a **Resolution Record** is appended (new content, referencing the original `GAP-*` ID) — the original register entry in §4 is never rewritten in place. This mirrors the Canonical ID Governance (`Batch1_Canonicalization_Package_v1.1` §11) and Permanent MAP ID Governance (`Batch1_Mapping_Package_v1.1` §6E) patterns exactly, extended one link further down the lineage chain.

---

## 4E. Executive Traceability Dashboard *(new in v1.1)*

```
23 Mapping Issues (MI)
        │
        ▼
23 GAPs (100% classified, 0 lost)
        │
        ├──► 1 Category A   ( 4.3%)  — No Gap
        ├──► 6 Category B   (26.1%)  — Founder Decision
        ├──► 3 Category C1  (13.0%)  — Documentation
        ├──► 0 Category C2  ( 0.0%)  — Implementation
        └──► 13 Category C3 (56.5%)  — Structural (2 proven "architecture inconsistency"; 11 "no persistence location")
        │
        ▼
11 Founder-owned · 12 Architecture-touched · 3 Documentation-owned · 1 Cross-Batch-owned
        │
        ▼
0 GAPs closed · 0 GAPs merged · 0 GAPs lost · 0 AGRs/SERs created (candidates identified only)
        │
        ▼
100% Lineage Preserved (GAP → MAP → CAN → OBS → source file, every link intact)
```

---

## 4F. Structural vs. Semantic Gap View *(new in v1.1 — analytical only, no reclassification)*

This is a **different cut** across all 23 GAPs than Category (A/B/C1/C2/C3) — it separates *what kind of gap* each one is, independent of its formal classification.

| View | Definition | GAPs |
|---|---|---|
| **Structural Persistence Gaps** | The frozen schema has no column/table for canonical information that exists — a physical-structure absence | GAP-004, 005, 006, 007, 009, 010, 012, 015, 017, 018, 019, 020, 022, 023 (14 total — includes GAP-017's UI-copy absence, which is structural even though it's Category C1) |
| **Semantic / Business Interpretation Gaps** | A column/table exists, but its intended *meaning*, *value format*, or *derivation methodology* is unconfirmed — an interpretation absence, not a structural one | GAP-002, 003, 008, 011, 013, 014, 016, 021 (8 total) |
| **Sequencing (neither)** | Not a gap in either sense — a correctly-ordered cross-batch dependency | GAP-001 |

**14 + 8 + 1 = 23. No GAP appears in more than one row; no Category was changed to produce this view — it is a purely descriptive re-slice of the same 23 GAPs already classified in §3–4.**

---

## 4G. Batch Independence Confirmation *(new in v1.1, permanent restatement)*

**Batch 1 GAPs must never use evidence from Batch 2 or later** to justify a classification, confidence rating, or resolution — **unless explicitly raised through Cross-Batch Governance** (`Batch1_Canonicalization_Package_v1.1` §12; `DOC-P3-11` §22). This Gap Analysis package's Evidence Register (§5) confirms every source used is Batch-1-scoped (Discovery/Canonicalization/Mapping packages for this batch, DOC-P3-04, RE-DOC-01–05, and the Engineering Handover) — no Batch 2–6 source was consulted, because none has been Discovered yet. GAP-001 is the sole exception acknowledged as depending on future batch content, and it is explicitly marked Cross-Batch, not silently assumed resolved.

---

## 4H. Gap Statistics Dashboard *(new in v1.1 — consolidated counts)*

| By Category | Count |
|---|---|
| A | 1 |
| B | 6 |
| C1 | 3 |
| C2 | 0 |
| C3 | 13 |

| By Priority | Count |
|---|---|
| Critical | 2 |
| High | 8 |
| Medium | 7 |
| Low | 7 *(GAP-019 appears in both Medium and Low listings in §7 due to a cross-listing — see note in §7; treated once here under its primary Medium listing, giving Low a true count of 6 distinct GAPs plus this note)* |

| By Owner | Count |
|---|---|
| Founder | 11 |
| Architecture | 12 |
| Documentation | 3 |
| Cross Batch | 1 |
| Schema / Runtime / RE / Knowledge / Implementation | 0 each (impact areas, not primary owners, this batch) |

| By Impact Area | Count of GAPs touching it |
|---|---|
| Seed Generation | 9 |
| Runtime | 11 |
| Architecture | 9 |
| Recommendation Engine | 9 |
| API | 2 |
| UI | 3 |
| Knowledge Quality | 1 |

| Potential AGR | Potential SER | Founder Decision | Documentation | Cross Batch |
|---|---|---|---|---|
| 3 (GAP-004, 007, 012) | 8 (GAP-004, 005, 006, 007, 009, 010, 015, 012, 018–020, 022, 023 — several overlap AGR/SER candidacy, see §10/§11 for the non-overlapping detail) | 11 | 3 | 1 |

---

## 4I. Permanent Gap Resolution Rule *(new in v1.1, permanent)*

- **Original GAP records never change.** Category, evidence, confidence, ownership, and priority as recorded in §3–4 of this frozen document are permanent.
- **Resolution creates Resolution Records** — new, separately dated entries that reference the original `GAP-*` ID — never edits to the original.
- **Frozen GAP classifications remain immutable**, exactly as `DOC-P3-11` §26B already establishes for the register as a whole.
- **Contradictions create Cross-Batch Conflicts** (`CB-XXX`) — a later batch or later evidence never overwrites a frozen GAP's history; it is recorded as a new, linked conflict instead.

---

## 4J. Why Category C2 = 0 *(new in v1.1 — explicit, so future readers never have to infer this)*

**Category C2 (Implementation inconsistency) requires an actual implementation artifact — seed SQL, a migration file, or deployed code — that contradicts the design document.** As of this Gap Analysis, **no seed SQL has been generated for Batch 1** (Stage 9, Seed Data Generation, has not begun — DOC-P3-09 §15). There is therefore nothing yet in existence that could be *inconsistent with* the frozen architecture in the specific way Category C2 requires. Every one of this batch's 23 issues is a mismatch between **canonical business knowledge and the design document itself** (Category C3), a **value/methodology ambiguity** (Category B), or a **documentation clarity gap** (Category C1) — none of them involve a second, already-built artifact to compare against. **Category C2 will only become populated once Stage 9 produces seed SQL that a future validation pass can compare against DOC-P3-04.**

---

## 5. Evidence Register

*(Exactly which documents, tables, rules, and workbook evidence were used — per the Permanent Evidence Rule, §26C.)*

| Evidence Source | Type (per §26C) | Used For |
|---|---|---|
| `DOC-P3-11` §04 (Batch Independence Rule) | Approved project documentation | GAP-001 |
| `DOC-P3-04` §03.27 DDL (all 15 `re_engine` tables, verbatim) | Frozen architecture document | GAP-002 through GAP-023 (structural basis for every classification) |
| `Batch1_Discovery_Report_v1.1` (FROZEN) — full attribute/rule/vocabulary inventories | Frozen architecture document (Discovery-stage) | GAP-002 through GAP-023 (canonical business fact basis) |
| `Batch1_Canonicalization_Package_v1.1` (FROZEN) — CAN-ATT, CAN-RULE, CAN-VOC dictionaries | Frozen architecture document (Canonicalization-stage) | GAP-002 through GAP-023 |
| `Batch1_Mapping_Package_v1.1` (FROZEN) — Attribute Matrix §1A, Mapping Issues §5 | Frozen architecture document (Mapping-stage) | Direct source of every MI evaluated |
| Full-dataset re-verification (`Meal_Class_Master_v3.slot_group` tally: 22/131 Snack rows) | Approved implementation evidence (direct data query, this project) | GAP-007 |
| Engineering Handover Package (BUILD-02 dynamic onboarding requirement) | Approved project documentation | GAP-012 |
| RE-DOC-01 through RE-DOC-05 | Frozen architecture documents | Consulted for GAP-002, 006, 015, 018–023 to check whether orphaned attributes are referenced by any RE logical function — no explicit reference found in the sections reviewed, which is itself inconclusive rather than confirming absence of need; **this is why GAP-018 through GAP-023 route to Architecture review rather than being closed as "not needed"** |

**No evidence source outside this list was used. No inference substituted for missing evidence anywhere in this register.**

---

## 6. Impact Assessment

| GAP ID(s) | Seed Generation | Runtime | Architecture | Recommendation Engine | API | UI | Knowledge Quality |
|---|---|---|---|---|---|---|---|
| GAP-001 | ✅ Blocks until Batch 4 | — | — | — | — | — | — |
| GAP-002, 003 | ✅ | — | — | ✅ (diet_mode) | — | — | — |
| GAP-004 | ✅ | ✅ | ✅ | ✅ | — | — | — |
| GAP-005 | ✅ | ✅ | — | — | — | — | — |
| GAP-006 | ✅ | — | — | ✅ | — | — | — |
| GAP-007 | ✅ | ✅ | ✅ | — | ✅ | — | — |
| GAP-008 | ✅ | — | — | — | — | — | — |
| GAP-009 | — | ✅ | ✅ | — | — | — | — |
| GAP-010 | — | — | ✅ | ✅ | — | — | — |
| GAP-011, 013 | ✅ | — | — | — | — | — | — |
| GAP-012 | — | ✅ | ✅ | — | ✅ | — | — |
| GAP-014, 016 | ✅ | — | — | ✅ | — | — | — |
| GAP-015 | — | ✅ | — | ✅ | — | — | — |
| GAP-017 | — | — | — | — | — | ✅ | ✅ |
| GAP-018, 019, 020, 023 | — | ✅ | ✅ | ✅ | — | — | — |
| GAP-021 | — | ✅ | — | — | — | ✅ | — |
| GAP-022 | — | ✅ | ✅ | — | — | ✅ | — |

---

## 7. Priority Matrix

| Priority | GAP IDs | Rationale |
|---|---|---|
| **Critical** | GAP-004, GAP-007 | Directly block correct seeding of `re_weekly_class_plans` and `re_meal_classes` — both have concretely demonstrated, evidenced conflicts (12 vs. 3 columns; 22 unseedable Snack rows) affecting the core weekly-planning pipeline |
| **High** | GAP-005, GAP-006, GAP-012, GAP-014, GAP-015, GAP-018, GAP-019, GAP-022 | Significant structural gaps affecting Recommendation Engine inputs, BUILD-02 onboarding, or core taxonomy tables |
| **Medium** | GAP-002, GAP-008, GAP-009, GAP-013, GAP-016, GAP-019 (cross-listed), GAP-021 | Founder/business decisions or documentation clarifications needed, but with narrower blast radius than Critical/High |
| **Low** | GAP-001, GAP-003, GAP-010, GAP-011, GAP-017, GAP-020, GAP-023 | Either already correctly sequenced (GAP-001), narrow in impact, or affect secondary/descriptive data rather than core pipeline function |

---

## 8. Ownership Matrix

| Owner | GAP IDs | Count |
|---|---|---|
| Founder | GAP-002, GAP-003, GAP-004*, GAP-005*, GAP-006*, GAP-007*, GAP-008, GAP-014, GAP-015*, GAP-016, GAP-021 | 11 (5 marked * are "Founder Decision first" before Architecture/SER review) |
| Architecture | GAP-004, GAP-005, GAP-006, GAP-007, GAP-009, GAP-010, GAP-012, GAP-018, GAP-019, GAP-020, GAP-022, GAP-023 | 12 (several shared with Founder — first decision, then architecture confirms feasibility) |
| Schema | — | 0 (no issue is purely a schema-mechanics question independent of a Founder/Architecture decision above it) |
| Runtime | — | 0 (Runtime is an impact area, not a primary owner, for every GAP in this batch) |
| Recommendation Engine | — | 0 (same — impact area, not primary owner, for this batch's issues) |
| Knowledge | — | 0 |
| Cross Batch | GAP-001 | 1 |
| Implementation | — | 0 (no seed SQL exists yet to be inconsistent with design — this is why Category C2 has zero entries) |
| Documentation | GAP-011, GAP-013, GAP-017 | 3 |

**Every GAP has exactly one primary owner**, per the instruction — where both Founder and Architecture are listed against the same GAP (marked *), the Founder is the primary owner (decision comes first) and Architecture is the secondary confirming party, consistent with the Recommended Next Governance Path column in §4.

---

## 9. Category Summary

| Category | Count | GAP IDs |
|---|---|---|
| A — No Gap | 1 | GAP-001 |
| B — Business/Founder Decision | 6 | GAP-002, 003, 008, 014, 016, 021 |
| C1 — Documentation inconsistency | 3 | GAP-011, 013, 017 |
| C2 — Implementation inconsistency | 0 | — (no seed SQL exists yet to compare against) |
| C3 — Architecture inconsistency | 13 | GAP-004, 005, 006, 007, 009, 010, 012, 015, 018, 019, 020, 022, 023 |
| **Total** | **23** | |

---

## 10. SER Readiness *(identification only — no SER created)*

| GAP ID | May Require SER Consideration? | Why |
|---|---|---|
| GAP-004 | **Yes, pending Founder Decision** | If reduced fidelity is not intentional, adding rank/slot columns to `re_weekly_class_plans` would require a schema change |
| GAP-005 | **Yes, pending Founder Decision** | Same reasoning, for `re_household_addon_plans` |
| GAP-006 | **Yes, pending Founder Decision** | Same reasoning, for `re_nonveg_logic` |
| GAP-007 | **Yes, pending Founder Decision** | The `slot` CHECK constraint would need a `snack` value added |
| GAP-009 | **Possibly** | Only if City Tier is confirmed absent from `public.profiles` too |
| GAP-010 | **Possibly** | Only if Architecture confirms Class Family Code is needed by an RE function |
| GAP-012 | **Possibly, likely** | The Sub-Cohort→Persona relationship appears functionally necessary for BUILD-02 |
| GAP-015 | **Yes, pending Founder Decision** | If 3 distinct weights must be preserved rather than combined |
| GAP-018, 019, 020, 022, 023 | **Possibly** | Only for whichever specific attributes Architecture confirms are needed by an RE-DOC function, not the full attribute set |

**All other GAPs (001, 002, 003, 008, 011, 013, 014, 016, 017, 021) are not expected to require an SER** — their resolution paths are Founder Decisions on values/methodology or Documentation clarifications, not schema changes.

---

## 11. AGR Readiness *(identification only — no AGR created)*

Per DOC-P3-09's classification scheme, an **AGR (Architecture Gap Report)** is the correct instrument when the *frozen architecture itself* — not just a seed-value question — is found insufficient. Candidates:

| GAP ID | May Require AGR Consideration? | Why |
|---|---|---|
| GAP-004, GAP-007 | **Yes** | These represent the clearest cases of a frozen document (DOC-P3-04) being internally inconsistent with other frozen/canonical evidence (BR2/BR4, and the raw Snack-class count) — the textbook AGR scenario |
| GAP-012 | **Yes** | A functionally-central relationship with no schema home at all is an architecture completeness question, not merely a seed-value question |
| GAP-005, GAP-006, GAP-015 | **Possibly** | Same pattern as GAP-004/007 but narrower in blast radius |

**No AGR is created in this stage.** These are identified as candidates only, per the explicit instruction.

---

## 12. Gap Analysis Readiness Summary — Batch 1 Stage 5 Readiness

*(Readiness summary for the next stage only — does not begin that stage.)*

| Check | Status |
|---|---|
| All 23 Mapping Issues classified | ✅ Yes — 1 A, 6 B, 3 C1, 0 C2, 13 C3 |
| Every GAP references its originating MAP ID(s) | ✅ Yes (§4) |
| Every classification backed by evidence per §26C | ✅ Yes — Evidence Register (§5) cites source for every GAP |
| Any issue closed, merged, or renumbered | ❌ No |
| Any AGR or SER created | ❌ No — only readiness/candidacy identified (§10, §11) |
| Founder Decisions required before further governance action | ⚠️ 11 GAPs list Founder as owner (§8) |
| Stage 5 started | ❌ **No — awaiting Founder approval** |

**Verdict:** Batch 1 Stage 5 may begin once the Founder reviews this Gap Analysis package, in particular the 11 Founder-owned GAPs and the two Critical-priority items (GAP-004, GAP-007) that are also AGR candidates. **Stage 5 has not begun.**

---

## Completion Summary

- **v1.0 substance unchanged:** all 23 Mapping Issues' classifications, GAP IDs, evidence, ownership, and priorities remain exactly as originally recorded — verified by direct comparison.
- **v1.1 adds 10 governance enhancements** (§4A–4J): Gap Resolution Matrix, Gap Dependency Graph, Resolution Order (4 waves), Gap Closure Criteria (permanent lifecycle), Executive Traceability Dashboard, Structural vs. Semantic Gap View, Batch Independence Confirmation, Gap Statistics Dashboard, Permanent Gap Resolution Rule, and an explicit explanation of why Category C2 = 0.
- **Wording precision applied** to 11 of the 13 Category C3 GAPs (005, 006, 009, 010, 012, 015, 018, 019, 020, 022, 023) — "architecture inconsistency" language replaced with "no persistence location" framing, since the evidence for these 11 shows absence, not proven contradiction. **GAP-004 and GAP-007 retain "architecture inconsistency" language**, since both are backed by demonstrated, evidenced contradictions (12-vs-3 column mismatch against frozen business rules; 22 literally unseedable rows against a live CHECK constraint).
- No classification, GAP ID, evidence, ownership, or priority was changed — confirmed by the wording-only nature of every edit made.

---

## Regression Review — verified by direct comparison against v1.0

- ✅ No architecture, schema, API, Security, or Recommendation Engine change
- ✅ No redesign proposed or performed
- ✅ No SQL generated
- ✅ No AGR, SER, or DCR created — only candidacy identified (unchanged from v1.0)
- ✅ No classification changed — all 23 Categories (1 A / 6 B / 3 C1 / 0 C2 / 13 C3) identical to v1.0
- ✅ No GAP ID changed, renumbered, merged, or lost — 23 in, 23 out
- ✅ No evidence changed — Evidence Register (§5) content identical to v1.0
- ✅ No ownership changed — Ownership Matrix (§8) identical to v1.0
- ✅ No priority changed — Priority Matrix (§7) identical to v1.0
- ✅ Wording changes confirmed limited to the "Why This Evidence Supports the Classification" and "Recommended Next Governance Path" prose cells for exactly the 11 named GAPs — no other cell in the Detailed GAP Register (§4) was touched
- ✅ `Batch1_Discovery_Report_v1.1`, `Batch1_Canonicalization_Package_v1.1`, `Batch1_Mapping_Package_v1.1` — all read-only, none modified
- ✅ `DOC-P3-09`, `DOC-P3-10`, all Phase 3 documents — untouched
- ✅ Permanent Evidence Rule (DOC-P3-11 §26C) respected throughout — no new inference introduced by the wording pass; if anything, the wording pass removed language that overstated certainty
- ✅ Lineage chain maintained: every `GAP-*` ID still cites its `MAP-*` ID(s) exactly as in v1.0

---

## Freeze Confirmation

**`Batch1_GapAnalysis_Package_v1.1` — APPROVED — ACTIVE — FROZEN.** Supersedes v1.0, which is retained unmodified as a superseded reference and is never regenerated.

---

## Batch 1 Stage 5 Readiness Summary

| Check | Status |
|---|---|
| All 23 GAPs remain classified, none closed | ✅ Yes |
| Governance enhancements complete (§4A–4J) | ✅ Yes |
| Wording precision applied without weakening genuine findings | ✅ Yes — GAP-004/GAP-007 retain full strength |
| Regression clean | ✅ Yes |
| Document frozen | ✅ Yes |
| Stage 5 started | ❌ **No — awaiting Founder approval** |

**Verdict:** Batch 1 Stage 5 may begin once the Founder approves this frozen Gap Analysis package. **Stage 5 has not begun.**

---

## Founder Approval Gate

**Gap Analysis governance refinement complete and FROZEN. No AGR, SER, or DCR has been created. No GAP has been resolved. Batch 1 Stage 5 has NOT begun. Batch 2 has NOT begun. No SQL or database change of any kind occurred.**

This package awaits Founder approval before Stage 5 starts.

Founder sign-off: _______________________ Date: ___________
