# DOC-P3-03 · Business Logic and Algorithm Specification

**Version:** 1.0  
**Date:** June 2026  
**Status:** ACTIVE — [FD-05, ratified 2026-07-16] a Founder signature is not required for `[ACTIVE]` status per the amended `[ACTIVE]_Repository_Naming_Standard_v1.0.md`; content freeze is the ratification mechanism. See `[ACTIVE]_Founder_Decision_Register_v1.0.md` FD-05.  
**Prepared by:** Claude (Solution Architect role)  
**Prerequisite:** DOC-P3-02 Conceptual Domain Model v1.1 (must be read before this document)  
**Next document:** DOC-P3-04 · Data Architecture and Entity Relationship Model

---

## How to read this document

This document specifies every business rule, algorithm, formula, computation, scoring mechanism, threshold, and parameter that drives FooFoo's Recommendation Engine and application behaviour. It is the bridge between the conceptual model (P3-02) and the data architecture (P3-04). Every specification is traceable to one or more source documents. Every gap or unresolved decision is explicitly flagged — nothing is assumed.

**Status tags used throughout:**

- `[DOCUMENTED]` — value or rule directly stated in a source document  
- `[CONFIRMED]` — value decided during this framework session, founder-approved  
- `[PROPOSED]` — value recommended but not yet confirmed  
- `[UNRESOLVED]` — product decision still required before implementation

**Traceability format:** `[Source: DOC-XX §YY]`

**Working principles applied:**

1. Every specification traces to source document(s)  
2. No assumptions — gaps flagged explicitly  
3. Hard constraints always run before scoring  
4. Config values stored in config tables, not hardcoded  
5. Failure behaviors specified with same precision as success paths  
6. All CDM entities referenced by name and number

---

## Section 01 — Source Document Registry

All documents that contribute to this specification, with the specific sections that feed P3-03.

| Document | Version | Sections contributing to P3-03 |
| :---- | :---- | :---- |
| DOC-01 Product Brief | v1.0 | §02 (product pipeline), §03 (four layers), §08 (knowledge base) |
| DOC-03 User Personas | v1.0 | §02 (Meera), §03 (Priya), V2 cohort mappings |
| DOC-04 PRD | v1.1 | §02 (6-step pipeline), F-01 through F-10, F-37 through F-41, NFRs |
| DOC-05 IA | v1.2 | OB-01 through OB-08b flows, Flow 3a (Not Today), Flow 3b (Never), H-01 states |
| DOC-06 UX Design System | v1.1 | C-07 (OB-07 signaling), C-11 (city overlay weights), C-02 (carousel reason tags) |
| DOC-09 Legal | v1.0 | §03 (DPDP consent, retention, deletion) |
| DOC-10 Technical Architecture | v1.0 | §05 (RE pipeline 8 stages with failure modes, CRON jobs), §06 (security) |
| RE-DOC-01 | v1.0 | §03 (API contract — request/response format, endpoints), §05 (failure handling) |
| RE-DOC-02 | v1.0 | §02 (20 genome dimensions), §03 (Food Graph, allergen propagation), §04 (household model, city overlay, member add-ons), §05 (weather affinity mapping) |
| RE-DOC-03 | v1.0 | §01 (26 class codes, class-first rule), §02 (FinalScore formula, weight ladder, signal definitions), §03 (6 hard constraints) |
| RE-DOC-04 | v1.0 | §01 (confidence ladder, cold-start contributions, fallback rules), §02 (MMR algorithm, variety window rules, edge cases), §03 (Never and Not Today rules) |
| RE-DOC-05 | v1.0 | §01 (4-state model, State A/B weights), §02 (feature store), §04 (acceptance rate definition, safety gate queries, offline evaluation metrics) |
| DOC-P3-02 CDM | v1.1 | All 51 entities, 14 invariants, 52 events, 8-layer dependency map |

---

## Section 02 — Pipeline Overview

The RE pipeline has 9 stages. They run in strict sequence. No stage may proceed if the previous stage failed without applying the documented failure behaviour.

**Source:** DOC-10 §05 (authoritative), corrected per conflict resolution C-003 (assign vs fetch persona)

| Stage | Function | Trigger | Failure behaviour |
| :---- | :---- | :---- | :---- |
| 1 | validateRequest() | API call received | Return 400\. App falls back to cached plan. |
| 2 | fetchPersona() | Stage 1 pass | If no persona found: Option B fallback — generic main cohort class plan, confidence 0.35. \[CONFIRMED\] |
| 3 | generateClassPlan() | Stage 2 complete | Use generic cohort class plan if DB read fails. |
| 4 | generateAddons() | Stage 3 complete | Skip add-ons silently. Return primary plan only. |
| 5 | expandAndFilter() | Stage 3 \+ 4 complete | If \< 3 candidates: static fallback of 8 popular dishes filtered by diet type only. |
| 6 | scoreCandidates() | Stage 5 pass | Rank by cohort popularity (CohortPrior only) if full scoring fails. |
| 7 | applyMMR() | Stage 6 complete | If \< 8 after MMR: pad with highest-scoring remaining candidates. |
| 8 | runSafetyGate() | Stage 7 complete | FAIL: discard slate, regenerate (max 2 retries). After 2 failures: return 500 \+ cached plan signal. |
| 9 | buildResponse() | Stage 8 PASS | — |

**Non-negotiable pipeline rules:**

- Hard constraints (Stage 5\) always run before scoring (Stage 6). No score can override a hard constraint violation.  
- Safety gate (Stage 8\) always runs after MMR. A slate that passes scoring and MMR but fails the safety gate must be discarded.  
- fetchPersona() (Stage 2\) is a read of the stored persona\_id from the profile. It is NOT an assignment. Persona is assigned exactly once, at POST /v1/onboarding.

**Performance constraint:** Full pipeline must complete in \< 800ms for Edge Function execution. Total end-to-end (network \+ render): \< 3s on Pixel 3a reference device. `[Source: DOC-10 §07, DOC-04 NFR]`

---

## Section 03 — Onboarding Pipeline

**Endpoint:** POST /v1/onboarding  
**Trigger:** User taps "Looks good — let's go\!" on OB-08b  
**Output:** persona\_id, overlay\_persona\_ids\[\], confidence\_score, first week plan

---

### LF-A01: processMainCohortSelection()

**Purpose:** Store the user's OB-01 main cohort selection as a coded value.  
**Source:** DOC-04 F-01, DOC-05 OB-01 `[DOCUMENTED]`

**Inputs:**

- user\_tap\_selection: one of 5 displayed options

**Mapping:** | Display label | Stored code | |---|---| | "Just me" / Solo | MC\_SOLO | | "Two of us" / Couple | MC\_COUPLE | | "Family with children" | MC\_NUCLEAR\_FAMILY | | "Joint family / multi-gen" | MC\_JOINT\_FAMILY | | "PG / hostel / shared" | MC\_PG\_HOSTEL |

**Output:** main\_cohort\_code stored in onboarding\_sessions (screen\_id=OB-01)  
**Failure:** If no selection: MC\_SOLO default applied, confidence −0.05 `[Source: RE-DOC-04 §01]`  
**CDM entities:** Main Cohort (9), Onboarding Session (28)

---

### LF-A02: processHouseholdBranch()

**Purpose:** Apply dynamic branching at OB-02 based on main cohort. Derive sub\_cohort\_tag and member\_segments\[\].  
**Source:** DOC-04 F-02, DOC-05 OB-02, DOC-03 sub-cohort codes `[DOCUMENTED]`

**Branching rules:** | main\_cohort\_code | OB-02 questions shown | sub\_cohort\_tag examples | |---|---|---| | MC\_NUCLEAR\_FAMILY | Children's age bands | SC\_WITH\_INFANT, SC\_WITH\_TODDLER, SC\_WITH\_SCHOOL\_CHILD, SC\_WITH\_TEEN, SC\_WITH\_MIXED\_AGES | | MC\_JOINT\_FAMILY | Elder members? Health conditions? | SC\_WITH\_DIABETIC\_ELDER, SC\_WITH\_ELDERLY\_STANDARD, SC\_MULTI\_GEN\_STANDARD | | MC\_COUPLE | (No branch questions) | SC\_COUPLE\_STANDARD | | MC\_SOLO | (No branch questions) | SC\_SOLO\_STANDARD | | MC\_PG\_HOSTEL | (No branch questions) | SC\_PG\_STANDARD |

**Member segment derivation from OB-02 answers:** | OB-02 answer | member\_segment created | |---|---| | Child age 0–12 months | INFANT | | Child age 1–3 years | TODDLER | | Child age 4–12 years | SCHOOL\_CHILD | | Diabetic elder member | DIABETIC\_ELDER | | Postpartum member | POSTPARTUM | | Fitness-focused member | FITNESS\_OVERLAY | | Fasting member | FASTING\_MEMBER |

**Output:** sub\_cohort\_tag (intermediate, used in LF-A08), household\_members\[\] created with appropriate segments  
**CDM entities:** Sub-cohort (10), Household Members (3)

---

### LF-A03: processRegionalIdentity()

**Purpose:** Capture home\_state, current\_city, migration\_duration at OB-03. Derive city\_overlay\_weight.  
**Source:** DOC-05 OB-03, DOC-06 C-11 `[DOCUMENTED]`

**City overlay weight derivation:** | migration\_duration\_band | city\_overlay\_weight | home\_state\_signature\_weight | |---|---|---| | \< 1 year | 0.15 | 0.85 | | 1–3 years | 0.30 | 0.70 | | 3–7 years | 0.50 | 0.50 | | 7+ years | 0.70 | 0.30 | | Native (same state) | 0.00 | 1.00 | | Skipped | 0.50 (3-year default) | 0.50 |

**Invariant:** home\_state\_signature\_weight \+ city\_overlay\_weight \= 1.0 always. `[Source: CDM Invariant 7]`

**Confidence impact:** OB-03 skipped → confidence −0.08. `[Source: DOC-06 C-11]`

**Output:** home\_state, current\_city, migration\_duration\_band, city\_overlay\_weight stored on User  
**CDM entities:** Regional Identity (4), User (1)

---

### LF-A04: processDietConfiguration()

