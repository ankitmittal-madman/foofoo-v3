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


def test_bundle_version_changes_when_config_changes(built, tmp_path):
    """A changed config file MUST produce a different version — otherwise a stale image could
    silently claim to be current."""
    out, original = built
    tampered_src = tmp_path / "src"
    shutil.copytree(export_bundle.DEFAULT_SOURCE_DIR, tampered_src)
    target = tampered_src / "filters.yaml"
    target.write_text(target.read_text() + "\n# changed\n")

    changed = export_bundle.build_bundle(str(tampered_src), str(tmp_path / "changed"))
    assert changed["bundle_version"] != original["bundle_version"]


def test_missing_config_file_fails_loudly(tmp_path):
    """An incomplete bundle must fail at BUILD time, not as a confusing crash inside a container."""
    partial = tmp_path / "src"
    shutil.copytree(export_bundle.DEFAULT_SOURCE_DIR, partial)
    (partial / "filters.yaml").unlink()
    with pytest.raises(FileNotFoundError, match="filters.yaml"):
        export_bundle.build_bundle(str(partial), str(tmp_path / "out"))


def test_bundle_catalogue_matches_fixture_catalogue(built):
    """The bundled catalogue must reconstruct the same dish set the fixtures produce — the bundle
    is a snapshot of the golden sample, not a lossy re-encoding of it."""
    out, _ = built
    from ghar_re_core.catalogue import Catalogue

    bundled = providers.BundleCatalogueProvider(out).load()
    direct = Catalogue()
    assert len(bundled.dishes) == len(direct.dishes)
    assert {d.name for d in bundled.dishes} == {d.name for d in direct.dishes}


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
