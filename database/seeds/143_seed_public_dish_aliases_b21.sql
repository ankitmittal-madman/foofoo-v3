-- Seed: 143_seed_public_dish_aliases_b21.sql
-- WP-19 Dish Ontology (public.dish_name_synonyms) — Batch 21.
-- Same rules as prior batches: data_source='real', cited, guarded, safety-filtered.

-- Chicken Malai Tikka  (https://www.mirchitales.com/chicken-malai-tikka-malai-boti/)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Malai Boti', 'real', 'common_name', NULL, 'urdu', 'https://www.mirchitales.com/chicken-malai-tikka-malai-boti/', 0.75 FROM public.dishes WHERE name = 'Chicken Malai Tikka'
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Chicken Korma (Mughlai)  (https://onestophalal.com/blogs/info/chicken-shahi-korma-a-royal-delight-of-mughlai-cuisine)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Shahi Korma', 'real', 'common_name', 'Delhi', 'urdu', 'https://onestophalal.com/blogs/info/chicken-shahi-korma-a-royal-delight-of-mughlai-cuisine', 0.7 FROM public.dishes WHERE name = 'Chicken Korma (Mughlai)'
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Chha Gosht  (https://www.slurrp.com/article/chha-gosht-this-himachali-mutton-curry-is-the-best-kept-secret-of-the-hills-1636990357469)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Khatta Gosht', 'real', 'regional_name', 'Himachal Pradesh', 'hindi', 'https://www.slurrp.com/article/chha-gosht-this-himachali-mutton-curry-is-the-best-kept-secret-of-the-hills-1636990357469', 0.7 FROM public.dishes WHERE name = 'Chha Gosht'
ON CONFLICT (dish_id, synonym) DO NOTHING;
