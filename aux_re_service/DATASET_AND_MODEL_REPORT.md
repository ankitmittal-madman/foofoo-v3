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

The v1 snapshot contains 86 canonical dishes, 10,000 households, and 35,000 interactions: 21,565
positive and 5,267 negative. Artifacts have SHA-256 checksums in `data/training/v1/manifest.json`.

## Measured model result

LightFM WARP hybrid was trained in pinned Python 3.11 and evaluated with a per-household time split
over 7,313 holdout interactions.

| Metric @10 | LightFM | Popularity baseline |
|---|---:|---:|
| Recall | 0.3635 | 0.1269 |
| Precision | 0.0363 | 0.0127 |
| NDCG | 0.1391 | 0.0547 |
| Catalogue coverage | 0.8721 | 0.1395 |

The offline gate passes for shadow use. Production activation remains blocked by synthetic-only
training and missing online shadow/A/B evidence. Runtime verification proved that shadow mode loads
the artifact and scores 86 candidates while preserving the existing engine output. Active mode
returns `synthetic_artifact_shadow_only` and does not apply the model.

## Model readiness

- LightFM: implemented, packaged, tested, and shadow-ready; not active-ready.
- Qdrant: 86 real canonical dish payloads/vectors uploaded and queried successfully with slot,
  region, diet, allergen, and unavailable-ingredient filtering.
- LightGCN: deferred because there are zero real interactions and no households with five synthetic
  positive events in this sparse snapshot.
- KGAT: deferred for the same interaction reasons and because only 43.0% of dishes currently have
  ingredient coverage.

The weekly and change-triggered workflow `.github/workflows/aux-re-quality.yml` runs tests, validates
checksums/counts/vectors/model metrics, confirms the shadow-only contract, builds the service image,
and uploads its quality report.