**Purpose:** Capture diet\_type and religious\_pref at OB-04. Store as household hard constraints.  
**Source:** DOC-04 F-04, DOC-05 OB-04 `[DOCUMENTED]`

**Diet type vocabulary:** veg, non\_veg, egg, vegan, jain  
**Religious pref vocabulary:** all, hindu\_veg, jain, halal, no\_beef, no\_pork

**Jain rule:** If diet\_type \= jain, religious\_pref is automatically set to jain. These are not independent choices for Jain households. `[Source: CDM Entity 5]`

**Confidence impact:** diet\_type captured → \+0.10. Skipped → −0.15. `[Source: RE-DOC-04 §01]`

**Output:** diet\_type, religious\_pref stored on User profile  
**CDM entities:** Diet Type (5), Religious Preference (6)

---

### LF-A05: processAllergenExclusions()

**Purpose:** Capture allergen exclusions at OB-05 via ingredient autocomplete. Store as bitfield per user and member.  
**Source:** DOC-04 F-05, RE-DOC-02 §02 genome dimension 13 `[DOCUMENTED]`

**Allergen bitfield definition:** | Bit | Integer value | Allergen | |---|---|---| | 0 | 1 | Nuts / peanuts | | 1 | 2 | Dairy | | 2 | 4 | Gluten | | 3 | 8 | Shellfish | | 4 | 16 | Egg | | 5 | 32 | Soy | | 6 | 64 | Sesame |

**Combined household allergen flags:** computed at candidate generation time as UNION (bitwise OR) of user.allergen\_flags AND all active household\_members.allergen\_flags. Not stored — computed at query time. `[Source: CDM Invariant 3]`

**Confidence impact:** allergen info captured → included in completeness score. Skipped → apply NO exclusions, mark confidence LOW. `[Source: RE-DOC-04 §01]`

**CDM entities:** Allergen (7), User (1), Household Members (3)

---

### LF-A06: processCookCapability()

**Purpose:** Capture cook\_capability at OB-06 to filter dish difficulty in recommendations.  
**Source:** DOC-04 F-06, RE-DOC-02 §02 genome dimension 8 `[DOCUMENTED]`

**Values:** beginner, intermediate, advanced

**RE impact at candidate selection:**

- beginner: class plan may exclude BF\_STUFFED\_FLATBREAD on weekdays. Dishes with difficulty=advanced excluded.  
- intermediate: full class range available. All difficulty levels available.  
- advanced: no restrictions.

**Special case — MC\_PG\_HOSTEL:** cook\_capability implicitly constrained. Class plan weighted toward BF\_NO\_COOK\_QUICK and BF\_LIGHT\_GRAIN regardless of stated capability. `[Source: RE-DOC-04 §01]`

**Confidence impact:** captured → \+0.07. Skipped → assume "needs instructions" (beginner equivalent). `[Source: RE-DOC-04 §01]`

**CDM entities:** Cook Capability (8), User (1)

---

### LF-A07: processClassPreferenceSwipes()

**Purpose:** Process OB-07 YES/NOPE swipes into class\_affinity signals. First behavioral Interaction Events.  
**Source:** DOC-06 C-07, DOC-04 F-07, DOC-05 OB-07 `[DOCUMENTED]` \+ CDM §33 `[CONFIRMED]`

**Dish pool at OB-07 (Indian-only):** `[Source: SESSION_HANDOFF-4 D-004]`  
Idli Sambar (→ BF\_SOUTH\_FERMENTED), Poha (→ BF\_LIGHT\_GRAIN), Aloo Paratha (→ BF\_STUFFED\_FLATBREAD), Rajma Chawal (→ LUNCH\_CURRY\_ROTI), Masala Dosa (→ BF\_SOUTH\_FERMENTED), Paneer Butter Masala (→ DIN\_CURRY\_ROTI), Chole Bhature (→ LUNCH\_STREET\_STYLE), Dal Makhani (→ DIN\_COMFORT\_WARM), Khichdi (→ LUNCH\_ONE\_POT), Chicken Biryani (shown only for non\_veg/egg households → DIN\_NON\_VEG\_MAIN)

**Processing rules:**

- Each card swipe \= 1 Interaction Event (event\_type \= onboarding\_class\_preference)  
- YES swipe: class\_affinity\[class\_code\] \+= 0.30 `[CONFIRMED — Claude recommendation, founder approved June 2026]`  
- NOPE swipe: class\_affinity\[class\_code\] −= 0.30 `[CONFIRMED]`  
- Contribution to interaction\_count: \+1 per card swiped. Maximum \+10 from OB-07.  
- De-duplication: if same class appears twice (same dish shown again due to app restart), only most recent swipe per class counts toward interaction\_count.  
- OB-07 skipped: class\_affinity initialised at 0.0 for all classes. Zero interaction signals from onboarding.

**Event weight in PersonalHistory:** 0.30 `[CONFIRMED]`

**Confidence impact:** OB-07 completed → \+0.12. Skipped → 0\. `[Source: RE-DOC-04 §01]`

**CDM entities:** Class Preference Swipe (33), Interaction Events (29), Taste Vector (42)

---

### LF-A08: computeOnboardingConfidence()

**Purpose:** Compute initial confidence score from onboarding signal contributions.  
**Source:** RE-DOC-04 §01 `[DOCUMENTED]`

**Confidence computation:**

confidence \= 0.40  (minimum base — all users)

if home\_state captured:      \+= 0.15

if diet\_type captured:       \+= 0.10

if current\_city overlay found: \+= 0.08

if cook\_capability captured:  \+= 0.07

if OB-07 swipes completed:   \+= 0.12

contextual signals (always): \+= 0.08

for each non-critical field skipped: \-= 0.05

if diet\_type skipped:        \-= 0.15

if OB-03 entirely skipped:   \-= 0.08

if ALL onboarding skipped:   confidence \= 0.35 (floor)

Maximum at Day 0 completion: 0.65

Range Day 0: 0.40 – 0.65

Range Day 1–3 (with interactions): 0.55 – 0.72

**[FD-03, ratified 2026-07-16]** The additive contributions above can sum beyond 0.65 (schema ceiling is 1.0); `computeOnboardingConfidence` clamps the result to **[0.35, 0.65] at Day 0**. The 1.0 schema ceiling governs only later warm-state evolution (Day 1+), not Day 0. See `[ACTIVE]_Founder_Decision_Register_v1.0.md` FD-03.

**Output:** confidence\_score float stored on User RE State  
**CDM entities:** Confidence Score (13)

---

### LF-A09: assignPersona()

**Purpose:** Map onboarding profile to one of 41 backend personas. Runs once at end of onboarding. Result stored. User never sees it.  
**Source:** DOC-04 Step 2, RE-DOC-01 §03 POST /v1/onboarding `[DOCUMENTED]`

**Implementation type:** Database lookup — NOT a computed function. The mapping lives in re\_persona\_assignment\_rules seed table.

**Lookup inputs:** (main\_cohort\_code, sub\_cohort\_tag, home\_state, diet\_type)  
**Lookup output:** persona\_id (FK to re\_personas, one of 41 rows)

**Overlay persona assignment:** For each household\_members.segment: | segment | overlay added | |---|---| | INFANT | O\_INFANT | | TODDLER | O\_TODDLER | | DIABETIC\_ELDER | O\_DIABETIC\_ELDER | | POSTPARTUM | O\_POSTPARTUM | | FITNESS\_OVERLAY | O\_FITNESS | | FASTING\_MEMBER | O\_FASTING | | SCHOOL\_CHILD, ADULT\_STANDARD | (no overlay) |

**Fallback (Option B — CONFIRMED):** If no matching row found in re\_persona\_assignment\_rules → use the cohort row for this user's main\_cohort\_code with the broadest state coverage → assign it as persona, confidence \= 0.35.  
`[CONFIRMED — Claude recommendation, founder approved June 2026]`

**Output:** persona\_id \+ overlay\_persona\_ids\[\] stored on User RE State  
**CDM entities:** Persona (11), Overlay (12)

---

## Section 04 — Class Plan Generation

### LF-B01: fetchPersona()

**Purpose:** At recommendation time, read the stored persona\_id and overlays. NOT a reassignment.  
**Source:** RE-DOC-01 §03, DOC-10 §05 Stage 2 (corrected) `[DOCUMENTED, corrected per C-003]`

**Logic:** SELECT persona\_id, overlay\_persona\_ids\[\] FROM user\_re\_state WHERE profile\_id \= :user\_id  
**Fallback:** If no persona\_id stored (incomplete onboarding): apply Option B fallback (LF-A09 fallback). Log as anomaly.  
**CDM entities:** Persona (11), User RE State aggregate

---

### LF-B02: generateClassPlan()

**Purpose:** Map persona \+ day context to class codes for all slots in the week.  
**Source:** DOC-04 Step 3, DOC-10 §05 Stage 3, RE-DOC-03 §01 `[DOCUMENTED]`

**Query pattern:**

SELECT day\_of\_week, breakfast\_class\_code, lunch\_class\_code, dinner\_class\_code

FROM re\_weekly\_class\_plans

WHERE cohort\_id \= (

  SELECT cohort\_id FROM re\_cohorts 

  WHERE persona\_id \= :persona\_id 

    AND state\_code \= :home\_state 

    AND diet\_mode \= :diet\_mode

)

ORDER BY day\_of\_week

**Weekday/weekend selection:** re\_weekly\_class\_plans contains separate rows per day\_of\_week. The 7-day plan is returned directly from seed data — no runtime calculation needed.

**Non-veg cadence overlay (for non\_veg and egg diet households):**  
After base class plan is fetched: lookup re\_nonveg\_logic WHERE state\_code \= home\_state → get weekly\_nonveg\_slots (count) and preferred\_slots\[\] (e.g., dinner, weekend lunch) → replace that many class codes with DIN\_NON\_VEG\_MAIN or appropriate non-veg class.

**Output:** Array of 21 class assignments: \[{slot\_date, meal\_slot, class\_code}\]  
**Dependencies:** Seed gates S-11, S-12 (re\_cohorts 2952 rows, re\_weekly\_class\_plans 20664 rows)  
**Failure:** DB read fails → use first matching cohort row for main\_cohort\_code generically. `[Source: DOC-10 Stage 3]`  
**CDM entities:** Meal Class (20), Week Plan (23), Plan Slot (24)

