"""
ghar_re_service.media — WP-18 dish media: Cloudinary image URLs + the offline recipe store.

Kept OUT of ghar_re_core on purpose: the core math package stays data-only (no image/CDN/recipe
concerns). The service layer attaches an image URL and (on the detail surface) a full recipe to each
dish view the planner produces.

IMAGE URLs are built deterministically from a dish name — no per-dish table needed. The convention
(all env-overridable, so it can be pointed at the real Cloudinary account without a code change):
    https://res.cloudinary.com/<CLOUD>/image/upload/<TRANSFORM>/<FOLDER>/<slug>.<ext>
    CLOUD     = CLOUDINARY_CLOUD_NAME        (required for a real URL; None -> image_url() = None so
                                              the app falls back to its own placeholder)
    FOLDER    = CLOUDINARY_DISH_FOLDER        (default 'foofoo/dishes')
    TRANSFORM = CLOUDINARY_DISH_TRANSFORM     (default 'w_800,h_600,c_fill,q_auto,f_auto')
    slug      = lowercased dish name, non-alphanumerics -> single hyphens
Confirm the FOLDER + slug convention against the actual Cloudinary asset public_ids; if the account
names assets differently (e.g. an id, or underscores), set the env vars / adjust _slug accordingly.

RECIPES are read from the baked recipes_v1.json (generate_recipes.py), resolved via the same
config.SRC seam every other bundled artifact uses.
"""

from __future__ import annotations

import json
import os
import re

# The Cloudinary CLOUD NAME is public (it appears in every delivery URL) — safe to ship as the
# default; env still overrides. The API key/secret are for UPLOAD/signing only and are deliberately
# NOT referenced here: this feature only DELIVERS images, which needs no credentials.
_CLOUD = os.environ.get("CLOUDINARY_CLOUD_NAME") or "dzlqsobol"
_FOLDER = os.environ.get("CLOUDINARY_DISH_FOLDER", "foofoo/dishes").strip("/")
_TRANSFORM = os.environ.get("CLOUDINARY_DISH_TRANSFORM", "w_800,h_600,c_fill,q_auto,f_auto")
_EXT = os.environ.get("CLOUDINARY_DISH_EXT", "jpg")

_RECIPES: dict | None = None


def _slug(name: str) -> str:
    """Dish name -> Cloudinary public_id slug: lowercase, non-alphanumerics collapsed to hyphens."""
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", name.lower())).strip("-")


def image_url(dish_name: str) -> str | None:
    """Deterministic Cloudinary URL for a dish, or None if no cloud name is configured (the app
    then shows its own placeholder). Never raises — media must not break a recommendation."""
    if not _CLOUD or not dish_name:
        return None
    return (
        f"https://res.cloudinary.com/{_CLOUD}/image/upload/"
        f"{_TRANSFORM}/{_FOLDER}/{_slug(dish_name)}.{_EXT}"
    )


def _recipes() -> dict:
    """Load + cache the recipe store from the bundled recipes_v1.json (config.SRC seam)."""
    global _RECIPES
    if _RECIPES is None:
        from ghar_re_core.config import SRC

        path = os.path.join(SRC, "recipes_v1.json")
        try:
            with open(path) as f:
                _RECIPES = json.load(f)
        except FileNotFoundError:
            _RECIPES = {}
    return _RECIPES


def recipe_for(dish_name: str) -> dict | None:
    """The structured recipe for a dish (or None if not in the store)."""
    return _recipes().get(dish_name)


def attach_image(dish_view: dict) -> dict:
    """Add an `image_url` to a planner dish view (mutates + returns it)."""
    dish_view["image_url"] = image_url(dish_view.get("name", ""))
    return dish_view
