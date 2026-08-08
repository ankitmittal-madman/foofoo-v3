from pathlib import Path

WORKFLOW = Path(".github/workflows/aux-re-rollout-inputs.yml")


def test_input_workflow_is_protected_and_has_no_deployment_or_database_authority():
    text = WORKFLOW.read_text()

    assert "environment: production" in text
    assert "FOOFOO_SUPABASE_URI" not in text
    assert "supabase secrets set" not in text
    assert "production-aux-re-rollout-inputs" in text


def test_input_workflow_accepts_only_two_successful_single_report_artifacts():
    text = WORKFLOW.read_text()

    assert text.count('--repo "$GITHUB_REPOSITORY"') >= 3
    assert 'test "$conclusion" = "success"' in text
    assert "--name aux-offline-report" in text
    assert "--name aux-load-report" in text
    assert text.count('wc -l)" -eq 1') == 2


def test_input_workflow_uses_protected_target_variables_and_uploads_only_package():
    text = WORKFLOW.read_text()
    upload = text.split("uses: actions/upload-artifact@v4", 1)[1]

    assert "AUX_ROLLOUT_APPROVAL_REFERENCE" in text
    assert "AUX_ROLLOUT_MIN_SHADOW_EVENTS" in text
    assert "ops.recommendation.rollout_inputs" in text
    assert "aux-rollout-inputs" in upload
    assert "offline-source" not in upload
    assert "load-source" not in upload
