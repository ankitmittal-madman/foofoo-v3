#!/usr/bin/env python3
"""
Build-time catalogue/config bundle export (Phase F Task 1, RE-DOC-10 §8).

WHAT THIS SOLVES
The RE currently reads its catalogue from ghar_re_core.fixtures (a Python module, so it ships
inside the installed package) and its config from <repo>/data/source/*.yaml (which does NOT ship
inside the package). That second path only resolves when the process runs from a checked-out repo.
In a container, ghar_re_core lives in site-packages and there is no data/source beside it — so the
service would fail at startup. RE-DOC-10 §8 answers this with an immutable, versioned bundle baked
into the image at build time, loaded once at startup, never fetched from a database at runtime.

SOURCE OF TRUTH FOR THIS BUNDLE
The real 810-dish catalogue (data/source/dishes.xlsx, transformed by
ghar_re_service.scripts.build_catalogue — Phase G Task 1) plus the YAML/CSV config layer — NOT the
39-dish golden-sample fixtures (ghar_re_core.fixtures.DISHES) and NOT Postgres. RE-DOC-10 §8
describes the eventual export as pulling from Postgres; that swap remains a separate, later task.
The bundle FORMAT is identical either way, which is the point: swapping the source only ever
changes this script (and now build_catalogue.py), never the service or the engine.

build_catalogue.build_catalogue() also returns a BuildReport (unresolved ingredient tokens,
hidden-allergen-risk dishes, unresolved cuisines, sig_scores_v1.csv join-match/unmatched counts) —
printed to stdout on every build so these known, open data gaps stay visible rather than
disappearing into a clean-looking bundle. See build_catalogue.py's module docstring for the full
account of each gap.

DETERMINISM
bundle_version is a content hash (sha256 over the canonical serialization of everything in the
bundle), not a timestamp. Two builds of unchanged inputs produce the identical version, so
"did the catalogue actually change between these two images?" is answerable by comparing one
string. `created_at` is recorded separately as information, and is excluded from the hash.

USAGE
    python -m ghar_re_service.scripts.export_bundle             # writes the default bundle dir
    python -m ghar_re_service.scripts.export_bundle --out DIR   # writes elsewhere
    python -m ghar_re_service.scripts.export_bundle --check     # verify existing bundle is current
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from datetime import UTC, datetime

from ghar_re_service.scripts import build_catalogue as BC

# The config layer the ENGINE reads at runtime. Deliberately an explicit allow-list, not a
# directory glob: data/source also holds seed spreadsheets and ETL CSVs (dishes.xlsx,
# ingredients_v5.csv, ...) that are inputs to the seed pipeline, not runtime engine config. Baking
# those into the image would inflate it and blur what the engine actually depends on.
# dishes.xlsx itself is read directly by build_catalogue.py (Phase G Task 1), not listed here —
# it's a catalogue INPUT the transform consumes at build time, not a runtime config file.
CONFIG_FILES = (
    "base_weights.yaml",
    "distance_weights.yaml",
    "q15_weights.yaml",
    "pairing_rules.yaml",
    "weather_rules.yaml",
    "filters.yaml",
    "derivation_params.yaml",
    "cohort_weights.yaml",
    "community_priors.csv",
    # Ingredient MASTER attributes (category / allergen flags / Jain compatibility) — read by
    # ghar_re_core.catalogue at import time for allergen + Jain derivation. This is ingredient
    # reference data, NOT the dish catalogue; the real 810-dish swap remains a separate task.
    "ingredients_v5.csv",
)

# class_first_v1/ subdirectory files (WP-15 class-cohort layer — ghar_re_core.knowledge reads
# these via the same config.SRC seam as everything above, so they must ship in the bundle too;
# see knowledge.py's class-first section for what each file is and how it was generated).
CLASS_FIRST_FILES = (
    "meal_class_master.csv",
    "class_dish_options.csv",
    "cohort_matrix.csv",
)

_HERE = os.path.dirname(os.path.abspath(__file__))  # .../ghar_re_service/scripts
_PKG_DIR = os.path.dirname(_HERE)  # .../ghar_re_service (the package)
_SERVICE_ROOT = os.path.dirname(_PKG_DIR)  # ghar_re_service/ (project dir)
_REPO_ROOT = os.path.dirname(_SERVICE_ROOT)  # repo root

DEFAULT_SOURCE_DIR = os.path.join(_REPO_ROOT, "data", "source")
DEFAULT_OUT_DIR = os.path.join(_SERVICE_ROOT, "data", "bundle")

BUNDLE_FORMAT_VERSION = 1
CATALOGUE_SOURCE = (
    "data/source/dishes.xlsx via ghar_re_service.scripts.build_catalogue (real 810-dish catalogue)"
)


def _canonical(obj) -> bytes:
    """Stable JSON bytes: sorted keys, no incidental whitespace. Hash input must not depend on
    dict iteration order or formatting, or the 'same inputs → same version' promise breaks."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode()


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def collect_catalogue(source_dir: str) -> tuple[list[dict], BC.BuildReport]:
    """The raw dish dicts, plus the BuildReport of everything build_catalogue.py flagged rather
    than silently papering over (unresolved ingredients, hidden-allergen-risk dishes, unresolved
    cuisines, sig_scores_v1.csv join mismatches — see build_catalogue.py's module docstring).

    Deliberately the dicts, not constructed Dish objects: ghar_re_core.catalogue.Catalogue takes
    exactly this shape as its constructor argument, so the bundle round-trips into an identical
    in-memory catalogue with no bespoke deserialization logic to drift.
    """
    dishes, report = BC.build_catalogue(source_dir)
    return [dict(d) for d in dishes], report


