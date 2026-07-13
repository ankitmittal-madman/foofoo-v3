-- Migration: 010_trigger_functions_and_triggers.sql
-- Implements: DOC-P3-04 v1.3 §03.6A (fn_derive_dish_attributes, fn_propagate_ingredient_change),
--   §03.2 (fn_sync_profile_allergen_union), §03.9 (fn_update_dish_genome_vector),
--   §03.19 (public.derivation_conflicts — relocated here at v1.2 per AGR-003 resolution; see
--   DOC-P3-05 Part (a) v1.2 Phase 16)
-- Logical functions: LF-K01 (deriveDishAttributes), LF-A05 (allergen propagation to profile
--   display column), LF-K02 (genome vector maintenance)
-- Governance refs: DOC-P3-05 Part (a) v1.2 Phase 7 (prerequisite: 009, transitively 002/005/006/008);
--   Phase 8.1 (derivation_conflicts table allocated here, AGR-003); Phase 8.2 (all 4 functions
--   grouped in this one file, by concern not strict first-eligibility); Phase 9 (idempotent
--   CREATE TRIGGER via DO $$ ... EXCEPTION WHEN duplicate_object guard)
-- CDM entities: Entity 15 (Dish), Entity 18 (Ingredient), Entity 16 (Food DNA), Entity 3
--   (Household Member), Entity 1 (User/Profile)
-- CDM invariants enforced: Invariant 6 (auto-derivation supremacy — procedural half; the
--   declarative half, the REVOKE statement, was created in file 008), Invariant 4 (member
--   allergen propagation)
-- AGR-003 RESOLVED (v1.2, at the planning layer): derivation_conflicts is now created in this
-- file, immediately below, before fn_derive_dish_attributes() is defined — closing the forward
-- reference that previously existed when this table lived in file 015.

CREATE TABLE public.derivation_conflicts (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  dish_id     uuid NOT NULL REFERENCES public.dishes(id),
  field_name  text NOT NULL,
  manual_value text,
  derived_value text,
  detected_at  timestamptz NOT NULL DEFAULT now(),
  resolved     boolean NOT NULL DEFAULT false
);

CREATE OR REPLACE FUNCTION public.fn_derive_dish_attributes() RETURNS trigger AS $$
DECLARE
  v_dish_id        uuid := COALESCE(NEW.dish_id, OLD.dish_id);
  v_any_nonveg     boolean;
  v_any_egg        boolean;
  v_all_vegan      boolean;
  v_all_jain_safe  boolean;
  v_ingredient_count integer;
  v_allergen_union integer;
  v_diet_type      text;
  v_is_jain        boolean;
  v_prior_diet     text;
  v_prior_jain     boolean;
  v_prior_allergen integer;
BEGIN
  SELECT diet_type, is_jain, allergen_flags
    INTO v_prior_diet, v_prior_jain, v_prior_allergen
    FROM public.dishes WHERE id = v_dish_id;

  SELECT
    count(*),
    bool_or(NOT i.is_veg),
    bool_or((i.allergen_flags & 16) > 0),
    bool_and(i.is_vegan),
    bool_and(NOT i.is_jain_excluded),
    COALESCE(bit_or(i.allergen_flags), 0)
  INTO
    v_ingredient_count, v_any_nonveg, v_any_egg, v_all_vegan, v_all_jain_safe, v_allergen_union
  FROM public.dish_ingredients di
  JOIN public.ingredients i ON i.id = di.ingredient_id
  WHERE di.dish_id = v_dish_id;

  IF v_ingredient_count = 0 THEN
    v_diet_type := NULL;
    v_is_jain   := false;
    v_allergen_union := 0;
  ELSE
    IF v_any_nonveg THEN
      v_diet_type := 'non_veg';
    ELSIF v_any_egg THEN
      v_diet_type := 'egg';
    ELSIF v_all_vegan THEN
      v_diet_type := 'vegan';
    ELSE
      v_diet_type := 'veg';
    END IF;
    v_is_jain := (v_all_jain_safe AND v_diet_type = 'veg');
  END IF;

  IF v_prior_diet IS NOT NULL AND (
       v_prior_diet IS DISTINCT FROM v_diet_type
       OR v_prior_jain IS DISTINCT FROM v_is_jain
       OR v_prior_allergen IS DISTINCT FROM v_allergen_union
     ) THEN
    INSERT INTO public.derivation_conflicts (dish_id, field_name, manual_value, derived_value)
    VALUES
      (v_dish_id, 'diet_type', v_prior_diet, v_diet_type),
      (v_dish_id, 'is_jain', v_prior_jain::text, v_is_jain::text),
      (v_dish_id, 'allergen_flags', v_prior_allergen::text, v_allergen_union::text);
  END IF;

  UPDATE public.dishes
    SET diet_type = v_diet_type,
        is_jain = v_is_jain,
        allergen_flags = v_allergen_union,
        updated_at = now()
    WHERE id = v_dish_id;

  RETURN NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DO $$ BEGIN
  CREATE TRIGGER trg_derive_dish_attributes
  AFTER INSERT OR UPDATE OR DELETE ON public.dish_ingredients
  FOR EACH ROW EXECUTE FUNCTION public.fn_derive_dish_attributes();
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

