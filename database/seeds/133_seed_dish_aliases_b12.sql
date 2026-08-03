-- Seed: 133_seed_dish_aliases_b12.sql
-- WP-19 Dish Ontology — Batch 12 (~10 dishes: Goan cuisine + Gujarat remainders).
-- Same format/rules as prior batches: data_source='real', every row cites source_url + confidence.
-- GUARDED inserts (WHERE EXISTS) matching the env-robust pattern established in seeds 122-132.
-- Safety filter: no alias string may equal another catalogue dish name (checked against catalogue.json before writing).

-- Vindaloo (Pork)  (https://en.wikipedia.org/wiki/Vindaloo)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Vindaloo (Pork)')::uuid, 'Vindalho', 'real', 'spelling_variant', 'Goa', 'konkani', 'https://en.wikipedia.org/wiki/Vindaloo', 0.8
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Vindaloo (Pork)')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Xacuti (Chicken)  (https://en.wikipedia.org/wiki/Xacuti)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Xacuti (Chicken)')::uuid, 'Shagoti', 'real', 'regional_name', 'Goa', 'konkani', 'https://en.wikipedia.org/wiki/Xacuti', 0.8
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Xacuti (Chicken)')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Bebinca  (https://en.wikipedia.org/wiki/Bebinca)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Bebinca')::uuid, 'Bibik', 'real', 'regional_name', 'Goa', 'konkani', 'https://en.wikipedia.org/wiki/Bebinca', 0.75
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Bebinca')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Bebinca')::uuid, 'Goan Layer Cake', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Bebinca', 0.8
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Bebinca')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Sorpotel  (https://en.wikipedia.org/wiki/Sarapatel)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Sorpotel')::uuid, 'Sarapatel', 'real', 'spelling_variant', 'Goa', 'konkani', 'https://en.wikipedia.org/wiki/Sarapatel', 0.85
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Sorpotel')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Fish Recheado  (https://theyummydelights.com/goan-recheado-fish-fry-recipe/)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Fish Recheado')::uuid, 'Recheado Fish Fry', 'real', 'common_name', 'Goa', 'konkani', 'https://theyummydelights.com/goan-recheado-fish-fry-recipe/', 0.8
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Fish Recheado')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Fish Recheado')::uuid, 'Stuffed Spiced Fried Fish', 'real', 'english_gloss', NULL, 'english', 'https://theyummydelights.com/goan-recheado-fish-fry-recipe/', 0.75
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Fish Recheado')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Prawn Balchao  (https://en.wikipedia.org/wiki/Balch%C3%A3o)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Prawn Balchao')::uuid, 'Balichao', 'real', 'spelling_variant', 'Goa', 'konkani', 'https://en.wikipedia.org/wiki/Balch%C3%A3o', 0.75
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Prawn Balchao')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Prawn Balchao')::uuid, 'Spicy Vinegar Prawn Pickle', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Balch%C3%A3o', 0.75
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Prawn Balchao')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Pao (Goan Bread)  (https://en.wikipedia.org/wiki/Poee)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Pao (Goan Bread)')::uuid, 'Poi', 'real', 'regional_name', 'Goa', 'konkani', 'https://en.wikipedia.org/wiki/Poee', 0.75
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Pao (Goan Bread)')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Goan Fish Curry  (https://www.tableandtraditions.com/recipes/goan-fish-curry)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Goan Fish Curry')::uuid, 'Xitti Kodi', 'real', 'regional_name', 'Goa', 'konkani', 'https://www.tableandtraditions.com/recipes/goan-fish-curry', 0.8
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Goan Fish Curry')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Khichu  (https://en.wikipedia.org/wiki/Khichu)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Khichu')::uuid, 'Khichiyu', 'real', 'spelling_variant', 'Gujarat', 'gujarati', 'https://en.wikipedia.org/wiki/Khichu', 0.75
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Khichu')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Khichu')::uuid, 'Steamed Spiced Rice Flour Dough', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Khichu', 0.75
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Khichu')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Muthiya  (https://en.wikipedia.org/wiki/Muthia)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Muthiya')::uuid, 'Muthia', 'real', 'spelling_variant', 'Gujarat', 'gujarati', 'https://en.wikipedia.org/wiki/Muthia', 0.8
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Muthiya')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Muthiya')::uuid, 'Vaataa', 'real', 'regional_name', 'Charotar, Gujarat', 'gujarati', 'https://en.wikipedia.org/wiki/Muthia', 0.7
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Muthiya')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
