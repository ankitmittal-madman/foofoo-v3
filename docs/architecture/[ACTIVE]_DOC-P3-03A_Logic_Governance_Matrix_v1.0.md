# DOC-P3-03A · Logic Governance and Execution Matrix

**Version:** 1.0
**Date:** June 2026
**Status:** ACTIVE — [FD-05, ratified 2026-07-16] a Founder signature is not required for `[ACTIVE]` status per the amended `[ACTIVE]_Repository_Naming_Standard_v1.0.md`; content freeze is the ratification mechanism. See `[ACTIVE]_Founder_Decision_Register_v1.0.md` FD-05.
**Companion to:** DOC-P3-03 · Business Logic and Algorithm Specification v1.0
**Purpose:** Governance, traceability, execution classification, auditability, and validation of all 61 logical functions defined in P3-03. Does not redefine business logic.
**Next document:** DOC-P3-04 · Data Architecture and Entity Relationship Model

## How this document relates to P3-03

DOC-P3-03 answers: **What does the logic do?**
DOC-P3-03A answers: **How is it organised, governed, executed, traced, and validated?**

Section cross-reference:

- P3-03A §01 (Dependency Graph) → feeds P3-04 table dependency design

- P3-03A §02 (Read/Write Matrix) → feeds P3-04 entity relationships and access patterns

- P3-03A §03 (Configuration Classification) → feeds P3-05 schema config tables

- P3-03A §04 (Traceability) → feeds DOC-P5-02 QA test cases

- P3-03A §05 (Decisions Register) → feeds all downstream documents

- P3-03A §06 (Data Lineage) → feeds P3-04 ERD and P3-06 API design

- P3-03A §07 (Execution Classification) → feeds P3-08 Integration Architecture and deployment plan

- P3-03A §08 (Auditability) → feeds P3-04 append-only table design

- P3-03A §09 (Validation Matrix) → feeds DOC-P5-01 Test Strategy

## Section 01 — Logic Dependency Graph

Organised as execution layers. Functions in the same layer can run in parallel. Functions in a higher layer depend on all outputs of lower layers they reference.

### Layer 0 — Seed and Reference Data (no runtime dependencies)

These are pre-loaded before any function executes. All functions below assume these exist and are valid.

[SEED: re_states, re_main_cohorts, re_personas, re_subcohorts]

[SEED: re_routing_rules]

[SEED: re_meal_classes, re_meal_class_overlap_rules]

[SEED: re_class_dish_options]

[SEED: re_addon_classes, re_addon_dish_options]

[SEED: re_cohorts, re_weekly_class_plans, re_household_addon_plans]

[SEED: re_nonveg_logic, re_city_migration_overlays]

[SEED: re_context_multipliers, re_weight_ladder_config, re_scoring_config]

[SEED: re_event_weights, re_confidence_config, re_variety_rules]

[CONTENT: dishes, ingredients, dish_ingredients, dish_tags, dish_combos]

[CONTENT: meal_classes (public mirror), tags master]

Gate: ALL 15 seed gates (S-01 through S-15) must pass before Layer 1 can execute for any user.

### Layer 1 — Onboarding Pipeline (once per user, sequential)

USER INPUT

    │

    ▼

LF-A01: processMainCohortSelection()

    │  outputs: main_cohort_code

    ▼

LF-A02: processHouseholdBranch()    ←── depends on: A01 output

    │  outputs: sub_cohort_tag, member_segments[]

    ├──→ creates: household_members records

    ▼

LF-A03: processRegionalIdentity()   ←── independent of A02

    │  outputs: home_state, current_city, migration_duration, city_overlay_weight

    ▼

LF-A04: processDietConfiguration()  ←── independent

    │  outputs: diet_type, religious_pref

    ▼

LF-A05: processAllergenExclusions() ←── depends on: A02 (member list)

    │  outputs: allergen_flags (user + members)

    ▼

LF-A06: processCookCapability()     ←── independent

    │  outputs: cook_capability

    ▼

LF-A07: processClassPreferenceSwipes() ←── depends on: diet_type (A04) for dish pool filtering

    │  outputs: class_affinity[] initial values, interaction_events (onboarding)

    ├──→ increments: interaction_count (up to +10)

    ▼

LF-A08: computeOnboardingConfidence() ←── depends on: A01-A07 completeness signals

    │  outputs: confidence_score

    ▼

LF-A09: assignPersona()             ←── depends on: A01 (cohort), A02 (subcohort), A03 (state), A04 (diet)

    │  outputs: persona_id, overlay_persona_ids[]

    │  reads: re_persona_assignment_rules (seed lookup)

    ▼

LF-L04: handleOB08bInteractions()  ←── depends on: A09 (persona needed for plan generation)

    │  generates: first interaction_events from plan preview

    ▼

[ONBOARDING COMPLETE: onboarding_completed = true]

**State transition:** User moves from onboarding_completed=false to true. Cold start mode begins.

### Layer 2 — Plan Generation (per week per user)

[TRIGGER: CRON (23:30 UTC daily) OR first app open after gap]

    │

    ▼

LF-B01: fetchPersona()              ←── reads: user_re_state

    │  outputs: persona_id, overlay_persona_ids[]

    ▼

LF-B02: generateClassPlan()        ←── depends on: B01, Layer 0 (re_weekly_class_plans)

    │  outputs: 21 class assignments [{slot_date, meal_slot, class_code}]

    ▼

LF-B03: applyNonVegCadence()       ←── depends on: B02, A04 (diet_type), A03 (home_state)

    │  outputs: modified class assignments with non-veg slots

    ▼

LF-C01: generateAddons()           ←── depends on: B02/B03, A02 (member_segments)

    │  outputs: addon_slot records [{member, slot_date, meal_slot, addon_class_code}]

    ▼

LF-C02: resolveAddonDish()         ←── depends on: C01 outputs, Layer 0 (re_addon_dish_options)

    │  outputs: dish_id per addon_slot

    ▼

[FOR EACH OF 21 PRIMARY SLOTS → Layer 3]

### Layer 3 — Candidate Generation (per slot, parallelisable across slots)

[INPUT: slot.class_code from Layer 2]

    │

    ▼

LF-D01: getClassCandidates()       ←── reads: re_class_dish_options (seed)

    │  outputs: candidate_dishes[] with base_scores

    ▼

LF-D02: applyDietTypeFilter()      ←── reads: user.diet_type, dishes.diet_type

    │  outputs: filtered_candidates[] (diet-safe)

    ▼

LF-D03: applyAllergenFilter()      ←── reads: combined_allergen_flags, dish_ingredients, ingredients.allergen_flags

    │  outputs: filtered_candidates[] (allergen-safe)

    ▼

LF-D04: applyReligiousFilter()     ←── reads: user.religious_pref, dishes.is_jain

    │  outputs: filtered_candidates[] (religiously compatible)

    ▼

LF-D05: applyMealOccasionFilter()  ←── reads: dishes.meal_occasion, current meal_slot

    │  outputs: filtered_candidates[] (slot-eligible)

    ▼

LF-D06: applyNeverListFilter()     ←── reads: re_engine.never_list (user)

    │  outputs: filtered_candidates[] (never-excluded removed)

    ▼

LF-D07: handleConstraintConflict() ←── triggered only if < 3 survivors

    │  outputs: static fallback dishes OR empty (triggers H-01 state)

    [proceeds to Layer 4 with survivors or fallback]

**Note:** D02–D06 execute in sequence. Each filter reduces the candidate pool. Order matters — diet first (broadest exclusion), never list last (specific user state).

### Layer 4 — Scoring (per candidate dish, per slot)

[INPUT: filtered_candidates[] from Layer 3]

    │

    ├──→ LF-I01 through LF-I05 (Context Assembly — runs in parallel)

    │       outputs: context object {weather, season, day, time, festival}

    │

    ▼

LF-E01: interpolateWeightLadder()  ←── reads: interaction_count, re_weight_ladder_config

    │  outputs: {w_cohort, w_content, w_history, w_context, w_explore}

    │

    [FOR EACH CANDIDATE DISH → parallel scoring]

    ├──→ LF-E02: computeCohortPrior()    ←── reads: re_cohort_class_priors (seed)

    ├──→ LF-E03: computeContentMatch()   ←── reads: user.genome_tag_affinity, dish.genome_vector

    ├──→ LF-E04: computePersonalHistory() ←── reads: interaction_events (this user, this dish), re_event_weights

    ├──→ LF-E05: computeContextFit()     ←── reads: context object (from I-01), dish genome tags, re_context_multipliers

    ├──→ LF-E06: computeExplorationBonus() ←── reads: re_dish_bandit_state (user, dish)

    ├──→ LF-E07: computePenaltyTerms()   ←── reads: not_today_suppression (user, dish)

    │

    ▼

