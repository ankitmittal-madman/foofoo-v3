# Debug log

## 2026-08-07 — Failed GitHub workflows on `main`

- Symptom: `re-ci`, `quality-gate`, and `prospective-user-recommendation-cycle` failed on commit `f1f2585`.
- Confirmed root causes:
  - `re-ci`: Ruff found an unformatted lifecycle-summary assertion.
  - `quality-gate`: 95 assertions still required raw `plate_score` ordering even though the production `home_v2` policy intentionally applies history-aware diversity selection; one additional failure exposed a real safety bug where household `peanut` did not match catalogue `peanuts`.
  - `prospective-user-recommendation-cycle`: Supabase Auth rejected the protected credential with `invalid_credentials`. The first guarded rotation then proved the protected email resolved to no Auth row; the account UUID and linked production profile remain the authoritative identity.
- Layer: recommendation policy, allergen safety normalization, CI formatting, and protected operational credentials.
- Structural fixes:
  - Canonicalize household and catalogue allergen vocabulary through one shared function and apply it to scoring and food-graph provenance.
  - Test the serving policy's hard guarantees—unique plates, policy metadata, finite scores, unique heroes, and meaningful cuisine/meal-class variety—while retaining exact selector-cap and backfill tests at the selector boundary.
  - Resolve the Auth email from the verified expected UUID inside the matching Supabase project, removing the stale duplicate email-secret dependency. Add a guarded credential-rotation operation that updates only that existing auth user after verifying its linked profile, then authenticate immediately after rotation.
  - Format the failing files and include the credential guard tests in `re-ci`.
- Local re-verification: Ruff lint/format passed; mypy passed; `re-ci` equivalent passed with 261 passed and one intentional skip; the full quality orchestrator passed with 752 passed, zero failed, and 27 environment-dependent skips.
- GitHub re-verification: `re-ci` passed on `581d853`; the first credential rotation failed closed before any database update because the legacy email secret did not identify the expected Auth row. UUID-bound recovery and the remaining workflow reruns are pending.