---

## Section 05 — Add-on Generation

### LF-C01: generateAddons()

**Purpose:** Generate member-specific add-on class codes for each primary slot.  
**Source:** DOC-04 Step 4, RE-DOC-02 §04 member segment table, DOC-10 §05 Stage 4 `[DOCUMENTED]`

**Processing per active Household Member (segment ≠ ADULT\_STANDARD):**

For each plan\_slot in week\_plan:

  For each household\_member with active segment:

    addon\_class\_code \= lookup re\_segment\_addon\_rule 

      WHERE segment \= member.segment 

        AND primary\_class\_code \= slot.class\_code

        AND slot \= plan\_slot.meal\_slot

    If found: create addon\_slot record

    If not found: skip silently, log coverage gap

**Member add-on class mappings (from RE-DOC-02 §04):** | Segment | Primary class example | Add-on class | |---|---|---| | INFANT | Any | ADDON\_INFANT | | TODDLER | Any | ADDON\_TODDLER | | DIABETIC\_ELDER | LUNCH\_RICE\_DAL\_CURRY | ADDON\_DIABETIC | | POSTPARTUM | Any | ADDON\_POSTPARTUM | | FITNESS\_OVERLAY | Any | ADDON\_FITNESS | | FASTING\_MEMBER | Any | ADDON\_FASTING |

**Invariant:** Add-on slot is ALWAYS additional. NEVER modifies the primary Plan Slot. `[Source: CDM Invariant 9, RE-DOC-02 §04]`

**Failure:** No matching rule → skip add-on for that member/slot. Primary plan returned without add-on. `[Source: DOC-10 Stage 4]`  
**CDM entities:** Add-on Slot (26), Household Members (3), Meal Class (20)

### LF-C02: resolveAddonDish()

**Purpose:** Select specific dish from add-on class for member's add-on slot.  
**Source:** RE-DOC-02 §04 examples, RE-DOC-03 ADDON class definitions `[DOCUMENTED]`

**Query:**

SELECT dish\_id FROM re\_addon\_dish\_options

WHERE addon\_class\_code \= :addon\_class\_code

  AND (allergen\_flags & :member\_allergen\_flags) \= 0

  AND diet\_type IN (:member\_diet\_type, 'veg')

ORDER BY suitability\_rank ASC

LIMIT 1

**Output:** dish\_id for add-on slot  
**CDM entities:** Add-on Slot (26), Dish (15)

---

## Section 06 — Candidate Generation and Hard Constraint Filtering

**Rule:** All 6 hard constraints run BEFORE any scoring. A dish that fails any hard constraint is permanently excluded from scoring for this request. `[Source: RE-DOC-03 §03, CDM Invariant 12]`

### LF-D01: getClassCandidates()

**Purpose:** Retrieve all dishes eligible for the assigned class from the Class-Dish Options junction.  
**Source:** RE-DOC-03 §01 class-first rule, CDM Entity 21 `[DOCUMENTED]`

**Query:**

SELECT cdo.dish\_id, cdo.base\_score

FROM re\_class\_dish\_options cdo

JOIN dishes d ON d.id \= cdo.dish\_id

WHERE cdo.meal\_class\_code \= :class\_code

  AND d.is\_active \= true

  AND d.is\_indian\_only \= true

**Output:** candidate\_dishes\[\]: \[{dish\_id, base\_score}\]  
**Dependencies:** Seed gate S-08 (re\_class\_dish\_options 1,050 rows)  
**CDM entities:** Class-Dish Option (21), Dish (15)

---

### LF-D02: applyDietTypeFilter() — Hard Constraint 1

**Purpose:** Remove dishes incompatible with household diet type.  
**Source:** RE-DOC-03 §03 Hard Constraint 1, CDM Invariant 1 `[DOCUMENTED]`

**Filter rules:** | user.diet\_type | Dishes excluded | |---|---| | veg | Any dish where dish.diet\_type NOT IN ('veg', 'vegan', 'jain') | | jain | Any dish where dish.is\_jain \= false | | vegan | Any dish where dish.diet\_type \!= 'vegan' | | egg | Any dish where dish.diet\_type NOT IN ('veg', 'vegan', 'jain', 'egg') | | non\_veg | No diet exclusions (all types eligible) |

**Note:** dish.diet\_type is auto-derived from ingredients. Never manually set. `[Source: CDM Invariant 6]`  
**Safety Gate 1** validates this after every RE change.  
**CDM entities:** Diet Type (5), Dish (15)

---

### LF-D03: applyAllergenFilter() — Hard Constraint 2

**Purpose:** Remove dishes with any ingredient matching user or household member allergen flags. Operates at ingredient level.  
**Source:** RE-DOC-03 §03, RE-DOC-02 §03 allergen propagation, CDM Invariant 3 `[DOCUMENTED]`

**Combined household allergen computation:**

combined\_allergen\_flags \= user.allergen\_flags 

  | household\_members\[0\].allergen\_flags 

  | household\_members\[1\].allergen\_flags 

  | ... (bitwise OR of all active members)

**Ingredient-level filter:**

\-- EXCLUDE any dish where any ingredient has overlapping allergen flags

SELECT DISTINCT dish\_id FROM dish\_ingredients di

JOIN ingredients i ON i.id \= di.ingredient\_id

WHERE (i.allergen\_flags & :combined\_allergen\_flags) \> 0

Any dish\_id appearing in this query is excluded from candidates.

**Critical:** This check MUST use ingredient-level allergen flags (via dish\_ingredients → ingredients). Dish-level allergen\_flags are a derived summary — they may not reflect recently added ingredients before the derivation pipeline has run. `[Source: CDM Invariant 3, Safety Gate 2]`  
**Safety Gate 2** validates this after every RE change.  
**CDM entities:** Allergen (7), Ingredient (18), Dish (15)

---

### LF-D04: applyReligiousFilter() — Hard Constraint 3

**Purpose:** Remove dishes incompatible with household religious preference.  
**Source:** RE-DOC-03 §03 Hard Constraint 3, CDM Invariant 2 `[DOCUMENTED]`

**Filter rules:** | user.religious\_pref | Dishes excluded | |---|---| | jain | Any dish where dish.is\_jain \= false | | halal | Any dish with non-halal meat ingredients (ingredient-level check) | | no\_beef | Any dish with beef-derived ingredients | | no\_pork | Any dish with pork-derived ingredients | | all, hindu\_veg | No additional exclusion (diet\_type handles this) |

**Note:** dish.is\_jain is auto-derived from ingredient.is\_jain\_excluded flags. `[Source: CDM Entity 18]`  
**Safety Gate 3** validates Jain violations.  
**CDM entities:** Religious Preference (6), Dish (15)

---

### LF-D05: applyMealOccasionFilter() — Hard Constraint 4

**Purpose:** Ensure dish is eligible for the current meal slot.  
**Source:** RE-DOC-03 §03 Hard Constraint 4, RE-DOC-02 §02 Dimension 1 `[DOCUMENTED]`

**Filter:** Exclude any dish where dish.meal\_occasion does NOT contain :meal\_slot AND does NOT contain 'any'  
**CDM entities:** Meal Occasion (22), Dish (15)

---

### LF-D06: applyNeverListFilter() — Hard Constraint 5

**Purpose:** Permanently exclude dishes the user has Never'd.  
**Source:** RE-DOC-03 §03 Hard Constraint 6, RE-DOC-04 §03, CDM Invariant 10 `[DOCUMENTED]`

**Filter:**

\-- EXCLUDE any dish in user's active never list

dish\_id NOT IN (

  SELECT dish\_id FROM re\_engine.never\_list 

  WHERE profile\_id \= :user\_id AND is\_active \= true

)

**Invariant:** No score, no context multiplier, no festival override bypasses an active Never entry. Hard exclusion identical in effect to allergen exclusion. `[Source: CDM Invariant 10]`  
**CDM entities:** Never List (30), Dish (15)

---

### LF-D07: handleConstraintConflict()

**Purpose:** Handle the case where \< 3 candidates survive all hard constraints.  
**Source:** RE-DOC-01 §05 (authoritative), DOC-10 §05 Stage 5 failure `[DOCUMENTED]`

**Logic:**

1. If candidates count \< 3 after all filters: log as coverage gap (dish database insufficient for this constraint combination)  
2. Return static fallback: 8 most popular dishes filtered by diet\_type ONLY (no class constraint, no other filters)  
3. App displays H-01 "Constraint conflict" state  
4. Flag user profile for content team review

**Note:** "Widen class" referenced in DOC-10 Stage 5 is superseded by RE-DOC-01 §05 static fallback approach. RE-DOC-01 is the authoritative RE specification. `[Source: Conflict resolution C-003 principle — RE-DOC-01 > DOC-10 on RE behaviour]`  
**CDM entities:** Plan Slot (24), Safety Gate (48)

---

## Section 07 — Scoring

**Rule:** Scoring only runs on candidates that have passed ALL 6 hard constraint filters. `[Source: RE-DOC-03 §03, CDM Invariant 12]`

### LF-E01: interpolateWeightLadder()

**Purpose:** Compute current scoring weights per user based on interaction\_count with smooth linear interpolation.  
**Source:** RE-DOC-03 §02, RE-DOC-05 §01 `[DOCUMENTED]`

**Tier table:** | Tier | interaction\_count range | w\_cohort | w\_content | w\_history | w\_context | w\_explore | |---|---|---|---|---|---|---| | Cold Start | 0 | 0.55 | 0.20 | 0.00 | 0.15 | 0.10 | | Early | 1–10 | 0.35 | 0.25 | 0.15 | 0.15 | 0.10 | | Emerging | 11–50 | 0.20 | 0.25 | 0.35 | 0.15 | 0.05 | | Established | 51–150 | 0.10 | 0.20 | 0.50 | 0.15 | 0.05 | | Mature | 150+ | 0.05 | 0.15 | 0.65 | 0.15 | 0.00 |

**Interpolation formula (linear between tiers):**

progress \= (interaction\_count \- tier\_lower\_bound) / (tier\_upper\_bound \- tier\_lower\_bound)

w\_x \= w\_x\_lower \+ progress × (w\_x\_upper \- w\_x\_lower)

