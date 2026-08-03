-- Seed: 132_seed_dish_aliases_b11.sql
-- WP-19 Dish Ontology — Batch 11 (~13 dishes: Maharashtra + Gujarat classics).
-- Same format/rules as prior batches: data_source='real', every row cites source_url + confidence.
-- GUARDED inserts (WHERE EXISTS) matching the env-robust pattern established in seeds 122-131.
-- Safety filter: no alias string may equal another catalogue dish name (checked against catalogue.json before writing).

-- Sabudana Khichdi  (https://en.wikipedia.org/wiki/Sabudana_khichri)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Sabudana Khichdi')::uuid, 'Sabudana Khichri', 'real', 'spelling_variant', 'Maharashtra', 'marathi', 'https://en.wikipedia.org/wiki/Sabudana_khichri', 0.85
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Sabudana Khichdi')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Sabudana Khichdi')::uuid, 'Tapioca Pearl Fasting Pilaf', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Sabudana_khichri', 0.75
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Sabudana Khichdi')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Batata Vada  (https://en.wikipedia.org/wiki/Batata_vada)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Batata Vada')::uuid, 'Potato Bonda', 'real', 'common_name', NULL, 'hindi', 'https://en.wikipedia.org/wiki/Batata_vada', 0.75
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Batata Vada')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Batata Vada')::uuid, 'Batate Ambado', 'real', 'regional_name', 'Coastal Karnataka', 'konkani', 'https://en.wikipedia.org/wiki/Batata_vada', 0.7
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Batata Vada')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Amti  (https://www.spiceupthecurry.com/amti-recipe-maharashtrian-amti-dal-recipe/)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Amti')::uuid, 'Aamti', 'real', 'spelling_variant', 'Maharashtra', 'marathi', 'https://www.spiceupthecurry.com/amti-recipe-maharashtrian-amti-dal-recipe/', 0.75
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Amti')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Amti')::uuid, 'Sweet-Tangy Toor Dal Curry', 'real', 'english_gloss', NULL, 'english', 'https://www.spiceupthecurry.com/amti-recipe-maharashtrian-amti-dal-recipe/', 0.75
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Amti')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Dal Dhokli  (https://en.wikipedia.org/wiki/Dal_dhokli)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Dal Dhokli')::uuid, 'Dal Pithi', 'real', 'regional_name', 'Rajasthan', 'rajasthani', 'https://en.wikipedia.org/wiki/Dal_dhokli', 0.7
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Dal Dhokli')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Dal Dhokli')::uuid, 'Wheat Dumplings in Lentil Stew', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Dal_dhokli', 0.75
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Dal Dhokli')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Handvo  (https://en.wikipedia.org/wiki/Handvo)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Handvo')::uuid, 'Ondhwo', 'real', 'regional_name', 'Kathiawad, Gujarat', 'gujarati', 'https://en.wikipedia.org/wiki/Handvo', 0.75
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Handvo')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Handvo')::uuid, 'Savoury Baked Lentil-Rice Cake', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Handvo', 0.8
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Handvo')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Patra  (https://en.wikipedia.org/wiki/Patra)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Patra')::uuid, 'Patravelia', 'real', 'regional_name', 'Gujarat', 'gujarati', 'https://en.wikipedia.org/wiki/Patra', 0.7
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Patra')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Patra')::uuid, 'Steamed Colocasia Leaf Rolls', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Patra', 0.8
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Patra')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Basundi  (https://en.wikipedia.org/wiki/Basundi)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Basundi')::uuid, 'Reduced Sweetened Milk', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Basundi', 0.75
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Basundi')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Gathiya  (https://en.wikipedia.org/wiki/Ganthiya)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Gathiya')::uuid, 'Ganthiya', 'real', 'spelling_variant', 'Gujarat', 'gujarati', 'https://en.wikipedia.org/wiki/Ganthiya', 0.85
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Gathiya')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Mohanthal  (https://en.wikipedia.org/wiki/Mohanthal)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Mohanthal')::uuid, 'Mohanthar', 'real', 'spelling_variant', 'Gujarat, Rajasthan', 'gujarati', 'https://en.wikipedia.org/wiki/Mohanthal', 0.7
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Mohanthal')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Mohanthal')::uuid, 'Gram Flour Fudge', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Mohanthal', 0.75
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Mohanthal')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Khakhra  (https://en.wikipedia.org/wiki/Khakhra)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Khakhra')::uuid, 'Crisp Wheat Flatbread Crackers', 'real', 'english_gloss', 'Gujarat', 'english', 'https://en.wikipedia.org/wiki/Khakhra', 0.75
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Khakhra')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Methi Na Gota  (https://www.spiceupthecurry.com/methi-gota-recipe-methi-pakoda/)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Methi Na Gota')::uuid, 'Methi Gota', 'real', 'spelling_variant', 'Gujarat', 'gujarati', 'https://www.spiceupthecurry.com/methi-gota-recipe-methi-pakoda/', 0.8
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Methi Na Gota')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Methi Na Gota')::uuid, 'Methi Na Bhajiya', 'real', 'regional_name', 'Gujarat', 'gujarati', 'https://www.spiceupthecurry.com/methi-gota-recipe-methi-pakoda/', 0.75
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Methi Na Gota')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Rotla  (https://www.tasteatlas.com/rotla)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Rotla')::uuid, 'Bajra Na Rotla', 'real', 'common_name', 'Saurashtra, Gujarat', 'gujarati', 'https://www.tasteatlas.com/rotla', 0.8
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Rotla')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
