-- Seed: 128_seed_dish_aliases_b7.sql
-- WP-19 Dish Ontology — Batch 7 (~8 dishes: Karnataka/Tamil Nadu classics).
-- Same format/rules as prior batches: data_source='real', every row cites source_url + confidence.
-- Safety filter: no alias string may equal another catalogue dish name (checked against catalogue.json before writing).

-- Bisi Bele Bath  (https://en.wikipedia.org/wiki/Bisi_Bele_Bath)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Bisi Bele Bath')::uuid, 'Bisi Bele Huli Anna', 'real', 'common_name', 'Karnataka', 'kannada', 'https://en.wikipedia.org/wiki/Bisi_Bele_Bath', 0.8
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Bisi Bele Bath')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Bisi Bele Bath')::uuid, 'Hot Lentil Rice', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Bisi_Bele_Bath', 0.85
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Bisi Bele Bath')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Ragi Mudde  (https://en.wikipedia.org/wiki/Ragi_mudde)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Ragi Mudde')::uuid, 'Ragi Sangati', 'real', 'regional_name', 'Rayalaseema, Andhra Pradesh', 'telugu', 'https://en.wikipedia.org/wiki/Ragi_mudde', 0.8
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Ragi Mudde')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Ragi Mudde')::uuid, 'Ragi Kali', 'real', 'regional_name', 'Tamil Nadu', 'tamil', 'https://en.wikipedia.org/wiki/Ragi_mudde', 0.75
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Ragi Mudde')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Ragi Mudde')::uuid, 'Finger Millet Balls', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Ragi_mudde', 0.8
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Ragi Mudde')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Neer Dosa  (https://en.wikipedia.org/wiki/Neer_dosa)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Neer Dosa')::uuid, 'Neer Dose', 'real', 'spelling_variant', 'Tulu Nadu, Karnataka', 'tulu', 'https://en.wikipedia.org/wiki/Neer_dosa', 0.85
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Neer Dosa')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Neer Dosa')::uuid, 'Panpale', 'real', 'regional_name', 'Konkan', 'konkani', 'https://en.wikipedia.org/wiki/Neer_dosa', 0.7
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Neer Dosa')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Neer Dosa')::uuid, 'Watery Rice Crepe', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Neer_dosa', 0.75
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Neer Dosa')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Jolada Rotti  (https://en.wikipedia.org/wiki/Jolada_rotti)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Jolada Rotti')::uuid, 'Jowar Roti', 'real', 'common_name', 'North Karnataka', 'kannada', 'https://en.wikipedia.org/wiki/Jolada_rotti', 0.8
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Jolada Rotti')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Jolada Rotti')::uuid, 'Jawarichi Bhakri', 'real', 'regional_name', 'Maharashtra', 'marathi', 'https://en.wikipedia.org/wiki/Jolada_rotti', 0.75
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Jolada Rotti')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Jolada Rotti')::uuid, 'Sorghum Flatbread', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Jolada_rotti', 0.8
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Jolada Rotti')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Goli Baje  (https://en.wikipedia.org/wiki/Mangalore_bajji)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Goli Baje')::uuid, 'Mangalore Bajji', 'real', 'regional_name', 'Mangalore, Karnataka', 'kannada', 'https://en.wikipedia.org/wiki/Mangalore_bajji', 0.85
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Goli Baje')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Goli Baje')::uuid, 'Golibaje', 'real', 'spelling_variant', 'Tulu Nadu', 'tulu', 'https://en.wikipedia.org/wiki/Mangalore_bajji', 0.8
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Goli Baje')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Tamarind Rice  (https://en.wikipedia.org/wiki/Pulihora)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Tamarind Rice')::uuid, 'Puliyodharai', 'real', 'regional_name', 'Tamil Nadu', 'tamil', 'https://en.wikipedia.org/wiki/Pulihora', 0.85
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Tamarind Rice')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Tamarind Rice')::uuid, 'Puliyogare', 'real', 'regional_name', 'Karnataka', 'kannada', 'https://en.wikipedia.org/wiki/Pulihora', 0.8
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Tamarind Rice')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Tomato Rice  (https://www.sharmispassions.com/tomato-rice-thakkali-sadam/)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Tomato Rice')::uuid, 'Thakkali Sadam', 'real', 'regional_name', 'Tamil Nadu', 'tamil', 'https://www.sharmispassions.com/tomato-rice-thakkali-sadam/', 0.8
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Tomato Rice')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Kootu  (https://en.wikipedia.org/wiki/Koottu)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Kootu')::uuid, 'Koottu', 'real', 'spelling_variant', 'Tamil Nadu', 'tamil', 'https://en.wikipedia.org/wiki/Koottu', 0.85
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Kootu')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Kootu')::uuid, 'Koottukari', 'real', 'regional_name', 'Kerala', 'malayalam', 'https://en.wikipedia.org/wiki/Koottu', 0.75
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Kootu')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Kootu')::uuid, 'Lentil and Vegetable Medley', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Koottu', 0.75
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Kootu')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
