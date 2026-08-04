import os

import pytest

from ghar_re_core import config as core_config

# Captured at conftest IMPORT time — pytest imports every conftest.py during collection, before
# any fixture (including session-scoped ones) runs. This is the only reliable "pristine" snapshot:
# ops/quality/suites/conftest.py's session-scoped TestClient fixture boots the real FastAPI
# lifespan ONCE, outside any individual test's setup/teardown boundary, and that startup's
# resolve_providers() -> BundleConfigProvider.load() repoints core_config.SRC / GHAR_RE_CONFIG_DIR
# / _CACHE at the bundle directory process-wide with no teardown of its own (see providers.py's
# docstring — it does this deliberately, since that's the only way an already-imported core module
# picks up the bundle in a real container boot). A per-test "restore to before this test" snapshot
# would already be corrupted by the time the first test runs, so it must be pinned here instead.
_PRISTINE_SRC = core_config.SRC
_PRISTINE_ENV = os.environ.get(core_config.CONFIG_DIR_VAR)


@pytest.fixture(autouse=True)
def _restore_core_config_globals():
    """Undoes the BundleConfigProvider leak described above after every test, so unrelated
    ghar_re_core tests that assume SRC is the checked-out data/source tree (e.g.
    test_pipeline.py::test_cuisine_zone_coverage) are unaffected by whichever test/fixture in the
    same pytest process happened to boot the real service first. Rooted here (not a suite-local
    conftest) so it wraps every test regardless of which suites get combined into one invocation."""
    yield
    core_config.SRC = _PRISTINE_SRC
    env_var = core_config.CONFIG_DIR_VAR
    if _PRISTINE_ENV is None:
        os.environ.pop(env_var, None)
    else:
        os.environ[env_var] = _PRISTINE_ENV
    core_config._CACHE.clear()  # noqa: SLF001
