-- Keep the offline/reference Ghar RE schema private even if a future Data API
-- configuration or default grant changes. Edge Functions use service_role and
-- therefore continue to work; client roles get no schema/table access and RLS
-- remains default-deny as a second boundary.

REVOKE ALL ON SCHEMA ghar_re FROM PUBLIC, anon, authenticated;
REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA ghar_re FROM PUBLIC, anon, authenticated;
ALTER DEFAULT PRIVILEGES IN SCHEMA ghar_re
  REVOKE ALL ON TABLES FROM PUBLIC, anon, authenticated;

ALTER TABLE ghar_re.cuisine_groups ENABLE ROW LEVEL SECURITY;
ALTER TABLE ghar_re.cuisines ENABLE ROW LEVEL SECURITY;
ALTER TABLE ghar_re.dishes ENABLE ROW LEVEL SECURITY;
ALTER TABLE ghar_re.ingredients ENABLE ROW LEVEL SECURITY;
ALTER TABLE ghar_re.dish_ingredients ENABLE ROW LEVEL SECURITY;
ALTER TABLE ghar_re.ingredient_aliases ENABLE ROW LEVEL SECURITY;
ALTER TABLE ghar_re.dish_name_synonyms ENABLE ROW LEVEL SECURITY;
ALTER TABLE ghar_re.tags ENABLE ROW LEVEL SECURITY;
ALTER TABLE ghar_re.dish_combos ENABLE ROW LEVEL SECURITY;
ALTER TABLE ghar_re.dish_combo_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE ghar_re.region_food_affinity ENABLE ROW LEVEL SECURITY;
ALTER TABLE ghar_re.community_priors ENABLE ROW LEVEL SECURITY;
ALTER TABLE ghar_re.households ENABLE ROW LEVEL SECURITY;
ALTER TABLE ghar_re.household_profile ENABLE ROW LEVEL SECURITY;
ALTER TABLE ghar_re.household_context ENABLE ROW LEVEL SECURITY;
ALTER TABLE ghar_re.household_modes ENABLE ROW LEVEL SECURITY;
ALTER TABLE ghar_re.feedback_event ENABLE ROW LEVEL SECURITY;
ALTER TABLE ghar_re.recommendation_event ENABLE ROW LEVEL SECURITY;
ALTER TABLE ghar_re.allergen_hidden_derivatives ENABLE ROW LEVEL SECURITY;
ALTER TABLE ghar_re.dish_variants ENABLE ROW LEVEL SECURITY;
ALTER TABLE ghar_re.dish_macro ENABLE ROW LEVEL SECURITY;
ALTER TABLE ghar_re.sig_scores ENABLE ROW LEVEL SECURITY;
ALTER TABLE ghar_re.prior_zone_slot_season ENABLE ROW LEVEL SECURITY;
ALTER TABLE ghar_re.zone_map ENABLE ROW LEVEL SECURITY;
ALTER TABLE ghar_re.comfort_hero_map ENABLE ROW LEVEL SECURITY;
ALTER TABLE ghar_re.negative_priors ENABLE ROW LEVEL SECURITY;
ALTER TABLE ghar_re.sig_score_bands ENABLE ROW LEVEL SECURITY;
ALTER TABLE ghar_re.ingredient_normalization_map ENABLE ROW LEVEL SECURITY;
