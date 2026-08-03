-- Seed: 140_seed_public_dish_aliases_b18.sql
-- WP-19 Dish Ontology (public.dish_name_synonyms) — Batch 18.
-- Same rules as prior batches: data_source='real', cited, guarded, safety-filtered.

-- Chicken Xacuti  (https://en.wikipedia.org/wiki/Xacuti)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Shagoti', 'real', 'regional_name', 'Goa', 'konkani', 'https://en.wikipedia.org/wiki/Xacuti', 0.7 FROM public.dishes WHERE name = 'Chicken Xacuti'
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Cham Cham  (https://en.wikipedia.org/wiki/Chomchom)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Chomchom', 'real', 'spelling_variant', 'West Bengal', 'bengali', 'https://en.wikipedia.org/wiki/Chomchom', 0.8 FROM public.dishes WHERE name = 'Cham Cham'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Chum Chum', 'real', 'spelling_variant', 'West Bengal', 'bengali', 'https://en.wikipedia.org/wiki/Chomchom', 0.75 FROM public.dishes WHERE name = 'Cham Cham'
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Chettinad Fish Curry  (https://www.kannammacooks.com/alamelus-authentic-chettinad-fish-meen-kuzhambu-curry/)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Chettinad Meen Kuzhambu', 'real', 'regional_name', 'Chettinad, Tamil Nadu', 'tamil', 'https://www.kannammacooks.com/alamelus-authentic-chettinad-fish-meen-kuzhambu-curry/', 0.75 FROM public.dishes WHERE name = 'Chettinad Fish Curry'
ON CONFLICT (dish_id, synonym) DO NOTHING;
