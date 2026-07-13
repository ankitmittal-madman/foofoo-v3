# DOC-P3-02 · Conceptual Domain Model

**Version:** 1.1
**Date:** June 2026
**Status:** DRAFT v1.1 — pending founder sign-off
**Author:** Claude (Solution Architect role)
**Sources read:** DOC-01, DOC-02, DOC-03, DOC-04, DOC-05, DOC-06, DOC-09, DOC-10, RE-DOC-01 through RE-DOC-05, all HTML visual documents
**Next document:** DOC-P3-03 · Business Logic and Algorithm Specification
**Prerequisite for:** DOC-P3-03 (business logic), DOC-P3-04 (data architecture), DOC-P3-05 (database schema)

## How to read this document

This document defines every concept that exists in the FooFoo product domain — not as database tables, but as business ideas. It answers the question: **what things exist in this world, and how do they relate to each other?**

Each entity definition follows this structure:

- **What it is:** a plain-language definition

- **Why it matters:** what breaks if this concept is misunderstood

- **Key attributes:** the properties that define this entity (not yet column definitions)

- **Relationships:** how it connects to other entities

Business invariants — rules that must always be true — are listed separately at the end. Lifecycle states for key entities follow after that.

## Domain overview

FooFoo operates across five interconnected domains that must work together for the product to function.

The **Household Domain** defines who the product serves — the household as the planning unit, the primary cook as the user, and household members as the people whose needs shape the plan.

The **Identity Domain** defines how the household is characterised — their food culture, dietary constraints, regional roots, and cooking context. These signals feed every recommendation.

The **Content Domain** defines what can be recommended — dishes, their food DNA, the ingredients they contain, the combos they form, and the variants they belong to.

The **Planning Domain** defines the output of the RE — week plans, day plans, meal slots, slates of alternatives, and add-on components for special members.

The **Recommendation Engine Domain** defines how the output is produced — the scoring signals, the weight ladder, the suppression rules, the variety constraints, and the contextual adjustments that together compute a final score for every candidate dish.

## Part 1 — Household Domain

### Entity 1: User (Profile)

**What it is:** The person who has an account in FooFoo. In MVP, the user is always the primary cook of the household. There is one account per household. The user's account contains both their personal identity and the household's collective profile.

**Why it matters:** Everything in FooFoo is built around one household's plan. The user is the lens through which the household is known. Confusing the user with the household, or with individual members, is the most common source of product misunderstanding.

**Key attributes:**

- Identity: name (display only), email, authentication state

- Food roots: home state, current city, migration duration

- Dietary: diet type, religious preference, allergen flags

- Cooking: cook capability level

- Preferences: notification time, app settings

- RE state: persona assignment, confidence score, interaction count, cold start state, RE engine version

- Lifecycle: onboarding completed flag, last active timestamp

**Relationships:**

- Belongs to exactly 1 Household (in MVP, user = household)

- Has 0 to 8 Household Members

- Has 1 Regional Identity (derived from home state + current city + migration duration)

- Has 0 or 1 assigned Persona (base) + 0 to N Overlay Personas

- Has 1 Taste Vector (updated over time)

- Generates many Interaction Events

- Has 1 Never List (containing 0 to many dishes)

- Has 1 Onboarding Session

- Has 0 to N Week Plans

### Entity 2: Household

**What it is:** The unit of meal planning. In MVP, a Household is the same as a User — one account, one household. A household has one primary cook (the User) and optionally additional household members with distinct dietary needs.

**Why it matters:** The RE generates one unified household meal plan. It is not a collection of individual plans. Every slot in the plan must serve all household members simultaneously — allergens, diet type, and religious preferences from any member apply to the whole plan.

**Key attributes:**

- Household type (Main Cohort): one of Solo, Couple, Nuclear Family, Joint Family, PG/Hostel

- Size: number of people (derived from members count)

- Primary cook: reference to User

**Relationships:**

- Has exactly 1 User as primary cook

- Has 0 to 8 Household Members (anyone beyond the primary cook with distinct needs)

- Generates 1 active Week Plan at a time

**Design note:** In Phase 1.5 (F-36 Family Profiles), households may have multiple sub-profiles. This concept is out of scope for MVP but the domain model should not prevent it. The Household concept exists as a distinct layer to enable this future expansion without rewriting the user model.

### Entity 3: Household Member

**What it is:** A person in the household who is not the primary cook but whose dietary needs the household meal plan must accommodate. Each member has a Segment that tells the RE what type of special needs they have.

**Why it matters:** The RE generates add-on slots based on household members. A household with an infant gets an infant add-on alongside the family breakfast. The add-on is always a separate, additional component — it never replaces the primary household meal. This is the core architectural distinction: household member needs modify the plan by addition, not by substitution.

**Key attributes:**

- Member name (display only, optional)

- Segment: the category of their dietary situation

- Allergen flags: their personal allergens, which propagate to the primary plan

- Diet type: only specified if different from household default (e.g., one member is Jain in an otherwise non-veg household)

- Active flag: soft-delete support

**Member Segments — complete vocabulary:**

- INFANT: 0–12 months. Soft, no-salt, no-spice foods only. Add-on class: ADDON_INFANT.

- TODDLER: 1–3 years. Mild, easily chewable. Add-on class: ADDON_TODDLER.

- SCHOOL_CHILD: 4–12 years. Influences tiffin-style add-ons. Not a separate add-on in V1 — influences class plan weighting.

- DIABETIC_ELDER: Low GI, low sugar priority. Add-on class: ADDON_DIABETIC.

- POSTPARTUM: Lactation-support traditional add-ons (methi ladoo, ragi, til). Add-on class: ADDON_POSTPARTUM. This is the Priya persona's household situation.

- FITNESS_OVERLAY: High-protein, higher-calorie additions. Add-on class: ADDON_FITNESS.

- FASTING_MEMBER: Special fasting-compatible options during fasting periods. Add-on class: ADDON_FASTING.

- ADULT_STANDARD: No special needs. No add-on generated. Influences household size only.

**Relationships:**

- Belongs to exactly 1 Household

- Has 0 to N allergen flags (bitfield)

- May have its own diet type if different from household

- Triggers generation of 0 or 1 Add-on Slot per Plan Slot per day

**Critical invariant:** Any allergen flag on any household member propagates to the primary household plan. If one member cannot eat nuts, no plan slot for the household should contain a nut-derived dish.

## Part 2 — Identity Domain

### Entity 4: Regional Identity

**What it is:** The combined signal of a user's food cultural roots. It is not a stored entity — it is a derived concept made of three components: Home State, Current City, and Migration Duration. Together these determine how much of the meal plan reflects the user's home food culture versus the food culture of the city they now live in.

**Why it matters:** This is one of FooFoo's core differentiators. A family from Madhya Pradesh living in Mumbai for 5 years does not eat the same food as a family born and raised in Mumbai. The Regional Identity concept makes this distinction mathematically precise.

**Components:**

- **Home State:** the Indian state or UT where the user's food culture originates. One of 36 states/UTs. Required field.

- **Current City:** the city where the user currently lives. May be in the same state as Home State (native) or a different state (migrant). Required field.

- **Migration Duration:** how long the user has lived in Current City. Captured as a 4-band selection: < 1 year, 1–3 years, 3–7 years, 7+ years. If skipped: defaults to 3-year band.

**Derived value — City Overlay Weight:** The Migration Duration maps to a precise city overlay weight. This weight determines how much the current city's food culture influences the plan:

- < 1 year → 0.15 (mostly home state food, light city exposure)

- 1–3 years → 0.30

- 3–7 years → 0.50

- 7+ years → 0.70 (strong city influence)

- Skipped → 0.50 (medium default), confidence −0.04

The complement (1 − city_overlay_weight) is the home state signature weight. These always sum to 1.0.

**Special case — native:** If home state and current city are in the same state, city_overlay_weight = 0.0. There is no migration overlay. The plan uses pure home state food culture.

### Entity 5: Diet Type

**What it is:** The household's primary dietary classification. A hard constraint — it applies to every dish in every plan slot, without exception.

**Values:**

- veg: No meat, no egg, no fish. Dairy and honey permitted.

- non_veg: No restrictions on meat.

- egg: Vegetarian but egg is permitted. No meat or fish.

- vegan: No animal products including dairy and honey.

- jain: Strict vegetarian. No root vegetables (onion, garlic, potato, carrot, beetroot). Jain is always a subset of veg — a Jain-compatible dish is always veg-compatible.

**Why it matters:** Diet type is the first hard filter in every recommendation pipeline. A household with diet_type = veg must never see a non-veg dish. This is a correctness requirement, not a preference. Violations are tracked by Safety Gate 1.

**Relationship with Jain:** A household can have diet_type = jain AND religious_pref = jain. Or they can have diet_type = veg and religious_pref = jain. In either case, the Jain constraint applies. The system should treat Jain as the most restrictive veg variant.

### Entity 6: Religious Preference

**What it is:** A religious dietary constraint that is separate from and stricter than diet type in some cases. Applied as a hard filter.

**Values:**

- all: No restrictions beyond diet type.

- hindu_veg: Strict vegetarian for religious reasons. Overlaps with diet_type = veg.

- jain: No root vegetables. No onion, garlic, potato, carrot, beetroot. Checked via is_jain flag on dishes.

- halal: Meat must be halal-certified. Applies only to non-veg households.

- no_beef: No beef or beef-derived ingredients.

- no_pork: No pork or pork-derived ingredients.

### Entity 7: Allergen

**What it is:** A food substance that causes allergic reactions in one or more household members. Allergens are stored as a bitfield (integer) on both users and household members, and also on each ingredient. A dish's allergen status is derived from its ingredients.

**Seven defined allergens and their bit positions:**

- Bit 0 (value 1): Nuts / peanuts

- Bit 1 (value 2): Dairy

- Bit 2 (value 4): Gluten

- Bit 3 (value 8): Shellfish

- Bit 4 (value 16): Egg

- Bit 5 (value 32): Soy

- Bit 6 (value 64): Sesame

**Why bitfields:** A single integer can represent any combination of allergen exclusions. Query: (user_allergen_flags AND dish_allergen_flags) = 0 means the dish is safe. This is fast and storage-efficient.

**Critical rule:** Allergen checking must happen at ingredient level, not dish level. A dish's allergen flags are derived from its ingredients' allergen flags (UNION). If the derivation pipeline has not run, dish-level allergen data cannot be trusted. Manual entry of allergen flags on dishes is not permitted.

### Entity 8: Cook Capability

**What it is:** The skill level of the primary cook. Used to filter dish candidates — a beginner cook should not be recommended a dish that takes advanced technique.

**Values:**

- beginner: Simple, quick, forgiving recipes. Max 2–3 ingredients or steps.

- intermediate: Moderate complexity. Standard Indian home cooking.

- advanced: Complex techniques, longer prep, premium results.

**Relationship to Meal Classes:** Cook capability filters which Meal Classes are eligible. A beginner household gets BF_NO_COOK_QUICK and BF_LIGHT_GRAIN as primary breakfast classes, not BF_STUFFED_FLATBREAD which requires technique. This is not a hard filter — it is a scoring weight applied at class selection time.

## Part 3 — Cohort and Persona Domain

### Entity 9: Main Cohort

**What it is:** One of 5 household type categories shown to the user during onboarding at OB-01. This is the only cohort-level concept that the user ever sees. The 5 options are deliberately simple and recognisable.

**The 5 Main Cohorts:**

- MC_SOLO: One person. Includes working professional, student.

- MC_COUPLE: Two adults. No children.

- MC_NUCLEAR_FAMILY: Two adults with one or more children.

- MC_JOINT_FAMILY: Multi-generational household. More than one family unit under one roof.

- MC_PG_HOSTEL: Paying guest or hostel accommodation. Shared kitchen, limited equipment.

**Why it matters:** The main cohort is the top-level entry point into the RE's persona system. It determines which sub-questions appear in OB-02 (dynamic branching). A Solo user skips child and elder questions entirely.

**Invariant:** The user sees exactly these 5 options at OB-01. No persona codes, no sub-cohort labels are ever shown to the user.

### Entity 10: Sub-cohort

**What it is:** A refinement within a Main Cohort, captured through the dynamic branching questions in OB-02. The sub-cohort is not a user-facing term — it is a descriptor derived from OB-02 answers and passed as an input to the assign_persona() function.

**Sub-cohort determination by main cohort:**

- MC_NUCLEAR_FAMILY → OB-02 asks: children's ages → derives SC_WITH_INFANT, SC_WITH_TODDLER, SC_WITH_SCHOOL_CHILD, SC_WITH_TEEN, SC_WITH_MIXED_AGES

