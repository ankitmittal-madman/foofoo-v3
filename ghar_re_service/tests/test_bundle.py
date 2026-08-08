"""
Baked catalogue/config bundle tests (Phase F Task 1, RE-DOC-10 §8).

What matters here is not just "the bundle loads" but the two properties deployment depends on:
  * the bundle is DETERMINISTIC — same inputs produce the same bundle_version, so comparing two
    images' versions is a real answer to "did the catalogue change?";
  * the bundle is SUFFICIENT — the engine runs from it with no access to <repo>/data/source at
    all, which is precisely the situation inside the container.
"""

import json
import os
import shutil

import pytest
import yaml
from ghar_re_service.scripts import export_bundle

from ghar_re_core import config as core_config
from ghar_re_service import providers


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    out = str(tmp_path_factory.mktemp("bundle") / "b")
    manifest = export_bundle.build_bundle(export_bundle.DEFAULT_SOURCE_DIR, out)
    return out, manifest


def test_bundle_has_expected_layout(built):
    out, manifest = built
    assert os.path.isfile(os.path.join(out, "manifest.json"))
    assert os.path.isfile(os.path.join(out, "catalogue.json"))
    for name in export_bundle.CONFIG_FILES:
        assert os.path.isfile(os.path.join(out, "config", name)), name
    assert manifest["dish_count"] > 0
    assert manifest["bundle_version"].startswith("sha256:")


def test_bundle_version_is_deterministic(built, tmp_path):
    """Same inputs → same version. Without this, comparing image versions means nothing."""
    _, first = built
    second = export_bundle.build_bundle(export_bundle.DEFAULT_SOURCE_DIR, str(tmp_path / "again"))
    assert second["bundle_version"] == first["bundle_version"]
    assert second["catalogue_sha256"] == first["catalogue_sha256"]


def _copy_source_tree(dest_parent):
    """Copy data/source/ AND its siblings sig_scores_v1.csv/dish_macro_v1.csv into an isolated tmp
    dir, mirroring the real repo layout (build_catalogue.load_sig_scores()/load_dish_macro()
    resolve those files one level ABOVE source_dir, per data/source/README.md's own `../*.csv`
    config-table entries — a bare copy of data/source/ alone is no longer a self-contained
    source tree)."""
    src = dest_parent / "src"
    shutil.copytree(export_bundle.DEFAULT_SOURCE_DIR, src)
    parent = os.path.dirname(export_bundle.DEFAULT_SOURCE_DIR)
    for fname in ("sig_scores_v1.csv", "dish_macro_v1.csv"):
        shutil.copy(os.path.join(parent, fname), dest_parent / fname)
    return src


def test_bundle_version_changes_when_config_changes(built, tmp_path):
    """A changed config file MUST produce a different version — otherwise a stale image could
    silently claim to be current."""
    out, original = built
    tampered_src = _copy_source_tree(tmp_path)
    target = tampered_src / "filters.yaml"
    target.write_text(target.read_text() + "\n# changed\n")

    changed = export_bundle.build_bundle(str(tampered_src), str(tmp_path / "changed"))
    assert changed["bundle_version"] != original["bundle_version"]


def test_missing_config_file_fails_loudly(tmp_path):
    """An incomplete bundle must fail at BUILD time, not as a confusing crash inside a container."""
    partial = _copy_source_tree(tmp_path)
    (partial / "filters.yaml").unlink()
    with pytest.raises(FileNotFoundError, match="filters.yaml"):
        export_bundle.build_bundle(str(partial), str(tmp_path / "out"))


def test_enabled_preference_artifact_is_bundled_and_content_addressed(tmp_path):
    source = _copy_source_tree(tmp_path)
    model_rel = "models/preference-v1.joblib"
    model_path = source / model_rel
    model_path.parent.mkdir(parents=True)
    model_path.write_bytes(b"governed-model-bytes")
    pref_path = source / "pref_model.yaml"
    pref = yaml.safe_load(pref_path.read_text())
    pref.update(
        {"mode": "active", "enabled": True, "w_pref": 0.2, "model_artifact_path": model_rel}
    )
    pref_path.write_text(yaml.safe_dump(pref, sort_keys=False))

    out = tmp_path / "bundle-with-model"
    manifest = export_bundle.build_bundle(str(source), str(out))

    assert (out / "config" / model_rel).read_bytes() == b"governed-model-bytes"
    assert model_rel in manifest["config_sha256"]


