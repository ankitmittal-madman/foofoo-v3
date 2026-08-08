from pathlib import Path

WORKFLOW = Path(".github/workflows/deploy-catalogue-identity-boundary.yml")


def test_identity_boundary_deploy_is_protected_idempotent_and_evidenced():
    """Pin the fail-closed production migration contract and aggregate evidence."""
    text = WORKFLOW.read_text()
    assert "environment: production" in text
    assert "apply-catalogue-identity-boundary" in text
    assert "database_identifies_project" in text
    assert "unsafe partial catalogue identity state" in text
    assert "--single-transaction" in text
    assert "122_publish_canonical_catalogue_identity.sql" in text
    assert "974_publish_canonical_catalogue_identity_validation.sql" in text
    assert "SET TRANSACTION READ ONLY" in text
    assert "canonical-catalogue-identity-deploy" in text
    assert "catalogue_identity_coverage()" in text