- MC_JOINT_FAMILY → OB-02 asks: elder members present? Health conditions? → derives SC_WITH_DIABETIC_ELDER, SC_WITH_ELDERLY_STANDARD, SC_MULTI_GEN_STANDARD

- MC_COUPLE → No sub-cohort branching in MVP. Sub-cohort = SC_COUPLE_STANDARD.

- MC_SOLO → No sub-cohort branching. Sub-cohort = SC_SOLO_STANDARD.

- MC_PG_HOSTEL → No sub-cohort branching. Sub-cohort = SC_PG_STANDARD.

**Important:** Sub-cohort is captured as an intermediate value during onboarding. It is not stored as a persistent field on the profile. The output of sub-cohort capture is the input to assign_persona().

### Entity 11: Persona

**What it is:** A backend classification that represents a specific type of household with a specific food identity. There are 41 personas total. The RE uses personas to look up pre-computed food preference data from the research database.

**Why it matters:** The persona is the bridge between onboarding (what the user told us) and the recommendation engine (what class plan to generate). Without a persona assignment, the RE has no research-based starting point for cold start plans.

**Key attributes:**

- Persona code: machine-readable identifier (e.g., MC3_NORTH_VEG, MC1_URBAN_SOLO)

- Display name: human-readable internal label (never shown to user)

- Parent main cohort: which of the 5 MC types this persona belongs to

- Primary diet: the diet type most common for this persona

- Home state group: the states this persona's food patterns reflect

**Invariant:** 41 personas total. User never sees a persona code. Persona is assigned silently by assign_persona() at the end of onboarding.

**Relationships:**

- Belongs to exactly 1 Main Cohort

- Applied to exactly 1 User at a time (base persona)

- Each persona maps to N Cohort rows in the research database (one per state)

### Entity 12: Overlay

**What it is:** A modifier applied on top of a base Persona for households with special members. Overlays do not replace the base persona — they add a dimension to it. A household can have zero overlays (typical) or multiple overlays (e.g., infant + diabetic elder simultaneously).

**Overlay types:**

- O_INFANT: Household has an infant member. Triggers ADDON_INFANT add-on generation.

- O_TODDLER: Household has a toddler. Triggers ADDON_TODDLER.

- O_DIABETIC_ELDER: Household has a diabetic elder. Triggers ADDON_DIABETIC.

- O_POSTPARTUM: Primary cook or household member is postpartum. Triggers ADDON_POSTPARTUM.

- O_FITNESS: A member follows a fitness-oriented diet. Triggers ADDON_FITNESS.

- O_FASTING: A member observes regular fasting. Triggers ADDON_FASTING.

**Relationship to Household Members:** Overlays are derived from Household Member segments. When a member with segment = INFANT is added, the O_INFANT overlay is applied automatically. Overlays are managed by the RE, not set manually.

**Stored as:** overlay_persona_ids[] — an array of overlay references on the user's RE state. Can be empty.

### Entity 13: Confidence Score

**What it is:** A number between 0.0 and 1.0 that represents how well the RE knows this user's food preferences. Higher confidence means more personalised recommendations. Lower confidence means the RE is relying more on cohort-level research data.

**When it starts:** Computed at the end of onboarding (OB-08b). Starting value: 0.40 (minimum) to 0.65 (maximum), determined by how completely the user answered onboarding questions.

**Contributions at onboarding:**

- All 8 questions answered: contributes to reaching 0.65

- Home state captured: +0.15

- Diet type captured: +0.10

- Current city overlay found: +0.08

- Cook capability captured: +0.07

- Class preference swipes completed (OB-07): +0.12

- Context signals always available: +0.08

- Each non-critical field skipped: −0.05

- Diet type skipped: −0.15

- OB-03 (home state + city) skipped entirely: −0.08

**How it evolves:** Confidence increases as interaction_count grows. At 14+ interactions, cold start exits and confidence accelerates toward 1.0 as personal history becomes the dominant scoring signal.

**When shown to user:** The app shows a "Still learning your taste" badge when confidence < 0.30. Not otherwise displayed numerically.

### Entity 14: Cold Start State

**What it is:** A boolean condition that is TRUE for a user until they have accumulated enough interaction signals for personal learning to be meaningful. During Cold Start, the RE relies primarily on cohort-level research data (CohortPrior) and less on personal history.

**Entry condition:** All new users start in Cold Start (cold_start_mode = true).

**Exit condition:** interaction_count >= 14 triggers cold_start_mode = false. The weight ladder begins shifting from cohort-dominant to history-dominant.

**What counts toward interaction_count:**

- OB-07 class preference swipes: each card swiped = 1 interaction (max 10 from onboarding)

- Post-onboarding events: dish_accepted, dish_never, dish_not_today, dish_swiped_past, dish_cooked, dish_rated, dish_locked

**De-duplication rule for OB-07 swipes:** If a user re-opens OB-07 or the same class is swiped more than once, only the most recent swipe per class counts toward interaction_count. Duplicate swipes of the same class do not inflate the count.

**Weight for OB-07 swipes:** 0.30 (weaker than post-onboarding dish_accepted at 0.40, because preference declaration is a weaker signal than observed cooking behaviour).

## Part 4 — Content Domain

### Entity 15: Dish

**What it is:** A specific Indian dish. The most important content entity. 500+ dishes must be fully tagged before launch (DOC-04 NFR). A dish is what gets recommended. Everything else in the content domain exists to characterise dishes for the RE.

**Key attributes:**

- Name (display): in English, Hindi, and regional language where applicable

- Meal occasion: when this dish can be served (breakfast, lunch, dinner, snack, any)

- Diet type: derived from ingredients (never manually set)

- Is Jain: derived from ingredients (never manually set)

- Allergen flags: derived from ingredients (never manually set)

- Active flag: soft delete. is_active=false removes dish from RE without deletion

- Is Indian only: true for all dishes. Non-Indian dishes excluded from the MVP dish pool.

- Popularity score: updated daily by CRON from suggestion_logs

**Three types of dish that must be distinguished:**

- **Standard dish:** a single dish with no parent and no combo membership. E.g., Poha, Khichdi.

- **Dish variant:** a regional or dietary variant of a parent dish. Has parent_dish_id set. E.g., "Paneer Butter Masala (Jain)" is a child of "Paneer Butter Masala." Never-listing the parent does NOT automatically exclude variants. RE boosts variants for matching regional profiles.

- **Combo component:** a dish that is part of one or more Combos. E.g., Chole is a component in "Chole Bhature" combo.

**Relationships:**

- Belongs to 0 or 1 parent Dish (variant relationship)

- Has many Dish Ingredients

- Has many Genome Tags (via dish_tags junction)

- Is a candidate in 1 or more Meal Classes (via class_dish_options junction)

- Can be part of 0 or more Dish Combos (via dish_combo_items junction)

- Appears in many Interaction Events

- Appears in many Suggestion Logs

### Entity 16: Food DNA / Meal Genome

**What it is:** The multi-dimensional characterisation of a dish. Not a stored table — the Genome is the collective set of Genome Tags applied to a dish. The Genome enables the RE to compute how well a dish matches a user's taste preferences (ContentMatch signal).

**Implementation:** Stored as a tag junction (dish_tags table), not as columns on the dish. This is a deliberate architectural decision: adding a new genome dimension requires inserting a row in the tags master table, not a schema migration.

**Three tiers of genome tags:**

- **Tier 1 (mandatory before launch):** meal_occasion, diet_type, allergens, spice_level, cook_time_band, difficulty, calorie_band. All 500 dishes must have Tier-1 tags before launch.

- **Tier 2 (enrichment):** texture, cooking_method, comfort_warmth_score, weather_affinity, seasonal_affinity, protein_level, main_ingredient_class, regional_origin, primary_taste. Improves ContentMatch quality.

- **Tier 3 (future ML):** combo_pairing_affinity, regional_microvariant, festival_relevance, dietary_subcategory. Not required at MVP.

**Confidence on tags:** Each dish_tags row has a confidence float. 1.0 = human-verified. 0.85 = AI-tagged. The RE can weight tags differently based on confidence.

### Entity 17: Genome Tag

**What it is:** A single descriptor within the Food DNA of a dish. A Genome Tag has a name, a value, a tier, and whether it is shown to users.

**Examples:**

- Tag: spice_level, Value: high, Tier: 1, User-facing: yes ("Spicy")

- Tag: cooking_method, Value: steamed, Tier: 2, User-facing: no

- Tag: weather_affinity, Value: rainy, Tier: 2, User-facing: no

- Tag: regional_origin, Value: south_indian, Tier: 2, User-facing: yes ("South Indian")

- Tag: comfort_warmth_score, Value: 4, Tier: 2, User-facing: no

**User Taste Vector relationship:** The Taste Vector stores per-user weights for genome tags. When a user consistently accepts dishes with cooking_method=steamed, their genome_tag_affinity for steamed increases. ContentMatch = cosine similarity between the user's tag affinity vector and the dish's tag vector.

### Entity 18: Ingredient

**What it is:** A food component used in one or more dishes. Ingredients are the ground truth for allergen and dietary classification. A dish's diet type, Jain compatibility, and allergen flags are all derived from its ingredients.

**Key attributes:**

- Name

- Allergen flags: bitfield. Which allergens this ingredient triggers.

- Is Jain excluded: boolean. True for onion, garlic, potato, carrot, beetroot, and other root vegetables.

- Is veg: boolean.

- Is vegan: boolean.

- Can substitute: reference to another ingredient that can replace this one (Food Graph substitution edge).

- Seasonal peak: when this ingredient is freshest and most available.

**Auto-derivation rule:** When ingredients are linked to a dish (or modified), the system must automatically recompute:

- dish.allergen_flags = UNION of all ingredient allergen_flags

- dish.diet_type = if ANY ingredient is_veg=false → non_veg; if ANY ingredient is egg (allergen bit 4) and is_veg → egg; if ALL ingredients are_vegan → vegan; else → veg

- dish.is_jain = if ALL ingredients is_jain_excluded=false AND diet_type=veg → true; else → false

This derivation is non-negotiable. Manual setting of these fields on dishes is a disallowed operation.

### Entity 19: Dish Combo

**What it is:** A meal that is presented and served as a single unit composed of two or more dishes. A combo is a first-class content entity — it can be recommended as a whole, not just its components separately.

**Examples:** Chole Bhature (Chole + Bhature), Rajma Chawal (Rajma + Chawal), Idli Sambar (Idli + Sambar + Coconut Chutney).

**Combo types:**

- inseparable: Components are always served together. Bhature without Chole is not a complete meal. E.g., Chole Bhature.

- base_with_sides: A main dish with standard accompaniments where the sides can vary. E.g., Rajma Chawal — the Chawal can be swapped for Roti.

- thali: A complete meal with multiple components served together. E.g., South Indian Thali.

**Swappable components:** Some components of a combo can be swapped by the user in the carousel. E.g., in Rajma Chawal, the Chawal component can be swapped for Roti or Paratha. This swap is presented via the C-08 bottom sheet. The Rajma component is not swappable.

**Relationships:**

- Has 2 to N Combo Items (via dish_combo_items junction)

- Each Combo Item has: role (primary / side / accompaniment), is_default (boolean), is_swappable (boolean), sort_order

## Part 5 — Classification Domain

### Entity 20: Meal Class

**What it is:** A category of meal that defines what TYPE of food fills a plan slot. The Meal Class is selected first, then dishes are expanded from within that class. This is the "class-first" principle that distinguishes FooFoo's RE from simpler recommendation systems.

**Why it matters:** By selecting a class first, the RE ensures nutritional balance and cultural variety across a week. A household doesn't just get "popular dishes" — they get a structured plan where breakfast is light grain on Tuesday, stuffed flatbread on Saturday, and eggs on Sunday, because that is what their cohort's research data shows works.

**131 total classes (26 conceptual, 131 actual rows):** The 26 conceptual class codes describe the taxonomy. The actual database table has 131 rows because each conceptual class has variants for diet types, day types, and regional specificity.

**Three Planning Roles — the most important attribute of a Meal Class:**

- MAIN_PRIMARY: Can be assigned to a primary breakfast, lunch, or dinner slot.

- ADDON_ONLY_NOT_PRIMARY: Can only be used for member add-on slots. Must never appear in a primary slot. 13 classes have this role.

- COMBO_TEMPLATE_NOT_PRIMARY: Resolves to a Dish Combo. Not directly assigned as a slot — the planner resolves it to a combo object.

**Other key attributes:**

- Slot: which meal occasion this class fits (breakfast, lunch, dinner, addon)

- Day type: weekday, weekend, or any — used to bias class selection by day

- Weekday fit score (1–5): how appropriate this class is on weekdays

- Weekend fit score (1–5): how appropriate on weekends

