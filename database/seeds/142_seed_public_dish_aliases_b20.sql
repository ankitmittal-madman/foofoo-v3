-- Seed: 142_seed_public_dish_aliases_b20.sql
-- WP-19 Dish Ontology (public.dish_name_synonyms) — Batch 20.
-- Same rules as prior batches: data_source='real', cited, guarded, safety-filtered.

-- Chettinad Mutton  (https://yourfoodfantasy.com/chettinad-lamb-mutton-curry-recipe/)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Chettinad Mutton Kuzhambu', 'real', 'regional_name', 'Chettinad, Tamil Nadu', 'tamil', 'https://yourfoodfantasy.com/chettinad-lamb-mutton-curry-recipe/', 0.7 FROM public.dishes WHERE name = 'Chettinad Mutton'
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Chepala Pulusu  (https://www.licious.in/blog/recipe/chepala-pulusu-andhra-style-fish-curry)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Andhra Fish Curry', 'real', 'english_gloss', 'Andhra Pradesh', 'english', 'https://www.licious.in/blog/recipe/chepala-pulusu-andhra-style-fish-curry', 0.75 FROM public.dishes WHERE name = 'Chepala Pulusu'
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Chanar Dalna  (https://www.vegrecipesofindia.com/chanar-dalna-recipe/)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Chhanar Dalna', 'real', 'spelling_variant', 'West Bengal', 'bengali', 'https://www.vegrecipesofindia.com/chanar-dalna-recipe/', 0.75 FROM public.dishes WHERE name = 'Chanar Dalna'
ON CONFLICT (dish_id, synonym) DO NOTHING;
