# foofoo-v3

FooFoo — an AI-powered meal-decision assistant for Indian households. A class-first
recommendation engine (household → cohort → class plan → dish pool) built documentation-first
on Supabase/PostgreSQL.

**Status:** Repository CERTIFIED GREEN (2026-07-14) — the Repository Recovery Program
(WP-5A → WP-5G) is complete and this repository is the permanent engineering baseline.
No application (backend/frontend) code exists yet; the repository currently holds the complete
documentation, database migration set, seeds, and validation that implementation will build from.

## Start here
- **AI assistants / contributors:** read `CLAUDE.md` (repo operating rules) first.
- **Documentation index:** `docs/README.md`.
- **Latest certification:** `docs/project-history/certificates/[ACTIVE]_REPO-CERT-006_Repository_Green_Certification_v1.0.md`.
- **What's next:** `docs/roadmaps/[ACTIVE]_FooFoo_Project_Roadmap_v1.1.md` (next gate: Data Gate — Seed Engineering).

## Layout
- `database/migrations/` — `001`–`029` schema migrations (numbered, ordered).
- `database/rollback/`   — `001`–`029` paired rollbacks (one per migration).
- `database/seeds/`      — `100`–`102` illustrative seed data.
- `database/validation/` — `900`–`904` structural + behavioural validation scripts.
- `docs/`                — product, architecture, governance, research, roadmaps, project-history.

## Rebuild (deterministic, verified)
Apply migrations `001`→`029` in order to a PostgreSQL 15 database, then seeds `100`→`102`,
then validation `900`→`904`; roll back with `029`→`001`. This build-and-teardown is
execution-proven in a disposable clean room (REPO-CERT-003 / REPO-CERT-006). Note: the
migrations assume the Supabase platform prerequisites (`auth.users`, the `anon`/`authenticated`/
`service_role` roles, `auth.uid()`); a local non-Supabase rebuild must provide these first
(see the WP-5F2 execution report for the compatibility bootstrap used).
