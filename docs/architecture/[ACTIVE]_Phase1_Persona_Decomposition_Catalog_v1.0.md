# [ACTIVE]_Phase1_Persona_Decomposition_Catalog_v1.0

**Status:** ACTIVE — Phase 1 deliverable of the Canonical Planning Semantics Architecture
**Date:** 2026-07-17
**Method:** Systematic classification of all 41 `Persona_Master_v3` rows, every field read, each row assigned to composition / condition / diet-dimension / compound-patch. Nothing sampled — the complete dataset.

---

## 1. Headline results

- **The composition catalog is ~5 archetypes, not 41.** Solo, Couple, Family-with-children, Joint/Multi-generation, Elderly-couple — plus the region/migration axis (which already exists separately as `city_migration_overlay`). Everything else in the 41 rows is a condition, a diet pattern, or a patch.
- **Open question #1 from the architecture doc is now answered:** composition-archetype count — 5 core (with 2–3 sub-variants like flatmates/hostel under Solo), not dozens.
- **The main-cohort layer itself is contaminated — a new finding.** MC1–MC4 are genuine composition groupings. **MC5 is not a cohort at all — it's a miscellaneous conditions bucket** holding 16 of the 41 rows: weight-loss, gym, Jain, fasting, cooking-capability rows, budget, foodie, all five non-veg patterns, and field-work. The "misc bucket" is itself structural evidence that conditions never fit the composition hierarchy — the researchers created a junk-drawer cohort because these rows had no compositional home.
- **P30–P34 are not personas at all.** Regular non-veg, eggitarian, seafood-coastal, Sunday-mutton, home-veg-outside-nonveg — these are the five values of the already-clean `nonveg_mode` enum, each wrapped in a persona costume. They dissolve completely into the existing diet dimension.
- **P41 dissolves entirely**, as predicted: `child_plus_diabetic_elder_overlap` = family composition + child condition + diabetic/elder condition, composed. The row exists only because composition wasn't possible.

## 2. Full classification of all 41 rows

| # | Label | Classification | Decomposes into |
|---|---|---|---|
| P01 | student_hostel_budget | Composition + conditions | Solo (hostel variant) + cost_bias=budget + kitchen_access=limited |
| P02 | solo_young_professional | **Composition** | Solo + time_pressure |
| P03 | working_woman_alone | Composition + mild condition | Solo + health_intent + time_pressure |
| P04 | dink_couple | **Composition** | Couple |
| P05 | newly_married_mixed_state | **Composition** (+ region) | Couple + two-home-state region mix |
| P06 | planning_pregnancy | Condition-driven | Couple + preconception condition |
| P07 | pregnant_household | Condition-driven | Couple + pregnancy condition |
| P08 | couple_with_infant_0_6m | Condition-driven | Couple + lactating-mother/infant-0-6m condition |
| P09 | couple_with_baby_6_18m | Condition-driven | Couple + baby-6-18m condition |
| P10 | family_with_toddler | Condition-driven | Family + toddler condition |
| P11 | family_with_school_kids | Condition-driven | Family + school-child condition |
| P12 | family_with_teenagers | Condition-driven | Family + teen-high-appetite condition |
| P13 | joint_multigeneration | **Composition** (+ implied conditions) | Joint/multigen; elder+child conditions derived from actual members |
| P14 | elderly_couple | **Composition** (+ auto-derived condition) | Elderly couple; elderly condition derives from member ages |
| P15 | diabetic_low_gi_household | Condition-driven | Any composition + diabetes condition |
| P16 | bp_heart_conscious | Condition-driven | Any composition + hypertension/heart condition |
| P17 | weight_loss_calorie_conscious | Condition-driven | Any + weight-loss goal |
| P18 | gym_high_protein | Condition-driven | Any + fitness goal |
| P19 | vegetarian_protein | Condition + diet | Veg diet + protein-seeking goal |
| P20 | strict_jain | **Diet dimension** | Jain diet (hard constraint — already modeled) |
| P21 | fasting_ritual | **Diet dimension** (temporal) | Fasting pattern |
| P22 | cook_assisted_skilled | Condition (cooking) | cook_capability=skilled |
| P23 | cook_needs_instruction | Condition (cooking) | cook_capability=needs_instruction |
| P24 | working_woman_managing_cook | Condition (cooking + time) | cook_capability=supervised + time_pressure |
| P25 | maid_dependent_batch_cook | Condition (cooking) | cook_capability=batch/helper |
| P26 | budget_family | Condition (economic) | cost_bias=budget |
| P27 | premium_experimental_foodie | Condition (economic/novelty) | cost_bias=premium + novelty_bias=experimental |
| P28 | migrant_adult_home_state | **Region axis** | Already modeled by city_migration_overlay |
| P29 | interstate_couple_mixed_cuisine | **Region axis** | Couple + dual-region mix |
| P30 | regular_nonveg_household | **Diet dimension** | nonveg_mode value |
| P31 | eggitarian_low_meat | **Diet dimension** | nonveg_mode value |
| P32 | seafood_coastal_nonveg | **Diet dimension** | nonveg_mode value |
| P33 | sunday_mutton_nonveg | **Diet dimension** | nonveg_mode value |
| P34 | home_veg_outside_nonveg | **Diet dimension** | nonveg_mode value |
| P35 | child_picky_eater | Condition-driven | Family + picky-child condition |
| P36 | recovery_senior_light | Condition-driven | Any + recovery condition |
| P37 | flatmates_shared_kitchen | **Composition** | Solo variant (shared kitchen) + kitchen_access=shared |
| P38 | field_work_heavy_breakfast | Condition (lifestyle) | Any + heavy-breakfast energy pattern |
| P39 | desk_job_sedentary | Condition (lifestyle) | Solo/any + sedentary pattern |
| P40 | homemaker_elaborate_family | Condition (cooking) | Family + cook_capability=elaborate |
| P41 | child_plus_diabetic_elder_overlap | **Compound patch** | Dissolves: family + child condition + diabetic/elder condition |

