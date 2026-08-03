"""
ghar_re_service.media — WP-18 dish media: Cloudinary image URLs + the offline recipe store.

Kept OUT of ghar_re_core on purpose: the core math package stays data-only (no image/CDN/recipe
concerns). The service layer attaches an image URL and (on the detail surface) a full recipe to each
dish view the planner produces.

IMAGE URLs use a static dish -> public_id map (dish_images_v1.json, built offline by
scripts/build_image_map.py from the account's real assets). The public_id ends in a random suffix
(`takoyaki_hero_01_bapbgt`) that is NOT derivable from the name, so a per-dish map is required. The
delivery URL is then:
    https://res.cloudinary.com/<CLOUD>/image/upload/<TRANSFORM>/<public_id>
    CLOUD     = CLOUDINARY_CLOUD_NAME        (public, default 'dzlqsobol'; env overrides)
    TRANSFORM = CLOUDINARY_DISH_TRANSFORM     (default 'f_auto,q_auto,c_fill,w_800,h_600')
A dish with no mapped asset (6/810 at build time) gets image_url() = None so the app shows its own
placeholder — never a guessed URL that 404s.

RECIPES are read from the baked recipes_v1.json (generate_recipes.py), resolved via the same
config.SRC seam every other bundled artifact uses.
"""

from __future__ import annotations

import json
import os

# The Cloudinary CLOUD NAME is public (it appears in every delivery URL) — safe to ship as the
# default; env still overrides. The API key/secret are for UPLOAD/signing only and are deliberately
# NOT referenced here: this feature only DELIVERS images, which needs no credentials.
_CLOUD = os.environ.get("CLOUDINARY_CLOUD_NAME") or "dzlqsobol"
_TRANSFORM = os.environ.get("CLOUDINARY_DISH_TRANSFORM", "f_auto,q_auto,c_fill,w_800,h_600")

_RECIPES: dict | None = None
_IMAGE_MAP: dict | None = None


def _image_map() -> dict:
    """Load + cache the dish -> Cloudinary public_id map (dish_images_v1.json, config.SRC seam)."""
    global _IMAGE_MAP
    if _IMAGE_MAP is None:
        from ghar_re_core.config import SRC

        try:
            with open(os.path.join(SRC, "dish_images_v1.json")) as f:
                _IMAGE_MAP = json.load(f)
        except FileNotFoundError:
            _IMAGE_MAP = {}
    return _IMAGE_MAP


def image_url(dish_name: str) -> str | None:
    """Cloudinary delivery URL for a dish via its mapped public_id, or None if the dish has no
    mapped asset (the app then shows its own placeholder). Never raises."""
    if not _CLOUD or not dish_name:
        return None
    pid = _image_map().get(dish_name)
    if not pid:
        return None
    return f"https://res.cloudinary.com/{_CLOUD}/image/upload/{_TRANSFORM}/{pid}"


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
