# P3-03 Context Baseline and Readiness Assessment

**Date:** June 2026  
**Purpose:** Complete document baseline, conflict identification, readiness validation, and working principles before writing DOC-P3-03 (Business Logic Specification)  
**Documents read:** All 18 active documents — DOC-01 through DOC-10, RE-DOC-01 through RE-DOC-05, DOC-P3-02 CDM v1.1, PM-SUPP-01, PM-SUPP-02, SESSION\_HANDOFF-4

---

## STEP 1 — Context Baseline

---

### DOC-01 · Product Brief v1.0

**Purpose:** Founding vision document. Defines the problem, the four-layer science, and the product promise.

**Key decisions captured:**

- Four-layer RE model: Layer 1 Genome (innermost), Layer 2 Food Graph, Layer 3 Household Intelligence, Layer 4 Context (outermost)  
- Processing order: Context wraps Household wraps Food Graph wraps Genome  
- 41 backend personas × 36 states  
- 500+ dishes tagged across 20 genome dimensions before launch  
- Class-first architecture (class determines meal type before dish)  
- "Zomato solved how to get food. Foofoo solves what to eat."  
- ₹25,000 total budget. Free tier infrastructure until 500 DAU.

**Critical inputs to P3-03:**

- Confirms the four-layer model is the scientific foundation for every algorithm  
- Section 08 Knowledge Base defines the input data required: meal class taxonomy, ingredient master with flags, context-meal affinity data — these become config tables in P3-03  
- The layered processing order (context → household → food graph → genome) is the master pipeline sequence

**Dependencies:** None. Founding document.

**Conflicts, ambiguities, issues:**

- Section 08 mentions "context-meal affinity data" as a pre-built knowledge base. The specific multiplier values within this data are never defined in DOC-01 or any other document. This is an unresolved gap that P3-03 must flag.  
- The Layer 1–4 naming convention (Genome=1 innermost, Context=4 outermost) is consistent with RE-DOC-02 but is inverted from intuitive understanding. Worth noting to avoid confusion in P3-03 descriptions.

**Assumptions still requiring validation:** None from this document. Vision is stable.

---

### DOC-02 · Market Research v1.0

**Purpose:** Market sizing, competitive analysis, whitespace identification.

**Critical inputs to P3-03:** None directly. No business logic defined here.

**Issues:** None. This document does not affect P3-03.

---

### DOC-03 · User Personas v1.0

**Purpose:** Five qualitative archetypes with day-in-life, journey maps, and backend cohort mapping.

**Key decisions captured:**

- Meera (P0): MC\_FAMILY → SC\_COUPLE\_WITH\_SCHOOL\_CHILD. Home: MP. City: Pune. Veg. Confident cook.  
- Priya (P2b): MC\_FAMILY → SC\_COUPLE\_WITH\_INFANT \+ O\_POSTPARTUM\_OVERLAY. Home: Tamil Nadu. City: Chennai. Non-veg.  
- Cold start confidence example for Meera: Day 1 \= 0.72, Day 7 \= 0.84  
- Sub-cohort naming pattern confirmed: SC\_ prefix for sub-cohorts, O\_ prefix for overlays  
- Postpartum overlay: ALWAYS additional to primary plan, never replaces it. Critical architectural rule.

**Critical inputs to P3-03:**

- Sub-cohort naming convention (SC\_, O\_) should be used consistently throughout P3-03  
- Postpartum add-on architecture principle is documented here — P3-03 must enforce this in the generate\_addons() specification  
- Persona code examples (MC\_FAMILY, SC\_COUPLE\_WITH\_SCHOOL\_CHILD) give P3-03 real-world references

**⚠ CONFLICT IDENTIFIED — C-001:** DOC-03 states Meera's "Cold-start confidence score: 0.72" at Day 1\. RE-DOC-04 states the maximum onboarding confidence is 0.65. The value 0.72 exceeds the documented maximum. One of these is wrong.

**Resolution required:** RE-DOC-04 is the authoritative source for confidence calculation. DOC-03's 0.72 is illustrative and incorrect. The correct maximum at onboarding completion is 0.65. P3-03 will use RE-DOC-04's values.

---

### DOC-04 · PRD v1.1

**Purpose:** Complete feature registry, 6-step product pipeline, user stories, NFRs, success metrics.

**Key decisions captured:**

- 6-step product pipeline: Onboarding signals → Persona assignment (silent) → 7-day class plan → Member add-ons → Class-to-dish expansion \+ scoring → Feedback loop  
- 41 backend personas × 36 states explicitly confirmed  
- 30 MVP features with acceptance criteria  
- Day-0 cold-start acceptance target: \>25%  
- Suggestion acceptance rate target: \>40% at Day 90  
- Plan generation speed NFR: \<3s end-to-end  
- DPDP compliance as NFR with same priority as functional requirements

**Critical inputs to P3-03:**

- The 6-step pipeline is the highest-level specification P3-03 must implement. Each step becomes a function.  
- F-09 (Skip handling with cold-start defaults per RE-DOC-04) explicitly cross-references RE-DOC-04 — P3-03 must implement every fallback rule in RE-DOC-04 §01.  
- F-39 (RE v1 class-first from cohort matrix) and F-40 (RE v2 personal history learning) are the two RE versions for MVP and Sprint 6\.  
- "class plan always comes first. Dish selection is always expansion within a class" — non-negotiable rule explicitly stated.  
- Success metrics (\>25% Day-0, \>40% Day-90 acceptance) are the test bench for P3-03 algorithm quality.

