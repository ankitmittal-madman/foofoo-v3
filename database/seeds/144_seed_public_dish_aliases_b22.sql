-- Seed: 144_seed_public_dish_aliases_b22.sql
-- WP-19 Dish Ontology (public.dish_name_synonyms) — Batch 22.
-- Same rules as prior batches: data_source='real', cited, guarded, safety-filtered.

-- Chapli Kebab  (https://en.wikipedia.org/wiki/Chappali_kebab)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Chappali Kebab', 'real', 'spelling_variant', 'Peshawar, Khyber Pakhtunkhwa', 'pashto', 'https://en.wikipedia.org/wiki/Chappali_kebab', 0.8 FROM public.dishes WHERE name = 'Chapli Kebab'
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Dabeli  (https://en.wikipedia.org/wiki/Dabeli)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Kutchi Dabeli', 'real', 'regional_name', 'Kutch, Gujarat', 'gujarati', 'https://en.wikipedia.org/wiki/Dabeli', 0.8 FROM public.dishes WHERE name = 'Dabeli'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Double Roti', 'real', 'common_name', 'Kutch, Gujarat', 'gujarati', 'https://en.wikipedia.org/wiki/Dabeli', 0.7 FROM public.dishes WHERE name = 'Dabeli'
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Falafel  (https://en.wikipedia.org/wiki/Falafel)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Taameya', 'real', 'regional_name', 'Egypt', 'arabic', 'https://en.wikipedia.org/wiki/Falafel', 0.75 FROM public.dishes WHERE name = 'Falafel'
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Fattoush  (https://en.wikipedia.org/wiki/Fattoush)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Fattoosh', 'real', 'spelling_variant', 'Levant', 'arabic', 'https://en.wikipedia.org/wiki/Fattoush', 0.7 FROM public.dishes WHERE name = 'Fattoush'
ON CONFLICT (dish_id, synonym) DO NOTHING;
