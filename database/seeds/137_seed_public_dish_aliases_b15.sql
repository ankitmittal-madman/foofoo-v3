-- Seed: 137_seed_public_dish_aliases_b15.sql
-- WP-19 Dish Ontology (public.dish_name_synonyms) — Batch 15.
-- Same rules as prior batches: data_source='real', cited, guarded, safety-filtered.

-- Nahari Kulcha  (https://raheemskulchanahari.com/)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Raheem Ki Nihari', 'real', 'regional_name', 'Lucknow', 'urdu', 'https://raheemskulchanahari.com/', 0.7 FROM public.dishes WHERE name = 'Nahari Kulcha'
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Mughlai Chicken  (https://www.vahrehvah.com/indianfood/mughlai-chicken-curry)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Murgh Mughlai', 'real', 'common_name', NULL, 'urdu', 'https://www.vahrehvah.com/indianfood/mughlai-chicken-curry', 0.7 FROM public.dishes WHERE name = 'Mughlai Chicken'
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Kerala Prawn Curry  (https://www.whiskaffair.com/kerala-prawn-curry-recipe/)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Chemmeen Curry', 'real', 'regional_name', 'Kerala', 'malayalam', 'https://www.whiskaffair.com/kerala-prawn-curry-recipe/', 0.8 FROM public.dishes WHERE name = 'Kerala Prawn Curry'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Malabar Chemmeen Curry', 'real', 'regional_name', 'Malabar, Kerala', 'malayalam', 'https://www.whiskaffair.com/kerala-prawn-curry-recipe/', 0.75 FROM public.dishes WHERE name = 'Kerala Prawn Curry'
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Beef Fry (Kerala)  (https://en.wikipedia.org/wiki/Kerala_beef_fry)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Erachi Ularthiyathu', 'real', 'regional_name', 'Kerala', 'malayalam', 'https://en.wikipedia.org/wiki/Kerala_beef_fry', 0.8 FROM public.dishes WHERE name = 'Beef Fry (Kerala)'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Beef Ularthiyathu', 'real', 'common_name', 'Kerala', 'malayalam', 'https://en.wikipedia.org/wiki/Kerala_beef_fry', 0.8 FROM public.dishes WHERE name = 'Beef Fry (Kerala)'
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Mutta Curry  (https://www.indianhealthyrecipes.com/kerala-egg-curry/)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Nadan Mutta Curry', 'real', 'common_name', 'Kerala', 'malayalam', 'https://www.indianhealthyrecipes.com/kerala-egg-curry/', 0.8 FROM public.dishes WHERE name = 'Mutta Curry'
ON CONFLICT (dish_id, synonym) DO NOTHING;
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Kerala Egg Curry', 'real', 'english_gloss', NULL, 'english', 'https://www.indianhealthyrecipes.com/kerala-egg-curry/', 0.8 FROM public.dishes WHERE name = 'Mutta Curry'
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Usal  (https://en.wikipedia.org/wiki/Usal)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Sprouted Legume Curry', 'real', 'english_gloss', 'Maharashtra', 'english', 'https://en.wikipedia.org/wiki/Usal', 0.75 FROM public.dishes WHERE name = 'Usal'
ON CONFLICT (dish_id, synonym) DO NOTHING;

-- Hakka Noodles  (https://en.wikipedia.org/wiki/Chow_mein)
INSERT INTO public.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence)
SELECT id, 'Chowmein', 'real', 'common_name', NULL, 'hindi', 'https://en.wikipedia.org/wiki/Chow_mein', 0.75 FROM public.dishes WHERE name = 'Hakka Noodles'
ON CONFLICT (dish_id, synonym) DO NOTHING;
