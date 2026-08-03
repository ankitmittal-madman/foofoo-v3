# Session log — test_10
_generated 2026-08-03T02:47:04.047989+00:00 · slot=dinner weekday=Saturday · engine Spine v1.0_

## 1. Onboarding inputs (raw)
- `q1_household_type` = couple_kids
- `q3_home_state` = MP
- `q4_current_city` = Mumbai
- `q5_diet` = veg
- `q13_who_cooks` = self
- `q14_eat_out_per_week` = 0
- `q15_objective` = awesome_taste
- `q11_conditions` = []

## 2. θ — derived household profile
- **home_state** = Madhya Pradesh
- **region** = Central
- **city_tier** = T1
- **is_migrant** = True
- **local_state** = Maharashtra
- **blend** = 0.73
- **diet** = veg
- **spice_ceiling** = 4
- **lifecycle_stage** = none
- **time_pressure** = 0.5
- **time_route** = SIMPLIFY
- **objective** = awesome_taste

## 3. Cohort feature vector (what the model keys on)
```
state_ut          = Madhya Pradesh
region_archetype  = CENTRAL_MIXED
city_tier_code    = T1
main_cohort_id    = MC3
lifecycle_stage   = none
time_pressure     = medium
nonveg_mode       = veg_default
```

## 4. Sub-cohort membership (nearest persona anchors — explainability)
- P36 · recovery_senior_light · match 0.667
- P26 · budget_family · match 0.667
- P21 · fasting_ritual · match 0.667
- P19 · vegetarian_protein · match 0.667

## 5. Migration / region blend
- destination_group = **MUMBAI_PUNE** · migrant = True
- weights → home 0.55 / city 0.3 / national 0.15  _(overlay applied — migrant)_

## 6. Class affinity — learned model (dinner/weekend)
- 1.00  `LD_WEEKEND_SPECIAL_REGIONAL`
- 0.68  `LD_FESTIVE_THALI`
- 0.19  `DN_LIGHT_ROTI_SABZI`
- 0.19  `LD_MAHARASHTRIAN_PITLA_BHAKRI`

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
1. **[5.22]** Bharli Vangi + Amti  (+ Roti)
2. **[4.51]** Aloo Gobhi + Dal Makhani  (+ Roti)
3. **[4.40]** Begun Bhaja + Dalma  (+ Roti)
4. **[4.33]** Aloo Posto + Cholar Dal  (+ Roti)
5. **[4.32]** Sannas + Pithla  (+ Roti)
6. **[4.32]** Stuffed Capsicum + Dal Tadka  (+ Roti)
7. **[4.30]** Thoran (Cabbage) + Vengaya Sambar  (+ Rice)

## 9. Per-dish scoring (dishes in the served plates)
| dish | zone | m_palette | sig | BASE | GAIN | s_cohort | s_foreign | score |
|---|---|---|---|---|---|---|---|---|
| Bharli Vangi | West | 0.27 | 0.75 | 1.81 | 1.13 | 0.19 | 0 | 2.17 |
| Amti | West | 0.27 | 0.75 | 1.81 | 1.02 | 0.00 | 0 | 1.85 |
| Aloo Gobhi | North | 0.00 | 0.75 | 1.54 | 1.06 | 0.00 | 0 | 1.63 |
| Dal Makhani | North | 0.00 | 0.75 | 1.54 | 1.19 | 0.00 | 0 | 1.84 |
| Begun Bhaja | East | 0.00 | 0.75 | 1.54 | 1.16 | 0.00 | 0 | 1.79 |
| Dalma | East | 0.00 | 0.60 | 1.50 | 1.06 | 0.00 | 0 | 1.59 |
| Aloo Posto | East | 0.00 | 0.75 | 1.54 | 1.02 | 0.00 | 0 | 1.58 |
| Cholar Dal | East | 0.00 | 0.75 | 1.54 | 1.14 | 0.00 | 0 | 1.76 |
| Sannas | West | 0.11 | 0.75 | 1.65 | 1.09 | 0.00 | 0 | 1.80 |
| Pithla | West | 0.27 | 0.75 | 1.81 | 1.02 | 0.19 | 0 | 1.96 |
