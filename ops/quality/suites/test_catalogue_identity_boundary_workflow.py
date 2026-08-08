from pathlib import Path

WORKFLOW = Path(".github/workflows/deploy-catalogue-identity-boundary.yml")
VALIDATION = Path("database/validation/974_publish_canonical_catalogue_identity_validation.sql")


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


def test_identity_validation_walks_every_page_and_checks_the_full_safety_subset():
    """More than 2,000 identities must not be mistaken for an incomplete publication."""
    text = VALIDATION.read_text()

    assert "v_identity_seen" in text
    assert "catalogue_identity_rows(v_identity_after, 2000)" in text
    assert "v_identity_seen <> v_identity_count" in text
    assert "catalogue_publication_rows(v_publication_after, 2000)" in text
    assert "AS published(row_data)" in text
    assert "v_publication_page_max <= v_publication_after" in text
    assert "array_agg(dish_id ORDER BY dish_id DESC)" in text
    assert "max(dish_id)" not in text
    assert "catalogue_identity_rows(NULL, 2000) identities" not in text
