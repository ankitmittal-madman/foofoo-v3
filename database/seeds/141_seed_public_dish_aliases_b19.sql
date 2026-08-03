-- Seed: 141_seed_public_dish_aliases_b19.sql
-- WP-19 Dish Ontology (public.dish_name_synonyms) — Batch 19.
-- Same rules as prior batches: data_source='real', cited, guarded, safety-filtered.

-- Chikki (Peanut)  (https://en.wikipedia.org/wiki/Chikki)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Gajak', 'real', 'regional_name', 'North India (Punjab)', 'hindi', 'https://en.wikipedia.org/wiki/Chikki', 0.7 FROM public.dishes WHERE name = 'Chikki (Peanut)'
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Chicken Karaage  (https://en.wikipedia.org/wiki/Karaage)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Japanese Fried Chicken', 'real', 'english_gloss', 'Japan', 'english', 'https://en.wikipedia.org/wiki/Karaage', 0.75 FROM public.dishes WHERE name = 'Chicken Karaage'
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Chicken Shawarma Plate  (https://en.wikipedia.org/wiki/Shawarma)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Shwarma', 'real', 'spelling_variant', 'Levant', 'arabic', 'https://en.wikipedia.org/wiki/Shawarma', 0.7 FROM public.dishes WHERE name = 'Chicken Shawarma Plate'
ON CONFLICT (dish_id, synonym) DO NOTHING;