- Variety cooldown days: minimum days before this class repeats in the same slot

- Max per week: variety guard cap

- Diet type: which dietary profile this class serves

- Cuisine family: used for 5-day cuisine variety window tracking

### Entity 21: Class-Dish Option

**What it is:** The relationship between a Meal Class and a candidate Dish. This is a many-to-many relationship — a dish can be a candidate for multiple classes, and a class has many candidate dishes.

**Why it matters:** This junction is how the RE expands from a class to dish candidates. When the plan says "Tuesday breakfast = BF_LIGHT_GRAIN", the RE queries all dishes linked to BF_LIGHT_GRAIN in this junction and then applies scoring and filtering.

**Key attributes:**

- Meal class code

- Dish ID

- Base score: the research-based starting score for this dish in this class (0.0–1.0)

- Is primary candidate: true if this dish is a signature candidate for this class (vs a secondary option)

**Approximate scale:** ~1,050 rows across all classes and dishes.

### Entity 22: Meal Occasion

**What it is:** The time-of-day appropriateness of a dish. Distinct from Meal Class. Meal Occasion is a property of the dish (when it can be served). Meal Class is a RE planning concept (what type of meal fills a slot).

**Values:** breakfast, lunch, dinner, snack, any

**Example distinction:** Poha has meal_occasion = breakfast. BF_LIGHT_GRAIN is the Meal Class. Poha appears in BF_LIGHT_GRAIN and also potentially in LUNCH_LIGHT_SALAD_SNACK (as a light lunch option). Both relationships exist in the Class-Dish Options junction.

## Part 6 — Planning Domain

### Entity 23: Week Plan

**What it is:** A 7-day meal plan for a Household. Contains 21 primary Plan Slots (7 days × 3 meal slots) plus any add-on slots for household members. There is exactly one active Week Plan per household per calendar week.

**Key attributes:**

- Profile ID: which household this plan belongs to

- Week start date: always Monday (IST)

- RE version: which version of the algorithm generated this plan

- Is locked: whether the entire week has been locked by the user

**Lifecycle:** Generated on Sunday evening for the coming week (pre-computation via CRON) OR on demand when the user opens the app on Monday. Individual slots can be refreshed (if not locked). The week plan expires at week end and is replaced by the next week's plan.

**Relationships:**

- Belongs to 1 User

- Contains 21 Plan Slots

- Contains 0 to N Add-on Slots (one per member per primary slot per day)

### Entity 24: Plan Slot

**What it is:** A single meal occasion on a specific date within a Week Plan. Each slot has one assigned Meal Class, a Slate of 8 candidate dishes, optionally one selected dish, a lock state, and add-on slots if household members require them.

**Key attributes:**

- Week plan ID: parent plan

- Slot date: the specific IST date

- Meal slot: breakfast, lunch, or dinner

- Class code: the Meal Class assigned to this slot by the class plan generator

- Selected dish ID: the dish the user has chosen (null until user selects or locks one)

- Is locked: user has locked this slot, protecting it from refresh

- Locked at: timestamp

- Slate dish IDs: the 8 ranked candidates generated by the RE

- Slate reasons: the primary reason code per dish in the slate (stored at generation time)

- Slate confidence: RE confidence at time of generation

- Slate generated at: timestamp

- Cold start mode: was cold start active at generation time

**States a slot can be in:**

- **Generated, unlocked:** Slate exists. No dish selected. Visible to user. Can be refreshed.

- **Selected, unlocked:** User has selected a dish from the carousel. Can still be refreshed (selection cleared on refresh).

- **Locked:** User has explicitly locked this slot. Refresh does not touch this slot. Selection persists.

### Entity 25: Slate

**What it is:** The ranked list of 8 candidate Dish alternatives for a specific Plan Slot. The first dish in the slate is the "headline" suggestion shown on the meal card. The remaining 7 are accessible via the swap carousel (C-02).

**Not a stored table:** The Slate is not a separate table. It is stored as slate_dish_ids uuid[] on the Plan Slot, plus slate_reasons jsonb for reason codes. The full ranking is represented by the order of IDs in the array.

**Generation process (high level):**

- Get class candidates from Class-Dish Options for the assigned class

- Apply all hard constraint filters (diet, allergen, Jain, never list, household member allergens)

- Score all surviving candidates using FinalScore formula

- Apply MMR variety algorithm to produce a diverse 8-item ranking

- Attach reason code to each ranked dish (primary scoring signal)

- Store as slate_dish_ids[] on Plan Slot

**RE Reason in the Slate:** Each of the 8 dishes in the Slate has an associated reason code stored at generation time. Reason codes map to labels shown in the carousel:

- regional_favourite → "Regional favourite"

- personal_taste → "Based on your taste"

- quick_cook → "Quick cook"

- context_fit → "Perfect for today's weather"

- cohort_match → "Loved by families like yours"

- exploration → "Try something new"

Storing at generation time (not computing at display time) ensures the reason is accurate to the conditions when the plan was made, and survives even if context or taste vectors change before the user views it.

### Entity 26: Add-on Slot

**What it is:** A member-specific additional meal component attached to a primary Plan Slot. Generated by generate_addons() based on Household Member segments. An add-on is always additional to the primary household meal — it never replaces or modifies it.

**Critical architectural distinction:** The postpartum overlay generates a postpartum add-on alongside the family meal. The family meal is unchanged. This is the exact distinction that makes FooFoo different from apps that convert a user's entire diet into a medical plan.

**Key attributes:**

- Parent plan slot ID

- Member name (display only)

- Addon class code: one of the 24 ADDON_* classes

- Dish ID: the specific add-on dish selected for this slot

- Addon slot date and meal slot (mirrors parent)

**Not swipeable:** Add-on rows in the UI (C-10) do not have carousel alternatives. The add-on dish is assigned by the RE, not user-selectable in V1 MVP.

### Entity 27: Plan Refresh

**What it is:** The action of regenerating all unlocked Plan Slots in the current Week Plan. Triggered by pull-to-refresh gesture on the Day View (H-01).

**Rules:**

- Locked slots are completely unaffected

- Unlocked slots get new slates generated with fresh RE scoring

- If a slot had a selected-but-unlocked dish, the selection is cleared on refresh

- Refresh does not change the Meal Class assignment for a slot (the class plan is stable for the week)

- Refresh generates new dish candidates within the same class

### Entity 28: Onboarding Session

**What it is:** The initial profile setup process. A series of screens (OB-00 through OB-08b) that capture household signals. Raw answers are stored per screen for debugging and possible future replay.

**Screens and what they capture:**

- OB-00: Conversational intro. No data captured.

- OB-01: Main Cohort selection. Captures: main_cohort_code.

- OB-02: Dynamic branch (depends on OB-01). Captures: sub_cohort signals (children ages, elder presence, health conditions).

- OB-03: Regional Identity. Captures: home_state, current_city, migration_duration.

- OB-04: Diet Type. Captures: diet_type, religious_pref.

- OB-05: Allergen exclusion. Captures: allergen_flags (via ingredient autocomplete).

- OB-06: Cook Capability. Captures: cook_capability.

- OB-07: Class Preference Swipes. Captures: class_preference_swipes[] (YES/NOPE per dish card). Generates Interaction Events (event_type = onboarding_class_preference).

- OB-08b: Plan Preview. Shows the first generated plan. User can interact (swap, lock, never). Interactions from OB-08b are valid Interaction Events.

**Completion:** Onboarding is considered complete when the user taps "Looks good — let's go!" on OB-08b. At this point: assign_persona() has run, first plan is generated, onboarding_completed = true on profile.

## Part 7 — Interaction Domain

### Entity 29: Interaction Event

**What it is:** A record of any user action that has meaning to the RE. Interaction Events are the raw data from which the RE learns user preferences over time. They are append-only — never modified or deleted (except under DPDP data deletion requests).

**Event types and their RE meaning:**

| **Event type** | **RE meaning** | **Updates** |
| --- | --- | --- |
| dish_accepted | User selected this dish from the carousel | Positive signal for dish and its classes/tags |
| dish_locked | User locked a slot (strongest positive signal) | Strong positive for dish, class, and tags |
| dish_cooked | User tapped "Cook This" | Strong positive — confirmed intent to cook |
| dish_ordered | User tapped "Order Instead" (Phase TBD) | Positive signal, lower weight than cooked |
| dish_rated | User gave an explicit star rating (1–5) | Calibrated signal based on rating value |
| dish_never | User confirmed Never gesture | Strong permanent negative. Triggers never_list addition. |
| dish_not_today | User confirmed Not Today | Temporary negative. Triggers not_today_suppression. |
| dish_swiped_past | User scrolled past a dish in carousel without selecting | Mild negative signal |
| onboarding_class_preference | OB-07 YES/NOPE swipe. Targets a Meal Class, not a dish. | Class-level affinity signal |
| plan_opened | User opened the day's plan | App engagement signal. No RE learning. |
| session_depth | How many dishes the user viewed in a session | App engagement signal. No RE learning. |

**Key attributes:**

- Profile ID

- Event type

- Dish ID (null for plan_opened, session_depth, onboarding_class_preference when no dish shown)

- Class code (for class_preference swipes and for dish events, derived from the dish)

- Meal slot

- Slot date

- Rank at interaction: where in the slate the dish appeared (1–8). Used for MRR metric.

- Time viewed in milliseconds: how long the dish card was visible before action

- Rating: 1–5, only for dish_rated events

- Context snapshot: weather, season, day at time of event

- RE version active at event time

- Confidence at time of event

- Occurred at: timestamp

- Synced to RE: false until async processor updates taste vectors

### Entity 30: Never List

**What it is:** A permanent per-user record of dishes the user has rejected forever. A dish on the Never List is excluded from candidate generation for all future Plan Slots. It is not a preference — it is a hard constraint equivalent to allergen exclusion in its effect on the RE pipeline.

**Key attributes:**

- Profile ID

- Dish ID

- Nevered at: timestamp

- Seasonal reactivation eligible: true if the dish has strong seasonal affinity (candidate for seasonal re-surface)

- Festival reactivation eligible: true if the dish has festival relevance tags

- Last reactivation check: when the RE last evaluated this dish for reactivation

- Reactivated count: how many times the dish has been re-surfaced

- Is active: false if the user removes the dish from their Never List

**Reactivation rules:**

- Never dishes do NOT automatically return after a time period

- Seasonal reactivation: if seasonal_reactivation_eligible=true AND dish's seasonal_affinity matches current season AND >6 months since nevered → RE surfaces a soft prompt ("It's monsoon season — want to try [dish] again?"). User must actively confirm.

- Festival reactivation: if festival_reactivation_eligible=true AND approaching matching festival AND >90 days since nevered → similar soft prompt.

**Invariant:** A never-listed dish with is_active=true is NEVER included in any Slate generation under any conditions. No scoring pathway, no context override, no festival override bypasses this. Only user reactivation restores it.

### Entity 31: Not Today Suppression

**What it is:** A time-decaying penalty applied to a dish after the user triggers "Not Today." Unlike Never, Not Today is temporary — the dish gradually returns to the candidate pool as the penalty decays.

**Decay formula:** Penalty(t) = P0 × e^(−λ × t)

- P0 = 0.80 (initial penalty — dish is strongly suppressed immediately)

- λ = 0.35 (decay rate — penalty halves approximately every 2 days)

- t = days elapsed since Not Today gesture

**Penalty values at specific days:**

- Day 0: 0.80 (strong suppression)

- Day 2: ~0.40 (moderate)

- Day 5: ~0.12 (mild)

- Day 7: ~0.05 (effectively gone, dish returns to normal pool)

**Context override:** A strong ContextFit score (>0.90) can partially override a decayed penalty after Day 3. Override reduces the remaining penalty by 50%. Example: a comfort food was Not Today'd 4 days ago, but today is rainy and cold — the context boost can still surface it if the fit is strong.

**Key attributes:**

- Profile ID + Dish ID (composite primary key)

- Suppressed at: timestamp

- P0: initial penalty (always 0.80 in V1 — configurable later)

- Lambda: decay rate (always 0.35 in V1 — configurable later)

- Effective until: approximate Day 7 from suppressed_at

- Is active: false once penalty < 0.05

### Entity 32: Variety Window State

**What it is:** A per-user rolling window that tracks recent plan history to enforce variety rules. The RE checks this before generating any slate to ensure the plan does not become repetitive.

**Variety rules enforced:**

- Same dish: no repeat within 30 days (unless user explicitly locked it)

- Same Meal Class (in same slot): max 3 times per week for breakfast/lunch; max 2 times per week for dinner

- Same cuisine family: max 2 of same cuisine family in breakfast or dinner over any 5-day window

