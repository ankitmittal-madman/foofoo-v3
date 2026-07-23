"""
ghar_re.fixtures — GOLDEN SAMPLE dataset (invented, clearly flagged).

Every row here is data_source='ai_generated' (a couple 'stub' where deliberately low-confidence).
NONE is 'real' — this is invented data (Task 2 rule + the Task-4 integrity assertion). The real
810-dish catalogue (dishes.xlsx) is NOT touched or referenced.

Ingredient references ARE real tokens from data/source/ingredients_v5.csv so the dish_ingredients
join resolves and the ING/allergen/jain derivations work.

Several dishes are named, BY NAME, after actual KB §R3 comfort heroes (Pakora=North rain,
Kanda Bhaji=West-MH rain, Curd Rice=South summer, Sarson Ka Saag=North winter, Khichuri=East-WB
rain, Undhiyu=West-GJ winter, Rasam/Medu Vada=South-TN rain, Pithla=West-MH winter) so the
weather×KB-§R3 test is traceable to ground truth.
"""

AI = "ai_generated"

# Cuisine → cuisine_group (real cuisines from cuisines_v4.csv; groups from cuisine_groups_v4).
CUISINES = [
    # name, display_name, group, parent, state_origin, tier
    ("punjabi",       "Punjabi",       "north_indian", None,    "Punjab",      "tier_1"),
    ("delhi",         "Delhi",         "north_indian", None,    "Delhi",       "tier_1"),
    ("up",            "UP (General)",  "north_indian", None,    "Uttar Pradesh","tier_1"),
    ("tamil",         "Tamil",         "south_indian", None,    "Tamil Nadu",  "tier_1"),
    ("chettinad",     "Chettinad",     "south_indian", "tamil", "Tamil Nadu",  "tier_2"),
    ("udupi",         "Udupi",         "south_indian", None,    "Karnataka",   "tier_1"),
    ("maharashtrian", "Maharashtrian", "west_indian",  None,    "Maharashtra", "tier_1"),
    ("gujarati",      "Gujarati",      "west_indian",  None,    "Gujarat",     "tier_1"),
    ("bengali",       "Bengali",       "east_indian",  None,    "West Bengal", "tier_1"),
    ("mughlai",       "Mughlai",       "mughlai_nawabi", None,  "Delhi",       "tier_1"),
]

def _dish(name, cuisine, diet, hero_role, sig_band, spice, heaviness, meal_type,
          dish_category, cooking_method, richness, texture, weather_affinity,
          jain, scope_tier, ingredients, macro, sweetness=0, farali=False,
          primary_taste=("savoury",), mouthfeel=("moist",), aroma=("mild",),
          fermentation="none", serving_temp="hot", difficulty="medium",
          calories=None, prep=15, cook=25, alt_names=None, synonyms=None):
    cal = calories if calories is not None else macro["calories"]
    return dict(
        name=name, cuisine=cuisine, diet=diet, hero_role=hero_role, sig_band=sig_band,
        spice_level=spice, sweetness=sweetness, heaviness=heaviness,
        difficulty=difficulty, prep_mins=prep, cook_mins=cook, total_mins=prep + cook,
        calories=cal, serving_size="1 plate",
        meal_type=list(meal_type), dish_category=list(dish_category),
        cooking_method=list(cooking_method), primary_taste=list(primary_taste),
        texture=list(texture), richness=list(richness), mouthfeel=list(mouthfeel),
        aroma_profile=list(aroma), fermentation=fermentation, serving_temp=serving_temp,
        weather_affinity=list(weather_affinity), jain_compatible=jain,
        scope_tier=scope_tier, farali_compatible=farali,
        alternate_names=list(alt_names) if alt_names else [],
        synonyms=list(synonyms) if synonyms else [],
        ingredients=ingredients,          # [(ingredient_name, is_main)]
        macro=macro,
    )

def _m(cal, protein, fibre, fat, carbs, sugar, sodium):
    return dict(calories=cal, protein_g=protein, fibre_g=fibre, fat_g=fat,
                carbs_g=carbs, sugar_g=sugar, sodium_mg=sodium)

