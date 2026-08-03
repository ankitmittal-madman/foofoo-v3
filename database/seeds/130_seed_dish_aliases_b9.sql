-- Seed: 130_seed_dish_aliases_b9.sql
-- WP-19 Dish Ontology — Batch 9 (~5 dishes: Bengali cuisine + Tulu Nadu).
-- Same format/rules as prior batches: data_source='real', every row cites source_url + confidence.
-- GUARDED inserts (WHERE EXISTS) matching the env-robust pattern established in seeds 122-129.
-- Safety filter: no alias string may equal another catalogue dish name (checked against catalogue.json before writing).

-- Chingri Malai Curry  (https://en.wikipedia.org/wiki/Chingri_malai_curry)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Chingri Malai Curry')::uuid, 'Prawn Malai Curry', 'real', 'common_name', 'West Bengal', 'bengali', 'https://en.wikipedia.org/wiki/Chingri_malai_curry', 0.85
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Chingri Malai Curry')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Chingri Malai Curry')::uuid, 'Chingri Macher Malaikari', 'real', 'regional_name', 'West Bengal', 'bengali', 'https://en.wikipedia.org/wiki/Chingri_malai_curry', 0.8
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Chingri Malai Curry')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Doi Maach  (https://foodiesterminal.com/doi-maach-recipe/)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Doi Maach')::uuid, 'Doi Mach', 'real', 'spelling_variant', 'West Bengal', 'bengali', 'https://foodiesterminal.com/doi-maach-recipe/', 0.8
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Doi Maach')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Doi Maach')::uuid, 'Fish in Yogurt Curry', 'real', 'english_gloss', NULL, 'english', 'https://foodiesterminal.com/doi-maach-recipe/', 0.85
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Doi Maach')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Shukto  (https://en.wikipedia.org/wiki/Shukto)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Shukto')::uuid, 'Sukto', 'real', 'spelling_variant', 'West Bengal', 'bengali', 'https://en.wikipedia.org/wiki/Shukto', 0.8
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Shukto')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Shukto')::uuid, 'Shuktoni', 'real', 'regional_name', 'Bangladesh', 'bengali', 'https://en.wikipedia.org/wiki/Shukto', 0.75
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Shukto')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Shukto')::uuid, 'Bitter Mixed Vegetable Stew', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Shukto', 0.75
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Shukto')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Pitha (Patishapta)  (https://en.wikipedia.org/wiki/Patisapta)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Pitha (Patishapta)')::uuid, 'Patisapta', 'real', 'spelling_variant', 'West Bengal, Bangladesh', 'bengali', 'https://en.wikipedia.org/wiki/Patisapta', 0.8
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Pitha (Patishapta)')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Pitha (Patishapta)')::uuid, 'Sweet Rice-Crepe Rolls', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Patisapta', 0.75
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Pitha (Patishapta)')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Kori Rotti  (https://en.wikipedia.org/wiki/Kori_rotti)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Kori Rotti')::uuid, 'Kori Rutti', 'real', 'spelling_variant', 'Tulu Nadu, Karnataka', 'tulu', 'https://en.wikipedia.org/wiki/Kori_rotti', 0.8
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Kori Rotti')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