**Example (continuous forward-transition reading — ratified FD-02, ratifies the interpretation already implemented in `interpolateWeightLadder`):** interaction\_count \= 30 (Emerging tier, 11–50, next tier Established, 51–150): progress \= (30-11)/(50-11) \= 0.487. Each weight interpolates from the *current* tier's value toward the *next* tier's value: w\_cohort \= 0.20 \+ 0.487 × (0.10-0.20) \= 0.151 w\_content \= 0.25 \+ 0.487 × (0.20-0.25) \= 0.226 w\_history \= 0.35 \+ 0.487 × (0.50-0.35) \= 0.423 w\_context \= 0.15 \+ 0.487 × (0.15-0.15) \= 0.150 w\_explore \= 0.05 \+ 0.487 × (0.05-0.05) \= 0.050 — sum \= 1.000 (partition-of-unity holds at every tier boundary, tested in `_tests/re_core.test.ts`).

**Implementation note:** Weights computed at request time from current interaction\_count. NOT stored as static values on the user profile. `[Source: RE-DOC-03 §02]`  
**CDM entities:** Weight Ladder (41)

---

### LF-E02: computeCohortPrior()

**Purpose:** Lookup research-based acceptance rate for (cohort, dish class) pair.  
**Source:** RE-DOC-03 §02 CohortPrior definition `[DOCUMENTED]`

**Logic:**

SELECT acceptance\_rate\_prior FROM re\_cohort\_class\_priors

WHERE cohort\_id \= :cohort\_id AND class\_code \= :class\_code

**Range:** 0–1. Higher values indicate dishes in this class are historically popular for this cohort.  
**Fallback:** If no matching row: use 0.50 (neutral prior). Log as seed data gap.  
**CDM entities:** Scoring Signal CohortPrior (35)

---

### LF-E03: computeContentMatch()

**Purpose:** Cosine similarity between user's taste vector and dish's genome vector.  
**Source:** RE-DOC-03 §02 ContentMatch definition `[DOCUMENTED]`

**Formula:** ContentMatch \= CosineSimilarity(user.genome\_tag\_affinity\_vector, dish.genome\_vector)

**Cosine similarity:**

similarity \= (A · B) / (|A| × |B|)

where A \= user\_taste\_vector, B \= dish\_genome\_vector

**Genome vector:** Dish's Tier-1 and Tier-2 genome tags expressed as a normalised float array. Format: fixed-dimension vector ordered by tag\_id sequence from the tags master table. `[Implementation decision deferred to P3-04]`

**Cold start handling:** If user has no interactions (interaction\_count \= 0), genome\_tag\_affinity\_vector defaults to the cohort's average taste profile. `[Implied from RE-DOC-03 §02 weight ladder — w_history=0 but w_content=0.20 at Day 0]`

**Range:** 0–1.  
**CDM entities:** ContentMatch (36), Taste Vector (42)

---

### LF-E04: computePersonalHistory()

**Purpose:** Weighted, time-decayed sum of user's prior interactions with a specific dish.  
**Source:** RE-DOC-03 §02 PersonalHistory definition, RE-DOC-04 §03 Not Today weight `[DOCUMENTED + CONFIRMED]`

**Formula:**

PersonalHistory(user, dish) \= Σ \[ event\_weight(event\_type) × e^(-λ\_history × days\_elapsed) \]

  for all interaction\_events where user\_id \= :user\_id AND dish\_id \= :dish\_id

**λ\_history \= 0.05** `[CONFIRMED — Claude recommendation, founder approved June 2026]` Slow decay — preferences are persistent. An event 60 days ago retains \~5% weight.

**Event weight table:** | event\_type | event\_weight | Source | |---|---|---| | dish\_cooked | \+0.80 | `[CONFIRMED]` | | dish\_locked | \+0.60 | `[CONFIRMED]` | | dish\_rated (5★) | \+0.60 | `[CONFIRMED]` | | dish\_accepted | \+0.40 | `[CONFIRMED]` | | dish\_rated (3★) | \+0.00 | `[CONFIRMED]` | | dish\_rated (1★) | −0.30 | `[CONFIRMED]` | | dish\_swiped\_past | −0.10 | `[CONFIRMED]` | | dish\_not\_today | −0.10 (Day 0, fades to 0 by Day 7\) | `[DOCUMENTED — RE-DOC-04 §03]` | | onboarding\_class\_preference | Applied to class\_affinity, not PersonalHistory | — | | dish\_never | Hard constraint filter excludes dish before scoring | — |

**Note for Not Today in PersonalHistory:** RE-DOC-04 §03 specifies "w\_history contribution: –0.1 on Day 0, fades to 0 by Day 7." This means the Not Today event has its own exponential fade: event\_weight\_nt(t) \= −0.10 × e^(−0.35 × t) where t \= days since gesture. This is applied within the PersonalHistory formula, separate from the Not Today penalty (LF-E08). These are two distinct mechanisms.

**Range:** −1 to \+1.  
**CDM entities:** PersonalHistory (37), Interaction Events (29)

---

### LF-E05: computeContextFit()

**Purpose:** Score how well a dish fits the current situational context.  
**Source:** RE-DOC-03 §02, RE-DOC-02 §05 `[DOCUMENTED]`

**Formula:**

ContextFit \= Σ(context\_attribute\_match × multiplier) 

  across: weather, season, day\_type, time\_of\_day, cook\_time

**Range:** 0–1.2 (can exceed 1.0 for ideal context fit) `[Source: RE-DOC-03 §02]`

**Weather multiplier direction (from RE-DOC-02 §05):** | weather\_condition | Genome tags boosted | Direction | |---|---|---| | rainy | weather\_affinity:rainy, comfort\_warmth\_score≥4, cooking\_method:fried | boost ×1.0–1.2 | | hot | weather\_affinity:hot, comfort\_warmth\_score≤1 | boost; heavy fried reduced 0.8× | | cold | weather\_affinity:cold, comfort\_warmth\_score≥4 | boost ×1.0–1.2 | | mild | All tags | neutral (1.0×) |

**Specific multiplier values:** Stored in configuration table `re_context_multipliers` (context\_type, context\_value, genome\_tag, multiplier\_value). Seeded from context-meal affinity knowledge base. `[Source: DOC-01 §08]`  
**Exact multiplier values are seed/configuration data — not hardcoded.** `[Source: Working Principle 7]`

**Day type adjustment:**  
Weekday: boost dishes with cook\_time\_band ≤ 30min. `[Source: RE-DOC-02 §05]`  
Weekend: allow all cook\_time bands. No restriction.

**Season adjustment:** Boost dishes where dish.seasonal\_affinity contains current\_season. `[Source: RE-DOC-02 §05]`

**CDM entities:** ContextFit (38), Context (43), Weather Condition (44)

---

### LF-E06: computeExplorationBonus()

**Purpose:** Thompson Sampling bandit to encourage dish discovery.  
**Source:** RE-DOC-03 §02, RE-DOC-05 §01 State A `[DOCUMENTED]`

**Formula:** ExplorationBonus \= random draw from Beta(α\_dish, β\_dish)

**Initial prior:** Beta(1,1) adjusted to cohort base acceptance rates. `[Source: RE-DOC-05 §01]`

**α and β update rules:**

- α \+= 1 on: dish\_accepted, dish\_locked, dish\_cooked  
- β \+= 1 on: dish\_swiped\_past, dish\_not\_today

**Exploration target:** \~10% of slate (approximately 1 of 8 dishes). `[Source: RE-DOC-05 §01]`

**Range:** 0–0.15 `[Source: RE-DOC-03 §02]`

**State-dependent behaviour:**

- State A (cold start): high explore weight (w\_explore=0.10)  
- State B (mature): minimal bandit; w\_explore approaches 0.00 `[Source: RE-DOC-05 §01]`

**CDM entities:** ExplorationBonus (39)

---

### LF-E07: computePenaltyTerms()

**Purpose:** Compute deductions for active Not Today suppression.  
**Source:** RE-DOC-04 §03 `[DOCUMENTED]`

**Not Today penalty:**

Penalty(t) \= P0 × e^(-λ × t)

  P0 \= 0.80   \[DOCUMENTED — RE-DOC-04 §03\]

  λ  \= 0.35   \[DOCUMENTED — RE-DOC-04 §03\]

  t  \= days elapsed since suppressed\_at timestamp

**Penalty values at key days:** | Days elapsed | Penalty | |---|---| | 0 | 0.80 | | 2 | \~0.40 | | 5 | \~0.12 | | 7 | \~0.05 (effectively zero — dish returns to normal) |

**Context override (Day 3+):** If t ≥ 3 AND ContextFit \> \[UNRESOLVED threshold — suggested 0.90\] → Penalty \= Penalty × 0.50. Strong contextual fit partially overrides decayed suppression. `[Source: RE-DOC-04 §03]`

**Variety penalty:** Computed during MMR stage (LF-F01), not here. The penalty listed in FinalScore formula as "variety\_penalty" is the MMR output term, not a separate calculation.

**CDM entities:** Penalty Terms (40), Not Today Suppression (31)

---

### LF-E08: computeFinalScore()

**Purpose:** Assemble all signals into a single ranked score for each candidate dish.  
**Source:** RE-DOC-03 §02 `[DOCUMENTED]`

**Formula:**

FinalScore(user, dish, context) \=

    w\_cohort  × CohortPrior(user\_cohort, dish\_class)

  \+ w\_content × ContentMatch(user\_taste\_vector, dish\_genome\_vector)

  \+ w\_history × PersonalHistory(user\_events, dish)

  \+ w\_context × ContextFit(dish\_genome, weather, day, season)

  \+ w\_explore × ExplorationBonus(dish)

  \- PenaltyTerms(not\_today\_decay)

SUBJECT TO:

  HardConstraintFilter(user, dish) \== PASS  ← always first, never bypassed

**Weights:** From LF-E01 interpolateWeightLadder() using current interaction\_count.

**Output:** score float per dish. Dishes ordered by FinalScore descending → input to MMR.  
**CDM entities:** FinalScore (34)

---

## Section 08 — Variety Re-ranking

### LF-F01: applyMMR()

**Purpose:** Re-rank scored candidates to produce a diverse 8-dish slate.  
**Source:** RE-DOC-04 §02 `[DOCUMENTED]`

