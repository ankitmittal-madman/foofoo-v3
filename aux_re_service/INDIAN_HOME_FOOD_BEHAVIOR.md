# Indian household food-behavior basis

This note separates authoritative nutrition guidance, observations in FooFoo's supplied synthetic
datasets, and product hypotheses. Synthetic observations are useful for feature engineering and
pipeline tests; they are not evidence about the Indian population.

## Authoritative grounding

- India's food-based dietary guidance emphasizes variety, vegetables and fruit, cereal and pulse
  balance, moderation of fats/animal foods, population-specific needs, safe food, and appropriate
  cooking methods. These principles justify weekly variety and safety guardrails, but do not imply
  that the recommender may diagnose a person or infer an allergy. Source: [FAO summary of India's
  NIN-led dietary guidelines](https://www.fao.org/nutrition/education/dietary-guidelines/regions/india/en/).
- ICMR-NIN reports that Indian Food Composition Tables 2017 covers 151 food components across 528
  foods and that Indian nutrient requirements differ by age and physiological group. This is the
  appropriate future basis for quantitative nutrition; the present ontology only carries
  non-quantitative traits. Source: [ICMR-NIN achievements and IFCT
  summary](https://nin.res.in/achievements.html).
- Household food expenditure and consumption differ across rural/urban and expenditure groups, so
  a production model needs representative, weighted household evidence rather than AI-generated
  personas. Source: [MoSPI Household Consumption Expenditure Survey
  collection](https://www.mospi.gov.in/themes/product/71-household-consumption-expenditure-survey-hces).

## What the supplied data actually contains

Dataset 1 contributes 5,000 households, 14,640 members, 10,000 meal-history rows, 10,000
recommendation events, 10,000 member/dish preferences, 19,020 meal-consumer reactions, confirmed
exclusions, cooking capacity, health goals, and 5,000 seasonal/occasion preferences.

Observed synthetic distributions include:

- Meal slots: 3,288 lunch, 3,199 dinner, 2,360 breakfast, and 1,153 snack events.
- Household feedback: 1,203 cooked, 1,194 planned, 941 skipped, 822 substituted, 498 `not_today`,
  and 296 `never` events, plus explicit member reactions and family-vote evidence.
- Household composition: 8,734 adult, 3,560 child, 1,750 elder, 389 infant, and 207 toddler member
  rows.
- Cooking context includes weekday/weekend time budgets, skill, equipment, novelty willingness,
  leftovers, office/home days, monsoon/summer flags, fasting, spice/oil/texture preference, and
  festival/season choices.

Dataset 2 contributes 15,000 additional meal rows and 60 dish names, especially useful for dish and
regional coverage. Its 15,000 meals all use one date (2026-08-01), and its five supporting member,
regional, exclusion, consumer, and feedback samples use orphan ID formats. Therefore Dataset 2 is
used for ontology and meal-pattern enrichment, while orphan feedback is excluded and its temporal
data must not be treated as weekday/weekend evidence.

## Product patterns encoded now

- Breakfast/lunch/dinner and weekday/weekend are separate context signals.
- Household preferences include children/elders/infants, decision model, member reactions,
  conflicting preferences, fasting, spice, cooking capacity, equipment, and comfort dishes.
- Weekly ranking penalizes recent and same-week repetition and considers cooking time, leftovers,
  season, occasion, pantry, regional familiarity, novelty, and safety.
- `substituted`, skips, rejects, low ratings, `never`, and member dislikes become explicit negative
  evidence. The chosen substitute becomes positive evidence.
- Confirmed allergies and exclusions remain hard filters. They are never inferred from avoidance.

## Research gaps that require real evidence

- Representative regional, rural/urban, income, age, religion/culture, and household-size sampling.
- Multi-week plans that reveal sequence, leftovers, fasting, weekday/weekend, and seasonality over
  time rather than generated snapshots.
- Quantitative recipe portions linked to reviewed IFCT ingredient mappings and clinician-approved
  rules for vulnerable household members.
- Consent-aware impression logs, member votes, cooks, skips, substitutions, repeat cooks, and
  outcomes from the real product. Until those exist, all learned models remain shadow-only.
