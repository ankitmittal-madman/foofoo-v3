-- Seed: 124_seed_dish_aliases_b3.sql
-- WP-19 Dish Ontology — Batch 3 of continued research (~35 dishes, mostly Awadhi/Hyderabadi/Mughlai).
-- Same format/rules as 122/123: data_source='real', every row cites source_url + confidence.
-- Safety filter: no alias string may equal another catalogue dish name (checked against catalogue.json before writing).

-- Kulcha  (https://en.wikipedia.org/wiki/Kulcha)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Kulcha')::uuid, 'Amritsari Kulcha', 'real', 'regional_name', 'Amritsar, Punjab', 'punjabi', 'https://en.wikipedia.org/wiki/Kulcha', 0.8
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Kulcha')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Kulcha')::uuid, 'Leavened Stuffed Flatbread', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Kulcha', 0.8
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Kulcha')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Egg Bhurji  (https://en.wikipedia.org/wiki/Egg_bhurji)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Egg Bhurji')::uuid, 'Anda Bhurji', 'real', 'common_name', NULL, 'hindi', 'https://en.wikipedia.org/wiki/Egg_bhurji', 0.9
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Egg Bhurji')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Egg Bhurji')::uuid, 'Ande Ka Khagina', 'real', 'regional_name', NULL, 'urdu', 'https://en.wikipedia.org/wiki/Egg_bhurji', 0.75
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Egg Bhurji')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Egg Bhurji')::uuid, 'Indian Scrambled Eggs', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Egg_bhurji', 0.85
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Egg Bhurji')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Mughlai Paratha  (https://en.wikipedia.org/wiki/Mughlai_paratha)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Mughlai Paratha')::uuid, 'Mughlai Porota', 'real', 'regional_name', 'West Bengal', 'bengali', 'https://en.wikipedia.org/wiki/Mughlai_paratha', 0.8
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Mughlai Paratha')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Mughlai Paratha')::uuid, 'Egg-Stuffed Fried Flatbread', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Mughlai_paratha', 0.8
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Mughlai Paratha')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Rumali Roti  (https://en.wikipedia.org/wiki/Rumali_roti)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Rumali Roti')::uuid, 'Manda Roti', 'real', 'regional_name', 'South India', 'kannada', 'https://en.wikipedia.org/wiki/Rumali_roti', 0.75
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Rumali Roti')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Rumali Roti')::uuid, 'Handkerchief Bread', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Rumali_roti', 0.85
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Rumali Roti')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Nihari  (https://en.wikipedia.org/wiki/Nihari)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Nihari')::uuid, 'Nahari', 'real', 'spelling_variant', 'Lucknow, Delhi', 'urdu', 'https://en.wikipedia.org/wiki/Nihari', 0.85
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Nihari')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Nihari')::uuid, 'Slow-Cooked Meat Stew', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Nihari', 0.8
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Nihari')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Mutton Rogan Josh  (https://en.wikipedia.org/wiki/Rogan_josh)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Mutton Rogan Josh')::uuid, 'Rogan Ghosht', 'real', 'spelling_variant', 'Kashmir', 'kashmiri', 'https://en.wikipedia.org/wiki/Rogan_josh', 0.8
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Mutton Rogan Josh')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Mutton Rogan Josh')::uuid, 'Kashmiri Red Lamb Curry', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Rogan_josh', 0.85
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Mutton Rogan Josh')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Kakori Kebab  (https://www.slurrp.com/article/kakori-kebabs-from-uttar-pradesh-history-and-origin-of-the-iconic-dish-explained-1725611897858)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Kakori Kebab')::uuid, 'Kakori Kabab', 'real', 'spelling_variant', 'Kakori, Uttar Pradesh', 'urdu', 'https://www.slurrp.com/article/kakori-kebabs-from-uttar-pradesh-history-and-origin-of-the-iconic-dish-explained-1725611897858', 0.75
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Kakori Kebab')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Shami Kebab  (https://en.wikipedia.org/wiki/Shami_kebab)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Shami Kebab')::uuid, 'Shammi Kabab', 'real', 'spelling_variant', 'Lucknow', 'urdu', 'https://en.wikipedia.org/wiki/Shami_kebab', 0.85
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Shami Kebab')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Pasanda  (https://en.wikipedia.org/wiki/Pasanda)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Pasanda')::uuid, 'Murgh Pasanda', 'real', 'common_name', NULL, 'urdu', 'https://en.wikipedia.org/wiki/Pasanda', 0.75
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Pasanda')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Pasanda')::uuid, 'Pasanday', 'real', 'spelling_variant', 'Pakistan', 'urdu', 'https://en.wikipedia.org/wiki/Pasanda', 0.75
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Pasanda')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Zarda  (https://en.wikipedia.org/wiki/Zarda_(food))
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Zarda')::uuid, 'Zarda Pulao', 'real', 'common_name', NULL, 'hindi', 'https://en.wikipedia.org/wiki/Zarda_(food)', 0.8
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Zarda')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Zarda')::uuid, 'Sweet Saffron Rice', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Zarda_(food)', 0.85
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Zarda')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Phirni  (https://en.wikipedia.org/wiki/Phirni)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Phirni')::uuid, 'Firni', 'real', 'spelling_variant', NULL, 'hindi', 'https://en.wikipedia.org/wiki/Phirni', 0.9
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Phirni')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Phirni')::uuid, 'Firin', 'real', 'regional_name', 'Kashmir', 'kashmiri', 'https://en.wikipedia.org/wiki/Phirni', 0.75
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Phirni')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Phirni')::uuid, 'Ground Rice Pudding', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Phirni', 0.85
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Phirni')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Haleem  (https://en.wikipedia.org/wiki/Hyderabadi_haleem)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Haleem')::uuid, 'Daleem', 'real', 'regional_name', 'Hyderabad', 'urdu', 'https://en.wikipedia.org/wiki/Hyderabadi_haleem', 0.75
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Haleem')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Haleem')::uuid, 'Wheat and Meat Porridge', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Hyderabadi_haleem', 0.8
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Haleem')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Rezala  (https://en.wikipedia.org/wiki/Chicken_Rezala)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Rezala')::uuid, 'Chicken Rezala', 'real', 'common_name', 'West Bengal', 'bengali', 'https://en.wikipedia.org/wiki/Chicken_Rezala', 0.85
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Rezala')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Rezala')::uuid, 'Rozila', 'real', 'regional_name', 'East Bengal', 'bengali', 'https://en.wikipedia.org/wiki/Chicken_Rezala', 0.7
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Rezala')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Hyderabadi Chicken Biryani  (https://en.wikipedia.org/wiki/Hyderabadi_biryani)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Hyderabadi Chicken Biryani')::uuid, 'Hyderabadi Murgh Dum Biryani', 'real', 'common_name', 'Hyderabad', 'urdu', 'https://en.wikipedia.org/wiki/Hyderabadi_biryani', 0.8
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Hyderabadi Chicken Biryani')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Hyderabadi Mutton Biryani  (https://en.wikipedia.org/wiki/Hyderabadi_biryani)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Hyderabadi Mutton Biryani')::uuid, 'Kacchi Gosht Biryani', 'real', 'regional_name', 'Hyderabad', 'urdu', 'https://en.wikipedia.org/wiki/Hyderabadi_biryani', 0.75
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Hyderabadi Mutton Biryani')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Mirchi Ka Salan  (https://en.wikipedia.org/wiki/Mirchi_ka_salan)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Mirchi Ka Salan')::uuid, 'Biryani Salan', 'real', 'common_name', 'Hyderabad', 'urdu', 'https://en.wikipedia.org/wiki/Mirchi_ka_salan', 0.75
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Mirchi Ka Salan')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Mirchi Ka Salan')::uuid, 'Curried Chilli Peppers', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Mirchi_ka_salan', 0.85
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Mirchi Ka Salan')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Double Ka Meetha  (https://en.wikipedia.org/wiki/Double_ka_meetha)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Double Ka Meetha')::uuid, 'Hyderabadi Bread Pudding', 'real', 'english_gloss', 'Hyderabad', 'english', 'https://en.wikipedia.org/wiki/Double_ka_meetha', 0.85
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Double Ka Meetha')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Bagara Baingan  (https://en.wikipedia.org/wiki/Baghaar-e-baingan)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Bagara Baingan')::uuid, 'Baghare Baingan', 'real', 'spelling_variant', 'Hyderabad', 'urdu', 'https://en.wikipedia.org/wiki/Baghaar-e-baingan', 0.85
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Bagara Baingan')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Bagara Baingan')::uuid, 'Bhagaray Baigan', 'real', 'spelling_variant', 'Hyderabad', 'urdu', 'https://en.wikipedia.org/wiki/Baghaar-e-baingan', 0.75
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Bagara Baingan')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Sev Puri  (https://en.wikipedia.org/wiki/Sev_puri)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Sev Puri')::uuid, 'Sev Batata Puri', 'real', 'regional_name', 'Mumbai, Maharashtra', 'marathi', 'https://en.wikipedia.org/wiki/Sev_puri', 0.8
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Sev Puri')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Baida Roti  (https://www.slurrp.com/article/chicken-baida-roti-crispy-layered-chicken-and-egg-paratha-1661785269423)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Baida Roti')::uuid, 'Layered Meat and Egg Paratha', 'real', 'english_gloss', 'Mumbai', 'english', 'https://www.slurrp.com/article/chicken-baida-roti-crispy-layered-chicken-and-egg-paratha-1661785269423', 0.75
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Baida Roti')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Warqi Paratha  (https://www.slurrp.com/article/what-makes-the-awadhi-warqi-paratha-so-special-and-what-can-you-pair-with-it-1654589805366)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Warqi Paratha')::uuid, 'Warqui Paratha', 'real', 'spelling_variant', 'Awadh', 'urdu', 'https://www.slurrp.com/article/what-makes-the-awadhi-warqi-paratha-so-special-and-what-can-you-pair-with-it-1654589805366', 0.75
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Warqi Paratha')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Warqi Paratha')::uuid, 'Layered Flaky Flatbread', 'real', 'english_gloss', NULL, 'english', 'https://www.slurrp.com/article/what-makes-the-awadhi-warqi-paratha-so-special-and-what-can-you-pair-with-it-1654589805366', 0.8
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Warqi Paratha')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Pathar Ka Gosht  (https://en.wikipedia.org/wiki/Pathar-ka-Gosht)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Pathar Ka Gosht')::uuid, 'Patthar Ka Gosht', 'real', 'spelling_variant', 'Hyderabad', 'urdu', 'https://en.wikipedia.org/wiki/Pathar-ka-Gosht', 0.85
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Pathar Ka Gosht')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Pathar Ka Gosht')::uuid, 'Stone-Grilled Meat', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Pathar-ka-Gosht', 0.85
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Pathar Ka Gosht')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Lukhmi  (https://en.wikipedia.org/wiki/Lukhmi)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Lukhmi')::uuid, 'Luqmi', 'real', 'spelling_variant', 'Hyderabad', 'urdu', 'https://en.wikipedia.org/wiki/Lukhmi', 0.85
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Lukhmi')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Lukhmi')::uuid, 'Hyderabadi Square Samosa', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Lukhmi', 0.75
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Lukhmi')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Mutton Korma  (https://foodbound.wordpress.com/2015/09/24/mutton-korma-mutton-qorma-%E0%A4%AE%E0%A4%9F%E0%A4%A8-%E0%A4%95%E0%A5%8B%E0%A4%B0%E0%A4%AE%E0%A4%BE/)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Mutton Korma')::uuid, 'Mutton Qorma', 'real', 'spelling_variant', NULL, 'urdu', 'https://foodbound.wordpress.com/2015/09/24/mutton-korma-mutton-qorma-%E0%A4%AE%E0%A4%9F%E0%A4%A8-%E0%A4%95%E0%A5%8B%E0%A4%B0%E0%A4%AE%E0%A4%BE/', 0.8
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Mutton Korma')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Galouti Kebab  (https://en.wikipedia.org/wiki/Tunde_ke_kabab)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Galouti Kebab')::uuid, 'Galawati Kebab', 'real', 'spelling_variant', 'Lucknow', 'urdu', 'https://en.wikipedia.org/wiki/Tunde_ke_kabab', 0.85
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Galouti Kebab')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT md5('ghar_re.dish:' || 'Galouti Kebab')::uuid, 'Melt-in-the-Mouth Kebab', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Tunde_ke_kabab', 0.8
WHERE EXISTS (SELECT 1 FROM ghar_re.dishes WHERE id = md5('ghar_re.dish:' || 'Galouti Kebab')::uuid)
ON CONFLICT (dish_id, synonym) DO NOTHING;
