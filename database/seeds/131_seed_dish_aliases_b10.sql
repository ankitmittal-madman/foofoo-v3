-- Seed: 131_seed_dish_aliases_b10.sql
-- WP-19 Dish Ontology — Batch 10 (~17 dishes: Maharashtra/Gujarat classics + Bengali).
-- Same format/rules as prior batches: data_source='real', every row cites source_url + confidence.
-- GUARDED inserts (WHERE EXISTS) matching the env-robust pattern established in seeds 122-130.
-- Safety filter: no alias string may equal another catalogue dish name (checked against catalogue.json before writing).
-- Note: "Solkadhi" (no space) is itself a distinct catalogue dish from "Sol Kadhi" (with space) below — excluded as an alias.

-- Vada Pav  (https://en.wikipedia.org/wiki/Vada_pav)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Vada Pav')::uuid, 'Wada Pav', 'real', 'spelling_variant', 'Mumbai, Maharashtra', 'marathi', 'https://en.wikipedia.org/wiki/Vada_pav', 0.8
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Vada Pav')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Vada Pav')::uuid, 'Indian Burger', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Vada_pav', 0.75
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Vada Pav')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Misal Pav  (https://en.wikipedia.org/wiki/Misal_pav)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Misal Pav')::uuid, 'Puneri Misal', 'real', 'regional_name', 'Pune, Maharashtra', 'marathi', 'https://en.wikipedia.org/wiki/Misal_pav', 0.75
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Misal Pav')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Misal Pav')::uuid, 'Nashik Misal', 'real', 'regional_name', 'Nashik, Maharashtra', 'marathi', 'https://en.wikipedia.org/wiki/Misal_pav', 0.7
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Misal Pav')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Thalipeeth  (https://en.wikipedia.org/wiki/Thalipeeth)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Thalipeeth')::uuid, 'Thalipith', 'real', 'spelling_variant', 'Maharashtra', 'marathi', 'https://en.wikipedia.org/wiki/Thalipeeth', 0.85
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Thalipeeth')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Thalipeeth')::uuid, 'Multigrain Savoury Flatbread', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Thalipeeth', 0.75
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Thalipeeth')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Bhakri  (https://en.wikipedia.org/wiki/Bhakri)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Bhakri')::uuid, 'Bhakhri', 'real', 'spelling_variant', 'Gujarat', 'gujarati', 'https://en.wikipedia.org/wiki/Bhakri', 0.75
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Bhakri')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Bhakri')::uuid, 'Millet Flatbread', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Bhakri', 0.8
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Bhakri')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Sol Kadhi  (https://en.wikipedia.org/wiki/Solkadhi)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Sol Kadhi')::uuid, 'Sol Kadi', 'real', 'spelling_variant', 'Konkan, Maharashtra', 'marathi', 'https://en.wikipedia.org/wiki/Solkadhi', 0.8
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Sol Kadhi')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Sol Kadhi')::uuid, 'Kokum and Coconut Milk Drink', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Solkadhi', 0.75
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Sol Kadhi')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Modak  (https://en.wikipedia.org/wiki/Modak)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Modak')::uuid, 'Kozhukattai', 'real', 'regional_name', 'Tamil Nadu', 'tamil', 'https://en.wikipedia.org/wiki/Modak', 0.8
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Modak')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Modak')::uuid, 'Kadubu', 'real', 'regional_name', 'Karnataka', 'kannada', 'https://en.wikipedia.org/wiki/Modak', 0.75
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Modak')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Shrikhand  (https://en.wikipedia.org/wiki/Shrikhand)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Shrikhand')::uuid, 'Chakka', 'real', 'regional_name', 'Maharashtra', 'marathi', 'https://en.wikipedia.org/wiki/Shrikhand', 0.75
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Shrikhand')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Shrikhand')::uuid, 'Matho', 'real', 'regional_name', 'Gujarat', 'gujarati', 'https://en.wikipedia.org/wiki/Shrikhand', 0.7
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Shrikhand')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Shrikhand')::uuid, 'Strained Sweet Yogurt', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Shrikhand', 0.8
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Shrikhand')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Khandvi  (https://en.wikipedia.org/wiki/Khandvi_(food))
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Khandvi')::uuid, 'Patuli', 'real', 'regional_name', 'Gujarat', 'gujarati', 'https://en.wikipedia.org/wiki/Khandvi_(food)', 0.7
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Khandvi')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Khandvi')::uuid, 'Suralichi Vadi', 'real', 'regional_name', 'Maharashtra', 'marathi', 'https://en.wikipedia.org/wiki/Khandvi_(food)', 0.75
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Khandvi')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Thepla  (https://en.wikipedia.org/wiki/Thepla)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Thepla')::uuid, 'Methi Thepla', 'real', 'common_name', 'Gujarat', 'gujarati', 'https://en.wikipedia.org/wiki/Thepla', 0.75
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Thepla')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Fafda Jalebi  (https://en.wikipedia.org/wiki/Fafda)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Fafda Jalebi')::uuid, 'Gujarati Breakfast Combo', 'real', 'english_gloss', 'Gujarat', 'english', 'https://en.wikipedia.org/wiki/Fafda', 0.7
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Fafda Jalebi')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Kombdi Vade (Malvani)  (https://en.wikipedia.org/wiki/Malvani_cuisine)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Kombdi Vade (Malvani)')::uuid, 'Malvani Chicken Curry with Fried Bread', 'real', 'english_gloss', 'Konkan, Maharashtra', 'english', 'https://en.wikipedia.org/wiki/Malvani_cuisine', 0.7
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Kombdi Vade (Malvani)')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Ghugni  (https://en.wikipedia.org/wiki/Ghugni)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Ghugni')::uuid, 'Ghugni Chaat', 'real', 'common_name', 'West Bengal', 'bengali', 'https://en.wikipedia.org/wiki/Ghugni', 0.8
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Ghugni')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Ghugni')::uuid, 'Ghughri', 'real', 'regional_name', 'Bihar', 'bhojpuri', 'https://en.wikipedia.org/wiki/Ghugni', 0.75
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Ghugni')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Ghugni')::uuid, 'Guguni', 'real', 'regional_name', 'Odisha', 'odia', 'https://en.wikipedia.org/wiki/Ghugni', 0.75
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Ghugni')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