LF-E08: computeFinalScore()        ←── assembles all E02-E07 outputs + E01 weights

    │  outputs: score float per dish

**Parallelism opportunity:** E02 through E07 can run in parallel per dish. E08 collects results.

### Layer 5 — Variety Re-ranking (per slot)

[INPUT: scored_candidates[] from Layer 4, variety_window_state]

    │

    ▼

LF-F02: checkVarietyWindowRules()  ←── reads: variety_window_state (user), re_variety_rules config

    │  outputs: variety_flags per candidate (which rules each dish would violate)

    ▼

LF-F01: applyMMR()                 ←── depends on: F02 flags, E08 scores

    │  reads: dish.genome_vector (for similarity computation)

    │  outputs: reranked_slate[] of 8 dishes in order

    ├──→ LF-F03: handleVarietyEdgeCases() [if needed]

    ▼

[SLATE of 8 ranked dishes → Layer 6]

### Layer 6 — Safety Validation (per slate, blocking)

[INPUT: slate from Layer 5, suggestion_logs (just written)]

    │

    ├──→ LF-H01: safetyGateDietViolations()

    ├──→ LF-H02: safetyGateAllergenViolations()

    ├──→ LF-H03: safetyGateJainViolations()

    └──→ LF-H04: safetyGatePlanningRoleViolations()

    │

    [IF any gate fails: discard slate → regenerate (max 2 retries) → if still fails: 500 + cached plan]

    [IF all gates pass: proceed]

    ▼

[RESPONSE BUILT → returned to app]

### Layer 7 — Interaction Processing (async, event-driven)

[TRIGGER: user interaction in app]

    │

    ▼

LF-J01: processInteractionEvent()  [synchronous: logs event immediately]

    │

    [ASYNC QUEUE — processed every 15 min]

    │

    ├──→ LF-J02: updateInteractionCount()

    │       ├──→ LF-J05: exitColdStart() [if threshold crossed]

    ├──→ LF-J03: updateGenomeTagAffinity()

    ├──→ LF-J04: updateBanditState()

    ├──→ LF-J06: updateClassAffinity() [for OB-07 and class Never signals]

    ├──→ LF-G01: processNeverGesture() [if event_type = dish_never]

    │       ├──→ LF-G04: processClassLevelNeverSignal()

    │       └──→ LF-L03: promoteSlateDish() [slot refresh trigger]

    └──→ LF-G02: processNotTodayGesture() [if event_type = dish_not_today]

            └──→ LF-L03: promoteSlateDish()

### Feedback Loops

FEEDBACK LOOP 1 — Taste Learning:

  User interaction (Layer 7)

    → genome_tag_affinity updated (J-03)

    → ContentMatch (E-03) changes for future requests

    → FinalScore shifts → different dishes rank higher

    → New slate surfaced → user interaction again

FEEDBACK LOOP 2 — Cold Start Exit:

  interaction_count grows (J-02)

    → Weight ladder interpolates (E-01)

    → w_history increases, w_cohort decreases

    → PersonalHistory contributes more to FinalScore

    → Plans become more personalised

FEEDBACK LOOP 3 — Class Affinity:

  Class-level Never gestures (G-01 → G-04)

    → class_affinity decreases for that class

    → generateClassPlan (B-02) queries weighted by class_affinity

    → That class appears less often in future plans

FEEDBACK LOOP 4 — Never Reactivation (weekly):

  G-05 CRON checks seasonal/festival conditions

    → Eligible Never dishes surfaced in prompt

    → User confirms or dismisses

    → If confirmed: dish returns to candidate pool

### State Transitions

| **State** | **Trigger function** | **From state** | **To state** |
| --- | --- | --- | --- |
| Onboarding complete | LF-A09 + LF-L04 | onboarding_completed=false | onboarding_completed=true |
| Cold start exit | LF-J05 | cold_start_mode=true | cold_start_mode=false |
| Slot locked | LF-L02 (user action) | is_locked=false | is_locked=true |
| Slot unlocked | LF-L02 (user action) | is_locked=true | is_locked=false |
| Never activated | LF-G01 | is_active=false (absent) | is_active=true |
| Never reactivated | LF-G05 (user confirm) | is_active=true | is_active=false |
| Not Today active | LF-G02 | absent | is_active=true |
| Not Today expired | LF-G03 (penalty < 0.05) | is_active=true | is_active=false |
| New RE version | Shadow mode → promote | re_version=X | re_version=X+1 |

## Section 02 — Read / Write Matrix

For each logical function group: what data is read, what is written, what is derived, and who consumes the output downstream.

### Group A — Onboarding

| **Function** | **Data Read** | **Data Written** | **Derived Outputs** | **Downstream Consumers** |
| --- | --- | --- | --- | --- |
| A01 CohortSelection | User tap input | onboarding_sessions (OB-01 answer) | main_cohort_code | A02, A09 |
| A02 HouseholdBranch | main_cohort_code, OB-02 user input, re_routing_rules | onboarding_sessions (OB-02), household_members (new rows) | sub_cohort_tag, member_segments[] | A05, A09, C01 |
| A03 RegionalIdentity | OB-03 user input | onboarding_sessions (OB-03), profiles (home_state, current_city, migration_duration, city_overlay_weight) | city_overlay_weight | A09, B02, E05 |
| A04 DietConfig | OB-04 user input | profiles (diet_type, religious_pref) | — | A07, D02, D04 |
| A05 Allergens | OB-05 input, ingredient autocomplete, household_members | profiles (allergen_flags), household_members (allergen_flags per member) | combined_allergen_flags | D03 |
| A06 CookCapability | OB-06 user input | profiles (cook_capability) | — | B02, D01 |
| A07 ClassPrefSwipes | OB-07 dish pool, user swipes, diet_type | interaction_events (10 rows), user_taste_vectors (class_affinity) | class_affinity[] initial | E02, E03, J06 |
| A08 OnboardingConfidence | All OB answers, onboarding_sessions completeness | user_re_state (confidence_score) | confidence_score | A09, RE pipeline (confidence signal) |
| A09 AssignPersona | main_cohort_code, sub_cohort_tag, home_state, diet_type, re_persona_assignment_rules | user_re_state (persona_id, overlay_persona_ids[]) | persona_id, overlay_persona_ids[] | B01, B02 |

### Group B — Class Plan Generation

| **Function** | **Data Read** | **Data Written** | **Derived Outputs** | **Downstream Consumers** |
| --- | --- | --- | --- | --- |
| B01 FetchPersona | user_re_state | — | persona_id, overlay_persona_ids[] | B02, C01 |
| B02 GenerateClassPlan | persona_id, home_state, re_cohorts, re_weekly_class_plans, re_class_taxonomy, cook_capability | week_plans (new), plan_slots (21 rows with class_code) | 21 class assignments | D01, C01 |
| B03 NonVegCadence | diet_type, home_state, re_nonveg_logic, plan_slots | plan_slots (updates class_code for non-veg slots) | modified class assignments | D01 |

### Group C — Add-on Generation

| **Function** | **Data Read** | **Data Written** | **Derived Outputs** | **Downstream Consumers** |
| --- | --- | --- | --- | --- |
| C01 GenerateAddons | member_segments[], plan_slots (class_codes), re_segment_addon_rule | plan_slots (addon_slots embedded) | addon_slot records | C02 |
| C02 ResolveAddonDish | addon_class_code, member.allergen_flags, re_addon_dish_options, dishes | plan_slots (addon dish_id) | dish_id per addon | App (display) |

### Group D — Candidate Generation

| **Function** | **Data Read** | **Data Written** | **Derived Outputs** | **Downstream Consumers** |
| --- | --- | --- | --- | --- |
| D01 GetClassCandidates | class_code, re_class_dish_options, dishes (is_active) | — | candidate_dishes[] with base_scores | D02–D07 |
| D02 DietFilter | dishes.diet_type, user.diet_type | — | filtered_candidates[] | D03 |
| D03 AllergenFilter | dish_ingredients, ingredients.allergen_flags, combined_allergen_flags | — | filtered_candidates[] | D04 |
| D04 ReligiousFilter | dishes.is_jain, user.religious_pref | — | filtered_candidates[] | D05 |
| D05 OccasionFilter | dishes.meal_occasion, meal_slot | — | filtered_candidates[] | D06 |
| D06 NeverListFilter | re_engine.never_list (user, is_active=true) | — | filtered_candidates[] | D07 or Layer 4 |
| D07 ConstraintConflict | filtered_candidates count, dishes (popular by diet type) | coverage_gap_log (new row) | fallback_candidates[] | Layer 4 or app fallback state |

### Group E — Scoring

