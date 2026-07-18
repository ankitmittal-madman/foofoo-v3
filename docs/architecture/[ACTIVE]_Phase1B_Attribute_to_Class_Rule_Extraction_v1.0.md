# [ACTIVE]_Phase1B_Attribute_to_Class_Rule_Extraction_v1.0

**Status:** ACTIVE — companion to Phase1 Persona Decomposition Catalog
**Date:** 2026-07-17
**Method:** All boost-class lists (`bf/ld/sn/dn_boost_classes`) across all 41 personas extracted, frequency-analyzed (92 distinct classes), and cluster-tested for convergence on shared attributes. Every rule below cites the actual class co-occurrence pattern that produced it.

---

## 1. The three-layer structure the data reveals

The 92 boost classes are not 41 independent lists. They form three clean layers:

**Layer 1 — Universal base classes** (high frequency, span all compositions — the "default Indian household" layer):
`LD_DAL_ROTI_SABZI` (20 of 41 personas), `BF_POHA_CHIVDA_LIGHT` (17), `SN_FRUIT_CHAAT` (15), `BF_STUFFED_FLATBREAD` (14), `DN_FAMILY_COMFORT_MEAL` (13). These belong to the **composition/cold-start prior layer**, not to any condition.

**Layer 2 — Shared attribute-driven classes** (mid frequency, cluster precisely by attribute — the extracted rules in §2).

**Layer 3 — Condition-specific specialization classes** (frequency 1–2: `BF_LACTATION_MOTHER`, `LD_PREGNANCY_BALANCED`, `BF_INFANT_6M_SOFT`, `LD_TEEN_HIGH_CALORIE`, `LD_RECOVERY_SOFT_PROTEIN`, `BF_FASTING_PHALAHARI`, `LD_JAIN_NO_ROOT_MAIN`, the seafood/mutton classes...). These stay attached to their specific condition rule as its specialization tier, layered *on top of* the shared attribute classes.

**Rule shape:** `condition — attributes — shared attribute classes (Layer 2) + condition's own specializations (Layer 3)`, on top of the composition base (Layer 1).

---

## 2. The extracted shared attribute→class rules (Layer 2)

### Rule A — `texture=soft ∧ digestive=light`
**Evidence:** P14 (elderly) and P36 (recovery) have *identical* BF lists (`BF_DIABETIC_LOW_GI | BF_STEAMED_FERMENTED_LIGHT | BF_UPMA_DALIA_SEVAI`) and *identical* DN lists (`DN_EARLY_ELDERLY_DINNER | DN_KHICHDI_SOUP`); P08/P09 (infant households) share `DN_KHICHDI_SOUP`, `LD_LIGHT_KHICHDI`, `LD_DAL_RICE_COMFORT`.
**Rule:** → `BF_STEAMED_FERMENTED_LIGHT`, `BF_UPMA_DALIA_SEVAI`, `LD_LIGHT_KHICHDI`, `LD_ELDERLY_SOFT_DIGESTIVE`, `LD_GOURD_PUMPKIN_LIGHT`, `DN_KHICHDI_SOUP`, `DN_LIGHT_DAL_RICE`, `DN_CURD_RICE_LIGHT`.
**Set by:** elderly, recovery, infant-in-household, postpartum conditions.

### Rule B — `protein_target=high`
**Evidence:** `BF_CHILLA_PROTEIN` appears in **all four** high-protein personas (P07 pregnant, P12 teen, P18 gym, P19 veg-protein); `BF_SPROUTS_FRUIT_CURD` in three of four; `LD_HIGH_PROTEIN_VEG_PLATE` and `LD_RAJMA_CHOLE_LEGUME` shared across the veg-compatible members of the group.
**Rule:** → `BF_CHILLA_PROTEIN`, `BF_SPROUTS_FRUIT_CURD`, `LD_HIGH_PROTEIN_VEG_PLATE`, `LD_RAJMA_CHOLE_LEGUME`, `SN_HEALTHY_PROTEIN_SNACK`, `SN_ROASTED_CHANA_NUTS`; **plus, gated on nonveg_mode**: `BF_EGG_FAST`, `LD_CHICKEN_HOME_CURRY`, `LD_EGG_CURRY_BHURJI`. (The diet gate is visible in the data: P19 veg-protein carries none of the egg/chicken classes P12/P18 carry.)
**Set by:** teen, fitness, veg-protein-seeker, pregnant/lactating conditions.

