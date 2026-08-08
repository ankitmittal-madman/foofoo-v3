from pathlib import Path

RUNBOOK = Path("docs/architecture/[ACTIVE]_RUNBOOK_Recommendation_Modernization_Deployment_v1.0.md")


def normalized_text() -> str:
    return " ".join(RUNBOOK.read_text().split())


def test_runbook_orders_off_schema_publication_services_shadow_and_canary():
    text = RUNBOOK.read_text()

    markers = [
        "AUX_RE_MODE=off",
        "Deploy recommendation modernization schema",
        "Recommendation catalogue publication",
        "Publish recommendation catalogue to Qdrant",
        "Deploy Ghar with recommendation catalogue",
        "Deploy Aux RE in shadow mode",
        "## 4. Phase B — shadow observation",
        "## 5. Phase C — approved canary",
    ]
    positions = [text.index(marker) for marker in markers]
    assert positions == sorted(positions)


def test_runbook_keeps_user_data_out_of_catalogue_and_requires_exact_identity():
    text = RUNBOOK.read_text()
    normalized = normalized_text()

    assert "must not contain user profiles, history or events" in text
    assert "same catalogue version" in normalized
    assert "exact number" in text
    assert "database row count of 3,409 is not the serving count" in normalized


def test_runbook_requires_real_consent_targets_and_fail_safe_rollout():
    text = RUNBOOK.read_text()

    assert "consented, household-disjoint, time-split real-outcome" in text
    assert "ratified=true" in text
    assert "never activates Aux" in text
    assert "stable household assignment" in text
    assert "Explicit facts outrank inferred context" in text


def test_runbook_separates_serving_and_database_rollback():
    text = RUNBOOK.read_text()
    normalized = normalized_text()

    assert "The additive migrations 092–101 remain in place" in text
    assert "strict reverse order: `101, 100, 099, 098, 097, 096, 095, 094, 093, 092`" in normalized
    assert "Never run seed rollback files" in text
    assert "Do not mutate or delete them as part of immediate rollback" in text


def test_runbook_discloses_unclosed_operational_gaps():
    text = RUNBOOK.read_text()
    normalized = normalized_text()

    assert "Aux RE off and shadow mode control" in text
    assert "first forces `off`" in text
    assert "no automated user-visible activation path" in normalized
    assert "household-stable canary mechanism" in normalized
    assert "consented real-outcome replay producer" in text
    assert "live publishable count is unknown" in text
    assert "## Founder Sign-off" in text