**Conflicts, ambiguities:** None found. DOC-04 is consistent with all other documents.

**Assumptions still requiring validation:**

- OQ-01: Phase assignment for 6 deferred features (F-24, F-27, F-28, F-46, F-50, F-57). Does not affect P3-03.  
- How "acceptance rate" is measured is not defined precisely (see Gap G-007).

---

### DOC-05 · Information Architecture v1.2

**Purpose:** 35 MVP screens, navigation model, critical user flows, gesture specification.

**Key decisions captured:**

- Gesture model (breaking change in v1.2): Swipe-left reveals Not Today/Never buttons. Carousel via tap on swap icon.  
- OB-07: Left/right card swipe for class preference signals  
- OB-08b: Plan preview before onboarding completes. User can interact (swap, lock, never) before leaving onboarding.  
- Not Today flow: slot regenerates immediately after confirmation  
- Never flow: slot regenerates immediately after confirmation  
- "Constraint conflict" screen state on H-01 — when RE returns an empty slate

**Critical inputs to P3-03:**

- Flow 3a explicitly documents: "RE background: Penalty P(t) \= 0.80 × e^(-0.35t) applied" — this confirms the Not Today decay formula and its parameters (P0=0.80, λ=0.35) are part of the product specification, not just an RE engineering detail  
- OB-08b interactions (swap, lock, never before onboarding\_completed) must be valid interaction events processed by the RE  
- "Slot regenerates immediately" after Never/Not Today confirmation — this means the RE must be callable for a single slot in real time, not just for full weekly plan generation  
- H-01 "Constraint conflict" state — the RE must return a specific signal when no candidates survive all hard constraints, not just an empty array  
- OB-07 skip behavior: skipping produces no class preference signals — cold start defaults apply (zero class\_affinity signals from onboarding)

**⚠ AMBIGUITY IDENTIFIED — A-001:** "Slot regenerates immediately" appears in both Not Today and Never flows. "Immediately" must mean one of two things: (a) the remaining 7 dishes in the existing 8-dish slate are used (i.e., the next ranked alternative is promoted), or (b) a full new RE request is made for that slot. If (a), no API call is needed. If (b), a new API call is needed and the \<3s performance NFR applies.

**Resolution required before P3-03:** Which behavior is correct? Recommendation: (a) promotes the next alternative from the existing slate first (fast, no API call). Only if the slate is exhausted does the RE generate a new set. This should be confirmed.

**⚠ AMBIGUITY IDENTIFIED — A-002:** H-01 "Constraint conflict" state — this occurs when RE returns an empty slate. What should the RE return in this case? An empty array? A specific error code? A fallback dish from a wider pool? This edge case is not defined in any RE document.

---

### DOC-06 · UX Design System v1.1

**Purpose:** Design tokens, component library, wireframes, gesture specifications.

**Key decisions captured:**

- C-11 Migration Duration Slider: Specific city overlay weight values defined:  
  - \< 1 year → 0.15  
  - 1–3 years → 0.30  
  - 3–7 years → 0.50  
  - 7+ years → 0.70  
  - Skip → 0.50 (3-year default), confidence −0.04  
- C-07 OB-07: YES swipe → class affinity boost. NOPE → class affinity penalty. Applied to cohort matrix weights.  
- C-02 Carousel reason tags: "Regional favourite," "Quick cook," "Based on your taste"  
- After Never or Not Today: slot regenerates

**Critical inputs to P3-03:**

- City overlay weight values from C-11 are DEFINED HERE — these are the authoritative values. Not in any RE document. P3-03 must use these exact values.  
- The skip penalty for OB-03 (confidence −0.04) is documented in DOC-06 C-11, not in RE-DOC-04. Both documents contribute to the confidence formula.  
- OB-07 skip: "Skipping produces no class preference signals — cold start defaults apply." P3-03 must specify that when OB-07 is skipped, class\_affinity is initialized at neutral (0.0 for all classes).  
- Reason tags (C-02) are confirmed as a stored field per P3-02 CDM decision.

**⚠ GAP IDENTIFIED — G-008:** DOC-06 C-07 says "YES \= class affinity boost. NOPE \= class affinity penalty." The specific magnitude of these boosts and penalties is not defined in DOC-06 or any other document. The OB-07 signal magnitude is an unresolved product decision.

**No conflicts found.** DOC-06 is internally consistent and consistent with other documents.

---

### DOC-07 · GTM v1.0

**Purpose:** Go-to-market strategy, acquisition channels, launch plan.

**Critical inputs to P3-03:** None directly. No business logic defined here.

---

### DOC-08 · Revenue v1.0

**Purpose:** Pricing model, monetisation strategy, financial projections.

**Critical inputs to P3-03:** None directly. The 90-day free period confirms no paywall during MVP, which means no feature gating logic is needed in the RE during MVP.

---

### DOC-09 · Legal v1.0

**Purpose:** DPDP Act 2023 compliance, app store requirements, product-specific legal items.

**Key decisions captured:**

- Consent: Granular, per data category. Health/dietary data requires separate consent from account data. No bundled consent.  
- Data export: within 72 hours of request  
- Account deletion: permanent erasure within 72 hours. Not soft-delete.  
- Interaction event retention: "2 years maximum" per DPDP  
- Allergen disclaimer required: "Foofoo's allergen filtering is a convenience feature. Always verify dish ingredients independently."  
- No health claims in MVP — medical disclaimer required if health features added (Phase 1+)  
- Minor protection: Age gate at signup. Under-13 blocked.

