# Phase 3.5 — Batch 1 — Stage 5: Knowledge Resolution
## Consolidated Deliverable Set v1.1

**Governed by:** `[ACTIVE]_DOC-P3-09_Knowledge_Integration_Governance_v1.0`, `[ACTIVE]_DOC-P3-10_Seed_Data_Integration_Framework_v1.1`
**Execution audit trail:** `[ACTIVE]_DOC-P3-11_Discovery_Execution_Register_v1.9`
**Inputs (frozen, immutable, used read-only — NOT reopened):** `Batch1_Discovery_Report_v1.1`, `Batch1_Canonicalization_Package_v1.1`, `Batch1_Mapping_Package_v1.1`, `Batch1_GapAnalysis_Package_v1.1`
**Supersedes:** `Batch1_Resolution_Package_v1.0` (not modified — retained as superseded reference)
**Scope:** Governance refinement only. Every RES ID, GAP ID, category, lineage, ownership, evidence, and recommendation from v1.0 is identical here.
**Date:** 2026-07-02
**Status:** Draft — Ready for Founder Review

**Revision Notice (v1.0 → v1.1) — governance improvements only, per DOC-P3-11 §26F–§26J:**
1. **Resolution Confidence** column added to §1 Resolution Register (per §26I)
2. **Expected Evidence Source** column added for all 8 Architecture Confirmations (per §26G)
3. **Founder Decision Register (§3) expanded** — all 11 Founder Decisions now presented as structured packs (Option A/B/C, Claude Recommendation, Reason, Impact, Trade-offs) per §26H. **No decision was made — every pack ends with the Founder's choice still open.**
4. **Executive Dashboard (§9) improved** with a Critical Resolution Chain (per §26J)

No RES ID, GAP ID, category, lineage, ownership, or evidence changed from v1.0 — confirmed by direct comparison in the Regression Review.

---

## 0. Method Note

Every GAP terminates through exactly one Resolution Record (`RES-NNN`), per the Permanent Resolution Record Framework (`DOC-P3-11` §26E). Each record's full lineage (OBS → CAN → MAP → GAP → RES) is reconstructed here from the four frozen Batch 1 documents — no lineage link is fabricated; where a GAP cites multiple MAP/CAN/OBS IDs, the primary one is listed with others noted. **This stage determines *what kind* of resolution each GAP needs — it does not perform the resolution itself.**

---

## 1. Resolution Register

*(One RES record for every GAP — 23 total.)*

