from pathlib import Path

WORKFLOW = Path(".github/workflows/aux-re-offline-report.yml")


def test_offline_report_accepts_only_the_governed_consented_replay_source():
    text = WORKFLOW.read_text()

    assert "environment: production" in text
    assert 'test "$workflow_name" = "Aux RE consented holdout replay"' in text
    assert '--repo "$GITHUB_REPOSITORY"' in text
    assert 'test "$conclusion" = "success"' in text
    assert "--name aux-offline-evidence" in text
    assert 'wc -l)" -eq 1' in text


def test_only_an_eligible_exact_publication_report_gets_the_accepted_name():
    text = WORKFLOW.read_text()
    accepted = text.split("name: aux-offline-report", 1)[0].rsplit(
        "uses: actions/upload-artifact@v4", 1
    )[1]

    assert "steps.evaluator.outputs.exit_code == '0'" in accepted
    assert ".publication_versions == [$version]" in text
    assert ".eligible_for_active_evaluation == true" in text
    assert "aux-offline-diagnostics" in text
    assert "Fail an ineligible or invalid offline comparison" in text


def test_raw_holdout_evidence_is_never_uploaded_by_the_report_workflow():
    text = WORKFLOW.read_text()
    uploads = text.split("uses: actions/upload-artifact@v4")[1:]

    assert uploads
    assert all("offline-evidence" not in upload for upload in uploads)
    assert "cat " not in text
    assert "FOOFOO_SUPABASE_URI" not in text
