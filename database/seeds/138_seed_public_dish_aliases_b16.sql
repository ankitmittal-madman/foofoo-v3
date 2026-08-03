-- Seed: 138_seed_public_dish_aliases_b16.sql
-- WP-19 Dish Ontology (public.dish_name_synonyms) — Batch 16.
-- Same rules as prior batches: data_source='real', cited, guarded, safety-filtered.

-- Ariselu  (https://en.wikipedia.org/wiki/Ariselu)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Adhirasam', 'real', 'regional_name', 'Tamil Nadu', 'tamil', 'https://en.wikipedia.org/wiki/Ariselu', 0.8 FROM public.dishes WHERE name = 'Ariselu'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Anarasa', 'real', 'regional_name', 'Maharashtra', 'marathi', 'https://en.wikipedia.org/wiki/Ariselu', 0.75 FROM public.dishes WHERE name = 'Ariselu'
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Avial (Kerala)  (https://en.wikipedia.org/wiki/Avial)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Aviyal', 'real', 'spelling_variant', 'Kerala', 'malayalam', 'https://en.wikipedia.org/wiki/Avial', 0.85 FROM public.dishes WHERE name = 'Avial (Kerala)'
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Baba Ganoush  (https://en.wikipedia.org/wiki/Baba_ghanoush)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Baba Ghanoush', 'real', 'spelling_variant', 'Levant', 'arabic', 'https://en.wikipedia.org/wiki/Baba_ghanoush', 0.8 FROM public.dishes WHERE name = 'Baba Ganoush'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Baba Ghanouj', 'real', 'spelling_variant', 'Levant', 'arabic', 'https://en.wikipedia.org/wiki/Baba_ghanoush', 0.75 FROM public.dishes WHERE name = 'Baba Ganoush'
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Balushahi  (https://www.vegrecipesofindia.com/balushahi-recipe-badusha-recipe/)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Badusha', 'real', 'regional_name', 'Tamil Nadu, Andhra Pradesh', 'tamil', 'https://www.vegrecipesofindia.com/balushahi-recipe-badusha-recipe/', 0.75 FROM public.dishes WHERE name = 'Balushahi'
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Bajra Roti  (https://www.vegrecipesofindia.com/bajra-roti-bajra-bhakri/)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Bajra Bhakri', 'real', 'regional_name', 'Maharashtra', 'marathi', 'https://www.vegrecipesofindia.com/bajra-roti-bajra-bhakri/', 0.75 FROM public.dishes WHERE name = 'Bajra Roti'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Bajri No Rotlo', 'real', 'regional_name', 'Gujarat', 'gujarati', 'https://binjalsvegkitchen.com/bajra-roti-or-bajri-no-rotlo-the-rustic-indian-millet-bread/', 0.7 FROM public.dishes WHERE name = 'Bajra Roti'
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- American Chop Suey  (https://en.wikipedia.org/wiki/American_chop_suey)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'American Goulash', 'real', 'common_name', 'New England, USA', 'english', 'https://en.wikipedia.org/wiki/American_chop_suey', 0.7 FROM public.dishes WHERE name = 'American Chop Suey'
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Arancini  (https://en.wikipedia.org/wiki/Arancini)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Arancine', 'real', 'regional_name', 'Western Sicily', 'italian', 'https://en.wikipedia.org/wiki/Arancini', 0.75 FROM public.dishes WHERE name = 'Arancini'
ON CONFLICT (dish_id, synonym) DO NOTHING;
