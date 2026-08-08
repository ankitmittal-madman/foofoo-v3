from pathlib import Path

import yaml

WORKFLOW = Path(".github/workflows/provision-aux-re-fly-app.yml")


def test_aux_fly_provision_is_protected_exact_and_idempotent():
    text = WORKFLOW.read_text()
    parsed = yaml.safe_load(text)
    job = parsed["jobs"]["provision"]

    assert "github.ref == 'refs/heads/main'" in job["if"]
    assert job["environment"] == "production"
    assert job["env"] == {
        "FLY_API_TOKEN": "${{ secrets.FLY_API_TOKEN }}",
        "FLY_GHAR_APP": "${{ vars.FLY_GHAR_APP }}",
        "FLY_AUX_APP": "${{ vars.FLY_AUX_APP }}",
    }
    assert 'test "$FLY_GHAR_APP" = "ghar-re"' in text
    assert 'test "$FLY_AUX_APP" = "foofoo-aux-re"' in text
    assert "flyctl apps list --json" in text
    assert 'flyctl apps create "$FLY_AUX_APP" --org "$owner" --yes' in text
    assert 'if [ -z "$existing_owner" ]' in text


def test_aux_fly_provision_does_not_deploy_or_change_runtime_mode():
    text = WORKFLOW.read_text()

    assert "flyctl deploy" not in text
    assert "flyctl secrets" not in text
    assert "supabase secrets" not in text
    assert "AUX_RE_MODE" not in text
    assert "deployed:false" in text
    assert "aux_influence_enabled:false" in text