| RES ID | GAP ID | MAP ID | CAN ID | OBS ID | Resolution Type | Evidence | Approval | Date | Resolution Confidence | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| RES-001 | GAP-001 | MAP-ENT-008/009/011 | CAN-ENT-008/009/011 | OBS-ENT-009/010/011/012 | Cross-Batch Dependency | Batch Independence Rule (DOC-P3-11 §04) | Pending (re-surfaces at Batch 4) | 2026-07-02 | High | OPEN |
| RES-002 | GAP-002 | MAP-VOC-008, MAP-ENT-012 | CAN-VOC-003, CAN-ENT-012 | OBS-VOC-003, OBS-ENT-013 | Founder Decision | `re_cohorts` DDL; Persona `nonveg_mode` full data | Pending | 2026-07-02 | High | OPEN |
| RES-003 | GAP-003 | MAP-ENT-012 | CAN-ENT-012 | OBS-ENT-013 | Founder Decision | `re_cohorts` DDL (`DEFAULT 1.0`); full-column check | Pending | 2026-07-02 | Medium | OPEN |
| RES-004 | GAP-004 | MAP-ENT-013, MAP-REL-006 | CAN-ENT-013, CAN-REL-002 | OBS-ENT-014, OBS-REL-002 | Founder Decision (Future AGR Candidate on non-approval path) | `re_weekly_class_plans` DDL vs. canonical Weekly Plan attribute list | Pending | 2026-07-02 | High | OPEN |
| RES-005 | GAP-005 | MAP-ENT-014, MAP-REL-007/008 | CAN-ENT-014, CAN-REL-003/011 | OBS-ENT-015, OBS-REL-003/011 | Founder Decision (Future SER Candidate on non-approval path) | `re_household_addon_plans` DDL vs. canonical attribute list | Pending | 2026-07-02 | High | OPEN |
| RES-006 | GAP-006 | MAP-ENT-015 | CAN-ENT-015 | OBS-ENT-016 | Founder Decision (Future SER Candidate on non-approval path) | `re_nonveg_logic` DDL vs. canonical attribute list | Pending | 2026-07-02 | High | OPEN |
| RES-007 | GAP-007 | MAP-VOC-003/004 | CAN-VOC-004/005 | OBS-VOC-004/005 | Founder Decision (Future AGR Candidate on non-approval path) | `re_meal_classes.slot` CHECK constraint vs. full 131-row tally (22 Snack rows) | Pending | 2026-07-02 | High | OPEN |
| RES-008 | GAP-008 | MAP-VOC-005 | CAN-VOC-001 | OBS-VOC-001 | Founder Decision | `re_main_cohorts` DDL comment vs. `Main_Cohort_Hierarchy` labels | Pending | 2026-07-02 | High | OPEN |
| RES-009 | GAP-009 | MAP-VOC-006 | CAN-VOC-006/007 | OBS-VOC-006 | Architecture Confirmation (Future SER Candidate if not resolved elsewhere) | Full DDL review, all 15 target tables | Pending | 2026-07-02 | Medium | OPEN |
| RES-010 | GAP-010 | MAP-VOC-007 | CAN-VOC-008 | OBS-VOC-007 | Architecture Confirmation (Future SER Candidate if confirmed needed) | Full DDL review of `re_meal_classes` | Pending | 2026-07-02 | Medium | OPEN |
| RES-011 | GAP-011 | MAP-VOC-010 | CAN-VOC-015 | OBS-VOC-014 | Documentation Clarification | `re_states.region` — no CHECK, no comment | Pending | 2026-07-02 | High | OPEN |
| RES-012 | GAP-012 | MAP-REL-002 | CAN-REL-005 | OBS-REL-005 | Architecture Confirmation (Future SER Candidate if confirmed needed) | `re_subcohorts` DDL vs. `Subcohort_Routing.maps_to_persona_id`; Engineering Handover BUILD-02 | Pending | 2026-07-02 | Medium | OPEN |
| RES-013 | GAP-013 | MAP-ENT-003 | CAN-ENT-003 | OBS-ENT-003 | Documentation Clarification | `re_personas.persona_code` — no example value | Pending | 2026-07-02 | High | OPEN |
| RES-014 | GAP-014 | MAP-RULE-004 | CAN-RULE-011 | OBS-RULE-011 | Founder Decision | `re_class_dish_options` DDL vs. `Class_Dish_Options_v3` attribute list | Pending | 2026-07-02 | High | OPEN |
| RES-015 | GAP-015 | MAP-RULE-005 | CAN-RULE-008 | OBS-RULE-008 | Founder Decision (Future SER Candidate on non-approval path) | `re_city_migration_overlays.city_overlay_weight` vs. 3 named canonical weights | Pending | 2026-07-02 | High | OPEN |
| RES-016 | GAP-016 | (attribute-level, MAP-ENT-011) | CAN-ENT-011 | OBS-ENT-012 | Founder Decision | `re_addon_dish_options.suitability_rank` vs. `Addon_Dish_Options` attribute list | Pending | 2026-07-02 | High | OPEN |
| RES-017 | GAP-017 | MAP-ENT-001/002 | CAN-ENT-001/002 | OBS-ENT-001/002 | Documentation Clarification | `re_main_cohorts`/`re_subcohorts` DDL vs. 6 onboarding-copy attributes | Pending | 2026-07-02 | Medium | OPEN |
| RES-018 | GAP-018 | MAP-ENT-003 | CAN-ENT-003 | OBS-ENT-003 | Architecture Confirmation | `re_personas` DDL (6 columns) vs. canonical Persona (23 attributes) | Pending | 2026-07-02 | Medium | OPEN |
| RES-019 | GAP-019 | MAP-ENT-005 | CAN-ENT-005 | OBS-ENT-005 | Architecture Confirmation | `re_states` DDL (3 columns) vs. canonical State/UT (13 attributes) | Pending | 2026-07-02 | Medium | OPEN |
| RES-020 | GAP-020 | MAP-ENT-006, MAP-ENT-010 | CAN-ENT-006, CAN-ENT-010 | OBS-ENT-006, OBS-ENT-011 | Architecture Confirmation | `re_city_migration_overlays`/`re_addon_classes` DDL vs. canonical attribute lists | Pending | 2026-07-02 | Medium | OPEN |
| RES-021 | GAP-021 | MAP-ENT-004 | CAN-ENT-004 | OBS-ENT-004 | Founder Decision | `re_routing_rules` DDL vs. canonical Routing Rule attributes | Pending | 2026-07-02 | High | OPEN |
| RES-022 | GAP-022 | MAP-ENT-007 | CAN-ENT-007 | OBS-ENT-007 | Architecture Confirmation (Future SER Candidate if confirmed needed) | `re_meal_classes` DDL (10 columns, no name) vs. canonical Meal Class (16 attributes) | Pending | 2026-07-02 | Medium | OPEN |
| RES-023 | GAP-023 | MAP-ENT-012 | CAN-ENT-012 | OBS-ENT-013 | Architecture Confirmation | `re_cohorts` DDL (5 columns) vs. canonical Cohort (9 attributes) | Pending | 2026-07-02 | Medium | OPEN |

