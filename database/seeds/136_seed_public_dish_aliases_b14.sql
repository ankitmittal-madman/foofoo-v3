-- Seed: 136_seed_public_dish_aliases_b14.sql
-- WP-19 Dish Ontology (public.dish_name_synonyms) — Batch 14.
-- data_source='real', every row cites source_url + confidence. Guarded (SELECT ... FROM public.dishes
-- WHERE name = ...) so a name absent from the live catalogue silently no-ops rather than failing.
-- Safety filter: no alias string may equal another catalogue dish name.

-- Achari Gosht  (https://sarchakra.com/2020/09/13/achari-gosht-mutton-with-pickle-spices/)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Achar Gosht', 'real', 'spelling_variant', 'Punjab', 'punjabi', 'https://sarchakra.com/2020/09/13/achari-gosht-mutton-with-pickle-spices/', 0.8 FROM public.dishes WHERE name = 'Achari Gosht'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Pickled Spice Mutton Curry', 'real', 'english_gloss', NULL, 'english', 'https://sarchakra.com/2020/09/13/achari-gosht-mutton-with-pickle-spices/', 0.8 FROM public.dishes WHERE name = 'Achari Gosht'
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Kuzhambu (Vathal)  (https://en.wikipedia.org/wiki/Kuzhambu)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Vathal Kuzhambu', 'real', 'common_name', 'Tamil Nadu', 'tamil', 'https://en.wikipedia.org/wiki/Kuzhambu', 0.85 FROM public.dishes WHERE name = 'Kuzhambu (Vathal)'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Vatha Kuzhambu', 'real', 'spelling_variant', 'Tamil Nadu', 'tamil', 'https://en.wikipedia.org/wiki/Kuzhambu', 0.8 FROM public.dishes WHERE name = 'Kuzhambu (Vathal)'
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Payasam (Semiya)  (https://www.indianhealthyrecipes.com/semiya-payasam-recipe/)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Seviyan Kheer', 'real', 'regional_name', 'North India', 'hindi', 'https://www.indianhealthyrecipes.com/semiya-payasam-recipe/', 0.8 FROM public.dishes WHERE name = 'Payasam (Semiya)'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Shavige Payasa', 'real', 'regional_name', 'Karnataka', 'kannada', 'https://www.indianhealthyrecipes.com/semiya-payasam-recipe/', 0.75 FROM public.dishes WHERE name = 'Payasam (Semiya)'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Vermicelli Kheer', 'real', 'english_gloss', NULL, 'english', 'https://www.indianhealthyrecipes.com/semiya-payasam-recipe/', 0.8 FROM public.dishes WHERE name = 'Payasam (Semiya)'
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Rasam Vada  (https://thetastesofindia.com/rasam-vada-recipe/)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Rasam Vadai', 'real', 'spelling_variant', 'Tamil Nadu', 'tamil', 'https://thetastesofindia.com/rasam-vada-recipe/', 0.75 FROM public.dishes WHERE name = 'Rasam Vada'
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Chettinad Egg Curry  (https://kitchenofdebjani.com/2020/06/chettinad-egg-curry-chettinad-muttai-masala/)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Chettinad Muttai Masala', 'real', 'common_name', 'Chettinad, Tamil Nadu', 'tamil', 'https://kitchenofdebjani.com/2020/06/chettinad-egg-curry-chettinad-muttai-masala/', 0.8 FROM public.dishes WHERE name = 'Chettinad Egg Curry'
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Fish Molee  (https://en.wikipedia.org/wiki/Fish_moolie)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Meen Moilee', 'real', 'regional_name', 'Kerala', 'malayalam', 'https://en.wikipedia.org/wiki/Fish_moolie', 0.8 FROM public.dishes WHERE name = 'Fish Molee'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Fish Moolie', 'real', 'spelling_variant', NULL, 'english', 'https://en.wikipedia.org/wiki/Fish_moolie', 0.75 FROM public.dishes WHERE name = 'Fish Molee'
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Parippu Curry  (https://www.vegrecipesofindia.com/kerala-parippu-curry-recipe/)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Kerala Lentil Curry', 'real', 'english_gloss', 'Kerala', 'english', 'https://www.vegrecipesofindia.com/kerala-parippu-curry-recipe/', 0.8 FROM public.dishes WHERE name = 'Parippu Curry'
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Erissery  (https://www.vegrecipesofindia.com/pumpkin-erissery-onam-sadya-recipe/)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Mathanga Erissery', 'real', 'common_name', 'Kerala', 'malayalam', 'https://www.vegrecipesofindia.com/pumpkin-erissery-onam-sadya-recipe/', 0.8 FROM public.dishes WHERE name = 'Erissery'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Ellisheri', 'real', 'spelling_variant', 'Kerala', 'malayalam', 'https://www.vegrecipesofindia.com/pumpkin-erissery-onam-sadya-recipe/', 0.7 FROM public.dishes WHERE name = 'Erissery'
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Palada Payasam  (https://en.wikipedia.org/wiki/Ada_pradhaman)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Palada Pradhaman', 'real', 'common_name', 'Kerala', 'malayalam', 'https://en.wikipedia.org/wiki/Ada_pradhaman', 0.85 FROM public.dishes WHERE name = 'Palada Payasam'
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Bagara Khana  (https://en.wikipedia.org/wiki/Bagara_khana)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Bagara Annam', 'real', 'regional_name', 'Hyderabad, Telangana', 'telugu', 'https://en.wikipedia.org/wiki/Bagara_khana', 0.8 FROM public.dishes WHERE name = 'Bagara Khana'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Bagara Chawal', 'real', 'common_name', 'Hyderabad, Telangana', 'urdu', 'https://en.wikipedia.org/wiki/Bagara_khana', 0.75 FROM public.dishes WHERE name = 'Bagara Khana'
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Dum Ka Murgh  (https://www.archanaskitchen.com/recipe/dum-ka-murgh-lagan-ka-murgh-recipe)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Lagan Ka Murgh', 'real', 'regional_name', 'Hyderabad', 'urdu', 'https://www.archanaskitchen.com/recipe/dum-ka-murgh-lagan-ka-murgh-recipe', 0.8 FROM public.dishes WHERE name = 'Dum Ka Murgh'
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Samosa  (https://en.wikipedia.org/wiki/Samosa)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Singara', 'real', 'regional_name', 'West Bengal', 'bengali', 'https://en.wikipedia.org/wiki/Samosa', 0.8 FROM public.dishes WHERE name = 'Samosa'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Samsa', 'real', 'spelling_variant', 'Sindh', 'sindhi', 'https://en.wikipedia.org/wiki/Samosa', 0.7 FROM public.dishes WHERE name = 'Samosa'
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Kathi Roll  (https://en.wikipedia.org/wiki/Kati_roll)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Kati Roll', 'real', 'spelling_variant', 'Kolkata, West Bengal', 'bengali', 'https://en.wikipedia.org/wiki/Kati_roll', 0.85 FROM public.dishes WHERE name = 'Kathi Roll'
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Pani Puri  (https://en.wikipedia.org/wiki/Panipuri)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Golgappa', 'real', 'regional_name', 'North India, Punjab, Delhi', 'hindi', 'https://en.wikipedia.org/wiki/Panipuri', 0.9 FROM public.dishes WHERE name = 'Pani Puri'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Puchka', 'real', 'regional_name', 'West Bengal, Bihar, Jharkhand', 'bengali', 'https://en.wikipedia.org/wiki/Panipuri', 0.9 FROM public.dishes WHERE name = 'Pani Puri'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Gup Chup', 'real', 'regional_name', 'Odisha, Chhattisgarh', 'odia', 'https://en.wikipedia.org/wiki/Panipuri', 0.75 FROM public.dishes WHERE name = 'Pani Puri'
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Jalebi  (https://en.wikipedia.org/wiki/Jalebi)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Jilebi', 'real', 'spelling_variant', NULL, 'hindi', 'https://en.wikipedia.org/wiki/Jalebi', 0.75 FROM public.dishes WHERE name = 'Jalebi'
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Gulab Jamun  (https://en.wikipedia.org/wiki/Gulab_jamun)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Gulab Jaman', 'real', 'spelling_variant', NULL, 'hindi', 'https://en.wikipedia.org/wiki/Gulab_jamun', 0.75 FROM public.dishes WHERE name = 'Gulab Jamun'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Kalo Jam', 'real', 'regional_name', 'West Bengal', 'bengali', 'https://en.wikipedia.org/wiki/Gulab_jamun', 0.7 FROM public.dishes WHERE name = 'Gulab Jamun'
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Gajar Ka Halwa  (https://en.wikipedia.org/wiki/Gajar_ka_halwa)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Gajrela', 'real', 'regional_name', 'Punjab', 'punjabi', 'https://en.wikipedia.org/wiki/Gajar_ka_halwa', 0.85 FROM public.dishes WHERE name = 'Gajar Ka Halwa'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Carrot Halwa', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Gajar_ka_halwa', 0.85 FROM public.dishes WHERE name = 'Gajar Ka Halwa'
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Sannas  (https://en.wikipedia.org/wiki/Sanna_(dish))
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Goan Steamed Rice Cake', 'real', 'english_gloss', 'Goa', 'english', 'https://en.wikipedia.org/wiki/Sanna_(dish)', 0.8 FROM public.dishes WHERE name = 'Sannas'
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Chicken Cafreal  (https://en.wikipedia.org/wiki/Cafreal)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Galinha Cafreal', 'real', 'regional_name', 'Goa', 'konkani', 'https://en.wikipedia.org/wiki/Cafreal', 0.8 FROM public.dishes WHERE name = 'Chicken Cafreal'
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Ros Omelette  (https://en.wikipedia.org/wiki/Ros_omelette)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Ras Omelette', 'real', 'spelling_variant', 'Goa', 'konkani', 'https://en.wikipedia.org/wiki/Ros_omelette', 0.8 FROM public.dishes WHERE name = 'Ros Omelette'
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Gujarati Kadhi  (https://en.wikipedia.org/wiki/Gujarati_kadhi)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Dapka Kadhi', 'real', 'regional_name', 'Gujarat', 'gujarati', 'https://www.theroute2roots.com/gujarati-dapka-kadhi/', 0.7 FROM public.dishes WHERE name = 'Gujarati Kadhi'
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Ukdiche Modak  (https://www.vegrecipesofindia.com/modak-recipe-ukadiche-modak-recipe/)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Ukadiche Modak', 'real', 'spelling_variant', 'Maharashtra', 'marathi', 'https://www.vegrecipesofindia.com/modak-recipe-ukadiche-modak-recipe/', 0.85 FROM public.dishes WHERE name = 'Ukdiche Modak'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Steamed Modak', 'real', 'english_gloss', NULL, 'english', 'https://www.vegrecipesofindia.com/modak-recipe-ukadiche-modak-recipe/', 0.85 FROM public.dishes WHERE name = 'Ukdiche Modak'
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Barfi (Kaju)  (https://en.wikipedia.org/wiki/Barfi)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Kaju Burfi', 'real', 'spelling_variant', NULL, 'hindi', 'https://en.wikipedia.org/wiki/Barfi', 0.8 FROM public.dishes WHERE name = 'Barfi (Kaju)'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Cashew Fudge', 'real', 'english_gloss', NULL, 'english', 'https://en.wikipedia.org/wiki/Barfi', 0.8 FROM public.dishes WHERE name = 'Barfi (Kaju)'
ON CONFLICT (dish_id, synonym) DO NOTHING;
