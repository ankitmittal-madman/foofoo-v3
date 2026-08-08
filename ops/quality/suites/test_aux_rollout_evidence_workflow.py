from pathlib import Path

WORKFLOW = Path(".github/workflows/aux-re-rollout-evidence.yml")


def test_evidence_workflow_reads_aggregates_in_protected_production_only():
    text = WORKFLOW.read_text()

    assert "environment: production" in text
    assert "FOOFOO_SUPABASE_URI" in text
    assert "live_rollout_evidence" in text
    assert "production-aux-re-rollout-evidence" in text
    assert "supabase secrets set" not in text


def test_evidence_workflow_requires_three_same_repo_successful_inputs():
    text = WORKFLOW.read_text()

    assert '--repo "$GITHUB_REPOSITORY"' in text
    assert 'test "$conclusion" = "success"' in text
    assert 'test "$workflow_name" = "Aux RE governed rollout inputs"' in text
    assert "--name aux-rollout-inputs" in text
    assert 'wc -l)" -eq 3' in text
    for name in ("offline.json", "load.json", "targets.json"):
        assert name in text


def test_evidence_workflow_uploads_only_composed_evidence():
    text = WORKFLOW.read_text()
    upload = text.split("uses: actions/upload-artifact@v4", 1)[1]

    assert "rollout-evidence.json" in upload
    assert "health.json" not in upload
    assert "guardrails.json" not in upload
    assert "offline.json" not in upload
    assert "cat " not in text
    assert "--current-mode auto" in text