**Formula:**

MMR(i) \= argmax over remaining i of:

  λ × ScoringRelevance(i, user) \- (1-λ) × max\_j∈Selected Similarity(i,j)

λ \= 0.70 (MVP classfirst\_v1)  \[DOCUMENTED — RE-DOC-04 §02\]

λ \= 0.55 (Phase 1+)           \[DOCUMENTED — RE-DOC-04 §02\]

ScoringRelevance(i) \= FinalScore(i) from LF-E08

Similarity(i,j) \= CosineSimilarity of genome vectors across variety-relevant dimensions:

  cuisine\_family, cooking\_method, main\_ingredient\_class, texture

**Process:**

1. Start with empty selected\_set  
2. Iteratively: pick dish i with highest MMR score → add to selected\_set → repeat  
3. Until selected\_set has 8 dishes OR candidates exhausted

**Fallback:** If \< 8 after MMR → pad with highest FinalScore remaining candidates. `[Source: DOC-10 §05 Stage 7]`

**Variety penalty term:** The (1-λ) × similarity term in MMR serves as the variety penalty referenced in FinalScore formula.  
**CDM entities:** Slate (25), Variety Window State (32)

---

### LF-F02: checkVarietyWindowRules()

**Purpose:** Validate the 7-day plan against rolling variety window rules.  
**Source:** RE-DOC-04 §02 `[DOCUMENTED]`

**Five variety rules:**

1. **Same cuisine family — 5-day window:** Max 2 of same cuisine family in breakfast slot per 5 consecutive days. Max 2 in dinner slot. `[Source: RE-DOC-04 §02]`  
2. **Same cooking method (fried) — 7-day:** Max 3 fried dishes per week in any slot. Monsoon season override: max 4\. `[Source: RE-DOC-04 §02]`  
3. **Same main ingredient — consecutive days:** No same primary ingredient (dimension 11\) on back-to-back days. Exception: rice is treated as distinct when in different preparation forms (pongal vs rice+dal vs curd rice). `[Source: RE-DOC-04 §02]`  
4. **Same dish — 30-day:** No exact dish repeat within 30 days unless explicitly locked by user. `[Source: RE-DOC-04 §02]`  
5. **Same breakfast class — weekly:** No same breakfast class more than 3 times per week. Weekend override: allow BF\_SWEET\_WARM and BF\_STUFFED\_FLATBREAD even if recently used. `[Source: RE-DOC-04 §02]`

**Monsoon override check:** Is current month within monsoon season (June–September)? If yes → fried limit \= 4\. Else → fried limit \= 3\.

**All 5 rules stored as configuration:** Table re\_variety\_rules (rule\_name, window\_days, cap\_value, override\_condition). MMR reads these at runtime. `[Working Principle 7]`

**CDM entities:** Variety Window State (32)

---

### LF-F03: handleVarietyEdgeCases()

**Purpose:** Apply resolution strategies when variety guard cannot find diverse candidates.  
**Source:** RE-DOC-04 §02 Edge Cases table `[DOCUMENTED]`

**Five edge cases with resolutions:**

1. **User likes only 3 dishes:** Relax λ toward 0.90 (relevance-dominant). Introduce genome-similar unexplored dishes. Increase exploration bonus temporarily.  
2. **Cohort has limited dish variety:** Borrow from geographically adjacent cohort. Flag as content database gap — trigger content ops to add dishes.  
3. **Mono-cuisine household:** Respect cuisine preference. Reduce variety pressure on cuisine dimension only. Maintain variety on cooking\_method and main\_ingredient\_class dimensions.  
4. **Festive week:** Suspend variety guard for cuisine dimension during declared festival week. Allow traditional dishes to repeat. Festival detection via festival\_calendar table.  
5. **Illness/recovery context:** If user repeatedly accepts comfort dishes and rejects variety → reduce variety pressure for 5-day window. Reset after 5 days.

**CDM entities:** Variety Window State (32), Festival (47)

---

## Section 09 — Suppression Rules

### LF-G01: processNeverGesture()

**Purpose:** Handle Never confirmation — permanent dish exclusion with class-level signal.  
**Source:** RE-DOC-04 §03, DOC-05 Flow 3b `[DOCUMENTED]`

**Processing steps (in order):**

1. Create entry in re\_engine.never\_list: {profile\_id, dish\_id, nevered\_at=now(), is\_active=true}  
2. Assess reactivation eligibility:  
   - seasonal\_reactivation\_eligible \= (dish.seasonal\_affinity is not empty AND seasonal\_affinity \!= \['all\_season'\])  
   - festival\_reactivation\_eligible \= (dish.festival\_relevance is not empty AND festival\_relevance \!= \['none'\])  
3. Count total active Nevers for dish.meal\_class\_code for this user:  
   - If count \>= 3: reduce class\_affinity\[class\_code\] by 0.15 per Never beyond threshold. `[CONFIRMED]`  
4. Log Interaction Event: {event\_type=dish\_never, dish\_id, meal\_slot, occurred\_at}  
5. Trigger slot refresh: POST /v1/recommendations with dish\_id in exclude\_dish\_ids\[\]

**Invariant:** Never entry with is\_active=true permanently excludes dish from ALL future candidate generation. `[Source: CDM Invariant 10]`  
**CDM entities:** Never List (30), Class Affinity (46), Interaction Events (29)

---

### LF-G02: processNotTodayGesture()

**Purpose:** Create temporary suppression for a dish.  
**Source:** RE-DOC-04 §03, DOC-05 Flow 3a `[DOCUMENTED]`

**Processing steps:**

1. Create/update not\_today\_suppression: {profile\_id, dish\_id, suppressed\_at=now(), P0=0.80, lambda=0.35, effective\_until=now()+7\_days, is\_active=true}  
2. Log Interaction Event: {event\_type=dish\_not\_today, dish\_id, meal\_slot, occurred\_at}  
3. Trigger slot refresh (same mechanism as G-01 step 5\)

**CDM entities:** Not Today Suppression (31), Interaction Events (29)

---

### LF-G03: computeNotTodayPenalty()

**Purpose:** At recommendation time, compute current penalty for a dish with active Not Today suppression.  
**Source:** RE-DOC-04 §03 `[DOCUMENTED]`

**Formula:**

t \= (now() \- suppressed\_at).days

Penalty(t) \= 0.80 × e^(-0.35 × t)

If Penalty \< 0.05: set is\_active \= false. Dish returns to normal pool.

Context override: if t \>= 3 AND ContextFit \> 0.90: Penalty \= Penalty × 0.50

**Implementation:** Query not\_today\_suppression WHERE profile\_id \= :user\_id AND dish\_id \= :dish\_id AND is\_active \= true. If found: compute Penalty(t). Apply to FinalScore as negative term.  
**CDM entities:** Not Today Suppression (31)

---

### LF-G04: processClassLevelNeverSignal()

**Purpose:** After 3+ Never gestures from same class, reduce that class's affinity weight.  
**Source:** RE-DOC-04 §03 `[DOCUMENTED]`, magnitude `[CONFIRMED]`

**Trigger:** count(never\_list WHERE class\_code \= :class\_code AND profile\_id \= :user\_id AND is\_active \= true) \>= 3  
**Logic:** class\_affinity\[class\_code\] −= 0.15 per Never beyond the 3rd. `[CONFIRMED]`  
Applied to user\_taste\_vectors.class\_affinity JSONB.  
**CDM entities:** Class Affinity (46), Never List (30)

---

### LF-G05: checkNeverReactivation()

**Purpose:** Weekly CRON check for never-listed dishes eligible for seasonal or festival re-surfacing.  
**Source:** RE-DOC-04 §03 reactivation rules `[DOCUMENTED]`

**Seasonal reactivation query:**

SELECT nl.profile\_id, nl.dish\_id

FROM re\_engine.never\_list nl

JOIN dishes d ON d.id \= nl.dish\_id

WHERE nl.seasonal\_reactivation\_eligible \= true

  AND nl.nevered\_at \< NOW() \- INTERVAL '6 months'

  AND :current\_season \= ANY(d.seasonal\_affinity)

  AND nl.is\_active \= true

**Festival reactivation query:**

SELECT nl.profile\_id, nl.dish\_id

FROM re\_engine.never\_list nl

JOIN dishes d ON d.id \= nl.dish\_id

JOIN re\_festival\_calendar fc ON :current\_date BETWEEN fc.start\_date \- INTERVAL '21 days' AND fc.end\_date

  AND fc.festival\_name \= ANY(d.festival\_relevance)

WHERE nl.festival\_reactivation\_eligible \= true

  AND nl.nevered\_at \< NOW() \- INTERVAL '90 days'

  AND nl.is\_active \= true

**Re-surfacing behaviour:** For each eligible: queue a soft prompt notification. User must actively confirm. Never entry is NOT automatically set to is\_active=false. Only user confirmation reactivates.  
**CDM entities:** Never List (30), Festival (47)

---

## Section 10 — Safety Gates

All 4 gates must return 0 rows before any plan is served and before any RE deployment. Any non-zero result is a P0 production incident. `[Source: RE-DOC-03 §03, RE-DOC-05 §04, CDM Invariant 11]`

### LF-H01: safetyGateDietViolations() — Gate 1

**Source:** RE-DOC-05 §04 Query 1 `[DOCUMENTED]`

SELECT sl.profile\_id, sl.dish\_id

FROM suggestion\_logs sl

JOIN dishes d ON d.id \= sl.dish\_id

JOIN profiles p ON p.id \= sl.profile\_id

WHERE 

  (p.diet\_type \= 'veg'    AND d.diet\_type NOT IN ('veg','vegan','jain'))

  OR (p.diet\_type \= 'jain'   AND d.is\_jain \= false)

  OR (p.diet\_type \= 'vegan'  AND d.diet\_type \!= 'vegan')

  OR (p.diet\_type \= 'egg'    AND d.diet\_type NOT IN ('veg','vegan','jain','egg'))

AND sl.created\_at \> NOW() \- INTERVAL '1 hour';

\-- Must return 0 rows

---

### LF-H02: safetyGateAllergenViolations() — Gate 2

