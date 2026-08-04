-- Seed: 145_seed_public_dish_aliases_b23.sql
-- WP-19 Dish Ontology (public.dish_name_synonyms) — Batch 23.
-- Same rules as prior batches: data_source='real', cited, guarded, safety-filtered.

-- Aamras  (https://www.spiceupthecurry.com/aamras-recipe-aamras-puripoori/)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Keri No Ras', 'real', 'regional_name', 'Gujarat', 'gujarati', 'https://www.spiceupthecurry.com/aamras-recipe-aamras-puripoori/', 0.7 FROM public.dishes WHERE name = 'Aamras'
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Akuri  (https://en.wikipedia.org/wiki/Akuri)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Akoori', 'real', 'spelling_variant', 'Parsi', 'gujarati', 'https://en.wikipedia.org/wiki/Akuri', 0.85 FROM public.dishes WHERE name = 'Akuri'
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Bhakarwadi  (https://en.wikipedia.org/wiki/Bakarwadi)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Bakarwadi', 'real', 'spelling_variant', 'Maharashtra, Gujarat', 'marathi', 'https://en.wikipedia.org/wiki/Bakarwadi', 0.85 FROM public.dishes WHERE name = 'Bhakarwadi'
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Aloo Chaat  (https://en.wikipedia.org/wiki/Alu_chat)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Dilli Aloo Chaat', 'real', 'regional_name', 'Delhi', 'hindi', 'https://en.wikipedia.org/wiki/Alu_chat', 0.75 FROM public.dishes WHERE name = 'Aloo Chaat'
ON CONFLICT (dish_id, synonym) DO NOTHING;