- Same cooking method: max 3 fried dishes per week (4 in monsoon season)

- Back-to-back same main ingredient: prevented (no Paneer at both lunch and dinner on same day)

**Key attributes:**

- Profile ID

- Last 7 class codes per slot (rolling)

- Last 7 cuisine families (rolling)

- Last 7 cooking methods (rolling)

- Last 30 dish IDs (rolling)

- Fried count this week

- Monsoon override active

### Entity 33: Class Preference Swipe

**What it is:** A special type of Interaction Event generated during OB-07 onboarding. Unlike post-onboarding events that target a specific dish, a class preference swipe targets a Meal Class (the dish shown is a representative of that class, not the target itself).

**Signal type:** Class-level affinity signal. YES swipe → class_affinity[class_code] +0.30 (onboarding weight). NOPE swipe → class_affinity[class_code] −0.30.

**De-duplication:** If the same class is swiped more than once, only the most recent swipe counts. Earlier swipes for the same class are ignored.

**Contribution to interaction_count:** Each card swiped = 1. Maximum 10 from OB-07 (10 cards shown). A user who completes all 10 swipes enters the app with interaction_count = 10.

**Stored as:** event_type = 'onboarding_class_preference' in interaction_events. The dish_id field references the dish shown as a class representative. The class_code field records which class was targeted.

## Part 8 — Recommendation Engine Domain

### Entity 34: FinalScore

**What it is:** The numeric score computed for each candidate dish in a Recommendation Request. Dishes are ranked by their FinalScore to produce the Slate.

**Formula:**

FinalScore = (w_cohort × CohortPrior)

           + (w_content × ContentMatch)

           + (w_history × PersonalHistory)

           + (w_context × ContextFit)

           + (w_explore × ExplorationBonus)

           - PenaltyTerms

**This formula is only applied to dishes that have passed ALL hard constraint filters.** Hard constraints run before scoring. No dish violating a hard constraint is ever scored.

**FinalScore is not stored.** It is computed at slate generation time and discarded after ranking. The ranked slate (dish IDs in order) is what gets stored.

### Entity 35: Scoring Signal (CohortPrior)

**What it is:** A research-based acceptance rate for the combination of (user's cohort) and (dish's meal class). Answers the question: "How likely is a household like this to accept a dish like this?"

**Source:** Pre-computed from the research database. Stored in a cohort_class_priors table: (cohort_id, class_code) → acceptance_rate_prior (float 0–1).

**Weight:** w_cohort at Day 0 = 0.55. Decreases as personal history accumulates.

### Entity 36: Scoring Signal (ContentMatch)

**What it is:** The cosine similarity between the user's Taste Vector and the dish's Genome Vector. Measures how well the dish's food DNA matches what the user has shown they like.

**Computation:** CosineSimilarity(user.genome_tag_affinity, dish.genome_vector)

**Dish genome vector:** The dish's tags assembled as a numeric vector across the ~20 dimensions. Stored as a pre-computed float array on the dish (dish.genome_vector) for query efficiency. Updated when dish tags change.

**Weight:** w_content = 0.20 (stable across most tiers — content match is consistently useful).

### Entity 37: Scoring Signal (PersonalHistory)

**What it is:** A weighted, time-decayed sum of the user's prior interactions with this specific dish. Captures what the user has told the system through their behaviour.

**Formula:** PersonalHistory = Σ(event_weight × e^(−λ_history × days_elapsed)) for all events on this dish

**Event weights (proposed, to be finalised in Business Logic Specification):**

- dish_cooked: +0.80

- dish_locked: +0.60

- dish_accepted: +0.40

- dish_rated (5 stars): +0.60 (3 stars: 0.00, 1 star: −0.30)

- dish_swiped_past: −0.10

- dish_not_today: −0.30 (separate from Not Today decay penalty)

- dish_never: −1.00 (this dish should be on the never list — PersonalHistory check is a secondary guard)

**Time decay:** λ_history = 0.05 (slow decay — preference signals are relatively stable)

**Weight:** w_history = 0.00 at Day 0, rising to 0.65 at Day 60+ as cold start exits.

### Entity 38: Scoring Signal (ContextFit)

**What it is:** A multiplier reflecting how well the dish fits the situational context at plan generation time. Context includes weather, season, day of week, time of day.

**Computation:** Σ(context_tag_multiplier × dish_genome_affinity_for_that_tag) across active context dimensions

**Example:** On a rainy day, dishes with weather_affinity=rainy get multiplier 1.2×. Comfort food dishes (comfort_warmth_score ≥ 4) get multiplier 1.15×.

**Range:** 0 to 1.2 (can exceed 1.0 — a perfectly contextually appropriate dish gets boosted beyond the base score).

**Weight:** w_context = 0.15 (stable across all tiers — context is always relevant).

### Entity 39: Scoring Signal (ExplorationBonus)

**What it is:** A Thompson Sampling draw from a Beta distribution per dish. Encourages the RE to surface dishes the user has not tried yet, preventing the recommendation pool from collapsing to the same familiar dishes.

**Formula:** ExplorationBonus = draw from Beta(α_dish, β_dish)

- Initial state: Beta(1, 1) adjusted to cohort base acceptance rates

- α incremented on accept/lock/cook

- β incremented on swiped-past/not-today

**Range:** 0 to 0.15

**Weight:** w_explore = 0.10 at Day 0, decreasing to 0.00 at Day 60+ as personal history takes over discovery.

### Entity 40: Penalty Terms

**What it is:** Deductions from FinalScore for suppression and variety violations.

**Components:**

- **Not Today decay penalty:** computed from not_today_suppression table if an active suppression exists. Penalty(t) = P0 × e^(−λ × t). Subtracted directly from FinalScore.

- **Variety penalty:** deduction applied to dishes that would violate variety window rules. Computed via MMR algorithm (post-scoring re-ranking step). Applied as a composite penalty: (1 − λ_mmr) × max_similarity_to_selected_dishes.

### Entity 41: Weight Ladder

**What it is:** The mechanism that shifts scoring weights from cohort-dominated (new user) to history-dominated (mature user) as the user's interaction count grows.

**Five tiers:**

| **Tier** | **interaction_count** | **w_cohort** | **w_content** | **w_history** | **w_context** | **w_explore** |
| --- | --- | --- | --- | --- | --- | --- |
| Cold Start | 0 | 0.55 | 0.20 | 0.00 | 0.15 | 0.10 |
| Early | 1–10 | 0.35 | 0.25 | 0.15 | 0.15 | 0.10 |
| Emerging | 11–50 | 0.20 | 0.25 | 0.35 | 0.15 | 0.05 |
| Established | 51–150 | 0.10 | 0.20 | 0.50 | 0.15 | 0.05 |
| Mature | 150+ | 0.05 | 0.15 | 0.65 | 0.15 | 0.00 |

**Critical rule:** Weights are NOT applied in hard tier steps. They are linearly interpolated based on the exact interaction_count between tier boundaries. No jarring transitions.

**Per-user:** Weight ladder values are computed per user at slate generation time from their current interaction_count. They are not stored as static values.

### Entity 42: Taste Vector

**What it is:** A per-user learned representation of food preferences. Has two components: class_affinity (per Meal Class weights) and genome_tag_affinity (per genome tag weights). Updated after each interaction event is processed.

**Class affinity:** {class_code: weight_float}. Updated when:

- OB-07 class preference swipe (YES or NOPE)

- 3+ Never gestures from the same class → class_affinity[class] reduced by defined delta

**Genome tag affinity:** {tag_name: weight_float}. Updated when:

- dish_accepted/locked/cooked: positive boost to all Tier-1 and Tier-2 tags of the accepted dish

- dish_swiped_past: mild negative to the dish's most prominent tags

**Processing:** Events are not processed synchronously. They are flagged (synced_to_re=false) and processed by an async worker every 15 minutes. After processing, synced_to_re=true.

## Part 9 — Context Domain

### Entity 43: Context

**What it is:** The set of situational signals active at plan generation time. Context is always computed server-side from external data sources and system time. The user never manually inputs context (except Mood Selector in Phase 1, which is out of scope for MVP).

**Components:**

- Weather Condition (derived from weather API + temperature band)

- Season (derived from current month + city)

- Day of week

- Is weekend (boolean)

- Time of day (morning, afternoon, evening)

- Festival proximity (within 21 days of a festival? Which one?)

**Context is logged** in the context_log table per slate generation (linked by slate_id). This is the feature store from Day 1 for future ML use.

### Entity 44: Weather Condition

**What it is:** A classification of current weather derived from temperature and precipitation data. Maps to food affinity multipliers.

**Derivation:**

- Temperature < 15°C → cold

- Temperature 15–22°C → mild

- Temperature 22–30°C with rain → rainy

- Temperature 22–28°C no rain → mild

- Temperature > 30°C → hot

**Food affinity multipliers per condition:**

- rainy → comfort food +1.2×, fried food +1.15×, warm/soupy +1.15×, cold salads −0.85×

- hot → cold/refreshing dishes +1.15×, light grain +1.10×, heavy fried −0.80×

- cold → warm/heavy dishes +1.20×, comfort food +1.20×

- mild → neutral (1.0× for all)

These multipliers are stored in a config table (re_engine.weather_food_multipliers), not hardcoded.

### Entity 45: Season

**What it is:** The current Indian season, derived from the current month and the user's city.

**Seasons:**

- summer: March–May (most cities)

- monsoon: June–September

- post_monsoon: October–November

- winter: December–February

**Season affects:**

- Seasonal affinity tags on dishes (dishes tagged seasonal_affinity=monsoon get boosted in monsoon season)

- Monsoon override: max fried dishes per week increases from 3 to 4

### Entity 46: Weather Cache

**What it is:** A city-level cache of weather API data. Shared across all users in the same city on the same day. TTL: 12 hours.

**Why it exists:** The free tier of weather APIs has a call limit (OpenWeatherMap free tier: 1,000 calls/day). At 500 DAU in a single city, calling the API per recommendation request would exhaust the limit within hours. The cache prevents this.

**Key attributes:**

- City (text — primary key component)

- Date (primary key component)

- Temperature in Celsius

- Humidity percentage

- Condition (hot / rainy / cold / mild)

- Fetched at timestamp

- Expires at (fetched_at + 12 hours)

**Invariant:** Every RE recommendation request must check weather_cache before calling the weather API. If a valid cache entry exists, use it. Only call the API on cache miss.

### Entity 47: Festival

**What it is:** A cultural event with a date window that affects dish preferences. Dishes with matching festival_relevance tags are boosted during a pre-festival window of 21 days and during the festival itself.

**Phase 2 feature (F-45).** Festival awareness is out of scope for MVP. However, dishes must have festival_relevance tags applied to them now (content operation), so Phase 2 can activate festival boosting without a dish re-tagging exercise. The domain concept is registered here for forward compatibility.

**Key attributes:** festival_name, start_date, end_date, pre_boost_days (default 21)

## Part 10 — Operations Domain

### Entity 48: Safety Gate

**What it is:** A validation query that must return exactly zero rows before any meal plan is served and before any RE change is deployed. Safety Gates are the last line of defence against incorrect recommendations reaching users.

**Four Safety Gates:**

**Gate 1 — Diet violations:** Confirms no user is seeing dishes outside their dietary classification. Checks: veg users not seeing non-veg dishes; Jain users not seeing non-Jain dishes; vegan users not seeing non-vegan dishes.

**Gate 2 — Allergen violations (ingredient level):** Confirms no user (or household member) is seeing dishes containing their allergen ingredients. Note: This gate joins through dish_ingredients to ingredient allergen flags — NOT dish-level allergen flags. Dish-level flags may be stale if derivation pipeline hasn't run.

**Gate 3 — Jain religious violations:** Confirms no user with religious_pref=jain is seeing dishes where is_jain=false.

**Gate 4 — Planning role violations:** Confirms no ADDON_ONLY_NOT_PRIMARY or COMBO_TEMPLATE_NOT_PRIMARY class appears in a primary plan slot.

**When gates run:**

- After every RE-related migration

- After every batch update to dishes or ingredients

- Before every production deployment of a new RE version

- After every safety-critical content update

**Invariant:** All 4 gates must return 0 rows. Any non-zero result is a P0 release blocker. No exceptions.

### Entity 49: Seed Data

**What it is:** The pre-computed research database that powers cold-start recommendations. 15 reference tables with specific row counts that must all be seeded from Indian_Meal_Cohort_Persona_DB_v3.xlsx before any RE function can run.

