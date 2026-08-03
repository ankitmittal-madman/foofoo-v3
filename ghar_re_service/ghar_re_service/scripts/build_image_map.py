"""
build_image_map — OFFLINE dish -> Cloudinary public_id map (WP-18), cached to
data/source/dish_images_v1.json.

Cloudinary asset public_ids follow `<dish_slug>_hero_<NN>_<random>` (e.g.
`takoyaki_hero_01_bapbgt`). The trailing random suffix is NOT derivable from the dish name, so a
URL cannot be built from the name alone — this script lists the account's assets ONCE via the
read-only Admin API and matches each asset's slug prefix to a catalogue dish, producing a static
name->public_id map the runtime (ghar_re_service.media) then uses to build delivery URLs (which need
no credentials).

Credentials are read from the environment, NEVER hardcoded or committed:
    CLOUDINARY_CLOUD_NAME  (default 'dzlqsobol')
    CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET   (required — Admin API list is read-only)

Run:  CLOUDINARY_API_KEY=... CLOUDINARY_API_SECRET=... \
      python3 -m ghar_re_service.scripts.build_image_map
"""

from __future__ import annotations

import base64
import json
import os
import re
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
CATALOGUE = os.path.join(REPO, "ghar_re_service", "data", "bundle", "catalogue.json")
OUT = os.path.join(REPO, "data", "source", "dish_images_v1.json")

CLOUD = os.environ.get("CLOUDINARY_CLOUD_NAME", "dzlqsobol")
# strip the `_hero_<NN>_<random>` suffix to recover the dish slug an asset was uploaded under
_SUFFIX = re.compile(r"_hero_\d+_[a-z0-9]+$", re.IGNORECASE)


def _slug(name: str) -> str:
    """Dish name -> the underscore slug Cloudinary assets are named with: lowercase, every run of
    non-alphanumerics collapsed to a single underscore (so 'Thai Spring Roll (Fried)' ->
    'thai_spring_roll_fried', matching the observed public_ids)."""
    return re.sub(r"_+", "_", re.sub(r"[^a-z0-9]+", "_", name.lower())).strip("_")


def list_assets() -> list[str]:
    """Every image public_id in the account (paginated Admin API list)."""
    key = os.environ["CLOUDINARY_API_KEY"]
    secret = os.environ["CLOUDINARY_API_SECRET"]
    auth = base64.b64encode(f"{key}:{secret}".encode()).decode()
    ids: list[str] = []
    cursor = None
    for _ in range(60):
        url = f"https://api.cloudinary.com/v1_1/{CLOUD}/resources/image?max_results=500"
        if cursor:
            url += f"&next_cursor={cursor}"
        req = urllib.request.Request(url, headers={"Authorization": f"Basic {auth}"})
        with urllib.request.urlopen(req, timeout=30) as r:  # noqa: S310 (fixed https Admin API host)
            data = json.load(r)
        ids += [a["public_id"] for a in data.get("resources", [])]
        cursor = data.get("next_cursor")
        if not cursor:
            break
    return ids


def build_map(asset_ids: list[str], dish_names: list[str]) -> dict[str, str]:
    """dish_name -> public_id, matching each asset's slug prefix to a dish's slug. Prefers the
    `_hero_01` asset when a dish has several; a dish with no matching asset is simply absent (the
    runtime then serves a placeholder), never guessed."""
    # slug -> best public_id (prefer hero_01, else first seen)
    by_slug: dict[str, str] = {}
    for pid in asset_ids:
        base = pid.split("/")[-1]  # ignore any folder prefix
        slug = _SUFFIX.sub("", base)
        if not slug:
            continue
        cur = by_slug.get(slug)
        if cur is None or ("_hero_01_" in base and "_hero_01_" not in cur):
            by_slug[slug] = pid
    out: dict[str, str] = {}
    for name in dish_names:
        pid = by_slug.get(_slug(name))
        if pid:
            out[name] = pid
    return out


def main():
    with open(CATALOGUE) as f:
        dish_names = [d["name"] for d in json.load(f)]
    asset_ids = list_assets()
    mapping = build_map(asset_ids, dish_names)
    with open(OUT, "w") as f:
        json.dump(mapping, f, indent=0, sort_keys=True)
    print(
        f"  {len(asset_ids)} assets listed; matched {len(mapping)}/{len(dish_names)} dishes -> "
        f"dish_images_v1.json"
    )
    missing = [n for n in dish_names if n not in mapping]
    if missing:
        print(f"  {len(missing)} dishes without an image (placeholder), e.g. {missing[:8]}")


if __name__ == "__main__":
    main()
