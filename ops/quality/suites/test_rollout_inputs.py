import pytest

from ops.recommendation.rollout_inputs import (
    RolloutInputError,
    build_target_policy,
    validate_inputs,
)

VERSION = "sha256:" + "a" * 64


def environment():
    return {
        "AUX_ROLLOUT_APPROVAL_REFERENCE": "product-council-2026-08",
        "AUX_ROLLOUT_APPROVED_AT": "2026-08-08T00:00:00Z",
        "AUX_ROLLOUT_MIN_SHADOW_EVENTS": "100",
        "AUX_ROLLOUT_MIN_RETRIEVAL_RATE": "0.98",
        "AUX_ROLLOUT_MAX_TIMEOUT_RATE": "0.01",
        "AUX_ROLLOUT_MIN_COMPARABLE_EVENT_RATE": "0.95",
        "AUX_ROLLOUT_MIN_SERVED_CANDIDATE_COVERAGE": "0.8",
        "AUX_ROLLOUT_MAX_P95_AUX_LATENCY_MS": "200",
    }


def reports():
    offline = {
        "schema_version": "recommendation-offline-validation-v1",
        "case_count": 100,
        "publication_versions": [VERSION],
        "governance": {},
        "metrics": {},
        "slices": {},
        "gates": {},
        "eligible_for_active_evaluation": True,
    }
    load = {
        "schema_version": "recommendation-load-report-v2",
        "service": "aux",
        "url_origin": "aux.internal",
        "publication_versions": [VERSION],
        "metrics": {},
        "evaluation": {"mode": "gated", "passed": True},
    }
    return offline, load


def test_target_policy_comes_only_from_complete_protected_configuration():
    policy = build_target_policy(VERSION, environment())

    assert policy["ratified"] is True
    assert policy["publication_version"] == VERSION
    assert policy["targets"]["min_shadow_events"] == 100

    incomplete = environment()
    incomplete.pop("AUX_ROLLOUT_MAX_TIMEOUT_RATE")
    with pytest.raises(RolloutInputError, match="missing or invalid"):
        build_target_policy(VERSION, incomplete)


def test_packager_accepts_only_passing_aggregate_reports_for_one_publication():
    offline, load = reports()
    targets = build_target_policy(VERSION, environment())

    validate_inputs(offline, load, targets, VERSION)

    load["evaluation"] = {"mode": "measurement_only", "passed": None}
    with pytest.raises(RolloutInputError, match="not gated and passing"):
        validate_inputs(offline, load, targets, VERSION)


def test_packager_rejects_raw_cases_or_identity_even_when_aggregate_flags_pass():
    offline, load = reports()
    targets = build_target_policy(VERSION, environment())
    offline["cases"] = [{"case_id": "opaque"}]
    with pytest.raises(RolloutInputError, match="unsupported aggregate shape"):
        validate_inputs(offline, load, targets, VERSION)

    offline, load = reports()
    offline["metrics"]["household_id"] = "private"
    with pytest.raises(ValueError, match="identity field"):
        validate_inputs(offline, load, targets, VERSION)