| **Function** | **Data Read** | **Data Written** | **Derived Outputs** | **Downstream Consumers** |
| --- | --- | --- | --- | --- |
| E01 WeightLadder | user_re_state.interaction_count, re_weight_ladder_config | — | {w_cohort, w_content, w_history, w_context, w_explore} tuple | E08 |
| E02 CohortPrior | re_cohort_class_priors (cohort_id, class_code) | — | prior_float 0–1 | E08 |
| E03 ContentMatch | user_taste_vectors.genome_tag_affinity, dishes.genome_vector | — | similarity_float 0–1 | E08 |
| E04 PersonalHistory | interaction_events (user_id, dish_id), re_event_weights config | — | history_float −1 to +1 | E08 |
| E05 ContextFit | context object, dish genome tags, re_context_multipliers config | — | context_fit_float 0–1.2 | E08 |
| E06 ExplorationBonus | re_dish_bandit_state (α, β per user-dish) | — | exploration_float 0–0.15 | E08 |
| E07 PenaltyTerms | not_today_suppression (user, dish, active), re_scoring_config | not_today_suppression (is_active → false if expired) | penalty_float 0–0.80 | E08 |
| E08 FinalScore | E01–E07 outputs | — | score float per dish | F01 |

### Group F — Variety Re-ranking

| **Function** | **Data Read** | **Data Written** | **Derived Outputs** | **Downstream Consumers** |
| --- | --- | --- | --- | --- |
| F01 MMR | E08 scores, dish.genome_vector (similarity), variety_window_state, re_variety_rules | plan_slots (slate_dish_ids[], slate_reasons jsonb) | reranked_slate[] of 8 | H01–H04, suggestion_logs |
| F02 VarietyWindowRules | variety_window_state, re_variety_rules config | — | variety_flags per candidate | F01 |
| F03 EdgeCases | F01 results, user.class_affinity | variety_window_state (adjustment flags) | adjusted candidates | F01 (re-input) |

### Group G — Suppression

| **Function** | **Data Read** | **Data Written** | **Derived Outputs** | **Downstream Consumers** |
| --- | --- | --- | --- | --- |
| G01 NeverGesture | user_id, dish_id, dish.meal_class_code, never_list count | re_engine.never_list (new row), interaction_events, user_taste_vectors.class_affinity | none (side-effect only) | D06 (future requests), G04, L03 |
| G02 NotTodayGesture | user_id, dish_id | not_today_suppression (new/update row), interaction_events | none (side-effect only) | E07 (future scoring), L03 |
| G03 NotTodayPenalty | not_today_suppression (user, dish) | not_today_suppression.is_active (may set false) | penalty float | E07 |
| G04 ClassLevelNever | user_id, class_code, never_list count | user_taste_vectors.class_affinity | updated class_affinity | E02, B02 |
| G05 NeverReactivation | never_list, dishes (seasonal/festival tags), festival_calendar, current date | push_notification_queue (new prompt) | reactivation candidates | User (prompt shown) |

### Group H — Safety Gates

| **Function** | **Data Read** | **Data Written** | **Derived Outputs** | **Downstream Consumers** |
| --- | --- | --- | --- | --- |
| H01 DietGate | suggestion_logs (last hour), dishes.diet_type, profiles.diet_type | safety_gate_log (if violation) | pass/fail | Deployment pipeline |
| H02 AllergenGate | suggestion_logs, dish_ingredients, ingredients.allergen_flags, profiles.allergen_flags, household_members.allergen_flags | safety_gate_log (if violation) | pass/fail | Deployment pipeline |
| H03 JainGate | suggestion_logs, dishes.is_jain, profiles.religious_pref | safety_gate_log (if violation) | pass/fail | Deployment pipeline |
| H04 PlanningRoleGate | plan_slots, re_meal_classes.planning_role | safety_gate_log (if violation) | pass/fail | Deployment pipeline |

### Group I — Context Assembly

| **Function** | **Data Read** | **Data Written** | **Derived Outputs** | **Downstream Consumers** |
| --- | --- | --- | --- | --- |
| I01 AssembleContext | I02-I05 outputs | context_log (append) | context object | E05, J07 |
| I02 WeatherCache | weather_cache (city, date), OpenWeatherMap API | weather_cache (new/update) | temp_c, condition | I03 |
| I03 ClassifyCondition | temp_c, precipitation | — | weather_condition string | I01 |
| I04 DeriveSeason | system date | — | season string | I01 |
| I05 FestivalProximity | festival_calendar, current date | — | festival_proximity object | I01, G05 |

### Group J — Learning Loop

| **Function** | **Data Read** | **Data Written** | **Derived Outputs** | **Downstream Consumers** |
| --- | --- | --- | --- | --- |
| J01 ProcessEvent | API input (event object) | interaction_events (append, synced_to_re=false) | routes to J02-J06, G01, G02 | J02–J06 |
| J02 UpdateCount | user_re_state.interaction_count | user_re_state.interaction_count++ | updated count | J05 (threshold check) |
| J03 GenomeAffinity | dish.genome_tags (Tier 1+2), re_event_weights | user_taste_vectors.genome_tag_affinity | updated affinity | E03 (future ContentMatch) |
| J04 BanditState | user_id, dish_id | re_dish_bandit_state (α or β++) | updated bandit state | E06 (future exploration) |
| J05 ExitColdStart | user_re_state.interaction_count | user_re_state.cold_start_mode=false | state change | E01 (weight ladder), L01 (plan gen) |
| J06 ClassAffinity | class_code, event_type, re_class_affinity_config | user_taste_vectors.class_affinity | updated class affinity | B02, E02 |
| J07 FeatureStore | all events, context object | context_log, suggestion_logs (plan features) | ML feature store rows | Future ML training |
| J08 CohortRecalibrate | suggestion_logs, interaction_events (7 days) | re_cohort_class_priors (conditional update) | updated priors | E02 (future CohortPrior) |
| J09 DishSnapshot | dishes, dish_tags, suggestion_logs | re_engine.dish_features (snapshot row per dish) | ML dish feature history | Future ML training |

### Groups K, L, M — Content, Plan Management, Compliance

| **Function** | **Data Read** | **Data Written** | **Derived Outputs** | **Downstream Consumers** |
| --- | --- | --- | --- | --- |
| K01 DeriveDishAttribs | dish_ingredients, ingredients | dishes (diet_type, is_jain, allergen_flags) | derived dish safety attributes | D02, D03, D04, H01-H03 |
| K02 GenomeVector | dish_tags (Tier 1+2) | dishes.genome_vector | float[] genome vector | E03 (ContentMatch) |
| K03 PopularityScore | suggestion_logs, interaction_events | dishes.popularity_score | daily popularity | D07 (fallback ranking), seed quality |
| K04 Tier1Validate | dish_tags (count by tier, name) | — | pass/fail for dish eligibility | Content ops workflow |
| L01 GenerateWeekPlan | All Layer 2-6 inputs | week_plans, plan_slots (all), suggestion_logs | complete week plan | App (display) |
| L02 RefreshUnlocked | plan_slots (is_locked), week_plans | plan_slots (slate_dish_ids[], slate_reasons — unlocked only) | refreshed slates | App (display) |
| L03 PromoteSlateDish | plan_slots.slate_dish_ids[], exclude list | plan_slots (slate update) | new slate from RE | App (display) |
| L04 OB08bInteractions | plan preview, user interactions | interaction_events (append) | first behavioral signals | J01 routing |
| M01 CaptureConsent | user input, consent categories | consent_records (new rows) | consent granted/denied | All data collection functions |
| M02 DataExport | All user-linked tables | export_queue | packaged user data | User delivery |
| M03 DataDeletion | All user-linked tables | All (DELETE rows), audit_log (retained) | deletion confirmation | User confirmation |

## Section 03 — Configuration Classification

Every numeric parameter, threshold, weight, and limit classified by how it should be managed.

**Classifications:**

- **CONFIG_TABLE:** Stored in a seed/config table. Readable at runtime. Changeable without code deploy.

- **RUNTIME_CALC:** Computed at request time from other values. Never stored.

- **HARDCODED:** Fixed constant. Changes require code deploy. Used only for values that must never change post-launch.

- **FEATURE_FLAG:** Controlled by a feature flag. Can be toggled per user or globally.

- **PERSISTED_USER:** Stored per-user. Changes as user behaviour evolves.

