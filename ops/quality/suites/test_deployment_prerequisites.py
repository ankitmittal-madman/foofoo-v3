import json
import re
from pathlib import Path

import yaml

from ops.recommendation.deployment_prerequisites import (
    PHASE_REQUIREMENTS,
    SECRET_NAMES,
    TARGET_PHASES,
    readiness_report,
    required_names,
)

WORKFLOW = Path(".github/workflows/recommendation-modernization-readiness.yml")


def test_complete_environment_is_ready_without_copying_values():
    environment = {name: f"sensitive-value-for-{name}" for name in required_names()}

    report = readiness_report(environment, "rollout")
    encoded = json.dumps(report)

    assert report["ready"] is True
    assert report["validation_scope"] == "configuration-name-presence-only"
    assert report["deployment_authorized"] is False
    assert report["target_phase"] == "rollout"
    assert report["evaluated_phases"] == list(TARGET_PHASES["rollout"])
    assert report["missing_names"] == []
    assert report["contains_values"] is False
    assert "sensitive-value" not in encoded


def test_missing_configuration_is_reported_by_name_and_phase_only():
    configured = {
        "FOOFOO_SUPABASE_URI": "hidden-database-url",
        "SUPABASE_ACCESS_TOKEN": "hidden-access-token",
        "FLY_API_TOKEN": "hidden-fly-token",
        "PRODUCTION_PROJECT_REF": "project-ref",
    }

    report = readiness_report(configured, "rollout")
    encoded = json.dumps(report)

    assert report["ready"] is False
    assert "AUX_RE_QDRANT_API_KEY" in report["missing_names"]
    assert report["phases"]["schema_and_catalogue"]["ready"] is True
    assert report["phases"]["aux_deployment"]["ready"] is False
    assert "hidden-" not in encoded


def test_foundation_scope_does_not_require_later_shadow_or_rollout_targets():
    environment = dict.fromkeys(required_names("foundation"), "configured")

    foundation = readiness_report(environment, "foundation")
    shadow = readiness_report(environment, "shadow")
    rollout = readiness_report(environment, "rollout")

    assert foundation["ready"] is True
    assert foundation["missing_names"] == []
    assert shadow["ready"] is False
    assert "AUX_LOAD_REQUESTS" in shadow["missing_names"]
    assert rollout["ready"] is False
    assert "AUX_ROLLOUT_APPROVAL_REFERENCE" in rollout["missing_names"]


def test_requirement_contract_covers_every_production_workflow_setting():
    workflow_names = (
        "deploy-recommendation-modernization.yml",
        "recommendation-catalogue-publication.yml",
        "recommendation-catalogue-qdrant.yml",
        "recommendation-catalogue-ghar-deploy.yml",
        "aux-re-deploy.yml",
        "aux-re-load-report.yml",
        "aux-re-mode-control.yml",
        "deploy-recommendation-edge-functions.yml",
        "aux-re-rollout-inputs.yml",
        "aux-re-rollout-evidence.yml",
        "aux-re-rollout-control.yml",
    )
    combined = "\n".join(Path(".github/workflows", name).read_text() for name in workflow_names)

    referenced = set(re.findall(r"\$\{\{\s+(?:secrets|vars)\.([A-Z0-9_]+)\s+\}\}", combined))

    assert referenced == required_names("rollout")
    for name in SECRET_NAMES:
        assert f"secrets.{name}" in combined
    assert len(PHASE_REQUIREMENTS) == 7
    assert tuple(TARGET_PHASES) == ("foundation", "shadow", "rollout")


def test_readiness_workflow_maps_exact_contract_and_is_read_only():
    text = WORKFLOW.read_text()
    parsed = yaml.safe_load(text)
    mapped = set(parsed["jobs"]["audit"]["env"])

    assert mapped == required_names("rollout")
    assert "github.ref == 'refs/heads/main'" in text
    assert "environment: production" in text
    assert "supabase secrets set" not in text
    assert "flyctl" not in text
    assert "curl " not in text
    assert "contains_values == false" in text
    assert 'validation_scope == "configuration-name-presence-only"' in text
    assert "deployment_authorized == false" in text
    assert '--target-phase "${{ inputs.target_phase }}"' in text
