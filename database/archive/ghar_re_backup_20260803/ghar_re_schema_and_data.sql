--
-- PostgreSQL database dump
--

\restrict zeRfS9TWhqOqTIeIon9Ijh2FrSaq6P3l8tiNqcvRvkom2m7YPdTgTZPDSmUyv1e

-- Dumped from database version 17.6
-- Dumped by pg_dump version 17.10 (Ubuntu 17.10-1.pgdg24.04+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: ghar_re; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA ghar_re;


--
-- Name: SCHEMA ghar_re; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON SCHEMA ghar_re IS 'Ghar RE v1.0 rebuild (isolated). Governs the rebuilt recommendation engine only; the retired persona/cohort/weight-ladder RE in re_engine/public is untouched.';


--
-- Name: data_source_kind; Type: TYPE; Schema: ghar_re; Owner: -
--

CREATE TYPE ghar_re.data_source_kind AS ENUM (
    'real',
    'ai_generated',
    'stub'
);


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: allergen_hidden_derivatives; Type: TABLE; Schema: ghar_re; Owner: -
--

CREATE TABLE ghar_re.allergen_hidden_derivatives (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    surface_token text NOT NULL,
    hidden_allergen text NOT NULL,
    note text,
    is_active boolean DEFAULT false NOT NULL,
    data_source ghar_re.data_source_kind NOT NULL
);


--
-- Name: comfort_hero_map; Type: TABLE; Schema: ghar_re; Owner: -
--

CREATE TABLE ghar_re.comfort_hero_map (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    zone text NOT NULL,
    weather_type text NOT NULL,
    dish_name text NOT NULL,
    dish_id uuid,
    verified_flag boolean NOT NULL,
    data_source ghar_re.data_source_kind NOT NULL,
    CONSTRAINT comfort_hero_map_weather_type_check CHECK ((weather_type = ANY (ARRAY['rain'::text, 'summer'::text, 'winter'::text])))
);


--
-- Name: community_priors; Type: TABLE; Schema: ghar_re; Owner: -
--

CREATE TABLE ghar_re.community_priors (
    state text NOT NULL,
    zone text NOT NULL,
    diet_lean text NOT NULL,
    default_non_veg_cadence text NOT NULL,
    data_source ghar_re.data_source_kind NOT NULL
);


--
-- Name: cuisine_groups; Type: TABLE; Schema: ghar_re; Owner: -
--

CREATE TABLE ghar_re.cuisine_groups (
    name text NOT NULL,
    display_name text NOT NULL,
    display_order integer,
    description text,
    data_source ghar_re.data_source_kind NOT NULL
);


--
-- Name: cuisines; Type: TABLE; Schema: ghar_re; Owner: -
--

CREATE TABLE ghar_re.cuisines (
    name text NOT NULL,
    display_name text NOT NULL,
    cuisine_group text NOT NULL,
    parent_cuisine text,
    state_origin text,
    tier text,
    is_user_facing boolean DEFAULT true NOT NULL,
    data_source ghar_re.data_source_kind NOT NULL
);


--
-- Name: dish_combo_items; Type: TABLE; Schema: ghar_re; Owner: -
--

CREATE TABLE ghar_re.dish_combo_items (
    combo_id uuid NOT NULL,
    dish_id uuid,
    dish_name text NOT NULL,
    role text,
    data_source ghar_re.data_source_kind NOT NULL
);


--
-- Name: dish_combos; Type: TABLE; Schema: ghar_re; Owner: -
--

CREATE TABLE ghar_re.dish_combos (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    name text NOT NULL,
    combo_type text,
    description text,
    data_source ghar_re.data_source_kind NOT NULL
);


--
-- Name: dish_ingredients; Type: TABLE; Schema: ghar_re; Owner: -
--

CREATE TABLE ghar_re.dish_ingredients (
    dish_id uuid NOT NULL,
    ingredient_name text NOT NULL,
    is_main_ingredient boolean DEFAULT false NOT NULL,
    data_source ghar_re.data_source_kind NOT NULL
);


--
-- Name: dish_macro; Type: TABLE; Schema: ghar_re; Owner: -
--

CREATE TABLE ghar_re.dish_macro (
    dish_id uuid NOT NULL,
    calories integer,
    protein_g real,
    fibre_g real,
    fat_g real,
    carbs_g real,
    sugar_g real,
    sodium_mg real,
    data_source ghar_re.data_source_kind NOT NULL
);


--
-- Name: dish_name_synonyms; Type: TABLE; Schema: ghar_re; Owner: -
--

CREATE TABLE ghar_re.dish_name_synonyms (
    dish_id uuid NOT NULL,
    synonym text NOT NULL,
    data_source ghar_re.data_source_kind NOT NULL,
    alias_type text,
    region text,
    language text,
    source_url text,
    confidence real,
    CONSTRAINT dish_name_synonyms_alias_type_check CHECK ((alias_type = ANY (ARRAY['regional_name'::text, 'common_name'::text, 'transliteration'::text, 'english_gloss'::text, 'spelling_variant'::text]))),
    CONSTRAINT dish_name_synonyms_confidence_check CHECK (((confidence >= (0)::double precision) AND (confidence <= (1)::double precision)))
);


--
-- Name: COLUMN dish_name_synonyms.alias_type; Type: COMMENT; Schema: ghar_re; Owner: -
--

COMMENT ON COLUMN ghar_re.dish_name_synonyms.alias_type IS 'WP-19: kind of alias — regional_name/common_name/transliteration/english_gloss/spelling_variant';


--
-- Name: COLUMN dish_name_synonyms.region; Type: COMMENT; Schema: ghar_re; Owner: -
--

COMMENT ON COLUMN ghar_re.dish_name_synonyms.region IS 'WP-19: region/state where this alias is the used name; NULL = pan-Indian';


--
-- Name: COLUMN dish_name_synonyms.language; Type: COMMENT; Schema: ghar_re; Owner: -
--

COMMENT ON COLUMN ghar_re.dish_name_synonyms.language IS 'WP-19: language of the alias, lowercase';


--
-- Name: COLUMN dish_name_synonyms.source_url; Type: COMMENT; Schema: ghar_re; Owner: -
--

COMMENT ON COLUMN ghar_re.dish_name_synonyms.source_url IS 'WP-19: citation URL for a web-researched (data_source=real) alias';


--
-- Name: COLUMN dish_name_synonyms.confidence; Type: COMMENT; Schema: ghar_re; Owner: -
--

COMMENT ON COLUMN ghar_re.dish_name_synonyms.confidence IS 'WP-19: researcher/model confidence in [0,1] that this alias names the same dish';


--
-- Name: dish_variants; Type: TABLE; Schema: ghar_re; Owner: -
--

CREATE TABLE ghar_re.dish_variants (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    from_dish_id uuid NOT NULL,
    to_dish_id uuid NOT NULL,
    variant_type text NOT NULL,
    note text,
    data_source ghar_re.data_source_kind NOT NULL,
    CONSTRAINT dish_variants_variant_type_check CHECK ((variant_type = ANY (ARRAY['veg_swap'::text, 'jain'::text, 'vegan'::text, 'no_onion_garlic'::text, 'farali'::text, 'lighter'::text, 'protein_swap'::text])))
);


--
-- Name: dishes; Type: TABLE; Schema: ghar_re; Owner: -
--

CREATE TABLE ghar_re.dishes (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    name text NOT NULL,
    short_description text,
    alternate_names text[],
    cuisine text,
    spice_level integer,
    sweetness integer,
    heaviness integer,
    difficulty text,
    prep_mins integer,
    cook_mins integer,
    total_mins integer,
    calories integer,
    serving_size text,
    meal_type text[] NOT NULL,
    dish_category text[],
    cooking_method text[],
    primary_taste text[],
    texture text[],
    richness text[],
    mouthfeel text[],
    aroma_profile text[],
    fermentation text,
    serving_temp text,
    weather_affinity text[],
    diet text NOT NULL,
    hero_role text NOT NULL,
    jain_compatible text NOT NULL,
    scope_tier text NOT NULL,
    farali_compatible boolean DEFAULT false NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    data_source ghar_re.data_source_kind NOT NULL,
    CONSTRAINT dishes_diet_check CHECK ((diet = ANY (ARRAY['veg'::text, 'egg'::text, 'non_veg'::text]))),
    CONSTRAINT dishes_difficulty_check CHECK ((difficulty = ANY (ARRAY['easy'::text, 'medium'::text, 'hard'::text]))),
    CONSTRAINT dishes_fermentation_check CHECK ((fermentation = ANY (ARRAY['none'::text, 'light'::text, 'medium'::text, 'heavy'::text]))),
    CONSTRAINT dishes_heaviness_check CHECK (((heaviness >= 1) AND (heaviness <= 3))),
    CONSTRAINT dishes_hero_role_check CHECK ((hero_role = ANY (ARRAY['liquid'::text, 'dry'::text, 'single'::text, 'standalone'::text, 'support'::text, 'snack'::text, 'accompaniment'::text]))),
    CONSTRAINT dishes_jain_compatible_check CHECK ((jain_compatible = ANY (ARRAY['Y'::text, 'N'::text]))),
    CONSTRAINT dishes_scope_tier_check CHECK ((scope_tier = ANY (ARRAY['indian_core'::text, 'indianised_daily'::text, 'experimental'::text]))),
    CONSTRAINT dishes_serving_temp_check CHECK ((serving_temp = ANY (ARRAY['hot'::text, 'warm'::text, 'room_temp'::text, 'chilled'::text, 'frozen'::text]))),
    CONSTRAINT dishes_spice_level_check CHECK (((spice_level >= 0) AND (spice_level <= 4))),
    CONSTRAINT dishes_sweetness_check CHECK (((sweetness >= 0) AND (sweetness <= 3)))
);


--
-- Name: feedback_event; Type: TABLE; Schema: ghar_re; Owner: -
--

CREATE TABLE ghar_re.feedback_event (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    household_id uuid NOT NULL,
    dish_id uuid,
    event_type text NOT NULL,
    plate_ref uuid,
    slot text,
    detail jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    data_source ghar_re.data_source_kind NOT NULL,
    CONSTRAINT feedback_event_event_type_check CHECK ((event_type = ANY (ARRAY['accept'::text, 'edit'::text, 'swap'::text, 'like'::text, 'dislike'::text, 'shown_not_tapped'::text])))
);


--
-- Name: household_context; Type: TABLE; Schema: ghar_re; Owner: -
--

CREATE TABLE ghar_re.household_context (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    household_id uuid NOT NULL,
    session_id text,
    slot text,
    season text,
    weekday text,
    weather_condition text,
    temp_c real,
    is_raining boolean,
    humidity real,
    active_modes text[],
    calorie_target integer,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    data_source ghar_re.data_source_kind NOT NULL,
    CONSTRAINT household_context_season_check CHECK ((season = ANY (ARRAY['summer'::text, 'monsoon'::text, 'winter'::text, 'transitional'::text, 'post_monsoon'::text]))),
    CONSTRAINT household_context_slot_check CHECK ((slot = ANY (ARRAY['breakfast'::text, 'lunch'::text, 'dinner'::text, 'snacks'::text])))
);


--
-- Name: household_modes; Type: TABLE; Schema: ghar_re; Owner: -
--

CREATE TABLE ghar_re.household_modes (
    household_id uuid NOT NULL,
    mode text NOT NULL,
    is_on boolean DEFAULT false NOT NULL,
    params jsonb,
    data_source ghar_re.data_source_kind NOT NULL,
    CONSTRAINT household_modes_mode_check CHECK ((mode = ANY (ARRAY['fasting'::text, 'festival'::text, 'veg_egg'::text])))
);


--
-- Name: household_profile; Type: TABLE; Schema: ghar_re; Owner: -
--

CREATE TABLE ghar_re.household_profile (
    household_id uuid NOT NULL,
    field_name text NOT NULL,
    value jsonb NOT NULL,
    confidence real DEFAULT 1.0 NOT NULL,
    source text NOT NULL,
    kind text NOT NULL,
    stability text NOT NULL,
    version text NOT NULL,
    computed_at timestamp with time zone DEFAULT now() NOT NULL,
    data_source ghar_re.data_source_kind NOT NULL,
    CONSTRAINT household_profile_confidence_check CHECK (((confidence >= (0)::double precision) AND (confidence <= (1)::double precision))),
    CONSTRAINT household_profile_kind_check CHECK ((kind = ANY (ARRAY['explicit'::text, 'derived'::text, 'learned'::text]))),
    CONSTRAINT household_profile_stability_check CHECK ((stability = ANY (ARRAY['stable'::text, 'dynamic'::text])))
);


--
-- Name: households; Type: TABLE; Schema: ghar_re; Owner: -
--

CREATE TABLE ghar_re.households (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    label text,
    q1_household_type text,
    q2_working_professionals integer,
    q3_home_state text,
    q4_current_city text,
    q5_diet text,
    q6_nonveg_types text[],
    q7_veg_days text[],
    q8_is_jain boolean DEFAULT false NOT NULL,
    q9_allergies text[],
    q10_allergy_other text,
    q11_conditions text[],
    q12_member_ages jsonb,
    q13_who_cooks text,
    q14_eat_out_per_week integer,
    q15_objective text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    data_source ghar_re.data_source_kind NOT NULL
);


--
-- Name: ingredient_aliases; Type: TABLE; Schema: ghar_re; Owner: -
--

CREATE TABLE ghar_re.ingredient_aliases (
    alias text NOT NULL,
    canonical_ingredient text NOT NULL,
    data_source ghar_re.data_source_kind NOT NULL
);


--
-- Name: ingredient_normalization_map; Type: TABLE; Schema: ghar_re; Owner: -
--

CREATE TABLE ghar_re.ingredient_normalization_map (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    surface_token text NOT NULL,
    canonical text,
    norm_type text NOT NULL,
    expansion text[],
    note text,
    data_source ghar_re.data_source_kind NOT NULL,
    CONSTRAINT ingredient_normalization_map_norm_type_check CHECK ((norm_type = ANY (ARRAY['alias'::text, 'synonym'::text, 'variety'::text, 'form'::text, 'equivalence'::text, 'expansion'::text])))
);


--
-- Name: ingredients; Type: TABLE; Schema: ghar_re; Owner: -
--

CREATE TABLE ghar_re.ingredients (
    name text NOT NULL,
    display_name text,
    category text,
    diet_type text,
    is_allergen boolean DEFAULT false NOT NULL,
    allergen_type text,
    is_jain_compatible boolean,
    is_vegan boolean,
    data_source ghar_re.data_source_kind NOT NULL,
    CONSTRAINT ingredients_diet_type_check CHECK ((diet_type = ANY (ARRAY['veg'::text, 'egg'::text, 'non_veg'::text])))
);


--
-- Name: negative_priors; Type: TABLE; Schema: ghar_re; Owner: -
--

CREATE TABLE ghar_re.negative_priors (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    discouragement text NOT NULL,
    context text,
    action text,
    in_spine boolean NOT NULL,
    enforced_via text,
    status text NOT NULL,
    data_source ghar_re.data_source_kind NOT NULL,
    CONSTRAINT negative_priors_status_check CHECK ((status = ANY (ARRAY['active'::text, 'deferred_v2'::text])))
);


--
-- Name: prior_zone_slot_season; Type: TABLE; Schema: ghar_re; Owner: -
--

CREATE TABLE ghar_re.prior_zone_slot_season (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    zone text NOT NULL,
    slot text NOT NULL,
    season text,
    match_kind text NOT NULL,
    match_value text NOT NULL,
    boost real NOT NULL,
    usage_tags text[],
    data_source ghar_re.data_source_kind NOT NULL,
    CONSTRAINT prior_zone_slot_season_match_kind_check CHECK ((match_kind = ANY (ARRAY['dish_name'::text, 'dish_category'::text, 'cuisine'::text, 'hero_role'::text, 'structure'::text, 'attribute'::text]))),
    CONSTRAINT prior_zone_slot_season_slot_check CHECK ((slot = ANY (ARRAY['breakfast'::text, 'lunch'::text, 'dinner'::text])))
);


--
-- Name: recommendation_event; Type: TABLE; Schema: ghar_re; Owner: -
--

CREATE TABLE ghar_re.recommendation_event (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    household_id uuid NOT NULL,
    session_id text,
    slot text,
    rank integer,
    plate jsonb NOT NULL,
    plate_score real,
    spine_version text,
    kb_version text,
    config_version text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    data_source ghar_re.data_source_kind NOT NULL
);


--
-- Name: region_food_affinity; Type: TABLE; Schema: ghar_re; Owner: -
--

CREATE TABLE ghar_re.region_food_affinity (
    state_code text NOT NULL,
    dish_name text NOT NULL,
    affinity_score real NOT NULL,
    source text,
    data_source ghar_re.data_source_kind NOT NULL,
    CONSTRAINT region_food_affinity_affinity_score_check CHECK (((affinity_score >= (0)::double precision) AND (affinity_score <= (1)::double precision)))
);


--
-- Name: sig_score_bands; Type: TABLE; Schema: ghar_re; Owner: -
--

CREATE TABLE ghar_re.sig_score_bands (
    score real NOT NULL,
    band_name text NOT NULL,
    definition text NOT NULL,
    data_source ghar_re.data_source_kind NOT NULL
);


--
-- Name: sig_scores; Type: TABLE; Schema: ghar_re; Owner: -
--

CREATE TABLE ghar_re.sig_scores (
    dish_id uuid NOT NULL,
    sig_score real NOT NULL,
    band text NOT NULL,
    evidence_confidence text,
    coverage_confidence text,
    owner text,
    method text,
    version text,
    data_source ghar_re.data_source_kind NOT NULL,
    CONSTRAINT sig_scores_sig_score_check CHECK (((sig_score >= (0)::double precision) AND (sig_score <= (1)::double precision)))
);


--
-- Name: tags; Type: TABLE; Schema: ghar_re; Owner: -
--

CREATE TABLE ghar_re.tags (
    category text NOT NULL,
    value text NOT NULL,
    display_value text,
    tier text,
    is_user_facing boolean DEFAULT true NOT NULL,
    data_source ghar_re.data_source_kind NOT NULL
);


--
-- Name: zone_map; Type: TABLE; Schema: ghar_re; Owner: -
--

CREATE TABLE ghar_re.zone_map (
    cuisine_group text NOT NULL,
    zone text NOT NULL,
    dish_count integer,
    data_source ghar_re.data_source_kind NOT NULL
);


--
-- Data for Name: allergen_hidden_derivatives; Type: TABLE DATA; Schema: ghar_re; Owner: -
--

COPY ghar_re.allergen_hidden_derivatives (id, surface_token, hidden_allergen, note, is_active, data_source) FROM stdin;
\.


--
-- Data for Name: comfort_hero_map; Type: TABLE DATA; Schema: ghar_re; Owner: -
--

COPY ghar_re.comfort_hero_map (id, zone, weather_type, dish_name, dish_id, verified_flag, data_source) FROM stdin;
90c5d526-3132-4b26-be4d-56e9c4189d66	North	rain	Samosa	\N	t	real
38513a97-877e-4f08-9957-201b8a21070e	North	rain	Kadhi-Pakora	\N	t	real
591a4db0-781c-44b9-ae50-19db303d4b9a	North	rain	Aloo Paratha	\N	t	real
926eab96-4914-4f96-bc12-89199237379b	West-MH	rain	Vada Pav	\N	t	real
2bb068e8-fed0-4b89-8b59-b82afdacc1f1	West-MH	rain	Pithla-Bhakri	\N	t	real
70cbc28c-ead0-4ee7-b087-5fd29800bc18	West-MH	rain	Sol Kadhi	\N	t	real
211c9eeb-cc51-4ba7-9eb2-c734c2bc39c7	West-GJ	rain	Bhajiya	\N	f	stub
92a6ae59-8dac-4f0d-aacb-7abfccd0d20c	West-GJ	rain	Dal-Dhokli	\N	f	stub
41ac2c0f-b5f2-42f1-8784-4d92063a259c	West-GJ	rain	Methi Na Gota	\N	f	stub
080f63af-a17d-47c6-b4ea-6ebd8007941b	South-TN	rain	Bajji/Bonda	\N	f	stub
565c711d-049f-467f-8669-135e2061cbf3	South-KL	rain	Parippu Vada	\N	f	stub
da44a7f1-fb92-4444-a140-676aa9874817	South-KL	rain	Pazham Pori	\N	f	stub
d44c9c4b-0346-4ee2-ae5d-aaff4282ba5c	East-WB	rain	Telebhaja	\N	f	stub
63b31c9e-1488-43bd-a01d-dc1af9f9dc1d	Central	rain	Poha	\N	t	real
afd447ee-d637-4ba7-8950-58276c664e40	NE	rain	Thukpa	\N	f	stub
3bb66b6d-23d6-421a-b4e7-4e97b3910cac	NE	rain	Momos	\N	f	stub
eabbc5df-60ff-4a46-b227-68632cec50d3	North	summer	Sattu	\N	t	real
4224c1b8-a3af-40a1-b68f-a7076296fdad	North	summer	Chaas	\N	f	stub
79e8b083-49a9-48bb-8cd3-204da7bf7372	North	summer	Aam Panna	\N	f	stub
8820048a-15e9-486b-a5ba-f43249df61ac	West	summer	Sol Kadhi	\N	t	real
42a11b20-16a9-41c0-8d87-b2c7220efeac	West	summer	Aamras	\N	f	stub
9c84b1f3-8e62-4e6a-952f-875856e99a43	South	summer	Neer Mor	\N	f	stub
0f82b7cd-b4a5-43d5-87c1-88269252ab05	East	summer	Panta Bhat	\N	f	stub
3031f535-3287-48d5-a279-294eb749561d	North	winter	Nihari	\N	t	real
43234c7f-688e-4836-9e8a-5b06e3bd7ed9	North	winter	Gajar Halwa	\N	f	stub
4625938b-cacf-4d44-a06e-fa13489e1b43	West-MH	winter	Bajra Bhakri	\N	f	stub
5cfddf2a-f483-4a4b-9eeb-7439e9802b7c	South	winter	Ven Pongal	\N	t	real
7f1cc27e-5d95-40b5-8ee2-bd779a7d05db	East	winter	Pithe	\N	f	stub
3cf0e144-0106-4620-ae0d-4b19d1656bc4	North	rain	Pakora	7ddaee12-915c-aada-6040-b9e733e98c7a	t	real
587e5690-0cc5-4cf0-8b39-10b1d356866f	Central	rain	Pakora	7ddaee12-915c-aada-6040-b9e733e98c7a	t	real
e12c5eaa-1691-4e7b-b73f-ea0e695e4361	North	winter	Sarson Ka Saag	62aa4772-38c3-9d41-51fd-37c7a4b17389	t	real
34465e5b-704c-4800-ade9-3705f3050650	West-MH	rain	Kanda Bhaji	580cc1e5-9c77-2cf7-0496-f105cc76a523	t	real
34f46df3-21f1-4dae-8671-1c091b8eee7b	South	summer	Curd Rice	bbad43bb-dd04-e820-b203-aa51852902ad	t	real
2fde8ce2-e7f0-4706-a417-aa6b469abc08	South	winter	Rasam	bad73b19-60e3-326a-4690-541ad275312f	t	real
747d148f-ff0e-478e-bdca-cbfee57bb0e4	South-TN	rain	Rasam-Rice	bad73b19-60e3-326a-4690-541ad275312f	t	real
955f1a45-4bec-4109-9a05-f82623117cb3	South-TN	rain	Medu Vada	fca7677f-b221-f385-c558-943784f2eaf9	t	real
e1546e73-716e-4da0-a9db-54a65f99c3da	East-WB	rain	Khichuri	fae1b50d-81ef-dde6-1b3e-e491fc2bb00c	t	real
4025803f-afa3-4ba3-a273-7f0ee97a0fdf	West-GJ	winter	Undhiyu	927cc5ba-b06a-26c7-ce46-170e4d92b57b	t	real
c3a3ca5e-90c1-4e13-b485-48f3b840e786	West-MH	winter	Pithla	ac4ffde2-19b1-aa9d-b9e6-d478546701ea	t	real
\.


--
-- Data for Name: community_priors; Type: TABLE DATA; Schema: ghar_re; Owner: -
--

COPY ghar_re.community_priors (state, zone, diet_lean, default_non_veg_cadence, data_source) FROM stdin;
Rajasthan	West	strongly_veg	rare	real
Gujarat	West	strongly_veg	rare	real
Haryana	North	strongly_veg	weekend	real
Punjab	North	veg_leaning	weekend	real
Madhya Pradesh	Central	strongly_veg	weekend	real
Uttar Pradesh	North	mixed	weekend	real
Maharashtra	West	mixed	weekend	real
Karnataka	South	mixed	frequent	real
Delhi	North	mixed	weekend	real
West Bengal	East	strongly_non_veg	frequent	real
Kerala	South	strongly_non_veg	daily	real
Telangana	South	strongly_non_veg	frequent	real
Andhra Pradesh	South	strongly_non_veg	frequent	real
Tamil Nadu	South	strongly_non_veg	frequent	real
Odisha	East	strongly_non_veg	frequent	real
Bihar	East	strongly_non_veg	frequent	real
Jharkhand	East	strongly_non_veg	frequent	real
Goa	West	strongly_non_veg	frequent	real
Assam	Northeast	strongly_non_veg	daily	real
\.


--
-- Data for Name: cuisine_groups; Type: TABLE DATA; Schema: ghar_re; Owner: -
--

COPY ghar_re.cuisine_groups (name, display_name, display_order, description, data_source) FROM stdin;
north_indian	North Indian	1	Punjabi, Kashmiri, Rajasthani, Bihari & more	real
south_indian	South Indian	2	Tamil, Kerala, Andhra, Karnataka & more	real
east_indian	East Indian	3	Bengali, Odia, Assamese & more	real
west_indian	West Indian	4	Maharashtrian, Gujarati, Goan, Parsi & more	real
central_indian	Central Indian	5	Madhya Pradesh, Indori, Chhattisgarhi	real
northeast_indian	Northeast Indian	6	Naga, Manipuri, Sikkimese & more	real
mughlai_nawabi	Mughlai / Nawabi	7	Biryanis, kebabs, kormas — Mughal & Nawabi traditions	real
street_food	Street Food / Chaat	8	Chaat, vada pav, pav bhaji, kathi rolls & more	real
chinese_asian	Chinese / Indo-Chinese	9	Hakka noodles, manchurian, momos, fried rice	real
continental	Continental	10	Grilled meats, soups, salads, sandwiches	real
italian	Italian	11	Pasta, pizza, risotto	real
american	American	12	Burgers, fries, BBQ, pancakes	real
mediterranean	Mediterranean	13	Grain bowls, grilled meats, olive oil based	real
anglo_indian	Anglo Indian	14	Railway curry, mulligatawny, jhal frezi — colonial fusion	real
thai	Thai	15	Pad thai, curries, tom yum, som tam	real
japanese	Japanese	16	Sushi, ramen, tempura, teriyaki	real
korean	Korean	17	Kimchi, bibimbap, Korean fried chicken	real
middle_eastern	Middle Eastern	18	Hummus, falafel, shawarma, kebab platters	real
bhutanese	Bhutanese	19	Ema datshi, phaksha paa. Chilli + cheese focused.	real
burmese	Burmese	20	Mohinga, khow suey, tea leaf salad. SE Asian + Indian fusion.	real
mexican	Mexican	21	Tacos, burritos, quesadillas. Corn + beans + chilli.	real
vietnamese	Vietnamese	22	Pho, banh mi, spring rolls. Fresh herbs + light broths.	real
\.


--
-- Data for Name: cuisines; Type: TABLE DATA; Schema: ghar_re; Owner: -
--

COPY ghar_re.cuisines (name, display_name, cuisine_group, parent_cuisine, state_origin, tier, is_user_facing, data_source) FROM stdin;
punjabi	Punjabi	north_indian	\N	Punjab	tier_1	t	real
delhi	Delhi	north_indian	\N	Delhi	tier_1	t	real
up	UP (General)	north_indian	\N	Uttar Pradesh	tier_1	t	real
tamil	Tamil	south_indian	\N	Tamil Nadu	tier_1	t	real
chettinad	Chettinad	south_indian	tamil	Tamil Nadu	tier_2	t	real
udupi	Udupi	south_indian	\N	Karnataka	tier_1	t	real
maharashtrian	Maharashtrian	west_indian	\N	Maharashtra	tier_1	t	real
gujarati	Gujarati	west_indian	\N	Gujarat	tier_1	t	real
bengali	Bengali	east_indian	\N	West Bengal	tier_1	t	real
mughlai	Mughlai	mughlai_nawabi	\N	Delhi	tier_1	t	real
\.


--
-- Data for Name: dish_combo_items; Type: TABLE DATA; Schema: ghar_re; Owner: -
--

COPY ghar_re.dish_combo_items (combo_id, dish_id, dish_name, role, data_source) FROM stdin;
\.


--
-- Data for Name: dish_combos; Type: TABLE DATA; Schema: ghar_re; Owner: -
--

COPY ghar_re.dish_combos (id, name, combo_type, description, data_source) FROM stdin;
\.


--
-- Data for Name: dish_ingredients; Type: TABLE DATA; Schema: ghar_re; Owner: -
--

COPY ghar_re.dish_ingredients (dish_id, ingredient_name, is_main_ingredient, data_source) FROM stdin;
7ddaee12-915c-aada-6040-b9e733e98c7a	onion	t	ai_generated
7ddaee12-915c-aada-6040-b9e733e98c7a	gram_flour	t	ai_generated
7ddaee12-915c-aada-6040-b9e733e98c7a	green_chilli	f	ai_generated
7ddaee12-915c-aada-6040-b9e733e98c7a	turmeric	f	ai_generated
7ddaee12-915c-aada-6040-b9e733e98c7a	ajwain	f	ai_generated
7ddaee12-915c-aada-6040-b9e733e98c7a	salt	f	ai_generated
7ddaee12-915c-aada-6040-b9e733e98c7a	vegetable_oil	f	ai_generated
62aa4772-38c3-9d41-51fd-37c7a4b17389	mustard_greens	t	ai_generated
62aa4772-38c3-9d41-51fd-37c7a4b17389	spinach	t	ai_generated
62aa4772-38c3-9d41-51fd-37c7a4b17389	ginger	f	ai_generated
62aa4772-38c3-9d41-51fd-37c7a4b17389	garlic	f	ai_generated
62aa4772-38c3-9d41-51fd-37c7a4b17389	green_chilli	f	ai_generated
62aa4772-38c3-9d41-51fd-37c7a4b17389	cornmeal	f	ai_generated
62aa4772-38c3-9d41-51fd-37c7a4b17389	ghee	f	ai_generated
62aa4772-38c3-9d41-51fd-37c7a4b17389	salt	f	ai_generated
5929056d-ea5b-6189-492e-4095f29290db	toor_dal	t	ai_generated
5929056d-ea5b-6189-492e-4095f29290db	onion	f	ai_generated
5929056d-ea5b-6189-492e-4095f29290db	tomato	f	ai_generated
5929056d-ea5b-6189-492e-4095f29290db	garlic	f	ai_generated
5929056d-ea5b-6189-492e-4095f29290db	cumin_seeds	f	ai_generated
5929056d-ea5b-6189-492e-4095f29290db	turmeric	f	ai_generated
5929056d-ea5b-6189-492e-4095f29290db	ghee	f	ai_generated
5929056d-ea5b-6189-492e-4095f29290db	salt	f	ai_generated
8f1dc758-de7c-33f6-b88a-1c72ee6d84da	kidney_beans	t	ai_generated
8f1dc758-de7c-33f6-b88a-1c72ee6d84da	onion	f	ai_generated
8f1dc758-de7c-33f6-b88a-1c72ee6d84da	tomato	f	ai_generated
8f1dc758-de7c-33f6-b88a-1c72ee6d84da	ginger	f	ai_generated
8f1dc758-de7c-33f6-b88a-1c72ee6d84da	garlic	f	ai_generated
8f1dc758-de7c-33f6-b88a-1c72ee6d84da	garam_masala	f	ai_generated
8f1dc758-de7c-33f6-b88a-1c72ee6d84da	red_chilli_powder	f	ai_generated
8f1dc758-de7c-33f6-b88a-1c72ee6d84da	salt	f	ai_generated
7d016491-175e-918c-94f2-d1580d56c402	potato	t	ai_generated
7d016491-175e-918c-94f2-d1580d56c402	cauliflower	t	ai_generated
7d016491-175e-918c-94f2-d1580d56c402	onion	f	ai_generated
7d016491-175e-918c-94f2-d1580d56c402	tomato	f	ai_generated
7d016491-175e-918c-94f2-d1580d56c402	turmeric	f	ai_generated
7d016491-175e-918c-94f2-d1580d56c402	cumin_seeds	f	ai_generated
7d016491-175e-918c-94f2-d1580d56c402	green_chilli	f	ai_generated
7d016491-175e-918c-94f2-d1580d56c402	salt	f	ai_generated
2e99df2f-27ee-9e0c-641d-be09e46e7f20	curd	t	ai_generated
2e99df2f-27ee-9e0c-641d-be09e46e7f20	gram_flour	t	ai_generated
2e99df2f-27ee-9e0c-641d-be09e46e7f20	onion	f	ai_generated
2e99df2f-27ee-9e0c-641d-be09e46e7f20	garlic	f	ai_generated
2e99df2f-27ee-9e0c-641d-be09e46e7f20	turmeric	f	ai_generated
2e99df2f-27ee-9e0c-641d-be09e46e7f20	fenugreek_seeds	f	ai_generated
2e99df2f-27ee-9e0c-641d-be09e46e7f20	dry_red_chilli	f	ai_generated
2e99df2f-27ee-9e0c-641d-be09e46e7f20	salt	f	ai_generated
0b5f372a-c53f-61a5-8c2a-637b131c1a4a	chickpeas	t	ai_generated
0b5f372a-c53f-61a5-8c2a-637b131c1a4a	onion	f	ai_generated
0b5f372a-c53f-61a5-8c2a-637b131c1a4a	tomato	f	ai_generated
0b5f372a-c53f-61a5-8c2a-637b131c1a4a	ginger	f	ai_generated
0b5f372a-c53f-61a5-8c2a-637b131c1a4a	garlic	f	ai_generated
0b5f372a-c53f-61a5-8c2a-637b131c1a4a	chaat_masala	f	ai_generated
0b5f372a-c53f-61a5-8c2a-637b131c1a4a	amchur	f	ai_generated
0b5f372a-c53f-61a5-8c2a-637b131c1a4a	salt	f	ai_generated
c93598a1-1298-c8a2-d5c9-aeb9a151266d	paneer	t	ai_generated
c93598a1-1298-c8a2-d5c9-aeb9a151266d	tomato	t	ai_generated
c93598a1-1298-c8a2-d5c9-aeb9a151266d	butter	f	ai_generated
c93598a1-1298-c8a2-d5c9-aeb9a151266d	cream	f	ai_generated
c93598a1-1298-c8a2-d5c9-aeb9a151266d	onion	f	ai_generated
c93598a1-1298-c8a2-d5c9-aeb9a151266d	garlic	f	ai_generated
c93598a1-1298-c8a2-d5c9-aeb9a151266d	garam_masala	f	ai_generated
c93598a1-1298-c8a2-d5c9-aeb9a151266d	kasuri_methi	f	ai_generated
c93598a1-1298-c8a2-d5c9-aeb9a151266d	salt	f	ai_generated
c334b845-1c6d-d749-b7e7-7083f55ff821	rice_basmati	t	ai_generated
c334b845-1c6d-d749-b7e7-7083f55ff821	carrot	f	ai_generated
c334b845-1c6d-d749-b7e7-7083f55ff821	green_peas	f	ai_generated
c334b845-1c6d-d749-b7e7-7083f55ff821	potato	f	ai_generated
c334b845-1c6d-d749-b7e7-7083f55ff821	onion	f	ai_generated
c334b845-1c6d-d749-b7e7-7083f55ff821	garlic	f	ai_generated
c334b845-1c6d-d749-b7e7-7083f55ff821	garam_masala	f	ai_generated
c334b845-1c6d-d749-b7e7-7083f55ff821	saffron	f	ai_generated
c334b845-1c6d-d749-b7e7-7083f55ff821	ghee	f	ai_generated
c334b845-1c6d-d749-b7e7-7083f55ff821	salt	f	ai_generated
6df98a0f-c6c3-116f-d2ff-40d4a9ae48a0	rice_regular	t	ai_generated
6df98a0f-c6c3-116f-d2ff-40d4a9ae48a0	moong_dal	t	ai_generated
6df98a0f-c6c3-116f-d2ff-40d4a9ae48a0	cumin_seeds	f	ai_generated
6df98a0f-c6c3-116f-d2ff-40d4a9ae48a0	turmeric	f	ai_generated
6df98a0f-c6c3-116f-d2ff-40d4a9ae48a0	ghee	f	ai_generated
6df98a0f-c6c3-116f-d2ff-40d4a9ae48a0	salt	f	ai_generated
3c13fb4c-7e8b-ea6a-bb0b-679aad62d613	rice_regular	t	ai_generated
3c13fb4c-7e8b-ea6a-bb0b-679aad62d613	urad_dal	t	ai_generated
3c13fb4c-7e8b-ea6a-bb0b-679aad62d613	potato	t	ai_generated
3c13fb4c-7e8b-ea6a-bb0b-679aad62d613	onion	f	ai_generated
3c13fb4c-7e8b-ea6a-bb0b-679aad62d613	mustard_seeds	f	ai_generated
3c13fb4c-7e8b-ea6a-bb0b-679aad62d613	curry_powder	f	ai_generated
3c13fb4c-7e8b-ea6a-bb0b-679aad62d613	turmeric	f	ai_generated
3c13fb4c-7e8b-ea6a-bb0b-679aad62d613	salt	f	ai_generated
1aab33f2-b951-00f3-fa1b-f2037d547c16	rice_regular	t	ai_generated
1aab33f2-b951-00f3-fa1b-f2037d547c16	urad_dal	t	ai_generated
1aab33f2-b951-00f3-fa1b-f2037d547c16	idli_rava	f	ai_generated
1aab33f2-b951-00f3-fa1b-f2037d547c16	salt	f	ai_generated
6695b916-d65f-9424-8536-30f5dd274941	toor_dal	t	ai_generated
6695b916-d65f-9424-8536-30f5dd274941	drumstick	f	ai_generated
6695b916-d65f-9424-8536-30f5dd274941	onion	f	ai_generated
6695b916-d65f-9424-8536-30f5dd274941	tomato	f	ai_generated
6695b916-d65f-9424-8536-30f5dd274941	tamarind	f	ai_generated
6695b916-d65f-9424-8536-30f5dd274941	sambar_powder	f	ai_generated
6695b916-d65f-9424-8536-30f5dd274941	mustard_seeds	f	ai_generated
6695b916-d65f-9424-8536-30f5dd274941	salt	f	ai_generated
bad73b19-60e3-326a-4690-541ad275312f	tamarind	t	ai_generated
bad73b19-60e3-326a-4690-541ad275312f	tomato	f	ai_generated
bad73b19-60e3-326a-4690-541ad275312f	toor_dal	f	ai_generated
bad73b19-60e3-326a-4690-541ad275312f	black_pepper	f	ai_generated
bad73b19-60e3-326a-4690-541ad275312f	garlic	f	ai_generated
bad73b19-60e3-326a-4690-541ad275312f	curry_powder	f	ai_generated
bad73b19-60e3-326a-4690-541ad275312f	mustard_seeds	f	ai_generated
bad73b19-60e3-326a-4690-541ad275312f	salt	f	ai_generated
bbad43bb-dd04-e820-b203-aa51852902ad	rice_regular	t	ai_generated
bbad43bb-dd04-e820-b203-aa51852902ad	curd	t	ai_generated
bbad43bb-dd04-e820-b203-aa51852902ad	mustard_seeds	f	ai_generated
bbad43bb-dd04-e820-b203-aa51852902ad	green_chilli	f	ai_generated
bbad43bb-dd04-e820-b203-aa51852902ad	curry_powder	f	ai_generated
bbad43bb-dd04-e820-b203-aa51852902ad	salt	f	ai_generated
fca7677f-b221-f385-c558-943784f2eaf9	urad_dal	t	ai_generated
fca7677f-b221-f385-c558-943784f2eaf9	black_pepper	f	ai_generated
fca7677f-b221-f385-c558-943784f2eaf9	green_chilli	f	ai_generated
fca7677f-b221-f385-c558-943784f2eaf9	curry_powder	f	ai_generated
fca7677f-b221-f385-c558-943784f2eaf9	ginger	f	ai_generated
fca7677f-b221-f385-c558-943784f2eaf9	salt	f	ai_generated
fca7677f-b221-f385-c558-943784f2eaf9	vegetable_oil	f	ai_generated
a8573473-a3cc-39a2-e3e0-656a7615e598	chicken	t	ai_generated
a8573473-a3cc-39a2-e3e0-656a7615e598	onion	f	ai_generated
a8573473-a3cc-39a2-e3e0-656a7615e598	tomato	f	ai_generated
a8573473-a3cc-39a2-e3e0-656a7615e598	garlic	f	ai_generated
a8573473-a3cc-39a2-e3e0-656a7615e598	black_pepper	f	ai_generated
a8573473-a3cc-39a2-e3e0-656a7615e598	dry_red_chilli	f	ai_generated
a8573473-a3cc-39a2-e3e0-656a7615e598	coconut_fresh	f	ai_generated
a8573473-a3cc-39a2-e3e0-656a7615e598	garam_masala	f	ai_generated
a8573473-a3cc-39a2-e3e0-656a7615e598	salt	f	ai_generated
580cc1e5-9c77-2cf7-0496-f105cc76a523	onion	t	ai_generated
580cc1e5-9c77-2cf7-0496-f105cc76a523	gram_flour	t	ai_generated
580cc1e5-9c77-2cf7-0496-f105cc76a523	green_chilli	f	ai_generated
580cc1e5-9c77-2cf7-0496-f105cc76a523	coriander_powder	f	ai_generated
580cc1e5-9c77-2cf7-0496-f105cc76a523	turmeric	f	ai_generated
580cc1e5-9c77-2cf7-0496-f105cc76a523	salt	f	ai_generated
580cc1e5-9c77-2cf7-0496-f105cc76a523	vegetable_oil	f	ai_generated
ac4ffde2-19b1-aa9d-b9e6-d478546701ea	gram_flour	t	ai_generated
ac4ffde2-19b1-aa9d-b9e6-d478546701ea	onion	f	ai_generated
ac4ffde2-19b1-aa9d-b9e6-d478546701ea	garlic	f	ai_generated
ac4ffde2-19b1-aa9d-b9e6-d478546701ea	green_chilli	f	ai_generated
ac4ffde2-19b1-aa9d-b9e6-d478546701ea	mustard_seeds	f	ai_generated
ac4ffde2-19b1-aa9d-b9e6-d478546701ea	turmeric	f	ai_generated
ac4ffde2-19b1-aa9d-b9e6-d478546701ea	curry_powder	f	ai_generated
ac4ffde2-19b1-aa9d-b9e6-d478546701ea	salt	f	ai_generated
927cc5ba-b06a-26c7-ce46-170e4d92b57b	potato	t	ai_generated
927cc5ba-b06a-26c7-ce46-170e4d92b57b	raw_banana	t	ai_generated
927cc5ba-b06a-26c7-ce46-170e4d92b57b	val_dal	t	ai_generated
927cc5ba-b06a-26c7-ce46-170e4d92b57b	eggplant	f	ai_generated
927cc5ba-b06a-26c7-ce46-170e4d92b57b	green_peas	f	ai_generated
927cc5ba-b06a-26c7-ce46-170e4d92b57b	coconut_fresh	f	ai_generated
927cc5ba-b06a-26c7-ce46-170e4d92b57b	green_chilli	f	ai_generated
927cc5ba-b06a-26c7-ce46-170e4d92b57b	jaggery	f	ai_generated
927cc5ba-b06a-26c7-ce46-170e4d92b57b	salt	f	ai_generated
add28dd4-e502-cbcc-d60a-970717e044fd	curd	t	ai_generated
add28dd4-e502-cbcc-d60a-970717e044fd	gram_flour	t	ai_generated
add28dd4-e502-cbcc-d60a-970717e044fd	ginger	f	ai_generated
add28dd4-e502-cbcc-d60a-970717e044fd	green_chilli	f	ai_generated
add28dd4-e502-cbcc-d60a-970717e044fd	curry_powder	f	ai_generated
add28dd4-e502-cbcc-d60a-970717e044fd	jaggery	f	ai_generated
add28dd4-e502-cbcc-d60a-970717e044fd	cumin_seeds	f	ai_generated
add28dd4-e502-cbcc-d60a-970717e044fd	salt	f	ai_generated
f82b0339-6154-8b83-ea50-1a8f952570cb	rohu	t	ai_generated
f82b0339-6154-8b83-ea50-1a8f952570cb	potato	f	ai_generated
f82b0339-6154-8b83-ea50-1a8f952570cb	tomato	f	ai_generated
f82b0339-6154-8b83-ea50-1a8f952570cb	panch_phoron	f	ai_generated
f82b0339-6154-8b83-ea50-1a8f952570cb	turmeric	f	ai_generated
f82b0339-6154-8b83-ea50-1a8f952570cb	mustard_seeds	f	ai_generated
f82b0339-6154-8b83-ea50-1a8f952570cb	green_chilli	f	ai_generated
f82b0339-6154-8b83-ea50-1a8f952570cb	salt	f	ai_generated
8891a879-55b1-4a59-565f-b62e641a9ce6	chana_dal	t	ai_generated
8891a879-55b1-4a59-565f-b62e641a9ce6	coconut_fresh	f	ai_generated
8891a879-55b1-4a59-565f-b62e641a9ce6	ginger	f	ai_generated
8891a879-55b1-4a59-565f-b62e641a9ce6	cumin_seeds	f	ai_generated
8891a879-55b1-4a59-565f-b62e641a9ce6	bay_leaf	f	ai_generated
8891a879-55b1-4a59-565f-b62e641a9ce6	ghee	f	ai_generated
8891a879-55b1-4a59-565f-b62e641a9ce6	jaggery	f	ai_generated
8891a879-55b1-4a59-565f-b62e641a9ce6	salt	f	ai_generated
fae1b50d-81ef-dde6-1b3e-e491fc2bb00c	rice_regular	t	ai_generated
fae1b50d-81ef-dde6-1b3e-e491fc2bb00c	moong_dal	t	ai_generated
fae1b50d-81ef-dde6-1b3e-e491fc2bb00c	cauliflower	f	ai_generated
fae1b50d-81ef-dde6-1b3e-e491fc2bb00c	potato	f	ai_generated
fae1b50d-81ef-dde6-1b3e-e491fc2bb00c	ginger	f	ai_generated
fae1b50d-81ef-dde6-1b3e-e491fc2bb00c	bay_leaf	f	ai_generated
fae1b50d-81ef-dde6-1b3e-e491fc2bb00c	cumin_seeds	f	ai_generated
fae1b50d-81ef-dde6-1b3e-e491fc2bb00c	ghee	f	ai_generated
fae1b50d-81ef-dde6-1b3e-e491fc2bb00c	salt	f	ai_generated
1cf96e14-7279-cf89-853c-a317ea628c59	potato	t	ai_generated
1cf96e14-7279-cf89-853c-a317ea628c59	poppy_seeds	t	ai_generated
1cf96e14-7279-cf89-853c-a317ea628c59	green_chilli	f	ai_generated
1cf96e14-7279-cf89-853c-a317ea628c59	nigella_seeds	f	ai_generated
1cf96e14-7279-cf89-853c-a317ea628c59	mustard_seeds	f	ai_generated
1cf96e14-7279-cf89-853c-a317ea628c59	salt	f	ai_generated
50c619c9-8c71-104e-9ce2-e59ad485eea6	egg	t	ai_generated
50c619c9-8c71-104e-9ce2-e59ad485eea6	onion	f	ai_generated
50c619c9-8c71-104e-9ce2-e59ad485eea6	tomato	f	ai_generated
50c619c9-8c71-104e-9ce2-e59ad485eea6	green_chilli	f	ai_generated
50c619c9-8c71-104e-9ce2-e59ad485eea6	turmeric	f	ai_generated
50c619c9-8c71-104e-9ce2-e59ad485eea6	red_chilli_powder	f	ai_generated
50c619c9-8c71-104e-9ce2-e59ad485eea6	salt	f	ai_generated
3724eab6-70e6-a157-240c-ca0b13d56f87	toor_dal	t	ai_generated
3724eab6-70e6-a157-240c-ca0b13d56f87	jaggery	f	ai_generated
3724eab6-70e6-a157-240c-ca0b13d56f87	ginger	f	ai_generated
3724eab6-70e6-a157-240c-ca0b13d56f87	green_chilli	f	ai_generated
3724eab6-70e6-a157-240c-ca0b13d56f87	turmeric	f	ai_generated
3724eab6-70e6-a157-240c-ca0b13d56f87	curry_leaves	f	ai_generated
3724eab6-70e6-a157-240c-ca0b13d56f87	salt	f	ai_generated
e2d96ee7-631c-ce43-728d-67b92048ca50	moong_dal	t	ai_generated
e2d96ee7-631c-ce43-728d-67b92048ca50	cumin_seeds	f	ai_generated
e2d96ee7-631c-ce43-728d-67b92048ca50	turmeric	f	ai_generated
e2d96ee7-631c-ce43-728d-67b92048ca50	ginger	f	ai_generated
e2d96ee7-631c-ce43-728d-67b92048ca50	ghee	f	ai_generated
e2d96ee7-631c-ce43-728d-67b92048ca50	salt	f	ai_generated
bccc96e8-98ae-5299-b77c-e2dc3191e7b8	cabbage	t	ai_generated
bccc96e8-98ae-5299-b77c-e2dc3191e7b8	green_peas	f	ai_generated
bccc96e8-98ae-5299-b77c-e2dc3191e7b8	mustard_seeds	f	ai_generated
bccc96e8-98ae-5299-b77c-e2dc3191e7b8	turmeric	f	ai_generated
bccc96e8-98ae-5299-b77c-e2dc3191e7b8	green_chilli	f	ai_generated
bccc96e8-98ae-5299-b77c-e2dc3191e7b8	curry_leaves	f	ai_generated
bccc96e8-98ae-5299-b77c-e2dc3191e7b8	salt	f	ai_generated
e2f73051-0267-30b2-1742-259348c25c3e	pumpkin	t	ai_generated
e2f73051-0267-30b2-1742-259348c25c3e	jaggery	f	ai_generated
e2f73051-0267-30b2-1742-259348c25c3e	fenugreek_seeds	f	ai_generated
e2f73051-0267-30b2-1742-259348c25c3e	dry_red_chilli	f	ai_generated
e2f73051-0267-30b2-1742-259348c25c3e	turmeric	f	ai_generated
e2f73051-0267-30b2-1742-259348c25c3e	salt	f	ai_generated
a0d1d9f8-0e03-0171-c0e4-0d0790ea281a	gram_flour	t	ai_generated
a0d1d9f8-0e03-0171-c0e4-0d0790ea281a	green_chilli	f	ai_generated
a0d1d9f8-0e03-0171-c0e4-0d0790ea281a	ginger	f	ai_generated
a0d1d9f8-0e03-0171-c0e4-0d0790ea281a	mustard_seeds	f	ai_generated
a0d1d9f8-0e03-0171-c0e4-0d0790ea281a	curry_leaves	f	ai_generated
a0d1d9f8-0e03-0171-c0e4-0d0790ea281a	sesame_seeds	f	ai_generated
a0d1d9f8-0e03-0171-c0e4-0d0790ea281a	salt	f	ai_generated
0025474a-7394-2e88-34c9-9932de7fcff1	rice_regular	t	ai_generated
0025474a-7394-2e88-34c9-9932de7fcff1	moong_dal	t	ai_generated
0025474a-7394-2e88-34c9-9932de7fcff1	black_pepper	f	ai_generated
0025474a-7394-2e88-34c9-9932de7fcff1	cumin_seeds	f	ai_generated
0025474a-7394-2e88-34c9-9932de7fcff1	ginger	f	ai_generated
0025474a-7394-2e88-34c9-9932de7fcff1	ghee	f	ai_generated
0025474a-7394-2e88-34c9-9932de7fcff1	curry_leaves	f	ai_generated
0025474a-7394-2e88-34c9-9932de7fcff1	salt	f	ai_generated
c708eba7-3e4b-47ad-4149-4d1a73880c9a	rice_regular	t	ai_generated
c708eba7-3e4b-47ad-4149-4d1a73880c9a	moong_dal	t	ai_generated
c708eba7-3e4b-47ad-4149-4d1a73880c9a	bottle_gourd	t	ai_generated
c708eba7-3e4b-47ad-4149-4d1a73880c9a	cumin_seeds	f	ai_generated
c708eba7-3e4b-47ad-4149-4d1a73880c9a	turmeric	f	ai_generated
c708eba7-3e4b-47ad-4149-4d1a73880c9a	ghee	f	ai_generated
c708eba7-3e4b-47ad-4149-4d1a73880c9a	salt	f	ai_generated
abb973e3-39cf-c755-2ae9-be427dd67f74	bottle_gourd	t	ai_generated
abb973e3-39cf-c755-2ae9-be427dd67f74	tomato	f	ai_generated
abb973e3-39cf-c755-2ae9-be427dd67f74	cumin_seeds	f	ai_generated
abb973e3-39cf-c755-2ae9-be427dd67f74	turmeric	f	ai_generated
abb973e3-39cf-c755-2ae9-be427dd67f74	green_chilli	f	ai_generated
abb973e3-39cf-c755-2ae9-be427dd67f74	salt	f	ai_generated
37576d5a-67f9-11ec-728a-a25e8efb77be	tapioca	t	ai_generated
37576d5a-67f9-11ec-728a-a25e8efb77be	potato	t	ai_generated
37576d5a-67f9-11ec-728a-a25e8efb77be	cumin_seeds	f	ai_generated
37576d5a-67f9-11ec-728a-a25e8efb77be	green_chilli	f	ai_generated
37576d5a-67f9-11ec-728a-a25e8efb77be	ghee	f	ai_generated
37576d5a-67f9-11ec-728a-a25e8efb77be	salt	f	ai_generated
23b0a8b1-5107-ad34-4732-059008e91491	wheat_flour	t	ai_generated
23b0a8b1-5107-ad34-4732-059008e91491	salt	f	ai_generated
7115870b-11c1-6b2e-2ebf-43bfd4d5e9bc	rice_regular	t	ai_generated
7115870b-11c1-6b2e-2ebf-43bfd4d5e9bc	salt	f	ai_generated
6821e31c-cd50-1995-7d27-d12e01de7c38	wheat_flour	t	ai_generated
6821e31c-cd50-1995-7d27-d12e01de7c38	vegetable_oil	f	ai_generated
6821e31c-cd50-1995-7d27-d12e01de7c38	salt	f	ai_generated
9dda7b5c-e4ed-5b85-3ab0-2cb423461995	jowar_flour	t	ai_generated
9dda7b5c-e4ed-5b85-3ab0-2cb423461995	salt	f	ai_generated
\.


--
-- Data for Name: dish_macro; Type: TABLE DATA; Schema: ghar_re; Owner: -
--

COPY ghar_re.dish_macro (dish_id, calories, protein_g, fibre_g, fat_g, carbs_g, sugar_g, sodium_mg, data_source) FROM stdin;
7ddaee12-915c-aada-6040-b9e733e98c7a	320	7	4	20	30	3	480	ai_generated
62aa4772-38c3-9d41-51fd-37c7a4b17389	280	9	8	16	22	4	520	ai_generated
5929056d-ea5b-6189-492e-4095f29290db	220	12	6	7	28	3	430	ai_generated
8f1dc758-de7c-33f6-b88a-1c72ee6d84da	300	14	11	8	42	5	500	ai_generated
7d016491-175e-918c-94f2-d1580d56c402	210	5	6	10	26	4	400	ai_generated
2e99df2f-27ee-9e0c-641d-be09e46e7f20	330	9	3	18	34	6	560	ai_generated
0b5f372a-c53f-61a5-8c2a-637b131c1a4a	340	13	12	9	50	6	620	ai_generated
c93598a1-1298-c8a2-d5c9-aeb9a151266d	450	15	3	30	26	8	640	ai_generated
c334b845-1c6d-d749-b7e7-7083f55ff821	480	10	6	16	72	6	700	ai_generated
6df98a0f-c6c3-116f-d2ff-40d4a9ae48a0	280	10	5	6	48	2	360	ai_generated
3c13fb4c-7e8b-ea6a-bb0b-679aad62d613	360	8	4	12	56	2	480	ai_generated
1aab33f2-b951-00f3-fa1b-f2037d547c16	150	5	2	1	30	1	300	ai_generated
6695b916-d65f-9424-8536-30f5dd274941	190	9	6	5	28	4	520	ai_generated
bad73b19-60e3-326a-4690-541ad275312f	90	4	2	3	12	3	440	ai_generated
bbad43bb-dd04-e820-b203-aa51852902ad	260	7	2	6	44	4	380	ai_generated
fca7677f-b221-f385-c558-943784f2eaf9	300	10	3	16	30	1	460	ai_generated
a8573473-a3cc-39a2-e3e0-656a7615e598	420	32	3	26	12	3	680	ai_generated
580cc1e5-9c77-2cf7-0496-f105cc76a523	310	6	4	19	30	3	470	ai_generated
ac4ffde2-19b1-aa9d-b9e6-d478546701ea	200	8	3	10	22	2	420	ai_generated
927cc5ba-b06a-26c7-ce46-170e4d92b57b	360	9	10	18	40	8	520	ai_generated
add28dd4-e502-cbcc-d60a-970717e044fd	180	6	2	8	22	9	400	ai_generated
f82b0339-6154-8b83-ea50-1a8f952570cb	260	24	2	14	12	2	560	ai_generated
8891a879-55b1-4a59-565f-b62e641a9ce6	240	11	8	7	34	6	380	ai_generated
fae1b50d-81ef-dde6-1b3e-e491fc2bb00c	380	12	6	12	56	3	440	ai_generated
1cf96e14-7279-cf89-853c-a317ea628c59	230	5	4	12	26	2	360	ai_generated
50c619c9-8c71-104e-9ce2-e59ad485eea6	240	16	1	17	6	3	420	ai_generated
3724eab6-70e6-a157-240c-ca0b13d56f87	200	10	5	4	32	7	360	ai_generated
e2d96ee7-631c-ce43-728d-67b92048ca50	180	11	4	4	26	2	320	ai_generated
bccc96e8-98ae-5299-b77c-e2dc3191e7b8	120	4	5	6	16	4	300	ai_generated
e2f73051-0267-30b2-1742-259348c25c3e	140	3	4	5	24	9	280	ai_generated
a0d1d9f8-0e03-0171-c0e4-0d0790ea281a	160	6	3	4	26	3	340	ai_generated
0025474a-7394-2e88-34c9-9932de7fcff1	320	10	4	12	44	1	420	ai_generated
c708eba7-3e4b-47ad-4149-4d1a73880c9a	260	9	5	6	44	3	340	ai_generated
abb973e3-39cf-c755-2ae9-be427dd67f74	110	3	4	5	16	4	280	ai_generated
37576d5a-67f9-11ec-728a-a25e8efb77be	300	4	2	10	52	1	300	ai_generated
23b0a8b1-5107-ad34-4732-059008e91491	120	3	2	3	20	0	180	ai_generated
7115870b-11c1-6b2e-2ebf-43bfd4d5e9bc	200	4	1	0	45	0	5	ai_generated
6821e31c-cd50-1995-7d27-d12e01de7c38	180	4	2	9	22	0	160	ai_generated
9dda7b5c-e4ed-5b85-3ab0-2cb423461995	130	4	4	2	26	0	150	ai_generated
\.


--
-- Data for Name: dish_name_synonyms; Type: TABLE DATA; Schema: ghar_re; Owner: -
--

COPY ghar_re.dish_name_synonyms (dish_id, synonym, data_source, alias_type, region, language, source_url, confidence) FROM stdin;
ac4ffde2-19b1-aa9d-b9e6-d478546701ea	Pitla	real	spelling_variant	Maharashtra	marathi	https://en.wikipedia.org/wiki/Jhunka	0.95
ac4ffde2-19b1-aa9d-b9e6-d478546701ea	Zunka	real	regional_name	Maharashtra, North Karnataka	marathi	https://en.wikipedia.org/wiki/Jhunka	0.8
ac4ffde2-19b1-aa9d-b9e6-d478546701ea	Jhunka	real	spelling_variant	Maharashtra	marathi	https://en.wikipedia.org/wiki/Jhunka	0.8
ac4ffde2-19b1-aa9d-b9e6-d478546701ea	Besan Curry	real	english_gloss	\N	english	https://en.wikipedia.org/wiki/Jhunka	0.85
0b5f372a-c53f-61a5-8c2a-637b131c1a4a	Chana Masala	real	common_name	\N	hindi	https://en.wikipedia.org/wiki/Chana_masala	0.95
0b5f372a-c53f-61a5-8c2a-637b131c1a4a	Chole Masala	real	common_name	Punjab	punjabi	https://en.wikipedia.org/wiki/Chana_masala	0.9
0b5f372a-c53f-61a5-8c2a-637b131c1a4a	Chholay	real	spelling_variant	\N	hindi	https://en.wikipedia.org/wiki/Chana_masala	0.85
0b5f372a-c53f-61a5-8c2a-637b131c1a4a	Kabuli Chana Masala	real	common_name	\N	hindi	https://en.wikipedia.org/wiki/Chana_masala	0.85
0b5f372a-c53f-61a5-8c2a-637b131c1a4a	Chickpea Curry	real	english_gloss	\N	english	https://en.wikipedia.org/wiki/Chana_masala	0.95
a0d1d9f8-0e03-0171-c0e4-0d0790ea281a	Khaman	real	common_name	Gujarat	gujarati	https://en.wikipedia.org/wiki/Dhokla	0.85
a0d1d9f8-0e03-0171-c0e4-0d0790ea281a	Khaman Dhokla	real	common_name	Gujarat	gujarati	https://en.wikipedia.org/wiki/Dhokla	0.9
a0d1d9f8-0e03-0171-c0e4-0d0790ea281a	Khatta Dhokla	real	regional_name	Gujarat	gujarati	https://en.wikipedia.org/wiki/Dhokla	0.85
a0d1d9f8-0e03-0171-c0e4-0d0790ea281a	Steamed Gram Flour Cake	real	english_gloss	\N	english	https://en.wikipedia.org/wiki/Dhokla	0.9
927cc5ba-b06a-26c7-ce46-170e4d92b57b	Oondhiya	real	spelling_variant	Gujarat	gujarati	https://en.wikipedia.org/wiki/Undhiyu	0.95
927cc5ba-b06a-26c7-ce46-170e4d92b57b	Umbadiyu	real	regional_name	South Gujarat	gujarati	https://en.wikipedia.org/wiki/Undhiyu	0.85
927cc5ba-b06a-26c7-ce46-170e4d92b57b	Surti Undhiyu	real	regional_name	Surat	gujarati	https://en.wikipedia.org/wiki/Undhiyu	0.9
927cc5ba-b06a-26c7-ce46-170e4d92b57b	Mixed Vegetable Curry	real	english_gloss	\N	english	https://en.wikipedia.org/wiki/Undhiyu	0.85
\.


--
-- Data for Name: dish_variants; Type: TABLE DATA; Schema: ghar_re; Owner: -
--

COPY ghar_re.dish_variants (id, from_dish_id, to_dish_id, variant_type, note, data_source) FROM stdin;
49ca6a74-a539-4efb-aa11-580b1368a115	a8573473-a3cc-39a2-e3e0-656a7615e598	c93598a1-1298-c8a2-d5c9-aeb9a151266d	veg_swap	non-veg -> veg single on veg-day	ai_generated
24dfd4a0-27fb-40b1-9f85-9ad25a73fde8	7ddaee12-915c-aada-6040-b9e733e98c7a	fca7677f-b221-f385-c558-943784f2eaf9	veg_swap	North fried snack -> South fried snack analogue	ai_generated
\.


--
-- Data for Name: dishes; Type: TABLE DATA; Schema: ghar_re; Owner: -
--

COPY ghar_re.dishes (id, name, short_description, alternate_names, cuisine, spice_level, sweetness, heaviness, difficulty, prep_mins, cook_mins, total_mins, calories, serving_size, meal_type, dish_category, cooking_method, primary_taste, texture, richness, mouthfeel, aroma_profile, fermentation, serving_temp, weather_affinity, diet, hero_role, jain_compatible, scope_tier, farali_compatible, is_active, data_source) FROM stdin;
7ddaee12-915c-aada-6040-b9e733e98c7a	Onion Pakora	\N	{}	punjabi	2	0	2	medium	15	25	40	320	1 plate	{snacks,dinner}	{snack_starter}	{deep_fried}	{savoury}	{crispy,crunchy}	{oily}	{dry}	{roasted_aroma}	none	hot	{rainy}	veg	dry	N	indian_core	f	t	ai_generated
62aa4772-38c3-9d41-51fd-37c7a4b17389	Sarson Ka Saag	\N	{}	punjabi	2	0	3	medium	15	25	40	280	1 plate	{lunch,dinner}	{dry_sabzi,curry}	{pressure_cooked,sauteed}	{savoury}	{smooth}	{ghee_rich}	{pasty}	{earthy,pungent}	none	hot	{cold_weather}	veg	liquid	N	indian_core	f	t	ai_generated
5929056d-ea5b-6189-492e-4095f29290db	Dal Tadka	\N	{}	punjabi	2	0	2	medium	15	25	40	220	1 plate	{lunch,dinner}	{dal_lentil}	{pressure_cooked,tempered}	{savoury}	{smooth}	{light}	{moist}	{earthy}	none	hot	{all_weather}	veg	liquid	N	indian_core	f	t	ai_generated
8f1dc758-de7c-33f6-b88a-1c72ee6d84da	Rajma	\N	{}	punjabi	2	0	3	medium	15	25	40	300	1 plate	{lunch,dinner}	{dal_lentil,curry}	{pressure_cooked,sauteed}	{savoury}	{smooth}	{light}	{moist}	{earthy}	none	hot	{all_weather,cold_weather}	veg	liquid	N	indian_core	f	t	ai_generated
7d016491-175e-918c-94f2-d1580d56c402	Aloo Gobi	\N	{}	up	2	0	2	medium	15	25	40	210	1 plate	{lunch,dinner}	{dry_sabzi}	{sauteed}	{savoury}	{soft}	{light}	{dry}	{earthy}	none	hot	{all_weather}	veg	dry	N	indian_core	f	t	ai_generated
2e99df2f-27ee-9e0c-641d-be09e46e7f20	Punjabi Kadhi Pakora	\N	{}	punjabi	2	0	3	medium	15	25	40	330	1 plate	{lunch,dinner}	{curry}	{sauteed,tempered}	{tangy,savoury}	{smooth}	{creamy}	{moist}	{pungent}	none	hot	{all_weather,rainy}	veg	liquid	N	indian_core	f	t	ai_generated
0b5f372a-c53f-61a5-8c2a-637b131c1a4a	Chole	\N	{}	delhi	3	0	3	medium	15	25	40	340	1 plate	{lunch,dinner}	{curry,dal_lentil}	{pressure_cooked,sauteed}	{spicy_hot,tangy}	{smooth}	{light}	{moist}	{pungent}	none	hot	{all_weather}	veg	liquid	N	indian_core	f	t	ai_generated
c93598a1-1298-c8a2-d5c9-aeb9a151266d	Paneer Butter Masala	\N	{}	punjabi	1	1	3	medium	15	25	40	450	1 plate	{lunch,dinner}	{curry}	{sauteed}	{savoury}	{smooth}	{creamy,buttery}	{velvety}	{roasted_aroma}	none	hot	{all_weather}	veg	single	N	indian_core	f	t	ai_generated
c334b845-1c6d-d749-b7e7-7083f55ff821	Veg Biryani	\N	{}	mughlai	3	0	3	medium	15	25	40	480	1 plate	{lunch,dinner}	{biryani_pulao}	{dum_cooked}	{savoury}	{grainy,fluffy}	{ghee_rich}	{moist}	{roasted_aroma,floral}	none	hot	{all_weather}	veg	standalone	N	indian_core	f	t	ai_generated
6df98a0f-c6c3-116f-d2ff-40d4a9ae48a0	Moong Dal Khichdi	\N	{}	up	1	0	2	medium	15	25	40	280	1 plate	{lunch,dinner}	{whole_meal}	{pressure_cooked,tempered}	{savoury}	{soft,sticky}	{light}	{moist}	{mild}	none	hot	{rainy,cold_weather,all_weather}	veg	standalone	Y	indian_core	f	t	ai_generated
3c13fb4c-7e8b-ea6a-bb0b-679aad62d613	Masala Dosa	\N	{}	udupi	2	0	2	medium	15	25	40	360	1 plate	{breakfast,dinner}	{dosa_idli}	{shallow_fried,fermented_cook}	{savoury}	{crispy}	{light}	{dry}	{fermented_aroma}	heavy	hot	{all_weather}	veg	standalone	N	indian_core	f	t	ai_generated
1aab33f2-b951-00f3-fa1b-f2037d547c16	Idli	\N	{}	udupi	0	0	1	medium	15	25	40	150	1 plate	{breakfast,dinner}	{dosa_idli}	{steamed,fermented_cook}	{savoury,sour}	{soft,fluffy}	{plain}	{moist}	{fermented_aroma}	heavy	hot	{all_weather}	veg	dry	Y	indian_core	f	t	ai_generated
6695b916-d65f-9424-8536-30f5dd274941	Sambar	\N	{}	tamil	2	0	2	medium	15	25	40	190	1 plate	{breakfast,lunch,dinner}	{dal_lentil,curry}	{pressure_cooked,tempered}	{tangy,savoury}	{smooth}	{light}	{moist}	{pungent}	none	hot	{all_weather}	veg	liquid	N	indian_core	f	t	ai_generated
bad73b19-60e3-326a-4690-541ad275312f	Rasam	\N	{}	tamil	2	0	1	medium	15	25	40	90	1 plate	{lunch,dinner}	{soup,curry}	{boiled,tempered}	{tangy,spicy_hot}	{smooth}	{light}	{moist}	{pungent,citrusy}	none	hot	{rainy,all_weather}	veg	liquid	N	indian_core	f	t	ai_generated
bbad43bb-dd04-e820-b203-aa51852902ad	Curd Rice	\N	{}	tamil	0	0	2	medium	15	25	40	260	1 plate	{lunch,dinner}	{whole_meal,rice}	{boiled,tempered}	{sour,savoury}	{soft,sticky}	{light}	{moist}	{mild}	none	chilled	{hot_weather}	veg	single	Y	indian_core	f	t	ai_generated
fca7677f-b221-f385-c558-943784f2eaf9	Medu Vada	\N	{}	tamil	2	0	2	medium	15	25	40	300	1 plate	{breakfast,snacks,dinner}	{snack_starter}	{deep_fried}	{savoury}	{crispy,fluffy}	{oily}	{dry}	{roasted_aroma}	none	hot	{rainy}	veg	dry	N	indian_core	f	t	ai_generated
a8573473-a3cc-39a2-e3e0-656a7615e598	Chettinad Chicken	\N	{}	chettinad	4	0	3	medium	15	25	40	420	1 plate	{lunch,dinner}	{curry}	{sauteed}	{spicy_hot,savoury}	{smooth}	{oily}	{moist}	{roasted_aroma,pungent}	none	hot	{all_weather}	non_veg	single	N	indian_core	f	t	ai_generated
580cc1e5-9c77-2cf7-0496-f105cc76a523	Kanda Bhaji	\N	{}	maharashtrian	2	0	2	medium	15	25	40	310	1 plate	{snacks,dinner}	{snack_starter}	{deep_fried}	{savoury}	{crispy,crunchy}	{oily}	{dry}	{roasted_aroma}	none	hot	{rainy}	veg	dry	N	indian_core	f	t	ai_generated
ac4ffde2-19b1-aa9d-b9e6-d478546701ea	Pithla	\N	{}	maharashtrian	2	0	2	medium	15	25	40	200	1 plate	{lunch,dinner}	{curry}	{sauteed,tempered}	{savoury}	{smooth}	{light}	{moist}	{pungent}	none	hot	{rainy,cold_weather,all_weather}	veg	liquid	N	indian_core	f	t	ai_generated
927cc5ba-b06a-26c7-ce46-170e4d92b57b	Undhiyu	\N	{}	gujarati	2	1	3	medium	15	25	40	360	1 plate	{lunch,dinner}	{dry_sabzi}	{sauteed}	{savoury}	{soft}	{oily}	{dry}	{earthy,herby}	none	hot	{cold_weather}	veg	dry	N	indian_core	f	t	ai_generated
add28dd4-e502-cbcc-d60a-970717e044fd	Gujarati Kadhi	\N	{}	gujarati	1	2	2	medium	15	25	40	180	1 plate	{lunch,dinner}	{curry}	{boiled,tempered}	{tangy,sweet}	{smooth}	{light}	{moist}	{mild}	none	hot	{all_weather}	veg	liquid	Y	indian_core	f	t	ai_generated
f82b0339-6154-8b83-ea50-1a8f952570cb	Macher Jhol	\N	{}	bengali	2	0	2	medium	15	25	40	260	1 plate	{lunch,dinner}	{curry}	{sauteed}	{savoury}	{smooth}	{light}	{moist}	{pungent}	none	hot	{all_weather,rainy}	non_veg	liquid	N	indian_core	f	t	ai_generated
8891a879-55b1-4a59-565f-b62e641a9ce6	Cholar Dal	\N	{}	bengali	1	1	2	medium	15	25	40	240	1 plate	{lunch,dinner}	{dal_lentil}	{pressure_cooked,tempered}	{savoury}	{smooth}	{light}	{moist}	{sweet_aroma}	none	hot	{all_weather}	veg	liquid	N	indian_core	f	t	ai_generated
fae1b50d-81ef-dde6-1b3e-e491fc2bb00c	Bhuna Khichuri	\N	{}	bengali	1	0	3	medium	15	25	40	380	1 plate	{lunch,dinner}	{whole_meal}	{sauteed,pressure_cooked}	{savoury}	{soft,sticky}	{ghee_rich}	{moist}	{roasted_aroma}	none	hot	{rainy,cold_weather}	veg	standalone	N	indian_core	f	t	ai_generated
1cf96e14-7279-cf89-853c-a317ea628c59	Aloo Posto	\N	{}	bengali	1	0	2	medium	15	25	40	230	1 plate	{lunch,dinner}	{dry_sabzi}	{sauteed}	{savoury}	{soft}	{light}	{dry}	{nutty}	none	hot	{all_weather}	veg	dry	N	indian_core	f	t	ai_generated
50c619c9-8c71-104e-9ce2-e59ad485eea6	Egg Bhurji	\N	{}	delhi	2	0	2	medium	15	25	40	240	1 plate	{breakfast,lunch,dinner}	{egg_dish}	{sauteed}	{savoury}	{crumbly}	{light}	{dry}	{pungent}	none	hot	{all_weather}	egg	dry	N	indian_core	f	t	ai_generated
3724eab6-70e6-a157-240c-ca0b13d56f87	Gujarati Toor Dal	\N	{}	gujarati	1	1	2	medium	15	25	40	200	1 plate	{lunch,dinner}	{dal_lentil}	{pressure_cooked,tempered}	{sweet,tangy}	{smooth}	{light}	{moist}	{mild}	none	hot	{all_weather}	veg	liquid	Y	indian_core	f	t	ai_generated
e2d96ee7-631c-ce43-728d-67b92048ca50	Moong Dal	\N	{}	gujarati	1	0	1	medium	15	25	40	180	1 plate	{lunch,dinner}	{dal_lentil}	{pressure_cooked,tempered}	{savoury}	{smooth}	{light}	{moist}	{mild}	none	hot	{all_weather}	veg	liquid	Y	indian_core	f	t	ai_generated
bccc96e8-98ae-5299-b77c-e2dc3191e7b8	Cabbage Sabzi	\N	{}	maharashtrian	1	0	1	medium	15	25	40	120	1 plate	{lunch,dinner}	{dry_sabzi}	{sauteed,tempered}	{savoury}	{soft}	{light}	{moist}	{mild}	none	hot	{all_weather}	veg	dry	Y	indian_core	f	t	ai_generated
e2f73051-0267-30b2-1742-259348c25c3e	Pumpkin Sabzi	\N	{}	gujarati	1	1	1	medium	15	25	40	140	1 plate	{lunch,dinner}	{dry_sabzi}	{sauteed}	{sweet,savoury}	{soft}	{light}	{moist}	{mild}	none	hot	{all_weather}	veg	dry	Y	indian_core	f	t	ai_generated
a0d1d9f8-0e03-0171-c0e4-0d0790ea281a	Dhokla	\N	{}	gujarati	1	1	1	medium	15	25	40	160	1 plate	{breakfast,lunch,dinner,snacks}	{snack_starter}	{steamed,fermented_cook}	{tangy,sweet}	{soft,fluffy}	{light}	{moist}	{fermented_aroma}	medium	hot	{all_weather}	veg	dry	Y	indian_core	f	t	ai_generated
0025474a-7394-2e88-34c9-9932de7fcff1	Ven Pongal	\N	{}	tamil	1	0	2	medium	15	25	40	320	1 plate	{breakfast,lunch,dinner}	{whole_meal,rice}	{pressure_cooked,tempered}	{savoury}	{soft,sticky}	{ghee_rich}	{moist}	{roasted_aroma}	none	hot	{cold_weather}	veg	single	Y	indian_core	f	t	ai_generated
c708eba7-3e4b-47ad-4149-4d1a73880c9a	Lauki Khichdi	\N	{}	up	1	0	2	medium	15	25	40	260	1 plate	{lunch,dinner}	{whole_meal}	{pressure_cooked,tempered}	{savoury}	{soft,sticky}	{light}	{moist}	{mild}	none	hot	{all_weather,cold_weather}	veg	standalone	Y	indian_core	f	t	ai_generated
abb973e3-39cf-c755-2ae9-be427dd67f74	Lauki Sabzi	\N	{}	up	1	0	1	medium	15	25	40	110	1 plate	{lunch,dinner}	{dry_sabzi}	{sauteed}	{savoury}	{soft}	{light}	{moist}	{mild}	none	hot	{all_weather}	veg	dry	Y	indian_core	f	t	ai_generated
37576d5a-67f9-11ec-728a-a25e8efb77be	Sabudana Khichdi	\N	{}	maharashtrian	1	0	2	medium	15	25	40	300	1 plate	{breakfast,lunch,dinner}	{whole_meal}	{sauteed}	{savoury}	{soft,sticky}	{oily}	{moist}	{nutty}	none	hot	{all_weather}	veg	standalone	N	indian_core	t	t	ai_generated
23b0a8b1-5107-ad34-4732-059008e91491	Roti	\N	{}	up	0	0	1	medium	10	10	20	120	1 plate	{breakfast,lunch,dinner}	{paratha_roti,bread}	{roasted}	{savoury}	{soft,layered}	{plain}	{dry}	{mild}	none	hot	{all_weather}	veg	support	Y	indian_core	f	t	ai_generated
7115870b-11c1-6b2e-2ebf-43bfd4d5e9bc	Steamed Rice	\N	{}	tamil	0	0	1	medium	5	15	20	200	1 plate	{breakfast,lunch,dinner}	{rice}	{boiled}	{savoury}	{soft,grainy}	{plain}	{moist}	{mild}	none	hot	{all_weather}	veg	support	Y	indian_core	f	t	ai_generated
6821e31c-cd50-1995-7d27-d12e01de7c38	Poori	\N	{}	up	0	0	2	medium	10	10	20	180	1 plate	{lunch,dinner}	{bread,paratha_roti}	{deep_fried}	{savoury}	{fluffy,crispy}	{oily}	{dry}	{roasted_aroma}	none	hot	{all_weather}	veg	support	Y	indian_core	f	t	ai_generated
9dda7b5c-e4ed-5b85-3ab0-2cb423461995	Jowar Bhakri	\N	{}	maharashtrian	0	0	1	medium	10	12	22	130	1 plate	{lunch,dinner}	{bread,paratha_roti}	{roasted}	{savoury}	{dense,crumbly}	{plain}	{dry}	{earthy}	none	hot	{all_weather}	veg	support	Y	indian_core	f	t	ai_generated
\.


--
-- Data for Name: feedback_event; Type: TABLE DATA; Schema: ghar_re; Owner: -
--

COPY ghar_re.feedback_event (id, household_id, dish_id, event_type, plate_ref, slot, detail, created_at, data_source) FROM stdin;
\.


--
-- Data for Name: household_context; Type: TABLE DATA; Schema: ghar_re; Owner: -
--

COPY ghar_re.household_context (id, household_id, session_id, slot, season, weekday, weather_condition, temp_c, is_raining, humidity, active_modes, calorie_target, created_at, data_source) FROM stdin;
\.


--
-- Data for Name: household_modes; Type: TABLE DATA; Schema: ghar_re; Owner: -
--

COPY ghar_re.household_modes (household_id, mode, is_on, params, data_source) FROM stdin;
\.


--
-- Data for Name: household_profile; Type: TABLE DATA; Schema: ghar_re; Owner: -
--

COPY ghar_re.household_profile (household_id, field_name, value, confidence, source, kind, stability, version, computed_at, data_source) FROM stdin;
\.


--
-- Data for Name: households; Type: TABLE DATA; Schema: ghar_re; Owner: -
--

COPY ghar_re.households (id, label, q1_household_type, q2_working_professionals, q3_home_state, q4_current_city, q5_diet, q6_nonveg_types, q7_veg_days, q8_is_jain, q9_allergies, q10_allergy_other, q11_conditions, q12_member_ages, q13_who_cooks, q14_eat_out_per_week, q15_objective, created_at, data_source) FROM stdin;
ffb5441e-bea2-d00a-2378-c308320fa686	Single professional, Bengaluru	single	1	Karnataka	Bengaluru	non_veg	{chicken,fish}	{}	f	{}	\N	{}	[{"age": 29, "role": "self"}]	self	4	awesome_taste	2026-08-01 09:56:51.15549+00	ai_generated
9f5682f2-cc3e-8cd8-ce01-45c48f338d18	Joint family with elders, Delhi	couple_kids_parents	2	Delhi	Delhi	veg	{}	{}	f	{}	\N	{}	[{"age": 40, "role": "adult"}, {"age": 38, "role": "adult"}, {"age": 9, "role": "child"}, {"age": 71, "role": "senior"}]	family	1	awesome_taste	2026-08-01 09:56:51.15549+00	ai_generated
fa3b1c17-c18b-165d-0860-2716f9decd01	Jain couple, Ahmedabad	couple	2	Gujarat	Ahmedabad	veg	{}	{}	t	{}	\N	{}	[{"age": 34, "role": "adult"}, {"age": 32, "role": "adult"}]	self	2	healthy_living	2026-08-01 09:56:51.15549+00	ai_generated
32a1d11b-2edc-b64e-fd39-c91aa30fd8bb	Couple with toddler, Pune	couple_kids	2	Maharashtra	Pune	veg	{}	{}	f	{}	\N	{}	[{"age": 31, "role": "adult"}, {"age": 30, "role": "adult"}, {"age": 1, "role": "weaning"}]	self	2	awesome_taste	2026-08-01 09:56:51.15549+00	ai_generated
92df4039-2ba5-ef43-2990-ac511ec2e1c5	Couple, Delhi (North)	couple	2	Delhi	Delhi	veg	{}	{}	f	{}	\N	{}	[{"age": 32, "role": "adult"}, {"age": 30, "role": "adult"}]	self	2	awesome_taste	2026-08-01 09:56:51.15549+00	ai_generated
20811ab8-028f-bcc7-b9c2-06ae1f388c63	Maharashtrian couple, Mumbai	couple	2	Maharashtra	Mumbai	veg	{}	{}	f	{}	\N	{}	[{"age": 33, "role": "adult"}, {"age": 31, "role": "adult"}]	self	2	awesome_taste	2026-08-01 09:56:51.15549+00	ai_generated
de25ec2c-f03d-319c-a1a2-9245d40e5f19	Migrant single, Bihar->Mumbai	flatmates	2	Bihar	Mumbai	non_veg	{chicken,fish,mutton}	{Tuesday}	f	{}	\N	{}	[{"age": 27, "role": "adult"}, {"age": 26, "role": "adult"}]	self	3	into_fitness	2026-08-01 09:56:51.15549+00	ai_generated
\.


--
-- Data for Name: ingredient_aliases; Type: TABLE DATA; Schema: ghar_re; Owner: -
--

COPY ghar_re.ingredient_aliases (alias, canonical_ingredient, data_source) FROM stdin;
\.


--
-- Data for Name: ingredient_normalization_map; Type: TABLE DATA; Schema: ghar_re; Owner: -
--

COPY ghar_re.ingredient_normalization_map (id, surface_token, canonical, norm_type, expansion, note, data_source) FROM stdin;
2a27c382-0950-485a-9efd-a62c406a733b	coriander_seeds	coriander	alias	\N	\N	real
fc3e55b7-7b10-4ed3-b475-921fa33de76b	cumin_powder	cumin	alias	\N	\N	real
8b9dbc57-70a3-4533-be7d-3cc4c8c972e9	basmati_rice	rice	variety	\N	basmati flag	real
ce9f8c27-c8e8-430a-8237-b45962add533	mixed_vegetables	\N	expansion	{potato,carrot,beans,peas,cauliflower}	KB ⚑ needs refinement	stub
0f7aef63-3131-4a5c-8787-86b31388a2bd	grated_coconut	coconut	form	\N	\N	real
a0727995-5c34-4d02-8943-3b6183afc66f	fish_fillet	fish	form	\N	\N	real
9dddcdbd-9cb1-41c7-b083-93e31970bd56	dhaniya	coriander	synonym	\N	\N	real
80d12bea-f50f-4b91-8a41-7203d702d2c3	palak	spinach	synonym	\N	\N	real
376ac132-524a-4bf3-afbe-6f6b65bb5f2b	mutton	goat	equivalence	\N	\N	real
\.


--
-- Data for Name: ingredients; Type: TABLE DATA; Schema: ghar_re; Owner: -
--

COPY ghar_re.ingredients (name, display_name, category, diet_type, is_allergen, allergen_type, is_jain_compatible, is_vegan, data_source) FROM stdin;
ajwain	Ajwain (Carom Seeds)	spice	veg	f	\N	t	t	real
amchur	Amchur (Dry Mango Powder)	spice	veg	f	\N	t	t	real
bay_leaf	Bay Leaf (Tej Patta)	spice	veg	f	\N	t	t	real
black_pepper	Black Pepper (Kali Mirch)	spice	veg	f	\N	t	t	real
bottle_gourd	Bottle Gourd (Lauki/Dudhi)	vegetable	veg	f	\N	t	t	real
butter	Butter (Makhan)	dairy	veg	t	dairy	t	f	real
cabbage	Cabbage (Patta Gobhi)	vegetable	veg	f	\N	t	t	real
carrot	Carrot (Gajar)	vegetable	veg	f	\N	f	t	real
cauliflower	Cauliflower (Gobhi)	vegetable	veg	f	\N	t	t	real
chaat_masala	Chaat Masala	spice	veg	f	\N	t	t	real
chana_dal	Chana Dal (Split Chickpea)	lentil_legume	veg	f	\N	t	t	real
chicken	Chicken (Murgh)	meat	non_veg	f	\N	f	f	real
chickpeas	Chickpeas (Chole/Kabuli Chana)	lentil_legume	veg	f	\N	t	t	real
coconut_fresh	Coconut Fresh (Nariyal)	coconut	veg	f	\N	t	t	real
coriander_powder	Coriander Powder (Dhaniya)	spice	veg	f	\N	t	t	real
cornmeal	Cornmeal (Makki ka Atta)	grain_flour	veg	f	\N	t	t	real
cream	Cream (Malai)	dairy	veg	t	dairy	t	f	real
cumin_seeds	Cumin Seeds (Jeera)	spice	veg	f	\N	t	t	real
curd	Curd / Yogurt (Dahi)	dairy	veg	t	dairy	t	f	real
curry_leaves	Curry Leaves (Kadi Patta)	herb_aromatic	veg	f	\N	t	t	real
curry_powder	Curry Powder	spice	veg	f	\N	t	t	real
drumstick	Drumstick (Sahjan/Moringa)	vegetable	veg	f	\N	t	t	real
dry_red_chilli	Dry Red Chilli (Sukhi Lal Mirch)	spice	veg	f	\N	t	t	real
egg	Egg (Anda)	egg	egg	t	egg_allergen	f	f	real
eggplant	Eggplant (Baingan)	vegetable	veg	f	\N	t	t	real
fenugreek_seeds	Fenugreek Seeds (Methi Dana)	spice	veg	f	\N	t	t	real
garam_masala	Garam Masala	spice	veg	f	\N	t	t	real
garlic	Garlic (Lahsun)	herb_aromatic	veg	f	\N	f	t	real
ghee	Ghee (Clarified Butter)	dairy	veg	t	dairy	t	f	real
ginger	Ginger (Adrak)	herb_aromatic	veg	f	\N	f	t	real
gram_flour	Gram Flour (Besan)	grain_flour	veg	f	\N	t	t	real
green_chilli	Green Chilli (Hari Mirch)	vegetable	veg	f	\N	t	t	real
green_peas	Green Peas (Matar)	vegetable	veg	f	\N	t	t	real
idli_rava	Idli Rava	grain_flour	veg	f	\N	t	t	real
jaggery	Jaggery (Gur)	sweetener	veg	f	\N	t	t	real
jowar_flour	Jowar Flour (Sorghum)	grain_flour	veg	f	\N	t	t	real
kasuri_methi	Kasuri Methi (Dried Fenugreek)	spice	veg	f	\N	t	t	real
kidney_beans	Kidney Beans (Rajma)	lentil_legume	veg	f	\N	t	t	real
moong_dal	Moong Dal (Split Green Gram)	lentil_legume	veg	f	\N	t	t	real
mustard_greens	Mustard Greens (Sarson)	leafy_green	veg	f	\N	t	t	real
mustard_seeds	Mustard Seeds (Rai/Sarson)	spice	veg	t	mustard	t	t	real
nigella_seeds	Nigella Seeds (Kalonji)	spice	veg	f	\N	t	t	real
onion	Onion (Pyaaz)	vegetable	veg	f	\N	f	t	real
panch_phoron	Panch Phoron	spice	veg	f	\N	t	t	real
paneer	Paneer (Cottage Cheese)	dairy	veg	t	dairy	t	f	real
poppy_seeds	Poppy Seeds (Khus Khus)	spice	veg	f	\N	t	t	real
potato	Potato (Aloo)	vegetable	veg	f	\N	f	t	real
pumpkin	Pumpkin (Kaddu)	vegetable	veg	f	\N	t	t	real
raw_banana	Raw Banana (Kaccha Kela)	vegetable	veg	f	\N	t	t	real
red_chilli_powder	Red Chilli Powder (Lal Mirch)	spice	veg	f	\N	t	t	real
rice_basmati	Basmati Rice	grain_flour	veg	f	\N	t	t	real
rice_regular	Regular Rice (Chawal)	grain_flour	veg	f	\N	t	t	real
rohu	Rohu	seafood	non_veg	t	fish	f	f	real
saffron	Saffron (Kesar)	spice	veg	f	\N	t	t	real
salt	Salt (Namak)	spice	veg	f	\N	t	t	real
sambar_powder	Sambar Powder	spice	veg	f	\N	t	t	real
sesame_seeds	Sesame Seeds (Til)	seed	veg	t	sesame	t	t	real
spinach	Spinach (Palak)	leafy_green	veg	f	\N	t	t	real
tamarind	Tamarind (Imli)	spice	veg	f	\N	t	t	real
tapioca	Tapioca (Sabudana)	grain_flour	veg	f	\N	t	t	real
tomato	Tomato (Tamatar)	vegetable	veg	f	\N	t	t	real
toor_dal	Toor Dal (Arhar)	lentil_legume	veg	f	\N	t	t	real
turmeric	Turmeric (Haldi)	spice	veg	f	\N	t	t	real
urad_dal	Urad Dal (Black Gram)	lentil_legume	veg	f	\N	t	t	real
val_dal	Val Dal (Field Bean)	lentil_legume	veg	f	\N	t	t	real
vegetable_oil	Vegetable Oil (Refined)	oil_fat	veg	f	\N	t	t	real
wheat_flour	Whole Wheat Flour (Atta)	grain_flour	veg	t	gluten	t	t	real
\.


--
-- Data for Name: negative_priors; Type: TABLE DATA; Schema: ghar_re; Owner: -
--

COPY ghar_re.negative_priors (id, discouragement, context, action, in_spine, enforced_via, status, data_source) FROM stdin;
54c4b037-a52a-4263-b11a-7996c563fe15	two rich/creamy gravies together	any plate	penalty (S4 hard-gate)	t	pairing_rules.yaml	active	real
fb328b5e-e549-4b3b-bf95-2a86b1635378	two same-base gravies (both tomato-onion / both coconut)	any plate	penalty	t	pairing_rules.yaml	active	real
e69a6019-c9ed-4146-aa23-d60990f101ef	two dry heroes as the pair	any plate	penalty	t	pairing_rules.yaml	active	real
3f39ca02-311f-4d49-9a74-ab8b78a57073	cross-region pair (Bengali + Punjabi hero)	any plate	penalty (cuisine-dist gate)	t	pairing_rules.yaml	active	real
92f180fc-48f8-485f-9e9c-b6407d6f784f	deep-fried / very-heavy	heatwave day	demote	t	weather	active	real
7b1fc360-8dab-4b37-9cce-5c641d400a7e	heavy lunch -> heavy dinner (same day)	slot sequence	demote (v2 needs history)	f	not_yet_active	deferred_v2	real
54d63168-5be1-485b-b18e-dae2a24c5899	three of the same vegetable base (e.g. 3 potato dishes)	across the 7	demote (variety)	f	not_yet_active	deferred_v2	real
742797ca-814e-4457-b987-d7cf30f5cbf7	raw salads / street-style	peak monsoon	mild demote	t	weather	active	real
\.


--
-- Data for Name: prior_zone_slot_season; Type: TABLE DATA; Schema: ghar_re; Owner: -
--

COPY ghar_re.prior_zone_slot_season (id, zone, slot, season, match_kind, match_value, boost, usage_tags, data_source) FROM stdin;
a4fc3861-50e9-4782-bf58-cd3e632ac902	North	breakfast	\N	dish_name	paratha	0.4	{Daily}	real
82ecdc2a-fb9c-45db-a676-98ff89551dd9	North	breakfast	\N	dish_name	poha	0.3	{Daily}	real
c5d420cb-7e1f-4535-bd77-2723b8842ea9	North	breakfast	\N	dish_name	chila	0.3	{Daily}	real
d99f08d9-e113-4ce0-9b44-d1b8eda2727f	South	breakfast	\N	dish_name	idli	0.5	{Daily}	real
48455fb6-e7d5-4cf6-9202-48d788374cea	South	breakfast	\N	dish_name	dosa	0.5	{Daily}	real
3d2fcbfb-87b7-4956-a54e-e8bb7a315ac2	South	breakfast	\N	dish_name	upma	0.3	{Daily}	real
e2a86f67-df8e-4e4f-ba6d-c15d5edc1f8a	South	breakfast	\N	dish_name	pongal	0.3	{Daily,Festival,Comfort}	real
85ce915d-cc17-42d8-a7c1-9f0ef90b1982	West	breakfast	\N	dish_name	poha	0.5	{Daily}	real
91077c43-fb85-48ae-bc67-870ce5109c5b	West	breakfast	\N	dish_name	thalipeeth	0.3	{Daily}	real
1e2f02eb-2d23-42dc-af00-329d84208de9	West	breakfast	\N	dish_name	upma	0.3	{Daily}	real
1daa1178-4e65-498d-ab91-064e07b8d14e	East	breakfast	\N	dish_name	luchi	0.4	{Weekend,Daily}	stub
0fc0b339-1a84-4e08-8154-6bc640ef4e8b	East	breakfast	\N	dish_name	bread-omelette	0.2	{Daily}	stub
7800e7b9-8914-4dc3-a140-cb5a44157f87	Central	breakfast	\N	dish_name	poha	0.5	{Daily}	real
c33c5573-11a8-46b3-8100-01cad0465bca	North	lunch	\N	structure	roti+sabzi+dal	0.4	{Daily}	real
41ed8a83-1974-4e1f-a252-1c30b2c326b9	North	lunch	\N	dish_name	rajma	0.3	{Daily,Comfort}	real
75256c3b-403a-4f38-b268-cc9b8189a704	North	lunch	\N	dish_name	chole	0.3	{Daily}	real
173387c1-da02-4395-b786-13773692bc89	South	lunch	\N	structure	rice+sambar	0.5	{Daily}	real
329a406b-81e0-4e11-b996-7231a9ad512a	South	lunch	\N	dish_name	rasam	0.5	{Daily}	real
a9980da6-d30b-4829-a8ce-a8ed7e55cb7b	South	lunch	\N	dish_name	poriyal	0.3	{Daily}	real
398000e5-6361-4cec-8f7e-d906f114ada7	South	lunch	\N	dish_name	curd rice	0.3	{Daily,Weather}	real
a79b82a9-d582-4d8c-9623-b703fc8ce91b	West	lunch	\N	structure	roti+sabzi+dal	0.4	{Daily}	real
1c6274c1-9819-4f60-bd6d-b6a9b3ae884b	West	lunch	\N	dish_name	varan	0.3	{Daily}	real
9e2e9b60-f70a-49df-8474-d7a62543ad09	East	lunch	\N	dish_name	macher jhol	0.5	{Daily}	real
38cbaaa5-15cf-46ef-b939-955eadfb1102	East	lunch	\N	dish_name	dal	0.3	{Daily}	real
db8fc368-5d33-4df3-84ab-cf9e01ccb895	Central	lunch	\N	structure	roti+dal+sabzi	0.4	{Daily}	real
30fad9f6-794a-48e9-905d-14072bdad5a2	Central	lunch	\N	dish_name	dal-bafla	0.3	{Daily}	real
817ed34c-7d15-48eb-b626-11048f5e2978	North	dinner	\N	structure	roti+sabzi+dal	0.4	{Daily}	real
596fdd4d-1e67-4a9f-a812-e22b5b9f8d91	North	dinner	\N	dish_name	khichdi	0.2	{Comfort,Recovery,Weather}	real
a11e03c5-8bc7-4f97-b67d-3eb5bafd01c9	South	dinner	\N	structure	rice+rasam	0.3	{Daily}	real
87ac779c-216a-426e-a023-9c929d9b95ac	South	dinner	\N	dish_name	dosa	0.3	{Daily}	real
180e0af5-24af-44c9-9b01-7b878ff182db	West	dinner	\N	structure	roti+sabzi	0.4	{Daily}	real
7cd32be4-65a6-4dab-9377-e88736aebddb	West	dinner	\N	dish_name	khichdi	0.2	{Comfort,Recovery}	real
589d08b5-5b41-44cf-82d4-be655b9e0e9a	East	dinner	\N	dish_name	jhol	0.4	{Daily}	real
\.


--
-- Data for Name: recommendation_event; Type: TABLE DATA; Schema: ghar_re; Owner: -
--

COPY ghar_re.recommendation_event (id, household_id, session_id, slot, rank, plate, plate_score, spine_version, kb_version, config_version, created_at, data_source) FROM stdin;
\.


--
-- Data for Name: region_food_affinity; Type: TABLE DATA; Schema: ghar_re; Owner: -
--

COPY ghar_re.region_food_affinity (state_code, dish_name, affinity_score, source, data_source) FROM stdin;
DL	Onion Pakora	0.7	golden-sample	ai_generated
PB	Sarson Ka Saag	0.95	golden-sample	ai_generated
MH	Kanda Bhaji	0.9	golden-sample	ai_generated
TN	Curd Rice	0.9	golden-sample	ai_generated
WB	Bhuna Khichuri	0.85	golden-sample	ai_generated
GJ	Undhiyu	0.9	golden-sample	ai_generated
\.


--
-- Data for Name: sig_score_bands; Type: TABLE DATA; Schema: ghar_re; Owner: -
--

COPY ghar_re.sig_score_bands (score, band_name, definition, data_source) FROM stdin;
1	national_icon	recognized/iconic across India (Butter Chicken, Hyderabadi Biryani, Masala Dosa)	real
0.9	state_icon	defining dish of a state (Dal Makhani, Undhiyu, Nihari, Litti Chokha)	real
0.75	regional_hero	strong regional standard (Bisi Bele Bath, Macher Jhol, Puran Poli)	real
0.6	very_common	well-known everyday-plus (Rajma Chawal, Poha, Aloo Paratha)	real
0.4	common	ordinary named dish (standard dals, upma, sabzi-with-name)	real
0.2	utility	plain staple (steamed rice, plain dal, roti, papad)	real
\.


--
-- Data for Name: sig_scores; Type: TABLE DATA; Schema: ghar_re; Owner: -
--

COPY ghar_re.sig_scores (dish_id, sig_score, band, evidence_confidence, coverage_confidence, owner, method, version, data_source) FROM stdin;
7ddaee12-915c-aada-6040-b9e733e98c7a	0.6	very_common	Low	High	golden-sample	ai_generated	v1.0	ai_generated
62aa4772-38c3-9d41-51fd-37c7a4b17389	0.9	state_icon	Low	High	golden-sample	ai_generated	v1.0	ai_generated
5929056d-ea5b-6189-492e-4095f29290db	0.4	common	Low	High	golden-sample	ai_generated	v1.0	ai_generated
8f1dc758-de7c-33f6-b88a-1c72ee6d84da	0.6	very_common	Low	High	golden-sample	ai_generated	v1.0	ai_generated
7d016491-175e-918c-94f2-d1580d56c402	0.4	common	Low	High	golden-sample	ai_generated	v1.0	ai_generated
2e99df2f-27ee-9e0c-641d-be09e46e7f20	0.6	very_common	Low	High	golden-sample	ai_generated	v1.0	ai_generated
0b5f372a-c53f-61a5-8c2a-637b131c1a4a	0.6	very_common	Low	High	golden-sample	ai_generated	v1.0	ai_generated
c93598a1-1298-c8a2-d5c9-aeb9a151266d	0.75	regional_hero	Low	High	golden-sample	ai_generated	v1.0	ai_generated
c334b845-1c6d-d749-b7e7-7083f55ff821	0.75	regional_hero	Low	High	golden-sample	ai_generated	v1.0	ai_generated
6df98a0f-c6c3-116f-d2ff-40d4a9ae48a0	0.4	common	Low	High	golden-sample	ai_generated	v1.0	ai_generated
3c13fb4c-7e8b-ea6a-bb0b-679aad62d613	1	national_icon	Low	High	golden-sample	ai_generated	v1.0	ai_generated
1aab33f2-b951-00f3-fa1b-f2037d547c16	0.6	very_common	Low	High	golden-sample	ai_generated	v1.0	ai_generated
6695b916-d65f-9424-8536-30f5dd274941	0.6	very_common	Low	High	golden-sample	ai_generated	v1.0	ai_generated
bad73b19-60e3-326a-4690-541ad275312f	0.6	very_common	Low	High	golden-sample	ai_generated	v1.0	ai_generated
bbad43bb-dd04-e820-b203-aa51852902ad	0.6	very_common	Low	High	golden-sample	ai_generated	v1.0	ai_generated
fca7677f-b221-f385-c558-943784f2eaf9	0.6	very_common	Low	High	golden-sample	ai_generated	v1.0	ai_generated
a8573473-a3cc-39a2-e3e0-656a7615e598	0.75	regional_hero	Low	High	golden-sample	ai_generated	v1.0	ai_generated
580cc1e5-9c77-2cf7-0496-f105cc76a523	0.6	very_common	Low	High	golden-sample	ai_generated	v1.0	ai_generated
ac4ffde2-19b1-aa9d-b9e6-d478546701ea	0.4	common	Low	High	golden-sample	ai_generated	v1.0	ai_generated
927cc5ba-b06a-26c7-ce46-170e4d92b57b	0.9	state_icon	Low	High	golden-sample	ai_generated	v1.0	ai_generated
add28dd4-e502-cbcc-d60a-970717e044fd	0.4	common	Low	High	golden-sample	ai_generated	v1.0	ai_generated
f82b0339-6154-8b83-ea50-1a8f952570cb	0.75	regional_hero	Low	High	golden-sample	ai_generated	v1.0	ai_generated
8891a879-55b1-4a59-565f-b62e641a9ce6	0.4	common	Low	High	golden-sample	ai_generated	v1.0	ai_generated
fae1b50d-81ef-dde6-1b3e-e491fc2bb00c	0.6	very_common	Low	High	golden-sample	ai_generated	v1.0	ai_generated
1cf96e14-7279-cf89-853c-a317ea628c59	0.75	regional_hero	Low	High	golden-sample	ai_generated	v1.0	ai_generated
50c619c9-8c71-104e-9ce2-e59ad485eea6	0.4	common	Low	High	golden-sample	ai_generated	v1.0	ai_generated
3724eab6-70e6-a157-240c-ca0b13d56f87	0.4	common	Low	High	golden-sample	ai_generated	v1.0	ai_generated
e2d96ee7-631c-ce43-728d-67b92048ca50	0.4	common	Low	High	golden-sample	ai_generated	v1.0	ai_generated
bccc96e8-98ae-5299-b77c-e2dc3191e7b8	0.4	common	Low	High	golden-sample	ai_generated	v1.0	ai_generated
e2f73051-0267-30b2-1742-259348c25c3e	0.4	common	Low	High	golden-sample	ai_generated	v1.0	ai_generated
a0d1d9f8-0e03-0171-c0e4-0d0790ea281a	0.6	very_common	Low	High	golden-sample	ai_generated	v1.0	ai_generated
0025474a-7394-2e88-34c9-9932de7fcff1	0.6	very_common	Low	High	golden-sample	ai_generated	v1.0	ai_generated
c708eba7-3e4b-47ad-4149-4d1a73880c9a	0.4	common	Low	High	golden-sample	ai_generated	v1.0	ai_generated
abb973e3-39cf-c755-2ae9-be427dd67f74	0.4	common	Low	High	golden-sample	ai_generated	v1.0	ai_generated
37576d5a-67f9-11ec-728a-a25e8efb77be	0.6	very_common	Low	High	golden-sample	ai_generated	v1.0	ai_generated
23b0a8b1-5107-ad34-4732-059008e91491	0.2	utility	Low	High	golden-sample	ai_generated	v1.0	ai_generated
7115870b-11c1-6b2e-2ebf-43bfd4d5e9bc	0.2	utility	Low	High	golden-sample	ai_generated	v1.0	ai_generated
6821e31c-cd50-1995-7d27-d12e01de7c38	0.2	utility	Low	High	golden-sample	ai_generated	v1.0	ai_generated
9dda7b5c-e4ed-5b85-3ab0-2cb423461995	0.2	utility	Low	High	golden-sample	ai_generated	v1.0	ai_generated
\.


--
-- Data for Name: tags; Type: TABLE DATA; Schema: ghar_re; Owner: -
--

COPY ghar_re.tags (category, value, display_value, tier, is_user_facing, data_source) FROM stdin;
meal_type	breakfast	Breakfast	tier_1	t	real
meal_type	lunch	Lunch	tier_1	t	real
meal_type	dinner	Dinner	tier_1	t	real
meal_type	snacks	Snacks	tier_1	t	real
dish_category	whole_meal	Whole Meal	tier_1	t	real
dish_category	bread	Bread / Roti	tier_1	t	real
dish_category	rice	Rice Dish	tier_1	t	real
dish_category	dal_lentil	Dal / Lentil	tier_1	t	real
dish_category	curry	Curry / Gravy	tier_1	t	real
dish_category	dry_sabzi	Dry Sabzi	tier_1	t	real
dish_category	salad_raita	Salad / Raita	tier_1	t	real
dish_category	chaat	Chaat	tier_1	t	real
dish_category	kebab	Kebab	tier_1	t	real
dish_category	biryani_pulao	Biryani / Pulao	tier_1	t	real
dish_category	sweet_dessert	Sweet / Dessert	tier_1	t	real
dish_category	beverage	Beverage	tier_1	t	real
dish_category	condiment_chutney	Condiment / Chutney	tier_1	t	real
dish_category	soup	Soup	tier_1	t	real
dish_category	paratha_roti	Paratha / Stuffed Roti	tier_1	t	real
dish_category	dosa_idli	Dosa / Idli / Fermented	tier_1	t	real
dish_category	noodle_pasta	Noodle / Pasta	tier_1	t	real
dish_category	egg_dish	Egg Dish	tier_1	t	real
dish_category	snack_starter	Snack / Starter	tier_1	t	real
dish_category	thali_combo	Thali / Combo	tier_1	t	real
cooking_method	deep_fried	Deep Fried	tier_2	t	real
cooking_method	shallow_fried	Shallow Fried	tier_2	t	real
cooking_method	stir_fried	Stir Fried	tier_2	t	real
cooking_method	steamed	Steamed	tier_2	t	real
cooking_method	boiled	Boiled	tier_2	t	real
cooking_method	grilled	Grilled	tier_2	t	real
cooking_method	roasted	Roasted	tier_2	t	real
cooking_method	baked	Baked	tier_2	t	real
cooking_method	tandoor	Tandoor	tier_2	t	real
cooking_method	dum_cooked	Dum Cooked	tier_2	t	real
cooking_method	pressure_cooked	Pressure Cooked	tier_2	f	real
cooking_method	sauteed	Sautéed	tier_2	f	real
cooking_method	tempered	Tempered (Tadka)	tier_2	f	real
cooking_method	raw	Raw / No Cook	tier_2	t	real
cooking_method	smoked	Smoked	tier_2	t	real
cooking_method	fermented_cook	Fermented	tier_2	t	real
primary_taste	savoury	Savoury	tier_2	t	real
primary_taste	sweet	Sweet	tier_2	t	real
primary_taste	sour	Sour	tier_2	t	real
primary_taste	bitter	Bitter	tier_2	f	real
primary_taste	umami	Umami	tier_2	f	real
primary_taste	tangy	Tangy	tier_2	t	real
primary_taste	spicy_hot	Spicy Hot	tier_2	t	real
texture	crispy	Crispy	tier_2	t	real
texture	crunchy	Crunchy	tier_2	t	real
texture	soft	Soft	tier_2	t	real
texture	chewy	Chewy	tier_2	t	real
texture	flaky	Flaky	tier_2	t	real
texture	smooth	Smooth	tier_2	t	real
texture	grainy	Grainy	tier_2	f	real
texture	crumbly	Crumbly	tier_2	f	real
texture	dense	Dense	tier_2	f	real
texture	fluffy	Fluffy	tier_2	t	real
texture	sticky	Sticky	tier_2	f	real
texture	layered	Layered	tier_2	t	real
richness	plain	Plain	tier_2	t	real
richness	light	Light	tier_2	t	real
richness	buttery	Buttery	tier_2	t	real
richness	creamy	Creamy	tier_2	t	real
richness	oily	Oily	tier_2	f	real
richness	ghee_rich	Ghee Rich	tier_2	t	real
richness	coconut_rich	Coconut Rich	tier_2	t	real
mouthfeel	silky	Silky	tier_3	f	real
mouthfeel	velvety	Velvety	tier_3	f	real
mouthfeel	mealy	Mealy	tier_3	f	real
mouthfeel	pasty	Pasty	tier_3	f	real
mouthfeel	waxy	Waxy	tier_3	f	real
mouthfeel	gritty	Gritty	tier_3	f	real
mouthfeel	juicy	Juicy	tier_3	t	real
mouthfeel	dry	Dry	tier_3	f	real
mouthfeel	moist	Moist	tier_3	f	real
mouthfeel	gelatinous	Gelatinous	tier_3	f	real
aroma_profile	smoky	Smoky	tier_3	t	real
aroma_profile	earthy	Earthy	tier_3	f	real
aroma_profile	floral	Floral	tier_3	f	real
aroma_profile	citrusy	Citrusy	tier_3	f	real
aroma_profile	herby	Herby	tier_3	f	real
aroma_profile	pungent	Pungent	tier_3	f	real
aroma_profile	mild	Mild	tier_3	f	real
aroma_profile	roasted_aroma	Roasted	tier_3	f	real
aroma_profile	fermented_aroma	Fermented	tier_3	f	real
aroma_profile	sweet_aroma	Sweet Aroma	tier_3	f	real
aroma_profile	nutty	Nutty	tier_3	f	real
fermentation	none	None	tier_3	f	real
fermentation	light	Light	tier_3	f	real
fermentation	medium	Medium	tier_3	f	real
fermentation	heavy	Heavy	tier_3	f	real
serving_temp	hot	Hot	tier_3	t	real
serving_temp	warm	Warm	tier_3	t	real
serving_temp	room_temp	Room Temperature	tier_3	t	real
serving_temp	chilled	Chilled	tier_3	t	real
serving_temp	frozen	Frozen	tier_3	t	real
weather_affinity	hot_weather	Hot Weather	tier_2	f	real
weather_affinity	cold_weather	Cold Weather	tier_2	f	real
weather_affinity	rainy	Rainy / Monsoon	tier_2	f	real
weather_affinity	all_weather	All Weather	tier_2	f	real
allergen	gluten	Gluten	tier_1	t	real
allergen	dairy	Dairy	tier_1	t	real
allergen	tree_nuts	Tree Nuts	tier_1	t	real
allergen	peanuts	Peanuts	tier_1	t	real
allergen	soy	Soy	tier_1	t	real
allergen	sesame	Sesame	tier_1	t	real
allergen	shellfish	Shellfish	tier_1	t	real
allergen	fish	Fish	tier_1	t	real
allergen	egg_allergen	Egg	tier_1	t	real
allergen	mustard	Mustard	tier_1	t	real
allergen	none	None	tier_1	t	real
\.


--
-- Data for Name: zone_map; Type: TABLE DATA; Schema: ghar_re; Owner: -
--

COPY ghar_re.zone_map (cuisine_group, zone, dish_count, data_source) FROM stdin;
north_indian	North	210	real
mughlai_nawabi	North	210	real
south_indian	South	141	real
west_indian	West	96	real
east_indian	East	68	real
central_indian	Central	22	real
northeast_indian	Northeast	31	real
street_food	PanIndia	55	real
chinese_asian	Global	187	real
continental	Global	187	real
italian	Global	187	real
\.


--
-- Name: allergen_hidden_derivatives allergen_hidden_derivatives_pkey; Type: CONSTRAINT; Schema: ghar_re; Owner: -
--

ALTER TABLE ONLY ghar_re.allergen_hidden_derivatives
    ADD CONSTRAINT allergen_hidden_derivatives_pkey PRIMARY KEY (id);


--
-- Name: comfort_hero_map comfort_hero_map_pkey; Type: CONSTRAINT; Schema: ghar_re; Owner: -
--

ALTER TABLE ONLY ghar_re.comfort_hero_map
    ADD CONSTRAINT comfort_hero_map_pkey PRIMARY KEY (id);


--
-- Name: comfort_hero_map comfort_hero_map_zone_weather_type_dish_name_key; Type: CONSTRAINT; Schema: ghar_re; Owner: -
--

ALTER TABLE ONLY ghar_re.comfort_hero_map
    ADD CONSTRAINT comfort_hero_map_zone_weather_type_dish_name_key UNIQUE (zone, weather_type, dish_name);


--
-- Name: community_priors community_priors_pkey; Type: CONSTRAINT; Schema: ghar_re; Owner: -
--

ALTER TABLE ONLY ghar_re.community_priors
    ADD CONSTRAINT community_priors_pkey PRIMARY KEY (state);


--
-- Name: cuisine_groups cuisine_groups_pkey; Type: CONSTRAINT; Schema: ghar_re; Owner: -
--

ALTER TABLE ONLY ghar_re.cuisine_groups
    ADD CONSTRAINT cuisine_groups_pkey PRIMARY KEY (name);


--
-- Name: cuisines cuisines_pkey; Type: CONSTRAINT; Schema: ghar_re; Owner: -
--

ALTER TABLE ONLY ghar_re.cuisines
    ADD CONSTRAINT cuisines_pkey PRIMARY KEY (name);


--
-- Name: dish_combo_items dish_combo_items_pkey; Type: CONSTRAINT; Schema: ghar_re; Owner: -
--

ALTER TABLE ONLY ghar_re.dish_combo_items
    ADD CONSTRAINT dish_combo_items_pkey PRIMARY KEY (combo_id, dish_name);


--
-- Name: dish_combos dish_combos_name_key; Type: CONSTRAINT; Schema: ghar_re; Owner: -
--

ALTER TABLE ONLY ghar_re.dish_combos
    ADD CONSTRAINT dish_combos_name_key UNIQUE (name);


--
-- Name: dish_combos dish_combos_pkey; Type: CONSTRAINT; Schema: ghar_re; Owner: -
--

ALTER TABLE ONLY ghar_re.dish_combos
    ADD CONSTRAINT dish_combos_pkey PRIMARY KEY (id);


--
-- Name: dish_ingredients dish_ingredients_pkey; Type: CONSTRAINT; Schema: ghar_re; Owner: -
--

ALTER TABLE ONLY ghar_re.dish_ingredients
    ADD CONSTRAINT dish_ingredients_pkey PRIMARY KEY (dish_id, ingredient_name);


--
-- Name: dish_macro dish_macro_pkey; Type: CONSTRAINT; Schema: ghar_re; Owner: -
--

ALTER TABLE ONLY ghar_re.dish_macro
    ADD CONSTRAINT dish_macro_pkey PRIMARY KEY (dish_id);


--
-- Name: dish_name_synonyms dish_name_synonyms_pkey; Type: CONSTRAINT; Schema: ghar_re; Owner: -
--

ALTER TABLE ONLY ghar_re.dish_name_synonyms
    ADD CONSTRAINT dish_name_synonyms_pkey PRIMARY KEY (dish_id, synonym);


--
-- Name: dish_name_synonyms dish_name_synonyms_real_needs_source; Type: CHECK CONSTRAINT; Schema: ghar_re; Owner: -
--

ALTER TABLE ghar_re.dish_name_synonyms
    ADD CONSTRAINT dish_name_synonyms_real_needs_source CHECK (((data_source <> 'real'::ghar_re.data_source_kind) OR (source_url IS NOT NULL))) NOT VALID;


--
-- Name: dish_variants dish_variants_from_dish_id_to_dish_id_variant_type_key; Type: CONSTRAINT; Schema: ghar_re; Owner: -
--

ALTER TABLE ONLY ghar_re.dish_variants
    ADD CONSTRAINT dish_variants_from_dish_id_to_dish_id_variant_type_key UNIQUE (from_dish_id, to_dish_id, variant_type);


--
-- Name: dish_variants dish_variants_pkey; Type: CONSTRAINT; Schema: ghar_re; Owner: -
--

ALTER TABLE ONLY ghar_re.dish_variants
    ADD CONSTRAINT dish_variants_pkey PRIMARY KEY (id);


--
-- Name: dishes dishes_name_key; Type: CONSTRAINT; Schema: ghar_re; Owner: -
--

ALTER TABLE ONLY ghar_re.dishes
    ADD CONSTRAINT dishes_name_key UNIQUE (name);


--
-- Name: dishes dishes_pkey; Type: CONSTRAINT; Schema: ghar_re; Owner: -
--

ALTER TABLE ONLY ghar_re.dishes
    ADD CONSTRAINT dishes_pkey PRIMARY KEY (id);


--
-- Name: feedback_event feedback_event_pkey; Type: CONSTRAINT; Schema: ghar_re; Owner: -
--

ALTER TABLE ONLY ghar_re.feedback_event
    ADD CONSTRAINT feedback_event_pkey PRIMARY KEY (id);


--
-- Name: household_context household_context_pkey; Type: CONSTRAINT; Schema: ghar_re; Owner: -
--

ALTER TABLE ONLY ghar_re.household_context
    ADD CONSTRAINT household_context_pkey PRIMARY KEY (id);


--
-- Name: household_modes household_modes_pkey; Type: CONSTRAINT; Schema: ghar_re; Owner: -
--

ALTER TABLE ONLY ghar_re.household_modes
    ADD CONSTRAINT household_modes_pkey PRIMARY KEY (household_id, mode);


--
-- Name: household_profile household_profile_pkey; Type: CONSTRAINT; Schema: ghar_re; Owner: -
--

ALTER TABLE ONLY ghar_re.household_profile
    ADD CONSTRAINT household_profile_pkey PRIMARY KEY (household_id, field_name);


--
-- Name: households households_pkey; Type: CONSTRAINT; Schema: ghar_re; Owner: -
--

ALTER TABLE ONLY ghar_re.households
    ADD CONSTRAINT households_pkey PRIMARY KEY (id);


--
-- Name: ingredient_aliases ingredient_aliases_pkey; Type: CONSTRAINT; Schema: ghar_re; Owner: -
--

ALTER TABLE ONLY ghar_re.ingredient_aliases
    ADD CONSTRAINT ingredient_aliases_pkey PRIMARY KEY (alias);


--
-- Name: ingredient_normalization_map ingredient_normalization_map_pkey; Type: CONSTRAINT; Schema: ghar_re; Owner: -
--

ALTER TABLE ONLY ghar_re.ingredient_normalization_map
    ADD CONSTRAINT ingredient_normalization_map_pkey PRIMARY KEY (id);


--
-- Name: ingredient_normalization_map ingredient_normalization_map_surface_token_norm_type_key; Type: CONSTRAINT; Schema: ghar_re; Owner: -
--

ALTER TABLE ONLY ghar_re.ingredient_normalization_map
    ADD CONSTRAINT ingredient_normalization_map_surface_token_norm_type_key UNIQUE (surface_token, norm_type);


--
-- Name: ingredients ingredients_pkey; Type: CONSTRAINT; Schema: ghar_re; Owner: -
--

ALTER TABLE ONLY ghar_re.ingredients
    ADD CONSTRAINT ingredients_pkey PRIMARY KEY (name);


--
-- Name: negative_priors negative_priors_pkey; Type: CONSTRAINT; Schema: ghar_re; Owner: -
--

ALTER TABLE ONLY ghar_re.negative_priors
    ADD CONSTRAINT negative_priors_pkey PRIMARY KEY (id);


--
-- Name: prior_zone_slot_season prior_zone_slot_season_pkey; Type: CONSTRAINT; Schema: ghar_re; Owner: -
--

ALTER TABLE ONLY ghar_re.prior_zone_slot_season
    ADD CONSTRAINT prior_zone_slot_season_pkey PRIMARY KEY (id);


--
-- Name: recommendation_event recommendation_event_pkey; Type: CONSTRAINT; Schema: ghar_re; Owner: -
--

ALTER TABLE ONLY ghar_re.recommendation_event
    ADD CONSTRAINT recommendation_event_pkey PRIMARY KEY (id);


--
-- Name: region_food_affinity region_food_affinity_pkey; Type: CONSTRAINT; Schema: ghar_re; Owner: -
--

ALTER TABLE ONLY ghar_re.region_food_affinity
    ADD CONSTRAINT region_food_affinity_pkey PRIMARY KEY (state_code, dish_name);


--
-- Name: sig_score_bands sig_score_bands_band_name_key; Type: CONSTRAINT; Schema: ghar_re; Owner: -
--

ALTER TABLE ONLY ghar_re.sig_score_bands
    ADD CONSTRAINT sig_score_bands_band_name_key UNIQUE (band_name);


--
-- Name: sig_score_bands sig_score_bands_pkey; Type: CONSTRAINT; Schema: ghar_re; Owner: -
--

ALTER TABLE ONLY ghar_re.sig_score_bands
    ADD CONSTRAINT sig_score_bands_pkey PRIMARY KEY (score);


--
-- Name: sig_scores sig_scores_pkey; Type: CONSTRAINT; Schema: ghar_re; Owner: -
--

ALTER TABLE ONLY ghar_re.sig_scores
    ADD CONSTRAINT sig_scores_pkey PRIMARY KEY (dish_id);


--
-- Name: tags tags_pkey; Type: CONSTRAINT; Schema: ghar_re; Owner: -
--

ALTER TABLE ONLY ghar_re.tags
    ADD CONSTRAINT tags_pkey PRIMARY KEY (category, value);


--
-- Name: zone_map zone_map_pkey; Type: CONSTRAINT; Schema: ghar_re; Owner: -
--

ALTER TABLE ONLY ghar_re.zone_map
    ADD CONSTRAINT zone_map_pkey PRIMARY KEY (cuisine_group);


--
-- Name: idx_dish_name_synonyms_region; Type: INDEX; Schema: ghar_re; Owner: -
--

CREATE INDEX idx_dish_name_synonyms_region ON ghar_re.dish_name_synonyms USING btree (region);


--
-- Name: idx_ghar_comfort_zone_weather; Type: INDEX; Schema: ghar_re; Owner: -
--

CREATE INDEX idx_ghar_comfort_zone_weather ON ghar_re.comfort_hero_map USING btree (zone, weather_type);


--
-- Name: idx_ghar_context_household; Type: INDEX; Schema: ghar_re; Owner: -
--

CREATE INDEX idx_ghar_context_household ON ghar_re.household_context USING btree (household_id, created_at);


--
-- Name: idx_ghar_feedback_hh; Type: INDEX; Schema: ghar_re; Owner: -
--

CREATE INDEX idx_ghar_feedback_hh ON ghar_re.feedback_event USING btree (household_id, created_at);


--
-- Name: idx_ghar_hh_profile_field; Type: INDEX; Schema: ghar_re; Owner: -
--

CREATE INDEX idx_ghar_hh_profile_field ON ghar_re.household_profile USING btree (field_name);


--
-- Name: idx_ghar_prior_zone_slot; Type: INDEX; Schema: ghar_re; Owner: -
--

CREATE INDEX idx_ghar_prior_zone_slot ON ghar_re.prior_zone_slot_season USING btree (zone, slot);


--
-- Name: idx_ghar_recevent_hh; Type: INDEX; Schema: ghar_re; Owner: -
--

CREATE INDEX idx_ghar_recevent_hh ON ghar_re.recommendation_event USING btree (household_id, created_at);


--
-- Name: idx_ghar_variants_from; Type: INDEX; Schema: ghar_re; Owner: -
--

CREATE INDEX idx_ghar_variants_from ON ghar_re.dish_variants USING btree (from_dish_id);


--
-- Name: comfort_hero_map comfort_hero_map_dish_id_fkey; Type: FK CONSTRAINT; Schema: ghar_re; Owner: -
--

ALTER TABLE ONLY ghar_re.comfort_hero_map
    ADD CONSTRAINT comfort_hero_map_dish_id_fkey FOREIGN KEY (dish_id) REFERENCES ghar_re.dishes(id);


--
-- Name: cuisines cuisines_cuisine_group_fkey; Type: FK CONSTRAINT; Schema: ghar_re; Owner: -
--

ALTER TABLE ONLY ghar_re.cuisines
    ADD CONSTRAINT cuisines_cuisine_group_fkey FOREIGN KEY (cuisine_group) REFERENCES ghar_re.cuisine_groups(name);


--
-- Name: cuisines cuisines_parent_cuisine_fkey; Type: FK CONSTRAINT; Schema: ghar_re; Owner: -
--

ALTER TABLE ONLY ghar_re.cuisines
    ADD CONSTRAINT cuisines_parent_cuisine_fkey FOREIGN KEY (parent_cuisine) REFERENCES ghar_re.cuisines(name);


--
-- Name: dish_combo_items dish_combo_items_combo_id_fkey; Type: FK CONSTRAINT; Schema: ghar_re; Owner: -
--

ALTER TABLE ONLY ghar_re.dish_combo_items
    ADD CONSTRAINT dish_combo_items_combo_id_fkey FOREIGN KEY (combo_id) REFERENCES ghar_re.dish_combos(id) ON DELETE CASCADE;


--
-- Name: dish_combo_items dish_combo_items_dish_id_fkey; Type: FK CONSTRAINT; Schema: ghar_re; Owner: -
--

ALTER TABLE ONLY ghar_re.dish_combo_items
    ADD CONSTRAINT dish_combo_items_dish_id_fkey FOREIGN KEY (dish_id) REFERENCES ghar_re.dishes(id);


--
-- Name: dish_ingredients dish_ingredients_dish_id_fkey; Type: FK CONSTRAINT; Schema: ghar_re; Owner: -
--

ALTER TABLE ONLY ghar_re.dish_ingredients
    ADD CONSTRAINT dish_ingredients_dish_id_fkey FOREIGN KEY (dish_id) REFERENCES ghar_re.dishes(id) ON DELETE CASCADE;


--
-- Name: dish_ingredients dish_ingredients_ingredient_name_fkey; Type: FK CONSTRAINT; Schema: ghar_re; Owner: -
--

ALTER TABLE ONLY ghar_re.dish_ingredients
    ADD CONSTRAINT dish_ingredients_ingredient_name_fkey FOREIGN KEY (ingredient_name) REFERENCES ghar_re.ingredients(name);


--
-- Name: dish_macro dish_macro_dish_id_fkey; Type: FK CONSTRAINT; Schema: ghar_re; Owner: -
--

ALTER TABLE ONLY ghar_re.dish_macro
    ADD CONSTRAINT dish_macro_dish_id_fkey FOREIGN KEY (dish_id) REFERENCES ghar_re.dishes(id) ON DELETE CASCADE;


--
-- Name: dish_name_synonyms dish_name_synonyms_dish_id_fkey; Type: FK CONSTRAINT; Schema: ghar_re; Owner: -
--

ALTER TABLE ONLY ghar_re.dish_name_synonyms
    ADD CONSTRAINT dish_name_synonyms_dish_id_fkey FOREIGN KEY (dish_id) REFERENCES ghar_re.dishes(id) ON DELETE CASCADE;


--
-- Name: dish_variants dish_variants_from_dish_id_fkey; Type: FK CONSTRAINT; Schema: ghar_re; Owner: -
--

ALTER TABLE ONLY ghar_re.dish_variants
    ADD CONSTRAINT dish_variants_from_dish_id_fkey FOREIGN KEY (from_dish_id) REFERENCES ghar_re.dishes(id) ON DELETE CASCADE;


--
-- Name: dish_variants dish_variants_to_dish_id_fkey; Type: FK CONSTRAINT; Schema: ghar_re; Owner: -
--

ALTER TABLE ONLY ghar_re.dish_variants
    ADD CONSTRAINT dish_variants_to_dish_id_fkey FOREIGN KEY (to_dish_id) REFERENCES ghar_re.dishes(id) ON DELETE CASCADE;


--
-- Name: dishes dishes_cuisine_fkey; Type: FK CONSTRAINT; Schema: ghar_re; Owner: -
--

ALTER TABLE ONLY ghar_re.dishes
    ADD CONSTRAINT dishes_cuisine_fkey FOREIGN KEY (cuisine) REFERENCES ghar_re.cuisines(name);


--
-- Name: feedback_event feedback_event_dish_id_fkey; Type: FK CONSTRAINT; Schema: ghar_re; Owner: -
--

ALTER TABLE ONLY ghar_re.feedback_event
    ADD CONSTRAINT feedback_event_dish_id_fkey FOREIGN KEY (dish_id) REFERENCES ghar_re.dishes(id);


--
-- Name: feedback_event feedback_event_household_id_fkey; Type: FK CONSTRAINT; Schema: ghar_re; Owner: -
--

ALTER TABLE ONLY ghar_re.feedback_event
    ADD CONSTRAINT feedback_event_household_id_fkey FOREIGN KEY (household_id) REFERENCES ghar_re.households(id) ON DELETE CASCADE;


--
-- Name: household_context household_context_household_id_fkey; Type: FK CONSTRAINT; Schema: ghar_re; Owner: -
--

ALTER TABLE ONLY ghar_re.household_context
    ADD CONSTRAINT household_context_household_id_fkey FOREIGN KEY (household_id) REFERENCES ghar_re.households(id) ON DELETE CASCADE;


--
-- Name: household_modes household_modes_household_id_fkey; Type: FK CONSTRAINT; Schema: ghar_re; Owner: -
--

ALTER TABLE ONLY ghar_re.household_modes
    ADD CONSTRAINT household_modes_household_id_fkey FOREIGN KEY (household_id) REFERENCES ghar_re.households(id) ON DELETE CASCADE;


--
-- Name: household_profile household_profile_household_id_fkey; Type: FK CONSTRAINT; Schema: ghar_re; Owner: -
--

ALTER TABLE ONLY ghar_re.household_profile
    ADD CONSTRAINT household_profile_household_id_fkey FOREIGN KEY (household_id) REFERENCES ghar_re.households(id) ON DELETE CASCADE;


--
-- Name: ingredient_aliases ingredient_aliases_canonical_ingredient_fkey; Type: FK CONSTRAINT; Schema: ghar_re; Owner: -
--

ALTER TABLE ONLY ghar_re.ingredient_aliases
    ADD CONSTRAINT ingredient_aliases_canonical_ingredient_fkey FOREIGN KEY (canonical_ingredient) REFERENCES ghar_re.ingredients(name);


--
-- Name: recommendation_event recommendation_event_household_id_fkey; Type: FK CONSTRAINT; Schema: ghar_re; Owner: -
--

ALTER TABLE ONLY ghar_re.recommendation_event
    ADD CONSTRAINT recommendation_event_household_id_fkey FOREIGN KEY (household_id) REFERENCES ghar_re.households(id) ON DELETE CASCADE;


--
-- Name: sig_scores sig_scores_dish_id_fkey; Type: FK CONSTRAINT; Schema: ghar_re; Owner: -
--

ALTER TABLE ONLY ghar_re.sig_scores
    ADD CONSTRAINT sig_scores_dish_id_fkey FOREIGN KEY (dish_id) REFERENCES ghar_re.dishes(id) ON DELETE CASCADE;


--
-- Name: allergen_hidden_derivatives; Type: ROW SECURITY; Schema: ghar_re; Owner: -
--

ALTER TABLE ghar_re.allergen_hidden_derivatives ENABLE ROW LEVEL SECURITY;

--
-- Name: comfort_hero_map; Type: ROW SECURITY; Schema: ghar_re; Owner: -
--

ALTER TABLE ghar_re.comfort_hero_map ENABLE ROW LEVEL SECURITY;

--
-- Name: community_priors; Type: ROW SECURITY; Schema: ghar_re; Owner: -
--

ALTER TABLE ghar_re.community_priors ENABLE ROW LEVEL SECURITY;

--
-- Name: cuisine_groups; Type: ROW SECURITY; Schema: ghar_re; Owner: -
--

ALTER TABLE ghar_re.cuisine_groups ENABLE ROW LEVEL SECURITY;

--
-- Name: cuisines; Type: ROW SECURITY; Schema: ghar_re; Owner: -
--

ALTER TABLE ghar_re.cuisines ENABLE ROW LEVEL SECURITY;

--
-- Name: dish_combo_items; Type: ROW SECURITY; Schema: ghar_re; Owner: -
--

ALTER TABLE ghar_re.dish_combo_items ENABLE ROW LEVEL SECURITY;

--
-- Name: dish_combos; Type: ROW SECURITY; Schema: ghar_re; Owner: -
--

ALTER TABLE ghar_re.dish_combos ENABLE ROW LEVEL SECURITY;

--
-- Name: dish_ingredients; Type: ROW SECURITY; Schema: ghar_re; Owner: -
--

ALTER TABLE ghar_re.dish_ingredients ENABLE ROW LEVEL SECURITY;

--
-- Name: dish_macro; Type: ROW SECURITY; Schema: ghar_re; Owner: -
--

ALTER TABLE ghar_re.dish_macro ENABLE ROW LEVEL SECURITY;

--
-- Name: dish_name_synonyms; Type: ROW SECURITY; Schema: ghar_re; Owner: -
--

ALTER TABLE ghar_re.dish_name_synonyms ENABLE ROW LEVEL SECURITY;

--
-- Name: dish_variants; Type: ROW SECURITY; Schema: ghar_re; Owner: -
--

ALTER TABLE ghar_re.dish_variants ENABLE ROW LEVEL SECURITY;

--
-- Name: dishes; Type: ROW SECURITY; Schema: ghar_re; Owner: -
--

ALTER TABLE ghar_re.dishes ENABLE ROW LEVEL SECURITY;

--
-- Name: feedback_event; Type: ROW SECURITY; Schema: ghar_re; Owner: -
--

ALTER TABLE ghar_re.feedback_event ENABLE ROW LEVEL SECURITY;

--
-- Name: household_context; Type: ROW SECURITY; Schema: ghar_re; Owner: -
--

ALTER TABLE ghar_re.household_context ENABLE ROW LEVEL SECURITY;

--
-- Name: household_modes; Type: ROW SECURITY; Schema: ghar_re; Owner: -
--

ALTER TABLE ghar_re.household_modes ENABLE ROW LEVEL SECURITY;

--
-- Name: household_profile; Type: ROW SECURITY; Schema: ghar_re; Owner: -
--

ALTER TABLE ghar_re.household_profile ENABLE ROW LEVEL SECURITY;

--
-- Name: households; Type: ROW SECURITY; Schema: ghar_re; Owner: -
--

ALTER TABLE ghar_re.households ENABLE ROW LEVEL SECURITY;

--
-- Name: ingredient_aliases; Type: ROW SECURITY; Schema: ghar_re; Owner: -
--

ALTER TABLE ghar_re.ingredient_aliases ENABLE ROW LEVEL SECURITY;

--
-- Name: ingredient_normalization_map; Type: ROW SECURITY; Schema: ghar_re; Owner: -
--

ALTER TABLE ghar_re.ingredient_normalization_map ENABLE ROW LEVEL SECURITY;

--
-- Name: ingredients; Type: ROW SECURITY; Schema: ghar_re; Owner: -
--

ALTER TABLE ghar_re.ingredients ENABLE ROW LEVEL SECURITY;

--
-- Name: negative_priors; Type: ROW SECURITY; Schema: ghar_re; Owner: -
--

ALTER TABLE ghar_re.negative_priors ENABLE ROW LEVEL SECURITY;

--
-- Name: prior_zone_slot_season; Type: ROW SECURITY; Schema: ghar_re; Owner: -
--

ALTER TABLE ghar_re.prior_zone_slot_season ENABLE ROW LEVEL SECURITY;

--
-- Name: recommendation_event; Type: ROW SECURITY; Schema: ghar_re; Owner: -
--

ALTER TABLE ghar_re.recommendation_event ENABLE ROW LEVEL SECURITY;

--
-- Name: region_food_affinity; Type: ROW SECURITY; Schema: ghar_re; Owner: -
--

ALTER TABLE ghar_re.region_food_affinity ENABLE ROW LEVEL SECURITY;

--
-- Name: sig_score_bands; Type: ROW SECURITY; Schema: ghar_re; Owner: -
--

ALTER TABLE ghar_re.sig_score_bands ENABLE ROW LEVEL SECURITY;

--
-- Name: sig_scores; Type: ROW SECURITY; Schema: ghar_re; Owner: -
--

ALTER TABLE ghar_re.sig_scores ENABLE ROW LEVEL SECURITY;

--
-- Name: tags; Type: ROW SECURITY; Schema: ghar_re; Owner: -
--

ALTER TABLE ghar_re.tags ENABLE ROW LEVEL SECURITY;

--
-- Name: zone_map; Type: ROW SECURITY; Schema: ghar_re; Owner: -
--

ALTER TABLE ghar_re.zone_map ENABLE ROW LEVEL SECURITY;

--
-- PostgreSQL database dump complete
--

\unrestrict zeRfS9TWhqOqTIeIon9Ijh2FrSaq6P3l8tiNqcvRvkom2m7YPdTgTZPDSmUyv1e