**Seed gate sequence (dependency-ordered):** S-01: re_states (36 rows) → S-02: re_main_cohorts (5 rows) → S-03: re_personas (41 rows) → S-04: re_subcohorts (41 rows) → S-05: re_routing_rules (8 rows) → S-06: re_meal_classes (131 rows) → S-07: re_meal_class_overlap_rules (13 rows) → S-08: re_class_dish_options (1,050 rows) → S-09: re_addon_classes (24 rows) → S-10: re_addon_dish_options (142–143 rows) → S-11: re_cohorts (2,952–2,953 rows) → S-12: re_weekly_class_plans (20,664 rows) → S-13: re_household_addon_plans (7,992 rows) → S-14: re_nonveg_logic (36 rows) → S-15: re_city_migration_overlays (324 rows)

**Invariant:** Row counts in all 15 gates must match expected values exactly. Any count mismatch halts deployment.

### Entity 50: RE Engine Version

**What it is:** The specific version of the recommendation algorithm. Each user's profile records which RE version generated their current plan. The system globally tracks which version is active.

**Versions planned:** classfirst_v1 (MVP), classfirst_v2 (Sprint 6), classfirst_v3 (Phase 1), cluster_v1 (Phase 2), ltr_v1 (Phase 3).

**Shadow mode:** Every new RE version runs in shadow mode for 72 hours before promotion. Shadow mode computes recommendations in parallel without showing them to users. Metrics are compared. Promotion only if all metrics equal or better.

### Entity 51: Consent Record

**What it is:** A granular per-user record of agreement to specific data uses. Required by DPDP Act 2023. Must be captured at signup and retained for the lifetime of the account.

**Consent types:** analytics, push_notifications, personalization, data_retention

**Key attributes:** profile_id, consent_type, granted (boolean), granted_at, IP address (hashed), privacy policy version

**DPDP requirements:** Data export within 72 hours of request. Account deletion within 72 hours of request. Audit log retained for 3 years.

## Part 11 — Business Invariants

Rules that must be true at all times. If any invariant is violated, it is a P0 production incident.

**Invariant 1 — Diet safety:** A dish of diet_type ≠ veg must never appear in any Plan Slot for a user with diet_type = veg, jain, or vegan. Safety Gate 1.

**Invariant 2 — Jain safety:** A dish with is_jain = false must never appear in any Plan Slot for a user with religious_pref = jain. Safety Gate 3.

**Invariant 3 — Allergen safety (ingredient level):** Any dish whose ingredients include allergen flags matching any user or household member allergen flag must never appear in a Plan Slot for that household. Safety Gate 2. This check goes to ingredient level.

**Invariant 4 — Member allergen propagation:** Any allergen flag on any household member propagates to the primary plan candidate filter. A household member's allergen is treated as a household constraint, not a personal constraint.

**Invariant 5 — Planning role safety:** A Meal Class with planning_role = ADDON_ONLY_NOT_PRIMARY must never appear in a primary Plan Slot. Safety Gate 4.

**Invariant 6 — Auto-derivation supremacy:** diet_type, is_jain, and allergen_flags on a Dish are always derived from ingredient flags. Manual overrides are not permitted. The derivation pipeline is the only authorised writer of these fields.

**Invariant 7 — City overlay balance:** For any user, home_state_signature_weight + city_overlay_weight = 1.0 always.

**Invariant 8 — Persona visibility:** Persona IDs and sub-cohort codes are never exposed to the user via any API response or UI element. Users see only the 5 Main Cohort labels.

**Invariant 9 — Add-on independence:** A member Add-on Slot is always additional to the primary Plan Slot. It never replaces, modifies, or affects the primary household meal.

**Invariant 10 — Never list permanence:** A dish with a never_list entry where is_active = true is excluded from ALL candidate generation. No scoring, no context override, no festival override, no passage of time bypasses this exclusion.

**Invariant 11 — One plan per week:** A household has exactly one Week Plan per calendar week. Duplicate plans for the same week are not permitted.

**Invariant 12 — Hard constraints before scoring:** Hard constraint filtering must run before FinalScore computation. No dish violating any hard constraint is ever scored. This order is non-negotiable.

**Invariant 13 — Seed data completeness:** All 15 seed gates must pass with correct row counts before any RE function is deployed.

**Invariant 14 — Reason tag immutability:** The RE reason code stored with each slate entry at generation time is never retroactively updated. It reflects the reasoning at generation, not at display.

## Part 12 — Entity Lifecycles

### User / Profile lifecycle

Created at auth signup → Onboarding starts (OB-00) → Household members added (OB-02) → Regional identity captured (OB-03) → Diet and allergens captured (OB-04, OB-05) → Cook capability captured (OB-06) → Class preference swipes generate first Interaction Events (OB-07) → assign_persona() runs → Plan Preview generated (OB-08b) → onboarding_completed = true → cold_start_mode = true, interaction_count growing → interaction_count reaches 14 → cold_start_mode = false → Taste Vector evolves with each interaction → Profile persists indefinitely → Account deletion request → All personal data deleted within 72 hours (DPDP). Interaction event audit log retained for 3 years per DPDP.

### Week Plan lifecycle

Pre-generated on Sunday evening for the coming week (CRON) OR generated on demand on Monday → Contains 21 primary slots with slates → User views Day View → Interacts (swaps, locks, nevers, not-todays) → Unlocked slots can be refreshed (pull-to-refresh regenerates slates within same class) → Locked slots persist through week → Week ends → Plan archived (retained for history) → Next week's plan begins.

### Dish lifecycle

Content ops creates dish record → Ingredients linked via dish_ingredients junction → Auto-derivation pipeline runs → diet_type, is_jain, allergen_flags computed and written → Dish tagged with Genome Tags (Tier 1 mandatory before launch, Tier 2 enrichment) → Dish linked to Meal Classes via class_dish_options → Dish eligible for recommendation → User interactions logged → popularity_score updated daily by CRON → Dish may be Never'd by user (is_active remains true, never_list_cache entry created, dish excluded from that user's future slates) → Dish may be deactivated (is_active = false — removes from RE for all users without deletion) → Dish is never deleted from the database.

### Interaction Event lifecycle

User action occurs in UI → Frontend logs event to interaction_events (append-only) → synced_to_re = false → Async processor reads unsynced events every 15 minutes → Updates user_taste_vectors, class_affinity, not_today_suppression, or never_list as appropriate → synced_to_re = true → RE uses updated vectors in next slate generation → Events retained per DPDP retention rules.

### Never List entry lifecycle

User triggers swipe-left → Never button revealed → User taps Never → Confirmation bottom sheet shown (H-07: dish photo + "Remove forever / Cancel") → User confirms → never_list entry created (is_active = true) → Dish immediately excluded from all future slate generation for this user → Seasonal/festival eligibility assessed and stored → If eligible and conditions met (>6 months + matching season/festival) → RE generates soft re-surface prompt → User can confirm or dismiss → If dismissed: no change → If confirmed: is_active = false on never_list entry → Dish returns to candidate pool.

## Part 13 — Known exclusions and deferred concepts

**Temporary Dietary Override (Navratri, fasting periods):** Explicitly out of scope for MVP and current phase. A household may observe temporary dietary restrictions during festivals (e.g., strict vegetarian during Navratri, specific fasting rules). The domain concept is acknowledged here for forward compatibility. When this feature is in scope, it will require a new entity: Dietary Override with start_date, end_date, diet_constraints[], and affected_members[]. No schema support needed now, but new components must not conflict with introducing this concept later.

**Cooking Equipment constraints:** Out of scope for current phase. Future modelling would add an Equipment entity (hot_plate, kettle, oven, pressure_cooker, tawa, kadai) linked to dish requirements and user capabilities. No current schema or filtering logic needed.

**Joint cooking / who cooks per slot:** Out of scope for MVP. The system assumes the primary user is the sole cook for all slots. Future phases (F-36 Family Profiles) may introduce slot-level cook assignment. The Household entity is designed as a separate concept from User to enable this future expansion.

**Mood Selector (F-41):** Out of scope for MVP. Mood is a user-input context signal (happy, tired, celebratory, comfort-seeking). When in scope, it becomes a component of the Context entity.

**Multi-language support:** Dishes have name_hindi and name_regional fields planned. Full localisation is a future phase.

## Part 14 — Open decisions captured during CDM production

**Decision 1 — Genome vector representation:** The ContentMatch signal requires a cosine similarity computation between the user's genome_tag_affinity vector and a dish genome vector. The genome vector representation needs to be decided in the Business Logic Specification: pre-computed float array stored on the dish (faster queries, requires recomputation when tags change) versus assembled at query time from dish_tags (always current, slower). Decision deferred to DOC-P3-03.

**Decision 2 — PersonalHistory event weights:** The specific numeric weights for each interaction event type are referenced in this document as proposals (cook=0.80, lock=0.60, accept=0.40, etc.) but are not yet finalised. These must be specified in DOC-P3-03 as configuration values, not hardcoded constants.

**Decision 3 — assign_persona() mapping rules:** The inputs to assign_persona() are defined: main_cohort × sub_cohort × home_state × diet_type → persona_id. The actual mapping table (which combination maps to which of the 41 personas) must be defined in DOC-P3-03 and seeded from the research database.

## Document sign-off

| **Field** | **Value** |
| --- | --- |
| Document | DOC-P3-02 · Conceptual Domain Model |
| Version | 1.0 |
| Status | DRAFT — pending founder sign-off |
| Entities defined | 51 domain entities across 10 domain areas |
| Business invariants | 14 |
| Entity lifecycles | 4 key lifecycles |
| Known exclusions | 5 |
| Open decisions | 3 (carried forward to DOC-P3-03) |
| Next document | DOC-P3-03 · Business Logic and Algorithm Specification |
| Blocks | DOC-P3-03 · DOC-P3-04 · DOC-P3-05 |

Founder sign-off: ___________________________ Date: _______________

## ── Enhancement v1.1 ── Parts 15–19

*Added in response to founder review. Pure conceptual additions. No implementation details, algorithms, formulas, or schema.*

## Part 15 — Aggregate Roots and Ownership

An Aggregate is a cluster of domain concepts that belong together and are always changed as a unit. The Aggregate Root is the single entry point — no concept outside the aggregate holds a direct reference to anything inside it, except through the Root. This section defines ownership boundaries that will govern both business logic and data architecture.

### Aggregate 1: Household

**Root:** User (Profile)

**Owns:**

- Household Members (all members of this household)

- Dietary Configuration (Diet Type, Religious Preference, Allergen Flags — at household level)

- Regional Identity (Home State, Current City, Migration Duration, City Overlay Weight)

- Cook Capability

- Onboarding Session (the answers that defined this household)

- Consent Records (DPDP consents granted by this user)

- Push Notification Preferences

**Ownership boundary:** Nothing outside this aggregate holds a direct reference to Household Members. All access to a household's members goes through the User. The RE does not write to this aggregate — it reads from it. The only writers to this aggregate are the user (via profile editing) and the onboarding pipeline (at initial setup).

**Invariants enforced by this aggregate:**

- The combined allergen flag for the household is the UNION of User allergen flags and all Household Member allergen flags. This combined flag is always current.

- Diet Type and Religious Preference apply uniformly to every plan slot for this household. No individual plan slot can override the household's dietary classification.

- A Household Member's allergen flags immediately become part of the household constraint — there is no grace period or activation step.

- Only one onboarding session exists per user. Onboarding cannot be restarted from scratch; subsequent changes go through profile editing.

### Aggregate 2: RE Identity

**Root:** User RE State

**Owns:**

- Persona Assignment (base persona + overlay personas)

- Confidence Score

- Cold Start State (boolean + interaction count)

- Weight Ladder State (current weights — interpolated at runtime, not stored directly)

- Taste Vector (Class Affinity + Genome Tag Affinity)

**Ownership boundary:** This aggregate is strictly the RE's view of the user. The Household Aggregate owns who the user is. The RE Identity Aggregate owns what the RE knows about the user's preferences. These two aggregates are deliberately separated — the RE must never write to the Household Aggregate, and the Household identity must never be derived from RE state. The RE Identity is updated only by the RE processor. The app reads from it to display confidence signals but never writes to it directly.

**Invariants enforced by this aggregate:**

- The base persona always references one of the 41 valid personas from the seed data. No persona can be assigned that does not exist in the reference data.

- Confidence score is always between 0.0 and 1.0 inclusive.

- Cold Start State is always an accurate reflection of interaction count. When interaction_count crosses 14, cold_start_mode transitions to false. No other trigger changes this.

- Weights in the Weight Ladder always represent a coherent tier for the current interaction count. Stale weight states are not persisted.

### Aggregate 3: Dish Content

**Root:** Dish

**Owns:**

- Dish Ingredients (the ingredients that compose this dish — via junction)

- Genome Tags (the Food DNA dimensions applied to this dish — via junction)

- Combo Memberships (which combos this dish belongs to as a component — via junction)

