-- Seed: 122_seed_dish_aliases.sql
-- WP-19 Dish Ontology — web-researched, CITED regional/common names for catalogue dishes.
-- data_source='real' (each row carries its source_url + confidence). Idempotent.
-- Batch 1 (8 dishes); the remaining catalogue is filled by continued research batches.
-- Each INSERT is GUARDED by WHERE EXISTS on the target dish, so the seed is environment-robust:
-- it loads only aliases whose dish is present (e.g. the golden-sample subset in a partial DB) and
-- never FK-fails or orphans. dish_id = md5('ghar_re.dish:'||name)::uuid (the ghar_re seed convention).


-- Bharli Vangi  (https://smithakalluraya.com/stuffed-brinjal-bharli-vangi-badnekayi-ennegayi-bharwa-baingan-recipe/)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Bharli Vangi')::uuid, 'Bharwa Baingan', 'real', 'regional_name', 'North India', 'hindi', 'https://smithakalluraya.com/stuffed-brinjal-bharli-vangi-badnekayi-ennegayi-bharwa-baingan-recipe/', 0.95
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Bharli Vangi')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Bharli Vangi')::uuid, 'Ennai Kathrikai', 'real', 'regional_name', 'Tamil Nadu', 'tamil', 'https://smithakalluraya.com/stuffed-brinjal-bharli-vangi-badnekayi-ennegayi-bharwa-baingan-recipe/', 0.9
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Bharli Vangi')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Bharli Vangi')::uuid, 'Badanekayi Ennegayi', 'real', 'regional_name', 'Karnataka', 'kannada', 'https://smithakalluraya.com/stuffed-brinjal-bharli-vangi-badnekayi-ennegayi-bharwa-baingan-recipe/', 0.9
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Bharli Vangi')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Bharli Vangi')::uuid, 'Stuffed Brinjal', 'real', 'english_gloss', NULL, 'english', 'https://smithakalluraya.com/stuffed-brinjal-bharli-vangi-badnekayi-ennegayi-bharwa-baingan-recipe/', 0.97
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Bharli Vangi')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Poha  (https://en.wikipedia.org/wiki/Poha_(rice))
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Poha')::uuid, 'Pohe', 'real', 'spelling_variant', 'Maharashtra', 'marathi', 'https://en.wikipedia.org/wiki/Poha_(rice)', 0.9
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Poha')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Poha')::uuid, 'Pauwa', 'real', 'regional_name', 'North India', 'hindi', 'https://en.wikipedia.org/wiki/Poha_(rice)', 0.85
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Poha')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Poha')::uuid, 'Aval', 'real', 'regional_name', 'Tamil Nadu, Kerala', 'tamil', 'https://en.wikipedia.org/wiki/Poha_(rice)', 0.95
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Poha')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Poha')::uuid, 'Avalakki', 'real', 'regional_name', 'Karnataka', 'kannada', 'https://en.wikipedia.org/wiki/Poha_(rice)', 0.95
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Poha')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Poha')::uuid, 'Atukulu', 'real', 'regional_name', 'Andhra Pradesh, Telangana', 'telugu', 'https://en.wikipedia.org/wiki/Poha_(rice)', 0.95
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Poha')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Poha')::uuid, 'Chira', 'real', 'regional_name', 'West Bengal', 'bengali', 'https://en.wikipedia.org/wiki/Poha_(rice)', 0.9
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Poha')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Poha')::uuid, 'Chuda', 'real', 'regional_name', 'Odisha', 'odia', 'https://en.wikipedia.org/wiki/Poha_(rice)', 0.85
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Poha')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Poha')::uuid, 'Flattened Rice', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Poha_(rice)', 0.97
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Poha')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Baingan Bharta  (https://en.wikipedia.org/wiki/Baingan_bharta)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Baingan Bharta')::uuid, 'Baigan Chokha', 'real', 'regional_name', 'Bihar, Uttar Pradesh', 'bhojpuri', 'https://en.wikipedia.org/wiki/Baingan_bharta', 0.85
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Baingan Bharta')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Baingan Bharta')::uuid, 'Vangyache Bharit', 'real', 'regional_name', 'Maharashtra', 'marathi', 'https://en.wikipedia.org/wiki/Baingan_bharta', 0.9
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Baingan Bharta')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Baingan Bharta')::uuid, 'Begun Pora', 'real', 'regional_name', 'West Bengal', 'bengali', 'https://en.wikipedia.org/wiki/Baingan_bharta', 0.9
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Baingan Bharta')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Baingan Bharta')::uuid, 'Ringan no Olo', 'real', 'regional_name', 'Gujarat', 'gujarati', 'https://en.wikipedia.org/wiki/Baingan_bharta', 0.85
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Baingan Bharta')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Baingan Bharta')::uuid, 'Smoky Mashed Eggplant', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Baingan_bharta', 0.9
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Baingan Bharta')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Pithla  (https://en.wikipedia.org/wiki/Jhunka)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Pithla')::uuid, 'Pitla', 'real', 'spelling_variant', 'Maharashtra', 'marathi', 'https://en.wikipedia.org/wiki/Jhunka', 0.95
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Pithla')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Pithla')::uuid, 'Zunka', 'real', 'regional_name', 'Maharashtra, North Karnataka', 'marathi', 'https://en.wikipedia.org/wiki/Jhunka', 0.8
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Pithla')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Pithla')::uuid, 'Jhunka', 'real', 'spelling_variant', 'Maharashtra', 'marathi', 'https://en.wikipedia.org/wiki/Jhunka', 0.8
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Pithla')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Pithla')::uuid, 'Besan Curry', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Jhunka', 0.85
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Pithla')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Chole  (https://en.wikipedia.org/wiki/Chana_masala)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Chole')::uuid, 'Chana Masala', 'real', 'common_name', NULL, 'hindi', 'https://en.wikipedia.org/wiki/Chana_masala', 0.95
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Chole')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Chole')::uuid, 'Chole Masala', 'real', 'common_name', 'Punjab', 'punjabi', 'https://en.wikipedia.org/wiki/Chana_masala', 0.9
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Chole')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Chole')::uuid, 'Chholay', 'real', 'spelling_variant', NULL, 'hindi', 'https://en.wikipedia.org/wiki/Chana_masala', 0.85
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Chole')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Chole')::uuid, 'Kabuli Chana Masala', 'real', 'common_name', NULL, 'hindi', 'https://en.wikipedia.org/wiki/Chana_masala', 0.85
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Chole')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Chole')::uuid, 'Chickpea Curry', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Chana_masala', 0.95
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Chole')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Puran Poli  (https://en.wikipedia.org/wiki/Puran_poli)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Puran Poli')::uuid, 'Holige', 'real', 'regional_name', 'North Karnataka', 'kannada', 'https://en.wikipedia.org/wiki/Puran_poli', 0.95
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Puran Poli')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Puran Poli')::uuid, 'Boli', 'real', 'regional_name', 'Kerala, Tamil Nadu', 'malayalam', 'https://en.wikipedia.org/wiki/Puran_poli', 0.9
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Puran Poli')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Puran Poli')::uuid, 'Sweet Flatbread', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Puran_poli', 0.9
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Puran Poli')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Dhokla  (https://en.wikipedia.org/wiki/Dhokla)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Dhokla')::uuid, 'Khaman', 'real', 'common_name', 'Gujarat', 'gujarati', 'https://en.wikipedia.org/wiki/Dhokla', 0.85
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Dhokla')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Dhokla')::uuid, 'Khaman Dhokla', 'real', 'common_name', 'Gujarat', 'gujarati', 'https://en.wikipedia.org/wiki/Dhokla', 0.9
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Dhokla')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Dhokla')::uuid, 'Khatta Dhokla', 'real', 'regional_name', 'Gujarat', 'gujarati', 'https://en.wikipedia.org/wiki/Dhokla', 0.85
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Dhokla')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Dhokla')::uuid, 'Steamed Gram Flour Cake', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Dhokla', 0.9
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Dhokla')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Undhiyu  (https://en.wikipedia.org/wiki/Undhiyu)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Undhiyu')::uuid, 'Oondhiya', 'real', 'spelling_variant', 'Gujarat', 'gujarati', 'https://en.wikipedia.org/wiki/Undhiyu', 0.95
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Undhiyu')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Undhiyu')::uuid, 'Umbadiyu', 'real', 'regional_name', 'South Gujarat', 'gujarati', 'https://en.wikipedia.org/wiki/Undhiyu', 0.85
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Undhiyu')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Undhiyu')::uuid, 'Surti Undhiyu', 'real', 'regional_name', 'Surat', 'gujarati', 'https://en.wikipedia.org/wiki/Undhiyu', 0.9
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Undhiyu')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Undhiyu')::uuid, 'Mixed Vegetable Curry', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Undhiyu', 0.85
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Undhiyu')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
