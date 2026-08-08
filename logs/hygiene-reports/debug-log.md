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
- GitHub re-verification:
  - `re-ci` passed on final code commit `8630205` (run `31206712544`).
  - The full `quality-gate` passed on `8630205` (run `31206713598`).
  - The first credential rotation failed closed before any database update because the legacy email secret did not identify the expected Auth row (run `31206387391`).
  - UUID-bound rotation verified the matching project, existing Auth user, linked profile, password update, and live authentication (run `31206717628`).
  - The original prospective-user workflow then passed in read-only identity mode (run `31206770919`).

## 2026-08-08 — User_50 recommendation components lacked canonical identity

- Symptom: the live User_50 audit found zero UUID-resolved recommendation components, so canonical naming and regional-affinity attribution were unmeasurable.
- Confirmed root cause: the active Ghar fallback bundle assigns `md5:<dish name>` identifiers, Edge omits bounded canonical candidates while Aux is disabled, and meal-episode persistence accepts only UUID dish IDs. The production publication replay resolved 641 of 809 fallback names exactly while preserving the candidate sequence.
- Layer: recommendation service catalogue startup and serving identity.
- Fix applied: reconcile exact canonical-name matches from the checksummed, user-free publication into the fallback catalogue at startup; reject invalid UUIDs, fuzzy/alias matching, and identity collisions; expose count-only UUID coverage.
- Re-verification: 28 focused service tests passed. A replay against production publication run `31252699487` resolved 641/809 fallback identities with candidate names unchanged. Full identity coverage remains pending an identity-only publication index for the 168 safety-incomplete rows.
- Pattern risk elsewhere: any serving path that manufactures a non-UUID dish identifier cannot support canonical feedback lineage; remaining legacy coverage is tracked explicitly rather than hidden.
