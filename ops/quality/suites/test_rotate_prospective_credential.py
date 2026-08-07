"""Safety-boundary tests for the production prospective credential rotation operation."""

from ops.recommendation.protected_identity import (
    database_identifies_project,
    supabase_project_ref,
)


def test_project_reference_matches_direct_and_pooler_database_urls():
    """Both supported Supabase PostgreSQL URL shapes must identify the same public project."""
    project_ref = supabase_project_ref("https://abcdefghijklmnopqrst.supabase.co")
    assert project_ref == "abcdefghijklmnopqrst"
    assert database_identifies_project(
        "postgresql://postgres:password@db.abcdefghijklmnopqrst.supabase.co:5432/postgres",
        project_ref,
    )
    assert database_identifies_project(
        "postgresql://postgres.abcdefghijklmnopqrst:password@aws-0-region.pooler.supabase.com:6543/postgres",
        project_ref,
    )


def test_project_reference_rejects_cross_project_and_non_supabase_targets():
    """A rotation must fail closed when its database URL cannot prove the expected project."""
    project_ref = "abcdefghijklmnopqrst"
    assert not database_identifies_project(
        "postgresql://postgres:password@db.otherprojectref.supabase.co:5432/postgres",
        project_ref,
    )
    assert not database_identifies_project(
        "postgresql://postgres:password@example.com:5432/postgres",
        project_ref,
    )