| **Parameter** | **Value** | **Classification** | **Table / Location** | **Rationale** |
| --- | --- | --- | --- | --- |
| **Weight ladder tier boundaries** | 0, 10, 50, 150 | CONFIG_TABLE | re_weight_ladder_config | Must be tunable after launch based on actual learning curves |
| **Tier 0 weights** (w_cohort=0.55, etc.) | See P3-03 §16 | CONFIG_TABLE | re_weight_ladder_config | Will be tuned post-launch |
| **Tier 4 weights** | See P3-03 §16 | CONFIG_TABLE | re_weight_ladder_config | Will be tuned post-launch |
| **Cold start exit threshold** | 14 interactions | CONFIG_TABLE | re_weight_ladder_config | May differ by cohort in Phase 2 |
| **Not Today P0** | 0.80 | CONFIG_TABLE | re_scoring_config | May be reduced if users find it too aggressive |
| **Not Today λ** | 0.35 | CONFIG_TABLE | re_scoring_config | Decay rate tunable |
| **Not Today expiry** | 7 days | CONFIG_TABLE | re_scoring_config | Tunable |
| **PersonalHistory λ_history** | 0.05 | CONFIG_TABLE | re_scoring_config | Slow decay; tuneable |
| **MMR λ MVP** | 0.70 | CONFIG_TABLE | re_scoring_config | Will shift to 0.55 in Phase 1 |
| **MMR λ Phase 1+** | 0.55 | CONFIG_TABLE | re_scoring_config | Feature-flagged to Phase 1 |
| **Exploration bonus max** | 0.15 | CONFIG_TABLE | re_scoring_config | Tunable |
| **Bandit explore pct** | ~10% (1 of 8) | CONFIG_TABLE | re_scoring_config | Tunable |
| **Event weight: dish_cooked** | +0.80 | CONFIG_TABLE | re_event_weights | Critical to tune from live data |
| **Event weight: dish_locked** | +0.60 | CONFIG_TABLE | re_event_weights | Tunable |
| **Event weight: dish_accepted** | +0.40 | CONFIG_TABLE | re_event_weights | Tunable |
| **Event weight: dish_swiped_past** | −0.10 | CONFIG_TABLE | re_event_weights | Tunable |
| **Event weight: dish_not_today** | −0.10 | CONFIG_TABLE | re_event_weights | Tunable |
| **Event weight: rated 5★** | +0.60 | CONFIG_TABLE | re_event_weights | Tunable |
| **Event weight: rated 1★** | −0.30 | CONFIG_TABLE | re_event_weights | Tunable |
| **OB-07 YES delta** | +0.30 | CONFIG_TABLE | re_class_affinity_config | Tunable |
| **OB-07 NOPE delta** | −0.30 | CONFIG_TABLE | re_class_affinity_config | Tunable |
| **Class Never trigger count** | 3 | CONFIG_TABLE | re_class_affinity_config | Tunable |
| **Class Never delta** | −0.15 | CONFIG_TABLE | re_class_affinity_config | Tunable |
| **Confidence contributions** | See P3-03 §16 | CONFIG_TABLE | re_confidence_config | Will recalibrate after measuring Day-0 quality |
| **City overlay weights** | See P3-03 §16 | CONFIG_TABLE | re_city_overlay_config | Research-derived; rarely change |
| **Variety window rules** | See P3-03 §16 | CONFIG_TABLE | re_variety_rules | Must be tunable for edge case handling |
| **Context multipliers** | 0.80–1.20 range | CONFIG_TABLE | re_context_multipliers | Seed data, tunable by content ops |
| **Weather TTL** | 12 hours | CONFIG_TABLE | re_scoring_config | May reduce to 6h if weather variability is high |
| **Never reactivation: seasonal** | 6 months | CONFIG_TABLE | re_scoring_config | Tunable |
| **Never reactivation: festival** | 90 days | CONFIG_TABLE | re_scoring_config | Tunable |
| **Festival pre-boost window** | 21 days | CONFIG_TABLE | re_festival_calendar | Per festival, tunable |
| **Current weights per user** | Interpolated from interaction_count | RUNTIME_CALC | Computed at request time | Must not be stored — always reflects current state |
| **FinalScore** | Σ of all signals | RUNTIME_CALC | Computed per dish per request | Never stored |
| **ContentMatch** | Cosine similarity | RUNTIME_CALC | Computed at request time | Never stored |
| **PersonalHistory** | Σ event × decay | RUNTIME_CALC | Computed at request time | Never stored |
| **ContextFit** | Σ multipliers | RUNTIME_CALC | Computed at request time | Never stored |
| **Not Today penalty** | P0 × e^(-λt) | RUNTIME_CALC | Computed at request time | Never stored (t is dynamic) |
| **MMR scores** | Diversity-relevance balance | RUNTIME_CALC | Computed during slate building | Never stored |
| **Combined allergen flags** | UNION of user + members | RUNTIME_CALC | Computed at candidate generation | Never stored independently |
| **Season** | Derived from month | RUNTIME_CALC | Computed per request | Stored in context_log for ML |
| **City overlay weight** | Derived from migration_duration | RUNTIME_CALC (initially), then PERSISTED | profiles / user_re_state | Computed once at onboarding, stored |
| **Interaction count** | Incremented on events | PERSISTED_USER | user_re_state | Stored; drives weight ladder |
| **Cold start mode** | Derived from count | PERSISTED_USER | user_re_state | Stored boolean |
| **Genome tag affinity** | Updated by events | PERSISTED_USER | user_taste_vectors | Stored, evolves continuously |
| **Class affinity** | Updated by OB-07 and class Nevers | PERSISTED_USER | user_taste_vectors | Stored, evolves |
| **Bandit α, β** | Updated by events | PERSISTED_USER | re_dish_bandit_state | Stored per user-dish pair |
| **Confidence score** | Computed + grows | PERSISTED_USER | user_re_state | Stored, updated as interactions grow |
| **Persona_id** | Assigned once | PERSISTED_USER | user_re_state | Stored after onboarding |
| **API version (v1/v2)** | Current RE version | FEATURE_FLAG | re_engine_versions | Toggles between classfirst_v1 and ltr_v1 etc. |
| **Shadow mode** | New RE version testing | FEATURE_FLAG | re_engine_versions | Toggles shadow mode for specific % of traffic |
| **Festival boost** | Phase 2 only | FEATURE_FLAG | feature_flags table | Disabled in MVP |
| **Mood selector** | Phase 1 only | FEATURE_FLAG | feature_flags table | Disabled in MVP |
| **n_results** | 8 dishes per slate | HARDCODED | RE API contract | Changing this requires API version increment |
| **Number of safety gate retries** | 2 | HARDCODED | Edge Function code | Changing requires code review |
| **Tier-1 genome tag confidence floor** | 0.85 | HARDCODED | Content validation | Should not change without content ops workflow redesign |

## Section 04 — Complete Traceability Matrix

For every function: source documents, CDM entities, invariants enforced, and business events triggered/consumed.