def test_enabled_preference_artifact_cannot_escape_source_tree(tmp_path):
    source = _copy_source_tree(tmp_path)
    pref_path = source / "pref_model.yaml"
    pref = yaml.safe_load(pref_path.read_text())
    pref.update(
        {
            "mode": "active",
            "enabled": True,
            "w_pref": 0.2,
            "model_artifact_path": "../outside.joblib",
        }
    )
    pref_path.write_text(yaml.safe_dump(pref, sort_keys=False))
    (tmp_path / "outside.joblib").write_bytes(b"must-not-be-bundled")

    with pytest.raises(ValueError, match="inside data/source"):
        export_bundle.build_bundle(str(source), str(tmp_path / "out"))


def test_shadow_preference_artifact_is_also_bundled(tmp_path):
    source = _copy_source_tree(tmp_path)
    model_rel = "models/preference-shadow.joblib"
    model_path = source / model_rel
    model_path.parent.mkdir(parents=True)
    model_path.write_bytes(b"shadow-model-bytes")
    pref_path = source / "pref_model.yaml"
    pref = yaml.safe_load(pref_path.read_text())
    pref.update(
        {"mode": "shadow", "enabled": False, "w_pref": 0.0, "model_artifact_path": model_rel}
    )
    pref_path.write_text(yaml.safe_dump(pref, sort_keys=False))

    out = tmp_path / "bundle-with-shadow-model"
    manifest = export_bundle.build_bundle(str(source), str(out))
    assert (out / "config" / model_rel).read_bytes() == b"shadow-model-bytes"
    assert model_rel in manifest["config_sha256"]


def test_bundle_catalogue_matches_build_catalogue_output(built):
    """The bundled catalogue must reconstruct the same dish set build_catalogue.py produces — the
    bundle is a snapshot of the real 810-dish catalogue (Phase G), not a lossy re-encoding of it.

    Superseded from comparing against the 39-dish golden-sample fixtures: export_bundle.py was
    wired to build_catalogue.py (Phase G Task 2), so the bundle no longer sources from
    ghar_re_core.fixtures.DISHES at all — that comparison would now fail by design, not by bug.
    """
    out, _ = built
    from ghar_re_service.scripts import build_catalogue

    bundled = providers.BundleCatalogueProvider(out).load()
    fresh_dishes, _report = build_catalogue.build_catalogue()
    assert len(bundled.dishes) == len(fresh_dishes)
    assert {d.name for d in bundled.dishes} == {d["name"] for d in fresh_dishes}


def test_bundle_catalogue_has_full_state_origin_coverage(built):
    """Regression guard for the archived RE audit's state_origin gap (§P2-9) and
    WP-14 §3.2 both flagged (536/810 dishes, 66%, had no state_origin, silently zeroing
    scoring._cuis()'s same-state 1.00-weight term for most of the real catalogue). Root cause was
    two-fold: build_catalogue.transform_dish_row() loaded cuisine_map but never wrote
    state_origin into the returned dict, and ghar_re_core.catalogue.Dish unconditionally
    overwrote any state_origin with its own 10-cuisine-only legacy lookup. Both fixed; this
    asserts the real 810-dish catalogue now has 100% coverage, not just that the code runs."""
    out, _ = built
    bundled = providers.BundleCatalogueProvider(out).load()
    missing = [d.name for d in bundled.dishes if d.state_origin is None]
    assert missing == [], f"{len(missing)}/810 dishes have no state_origin: {missing[:10]}..."


def test_authored_staple_and_liquid_combinations_are_standalone(built):
    """Complete named combinations must not be nested inside another generated plate."""
    out, _ = built
    catalogue = providers.BundleCatalogueProvider(out).load()
    expected = {
        "Aloo Puri",
        "Appam with Stew",
        "Chholar Dal with Luchi",
        "Dal Pakwan",
        "Kombdi Vade (Malvani)",
        "Nahari Kulcha",
        "Pithla Bhakri",
        "Sheermal with Nihari",
    }

    assert {
        dish.name for dish in catalogue if dish.name in expected and dish.hero_role == "standalone"
    } == expected