# ---------------------------------------------------------------------------
# GOLDEN DISHES  (~30, spanning North / South / West / East)
# ---------------------------------------------------------------------------
DISHES = [
    # ===================== NORTH =====================
    # KB §R3 North RAIN hero ✓
    _dish("Onion Pakora", "punjabi", "veg", "dry", "very_common", spice=2, heaviness=2,
          meal_type=("snacks","dinner"), dish_category=("snack_starter",),
          cooking_method=("deep_fried",), richness=("oily",), texture=("crispy","crunchy"),
          weather_affinity=("rainy",), jain="N", scope_tier="indian_core",
          aroma=("roasted_aroma",), mouthfeel=("dry",),
          ingredients=[("onion",True),("gram_flour",True),("green_chilli",False),
                       ("turmeric",False),("ajwain",False),("salt",False),("vegetable_oil",False)],
          macro=_m(320, 7, 4, 20, 30, 3, 480)),
    # KB §R3 North WINTER hero ✓ ; state_icon
    _dish("Sarson Ka Saag", "punjabi", "veg", "liquid", "state_icon", spice=2, heaviness=3,
          meal_type=("lunch","dinner"), dish_category=("dry_sabzi","curry"),
          cooking_method=("pressure_cooked","sauteed"), richness=("ghee_rich",),
          texture=("smooth",), weather_affinity=("cold_weather",), jain="N",
          scope_tier="indian_core", aroma=("earthy","pungent"), mouthfeel=("pasty",),
          ingredients=[("mustard_greens",True),("spinach",True),("ginger",False),
                       ("garlic",False),("green_chilli",False),("cornmeal",False),
                       ("ghee",False),("salt",False)],
          macro=_m(280, 9, 8, 16, 22, 4, 520)),
    _dish("Dal Tadka", "punjabi", "veg", "liquid", "common", spice=2, heaviness=2,
          meal_type=("lunch","dinner"), dish_category=("dal_lentil",),
          cooking_method=("pressure_cooked","tempered"), richness=("light",),
          texture=("smooth",), weather_affinity=("all_weather",), jain="N",
          scope_tier="indian_core", aroma=("earthy",),
          ingredients=[("toor_dal",True),("onion",False),("tomato",False),("garlic",False),
                       ("cumin_seeds",False),("turmeric",False),("ghee",False),("salt",False)],
          macro=_m(220, 12, 6, 7, 28, 3, 430)),
    _dish("Rajma", "punjabi", "veg", "liquid", "very_common", spice=2, heaviness=3,
          meal_type=("lunch","dinner"), dish_category=("dal_lentil","curry"),
          cooking_method=("pressure_cooked","sauteed"), richness=("light",),
          texture=("smooth",), weather_affinity=("all_weather","cold_weather"), jain="N",
          scope_tier="indian_core", aroma=("earthy",),
          ingredients=[("kidney_beans",True),("onion",False),("tomato",False),("ginger",False),
                       ("garlic",False),("garam_masala",False),("red_chilli_powder",False),("salt",False)],
          macro=_m(300, 14, 11, 8, 42, 5, 500)),
    _dish("Aloo Gobi", "up", "veg", "dry", "common", spice=2, heaviness=2,
          meal_type=("lunch","dinner"), dish_category=("dry_sabzi",),
          cooking_method=("sauteed",), richness=("light",), texture=("soft",),
          weather_affinity=("all_weather",), jain="N", scope_tier="indian_core",
          aroma=("earthy",), mouthfeel=("dry",),
          ingredients=[("potato",True),("cauliflower",True),("onion",False),("tomato",False),
                       ("turmeric",False),("cumin_seeds",False),("green_chilli",False),("salt",False)],
          macro=_m(210, 5, 6, 10, 26, 4, 400)),
    _dish("Punjabi Kadhi Pakora", "punjabi", "veg", "liquid", "very_common", spice=2, heaviness=3,
          meal_type=("lunch","dinner"), dish_category=("curry",),
          cooking_method=("sauteed","tempered"), richness=("creamy",), texture=("smooth",),
          weather_affinity=("all_weather","rainy"), jain="N", scope_tier="indian_core",
          primary_taste=("tangy","savoury"), aroma=("pungent",),
          ingredients=[("curd",True),("gram_flour",True),("onion",False),("garlic",False),
                       ("turmeric",False),("fenugreek_seeds",False),("dry_red_chilli",False),("salt",False)],
          macro=_m(330, 9, 3, 18, 34, 6, 560)),
    _dish("Chole", "delhi", "veg", "liquid", "very_common", spice=3, heaviness=3,
          meal_type=("lunch","dinner"), dish_category=("curry","dal_lentil"),
          cooking_method=("pressure_cooked","sauteed"), richness=("light",),
          texture=("smooth",), weather_affinity=("all_weather",), jain="N",
          scope_tier="indian_core", primary_taste=("spicy_hot","tangy"), aroma=("pungent",),
          ingredients=[("chickpeas",True),("onion",False),("tomato",False),("ginger",False),
                       ("garlic",False),("chaat_masala",False),("amchur",False),("salt",False)],
          macro=_m(340, 13, 12, 9, 50, 6, 620)),
    # rich → SINGLE (leaves the liquid-pairing pool per §S4)
    _dish("Paneer Butter Masala", "punjabi", "veg", "single", "regional_hero", spice=1, heaviness=3,
          meal_type=("lunch","dinner"), dish_category=("curry",),
          cooking_method=("sauteed",), richness=("creamy","buttery"), texture=("smooth",),
          weather_affinity=("all_weather",), jain="N", scope_tier="indian_core",
          sweetness=1, mouthfeel=("velvety",), aroma=("roasted_aroma",),
          ingredients=[("paneer",True),("tomato",True),("butter",False),("cream",False),
                       ("onion",False),("garlic",False),("garam_masala",False),("kasuri_methi",False),("salt",False)],
          macro=_m(450, 15, 3, 30, 26, 8, 640)),
    # standalone bypass
    _dish("Veg Biryani", "mughlai", "veg", "standalone", "regional_hero", spice=3, heaviness=3,
          meal_type=("lunch","dinner"), dish_category=("biryani_pulao",),
          cooking_method=("dum_cooked",), richness=("ghee_rich",), texture=("grainy","fluffy"),
          weather_affinity=("all_weather",), jain="N", scope_tier="indian_core",
          aroma=("roasted_aroma","floral"),
          ingredients=[("rice_basmati",True),("carrot",False),("green_peas",False),("potato",False),
                       ("onion",False),("garlic",False),("garam_masala",False),("saffron",False),("ghee",False),("salt",False)],
          macro=_m(480, 10, 6, 16, 72, 6, 700)),
    # standalone + JAIN-COMPATIBLE + weaning-safe
    _dish("Moong Dal Khichdi", "up", "veg", "standalone", "common", spice=1, heaviness=2,
          meal_type=("lunch","dinner"), dish_category=("whole_meal",),
          cooking_method=("pressure_cooked","tempered"), richness=("light",),
          texture=("soft","sticky"), weather_affinity=("rainy","cold_weather","all_weather"),
          jain="Y", scope_tier="indian_core", mouthfeel=("moist",), aroma=("mild",),
          ingredients=[("rice_regular",True),("moong_dal",True),("cumin_seeds",False),
                       ("turmeric",False),("ghee",False),("salt",False)],
          macro=_m(280, 10, 5, 6, 48, 2, 360)),

    # ===================== SOUTH =====================
    # national_icon 1.0, standalone
    _dish("Masala Dosa", "udupi", "veg", "standalone", "national_icon", spice=2, heaviness=2,
          meal_type=("breakfast","dinner"), dish_category=("dosa_idli",),
          cooking_method=("shallow_fried","fermented_cook"), richness=("light",),
          texture=("crispy",), weather_affinity=("all_weather",), jain="N",
          scope_tier="indian_core", fermentation="heavy", aroma=("fermented_aroma",),
          mouthfeel=("dry",),
          ingredients=[("rice_regular",True),("urad_dal",True),("potato",True),("onion",False),
                       ("mustard_seeds",False),("curry_powder",False),("turmeric",False),("salt",False)],
          macro=_m(360, 8, 4, 12, 56, 2, 480)),
    # JAIN-COMPATIBLE + weaning-safe (spice 0, soft/fluffy)
    _dish("Idli", "udupi", "veg", "dry", "very_common", spice=0, heaviness=1,
          meal_type=("breakfast","dinner"), dish_category=("dosa_idli",),
          cooking_method=("steamed","fermented_cook"), richness=("plain",),
          texture=("soft","fluffy"), weather_affinity=("all_weather",), jain="Y",
          scope_tier="indian_core", fermentation="heavy", aroma=("fermented_aroma",),
          mouthfeel=("moist",), primary_taste=("savoury","sour"),
          ingredients=[("rice_regular",True),("urad_dal",True),("idli_rava",False),("salt",False)],
          macro=_m(150, 5, 2, 1, 30, 1, 300)),
    _dish("Sambar", "tamil", "veg", "liquid", "very_common", spice=2, heaviness=2,
          meal_type=("breakfast","lunch","dinner"), dish_category=("dal_lentil","curry"),
          cooking_method=("pressure_cooked","tempered"), richness=("light",),
          texture=("smooth",), weather_affinity=("all_weather",), jain="N",
          scope_tier="indian_core", primary_taste=("tangy","savoury"), aroma=("pungent",),
          ingredients=[("toor_dal",True),("drumstick",False),("onion",False),("tomato",False),
                       ("tamarind",False),("sambar_powder",False),("mustard_seeds",False),("salt",False)],
          macro=_m(190, 9, 6, 5, 28, 4, 520)),
    # KB §R3 South-TN RAIN hero ✓ (Rasam-Rice)
    _dish("Rasam", "tamil", "veg", "liquid", "very_common", spice=2, heaviness=1,
          meal_type=("lunch","dinner"), dish_category=("soup","curry"),
          cooking_method=("boiled","tempered"), richness=("light",), texture=("smooth",),
          weather_affinity=("rainy","all_weather"), jain="N", scope_tier="indian_core",
          primary_taste=("tangy","spicy_hot"), aroma=("pungent","citrusy"),
          ingredients=[("tamarind",True),("tomato",False),("toor_dal",False),("black_pepper",False),
                       ("garlic",False),("curry_powder",False),("mustard_seeds",False),("salt",False)],
          macro=_m(90, 4, 2, 3, 12, 3, 440)),
    # KB §R3 South SUMMER hero ✓ ; single complete; JAIN-COMPATIBLE + weaning-safe
    _dish("Curd Rice", "tamil", "veg", "single", "very_common", spice=0, heaviness=2,
          meal_type=("lunch","dinner"), dish_category=("whole_meal","rice"),
          cooking_method=("boiled","tempered"), richness=("light",),
          texture=("soft","sticky"), weather_affinity=("hot_weather",), jain="Y",
          scope_tier="indian_core", serving_temp="chilled", primary_taste=("sour","savoury"),
          mouthfeel=("moist",), aroma=("mild",),
          ingredients=[("rice_regular",True),("curd",True),("mustard_seeds",False),
                       ("green_chilli",False),("curry_powder",False),("salt",False)],
          macro=_m(260, 7, 2, 6, 44, 4, 380)),
    # KB §R3 South-TN RAIN hero ✓ (Medu Vada)
    _dish("Medu Vada", "tamil", "veg", "dry", "very_common", spice=2, heaviness=2,
          meal_type=("breakfast","snacks","dinner"), dish_category=("snack_starter",),
          cooking_method=("deep_fried",), richness=("oily",), texture=("crispy","fluffy"),
          weather_affinity=("rainy",), jain="N", scope_tier="indian_core",
          aroma=("roasted_aroma",), mouthfeel=("dry",),
          ingredients=[("urad_dal",True),("black_pepper",False),("green_chilli",False),
                       ("curry_powder",False),("ginger",False),("salt",False),("vegetable_oil",False)],
          macro=_m(300, 10, 3, 16, 30, 1, 460)),
    # high-spice NON_VEG (veg-filter + spice-ceiling test)
    _dish("Chettinad Chicken", "chettinad", "non_veg", "single", "regional_hero", spice=4, heaviness=3,
          meal_type=("lunch","dinner"), dish_category=("curry",),
          cooking_method=("sauteed",), richness=("oily",), texture=("smooth",),
          weather_affinity=("all_weather",), jain="N", scope_tier="indian_core",
          primary_taste=("spicy_hot","savoury"), aroma=("roasted_aroma","pungent"),
          ingredients=[("chicken",True),("onion",False),("tomato",False),("garlic",False),
                       ("black_pepper",False),("dry_red_chilli",False),("coconut_fresh",False),("garam_masala",False),("salt",False)],
          macro=_m(420, 32, 3, 26, 12, 3, 680)),

    # ===================== WEST =====================
    # KB §R3 West-MH RAIN hero ✓ (Kanda Bhaji) — the West counterpart to North's Pakora
    _dish("Kanda Bhaji", "maharashtrian", "veg", "dry", "very_common", spice=2, heaviness=2,
          meal_type=("snacks","dinner"), dish_category=("snack_starter",),
          cooking_method=("deep_fried",), richness=("oily",), texture=("crispy","crunchy"),
          weather_affinity=("rainy",), jain="N", scope_tier="indian_core",
          aroma=("roasted_aroma",), mouthfeel=("dry",),
          ingredients=[("onion",True),("gram_flour",True),("green_chilli",False),
                       ("coriander_powder",False),("turmeric",False),("salt",False),("vegetable_oil",False)],
          macro=_m(310, 6, 4, 19, 30, 3, 470)),
    # KB §R3 West-MH WINTER hero ✓ (Pithla) ; liquid
    _dish("Pithla", "maharashtrian", "veg", "liquid", "common", spice=2, heaviness=2,
          meal_type=("lunch","dinner"), dish_category=("curry",),
          cooking_method=("sauteed","tempered"), richness=("light",), texture=("smooth",),
          weather_affinity=("rainy","cold_weather","all_weather"), jain="N",
          scope_tier="indian_core", aroma=("pungent",),
          ingredients=[("gram_flour",True),("onion",False),("garlic",False),("green_chilli",False),
                       ("mustard_seeds",False),("turmeric",False),("curry_powder",False),("salt",False)],
          macro=_m(200, 8, 3, 10, 22, 2, 420)),
    # KB §R3 West-GJ WINTER hero ✓ (Undhiyu) ; state_icon
    _dish("Undhiyu", "gujarati", "veg", "dry", "state_icon", spice=2, heaviness=3,
          meal_type=("lunch","dinner"), dish_category=("dry_sabzi",),
          cooking_method=("sauteed",), richness=("oily",), texture=("soft",),
          weather_affinity=("cold_weather",), jain="N", scope_tier="indian_core",
          sweetness=1, aroma=("earthy","herby"), mouthfeel=("dry",),
          ingredients=[("potato",True),("raw_banana",True),("val_dal",True),("eggplant",False),
                       ("green_peas",False),("coconut_fresh",False),("green_chilli",False),("jaggery",False),("salt",False)],
          macro=_m(360, 9, 10, 18, 40, 8, 520)),
    # JAIN-COMPATIBLE (no onion/garlic Gujarati kadhi) ; sweet-lean
    _dish("Gujarati Kadhi", "gujarati", "veg", "liquid", "common", spice=1, heaviness=2,
          meal_type=("lunch","dinner"), dish_category=("curry",),
          cooking_method=("boiled","tempered"), richness=("light",), texture=("smooth",),
          weather_affinity=("all_weather",), jain="Y", scope_tier="indian_core",
          sweetness=2, primary_taste=("tangy","sweet"), aroma=("mild",),
          ingredients=[("curd",True),("gram_flour",True),("ginger",False),("green_chilli",False),
                       ("curry_powder",False),("jaggery",False),("cumin_seeds",False),("salt",False)],
          macro=_m(180, 6, 2, 8, 22, 9, 400)),

    # ===================== EAST =====================
    # regional_hero ; NON_VEG (fish) — eggetarian/veg filter tests
    _dish("Macher Jhol", "bengali", "non_veg", "liquid", "regional_hero", spice=2, heaviness=2,
          meal_type=("lunch","dinner"), dish_category=("curry",),
          cooking_method=("sauteed",), richness=("light",), texture=("smooth",),
          weather_affinity=("all_weather","rainy"), jain="N", scope_tier="indian_core",
          primary_taste=("savoury",), aroma=("pungent",),
          ingredients=[("rohu",True),("potato",False),("tomato",False),("panch_phoron",False),
                       ("turmeric",False),("mustard_seeds",False),("green_chilli",False),("salt",False)],
          macro=_m(260, 24, 2, 14, 12, 2, 560)),
    _dish("Cholar Dal", "bengali", "veg", "liquid", "common", spice=1, heaviness=2,
          meal_type=("lunch","dinner"), dish_category=("dal_lentil",),
          cooking_method=("pressure_cooked","tempered"), richness=("light",),
          texture=("smooth",), weather_affinity=("all_weather",), jain="N",
          scope_tier="indian_core", sweetness=1, aroma=("sweet_aroma",),
          ingredients=[("chana_dal",True),("coconut_fresh",False),("ginger",False),
                       ("cumin_seeds",False),("bay_leaf",False),("ghee",False),("jaggery",False),("salt",False)],
          macro=_m(240, 11, 8, 7, 34, 6, 380)),
    # KB §R3 East-WB RAIN hero ✓ (Khichuri) ; standalone
    _dish("Bhuna Khichuri", "bengali", "veg", "standalone", "very_common", spice=1, heaviness=3,
          meal_type=("lunch","dinner"), dish_category=("whole_meal",),
          cooking_method=("sauteed","pressure_cooked"), richness=("ghee_rich",),
          texture=("soft","sticky"), weather_affinity=("rainy","cold_weather"), jain="N",
          scope_tier="indian_core", aroma=("roasted_aroma",), mouthfeel=("moist",),
          ingredients=[("rice_regular",True),("moong_dal",True),("cauliflower",False),("potato",False),
                       ("ginger",False),("bay_leaf",False),("cumin_seeds",False),("ghee",False),("salt",False)],
          macro=_m(380, 12, 6, 12, 56, 3, 440)),
    _dish("Aloo Posto", "bengali", "veg", "dry", "regional_hero", spice=1, heaviness=2,
          meal_type=("lunch","dinner"), dish_category=("dry_sabzi",),
          cooking_method=("sauteed",), richness=("light",), texture=("soft",),
          weather_affinity=("all_weather",), jain="N", scope_tier="indian_core",
          aroma=("nutty",), mouthfeel=("dry",),
          ingredients=[("potato",True),("poppy_seeds",True),("green_chilli",False),
                       ("nigella_seeds",False),("mustard_seeds",False),("salt",False)],
          macro=_m(230, 5, 4, 12, 26, 2, 360)),

    # ===================== EGG + SUPPORTS =====================
    _dish("Egg Bhurji", "delhi", "egg", "dry", "common", spice=2, heaviness=2,
          meal_type=("breakfast","lunch","dinner"), dish_category=("egg_dish",),
          cooking_method=("sauteed",), richness=("light",), texture=("crumbly",),
          weather_affinity=("all_weather",), jain="N", scope_tier="indian_core",
          aroma=("pungent",), mouthfeel=("dry",),
          ingredients=[("egg",True),("onion",False),("tomato",False),("green_chilli",False),
                       ("turmeric",False),("red_chilli_powder",False),("salt",False)],
          macro=_m(240, 16, 1, 17, 6, 3, 420)),

    # ===================== JAIN-COMPATIBLE / WEANING-SAFE additions =====================
    # (added so the constrained golden households — Jain, weaning-present — can still form 7
    #  cuisine-coherent plates; realistic no-onion/no-garlic/no-root dishes, low-spice/soft.)
    _dish("Gujarati Toor Dal", "gujarati", "veg", "liquid", "common", spice=1, heaviness=2,
          meal_type=("lunch","dinner"), dish_category=("dal_lentil",),
          cooking_method=("pressure_cooked","tempered"), richness=("light",),
          texture=("smooth",), weather_affinity=("all_weather",), jain="Y",
          scope_tier="indian_core", sweetness=1, primary_taste=("sweet","tangy"), aroma=("mild",),
          ingredients=[("toor_dal",True),("jaggery",False),("ginger",False),("green_chilli",False),
                       ("turmeric",False),("curry_leaves",False),("salt",False)],
          macro=_m(200, 10, 5, 4, 32, 7, 360)),
    _dish("Moong Dal", "gujarati", "veg", "liquid", "common", spice=1, heaviness=1,
          meal_type=("lunch","dinner"), dish_category=("dal_lentil",),
          cooking_method=("pressure_cooked","tempered"), richness=("light",),
          texture=("smooth",), weather_affinity=("all_weather",), jain="Y",
          scope_tier="indian_core", aroma=("mild",),
          ingredients=[("moong_dal",True),("cumin_seeds",False),("turmeric",False),
                       ("ginger",False),("ghee",False),("salt",False)],
          macro=_m(180, 11, 4, 4, 26, 2, 320)),
    _dish("Cabbage Sabzi", "maharashtrian", "veg", "dry", "common", spice=1, heaviness=1,
          meal_type=("lunch","dinner"), dish_category=("dry_sabzi",),
          cooking_method=("sauteed","tempered"), richness=("light",), texture=("soft",),
          weather_affinity=("all_weather",), jain="Y", scope_tier="indian_core",
          aroma=("mild",), mouthfeel=("moist",),
          ingredients=[("cabbage",True),("green_peas",False),("mustard_seeds",False),
                       ("turmeric",False),("green_chilli",False),("curry_leaves",False),("salt",False)],
          macro=_m(120, 4, 5, 6, 16, 4, 300)),
    _dish("Pumpkin Sabzi", "gujarati", "veg", "dry", "common", spice=1, heaviness=1,
          meal_type=("lunch","dinner"), dish_category=("dry_sabzi",),
          cooking_method=("sauteed",), richness=("light",), texture=("soft",),
          weather_affinity=("all_weather",), jain="Y", scope_tier="indian_core",
          sweetness=1, primary_taste=("sweet","savoury"), aroma=("mild",), mouthfeel=("moist",),
          ingredients=[("pumpkin",True),("jaggery",False),("fenugreek_seeds",False),
                       ("dry_red_chilli",False),("turmeric",False),("salt",False)],
          macro=_m(140, 3, 4, 5, 24, 9, 280)),
    _dish("Dhokla", "gujarati", "veg", "dry", "very_common", spice=1, heaviness=1,
          meal_type=("breakfast","lunch","dinner","snacks"), dish_category=("snack_starter",),
          cooking_method=("steamed","fermented_cook"), richness=("light",),
          texture=("soft","fluffy"), weather_affinity=("all_weather",), jain="Y",
          scope_tier="indian_core", fermentation="medium", sweetness=1,
          primary_taste=("tangy","sweet"), aroma=("fermented_aroma",), mouthfeel=("moist",),
          ingredients=[("gram_flour",True),("green_chilli",False),("ginger",False),
                       ("mustard_seeds",False),("curry_leaves",False),("sesame_seeds",False),("salt",False)],
          macro=_m(160, 6, 3, 4, 26, 3, 340)),
    # KB §R3 South WINTER hero ✓ (Ven Pongal) ; jain-compatible single
    _dish("Ven Pongal", "tamil", "veg", "single", "very_common", spice=1, heaviness=2,
          meal_type=("breakfast","lunch","dinner"), dish_category=("whole_meal","rice"),
          cooking_method=("pressure_cooked","tempered"), richness=("ghee_rich",),
          texture=("soft","sticky"), weather_affinity=("cold_weather",), jain="Y",
          scope_tier="indian_core", aroma=("roasted_aroma",), mouthfeel=("moist",),
          ingredients=[("rice_regular",True),("moong_dal",True),("black_pepper",False),
                       ("cumin_seeds",False),("ginger",False),("ghee",False),("curry_leaves",False),("salt",False)],
          macro=_m(320, 10, 4, 12, 44, 1, 420)),
    _dish("Lauki Khichdi", "up", "veg", "standalone", "common", spice=1, heaviness=2,
          meal_type=("lunch","dinner"), dish_category=("whole_meal",),
          cooking_method=("pressure_cooked","tempered"), richness=("light",),
          texture=("soft","sticky"), weather_affinity=("all_weather","cold_weather"), jain="Y",
          scope_tier="indian_core", mouthfeel=("moist",), aroma=("mild",),
          ingredients=[("rice_regular",True),("moong_dal",True),("bottle_gourd",True),
                       ("cumin_seeds",False),("turmeric",False),("ghee",False),("salt",False)],
          macro=_m(260, 9, 5, 6, 44, 3, 340)),
    _dish("Lauki Sabzi", "up", "veg", "dry", "common", spice=1, heaviness=1,
          meal_type=("lunch","dinner"), dish_category=("dry_sabzi",),
          cooking_method=("sauteed",), richness=("light",), texture=("soft",),
          weather_affinity=("all_weather",), jain="Y", scope_tier="indian_core",
          aroma=("mild",), mouthfeel=("moist",),
          ingredients=[("bottle_gourd",True),("tomato",False),("cumin_seeds",False),
                       ("turmeric",False),("green_chilli",False),("salt",False)],
          macro=_m(110, 3, 4, 5, 16, 4, 280)),
    # farali (fasting-mode) coverage: sabudana khichdi is farali_compatible but NOT jain (potato=root)
    _dish("Sabudana Khichdi", "maharashtrian", "veg", "standalone", "very_common", spice=1, heaviness=2,
          meal_type=("breakfast","lunch","dinner"), dish_category=("whole_meal",),
          cooking_method=("sauteed",), richness=("oily",), texture=("soft","sticky"),
          weather_affinity=("all_weather",), jain="N", scope_tier="indian_core", farali=True,
          mouthfeel=("moist",), aroma=("nutty",),
          ingredients=[("tapioca",True),("potato",True),("cumin_seeds",False),
                       ("green_chilli",False),("ghee",False),("salt",False)],
          macro=_m(300, 4, 2, 10, 52, 1, 300)),

    # supports (hero_role='support'; not scored; carb-attach targets)
    _dish("Roti", "up", "veg", "support", "utility", spice=0, heaviness=1,
          meal_type=("breakfast","lunch","dinner"), dish_category=("paratha_roti","bread"),
          cooking_method=("roasted",), richness=("plain",), texture=("soft","layered"),
          weather_affinity=("all_weather",), jain="Y", scope_tier="indian_core",
          mouthfeel=("dry",), aroma=("mild",), prep=10, cook=10,
          ingredients=[("wheat_flour",True),("salt",False)],
          macro=_m(120, 3, 2, 3, 20, 0, 180)),
    _dish("Steamed Rice", "tamil", "veg", "support", "utility", spice=0, heaviness=1,
          meal_type=("breakfast","lunch","dinner"), dish_category=("rice",),
          cooking_method=("boiled",), richness=("plain",), texture=("soft","grainy"),
          weather_affinity=("all_weather",), jain="Y", scope_tier="indian_core",
          mouthfeel=("moist",), aroma=("mild",), prep=5, cook=15,
          ingredients=[("rice_regular",True),("salt",False)],
          macro=_m(200, 4, 1, 0, 45, 0, 5)),
    _dish("Poori", "up", "veg", "support", "utility", spice=0, heaviness=2,
          meal_type=("lunch","dinner"), dish_category=("bread","paratha_roti"),
          cooking_method=("deep_fried",), richness=("oily",), texture=("fluffy","crispy"),
          weather_affinity=("all_weather",), jain="Y", scope_tier="indian_core",
          mouthfeel=("dry",), aroma=("roasted_aroma",), prep=10, cook=10,
          ingredients=[("wheat_flour",True),("vegetable_oil",False),("salt",False)],
          macro=_m(180, 4, 2, 9, 22, 0, 160)),
    _dish("Jowar Bhakri", "maharashtrian", "veg", "support", "utility", spice=0, heaviness=1,
          meal_type=("lunch","dinner"), dish_category=("bread","paratha_roti"),
          cooking_method=("roasted",), richness=("plain",), texture=("dense","crumbly"),
          weather_affinity=("all_weather",), jain="Y", scope_tier="indian_core",
          mouthfeel=("dry",), aroma=("earthy",), prep=10, cook=12,
          ingredients=[("jowar_flour",True),("salt",False)],
          macro=_m(130, 4, 4, 2, 26, 0, 150)),
]

