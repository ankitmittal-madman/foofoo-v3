# RLS Policy Correctness Audit

## Scope: the 6 tables re-homed from `re_engine` to `public` by WP-20 migration 046

| Table | Role | Policies count | SELECT ok | INSERT ok | UPDATE ok | Status |
|---|---|---|---|---|---|---|
| `public.re_states` | reference (no user_id; state_code/state_name/region) | 1 (after fix) | ✅ (public read) | n/a (service-role writes) | n/a | **FIXED** — was CRITICAL |
| `public.never_list` | user-owned (profile_id) | 0 | service-role only | service-role only | service-role only | OK — intentional |
| `public.not_today_suppression` | user-owned (profile_id) | 0 | service-role only | service-role only | service-role only | OK — intentional |
| `public.user_re_state` | user-owned (profile_id) | 0 | service-role only | service-role only | service-role only | OK — intentional |
| `public.user_taste_vectors` | user-owned (profile_id) | 0 | service-role only | service-role only | service-role only | OK — intentional |
| `public.re_dish_bandit_state` | per-dish RE state (profile_id, dish_id) | 0 | service-role only | service-role only | service-role only | OK — intentional |

## CRITICAL finding (fixed)

**`public.re_states` had RLS enabled with ZERO policies** immediately after migration 046 ran —
meaning it was silently unreadable by `anon`/`authenticated`/`public`, contradicting 046's own
stated intent ("re_states is non-PII reference vocabulary; it is left readable like other public
reference data").

**Root cause:** 046 cloned the table with `CREATE TABLE ... (LIKE re_engine.re_states INCLUDING
ALL)`. Postgres's `LIKE ... INCLUDING ALL` does not copy whether RLS is enabled on the source, but
this project's platform-level `ensure_rls` event trigger (`ddl_command_end`) auto-force-enables RLS
on every newly created table — so `public.re_states` came up with RLS on and no policies, which
(Postgres semantics: no policy ⇒ no rows visible to non-owner/non-superuser roles) blocks all
non-service-role reads. Every other reference table in `public` (`cuisines`, `dish_tags`,
`ingredients`, `meal_classes`) already carries exactly one `FOR SELECT USING (true)` policy — 046
simply didn't add the matching one for `re_states`.

**Fix:** migration `048_re_states_public_read_policy.sql` — `CREATE POLICY re_states_public_read ON
public.re_states FOR SELECT USING (true)`, matching the established convention exactly (same naming
pattern, same policy shape as `cuisines_public_read` / `meal_classes_public_read`). Applied to
production and verified: `re_states` now shows 1 policy, `SELECT`, `qual=true`.

**Impact window:** the gap existed from the moment 046 ran (a few minutes) until 048 was applied,
in this same session. `public.profiles.home_state`'s FK constraint was unaffected the whole time —
Postgres FK checks run with elevated privilege and don't require the referencing role to have SELECT
on the referenced table, so no INSERT/UPDATE on `profiles` would have failed. The only real exposure
was: any client-side (anon/authenticated key) attempt to read `re_states` directly (e.g. to populate
a state-code dropdown) would have gotten an empty result during that window.

## The 5 per-user tables — not a finding

RLS enabled, zero policies, on `never_list` / `not_today_suppression` / `user_re_state` /
`user_taste_vectors` / `re_dish_bandit_state` is **intentional and correct** — it reproduces the old
`re_engine` posture verbatim ("service-role only; REVOKED from anon/authenticated",
`supabase/functions/_shared/constants/schemas.ts`). These are per-user RE state tables the edge
functions touch only via the service-role client, which bypasses RLS entirely. No end user or
anon/authenticated-keyed client is meant to read these directly.

## Cross-user isolation test

Not applicable this pass — none of the 6 audited tables are user-facing rows behind
`auth.uid()`-scoped policies (the 5 per-user tables are service-role-only by design, with no
end-user-facing policy to test; `re_states` is a public reference table with no per-user
isolation concept). No test-user infrastructure was exercised.

## Audit completed 2026-08-03
Tables audited: 6 (the WP-20 re-homed set)
CRITICAL findings: 1 (fixed: 1)
HIGH findings: 0
Cross-user isolation test: N/A (no user-owned-with-per-user-policy tables in this scope)
