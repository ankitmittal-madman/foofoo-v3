-- Seed: 129_seed_dish_aliases_b8.sql
-- WP-19 Dish Ontology — Batch 8 (~15 dishes: Karnataka classics + Bengali cuisine).
-- Same format/rules as prior batches: data_source='real', every row cites source_url + confidence.
-- GUARDED inserts (WHERE EXISTS) matching the env-robust pattern established in seeds 122-128.
-- Safety filter: no alias string may equal another catalogue dish name (checked against catalogue.json before writing).

-- Mysore Pak  (https://en.wikipedia.org/wiki/Mysore_pak)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Mysore Pak')::uuid, 'Mysore Bhog', 'real', 'regional_name', 'Mysore, Karnataka', 'kannada', 'https://en.wikipedia.org/wiki/Mysore_pak', 0.7
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Mysore Pak')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Vangi Bath  (https://en.wikipedia.org/wiki/Vangibath)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Vangi Bath')::uuid, 'Vangi Bhath', 'real', 'spelling_variant', 'Karnataka', 'kannada', 'https://en.wikipedia.org/wiki/Vangibath', 0.8
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Vangi Bath')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Vangi Bath')::uuid, 'Brinjal Rice', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Vangibath', 0.85
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Vangi Bath')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Kesari Bath  (https://en.wikipedia.org/wiki/Kesari_bat)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Kesari Bath')::uuid, 'Rava Kesari', 'real', 'regional_name', 'Tamil Nadu, Telangana', 'telugu', 'https://en.wikipedia.org/wiki/Kesari_bat', 0.8
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Kesari Bath')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Kesari Bath')::uuid, 'Sheera', 'real', 'regional_name', 'Maharashtra', 'marathi', 'https://en.wikipedia.org/wiki/Kesari_bat', 0.75
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Kesari Bath')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Akki Rotti  (https://en.wikipedia.org/wiki/Akki_rotti)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Akki Rotti')::uuid, 'Akki Roti', 'real', 'spelling_variant', 'Karnataka', 'kannada', 'https://en.wikipedia.org/wiki/Akki_rotti', 0.85
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Akki Rotti')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Akki Rotti')::uuid, 'Rice Flour Flatbread', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Akki_rotti', 0.8
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Akki Rotti')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Mangalorean Fish Gassi  (https://simpleindianmeals.com/mangalorean-fish-curry-meen-gassi/)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Mangalorean Fish Gassi')::uuid, 'Meen Gassi', 'real', 'regional_name', 'Mangalore, Karnataka', 'tulu', 'https://simpleindianmeals.com/mangalorean-fish-curry-meen-gassi/', 0.8
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Mangalorean Fish Gassi')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Machher Jhol  (https://en.wikipedia.org/wiki/Machher_jhol)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Machher Jhol')::uuid, 'Macher Jhol', 'real', 'spelling_variant', 'West Bengal', 'bengali', 'https://en.wikipedia.org/wiki/Machher_jhol', 0.85
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Machher Jhol')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Machher Jhol')::uuid, 'Bengali Fish Curry', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Machher_jhol', 0.85
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Machher Jhol')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Shorshe Ilish  (https://en.wikipedia.org/wiki/Shorshe_ilish)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Shorshe Ilish')::uuid, 'Sorshe Ilish', 'real', 'spelling_variant', 'West Bengal', 'bengali', 'https://en.wikipedia.org/wiki/Shorshe_ilish', 0.8
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Shorshe Ilish')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Shorshe Ilish')::uuid, 'Hilsa in Mustard Gravy', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Shorshe_ilish', 0.85
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Shorshe Ilish')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Aloo Posto  (https://www.vegrecipesofindia.com/aloo-posto-recipe/)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Aloo Posto')::uuid, 'Aloo Poshto', 'real', 'spelling_variant', 'West Bengal', 'bengali', 'https://www.vegrecipesofindia.com/aloo-posto-recipe/', 0.8
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Aloo Posto')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Aloo Posto')::uuid, 'Potato Poppy Seed Curry', 'real', 'english_gloss', NULL, 'english', 'https://www.vegrecipesofindia.com/aloo-posto-recipe/', 0.85
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Aloo Posto')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Luchi  (https://en.wikipedia.org/wiki/Luchi)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Luchi')::uuid, 'Deep-Fried Maida Bread', 'real', 'english_gloss', 'West Bengal', 'english', 'https://en.wikipedia.org/wiki/Luchi', 0.8
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Luchi')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Cholar Dal  (https://holycowvegan.net/cholar-dal/)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Cholar Dal')::uuid, 'Chholar Dal', 'real', 'spelling_variant', 'West Bengal', 'bengali', 'https://holycowvegan.net/cholar-dal/', 0.8
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Cholar Dal')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Cholar Dal')::uuid, 'Bengali Chana Dal with Coconut', 'real', 'english_gloss', NULL, 'english', 'https://holycowvegan.net/cholar-dal/', 0.75
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Cholar Dal')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Kosha Mangsho  (https://www.whiskaffair.com/bengali-kosha-mangsho-recipe/)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Kosha Mangsho')::uuid, 'Mutton Kosha', 'real', 'common_name', 'West Bengal', 'bengali', 'https://www.whiskaffair.com/bengali-kosha-mangsho-recipe/', 0.8
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Kosha Mangsho')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Kosha Mangsho')::uuid, 'Slow-Cooked Bengali Mutton Curry', 'real', 'english_gloss', NULL, 'english', 'https://www.whiskaffair.com/bengali-kosha-mangsho-recipe/', 0.8
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Kosha Mangsho')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Mishti Doi  (https://en.wikipedia.org/wiki/Mishti_doi)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Mishti Doi')::uuid, 'Lal Doi', 'real', 'regional_name', 'West Bengal', 'bengali', 'https://en.wikipedia.org/wiki/Mishti_doi', 0.7
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Mishti Doi')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Mishti Doi')::uuid, 'Sweet Fermented Yogurt', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Mishti_doi', 0.85
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Mishti Doi')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Sandesh  (https://en.wikipedia.org/wiki/Sandesh_(confectionery))
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Sandesh')::uuid, 'Sondesh', 'real', 'spelling_variant', 'West Bengal', 'bengali', 'https://en.wikipedia.org/wiki/Sandesh_(confectionery)', 0.75
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Sandesh')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Rasgulla  (https://en.wikipedia.org/wiki/Rasgulla)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Rasgulla')::uuid, 'Rosogolla', 'real', 'regional_name', 'West Bengal', 'bengali', 'https://en.wikipedia.org/wiki/Rasgulla', 0.85
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Rasgulla')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Rasgulla')::uuid, 'Rasagola', 'real', 'regional_name', 'Odisha', 'odia', 'https://en.wikipedia.org/wiki/Rasgulla', 0.85
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Rasgulla')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Begun Bhaja  (https://www.vegrecipesofindia.com/baingan-fry-baingan-bhaja-eggplant-fries/)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Begun Bhaja')::uuid, 'Baingan Bhaja', 'real', 'regional_name', NULL, 'hindi', 'https://www.vegrecipesofindia.com/baingan-fry-baingan-bhaja-eggplant-fries/', 0.75
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Begun Bhaja')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Begun Bhaja')::uuid, 'Fried Eggplant Slices', 'real', 'english_gloss', NULL, 'english', 'https://www.vegrecipesofindia.com/baingan-fry-baingan-bhaja-eggplant-fries/', 0.8
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Begun Bhaja')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
