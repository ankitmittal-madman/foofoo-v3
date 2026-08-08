from pathlib import Path

WORKFLOW = Path(".github/workflows/aux-re-quality.yml")
AUTO_ENGINE_WORKFLOW = Path(".github/workflows/recommendation-auto-engine.yml")
RUNTIME_DOCKERFILE = Path("aux_re_service/Dockerfile")
TRAINING_DOCKERFILE = Path("aux_re_service/Dockerfile.train")
LOCAL_COMPOSE = Path("aux_re_service/compose.local.yml")


def test_lightfm_uses_the_pinned_legacy_build_environment():
    """Keep LightFM installable after pip 25.3 removed the legacy build path."""
    text = WORKFLOW.read_text()

    tooling_install = (
        'python -m pip install "pip==25.2" "setuptools==79.0.1" "wheel==0.45.1"'
    )
    test_install = 'python -m pip install -e "./aux_re_service[test]"'
    joblib_install = 'python -m pip install "joblib>=1.4"'
    lightfm_install = 'python -m pip install --no-use-pep517 "lightfm==1.17"'

    assert "./aux_re_service[test,models]" not in text
    assert tooling_install in text
    assert test_install in text
    assert joblib_install in text
    assert lightfm_install in text
    assert text.index(tooling_install) < text.index(lightfm_install)


def test_all_operational_lightfm_installs_use_the_compatible_pip_path():
    """CI, training and runtime images must not silently select pip's broken PEP 517 path."""
    for path in (AUTO_ENGINE_WORKFLOW, RUNTIME_DOCKERFILE, TRAINING_DOCKERFILE):
        text = path.read_text()
        assert '"pip==25.2"' in text, path
        assert '--no-use-pep517 "lightfm==1.17"' in text, path
        assert '--no-build-isolation "lightfm==1.17"' not in text, path


def test_aux_quality_commands_resolve_the_inner_python_package():
    """The repository's outer directory must not shadow the installed Aux package in CI."""
    text = WORKFLOW.read_text()
    assert "PYTHONPATH=aux_re_service python -m pytest aux_re_service/tests -q" in text
    assert (
        "PYTHONPATH=aux_re_service python -m aux_re_service.training.quality_gate" in text
    )


def test_live_quality_probe_preserves_aux_service_authentication():
    """The local shadow proof must configure auth and sign the exact request bytes."""
    workflow = WORKFLOW.read_text()
    compose = LOCAL_COMPOSE.read_text()
    assert "AUX_REC_SERVICE_SECRET must be set" in compose
    assert 'AUX_REC_SERVICE_SECRET="$(openssl rand -hex 32)"' in workflow
    assert "printf '%s.' \"${request_timestamp}\"" in workflow
    assert 'cat "${request_path}"' in workflow
    assert 'X-Aux-Signature: t=${request_timestamp},v1=${request_signature}' in workflow
    assert "docker compose -f aux_re_service/compose.local.yml logs --no-color" in workflow