**Source:** RE-DOC-05 §04 Query 2 — corrected to ingredient level `[DOCUMENTED + corrected per C-003 principle]`

\-- Ingredient-level check (more rigorous than dish-level)

SELECT DISTINCT sl.profile\_id, sl.dish\_id, i.name as allergen\_ingredient

FROM suggestion\_logs sl

JOIN dish\_ingredients di ON di.dish\_id \= sl.dish\_id

JOIN ingredients i ON i.id \= di.ingredient\_id

JOIN profiles p ON p.id \= sl.profile\_id

WHERE (i.allergen\_flags & p.allergen\_flags) \> 0

  AND sl.created\_at \> NOW() \- INTERVAL '1 hour'

UNION ALL

\-- Also check household member allergens

SELECT DISTINCT sl.profile\_id, sl.dish\_id, i.name

FROM suggestion\_logs sl

JOIN dish\_ingredients di ON di.dish\_id \= sl.dish\_id

JOIN ingredients i ON i.id \= di.ingredient\_id

JOIN household\_members hm ON hm.profile\_id \= sl.profile\_id AND hm.is\_active \= true

WHERE (i.allergen\_flags & hm.allergen\_flags) \> 0

  AND sl.created\_at \> NOW() \- INTERVAL '1 hour';

\-- Must return 0 rows

---

### LF-H03: safetyGateJainViolations() — Gate 3

**Source:** RE-DOC-05 §04 Query 3 `[DOCUMENTED]`

SELECT sl.profile\_id, sl.dish\_id

FROM suggestion\_logs sl

JOIN dishes d ON d.id \= sl.dish\_id

JOIN profiles p ON p.id \= sl.profile\_id

WHERE p.religious\_pref \= 'jain'

  AND d.is\_jain \= false

  AND sl.created\_at \> NOW() \- INTERVAL '1 hour';

\-- Must return 0 rows

---

### LF-H04: safetyGatePlanningRoleViolations() — Gate 4

**Source:** CDM Invariant 5, RE-DOC-03 §01 `[DOCUMENTED]`

SELECT ps.id, ps.class\_code

FROM plan\_slots ps

JOIN re\_meal\_classes rmc ON rmc.class\_code \= ps.class\_code

WHERE ps.is\_addon \= false

  AND rmc.planning\_role \!= 'MAIN\_PRIMARY'

  AND ps.created\_at \> NOW() \- INTERVAL '1 hour';

\-- Must return 0 rows

---

## Section 11 — Context Assembly

### LF-I01: assembleContext()

**Purpose:** Build the complete context object for a recommendation request.  
**Source:** RE-DOC-02 §05, RE-DOC-01 §03 API format `[DOCUMENTED]`

**Context object structure:**

{

  "weather\_condition": "rainy|hot|cold|mild",

  "temp\_c": float,

  "city": string,

  "day\_of\_week": "monday|tuesday|...|sunday",

  "is\_weekend": boolean,

  "season": "summer|monsoon|post\_monsoon|winter",

  "time\_of\_day": "morning|afternoon|evening",

  "festival\_proximity": {"festival\_name": string, "days\_until": integer} | null

}

**Assembly sequence:** LF-I02 (weather) → LF-I03 (condition) → LF-I04 (season) → LF-I05 (festival) → compose object  
**Logged per request** in context\_log (append-only ML feature store). `[Source: RE-DOC-05 §02]`

---

### LF-I02: fetchWeatherWithCache()

**Purpose:** Check city-level weather cache before calling OpenWeatherMap API.  
**Source:** CDM Entity 46, DOC-10 §02 external services `[DOCUMENTED]`

**Logic:**

1\. SELECT \* FROM weather\_cache WHERE city \= :city AND date \= :today AND expires\_at \> now()

2\. If cache hit (valid): return cached condition

3\. If cache miss (expired or absent):

   a. Call OpenWeatherMap API: GET /forecast?q={city}\&appid={key}

   b. Extract temp\_c and precipitation from response

   c. INSERT INTO weather\_cache: (city, date, temp\_c, humidity\_pct, condition, fetched\_at, expires\_at=now()+12h)

   d. Return new condition

**Free tier constraint:** 1,000 calls/day. City-level cache ensures maximum \~20–30 cities/day of API calls at MVP scale, well within free tier. `[Source: DOC-10 §02]`  
**Failure:** API unavailable AND cache expired → use 'mild' as safe default. Log as warning.

---

### LF-I03: classifyWeatherCondition()

**Purpose:** Derive weather\_condition enum from temperature and precipitation.  
**Source:** RE-DOC-02 §05 temperature bands `[DOCUMENTED]`

if temp\_c \< 15: condition \= 'cold'

elif temp\_c \<= 28 AND precipitation \> 0.1mm: condition \= 'rainy'  

elif temp\_c \>= 30: condition \= 'hot'

else: condition \= 'mild'

---

### LF-I04: deriveSeason()

**Purpose:** Derive current Indian season from calendar month.  
**Source:** CDM Entity 45 `[DOCUMENTED]`

if month in \[3,4,5\]: season \= 'summer'

if month in \[6,7,8,9\]: season \= 'monsoon'

if month in \[10,11\]: season \= 'post\_monsoon'

if month in \[12,1,2\]: season \= 'winter'

Note: City-specific monsoon onset varies. V1 uses calendar approximation.

---

### LF-I05: checkFestivalProximity()

**Purpose:** Determine if within 21-day festival window.  
**Source:** RE-DOC-02 §05, RE-DOC-04 §03 `[DOCUMENTED]`

**Phase 2 feature.** For MVP: always returns null. Festival calendar table populated before Phase 2 activation.

\-- Phase 2 only:

SELECT festival\_name, (start\_date \- :today) AS days\_until

FROM re\_festival\_calendar

WHERE :today BETWEEN (start\_date \- INTERVAL '21 days') AND end\_date

ORDER BY start\_date ASC

LIMIT 1

---

## Section 12 — Learning Loop and Feature Store

### LF-J01: processInteractionEvent()

**Purpose:** Route incoming interaction event to appropriate update functions.  
**Source:** DOC-10 §05 POST /v1/events, RE-DOC-05 §02 `[DOCUMENTED]`

**All events → log to interaction\_events (append-only)**

**Event routing:** | event\_type | Additional functions triggered | |---|---| | dish\_never | LF-G01, LF-G04 | | dish\_not\_today | LF-G02 | | dish\_accepted, dish\_locked, dish\_cooked, dish\_rated, dish\_swiped\_past | LF-J03, LF-J04 | | dish\_accepted, dish\_locked, dish\_cooked | also LF-J02 (interaction\_count++) | | dish\_swiped\_past, dish\_not\_today | also LF-J02, LF-J04 (β++) | | onboarding\_class\_preference | LF-J06 only | | plan\_opened, session\_depth | no RE learning functions (analytics only) |

**Processing:** Async. Events logged immediately (synced\_to\_re=false). Background processor runs every 15 minutes. After processing: synced\_to\_re=true.

---

### LF-J02: updateInteractionCount()

**Purpose:** Increment interaction\_count and check cold start threshold.  
**Source:** CDM Entity 14, RE-DOC-03 §02 weight ladder `[DOCUMENTED]`

**Logic:**

interaction\_count \+= 1

if interaction\_count \>= 14 AND cold\_start\_mode \= true:

  trigger LF-J05 (exitColdStart)

**Events that count:** dish\_accepted, dish\_locked, dish\_cooked, dish\_rated, dish\_swiped\_past, dish\_not\_today, dish\_never, onboarding\_class\_preference  
**Events that do NOT count:** plan\_opened, session\_depth

---

### LF-J03: updateGenomeTagAffinity()

**Purpose:** Update user's genome\_tag\_affinity taste vector based on accepted/rejected dish genome.  
**Source:** RE-DOC-03 §02 ContentMatch signal `[DOCUMENTED]`, update formula `[CONFIRMED]`

**For positive events (dish\_accepted, dish\_locked, dish\_cooked):**

For each Tier-1 and Tier-2 genome tag in dish:

  genome\_tag\_affinity\[tag\] \+= event\_weight × (1 \- genome\_tag\_affinity\[tag\] × 0.1)

  // dampening\_factor=0.1 prevents runaway high scores

**For mild negative events (dish\_swiped\_past):**

For the top 3 most prominent Tier-1 genome tags of dish:

  genome\_tag\_affinity\[tag\] \-= event\_weight × 0.5

  // Only top 3 tags, at half strength

**Floors and ceilings:** genome\_tag\_affinity values bounded to \[−1.0, 2.0\].

---

### LF-J04: updateBanditState()

**Purpose:** Update Thompson Sampling α and β parameters.  
**Source:** RE-DOC-03 §02, RE-DOC-05 §01 `[DOCUMENTED]`

**Logic:**

positive events (accepted, locked, cooked): α \+= 1

negative events (swiped\_past, not\_today):   β \+= 1

Applied to re\_dish\_bandit\_state WHERE profile\_id \= :user\_id AND dish\_id \= :dish\_id. Create row if absent (initial: α=1, β=1 adjusted to cohort base).

---

### LF-J05: exitColdStart()

**Purpose:** Transition user out of cold start mode.  
**Source:** CDM Entity 14 `[DOCUMENTED]`

**Logic:** If interaction\_count \>= 14 AND cold\_start\_mode \= true → SET cold\_start\_mode \= false on user\_re\_state.  
**Effect:** Weight ladder continues interpolating from current interaction\_count. The "Still learning your taste" badge no longer shows. `[Source: RE-DOC-01 §05]`

---

### LF-J06: updateClassAffinity()

**Purpose:** Update class-level affinity weights from OB-07 swipes and class-level Never signals.  
**Source:** DOC-06 C-07, RE-DOC-04 §03 `[DOCUMENTED]`, magnitudes `[CONFIRMED]`

**OB-07 swipe signal:**

YES swipe: class\_affinity\[class\_code\] \= min(2.0, class\_affinity\[class\_code\] \+ 0.30)

NOPE swipe: class\_affinity\[class\_code\] \= max(-1.0, class\_affinity\[class\_code\] \- 0.30)

**Class-level Never signal (triggered from LF-G04):**

For each Never beyond the 3rd for a class\_code:

  class\_affinity\[class\_code\] \= max(-1.0, class\_affinity\[class\_code\] \- 0.15)

