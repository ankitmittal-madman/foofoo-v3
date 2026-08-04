# STATUS

ARCHIVED

## Reason

Implementation completed.

This document is retained for historical reference only.

It must not be used as the primary implementation guide.

Refer to the active documentation for the current source of truth.

---

# Session log — test_10
_generated 2026-08-03T03:25:19.902904+00:00 · slot=dinner weekday=Wednesday · engine Spine v1.0_

## 1. Onboarding inputs (raw)
- `q1_household_type` = couple_kids
- `q3_home_state` = MP
- `q4_current_city` = Mumbai
- `q5_diet` = veg
- `q13_who_cooks` = self
- `q14_eat_out_per_week` = 1
- `q15_objective` = awesome_taste
- `q11_conditions` = ['toddler']

## 2. θ — derived household profile
- **home_state** = Madhya Pradesh
- **region** = Central
- **city_tier** = T1
- **is_migrant** = True
- **local_state** = Maharashtra
- **blend** = 0.73
- **diet** = veg
- **spice_ceiling** = 1
- **lifecycle_stage** = toddler
- **time_pressure** = 0.75
- **time_route** = SIMPLIFY
- **objective** = awesome_taste

## 3. Cohort feature vector (what the model keys on)
```
state_ut          = Madhya Pradesh
region_archetype  = CENTRAL_MIXED
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
- destination_group = **MUMBAI_PUNE** · migrant = True
- weights → home 0.55 / city 0.3 / national 0.15  _(overlay applied — migrant)_

## 6. Class plan — compositional + learned (dinner/weekday)
**Compositional plan (WP-17: persona core ∩ state pool + migration, spine-filtered):**
- 1.00  `DN_CHILD_FRIENDLY_DINNER`
- 1.00  `DN_LIGHT_DAL_RICE`
- 0.70  `LD_CHILD_MILD_PLATE`
- 0.60  `DN_LIGHT_ROTI_SABZI`
- 0.60  `BF_POHA_CHIVDA_LIGHT`
- 0.55  `LD_LIGHT_KHICHDI`
- 0.46  `LD_DAL_ROTI_SABZI`
- 0.44  `LD_MAHARASHTRIAN_PITLA_BHAKRI`

**Fused affinity (compositional×0.7 + learned×0.3, what scoring uses):**
- 1.00  `DN_LIGHT_DAL_RICE`
- 0.86  `DN_LIGHT_ROTI_SABZI`
- 0.83  `DN_CHILD_FRIENDLY_DINNER`
- 0.58  `LD_CHILD_MILD_PLATE`
- 0.50  `BF_POHA_CHIVDA_LIGHT`
- 0.46  `LD_LIGHT_KHICHDI`
- 0.42  `LD_MAHARASHTRIAN_PITLA_BHAKRI`
- 0.38  `LD_DAL_ROTI_SABZI`

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
1. **[4.92]** Undhiyu + Gujarati Toor Dal  (+ Roti)
2. **[4.56]** Kanda Bhaji + Gujarati Kadhi  (+ Rice)
3. **[3.91]** Lauki Sabzi + Sarson Ka Saag  (+ Roti)
4. **[3.87]** Medu Vada + Rasam  (+ Rice)
5. **[3.81]** Onion Pakora + Chole  (+ Poori)
6. **[3.67]** Cabbage Sabzi + Moong Dal  (+ Roti)
7. **[3.57]** Dhokla + Pithla  (+ Roti)

## 9. Per-dish scoring (dishes in the served plates)
| dish | zone | m_palette | sig | BASE | GAIN | s_cohort | s_foreign | score |
|---|---|---|---|---|---|---|---|---|
| Gujarati Toor Dal | West | 0.11 | 0.40 | 1.55 | 1.05 | 0.00 | 0 | 1.63 |
| Undhiyu | West | 0.11 | 0.90 | 1.59 | 1.18 | 0.00 | 0 | 1.88 |
| Kanda Bhaji | West | 0.27 | 0.60 | 1.66 | 1.21 | 0.00 | 0 | 2.02 |
| Gujarati Kadhi | West | 0.11 | 0.40 | 1.55 | 1.05 | 0.00 | 0 | 1.63 |
| Lauki Sabzi | North | 0.00 | 0.40 | 1.44 | 1.01 | 0.34 | 0 | 1.65 |
| Sarson Ka Saag | North | 0.00 | 0.90 | 1.48 | 1.17 | 0.00 | 0 | 1.74 |
| Rasam | South | 0.00 | 0.60 | 1.39 | 1.01 | 0.00 | 0 | 1.40 |
| Medu Vada | South | 0.00 | 0.60 | 1.39 | 1.21 | 0.00 | 0 | 1.69 |
| Onion Pakora | North | 0.00 | 0.60 | 1.39 | 1.22 | 0.00 | 0 | 1.70 |
| Chole | North | 0.00 | 0.60 | 1.22 | 1.11 | 0.00 | 0 | 1.35 |
