# Rollback Readiness — 2026-08-07

Deploy scope: production deployment of `main` at `672c58d` plus database migration 090.

## Migrations in this deploy

| Migration | Reversible? | Down script exists | Risk |
|---|---|---|---|
| `090_preference_training_readiness_v2.sql` | Yes; additive function only | Yes: `090_preference_training_readiness_v2_rollback.sql` | Low. No table, row, column, policy, or existing function is modified. |

## Deployment rollback path

- Platform: Fly.io production environment plus Supabase PostgreSQL.
- Previous application deployment identifiable: Yes, through Fly release history and GitHub deployment runs.
- Migration/code compatibility on rollback: Safe. Old code continues using v1. New code detects v2 with `to_regprocedure` and falls back closed to v1 if the rollback drops v2.
- Database rollback command: apply the paired rollback file with `ON_ERROR_STOP=1`, a single transaction, and the production schema advisory lock.

## Feature flag coverage

| Feature | Flag-gated | Recommendation |
|---|---|---|
| Preference readiness v2 | Capability-detected | Appropriate. Removing the function is the kill switch; model activation remains separately governed and disabled below thresholds. |

## Overall verdict

READY TO DEPLOY. Migration 090 is additive, reversible, privilege-bounded, and backward-compatible with both the previous and current orchestration code.

## Readiness check completed 2026-08-07

- Migrations checked: 1 (irreversible/risky: 0)
- Deployment rollback path: Safe
- Flag coverage gaps: 0
- Verdict: READY