Applied to user\_taste\_vectors.class\_affinity JSONB.

---

### LF-J07: logFeatureStore()

**Purpose:** Append all required ML feature categories from Day 1\.  
**Source:** RE-DOC-05 §02 `[DOCUMENTED]`

**Per recommendation request:** Append to context\_log (context features). Append to suggestion\_logs per dish shown (plan features including slate\_id, class\_code, confidence, re\_version, cold\_start\_mode, n\_candidates\_before\_filter).

**Per interaction event:** Append to interaction\_events (interaction features including rank\_at\_interaction, time\_viewed\_ms, confidence\_at\_time, re\_version).

**Daily CRON:** Run LF-J09 (dish feature snapshot).

**Critical principle:** Features not logged from Day 1 cannot be used in future ML models. `[Source: RE-DOC-05 §02]`

---

### LF-J08: cohortWeightRecalibration()

**Purpose:** Weekly CRON to compare actual acceptance rates per cohort vs research priors.  
**Source:** DOC-10 §05 CRON schedule (Sunday 18:00 UTC) `[DOCUMENTED]`  
**Algorithm:** `[UNRESOLVED — the comparison and update logic is not defined in any document]`

**CRON schedule:** Sunday 18:00 UTC \= Sunday 23:30 IST. `[Source: DOC-10 §05]`

**Data inputs available:** suggestion\_logs (past 7 days), interaction\_events with dish\_accepted for same period.

**Unresolved:** How much divergence triggers an update? What is the update formula? This algorithm requires a product decision before Sprint 6 when it first becomes meaningful (insufficient data at launch for meaningful recalibration).

**P3-03 flag:** `[UNRESOLVED — product decision required before implementation of this CRON. Can be a no-op at launch without impact to MVP quality]`

---

### LF-J09: dailyDishFeatureSnapshot()

**Purpose:** Daily snapshot of current dish feature state for future ML training.  
**Source:** RE-DOC-05 §02 `[DOCUMENTED]`

**CRON:** Daily 00:00 UTC.

**Snapshot per active dish:**

INSERT INTO re\_engine.dish\_features (dish\_id, snapshot\_date, genome\_tags\_json, 

  meal\_class\_codes, popularity\_score, acceptance\_rate\_7d, acceptance\_rate\_30d)

SELECT 

  d.id, CURRENT\_DATE,

  (SELECT jsonb\_object\_agg(tag\_name, confidence) FROM dish\_tags WHERE dish\_id \= d.id),

  ARRAY(SELECT class\_code FROM re\_class\_dish\_options WHERE dish\_id \= d.id),

  d.popularity\_score,

  \-- acceptance\_rate\_7d: accepted events / shown events in last 7 days

  COALESCE(

    COUNT(ie.id) FILTER (WHERE ie.event\_type IN ('dish\_accepted','dish\_locked','dish\_cooked'))::float

    / NULLIF(COUNT(sl.id), 0), 0

  ) as acceptance\_rate\_7d

FROM dishes d

LEFT JOIN suggestion\_logs sl ON sl.dish\_id \= d.id AND sl.suggested\_at \> NOW() \- INTERVAL '7 days'

LEFT JOIN interaction\_events ie ON ie.dish\_id \= d.id AND ie.occurred\_at \> NOW() \- INTERVAL '7 days'

WHERE d.is\_active \= true

GROUP BY d.id

---

## Section 13 — Dish Content Derivation

### LF-K01: deriveDishAttributes()

**Purpose:** Auto-derive diet\_type, is\_jain, allergen\_flags from ingredients. NEVER manually set.  
**Source:** CDM Invariant 6, RE-DOC-02 §03 `[DOCUMENTED]`

**Triggers:** AFTER INSERT or UPDATE on dish\_ingredients. Also runs as weekly batch for all dishes.

**Derivation rules:**

allergen\_flags (dish) \= bitwise OR of all ingredients.allergen\_flags

diet\_type (dish):

  if ANY ingredient where is\_veg \= false: diet\_type \= 'non\_veg'

  elif ANY ingredient where allergen\_flags & 16 \> 0 (egg bit): diet\_type \= 'egg'

  elif ALL ingredients where is\_vegan \= true: diet\_type \= 'vegan'

  else: diet\_type \= 'veg'

is\_jain (dish):

  if ALL ingredients where is\_jain\_excluded \= false AND diet\_type \= 'veg': is\_jain \= true

  else: is\_jain \= false

**Conflict detection:** If derived value differs from any manually-set value → log conflict to derivation\_conflicts table. Derived value always wins.  
**CDM entities:** Dish (15), Ingredient (18)

---

### LF-K02: updateDishGenomeVector()

**Purpose:** Recompute dish's genome vector when genome tags change.  
**Source:** RE-DOC-02 §02 `[DOCUMENTED]`, format `[Implementation decision for P3-04]`

**Trigger:** AFTER INSERT or UPDATE on dish\_tags WHERE tier IN (1,2).

**Logic:** Assemble float vector from all Tier-1 and Tier-2 tags ordered by tag\_id sequence. Normalise. Store as dish.genome\_vector.

**Format decision:** Vector is a float\[\] array with fixed dimension order from tags master table. `[P3-04 will specify exact format]`

---

### LF-K03: updateDishPopularityScore()

**Purpose:** Daily update of dish popularity from acceptance logs.  
**Source:** RE-DOC-05 §02, CDM Entity 15 `[DOCUMENTED]`, weights `[PROPOSED]`

**Formula:**

popularity\_score \= 0.60 × acceptance\_rate\_7d \+ 0.40 × acceptance\_rate\_30d

Where acceptance\_rate \= accepted\_count / shown\_count.  
**Run by:** LF-J09 daily snapshot CRON.

---

### LF-K04: validateDishTier1Completeness()

**Purpose:** Validate all mandatory Tier-1 genome tags before dish is eligible for recommendation.  
**Source:** CDM Entity 15, RE-DOC-02 §02 `[DOCUMENTED]`

**Required Tier-1 tags:** meal\_occasion, diet\_type, allergen\_flags, spice\_level, cook\_time\_band, difficulty, calorie\_band

**Logic:** SELECT COUNT(\*) FROM dish\_tags WHERE dish\_id \= :id AND tier \= 1 AND tag\_name IN (...required 7...) AND confidence \>= 0.85

**If incomplete:** Dish must NOT be added to re\_class\_dish\_options. Content ops must complete Tier-1 tagging first.

---

## Section 14 — Plan Management

### LF-L01: generateWeekPlan()

**Purpose:** Orchestrate complete 7-day plan generation for a household.  
**Source:** DOC-10 §05 morning CRON, DOC-04 Steps 1–6 `[DOCUMENTED]`

**Sequence:**

1\. LF-B01 fetchPersona()

2\. LF-B02 generateClassPlan()  → 21 class assignments

3\. LF-B03 (non-veg cadence overlay if applicable)

4\. LF-C01 generateAddons()     → add-on slot records

5\. For each of 21 primary slots:

   a. LF-D01 getClassCandidates()

   b. LF-D02 through LF-D06 (all 5 hard constraint filters)

   c. LF-D07 if \< 3 candidates survive

   d. LF-E01 through LF-E08 (scoring)

   e. LF-F01 applyMMR()

   f. LF-F02 checkVarietyWindowRules()

6\. LF-H01 through LF-H04 (all 4 safety gates)

7\. Write week\_plans \+ plan\_slots to database

8\. Populate plan\_cache for morning load

**CRON schedule:** 23:30 UTC daily (05:00 IST) for all users with last\_active\_at within 7 days. `[Source: DOC-10 §05]`

**Performance target:** \< 3s total end-to-end. Edge Function execution: \< 800ms. `[Source: DOC-04 NFR, DOC-10 §07]`

---

### LF-L02: refreshUnlockedSlots()

**Purpose:** Regenerate slates for all unlocked slots on pull-to-refresh.  
**Source:** DOC-05 §06 gesture, DOC-10 §04 `[DOCUMENTED]`

**Logic:** For each plan\_slot WHERE week\_plan\_id \= :current\_week\_plan AND is\_locked \= false:

- Re-run LF-D01 through LF-F02 for that slot  
- class\_code assignment does NOT change on refresh — only dish candidates within the same class regenerate  
- Write new slate\_dish\_ids\[\] and slate\_reasons to plan\_slot

**Locked slots:** Completely untouched. is\_locked=true slots skip all refresh operations.

---

### LF-L03: promoteSlateDish()

**Purpose:** When user rejects primary dish (Not Today or Never), trigger single-slot refresh.  
**Source:** RE-DOC-01 §03 API (exclude\_dish\_ids\[\]), DOC-05 Flow 3a/3b `[DOCUMENTED]`

**Mechanism:** App sends POST /v1/recommendations for that specific slot\_date \+ meal\_slot, with rejected dish\_id in exclude\_dish\_ids\[\]. The RE runs the full pipeline for that single slot, excluding the rejected dish. Returns a fresh slate.

**Fast path:** While waiting for the fresh slate, the next-ranked dish from the existing stored slate\_dish\_ids\[\] is promoted immediately in the UI.

---

### LF-L04: handleOB08bInteractions()

**Purpose:** Process interactions on plan preview before onboarding is complete.  
**Source:** DOC-05 OB-08b, DOC-06 wireframe `[DOCUMENTED]`

**Logic:** Interactions on OB-08b are valid Interaction Events with event\_type (dish\_accepted, dish\_never, dish\_not\_today). They:

- Are logged to interaction\_events with occurred\_at \= now()  
- Increment interaction\_count  
- Are processed through the same LF-J01 routing as post-onboarding events  
- Count toward the 14-interaction cold start threshold

**Note:** These events occur before onboarding\_completed \= true is set on the profile. The RE must accept events from users in onboarding state.

---

## Section 15 — Compliance Functions

### LF-M01: captureConsent()

**Purpose:** Record granular DPDP consent at signup.  
**Source:** DOC-09 §03 `[DOCUMENTED]`

**Consent categories (separate explicit action required for each):** | Consent type | Required for | |---|---| | personalization | Dietary preference collection, RE personalization | | analytics | PostHog event tracking | | push\_notifications | OneSignal morning plan notifications | | data\_retention | Retention of interaction events for RE learning |