**23 Resolution Records created, each now carrying a Resolution Confidence rating (per DOC-P3-11 §26I), citing the same evidence already in the Evidence column — no new inference introduced.** All Status = OPEN — no resolution has actually occurred; this register only determines the required path. No GAP was modified to produce this table.

---

## 2. Resolution Matrix

| GAP | Resolution Type | Owner | Evidence Required | Approval Required | Next Action |
|---|---|---|---|---|---|
| GAP-001 | Cross-Batch Dependency | Cross Batch | Batch 4 Canonicalization output | Founder (at Cross-Batch Conflict resolution) | Re-surface when Batch 4 canonicalizes `dishes.xlsx` |
| GAP-002 | Founder Decision | Founder | `nonveg_mode → diet_mode` transformation rule | Founder | Present transformation options to Founder |
| GAP-003 | Founder Decision | Founder | Confirmation of `DEFAULT 1.0` intent | Founder | Present question to Founder |
| GAP-004 | Founder Decision | Founder | Confirm intentional-vs-gap status of reduced fidelity | Founder, then Architecture if AGR pursued | Present the 3 options from Mapping MI-004 to Founder |
| GAP-005 | Founder Decision | Founder | Confirm intentional-vs-gap status of dropped granularity | Founder, then Architecture if SER pursued | Present options to Founder |
| GAP-006 | Founder Decision | Founder | Confirm which of 6 counts maps to `weekly_nonveg_slots` | Founder, then Architecture if SER pursued | Present options to Founder |
| GAP-007 | Founder Decision | Founder | Confirm intentional-vs-gap status of missing `snack` value | Founder, then Architecture if AGR pursued | Present the 22-row evidence to Founder |
| GAP-008 | Founder Decision | Founder | MC5's correct `cohort_code` | Founder | Ask Founder directly — no evidence path exists otherwise |
| GAP-009 | Architecture Confirmation | Architecture | Confirm whether `public.profiles` holds City Tier | Architecture owner | Review `public.profiles` schema (outside Batch 1's 15-table scope) |
| GAP-010 | Architecture Confirmation | Architecture | Confirm RE-DOC need for Class Family Code | Architecture owner | Cross-check RE-DOC-01–05 |
| GAP-011 | Documentation Clarification | Documentation | Confirm `region` value domain | Documentation owner or Founder | Add clarifying note to DOC-P3-04 or a companion document |
| GAP-012 | Architecture Confirmation | Architecture | Confirm BUILD-02 dependency on this relationship | Architecture owner | Review against Engineering Handover BUILD-02 |
| GAP-013 | Documentation Clarification | Documentation | Confirm `persona_code` convention | Documentation owner or Founder | Add clarifying note |
| GAP-014 | Founder Decision | Founder | `base_score` methodology; `is_primary_candidate` derivation rule | Founder/Product | Present scoring-methodology question |
| GAP-015 | Founder Decision | Founder | Confirm whether 3 weights combine or need separate columns | Founder, then Architecture if SER pursued | Present options |
| GAP-016 | Founder Decision | Founder | Ranking methodology for `suitability_rank` | Founder/Product | Present ranking-methodology question |
| GAP-017 | Documentation Clarification | Documentation | Confirm onboarding-copy storage location | Documentation owner | Confirm intended location (DB column vs. app config) |
| GAP-018 | Architecture Confirmation | Architecture | Confirm which (if any) Persona attributes are RE-function inputs | Architecture owner | Cross-check RE-DOC-01–05 |
| GAP-019 | Architecture Confirmation | Architecture | Confirm which (if any) State/UT attributes are RE-function inputs | Architecture owner | Cross-check RE-DOC-01–05 |
| GAP-020 | Architecture Confirmation | Architecture | Confirm which (if any) Add-on/Overlay attributes are RE-function inputs | Architecture owner | Cross-check RE-DOC-01–05 |
| GAP-021 | Founder Decision | Founder | Confirm `shown_when`/`maps_to_fields` → column correspondence | Founder/BUILD-02 owner | Present correspondence question |
| GAP-022 | Architecture Confirmation | Architecture | Confirm whether `class_code` alone suffices for the app | Architecture owner | Review app UI requirements |
| GAP-023 | Architecture Confirmation | Architecture | Confirm which (if any) Cohort attributes are RE-function inputs | Architecture owner | Cross-check RE-DOC-01–05 |

---

## 3. Founder Decision Register *(expanded in v1.1 — structured decision packs per DOC-P3-11 §26H; no decision made)*

Each pack presents structured options, a Claude Recommendation with reasoning, impact, and trade-offs. **The Founder's choice remains open in every pack below — nothing here is a decision, only a decision-ready summary.**

---

**GAP-002 — Persona `nonveg_mode` → `re_cohorts.diet_mode`**

| Field | Content |
|---|---|
| Decision | How should `nonveg_mode`'s 12 values map into `diet_mode`? |
| Option A | Map all 12 values verbatim (no transformation) |
| Option B | Collapse to a simplified 4-value core (veg/nonveg/egg/mixed) |
| Option C | Leave `diet_mode` unpopulated pending a dedicated transformation-rule design session |
| Claude Recommendation | Option A |
| Reason | `diet_mode` is unconstrained text — no CHECK constraint blocks any of the 12 values; verbatim mapping preserves full fidelity without inventing a new taxonomy |
| Impact | Seed Generation, Recommendation Engine |
| Trade-offs | A risks the RE logic expecting a simpler value set if it wasn't designed for all 12 values; B risks losing nuance; C delays Seed Generation entirely |

---

**GAP-003 — `re_cohorts.prior_weight`**

| Field | Content |
|---|---|
| Decision | Should `prior_weight` use the schema's `DEFAULT 1.0` for all cohorts, or does a real weight need deriving? |
| Option A | Accept `DEFAULT 1.0` for all rows (no seed value supplied) |
| Option B | Derive a weight from `planning_confidence_v3` via a new categorical-to-numeric mapping |
| Option C | Treat as a genuine gap requiring new business input before any value is set |
| Claude Recommendation | Option A |
| Reason | No canonical numeric signal exists; inventing one (B) would be an unevidenced fabrication, which governance (DOC-P3-11 §26C) forbids |
| Impact | Seed Generation |
| Trade-offs | A may under-differentiate cohorts in early RE scoring; B risks a fabricated proxy; C blocks progress indefinitely |

---

**GAP-004 — `re_weekly_class_plans` structure**

| Field | Content |
|---|---|
| Decision | Should the 3-column, no-rank, no-snack structure be accepted, or does it need an SER? |
| Option A | Accept as intentional simplification — only primary class per slot seeded; secondary/tertiary and snack dropped |
| Option B | Raise an SER to add rank + snack columns, matching full canonical fidelity |
| Option C | Store the dropped detail in a supplementary structure outside this table, leaving the frozen schema untouched |
| Claude Recommendation | Option B |
| Reason | BR2/BR4 — already-frozen, independently-verified business rules — explicitly depend on the excluded detail; Option A risks silently discarding rules already validated as correct |
| Impact | Seed Generation, Runtime, Architecture, Recommendation Engine |
| Trade-offs | B requires reopening frozen architecture (cost/schedule impact); A is fastest but may degrade RE quality; C avoids schema change but adds a second, less-integrated data path |

---

**GAP-005 — `re_household_addon_plans` granularity**

| Field | Content |
|---|---|
| Decision | Should the missing day/slot/attached-class detail be added via SER, or is the current grain acceptable? |
| Option A | Accept current grain (segment+cohort+addon_class only) |
| Option B | SER to add `day_of_week`/`meal_slot`/`attached_to_main_class_code` columns |
| Option C | Treat day/slot as implied by `re_addon_classes.slot` rather than a stored column, pending Architecture confirmation |
| Claude Recommendation | Option C |
| Reason | The exact 7,992-row match to canonical data suggests the schema's grain may already capture this implicitly — worth confirming before reopening architecture |
| Impact | Seed Generation, Runtime |
| Trade-offs | C is cheapest but unverified; B is safest but reopens frozen architecture; A risks losing real scheduling detail |

---

**GAP-006 — `re_nonveg_logic` count collapse**

| Field | Content |
|---|---|
| Decision | Which of the 6 canonical weekly counts maps to `weekly_nonveg_slots`? |
| Option A | Sum of all 6 counts into one aggregate value |
| Option B | Only the "regular_nonveg" count maps; other 5 counts dropped |
| Option C | SER to add all 6 as separate columns |
| Claude Recommendation | Option C |
| Reason | The 6 counts represent materially different protein types (fish/chicken/mutton/egg/omnivore/regular); BR6's diet-mode logic depends on distinguishing them, not an aggregate |
| Impact | Seed Generation, Recommendation Engine |
| Trade-offs | C reopens architecture; A/B both lose real distinctions the canonical data preserves |

---

**GAP-007 — `re_meal_classes.slot` missing `snack`**

| Field | Content |
|---|---|
| Decision | Should the CHECK constraint be amended to add `snack`, or should the 22 Snack-slot classes be remapped? |
| Option A | SER to add `snack` to the CHECK constraint |
| Option B | Remap Snack-slot classes to the existing `addon` value |
| Option C | Exclude the 22 Snack-slot classes from seeding entirely, pending future architecture work |
| Claude Recommendation | Option A |
| Reason | Option B was already rejected during Mapping (`MAP-DEC-003`) as conflating two different concepts (planning role vs. time-of-day slot); Option C silently drops 22 real, evidenced classes |
| Impact | Seed Generation, Runtime, Architecture, API |
| Trade-offs | A is the only option preserving full fidelity but requires reopening frozen architecture |

---

**GAP-008 — MC5 `cohort_code`**

| Field | Content |
|---|---|
| Decision | What is MC5's correct `cohort_code`? |
| Option A | `MC_PG_HOSTEL` (the schema's 5th example value, by elimination) |
| Option B | A new code not yet in the schema's example list (e.g., `MC_SPECIAL_GOAL`) |
| Option C | Escalate to whoever authored the original DOC-P3-04 comment for clarification before assigning any code |
| Claude Recommendation | Option C |
| Reason | No evidence supports A or B — the label "Special goal or kitchen operating mode" doesn't semantically match "PG_HOSTEL," and inventing a new code (B) would itself be an unevidenced assumption |
| Impact | Seed Generation |
| Trade-offs | C is slowest but avoids seeding a wrong value that needs correcting later; A risks silent misclassification; B risks schema/documentation drift |

---

**GAP-014 — `base_score` / `is_primary_candidate` methodology**

| Field | Content |
|---|---|
| Decision | What methodology determines `base_score` and `is_primary_candidate`? |
| Option A | `is_primary_candidate = TRUE` where `class_use_scope_v3 = 'main_class_dish_pool'` (946 rows), `FALSE` for the 104 legacy/addon rows; `base_score` left unseeded pending a real methodology |
| Option B | Both fields require a new scoring methodology to be designed before any seeding |
| Option C | `base_score` seeded as a uniform placeholder (e.g., 0.5) pending future refinement |
| Claude Recommendation | Option A |
| Reason | `is_primary_candidate` has direct evidence (`class_use_scope_v3`); `base_score` does not, and Option C would fabricate a value with no basis, which governance forbids |
| Impact | Seed Generation, Recommendation Engine |
| Trade-offs | A leaves `base_score` unseeded until a real methodology exists (may block RE scoring quality); C provides a stopgap but risks being mistaken for real signal |

---

**GAP-015 — City Migration Overlay weights**

| Field | Content |
|---|---|
| Decision | Should the 3 canonical weights combine into 1 seeded value, or should the schema gain 2 more columns? |
| Option A | SER to add 2 more weight columns, preserving all 3 named weights |
| Option B | Combine via an equal-weighted average into the single `city_overlay_weight` column |
| Option C | Combine via a Founder-specified weighted formula (not equal) |
| Claude Recommendation | Option A |
| Reason | BR8 treats the 3 weights as functionally distinct (home-state signature vs. current-city lifestyle vs. national-modern trend); collapsing them (B/C) discards a distinction the business rule itself relies on |
| Impact | Runtime, Recommendation Engine |
| Trade-offs | A reopens architecture; B/C are faster but risk losing the nuance BR8 depends on |

---

**GAP-016 — `suitability_rank` methodology**

| Field | Content |
|---|---|
| Decision | What methodology determines `suitability_rank`? |
| Option A | Uniform default rank for all rows pending future refinement |
| Option B | Derive rank from row order within each `addon_class_code`, as listed in the source sheet |
| Option C | Require a new scoring methodology before any seeding |
| Claude Recommendation | Option B |
| Reason | Row order is directly observable evidence, not fabricated, unlike Option A's arbitrary uniform value |
| Impact | Seed Generation, Recommendation Engine |
| Trade-offs | B assumes the source workbook's row order is meaningful, which hasn't been explicitly confirmed by the Founder; C is safest but slowest |

---

**GAP-021 — Routing Rule column correspondence**

| Field | Content |
|---|---|
| Decision | Do `shown_when`/`maps_to_fields` correspond to `trigger_answer`/`show_question_key`? |
| Option A | Confirm the correspondence as plausible and proceed with that mapping |
| Option B | Reject the correspondence — these need different/new columns |
| Option C | Escalate to the BUILD-02 owner for confirmation before deciding |
| Claude Recommendation | Option C |
| Reason | This mapping affects a functionally live feature (BUILD-02 dynamic onboarding, a documented HARD REQUIREMENT); guessing wrong here has direct UX consequences |
| Impact | UI, Runtime |
| Trade-offs | C is slowest but lowest-risk given BUILD-02's explicit hard-requirement status |

---

## 4. Architecture Confirmation Register

*(Separated from true Founder Decisions — 8 total. Each now names an Expected Evidence Source per DOC-P3-11 §26G — Architecture Confirmation can never rely on memory.)*

| GAP | Confirmation Needed | Expected Evidence Source |
|---|---|---|
| GAP-009 | Whether `public.profiles` (outside Batch 1 scope) holds City Tier | `DOC-P3-04` (public schema section, if present); Implementation evidence (actual `public.profiles` table definition) |
| GAP-010 | Whether Class Family Code is needed by any RE-DOC logical function | `RE-DOC-01` through `RE-DOC-05` |
| GAP-012 | Whether Sub-Cohort→Persona relationship is needed by BUILD-02 | Engineering Handover Package (BUILD-02 requirement); `RE-DOC-01`–`05` (onboarding routing logic, if documented there) |
| GAP-018 | Whether orphaned Persona attributes are needed by any RE-DOC function | `RE-DOC-01` through `RE-DOC-05` |
| GAP-019 | Whether orphaned State/UT attributes are needed by any RE-DOC function | `RE-DOC-01` through `RE-DOC-05` |
| GAP-020 | Whether orphaned Add-on/Overlay attributes are needed by any RE-DOC function | `RE-DOC-01` through `RE-DOC-05` |
| GAP-022 | Whether `re_meal_classes` needs a display-name column | `DOC-P3-06` (API Contract Specification — to check if any endpoint response expects a class display name); UI-facing documentation if it exists |
| GAP-023 | Whether orphaned Cohort attributes are needed by any RE-DOC function | `RE-DOC-01` through `RE-DOC-05` |

**No Architecture Confirmation above has been performed yet — this table only names the source each confirmation must be checked against when the confirmation is actually carried out.**

---

## 5. Documentation Resolution Register

*(Documentation-only work, separated — 3 total.)*

| GAP | Documentation Action Needed |
|---|---|
| GAP-011 | Clarify `re_states.region`'s intended value domain |
| GAP-013 | Clarify `re_personas.persona_code`'s intended convention |
| GAP-017 | Clarify intended storage location for onboarding UI copy |

---

## 6. Cross Batch Resolution Register

*(Includes GAP-001, as instructed.)*

| GAP | Dependency | Trigger |
|---|---|---|
| GAP-001 | `dish_id` (UUID FK to `public.dishes`) has no canonical source until `dishes.xlsx` is canonicalized | Re-surface as a Cross-Batch Conflict when Batch 4 completes Canonicalization; `CAN-ENT-009`/`CAN-ENT-011` (this batch's dish names) must never be merged automatically with Batch 4's dish catalogue (per Canonicalization §12) |

---

## 7. Future SER Candidate Register *(reference only — no SER created)*

| GAP | Why It May Need an SER |
|---|---|
| GAP-004 | Would need rank/slot columns added to `re_weekly_class_plans` if reduced fidelity is not intentional |
| GAP-005 | Would need day/slot/attached-class columns added to `re_household_addon_plans` |
| GAP-006 | Would need additional count columns on `re_nonveg_logic` |
| GAP-007 | Would need the `slot` CHECK constraint amended to include `snack` |
| GAP-009 | Would need a City Tier column added, if not found in `public.profiles` |
| GAP-010 | Would need a Class Family Code column added, if confirmed needed |
| GAP-012 | Would need a Sub-Cohort→Persona FK added, if confirmed needed for BUILD-02 |
| GAP-015 | Would need 2 additional weight columns on `re_city_migration_overlays`, if 3 weights must be preserved |
| GAP-018, 019, 020, 022, 023 | Would need specific descriptive columns added, only for whichever attributes Architecture confirms are genuinely needed |

**No SER is created in this stage.**

---

## 8. Future AGR Candidate Register *(reference only — no AGR created)*

| GAP | Why It May Need an AGR |
|---|---|
| GAP-004 | Frozen DOC-P3-04 potentially inconsistent with its own frozen business rules (BR2/BR4) — the clearest AGR-shaped finding in this batch |
| GAP-007 | Same pattern — frozen DOC-P3-04's `slot` CHECK constraint demonstrably cannot represent 22 real, evidenced rows |
| GAP-012 | A functionally-central relationship (BUILD-02-relevant) with no schema home may indicate an architecture completeness gap, not just a missing seed value |

**No AGR is created in this stage.**

---

## 9. Executive Resolution Dashboard *(improved in v1.1 — Critical Resolution Chain added per DOC-P3-11 §26J)*

```
Total GAPs: 23
        │
        ├──► Resolved Automatically:     0   ( 0.0%)
        ├──► Need Founder:               11  (47.8%)
        ├──► Need Architecture:          8   (34.8%)
        ├──► Need Documentation:         3   (13.0%)
        ├──► Need Cross Batch:           1   ( 4.3%)
        │
        ├──► Potential AGR:              3   (GAP-004, 007, 012)
        └──► Potential SER:              13  (GAP-004, 005, 006, 007, 009, 010, 012, 015, 018, 019, 020, 022, 023)
```

**0 GAPs resolved automatically** — every one of the 23 requires an external input (Founder, Architecture, Documentation, or a future batch) before it can move toward closure. This is expected and correct: Stage 5's job is to determine the *path*, not to walk it.

### Critical Resolution Chain *(new — per §26J)*

```
GAP-007 (Founder Decision, Option A recommended: SER to fix `slot` CHECK constraint)
   │
   ▼
GAP-004 (Founder Decision, Option B recommended: SER to fix Weekly Plan structure)
   │  — both block Architecture confirmation of re_meal_classes / re_weekly_class_plans
   ▼
Potential AGR/SER decision (Architecture) — blocks:
   │
   ├──► GAP-006, GAP-015 (RE-scoring-adjacent Founder Decisions — best resolved after
   │     the core Meal Class / Weekly Plan structure is settled, since their SER
   │     candidacy depends on the same tables)
   │
   ▼
Seed SQL for re_meal_classes / re_weekly_class_plans (Stage 9) — cannot begin
until GAP-004 and GAP-007 reach a Founder-approved path
   │
   ▼
Implementation (Batch 1's core weekly-planning pipeline)

Separate, independent chain:
GAP-012 (Architecture Confirmation — BUILD-02 dependency)
   │
   ▼
Potential SER (Sub-Cohort→Persona relationship)
   │
   ▼
Onboarding/BUILD-02 Implementation — blocked independently of the Meal-Class chain above
```

**GAP-004 and GAP-007 are the critical path for Batch 1's core seed generation** — every other Founder Decision and Architecture Confirmation can proceed in parallel, but Stage 9 (Seed Data Generation) for the two central tables (`re_meal_classes`, `re_weekly_class_plans`) cannot begin until these two resolve. GAP-012 is on a separate, BUILD-02-specific critical path that does not block Batch 1's core pipeline.

---

## 10. Resolution Dependency Graph

```
GAP-004 (Founder) ──┬──► if not approved as-is ──► Potential AGR ──► Architecture
                     │
GAP-007 (Founder) ──┼──► if not approved as-is ──► Potential AGR ──► Architecture
                     │
GAP-012 (Architecture) ──► if confirmed needed ──► Potential SER ──► Architecture

GAP-005, GAP-006, GAP-015 (Founder) ──► if not approved as-is ──► Potential SER ──► Architecture

GAP-009, GAP-010, GAP-018, GAP-019, GAP-020, GAP-022, GAP-023 (Architecture) ──► if confirmed needed ──► Potential SER

GAP-001 (Cross Batch) ──► gated entirely on Batch 4 completion — independent of all other GAPs above
```

**This shows resolution-path dependency only — no GAP is resolved by this graph.**

---

## 11. Resolution Traceability Matrix

*(OBS → CAN → MAP → GAP → RES for all 23, condensed to entity-level groupings — full detail in §1.)*

| Source Entity Group | OBS IDs | CAN IDs | MAP IDs | GAP IDs | RES IDs |
|---|---|---|---|---|---|
| Main Cohort / Sub-Cohort | OBS-ENT-001/002 | CAN-ENT-001/002, CAN-VOC-001 | MAP-ENT-001/002, MAP-VOC-005 | GAP-008, GAP-017 | RES-008, RES-017 |
| Persona | OBS-ENT-003 | CAN-ENT-003 | MAP-ENT-003 | GAP-013, GAP-018 | RES-013, RES-018 |
| Routing Rule | OBS-ENT-004 | CAN-ENT-004 | MAP-ENT-004 | GAP-021 | RES-021 |
| State/UT | OBS-ENT-005, OBS-VOC-014 | CAN-ENT-005, CAN-VOC-015 | MAP-ENT-005, MAP-VOC-010 | GAP-011, GAP-019 | RES-011, RES-019 |
| City Migration Overlay | OBS-ENT-006 | CAN-ENT-006 | MAP-ENT-006 | GAP-020 | RES-020 |
| Meal Class | OBS-ENT-007, OBS-VOC-004/005/007 | CAN-ENT-007, CAN-VOC-004/005/008 | MAP-ENT-007, MAP-VOC-003/004/007 | GAP-007, GAP-010, GAP-022 | RES-007, RES-010, RES-022 |
| Class-Dish Option / Dish | OBS-ENT-009/010, OBS-RULE-011 | CAN-ENT-008/009, CAN-RULE-011 | MAP-ENT-008/009, MAP-RULE-004 | GAP-001, GAP-014 | RES-001, RES-014 |
| Add-on Component Class / Add-on Dish Option | OBS-ENT-011/012 | CAN-ENT-010/011 | MAP-ENT-010/011 | GAP-001, GAP-016, GAP-020 | RES-001, RES-016, RES-020 |
| Cohort | OBS-ENT-013, OBS-VOC-003/006 | CAN-ENT-012, CAN-VOC-003, CAN-VOC-006/007 | MAP-ENT-012, MAP-VOC-006/008 | GAP-002, GAP-003, GAP-009, GAP-023 | RES-002, RES-003, RES-009, RES-023 |
| Weekly Plan Day | OBS-ENT-014, OBS-REL-002 | CAN-ENT-013, CAN-REL-002 | MAP-ENT-013, MAP-REL-006 | GAP-004 | RES-004 |
| Household Addon Plan Entry | OBS-ENT-015, OBS-REL-003/011 | CAN-ENT-014, CAN-REL-003/011 | MAP-ENT-014, MAP-REL-007/008 | GAP-005 | RES-005 |
| NonVeg Logic Profile | OBS-ENT-016 | CAN-ENT-015 | MAP-ENT-015 | GAP-006 | RES-006 |
| Sub-Cohort→Persona relationship | OBS-REL-005 | CAN-REL-005 | MAP-REL-002 | GAP-012 | RES-012 |
| City Overlay weighting rule | OBS-RULE-008 | CAN-RULE-008 | MAP-RULE-005 | GAP-015 | RES-015 |

**Every GAP appears exactly once in §1's full register; this matrix groups them for readability only.**

---

## 12. Resolution Statistics

| Metric | Count | % of 23 |
|---|---|---|
| Total GAPs | 23 | 100% |
| Resolution Records created | 23 | 100% |
| Resolved automatically (No Action, closed now) | 0 | 0% |
| Founder Decision | 11 | 47.8% |
| Architecture Confirmation | 8 | 34.8% |
| Documentation Clarification | 3 | 13.0% |
| Cross-Batch Dependency | 1 | 4.3% |
| Future AGR Candidates identified | 3 | 13.0% |
| Future SER Candidates identified | 13 | 56.5% |
| AGRs created | 0 | 0% |
| SERs created | 0 | 0% |
| GAPs modified | 0 | 0% |
| GAPs closed | 0 | 0% |

---

## Regression Review — verified by direct comparison against v1.0

- ✅ Discovery, Canonicalization, Mapping, Gap Analysis — none opened for edit; all four frozen Batch 1 documents confirmed unchanged
- ✅ Architecture unchanged — DOC-P3-04 not touched
- ✅ RE unchanged — RE-DOC-01–05 not touched
- ✅ API unchanged
- ✅ Schema unchanged — no SQL generated, no migration touched
- ✅ **Every RES ID identical to v1.0** — 23 in, 23 out, none renumbered
- ✅ **Every GAP ID, Category, lineage (OBS/CAN/MAP), ownership, and Evidence cell identical to v1.0** — confirmed by direct comparison; only new columns (Resolution Confidence, Expected Evidence Source) and new content (expanded Founder Decision packs, Critical Resolution Chain) were added
- ✅ **No recommendation was changed** — the Claude Recommendations in the expanded Founder Decision packs are newly *articulated* in this revision (they did not exist as explicit fields in v1.0's simpler table) but do not contradict anything v1.0 implied; no decision was made on the Founder's behalf in either version
- ✅ No AGR created — 3 candidates identified only (§8, unchanged from v1.0)
- ✅ No SER created — 13 candidates identified only (§7, unchanged from v1.0)
- ✅ No GAP closed, resolved, or modified — all 23 Resolution Records still show Status = OPEN
- ✅ No frozen document changed — confirmed by direct comparison, no diff exists against the four frozen Batch 1 files

---

## Stage Completion Summary

- v1.0's substance fully preserved: all 23 Resolution Records, GAP references, lineage, ownership, evidence, and categories unchanged.
- v1.1 adds: Resolution Confidence (§1, per §26I), Expected Evidence Source for all 8 Architecture Confirmations (§4, per §26G), fully expanded structured decision packs for all 11 Founder Decisions (§3, per §26H — no decision made), and a Critical Resolution Chain identifying GAP-004/GAP-007 as blocking Batch 1's core seed generation, with GAP-012 on a separate BUILD-02-specific path (§9, per §26J).
- **0 GAPs resolved automatically. 0 decisions made on the Founder's behalf.**

---

## Stage 6 Readiness Summary

| Check | Status |
|---|---|
| All 23 GAPs have a Resolution Record with Confidence | ✅ Yes |
| All Architecture Confirmations name an Expected Evidence Source | ✅ Yes |
| All 11 Founder Decisions presented as structured packs, no decision made | ✅ Yes |
| Critical Resolution Chain identified | ✅ Yes — GAP-004/GAP-007 (core pipeline), GAP-012 (BUILD-02, separate) |
| Any GAP resolved, closed, or modified | ❌ No |
| Any frozen document touched | ❌ No |
| Stage 6 started | ❌ **No — awaiting Founder approval** |

**Verdict:** Batch 1 Stage 6 may begin once the Founder reviews this Resolution Package — most urgently the Critical Resolution Chain's two items (GAP-004, GAP-007), since they gate Stage 9 seed generation for Batch 1's two central tables. **Stage 6 has not begun.**

---

## Founder Approval Gate

**Stage 5 (Knowledge Resolution) governance refinement complete. No AGR, SER, or DCR has been created. No GAP has been resolved, closed, or modified. No frozen document has been changed. Stage 6 has NOT begun. Batch 2 has NOT begun.**

This package awaits Founder approval before Stage 6 starts.

Founder sign-off: _______________________ Date: ___________