**Critical inputs to P3-03:**

- The RE must not process personalization data until explicit consent is confirmed. P3-03 must specify the consent check before the onboarding pipeline begins processing dietary and preference data.  
- The allergen disclaimer is a product requirement that affects onboarding UX — P3-03 must include consent capture before allergen data is collected.  
- 2-year interaction event retention affects the feature store design — events older than 2 years must not contribute to PersonalHistory or Taste Vector updates.

**⚠ CONFLICT IDENTIFIED — C-002:** DOC-09 requires "health/dietary data requires separate consent from account data." DOC-10 stores consent as `profiles.consent_record (JSONB)` — a single field on the profiles table. The CDM v1.1 defines a separate Consent Records entity (separate table, append-only for audit trail).

**Resolution:** CDM v1.1 is correct. Consent must be a separate table (one row per consent type per user) to enable: (a) granular per-category tracking, (b) consent version history, (c) audit log for DPDP. DOC-10's JSONB approach is a pre-CDM design that is superseded. P3-04 will use the separate table approach.

---

### DOC-10 · Technical Architecture v1.0

**Purpose:** Tech stack, system architecture, Edge Function specifications, security, performance, offline, timezone rules.

**Key decisions captured:**

- RE is sovereign — Principle 2\. No RE logic in the app. API contract only.  
- 8-stage RE pipeline (later corrected to 9 steps including final response): validate → assign\_persona → generate\_class\_plan → generate\_addons → expand\_dishes → score\_candidates → mmr\_rerank → safety\_gate → return  
- 5 Edge Function endpoints: /v1/recommendations, /v1/events, /v1/onboarding, /v1/plan, /v1/health  
- Failure behaviour per stage is explicitly defined (important for P3-03)  
- When \< 3 candidates after constraint filter: "widen class, log as coverage gap"  
- Cron jobs: morning plan pre-generation (23:30 UTC / 5:00 IST), cohort weight recalibration (Sunday), feature store cleanup (daily), health check (every 5 min)  
- All timestamps UTC. IST computation in Edge Functions only.  
- Performance: \<3s plan generation, \<100ms swipe response  
- Offline: MMKV-cached plan, event queue flushed on reconnect

**Critical inputs to P3-03:**

- The 8-stage RE pipeline with failure behaviors is the most detailed implementation specification in all documents. P3-03 must honor this pipeline sequence and every failure behavior.  
- The fallback behaviors (rank by cohort popularity if scoring fails; use default class plan if DB read fails) become explicit fallback specifications in P3-03.  
- Cohort weight recalibration cron: "Compares actual acceptance rates per cohort vs research weights. Updates cohort\_matrix.weight where reality diverges." The algorithm for this comparison and update is not defined — it is a P1 gap.  
- "Widen class" behavior when \< 3 candidates — not defined. P3-03 must specify what "widen class" means.

**⚠ CONFLICT IDENTIFIED — C-003:** DOC-10 pipeline Step 2 is named `assignPersona()`. RE-DOC-01 clearly states persona is assigned ONCE at onboarding (POST /v1/onboarding). If persona is already stored in the profile after onboarding, the recommendation pipeline should not reassign it — it should FETCH it. The function name in DOC-10 is a naming error that implies wrong behavior.

**Resolution:** Step 2 in the recommendation pipeline is `fetchPersona()` — reading the stored persona\_id from the profile. `assignPersona()` runs only in POST /v1/onboarding. P3-03 must use this corrected naming and behavior.

**⚠ CONFLICT IDENTIFIED — C-004:** DOC-10 pipeline Step 2 fallback: "If no persona match: use MC\_GENERIC fallback with confidence 0.35." The persona code "MC\_GENERIC" does not appear in any RE document, CDM, or persona definition. It is an undocumented fallback persona.

**Resolution required:** Three options: (a) MC\_GENERIC is a real row in the cohort seed data — needs to be confirmed and added to seed data specification; (b) MC\_GENERIC is a hardcoded default behavior (not a persona row), meaning the RE uses the most generic available class plan; (c) the correct fallback is to trigger a re-onboarding prompt. A product decision is needed before P3-03 can specify this behavior.

**⚠ CONFLICT IDENTIFIED — C-005:** DOC-10 lists the re\_engine schema tables as: `cohort_matrix, re_class_taxonomy, re_dish_genome, re_persona_slot_plan, re_segment_addon_rule, re_state_class_affinity`. These names do not match the CDM v1.1 entity names or the RE document terminology. Specifically, `re_dish_genome` suggests dish genome data lives in the RE schema — but CDM v1.1 establishes dish\_tags lives in the public schema (accessible to app client for display purposes).

**Resolution:** CDM v1.1 supersedes DOC-10 on table naming and schema placement. DOC-10's table list is a pre-CDM design and is outdated. P3-04 (Data Architecture) will establish the correct schema.

**⚠ AMBIGUITY IDENTIFIED — A-003:** "If \< 3 candidates after constraint filter: widen class, log as coverage gap." What does "widen class" mean? Expand to adjacent meal classes? Remove one hard constraint? Lower the difficulty filter? This is not defined in any document. P3-03 must either specify the widen logic or flag it as an unresolved product decision.

---

### RE-DOC-01 · Architecture and Module Design v1.0

