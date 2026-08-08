import tomllib
from pathlib import Path

WORKFLOW = Path(".github/workflows/aux-re-deploy.yml")
AUX_CONFIG = Path("aux_re_service/fly.toml")


def test_aux_fly_defaults_are_shadow_only_and_never_scale_to_zero():
    config = tomllib.loads(AUX_CONFIG.read_text())
    env = config["env"]

    assert env["AUX_REC_ENABLED"] == "true"
    assert env["AUX_REC_MODE"] == "shadow"
    assert env["AUX_REC_ALLOW_OVERRIDE"] == "false"
    assert env["AUX_REC_MODEL_LIGHTFM_ENABLED"] == "false"
    assert env["AUX_REC_MODEL_LIGHTFM_ALLOW_SYNTHETIC"] == "false"
    assert config["http_service"]["auto_stop_machines"] is False
    assert config["http_service"]["min_machines_running"] == 1


def test_deploy_requires_governed_qdrant_and_exact_loaded_publication():
    text = WORKFLOW.read_text()

    assert "environment: production" in text
    assert 'test "$workflow_name" = "Publish recommendation catalogue to Qdrant"' in text
    assert "--name recommendation-catalogue-qdrant-report" in text
    assert 'wc -l)" -eq 1' in text
    assert 'test "$EXPECTED_ROW_COUNT" -gt 0' in text
    assert "AUX_RE_QDRANT_ALLOWED_HOST" in text
    assert "AUX_RE_QDRANT_API_KEY" in text
    assert "qdrant-curl.conf" in text
    assert '--header "api-key:' not in text
    assert ".result.points_count == $count" in text
    assert "AUX_REC_CATALOGUE_PUBLICATION_VERSION=$PUBLICATION_VERSION" in text


def test_deploy_cannot_enable_aux_override_or_edge_active_mode():
    text = WORKFLOW.read_text()

    assert "AUX_REC_MODE=active" not in text
    assert "AUX_REC_ALLOW_OVERRIDE=true" not in text
    assert "AUX_RE_MODE=active" not in text
    assert "supabase secrets set" not in text
    assert "flyctl secrets import" in text
    assert "flyctl config validate --strict" in text
    assert "qdrant.fly.toml" not in text
