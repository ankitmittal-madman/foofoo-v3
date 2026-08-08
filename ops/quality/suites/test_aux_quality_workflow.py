from pathlib import Path

WORKFLOW = Path(".github/workflows/aux-re-quality.yml")


def test_lightfm_uses_the_pinned_non_isolated_build_environment():
    """Keep legacy LightFM on the known-good setuptools build path used by Auto Engine."""
    text = WORKFLOW.read_text()

    setuptools_install = 'python -m pip install "setuptools==79.0.1" "wheel==0.45.1"'
    test_install = 'python -m pip install -e "./aux_re_service[test]"'
    joblib_install = 'python -m pip install "joblib>=1.4"'
    lightfm_install = 'python -m pip install --no-build-isolation "lightfm==1.17"'

    assert "./aux_re_service[test,models]" not in text
    assert setuptools_install in text
    assert test_install in text
    assert joblib_install in text
    assert lightfm_install in text
    assert text.index(setuptools_install) < text.index(lightfm_install)