**Ownership boundary:** Diet Type, Religious Compatibility (is_jain), and Allergen Flags on a dish are owned exclusively by the derivation pipeline. No other process may set these values. Dish Variants reference their parent via parent_dish_id but are independent dishes — they are not strictly owned by the parent. Never-listing a parent dish does not cascade to its variants.

**Invariants enforced by this aggregate:**

- diet_type, is_jain, and allergen_flags are always computed from Ingredients. Any direct write to these fields by non-derivation code is a violation.

- A Dish can only be deactivated (is_active = false), never deleted. Deactivation removes the dish from all future recommendation pools for all users.

- A Dish must have all Tier-1 Genome Tags applied before it is eligible for any Plan Slot. A dish with incomplete Tier-1 tagging is not a valid recommendation candidate.

- A Dish Variant does not inherit the Never-list status of its parent dish. They are independent content entities.

### Aggregate 4: Meal Plan

**Root:** Week Plan

**Owns:**

- Plan Slots (all 21 primary slots for the week)

- Add-on Slots (all member-specific add-ons for the week)

**Ownership boundary:** Plan Slots cannot exist without a Week Plan. The Week Plan owns the complete planning state for the week. External systems (the RE, the user) interact with the Week Plan through defined operations: generate, refresh, lock, select. No system directly mutates a Plan Slot without going through the Week Plan's rules. A Plan Slot's Slate and Reason Codes are immutable once stored.

**Invariants enforced by this aggregate:**

- Exactly one Week Plan exists per household per calendar week. Duplicate plans for the same week are not permitted.

- A Week Plan always contains exactly 21 primary Plan Slots (7 days × 3 meal occasions). Partial plans do not exist.

- A locked Plan Slot is immutable to all refresh operations. Lock state can only be changed by the user explicitly.

- Add-on Slots are always additional to primary Plan Slots. No Add-on Slot replaces or modifies the primary slot's dish.

- Slate Reason Codes stored at generation time are never retroactively updated. They remain as recorded at generation.

- The Meal Class assigned to a Plan Slot does not change within a week once the class plan is generated. Refresh generates new dish candidates within the same class.

### Aggregate 5: Interaction History

**Root:** User (as the anchor for all behavioral records)

**Owns:**

- Interaction Events (all user actions on dishes and plans)

- Never List (permanent dish exclusions)

- Not Today Suppression Records (temporary dish penalties)

- Variety Window State (rolling window of recent plan history)

**Ownership boundary:** Interaction Events are append-only. No process may modify or delete an event within its retention period. The RE processor reads events to update the RE Identity Aggregate — it does not modify the events themselves. The Never List and Not Today Suppression records are owned by this aggregate and updated based on specific Interaction Events (NeverApplied, NotTodayApplied events). External systems query this aggregate as read-only inputs to recommendation generation.

**Invariants enforced by this aggregate:**

- Interaction Events are never modified after creation. They are permanently append-only.

- A Never List entry where is_active = true is a permanent exclusion. No time-based expiry. No automatic reactivation. Only explicit user reactivation changes this.

- Not Today Suppression records are active until the penalty decays below the threshold (approximately Day 7) or the user selects that dish, at which point the suppression is resolved.

- Variety Window State always reflects the actual recent plan history. It is a materialized view of recent interactions, not a separate input.

### Aggregate 6: Reference Data

**Root:** Meal Class (representing the entire seed data corpus)

**Owns:**

- Meal Classes (131 rows — the taxonomy)

- Class-Dish Options (which dishes are candidates for each class)

- Main Cohorts (5 reference values)

- Personas (41 reference records)

- Cohort-State Matrix (2,952–2,953 rows)

- Weekly Class Plans (20,664 pre-computed rows)

- Add-on Plans (7,992 rows)

- Routing Rules (8 rows)

- State Profiles (36 rows)

- Non-Veg Logic (36 rows)

- City Migration Overlays (324 rows)

**Ownership boundary:** Reference Data is written only by the seeding pipeline before launch. Application logic never writes to this aggregate. All RE functions treat this data as read-only. Updates to reference data (e.g., adding a new meal class) are treated as seeding events, not application writes, and require full seed gate re-validation before deployment.

**Invariants enforced by this aggregate:**

- All 15 seed gates must pass with correct row counts before any RE function is deployed.

- The Planning Role of a Meal Class never changes at runtime. It is a seeded property.

- The Meal Class assigned to a Plan Slot must always be a valid MAIN_PRIMARY class from the seed data.

### Aggregate 7: Context

**Root:** Weather Cache Entry (keyed by city + date)

**Owns:**

- Weather condition for a specific city on a specific day

**Ownership boundary:** Context is assembled fresh per recommendation request. The Weather Cache is the only persisted piece of context — everything else (day of week, season, time of day, festival proximity) is derived from system time at request time. The Weather Cache is shared across all users in the same city — it is not user-specific. No user-level state is owned by this aggregate.

**Invariants enforced by this aggregate:**

- A Weather Cache entry is always checked before calling the external weather API. If a valid entry exists (not expired), it must be used. API calls are made only on cache miss.

- A Weather Cache entry expires after 12 hours. Expired entries must not be used.

- Context is logged per recommendation request in the context_log for ML feature store purposes. This log is append-only.

## Part 16 — Entity Responsibilities

Every entity has one job. This section makes that job explicit, along with what the entity must never be asked to do. This prevents responsibility creep — the source of most architectural confusion.

| **Entity** | **Why it exists** | **Business responsibility it owns** | **Must never be responsible for** |
| --- | --- | --- | --- |
| **User (Profile)** | To represent a household's identity and food context in the system | Owning who the household is — their food culture, dietary constraints, and cooking context | Owning RE scoring state, recommendation logic, or behavioral learning. Those belong to RE Identity. |
| **Household Member** | To capture special dietary needs of additional household members that modify the plan | Carrying the segment classification, allergen flags, and diet override for a specific non-primary member | Carrying a complete standalone meal plan. A member modifies the household plan — they do not have their own plan. |
| **Regional Identity** | To express the cultural duality of migrant households (food roots vs. current city influence) | Holding the home state, current city, migration duration, and the derived overlay weight | Making recommendation decisions. Regional Identity provides inputs; it does not determine outputs. |
| **Diet Type** | To declare the household's primary dietary classification as a hard constraint | Being the first and most absolute filter applied to every dish candidate | Acting as a preference or a score. Diet Type is a gate — either pass or fail. |
| **Allergen** | To identify food substances that must never reach any household member | Representing a safety constraint at ingredient level, propagated to the household level | Being a preference or a dislikes signal. Allergens are never soft signals — they are always hard exclusions. |
| **Main Cohort** | To classify household type in user-visible, plain-language terms | Providing the user-facing entry point to the cohort system during onboarding | Directly driving recommendation logic. Main Cohort feeds assign_persona(); it does not drive the RE itself. |
| **Persona** | To represent the RE's internal classification of a household for cold-start plan generation | Being the research-data anchor that connects a household to pre-computed food preference patterns | Being shown to the user in any form. Persona codes are internal identifiers. |
| **Confidence Score** | To quantify how well the RE knows this user's preferences | Signalling the balance between research-data reliance and personal learning | Controlling which dishes are shown. Confidence Score affects weight allocation; it does not filter candidates. |
| **Cold Start State** | To signal whether the RE has enough personal data to move beyond cohort-level defaults | Triggering the transition from cohort-dominated to history-dominated scoring | Defining the permanent quality of recommendations. Cold Start State is transient — it exits and never returns once the threshold is crossed. |
| **Dish** | To represent a specific Indian dish with all its intrinsic properties | Carrying the dish's physical and cultural characteristics — its genome, ingredients, dietary classification | Carrying any user-specific preference data. A dish does not know who likes it or who doesn't — that belongs to Taste Vector and Interaction History. |
| **Food DNA / Genome** | To characterise a dish along multiple dimensions so the RE can match it to users | Enabling content-based matching by representing a dish as a multi-dimensional vector | Storing user preference data. The Genome characterises the dish; the Taste Vector characterises the user. |
| **Meal Class** | To define what TYPE of meal should fill a plan slot, enabling structured planning | Classifying dishes by their role in a meal plan, enforcing variety and balance at the planning level | Storing user preferences or recommendation scores. Meal Class is a classification system, not a personalisation system. |
| **Week Plan** | To be the container for a household's complete meal decisions for one week | Owning the structure, state, and lifecycle of all slots and add-ons for one week | Owning dish content, scoring logic, or RE computation. The Week Plan holds results — it does not produce them. |
| **Plan Slot** | To represent one specific meal occasion in a plan with its current state | Carrying the class assignment, candidate slate, lock state, and selected dish for one meal on one day | Generating its own candidates or applying scoring. A slot receives its slate from the RE — it does not create it. |
| **Slate** | To hold the ranked set of 8 candidate dishes and their reasons for a slot | Providing the alternatives the user sees in the carousel, with traceability to the reasoning | Being regenerated on-the-fly for display. A Slate is generated once and stored. It reflects conditions at generation time. |
| **Add-on Slot** | To represent a member-specific additional component alongside a primary slot | Being the mechanism by which household member needs are served without disrupting the primary plan | Replacing or modifying the primary plan slot. An add-on is always additional — never a substitute. |
| **Interaction Event** | To record a user's action with full context for the RE learning loop | Being the permanent, immutable record of what the user did and when | Being interpreted at creation time. Interpretation is the RE processor's job. Events just record facts. |
| **Never List** | To enforce a user's permanent exclusion of a dish | Being the hard constraint boundary that no RE scoring can cross | Being a preference strength signal. Never is binary — either a dish is excluded or it is not. |
| **Not Today Suppression** | To apply a time-decaying penalty after a temporary rejection | Being the mechanism that temporarily reduces a dish's score without permanently excluding it | Being a permanent exclusion. Not Today always decays. After ~7 days, the dish is fully restored. |
| **Taste Vector** | To store the RE's learned model of a user's preferences across genome dimensions and meal classes | Being the persistent output of the RE learning loop — the accumulated preference signal | Being the raw interaction record. The Taste Vector is the interpreted, aggregated result of events — not the events themselves. |
| **FinalScore** | To rank candidate dishes within a slate | Being the single number that orders all surviving candidates for a slot | Being stored. FinalScore is a computation artifact. It exists during slate generation and is discarded once the slate is ranked and stored. |
| **Safety Gate** | To validate that no plan violates a hard constraint before it reaches the user | Being the last line of defence that catches any error in the recommendation pipeline | Being a performance optimisation or a recommendation quality metric. Safety Gates only check correctness — they do not improve quality. |
| **Weather Cache** | To share weather data across all users in a city without exhausting free-tier API limits | Being the shared, city-level buffer between the recommendation pipeline and the external weather API | Storing user-specific context. Weather Cache is city-level and date-level — never user-level. |
| **Consent Record** | To satisfy DPDP Act compliance by recording exactly what data uses the user has agreed to | Being the legal record of user agreement per data use category | Being a gating mechanism in the recommendation pipeline. Consent is a compliance record, not a real-time filter on recommendations. |

## Part 17 — Data Nature Classification

Every significant business concept in FooFoo falls into one of five data categories. This classification determines how the concept is stored, accessed, and maintained. It is the conceptual input to data architecture decisions.

**Five categories:**

- **Persisted:** Stored permanently in the database. Survives restarts. Requires explicit deletion.

- **Derived-Stored:** Computed from other persisted data and then stored. Updated when source data changes (via trigger or batch). The computed result is persisted for query efficiency.

- **Derived-Transient:** Computed on demand at runtime. Not stored. Discarded after use.

- **Cached:** Temporarily stored with a time-to-live. Used to avoid repeated expensive computation or external API calls. Recomputed on cache miss.

- **Seeded:** Populated from the research database before launch. Read-only from the application's perspective. Changes only via controlled seeding operations.

- **Session:** Exists only within a user interaction session or request. Not persisted beyond the request.

