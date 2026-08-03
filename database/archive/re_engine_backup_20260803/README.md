# re_engine schema backup — 2026-08-03

Full JSON export of every populated table in the **legacy TypeScript-RE** schema
`re_engine`, taken before the WP-20 decommission of that schema. One `<table>.json`
file per table, each an array of row objects (`to_jsonb`).

**Why:** `re_engine` is the pre-"Ghar RE v1.0 rebuild" engine's schema (superseded by
the `ghar_re` offline knowledge schema + the bundle-based Python RE service). Most of its
~32k rows are precomputed reference data (weekly class plans, cohorts, addon plans) derived
from `data/source/Indian_Meal_Cohort_Persona_DB_v3.xlsx`. This archive guarantees no seeded
record is lost when the schema is dropped, and lets any row be restored or inspected later.

**Row counts at backup time:**
re_weekly_class_plans 20664 · re_household_addon_plans 7992 · re_cohorts 2952 ·
re_class_dish_options 165 · re_meal_classes 131 · re_dish_regional_affinity 130 ·
re_persona_assignment_rules 82 · re_personas 41 · re_subcohorts 41 · re_states 36 ·
re_nonveg_logic 36 · re_addon_classes 24 · re_routing_rules 16 · re_meal_class_overlap_rules 13 ·
re_scoring_config 13 · re_confidence_config 12 · re_event_weights 8 · re_addon_dish_options 6 ·
re_city_overlay_config 6 · re_class_affinity_config 6 · re_variety_rules 6 · re_main_cohorts 5 ·
re_weight_ladder_config 5 · re_context_multipliers 4 · re_festival_calendar 2 · re_engine_versions 1

Empty at backup (no file): dish_features, never_list, not_today_suppression,
re_city_migration_overlays, re_cohort_class_priors, re_dish_bandit_state, user_re_state,
user_taste_vectors, variety_window_state.
