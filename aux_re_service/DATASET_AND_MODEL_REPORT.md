# Dataset and model evidence

Generated on 2026-08-07. All runtime AI/ML is fully local; no paid model or external AI call is
used.

## Source audit

| Source | Useful content | Decision |
|---|---:|---|
| Dataset 1 workbook | 5,000 households, 14,640 members, 10,000 meal-history rows, 10,000 recommendation events, 37 dishes | Primary interaction and household source |
| Dataset 2 workbook | 5,000 households, 15,000 meal-history rows, 60 dishes | Meal-history and ontology enrichment |
| Dataset 2 supporting rows | 5-row samples with mismatched `HH-0001`/`HH00001` and user IDs | Audited as orphaned; they cannot enter LightFM because no matching household feature exists |
| Dataset 1 catalogue | 29 states, 31 cities, 20 personas, 24 household types, 37 seed dishes | Geography and household vocabulary |
| Existing recipe catalogue | 810 recipes | Ingredient, allergen, diet, cuisine, and technique enrichment |

Both workbooks identify themselves as generated synthetic data. They are useful for engineering and
offline shadow validation, not proof of production preference quality.

## Canonical training contract

- Dish: canonical ID/name, aliases, ingredients, allergens, diet types, cuisines, regions, observed
  regions, meal slots, cooking methods, and sources.
- Household: namespaced household ID plus state, origin, setup, size, diet, and regional features.
- Interaction: household ID, canonical dish ID, timestamp, meal slot, signed weight, event type, and
  source dataset. Likes/cooks/repeats/rating signals are positive; skips/rejects/low ratings are
  negative.
- Graph: typed nodes and relations such as `contains`, `belongs_to`, `eaten_in`, `served_at`,
  `compatible_with`, and `cooked_with`.
- Retrieval: one deterministic 64-dimensional local vector and filterable payload per canonical
  dish.

The v2 canonical snapshot contains 86 dishes and 10,000 households. It now uses recommendation
events, meal history, member reactions, explicit dish preferences, family-vote evidence, and chosen
substitutes: 64,842 interactions, including 46,047 positive and 17,459 negative rows. It also
contains 10,000 weekly-signal rows, 29,020 household/member graph edges, and disjoint train,
validation, and test tables. Artifacts have SHA-256 checksums in `data/training/v1/manifest.json`.

## Measured model result

LightFM WARP hybrid v2 was trained in pinned Python 3.11 with 17,459 negative events affecting the
eligible positive pairs. It was evaluated on a harder, leakage-resistant 4,219-household holdout.

| Metric @10 | LightFM | Popularity baseline |
|---|---:|---:|
| Recall | 0.1093 | 0.0351 |
| Precision | 0.0109 | 0.0035 |
| NDCG | 0.0393 | 0.0149 |
| Catalogue coverage | 0.6047 | 0.1395 |

The offline gate passes for shadow use. Production activation remains blocked by synthetic-only
training and missing online shadow/A/B evidence. Runtime verification proved that shadow mode loads
the artifact and scores 86 candidates while preserving the existing engine output. Active mode
returns `synthetic_artifact_shadow_only` and does not apply the model.

## Model readiness

- LightFM: implemented, packaged, tested, and shadow-ready; not active-ready.
- Qdrant: 86 real canonical dish payloads/vectors uploaded and queried successfully with slot,
  region, diet, allergen, and unavailable-ingredient filtering.
- LightGCN: its RecBole input is exported, but training is deferred because there are zero real
  interactions and only 4,357 households have five positive synthetic events.
- KGAT: deferred for the same interaction reasons and because only 43.0% of dishes currently have
  ingredient coverage.

The weekly and change-triggered workflow `.github/workflows/aux-re-quality.yml` runs tests, validates
checksums/counts/vectors/model metrics, confirms the shadow-only contract, builds the service image,
and uploads its quality report.
