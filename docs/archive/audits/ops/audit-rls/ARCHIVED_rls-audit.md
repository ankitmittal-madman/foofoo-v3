# STATUS

ARCHIVED

## Reason

Implementation completed.

This document is retained for historical reference only.

It must not be used as the primary implementation guide.

Refer to the active documentation for the current source of truth.

---

# RLS Policy Correctness Audit

Report only. Live Supabase project `cmkswalqpmmqojwdmqbv` (foofoo-v3, ap-south-1) audited via Supabase MCP directly against `pg_policies` / `pg_tables`, cross-referenced with `database/migrations/019_rls_policies.sql` (canonical RLS intent) and `029_pf1_security_hardening.sql`. No migrations, policies, or grants were changed.

## Method
1. `pg_tables` — every `public` schema table has `rowsecurity = true` (32 tables total, RLS enabled repo-wide, no exceptions found).
2. `pg_policies` — 26 policies found across 19 tables.
3. Classified each table's role (user-owned / reference-lookup / junction / internal-only-log / partition-child) by columns and by migration 019's own stated design, then verified each against its expected access pattern.

## Table Classification & Status

| Table | Role | Policies | SELECT | INSERT | UPDATE | Status |
|---|---|---|---|---|---|---|
| profiles | user-owned | 2 | own (`auth.uid()=id`) | — (created via auth trigger) | own | OK |
| household_members | user-owned | 1 (`ALL`) | own | own | own | OK |
| onboarding_sessions | user-owned | 1 | own | — (service-role only) | — | OK by design |
| consent_records | user-owned, append-only | 1 | own | — (service-role only, see below) | — | OK by design |
| week_plans | user-owned | 2 | own | — (service-role generates) | own | OK by design |
| plan_slots | user-owned (via week_plans) | 2 | own (join) | — | own (join) | OK |
| addon_slots | user-owned (via plan_slots→week_plans) | 1 | own (2-hop join) | — | — | OK by design |
| interaction_events | user-owned, append-only | 2 | own | own | — (append-only, correct) | OK |
| suggestion_logs | user-owned, append-only | 1 | own | — (service-role writes) | — | OK by design |
| context_log | user-owned, append-only | 1 | own | — (service-role writes) | — | OK by design |
| dishes, ingredients, tags, dish_tags, dish_ingredients, dish_combos, dish_combo_items, cuisines, meal_classes, weather_cache | reference/lookup | 1 each (`USING (true)`) | public read | — (service-role/admin only) | — | OK |
| **audit_log, coverage_gap_log, derivation_conflicts, etl_job_runs, feature_flags, push_notification_logs, safety_gate_log** | internal-only | **0** | — | — | — | See CRITICAL/finding below |
| **interaction_events_2026_07 / _08 / _09** | partition children of interaction_events | **0 (own)** | inherited via parent only | inherited via parent only | — | See HIGH finding below |
| **suggestion_logs_2026_07 / _08 / _09** | partition children of suggestion_logs | **0 (own)** | inherited via parent only | inherited via parent only | — | See HIGH finding below |

## Findings

### FINDING 1 — MEDIUM (documentation/live drift, not a functional bug): 7 "internal-only" tables have RLS enabled with zero policies, contradicting migration 019's own comment
Migration `019_rls_policies.sql` (lines 83-88) explicitly states: *"audit_log, derivation_conflicts, coverage_gap_log, safety_gate_log, push_notification_logs, feature_flags, etl_job_runs: ... RLS is intentionally NOT enabled on these."*

Live DB reality: `rowsecurity = true` on **all seven** of these tables (confirmed via `pg_tables`), each with **zero** `pg_policies` rows.

**Why this isn't a CRITICAL lockout in practice:** `service_role` (used by all Edge Functions per the repo's own architecture) has Postgres `BYPASSRLS`, so it can read/write these tables regardless of RLS state. For `anon`/`authenticated` roles, RLS-enabled + zero policies = default-deny, which is actually the *more* secure outcome than the migration's stated design (RLS disabled + relying only on GRANT revokes would have been weaker). So functionally this is safe — but it is a real drift between what the canonical migration file documents and what production actually has, and 019's own text was written specifically to pre-empt exactly this kind of "is this an oversight" ambiguity. Recommend either updating migration 019's commentary to match live reality, or adding a migration that formally documents/pins the current RLS-enabled-zero-policy state, so a future session doesn't "fix" this as a bug.

**Evidence:** `pg_tables` query in this session; `019_rls_policies.sql` lines 83-88.

### FINDING 2 — HIGH: 6 partition-child tables have RLS enabled but no policies of their own, and Supabase/PostgREST exposes every public-schema table as its own REST endpoint
`interaction_events_2026_07/08/09` and `suggestion_logs_2026_07/08/09` are declarative-partitioning children of `interaction_events` / `suggestion_logs`. Both parents have correct, working policies (`ie_insert_own`, `ie_select_own`, `sl_select_own`). Postgres routes queries against the parent to the correct partition and applies the **parent's** policies automatically — so normal application traffic (which should only ever reference `interaction_events`/`suggestion_logs`) is unaffected.

The risk: Supabase's PostgREST layer auto-exposes every table in the `public` schema as its own REST resource, including partition children, by table name. If any client code (or a probing attacker) queries `/rest/v1/interaction_events_2026_08` directly instead of the parent, RLS-enabled + zero own policies means default-deny for `anon`/`authenticated` — not a leak, but a **silent, unexplained empty-result/403** that would be confusing to debug and is functionally inconsistent with the parent. Recommend either: (a) revoking PostgREST/API exposure for partition-child tables explicitly (`pgrst.exclude` or schema config), or (b) mirroring the parent's policies onto each partition for consistency, or (c) adding a migration comment analogous to 019's internal-only-table note so this is never mistaken for an oversight later.

**Evidence:** `pg_policies`/`pg_tables` cross-reference; `017_initial_partitions.sql`.

### No CRITICAL silent-lockout or cross-user data-leak findings on any client-facing, user-owned table
Every table classified as user-owned or reference-lookup has at least one correct policy matching migration 019's design, and every `qual` on a user-owned table uses `auth.uid()` (directly or via an `EXISTS` join back to `profiles`/`week_plans`) — no policy was found missing the ownership check, and no reference table is accidentally restricted by a `user_id`-style condition.

### Note: `dishes` has SELECT-only RLS, no client INSERT/UPDATE policy
This is correct by design — migration `029_pf1_security_hardening.sql` additionally REVOKEs column-level INSERT/UPDATE/REFERENCES on the derived dish columns from `authenticated`/`anon` as defense-in-depth on top of RLS default-deny. Catalogue content is admin/service-role-managed only. Not a finding.

### Cross-user isolation test (Step 7)
**MANUAL — not run.** No test-user infrastructure/seed accounts exist in this project (all transactional tables — `profiles`, `household_members`, `week_plans`, `interaction_events`, `consent_records` — currently have 0 rows; only catalogue/reference data is seeded). A live two-user SELECT-isolation test cannot be run without fabricating auth users, which this report-only round does not do. Flagged as a manual follow-up once real accounts exist.

## Audit completed 2026-07-30
Tables audited: 32
CRITICAL findings: 0
HIGH findings: 1 (partition-child RLS/PostgREST exposure gap — not fixed, report only)
MEDIUM findings: 1 (migration-019-vs-live drift on internal-only tables — not fixed, report only)
Cross-user isolation test: MANUAL (not run — no test users exist)

No fixes applied. This was a REPORT-ONLY round per explicit instruction; all findings above require human review/confirmation before any migration or policy change.
