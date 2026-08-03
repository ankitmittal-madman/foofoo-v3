-- Seed: 135_seed_public_dish_aliases_migrated.sql
-- WP-19 Dish Ontology — migrates ALL 13 batches of cited alias research (seeds 122-134,
-- previously targeting the now-dropped ghar_re schema) onto public.dish_name_synonyms
-- (migration 051). Every row here was independently web-researched and cited in an
-- earlier WP-19 batch; this seed only retargets dish_id resolution (by name, against the
-- real public.dishes table) — no alias content, citation, or confidence was changed.
-- Idempotent (ON CONFLICT DO NOTHING) and guarded (WHERE EXISTS on the target dish).

-- Bharli Vangi  (https://smithakalluraya.com/stuffed-brinjal-bharli-vangi-badnekayi-ennegayi-bharwa-baingan-recipe/)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Bharwa Baingan', 'real', 'regional_name', 'North India', 'hindi', 'https://smithakalluraya.com/stuffed-brinjal-bharli-vangi-badnekayi-ennegayi-bharwa-baingan-recipe/', 0.95 FROM public.dishes WHERE name = 'Bharli Vangi'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Ennai Kathrikai', 'real', 'regional_name', 'Tamil Nadu', 'tamil', 'https://smithakalluraya.com/stuffed-brinjal-bharli-vangi-badnekayi-ennegayi-bharwa-baingan-recipe/', 0.9 FROM public.dishes WHERE name = 'Bharli Vangi'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Badanekayi Ennegayi', 'real', 'regional_name', 'Karnataka', 'kannada', 'https://smithakalluraya.com/stuffed-brinjal-bharli-vangi-badnekayi-ennegayi-bharwa-baingan-recipe/', 0.9 FROM public.dishes WHERE name = 'Bharli Vangi'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Stuffed Brinjal', 'real', 'english_gloss', NULL, 'english', 'https://smithakalluraya.com/stuffed-brinjal-bharli-vangi-badnekayi-ennegayi-bharwa-baingan-recipe/', 0.97 FROM public.dishes WHERE name = 'Bharli Vangi'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Poha  (https://en.wikipedia.org/wiki/Poha_(rice))
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Pohe', 'real', 'spelling_variant', 'Maharashtra', 'marathi', 'https://en.wikipedia.org/wiki/Poha_(rice)', 0.9 FROM public.dishes WHERE name = 'Poha'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Pauwa', 'real', 'regional_name', 'North India', 'hindi', 'https://en.wikipedia.org/wiki/Poha_(rice)', 0.85 FROM public.dishes WHERE name = 'Poha'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Aval', 'real', 'regional_name', 'Tamil Nadu, Kerala', 'tamil', 'https://en.wikipedia.org/wiki/Poha_(rice)', 0.95 FROM public.dishes WHERE name = 'Poha'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Avalakki', 'real', 'regional_name', 'Karnataka', 'kannada', 'https://en.wikipedia.org/wiki/Poha_(rice)', 0.95 FROM public.dishes WHERE name = 'Poha'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Atukulu', 'real', 'regional_name', 'Andhra Pradesh, Telangana', 'telugu', 'https://en.wikipedia.org/wiki/Poha_(rice)', 0.95 FROM public.dishes WHERE name = 'Poha'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Chira', 'real', 'regional_name', 'West Bengal', 'bengali', 'https://en.wikipedia.org/wiki/Poha_(rice)', 0.9 FROM public.dishes WHERE name = 'Poha'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Chuda', 'real', 'regional_name', 'Odisha', 'odia', 'https://en.wikipedia.org/wiki/Poha_(rice)', 0.85 FROM public.dishes WHERE name = 'Poha'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Flattened Rice', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Poha_(rice)', 0.97 FROM public.dishes WHERE name = 'Poha'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Baingan Bharta  (https://en.wikipedia.org/wiki/Baingan_bharta)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Baigan Chokha', 'real', 'regional_name', 'Bihar, Uttar Pradesh', 'bhojpuri', 'https://en.wikipedia.org/wiki/Baingan_bharta', 0.85 FROM public.dishes WHERE name = 'Baingan Bharta'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Vangyache Bharit', 'real', 'regional_name', 'Maharashtra', 'marathi', 'https://en.wikipedia.org/wiki/Baingan_bharta', 0.9 FROM public.dishes WHERE name = 'Baingan Bharta'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Begun Pora', 'real', 'regional_name', 'West Bengal', 'bengali', 'https://en.wikipedia.org/wiki/Baingan_bharta', 0.9 FROM public.dishes WHERE name = 'Baingan Bharta'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Ringan no Olo', 'real', 'regional_name', 'Gujarat', 'gujarati', 'https://en.wikipedia.org/wiki/Baingan_bharta', 0.85 FROM public.dishes WHERE name = 'Baingan Bharta'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Smoky Mashed Eggplant', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Baingan_bharta', 0.9 FROM public.dishes WHERE name = 'Baingan Bharta'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Pithla  (https://en.wikipedia.org/wiki/Jhunka)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Pitla', 'real', 'spelling_variant', 'Maharashtra', 'marathi', 'https://en.wikipedia.org/wiki/Jhunka', 0.95 FROM public.dishes WHERE name = 'Pithla'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Zunka', 'real', 'regional_name', 'Maharashtra, North Karnataka', 'marathi', 'https://en.wikipedia.org/wiki/Jhunka', 0.8 FROM public.dishes WHERE name = 'Pithla'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Jhunka', 'real', 'spelling_variant', 'Maharashtra', 'marathi', 'https://en.wikipedia.org/wiki/Jhunka', 0.8 FROM public.dishes WHERE name = 'Pithla'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Besan Curry', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Jhunka', 0.85 FROM public.dishes WHERE name = 'Pithla'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Chole  (https://en.wikipedia.org/wiki/Chana_masala)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Chana Masala', 'real', 'common_name', NULL, 'hindi', 'https://en.wikipedia.org/wiki/Chana_masala', 0.95 FROM public.dishes WHERE name = 'Chole'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Chole Masala', 'real', 'common_name', 'Punjab', 'punjabi', 'https://en.wikipedia.org/wiki/Chana_masala', 0.9 FROM public.dishes WHERE name = 'Chole'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Chholay', 'real', 'spelling_variant', NULL, 'hindi', 'https://en.wikipedia.org/wiki/Chana_masala', 0.85 FROM public.dishes WHERE name = 'Chole'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Kabuli Chana Masala', 'real', 'common_name', NULL, 'hindi', 'https://en.wikipedia.org/wiki/Chana_masala', 0.85 FROM public.dishes WHERE name = 'Chole'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Chickpea Curry', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Chana_masala', 0.95 FROM public.dishes WHERE name = 'Chole'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Puran Poli  (https://en.wikipedia.org/wiki/Puran_poli)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Holige', 'real', 'regional_name', 'North Karnataka', 'kannada', 'https://en.wikipedia.org/wiki/Puran_poli', 0.95 FROM public.dishes WHERE name = 'Puran Poli'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Boli', 'real', 'regional_name', 'Kerala, Tamil Nadu', 'malayalam', 'https://en.wikipedia.org/wiki/Puran_poli', 0.9 FROM public.dishes WHERE name = 'Puran Poli'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Sweet Flatbread', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Puran_poli', 0.9 FROM public.dishes WHERE name = 'Puran Poli'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Dhokla  (https://en.wikipedia.org/wiki/Dhokla)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Khaman', 'real', 'common_name', 'Gujarat', 'gujarati', 'https://en.wikipedia.org/wiki/Dhokla', 0.85 FROM public.dishes WHERE name = 'Dhokla'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Khaman Dhokla', 'real', 'common_name', 'Gujarat', 'gujarati', 'https://en.wikipedia.org/wiki/Dhokla', 0.9 FROM public.dishes WHERE name = 'Dhokla'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Khatta Dhokla', 'real', 'regional_name', 'Gujarat', 'gujarati', 'https://en.wikipedia.org/wiki/Dhokla', 0.85 FROM public.dishes WHERE name = 'Dhokla'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Steamed Gram Flour Cake', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Dhokla', 0.9 FROM public.dishes WHERE name = 'Dhokla'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Undhiyu  (https://en.wikipedia.org/wiki/Undhiyu)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Oondhiya', 'real', 'spelling_variant', 'Gujarat', 'gujarati', 'https://en.wikipedia.org/wiki/Undhiyu', 0.95 FROM public.dishes WHERE name = 'Undhiyu'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Umbadiyu', 'real', 'regional_name', 'South Gujarat', 'gujarati', 'https://en.wikipedia.org/wiki/Undhiyu', 0.85 FROM public.dishes WHERE name = 'Undhiyu'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Surti Undhiyu', 'real', 'regional_name', 'Surat', 'gujarati', 'https://en.wikipedia.org/wiki/Undhiyu', 0.9 FROM public.dishes WHERE name = 'Undhiyu'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Mixed Vegetable Curry', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Undhiyu', 0.85 FROM public.dishes WHERE name = 'Undhiyu'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Butter Chicken  (https://en.wikipedia.org/wiki/Butter_chicken)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Murgh Makhani', 'real', 'common_name', 'Punjab', 'hindi', 'https://en.wikipedia.org/wiki/Butter_chicken', 0.95 FROM public.dishes WHERE name = 'Butter Chicken'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Murgh Makhani Curry', 'real', 'common_name', NULL, 'hindi', 'https://en.wikipedia.org/wiki/Butter_chicken', 0.8 FROM public.dishes WHERE name = 'Butter Chicken'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Dal Makhani  (https://en.wikipedia.org/wiki/Dal_makhani)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Maa Ki Dal', 'real', 'regional_name', 'Punjab', 'punjabi', 'https://en.wikipedia.org/wiki/Dal_makhani', 0.85 FROM public.dishes WHERE name = 'Dal Makhani'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Buttered Black Lentils', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Dal_makhani', 0.85 FROM public.dishes WHERE name = 'Dal Makhani'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Sarson Ka Saag  (https://en.wikipedia.org/wiki/Sarson_da_saag)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Sarson Da Saag', 'real', 'spelling_variant', 'Punjab', 'punjabi', 'https://en.wikipedia.org/wiki/Sarson_da_saag', 0.9 FROM public.dishes WHERE name = 'Sarson Ka Saag'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Mustard Greens Curry', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Sarson_da_saag', 0.85 FROM public.dishes WHERE name = 'Sarson Ka Saag'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Makki Ki Roti  (https://en.wikipedia.org/wiki/Makki_di_roti)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Makki Di Roti', 'real', 'spelling_variant', 'Punjab', 'punjabi', 'https://en.wikipedia.org/wiki/Makki_di_roti', 0.9 FROM public.dishes WHERE name = 'Makki Ki Roti'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Corn Flatbread', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Makki_di_roti', 0.85 FROM public.dishes WHERE name = 'Makki Ki Roti'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Tandoori Chicken  (https://en.wikipedia.org/wiki/Tandoori_chicken)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Murgh Tandoori', 'real', 'common_name', NULL, 'hindi', 'https://en.wikipedia.org/wiki/Tandoori_chicken', 0.9 FROM public.dishes WHERE name = 'Tandoori Chicken'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Paneer Tikka  (https://en.wikipedia.org/wiki/Paneer_tikka)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Grilled Cottage Cheese', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Paneer_tikka', 0.85 FROM public.dishes WHERE name = 'Paneer Tikka'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Amritsari Fish Fry  (https://www.indianhealthyrecipes.com/amritsari-tawa-fish-fry-pan-fried-amritsari-fish/)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Amritsari Macchi', 'real', 'regional_name', 'Amritsar, Punjab', 'punjabi', 'https://www.indianhealthyrecipes.com/amritsari-tawa-fish-fry-pan-fried-amritsari-fish/', 0.8 FROM public.dishes WHERE name = 'Amritsari Fish Fry'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Amritsari Fried Fish', 'real', 'common_name', 'Amritsar, Punjab', 'english', 'https://www.indianhealthyrecipes.com/amritsari-tawa-fish-fry-pan-fried-amritsari-fish/', 0.8 FROM public.dishes WHERE name = 'Amritsari Fish Fry'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Rajma  (https://en.wikipedia.org/wiki/Rajma)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Razma', 'real', 'spelling_variant', NULL, 'hindi', 'https://en.wikipedia.org/wiki/Rajma', 0.8 FROM public.dishes WHERE name = 'Rajma'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Laal Lobia', 'real', 'regional_name', 'North India', 'hindi', 'https://en.wikipedia.org/wiki/Rajma', 0.75 FROM public.dishes WHERE name = 'Rajma'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Kidney Bean Curry', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Rajma', 0.9 FROM public.dishes WHERE name = 'Rajma'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Palak Paneer  (https://en.wikipedia.org/wiki/Palak_paneer)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Palak Chhena', 'real', 'regional_name', 'Odisha', 'odia', 'https://en.wikipedia.org/wiki/Palak_paneer', 0.75 FROM public.dishes WHERE name = 'Palak Paneer'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Spinach Cottage Cheese Curry', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Palak_paneer', 0.9 FROM public.dishes WHERE name = 'Palak Paneer'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Aloo Gobhi  (https://en.wikipedia.org/wiki/Aloo_gobi)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Aloo Gobi', 'real', 'spelling_variant', NULL, 'hindi', 'https://en.wikipedia.org/wiki/Aloo_gobi', 0.9 FROM public.dishes WHERE name = 'Aloo Gobhi'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Potato Cauliflower Curry', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Aloo_gobi', 0.9 FROM public.dishes WHERE name = 'Aloo Gobhi'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Paneer Butter Masala  (https://en.wikipedia.org/wiki/Paneer_makhani)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Paneer Makhani', 'real', 'common_name', NULL, 'hindi', 'https://en.wikipedia.org/wiki/Paneer_makhani', 0.9 FROM public.dishes WHERE name = 'Paneer Butter Masala'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Shahi Paneer  (https://en.wikipedia.org/wiki/Shahi_paneer)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Shahi Panir', 'real', 'spelling_variant', NULL, 'hindi', 'https://en.wikipedia.org/wiki/Shahi_paneer', 0.75 FROM public.dishes WHERE name = 'Shahi Paneer'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Royal Cottage Cheese Curry', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Shahi_paneer', 0.8 FROM public.dishes WHERE name = 'Shahi Paneer'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Chicken Tikka  (https://en.wikipedia.org/wiki/Chicken_tikka)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Murgh Tikka', 'real', 'common_name', NULL, 'hindi', 'https://en.wikipedia.org/wiki/Chicken_tikka', 0.9 FROM public.dishes WHERE name = 'Chicken Tikka'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Seekh Kebab  (https://en.wikipedia.org/wiki/Seekh_kebab)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Sikh Kebab', 'real', 'spelling_variant', NULL, 'hindi', 'https://en.wikipedia.org/wiki/Seekh_kebab', 0.7 FROM public.dishes WHERE name = 'Seekh Kebab'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Skewered Minced Meat Kebab', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Seekh_kebab', 0.85 FROM public.dishes WHERE name = 'Seekh Kebab'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Kadhi Pakora  (https://en.wikipedia.org/wiki/Kadhi_chawal)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Punjabi Kadhi', 'real', 'regional_name', 'Punjab', 'punjabi', 'https://en.wikipedia.org/wiki/Kadhi_chawal', 0.85 FROM public.dishes WHERE name = 'Kadhi Pakora'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Kadhi Badi', 'real', 'regional_name', 'Purvanchal, Bihar', 'bhojpuri', 'https://en.wikipedia.org/wiki/Kadhi_chawal', 0.75 FROM public.dishes WHERE name = 'Kadhi Pakora'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Yogurt Gram Flour Curry with Fritters', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Kadhi_chawal', 0.8 FROM public.dishes WHERE name = 'Kadhi Pakora'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Naan  (https://en.wikipedia.org/wiki/Naan)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Nan', 'real', 'spelling_variant', NULL, 'hindi', 'https://en.wikipedia.org/wiki/Naan', 0.75 FROM public.dishes WHERE name = 'Naan'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Leavened Tandoor Bread', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Naan', 0.85 FROM public.dishes WHERE name = 'Naan'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Lassi (Sweet)  (https://en.wikipedia.org/wiki/Lassi)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Meethi Lassi', 'real', 'common_name', 'Punjab', 'punjabi', 'https://en.wikipedia.org/wiki/Lassi', 0.85 FROM public.dishes WHERE name = 'Lassi (Sweet)'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Sweet Yogurt Drink', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Lassi', 0.85 FROM public.dishes WHERE name = 'Lassi (Sweet)'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Lassi (Salted)  (https://en.wikipedia.org/wiki/Lassi)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Namkeen Lassi', 'real', 'common_name', 'Punjab', 'punjabi', 'https://en.wikipedia.org/wiki/Lassi', 0.85 FROM public.dishes WHERE name = 'Lassi (Salted)'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Salted Yogurt Drink', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Lassi', 0.85 FROM public.dishes WHERE name = 'Lassi (Salted)'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Matar Paneer  (https://en.wikipedia.org/wiki/Matar_paneer)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Mutter Paneer', 'real', 'spelling_variant', NULL, 'hindi', 'https://en.wikipedia.org/wiki/Matar_paneer', 0.85 FROM public.dishes WHERE name = 'Matar Paneer'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Peas and Cottage Cheese Curry', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Matar_paneer', 0.85 FROM public.dishes WHERE name = 'Matar Paneer'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Dal Tadka  (https://en.wikipedia.org/wiki/Dal_tadka)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Dal Fry Tadka', 'real', 'common_name', NULL, 'hindi', 'https://en.wikipedia.org/wiki/Dal_tadka', 0.8 FROM public.dishes WHERE name = 'Dal Tadka'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Tempered Lentil Curry', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Dal_tadka', 0.85 FROM public.dishes WHERE name = 'Dal Tadka'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Bhindi Masala  (https://en.wikipedia.org/wiki/Bhindi_masala)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Bhindi Fry', 'real', 'common_name', NULL, 'hindi', 'https://en.wikipedia.org/wiki/Bhindi_masala', 0.75 FROM public.dishes WHERE name = 'Bhindi Masala'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Spiced Okra', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Bhindi_masala', 0.85 FROM public.dishes WHERE name = 'Bhindi Masala'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Dum Aloo  (https://en.wikipedia.org/wiki/Dum_aloo)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Kashmiri Dum Aloo', 'real', 'regional_name', 'Kashmir', 'kashmiri', 'https://en.wikipedia.org/wiki/Dum_aloo', 0.85 FROM public.dishes WHERE name = 'Dum Aloo'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Slow-Cooked Potato Curry', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Dum_aloo', 0.8 FROM public.dishes WHERE name = 'Dum Aloo'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Jeera Rice  (https://en.wikipedia.org/wiki/Jeera_rice)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Cumin Rice', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Jeera_rice', 0.9 FROM public.dishes WHERE name = 'Jeera Rice'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Pindi Chole  (https://en.wikipedia.org/wiki/Chana_masala)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Pindi Chana', 'real', 'regional_name', 'Rawalpindi/Punjab', 'punjabi', 'https://en.wikipedia.org/wiki/Chana_masala', 0.75 FROM public.dishes WHERE name = 'Pindi Chole'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Keema Matar  (https://en.wikipedia.org/wiki/Keema)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Kheema Matar', 'real', 'spelling_variant', NULL, 'hindi', 'https://en.wikipedia.org/wiki/Keema', 0.75 FROM public.dishes WHERE name = 'Keema Matar'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Minced Meat with Peas', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Keema', 0.8 FROM public.dishes WHERE name = 'Keema Matar'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Phulka  (https://en.wikipedia.org/wiki/Chapati)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Chapati', 'real', 'common_name', NULL, 'hindi', 'https://en.wikipedia.org/wiki/Chapati', 0.8 FROM public.dishes WHERE name = 'Phulka'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Puffed Flatbread', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Chapati', 0.85 FROM public.dishes WHERE name = 'Phulka'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Bhatura  (https://en.wikipedia.org/wiki/Bhatura)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Bhatoora', 'real', 'spelling_variant', NULL, 'hindi', 'https://en.wikipedia.org/wiki/Bhatura', 0.85 FROM public.dishes WHERE name = 'Bhatura'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Batura', 'real', 'spelling_variant', NULL, 'punjabi', 'https://en.wikipedia.org/wiki/Bhatura', 0.8 FROM public.dishes WHERE name = 'Bhatura'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Deep-Fried Leavened Bread', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Bhatura', 0.85 FROM public.dishes WHERE name = 'Bhatura'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Dahi Bhalla  (https://en.wikipedia.org/wiki/Dahi_vada)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Dahi Vada', 'real', 'common_name', NULL, 'hindi', 'https://en.wikipedia.org/wiki/Dahi_vada', 0.85 FROM public.dishes WHERE name = 'Dahi Bhalla'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Doi Bora', 'real', 'regional_name', 'West Bengal', 'bengali', 'https://en.wikipedia.org/wiki/Dahi_vada', 0.8 FROM public.dishes WHERE name = 'Dahi Bhalla'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Lentil Fritters in Yogurt', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Dahi_vada', 0.85 FROM public.dishes WHERE name = 'Dahi Bhalla'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Aloo Tikki  (https://en.wikipedia.org/wiki/Aloo_tikki)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Aloo Ki Tikki', 'real', 'spelling_variant', NULL, 'hindi', 'https://en.wikipedia.org/wiki/Aloo_tikki', 0.85 FROM public.dishes WHERE name = 'Aloo Tikki'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Potato Cutlet', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Aloo_tikki', 0.85 FROM public.dishes WHERE name = 'Aloo Tikki'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Bhel Puri  (https://en.wikipedia.org/wiki/Bhelpuri)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Bhelpuri', 'real', 'spelling_variant', 'Maharashtra', 'marathi', 'https://en.wikipedia.org/wiki/Bhelpuri', 0.9 FROM public.dishes WHERE name = 'Bhel Puri'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Puffed Rice Chaat', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Bhelpuri', 0.85 FROM public.dishes WHERE name = 'Bhel Puri'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Chaat Papdi  (https://en.wikipedia.org/wiki/Papri_chat)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Papri Chaat', 'real', 'spelling_variant', NULL, 'hindi', 'https://en.wikipedia.org/wiki/Papri_chat', 0.9 FROM public.dishes WHERE name = 'Chaat Papdi'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Dahi Papdi Chaat', 'real', 'common_name', NULL, 'hindi', 'https://en.wikipedia.org/wiki/Papri_chat', 0.8 FROM public.dishes WHERE name = 'Chaat Papdi'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Kachori (Dal)  (https://en.wikipedia.org/wiki/Kachori)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Khasta Dal Kachori', 'real', 'common_name', 'Rajasthan', 'hindi', 'https://en.wikipedia.org/wiki/Kachori', 0.8 FROM public.dishes WHERE name = 'Kachori (Dal)'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Lentil-Stuffed Fried Pastry', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Kachori', 0.8 FROM public.dishes WHERE name = 'Kachori (Dal)'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Garlic Naan  (https://www.vegrecipesofindia.com/garlic-naan-recipe/)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Lehsuni Naan', 'real', 'regional_name', NULL, 'hindi', 'https://www.vegrecipesofindia.com/garlic-naan-recipe/', 0.85 FROM public.dishes WHERE name = 'Garlic Naan'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Lasuni Naan', 'real', 'spelling_variant', NULL, 'hindi', 'https://www.vegrecipesofindia.com/garlic-naan-recipe/', 0.75 FROM public.dishes WHERE name = 'Garlic Naan'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Mooli Paratha  (https://en.wikipedia.org/wiki/Paratha)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Mooli Ka Paratha', 'real', 'regional_name', 'Punjab', 'punjabi', 'https://en.wikipedia.org/wiki/Paratha', 0.85 FROM public.dishes WHERE name = 'Mooli Paratha'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Radish Stuffed Flatbread', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Paratha', 0.85 FROM public.dishes WHERE name = 'Mooli Paratha'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Kulcha  (https://en.wikipedia.org/wiki/Kulcha)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Amritsari Kulcha', 'real', 'regional_name', 'Amritsar, Punjab', 'punjabi', 'https://en.wikipedia.org/wiki/Kulcha', 0.8 FROM public.dishes WHERE name = 'Kulcha'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Leavened Stuffed Flatbread', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Kulcha', 0.8 FROM public.dishes WHERE name = 'Kulcha'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Egg Bhurji  (https://en.wikipedia.org/wiki/Egg_bhurji)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Anda Bhurji', 'real', 'common_name', NULL, 'hindi', 'https://en.wikipedia.org/wiki/Egg_bhurji', 0.9 FROM public.dishes WHERE name = 'Egg Bhurji'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Ande Ka Khagina', 'real', 'regional_name', NULL, 'urdu', 'https://en.wikipedia.org/wiki/Egg_bhurji', 0.75 FROM public.dishes WHERE name = 'Egg Bhurji'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Indian Scrambled Eggs', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Egg_bhurji', 0.85 FROM public.dishes WHERE name = 'Egg Bhurji'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Mughlai Paratha  (https://en.wikipedia.org/wiki/Mughlai_paratha)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Mughlai Porota', 'real', 'regional_name', 'West Bengal', 'bengali', 'https://en.wikipedia.org/wiki/Mughlai_paratha', 0.8 FROM public.dishes WHERE name = 'Mughlai Paratha'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Egg-Stuffed Fried Flatbread', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Mughlai_paratha', 0.8 FROM public.dishes WHERE name = 'Mughlai Paratha'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Rumali Roti  (https://en.wikipedia.org/wiki/Rumali_roti)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Manda Roti', 'real', 'regional_name', 'South India', 'kannada', 'https://en.wikipedia.org/wiki/Rumali_roti', 0.75 FROM public.dishes WHERE name = 'Rumali Roti'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Handkerchief Bread', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Rumali_roti', 0.85 FROM public.dishes WHERE name = 'Rumali Roti'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Nihari  (https://en.wikipedia.org/wiki/Nihari)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Nahari', 'real', 'spelling_variant', 'Lucknow, Delhi', 'urdu', 'https://en.wikipedia.org/wiki/Nihari', 0.85 FROM public.dishes WHERE name = 'Nihari'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Slow-Cooked Meat Stew', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Nihari', 0.8 FROM public.dishes WHERE name = 'Nihari'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Mutton Rogan Josh  (https://en.wikipedia.org/wiki/Rogan_josh)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Rogan Ghosht', 'real', 'spelling_variant', 'Kashmir', 'kashmiri', 'https://en.wikipedia.org/wiki/Rogan_josh', 0.8 FROM public.dishes WHERE name = 'Mutton Rogan Josh'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Kashmiri Red Lamb Curry', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Rogan_josh', 0.85 FROM public.dishes WHERE name = 'Mutton Rogan Josh'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Kakori Kebab  (https://www.slurrp.com/article/kakori-kebabs-from-uttar-pradesh-history-and-origin-of-the-iconic-dish-explained-1725611897858)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Kakori Kabab', 'real', 'spelling_variant', 'Kakori, Uttar Pradesh', 'urdu', 'https://www.slurrp.com/article/kakori-kebabs-from-uttar-pradesh-history-and-origin-of-the-iconic-dish-explained-1725611897858', 0.75 FROM public.dishes WHERE name = 'Kakori Kebab'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Shami Kebab  (https://en.wikipedia.org/wiki/Shami_kebab)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Shammi Kabab', 'real', 'spelling_variant', 'Lucknow', 'urdu', 'https://en.wikipedia.org/wiki/Shami_kebab', 0.85 FROM public.dishes WHERE name = 'Shami Kebab'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Pasanda  (https://en.wikipedia.org/wiki/Pasanda)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Murgh Pasanda', 'real', 'common_name', NULL, 'urdu', 'https://en.wikipedia.org/wiki/Pasanda', 0.75 FROM public.dishes WHERE name = 'Pasanda'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Pasanday', 'real', 'spelling_variant', 'Pakistan', 'urdu', 'https://en.wikipedia.org/wiki/Pasanda', 0.75 FROM public.dishes WHERE name = 'Pasanda'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Zarda  (https://en.wikipedia.org/wiki/Zarda_(food))
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Zarda Pulao', 'real', 'common_name', NULL, 'hindi', 'https://en.wikipedia.org/wiki/Zarda_(food)', 0.8 FROM public.dishes WHERE name = 'Zarda'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Sweet Saffron Rice', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Zarda_(food)', 0.85 FROM public.dishes WHERE name = 'Zarda'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Phirni  (https://en.wikipedia.org/wiki/Phirni)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Firni', 'real', 'spelling_variant', NULL, 'hindi', 'https://en.wikipedia.org/wiki/Phirni', 0.9 FROM public.dishes WHERE name = 'Phirni'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Firin', 'real', 'regional_name', 'Kashmir', 'kashmiri', 'https://en.wikipedia.org/wiki/Phirni', 0.75 FROM public.dishes WHERE name = 'Phirni'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Ground Rice Pudding', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Phirni', 0.85 FROM public.dishes WHERE name = 'Phirni'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Haleem  (https://en.wikipedia.org/wiki/Hyderabadi_haleem)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Daleem', 'real', 'regional_name', 'Hyderabad', 'urdu', 'https://en.wikipedia.org/wiki/Hyderabadi_haleem', 0.75 FROM public.dishes WHERE name = 'Haleem'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Wheat and Meat Porridge', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Hyderabadi_haleem', 0.8 FROM public.dishes WHERE name = 'Haleem'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Rezala  (https://en.wikipedia.org/wiki/Chicken_Rezala)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Chicken Rezala', 'real', 'common_name', 'West Bengal', 'bengali', 'https://en.wikipedia.org/wiki/Chicken_Rezala', 0.85 FROM public.dishes WHERE name = 'Rezala'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Rozila', 'real', 'regional_name', 'East Bengal', 'bengali', 'https://en.wikipedia.org/wiki/Chicken_Rezala', 0.7 FROM public.dishes WHERE name = 'Rezala'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Hyderabadi Chicken Biryani  (https://en.wikipedia.org/wiki/Hyderabadi_biryani)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Hyderabadi Murgh Dum Biryani', 'real', 'common_name', 'Hyderabad', 'urdu', 'https://en.wikipedia.org/wiki/Hyderabadi_biryani', 0.8 FROM public.dishes WHERE name = 'Hyderabadi Chicken Biryani'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Hyderabadi Mutton Biryani  (https://en.wikipedia.org/wiki/Hyderabadi_biryani)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Kacchi Gosht Biryani', 'real', 'regional_name', 'Hyderabad', 'urdu', 'https://en.wikipedia.org/wiki/Hyderabadi_biryani', 0.75 FROM public.dishes WHERE name = 'Hyderabadi Mutton Biryani'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Mirchi Ka Salan  (https://en.wikipedia.org/wiki/Mirchi_ka_salan)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Biryani Salan', 'real', 'common_name', 'Hyderabad', 'urdu', 'https://en.wikipedia.org/wiki/Mirchi_ka_salan', 0.75 FROM public.dishes WHERE name = 'Mirchi Ka Salan'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Curried Chilli Peppers', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Mirchi_ka_salan', 0.85 FROM public.dishes WHERE name = 'Mirchi Ka Salan'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Double Ka Meetha  (https://en.wikipedia.org/wiki/Double_ka_meetha)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Hyderabadi Bread Pudding', 'real', 'english_gloss', 'Hyderabad', 'english', 'https://en.wikipedia.org/wiki/Double_ka_meetha', 0.85 FROM public.dishes WHERE name = 'Double Ka Meetha'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Bagara Baingan  (https://en.wikipedia.org/wiki/Baghaar-e-baingan)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Baghare Baingan', 'real', 'spelling_variant', 'Hyderabad', 'urdu', 'https://en.wikipedia.org/wiki/Baghaar-e-baingan', 0.85 FROM public.dishes WHERE name = 'Bagara Baingan'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Bhagaray Baigan', 'real', 'spelling_variant', 'Hyderabad', 'urdu', 'https://en.wikipedia.org/wiki/Baghaar-e-baingan', 0.75 FROM public.dishes WHERE name = 'Bagara Baingan'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Sev Puri  (https://en.wikipedia.org/wiki/Sev_puri)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Sev Batata Puri', 'real', 'regional_name', 'Mumbai, Maharashtra', 'marathi', 'https://en.wikipedia.org/wiki/Sev_puri', 0.8 FROM public.dishes WHERE name = 'Sev Puri'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Baida Roti  (https://www.slurrp.com/article/chicken-baida-roti-crispy-layered-chicken-and-egg-paratha-1661785269423)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Layered Meat and Egg Paratha', 'real', 'english_gloss', 'Mumbai', 'english', 'https://www.slurrp.com/article/chicken-baida-roti-crispy-layered-chicken-and-egg-paratha-1661785269423', 0.75 FROM public.dishes WHERE name = 'Baida Roti'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Warqi Paratha  (https://www.slurrp.com/article/what-makes-the-awadhi-warqi-paratha-so-special-and-what-can-you-pair-with-it-1654589805366)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Warqui Paratha', 'real', 'spelling_variant', 'Awadh', 'urdu', 'https://www.slurrp.com/article/what-makes-the-awadhi-warqi-paratha-so-special-and-what-can-you-pair-with-it-1654589805366', 0.75 FROM public.dishes WHERE name = 'Warqi Paratha'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Layered Flaky Flatbread', 'real', 'english_gloss', NULL, 'english', 'https://www.slurrp.com/article/what-makes-the-awadhi-warqi-paratha-so-special-and-what-can-you-pair-with-it-1654589805366', 0.8 FROM public.dishes WHERE name = 'Warqi Paratha'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Pathar Ka Gosht  (https://en.wikipedia.org/wiki/Pathar-ka-Gosht)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Patthar Ka Gosht', 'real', 'spelling_variant', 'Hyderabad', 'urdu', 'https://en.wikipedia.org/wiki/Pathar-ka-Gosht', 0.85 FROM public.dishes WHERE name = 'Pathar Ka Gosht'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Stone-Grilled Meat', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Pathar-ka-Gosht', 0.85 FROM public.dishes WHERE name = 'Pathar Ka Gosht'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Lukhmi  (https://en.wikipedia.org/wiki/Lukhmi)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Luqmi', 'real', 'spelling_variant', 'Hyderabad', 'urdu', 'https://en.wikipedia.org/wiki/Lukhmi', 0.85 FROM public.dishes WHERE name = 'Lukhmi'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Hyderabadi Square Samosa', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Lukhmi', 0.75 FROM public.dishes WHERE name = 'Lukhmi'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Mutton Korma  (https://foodbound.wordpress.com/2015/09/24/mutton-korma-mutton-qorma-%E0%A4%AE%E0%A4%9F%E0%A4%A8-%E0%A4%95%E0%A5%8B%E0%A4%B0%E0%A4%AE%E0%A4%BE/)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Mutton Qorma', 'real', 'spelling_variant', NULL, 'urdu', 'https://foodbound.wordpress.com/2015/09/24/mutton-korma-mutton-qorma-%E0%A4%AE%E0%A4%9F%E0%A4%A8-%E0%A4%95%E0%A5%8B%E0%A4%B0%E0%A4%AE%E0%A4%BE/', 0.8 FROM public.dishes WHERE name = 'Mutton Korma'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Galouti Kebab  (https://en.wikipedia.org/wiki/Tunde_ke_kabab)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Galawati Kebab', 'real', 'spelling_variant', 'Lucknow', 'urdu', 'https://en.wikipedia.org/wiki/Tunde_ke_kabab', 0.85 FROM public.dishes WHERE name = 'Galouti Kebab'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Melt-in-the-Mouth Kebab', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Tunde_ke_kabab', 0.8 FROM public.dishes WHERE name = 'Galouti Kebab'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Aloo Paratha  (https://en.wikipedia.org/wiki/Paratha)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Potato Stuffed Flatbread', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Paratha', 0.85 FROM public.dishes WHERE name = 'Aloo Paratha'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Chicken Curry  (https://en.wikipedia.org/wiki/Chicken_curry)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Murgh Curry', 'real', 'common_name', NULL, 'hindi', 'https://en.wikipedia.org/wiki/Chicken_curry', 0.75 FROM public.dishes WHERE name = 'Chicken Curry'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Egg Curry  (https://en.wikipedia.org/wiki/Egg_curry)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Anda Curry', 'real', 'common_name', NULL, 'hindi', 'https://en.wikipedia.org/wiki/Egg_curry', 0.8 FROM public.dishes WHERE name = 'Egg Curry'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Kulfi Falooda  (https://en.wikipedia.org/wiki/Falooda)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Falooda Kulfi', 'real', 'common_name', NULL, 'hindi', 'https://en.wikipedia.org/wiki/Falooda', 0.75 FROM public.dishes WHERE name = 'Kulfi Falooda'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Khubani Ka Meetha  (https://en.wikipedia.org/wiki/Khubani_ka_meetha)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Stewed Apricot Dessert', 'real', 'english_gloss', 'Hyderabad', 'english', 'https://en.wikipedia.org/wiki/Khubani_ka_meetha', 0.85 FROM public.dishes WHERE name = 'Khubani Ka Meetha'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Hyderabadi Marag  (https://en.wikipedia.org/wiki/Hyderabadi_marag)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Mutton Marag', 'real', 'common_name', 'Hyderabad', 'urdu', 'https://en.wikipedia.org/wiki/Hyderabadi_marag', 0.8 FROM public.dishes WHERE name = 'Hyderabadi Marag'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Spicy Mutton Bone Soup', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Hyderabadi_marag', 0.8 FROM public.dishes WHERE name = 'Hyderabadi Marag'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Dalcha  (https://en.wikipedia.org/wiki/Dalcha)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Mutton Dalcha', 'real', 'common_name', 'Hyderabad', 'urdu', 'https://en.wikipedia.org/wiki/Dalcha', 0.8 FROM public.dishes WHERE name = 'Dalcha'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Lentil and Meat Stew', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Dalcha', 0.8 FROM public.dishes WHERE name = 'Dalcha'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Osmania Biscuit  (https://en.wikipedia.org/wiki/Osmania_biscuit)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Osmania Biscuits', 'real', 'spelling_variant', 'Hyderabad', 'urdu', 'https://en.wikipedia.org/wiki/Osmania_biscuit', 0.8 FROM public.dishes WHERE name = 'Osmania Biscuit'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Irani Chai  (https://en.wikipedia.org/wiki/Irani_caf%C3%A9)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Hyderabadi Dum Chai', 'real', 'regional_name', 'Hyderabad', 'urdu', 'https://en.wikipedia.org/wiki/Irani_caf%C3%A9', 0.75 FROM public.dishes WHERE name = 'Irani Chai'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Irani Dum Chai', 'real', 'spelling_variant', 'Hyderabad', 'urdu', 'https://en.wikipedia.org/wiki/Irani_caf%C3%A9', 0.75 FROM public.dishes WHERE name = 'Irani Chai'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Tahari  (https://myfoodstory.com/tahari-tehri-recipe/)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Tehri', 'real', 'spelling_variant', 'Uttar Pradesh, Bihar', 'hindi', 'https://myfoodstory.com/tahari-tehri-recipe/', 0.8 FROM public.dishes WHERE name = 'Tahari'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Tehari', 'real', 'spelling_variant', 'Uttar Pradesh, Bihar', 'hindi', 'https://myfoodstory.com/tahari-tehri-recipe/', 0.75 FROM public.dishes WHERE name = 'Tahari'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Masala Dosa  (https://en.wikipedia.org/wiki/Masala_dosa)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Masala Dosai', 'real', 'regional_name', 'Tamil Nadu', 'tamil', 'https://en.wikipedia.org/wiki/Masala_dosa', 0.85 FROM public.dishes WHERE name = 'Masala Dosa'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Masale Dose', 'real', 'regional_name', 'Karnataka', 'kannada', 'https://en.wikipedia.org/wiki/Masala_dosa', 0.85 FROM public.dishes WHERE name = 'Masala Dosa'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Idli  (https://en.wikipedia.org/wiki/Idli)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Idly', 'real', 'spelling_variant', NULL, 'tamil', 'https://en.wikipedia.org/wiki/Idli', 0.85 FROM public.dishes WHERE name = 'Idli'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Steamed Rice Cake', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Idli', 0.85 FROM public.dishes WHERE name = 'Idli'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Sambar  (https://en.wikipedia.org/wiki/Sambar_(dish))
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Sambhar', 'real', 'spelling_variant', NULL, 'hindi', 'https://en.wikipedia.org/wiki/Sambar_(dish)', 0.85 FROM public.dishes WHERE name = 'Sambar'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Lentil and Vegetable Stew', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Sambar_(dish)', 0.8 FROM public.dishes WHERE name = 'Sambar'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Rasam  (https://en.wikipedia.org/wiki/Rasam)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Chaaru', 'real', 'regional_name', 'Andhra Pradesh, Telangana', 'telugu', 'https://en.wikipedia.org/wiki/Rasam', 0.85 FROM public.dishes WHERE name = 'Rasam'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Peppery Tamarind Soup', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Rasam', 0.8 FROM public.dishes WHERE name = 'Rasam'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Coconut Chutney  (https://en.wikipedia.org/wiki/Chutney)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Thengai Chutney', 'real', 'regional_name', 'Tamil Nadu', 'tamil', 'https://en.wikipedia.org/wiki/Chutney', 0.75 FROM public.dishes WHERE name = 'Coconut Chutney'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Medu Vada  (https://en.wikipedia.org/wiki/Vada_(food))
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Uzhunnu Vada', 'real', 'regional_name', 'Kerala', 'malayalam', 'https://en.wikipedia.org/wiki/Vada_(food)', 0.8 FROM public.dishes WHERE name = 'Medu Vada'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Savoury Lentil Doughnut', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Vada_(food)', 0.75 FROM public.dishes WHERE name = 'Medu Vada'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Uttapam  (https://en.wikipedia.org/wiki/Uttapam)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Uthappam', 'real', 'spelling_variant', 'Tamil Nadu', 'tamil', 'https://en.wikipedia.org/wiki/Uttapam', 0.85 FROM public.dishes WHERE name = 'Uttapam'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Thick Savoury Rice Pancake', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Uttapam', 0.8 FROM public.dishes WHERE name = 'Uttapam'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Pongal (Ven)  (https://en.wikipedia.org/wiki/Pongal_(dish))
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Khara Pongal', 'real', 'common_name', 'Karnataka', 'kannada', 'https://en.wikipedia.org/wiki/Pongal_(dish)', 0.85 FROM public.dishes WHERE name = 'Pongal (Ven)'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Ghee Pongal', 'real', 'common_name', 'Tamil Nadu', 'tamil', 'https://en.wikipedia.org/wiki/Pongal_(dish)', 0.8 FROM public.dishes WHERE name = 'Pongal (Ven)'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Pongal (Sweet)  (https://en.wikipedia.org/wiki/Pongal_(dish))
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Sakkarai Pongal', 'real', 'common_name', 'Tamil Nadu', 'tamil', 'https://en.wikipedia.org/wiki/Pongal_(dish)', 0.85 FROM public.dishes WHERE name = 'Pongal (Sweet)'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Curd Rice  (https://en.wikipedia.org/wiki/Curd_rice)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Thayir Sadam', 'real', 'regional_name', 'Tamil Nadu', 'tamil', 'https://en.wikipedia.org/wiki/Curd_rice', 0.85 FROM public.dishes WHERE name = 'Curd Rice'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Mosaru Anna', 'real', 'regional_name', 'Karnataka', 'kannada', 'https://en.wikipedia.org/wiki/Curd_rice', 0.8 FROM public.dishes WHERE name = 'Curd Rice'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Perugu Annam', 'real', 'regional_name', 'Andhra Pradesh, Telangana', 'telugu', 'https://en.wikipedia.org/wiki/Curd_rice', 0.8 FROM public.dishes WHERE name = 'Curd Rice'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Lemon Rice  (https://en.wikipedia.org/wiki/Lemon_rice)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Elumichai Sadam', 'real', 'regional_name', 'Tamil Nadu', 'tamil', 'https://en.wikipedia.org/wiki/Lemon_rice', 0.8 FROM public.dishes WHERE name = 'Lemon Rice'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Avial  (https://en.wikipedia.org/wiki/Avial)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Aviyal', 'real', 'spelling_variant', 'Kerala', 'malayalam', 'https://en.wikipedia.org/wiki/Avial', 0.9 FROM public.dishes WHERE name = 'Avial'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Mixed Vegetable Coconut Stew', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Avial', 0.8 FROM public.dishes WHERE name = 'Avial'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Appam  (https://en.wikipedia.org/wiki/Appam)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Palappam', 'real', 'regional_name', 'Kerala', 'malayalam', 'https://en.wikipedia.org/wiki/Appam', 0.8 FROM public.dishes WHERE name = 'Appam'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Hoppers', 'real', 'english_gloss', 'Kerala', 'english', 'https://en.wikipedia.org/wiki/Appam', 0.75 FROM public.dishes WHERE name = 'Appam'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Puttu  (https://en.wikipedia.org/wiki/Puttu)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Pittu', 'real', 'spelling_variant', 'Kerala, Sri Lanka', 'malayalam', 'https://en.wikipedia.org/wiki/Puttu', 0.8 FROM public.dishes WHERE name = 'Puttu'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Steamed Rice-Coconut Cylinders', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Puttu', 0.8 FROM public.dishes WHERE name = 'Puttu'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Kerala Fish Curry  (https://en.wikipedia.org/wiki/Malabar_matthi_curry)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Nadan Meen Curry', 'real', 'regional_name', 'Kerala', 'malayalam', 'https://en.wikipedia.org/wiki/Malabar_matthi_curry', 0.8 FROM public.dishes WHERE name = 'Kerala Fish Curry'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Meen Vevichathu', 'real', 'regional_name', 'Kerala', 'malayalam', 'https://en.wikipedia.org/wiki/Malabar_matthi_curry', 0.75 FROM public.dishes WHERE name = 'Kerala Fish Curry'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Parotta (Kerala/Tamil)  (https://en.wikipedia.org/wiki/Parotta)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Porotta', 'real', 'spelling_variant', 'Kerala', 'malayalam', 'https://en.wikipedia.org/wiki/Parotta', 0.85 FROM public.dishes WHERE name = 'Parotta (Kerala/Tamil)'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Malabar Parotta', 'real', 'regional_name', 'Malabar Coast', 'malayalam', 'https://en.wikipedia.org/wiki/Parotta', 0.85 FROM public.dishes WHERE name = 'Parotta (Kerala/Tamil)'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Barotta', 'real', 'spelling_variant', 'Tamil Nadu', 'tamil', 'https://en.wikipedia.org/wiki/Parotta', 0.75 FROM public.dishes WHERE name = 'Parotta (Kerala/Tamil)'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Chicken Chettinad  (https://en.wikipedia.org/wiki/Chicken_Chettinad)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Chettinad Chicken Curry', 'real', 'common_name', 'Chettinad, Tamil Nadu', 'tamil', 'https://en.wikipedia.org/wiki/Chicken_Chettinad', 0.8 FROM public.dishes WHERE name = 'Chicken Chettinad'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Filter Coffee  (https://en.wikipedia.org/wiki/Indian_filter_coffee)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Filter Kaapi', 'real', 'common_name', 'Tamil Nadu, Karnataka', 'tamil', 'https://www.vegrecipesofindia.com/filter-coffee-recipe/', 0.85 FROM public.dishes WHERE name = 'Filter Coffee'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Degree Coffee', 'real', 'regional_name', 'Tamil Nadu', 'tamil', 'https://www.vegrecipesofindia.com/filter-coffee-recipe/', 0.7 FROM public.dishes WHERE name = 'Filter Coffee'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Poriyal  (https://en.wikipedia.org/wiki/Poriyal)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Palya', 'real', 'regional_name', 'Karnataka', 'kannada', 'https://en.wikipedia.org/wiki/Poriyal', 0.8 FROM public.dishes WHERE name = 'Poriyal'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Vepudu', 'real', 'regional_name', 'Andhra Pradesh, Telangana', 'telugu', 'https://en.wikipedia.org/wiki/Poriyal', 0.8 FROM public.dishes WHERE name = 'Poriyal'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Mezhukkupuratti', 'real', 'regional_name', 'Kerala', 'malayalam', 'https://en.wikipedia.org/wiki/Poriyal', 0.8 FROM public.dishes WHERE name = 'Poriyal'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Paniyaram  (https://en.wikipedia.org/wiki/Paddu)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Kuzhi Paniyaram', 'real', 'common_name', 'Tamil Nadu', 'tamil', 'https://en.wikipedia.org/wiki/Paddu', 0.85 FROM public.dishes WHERE name = 'Paniyaram'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Paddu', 'real', 'regional_name', 'Karnataka', 'kannada', 'https://en.wikipedia.org/wiki/Paddu', 0.8 FROM public.dishes WHERE name = 'Paniyaram'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Ponganalu', 'real', 'regional_name', 'Andhra Pradesh, Telangana', 'telugu', 'https://en.wikipedia.org/wiki/Paddu', 0.75 FROM public.dishes WHERE name = 'Paniyaram'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Murukku  (https://en.wikipedia.org/wiki/Murukku)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Chakralu', 'real', 'regional_name', 'Andhra Pradesh, Telangana', 'telugu', 'https://en.wikipedia.org/wiki/Murukku', 0.75 FROM public.dishes WHERE name = 'Murukku'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Janthikalu', 'real', 'regional_name', 'Andhra Pradesh', 'telugu', 'https://en.wikipedia.org/wiki/Murukku', 0.7 FROM public.dishes WHERE name = 'Murukku'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Spiral Fried Savoury Snack', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Murukku', 0.8 FROM public.dishes WHERE name = 'Murukku'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Sadya Thali  (https://en.wikipedia.org/wiki/Sadya)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Sadya', 'real', 'common_name', 'Kerala', 'malayalam', 'https://en.wikipedia.org/wiki/Sadya', 0.85 FROM public.dishes WHERE name = 'Sadya Thali'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Onasadya', 'real', 'common_name', 'Kerala', 'malayalam', 'https://en.wikipedia.org/wiki/Sadya', 0.8 FROM public.dishes WHERE name = 'Sadya Thali'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Kerala Banana-Leaf Feast', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Sadya', 0.8 FROM public.dishes WHERE name = 'Sadya Thali'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Malabar Biryani  (https://en.wikipedia.org/wiki/Thalassery_cuisine)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Thalassery Biryani', 'real', 'regional_name', 'Thalassery, Kerala', 'malayalam', 'https://en.wikipedia.org/wiki/Thalassery_cuisine', 0.85 FROM public.dishes WHERE name = 'Malabar Biryani'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Pathiri  (https://en.wikipedia.org/wiki/Pathiri)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Ari Pathil', 'real', 'regional_name', 'Malabar, Kerala', 'malayalam', 'https://en.wikipedia.org/wiki/Pathiri', 0.75 FROM public.dishes WHERE name = 'Pathiri'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Rice Flour Flatbread', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Pathiri', 0.8 FROM public.dishes WHERE name = 'Pathiri'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Unniyappam  (https://en.wikipedia.org/wiki/Unni_appam)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Unni Appam', 'real', 'spelling_variant', 'Kerala', 'malayalam', 'https://en.wikipedia.org/wiki/Unni_appam', 0.85 FROM public.dishes WHERE name = 'Unniyappam'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Karollappam', 'real', 'regional_name', 'Kerala', 'malayalam', 'https://en.wikipedia.org/wiki/Unni_appam', 0.75 FROM public.dishes WHERE name = 'Unniyappam'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Olan  (https://mariasmenu.com/vegetarian/kerala-olan-onam-recipe)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Ash Gourd and Coconut Milk Curry', 'real', 'english_gloss', 'Kerala', 'english', 'https://mariasmenu.com/vegetarian/kerala-olan-onam-recipe', 0.8 FROM public.dishes WHERE name = 'Olan'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Kadala Curry  (https://www.vegrecipesofindia.com/kadala-curry-recipe-kadala-kari/)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Kadala Kari', 'real', 'spelling_variant', 'Kerala', 'malayalam', 'https://www.vegrecipesofindia.com/kadala-curry-recipe-kadala-kari/', 0.8 FROM public.dishes WHERE name = 'Kadala Curry'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Black Chickpea Curry', 'real', 'english_gloss', NULL, 'english', 'https://www.vegrecipesofindia.com/kadala-curry-recipe-kadala-kari/', 0.85 FROM public.dishes WHERE name = 'Kadala Curry'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Sundal  (https://www.vegrecipesofindia.com/chana-sundal/)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Kondakadalai Sundal', 'real', 'common_name', 'Tamil Nadu', 'tamil', 'https://www.vegrecipesofindia.com/chana-sundal/', 0.75 FROM public.dishes WHERE name = 'Sundal'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Tempered Legume Salad', 'real', 'english_gloss', NULL, 'english', 'https://www.vegrecipesofindia.com/chana-sundal/', 0.75 FROM public.dishes WHERE name = 'Sundal'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Kothu Parotta  (https://en.wikipedia.org/wiki/South_Indian_parotta)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Kothu Parota', 'real', 'spelling_variant', 'Tamil Nadu', 'tamil', 'https://en.wikipedia.org/wiki/South_Indian_parotta', 0.75 FROM public.dishes WHERE name = 'Kothu Parotta'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Shredded Flatbread Stir-Fry', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/South_Indian_parotta', 0.75 FROM public.dishes WHERE name = 'Kothu Parotta'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Banana Chips  (https://www.vegrecipesofindia.com/banana-chips-or-banana-wafers-recipe/)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Kaya Upperi', 'real', 'regional_name', 'Kerala', 'malayalam', 'https://www.vegrecipesofindia.com/banana-chips-or-banana-wafers-recipe/', 0.8 FROM public.dishes WHERE name = 'Banana Chips'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Ethakka Upperi', 'real', 'regional_name', 'Kerala', 'malayalam', 'https://www.vegrecipesofindia.com/banana-chips-or-banana-wafers-recipe/', 0.75 FROM public.dishes WHERE name = 'Banana Chips'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Bisi Bele Bath  (https://en.wikipedia.org/wiki/Bisi_Bele_Bath)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Bisi Bele Huli Anna', 'real', 'common_name', 'Karnataka', 'kannada', 'https://en.wikipedia.org/wiki/Bisi_Bele_Bath', 0.8 FROM public.dishes WHERE name = 'Bisi Bele Bath'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Hot Lentil Rice', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Bisi_Bele_Bath', 0.85 FROM public.dishes WHERE name = 'Bisi Bele Bath'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Ragi Mudde  (https://en.wikipedia.org/wiki/Ragi_mudde)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Ragi Sangati', 'real', 'regional_name', 'Rayalaseema, Andhra Pradesh', 'telugu', 'https://en.wikipedia.org/wiki/Ragi_mudde', 0.8 FROM public.dishes WHERE name = 'Ragi Mudde'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Ragi Kali', 'real', 'regional_name', 'Tamil Nadu', 'tamil', 'https://en.wikipedia.org/wiki/Ragi_mudde', 0.75 FROM public.dishes WHERE name = 'Ragi Mudde'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Finger Millet Balls', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Ragi_mudde', 0.8 FROM public.dishes WHERE name = 'Ragi Mudde'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Neer Dosa  (https://en.wikipedia.org/wiki/Neer_dosa)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Neer Dose', 'real', 'spelling_variant', 'Tulu Nadu, Karnataka', 'tulu', 'https://en.wikipedia.org/wiki/Neer_dosa', 0.85 FROM public.dishes WHERE name = 'Neer Dosa'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Panpale', 'real', 'regional_name', 'Konkan', 'konkani', 'https://en.wikipedia.org/wiki/Neer_dosa', 0.7 FROM public.dishes WHERE name = 'Neer Dosa'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Watery Rice Crepe', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Neer_dosa', 0.75 FROM public.dishes WHERE name = 'Neer Dosa'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Jolada Rotti  (https://en.wikipedia.org/wiki/Jolada_rotti)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Jowar Roti', 'real', 'common_name', 'North Karnataka', 'kannada', 'https://en.wikipedia.org/wiki/Jolada_rotti', 0.8 FROM public.dishes WHERE name = 'Jolada Rotti'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Jawarichi Bhakri', 'real', 'regional_name', 'Maharashtra', 'marathi', 'https://en.wikipedia.org/wiki/Jolada_rotti', 0.75 FROM public.dishes WHERE name = 'Jolada Rotti'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Sorghum Flatbread', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Jolada_rotti', 0.8 FROM public.dishes WHERE name = 'Jolada Rotti'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Goli Baje  (https://en.wikipedia.org/wiki/Mangalore_bajji)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Mangalore Bajji', 'real', 'regional_name', 'Mangalore, Karnataka', 'kannada', 'https://en.wikipedia.org/wiki/Mangalore_bajji', 0.85 FROM public.dishes WHERE name = 'Goli Baje'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Golibaje', 'real', 'spelling_variant', 'Tulu Nadu', 'tulu', 'https://en.wikipedia.org/wiki/Mangalore_bajji', 0.8 FROM public.dishes WHERE name = 'Goli Baje'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Tamarind Rice  (https://en.wikipedia.org/wiki/Pulihora)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Puliyodharai', 'real', 'regional_name', 'Tamil Nadu', 'tamil', 'https://en.wikipedia.org/wiki/Pulihora', 0.85 FROM public.dishes WHERE name = 'Tamarind Rice'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Puliyogare', 'real', 'regional_name', 'Karnataka', 'kannada', 'https://en.wikipedia.org/wiki/Pulihora', 0.8 FROM public.dishes WHERE name = 'Tamarind Rice'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Tomato Rice  (https://www.sharmispassions.com/tomato-rice-thakkali-sadam/)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Thakkali Sadam', 'real', 'regional_name', 'Tamil Nadu', 'tamil', 'https://www.sharmispassions.com/tomato-rice-thakkali-sadam/', 0.8 FROM public.dishes WHERE name = 'Tomato Rice'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Kootu  (https://en.wikipedia.org/wiki/Koottu)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Koottu', 'real', 'spelling_variant', 'Tamil Nadu', 'tamil', 'https://en.wikipedia.org/wiki/Koottu', 0.85 FROM public.dishes WHERE name = 'Kootu'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Koottukari', 'real', 'regional_name', 'Kerala', 'malayalam', 'https://en.wikipedia.org/wiki/Koottu', 0.75 FROM public.dishes WHERE name = 'Kootu'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Lentil and Vegetable Medley', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Koottu', 0.75 FROM public.dishes WHERE name = 'Kootu'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Mysore Pak  (https://en.wikipedia.org/wiki/Mysore_pak)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Mysore Bhog', 'real', 'regional_name', 'Mysore, Karnataka', 'kannada', 'https://en.wikipedia.org/wiki/Mysore_pak', 0.7 FROM public.dishes WHERE name = 'Mysore Pak'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Vangi Bath  (https://en.wikipedia.org/wiki/Vangibath)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Vangi Bhath', 'real', 'spelling_variant', 'Karnataka', 'kannada', 'https://en.wikipedia.org/wiki/Vangibath', 0.8 FROM public.dishes WHERE name = 'Vangi Bath'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Brinjal Rice', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Vangibath', 0.85 FROM public.dishes WHERE name = 'Vangi Bath'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Kesari Bath  (https://en.wikipedia.org/wiki/Kesari_bat)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Rava Kesari', 'real', 'regional_name', 'Tamil Nadu, Telangana', 'telugu', 'https://en.wikipedia.org/wiki/Kesari_bat', 0.8 FROM public.dishes WHERE name = 'Kesari Bath'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Sheera', 'real', 'regional_name', 'Maharashtra', 'marathi', 'https://en.wikipedia.org/wiki/Kesari_bat', 0.75 FROM public.dishes WHERE name = 'Kesari Bath'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Akki Rotti  (https://en.wikipedia.org/wiki/Akki_rotti)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Akki Roti', 'real', 'spelling_variant', 'Karnataka', 'kannada', 'https://en.wikipedia.org/wiki/Akki_rotti', 0.85 FROM public.dishes WHERE name = 'Akki Rotti'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Rice Flour Flatbread', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Akki_rotti', 0.8 FROM public.dishes WHERE name = 'Akki Rotti'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Mangalorean Fish Gassi  (https://simpleindianmeals.com/mangalorean-fish-curry-meen-gassi/)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Meen Gassi', 'real', 'regional_name', 'Mangalore, Karnataka', 'tulu', 'https://simpleindianmeals.com/mangalorean-fish-curry-meen-gassi/', 0.8 FROM public.dishes WHERE name = 'Mangalorean Fish Gassi'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Machher Jhol  (https://en.wikipedia.org/wiki/Machher_jhol)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Macher Jhol', 'real', 'spelling_variant', 'West Bengal', 'bengali', 'https://en.wikipedia.org/wiki/Machher_jhol', 0.85 FROM public.dishes WHERE name = 'Machher Jhol'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Bengali Fish Curry', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Machher_jhol', 0.85 FROM public.dishes WHERE name = 'Machher Jhol'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Shorshe Ilish  (https://en.wikipedia.org/wiki/Shorshe_ilish)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Sorshe Ilish', 'real', 'spelling_variant', 'West Bengal', 'bengali', 'https://en.wikipedia.org/wiki/Shorshe_ilish', 0.8 FROM public.dishes WHERE name = 'Shorshe Ilish'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Hilsa in Mustard Gravy', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Shorshe_ilish', 0.85 FROM public.dishes WHERE name = 'Shorshe Ilish'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Aloo Posto  (https://www.vegrecipesofindia.com/aloo-posto-recipe/)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Aloo Poshto', 'real', 'spelling_variant', 'West Bengal', 'bengali', 'https://www.vegrecipesofindia.com/aloo-posto-recipe/', 0.8 FROM public.dishes WHERE name = 'Aloo Posto'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Potato Poppy Seed Curry', 'real', 'english_gloss', NULL, 'english', 'https://www.vegrecipesofindia.com/aloo-posto-recipe/', 0.85 FROM public.dishes WHERE name = 'Aloo Posto'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Luchi  (https://en.wikipedia.org/wiki/Luchi)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Deep-Fried Maida Bread', 'real', 'english_gloss', 'West Bengal', 'english', 'https://en.wikipedia.org/wiki/Luchi', 0.8 FROM public.dishes WHERE name = 'Luchi'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Cholar Dal  (https://holycowvegan.net/cholar-dal/)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Chholar Dal', 'real', 'spelling_variant', 'West Bengal', 'bengali', 'https://holycowvegan.net/cholar-dal/', 0.8 FROM public.dishes WHERE name = 'Cholar Dal'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Bengali Chana Dal with Coconut', 'real', 'english_gloss', NULL, 'english', 'https://holycowvegan.net/cholar-dal/', 0.75 FROM public.dishes WHERE name = 'Cholar Dal'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Kosha Mangsho  (https://www.whiskaffair.com/bengali-kosha-mangsho-recipe/)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Mutton Kosha', 'real', 'common_name', 'West Bengal', 'bengali', 'https://www.whiskaffair.com/bengali-kosha-mangsho-recipe/', 0.8 FROM public.dishes WHERE name = 'Kosha Mangsho'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Slow-Cooked Bengali Mutton Curry', 'real', 'english_gloss', NULL, 'english', 'https://www.whiskaffair.com/bengali-kosha-mangsho-recipe/', 0.8 FROM public.dishes WHERE name = 'Kosha Mangsho'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Mishti Doi  (https://en.wikipedia.org/wiki/Mishti_doi)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Lal Doi', 'real', 'regional_name', 'West Bengal', 'bengali', 'https://en.wikipedia.org/wiki/Mishti_doi', 0.7 FROM public.dishes WHERE name = 'Mishti Doi'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Sweet Fermented Yogurt', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Mishti_doi', 0.85 FROM public.dishes WHERE name = 'Mishti Doi'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Sandesh  (https://en.wikipedia.org/wiki/Sandesh_(confectionery))
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Sondesh', 'real', 'spelling_variant', 'West Bengal', 'bengali', 'https://en.wikipedia.org/wiki/Sandesh_(confectionery)', 0.75 FROM public.dishes WHERE name = 'Sandesh'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Rasgulla  (https://en.wikipedia.org/wiki/Rasgulla)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Rosogolla', 'real', 'regional_name', 'West Bengal', 'bengali', 'https://en.wikipedia.org/wiki/Rasgulla', 0.85 FROM public.dishes WHERE name = 'Rasgulla'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Rasagola', 'real', 'regional_name', 'Odisha', 'odia', 'https://en.wikipedia.org/wiki/Rasgulla', 0.85 FROM public.dishes WHERE name = 'Rasgulla'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Begun Bhaja  (https://www.vegrecipesofindia.com/baingan-fry-baingan-bhaja-eggplant-fries/)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Baingan Bhaja', 'real', 'regional_name', NULL, 'hindi', 'https://www.vegrecipesofindia.com/baingan-fry-baingan-bhaja-eggplant-fries/', 0.75 FROM public.dishes WHERE name = 'Begun Bhaja'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Fried Eggplant Slices', 'real', 'english_gloss', NULL, 'english', 'https://www.vegrecipesofindia.com/baingan-fry-baingan-bhaja-eggplant-fries/', 0.8 FROM public.dishes WHERE name = 'Begun Bhaja'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Chingri Malai Curry  (https://en.wikipedia.org/wiki/Chingri_malai_curry)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Prawn Malai Curry', 'real', 'common_name', 'West Bengal', 'bengali', 'https://en.wikipedia.org/wiki/Chingri_malai_curry', 0.85 FROM public.dishes WHERE name = 'Chingri Malai Curry'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Chingri Macher Malaikari', 'real', 'regional_name', 'West Bengal', 'bengali', 'https://en.wikipedia.org/wiki/Chingri_malai_curry', 0.8 FROM public.dishes WHERE name = 'Chingri Malai Curry'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Doi Maach  (https://foodiesterminal.com/doi-maach-recipe/)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Doi Mach', 'real', 'spelling_variant', 'West Bengal', 'bengali', 'https://foodiesterminal.com/doi-maach-recipe/', 0.8 FROM public.dishes WHERE name = 'Doi Maach'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Fish in Yogurt Curry', 'real', 'english_gloss', NULL, 'english', 'https://foodiesterminal.com/doi-maach-recipe/', 0.85 FROM public.dishes WHERE name = 'Doi Maach'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Shukto  (https://en.wikipedia.org/wiki/Shukto)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Sukto', 'real', 'spelling_variant', 'West Bengal', 'bengali', 'https://en.wikipedia.org/wiki/Shukto', 0.8 FROM public.dishes WHERE name = 'Shukto'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Shuktoni', 'real', 'regional_name', 'Bangladesh', 'bengali', 'https://en.wikipedia.org/wiki/Shukto', 0.75 FROM public.dishes WHERE name = 'Shukto'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Bitter Mixed Vegetable Stew', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Shukto', 0.75 FROM public.dishes WHERE name = 'Shukto'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Pitha (Patishapta)  (https://en.wikipedia.org/wiki/Patisapta)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Patisapta', 'real', 'spelling_variant', 'West Bengal, Bangladesh', 'bengali', 'https://en.wikipedia.org/wiki/Patisapta', 0.8 FROM public.dishes WHERE name = 'Pitha (Patishapta)'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Sweet Rice-Crepe Rolls', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Patisapta', 0.75 FROM public.dishes WHERE name = 'Pitha (Patishapta)'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Kori Rotti  (https://en.wikipedia.org/wiki/Kori_rotti)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Kori Rutti', 'real', 'spelling_variant', 'Tulu Nadu, Karnataka', 'tulu', 'https://en.wikipedia.org/wiki/Kori_rotti', 0.8 FROM public.dishes WHERE name = 'Kori Rotti'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Vada Pav  (https://en.wikipedia.org/wiki/Vada_pav)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Wada Pav', 'real', 'spelling_variant', 'Mumbai, Maharashtra', 'marathi', 'https://en.wikipedia.org/wiki/Vada_pav', 0.8 FROM public.dishes WHERE name = 'Vada Pav'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Indian Burger', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Vada_pav', 0.75 FROM public.dishes WHERE name = 'Vada Pav'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Misal Pav  (https://en.wikipedia.org/wiki/Misal_pav)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Puneri Misal', 'real', 'regional_name', 'Pune, Maharashtra', 'marathi', 'https://en.wikipedia.org/wiki/Misal_pav', 0.75 FROM public.dishes WHERE name = 'Misal Pav'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Nashik Misal', 'real', 'regional_name', 'Nashik, Maharashtra', 'marathi', 'https://en.wikipedia.org/wiki/Misal_pav', 0.7 FROM public.dishes WHERE name = 'Misal Pav'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Thalipeeth  (https://en.wikipedia.org/wiki/Thalipeeth)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Thalipith', 'real', 'spelling_variant', 'Maharashtra', 'marathi', 'https://en.wikipedia.org/wiki/Thalipeeth', 0.85 FROM public.dishes WHERE name = 'Thalipeeth'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Multigrain Savoury Flatbread', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Thalipeeth', 0.75 FROM public.dishes WHERE name = 'Thalipeeth'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Bhakri  (https://en.wikipedia.org/wiki/Bhakri)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Bhakhri', 'real', 'spelling_variant', 'Gujarat', 'gujarati', 'https://en.wikipedia.org/wiki/Bhakri', 0.75 FROM public.dishes WHERE name = 'Bhakri'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Millet Flatbread', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Bhakri', 0.8 FROM public.dishes WHERE name = 'Bhakri'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Sol Kadhi  (https://en.wikipedia.org/wiki/Solkadhi)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Sol Kadi', 'real', 'spelling_variant', 'Konkan, Maharashtra', 'marathi', 'https://en.wikipedia.org/wiki/Solkadhi', 0.8 FROM public.dishes WHERE name = 'Sol Kadhi'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Kokum and Coconut Milk Drink', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Solkadhi', 0.75 FROM public.dishes WHERE name = 'Sol Kadhi'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Modak  (https://en.wikipedia.org/wiki/Modak)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Kozhukattai', 'real', 'regional_name', 'Tamil Nadu', 'tamil', 'https://en.wikipedia.org/wiki/Modak', 0.8 FROM public.dishes WHERE name = 'Modak'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Kadubu', 'real', 'regional_name', 'Karnataka', 'kannada', 'https://en.wikipedia.org/wiki/Modak', 0.75 FROM public.dishes WHERE name = 'Modak'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Shrikhand  (https://en.wikipedia.org/wiki/Shrikhand)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Chakka', 'real', 'regional_name', 'Maharashtra', 'marathi', 'https://en.wikipedia.org/wiki/Shrikhand', 0.75 FROM public.dishes WHERE name = 'Shrikhand'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Matho', 'real', 'regional_name', 'Gujarat', 'gujarati', 'https://en.wikipedia.org/wiki/Shrikhand', 0.7 FROM public.dishes WHERE name = 'Shrikhand'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Strained Sweet Yogurt', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Shrikhand', 0.8 FROM public.dishes WHERE name = 'Shrikhand'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Khandvi  (https://en.wikipedia.org/wiki/Khandvi_(food))
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Patuli', 'real', 'regional_name', 'Gujarat', 'gujarati', 'https://en.wikipedia.org/wiki/Khandvi_(food)', 0.7 FROM public.dishes WHERE name = 'Khandvi'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Suralichi Vadi', 'real', 'regional_name', 'Maharashtra', 'marathi', 'https://en.wikipedia.org/wiki/Khandvi_(food)', 0.75 FROM public.dishes WHERE name = 'Khandvi'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Thepla  (https://en.wikipedia.org/wiki/Thepla)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Methi Thepla', 'real', 'common_name', 'Gujarat', 'gujarati', 'https://en.wikipedia.org/wiki/Thepla', 0.75 FROM public.dishes WHERE name = 'Thepla'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Fafda Jalebi  (https://en.wikipedia.org/wiki/Fafda)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Gujarati Breakfast Combo', 'real', 'english_gloss', 'Gujarat', 'english', 'https://en.wikipedia.org/wiki/Fafda', 0.7 FROM public.dishes WHERE name = 'Fafda Jalebi'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Kombdi Vade (Malvani)  (https://en.wikipedia.org/wiki/Malvani_cuisine)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Malvani Chicken Curry with Fried Bread', 'real', 'english_gloss', 'Konkan, Maharashtra', 'english', 'https://en.wikipedia.org/wiki/Malvani_cuisine', 0.7 FROM public.dishes WHERE name = 'Kombdi Vade (Malvani)'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Ghugni  (https://en.wikipedia.org/wiki/Ghugni)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Ghugni Chaat', 'real', 'common_name', 'West Bengal', 'bengali', 'https://en.wikipedia.org/wiki/Ghugni', 0.8 FROM public.dishes WHERE name = 'Ghugni'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Ghughri', 'real', 'regional_name', 'Bihar', 'bhojpuri', 'https://en.wikipedia.org/wiki/Ghugni', 0.75 FROM public.dishes WHERE name = 'Ghugni'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Guguni', 'real', 'regional_name', 'Odisha', 'odia', 'https://en.wikipedia.org/wiki/Ghugni', 0.75 FROM public.dishes WHERE name = 'Ghugni'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Sabudana Khichdi  (https://en.wikipedia.org/wiki/Sabudana_khichri)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Sabudana Khichri', 'real', 'spelling_variant', 'Maharashtra', 'marathi', 'https://en.wikipedia.org/wiki/Sabudana_khichri', 0.85 FROM public.dishes WHERE name = 'Sabudana Khichdi'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Tapioca Pearl Fasting Pilaf', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Sabudana_khichri', 0.75 FROM public.dishes WHERE name = 'Sabudana Khichdi'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Batata Vada  (https://en.wikipedia.org/wiki/Batata_vada)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Potato Bonda', 'real', 'common_name', NULL, 'hindi', 'https://en.wikipedia.org/wiki/Batata_vada', 0.75 FROM public.dishes WHERE name = 'Batata Vada'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Batate Ambado', 'real', 'regional_name', 'Coastal Karnataka', 'konkani', 'https://en.wikipedia.org/wiki/Batata_vada', 0.7 FROM public.dishes WHERE name = 'Batata Vada'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Amti  (https://www.spiceupthecurry.com/amti-recipe-maharashtrian-amti-dal-recipe/)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Aamti', 'real', 'spelling_variant', 'Maharashtra', 'marathi', 'https://www.spiceupthecurry.com/amti-recipe-maharashtrian-amti-dal-recipe/', 0.75 FROM public.dishes WHERE name = 'Amti'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Sweet-Tangy Toor Dal Curry', 'real', 'english_gloss', NULL, 'english', 'https://www.spiceupthecurry.com/amti-recipe-maharashtrian-amti-dal-recipe/', 0.75 FROM public.dishes WHERE name = 'Amti'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Dal Dhokli  (https://en.wikipedia.org/wiki/Dal_dhokli)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Dal Pithi', 'real', 'regional_name', 'Rajasthan', 'rajasthani', 'https://en.wikipedia.org/wiki/Dal_dhokli', 0.7 FROM public.dishes WHERE name = 'Dal Dhokli'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Wheat Dumplings in Lentil Stew', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Dal_dhokli', 0.75 FROM public.dishes WHERE name = 'Dal Dhokli'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Handvo  (https://en.wikipedia.org/wiki/Handvo)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Ondhwo', 'real', 'regional_name', 'Kathiawad, Gujarat', 'gujarati', 'https://en.wikipedia.org/wiki/Handvo', 0.75 FROM public.dishes WHERE name = 'Handvo'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Savoury Baked Lentil-Rice Cake', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Handvo', 0.8 FROM public.dishes WHERE name = 'Handvo'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Patra  (https://en.wikipedia.org/wiki/Patra)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Patravelia', 'real', 'regional_name', 'Gujarat', 'gujarati', 'https://en.wikipedia.org/wiki/Patra', 0.7 FROM public.dishes WHERE name = 'Patra'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Steamed Colocasia Leaf Rolls', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Patra', 0.8 FROM public.dishes WHERE name = 'Patra'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Basundi  (https://en.wikipedia.org/wiki/Basundi)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Reduced Sweetened Milk', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Basundi', 0.75 FROM public.dishes WHERE name = 'Basundi'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Gathiya  (https://en.wikipedia.org/wiki/Ganthiya)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Ganthiya', 'real', 'spelling_variant', 'Gujarat', 'gujarati', 'https://en.wikipedia.org/wiki/Ganthiya', 0.85 FROM public.dishes WHERE name = 'Gathiya'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Mohanthal  (https://en.wikipedia.org/wiki/Mohanthal)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Mohanthar', 'real', 'spelling_variant', 'Gujarat, Rajasthan', 'gujarati', 'https://en.wikipedia.org/wiki/Mohanthal', 0.7 FROM public.dishes WHERE name = 'Mohanthal'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Gram Flour Fudge', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Mohanthal', 0.75 FROM public.dishes WHERE name = 'Mohanthal'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Khakhra  (https://en.wikipedia.org/wiki/Khakhra)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Crisp Wheat Flatbread Crackers', 'real', 'english_gloss', 'Gujarat', 'english', 'https://en.wikipedia.org/wiki/Khakhra', 0.75 FROM public.dishes WHERE name = 'Khakhra'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Methi Na Gota  (https://www.spiceupthecurry.com/methi-gota-recipe-methi-pakoda/)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Methi Gota', 'real', 'spelling_variant', 'Gujarat', 'gujarati', 'https://www.spiceupthecurry.com/methi-gota-recipe-methi-pakoda/', 0.8 FROM public.dishes WHERE name = 'Methi Na Gota'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Methi Na Bhajiya', 'real', 'regional_name', 'Gujarat', 'gujarati', 'https://www.spiceupthecurry.com/methi-gota-recipe-methi-pakoda/', 0.75 FROM public.dishes WHERE name = 'Methi Na Gota'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Rotla  (https://www.tasteatlas.com/rotla)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Bajra Na Rotla', 'real', 'common_name', 'Saurashtra, Gujarat', 'gujarati', 'https://www.tasteatlas.com/rotla', 0.8 FROM public.dishes WHERE name = 'Rotla'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Vindaloo (Pork)  (https://en.wikipedia.org/wiki/Vindaloo)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Vindalho', 'real', 'spelling_variant', 'Goa', 'konkani', 'https://en.wikipedia.org/wiki/Vindaloo', 0.8 FROM public.dishes WHERE name = 'Vindaloo (Pork)'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Xacuti (Chicken)  (https://en.wikipedia.org/wiki/Xacuti)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Shagoti', 'real', 'regional_name', 'Goa', 'konkani', 'https://en.wikipedia.org/wiki/Xacuti', 0.8 FROM public.dishes WHERE name = 'Xacuti (Chicken)'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Bebinca  (https://en.wikipedia.org/wiki/Bebinca)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Bibik', 'real', 'regional_name', 'Goa', 'konkani', 'https://en.wikipedia.org/wiki/Bebinca', 0.75 FROM public.dishes WHERE name = 'Bebinca'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Goan Layer Cake', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Bebinca', 0.8 FROM public.dishes WHERE name = 'Bebinca'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Sorpotel  (https://en.wikipedia.org/wiki/Sarapatel)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Sarapatel', 'real', 'spelling_variant', 'Goa', 'konkani', 'https://en.wikipedia.org/wiki/Sarapatel', 0.85 FROM public.dishes WHERE name = 'Sorpotel'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Fish Recheado  (https://theyummydelights.com/goan-recheado-fish-fry-recipe/)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Recheado Fish Fry', 'real', 'common_name', 'Goa', 'konkani', 'https://theyummydelights.com/goan-recheado-fish-fry-recipe/', 0.8 FROM public.dishes WHERE name = 'Fish Recheado'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Stuffed Spiced Fried Fish', 'real', 'english_gloss', NULL, 'english', 'https://theyummydelights.com/goan-recheado-fish-fry-recipe/', 0.75 FROM public.dishes WHERE name = 'Fish Recheado'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Prawn Balchao  (https://en.wikipedia.org/wiki/Balch%C3%A3o)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Balichao', 'real', 'spelling_variant', 'Goa', 'konkani', 'https://en.wikipedia.org/wiki/Balch%C3%A3o', 0.75 FROM public.dishes WHERE name = 'Prawn Balchao'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Spicy Vinegar Prawn Pickle', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Balch%C3%A3o', 0.75 FROM public.dishes WHERE name = 'Prawn Balchao'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Pao (Goan Bread)  (https://en.wikipedia.org/wiki/Poee)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Poi', 'real', 'regional_name', 'Goa', 'konkani', 'https://en.wikipedia.org/wiki/Poee', 0.75 FROM public.dishes WHERE name = 'Pao (Goan Bread)'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Goan Fish Curry  (https://www.tableandtraditions.com/recipes/goan-fish-curry)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Xitti Kodi', 'real', 'regional_name', 'Goa', 'konkani', 'https://www.tableandtraditions.com/recipes/goan-fish-curry', 0.8 FROM public.dishes WHERE name = 'Goan Fish Curry'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Khichu  (https://en.wikipedia.org/wiki/Khichu)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Khichiyu', 'real', 'spelling_variant', 'Gujarat', 'gujarati', 'https://en.wikipedia.org/wiki/Khichu', 0.75 FROM public.dishes WHERE name = 'Khichu'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Steamed Spiced Rice Flour Dough', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Khichu', 0.75 FROM public.dishes WHERE name = 'Khichu'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Muthiya  (https://en.wikipedia.org/wiki/Muthia)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Muthia', 'real', 'spelling_variant', 'Gujarat', 'gujarati', 'https://en.wikipedia.org/wiki/Muthia', 0.8 FROM public.dishes WHERE name = 'Muthiya'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Vaataa', 'real', 'regional_name', 'Charotar, Gujarat', 'gujarati', 'https://en.wikipedia.org/wiki/Muthia', 0.7 FROM public.dishes WHERE name = 'Muthiya'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Dal Baati Churma  (https://en.wikipedia.org/wiki/Dal_bati_churma)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Dal Bati Churma', 'real', 'spelling_variant', 'Rajasthan', 'rajasthani', 'https://en.wikipedia.org/wiki/Dal_bati_churma', 0.85 FROM public.dishes WHERE name = 'Dal Baati Churma'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Laal Maas  (https://en.wikipedia.org/wiki/Laal_maas)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Ratto Maas', 'real', 'regional_name', 'Rajasthan', 'rajasthani', 'https://en.wikipedia.org/wiki/Laal_maas', 0.75 FROM public.dishes WHERE name = 'Laal Maas'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Fiery Red Mutton Curry', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Laal_maas', 0.8 FROM public.dishes WHERE name = 'Laal Maas'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Gatte Ki Sabzi  (https://www.vegrecipesofindia.com/gatte-ki-sabji-recipe/)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Gatte Ki Sabji', 'real', 'spelling_variant', 'Rajasthan', 'rajasthani', 'https://www.vegrecipesofindia.com/gatte-ki-sabji-recipe/', 0.8 FROM public.dishes WHERE name = 'Gatte Ki Sabzi'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Gram Flour Dumpling Curry', 'real', 'english_gloss', NULL, 'english', 'https://www.vegrecipesofindia.com/gatte-ki-sabji-recipe/', 0.8 FROM public.dishes WHERE name = 'Gatte Ki Sabzi'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Ker Sangri  (https://medium.com/@narang.kapil/ker-sangri-a-delightful-taste-of-the-rajasthani-desert-9cb7efef024)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Desert Berry and Bean Curry', 'real', 'english_gloss', 'Rajasthan', 'english', 'https://medium.com/@narang.kapil/ker-sangri-a-delightful-taste-of-the-rajasthani-desert-9cb7efef024', 0.75 FROM public.dishes WHERE name = 'Ker Sangri'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Dum Aloo (Kashmiri)  (https://en.wikipedia.org/wiki/Dum_aloo)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Dum Olav', 'real', 'regional_name', 'Kashmir', 'kashmiri', 'https://en.wikipedia.org/wiki/Dum_aloo', 0.8 FROM public.dishes WHERE name = 'Dum Aloo (Kashmiri)'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Yakhni  (https://en.wikipedia.org/wiki/Yakhni)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Kashmiri Yogurt Meat Curry', 'real', 'english_gloss', 'Kashmir', 'english', 'https://en.wikipedia.org/wiki/Yakhni', 0.75 FROM public.dishes WHERE name = 'Yakhni'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Kahwa  (https://en.wikipedia.org/wiki/Kahwah)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Kehwa', 'real', 'spelling_variant', 'Kashmir', 'kashmiri', 'https://en.wikipedia.org/wiki/Kahwah', 0.8 FROM public.dishes WHERE name = 'Kahwa'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Kashmiri Saffron Green Tea', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Kahwah', 0.8 FROM public.dishes WHERE name = 'Kahwa'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Noon Chai  (https://en.wikipedia.org/wiki/Noon_chai)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Nun Chai', 'real', 'spelling_variant', 'Kashmir', 'kashmiri', 'https://en.wikipedia.org/wiki/Noon_chai', 0.8 FROM public.dishes WHERE name = 'Noon Chai'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Gulabi Chai', 'real', 'common_name', 'Kashmir', 'kashmiri', 'https://en.wikipedia.org/wiki/Noon_chai', 0.8 FROM public.dishes WHERE name = 'Noon Chai'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Gushtaba  (https://en.wikipedia.org/wiki/Goshtaab)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'King of Kashmiri Wazwan Meatballs', 'real', 'english_gloss', 'Kashmir', 'english', 'https://en.wikipedia.org/wiki/Goshtaab', 0.7 FROM public.dishes WHERE name = 'Gushtaba'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Haak (Kashmiri Greens)  (https://holycowvegan.net/kashmiri-collard-greens/)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Haakh', 'real', 'spelling_variant', 'Kashmir', 'kashmiri', 'https://holycowvegan.net/kashmiri-collard-greens/', 0.75 FROM public.dishes WHERE name = 'Haak (Kashmiri Greens)'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Gongura Chicken  (https://www.indianhealthyrecipes.com/gongura-chicken-curry-chicken-with-red-sorrel-leaves/)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Ambadi Chicken', 'real', 'regional_name', 'Andhra Pradesh, Telangana', 'telugu', 'https://www.indianhealthyrecipes.com/gongura-chicken-curry-chicken-with-red-sorrel-leaves/', 0.7 FROM public.dishes WHERE name = 'Gongura Chicken'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Sorrel Leaf Chicken Curry', 'real', 'english_gloss', NULL, 'english', 'https://www.indianhealthyrecipes.com/gongura-chicken-curry-chicken-with-red-sorrel-leaves/', 0.8 FROM public.dishes WHERE name = 'Gongura Chicken'
ON CONFLICT (dish_id, synonym) DO NOTHING;
-- Gutti Vankaya  (https://www.vegrecipesofindia.com/gutti-vankaya-kura-recipe/)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Gutti Vankaya Kura', 'real', 'common_name', 'Rayalaseema, Andhra Pradesh', 'telugu', 'https://www.vegrecipesofindia.com/gutti-vankaya-kura-recipe/', 0.8 FROM public.dishes WHERE name = 'Gutti Vankaya'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Stuffed Baby Eggplant Curry', 'real', 'english_gloss', NULL, 'english', 'https://www.vegrecipesofindia.com/gutti-vankaya-kura-recipe/', 0.8 FROM public.dishes WHERE name = 'Gutti Vankaya'
ON CONFLICT (dish_id, synonym) DO NOTHING;
