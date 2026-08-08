from pathlib import Path

WORKFLOW = Path(".github/workflows/aux-re-rollout-control.yml")


def test_rollout_workflow_can_only_automate_the_fail_safe_direction():
    text = WORKFLOW.read_text()

    assert "supabase secrets set AUX_RE_MODE=off" in text
    assert "supabase secrets set AUX_RE_MODE=active" not in text
    assert "this workflow never sets AUX_RE_MODE=active" in text
    assert "steps.decision.outputs.exit_code == '2'" in text


def test_rollout_workflow_uses_same_repo_successful_artifact_and_production_environment():
    text = WORKFLOW.read_text()

    assert "environment: production" in text
    assert "github.ref == 'refs/heads/main'" in text
    assert "group: production-aux-re-mode-control" in text
    assert '--repo "$GITHUB_REPOSITORY"' in text
    assert 'test "$conclusion" = "success"' in text
    assert 'test "$workflow_name" = "Aux RE rollout evidence"' in text
    assert 'test "$head_branch" = "main"' in text
    assert "--name aux-rollout-evidence" in text
    assert 'test "$(find "$RUNNER_TEMP/aux-rollout-evidence" -type f | wc -l)" -eq 1' in text


def test_rollout_workflow_never_prints_or_uploads_source_evidence():
    text = WORKFLOW.read_text()

    assert "rollout-evidence.json" not in text.split("uses: actions/upload-artifact@v4", 1)[1]
    assert "rollout-decision.json" in text.split("uses: actions/upload-artifact@v4", 1)[1]
    assert "cat $RUNNER_TEMP" not in text