**Tally:** ~8 composition rows (5 archetypes + variants), ~22 condition-driven rows, ~7 diet-dimension rows, 2 region-axis rows, 1 compound patch, with some rows carrying both a composition and a condition component.

## 3. Extracted condition dimension catalog (with genome-space attributes)

Six condition families, extracted from actual row data — each independent, member-scoped where applicable, expressed in existing genome dimensions:

**A. Life-stage conditions** (member-scoped, route to add-on channel): preconception, pregnant, lactating+infant-0-6m, baby-6-18m, toddler, school-child, teen-high-appetite, picky-child, elderly, recovery. Attributes: texture (soft for infant/toddler/recovery/elderly), spice_tolerance (low for young children), protein_target (high for teen/pregnant/lactating), portion/snack patterns. *Every one already has a clean `dependent_addon_default` value in the research — the vocabulary exists.*

**B. Health conditions** (member-scoped; safety-tier attributes that outrank preferences): diabetes — glycemic_target=low-GI; hypertension/heart — sodium/oil restricted; health-intent (mild general bias).

**C. Lifestyle/nutrition goals** (member- or household-scoped): fitness — protein_target=high; weight-loss — calorie-adjusted; veg-protein-seeking; sedentary; field-work — heavy-breakfast energy pattern (a meal-timing bias, notable as the only condition that shifts *which meal* carries the load).

**D. Cooking capability** (household-scoped — answers open question #2: it attaches to the household's cooking arrangement, not a member): skilled / needs-instruction / owner-supervised / batch-helper / elaborate-homemaker / limited-kitchen. Attribute: recipe_complexity_bias.

**E. Economic/behavioral** (household-scoped): cost_bias (budget/premium), novelty_bias (familiar/experimental).

**F. Diet patterns** (hard-constraint tier — already correctly modeled, no change): Jain, fasting, the 5 nonveg_mode values.

## 4. What this means for the open questions

- **Open question #1 (composition count): answered — ~5 archetypes** + region axis.
- **Open question #2 (cooking-capability attachment): answered by the data — household-scoped.** Every cooking row describes the household's cooking arrangement, never an individual member's dietary need.
- **Conflict resolution: already resolved in §9c** of the architecture doc; nothing in this pass contradicted it.

## 5. Recommended next step (Phase 1 — Phase 2 bridge)

The boost-class lists on each persona row (`bf/ld/sn/dn_boost_classes`) are the remaining unextracted knowledge: they encode *attribute-combination — meal-class* mappings (e.g., toddler's BF list = the "soft, mild, kid-appropriate breakfast" classes). Phase 2's vocabulary fix should be accompanied by extracting these into the shared attribute→class mapping — one rule per attribute pattern, replacing 41 hand-attached lists.
