-- Seed: 127_seed_dish_aliases_b6.sql
-- WP-19 Dish Ontology — Batch 6 (~10 dishes: Kerala Sadya/Malabar classics).
-- Same format/rules as prior batches: data_source='real', every row cites source_url + confidence.
-- Safety filter: no alias string may equal another catalogue dish name (checked against catalogue.json before writing).

-- Sadya Thali  (https://en.wikipedia.org/wiki/Sadya)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Sadya Thali')::uuid, 'Sadya', 'real', 'common_name', 'Kerala', 'malayalam', 'https://en.wikipedia.org/wiki/Sadya', 0.85) ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Sadya Thali')::uuid, 'Onasadya', 'real', 'common_name', 'Kerala', 'malayalam', 'https://en.wikipedia.org/wiki/Sadya', 0.8) ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Sadya Thali')::uuid, 'Kerala Banana-Leaf Feast', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Sadya', 0.8) ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Malabar Biryani  (https://en.wikipedia.org/wiki/Thalassery_cuisine)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Malabar Biryani')::uuid, 'Thalassery Biryani', 'real', 'regional_name', 'Thalassery, Kerala', 'malayalam', 'https://en.wikipedia.org/wiki/Thalassery_cuisine', 0.85) ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Pathiri  (https://en.wikipedia.org/wiki/Pathiri)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Pathiri')::uuid, 'Ari Pathil', 'real', 'regional_name', 'Malabar, Kerala', 'malayalam', 'https://en.wikipedia.org/wiki/Pathiri', 0.75) ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Pathiri')::uuid, 'Rice Flour Flatbread', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Pathiri', 0.8) ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Unniyappam  (https://en.wikipedia.org/wiki/Unni_appam)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Unniyappam')::uuid, 'Unni Appam', 'real', 'spelling_variant', 'Kerala', 'malayalam', 'https://en.wikipedia.org/wiki/Unni_appam', 0.85) ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Unniyappam')::uuid, 'Karollappam', 'real', 'regional_name', 'Kerala', 'malayalam', 'https://en.wikipedia.org/wiki/Unni_appam', 0.75) ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Olan  (https://mariasmenu.com/vegetarian/kerala-olan-onam-recipe)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Olan')::uuid, 'Ash Gourd and Coconut Milk Curry', 'real', 'english_gloss', 'Kerala', 'english', 'https://mariasmenu.com/vegetarian/kerala-olan-onam-recipe', 0.8) ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Kadala Curry  (https://www.vegrecipesofindia.com/kadala-curry-recipe-kadala-kari/)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Kadala Curry')::uuid, 'Kadala Kari', 'real', 'spelling_variant', 'Kerala', 'malayalam', 'https://www.vegrecipesofindia.com/kadala-curry-recipe-kadala-kari/', 0.8) ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Kadala Curry')::uuid, 'Black Chickpea Curry', 'real', 'english_gloss', NULL, 'english', 'https://www.vegrecipesofindia.com/kadala-curry-recipe-kadala-kari/', 0.85) ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Sundal  (https://www.vegrecipesofindia.com/chana-sundal/)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Sundal')::uuid, 'Kondakadalai Sundal', 'real', 'common_name', 'Tamil Nadu', 'tamil', 'https://www.vegrecipesofindia.com/chana-sundal/', 0.75) ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Sundal')::uuid, 'Tempered Legume Salad', 'real', 'english_gloss', NULL, 'english', 'https://www.vegrecipesofindia.com/chana-sundal/', 0.75) ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Kothu Parotta  (https://en.wikipedia.org/wiki/South_Indian_parotta)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Kothu Parotta')::uuid, 'Kothu Parota', 'real', 'spelling_variant', 'Tamil Nadu', 'tamil', 'https://en.wikipedia.org/wiki/South_Indian_parotta', 0.75) ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Kothu Parotta')::uuid, 'Shredded Flatbread Stir-Fry', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/South_Indian_parotta', 0.75) ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Banana Chips  (https://www.vegrecipesofindia.com/banana-chips-or-banana-wafers-recipe/)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Banana Chips')::uuid, 'Kaya Upperi', 'real', 'regional_name', 'Kerala', 'malayalam', 'https://www.vegrecipesofindia.com/banana-chips-or-banana-wafers-recipe/', 0.8) ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Banana Chips')::uuid, 'Ethakka Upperi', 'real', 'regional_name', 'Kerala', 'malayalam', 'https://www.vegrecipesofindia.com/banana-chips-or-banana-wafers-recipe/', 0.75) ON CONFLICT (dish_id, synonym) DO NOTHING;
