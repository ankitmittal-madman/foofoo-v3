-- Seed: 125_seed_dish_aliases_b4.sql
-- WP-19 Dish Ontology — Batch 4 (~22 dishes: Hyderabadi specialties + South Indian tiffin classics).
-- Same format/rules as prior batches: data_source='real', every row cites source_url + confidence.
-- Safety filter: no alias string may equal another catalogue dish name (checked against catalogue.json before writing).

-- Aloo Paratha  (https://en.wikipedia.org/wiki/Paratha)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Aloo Paratha')::uuid, 'Potato Stuffed Flatbread', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Paratha', 0.85) ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Chicken Curry  (https://en.wikipedia.org/wiki/Chicken_curry)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Chicken Curry')::uuid, 'Murgh Curry', 'real', 'common_name', NULL, 'hindi', 'https://en.wikipedia.org/wiki/Chicken_curry', 0.75) ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Egg Curry  (https://en.wikipedia.org/wiki/Egg_curry)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Egg Curry')::uuid, 'Anda Curry', 'real', 'common_name', NULL, 'hindi', 'https://en.wikipedia.org/wiki/Egg_curry', 0.8) ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Kulfi Falooda  (https://en.wikipedia.org/wiki/Falooda)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Kulfi Falooda')::uuid, 'Falooda Kulfi', 'real', 'common_name', NULL, 'hindi', 'https://en.wikipedia.org/wiki/Falooda', 0.75) ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Khubani Ka Meetha  (https://en.wikipedia.org/wiki/Khubani_ka_meetha)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Khubani Ka Meetha')::uuid, 'Stewed Apricot Dessert', 'real', 'english_gloss', 'Hyderabad', 'english', 'https://en.wikipedia.org/wiki/Khubani_ka_meetha', 0.85) ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Hyderabadi Marag  (https://en.wikipedia.org/wiki/Hyderabadi_marag)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Hyderabadi Marag')::uuid, 'Mutton Marag', 'real', 'common_name', 'Hyderabad', 'urdu', 'https://en.wikipedia.org/wiki/Hyderabadi_marag', 0.8) ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Hyderabadi Marag')::uuid, 'Spicy Mutton Bone Soup', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Hyderabadi_marag', 0.8) ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Dalcha  (https://en.wikipedia.org/wiki/Dalcha)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Dalcha')::uuid, 'Mutton Dalcha', 'real', 'common_name', 'Hyderabad', 'urdu', 'https://en.wikipedia.org/wiki/Dalcha', 0.8) ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Dalcha')::uuid, 'Lentil and Meat Stew', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Dalcha', 0.8) ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Osmania Biscuit  (https://en.wikipedia.org/wiki/Osmania_biscuit)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Osmania Biscuit')::uuid, 'Osmania Biscuits', 'real', 'spelling_variant', 'Hyderabad', 'urdu', 'https://en.wikipedia.org/wiki/Osmania_biscuit', 0.8) ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Irani Chai  (https://en.wikipedia.org/wiki/Irani_caf%C3%A9)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Irani Chai')::uuid, 'Hyderabadi Dum Chai', 'real', 'regional_name', 'Hyderabad', 'urdu', 'https://en.wikipedia.org/wiki/Irani_caf%C3%A9', 0.75) ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Irani Chai')::uuid, 'Irani Dum Chai', 'real', 'spelling_variant', 'Hyderabad', 'urdu', 'https://en.wikipedia.org/wiki/Irani_caf%C3%A9', 0.75) ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Tahari  (https://myfoodstory.com/tahari-tehri-recipe/)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Tahari')::uuid, 'Tehri', 'real', 'spelling_variant', 'Uttar Pradesh, Bihar', 'hindi', 'https://myfoodstory.com/tahari-tehri-recipe/', 0.8) ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Tahari')::uuid, 'Tehari', 'real', 'spelling_variant', 'Uttar Pradesh, Bihar', 'hindi', 'https://myfoodstory.com/tahari-tehri-recipe/', 0.75) ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Masala Dosa  (https://en.wikipedia.org/wiki/Masala_dosa)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Masala Dosa')::uuid, 'Masala Dosai', 'real', 'regional_name', 'Tamil Nadu', 'tamil', 'https://en.wikipedia.org/wiki/Masala_dosa', 0.85) ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Masala Dosa')::uuid, 'Masale Dose', 'real', 'regional_name', 'Karnataka', 'kannada', 'https://en.wikipedia.org/wiki/Masala_dosa', 0.85) ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Idli  (https://en.wikipedia.org/wiki/Idli)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Idli')::uuid, 'Idly', 'real', 'spelling_variant', NULL, 'tamil', 'https://en.wikipedia.org/wiki/Idli', 0.85) ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Idli')::uuid, 'Steamed Rice Cake', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Idli', 0.85) ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Sambar  (https://en.wikipedia.org/wiki/Sambar_(dish))
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Sambar')::uuid, 'Sambhar', 'real', 'spelling_variant', NULL, 'hindi', 'https://en.wikipedia.org/wiki/Sambar_(dish)', 0.85) ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Sambar')::uuid, 'Lentil and Vegetable Stew', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Sambar_(dish)', 0.8) ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Rasam  (https://en.wikipedia.org/wiki/Rasam)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Rasam')::uuid, 'Chaaru', 'real', 'regional_name', 'Andhra Pradesh, Telangana', 'telugu', 'https://en.wikipedia.org/wiki/Rasam', 0.85) ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Rasam')::uuid, 'Peppery Tamarind Soup', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Rasam', 0.8) ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Coconut Chutney  (https://en.wikipedia.org/wiki/Chutney)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Coconut Chutney')::uuid, 'Thengai Chutney', 'real', 'regional_name', 'Tamil Nadu', 'tamil', 'https://en.wikipedia.org/wiki/Chutney', 0.75) ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Medu Vada  (https://en.wikipedia.org/wiki/Vada_(food))
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Medu Vada')::uuid, 'Uzhunnu Vada', 'real', 'regional_name', 'Kerala', 'malayalam', 'https://en.wikipedia.org/wiki/Vada_(food)', 0.8) ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Medu Vada')::uuid, 'Savoury Lentil Doughnut', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Vada_(food)', 0.75) ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Uttapam  (https://en.wikipedia.org/wiki/Uttapam)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Uttapam')::uuid, 'Uthappam', 'real', 'spelling_variant', 'Tamil Nadu', 'tamil', 'https://en.wikipedia.org/wiki/Uttapam', 0.85) ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Uttapam')::uuid, 'Thick Savoury Rice Pancake', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Uttapam', 0.8) ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Pongal (Ven)  (https://en.wikipedia.org/wiki/Pongal_(dish))
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Pongal (Ven)')::uuid, 'Khara Pongal', 'real', 'common_name', 'Karnataka', 'kannada', 'https://en.wikipedia.org/wiki/Pongal_(dish)', 0.85) ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Pongal (Ven)')::uuid, 'Ghee Pongal', 'real', 'common_name', 'Tamil Nadu', 'tamil', 'https://en.wikipedia.org/wiki/Pongal_(dish)', 0.8) ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Pongal (Sweet)  (https://en.wikipedia.org/wiki/Pongal_(dish))
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Pongal (Sweet)')::uuid, 'Sakkarai Pongal', 'real', 'common_name', 'Tamil Nadu', 'tamil', 'https://en.wikipedia.org/wiki/Pongal_(dish)', 0.85) ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Curd Rice  (https://en.wikipedia.org/wiki/Curd_rice)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Curd Rice')::uuid, 'Thayir Sadam', 'real', 'regional_name', 'Tamil Nadu', 'tamil', 'https://en.wikipedia.org/wiki/Curd_rice', 0.85) ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Curd Rice')::uuid, 'Mosaru Anna', 'real', 'regional_name', 'Karnataka', 'kannada', 'https://en.wikipedia.org/wiki/Curd_rice', 0.8) ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Curd Rice')::uuid, 'Perugu Annam', 'real', 'regional_name', 'Andhra Pradesh, Telangana', 'telugu', 'https://en.wikipedia.org/wiki/Curd_rice', 0.8) ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Lemon Rice  (https://en.wikipedia.org/wiki/Lemon_rice)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Lemon Rice')::uuid, 'Elumichai Sadam', 'real', 'regional_name', 'Tamil Nadu', 'tamil', 'https://en.wikipedia.org/wiki/Lemon_rice', 0.8) ON CONFLICT (dish_id, synonym) DO NOTHING;
