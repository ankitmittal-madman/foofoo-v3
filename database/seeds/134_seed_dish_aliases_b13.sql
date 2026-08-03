-- Seed: 134_seed_dish_aliases_b13.sql
-- WP-19 Dish Ontology — Batch 13 (~11 dishes: Rajasthani + Kashmiri + Andhra cuisine).
-- Same format/rules as prior batches: data_source='real', every row cites source_url + confidence.
-- GUARDED inserts (WHERE EXISTS) matching the env-robust pattern established in seeds 122-133.
-- Safety filter: no alias string may equal another catalogue dish name (checked against catalogue.json before writing).
-- Note: "Goshtaba" (no "s") is itself a distinct catalogue dish from "Gushtaba" below — excluded as alias.
-- Note: "Zarda" is itself a distinct catalogue dish (seed 124) — excluded as alias for Modur Pulao.

-- Dal Baati Churma  (https://en.wikipedia.org/wiki/Dal_bati_churma)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Dal Baati Churma')::uuid, 'Dal Bati Churma', 'real', 'spelling_variant', 'Rajasthan', 'rajasthani', 'https://en.wikipedia.org/wiki/Dal_bati_churma', 0.85
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Dal Baati Churma')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Laal Maas  (https://en.wikipedia.org/wiki/Laal_maas)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Laal Maas')::uuid, 'Ratto Maas', 'real', 'regional_name', 'Rajasthan', 'rajasthani', 'https://en.wikipedia.org/wiki/Laal_maas', 0.75
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Laal Maas')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Laal Maas')::uuid, 'Fiery Red Mutton Curry', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Laal_maas', 0.8
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Laal Maas')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Gatte Ki Sabzi  (https://www.vegrecipesofindia.com/gatte-ki-sabji-recipe/)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Gatte Ki Sabzi')::uuid, 'Gatte Ki Sabji', 'real', 'spelling_variant', 'Rajasthan', 'rajasthani', 'https://www.vegrecipesofindia.com/gatte-ki-sabji-recipe/', 0.8
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Gatte Ki Sabzi')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Gatte Ki Sabzi')::uuid, 'Gram Flour Dumpling Curry', 'real', 'english_gloss', NULL, 'english', 'https://www.vegrecipesofindia.com/gatte-ki-sabji-recipe/', 0.8
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Gatte Ki Sabzi')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Ker Sangri  (https://medium.com/@narang.kapil/ker-sangri-a-delightful-taste-of-the-rajasthani-desert-9cb7efef024)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Ker Sangri')::uuid, 'Desert Berry and Bean Curry', 'real', 'english_gloss', 'Rajasthan', 'english', 'https://medium.com/@narang.kapil/ker-sangri-a-delightful-taste-of-the-rajasthani-desert-9cb7efef024', 0.75
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Ker Sangri')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Dum Aloo (Kashmiri)  (https://en.wikipedia.org/wiki/Dum_aloo)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Dum Aloo (Kashmiri)')::uuid, 'Dum Olav', 'real', 'regional_name', 'Kashmir', 'kashmiri', 'https://en.wikipedia.org/wiki/Dum_aloo', 0.8
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Dum Aloo (Kashmiri)')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Yakhni  (https://en.wikipedia.org/wiki/Yakhni)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Yakhni')::uuid, 'Kashmiri Yogurt Meat Curry', 'real', 'english_gloss', 'Kashmir', 'english', 'https://en.wikipedia.org/wiki/Yakhni', 0.75
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Yakhni')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Kahwa  (https://en.wikipedia.org/wiki/Kahwah)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Kahwa')::uuid, 'Kehwa', 'real', 'spelling_variant', 'Kashmir', 'kashmiri', 'https://en.wikipedia.org/wiki/Kahwah', 0.8
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Kahwa')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Kahwa')::uuid, 'Kashmiri Saffron Green Tea', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Kahwah', 0.8
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Kahwa')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Noon Chai  (https://en.wikipedia.org/wiki/Noon_chai)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Noon Chai')::uuid, 'Nun Chai', 'real', 'spelling_variant', 'Kashmir', 'kashmiri', 'https://en.wikipedia.org/wiki/Noon_chai', 0.8
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Noon Chai')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Noon Chai')::uuid, 'Gulabi Chai', 'real', 'common_name', 'Kashmir', 'kashmiri', 'https://en.wikipedia.org/wiki/Noon_chai', 0.8
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Noon Chai')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Gushtaba  (https://en.wikipedia.org/wiki/Goshtaab)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Gushtaba')::uuid, 'King of Kashmiri Wazwan Meatballs', 'real', 'english_gloss', 'Kashmir', 'english', 'https://en.wikipedia.org/wiki/Goshtaab', 0.7
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Gushtaba')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Haak (Kashmiri Greens)  (https://holycowvegan.net/kashmiri-collard-greens/)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Haak (Kashmiri Greens)')::uuid, 'Haakh', 'real', 'spelling_variant', 'Kashmir', 'kashmiri', 'https://holycowvegan.net/kashmiri-collard-greens/', 0.75
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Haak (Kashmiri Greens)')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Gongura Chicken  (https://www.indianhealthyrecipes.com/gongura-chicken-curry-chicken-with-red-sorrel-leaves/)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Gongura Chicken')::uuid, 'Ambadi Chicken', 'real', 'regional_name', 'Andhra Pradesh, Telangana', 'telugu', 'https://www.indianhealthyrecipes.com/gongura-chicken-curry-chicken-with-red-sorrel-leaves/', 0.7
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Gongura Chicken')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Gongura Chicken')::uuid, 'Sorrel Leaf Chicken Curry', 'real', 'english_gloss', NULL, 'english', 'https://www.indianhealthyrecipes.com/gongura-chicken-curry-chicken-with-red-sorrel-leaves/', 0.8
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Gongura Chicken')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Gutti Vankaya  (https://www.vegrecipesofindia.com/gutti-vankaya-kura-recipe/)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Gutti Vankaya')::uuid, 'Gutti Vankaya Kura', 'real', 'common_name', 'Rayalaseema, Andhra Pradesh', 'telugu', 'https://www.vegrecipesofindia.com/gutti-vankaya-kura-recipe/', 0.8
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Gutti Vankaya')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Gutti Vankaya')::uuid, 'Stuffed Baby Eggplant Curry', 'real', 'english_gloss', NULL, 'english', 'https://www.vegrecipesofindia.com/gutti-vankaya-kura-recipe/', 0.8
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Gutti Vankaya')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
