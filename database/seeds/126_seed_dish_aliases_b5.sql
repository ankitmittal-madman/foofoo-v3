-- Seed: 126_seed_dish_aliases_b5.sql
-- WP-19 Dish Ontology — Batch 5 (~10 dishes: Kerala/Tamil Nadu classics).
-- Same format/rules as prior batches: data_source='real', every row cites source_url + confidence.
-- Safety filter: no alias string may equal another catalogue dish name (checked against catalogue.json before writing).

-- Avial  (https://en.wikipedia.org/wiki/Avial)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Avial')::uuid, 'Aviyal', 'real', 'spelling_variant', 'Kerala', 'malayalam', 'https://en.wikipedia.org/wiki/Avial', 0.9) ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Avial')::uuid, 'Mixed Vegetable Coconut Stew', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Avial', 0.8) ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Appam  (https://en.wikipedia.org/wiki/Appam)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Appam')::uuid, 'Palappam', 'real', 'regional_name', 'Kerala', 'malayalam', 'https://en.wikipedia.org/wiki/Appam', 0.8) ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Appam')::uuid, 'Hoppers', 'real', 'english_gloss', 'Kerala', 'english', 'https://en.wikipedia.org/wiki/Appam', 0.75) ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Puttu  (https://en.wikipedia.org/wiki/Puttu)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Puttu')::uuid, 'Pittu', 'real', 'spelling_variant', 'Kerala, Sri Lanka', 'malayalam', 'https://en.wikipedia.org/wiki/Puttu', 0.8) ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Puttu')::uuid, 'Steamed Rice-Coconut Cylinders', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Puttu', 0.8) ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Kerala Fish Curry  (https://en.wikipedia.org/wiki/Malabar_matthi_curry)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Kerala Fish Curry')::uuid, 'Nadan Meen Curry', 'real', 'regional_name', 'Kerala', 'malayalam', 'https://en.wikipedia.org/wiki/Malabar_matthi_curry', 0.8) ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Kerala Fish Curry')::uuid, 'Meen Vevichathu', 'real', 'regional_name', 'Kerala', 'malayalam', 'https://en.wikipedia.org/wiki/Malabar_matthi_curry', 0.75) ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Parotta (Kerala/Tamil)  (https://en.wikipedia.org/wiki/Parotta)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Parotta (Kerala/Tamil)')::uuid, 'Porotta', 'real', 'spelling_variant', 'Kerala', 'malayalam', 'https://en.wikipedia.org/wiki/Parotta', 0.85) ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Parotta (Kerala/Tamil)')::uuid, 'Malabar Parotta', 'real', 'regional_name', 'Malabar Coast', 'malayalam', 'https://en.wikipedia.org/wiki/Parotta', 0.85) ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Parotta (Kerala/Tamil)')::uuid, 'Barotta', 'real', 'spelling_variant', 'Tamil Nadu', 'tamil', 'https://en.wikipedia.org/wiki/Parotta', 0.75) ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Chicken Chettinad  (https://en.wikipedia.org/wiki/Chicken_Chettinad)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Chicken Chettinad')::uuid, 'Chettinad Chicken Curry', 'real', 'common_name', 'Chettinad, Tamil Nadu', 'tamil', 'https://en.wikipedia.org/wiki/Chicken_Chettinad', 0.8) ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Filter Coffee  (https://en.wikipedia.org/wiki/Indian_filter_coffee)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Filter Coffee')::uuid, 'Filter Kaapi', 'real', 'common_name', 'Tamil Nadu, Karnataka', 'tamil', 'https://www.vegrecipesofindia.com/filter-coffee-recipe/', 0.85) ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Filter Coffee')::uuid, 'Degree Coffee', 'real', 'regional_name', 'Tamil Nadu', 'tamil', 'https://www.vegrecipesofindia.com/filter-coffee-recipe/', 0.7) ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Poriyal  (https://en.wikipedia.org/wiki/Poriyal)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Poriyal')::uuid, 'Palya', 'real', 'regional_name', 'Karnataka', 'kannada', 'https://en.wikipedia.org/wiki/Poriyal', 0.8) ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Poriyal')::uuid, 'Vepudu', 'real', 'regional_name', 'Andhra Pradesh, Telangana', 'telugu', 'https://en.wikipedia.org/wiki/Poriyal', 0.8) ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Poriyal')::uuid, 'Mezhukkupuratti', 'real', 'regional_name', 'Kerala', 'malayalam', 'https://en.wikipedia.org/wiki/Poriyal', 0.8) ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Paniyaram  (https://en.wikipedia.org/wiki/Paddu)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Paniyaram')::uuid, 'Kuzhi Paniyaram', 'real', 'common_name', 'Tamil Nadu', 'tamil', 'https://en.wikipedia.org/wiki/Paddu', 0.85) ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Paniyaram')::uuid, 'Paddu', 'real', 'regional_name', 'Karnataka', 'kannada', 'https://en.wikipedia.org/wiki/Paddu', 0.8) ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Paniyaram')::uuid, 'Ponganalu', 'real', 'regional_name', 'Andhra Pradesh, Telangana', 'telugu', 'https://en.wikipedia.org/wiki/Paddu', 0.75) ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Murukku  (https://en.wikipedia.org/wiki/Murukku)
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Murukku')::uuid, 'Chakralu', 'real', 'regional_name', 'Andhra Pradesh, Telangana', 'telugu', 'https://en.wikipedia.org/wiki/Murukku', 0.75) ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Murukku')::uuid, 'Janthikalu', 'real', 'regional_name', 'Andhra Pradesh', 'telugu', 'https://en.wikipedia.org/wiki/Murukku', 0.7) ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) VALUES (md5('ghar_re.dish:' || 'Murukku')::uuid, 'Spiral Fried Savoury Snack', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Murukku', 0.8) ON CONFLICT (dish_id, synonym) DO NOTHING;
