# Session log — test_14
_generated 2026-08-03T02:47:04.130554+00:00 · slot=dinner weekday=Saturday · engine Spine v1.0_

## 1. Onboarding inputs (raw)
- `q1_household_type` = couple_kids
- `q3_home_state` = MH
- `q4_current_city` = Pune
- `q5_diet` = veg
- `q13_who_cooks` = self
- `q14_eat_out_per_week` = 0
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
- **time_pressure** = 0.8
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

## 4. Sub-cohort membership (nearest persona anchors — explainability)
- P39 · desk_job_sedentary · match 0.667
- P17 · weight_loss_calorie_conscious · match 0.667
- P11 · family_with_school_kids · match 0.667
- P10 · family_with_toddler · match 0.667

## 5. Migration / region blend
- destination_group = **HOME_STATE_TIER1** · migrant = False
- weights → home 0.7 / city 0.2 / national 0.1  _(overlay NOT applied — home-state resident)_

## 6. Class affinity — learned model (dinner/weekend)
- 1.00  `LD_FESTIVE_THALI`
- 0.60  `LD_WEEKEND_SPECIAL_REGIONAL`

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
1. **[6.82]** Bharli Vangi + Amti  (+ Roti)
2. **[5.42]** Sannas + Pithla Bhakri  (+ Roti)
3. **[4.40]** Begun Bhaja + Dalma  (+ Roti)
4. **[4.36]** Aloo Gobhi + Dal Makhani  (+ Roti)
5. **[4.33]** Aloo Posto + Cholar Dal  (+ Roti)
6. **[4.23]** Mochar Ghonto + Tok Dal  (+ Roti)
7. **[4.22]** Poriyal + Parippu Curry  (+ Roti)

## 9. Per-dish scoring (dishes in the served plates)
| dish | zone | m_palette | sig | BASE | GAIN | s_cohort | s_foreign | score |
|---|---|---|---|---|---|---|---|---|
| Bharli Vangi | West | 1.00 | 0.75 | 2.44 | 1.13 | 0.00 | 0 | 2.77 |
| Amti | West | 1.00 | 0.75 | 2.44 | 1.02 | 0.00 | 0 | 2.48 |
| Sannas | West | 0.40 | 0.75 | 1.95 | 1.09 | 0.00 | 0 | 2.12 |
| Pithla Bhakri | West | 1.00 | 0.75 | 2.44 | 1.06 | 0.00 | 0 | 2.60 |
| Begun Bhaja | East | 0.00 | 0.75 | 1.54 | 1.16 | 0.00 | 0 | 1.79 |
| Dalma | East | 0.00 | 0.60 | 1.50 | 1.06 | 0.00 | 0 | 1.59 |
| Aloo Gobhi | North | 0.00 | 0.75 | 1.44 | 1.06 | 0.00 | 0 | 1.52 |
| Dal Makhani | North | 0.00 | 0.75 | 1.54 | 1.19 | 0.00 | 0 | 1.84 |
| Aloo Posto | East | 0.00 | 0.75 | 1.54 | 1.02 | 0.00 | 0 | 1.58 |
| Cholar Dal | East | 0.00 | 0.75 | 1.54 | 1.14 | 0.00 | 0 | 1.76 |