**Purpose:** Module boundaries, API contract, versioning, fallback behavior.

**Key decisions captured:**

- RE is a sovereign module. All RE intelligence lives server-side.  
- POST /v1/onboarding → returns persona\_id \+ confidence\_score  
- POST /v1/recommendations → returns ranked slate (8 dishes per slot)  
- POST /v1/events → logs interaction events  
- GET /v1/plan → returns cached plan for week  
- "Still learning your taste" message when confidence \< 0.30

**Critical inputs to P3-03:**

- Module boundary principle: no RE logic in the app. P3-03 must specify every computation as an Edge Function operation, not a client-side operation.  
- The onboarding endpoint is where persona assignment happens — confirmed by RE-DOC-01. This resolves Conflict C-003 (DOC-10 named it assignPersona in the recommendation pipeline incorrectly).  
- Confidence threshold for "Still learning" UI: 0.30

**⚠ AMBIGUITY IDENTIFIED — A-004:** RE-DOC-01 mentions a single-slot refresh capability but the 5 Edge Function endpoints in DOC-10 don't include a dedicated single-slot refresh endpoint. DOC-05 Flow 3a says "slot regenerates immediately" after Not Today. How does this work technically?

**Resolution required:** See A-001 (from DOC-05). This is the same issue. Both documents confirm the behavior; neither defines the mechanism. Recommendation for P3-03: specify that "slot regenerates" means promoting the next-ranked dish from the existing stored slate (dishes 2–8 from the original 8). Only when the slate is exhausted (user has rejected all 8\) does a fresh RE request generate new candidates for that slot. This avoids a new API call on every Not Today/Never action.

**⚠ GAP IDENTIFIED — G-009:** "Still learning your taste" UI trigger is defined (confidence \< 0.30). But there is no UI component for this in DOC-06. No sentry, no badge, no bottom sheet. Where does this appear in the UI? This is a product decision gap — the message is defined but its surface is not designed.

---

### RE-DOC-02 · The Four Layers v1.0

**Purpose:** Scientific description of the four-layer model.

**Key decisions captured:**

- 20 genome dimensions (16 explicitly named, 4 implied)  
- Food Graph node types: Dish, Ingredient, AllergenFlag, MealClass, UserProfile, MemberSegment  
- Household model: primary plan \+ member add-ons. Add-ons are always separate.  
- Context signals: weather, temperature band, season, day of week, time of day  
- City overlay: home\_state\_signature\_weight \+ current\_city\_lifestyle\_weight \= 1.0 always  
- Weather multipliers: rainy/cold → comfort food. Hot → light food. Range 0.8 to 1.2×.

**Critical inputs to P3-03:**

- The worked example (rainy Tuesday 7AM Mumbai, MP family, vegetarian, peanut allergy, infant) is the most concrete single specification of how all four layers interact. P3-03 must be able to reproduce this example from its specifications.  
- Allergen propagation through Food Graph \= ingredient-level check. This is confirmed here and is the basis for Safety Gate 2\.  
- "combo\_dish\_ids" pattern for combo meals — but RE-DOC-02 uses a different approach than what CDM v1.1 established (dish\_combos \+ dish\_combo\_items junction). This is a terminology difference, not a conflict.

**⚠ GAP IDENTIFIED — G-003:** The genome "20 dimensions" are referenced throughout but only 16 are explicitly named in RE-DOC-02: spice\_level, texture\_profile, cooking\_method, primary\_taste, meal\_occasion, protein\_level, cook\_time\_band, difficulty, calorie\_band, regional\_origin, weather\_affinity, seasonal\_affinity, comfort\_warmth\_score, main\_ingredient\_class, religious\_compatibility, festival\_relevance. The remaining 4 are not named in any document. P3-03 must enumerate all 20 explicitly or acknowledge that the 4 unnamed dimensions are to be defined during content operations (before launch).

**⚠ GAP IDENTIFIED — G-004:** Context multiplier values: RE-DOC-02 describes weather × food affinities directionally but does not define specific multiplier values per weather condition × genome tag. The range (0.8 to 1.2×) is stated. The exact value for "rainy → comfort\_warmth\_score boost" is not stated. P3-03 must either define these values or flag them as a content operations decision to be put in a configuration table.

---

### RE-DOC-03 · Meal Class Taxonomy and Scoring v1.0

**Purpose:** 26 class codes (conceptual), scoring formula, hard constraint list, weight ladder.

**Key decisions captured:**

- FinalScore formula with 5 signals: CohortPrior, ContentMatch, PersonalHistory, ContextFit, ExplorationBonus  
- Five scoring signals and their weight tier allocations  
- Weight ladder: 5 tiers from 0 interactions to 150+ interactions  
- Smooth interpolation between tiers (not hard switches)  
- Six hard constraints (pre-filter before scoring)  
- Thompson Sampling Beta(α,β) for ExplorationBonus  
- Non-veg logic note: separate logic needed per state

**Critical inputs to P3-03:**

- FinalScore formula is the single most important specification in all RE documents. P3-03's scoring section derives entirely from this.  
- All 5 weight tier rows (interaction count thresholds and corresponding weights) must be enumerated in P3-03.  
- Hard constraint list is the pre-filter checklist. P3-03 must implement these in order.  
- "No hard switch between tiers. Weights are interpolated" — this is an explicit behavioral specification.

