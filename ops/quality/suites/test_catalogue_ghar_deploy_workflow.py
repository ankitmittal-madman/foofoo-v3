from pathlib import Path

WORKFLOW = Path(".github/workflows/recommendation-catalogue-ghar-deploy.yml")
GENERIC_WORKFLOW = Path(".github/workflows/fly_deploy.yml")
DOCKERFILE = Path("ghar_re_service/Dockerfile")


def test_ghar_image_has_explicit_fail_closed_publication_build_mode():
    text = DOCKERFILE.read_text()

    assert "COPY ghar_re_service/runtime-publication /srv/ghar-re/publication" in text
    assert "ARG GHAR_RE_PUBLICATION_REQUIRED=false" in text
    assert "catalogue.sqlite3" in text
    assert "manifest.json" in text


def test_ghar_deploy_accepts_only_the_same_governed_publication_source():
    text = WORKFLOW.read_text()

    assert "environment: production" in text
    assert 'test "$workflow_name" = "Recommendation catalogue publication"' in text
    assert 'test "$conclusion" = "success"' in text
    assert "--name recommendation-catalogue-publication" in text
    assert 'wc -l)" -eq 3' in text


def test_ghar_deploy_requires_publication_in_image_and_verifies_live_identity():
    text = WORKFLOW.read_text()

    assert "--build-arg GHAR_RE_PUBLICATION_REQUIRED=true" in text
    assert "GHAR_RE_PUBLISHED_CATALOGUE_DIR=/srv/ghar-re/publication" in text
    assert ".published_catalogue.publication_version == $version" in text
    assert "AUX_RE_MODE" not in text
    assert "supabase secrets set" not in text


def test_generic_fly_workflow_cannot_deploy_production_without_publication():
    text = GENERIC_WORKFLOW.read_text()

    assert "options: [staging]" in text
    assert "production:" not in text
    assert "secrets.FLY_API_TOKEN" not in text
    assert "recommendation-catalogue-ghar-deploy.yml" not in text
