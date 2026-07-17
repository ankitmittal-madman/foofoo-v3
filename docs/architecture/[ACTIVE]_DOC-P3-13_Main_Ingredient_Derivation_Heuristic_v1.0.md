# [ACTIVE]_DOC-P3-13_Main_Ingredient_Derivation_Heuristic_v1.0

**Status:** ACTIVE — first-pass heuristic, not a substitute for Founder review on ambiguous cases.
**Version:** v1.0
**Date:** 2026-07-17
**Placement:** docs/architecture/[ACTIVE]_DOC-P3-13_Main_Ingredient_Derivation_Heuristic_v1.0.md
**Supersedes:** None.
**Dependencies:** `[ACTIVE]_SER-002_dish_ingredients_main_ingredient_flag_v1.0.md` (the `is_main_ingredient` column this heuristic populates); `[ACTIVE]_Founder_Decision_Register_v1.0.md` FD-11 (the original "dominant ingredient" derivation-rule question this heuristic answers, extracted from the Founder's own 810-dish dataset, not invented independently).

---

## Executive Summary

The Founder supplied `is_main_ingredient` classifications with reasoning (the `logic` column) for 810 dishes — 842 (dish, ingredient) pairs once the 40 multi-main-ingredient dishes are split. This document extracts the general pattern behind that reasoning, evidenced directly from the supplied `logic` text (not invented), so that the *next* new dish added to the catalog without founder-supplied data has a documented rule to follow instead of guessing. **This is a first-pass heuristic. It does not replace Founder review for genuinely ambiguous cases** — treat its output the way this repository treats a "Medium" confidence tag: usable, but flagged for a human pass before being trusted as final, consistent with how confidence tiers are already used elsewhere in this dataset (see §3).

## 1. The General Rule

**The main ingredient is the one that defines the dish's culinary identity and category — not the one that dominates by weight, quantity, or ingredient-list position.**

Concretely, applied in this priority order:

1. **A named protein or pulse, if the dish is built around one.** Meat, dairy-as-protein (paneer, curd, khoya), egg, or seafood is flagged main whenever it's the ingredient that makes the dish *what it is* — "Butter Chicken" is a chicken dish regardless of how much cream, tomato, and butter also went in.
2. **Otherwise, the grain/flour that forms the dish's structural base.** Breads, rices, and batters are flagged by their cereal component (wheat_flour, rice_basmati, rice_flour, refined_flour) — the dish cannot exist as that dish without it, even though it's rarely the ingredient a person would name first.
3. **Otherwise, the single ingredient a reader would use to answer "what is this dish, fundamentally?"** — a vegetable for a sabzi, a legume for a dal, coconut for a coconut-based curry, a nut/dry fruit or dairy component for a sweet whose identity is that ingredient (Barfi = cashew, Basundi = pistachio, Peda = khoya).
4. **Multiple main ingredients are used when the dish's identity genuinely rests on more than one component simultaneously** — not merely because more than one ingredient is prominent. See §2.

**What this rule explicitly does NOT use:** ingredient quantity, listing order in the source recipe, or nutritional dominance. A dish with 200g of onion and 50g of paneer still flags paneer, because identity — not mass — is the criterion.

## 2. When to Flag More Than One Main Ingredient

40 of the 810 supplied dishes (4.9%) carry two main ingredients. Reading the `logic` column across all of them shows exactly two recurring justifications — no others appear:

- **Co-equal structural role**, most often "rice forms the base, protein defines the variant" — e.g. **Biryani (Mughlai Chicken)**: `rice_basmati; chicken` — *"Rice forms the structural base; co-equal protein defines the dish variant."* The same pattern recurs for every biryani/pulao-with-protein dish in the set (Lucknowi Biryani, Hyderabadi Chicken/Mutton/Egg Biryani, Malabar Biryani, Kolkata Biryani, Goan Sausage Pulao, and the fried-rice family: Chicken Fried Rice, Egg Fried Rice, Japanese/Thai/Korean fried rice variants).
- **Fermented batter identity**, specifically the rice-lentil ferment family — e.g. **Masala Dosa**, **Idli**, **Plain Dosa**, **Uttapam**: `rice_regular; urad_dal` — *"Fermented rice-lentil batter co-defines the dish's structural base."* Both grains are structurally inseparable in a fermented batter; flagging only one would misrepresent the dish's actual composition.
- **Dual defining pulses**, a narrower case — **Dal Makhani**: `black_lentil; kidney_beans` — *"Dual defining pulses forming the lentil base."* Applies when two legumes are both named in the dish's own identity, not merely co-present.
- **Named stuffing as co-defining component** — **Paneer Paratha**, **Stuffed Naan (Paneer)**: `wheat_flour; paneer` — *"Grain flour base with named stuffing ingredient as co-defining component."* The grain is structural (per §1 rule 2); the named filling is also flagged because the dish's name itself names it.

**The pattern, stated generally:** flag a second main ingredient only when the `logic` would need to name it to correctly answer "what is this dish" — a rice dish that happens to contain chicken doesn't need "rice" flagged as co-equal to chicken (see counter-examples in §4), but a dish whose *name* is a composite ("Chicken Biryani," "Paneer Paratha") usually does.

## 3. Confidence Is Part of the Signal, Not Noise

The supplied dataset carries a `confidence` column (High/Medium) alongside every classification — 662 rows (81.7%) are High confidence, 148 (18.3%) are Medium. Reading the pattern: **High confidence corresponds to rows where the main ingredient is a named protein/pulse/grain with no real competing candidate** (Butter Chicken → chicken, Puri → wheat_flour). **Medium confidence corresponds to rows where the dish is vegetable-forward and a specific vegetable had to be chosen among several plausible candidates** (Aloo Gobhi → cauliflower over potato; Mix Veg → cauliflower over carrot/beans/peas). This heuristic inherits that same confidence structure: a future classification following this rule should be marked Medium, not High, whenever the choice is "which vegetable among several," and should get a human spot-check before being trusted, exactly as the Founder's own Medium-confidence rows were flagged rather than silently treated as certain.

## 4. Worked Examples (cited from the actual dataset, not invented)

| Dish | Main ingredient(s) | Logic (verbatim from source) | Confidence |
|---|---|---|---|
| Butter Chicken | chicken | Primary protein defining dish identity | High |
| Dal Makhani | black_lentil; kidney_beans | Dual defining pulses forming the lentil base | High |
| Makki Ki Roti | cornmeal | Primary cereal flour forming structural base of the bread | High |
| Aloo Gobhi | cauliflower | Primary vegetable defining dish composition | Medium |
| Biryani (Mughlai Chicken) | rice_basmati; chicken | Rice forms the structural base; co-equal protein defines the dish variant | High |
| Masala Dosa | rice_regular; urad_dal | Fermented rice-lentil batter co-defines the dish's structural base | High |
| Paneer Paratha | wheat_flour; paneer | Grain flour base with named stuffing ingredient as co-defining component | High |
| Barfi (Kaju) | cashew | Primary nut/dry fruit component defining the sweet's identity | High |
| Sol Kadhi | coconut_milk | Primary coconut base defining the beverage | High |
| Coconut Chutney | green_chilli | Primary vegetable/fruit base defining the condiment | High |

The last row is a useful counter-example against a naive reading of the rule: one might expect "coconut" to be flagged for a dish literally named "Coconut Chutney" — but the Founder's own data flags `green_chilli` instead, with the condiment-base framing. **This is exactly the kind of case this heuristic cannot reliably predict on its own** — it is included here precisely so a future classifier doesn't over-generalize from the dish name.

## 5. How to Apply This to a New Dish

1. Identify the dish's named protein/pulse (meat, dairy-as-protein, egg, seafood). If one exists and defines the dish, flag it main, High confidence.
2. If no protein applies, identify the grain/flour forming the structural base (bread, rice dish, batter). Flag it main, High confidence.
3. If neither applies cleanly, identify the single vegetable, coconut component, or sweet-defining dairy/nut component that answers "what is this dish." Flag it, Medium confidence, and note it as a candidate for human spot-check.
4. Only add a second main ingredient if §2's co-equal-structural-role, fermented-batter, dual-pulse, or named-stuffing pattern applies — not merely because a second ingredient is prominent.
5. **Do not treat this document's output as final for any dish where step 3 was needed and the choice among vegetables/components felt arbitrary** — route it back to a Founder pass, the same way FD-11's own Medium-confidence rows are meant to be spot-checked, not silently trusted.

## Critical Self-Review

- **Is this heuristic invented, or extracted?** Extracted — every rule and example above traces to actual `logic` text in the Founder-supplied 810-row dataset; nothing here is a guess about future data this document hasn't seen.
- **Does this replace Founder review?** No — §3 and §5 explicitly route Medium-confidence-equivalent cases back to human review, and §4's Coconut Chutney example is included specifically to show where the heuristic would mispredict if trusted blindly.
- **Scope:** this document governs *classification of new dishes not yet in the Founder-supplied set*. It does not retroactively second-guess any of the 842 already-loaded pairs from the original dataset — those are Founder-supplied fact, not heuristic output.

## Versioning & Placement

v1.0, `docs/architecture/`, per the Placement Rule; naming per WP-5AA (`DOC-P3-13`, next sequential number in the `DOC-P3-NN` series).

Founder sign-off: _______________________ Date: ___________