| **Function** | **Source Document(s)** | **CDM Entities** | **CDM Invariants** | **Events (Triggered / Consumed)** |
| --- | --- | --- | --- | --- |
| A01 CohortSelection | DOC-04 F-01, DOC-05 OB-01 | Main Cohort (9), Onboarding Session (28) | None | Consumed: None. Triggered: OnboardingStarted, MainCohortSelected |
| A02 HouseholdBranch | DOC-04 F-02, DOC-05 OB-02, DOC-03 sub-cohorts | Sub-cohort (10), Household Members (3) | None at this stage | Triggered: HouseholdMembersCapture |
| A03 RegionalIdentity | DOC-05 OB-03, DOC-06 C-11 | Regional Identity (4), User (1) | Invariant 7 (overlay weights sum to 1.0) | Triggered: RegionalIdentityCaptured |
| A04 DietConfig | DOC-05 OB-04 | Diet Type (5), Religious Preference (6) | Invariant 1 (diet safety), Invariant 2 (Jain safety) | Triggered: DietConfigured |
| A05 Allergens | DOC-05 OB-05, RE-DOC-02 §03 | Allergen (7), Ingredient (18), User (1), Members (3) | Invariant 3 (allergen safety), Invariant 4 (member propagation) | Triggered: AllergensConfigured |
| A06 CookCapability | DOC-05 OB-06 | Cook Capability (8), User (1) | None | Triggered: CookCapabilitySelected |
| A07 ClassPrefSwipes | DOC-06 C-07, DOC-04 F-07 | Class Preference Swipe (33), Interaction Events (29), Taste Vector (42) | None | Triggered: ClassPreferenceSwiped (×10 max) |
| A08 OnboardingConfidence | RE-DOC-04 §01 | Confidence Score (13) | None | None directly |
| A09 AssignPersona | DOC-04 Step 2, RE-DOC-01 §03 | Persona (11), Overlay (12) | Invariant 13 (persona from valid 41) | Triggered: PersonaAssigned |
| L04 OB08bInteractions | DOC-05 OB-08b | Interaction Events (29) | All (same as post-onboarding) | Triggered: PlanPreviewInteracted, then OnboardingCompleted |
| B01 FetchPersona | RE-DOC-01 §03 (corrected) | Persona (11) | None | None |
| B02 GenerateClassPlan | DOC-04 Step 3, RE-DOC-03 §01, DOC-10 §05 | Meal Class (20), Week Plan (23), Plan Slot (24) | Invariant 5 (planning role), Invariant 11 (one plan per week) | Triggered: WeekPlanGenerated, PlanSlotGenerated |
| B03 NonVegCadence | RE-DOC-03 §05 (amendment) | Diet Type (5), Meal Class (20) | Invariant 1 | None |
| C01 GenerateAddons | DOC-04 Step 4, RE-DOC-02 §04 | Add-on Slot (26), Members (3), Meal Class (20) | Invariant 9 (add-on never replaces primary) | Triggered: AddOnSlotsGenerated |
| C02 ResolveAddonDish | RE-DOC-02 §04 | Add-on Slot (26), Dish (15) | Invariants 1-4 (all hard constraints apply to add-ons too) | None |
| D01 GetCandidates | RE-DOC-03 §01 | Class-Dish Option (21), Dish (15) | None | None |
| D02 DietFilter | RE-DOC-03 §03 HC1, CDM Inv 1 | Diet Type (5), Dish (15) | **Invariant 1** | None — filtering only |
| D03 AllergenFilter | RE-DOC-03 §03 HC2, RE-DOC-02 §03 | Allergen (7), Ingredient (18), Dish (15) | **Invariant 3, 4** | None — filtering only |
| D04 ReligiousFilter | RE-DOC-03 §03 HC3, CDM Inv 2 | Religious Pref (6), Dish (15) | **Invariant 2** | None |
| D05 OccasionFilter | RE-DOC-03 §03 HC4 | Meal Occasion (22), Dish (15) | None | None |
| D06 NeverListFilter | RE-DOC-03 §03 HC6, RE-DOC-04 §03 | Never List (30), Dish (15) | **Invariant 10** | None |
| D07 ConstraintConflict | RE-DOC-01 §05, DOC-10 Stage 5 failure | Plan Slot (24), Safety Gate (48) | None | Triggered: SafetyGateViolation (if needed) |
| E01 WeightLadder | RE-DOC-03 §02, RE-DOC-05 §01 | Weight Ladder (41) | None | None |
| E02 CohortPrior | RE-DOC-03 §02 | Scoring Signal CohortPrior (35) | None | None |
| E03 ContentMatch | RE-DOC-03 §02 | ContentMatch (36), Taste Vector (42) | None | None |
| E04 PersonalHistory | RE-DOC-03 §02, RE-DOC-04 §03 | PersonalHistory (37), Interaction Events (29) | None | None |
| E05 ContextFit | RE-DOC-03 §02, RE-DOC-02 §05 | ContextFit (38), Context (43), Weather (44) | None | None |
| E06 ExplorationBonus | RE-DOC-03 §02, RE-DOC-05 §01 | ExplorationBonus (39) | None | None |
| E07 PenaltyTerms | RE-DOC-04 §03 | Penalty Terms (40), Not Today Suppression (31) | None | Triggered: NotTodayExpired (state change) |
| E08 FinalScore | RE-DOC-03 §02 | FinalScore (34) | **Invariant 12** (hard constraints must have run first) | None |
| F01 MMR | RE-DOC-04 §02 | Slate (25), Variety Window State (32) | None | None |
| F02 VarietyRules | RE-DOC-04 §02 | Variety Window State (32) | None | None |
| F03 EdgeCases | RE-DOC-04 §02 | Variety Window State (32) | None | None |
| G01 NeverGesture | RE-DOC-04 §03, DOC-05 Flow 3b | Never List (30), Class Affinity (46), Interaction Events (29) | **Invariant 10** | Triggered: NeverApplied |
| G02 NotTodayGesture | RE-DOC-04 §03, DOC-05 Flow 3a | Not Today Suppression (31), Interaction Events (29) | None | Triggered: NotTodayApplied |
| G03 NotTodayPenalty | RE-DOC-04 §03 | Not Today Suppression (31) | None | Triggered: NotTodayExpired (when penalty < 0.05) |
| G04 ClassNeverSignal | RE-DOC-04 §03 | Class Affinity (46), Never List (30) | None | None |
| G05 NeverReactivation | RE-DOC-04 §03 | Never List (30), Festival (47) | **Invariant 10** (user must confirm, not automatic) | Triggered: NeverReactivationPrompted |
| H01 DietGate | RE-DOC-05 §04 Q1, RE-DOC-03 §03 | Safety Gate (48) | **Invariant 1** | Triggered: SafetyGateViolation (if fail) |
| H02 AllergenGate | RE-DOC-05 §04 Q2, CDM Inv 3 | Safety Gate (48) | **Invariant 3, 4** | Triggered: SafetyGateViolation (if fail) |
| H03 JainGate | RE-DOC-05 §04 Q3 | Safety Gate (48) | **Invariant 2** | Triggered: SafetyGateViolation (if fail) |
| H04 PlanningRoleGate | CDM Inv 5 | Safety Gate (48) | **Invariant 5** | Triggered: SafetyGateViolation (if fail) |
| H01-H04 (all) | — | Safety Gate (48) | **Invariant 14** (all 4 must pass) | SeedGatesValidated prerequisite |
| I01–I05 Context | RE-DOC-02 §05, RE-DOC-01 §03 | Context (43), Weather (44), Season (45), Festival (47), Weather Cache (46) | None | Triggered: WeatherCacheMiss (I02) |
| J01 ProcessEvent | DOC-10 §05, RE-DOC-05 §02 | Interaction Events (29) | None | Consumes: all user interaction events |
| J02–J06 Learning | RE-DOC-03 §02, RE-DOC-04, RE-DOC-05 | Taste Vector (42), Class Affinity (46), Bandit State, Cold Start (14) | None | Triggered: TasteVectorUpdated, ClassAffinityUpdated, ColdStartExited |
| K01 DeriveDishAttribs | CDM Inv 6, RE-DOC-02 §03 | Dish (15), Ingredient (18) | **Invariant 6** | Triggered: DishDerivationRun |
| K02–K04 Content | RE-DOC-02 §02 | Dish (15), Food DNA (16) | None | None |
| L01–L04 PlanMgmt | DOC-10 §05, DOC-05 | Week Plan (23), Plan Slot (24), Slate (25) | **Invariant 11** (one plan per week) | Triggered: WeekPlanGenerated, PlanRefreshed, SlotRefreshed |
| M01–M03 Compliance | DOC-09 §03 | Consent Records (51) | None | Triggered: ConsentGranted, DataExportRequested, AccountDeletionRequested |

## Section 05 — Assumptions and Product Decision Register

All unresolved items consolidated. No hidden decisions in any document.

| **#** | **Description** | **Impact** | **Affected Functions** | **Owner** | **Recommended Resolution** | **Implementation Blocker?** |
| --- | --- | --- | --- | --- | --- | --- |
| **D-001** | Context override threshold in Not Today penalty (ContextFit > ? → penalty ×0.50) | Minor scoring behaviour — determines when a decayed Not Today dish can re-surface contextually | E07 computePenaltyTerms | Product | Suggest 0.90 as threshold. Set in re_scoring_config. | **No** — can default to 0.90 at launch |
| **D-002** | Cohort weight recalibration algorithm (Sunday CRON) — comparison logic and update formula undefined | Weekly CRON produces no effect until algorithm is defined | J08 CohortRecalibrate | Product + Data Science | Can be a no-op at launch. Define after 30 days of live data is available. Suggested approach: if actual_acceptance_rate for (cohort, class) differs from prior by > 15% over 7 days → update prior by 20% of the difference. | **No** — CRON can be no-op for MVP |
| **D-003** | "Still learning your taste" UI surface — RE-DOC-01 defines the trigger (confidence < 0.30) but no UI component exists in DOC-05/06 | UX gap — message trigger is specified, display surface is not | J05 ExitColdStart signal | Product + UX | Add a badge or subtitle to the H-01 Day View header when confidence < 0.30. Needs DOC-05/06 update. | **No** — can be added post-launch as a UX polish item |
| **D-004** | Genre vector format for dish.genome_vector — pre-computed float[] vs assembled at query time | Affects ContentMatch query performance and storage design | E03 ContentMatch, K02 | Architecture | Pre-computed float[] stored on dish. Recomputed on dish_tags UPDATE trigger. Enables O(1) cosine similarity at scoring time. | **Yes** — P3-04 must decide table column type before schema is written |
| **D-005** | PersonalHistory computation strategy — compute from full event log vs pre-aggregated in Taste Vector | Affects query performance at >10K events per user | E04 PersonalHistory | Architecture | At MVP: compute from interaction_events at query time (low event counts). At Phase 1: pre-aggregate into taste_vector.recent_events_summary when user exceeds 500 events. | **No** — full event scan acceptable at MVP scale |
| **D-006** | Anti-filter-bubble cuisine diversity counter — how to track cuisine family count over 30 days | Requires a rolling window of accepted dish cuisine families | RE-DOC-05 §01 State D anti-filter-bubble, J03 | Architecture | Log cuisine_family on each accepted dish in interaction_events. Compute count in rolling 30-day window at weekly batch. Not needed for MVP (State D feature). | **No** — State D feature |
| **D-007** | OB-07 dish pool is fixed (10 cards) but should non-veg dishes only show for non-veg users — filtering rule at OB-07 | Jain/veg users should not see Chicken Biryani card | A07 ClassPrefSwipes | Product | Filter OB-07 dish pool by user.diet_type before rendering. Non-veg card shown only if diet_type = non_veg or egg. This is a content rule not a business logic gap. | **No** — content/UX rule, no logic change |
| **D-008** | Dish popularity score calculation — weight of 7-day vs 30-day acceptance rate (proposed 0.60/0.40) | Affects fallback ranking in D07 and feature store quality | K03 PopularityScore | Data Science | Start with 0.60 × 7d + 0.40 × 30d. Review after 60 days of live data. Stored in config. | **No** — can use proposed values at launch |
| **D-009** | Variety score metric computation — exactly how "average pairwise genome dissimilarity" is calculated for reporting | Affects RE-DOC-05 §04 variety score metric | RE-DOC-05 §04 | Analytics | Pairwise cosine distance between all dish pairs in 7-day plan using 4 variety-relevant genome dimensions (cuisine, method, ingredient, texture). Average of all pairs. | **No** — analytics metric, not blocking |
| **D-010** | RE version promotion automation — is promotion from shadow to production automatic or manual approval? | Deployment safety | RE-DOC-01 §04 shadow mode | Founder | Manual approval at MVP scale. One-founder org — automated promotion adds risk. Review promotion dashboard, manually approve each version upgrade. | **No** — operational decision |