def _print_report(report: BC.BuildReport) -> None:
    """Surface the known, open data gaps on every build — never silent, never blocking."""
    print(f"[build_catalogue] {report.dish_count} dishes transformed.", file=sys.stderr)
    print(
        f"[build_catalogue] incomplete ING-blocks: {len(report.incomplete_ing_blocks)}",
        file=sys.stderr,
    )
    print(
        f"[build_catalogue] unresolved cuisines: {len(report.unresolved_cuisines)}",
        file=sys.stderr,
    )
    print(
        f"[build_catalogue] hidden-allergen-risk dishes (hing/asafoetida — NOT auto-filtered, "
        f"hidden-derivative allergen layer remains an open P0 gap): "
        f"{len(report.hidden_allergen_risk)}",
        file=sys.stderr,
    )
    print(
        f"[build_catalogue] sig_band matched from sig_scores_v1.csv: "
        f"{len(report.sig_band_matched)}; unmatched (join failed): "
        f"{len(report.sig_band_unmatched)}",
        file=sys.stderr,
    )
    if report.sig_band_unmatched:
        print(
            f"[build_catalogue] sig_band unmatched dishes: {report.sig_band_unmatched}",
            file=sys.stderr,
        )


def build_bundle(source_dir: str, out_dir: str) -> dict:
    """Write the bundle to out_dir and return its manifest."""
    catalogue, report = collect_catalogue(source_dir)
    _print_report(report)

    missing = [f for f in CONFIG_FILES if not os.path.isfile(os.path.join(source_dir, f))]
    missing += [
        os.path.join("class_first_v1", f)
        for f in CLASS_FIRST_FILES
        if not os.path.isfile(os.path.join(source_dir, "class_first_v1", f))
    ]
    if missing:
        # Fail loudly rather than shipping a partial bundle — a config file silently missing from
        # the image surfaces as a confusing startup crash inside a container.
        raise FileNotFoundError(
            f"config files missing from {source_dir}: {', '.join(missing)}. "
            "Refusing to build an incomplete bundle."
        )

    config_hashes: dict[str, str] = {}
    config_payload: dict[str, str] = {}
    for name in CONFIG_FILES:
        with open(os.path.join(source_dir, name), "rb") as fh:
            raw = fh.read()
        config_hashes[name] = _sha256_bytes(raw)
        config_payload[name] = raw.decode("utf-8")
    for name in CLASS_FIRST_FILES:
        rel = f"class_first_v1/{name}"
        with open(os.path.join(source_dir, "class_first_v1", name), "rb") as fh:
            raw = fh.read()
        config_hashes[rel] = _sha256_bytes(raw)
        config_payload[rel] = raw.decode("utf-8")

    catalogue_hash = _sha256_bytes(_canonical(catalogue))

    # The bundle version covers the catalogue AND every config file AND the format version.
    # created_at is excluded on purpose (see module docstring).
    bundle_version = (
        "sha256:"
        + _sha256_bytes(
            _canonical(
                {
                    "format": BUNDLE_FORMAT_VERSION,
                    "catalogue": catalogue_hash,
                    "config": config_hashes,
                }
            )
        )[:16]
    )

    manifest = {
        "bundle_version": bundle_version,
        "bundle_format": BUNDLE_FORMAT_VERSION,
        "created_at": datetime.now(UTC).isoformat(),
        "catalogue_source": CATALOGUE_SOURCE,
        "catalogue_sha256": catalogue_hash,
        "dish_count": len(catalogue),
        "config_sha256": config_hashes,
    }

    # Write atomically-ish: build into a temp dir, then swap. A half-written bundle left behind by
    # an interrupted build is worse than no bundle, because it still looks loadable.
    tmp_dir = out_dir + ".tmp"
    if os.path.isdir(tmp_dir):
        shutil.rmtree(tmp_dir)
    os.makedirs(os.path.join(tmp_dir, "config", "class_first_v1"), exist_ok=True)

    with open(os.path.join(tmp_dir, "catalogue.json"), "w") as fh:
        json.dump(catalogue, fh, sort_keys=True, separators=(",", ":"), default=str)
    for name, text in config_payload.items():
        with open(os.path.join(tmp_dir, "config", name), "w") as fh:
            fh.write(text)
    with open(os.path.join(tmp_dir, "manifest.json"), "w") as fh:
        json.dump(manifest, fh, indent=2, sort_keys=True)
        fh.write("\n")

    if os.path.isdir(out_dir):
        shutil.rmtree(out_dir)
    os.rename(tmp_dir, out_dir)
    return manifest