**⚠ GAP IDENTIFIED — G-001 (P0):** PersonalHistory event weights are not defined anywhere in RE-DOC-03 or any other document. "PersonalHistory \= Σ(event\_weight × time\_decay)" — but what is event\_weight for each event type? The CDM proposes values (cook=0.80, lock=0.60, accept=0.40, swiped\_past=−0.10, not\_today=−0.30, never=−1.00) but explicitly marks these as "proposals to be finalised in Business Logic Specification." This is the single largest gap in all active documents.

**⚠ GAP IDENTIFIED — G-005:** The cohort-to-class prior lookup table structure — CohortPrior \= "Lookup(cohort × dish\_class acceptance rate from research DB)" — references a table that is never defined in any document. What is the structure of this table? Is it (cohort\_id × class\_code → prior\_float)? Or (persona\_id × class\_code → prior\_float)? Or something else? P3-03 must define this structure.

---

### RE-DOC-04 · Cold Start, Variety Guard and Suppression v1.0

**Purpose:** Confidence calculation, MMR variety algorithm, suppression rules, variety window rules.

**Key decisions captured:**

- Onboarding confidence: 0.40–0.65 range. Specific contributions per signal documented.  
- Cold start fallback rules: 6 rules for each skipped/missing data case.  
- MMR formula: MMR(i) \= argmax\[λ × ScoringRelevance(i) − (1−λ) × max\_j∈Selected Similarity(i,j)\]  
- λ \= 0.7 for MVP (relevance-leaning)  
- Not Today decay: P(t) \= P0 × e^(−λt) where P0=0.80, λ=0.35  
- Variety rules: same dish max 30 days; same class max 3×/week breakfast/lunch, 2×/week dinner; same cuisine family max 2 in 5 days; same cooking method max 3 fried/week (4 in monsoon)  
- Never reactivation: seasonal (\>6 months \+ matching season), festival (\>90 days \+ matching festival)

**Critical inputs to P3-03:**

