"""
generate_recipes — OFFLINE recipe builder (WP-18), cached to data/source/recipes_v1.json.

The catalogue has each dish's real ingredients, cooking methods, category, spice, and prep/cook
times — but no cooking STEPS. This composes a structured, coherent recipe per dish AS A CHEF WOULD,
deterministically from those real attributes: an intro, the ingredient list (from data), numbered
method steps ordered by the dish's own cooking_method + category, its real times and serving size,
and a serving suggestion.

HONESTY (FD-11): quantities are expressed qualitatively / "to taste" — the source data has no gram
amounts, so none are invented. Every recipe is tagged `method_source: "auto_draft_from_attributes"`
and carries the dish's real attribute basis, so a reviewer/chef can see exactly what each step was
derived from and refine later. This is a cached draft, not a claim of an authoritative recipe.

Run:  cd ghar_re_service && PYTHONPATH=..:. python3 -m ghar_re_service.scripts.generate_recipes
"""

from __future__ import annotations

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
CATALOGUE = os.path.join(REPO, "ghar_re_service", "data", "bundle", "catalogue.json")
OUT = os.path.join(REPO, "data", "source", "recipes_v1.json")

# cooking_method token -> a step phrase, ordered by this cook_order so a dish's methods compose into
# a sensible sequence (prep first, tempering, sauté, main cook, then finishing fry/bake/steam).
COOK_ORDER = [
    "tempered",
    "sauteed",
    "stir_fried",
    "roasted",
    "boiled",
    "pressure_cooked",
    "steamed",
    "dum_cooked",
    "smoked",
    "baked",
    "grilled",
    "tandoor",
    "fermented_cook",
    "shallow_fried",
    "deep_fried",
    "raw",
]
COOK_STEP = {
    "tempered": "Heat oil or ghee and add the tempering (mustard/cumin, curry leaves, dried "
    "chilli); let it splutter.",
    "sauteed": "Sauté onions and aromatics till golden; stir in tomatoes and ground spices and "
    "cook till the fat separates.",
    "stir_fried": "Add the vegetables and stir-fry on high heat, keeping them crisp-tender.",
    "roasted": "Dry-roast the key ingredients until fragrant and lightly coloured.",
    "boiled": "Add water as needed and boil/simmer until cooked through and the flavours meld.",
    "pressure_cooked": "Add water, cover and pressure-cook until the lentils/main are soft "
    "(about {cook} minutes).",
    "steamed": "Pour into a greased mould and steam until set and a tester comes out clean "
    "(about {cook} minutes).",
    "dum_cooked": "Cover tightly and cook on low 'dum' so the dish finishes in its own steam.",
    "smoked": "Finish with a charcoal/dhungar smoking for a few minutes for aroma.",
    "baked": "Bake in a preheated oven until cooked through and golden.",
    "grilled": "Grill, turning once, until charred at the edges and cooked through.",
    "tandoor": "Cook in a very hot tandoor/oven until charred and just done.",
    "fermented_cook": "Cook the fermented batter on a hot griddle/mould until set and lightly "
    "crisp.",
    "shallow_fried": "Shallow-fry on a tawa with a little oil until golden on both sides.",
    "deep_fried": "Deep-fry in hot oil until crisp and golden; drain on paper.",
    "raw": "Combine everything fresh, without cooking, and mix well.",
}

# dish_category -> a serving suggestion (the accompaniment the plate usually needs).
SERVE_WITH = {
    "dal_lentil": "hot steamed rice or roti",
    "curry": "roti, paratha or steamed rice",
    "dry_sabzi": "phulka/roti and dal",
    "rice": "raita and papad",
    "biryani_pulao": "raita and a salad",
    "dosa_idli": "sambar and coconut chutney",
    "bread": "a sabzi, dal or curd",
    "paratha_roti": "curd, pickle and butter",
    "snack_starter": "green chutney or ketchup",
    "chaat": "extra chutneys on the side",
    "soup": "bread or on its own",
    "kebab": "mint chutney, onion rings and lemon",
    "egg_dish": "toast or paratha",
    "sweet_dessert": "warm or chilled, as you like",
    "beverage": "chilled",
    "salad_raita": "as a cooling side",
    "thali_combo": "as a full plate",
    "whole_meal": "as a complete one-plate meal",
    "condiment_chutney": "as a side with any meal",
    "noodle_pasta": "hot, with a sauce or chutney on the side",
}


def _fmt(step, cook):
    return step.replace("{cook}", str(cook or 10))


def _ingredient_lines(dish):
    """Ingredient list from the dish's real ingredients — mains first, then the rest, quantities
    'to taste' (the data carries no amounts, so none are invented)."""
    mains = [i[0] for i in dish.get("ingredients", []) if i[1]]
    rest = [i[0] for i in dish.get("ingredients", []) if not i[1]]
    lines = [f"{m} — main ingredient" for m in mains]
    lines += [f"{r} — to taste" for r in rest]
    return lines or ["(ingredients not itemised for this dish)"]


def build_recipe(dish):
    """Compose one structured recipe dict from a catalogue dish's attributes."""
    name = dish["name"]
    cats = set(dish.get("dish_category", []))
    methods = [m for m in COOK_ORDER if m in set(dish.get("cooking_method", []))]
    prep = dish.get("prep_mins") or 0
    cook = dish.get("cook_mins") or 0
    steps = [
        f"Prep: rinse, peel and chop the main ingredients and keep the spices measured out "
        f"(about {prep or 10} minutes)."
    ]
    for m in methods:
        steps.append(_fmt(COOK_STEP[m], cook))
    if not methods:
        steps.append("Cook the ingredients together over medium heat until done.")
    # category-specific finishing
    if cats & {"dal_lentil", "curry", "dry_sabzi"}:
        steps.append("Adjust salt, simmer for a minute, and finish with fresh coriander.")
    if cats & {"dosa_idli", "bread", "paratha_roti"}:
        steps.append("Serve hot off the griddle.")
    serve = next(
        (SERVE_WITH[c] for c in dish.get("dish_category", []) if c in SERVE_WITH),
        "hot, fresh off the stove",
    )
    steps.append(f"Serve {serve}.")
    return {
        "dish_name": name,
        "cuisine": dish.get("cuisine"),
        "diet": dish.get("diet"),
        "serves": dish.get("serving_size") or "2-3",
        "prep_mins": prep,
        "cook_mins": cook,
        "total_mins": dish.get("total_mins") or (prep + cook),
        "spice_level": dish.get("spice_level"),
        "ingredients": _ingredient_lines(dish),
        "steps": steps,
        "method_source": "auto_draft_from_attributes",
        "attribute_basis": {
            "cooking_method": dish.get("cooking_method", []),
            "dish_category": dish.get("dish_category", []),
        },
    }


def main():
    with open(CATALOGUE) as f:
        dishes = json.load(f)
    recipes = {d["name"]: build_recipe(d) for d in dishes}
    with open(OUT, "w") as f:
        json.dump(recipes, f, separators=(",", ":"), sort_keys=True)
    avg_steps = sum(len(r["steps"]) for r in recipes.values()) / max(len(recipes), 1)
    print(f"  wrote recipes_v1.json ({len(recipes)} recipes, avg {avg_steps:.1f} steps/recipe)")


if __name__ == "__main__":
    main()