| **Concept** | **Category** | **Notes** |
| --- | --- | --- |
| User identity (name, email, auth state) | Persisted | Core record. DPDP deletion deletes this. |
| Diet Type (on User) | Persisted | Set by user at onboarding, editable in profile. |
| Allergen Flags (on User) | Persisted | Set by user. Combined household flag is Derived-Transient. |
| Home State | Persisted |  |
| Current City | Persisted |  |
| Migration Duration | Persisted | The 4-band selection. |
| City Overlay Weight | Derived-Stored | Computed from Migration Duration. Stored for RE use. Updated when Migration Duration changes. |
| Household Members (list) | Persisted | Soft-deleted (is_active flag). |
| Member Allergen Flags | Persisted |  |
| Combined Household Allergen Flags | Derived-Transient | Computed at query time from User + all Member flags. Never stored as a standalone value. |
| Persona Assignment (base persona_id) | Derived-Stored | Assigned by assign_persona() at onboarding. Stored on User RE State. |
| Overlay Personas (array) | Derived-Stored | Derived from Household Member segments. Stored on User RE State. |
| Confidence Score | Derived-Stored | Computed at onboarding end, updated as interactions accumulate. Stored on User RE State. |
| Cold Start State (boolean) | Derived-Stored | Derived from interaction_count crossing threshold. Stored on User RE State. |
| Interaction Count | Persisted | Incremented on each qualifying interaction event. |
| Taste Vector (class + genome affinity) | Derived-Stored | Derived from Interaction Events by async processor. Stored on User RE State. Updated every 15 minutes by CRON. |
| Dish identity (name, occasion, active flag) | Persisted | Core content record. Never deleted. |
| Diet Type (on Dish) | Derived-Stored | Auto-derived from Ingredients by trigger. Stored on Dish. |
| Is Jain (on Dish) | Derived-Stored | Auto-derived from Ingredients by trigger. Stored on Dish. |
| Allergen Flags (on Dish) | Derived-Stored | Auto-derived from Ingredients by trigger. Stored on Dish. |
| Dish Genome Tags (junction) | Persisted | Human or AI-tagged. Confidence score per tag. |
| Dish Genome Vector | Derived-Stored | Pre-computed float array from genome tags. Stored on Dish. Recomputed when tags change. Used for ContentMatch cosine similarity. |
| Dish Popularity Score | Derived-Stored | Computed daily from suggestion logs by CRON. Stored on Dish. |
| Dish Combo Structure | Persisted | Combo + Combo Items junction. |
| Ingredient Records | Persisted |  |
| Allergen Flags (on Ingredient) | Persisted | Ground truth for all allergen derivation. |
| Meal Class definitions | Seeded | 131 rows. Read-only at runtime. |
| Class-Dish Options | Seeded | 1,050 rows. Read-only at runtime. |
| Cohort-State Matrix | Seeded | 2,952–2,953 rows. Read-only at runtime. |
| Weekly Class Plans | Seeded | 20,664 rows. Read-only at runtime. |
| Week Plan | Persisted | Generated per week per household. |
| Plan Slot | Persisted | 21 per week plan. Includes slate dish IDs and reason codes. |
| Slate (dish IDs + reasons) | Persisted | Stored as arrays on Plan Slot. Generated once. Immutable after storage. |
| FinalScore | Derived-Transient | Computed per dish per request. Discarded after slate is ranked. |
| CohortPrior | Derived-Transient | Looked up from seeded cohort-class data at request time. Not stored per-request. |
| ContentMatch | Derived-Transient | Computed as cosine similarity at request time using stored genome vectors. |
| PersonalHistory | Derived-Transient | Computed from stored Taste Vector at request time. |
| ContextFit | Derived-Transient | Computed from Weather Condition + Dish genome tags at request time. |
| ExplorationBonus | Derived-Transient | Thompson Sampling draw at request time from stored α, β state. |
| Weight Ladder weights | Derived-Transient | Interpolated from interaction_count at request time. Never stored as explicit values. |
| Variety Penalty | Derived-Transient | Computed by MMR algorithm at slate generation time. Part of FinalScore computation. |
| Not Today Penalty | Derived-Transient | Computed from stored P0, λ, elapsed days at request time. |
| Interaction Events | Persisted | Append-only. DPDP audit log retained 3 years. |
| Never List entries | Persisted | Permanent until user reactivates. |
| Not Today Suppression records | Persisted | Active until penalty < threshold. Then marked inactive. |
| Variety Window State | Derived-Stored | Derived from recent Interaction Events. Stored as rolling window per user. Updated after each plan generation. |
| Bandit State (α, β per dish per user) | Persisted | Updated on each accept/reject interaction. Grows as user interacts. |
| Context (weather, season, day, time) | Session | Assembled per recommendation request. Not stored independently. Logged in context_log for ML. |
| Weather Condition | Cached | Derived from weather API per city per day. 12-hour TTL. |
| Context Log | Persisted | Append-only ML feature store. One record per recommendation request. |
| Suggestion Log | Persisted | Append-only. Every dish shown to every user. Safety gate source. |
| Onboarding Session Answers | Persisted | Raw per-screen answers stored for debugging. |
| Sub-cohort Tag | Session | Derived from OB-02 answers within the onboarding session. Input to assign_persona(). Not stored independently after persona is assigned. |
| RE Reason Code (per dish in slate) | Persisted | Stored at generation time as part of slate. Immutable. |
| RE Engine Version | Persisted | Tracked globally (active version) and per-user (which version generated their current plan). |
| Consent Records | Persisted | DPDP compliance. Retained for account lifetime. |
| Audit Log | Persisted | Append-only. 3-year DPDP retention. |
| Weather Cache | Cached | City + date keyed. 12-hour TTL. |
| Routing Rules | Seeded | 8 rows. Read-only at runtime. Drives dynamic onboarding. |

## Part 18 — Business Events Catalogue

A business event is something that happens in the domain that is meaningful to the system. Events are the signals that trigger state changes, start processes, or update other entities. The Business Logic Specification (P3-03) will define how each event is handled. Listed here for conceptual completeness.

### Onboarding Events

| **Event Name** | **Trigger** | **Source Entity** | **Affected Entities** | **Business Meaning** |
| --- | --- | --- | --- | --- |
| **OnboardingStarted** | User opens app for the first time after download | User | User, Onboarding Session | The household profile creation process begins |
| **MainCohortSelected** | User selects one of 5 household types at OB-01 | User | User RE State (sub-cohort routing begins), Onboarding Session | Main household type is known; OB-02 branching determined |
| **HouseholdMembersCapture** | User completes OB-02 dynamic branch questions | Onboarding Session | Household Members, Overlay selection | Household composition and sub-cohort signals are captured |
| **RegionalIdentityCaptured** | User completes OB-03 (home state + city + migration duration) | Onboarding Session | User, City Overlay Weight | Food cultural context established; city overlay weight derived and stored |
| **DietConfigured** | User completes OB-04 (diet type + religious pref) | Onboarding Session | User, Diet Type, Religious Preference | Household hard dietary constraint established |
| **AllergensConfigured** | User completes OB-05 | Onboarding Session | User, Household Allergen Flags | Safety constraint boundary established for this household |
| **CookCapabilitySelected** | User completes OB-06 | Onboarding Session | User, Cook Capability | Dish complexity filtering parameter established |
| **ClassPreferenceSwiped** | User swipes a dish card in OB-07 (YES or NOPE) | User | Interaction Events (onboarding_class_preference), Class Affinity | First behavioral signal received; class-level preference recorded; interaction_count incremented |
| **PersonaAssigned** | assign_persona() function completes at end of onboarding | RE Engine | User RE State (persona_id, confidence_score, overlay_persona_ids[]) | RE has a research-data anchor. Cold-start plan generation is now possible. |
| **PlanPreviewGenerated** | First plan generated at OB-08b | RE Engine | Week Plan, Plan Slots | User sees first output of the RE before leaving onboarding |
| **PlanPreviewInteracted** | User swaps, locks, or nevers a dish on OB-08b | User | Interaction Events, Plan Slot, Never List | First post-onboarding interactions recorded before main experience begins |
| **OnboardingCompleted** | User taps "Looks good — let's go!" on OB-08b | User | User (onboarding_completed = true), Week Plan (activated) | Household profile is complete; RE is operational; main experience begins |

### Planning Events

| **Event Name** | **Trigger** | **Source Entity** | **Affected Entities** | **Business Meaning** |
| --- | --- | --- | --- | --- |
| **WeekPlanGenerated** | Sunday CRON or first app open on Monday | RE Engine | Week Plan, Plan Slots (all 21), Add-on Slots | A complete 7-day meal plan is created for the household; class assignments made per cohort research data |
| **AddOnSlotsGenerated** | Week Plan generation for household with active overlays | RE Engine | Add-on Slots, Household Members | Member-specific add-on components generated and attached to primary slots |
| **SlateGenerated** | Plan Slot class assigned; dish candidates needed | RE Engine | Plan Slot, Dish Content (read), Interaction History (read), Context (read) | All hard constraints applied, surviving dishes scored and ranked; 8 candidates stored with reason codes |
| **PlanPreviewViewed** | User opens Day View (H-01) or OB-08b | User | Suggestion Log | System records which dishes were shown to this user; Safety Gate baseline established |
| **DayViewOpened** | User navigates to H-01 | User | Context (assembled), Week Plan (read) | Current day's plan surfaced; context signals assembled for possible re-scoring |
| **WeekViewOpened** | User navigates to Week View | User | Week Plan (read) | Full 7-day plan surfaced for review |

### Interaction Events

| **Event Name** | **Trigger** | **Source Entity** | **Affected Entities** | **Business Meaning** |
| --- | --- | --- | --- | --- |
| **DishAccepted** | User selects a dish from carousel or keeps the headline suggestion | User | Interaction Events, Taste Vector (pending sync), interaction_count | Positive preference signal; dish and its genome tags will be boosted in next Taste Vector update |
| **DishLocked** | User taps lock icon on a meal card | User | Plan Slot (lock state = true), Interaction Events | Strongest positive signal; this slot is protected from all future refreshes; dish will be boosted in RE |
| **DishUnlocked** | User taps lock icon on a locked card | User | Plan Slot (lock state = false) | Slot reopened for refresh; the previous lock signal in interaction history persists |
| **CarouselOpened** | User taps swap icon on a meal card | User | Plan Slot (carousel state) | User wants alternatives; slate alternatives surfaced from stored slate |
| **DishSwiped_NotToday** | User reveals action buttons, taps Not Today, confirms at H-06 | User | Interaction Events, Not Today Suppression (created), interaction_count | Temporary rejection; dish suppressed with exponential decay for ~7 days; mild negative in PersonalHistory |
| **DishNevered** | User reveals action buttons, taps Never, confirms at H-07 | User | Interaction Events, Never List (entry created), interaction_count | Permanent rejection; dish added to never list with is_active = true; immediately excluded from all future slates |
| **DishSwipedPast** | User scrolls past a dish in carousel without selecting | User | Interaction Events, interaction_count | Mild negative signal; dish was seen and passed over |
| **DishCooked** | User taps "Cook This" on Meal Detail | User | Interaction Events, interaction_count | Strongest confirmed positive signal; user has committed to making this dish |
| **DishRated** | User gives explicit star rating | User | Interaction Events, interaction_count | Calibrated preference signal; rating value maps to specific event weight |
| **ComboComponentSwapped** | User taps swap on a swappable combo component | User | Plan Slot (selected dish updated), Interaction Events | User has personalised a combo; swapped component records a weak positive; original component records a mild negative |
| **MealDetailOpened** | User taps a dish card to see the detail page | User | Interaction Events (engagement signal) | User showed interest in a dish; not a preference signal but an engagement signal |

### Plan Management Events

| **Event Name** | **Trigger** | **Source Entity** | **Affected Entities** | **Business Meaning** |
| --- | --- | --- | --- | --- |
| **PlanRefreshed** | User pulls to refresh on Day View | User | Week Plan, all unlocked Plan Slots (new slates), Variety Window State | RE regenerates slates for all unlocked slots within their existing class assignments; locked slots untouched |
| **SlotRefreshed** | Individual slot regenerated as part of plan refresh | RE Engine | Plan Slot (new slate), Suggestion Log (new entries) | One slot's 8 candidates replaced; new reason codes stored; previous slate archived |
| **DishSelected** | User selects a specific dish (not locked) | User | Plan Slot (selected_dish_id set) | User has chosen a dish but has not committed (not locked). Can be cleared on next refresh. |

### Profile Events

| **Event Name** | **Trigger** | **Source Entity** | **Affected Entities** | **Business Meaning** |
| --- | --- | --- | --- | --- |
| **ProfileUpdated** | User edits household composition, diet, allergens, or city | User | User, Household Members, potentially: Persona (reassignment may be needed) | Household identity changed; depending on significance of change, persona may need reassignment |
| **HouseholdMemberAdded** | User adds a new member from Profile screen (post-onboarding) | User | Household Members, Overlay Personas, Add-on Slot generation (for future plans) | New household member's constraints now apply to all future plans |
| **HouseholdMemberRemoved** | User soft-deletes a member | User | Household Members (is_active = false), Overlay Personas | Member's add-on slot no longer generated; their constraint removed from household combined flags |
| **RegionalIdentityUpdated** | User changes home state, current city, or migration duration | User | Regional Identity, City Overlay Weight (recomputed) | Food cultural context updated; overlay weight recomputed; may trigger persona reassignment |
| **PersonaReassigned** | Significant change in onboarding profile variables after onboarding | RE Engine | User RE State (persona_id updated) | RE has recalculated the best persona match given updated household profile |

