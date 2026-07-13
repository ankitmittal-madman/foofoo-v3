-- Migration: 016_dish_features.sql
-- Implements: DOC-P3-04 v1.3 §03.29 (re_engine.dish_features)
-- Logical functions: LF-J09 (dailyDishFeatureSnapshot)
-- Governance refs: DOC-P3-05 Part (a) Phase 7 (prerequisite: 008, soft reference to dishes,
--   same non-enforced pattern as re_class_dish_options per P3-04 §03.27 note)
-- CDM entities: Entity 15 (Dish, via feature snapshot)
-- CDM invariants enforced: none — this is an ML feature-store table, intentionally retained
--   indefinitely per DOC-P3-04 §07 retention policy

CREATE TABLE re_engine.dish_features (
  dish_id              uuid NOT NULL,
  snapshot_date         date NOT NULL,
  genome_tags_json        jsonb,
  meal_class_codes         text[],
  popularity_score          real,
  acceptance_rate_7d          real,
  acceptance_rate_30d           real,
  best_slot                       text,
  best_day                          text,
  PRIMARY KEY (dish_id, snapshot_date)
);
