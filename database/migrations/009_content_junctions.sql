-- Migration: 009_content_junctions.sql
-- Implements: DOC-P3-04 v1.2 §03.7 (dish_ingredients), §03.9 (dish_tags), §03.10 (dish_combo_items)
-- Logical functions: LF-D03/H02/K01 (dish_ingredients — safety-critical join, GR-06),
--   LF-K02/K04 (dish_tags), CDM Entity 19 (dish_combo_items)
-- Governance refs: DOC-P3-05 Part (a) Phase 7 (prerequisite: 002 for ingredient/tag FKs,
--   008 for dish/combo FKs)
-- CDM entities: Entity 18 (Ingredient, via junction), Entity 16/17 (Food DNA/Genome Tag, via
--   junction), Entity 19 (Dish Combo, via junction)
-- CDM invariants enforced: Invariant 3 (ingredient-level allergen safety — this junction table
--   IS the mechanism GR-06 requires; the safety gate and hard-constraint filter queries that
--   read through it are Part (d)/DOC-P4 concerns, not created here)
-- Note: indexes (idx_dish_ingredients_ingredient, idx_dish_tags_tag) and RLS policies are NOT
-- created here — see 020/019.
-- Note: the triggers that fire on these tables (trg_derive_dish_attributes on dish_ingredients,
-- trg_update_genome_vector on dish_tags) are allocated to file 010 per Phase 8.2, NOT here.

CREATE TABLE public.dish_ingredients (
  dish_id        uuid NOT NULL REFERENCES public.dishes(id) ON DELETE CASCADE,
  ingredient_id  uuid NOT NULL REFERENCES public.ingredients(id),
  is_optional    boolean NOT NULL DEFAULT false,
  PRIMARY KEY (dish_id, ingredient_id)
);

CREATE TABLE public.dish_tags (
  dish_id      uuid NOT NULL REFERENCES public.dishes(id) ON DELETE CASCADE,
  tag_id       uuid NOT NULL REFERENCES public.tags(id),
  confidence   real NOT NULL DEFAULT 1.0 CHECK (confidence BETWEEN 0 AND 1),
  PRIMARY KEY (dish_id, tag_id)
);

CREATE TABLE public.dish_combo_items (
  combo_id     uuid NOT NULL REFERENCES public.dish_combos(id) ON DELETE CASCADE,
  dish_id      uuid NOT NULL REFERENCES public.dishes(id),
  role         text NOT NULL CHECK (role IN ('primary','side','accompaniment')),
  is_default   boolean NOT NULL DEFAULT true,
  is_swappable boolean NOT NULL DEFAULT false,
  sort_order   smallint NOT NULL DEFAULT 0,
  PRIMARY KEY (combo_id, dish_id)
);
