# Session log — test_14
_generated 2026-08-03T03:25:19.937847+00:00 · slot=dinner weekday=Wednesday · engine Spine v1.0_

## 1. Onboarding inputs (raw)
- `q1_household_type` = couple_kids
- `q3_home_state` = MH
- `q4_current_city` = Pune
- `q5_diet` = veg
- `q13_who_cooks` = self
- `q14_eat_out_per_week` = 1
- `q15_objective` = awesome_taste
- `q11_conditions` = ['toddler']

## 2. θ — derived household profile
- **home_state** = Maharashtra
- **region** = West
- **city_tier** = T1
- **is_migrant** = False
- **local_state** = Maharashtra
- **blend** = 1.0
- **diet** = veg
- **spice_ceiling** = 1
- **lifecycle_stage** = toddler
- **time_pressure** = 0.75
- **time_route** = SIMPLIFY
- **objective** = awesome_taste

## 3. Cohort feature vector (what the model keys on)
```
state_ut          = Maharashtra
region_archetype  = WEST_COASTAL
city_tier_code    = T1
main_cohort_id    = MC3
lifecycle_stage   = toddler
time_pressure     = high
nonveg_mode       = veg_default
```

## 4. Resolved persona + sub-cohort membership
**Compositional persona resolution (WP-17 — the plan core):**
- **P10** · family_with_toddler · match 1.0
- **P11** · family_with_school_kids · match 0.429
- **P17** · weight_loss_calorie_conscious · match 0.429

_nearest anchors (learned-model explainability):_
- P39 · desk_job_sedentary · match 0.667
- P17 · weight_loss_calorie_conscious · match 0.667
- P11 · family_with_school_kids · match 0.667

## 5. Migration / region blend
- destination_group = **HOME_STATE_TIER1** · migrant = False
- weights → home 0.7 / city 0.2 / national 0.1  _(overlay NOT applied — home-state resident)_

## 6. Class plan — compositional + learned (dinner/weekday)
**Compositional plan (WP-17: persona core ∩ state pool + migration, spine-filtered):**
- 1.00  `DN_CHILD_FRIENDLY_DINNER`
- 1.00  `DN_LIGHT_DAL_RICE`
- 0.70  `LD_CHILD_MILD_PLATE`
- 0.55  `DN_LIGHT_ROTI_SABZI`
- 0.46  `LD_DAL_ROTI_SABZI`
- 0.41  `LD_MAHARASHTRIAN_PITLA_BHAKRI`
- 0.41  `LD_COCONUT_VEG_STEW`
- 0.39  `LD_SIMPLE_GREEN_VEG_SABZI`

**Fused affinity (compositional×0.7 + learned×0.3, what scoring uses):**
- 1.00  `DN_LIGHT_DAL_RICE`
- 0.81  `DN_CHILD_FRIENDLY_DINNER`
- 0.79  `DN_LIGHT_ROTI_SABZI`
- 0.57  `LD_CHILD_MILD_PLATE`
- 0.37  `LD_DAL_ROTI_SABZI`
- 0.33  `LD_COCONUT_VEG_STEW`
- 0.33  `LD_MAHARASHTRIAN_PITLA_BHAKRI`
- 0.32  `LD_SIMPLE_GREEN_VEG_SABZI`

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
1. **[6.40]** Kanda Bhaji + Pithla  (+ Roti)
2. **[5.83]** Undhiyu + Gujarati Toor Dal  (+ Roti)
3. **[4.75]** Cabbage Sabzi + Moong Dal  (+ Roti)
4. **[3.89]** Lauki Sabzi + Sarson Ka Saag  (+ Roti)
5. **[3.87]** Medu Vada + Rasam  (+ Rice)
6. **[3.81]** Onion Pakora + Chole  (+ Poori)
7. **[3.51]** Aloo Gobi + Punjabi Kadhi Pakora  (+ Rice)

## 9. Per-dish scoring (dishes in the served plates)
| dish | zone | m_palette | sig | BASE | GAIN | s_cohort | s_foreign | score |
|---|---|---|---|---|---|---|---|---|
| Kanda Bhaji | West | 1.00 | 0.60 | 2.40 | 1.21 | 0.00 | 0 | 2.91 |
| Pithla | West | 1.00 | 0.40 | 2.34 | 1.05 | 0.33 | 0 | 2.66 |
| Gujarati Toor Dal | West | 0.40 | 0.40 | 1.84 | 1.05 | 0.00 | 0 | 1.94 |
| Undhiyu | West | 0.40 | 0.90 | 1.88 | 1.18 | 0.00 | 0 | 2.23 |
| Moong Dal | West | 0.40 | 0.40 | 1.84 | 1.01 | 0.00 | 0 | 1.87 |
| Cabbage Sabzi | West | 1.00 | 0.40 | 2.44 | 1.01 | 0.32 | 0 | 2.65 |
| Lauki Sabzi | North | 0.00 | 0.40 | 1.44 | 1.01 | 0.32 | 0 | 1.64 |
| Sarson Ka Saag | North | 0.00 | 0.90 | 1.48 | 1.17 | 0.00 | 0 | 1.74 |
| Rasam | South | 0.00 | 0.60 | 1.39 | 1.01 | 0.00 | 0 | 1.40 |
| Medu Vada | South | 0.00 | 0.60 | 1.39 | 1.21 | 0.00 | 0 | 1.69 |