### Rule C — `child_appropriate` (spice_tolerance=low ∧ kid-format)
**Evidence:** `BF_KID_TIFFIN`, `LD_CHILD_MILD_PLATE`, `DN_CHILD_FRIENDLY_DINNER`, `SN_KIDS_TIFFIN_SNACK` cluster across P09/P10/P11/P35 (baby, toddler, school-kids, picky-child) and nowhere else.
**Rule:** → those four classes + `BF_STEAMED_FERMENTED_LIGHT` (overlaps Rule A — young children inherit soft-texture classes, exactly as attribute-sharing predicts).
**Set by:** baby/toddler/school-child/picky-child conditions.

### Rule D — `glycemic_target=low-GI`
**Evidence:** `BF_DIABETIC_LOW_GI` (7 uses: diabetic, BP, elderly, recovery, veg-protein, weight-loss personas), `DN_LOW_CARB_DINNER` (7), `LD_LOW_CARB_PROTEIN_PLATE`, `DN_MILLET_LIGHT_DINNER`.
**Rule:** → those classes.
**Set by:** diabetes, hypertension/heart, weight-loss conditions; also boosted for elderly (the research applies low-GI preventively with age — a real pattern worth preserving deliberately, not accidentally).

### Rule E — `calorie=restricted`
**Evidence:** weight-loss (P17) combines Rule D classes + `LD_MODERN_SALAD_BOWL`, `BF_OATS_MUESLI_FIT` (shared with gym P18 and sedentary P39).
**Rule:** → `LD_MODERN_SALAD_BOWL`, `BF_OATS_MUESLI_FIT`, `SN_FRUIT_CHAAT`, plus Rule D's low-carb dinner classes.

### Rule F — `time_pressure=high` (already a clean dimension)
**Evidence:** `LD_ONE_POT_PRESSURE` (7), `DN_ONE_POT_DINNER` (5), `BF_BREAD_MODERN_FAST` (5), `LD_OUTSIDE_DELIVERY_INDIAN` (6), `LD_LEFTOVER_REUSE`/`DN_LEFTOVER_THALI` cluster on solo/working/time-pressured personas.
**Rule:** → those classes.

### Rule G — `cost_bias` and `novelty_bias`
**Evidence:** budget personas — leftover/simple classes; foodie (P27) uniquely carries `SN_BAKERY_CAFE`, `SN_MOMO_NOODLES_SNACK`, `LD_INDO_CHINESE_MEAL`, `BF_OUTSIDE_CAFE_BRUNCH`, `DN_WEEKEND_INDULGENCE` boosted.
**Rule:** budget — simplicity/reuse classes; premium/experimental — café/international/indulgence classes.

### Rule H — `meal_energy_pattern=heavy_breakfast`
**Evidence:** P38 field-work uniquely carries `BF_FIELD_WORK_HEAVY`; the only rule that shifts *which meal carries the caloric load* rather than what's in it.

---

## 3. What stays condition-specific (Layer 3, correctly NOT generalized)

Specialization classes that genuinely belong to one condition and should remain attached to it (not forced into shared attributes): pregnancy (`LD_PREGNANCY_BALANCED`), lactation (`BF_LACTATION_MOTHER`, `LD_LACTATION_POSTPARTUM`), infant weaning (`BF_INFANT_6M_SOFT`), teen calories (`LD_TEEN_HIGH_CALORIE`), recovery (`LD_RECOVERY_SOFT_PROTEIN`), and all diet-pattern classes (Jain, fasting, seafood, mutton, biryani — these belong to the diet dimension, Layer F of the decomposition catalog, not to conditions at all).

---

## 4. Validation summary

- **Convergence confirmed empirically, not assumed:** identical class lists across differently-labeled personas (P14≡P36 on BF and DN) prove the research was already operating on shared attribute rules — it just stored the outputs per-persona instead of the rules themselves.
- **The diet gate inside Rule B** (egg/chicken classes present for teen/gym, absent for veg-protein) shows attribute rules must compose with the existing hard-constraint diet dimension — which the architecture already requires (hard constraints filter before scoring). No new mechanism needed.
- **Rules extracted: 8 shared rules + ~12 condition specializations replace 41 hand-attached boost lists** — with no research knowledge lost: every one of the 92 classes is accounted for in Layer 1, 2, or 3.

---

## 5. Next step (Phase 2 readiness)

This document plus the Decomposition Catalog together contain everything Phase 2 (vocabulary fix) and Phase 3 (LF-C add-on build) need: the member-condition vocabulary, the attributes each condition sets, the shared attribute→class rules, and the per-condition specializations. Recommend Founder review of the rules above — especially Rule D's deliberate elderly-gets-low-GI-preventively pattern, which is a real product judgment inherited from the research that should be consciously kept or dropped, not silently carried.
