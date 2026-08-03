-- Seed: 139_seed_public_dish_aliases_b17.sql
-- WP-19 Dish Ontology (public.dish_name_synonyms) — Batch 17.
-- Same rules as prior batches: data_source='real', cited, guarded, safety-filtered.

-- Bisi Bele Bath Mix Veg  (https://en.wikipedia.org/wiki/Bisi_Bele_Bath)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Bisi Bele Huliyanna', 'real', 'regional_name', 'Karnataka', 'kannada', 'https://en.wikipedia.org/wiki/Bisi_Bele_Bath', 0.8 FROM public.dishes WHERE name = 'Bisi Bele Bath Mix Veg'
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Bobbatlu  (https://en.wikipedia.org/wiki/Puran_poli)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Holige', 'real', 'regional_name', 'North Karnataka', 'kannada', 'https://en.wikipedia.org/wiki/Puran_poli', 0.75 FROM public.dishes WHERE name = 'Bobbatlu'
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Bihari Kebab  (https://en.wikipedia.org/wiki/Bihari_kebab)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Bihari Boti', 'real', 'common_name', 'Bihar', 'urdu', 'https://en.wikipedia.org/wiki/Bihari_kebab', 0.75 FROM public.dishes WHERE name = 'Bihari Kebab'
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Bruschetta  (https://en.wikipedia.org/wiki/Bruschetta)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Fettunta', 'real', 'regional_name', 'Tuscany', 'italian', 'https://en.wikipedia.org/wiki/Bruschetta', 0.7 FROM public.dishes WHERE name = 'Bruschetta'
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Chaas  (https://en.wikipedia.org/wiki/Chaas)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Moru', 'real', 'regional_name', 'Tamil Nadu, Kerala', 'tamil', 'https://en.wikipedia.org/wiki/Chaas', 0.75 FROM public.dishes WHERE name = 'Chaas'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Majjige', 'real', 'regional_name', 'Karnataka', 'kannada', 'https://en.wikipedia.org/wiki/Chaas', 0.75 FROM public.dishes WHERE name = 'Chaas'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Taak', 'real', 'regional_name', 'Maharashtra', 'marathi', 'https://en.wikipedia.org/wiki/Chaas', 0.75 FROM public.dishes WHERE name = 'Chaas'
ON CONFLICT (dish_id, synonym) DO NOTHING;
