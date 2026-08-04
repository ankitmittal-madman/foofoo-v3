# foofoo-v3

FooFoo — an AI-powered meal-decision assistant for Indian households. A class-first
recommendation engine (household → cohort → class plan → dish pool) built documentation-first
on Supabase/PostgreSQL.

**Status:** Active implementation repository. It contains the Python recommendation service,
Supabase Edge Functions and migrations, and an Expo/React Native mobile client. See
`docs/active/CURRENT_STATUS.md` for the deployed-state snapshot; local changes may be newer and
must not be described as deployed until their migrations/functions/builds are promoted.

## Start here
- **AI assistants / contributors:** read `CLAUDE.md` (repo operating rules) first.
- **Documentation index:** `docs/README.md`.
- **Latest certification:** `docs/archive/certificates/ARCHIVED_REPO-CERT-006_Repository_Green_Certification_v1.0.md`.
- **What's next:** `docs/active/ROADMAP.md`.

## Layout
- `database/migrations/` — ordered PostgreSQL/Supabase schema migrations.
- `database/rollback/`   — paired rollback scripts.
- `database/seeds/`      — `100`–`102` illustrative seed data.
- `database/validation/` — `900`–`904` structural + behavioural validation scripts.
- `docs/`                — product, architecture, governance, research, roadmaps, project-history.

## Rebuild (deterministic, verified)
Apply migrations in numeric order, then the relevant seeds and validations. Migrations assume
Supabase platform prerequisites (`auth.users`, `anon`/`authenticated`/`service_role` roles and
`auth.uid()`); a plain PostgreSQL rebuild must provide compatible bootstrap objects first.