CREATE OR REPLACE FUNCTION public.fn_propagate_ingredient_change() RETURNS trigger AS $$
DECLARE
  v_affected_dish uuid;
BEGIN
  IF (NEW.allergen_flags IS DISTINCT FROM OLD.allergen_flags)
     OR (NEW.is_veg IS DISTINCT FROM OLD.is_veg)
     OR (NEW.is_vegan IS DISTINCT FROM OLD.is_vegan)
     OR (NEW.is_jain_excluded IS DISTINCT FROM OLD.is_jain_excluded) THEN

    FOR v_affected_dish IN
      SELECT DISTINCT dish_id FROM public.dish_ingredients WHERE ingredient_id = NEW.id
    LOOP
      UPDATE public.dish_ingredients
        SET is_optional = is_optional
        WHERE dish_id = v_affected_dish AND ingredient_id = NEW.id;
    END LOOP;
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DO $$ BEGIN
  CREATE TRIGGER trg_propagate_ingredient_change
  AFTER UPDATE ON public.ingredients
  FOR EACH ROW EXECUTE FUNCTION public.fn_propagate_ingredient_change();
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

CREATE OR REPLACE FUNCTION public.fn_sync_profile_allergen_union() RETURNS trigger AS $$
BEGIN
  UPDATE public.profiles p
  SET allergen_flags = (
    SELECT p.allergen_flags | COALESCE(bit_or(hm.allergen_flags), 0)
    FROM public.household_members hm
    WHERE hm.profile_id = NEW.profile_id AND hm.is_active = true
  )
  WHERE p.id = NEW.profile_id;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DO $$ BEGIN
  CREATE TRIGGER trg_sync_allergen_union
  AFTER INSERT OR UPDATE ON public.household_members
  FOR EACH ROW EXECUTE FUNCTION public.fn_sync_profile_allergen_union();
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

CREATE OR REPLACE FUNCTION public.fn_update_dish_genome_vector() RETURNS trigger AS $$
DECLARE
  v_dish uuid := COALESCE(NEW.dish_id, OLD.dish_id);
  v_dim  integer;
  v_vec  real[];
BEGIN
  SELECT max(vector_position) + 1 INTO v_dim FROM public.tags;
  v_vec := array_fill(0::real, ARRAY[v_dim]);
  SELECT array_agg(t.confidence ORDER BY tg.vector_position)
    INTO v_vec
    FROM public.dish_tags t JOIN public.tags tg ON tg.id = t.tag_id
    WHERE t.dish_id = v_dish AND tg.tier IN (1,2);
  UPDATE public.dishes SET genome_vector = v_vec, updated_at = now() WHERE id = v_dish;
  RETURN NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DO $$ BEGIN
  CREATE TRIGGER trg_update_genome_vector
  AFTER INSERT OR UPDATE OR DELETE ON public.dish_tags
  FOR EACH ROW EXECUTE FUNCTION public.fn_update_dish_genome_vector();
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
