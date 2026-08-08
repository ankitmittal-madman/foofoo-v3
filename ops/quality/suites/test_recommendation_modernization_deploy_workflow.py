from pathlib import Path

WORKFLOW = Path(".github/workflows/deploy-recommendation-modernization.yml")


def test_schema_deploy_is_project_verified_serialized_and_protected():
    text = WORKFLOW.read_text()

    assert "environment: production" in text
    assert "github.ref == 'refs/heads/main'" in text
    assert "database_identifies_project" in text
    assert "production-database-migrations" in text
    assert "pg_advisory_xact_lock" in text
    assert "--single-transaction" in text


def test_schema_deploy_refuses_partial_state_and_applies_exact_order():
    text = WORKFLOW.read_text()

    assert "unsafe partial modernization state" in text
    assert "-At -F ' '" in text
    positions = [text.index(f"database/migrations/{number:03d}_") for number in range(92, 102)]
    assert positions == sorted(positions)
    assert text.count("database/migrations/") == 10


def test_every_migration_validation_and_rollback_exists():
    for number in range(92, 102):
        migration_number = f"{number:03d}"
        assert len(list(Path("database/migrations").glob(f"{migration_number}_*.sql"))) == 1
        assert len(list(Path("database/validation").glob(f"{number + 852}_*.sql"))) == 1
        matching_rollbacks = [
            path
            for path in Path("database/rollback").glob(f"{migration_number}_*_rollback.sql")
            if "seed_" not in path.name
        ]
        assert len(matching_rollbacks) == 1


def test_completed_schema_revalidation_is_read_only_and_evidence_has_no_counts():
    text = WORKFLOW.read_text()
    evidence = text.split("Produce non-identifying deployment evidence", 1)[1]

    assert "steps.state.outputs.action == 'validate'" in text
    assert "SET TRANSACTION READ ONLY" in text
    assert "profile" not in evidence
    assert "household" not in evidence
    assert "recommendation-modernization-schema" in evidence