- Confidence contribution values per signal — these are the authoritative values (supersede DOC-03's illustrative example)  
- All 6 cold start fallback rules must be implemented exactly as specified  
- MMR formula and λ value — exact formula specified  
- Not Today decay — exact formula and parameters specified. This is a rare case of a fully quantified algorithm in the RE documents.  
- All 4 variety window rules with exact thresholds  
- Never reactivation rules with exact time thresholds

**⚠ CONFLICT IDENTIFIED — C-001 (confirmed):** RE-DOC-04 maximum onboarding confidence \= 0.65. DOC-03 Meera's Day 1 confidence \= 0.72. RE-DOC-04 is authoritative. The 0.72 in DOC-03 is illustrative error.

**⚠ GAP IDENTIFIED — G-006:** PersonalHistory time decay lambda (λ\_history). RE-DOC-04 defines λ=0.35 for Not Today decay. This same λ is NOT the λ for PersonalHistory time decay. PersonalHistory decays more slowly (preferences are more persistent than "not today" sentiments). The λ\_history value is not defined anywhere. P3-03 must either define it or flag it as a product decision.

---

### RE-DOC-05 · Evolution Roadmap v1.0

**Purpose:** 4-state evolution model, ML upgrade path, feature store requirements, shadow mode, offline evaluation metrics.

**Key decisions captured:**

- State A (MVP): research data dominant. Day 0 acceptance \>25%.  
- State B (Sprint 6+): personal history dominant. 30+ days active.  
- State C (Phase 2): cluster-based cold start. 5,000+ DAU.  
- State D (Phase 3+): full ML. Personal \+ cluster trends \+ optional CF.  
- Feature store: 5 categories to log from Day 1 (user, dish, interaction, context, plan features)  
- Shadow mode: 72 hours. Promote only if all metrics equal or better.  
- Offline metrics: MRR@8, NDCG@8, diversity score, constraint compliance

**Critical inputs to P3-03:**

- Feature store requirements define what must be logged from Day 1\. P3-03 must specify logging requirements for the context\_log and suggestion\_log tables.  
- Anti-filter-bubble logic: "\<3 cuisine families for 30 days → exploration bonus \+0.10." P3-03 must specify how cuisine family diversity is tracked (rolling window) and how the bonus is applied.  
- Shadow mode procedure — P3-03 must specify how new RE versions are tested before promotion.

**⚠ GAP IDENTIFIED — G-007:** Success metric "Day 0 acceptance \>25%" — how is "acceptance" defined precisely? DOC-04 and RE-DOC-05 both state this target but neither defines what constitutes an accepted dish. Is it: (a) user selects a dish from the carousel? (b) user does NOT swipe-left (Not Today or Never)? (c) user taps "Cook This"? The definition determines how the metric is measured and whether the target is achievable. P3-03 must define acceptance precisely.

**No conflicts found with other documents.** RE-DOC-05 is consistent throughout.

---

### DOC-P3-02 · Conceptual Domain Model v1.1

**Purpose:** 51 domain entities, 7 aggregate roots, business invariants, event catalogue, dependency map.

**Key decisions captured:** All 51 domain concepts defined. 14 business invariants. 52 business events. 8-layer dependency map.

**Three open decisions carried forward (explicitly noted):**

1. Genome vector representation (pre-computed vs assembled at query time)  
2. PersonalHistory event weights (proposed values, not yet confirmed)  
3. assign\_persona() mapping rules (input-output documented, mapping logic not)

**Critical inputs to P3-03:** This document IS the conceptual foundation. P3-03 must not introduce any new domain concept that is not in the CDM. If a new concept emerges during P3-03 writing, the CDM must be updated first.

**No conflicts found.** The CDM synthesized all other documents. All conflicts discovered during CDM creation were resolved in the CDM's favor.

---

### PM-SUPP-01 · Roadmap and SESSION\_HANDOFF-4

**Purpose:** Phase sequencing and session continuity.

**Notes for P3-03:**

- SESSION\_HANDOFF-4 references the old repo (foofoo) and old Supabase staging IDs. These are outdated per infra reset decisions in sessions \#002–\#004.  
- SESSION\_HANDOFF-4 lists DOC-11 as the next document. This has been superseded by the APDF framework decision: CDM → Business Logic Specification → Data Architecture → Schema. P3-03 (Business Logic Specification) precedes the schema.

---

## STEP 2 — Readiness Validation

### Conflicts requiring resolution before P3-03

| \# | Conflict | Source A | Source B | Resolution |
| :---- | :---- | :---- | :---- | :---- |
| **C-001** | Confidence score maximum: DOC-03 says 0.72, RE-DOC-04 says 0.65 max | DOC-03 Meera Day 1 confidence | RE-DOC-04 §01 | **Resolved: RE-DOC-04 is authoritative. Max \= 0.65. DOC-03 value is illustrative error. P3-03 uses RE-DOC-04 values.** |
| **C-002** | DPDP consent storage: DOC-10 uses JSONB on profiles; CDM uses separate table | DOC-10 §06 | CDM v1.1 Entity 51 | **Resolved: CDM v1.1 supersedes. Separate consent table with append-only rows for audit trail.** |
| **C-003** | assignPersona() in recommendation pipeline: DOC-10 says it runs at recommendation time; RE-DOC-01 says it runs at onboarding | DOC-10 §05 Stage 2 | RE-DOC-01 §03 | **Resolved: Persona assigned ONCE at onboarding. Recommendation pipeline calls fetchPersona(), not assignPersona(). DOC-10 naming is wrong.** |
| **C-004** | MC\_GENERIC fallback: DOC-10 references it; no other document defines it | DOC-10 §05 Stage 2 failure | No other document | **Unresolved. Requires product decision (see below).** |
| **C-005** | RE schema table names in DOC-10 don't match CDM v1.1 entity names | DOC-10 §05 database overview | CDM v1.1 | **Resolved: CDM v1.1 supersedes. DOC-10 table names are pre-CDM design. P3-04 will establish correct names.** |

---

### Unresolved gaps requiring decisions before or during P3-03

**P0 Gaps — P3-03 cannot fully specify the algorithm without these:**

| \# | Gap | Where referenced | What is missing | Recommendation |
| :---- | :---- | :---- | :---- | :---- |
| **G-001** | PersonalHistory event weights | RE-DOC-03 §02 (mentions signal, not values) | Exact numeric weight for each event type: accept, lock, cook, rate (per star level), never, not\_today, swiped\_past | **Must be defined as a product decision before P3-03 writes the PersonalHistory specification. CDM proposes values — founder confirmation needed.** |
| **G-002** | assign\_persona() mapping rules | DOC-04 Step 2, RE-DOC-01 | The mapping from (main\_cohort × sub\_cohort × home\_state × diet\_type) → persona\_id (from 41 options). Inputs documented; lookup logic not defined | **This is a data specification, not an algorithm. The mapping lives in seed data. P3-03 must specify that assign\_persona() is a database lookup, not a computed function. The actual persona assignment table must be part of seed data specification.** |
| **G-003** | 4 unnamed genome dimensions | RE-DOC-02 §02 (mentions 20, names 16\) | The 4 unspecified genome dimensions | **Can be flagged in P3-03 as "to be defined during content operations." Does not block algorithm specification if Tier-1 tags are complete.** |
| **G-004** | Context multiplier values | RE-DOC-02 §05, DOC-01 §08 | Exact multiplier per weather condition × genome tag (e.g., rainy → comfort\_warmth\_score × ?) | **Must be defined as a config table seeded from research data. P3-03 will define the structure of the config table. The actual values are a content decision.** |

**P1 Gaps — P3-03 should address these or explicitly flag them:**

| \# | Gap | Where referenced | What is missing |
| :---- | :---- | :---- | :---- |
| **G-005** | Cohort-to-class prior table structure | RE-DOC-03 (references "research DB") | Is CohortPrior a (cohort\_id × class\_code → float) lookup? Structure undefined. |
| **G-006** | PersonalHistory time decay lambda | No document | λ\_history for PersonalHistory decay over time. Different from λ=0.35 for Not Today. |
| **G-007** | Definition of "acceptance" for metrics | DOC-04, RE-DOC-05 success metrics | What user action constitutes an "accepted" dish for measurement purposes? |
| **G-008** | OB-07 class affinity signal magnitude | DOC-06 C-07 | How much does a YES/NOPE swipe change class\_affinity? |
| **G-009** | "Still learning" UI surface | RE-DOC-01 §05 | confidence \< 0.30 triggers message, but no UI component exists in DOC-06 |
| **G-010** | "Widen class" behavior | DOC-10 Stage 5 failure | What does widening a class mean when \< 3 candidates survive constraints? |
| **G-011** | Slate exhaustion behavior | DOC-05 Flow 3a/3b | What happens when user has rejected all 8 dishes in a slate? |
| **G-012** | Cohort weight recalibration algorithm | DOC-10 cron schedule | How does the Sunday cron compare acceptance rates and update weights? |
| **G-013** | MC\_GENERIC fallback persona | DOC-10 Stage 2 failure | Is MC\_GENERIC a real seed data row or a coded fallback behavior? |
| **G-014** | Constraint conflict resolution | DOC-05 H-01 "Constraint conflict" state | What does the RE return when no candidates survive all constraints? |

---

### Prerequisite document check

| Prerequisite | Status | Notes |
| :---- | :---- | :---- |
| DOC-P0-01 Business Model | ✅ Present | DOC-01 |
| DOC-P0-02 Market Research | ✅ Present | DOC-02 |
| DOC-P0-03 User Personas | ✅ Present | DOC-03 |
| DOC-P0-04 Problem Statement | ✅ Present | Within DOC-01 |
| DOC-P1-01 PRD | ✅ Present | DOC-04 |
| DOC-P1-02 User Journeys | ✅ Adequate | Within DOC-05 |
| DOC-P1-03 Roadmap | ✅ Present | PM-SUPP-01 |
| DOC-P1-04 Legal | ✅ Present | DOC-09 |
| DOC-P2-01 Information Architecture | ✅ Present | DOC-05 |
| DOC-P2-02 Design System | ✅ Present | DOC-06 |
| DOC-P3-01 System Architecture | ✅ Present | DOC-10 |
| DOC-P3-02 Conceptual Domain Model | ✅ Present | CDM v1.1 |
| RE Concept Documents | ✅ All 5 present | RE-DOC-01 through RE-DOC-05 |

**All prerequisites are present.** No missing prerequisite document.

---

### Feature-to-CDM mapping check

Verified that all 30 MVP features from DOC-04 can be traced to CDM entities:

- F-01 through F-09 (Onboarding): Entities 1, 9, 10, 11, 12, 13, 14, 28 (User, Cohorts, Onboarding Session, Confidence)  
- F-10 through F-14 (Plan display): Entities 23, 24, 25, 26, 19 (Week Plan, Plan Slot, Slate, Add-on, Dish Combo)  
- F-15 through F-19 (Gestures): Entities 29, 30, 31 (Interaction Events, Never List, Not Today Suppression)  
- F-20 through F-25 (Screens): Entities 23, 24, 15 (Plans, Slots, Dishes)  
- F-30 through F-34 (Search/Profile): Entities 1, 2, 3, 15 (User, Household, Members, Dishes)  
- F-37 (Push notification): Entity 63 (Push Notification in CDM)  
- F-39 through F-40 (RE versions): Entities 34–42 (Scoring signals, Weight Ladder)  
- F-55, F-56 (Analytics, monitoring): Operations layer entities

**All 30 MVP features map to CDM entities. ✅**

---

### Readiness verdict

| Check | Status | Notes |
| :---- | :---- | :---- |
| All prerequisite documents present | ✅ Yes | All 18 active documents read |
| CDM provides sufficient conceptual clarity | ✅ Yes | 51 entities, 14 invariants, event catalogue, dependency map |
| Every entity has a clear owner | ✅ Yes | 7 aggregates defined with ownership boundaries |
| Every MVP feature maps to CDM | ✅ Yes | All 30 features mapped |
| RE documents analyzed, logical functions identified | ✅ Yes | Business Logic Audit (\#027) \+ CDM v1.1 |
| Conflicts resolved | ⚠️ Mostly | C-001, C-002, C-003, C-005 resolved. C-004 (MC\_GENERIC) unresolved. |
| P0 gaps resolved | ⚠️ Partially | G-001 (event weights) requires founder confirmation. G-002, G-003, G-004 can be handled structurally in P3-03. |

**Verdict: CONDITIONALLY READY**

P3-03 can begin. Five conflicts have been resolved. The four remaining P0 gaps will be handled as follows: G-001 (event weights) will be presented as proposed values requiring founder confirmation before the document is signed. G-002, G-003, G-004 will be specified structurally (defining the configuration table or lookup mechanism) with the actual values flagged as seed data decisions. The fourteen P1 gaps will each be explicitly flagged as unresolved product decisions within P3-03 — none will be silently assumed.

---

## STEP 3 — Working Principles for P3-03

These principles govern every statement in the Business Logic Specification. They are not aspirational — they are operating rules. Violations are not permitted.

---

### Principle 1 — Documentary evidence required for every specification

Every algorithm, computation, decision rule, threshold, formula, and parameter in P3-03 must cite its source document(s). Format: `[Source: RE-DOC-03 §02]` after every specification.

If a specification cannot be traced to a source document, it is NOT included as a specification. Instead, it is listed as an unresolved product decision with an explicit flag: `[⚠ UNRESOLVED — product decision required]`.

This principle has no exceptions. The FinalScore formula is documented. The Not Today decay formula is documented. The PersonalHistory event weights are not documented — they will be flagged, not assumed.

---

### Principle 2 — Assumptions are prohibited; flags are required

P3-03 will never fill a gap with an assumption. When information is missing, the exact gap is stated and the decision required to fill it is described. The document distinguishes between:

- **Documented fact:** traceable to a specific source  
- **Derived fact:** logically inferred from documented facts with the derivation stated  
- **Proposed value:** a value recommended by the architect, clearly marked as requiring founder confirmation  
- **Unresolved decision:** a decision that must be made before implementation begins

---

### Principle 3 — Synthesis over repetition

Where multiple documents contribute to a single logical function, P3-03 synthesises them into one coherent specification. It does not repeat each document's description separately. The synthesis is authoritative; the source documents remain as reference. When documents conflict, P3-03 states the conflict, names both sources, and declares the resolution.

---

### Principle 4 — Algorithm specifications must be implementation-ready

Every algorithm in P3-03 must be specified precisely enough that two engineers independently implementing it would produce identical behavior for any given input. "The system scores candidates" is not a specification. "The system computes FinalScore \= (w\_cohort × CohortPrior) \+ (w\_content × ContentMatch) \+ ... and orders candidates by FinalScore descending" is a specification.

---

### Principle 5 — Hard constraints before soft scoring — always

P3-03 must make the ordering explicit in every pipeline section: hard constraint filters run before any scoring is applied. No dish violating any hard constraint is ever scored. This ordering is an invariant (CDM §14, Business Invariant 12\) and must be explicit in P3-03, not implied.

---

### Principle 6 — Fallback behaviors are first-class specifications

Every algorithm in P3-03 must specify its failure behavior with the same precision as its success path. DOC-10 defines failure behaviors for the 8 pipeline stages — P3-03 must incorporate and expand these. Unspecified failure behavior becomes a bug.

---

### Principle 7 — Configuration values belong in configuration tables

No numeric parameter (weight, threshold, lambda, multiplier) is hardcoded in P3-03's algorithm specifications. Every parameter is labeled as either: (a) a specific value from a source document, or (b) a configurable value to be stored in a named configuration table. This enables post-launch tuning without code deployment.

---

### Principle 8 — Traceability chain: CDM → P3-03 → P3-04 → P3-05

Every entity used in P3-03 must exist in the CDM. Every data structure required by P3-03 becomes a candidate for P3-04 (Data Architecture). Every derived field in P3-03 becomes a computed column or trigger specification in P3-05 (Schema). P3-03 does not design the database — it specifies the computations. P3-04 designs the database.

---

### Principle 9 — Event weights are proposed, not assumed

The CDM proposes PersonalHistory event weights (accept=0.40, lock=0.60, cook=0.80, etc.). P3-03 will present these proposed values explicitly and flag them as requiring founder confirmation before the document is signed off. Until confirmed, they are marked `[PROPOSED — awaiting confirmation]`.

---

### P3-03 document structure (proposed, subject to founder approval)

Given the principles above, P3-03 will be organized as follows:

1. **Purpose and scope**  
2. **Source document registry** — every document contributing to this specification with the specific sections referenced  
3. **Pipeline overview** — the 8-stage pipeline from DOC-10, corrected per conflict resolutions  
4. **Onboarding pipeline** — POST /v1/onboarding. Includes: persona assignment, confidence calculation, class preference swipe processing, plan preview generation  
5. **Class plan generation** — generateClassPlan(). Includes: cohort-to-class lookup, weekday/weekend logic, non-veg cadence  
6. **Add-on generation** — generateAddons(). Includes: member segment to add-on class mapping  
7. **Candidate generation** — expandClassToDishes(). Includes: class-dish options query, all 6 hard constraints in order, combined household allergen check  
8. **Scoring** — scoreCandidates(). Includes: all 5 FinalScore signals, weight ladder interpolation, penalty terms  
9. **Variety re-ranking** — mmrRerank(). Includes: MMR formula, variety window rules, variety penalty  
10. **Suppression rules** — Never list, Not Today decay, class-level affinity reduction  
11. **Safety gates** — all 4 gates, when they run, what failure triggers  
12. **Context assembly** — weather cache lookup, season derivation, festival proximity check  
13. **Learning loop** — event processing, taste vector updates, class affinity updates, cold start exit  
14. **Configuration parameters** — all numeric values from source documents, organized by configuration table  
15. **Unresolved decisions register** — all gaps and decisions flagged in Steps 1 and 2, explicitly listed with recommended resolutions  
16. **Source document citations** — full traceability index

---

## Summary for founder before P3-03 begins

**Five conflicts found and resolved:** C-001 (confidence max \= 0.65, not 0.72), C-002 (consent \= separate table), C-003 (fetchPersona not assignPersona in recommendation pipeline), C-004 (MC\_GENERIC undefined — needs decision), C-005 (DOC-10 table names superseded by CDM).

**Fourteen gaps identified.** Of these, four require decisions:

1. **G-001 — Event weights for PersonalHistory** (most critical): Confirm or adjust the proposed values in CDM §37: cook=0.80, lock=0.60, accept=0.40, rated\_5=0.60, rated\_3=0.00, rated\_1=−0.30, swiped\_past=−0.10, not\_today=−0.30, never=−1.00.  
2. **G-013/C-004 — MC\_GENERIC fallback**: What should happen when no persona can be assigned? Options: (a) A MC\_GENERIC row in seed data, (b) Use the most generic available class plan for main cohort, (c) Prompt re-onboarding.  
3. **G-007 — Definition of "accepted"**: What user action constitutes an accepted dish for success metric measurement? Recommendation: dish\_accepted event type (user selects from carousel OR keeps the headline suggestion without rejecting it).  
4. **G-009 — "Still learning" UI surface**: Where does this message appear in the app? Needs DOC-05/DOC-06 decision.

If you confirm the event weights (G-001) and the MC\_GENERIC fallback (C-004/G-013), P3-03 can be written without flagging those two as unresolved. The other 12 gaps can be handled structurally within P3-03.  