def read_manifest(bundle_dir: str) -> dict | None:
    path = os.path.join(bundle_dir, "manifest.json")
    if not os.path.isfile(path):
        return None
    with open(path) as fh:
        return json.load(fh)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Export the immutable catalogue/config bundle.")
    ap.add_argument("--source", default=DEFAULT_SOURCE_DIR, help="config layer directory")
    ap.add_argument("--out", default=DEFAULT_OUT_DIR, help="bundle output directory")
    ap.add_argument(
        "--check",
        action="store_true",
        help="verify the existing bundle matches current sources; do not write",
    )
    args = ap.parse_args(argv)

    if args.check:
        existing = read_manifest(args.out)
        if existing is None:
            print(f"FAIL: no bundle at {args.out}", file=sys.stderr)
            return 1
        # Rebuild into a scratch dir and compare versions — the only honest way to answer
        # "is the committed bundle current?".
        scratch = args.out + ".check"
        try:
            fresh = build_bundle(args.source, scratch)
        finally:
            if os.path.isdir(scratch):
                shutil.rmtree(scratch)
        if fresh["bundle_version"] != existing["bundle_version"]:
            print(
                f"FAIL: bundle is stale.\n"
                f"  committed: {existing['bundle_version']}\n"
                f"  current:   {fresh['bundle_version']}\n"
                f"Re-run: python -m ghar_re_service.scripts.export_bundle",
                file=sys.stderr,
            )
            return 1
        print(f"OK: bundle is current ({existing['bundle_version']})")
        return 0

    manifest = build_bundle(args.source, args.out)
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