def test_named_animal_dishes_cannot_be_derived_as_vegetarian(built):
    """Missing spreadsheet ingredients must fail safe at the catalogue build boundary."""
    out, _ = built
    catalogue = providers.BundleCatalogueProvider(out).load()
    expected_main_ingredients = {
        "Duck Curry (Assamese)": "duck",
        "Eromba": "fish_generic",
        "Singju": "fish_generic",
        "Tisrya Masala": "clam",
    }

    for dish_name, ingredient_name in expected_main_ingredients.items():
        dish = catalogue.get(dish_name)
        assert dish is not None
        assert dish.diet == "non_veg"
        assert ingredient_name in dish.main_ingredients


def test_clam_safety_override_retains_shellfish_allergen(built):
    out, _ = built
    catalogue = providers.BundleCatalogueProvider(out).load()

    from ghar_re_core.catalogue import dish_allergens

    assert "shellfish" in dish_allergens(catalogue.get("Tisrya Masala"))


def test_vegetarian_candidate_pool_excludes_corrected_animal_dishes_in_every_slot(built):
    out, _ = built
    catalogue = providers.BundleCatalogueProvider(out).load()

    from ghar_re_core import fixtures
    from ghar_re_core.derivation import derive_theta
    from ghar_re_core.pipeline import make_context
    from ghar_re_core.scoring import eligible

    household = next(row for row in fixtures.HOUSEHOLDS if row["id_key"] == "couple_mumbai_mh")
    theta = derive_theta(household)
    corrected = {"Duck Curry (Assamese)", "Eromba", "Singju", "Tisrya Masala"}
    for slot in ("breakfast", "lunch", "dinner"):
        context = make_context(slot=slot)
        candidates = {dish.name for dish in catalogue if eligible(dish, theta, context)}
        assert candidates.isdisjoint(corrected)
        assert all(catalogue.get(name).diet == "veg" for name in candidates)


def test_bundle_catalogue_identity_is_canonical_and_ambiguous_aliases_fail_closed(built):
    """Pin the identity health of the production bundle and canonical-name precedence."""
    out, _ = built
    catalogue = providers.BundleCatalogueProvider(out).load()

    assert all(catalogue.get(dish.name) is dish for dish in catalogue.dishes)
    assert len(catalogue.ambiguous_aliases) == 8
    assert len(catalogue.shadowed_aliases) == 16
    assert all(catalogue.get(alias) is None for alias in catalogue.ambiguous_aliases)


def test_engine_runs_from_bundle_without_repo_config(built, monkeypatch):
    """The container case: serve a real recommendation with the config layer read ONLY from the
    bundle. Pointing core_config at a non-existent repo path first proves the bundle is genuinely
    sufficient — if anything still reached for <repo>/data/source, this would fail.
    """
    out, manifest = built
    monkeypatch.setattr(core_config, "SRC", "/nonexistent/data/source")
    core_config._CACHE.clear()

    cfg = providers.BundleConfigProvider(out).load()
    catalogue = providers.BundleCatalogueProvider(out).load()
    assert os.path.join(out, "config") == core_config.SRC

    from ghar_re_service.modules import build_registry

    from ghar_re_core import fixtures as F
    from ghar_re_service import engine

    hh = [h for h in F.HOUSEHOLDS if h["id_key"] == "couple_mumbai_mh"][0]
    resp = engine.run(
        {
            "household": {k: v for k, v in hh.items() if k != "id_key"},
            "context": {
                "slot": "dinner",
                "season": "monsoon",
                "weather": {"is_raining": True, "temp_c": 27},
            },
        },
        catalogue,
        cfg,
        build_registry(),
    )
    assert len(resp["plates"]) == 7


def test_check_mode_detects_a_stale_bundle(built, tmp_path):
    """`--check` is the CI gate that stops a stale committed bundle from shipping."""
    out, manifest = built
    # Current bundle passes.
    assert (
        export_bundle.main(["--source", export_bundle.DEFAULT_SOURCE_DIR, "--out", out, "--check"])
        == 0
    )

    # Corrupt the recorded version → check must fail.
    path = os.path.join(out, "manifest.json")
    with open(path) as fh:
        data = json.load(fh)
    data["bundle_version"] = "sha256:0000000000000000"
    with open(path, "w") as fh:
        json.dump(data, fh)
    assert (
        export_bundle.main(["--source", export_bundle.DEFAULT_SOURCE_DIR, "--out", out, "--check"])
        == 1
    )