## Section 06 — Data Lineage

End-to-end information flow showing how every derived value has a clearly understood origin.

### Primary Data Lineage

USER INPUT (OB-01 through OB-07)

    │

    ├── main_cohort_code [OB-01 tap]

    │       ↓

    │   sub_cohort_tag [OB-02 answers + branching]

    │       ↓

    │   persona_id [DB lookup: cohort × subcohort × state × diet → re_persona_assignment_rules]

    │       ↓

    │   class_plan [DB lookup: persona × state × day → re_weekly_class_plans]

    │       ↓

    │   addon_classes [DB lookup: member_segment × class → re_segment_addon_rule]

    │

    ├── home_state + current_city + migration_duration [OB-03 selections]

    │       ↓

    │   city_overlay_weight [lookup: migration_band → re_city_overlay_config]

    │       ↓ (applied in scoring via regional affinity on dish genome)

    │   regional_affinity adjustment in ContextFit or ContentMatch

    │

    ├── diet_type + religious_pref [OB-04]

    │       ↓

    │   Hard constraint filters D02, D04 [applied every recommendation]

    │       ↓

    │   Permanently shapes candidate pool

    │

    ├── allergen_flags [OB-05 — propagated from user + all members]

    │       ↓

    │   Hard constraint filter D03 [ingredient-level check every recommendation]

    │

    ├── cook_capability [OB-06]

    │       ↓

    │   Class plan bias (beginner → simpler classes)

    │       ↓

    │   Dish difficulty filter (beginner → no advanced dishes)

    │

    └── OB-07 class preference swipes

            ↓

        class_affinity[class_code] initial values [stored in user_taste_vectors]

            ↓

        CohortPrior weighting adjustment in class plan generation

CONTEXT (assembled per recommendation request)

    │

    ├── weather_condition [OpenWeatherMap API → classified → cached 12h]

    ├── season [derived from system month]

    ├── day_of_week + is_weekend [system date]

    └── festival_proximity [festival_calendar table lookup]

            ↓

        ContextFit score [re_context_multipliers × dish genome tags]

            ↓

        Applied to FinalScore (weight: w_context=0.15 stable across all tiers)

PERSONA → CLASS PLAN → CANDIDATES → SCORING → SLATE

    │

    ▼

Cohort Prior [re_cohort_class_priors lookup: (cohort, class) → acceptance_rate]

    ↓ (0–1 float, weighted by w_cohort=0.55 at Day 0)

    ↓

Content Match [CosineSim(user_taste_vector, dish.genome_vector)]

    ↓ (0–1 float, weighted by w_content=0.20)

    ↓

Personal History [Σ event_weight × e^(-0.05×t) over interaction_events for this dish]

    ↓ (−1 to +1, weighted by w_history=0.00→0.65 growing with time)

    ↓

Context Fit [Σ multipliers across weather/season/day tags]

    ↓ (0–1.2, weighted by w_context=0.15 stable)

    ↓

Exploration Bonus [Thompson Sampling Beta(α,β)]

    ↓ (0–0.15, weighted by w_explore=0.10→0.00 declining)

    ↓

Penalty Terms [P0×e^(-λt) if Not Today active]

    ↓ (0–0.80 deducted)

    ↓

FinalScore [assembled] → MMR re-ranking → Slate of 8 dishes

    ↓

Shown to user as suggestion_logs (append)

USER INTERACTION (post-slate)

    ↓

interaction_events (append-only)

    ↓ [async, 15-min batch]

    ├── genome_tag_affinity updated [for accepted/rejected dishes]

    │       ↓

    │   ContentMatch changes for future requests (feedback loop)

    │

    ├── class_affinity updated [for class-level Never signals or OB-07]

    │       ↓

    │   Class plan weighting shifts for future weeks (feedback loop)

    │

    ├── bandit state (α, β) updated

    │       ↓

    │   ExplorationBonus shifts per dish (feedback loop)

    │

    └── interaction_count incremented

            ↓

        Weight ladder interpolates (w_history rises, w_cohort falls)

            ↓

        Plans become more personalised over time (meta feedback loop)

### Derived Value Lineage Summary

| **Derived Value** | **Origin** | **Updated by** | **Consumed by** |
| --- | --- | --- | --- |
| city_overlay_weight | migration_duration_band → re_city_overlay_config | Once at OB-03, on profile update | ContentMatch (regional tags), ContextFit |
| dish.diet_type | Ingredients (is_veg, is_vegan) → derivation trigger | K01 on ingredient change | D02, H01 |
| dish.is_jain | Ingredients (is_jain_excluded) → derivation trigger | K01 on ingredient change | D04, H03 |
| dish.allergen_flags | Ingredients (allergen_flags UNION) → derivation trigger | K01 on ingredient change | D03, H02 |
| dish.genome_vector | dish_tags (Tier 1+2) → K02 | K02 on tag change | E03 ContentMatch |
| persona_id | (cohort × subcohort × state × diet) → re_persona_assignment_rules | A09 once at onboarding | B01, B02 |
| class_plan | persona × state × day → re_weekly_class_plans | B02 per week | D01 |
| confidence_score | Onboarding completeness signals → A08 | A08 at end of OB; grows with interaction_count | RE pipeline (display signal) |
| cold_start_mode | interaction_count ≥ 14 → J05 | J02 on each event; J05 on threshold | E01 weight ladder |
| genome_tag_affinity | interaction_events → J03 (async) | J03 every 15 min | E03 ContentMatch |
| class_affinity | OB-07 → A07; class Never → G04 | A07 at OB, J06 ongoing | B02 class plan, E02 CohortPrior |
| FinalScore | E01–E07 assembled by E08 | Per request | F01 MMR |
| slate (8 dishes) | F01 MMR output | Per request or refresh | User display, suggestion_logs |
| reason_tags | Dominant scoring signal per dish at slate generation | With each slate | Stored in plan_slots.slate_reasons, shown in carousel |
| popularity_score | Acceptance events / shown events → K03 | K03 daily CRON | D07 fallback ranking |

## Section 07 — Execution Classification

For every logical function: how it executes in production.