**Rule:** personalization consent must be granted BEFORE any dietary or preference data is collected in onboarding. If personalization consent is denied, the RE cannot function — user must be informed. `[Source: DOC-09 §03]`

**Storage:** One row per consent category per user. Append-only on consent changes. `[Source: CDM Invariant — separate consent table per C-002 resolution]`

---

### LF-M02: executeDataExport()

**Purpose:** DPDP data export within 72 hours of user request.  
**Source:** DOC-09 §03, DOC-10 §06 `[DOCUMENTED]`

**Data scope:** profiles, household\_members, interaction\_events, week\_plans, plan\_slots, never\_list, onboarding\_sessions, consent\_records  
**Endpoint:** GET /v1/user/export (JWT authenticated)  
**Format:** JSON. Queued job completes within 72 hours.

---

### LF-M03: executeDataDeletion()

**Purpose:** DPDP account deletion — permanent erasure within 72 hours.  
**Source:** DOC-09 §03, DOC-10 §06 `[DOCUMENTED]`

**Logic:** Soft-delete immediately (mark deleted\_at). Hard-delete all personal data within 72h via CRON.  
**Exception:** audit\_log rows retained for 3 years per DPDP Act requirements.  
**Scope:** All personal data — including interaction\_events (not anonymized, fully deleted for this user).  
**Note:** This is permanent erasure, NOT soft-delete. `[Source: DOC-09 §03]`

---

## Section 16 — Configuration Parameters

All numeric parameters are stored in configuration tables. No value is hardcoded. Edge Functions read these tables at runtime.

**Table: re\_weight\_ladder\_config** | config\_key | value | source | |---|---|---| | tier\_0\_interactions | 0 | RE-DOC-03 | | tier\_1\_interactions | 10 | RE-DOC-03 | | tier\_2\_interactions | 50 | RE-DOC-03 | | tier\_3\_interactions | 150 | RE-DOC-03 | | cold\_start\_exit\_threshold | 14 | CDM Entity 14 | | tier\_0\_w\_cohort | 0.55 | RE-DOC-03 | | tier\_0\_w\_content | 0.20 | RE-DOC-03 | | tier\_0\_w\_history | 0.00 | RE-DOC-03 | | tier\_0\_w\_context | 0.15 | RE-DOC-03 | | tier\_0\_w\_explore | 0.10 | RE-DOC-03 | | tier\_4\_w\_cohort | 0.05 | RE-DOC-03 | | tier\_4\_w\_history | 0.65 | RE-DOC-03 | | tier\_4\_w\_explore | 0.00 | RE-DOC-03 |

**Table: re\_scoring\_config** | config\_key | value | source | |---|---|---| | not\_today\_P0 | 0.80 | RE-DOC-04 | | not\_today\_lambda | 0.35 | RE-DOC-04 | | not\_today\_expiry\_days | 7 | RE-DOC-04 | | not\_today\_decay\_threshold | 0.05 | RE-DOC-04 | | personal\_history\_lambda | 0.05 | CONFIRMED | | mmr\_lambda\_mvp | 0.70 | RE-DOC-04 | | mmr\_lambda\_phase1 | 0.55 | RE-DOC-04 | | exploration\_bonus\_max | 0.15 | RE-DOC-03 | | bandit\_explore\_pct | 0.10 | RE-DOC-05 |

**Table: re\_event\_weights** | event\_type | weight | source | |---|---|---| | dish\_cooked | \+0.80 | CONFIRMED | | dish\_locked | \+0.60 | CONFIRMED | | dish\_rated\_5star | \+0.60 | CONFIRMED | | dish\_accepted | \+0.40 | CONFIRMED | | dish\_rated\_3star | \+0.00 | CONFIRMED | | dish\_rated\_1star | −0.30 | CONFIRMED | | dish\_swiped\_past | −0.10 | CONFIRMED | | dish\_not\_today | −0.10 | DOCUMENTED (RE-DOC-04 §03) | | onboarding\_class\_preference\_yes | \+0.30 | CONFIRMED | | onboarding\_class\_preference\_nope | −0.30 | CONFIRMED |

**Table: re\_confidence\_config** | config\_key | value | source | |---|---|---| | base\_confidence\_floor | 0.40 | RE-DOC-04 | | home\_state\_contribution | \+0.15 | RE-DOC-04 | | diet\_type\_contribution | \+0.10 | RE-DOC-04 | | city\_overlay\_contribution | \+0.08 | RE-DOC-04 | | cook\_capability\_contribution | \+0.07 | RE-DOC-04 | | class\_pref\_swipes\_contribution | \+0.12 | RE-DOC-04 | | context\_signals\_contribution | \+0.08 | RE-DOC-04 | | skip\_non\_critical\_penalty | −0.05 | RE-DOC-04 | | skip\_diet\_type\_penalty | −0.15 | RE-DOC-04 | | skip\_ob03\_penalty | −0.08 | DOC-06 C-11 | | all\_skipped\_floor | 0.35 | RE-DOC-04 | | still\_learning\_threshold | 0.30 | RE-DOC-01 |

**Table: re\_city\_overlay\_config** | migration\_band | city\_overlay\_weight | source | |---|---|---| | \<1yr | 0.15 | DOC-06 C-11 | | 1\_3yr | 0.30 | DOC-06 C-11 | | 3\_7yr | 0.50 | DOC-06 C-11 | | 7plus\_yr | 0.70 | DOC-06 C-11 | | skip\_default | 0.50 | DOC-06 C-11 |

**Table: re\_variety\_rules** (seed data per rule) | rule\_name | window\_days | cap\_value | override\_condition | source | |---|---|---|---|---| | same\_cuisine\_breakfast | 5 | 2 | — | RE-DOC-04 | | same\_cuisine\_dinner | 5 | 2 | — | RE-DOC-04 | | fried\_method | 7 | 3 | monsoon→4 | RE-DOC-04 | | same\_main\_ingredient | 2 | 1 | rice\_forms\_distinct | RE-DOC-04 | | same\_dish | 30 | 1 | locked\_override | RE-DOC-04 | | same\_breakfast\_class | 7 | 3 | weekend\_sweet\_warm | RE-DOC-04 |

**Table: re\_class\_affinity\_config** | config\_key | value | source | |---|---|---| | ob07\_yes\_delta | \+0.30 | CONFIRMED | | ob07\_nope\_delta | −0.30 | CONFIRMED | | never\_class\_trigger\_count | 3 | RE-DOC-04 | | never\_class\_delta | −0.15 | CONFIRMED | | class\_affinity\_floor | −1.00 | CDM | | class\_affinity\_ceiling | \+2.00 | CDM |

---

## Section 17 — Unresolved Decisions Register

Items that remain unresolved after all documentation was reviewed. Must be resolved before implementation begins.

| \# | Item | Impact | Recommended resolution | Priority |
| :---- | :---- | :---- | :---- | :---- |
| U-001 | Context override threshold in LF-E07 (ContextFit \> ? for Not Today partial override) | Minor scoring behaviour | Suggest 0.90 as threshold | Low |
| U-002 | Cohort weight recalibration algorithm in LF-J08 | Weekly CRON behaviour | Can be a no-op at launch. Define algorithm before 30 days post-launch. | P2 (not MVP blocking) |
| U-003 | "Still learning" UI surface (RE-DOC-01: confidence \< 0.30 → message) | UX only | Design decision needed in DOC-05/DOC-06 | Low |
| U-004 | MC\_GENERIC fallback | Confirmed as Option B by founder | RESOLVED in LF-A09 | — |
| U-005 | Event weights | Confirmed by founder | RESOLVED in LF-E04 | — |

---

## Section 18 — Metric Definitions

Success metrics from RE-DOC-05 §04, formally defined:

**Acceptance rate:** (count of dish\_locked \+ dish\_cooked \+ dish\_ordered events) ÷ (count of dishes shown in suggestion\_logs). Measured per user per day. `[Source: RE-DOC-05 §04]`

**Never rate:** (count of dish\_never events) ÷ (count of dishes shown). `[Source: RE-DOC-05 §04]`

**Session depth:** count of dish interactions (swipes, taps) before first dish\_accepted event per session. `[Source: RE-DOC-05 §04]`

**Class hit rate:** (count of plan\_slots where final\_selected\_dish.class\_code \= slot.class\_code) ÷ total plan\_slots with a selected dish. `[Source: RE-DOC-05 §04]`

**Constraint compliance:** 100% always. Any safety gate violation \= compliance failure. `[Source: RE-DOC-05 §04]`

**Variety score:** Average pairwise cosine dissimilarity of dishes in a user's 7-day plan. Target: \> 0.55. `[Source: RE-DOC-05 §04]`

**Offline evaluation (for RE version promotion):**

- MRR@8: Mean Reciprocal Rank of first accepted dish in 8-item slate. New version must be \>= current. `[Source: RE-DOC-05 §04]`  
- NDCG@8: Normalized DCG. New version must be \>= current − 0.02. `[Source: RE-DOC-05 §04]`  
- Diversity score: New version \>= current − 0.03. `[Source: RE-DOC-05 §04]`  
- Shadow mode acceptance: Within 5% of production over 72h shadow run. `[Source: RE-DOC-05 §04]`

---

## Document sign-off

| Field | Value |
| :---- | :---- |
| Document | DOC-P3-03 · Business Logic and Algorithm Specification |
| Version | 1.0 |
| Status | ACTIVE — [FD-05, 2026-07-16] no Founder signature required for `[ACTIVE]` status; see naming standard amendment |
| Logical functions specified | 61 across 13 groups |
| Documented facts | All specifications with \[DOCUMENTED\] tag |
| Confirmed decisions | Event weights, MC\_GENERIC fallback, class affinity magnitudes (all \[CONFIRMED\]) |
| Unresolved decisions | 3 — all P2 or Low priority, none MVP-blocking |
| Source coverage | 18 active documents. 13 contribute to P3-03. 5 confirmed as non-contributing. |
| Next document | DOC-P3-04 · Data Architecture and Entity Relationship Model |
| Prerequisite for | DOC-P3-04, DOC-P3-05 (Database Schema), DOC-P4-02 (Service Specifications) |

Founder sign-off: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ Date: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_  
