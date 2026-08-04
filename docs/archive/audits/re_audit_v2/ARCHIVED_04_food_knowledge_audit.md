# STATUS

ARCHIVED

## Reason

Implementation completed.

This document is retained for historical reference only.

It must not be used as the primary implementation guide.

Refer to the active documentation for the current source of truth.

---

STATUS: ARCHIVED
Reason: Superseded by docs/active/ (2026-08-04 documentation restructure). This audit remains the evidentiary source for docs/active/CURRENT_STATUS.md, OPEN_ITEMS.md, ROADMAP.md, and LAUNCH_BLOCKERS.md.

# Food Knowledge & Ontology Audit (fresh, 2026-08-04)

| # | Area | Status | Evidence |
|---|---|---|---|
| 1 | Ingredient ontology | Complete | `ingredients_v5.csv`, 198 ingredients, full attribute set (category/diet/allergen/jain/vegan/farali) |
| 2 | Cuisine hierarchy | Complete | 65 cuisines, 0 unresolved to a zone (verified programmatically) |
| 3 | Meal-class hierarchy | Complete | `hero_role` + `dish_category` + class-first CSV mapping, 810/810 dish coverage |
| 4 | Knowledge graph | **Missing** | No node/edge graph structure anywhere — flat dicts/lists/CSVs only |
| 5 | Region mapping (PRIOR table) | **Partial** | 18/24 core zone×slot cells (North/South/West/East/Central/Northeast × breakfast/lunch/dinner); PanIndia and Global zones (187/810 dishes) have zero rows — intentional per the code's own comment, but a real coverage gap for those dishes |
| 6 | Festival mapping | **Missing** | Only 2 incidental "Festival" usage-tag mentions and one behavioral meal-class; no real field, no calendar |
| 7 | Seasonality | **Partial** | A distinct scoring term exists (`m_season`) but derives its fit from `weather_affinity` tags — no independently-modeled season dimension |
| 8 | Nutrition data | **Partial** | 50/810 dishes (6.2%) have real macro values; wired correctly into the build, just narrow |
| 9 | Substitution graph | **Partial** | 13 curated dish-level pairs, flat lookup (not a graph), built this week, unwired from live scoring |
| 10 | Disease/health-condition mapping | **Missing** | No dish/ingredient-level health-condition data anywhere (all greps for diabetes/BP/kidney/thyroid were false positives) |
| 11 | Weather mapping | Complete as a rule table; weather itself is mocked/injected, no live API |
| 12 | Comfort-food mapping | **Partial** | 17/36 (47%) distinct named heroes resolve to a real catalogue dish |
| 13 | Alias/synonym graph | Complete | 786 live DB rows (`dish_name_synonyms`) + 2 CSVs confirmed wired into `build_catalogue.py` |
| 14 | Hidden allergens | **Partial** | 4 entries, gluten-only coverage (hing/soy-sauce/sambar-powder/chaat-masala) |

## Reconciliation note
An earlier pass in this same session counted comfort-hero resolution two different ways (17 vs 20)
depending on whether duplicate dict values were counted. Verified directly: **17 of 36 distinct
hero names** resolve to a dish actually present in the 810-dish catalogue — use this figure.

## What's genuinely missing vs. what's honestly narrow-scoped
Festival mapping and disease/health mapping are **genuinely absent** — not narrow, absent. Region
mapping, nutrition, substitution, and comfort-hero are all **real but narrow** — each is wired
correctly into the pipeline it's meant to feed, just covering a fraction of the 810-dish catalogue.
The distinction matters for prioritization: narrow-but-wired is an extend-the-data task; absent is
a build-the-feature task.
</content>