# ---------------------------------------------------------------------------
# Extra ingredient master rows the golden dishes need that may not be in the
# reference subset (kept minimal; all are real tokens from ingredients_v5.csv
# EXCEPT 'egg','jaggery','raisins' handled in seedgen). Provenance of the ingredient
# MASTER rows = 'real' (reference), but the golden dish_ingredients links = ai_generated.
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# GOLDEN HOUSEHOLDS (5) — varied; incl. a zone-crossing migrant (Bihar East -> Mumbai West).
# member_ages: list of {role, age}. who_cooks/objective drive D2/Q15.
# ---------------------------------------------------------------------------
HOUSEHOLDS = [
    dict(id_key="single_professional_blr", label="Single professional, Bengaluru",
         q1_household_type="single", q2_working_professionals=1,
         q3_home_state="Karnataka", q4_current_city="Bengaluru",
         q5_diet="non_veg", q6_nonveg_types=["chicken","fish"], q7_veg_days=[],
         q8_is_jain=False, q9_allergies=[], q11_conditions=[],
         q12_member_ages=[{"role":"self","age":29}],
         q13_who_cooks="self", q14_eat_out_per_week=4, q15_objective="awesome_taste"),

    # NORTH zone (weather test: rain -> Pakora). Joint family with a senior (spice ceiling 3).
    dict(id_key="joint_family_elders_delhi", label="Joint family with elders, Delhi",
         q1_household_type="couple_kids_parents", q2_working_professionals=2,
         q3_home_state="Delhi", q4_current_city="Delhi",
         q5_diet="veg", q6_nonveg_types=[], q7_veg_days=[],
         q8_is_jain=False, q9_allergies=[], q11_conditions=[],
         q12_member_ages=[{"role":"adult","age":40},{"role":"adult","age":38},
                          {"role":"child","age":9},{"role":"senior","age":71}],
         q13_who_cooks="family", q14_eat_out_per_week=1, q15_objective="awesome_taste"),

    # WEST zone, JAIN household (Jain filter test). Ahmedabad, Gujarat.
    dict(id_key="jain_couple_ahmedabad", label="Jain couple, Ahmedabad",
         q1_household_type="couple", q2_working_professionals=2,
         q3_home_state="Gujarat", q4_current_city="Ahmedabad",
         q5_diet="veg", q6_nonveg_types=[], q7_veg_days=[],
         q8_is_jain=True, q9_allergies=[], q11_conditions=[],
         q12_member_ages=[{"role":"adult","age":34},{"role":"adult","age":32}],
         q13_who_cooks="self", q14_eat_out_per_week=2, q15_objective="healthy_living"),

    # WEST-MH zone (weather test: rain -> Kanda Bhaji). Couple + toddler (weaning A4).
    dict(id_key="couple_toddler_pune", label="Couple with toddler, Pune",
         q1_household_type="couple_kids", q2_working_professionals=2,
         q3_home_state="Maharashtra", q4_current_city="Pune",
         q5_diet="veg", q6_nonveg_types=[], q7_veg_days=[],
         q8_is_jain=False, q9_allergies=[], q11_conditions=[],
         q12_member_ages=[{"role":"adult","age":31},{"role":"adult","age":30},
                          {"role":"weaning","age":1}],
         q13_who_cooks="self", q14_eat_out_per_week=2, q15_objective="awesome_taste"),

    # NORTH clean (no senior/weaning): the rain->Pakora weather-test household. The joint-with-
    # elders North household is unsuitable here because its senior imposes a soft-texture floor
    # (m_age) that correctly demotes crispy Pakora below soft Khichdi — real behaviour, not a bug.
    dict(id_key="couple_delhi_north", label="Couple, Delhi (North)",
         q1_household_type="couple", q2_working_professionals=2,
         q3_home_state="Delhi", q4_current_city="Delhi",
         q5_diet="veg", q6_nonveg_types=[], q7_veg_days=[],
         q8_is_jain=False, q9_allergies=[], q11_conditions=[],
         q12_member_ages=[{"role":"adult","age":32},{"role":"adult","age":30}],
         q13_who_cooks="self", q14_eat_out_per_week=2, q15_objective="awesome_taste"),

    # WEST-MH clean (no weaning): the rain->Kanda Bhaji weather-test counterpart to the North
    # household. Separate from the Pune weaning household because Kanda Bhaji is fried/crispy and is
    # (correctly) removed by the weaning A4 hard filter, so the two tests cannot share a household.
    dict(id_key="couple_mumbai_mh", label="Maharashtrian couple, Mumbai",
         q1_household_type="couple", q2_working_professionals=2,
         q3_home_state="Maharashtra", q4_current_city="Mumbai",
         q5_diet="veg", q6_nonveg_types=[], q7_veg_days=[],
         q8_is_jain=False, q9_allergies=[], q11_conditions=[],
         q12_member_ages=[{"role":"adult","age":33},{"role":"adult","age":31}],
         q13_who_cooks="self", q14_eat_out_per_week=2, q15_objective="awesome_taste"),

    # Zone-crossing MIGRANT: home Bihar (East) -> Mumbai (West). D4 blend + region weather.
    dict(id_key="migrant_bihar_mumbai", label="Migrant single, Bihar->Mumbai",
         q1_household_type="flatmates", q2_working_professionals=2,
         q3_home_state="Bihar", q4_current_city="Mumbai",
         q5_diet="non_veg", q6_nonveg_types=["chicken","fish","mutton"], q7_veg_days=["Tuesday"],
         q8_is_jain=False, q9_allergies=[], q11_conditions=[],
         q12_member_ages=[{"role":"adult","age":27},{"role":"adult","age":26}],
         q13_who_cooks="self", q14_eat_out_per_week=3, q15_objective="into_fitness"),
]

# City -> tier (D1 city_tier_n). Real metro tiers.
CITY_TIER = {
    "Bengaluru": "tier1", "Delhi": "tier1", "Mumbai": "tier1", "Ahmedabad": "tier1",
    "Pune": "tier1", "Chennai": "tier1", "Hyderabad": "tier1", "Kolkata": "tier1",
}

# Golden region_food_affinity rows (ai_generated) — a few, to exercise the affinity join.
REGION_AFFINITY = [
    ("DL", "Onion Pakora", 0.7),
    ("PB", "Sarson Ka Saag", 0.95),
    ("MH", "Kanda Bhaji", 0.9),
    ("TN", "Curd Rice", 0.9),
    ("WB", "Bhuna Khichuri", 0.85),
    ("GJ", "Undhiyu", 0.9),
]
