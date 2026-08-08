from pathlib import Path

WORKFLOW = Path(".github/workflows/recommendation-catalogue-publication.yml")


def test_publication_workflow_is_project_verified_and_read_only():
    text = WORKFLOW.read_text()

    assert "environment: production" in text
    assert "FOOFOO_SUPABASE_URI" in text
    assert "PRODUCTION_PROJECT_REF" in text
    assert "ops.recommendation.catalogue_publication" in text
    assert "supabase db push" not in text
    assert "psql" not in text


def test_publication_artifact_has_exact_files_and_aggregate_coverage_gate():
    text = WORKFLOW.read_text()

    assert 'wc -l)" -eq 3' in text
    for name in ("manifest.json", "catalogue.jsonl", "catalogue.sqlite3"):
        assert name in text
    assert ".coverage.publishable_dishes == .row_count" in text
    assert ".identity_row_count >= .row_count" in text
    assert "name: recommendation-catalogue-publication" in text
