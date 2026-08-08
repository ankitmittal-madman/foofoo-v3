from pathlib import Path

import yaml

WORKFLOW = Path(".github/workflows/aux-re-mode-control.yml")


def workflow_text() -> str:
    return WORKFLOW.read_text()


def test_mode_control_is_main_only_protected_and_serialized_with_kill_switch():
    text = workflow_text()

    assert "github.ref == 'refs/heads/main'" in text
    assert "environment: production" in text
    assert "group: production-aux-re-mode-control" in text
    assert "supabase secrets set AUX_RE_MODE=off" in text
    assert "AUX_RE_MODE=active" not in text


def test_every_transition_forces_off_before_shadow_preflight_and_mutation():
    text = workflow_text()

    off = text.index("Force fail-safe off before evaluating any transition")
    lineage = text.index("Validate exact shadow evidence lineage")
    live = text.index("Verify both live engines expose the exact publication")
    shadow = text.index("Enable evidence-only shadow mode")
    assert off < lineage < live < shadow


def test_shadow_requires_exact_deploy_load_and_runtime_lineage():
    text = workflow_text()

    assert 'workflowName --jq \'.workflowName\')" = "Deploy Aux RE in shadow mode"' in text
    assert (
        'workflowName --jq \'.workflowName\')" = "Deploy Ghar with recommendation catalogue"'
        in text
    )
    assert 'workflowName --jq \'.workflowName\')" = "Aux RE deployed load report"' in text
    assert text.count("--json headBranch --jq '.headBranch'") == 3
    assert "--name aux-load-report" in text
    assert ".publication_versions == [$version]" in text
    assert ".published_catalogue.row_count == $count" in text


def test_off_mode_does_not_require_shadow_inputs_and_evidence_is_identity_free():
    parsed = yaml.safe_load(WORKFLOW.read_text())
    inputs = parsed[True]["workflow_dispatch"]["inputs"]
    text = workflow_text()
    evidence = text.split("Produce identity-free transition evidence", 1)[1]

    for name in (
        "aux_deploy_run_id",
        "ghar_deploy_run_id",
        "load_run_id",
        "publication_version",
        "expected_row_count",
    ):
        assert inputs[name]["required"] is False
    assert "household" not in evidence
    assert "profile" not in evidence
    assert "user_id" not in evidence


def test_every_mutating_or_trusted_source_workflow_is_main_only():
    workflows = (
        "recommendation-catalogue-publication.yml",
        "recommendation-catalogue-qdrant.yml",
        "recommendation-catalogue-ghar-deploy.yml",
        "aux-re-deploy.yml",
        "aux-re-load-report.yml",
        "deploy-recommendation-edge-functions.yml",
    )

    for filename in workflows:
        text = Path(".github/workflows", filename).read_text()
        assert "github.ref == 'refs/heads/main'" in text

    for filename in (
        "recommendation-catalogue-qdrant.yml",
        "recommendation-catalogue-ghar-deploy.yml",
        "aux-re-deploy.yml",
    ):
        text = Path(".github/workflows", filename).read_text()
        assert "--json headBranch --jq '.headBranch'" in text
        assert 'test "$head_branch" = "main"' in text
