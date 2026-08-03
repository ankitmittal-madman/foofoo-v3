# Session log — test_13
_generated 2026-08-03T02:47:04.098800+00:00 · slot=dinner weekday=Saturday · engine Spine v1.0_

## 1. Onboarding inputs (raw)
- `q1_household_type` = couple_kids
- `q3_home_state` = GJ
- `q4_current_city` = Pune
- `q5_diet` = veg
- `q13_who_cooks` = self
- `q14_eat_out_per_week` = 2
- `q15_objective` = awesome_taste
- `q11_conditions` = []

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
- **time_pressure** = 0.7
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

## 4. Sub-cohort membership (nearest persona anchors — explainability)
- P39 · desk_job_sedentary · match 0.667
- P17 · weight_loss_calorie_conscious · match 0.667
- P11 · family_with_school_kids · match 0.667
- P10 · family_with_toddler · match 0.667

## 5. Migration / region blend
- destination_group = **MUMBAI_PUNE** · migrant = False
- weights → home 0.55 / city 0.3 / national 0.15  _(overlay NOT applied — home-state resident)_

## 6. Class affinity — learned model (dinner/weekend)
- 1.00  `LD_FESTIVE_THALI`
- 0.47  `LD_WEEKEND_SPECIAL_REGIONAL`
- 0.27  `DN_LIGHT_ROTI_SABZI`
- 0.23  `LD_MAHARASHTRIAN_PITLA_BHAKRI`

- cohort weight w_cohort(n=0) = **0.60** · foreign_demote(n=0) = **0.80**

## 7. Eligibility funnel
```
catalogue_total         : 810
after_diet_filter       : 539
after_jain_filter       : 539
after_allergen_filter   : 539
after_fasting_filter    : 539
```

## 8. Final plates (Assemble-7)
1. **[6.59]** Bharli Vangi + Dal Dhokli  (+ Roti)
2. **[5.42]** Sannas + Gujarati Dal  (+ Roti)
3. **[4.51]** Aloo Gobhi + Dal Makhani  (+ Roti)
4. **[4.40]** Begun Bhaja + Dalma  (+ Roti)
5. **[4.33]** Aloo Posto + Cholar Dal  (+ Roti)
6. **[4.32]** Stuffed Capsicum + Dal Tadka  (+ Roti)
7. **[4.30]** Thoran (Cabbage) + Vengaya Sambar  (+ Rice)

## 9. Per-dish scoring (dishes in the served plates)
| dish | zone | m_palette | sig | BASE | GAIN | s_cohort | s_foreign | score |
|---|---|---|---|---|---|---|---|---|
| Bharli Vangi | West | 0.40 | 0.75 | 1.95 | 1.13 | 0.23 | 0 | 2.35 |
| Dal Dhokli | West | 1.00 | 0.75 | 2.55 | 1.07 | 0.00 | 0 | 2.72 |
| Sannas | West | 0.40 | 0.75 | 1.95 | 1.09 | 0.00 | 0 | 2.12 |
| Gujarati Dal | West | 1.00 | 0.75 | 2.55 | 1.02 | 0.00 | 0 | 2.59 |
| Aloo Gobhi | North | 0.00 | 0.75 | 1.54 | 1.06 | 0.00 | 0 | 1.63 |
| Dal Makhani | North | 0.00 | 0.75 | 1.54 | 1.19 | 0.00 | 0 | 1.84 |
| Begun Bhaja | East | 0.00 | 0.75 | 1.54 | 1.16 | 0.00 | 0 | 1.79 |
| Dalma | East | 0.00 | 0.60 | 1.50 | 1.06 | 0.00 | 0 | 1.59 |
| Aloo Posto | East | 0.00 | 0.75 | 1.54 | 1.02 | 0.00 | 0 | 1.58 |
| Cholar Dal | East | 0.00 | 0.75 | 1.54 | 1.14 | 0.00 | 0 | 1.76 |
