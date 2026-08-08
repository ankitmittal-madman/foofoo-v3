from pathlib import Path

WORKFLOW = Path(".github/workflows/recommendation-catalogue-qdrant.yml")


def test_qdrant_upload_accepts_only_the_governed_publication_workflow():
    text = WORKFLOW.read_text()

    assert "environment: production" in text
    assert 'test "$workflow_name" = "Recommendation catalogue publication"' in text
    assert 'test "$conclusion" = "success"' in text
    assert "--name recommendation-catalogue-publication" in text
    assert 'wc -l)" -eq 3' in text


def test_qdrant_upload_uses_secret_by_environment_name_and_exact_hash_collection():
    text = WORKFLOW.read_text()

    assert "--qdrant-api-key-env AUX_RE_QDRANT_API_KEY" in text
    assert '--qdrant-api-key "$AUX_RE_QDRANT_API_KEY"' not in text
    assert 'collection="foofoo_recipes__${digest:0:12}"' in text
    assert ".publication_version == $version" in text
    assert ".verified_count == .uploaded" in text


def test_qdrant_workflow_uploads_only_aggregate_import_report():
    text = WORKFLOW.read_text()
    upload = text.split("uses: actions/upload-artifact@v4", 1)[1]

    assert "qdrant-upload.json" in upload
    assert "catalogue.jsonl" not in upload
    assert "catalogue.sqlite3" not in upload
