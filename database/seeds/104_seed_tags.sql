-- Migration: 104_seed_tags.sql
-- Title: public.tags — controlled genome/vocabulary tags
-- Layer: ICD-1 content (WP-6D-gen v1.0)
-- Generated: 2026-07-14T03:41:23Z  by database/etl/generate_icd1_seeds.py (deterministic)
-- Transformation version: WP-6D-gen v1.0
-- Provenance (source workbook/sheet + checksum):
--   source: tags_v4.csv (sha256:ad2b83e282607c0a) — 111 rows
-- Business rules applied:
--   - tag_name = source `value` [TR-001/002]; dimension = source `category`
--   - tier = int(tier_x)  [TR-009]; is_user_facing = (is_user_facing=='Y')
--   - vector_position: provisional (900000+i) at insert, then deterministically reassigned
--   -   by public.fn_assign_tag_vector_positions() (migration 023) — ORDER BY tier,dimension,tag_name
-- Idempotency: INSERT ... ON CONFLICT DO NOTHING. Re-runnable. Paired _rollback.sql.
-- NOTE: supersedes the illustrative rows in 101/102 for the same tables (never edited in place).

BEGIN;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('breakfast','meal_type',1,true,900000) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('lunch','meal_type',1,true,900001) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('dinner','meal_type',1,true,900002) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('snacks','meal_type',1,true,900003) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('whole_meal','dish_category',1,true,900004) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('bread','dish_category',1,true,900005) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('rice','dish_category',1,true,900006) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('dal_lentil','dish_category',1,true,900007) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('curry','dish_category',1,true,900008) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('dry_sabzi','dish_category',1,true,900009) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('salad_raita','dish_category',1,true,900010) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('chaat','dish_category',1,true,900011) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('kebab','dish_category',1,true,900012) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('biryani_pulao','dish_category',1,true,900013) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('sweet_dessert','dish_category',1,true,900014) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('beverage','dish_category',1,true,900015) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('condiment_chutney','dish_category',1,true,900016) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('soup','dish_category',1,true,900017) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('paratha_roti','dish_category',1,true,900018) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('dosa_idli','dish_category',1,true,900019) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('noodle_pasta','dish_category',1,true,900020) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('egg_dish','dish_category',1,true,900021) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('snack_starter','dish_category',1,true,900022) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('thali_combo','dish_category',1,true,900023) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('deep_fried','cooking_method',2,true,900024) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('shallow_fried','cooking_method',2,true,900025) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('stir_fried','cooking_method',2,true,900026) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('steamed','cooking_method',2,true,900027) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('boiled','cooking_method',2,true,900028) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('grilled','cooking_method',2,true,900029) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('roasted','cooking_method',2,true,900030) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('baked','cooking_method',2,true,900031) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('tandoor','cooking_method',2,true,900032) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('dum_cooked','cooking_method',2,true,900033) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('pressure_cooked','cooking_method',2,false,900034) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('sauteed','cooking_method',2,false,900035) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('tempered','cooking_method',2,false,900036) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('raw','cooking_method',2,true,900037) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('smoked','cooking_method',2,true,900038) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('fermented_cook','cooking_method',2,true,900039) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('savoury','primary_taste',2,true,900040) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('sweet','primary_taste',2,true,900041) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('sour','primary_taste',2,true,900042) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('bitter','primary_taste',2,false,900043) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('umami','primary_taste',2,false,900044) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('tangy','primary_taste',2,true,900045) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('spicy_hot','primary_taste',2,true,900046) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('crispy','texture',2,true,900047) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('crunchy','texture',2,true,900048) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('soft','texture',2,true,900049) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('chewy','texture',2,true,900050) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('flaky','texture',2,true,900051) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('smooth','texture',2,true,900052) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('grainy','texture',2,false,900053) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('crumbly','texture',2,false,900054) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('dense','texture',2,false,900055) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('fluffy','texture',2,true,900056) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('sticky','texture',2,false,900057) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('layered','texture',2,true,900058) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('plain','richness',2,true,900059) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('light','richness',2,true,900060) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('buttery','richness',2,true,900061) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('creamy','richness',2,true,900062) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('oily','richness',2,false,900063) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('ghee_rich','richness',2,true,900064) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('coconut_rich','richness',2,true,900065) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('silky','mouthfeel',3,false,900066) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('velvety','mouthfeel',3,false,900067) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('mealy','mouthfeel',3,false,900068) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('pasty','mouthfeel',3,false,900069) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('waxy','mouthfeel',3,false,900070) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('gritty','mouthfeel',3,false,900071) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('juicy','mouthfeel',3,true,900072) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('dry','mouthfeel',3,false,900073) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('moist','mouthfeel',3,false,900074) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('gelatinous','mouthfeel',3,false,900075) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('smoky','aroma_profile',3,true,900076) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('earthy','aroma_profile',3,false,900077) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('floral','aroma_profile',3,false,900078) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('citrusy','aroma_profile',3,false,900079) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('herby','aroma_profile',3,false,900080) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('pungent','aroma_profile',3,false,900081) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('mild','aroma_profile',3,false,900082) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('roasted_aroma','aroma_profile',3,false,900083) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('fermented_aroma','aroma_profile',3,false,900084) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('sweet_aroma','aroma_profile',3,false,900085) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('nutty','aroma_profile',3,false,900086) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('none','fermentation',3,false,900087) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('light','fermentation',3,false,900088) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('medium','fermentation',3,false,900089) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('heavy','fermentation',3,false,900090) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('hot','serving_temp',3,true,900091) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('warm','serving_temp',3,true,900092) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('room_temp','serving_temp',3,true,900093) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('chilled','serving_temp',3,true,900094) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('frozen','serving_temp',3,true,900095) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('hot_weather','weather_affinity',2,false,900096) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('cold_weather','weather_affinity',2,false,900097) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('rainy','weather_affinity',2,false,900098) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('all_weather','weather_affinity',2,false,900099) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('gluten','allergen',1,true,900100) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('dairy','allergen',1,true,900101) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('tree_nuts','allergen',1,true,900102) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('peanuts','allergen',1,true,900103) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('soy','allergen',1,true,900104) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('sesame','allergen',1,true,900105) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('shellfish','allergen',1,true,900106) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('fish','allergen',1,true,900107) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('egg_allergen','allergen',1,true,900108) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('mustard','allergen',1,true,900109) ON CONFLICT (dimension,tag_name) DO NOTHING;
INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) VALUES ('none','allergen',1,true,900110) ON CONFLICT (dimension,tag_name) DO NOTHING;
-- Deterministic genome-vector position assignment (migration 023):
SELECT public.fn_assign_tag_vector_positions();
COMMIT;