| **Function** | **Execution Type** | **Trigger** | **Latency Target** | **Notes** |
| --- | --- | --- | --- | --- |
| A01–A07 Onboarding steps | **Synchronous** | User screen tap | < 200ms per step | User waits for each response |
| A08 OnboardingConfidence | **Synchronous** | End of onboarding | < 50ms | Pure computation, no DB write except final |
| A09 AssignPersona | **Synchronous** | End of onboarding | < 200ms | Single DB lookup + write |
| L04 OB08bInteractions | **Synchronous** | User gesture on OB-08b | < 100ms | Same as post-onboarding events |
| B01 FetchPersona | **Synchronous** | Start of recommendation pipeline | < 50ms | Single row read |
| B02 GenerateClassPlan | **Synchronous** | Week plan generation | < 300ms | DB query on 20,664-row seed table |
| B03 NonVegCadence | **Synchronous** | After B02 | < 50ms | Small lookup |
| C01 GenerateAddons | **Synchronous** | After B02/B03 | < 100ms | Per member, per slot |
| C02 ResolveAddonDish | **Synchronous** | After C01 | < 100ms | Per addon slot |
| D01–D07 Candidate generation | **Synchronous** | Per slot in pipeline | < 200ms total for all filters | D01-D06 sequential, fast filters |
| E01–E08 Scoring | **Synchronous** | After D-group | < 200ms per slot | E02-E07 parallelisable within slot |
| F01–F03 MMR | **Synchronous** | After E-group | < 100ms | O(n²) over 8 candidates — fast |
| H01–H04 Safety gates | **Synchronous (blocking)** | After F-group, after any RE deploy | < 100ms per gate | Must block — no slate served if gates fail |
| I01–I05 Context assembly | **Synchronous** | Parallel with Layer 2 start | < 500ms (includes possible API call) | I02 may call external API — must complete before scoring |
| J01 processInteractionEvent | **Synchronous (log only)** | User action via API | < 100ms | Logs to DB, sets synced_to_re=false. User sees instant response. |
| J02–J06 Learning updates | **Asynchronous (batch)** | CRON every 15 min | Batch: < 5min for all pending | Reads unsynced events, processes, sets synced_to_re=true |
| J05 ExitColdStart | **Asynchronous** | Within J02 batch | Next batch run | State change propagates to next recommendation |
| J07 FeatureStore logging | **Synchronous (inline with J01)** | Every recommendation request | < 50ms | Appends to context_log, suggestion_logs |
| J08 CohortRecalibrate | **Scheduled CRON** | Sunday 18:00 UTC | Batch: < 30min | Weekly background job |
| J09 DishSnapshot | **Scheduled CRON** | Daily 00:00 UTC | Batch: < 10min | Daily background job per active dish |
| G01 NeverGesture | **Synchronous (immediate)** | User confirms Never | < 200ms | Writes to never_list + triggers slot refresh |
| G02 NotTodayGesture | **Synchronous (immediate)** | User confirms Not Today | < 200ms | Writes suppression + triggers slot refresh |
| G03 NotTodayPenalty | **Synchronous** | Per scoring request | < 10ms | Simple formula on stored values |
| G04 ClassNeverSignal | **Asynchronous (inline with G01 batch)** | Within J02 batch after Never processed | < 5min | Class affinity update is not urgent |
| G05 NeverReactivation | **Scheduled CRON** | Weekly (Sunday 18:00 UTC) | Batch: < 15min | Queues prompts — not urgent |
| K01 DeriveDishAttribs | **Event-driven trigger** | After dish_ingredients INSERT/UPDATE | < 500ms per dish | Database trigger |
| K02 UpdateGenomeVector | **Event-driven trigger** | After dish_tags INSERT/UPDATE | < 200ms per dish | Database trigger |
| K03 PopularityScore | **Scheduled CRON (via J09)** | Daily 00:00 UTC | Within J09 batch |  |
| K04 Tier1Validate | **One-time (content ops)** | Before dish added to re_class_dish_options | Manual | Content ops workflow gate |
| L01 GenerateWeekPlan | **Scheduled CRON** | 23:30 UTC daily | < 3min for all active users | Pre-generates plans before morning |
| L02 RefreshUnlocked | **Synchronous (on-demand)** | User pulls to refresh | < 3s | User waits for fresh slates |
| L03 PromoteSlateDish | **Synchronous** | User Never/Not Today | < 3s | Triggers new recommendation API call |
| M01 CaptureConsent | **Synchronous** | Signup | < 200ms | Blocking — no onboarding without consent |
| M02 DataExport | **Asynchronous (queued)** | User request | < 72h | DPDP legal requirement |
| M03 DataDeletion | **Asynchronous (queued)** | User request | < 72h | DPDP legal requirement |
| H01–H04 (RE deploy) | **Synchronous (blocking deployment)** | Before any RE deploy | < 5min | Blocks deployment pipeline |

## Section 08 — Auditability

How every recommendation can be fully reconstructed after the fact. Answers: why was this dish shown? What signals contributed? Which config values were used?

### What is logged per recommendation request

Every slate generation writes to the following append-only stores:

**suggestion_logs** (one row per dish shown):

- slate_id (groups all 8 dishes in one request)

- profile_id, dish_id

- meal_slot, slot_date

- rank_in_slate (1–8)

- class_code (which class was assigned to this slot)

- re_version (classfirst_v1 etc.)

- confidence_at_suggestion

- cold_start_mode (was the user in cold start at this moment)

- n_candidates_before_filter (how many dishes were in the class before hard constraints)

- context_snapshot (weather, season, day, festival proximity at generation time)

- slate_reasons (jsonb: {dish_id: reason_tags[]})

**context_log** (one row per request):

- slate_id

- weather_condition, temp_c, city

- day_of_week, is_weekend

- season, time_of_day

- festival_proximity

- re_version

**user_re_state** (snapshot of user state at that moment):

- persona_id

- interaction_count (can infer weight ladder tier)

- cold_start_mode

- re_engine_version

### Reconstruction query: Why was dish X ranked #1 for user Y on date Z?

-- Step 1: Find the slate

SELECT sl.slate_id, sl.class_code, sl.confidence_at_suggestion, 

       sl.cold_start_mode, sl.n_candidates_before_filter,

       sl.context_snapshot, sl.re_version, sl.slate_reasons

FROM suggestion_logs sl

WHERE sl.profile_id = :user_id 

  AND sl.dish_id = :dish_id 

  AND sl.slot_date = :date

  AND sl.rank_in_slate = 1;

-- Step 2: Get context at that time

SELECT * FROM context_log WHERE slate_id = :slate_id;

-- Step 3: Get user state at that time (interaction_count drives weight tier)

-- (approximated from interaction_events count up to that date)

SELECT COUNT(*) FROM interaction_events 

WHERE profile_id = :user_id AND occurred_at <= :date;

-- Step 4: Get reason tags (stored at generation)

-- Already in suggestion_logs.slate_reasons: {dish_id: ["regional","weather"]}

-- Step 5: Get config that was active (re_version → config snapshot)

-- Config tables are not versioned at MVP — this is a known limitation

-- Future: version re_scoring_config rows by re_version

### Auditability of each recommendation dimension

| **Dimension** | **Reconstructable?** | **Source** |
| --- | --- | --- |
| Which class was assigned | ✅ Yes | plan_slots.class_code |
| Which RE version ran | ✅ Yes | suggestion_logs.re_version |
| Was cold start active | ✅ Yes | suggestion_logs.cold_start_mode |
| How many candidates before filtering | ✅ Yes | suggestion_logs.n_candidates_before_filter |
| What context signals were active | ✅ Yes | context_log per slate_id |
| Why this dish — reason tags | ✅ Yes | suggestion_logs.slate_reasons |
| User's interaction count at time | ✅ Approximated | COUNT(interaction_events) up to date |
| Weight ladder weights at time | ✅ Computed | interaction_count → interpolation formula |
| Exact FinalScore per signal | ❌ Not logged at MVP | FinalScore is a transient computation, not stored |
| Which config values were used | ⚠️ Partial | Config tables not versioned at MVP. Known limitation. |
| Which dishes were in candidate pool | ❌ Not logged | Only n_candidates_before_filter is logged |

**Known auditability limitation:** At MVP, individual signal contributions (CohortPrior=0.31, ContentMatch=0.24 etc.) are not stored. Only the final ranked slate, reason tags, and context are available. Full signal-level audit requires a re_recommendation_debug_log table (5% sampled, 30-day retention). This is a Phase 1 enhancement.

### Reconstructing a safety gate violation

-- Find which dishes were shown that violated safety

SELECT sl.profile_id, sl.dish_id, sl.slate_id, sl.slot_date,

       d.diet_type, p.diet_type as user_diet

FROM suggestion_logs sl

JOIN dishes d ON d.id = sl.dish_id

JOIN profiles p ON p.id = sl.profile_id

WHERE d.diet_type NOT IN ('veg','vegan','jain')

  AND p.diet_type = 'veg'

  AND sl.created_at > NOW() - INTERVAL '24 hours';

-- Immediately identifies: which user, which dish, when it was shown, and both diet types

## Section 09 — Logic Validation Matrix

For every logical function group: expected behaviour, failure behaviour, boundary conditions, edge cases, and success criteria. This is a validation framework, not a QA test plan.

### Onboarding Pipeline Validation

