-- Seed: 123_seed_dish_aliases_b2.sql
-- WP-19 Dish Ontology — Batch 2 of continued research (~40 dishes).
-- Same format/rules as 122_seed_dish_aliases.sql: data_source='real', every row cites source_url + confidence.
-- Safety filter: no alias string may equal another catalogue dish name (checked against catalogue.json before writing).

-- Butter Chicken  (https://en.wikipedia.org/wiki/Butter_chicken)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Butter Chicken')::uuid, 'Murgh Makhani', 'real', 'common_name', 'Punjab', 'hindi', 'https://en.wikipedia.org/wiki/Butter_chicken', 0.95) ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Butter Chicken')::uuid, 'Murgh Makhani Curry', 'real', 'common_name', NULL, 'hindi', 'https://en.wikipedia.org/wiki/Butter_chicken', 0.8) ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Dal Makhani  (https://en.wikipedia.org/wiki/Dal_makhani)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Dal Makhani')::uuid, 'Maa Ki Dal', 'real', 'regional_name', 'Punjab', 'punjabi', 'https://en.wikipedia.org/wiki/Dal_makhani', 0.85) ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Dal Makhani')::uuid, 'Buttered Black Lentils', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Dal_makhani', 0.85) ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Sarson Ka Saag  (https://en.wikipedia.org/wiki/Sarson_da_saag)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Sarson Ka Saag')::uuid, 'Sarson Da Saag', 'real', 'spelling_variant', 'Punjab', 'punjabi', 'https://en.wikipedia.org/wiki/Sarson_da_saag', 0.9) ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Sarson Ka Saag')::uuid, 'Mustard Greens Curry', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Sarson_da_saag', 0.85) ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Makki Ki Roti  (https://en.wikipedia.org/wiki/Makki_di_roti)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Makki Ki Roti')::uuid, 'Makki Di Roti', 'real', 'spelling_variant', 'Punjab', 'punjabi', 'https://en.wikipedia.org/wiki/Makki_di_roti', 0.9) ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Makki Ki Roti')::uuid, 'Corn Flatbread', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Makki_di_roti', 0.85) ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Tandoori Chicken  (https://en.wikipedia.org/wiki/Tandoori_chicken)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Tandoori Chicken')::uuid, 'Murgh Tandoori', 'real', 'common_name', NULL, 'hindi', 'https://en.wikipedia.org/wiki/Tandoori_chicken', 0.9) ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Paneer Tikka  (https://en.wikipedia.org/wiki/Paneer_tikka)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Paneer Tikka')::uuid, 'Grilled Cottage Cheese', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Paneer_tikka', 0.85) ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Amritsari Fish Fry  (https://www.indianhealthyrecipes.com/amritsari-tawa-fish-fry-pan-fried-amritsari-fish/)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Amritsari Fish Fry')::uuid, 'Amritsari Macchi', 'real', 'regional_name', 'Amritsar, Punjab', 'punjabi', 'https://www.indianhealthyrecipes.com/amritsari-tawa-fish-fry-pan-fried-amritsari-fish/', 0.8) ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Amritsari Fish Fry')::uuid, 'Amritsari Fried Fish', 'real', 'common_name', 'Amritsar, Punjab', 'english', 'https://www.indianhealthyrecipes.com/amritsari-tawa-fish-fry-pan-fried-amritsari-fish/', 0.8) ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Rajma  (https://en.wikipedia.org/wiki/Rajma)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Rajma')::uuid, 'Razma', 'real', 'spelling_variant', NULL, 'hindi', 'https://en.wikipedia.org/wiki/Rajma', 0.8) ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Rajma')::uuid, 'Laal Lobia', 'real', 'regional_name', 'North India', 'hindi', 'https://en.wikipedia.org/wiki/Rajma', 0.75) ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Rajma')::uuid, 'Kidney Bean Curry', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Rajma', 0.9) ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Palak Paneer  (https://en.wikipedia.org/wiki/Palak_paneer)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Palak Paneer')::uuid, 'Palak Chhena', 'real', 'regional_name', 'Odisha', 'odia', 'https://en.wikipedia.org/wiki/Palak_paneer', 0.75) ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Palak Paneer')::uuid, 'Spinach Cottage Cheese Curry', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Palak_paneer', 0.9) ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Aloo Gobhi  (https://en.wikipedia.org/wiki/Aloo_gobi)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Aloo Gobhi')::uuid, 'Aloo Gobi', 'real', 'spelling_variant', NULL, 'hindi', 'https://en.wikipedia.org/wiki/Aloo_gobi', 0.9) ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Aloo Gobhi')::uuid, 'Potato Cauliflower Curry', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Aloo_gobi', 0.9) ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Paneer Butter Masala  (https://en.wikipedia.org/wiki/Paneer_makhani)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Paneer Butter Masala')::uuid, 'Paneer Makhani', 'real', 'common_name', NULL, 'hindi', 'https://en.wikipedia.org/wiki/Paneer_makhani', 0.9) ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Shahi Paneer  (https://en.wikipedia.org/wiki/Shahi_paneer)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Shahi Paneer')::uuid, 'Shahi Panir', 'real', 'spelling_variant', NULL, 'hindi', 'https://en.wikipedia.org/wiki/Shahi_paneer', 0.75) ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Shahi Paneer')::uuid, 'Royal Cottage Cheese Curry', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Shahi_paneer', 0.8) ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Chicken Tikka  (https://en.wikipedia.org/wiki/Chicken_tikka)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Chicken Tikka')::uuid, 'Murgh Tikka', 'real', 'common_name', NULL, 'hindi', 'https://en.wikipedia.org/wiki/Chicken_tikka', 0.9) ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Seekh Kebab  (https://en.wikipedia.org/wiki/Seekh_kebab)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Seekh Kebab')::uuid, 'Sikh Kebab', 'real', 'spelling_variant', NULL, 'hindi', 'https://en.wikipedia.org/wiki/Seekh_kebab', 0.7) ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Seekh Kebab')::uuid, 'Skewered Minced Meat Kebab', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Seekh_kebab', 0.85) ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Kadhi Pakora  (https://en.wikipedia.org/wiki/Kadhi_chawal)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Kadhi Pakora')::uuid, 'Punjabi Kadhi', 'real', 'regional_name', 'Punjab', 'punjabi', 'https://en.wikipedia.org/wiki/Kadhi_chawal', 0.85) ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Kadhi Pakora')::uuid, 'Kadhi Badi', 'real', 'regional_name', 'Purvanchal, Bihar', 'bhojpuri', 'https://en.wikipedia.org/wiki/Kadhi_chawal', 0.75) ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Kadhi Pakora')::uuid, 'Yogurt Gram Flour Curry with Fritters', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Kadhi_chawal', 0.8) ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Naan  (https://en.wikipedia.org/wiki/Naan)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Naan')::uuid, 'Nan', 'real', 'spelling_variant', NULL, 'hindi', 'https://en.wikipedia.org/wiki/Naan', 0.75) ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Naan')::uuid, 'Leavened Tandoor Bread', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Naan', 0.85) ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Lassi (Sweet)  (https://en.wikipedia.org/wiki/Lassi)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Lassi (Sweet)')::uuid, 'Meethi Lassi', 'real', 'common_name', 'Punjab', 'punjabi', 'https://en.wikipedia.org/wiki/Lassi', 0.85) ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Lassi (Sweet)')::uuid, 'Sweet Yogurt Drink', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Lassi', 0.85) ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Lassi (Salted)  (https://en.wikipedia.org/wiki/Lassi)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Lassi (Salted)')::uuid, 'Namkeen Lassi', 'real', 'common_name', 'Punjab', 'punjabi', 'https://en.wikipedia.org/wiki/Lassi', 0.85) ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Lassi (Salted)')::uuid, 'Salted Yogurt Drink', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Lassi', 0.85) ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Matar Paneer  (https://en.wikipedia.org/wiki/Matar_paneer)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Matar Paneer')::uuid, 'Mutter Paneer', 'real', 'spelling_variant', NULL, 'hindi', 'https://en.wikipedia.org/wiki/Matar_paneer', 0.85) ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Matar Paneer')::uuid, 'Peas and Cottage Cheese Curry', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Matar_paneer', 0.85) ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Dal Tadka  (https://en.wikipedia.org/wiki/Dal_tadka)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Dal Tadka')::uuid, 'Dal Fry Tadka', 'real', 'common_name', NULL, 'hindi', 'https://en.wikipedia.org/wiki/Dal_tadka', 0.8) ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Dal Tadka')::uuid, 'Tempered Lentil Curry', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Dal_tadka', 0.85) ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Bhindi Masala  (https://en.wikipedia.org/wiki/Bhindi_masala)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Bhindi Masala')::uuid, 'Bhindi Fry', 'real', 'common_name', NULL, 'hindi', 'https://en.wikipedia.org/wiki/Bhindi_masala', 0.75) ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Bhindi Masala')::uuid, 'Spiced Okra', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Bhindi_masala', 0.85) ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Dum Aloo  (https://en.wikipedia.org/wiki/Dum_aloo)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Dum Aloo')::uuid, 'Kashmiri Dum Aloo', 'real', 'regional_name', 'Kashmir', 'kashmiri', 'https://en.wikipedia.org/wiki/Dum_aloo', 0.85) ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Dum Aloo')::uuid, 'Slow-Cooked Potato Curry', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Dum_aloo', 0.8) ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Jeera Rice  (https://en.wikipedia.org/wiki/Jeera_rice)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Jeera Rice')::uuid, 'Cumin Rice', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Jeera_rice', 0.9) ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Pindi Chole  (https://en.wikipedia.org/wiki/Chana_masala)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Pindi Chole')::uuid, 'Pindi Chana', 'real', 'regional_name', 'Rawalpindi/Punjab', 'punjabi', 'https://en.wikipedia.org/wiki/Chana_masala', 0.75) ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Keema Matar  (https://en.wikipedia.org/wiki/Keema)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Keema Matar')::uuid, 'Kheema Matar', 'real', 'spelling_variant', NULL, 'hindi', 'https://en.wikipedia.org/wiki/Keema', 0.75) ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Keema Matar')::uuid, 'Minced Meat with Peas', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Keema', 0.8) ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Phulka  (https://en.wikipedia.org/wiki/Chapati)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Phulka')::uuid, 'Chapati', 'real', 'common_name', NULL, 'hindi', 'https://en.wikipedia.org/wiki/Chapati', 0.8) ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Phulka')::uuid, 'Puffed Flatbread', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Chapati', 0.85) ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Bhatura  (https://en.wikipedia.org/wiki/Bhatura)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Bhatura')::uuid, 'Bhatoora', 'real', 'spelling_variant', NULL, 'hindi', 'https://en.wikipedia.org/wiki/Bhatura', 0.85) ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Bhatura')::uuid, 'Batura', 'real', 'spelling_variant', NULL, 'punjabi', 'https://en.wikipedia.org/wiki/Bhatura', 0.8) ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Bhatura')::uuid, 'Deep-Fried Leavened Bread', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Bhatura', 0.85) ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Dahi Bhalla  (https://en.wikipedia.org/wiki/Dahi_vada)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Dahi Bhalla')::uuid, 'Dahi Vada', 'real', 'common_name', NULL, 'hindi', 'https://en.wikipedia.org/wiki/Dahi_vada', 0.85) ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Dahi Bhalla')::uuid, 'Doi Bora', 'real', 'regional_name', 'West Bengal', 'bengali', 'https://en.wikipedia.org/wiki/Dahi_vada', 0.8) ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Dahi Bhalla')::uuid, 'Lentil Fritters in Yogurt', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Dahi_vada', 0.85) ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Aloo Tikki  (https://en.wikipedia.org/wiki/Aloo_tikki)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Aloo Tikki')::uuid, 'Aloo Ki Tikki', 'real', 'spelling_variant', NULL, 'hindi', 'https://en.wikipedia.org/wiki/Aloo_tikki', 0.85) ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Aloo Tikki')::uuid, 'Potato Cutlet', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Aloo_tikki', 0.85) ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Bhel Puri  (https://en.wikipedia.org/wiki/Bhelpuri)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Bhel Puri')::uuid, 'Bhelpuri', 'real', 'spelling_variant', 'Maharashtra', 'marathi', 'https://en.wikipedia.org/wiki/Bhelpuri', 0.9) ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Bhel Puri')::uuid, 'Puffed Rice Chaat', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Bhelpuri', 0.85) ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Chaat Papdi  (https://en.wikipedia.org/wiki/Papri_chat)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Chaat Papdi')::uuid, 'Papri Chaat', 'real', 'spelling_variant', NULL, 'hindi', 'https://en.wikipedia.org/wiki/Papri_chat', 0.9) ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Chaat Papdi')::uuid, 'Dahi Papdi Chaat', 'real', 'common_name', NULL, 'hindi', 'https://en.wikipedia.org/wiki/Papri_chat', 0.8) ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Kachori (Dal)  (https://en.wikipedia.org/wiki/Kachori)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Kachori (Dal)')::uuid, 'Khasta Dal Kachori', 'real', 'common_name', 'Rajasthan', 'hindi', 'https://en.wikipedia.org/wiki/Kachori', 0.8) ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Kachori (Dal)')::uuid, 'Lentil-Stuffed Fried Pastry', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Kachori', 0.8) ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Garlic Naan  (https://www.vegrecipesofindia.com/garlic-naan-recipe/)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Garlic Naan')::uuid, 'Lehsuni Naan', 'real', 'regional_name', NULL, 'hindi', 'https://www.vegrecipesofindia.com/garlic-naan-recipe/', 0.85) ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Garlic Naan')::uuid, 'Lasuni Naan', 'real', 'spelling_variant', NULL, 'hindi', 'https://www.vegrecipesofindia.com/garlic-naan-recipe/', 0.75) ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Mooli Paratha  (https://en.wikipedia.org/wiki/Paratha)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Mooli Paratha')::uuid, 'Mooli Ka Paratha', 'real', 'regional_name', 'Punjab', 'punjabi', 'https://en.wikipedia.org/wiki/Paratha', 0.85) ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Mooli Paratha')::uuid, 'Radish Stuffed Flatbread', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Paratha', 0.85) ON CONFLICT (dish_id, synonym) DO NOTHING;
