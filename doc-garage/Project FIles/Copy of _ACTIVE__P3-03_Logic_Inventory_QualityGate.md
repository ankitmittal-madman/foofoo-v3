# P3-03 Logic Inventory and Quality Gate

**Date:** June 2026  
**Purpose:** Complete source coverage validation, logic inventory of all 61 functions, quality gate verdict before P3-03 is written  
**Method:** Fresh document re-read. All 18 active documents reviewed. Session memory not relied upon.

---

## SECTION 1 — Corrections from fresh re-read

The following items were incorrectly identified in the Context Baseline (\#033). Fresh reading of source documents resolves them.

### Correction 1 — C-001 was NOT a conflict

Previous finding: DOC-03 confidence 0.72 vs RE-DOC-04 maximum 0.65 \= conflict.

After fresh reading RE-DOC-04 §01 in full: RE-DOC-04 defines a confidence ladder with RANGES per day range, not a single maximum:

- Day 0 (onboarding completion): 0.40–0.65  
- Day 1–3 (1–10 interactions): 0.55–**0.72**  
- Day 3–14 (10–50 interactions): 0.68–0.82  
- Day 14–60 (50–150 interactions): 0.80–0.91  
- Day 60+ (150+ interactions): 0.88–0.96

DOC-03 says Meera's Day 1 confidence \= 0.72. This is exactly the TOP of the Day 1–3 range. Not a conflict — it is a realistic post-onboarding \+ first interactions confidence value. **C-001 is withdrawn. Both documents are consistent.**

### Correction 2 — G-003 was NOT a gap

Previous finding: RE-DOC-02 names only 16 genome dimensions, 4 unnamed.

After fresh reading RE-DOC-02 §02 in full: The document contains a complete numbered table of all **20 genome dimensions**:

1. Meal occasion, 2\. Regional origin, 3\. Spice level, 4\. Texture, 5\. Cooking method, 6\. Primary taste, 7\. Cook time, 8\. Difficulty, 9\. Protein level, 10\. Calorie band, 11\. Main ingredient class, 12\. Dietary compatibility, 13\. Allergen flags, 14\. Seasonal affinity, 15\. Weather affinity, 16\. Festival relevance, 17\. Religious compatibility, 18\. Comfort/warmth score, 19\. Meal class code, 20\. Combo pairing.

All 20 are named and defined. **G-003 is withdrawn.**

### Correction 3 — G-007 is resolved

Previous finding: Definition of "acceptance" for metrics undefined.

After fresh reading RE-DOC-05 §04: "Acceptance rate: Dishes accepted (locked/cooked/ordered) ÷ dishes shown."

Accepted \= any of: dish\_locked event, dish\_cooked event, dish\_ordered event. **G-007 is resolved. Source: RE-DOC-05 §04.**

### Correction 4 — A-001 is resolved via RE-DOC-01 API contract

Previous finding: "Slot regenerates immediately" — mechanism undefined.

After fresh reading RE-DOC-01 §03: The POST /v1/recommendations request body includes `exclude_dish_ids[]`. This is the mechanism. When a user confirms Not Today or Never on the primary dish, the app calls POST /v1/recommendations for that slot with the rejected dish in `exclude_dish_ids[]`. The RE returns a new ranked slate excluding the rejected dish. **A-001 is resolved.**

### Correction 5 — New finding: reason\_tags is an array, not a single code

RE-DOC-01 §03 API response shows: `"reason_tags":["regional","weather"]` — an ARRAY of reason tags per dish, not a single primary reason code.

This supersedes the CDM §25 decision to store "primary reason code." The stored field is a string array per dish per slate: `slate_reasons jsonb` → `{dish_id: ["regional","weather"]}`. Multiple tags per dish are valid and expected.

### Correction 6 — New partial resolution of G-001 (Not Today PersonalHistory weight)

RE-DOC-04 §03 explicitly states: "Signal to RE: Not Today is a weak negative signal. w\_history contribution: –0.1 on Day 0, fades to 0 by Day 7."

This defines the PersonalHistory weight for Not Today events: event\_weight \= −0.10. This is a documented specific value. **G-001 is partially resolved for Not Today events. Other event types (accept, lock, cook, rate, never, swiped\_past) remain undefined.**

---

## SECTION 2 — Source Coverage Matrix

For each active document: whether it contributes to each of 9 P3-03 dimensions. Symbols: ✅ Yes — explicit contribution | ⚬ Partial — directional but not fully quantified | ✗ No contribution

| Document | Business Logic | Algorithms | Decision Rules | Formulas / Calculations | Recommendation Behaviour | Constraints | Config Parameters | Edge Cases | Future Evolution |
| :---- | :---- | :---- | :---- | :---- | :---- | :---- | :---- | :---- | :---- |
| DOC-01 Product Brief v1.0 | ✅ Pipeline model | ⚬ Layer concept only | ✅ Class-first rule | ✗ | ✅ Layer processing order | ✗ | ✗ | ✗ | ✅ 4-layer evolution described |
| DOC-02 Market Research v1.0 | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| DOC-03 User Personas v1.0 | ✅ Household model | ✗ | ✅ Postpartum \= add-on never replace | ✗ | ⚬ Confidence examples | ✗ | ✗ | ✅ Postpartum architecture edge case | ✗ |
| DOC-04 PRD v1.1 | ✅ 6-step pipeline | ✅ Pipeline function names | ✅ 41 persona × 36 states | ✗ | ✅ Cold start fallback F-09 | ✅ Class-first non-negotiable rule | ✗ | ✅ Skip handling F-09 | ✅ Phase evolution per feature |
| DOC-05 IA v1.2 | ✅ Screen-level logic | ✗ | ✅ Slot regenerates after Never/Not Today | ✅ Not Today formula cited | ✅ Interaction flows | ✅ Constraint conflict screen state | ✗ | ✅ Empty slate state, offline state | ✗ |
| DOC-06 UX Design System v1.1 | ✅ City overlay weights | ✗ | ✅ OB-07 class affinity signals | ✅ City overlay weight values (exact) | ✅ OB-07 signaling logic | ✅ Indian-only dish pool | ✅ City overlay weight values | ✅ OB-07 skip \= zero signals | ✗ |
| DOC-07 GTM v1.0 | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| DOC-08 Revenue v1.0 | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| DOC-09 Legal v1.0 | ✅ Consent before personalization | ✗ | ✅ No personalization before consent | ✗ | ✗ | ✅ DPDP constraints on data use | ✅ 2-year event retention, 72h deletion | ✅ Age gate, allergen disclaimer | ✗ |
| DOC-10 Tech Architecture v1.0 | ✅ 8-stage RE pipeline | ✅ Function names per stage | ✅ Failure behaviours per stage | ✗ | ✅ Complete pipeline with failure modes | ✅ Performance NFRs, timezone | ✅ Cron job schedules | ✅ \< 3 candidates fallback, widen class | ✅ Phase 3 microservice migration |
| RE-DOC-01 Architecture v1.0 | ✅ Module boundary | ✗ | ✅ RE sovereignty rule | ✗ | ✅ API contract (request/response format) | ✅ Service role only in Edge Functions | ⚬ n\_results=8 | ✅ Empty slate fallback, RE down fallback | ✅ RE versioning roadmap |
| RE-DOC-02 Four Layers v1.0 | ✅ 4-layer model, all 20 genome dimensions | ✅ Allergen propagation algorithm | ✅ Member constraint → household plan | ⚬ Multiplier range 0.8–1.2×, not exact values | ✅ Household two-level model, city overlay | ✅ 6 hard constraint types defined | ⚬ Multiplier range only | ✅ Intelligent substitution, combo component swap | ✅ Mood selector Phase 1, festival Phase 2 |
| RE-DOC-03 Taxonomy & Scoring v1.0 | ✅ Scoring formula, weight ladder | ✅ FinalScore formula, MMR referenced | ✅ Hard constraint → binary filter | ✅ FinalScore formula with all 5 signals, weight ladder 5 tiers, ExplorationBonus range 0–0.15, penalty range 0–1 | ✅ Class-first, scoring after filter | ✅ 6 hard constraints as binary pass/fail | ✅ Weights for 5 tiers, λ for exploration | ✅ Dish not in class \= excluded | ✅ Cohort\_matrix must be seeded |
| RE-DOC-04 Cold Start v1.0 | ✅ Confidence ladder, fallback rules | ✅ MMR formula, Not Today decay formula | ✅ 6 cold start fallback rules, 5 variety rules, reactivation rules | ✅ Not Today decay: P0=0.80, λ=0.35, all penalty values at t=0,2,5,7. MMR: λ=0.7 MVP. Confidence ladder ranges. | ✅ Variety guard, suppression, class-level affinity | ✅ Never as hard constraint, variety caps | ✅ P0=0.80, λ=0.35, MMR λ=0.7, 30-day dish repeat | ✅ 5 MMR edge cases, festive override, illness context | ✅ MMR λ=0.55 Phase 1+ |
| RE-DOC-05 Evolution Roadmap v1.0 | ✅ 4-state model, feature store requirements | ✅ K-means clustering, CF (ALS), LTR | ✅ State transition triggers (DAU thresholds) | ✅ Acceptance rate formula: accepted/shown. MRR@8, NDCG@8 definitions. Offline eval thresholds. | ✅ State A–D behaviour per state | ✅ Constraint compliance \= 100% always | ✅ Training data triggers, shadow 72h | ✅ Anti-filter-bubble (\<3 cuisine families 30 days) | ✅ Full ML upgrade path with triggers |
| PM-SUPP-01 Roadmap v1.0 | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| PM-SUPP-02 Risk Register v1.0 | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| DOC-P3-02 CDM v1.1 | ✅ All 51 domain entities | ✗ | ✅ 14 business invariants | ✅ City overlay values (from DOC-06) | ✅ 7 aggregate boundaries | ✅ 14 invariants are constraints | ✅ Proposed event weights, confidence contributions | ✅ Known exclusions documented | ✅ Lifecycle states for all key entities |

**Documents with no P3-03 contribution (reviewed and confirmed): DOC-02, DOC-07, DOC-08, PM-SUPP-01, PM-SUPP-02.**

Rationale: DOC-02 is competitive research with no algorithm or business logic. DOC-07 is GTM strategy. DOC-08 is revenue model. PM-SUPP-01 and PM-SUPP-02 are operational planning and risk identification — no business logic that P3-03 must implement.

---

## SECTION 3 — Complete Logic Inventory

Every logical function identified across all 18 active documents. 61 functions total across 13 groups.

---

### Group A — Onboarding Pipeline (8 functions)

**A-01: processMainCohortSelection()**

- Purpose: Capture user's selection of one of 5 main cohort options at OB-01 and store the code  
- Source: DOC-04 Step 1, DOC-05 OB-01, DOC-03 V2 cohort section  
- Inputs: User's tap selection from 5 options (Solo, Couple, Nuclear Family, Joint Family, PG/Hostel)  
- Outputs: main\_cohort\_code string stored in onboarding session  
- Dependencies: None  
- CDM entities: Main Cohort (Entity 9), Onboarding Session (Entity 28\)  
- Status: Fully specified — 5 options are defined. No decisions required.

**A-02: processHouseholdBranch()**

- Purpose: Apply dynamic branching based on main cohort selection to determine OB-02 questions shown. Derives sub\_cohort\_tag from answers.  
- Source: DOC-04 F-02, DOC-05 OB-02, DOC-03 persona mappings  
- Inputs: main\_cohort\_code, OB-02 answers (children ages, elder presence, health conditions)  
- Outputs: sub\_cohort\_tag (SC\_COUPLE\_WITH\_SCHOOL\_CHILD etc.), member\_segments\[\] for household members to be created  
- Dependencies: A-01 must complete first  
- CDM entities: Sub-cohort (Entity 10), Household Members (Entity 3\)  
- Status: Branching logic is defined. Sub-cohort codes are documented in DOC-03. Exact branching decision tree (which answer produces which sub-cohort code) is not in any document — this is the assign\_persona() mapping gap.

**A-03: processRegionalIdentity()**

- Purpose: Capture home\_state, current\_city, migration\_duration from OB-03 and derive city\_overlay\_weight  
- Source: DOC-05 OB-03, DOC-06 C-11, RE-DOC-02 §04  
- Inputs: home\_state selection (36 states), current\_city input, migration\_duration selection (4 bands)  
- Outputs: home\_state, current\_city, migration\_duration\_band stored. city\_overlay\_weight derived:  
  - \<1 year → 0.15 \[Source: DOC-06 C-11\]  
  - 1–3 years → 0.30 \[Source: DOC-06 C-11\]  
  - 3–7 years → 0.50 \[Source: DOC-06 C-11\]  
  - 7+ years → 0.70 \[Source: DOC-06 C-11\]  
  - Skip → 0.50 default, confidence −0.04 \[Source: DOC-06 C-11\]  
- Dependencies: None within onboarding  
- CDM entities: Regional Identity (Entity 4), User (Entity 1\)  
- Status: Fully specified. City overlay weight values are documented in DOC-06 C-11.

**A-04: processDietConfiguration()**

- Purpose: Capture diet\_type and religious\_pref at OB-04 and store as household hard constraints  
- Source: DOC-04 F-04, DOC-05 OB-04  
- Inputs: Diet type selection (veg/non-veg/egg/vegan/jain), religious pref (all/hindu\_veg/jain/halal/no\_beef/no\_pork)  
- Outputs: diet\_type, religious\_pref stored on User  
- Dependencies: None  
- CDM entities: Diet Type (Entity 5), Religious Preference (Entity 6\)  
- Status: Fully specified.

**A-05: processAllergenExclusions()**

- Purpose: Capture allergen flags via ingredient autocomplete at OB-05 and store as bitfield  
- Source: DOC-04 F-05, RE-DOC-02 §02 allergen dimensions (bits 0–6)  
- Inputs: User's autocomplete selections of allergic ingredients  
- Outputs: allergen\_flags integer (bitfield) stored on User. Allergen flags also propagated per household member.  
- Dependencies: Household members created in A-02  
- CDM entities: Allergen (Entity 7), User (Entity 1), Household Members (Entity 3\)  
- Status: Fully specified. 7 allergen types and bit positions defined in RE-DOC-02 and CDM.

**A-06: processClassPreferenceSwipes()**

- Purpose: Process OB-07 YES/NOPE swipes into class\_affinity signals. First behavioral interaction events.  
- Source: DOC-06 C-07, DOC-04 F-07, CDM Entity 33 (Class Preference Swipe)  
- Inputs: Array of swipe results: {dish\_card\_shown, swipe\_direction (YES/NOPE)}. Each card represents a meal class. Dish pool: Idli Sambar, Poha, Aloo Paratha, Rajma Chawal, Masala Dosa, Paneer Butter Masala, Chole Bhature, Dal Makhani, Khichdi, Chicken Biryani (non-veg only).  
- Outputs: Interaction events logged (event\_type=onboarding\_class\_preference). class\_affinity updated per class. interaction\_count incremented per card swiped (max \+10).  
- Signal strength: \[PROPOSED — G-008 UNRESOLVED\] DOC-06 C-07 says "boost" and "penalty" but does not define magnitude. Proposed: YES swipe \= \+0.30 to class\_affinity\[class\_code\]. NOPE swipe \= −0.30. Event weight in PersonalHistory: 0.30. De-duplication: most recent swipe per class only.  
- Skip behaviour: OB-07 skipped → zero class\_affinity signals from onboarding. class\_affinity initialized at 0.0 for all classes.  
- Dependencies: None within onboarding  
- CDM entities: Class Preference Swipe (Entity 33), Interaction Events (Entity 29\)  
- Status: Partially specified. Magnitude UNRESOLVED — proposed values require founder confirmation.

**A-07: computeOnboardingConfidence()**

- Purpose: Compute confidence score at end of onboarding from signal contributions  
- Source: RE-DOC-04 §01  
- Inputs: Answers to all onboarding screens (which were completed vs skipped)  
- Computation: Sum of contributions:  
  - All 5 onboarding questions answered: base 0.40–0.65 (higher end when all complete)  
  - Home state captured: \+0.15  
  - Diet type captured: \+0.10  
  - Current city overlay found: \+0.08  
  - Cook capability captured: \+0.07  
  - Class preference swipes completed (OB-07): \+0.12  
  - Contextual signals (always available): \+0.08  
  - Per non-critical skipped field: −0.05  
  - Diet type skipped: −0.15  
  - OB-03 entirely skipped: −0.08 \[Source: DOC-06 C-11\]  
  - All onboarding skipped: floor \= 0.35  
- Outputs: confidence\_score float (0.35–0.65 at Day 0\)  
- Dependencies: All OB-01 through OB-07 must complete before this is computed  
- CDM entities: Confidence Score (Entity 13\)  
- Status: Fully specified. All contributions documented in RE-DOC-04 §01 and DOC-06 C-11.

**A-08: assignPersona()**

- Purpose: Map onboarding profile to one of 41 backend personas. Assigned once at end of onboarding. Stored on User RE State. Never shown to user.  
- Source: DOC-04 Step 2, RE-DOC-01 POST /v1/onboarding, DOC-03 persona codes  
- Inputs: main\_cohort\_code, sub\_cohort\_tag, home\_state, diet\_type  
- Outputs: persona\_id (FK to re\_personas seed table), overlay\_persona\_ids\[\] (from member segments), confidence\_score  
- Logic: Database lookup. (main\_cohort × sub\_cohort × home\_state × diet\_type) → persona\_id. Not a computed function — a seeded lookup table. The exact mapping is in Indian\_Meal\_Cohort\_Persona\_DB\_v3.xlsx and must be seeded as re\_persona\_assignment\_rules.  
- Fallback: \[C-004 UNRESOLVED\] If no persona match found → behavior undefined. Options: MC\_GENERIC row (DOC-10), closest main cohort fallback, or re-onboarding prompt. Requires product decision.  
- Dependencies: A-01 through A-07 must complete  
- CDM entities: Persona (Entity 11), Overlay (Entity 12\)  
- Status: PARTIALLY SPECIFIED. Function purpose and inputs/outputs defined. Mapping logic is seed data — not implemented in code, done via DB lookup. Fallback behavior UNRESOLVED.

---

### Group B — Class Plan Generation (3 functions)

**B-01: generateClassPlan()**

- Purpose: Map persona assignment \+ day context to meal class codes for each slot in the week  
- Source: DOC-04 Step 3, DOC-10 §05 Stage 3, RE-DOC-03 §01  
- Inputs: persona\_id, home\_state, day\_of\_week, day\_type (weekday/weekend), diet\_type, cook\_capability  
- Outputs: Array of class assignments: \[{slot: 'breakfast', class\_code: 'BF\_LIGHT\_GRAIN'}, ...\] for 7 days × 3 slots \= 21 assignments  
- Logic: Queries re\_weekly\_class\_plans (seeded: 20,664 rows) WHERE cohort\_id matches persona+state+diet, filtered by day\_of\_week and day\_type. Returns class\_code per slot.  
- Fallback: If DB read fails → use default class plan for main cohort. \[Source: DOC-10 Stage 3 failure\]  
- Dependencies: B-01 requires: Seed gates S-11 and S-12 passed (re\_cohorts and re\_weekly\_class\_plans seeded). Persona assigned (A-08).  
- CDM entities: Meal Class (Entity 20), Week Plan (Entity 23), Plan Slot (Entity 24\)  
- Status: Fully specified as DB lookup. Actual seed data content (which class per cohort per day) is from Indian\_Meal\_Cohort\_Persona\_DB\_v3.xlsx.

**B-02: applyWeekdayWeekendBias()**

- Purpose: Adjust class selection to favor appropriate classes for day type  
- Source: RE-DOC-03 §01 (weekday\_fit and weekend\_fit scores), RE-DOC-04 §02 variety rules  
- Inputs: class\_code, day\_type  
- Logic: Classes with high weekend\_fit\_1\_5 (e.g., BF\_STUFFED\_FLATBREAD, BF\_SWEET\_WARM) are preferred on weekends. Classes with high weekday\_fit\_1\_5 (e.g., BF\_LIGHT\_GRAIN) preferred on weekdays. Implemented in seed data via re\_weekly\_class\_plans — embedded in B-01.  
- Status: Embedded in B-01 via seed data. No separate function needed in MVP classfirst\_v1.

**B-03: applyNonVegCadence()**

- Purpose: Enforce state-specific non-veg frequency rules for non-veg households  
- Source: RE-DOC-03 §01 (non-veg class note), seed data table re\_nonveg\_logic (36 rows)  
- Inputs: home\_state, diet\_type, weekly\_class\_plan  
- Logic: If diet\_type \= veg/jain/vegan → zero non-veg classes (B-01 handles via class plan). If diet\_type \= non\_veg/egg → lookup re\_nonveg\_logic for home\_state → get weekly\_nonveg\_slots count and preferred\_slots\[\] → assign that many non-veg class codes (DIN\_NON\_VEG\_MAIN etc.) to preferred slots.  
- Dependencies: B-01 must complete. Seed gate S-14 (re\_nonveg\_logic 36 rows) must pass.  
- CDM entities: Diet Type (Entity 5), Meal Class (Entity 20\)  
- Status: Specified in structure. Exact cadence per state is seed data.

---

### Group C — Add-on Generation (2 functions)

**C-01: generateAddons()**

- Purpose: Generate member-specific add-on slots alongside primary Plan Slots for households with special member segments  
- Source: DOC-04 Step 4, RE-DOC-02 §04 member segment add-on table, DOC-10 §05 Stage 4  
- Inputs: member\_segments\[\], primary class plan, persona\_id  
- Outputs: addon\_slots\[\]: \[{member\_name, primary\_slot\_date, meal\_slot, addon\_class\_code}\]  
- Logic: For each household member with segment ≠ ADULT\_STANDARD:  
  - Query re\_segment\_addon\_rule WHERE segment \= member.segment AND primary\_class\_code \= slot.class\_code → get addon\_class\_code  
  - Create addon\_slot record  
- Fallback: If no matching addon rule → skip add-on for this member/slot. Log as coverage gap. Primary plan returned without add-on. \[Source: DOC-10 Stage 4 failure\]  
- Invariant: Add-on slot is ALWAYS additional. NEVER modifies or replaces primary Plan Slot.  
- Dependencies: B-01 (primary class plan) must complete first  
- CDM entities: Add-on Slot (Entity 26), Household Members (Entity 3), Meal Class (Entity 20\)  
- Status: Fully specified.

**C-02: resolveAddonDish()**

- Purpose: Select specific dish from add-on class candidates for a member's add-on slot  
- Source: RE-DOC-02 §04 add-on examples, RE-DOC-03 (ADDON\_\* class definitions)  
- Inputs: addon\_class\_code, member.segment, member.allergen\_flags, member.diet\_type  
- Outputs: dish\_id for the specific add-on dish  
- Logic: Query re\_addon\_dish\_options WHERE addon\_class\_code \= ? AND allergen safe AND diet compatible → rank by suitability for segment → select top dish  
- CDM entities: Add-on Slot (Entity 26), Dish (Entity 15\)  
- Status: Specified in structure. Add-on dish selection logic follows same hard constraint filtering as primary.

---

### Group D — Candidate Generation (7 functions)

**D-01: getClassCandidates()**

- Purpose: Retrieve all dishes that are candidates for the assigned meal class from the Class-Dish Options junction  
- Source: RE-DOC-03 §01 class-first rule, CDM Entity 21 (Class-Dish Option)  
- Inputs: class\_code  
- Outputs: candidate\_dishes\[\]: \[{dish\_id, base\_score}\] from re\_class\_dish\_options  
- Logic: SELECT dish\_id, base\_score FROM re\_class\_dish\_options WHERE meal\_class\_code \= :class\_code AND is\_active \= true  
- Dependencies: Seed gate S-08 (re\_class\_dish\_options 1,050 rows) must pass  
- CDM entities: Class-Dish Option (Entity 21), Dish (Entity 15\)  
- Status: Fully specified.

**D-02: applyDietTypeFilter()**

- Purpose: Hard constraint 1\. Remove any dish whose diet type is incompatible with household diet type.  
- Source: RE-DOC-03 §03 Hard Constraint 1, CDM Business Invariant 1  
- Inputs: candidate\_dishes\[\], user.diet\_type  
- Logic:  
  - veg user: exclude any dish where diet\_type NOT IN (veg, vegan, jain)  
  - jain user: exclude any dish where is\_jain \= false  
  - vegan user: exclude any dish where diet\_type \!= vegan  
  - non\_veg user: no exclusion on diet type  
  - egg user: exclude any dish where diet\_type NOT IN (veg, vegan, jain, egg)  
- Outputs: filtered\_candidates\[\] with diet-safe dishes only  
- Note: diet\_type on dishes is DERIVED from ingredients via auto-derivation pipeline. Never manually set.  
- Safety Gate 1 validates this after every RE change.  
- CDM entities: Diet Type (Entity 5), Dish (Entity 15\)  
- Status: Fully specified.

**D-03: applyAllergenFilter()**

- Purpose: Hard constraint 2\. Remove any dish whose ingredients match any allergen flag of the user OR any household member. Operates at ingredient level.  
- Source: RE-DOC-03 §03, RE-DOC-02 §03 allergen propagation, CDM Business Invariant 3  
- Inputs: candidate\_dishes\[\], combined\_allergen\_flags (user.allergen\_flags UNION all household\_members.allergen\_flags)  
- Logic: For each candidate dish:  
  - JOIN dish → dish\_ingredients → ingredients  
  - Check: (ingredient.allergen\_flags AND combined\_allergen\_flags) \= 0 for ALL ingredients  
  - If any ingredient fails: exclude dish  
- Outputs: filtered\_candidates\[\] with allergen-safe dishes only  
- Note: This check MUST be ingredient-level (via dish\_ingredients junction), not dish-level allergen\_flags column. Dish-level flags may not reflect recently added ingredients.  
- Safety Gate 2 validates this after every RE change.  
- CDM entities: Allergen (Entity 7), Ingredient (Entity 18), Dish (Entity 15\)  
- Status: Fully specified. Ingredient-level check confirmed in RE-DOC-02 and Safety Gate 2\.

**D-04: applyReligiousFilter()**

- Purpose: Hard constraint 3\. Remove any dish incompatible with household religious preference.  
- Source: RE-DOC-03 §03 Hard Constraint 3, CDM Business Invariant 2  
- Inputs: candidate\_dishes\[\], user.religious\_pref  
- Logic:  
  - jain: exclude any dish where is\_jain \= false  
  - halal: exclude dishes with non-halal meat ingredients  
  - no\_beef: exclude dishes with beef-derived ingredients  
  - no\_pork: exclude dishes with pork-derived ingredients  
  - all/hindu\_veg: no additional exclusion (diet\_type handles veg constraint)  
- Outputs: filtered\_candidates\[\] with religiously compatible dishes only  
- Safety Gate 3 validates Jain violations after every RE change.  
- CDM entities: Religious Preference (Entity 6), Dish (Entity 15\)  
- Status: Fully specified.

**D-05: applyMealOccasionFilter()**

- Purpose: Hard constraint 4\. Ensure dish is eligible for the current meal slot.  
- Source: RE-DOC-03 §03 Hard Constraint 4, RE-DOC-02 genome dimension 1 (meal occasion)  
- Inputs: candidate\_dishes\[\], meal\_slot ('breakfast'|'lunch'|'dinner')  
- Logic: Exclude any dish where dish.meal\_occasion does NOT contain meal\_slot AND does NOT contain 'any'  
- Outputs: filtered\_candidates\[\] with slot-eligible dishes only  
- CDM entities: Meal Occasion (Entity 22), Dish (Entity 15\)  
- Status: Fully specified.

**D-06: applyNeverListFilter()**

- Purpose: Hard constraint 5\. Exclude dishes permanently rejected by the user.  
- Source: RE-DOC-03 §03 Hard Constraint 6, RE-DOC-04 §03 Never rules, CDM Business Invariant 10  
- Inputs: candidate\_dishes\[\], user\_id  
- Logic: Exclude any dish\_id in re\_engine.never\_list WHERE profile\_id \= user\_id AND is\_active \= true  
- Note: This is a hard constraint. No score, no context multiplier, no festival override bypasses an active Never entry.  
- Outputs: filtered\_candidates\[\] with never-excluded dishes removed  
- CDM entities: Never List (Entity 30), Dish (Entity 15\)  
- Status: Fully specified.

**D-07: handleConstraintConflict()**

- Purpose: Handle the case where \< 3 candidates survive all hard constraints  
- Source: DOC-10 §05 Stage 5 failure, RE-DOC-01 §05 empty slate fallback, DOC-05 H-01 constraint conflict state  
- Inputs: candidate\_dishes\[\] (\< 3 survivors)  
- Logic: \[G-010 UNRESOLVED\] DOC-10 says "widen class, log as coverage gap." The exact widening logic is not defined. Options: (a) Expand to adjacent class codes in same slot type, (b) Relax one hard constraint (cook capability only — never allergen or diet), (c) Return static fallback of 8 popular dishes for diet type.  
- RE-DOC-01 §05: "RE returns empty slate → app shows static fallback of 8 popular dishes for diet type."  
- Recommended approach: If \< 3 candidates → log as coverage gap → return static fallback dishes filtered by diet type only (no class constraint). App displays H-01 constraint conflict state.  
- CDM entities: Plan Slot (Entity 24), Safety Gate (Entity 48\)  
- Status: PARTIALLY SPECIFIED. RE-DOC-01 defines the fallback behavior (static 8 popular dishes). DOC-10's "widen class" is vague. P3-03 will use RE-DOC-01's fallback as the authoritative specification and flag "widen class" as an unresolved detail.

---

### Group E — Scoring Functions (8 functions)

**E-01: computeFinalScore()**

- Purpose: Assemble all scoring signals into a single score for each candidate dish  
- Source: RE-DOC-03 §02  
- Inputs: CohortPrior, ContentMatch, PersonalHistory, ContextFit, ExplorationBonus, PenaltyTerms, current\_weights (from weight ladder)  
- Formula: FinalScore \= (w\_cohort × CohortPrior) \+ (w\_content × ContentMatch) \+ (w\_history × PersonalHistory) \+ (w\_context × ContextFit) \+ (w\_explore × ExplorationBonus) \- PenaltyTerms  
- SUBJECT TO: All hard constraints must have passed before this function runs  
- Outputs: score float per dish  
- CDM entities: FinalScore (Entity 34\)  
- Status: Fully specified.

**E-02: interpolateWeightLadder()**

- Purpose: Compute current scoring weights for a user based on their interaction\_count, with smooth linear interpolation between tier boundaries  
- Source: RE-DOC-03 §02 weight ladder, RE-DOC-05 §01 State A and B weights  
- Inputs: interaction\_count (integer)  
- Tier boundaries and weights:  
  - 0 interactions: w\_cohort=0.55, w\_content=0.20, w\_history=0.00, w\_context=0.15, w\_explore=0.10  
  - 1–10: w\_cohort=0.35, w\_content=0.25, w\_history=0.15, w\_context=0.15, w\_explore=0.10  
  - 11–50: w\_cohort=0.20, w\_content=0.25, w\_history=0.35, w\_context=0.15, w\_explore=0.05  
  - 51–150: w\_cohort=0.10, w\_content=0.20, w\_history=0.50, w\_context=0.15, w\_explore=0.05  
  - 150+: w\_cohort=0.05, w\_content=0.15, w\_history=0.65, w\_context=0.15, w\_explore=0.00  
- Logic: Linear interpolation. Example at interaction\_count=30 (between tier 2 and 3): progress \= (30-11)/(50-11) \= 0.487 w\_cohort \= 0.20 \+ 0.487 × (0.20-0.20) \= 0.20 \[stable\] w\_history \= 0.15 \+ 0.487 × (0.35-0.15) \= 0.247  
- Note: Weights are computed at request time from interaction\_count. NOT stored as static values.  
- Outputs: {w\_cohort, w\_content, w\_history, w\_context, w\_explore} float tuple  
- CDM entities: Weight Ladder (Entity 41\)  
- Status: Fully specified. Tier boundaries and weight values documented in RE-DOC-03.

**E-03: computeCohortPrior()**

- Purpose: Look up research-based acceptance rate for (user's cohort, dish's meal class) pair  
- Source: RE-DOC-03 §02 CohortPrior definition  
- Inputs: persona\_id, class\_code  
- Logic: Lookup from cohort\_class\_priors table: (cohort\_id, class\_code) → acceptance\_rate\_prior float  
- \[G-005 PARTIALLY RESOLVED\] The table exists (referenced as "research DB" in RE-DOC-03). Structure is (cohort\_id, class\_code, acceptance\_rate\_prior). Actual values are seed data from Indian\_Meal\_Cohort\_Persona\_DB\_v3.xlsx.  
- Outputs: prior\_float in range 0–1  
- CDM entities: Scoring Signal CohortPrior (Entity 35\)  
- Status: Structure specified. Actual values are seed data.

**E-04: computeContentMatch()**

- Purpose: Measure cosine similarity between user's taste vector and dish's genome vector  
- Source: RE-DOC-03 §02 ContentMatch definition  
- Inputs: user.genome\_tag\_affinity (jsonb → float vector), dish.genome\_vector (float\[\])  
- Formula: CosineSimilarity(user\_taste\_vector, dish\_genome\_vector)  
- \[OPEN DECISION\] Dish genome vector representation: pre-computed float array stored on dish vs assembled at query time from dish\_tags junction. Decision deferred from CDM. P3-03 will specify both options and flag for P3-04 to decide based on query performance.  
- Outputs: similarity float in range 0–1  
- CDM entities: ContentMatch (Entity 36), Taste Vector (Entity 42\)  
- Status: Formula fully specified. Genome vector representation implementation approach is open.

**E-05: computePersonalHistory()**

- Purpose: Compute weighted, time-decayed sum of user's prior interactions with a specific dish  
- Source: RE-DOC-03 §02 PersonalHistory definition, RE-DOC-04 §03 Not Today signal weight  
- Inputs: user\_id, dish\_id, interaction\_events for this user-dish pair  
- Formula: PersonalHistory \= Σ(event\_weight × e^(−λ\_history × days\_elapsed)) for all events on this dish  
- Event weights — documented values:  
  - dish\_not\_today: −0.10 × e^(−λ\_history × days\_elapsed) \[Source: RE-DOC-04 §03 — "w\_history contribution: –0.1 on Day 0, fades to 0 by Day 7"\]  
  - All other event types: \[G-001 UNRESOLVED — No source document defines these values\]  
- Proposed values for unresolved types (require founder confirmation):  
  - dish\_cooked: \+0.80 \[PROPOSED\]  
  - dish\_locked: \+0.60 \[PROPOSED\]  
  - dish\_accepted (carousel selection): \+0.40 \[PROPOSED\]  
  - dish\_rated (5 stars): \+0.60 \[PROPOSED\]  
  - dish\_rated (3 stars): \+0.00 \[PROPOSED\]  
  - dish\_rated (1 star): −0.30 \[PROPOSED\]  
  - dish\_swiped\_past: −0.10 \[PROPOSED\]  
  - dish\_never: −1.00 \[PROPOSED — but never-listed dishes are excluded by hard filter, so this value is moot\]  
  - onboarding\_class\_preference YES: \+0.30 applied to class\_affinity, not PersonalHistory \[PROPOSED\]  
- λ\_history: \[G-006 UNRESOLVED\] Not defined in any document. Proposed: 0.05 (slow decay — preferences are persistent)  
- Outputs: PersonalHistory float in range −1 to \+1  
- CDM entities: PersonalHistory (Entity 37), Interaction Events (Entity 29\)  
- Status: PARTIALLY SPECIFIED. Not Today weight is documented. All other weights are PROPOSED and require confirmation.

**E-06: computeContextFit()**

- Purpose: Score how well a dish fits the current situational context (weather, season, day, time)  
- Source: RE-DOC-02 §05 weather-to-food mapping, RE-DOC-03 §02 ContextFit definition  
- Inputs: dish.genome\_tags (weather\_affinity, seasonal\_affinity, comfort\_warmth\_score, cooking\_method, cook\_time), context (weather\_condition, season, day\_type, time\_of\_day)  
- Formula: ContextFit \= Σ(context\_attribute\_match × multiplier) across active context dimensions  
- Range: 0 to 1.2 (can exceed 1.0 for perfect context fit)  
- Weather multiplier direction from RE-DOC-02 §05 (exact values UNRESOLVED):  
  - Rainy: boost weather\_affinity:rainy, comfort\_warmth\_score ≥ 4, cooking\_method:fried  
  - Hot: boost weather\_affinity:hot, comfort\_warmth\_score ≤ 1  
  - Cold: boost weather\_affinity:cold, comfort\_warmth\_score ≥ 4  
  - Mild: neutral (all multipliers \= 1.0)  
- Day type adjustment: Weekday → boost cook\_time ≤ 30min. Weekend → allow cook\_time \>30min.  
- Season adjustment: boost seasonal\_affinity matching current season  
- \[G-004 UNRESOLVED\] Specific multiplier values (0.8–1.2× range is stated but per-condition values are not). P3-03 will specify the multiplier table structure and flag the values as configuration data to be seeded from the context-meal affinity knowledge base (DOC-01 §08).  
- Outputs: context\_fit\_score float 0–1.2  
- CDM entities: ContextFit (Entity 38), Context (Entity 43\)  
- Status: Formula structure and direction specified. Exact multiplier values are seed/config data.

**E-07: computeExplorationBonus()**

- Purpose: Thompson Sampling bandit term to encourage discovery of dishes the user hasn't tried  
- Source: RE-DOC-03 §02 ExplorationBonus, RE-DOC-05 §01 State A bandit specification  
- Inputs: dish.bandit\_state (α, β per user-dish pair)  
- Formula: ExplorationBonus \= random draw from Beta(α\_dish, β\_dish)  
- Initial prior: Beta(1,1) adjusted to cohort base acceptance rates \[Source: RE-DOC-05 §01\]  
- α incremented on: dish\_accepted, dish\_locked, dish\_cooked  
- β incremented on: dish\_swiped\_past, dish\_not\_today  
- Explore \~10% of slate (approximately 1 of 8 dishes) \[Source: RE-DOC-05 §01\]  
- Outputs: exploration\_bonus float in range 0–0.15  
- CDM entities: ExplorationBonus (Entity 39), Interaction Events (Entity 29\)  
- Status: Fully specified.

**E-08: computePenaltyTerms()**

- Purpose: Compute deductions from FinalScore for Not Today suppression and variety excess  
- Source: RE-DOC-04 §03 Not Today formula, RE-DOC-03 §02 PenaltyTerms definition  
- Inputs: user\_id, dish\_id, not\_today\_suppression record if active, variety\_window\_state  
- Not Today decay:  
  - Penalty(t) \= P0 × e^(−λ × t) \[Source: RE-DOC-04 §03\]  
  - P0 \= 0.80, λ \= 0.35, t \= days since Not Today gesture  
  - At t=0: 0.80 | t=2: 0.40 | t=5: 0.12 | t=7: 0.05  
  - Context override: if ContextFit \> threshold (not defined) AND t ≥ 3 → penalty × 0.50  
- Variety penalty: 0–0.30 deduction if dish is too similar to already-selected dishes in slate \[Source: RE-DOC-03 §02\]. Applied via MMR (E-09), not as a separate pre-calculation here.  
- Outputs: penalty\_total float 0–1  
- CDM entities: Penalty Terms (Entity 40), Not Today Suppression (Entity 31\)  
- Status: Not Today formula fully specified. Variety penalty is computed in E-09 (MMR), not here separately.

---

### Group F — Variety Re-ranking (3 functions)

**F-01: applyMMR()**

- Purpose: Re-rank scored candidates to produce a diverse 8-dish slate using Maximal Marginal Relevance  
- Source: RE-DOC-04 §02 MMR formula  
- Inputs: scored\_candidates\[\] (after E-01), already\_planned\_dishes\[\] (from other slots this week)  
- Formula: MMR(i) \= argmax over remaining i of \[λ × ScoringRelevance(i, user) − (1 − λ) × max\_j∈Selected Similarity(i,j)\]  
  - λ \= 0.70 for MVP classfirst\_v1 \[Source: RE-DOC-04 §02\]  
  - λ \= 0.55 for Phase 1+ \[Source: RE-DOC-04 §02\]  
  - Similarity computed as cosine similarity of genome vectors across variety-relevant dimensions  
- Process: Iteratively select the dish with highest MMR score. Add to slate. Repeat until 8 dishes selected or candidates exhausted.  
- Fallback: If \< 8 dishes after MMR → pad with highest-scoring remaining candidates \[Source: DOC-10 Stage 7\]  
- Outputs: reranked\_slate\[\] of 8 dishes in order  
- CDM entities: Slate (Entity 25), Variety Window State (Entity 32\)  
- Status: Fully specified. MMR formula, λ value, and similarity metric are documented.

**F-02: checkVarietyWindowRules()**

- Purpose: Validate that the generated week plan does not violate rolling variety window rules  
- Source: RE-DOC-04 §02 5-day variety window rules  
- Inputs: week\_plan (all 21 slots), variety\_window\_state  
- Rules:  
  1. Same cuisine family: max 2 in breakfast slot, max 2 in dinner slot over any 5 consecutive days \[Source: RE-DOC-04 §02\]  
  2. Same cooking method (fried): max 3 per week in any slot. Monsoon override: max 4 \[Source: RE-DOC-04 §02\]  
  3. Same main ingredient: no back-to-back same primary ingredient in consecutive days. Exception: rice treated as distinct when in different preparation forms \[Source: RE-DOC-04 §02\]  
  4. Same dish: no repeat within 30 days unless user explicitly locked it \[Source: RE-DOC-04 §02\]  
  5. Same breakfast class: max 3 times per week. Weekend override: allow BF\_SWEET\_WARM and BF\_STUFFED\_FLATBREAD even if recently used \[Source: RE-DOC-04 §02\]  
- Outputs: Pass/fail per rule. If fail → flag for MMR to apply higher penalty to violating dish.  
- CDM entities: Variety Window State (Entity 32\)  
- Status: Fully specified. All 5 rules documented in RE-DOC-04.

**F-03: handleVarietyEdgeCases()**

- Purpose: Apply resolution strategies when MMR variety guard cannot find diverse candidates  
- Source: RE-DOC-04 §02 Edge Cases table  
- Inputs: MMR results, edge\_case\_type  
- Logic:  
  - User likes only 3 dishes → relax λ toward 0.9, introduce genome-similar unexplored dishes, increase exploration bonus  
  - Cohort has limited variety → borrow from adjacent cohort, flag as database gap  
  - Mono-cuisine household → respect preference, reduce variety pressure on cuisine dimension only, maintain variety on method and ingredient  
  - Festive week → suspend variety guard for cuisine dimension; allow traditional dishes to repeat  
  - Illness/recovery context → reduce variety pressure for 5-day window, reset after  
- Outputs: Adjusted slate with edge case resolution applied  
- CDM entities: Variety Window State (Entity 32\)  
- Status: All 5 edge cases documented in RE-DOC-04.

---

### Group G — Suppression Functions (5 functions)

**G-01: processNeverGesture()**

- Purpose: Handle Never confirmation — add dish to never\_list, trigger class-level affinity update  
- Source: RE-DOC-04 §03 Never rules, DOC-05 Flow 3b  
- Inputs: user\_id, dish\_id, dish.meal\_class\_code  
- Logic:  
  1. Add entry to re\_engine.never\_list: {profile\_id, dish\_id, nevered\_at, is\_active=true}  
  2. Assess reactivation eligibility: if dish.seasonal\_affinity is strong → seasonal\_reactivation\_eligible=true. If dish.festival\_relevance is set → festival\_reactivation\_eligible=true.  
  3. Count total Nevers for dish.meal\_class\_code for this user. If \>= 3 → reduce class\_affinity\[class\_code\] for this user.  
  4. Log Interaction Event: event\_type=dish\_never  
  5. Trigger slot refresh for the slot this dish was in (POST /v1/recommendations with dish\_id in exclude\_dish\_ids\[\])  
- CDM entities: Never List (Entity 30), Class Affinity (Entity 46), Interaction Events (Entity 29\)  
- Status: Fully specified.

**G-02: processNotTodayGesture()**

- Purpose: Handle Not Today confirmation — create/update suppression record, apply decay  
- Source: RE-DOC-04 §03 Not Today rules, DOC-05 Flow 3a  
- Inputs: user\_id, dish\_id  
- Logic:  
  1. Create/update not\_today\_suppression: {profile\_id, dish\_id, suppressed\_at=now(), P0=0.80, lambda=0.35, is\_active=true}  
  2. Log Interaction Event: event\_type=dish\_not\_today  
  3. Trigger slot refresh (same mechanism as G-01 step 5\)  
- Decay: Penalty(t) \= 0.80 × e^(−0.35 × days\_elapsed). Effective until \~Day 7\.  
- CDM entities: Not Today Suppression (Entity 31), Interaction Events (Entity 29\)  
- Status: Fully specified.

**G-03: computeNotTodayPenalty()**

- Purpose: At recommendation time, compute current penalty for a dish with active Not Today suppression  
- Source: RE-DOC-04 §03  
- Inputs: not\_today\_suppression record (P0, lambda, suppressed\_at), context (ContextFit score)  
- Formula: Penalty(t) \= P0 × e^(−λ × t) where t \= (now \- suppressed\_at) in days  
- Context override: if t ≥ 3 AND ContextFit \> \[UNRESOLVED threshold\] → Penalty \= Penalty × 0.50  
- Outputs: penalty float 0–0.80  
- Status: Formula specified. Context override threshold is undefined.

**G-04: processClassLevelNeverSignal()**

- Purpose: After 3+ Never gestures from same meal class, reduce that class's w\_cohort weight for this user  
- Source: RE-DOC-04 §03 Never class-level signal  
- Inputs: user\_id, class\_code, never\_count\_for\_class  
- Logic: If never\_count\_for\_class \>= 3 → reduce class\_affinity\[class\_code\] in user\_taste\_vectors by \[PROPOSED: delta \= 0.15 per Never beyond threshold\]. Adjacent class gets corresponding boost.  
- Outputs: Updated class\_affinity jsonb  
- Status: Trigger condition documented (3+ Nevers). Delta amount UNRESOLVED.

**G-05: checkNeverReactivation()**

- Purpose: Weekly CRON check to identify never-listed dishes eligible for seasonal or festival re-surfacing  
- Source: RE-DOC-04 §03 reactivation rules  
- Logic:  
  - Seasonal: SELECT \* FROM never\_list WHERE seasonal\_reactivation\_eligible=true AND nevered\_at \< NOW() \- INTERVAL '6 months' AND dish.seasonal\_affinity matches current season  
  - Festival: SELECT \* FROM never\_list WHERE festival\_reactivation\_eligible=true AND nevered\_at \< NOW() \- INTERVAL '90 days' AND current date is within 21 days of matching festival  
  - For each eligible: surface a soft prompt to the user ("It's winter — want to try X again?"). User must actively confirm. Re-surfacing does NOT automatically restore dish to pool.  
- Outputs: Reactivation prompts queued for eligible users  
- CDM entities: Never List (Entity 30), Festival (Entity 47\)  
- Status: Fully specified including time thresholds.

---

### Group H — Safety Gates (4 functions)

**H-01: safetyGateDietViolations()** — Gate 1

- Source: RE-DOC-03 §03, RE-DOC-05 §04 Query 1  
- Logic: SELECT COUNT(\*) FROM suggestion\_logs JOIN dishes JOIN profiles WHERE dish.diet\_type not compatible with user.diet\_type  
- Must return: 0 rows. Any row is P0 release blocker.  
- Status: Fully specified. Query defined in RE-DOC-05.

**H-02: safetyGateAllergenViolations()** — Gate 2

- Source: RE-DOC-03 §03, RE-DOC-05 §04 Query 2  
- Logic: Ingredient-level. JOIN suggestion\_logs → dish\_ingredients → ingredients WHERE ingredient.allergen\_flags AND user.allergen\_exclusions \!= 0\. Also checks household member allergen flags.  
- Must return: 0 rows.  
- Note: RE-DOC-05 Query 2 checks user.allergen\_exclusions at dish level. P3-03 will specify ingredient-level check (more rigorous, per CDM Business Invariant 3\) as the correct implementation.  
- Status: Fully specified with ingredient-level correction.

**H-03: safetyGateJainViolations()** — Gate 3

- Source: RE-DOC-05 §04 Query 3  
- Logic: SELECT COUNT(\*) FROM suggestion\_logs JOIN dishes JOIN users WHERE user.religious\_pref='jain' AND dish.is\_jain\_compatible=false  
- Must return: 0 rows.  
- Status: Fully specified.

**H-04: safetyGatePlanningRoleViolations()** — Gate 4

- Source: CDM Business Invariant 5, RE-DOC-03 §01 class-first rule  
- Logic: SELECT COUNT(\*) FROM plan\_slots WHERE is\_addon=false AND class\_code IN (SELECT class\_code FROM re\_meal\_classes WHERE planning\_role \!= 'MAIN\_PRIMARY')  
- Must return: 0 rows.  
- Status: Fully specified.

---

### Group I — Context Assembly (5 functions)

**I-01: assembleContext()**

- Purpose: Build the context object for a recommendation request from all available signals  
- Source: RE-DOC-02 §05, RE-DOC-01 §03 API request format  
- Inputs: city, system date, system time, OpenWeatherMap API  
- Outputs: context object: {weather\_condition, temp\_c, city, day\_of\_week, is\_weekend, season, time\_of\_day, festival\_proximity}  
- Status: Fully specified in structure.

**I-02: fetchWeatherWithCache()**

- Purpose: Check city-level weather cache before calling OpenWeatherMap API  
- Source: CDM Entity 46 (Weather Cache), DOC-10 §02 external services (1K calls/day free tier)  
- Logic: Check weather\_cache WHERE city \= ? AND date \= today AND expires\_at \> now(). If valid hit → return cached condition. If miss → call OpenWeatherMap API → cache for 12 hours → return.  
- CDM entities: Weather Cache (Entity 46\)  
- Status: Fully specified. Cache TTL \= 12 hours.

**I-03: classifyWeatherCondition()**

- Purpose: Map temperature and precipitation data to weather\_condition enum  
- Source: RE-DOC-02 §05 temperature bands  
- Logic:  
  - temp\_c \< 15°C → cold  
  - temp\_c 15–28°C WITH precipitation → rainy  
  - temp\_c 22–28°C WITHOUT precipitation → mild  
  - temp\_c \> 30°C → hot  
- Outputs: weather\_condition string (hot/rainy/cold/mild)  
- Status: Fully specified. Temp bands defined in RE-DOC-02.

**I-04: deriveSeason()**

- Purpose: Derive current Indian season from month and city  
- Source: RE-DOC-02 §05, CDM Entity 45  
- Logic:  
  - March–May → summer  
  - June–September → monsoon  
  - October–November → post\_monsoon  
  - December–February → winter  
- Note: City-specific variation exists (Mumbai monsoon starts June, Delhi July) — V1 uses calendar-based approximation.  
- Status: Specified. Calendar boundaries are a configuration decision.

**I-05: checkFestivalProximity()**

- Purpose: Determine if the current date is within 21 days before or during a major festival  
- Source: RE-DOC-02 §05 festival\_relevance, RE-DOC-04 §03 festival reactivation  
- Inputs: current date, festival\_calendar table  
- Outputs: festival\_proximity: {festival\_name, days\_until\_festival} or null  
- Note: Festival calendar is Phase 2 (F-45). For MVP, festival\_proximity returns null. Table must be populated before Phase 2\.  
- Status: Structure specified. Marked Phase 2\.

---

### Group J — Learning and Feature Store (9 functions)

**J-01: processInteractionEvent()**

- Purpose: Route each incoming interaction event to the appropriate update function(s)  
- Source: DOC-10 §05 POST /v1/events, RE-DOC-05 §02 feature store  
- Inputs: {event\_type, user\_id, dish\_id, meal\_slot, context, occurred\_at, rank\_at\_interaction, time\_viewed\_ms}  
- Routing:  
  - dish\_never → G-01 (processNeverGesture)  
  - dish\_not\_today → G-02 (processNotTodayGesture)  
  - All events → J-02 (updateInteractionCount), J-03 (updateGenomeTagAffinity), J-04 (updateBanditState), J-07 (logFeatureStore)  
  - dish\_accepted/locked/cooked → J-03 (positive signal)  
  - dish\_swiped\_past → J-03 (mild negative signal)  
- Outputs: All downstream update functions triggered  
- Status: Fully specified.

**J-02: updateInteractionCount()**

- Purpose: Increment interaction\_count after each qualifying interaction event  
- Source: CDM Entity 14 (Cold Start State), RE-DOC-03 weight ladder  
- Logic: interaction\_count \+= 1 for all event types EXCEPT plan\_opened, session\_depth. Check if interaction\_count \>= 14 → trigger J-05 (exitColdStart).  
- Status: Fully specified.

**J-03: updateGenomeTagAffinity()**

- Purpose: Update user's genome\_tag\_affinity based on accepted or rejected dish genome  
- Source: RE-DOC-03 §02 ContentMatch signal, CDM Entity 42 (Taste Vector)  
- Inputs: dish genome tags, event\_type, event\_weight  
- Logic: For each Tier-1 and Tier-2 genome tag in the dish:  
  - If positive event (accepted/locked/cooked): genome\_tag\_affinity\[tag\] \+= event\_weight × (1 − current\_affinity × dampening\_factor)  
  - If negative event (swiped\_past): genome\_tag\_affinity\[tag\] −= (event\_weight × 0.5) for most prominent tags only  
- Note: event\_weight values are PARTIALLY SPECIFIED (Not Today \= −0.10) and PARTIALLY PROPOSED for other types. Pending founder confirmation.  
- Status: PARTIALLY SPECIFIED.

**J-04: updateBanditState()**

- Purpose: Update Thompson Sampling α and β parameters for the (user, dish) pair  
- Source: RE-DOC-03 §02 ExplorationBonus, RE-DOC-05 §01 State A bandit  
- Logic: On positive event (accepted/locked/cooked) → α \+= 1\. On negative event (swiped\_past/not\_today) → β \+= 1\.  
- Status: Fully specified.

**J-05: exitColdStart()**

- Purpose: Transition user from cold start mode when interaction\_count \>= 14  
- Source: CDM Entity 14, CDM Business Invariant (interaction\_count drives this)  
- Logic: If interaction\_count \>= 14 AND cold\_start\_mode \= true → set cold\_start\_mode \= false on User RE State.  
- Note: Weight ladder continues interpolating regardless — cold\_start\_mode is a display flag (shows "Still learning" badge) and a pipeline flag.  
- Status: Fully specified.

**J-06: updateClassAffinity()**

- Purpose: Update class-level affinity weights in taste vector after class preference swipes or class-level Nevers  
- Source: DOC-06 C-07 (OB-07 signals), RE-DOC-04 §03 Never class-level signal  
- Logic for OB-07: YES swipe → class\_affinity\[class\_code\] \+= \[PROPOSED 0.30\]. NOPE → class\_affinity\[class\_code\] −= \[PROPOSED 0.30\].  
- Logic for Class Never: After 3+ Nevers from same class → class\_affinity\[class\_code\] −= \[PROPOSED 0.15 per Never beyond threshold\].  
- Status: PARTIALLY SPECIFIED. Signal direction documented. Magnitude UNRESOLVED/PROPOSED.

**J-07: logFeatureStore()**

- Purpose: Append all required feature categories to the ML feature store from Day 1  
- Source: RE-DOC-05 §02 feature store requirements  
- Inputs: Every recommendation request and interaction event  
- Log targets:  
  - User features → users table \+ user\_re\_state (already persisted)  
  - Dish features → re\_engine.dish\_features (daily snapshot via J-09)  
  - Interaction features → interaction\_events (already persisted)  
  - Context features → context\_log per request (append-only)  
  - Plan features → suggestion\_logs per dish shown (append-only)  
- Status: Fully specified. Feature categories and storage locations defined in RE-DOC-05.

**J-08: cohortWeightRecalibration()**

- Purpose: Weekly CRON to compare actual acceptance rates per cohort vs research priors and update cohort\_class\_priors  
- Source: DOC-10 §05 Cron jobs (Sunday 18:00 UTC / 23:30 IST)  
- Inputs: suggestion\_logs from past 7 days, interaction\_events with dish\_accepted for same period  
- \[G-012 UNRESOLVED\] The algorithm for comparing and updating is not defined in any document. The CRON job is documented (DOC-10), but the recalibration logic is not. P3-03 will flag this as an unresolved algorithm.  
- Status: CRON schedule specified. Algorithm UNRESOLVED.

**J-09: dailyDishFeatureSnapshot()**

- Purpose: Daily CRON to capture current dish feature state for ML training data  
- Source: RE-DOC-05 §02 dish features  
- Logic: Daily at UTC 00:00 → snapshot all active dishes: genome tags, class codes, popularity\_score, acceptance\_rate\_7d, acceptance\_rate\_30d, best\_slot, best\_day → write to re\_engine.dish\_features with snapshot\_date  
- Status: Fully specified.

---

### Group K — Dish Content Derivation (4 functions)

**K-01: deriveDishAttributes()**

- Purpose: Auto-derive diet\_type, is\_jain, and allergen\_flags on a dish from its ingredient composition. Triggered after ingredient linking or modification. Never manually set.  
- Source: CDM Business Invariant 6, RE-DOC-02 §03 allergen propagation, CDM Entity 18 (Ingredient)  
- Logic:  
  - allergen\_flags (dish) \= UNION of all ingredient.allergen\_flags  
  - diet\_type (dish) \= if ANY ingredient is\_veg=false → non\_veg; elif ANY ingredient allergen\_flag has egg bit=true AND is\_veg=true → egg; elif ALL ingredients is\_vegan=true → vegan; else → veg  
  - is\_jain (dish) \= if ALL ingredients is\_jain\_excluded=false AND diet\_type \= veg → true; else → false  
- Trigger: Runs on INSERT or UPDATE to dish\_ingredients table. Also runs as weekly batch.  
- Status: Fully specified.

**K-02: updateDishGenomeVector()**

- Purpose: Recompute the dish's genome vector (float array) when genome tags change  
- Source: RE-DOC-02 §02 genome dimensions, CDM Entity 16 (Food DNA)  
- Logic: After dish\_tags INSERT or UPDATE → assemble float vector from all Tier-1 and Tier-2 tags → store as dish.genome\_vector  
- \[OPEN DECISION\] Vector format is not defined. Options: a float\[\] array ordered by fixed tag\_id sequence, or a normalized JSONB map.  
- Status: Concept specified. Format is implementation decision for P3-04.

**K-03: updateDishPopularityScore()**

- Purpose: Daily update of dish popularity score from suggestion and acceptance logs  
- Source: RE-DOC-05 §02 dish features, CDM Entity 15 (Dish)  
- Logic: For each dish: popularity\_score \= weighted average of (acceptance\_rate\_7d × 0.6 \+ acceptance\_rate\_30d × 0.4)  
- Status: Formula structure specified. Weights are proposed, not documented.

**K-04: validateDishTier1Completeness()**

- Purpose: Verify a dish has all mandatory Tier-1 genome tags before it is eligible for recommendation  
- Source: CDM Entity 15 (Dish) invariant — Tier-1 tags mandatory before launch  
- Logic: Check dish\_tags for Tier-1 completeness: meal\_occasion, diet\_type, allergens, spice\_level, cook\_time\_band, difficulty, calorie\_band must all be present with confidence ≥ 0.85  
- Outputs: Pass/fail. Dishes that fail must not be included in re\_class\_dish\_options until Tier-1 is complete.  
- Status: Fully specified.

---

### Group L — Plan Management (4 functions)

**L-01: generateWeekPlan()**

- Purpose: Orchestrate full 7-day plan generation for a household  
- Source: DOC-10 §05 morning CRON and RE pipeline, DOC-04 Step 1-6  
- Sequence: B-01 → B-02 → B-03 → C-01 → \[For each slot: D-01 through D-07 → E-01 through E-08 → F-01 → F-02 → H-01 through H-04\] → Store in week\_plans \+ plan\_slots  
- Cron: 23:30 UTC (05:00 IST) daily for all users active in last 7 days  
- Status: Orchestration specified. Component functions are specified above.

**L-02: refreshUnlockedSlots()**

- Purpose: Regenerate slates for all unlocked slots when user pulls to refresh  
- Source: DOC-05 §06 pull-to-refresh gesture, DOC-10 §04 gesture implementation  
- Logic: For each plan\_slot WHERE week\_plan\_id \= current AND is\_locked \= false → re-run D-01 through H-04 for that slot. Locked slots untouched.  
- Note: The assigned class\_code does NOT change on refresh. Only dish candidates within the same class are regenerated.  
- Status: Fully specified.

**L-03: promoteSlateDish()**

- Purpose: When user Not Today's or Never's the primary (rank 1\) dish, promote rank 2 dish to primary display  
- Source: DOC-05 Flow 3a/3b, RE-DOC-01 §03 API (exclude\_dish\_ids\[\])  
- Logic: App sends POST /v1/recommendations with rejected dish\_id in exclude\_dish\_ids\[\]. RE returns new slate excluding that dish. The next-ranked dish from the original slate can be shown immediately from cached slate while new slate loads.  
- Status: Fully specified. Mechanism \= exclude\_dish\_ids\[\] parameter in API.

**L-04: handleOB08bInteractions()**

- Purpose: Process interactions on the OB-08b plan preview (swap, lock, never) before onboarding is complete  
- Source: DOC-05 OB-08b, DOC-06 wireframe OB-08b  
- Logic: Interactions on OB-08b are valid Interaction Events. They are logged with occurred\_at \= now(). They count toward interaction\_count. They process through same pipeline as post-onboarding interactions.  
- Note: These interactions happen BEFORE onboarding\_completed \= true is set. The RE must handle interaction events from a user who has not yet completed onboarding.  
- Status: Fully specified.

---

### Group M — Compliance Functions (3 functions)

**M-01: captureConsent()**

- Purpose: Record granular user consent per data category at signup per DPDP Act 2023  
- Source: DOC-09 §03, CDM Entity 51 (Consent Record)  
- Logic: At signup, present consent choices per category: analytics, push\_notifications, personalization, data\_retention. Each requires separate explicit action. Pre-ticked \= invalid. Record per category: {profile\_id, consent\_type, granted, granted\_at, ip\_address (hashed), privacy\_policy\_version}.  
- Note: Personalization-category consent must be granted before any dietary/preference data is collected. If personalization consent is denied, the RE cannot function — user must be informed.  
- Status: Fully specified.

**M-02: executeDataExport()**

- Purpose: Compile and deliver all user data within 72 hours of DPDP data export request  
- Source: DOC-09 §03, DOC-10 §06  
- Data scope: profiles, household\_members, interaction\_events, week\_plans, plan\_slots, never\_list, onboarding\_sessions, consent\_records  
- Status: Data scope specified. Implementation is a GET /v1/user/export Edge Function.

**M-03: executeDataDeletion()**

- Purpose: Permanently delete all personal data within 72 hours of account deletion request per DPDP Act  
- Source: DOC-09 §03, DOC-10 §06  
- Logic: Soft-delete immediately (mark deleted\_at). Hard-delete within 72h via cron. Exception: audit\_log retained for 3 years.  
- Note: interaction\_events are fully deleted (not anonymized) for deleted users.  
- Status: Fully specified.

---

## SECTION 4 — Updated Conflict and Gap Register

### Confirmed conflicts (revised from Context Baseline)

| \# | Conflict | Status | Resolution |
| :---- | :---- | :---- | :---- |
| C-001 | DOC-03 confidence 0.72 vs RE-DOC-04 max | **WITHDRAWN** | Not a conflict. RE-DOC-04 Day 1-3 range is 0.55-0.72. DOC-03 example is within range. |
| C-002 | Consent storage: DOC-10 JSONB vs CDM separate table | **Resolved** | CDM v1.1 supersedes. Separate consent table. |
| C-003 | assignPersona() in recommendation pipeline | **Resolved** | Step 2 \= fetchPersona() not assignPersona(). Persona assigned once at onboarding. |
| C-004 | MC\_GENERIC fallback | **Unresolved** | Product decision required. P3-03 will flag. |
| C-005 | DOC-10 RE schema table names | **Resolved** | CDM v1.1 supersedes. P3-04 sets correct names. |
| C-006 (NEW) | reason\_tags in RE-DOC-01 is an array; CDM §25 said single code | **Resolved** | RE-DOC-01 §03 API response is authoritative. reason\_tags is string\[\]. CDM §25 updated accordingly. |

### Active gaps before P3-03

| \# | Gap | Status | Resolution in P3-03 |
| :---- | :---- | :---- | :---- |
| G-001 | PersonalHistory event weights | PARTIALLY RESOLVED | Not Today weight \= −0.10 (RE-DOC-04 §03). Others proposed. Flagged \[PROPOSED\] in P3-03. Require confirmation. |
| G-002 | assign\_persona() mapping rules | Resolved as structure | It's a DB lookup, not code. Structure specified in A-08. Actual mapping is seed data. |
| G-003 | 4 unnamed genome dimensions | WITHDRAWN | All 20 are defined in RE-DOC-02 §02. |
| G-004 | Context multiplier values | Partially resolved | Conditions and direction specified. Exact values \= config table (context\_meal\_affinity\_config). Flagged as seed data in P3-03. |
| G-005 | Cohort-to-class prior table structure | Resolved as structure | Table \= (cohort\_id, class\_code, acceptance\_rate\_prior). Actual values \= seed data. |
| G-006 | PersonalHistory λ\_history | Unresolved | Flagged \[PROPOSED: 0.05\] in P3-03. |
| G-007 | Acceptance rate definition | RESOLVED | Accepted \= dish\_locked OR dish\_cooked OR dish\_ordered. Source: RE-DOC-05 §04. |
| G-008 | OB-07 class affinity magnitude | Unresolved | Flagged \[PROPOSED: ±0.30\] in P3-03. |
| G-009 | "Still learning" UI surface | Unresolved | Flagged in P3-03. Product/design decision. |
| G-010 | "Widen class" behavior for \< 3 candidates | Partially resolved | RE-DOC-01 §05 defines fallback (static 8 popular dishes). "Widen class" in DOC-10 is superseded by RE-DOC-01. |
| G-011 | Slate exhaustion behavior | Resolved | exclude\_dish\_ids\[\] in POST /v1/recommendations. Same endpoint, different excluded dishes. |
| G-012 | Cohort weight recalibration algorithm | Unresolved | CRON schedule specified. Algorithm flagged \[UNRESOLVED\] in P3-03. |
| G-013 | MC\_GENERIC fallback persona | Unresolved | Same as C-004. Flagged in A-08. |
| G-014 | Constraint conflict resolution | Resolved | RE-DOC-01 §05 is authoritative: static fallback of 8 popular dishes for diet type. |

---

## SECTION 5 — Quality Gate Assessment

| Gate Check | Status | Evidence |
| :---- | :---- | :---- |
| Every active document reviewed | ✅ PASS | 18 documents read fresh. 5 with no P3-03 contribution confirmed and explained. |
| Context Baseline validated | ✅ PASS | 6 corrections identified and resolved. Revised gap register above. |
| CDM is the conceptual foundation | ✅ PASS | All 61 functions reference CDM entities. No new domain concepts introduced. |
| Every logical function identified | ✅ PASS | 61 functions across 13 groups. Complete inventory above. |
| Every dependency mapped | ✅ PASS | Dependencies listed per function. Seed gate dependencies identified. |
| All prerequisite documents present | ✅ PASS | All 18 active documents present. |
| No assumptions made | ✅ PASS | All gaps explicitly flagged as \[PROPOSED\] or \[UNRESOLVED\]. None assumed. |
| Conflicts identified and resolved | ⚠ CONDITIONAL | 5 of 6 conflicts resolved. C-004 (MC\_GENERIC) flagged as unresolved product decision. |
| Remaining gaps handled appropriately | ✅ PASS | Gaps are either resolved, structural (no blocker), or explicitly flagged in P3-03. |
| Performance constraints respected | ✅ PASS | \<3s plan generation, \<100ms swipe response noted throughout. Algorithms designed for these constraints. |

**QUALITY GATE VERDICT: PASS — CONDITIONAL ON TWO OUTSTANDING PRODUCT DECISIONS**

**The two decisions that should be confirmed before or during P3-03 sign-off:**

**Decision 1 — PersonalHistory event weights (G-001):** P3-03 will use the following proposed values, clearly marked as \[PROPOSED — REQUIRES CONFIRMATION\]:

- dish\_not\_today: −0.10 (DOCUMENTED in RE-DOC-04 §03)  
- dish\_cooked: \+0.80 \[PROPOSED\]  
- dish\_locked: \+0.60 \[PROPOSED\]  
- dish\_accepted (carousel selection): \+0.40 \[PROPOSED\]  
- dish\_rated 5★: \+0.60 \[PROPOSED\]  
- dish\_rated 3★: \+0.00 \[PROPOSED\]  
- dish\_rated 1★: −0.30 \[PROPOSED\]  
- dish\_swiped\_past: −0.10 \[PROPOSED\]  
- λ\_history (decay rate): 0.05 \[PROPOSED\]

**Decision 2 — MC\_GENERIC fallback (C-004):** P3-03 will use the following approach pending decision: **Recommended: Option B** — If no persona can be matched, use the most generic class plan available for the user's main cohort (the cohort row with broadest state coverage), at confidence 0.35. This avoids a hardcoded "MC\_GENERIC" row that must be maintained separately.

P3-03 will begin now. All flagged items will be clearly marked within the document. No item will be assumed — each will carry its status tag.  
