# STATUS

ARCHIVED

## Reason

Implementation completed.

This document is retained for historical reference only.

It must not be used as the primary implementation guide.

Refer to the active documentation for the current source of truth.

---

# Session log — test_13
_generated 2026-08-03T03:25:19.932592+00:00 · slot=dinner weekday=Wednesday · engine Spine v1.0_

## 1. Onboarding inputs (raw)
- `q1_household_type` = couple_kids
- `q3_home_state` = Gujarat
- `q4_current_city` = Pune
- `q5_diet` = veg
- `q13_who_cooks` = self
- `q14_eat_out_per_week` = 1
- `q15_objective` = awesome_taste
- `q11_conditions` = ['school_child']

## 2. θ — derived household profile
- **home_state** = Gujarat
- **region** = West
- **city_tier** = T1
- **is_migrant** = False
- **local_state** = Maharashtra
- **blend** = 1.0
- **diet** = veg
- **spice_ceiling** = 2
- **lifecycle_stage** = school_child
- **time_pressure** = 0.75
- **time_route** = SIMPLIFY
- **objective** = awesome_taste

## 3. Cohort feature vector (what the model keys on)
```
state_ut          = Gujarat
region_archetype  = WEST_VEG
city_tier_code    = T1
main_cohort_id    = MC3
lifecycle_stage   = school_child
time_pressure     = high
nonveg_mode       = veg_default
```

## 4. Resolved persona + sub-cohort membership
**Compositional persona resolution (WP-17 — the plan core):**
- **P11** · family_with_school_kids · match 1.0
- **P35** · child_picky_eater · match 1.0
- **P10** · family_with_toddler · match 0.429

_nearest anchors (learned-model explainability):_
- P39 · desk_job_sedentary · match 0.667
- P17 · weight_loss_calorie_conscious · match 0.667
- P11 · family_with_school_kids · match 0.667

## 5. Migration / region blend
- destination_group = **MUMBAI_PUNE** · migrant = False
- weights → home 0.55 / city 0.3 / national 0.15  _(overlay NOT applied — home-state resident)_

## 6. Class plan — compositional + learned (dinner/weekday)
**Compositional plan (WP-17: persona core ∩ state pool + migration, spine-filtered):**
- 1.00  `DN_CHILD_FRIENDLY_DINNER`
- 0.70  `LD_CHILD_MILD_PLATE`
- 0.65  `DN_FAMILY_COMFORT_MEAL`
- 0.60  `DN_LIGHT_ROTI_SABZI`
- 0.60  `BF_POHA_CHIVDA_LIGHT`
- 0.55  `DN_LIGHT_DAL_RICE`
- 0.55  `LD_LIGHT_KHICHDI`
- 0.52  `LD_DAL_ROTI_SABZI`

**Fused affinity (compositional×0.7 + learned×0.3, what scoring uses):**
- 1.00  `DN_LIGHT_ROTI_SABZI`
- 0.97  `DN_CHILD_FRIENDLY_DINNER`
- 0.73  `DN_LIGHT_DAL_RICE`
- 0.68  `LD_CHILD_MILD_PLATE`
- 0.63  `DN_FAMILY_COMFORT_MEAL`
- 0.58  `BF_POHA_CHIVDA_LIGHT`
- 0.54  `LD_LIGHT_KHICHDI`
- 0.51  `LD_DAL_ROTI_SABZI`

- cohort weight w_cohort(n=0) = **0.60** · foreign_demote(n=0) = **0.80**

## 7. Eligibility funnel
```
catalogue_total         : 39
after_diet_filter       : 36
after_jain_filter       : 36
after_allergen_filter   : 36
after_fasting_filter    : 36
```

## 8. Final plates (Assemble-7)
1. **[8.22]** Undhiyu + Gujarati Toor Dal  (+ Roti)
2. **[6.09]** Kanda Bhaji + Gujarati Kadhi  (+ Rice)
3. **[5.19]** Pumpkin Sabzi + Moong Dal  (+ Roti)
4. **[4.77]** Dhokla + Pithla  (+ Roti)
5. **[4.16]** Medu Vada + Rasam  (+ Rice)
6. **[4.11]** Onion Pakora + Chole  (+ Poori)
7. **[4.08]** Lauki Sabzi + Sarson Ka Saag  (+ Roti)

## 9. Per-dish scoring (dishes in the served plates)
| dish | zone | m_palette | sig | BASE | GAIN | s_cohort | s_foreign | score |
|---|---|---|---|---|---|---|---|---|
| Gujarati Toor Dal | West | 1.00 | 0.40 | 2.44 | 1.05 | 0.00 | 0 | 2.57 |
| Undhiyu | West | 1.00 | 0.90 | 2.59 | 1.18 | 0.40 | 0 | 3.30 |
| Kanda Bhaji | West | 0.40 | 0.60 | 1.90 | 1.21 | 0.00 | 0 | 2.31 |
| Gujarati Kadhi | West | 1.00 | 0.40 | 2.44 | 1.05 | 0.00 | 0 | 2.57 |
| Moong Dal | West | 1.00 | 0.40 | 2.44 | 1.01 | 0.00 | 0 | 2.48 |
| Pumpkin Sabzi | West | 1.00 | 0.40 | 2.44 | 1.01 | 0.00 | 0 | 2.47 |
| Dhokla | West | 1.00 | 0.60 | 2.50 | 1.01 | 0.00 | 0 | 2.53 |
| Pithla | West | 0.40 | 0.40 | 1.84 | 1.05 | 0.49 | 0 | 2.24 |
| Rasam | South | 0.00 | 0.60 | 1.50 | 1.01 | 0.00 | 0 | 1.51 |
| Medu Vada | South | 0.00 | 0.60 | 1.50 | 1.21 | 0.00 | 0 | 1.82 |