| **Function** | **Expected behaviour** | **Failure behaviour** | **Boundary condition** | **Edge case** | **Success criteria** |
| --- | --- | --- | --- | --- | --- |
| A01 CohortSelection | One of 5 options selected and stored | No selection: MC_SOLO default, confidence −0.05 | User taps each option in sequence | User changes selection before proceeding | Correct main_cohort_code stored. Never null. |
| A02 HouseholdBranch | Correct dynamic questions shown for selected cohort | Questions displayed for wrong cohort | MC_COUPLE: no child questions shown | User selects MC_NUCLEAR_FAMILY then goes back and selects MC_SOLO | Sub_cohort_tag always matches main_cohort_code. Household members created only when declared. |
| A03 RegionalIdentity | city_overlay_weight derived correctly from migration band | Home state skipped: current city as proxy, LOW confidence | User selects same state as current city → native flag | User in union territory | city_overlay_weight always in {0.00, 0.15, 0.30, 0.50, 0.70}. Never null. Sum with home_weight = 1.0. |
| A08 OnboardingConfidence | Confidence between 0.35 and 0.65 | All skipped: exactly 0.35 | Perfect completion: exactly 0.65 | User answers diet type but skips all else | confidence_score never below 0.35, never above 0.65 at Day 0 completion. |
| A09 AssignPersona | Valid persona_id from re_personas table | No match: Option B fallback → generic cohort plan, confidence=0.35 | Jain user: religious_pref overrides diet_type constraint | User with rare combination (PG + Jain + Northeast India) | persona_id always references a valid row in re_personas. Never null. |

### Class Plan Generation Validation

| **Function** | **Expected behaviour** | **Failure behaviour** | **Boundary condition** | **Edge case** | **Success criteria** |
| --- | --- | --- | --- | --- | --- |
| B02 GenerateClassPlan | 21 distinct class assignments, all MAIN_PRIMARY | DB read fails: generic cohort fallback | 7 days × 3 slots = exactly 21 | User changes home_state post-onboarding | All 21 class_codes reference valid re_meal_classes rows. All have planning_role=MAIN_PRIMARY. |
| B03 NonVegCadence | Non-veg slots within state-specified weekly count | Veg user: zero non-veg classes regardless | Bengali household: up to 5 non-veg slots/week | Diet type changed from veg to non-veg post-onboarding | No non-veg class appears for veg/jain/vegan households. Count matches re_nonveg_logic for state. |

### Candidate Generation Validation

| **Function** | **Expected behaviour** | **Failure behaviour** | **Boundary condition** | **Edge case** | **Success criteria** |
| --- | --- | --- | --- | --- | --- |
| D02 DietFilter | Zero non-veg dishes for veg household | Wrong diet_type on dish (not yet derived) | diet_type=jain: only is_jain=true dishes pass | Household with egg diet: sees egg dishes but not full non-veg | Safety Gate H01 must return 0. Zero tolerance. |
| D03 AllergenFilter | Zero dishes with any allergen matching any household member's flags at ingredient level | Dish-level allergen_flags not updated (derivation not run) | User with all 7 allergens: very restricted pool | Family where child is allergic but parent is not | Safety Gate H02 must return 0. Zero tolerance. |
| D06 NeverListFilter | Zero never-listed dishes appear in any candidate set | is_active flag incorrectly set | User has 500 dishes never'd: very restricted pool | User never's and immediately requests refresh | Never-listed dish (is_active=true) never appears in suggestion_logs. |
| D07 ConstraintConflict | < 3 candidates → static popular fallback by diet type | All candidates filtered → empty slate | Exactly 3 candidates: no fallback triggered | Jain user with nuts+dairy+gluten allergies | Coverage gap logged. Fallback shown. H-01 constraint conflict UI state triggered. |

### Scoring Validation

| **Function** | **Expected behaviour** | **Failure behaviour** | **Boundary condition** | **Edge case** | **Success criteria** |
| --- | --- | --- | --- | --- | --- |
| E01 WeightLadder | Weights sum to 1.0 always. Smooth interpolation. | Config table missing: default to tier 0 weights | interaction_count = exactly 10: at tier boundary | interaction_count = 0: pure tier 0 weights | w_cohort + w_content + w_history + w_context + w_explore = 1.0 (within floating point tolerance). |
| E04 PersonalHistory | Range −1 to +1. Recent events weighted higher. | interaction_events table unavailable: return 0.0 (neutral) | Only one event on this dish: single event × decay | User rates same dish twice (different dates) | PersonalHistory never exceeds 1.0 or falls below −1.0. Dishes with zero interactions return exactly 0.0. |
| E07 PenaltyTerms | Penalty decays from 0.80 to 0.05 over 7 days | not_today_suppression record corrupt | t=0 exactly: penalty=0.80 | Not Today'd dish rated 5★ immediately after | Penalty at Day 7 always < 0.05. Penalty at Day 0 always = 0.80. Context override only applies at t≥3. |
| E08 FinalScore | Hard constraint check ran first | Hard constraint bypassed: P0 safety incident | All signals at maximum: theoretical max FinalScore | Two dishes with identical FinalScore: tie-break by base_score | FinalScore only computed for dishes that passed ALL D02–D06 filters. FinalScore never positive for a never-listed dish (excluded before scoring). |

### MMR and Variety Validation

| **Function** | **Expected behaviour** | **Failure behaviour** | **Boundary condition** | **Edge case** | **Success criteria** |
| --- | --- | --- | --- | --- | --- |
| F01 MMR | 8 distinct dishes in slate. More diverse than raw score ranking. | < 8 candidates after MMR: pad with highest-score remaining | Exactly 8 candidates: MMR selects all | λ=0.70: all dishes from same class still diversified on genome | All 8 slate positions filled. No dish appears twice in same slate. |
| F02 VarietyRules | No rule violated in generated 7-day plan | variety_window_state unavailable: skip variety check, log warning | User has locked all 21 slots: variety rules don't apply | User in single-cuisine household and variety rule conflict | If no variety violations: generate without MMR variety pressure. |

### Safety Gate Validation

| **Function** | **Expected behaviour** | **Failure behaviour** | **Boundary condition** | **Edge case** | **Success criteria** |
| --- | --- | --- | --- | --- | --- |
| H01–H04 All gates | Return 0 rows. Deployment proceeds. | Return > 0 rows. Deployment BLOCKED. Alert triggered. | 0 rows in suggestion_logs (first deployment): gates trivially pass | Gate runs during shadow mode: violations in shadow count as failures | **Zero tolerance on all 4 gates at all times.** Any violation = immediate P0 investigation. |

### Learning Loop Validation

| **Function** | **Expected behaviour** | **Failure behaviour** | **Boundary condition** | **Edge case** | **Success criteria** |
| --- | --- | --- | --- | --- | --- |
| J02 UpdateCount | interaction_count increments by exactly 1 per qualifying event | Duplicate event logged: interaction_count double-incremented | interaction_count = 13 → 14: J05 exitColdStart triggers | App offline: events queued, batch processed on reconnect | interaction_count never decrements. Cold start exit happens exactly once per user lifetime. |
| J03 GenomeAffinity | genome_tag_affinity updates reflect dish genome tags of accepted dish | Event not synced: affinity stale until next batch | First ever accepted dish: genome_tag_affinity moves from 0.0 | User accepts a dish with no Tier-1 tags (content ops gap) | genome_tag_affinity values bounded [−1.0, 2.0]. ContentMatch improves over time as affinity aligns with preferences. |

### Safety and Compliance Validation

| **Function** | **Expected behaviour** | **Failure behaviour** | **Boundary condition** | **Edge case** | **Success criteria** |
| --- | --- | --- | --- | --- | --- |
| K01 DeriveDishAttribs | dish.diet_type, is_jain, allergen_flags always reflect current ingredients | Derivation trigger fails: dish serves wrong food | Dish with zero ingredients: diet_type=null (blocked from recommendation) | Ingredient is_jain_excluded flag changed retroactively | Zero manual overrides. Safety Gate H01-H03 return 0 after every derivation run. |
| M01 CaptureConsent | Separate consent per category. Pre-ticked invalid. | User exits without consenting: onboarding cannot proceed | User denies personalization: RE cannot function | User revokes consent post-signup | personalization consent required before ANY dietary data collection. Consent stored append-only. |
| M03 DataDeletion | All personal data deleted within 72 hours | Deletion job fails: retry with alert | User with 2 years of interactions: large deletion batch | User re-registers after deletion | interaction_events, profiles, household_members, never_list — all deleted. audit_log retained. User cannot be identified post-deletion. |

## Document sign-off

| **Field** | **Value** |
| --- | --- |
| Document | DOC-P3-03A · Logic Governance and Execution Matrix |
| Version | 1.0 |
| Status | ACTIVE — [FD-05, 2026-07-16] no Founder signature required for `[ACTIVE]` status; see naming standard amendment |
| Sections | 9 sections across 61 logical functions |
| Read/Write Matrix | All 61 functions mapped to data read, written, derived, and consumed |
| Configuration parameters | 47 parameters classified across 6 config tables |
| Traceability | All functions traced to source documents, CDM entities, invariants, events |
| Decisions register | 10 items — 3 are implementation decisions (D-001, D-004, D-010), 7 are non-blocking |
| Execution types | Synchronous (24), Asynchronous (15), CRON scheduled (6), Event-driven (3), One-time (1) |
| Companion to | DOC-P3-03 v1.0 |
| Next document | DOC-P3-04 · Data Architecture and Entity Relationship Model |

Founder sign-off: ___________________________ Date: _______________