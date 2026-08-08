import json
from pathlib import Path

from aux_re_service.aux_re_service.schemas import RecommendationRequest

WORKFLOW = Path(".github/workflows/aux-re-load-report.yml")
PAYLOAD = Path("ops/quality/fixtures/aux_load_request.json")


def test_aux_load_payload_is_valid_and_uses_only_fixed_test_identity():
    payload = json.loads(PAYLOAD.read_text())

    RecommendationRequest.model_validate(payload)
    assert payload["user_id"] == "load-test-user-v1"
    assert payload["household_id"] == "load-test-household-v1"
    assert "email" not in str(payload).lower()


def test_load_workflow_uses_protected_https_service_and_secret_by_environment_name():
    text = WORKFLOW.read_text()

    assert "environment: production" in text
    assert "https://*" in text
    assert "--secret-env AUX_RE_SERVICE_SECRET" in text
    assert '--secret "$AUX_RE_SERVICE_SECRET"' not in text
    assert "AUX_LOAD_MAX_P95_MS" in text
    assert "AUX_LOAD_MAX_ERROR_RATE" in text
    assert "AUX_LOAD_MIN_THROUGHPUT_RPS" in text


def test_only_a_passing_version_bound_run_gets_the_accepted_artifact_name():
    text = WORKFLOW.read_text()

    accepted = text.split("name: aux-load-report", 1)[0].rsplit(
        "uses: actions/upload-artifact@v4", 1
    )[1]
    assert "steps.probe.outputs.exit_code == '0'" in accepted
    assert ".publication_versions == [$version]" in text
    assert ".evaluation.passed == true" in text
    assert "aux-load-diagnostics" in text
    assert "Fail a breached or unavailable load gate" in text