### Learning Events

| **Event Name** | **Trigger** | **Source Entity** | **Affected Entities** | **Business Meaning** |
| --- | --- | --- | --- | --- |
| **TasteVectorUpdated** | Async processor runs on unsynced Interaction Events (every 15 min) | RE Processor | Taste Vector (genome_tag_affinity updated), synced_to_re flags set to true | RE has integrated recent user behaviour into its preference model; next slate will be more personalised |
| **ClassAffinityUpdated** | OB-07 swipe OR 3+ Nevers from same class processed | RE Processor | Taste Vector (class_affinity updated) | Class-level preference signal integrated; certain Meal Classes now weighted up or down for this user |
| **ColdStartExited** | interaction_count reaches 14 | RE Processor | User RE State (cold_start_mode = false) | RE has enough personal data to begin reducing reliance on cohort priors; PersonalHistory weight begins rising |
| **BanditStateUpdated** | Accept or reject event processed for a dish | RE Processor | Bandit State (α or β incremented for dish-user pair) | Thompson Sampling parameters updated; exploration bonus adjusted for this dish |

### Suppression Events

| **Event Name** | **Trigger** | **Source Entity** | **Affected Entities** | **Business Meaning** |
| --- | --- | --- | --- | --- |
| **NotTodayApplied** | DishSwiped_NotToday confirmed | User | Not Today Suppression (record created, P0=0.80) | Dish temporarily removed from recommendation pool; penalty begins decaying immediately |
| **NotTodayExpired** | Penalty decays below 0.05 threshold (~Day 7) | RE Processor | Not Today Suppression (is_active = false) | Dish fully restored to recommendation pool; suppression no longer applied at scoring |
| **NeverApplied** | DishNevered confirmed | User | Never List (entry created, is_active = true) | Dish permanently excluded from all future slates for this user |
| **NeverReactivationPrompted** | Seasonal or festival conditions met for a Never'd dish | RE Processor | Notification, Plan Slot (re-surface candidate added) | RE surfaces a soft prompt offering the user a chance to restore the dish |
| **NeverReactivated** | User confirms reactivation prompt | User | Never List (is_active = false), Taste Vector (mild positive) | Dish restored to candidate pool; treated as a fresh dish with no negative history bias |

### System Events

| **Event Name** | **Trigger** | **Source Entity** | **Affected Entities** | **Business Meaning** |
| --- | --- | --- | --- | --- |
| **SafetyGateViolation** | Any safety gate query returns non-zero rows | RE Engine or Migration Pipeline | P0 incident raised | Hard correctness failure detected; deployment or plan serving must be halted |
| **SeedGatesValidated** | All 15 seed gate row count checks pass | Seeding Pipeline | RE Engine (unblocked) | Reference data is complete and correct; RE is now permitted to run |
| **DishDerivationRun** | New ingredients linked OR ingredients modified | Derivation Pipeline | Dish (diet_type, is_jain, allergen_flags updated) | Dish dietary attributes recomputed from ground truth ingredients |
| **WeatherCacheMiss** | Recommendation request finds no valid cache entry | RE Engine | Weather Cache (new entry created via API call), Context (current request) | Fresh weather data fetched and cached; API call consumed |
| **WeatherCacheRefreshed** | Cache miss triggers successful API call | External API → System | Weather Cache | City's weather data refreshed for next 12 hours |
| **PlanCRONCompleted** | Sunday evening scheduled job runs | CRON | Week Plans (next week pre-generated for all active users) | Next week's plans ready before Monday morning; users see fresh plan immediately on first open |
| **REVersionPromoted** | Shadow mode metrics pass all thresholds after 72 hours | RE Operator | RE Engine Version (new version active), User RE State (re_engine_version updated) | New RE algorithm goes live for all users |
| **BulkPlanInvalidated** | Major dish content update or RE data change | RE Engine | Week Plans (future unlocked slots flagged for regeneration) | Plans may reflect stale data; unlocked slots will be refreshed at next user open |

### Compliance Events

| **Event Name** | **Trigger** | **Source Entity** | **Affected Entities** | **Business Meaning** |
| --- | --- | --- | --- | --- |
| **ConsentGranted** | User grants consent at signup or in settings | User | Consent Records | Legal record created; corresponding data use unlocked |
| **ConsentRevoked** | User revokes a consent type in settings | User | Consent Records, corresponding data use (suspended) | Legal record updated; corresponding data use must stop |
| **DataExportRequested** | User requests DPDP data export | User | Audit Log, all user data (assembled for export) | 72-hour clock starts; all user data must be compiled and delivered |
| **AccountDeletionRequested** | User requests account deletion | User | Audit Log, all personal data | 72-hour clock starts; all personal data except audit log must be deleted |
| **DataDeletedDPDP** | 72 hours after deletion request | System | User, Household Members, Interaction Events, Never List, Taste Vector, Week Plans, Plan Slots (all personal data) | Deletion completed; audit log retained per 3-year DPDP requirement |

## Part 19 — Entity Dependency Map

This map shows which concepts must exist, or which outputs must be available, before another concept can exist or operate. It is not a database relationship diagram. It is a conceptual dependency view that answers: what must happen first?

The map is organised into layers. Higher layers depend on lower layers. Concepts at the same layer can be developed in parallel.

### Layer 0 — Pure Reference (no dependencies)

These concepts exist independently. They are pre-defined lookup values or seeded research data. Nothing needs to exist before these.

- Ingredient records (content operations create these)

- Genome Tag master list (tag taxonomy defined upfront)

- Meal Class definitions (seeded from research data)

- Main Cohort types (5 fixed values)

- State profiles (36 fixed values)

- Festival calendar (cultural reference data)

- Season definitions (month-to-season mapping)

- RE configuration parameters (weight ladder config, MMR lambda, confidence contribution values)

### Layer 1 — User Foundation (depends on Layer 0)

These concepts can only exist once a user account is created.

- **User (Profile)** — depends on: auth system only

- **Onboarding Session** — depends on: User existing

- **Consent Records** — depends on: User existing (created at signup)

### Layer 2 — Household Profile (depends on Layer 1)

These concepts are established during onboarding.

- **Household Members** — depends on: User (OB-02 branching)

- **Regional Identity** — depends on: User, State profiles (OB-03)

- **Diet Type + Religious Preference** — depends on: User (OB-04)

- **Allergen Flags** (on User and Members) — depends on: User, Household Members, Ingredients (OB-05)

- **Cook Capability** — depends on: User (OB-06)

- **Class Preference Swipes** — depends on: User, Meal Class definitions (OB-07); generates first Interaction Events

### Layer 3 — Persona and Cohort (depends on Layer 2 + Reference Data)

These are derived at the end of onboarding and whenever the profile significantly changes.

- **Sub-cohort Tag** — depends on: Main Cohort selection (Layer 2), Household Members (Layer 2)

- **Persona Assignment (base)** — depends on: Main Cohort, Sub-cohort, Home State, Diet Type; also depends on: Persona seed data (Layer 0), Cohort-State Matrix (Layer 0)

- **Overlay Personas** — depends on: Household Member segments (Layer 2)

- **City Overlay Weight** — depends on: Migration Duration (Layer 2)

- **Confidence Score** — depends on: Onboarding completeness (Layer 2), Interaction Count (grows from Layer 2 onward)

### Layer 4 — Dish Content (depends on Layer 0 + Content Operations)

These concepts are built by content operations before launch and maintained ongoing.

- **Dish** — depends on: Ingredients (Layer 0), Genome Tag master list (Layer 0)

- **Dish Ingredients (junction)** — depends on: Dish, Ingredients

- **Genome Tags on Dish (junction)** — depends on: Dish, Genome Tag master list

- **Dish diet_type / is_jain / allergen_flags** — depends on: Dish Ingredients (derivation runs after this)

- **Dish Genome Vector** — depends on: Genome Tags on Dish (derived and stored)

- **Dish Variant** — depends on: Dish (parent exists)

- **Dish Combo** — depends on: Dish (components exist)

- **Class-Dish Options (junction)** — depends on: Dish (Layer 4), Meal Class (Layer 0)

### Layer 5 — Week Plan (depends on Layers 3 + 4 + Reference Data)

A Week Plan cannot exist without a persona assignment and without the dish content being available.

- **Week Plan** — depends on: User RE State (persona assigned, Layer 3), Weekly Class Plans seed data (Layer 0)

- **Plan Slot class assignment** — depends on: Week Plan, Weekly Class Plans (class per slot determined by persona × day × meal occasion)

- **Add-on Slot** — depends on: Plan Slot, Household Members with active segments (Layer 2), Addon Classes seed data (Layer 0)

### Layer 6 — Slate Generation (depends on Layer 5 + All Constraints)

A Slate can only be generated once a Plan Slot has its class assignment and all constraints are resolvable.

- **Hard Constraint Resolution** — depends on: User Diet Type (Layer 2), User + Member Allergen Flags (Layer 2), Never List (Layer 7 — grows over time), Class-Dish Options (Layer 4)

- **Context Assembly** — depends on: Weather Cache (external), System time (season, day), Festival Calendar (Layer 0)

- **FinalScore computation** — depends on: Hard Constraint survivors (above), Taste Vector (Layer 7 — grows over time), CohortPrior from seed data (Layer 0), Context (above), Bandit State (Layer 7 — grows over time)

- **Slate** — depends on: FinalScore for all surviving candidates, MMR algorithm (post-scoring re-ranking)

- **Suggestion Log entries** — depends on: Slate (what was shown must be logged)

### Layer 7 — Interaction and Learning (depends on Layer 6, grows over time)

These concepts grow continuously from user behavior after first use.

- **Interaction Events** — depends on: User (Layer 1), Plan Slot (Layer 5), Dish (Layer 4)

- **Never List** — depends on: Interaction Events of type dish_never

- **Not Today Suppression** — depends on: Interaction Events of type dish_not_today

- **Variety Window State** — depends on: Interaction Events, Plan Slot history

- **Bandit State (α, β)** — depends on: Interaction Events (accept/reject signals per dish per user)

- **Taste Vector update** — depends on: Unsynced Interaction Events (processed by async job)

- **Class Affinity update** — depends on: Class Preference Swipes (Layer 2 onward) + Class-level Never signals

- **Cold Start State transition** — depends on: interaction_count crossing threshold

### Layer 8 — Analytics and Compliance (depends on all layers)

These are derived views or compliance records over all other data.

- **Safety Gate results** — depends on: Suggestion Logs (Layer 6), Dish content (Layer 4), User profile (Layer 2)

- **Context Log** — depends on: Slate generation (Layer 6)

- **Dish Popularity Score** — depends on: Suggestion Logs + Interaction Events (updated daily)

- **Audit Log** — depends on: Any data change event across all layers

- **DPDP Data Export** — depends on: All layers (assembles all user data)

### Key dependency rules to carry into P3-03 and P3-04

These are the most important dependency rules for business logic and data architecture design:

- **A Slate cannot be generated until the persona is assigned.** Persona assignment depends on onboarding completion. No plan, no slate, no recommendation without a complete persona.

- **A Dish must pass the auto-derivation pipeline before it is eligible for any Slate.** Untag-derived dishes are not safe candidates.

- **Allergen constraint checking must use ingredient-level data, not dish-level data.** This means the dish_ingredients junction must be queryable at slate generation time.

- **The Taste Vector is only as fresh as the last async processing run.** A user who just interacted will not see those signals in the next Slate unless the async processor has run.

- **The Never List feeds into slate generation at Layer 6, but is populated by Layer 7 events.** This means the Never List grows over time and each slate generation must query the current state of the never list.

- **Confidence Score and Cold Start State are always derived from interaction_count.** No manual override of these values is permitted.

- **All 15 seed gates (Layer 0) must be valid before Layer 5 (Week Plan) can operate.** The RE has no fallback if seed data is missing.

- **Context (Layer 6) depends on Weather Cache (external).** If the weather API is unavailable and cache is expired, the system must have a defined fallback (e.g., use 'mild' as default condition) rather than blocking slate generation.

## Document update record

| **Version** | **Changes** | **Date** |
| --- | --- | --- |
| 1.0 | Initial release — 51 entities, 14 invariants, 4 lifecycles, 5 known exclusions | June 2026 |
| 1.1 | Added Parts 15–19: Aggregate Roots (7 aggregates), Entity Responsibilities (24 entities), Data Nature Classification (47 concepts), Business Events Catalogue (52 events across 7 categories), Entity Dependency Map (8 layers) | June 2026 |