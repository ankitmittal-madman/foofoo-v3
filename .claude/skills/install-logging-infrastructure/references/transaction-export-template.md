# Transaction Export Script — Reference Template

A script that reads structured event rows from the database for a given day
and writes human-readable transaction logs to disk — bridging raw DB rows
into the same plain-English narrative style as the User Journey Logger, but
for after-the-fact reporting rather than real-time logging.

## Only scaffold this if applicable

Only relevant if the project persists user/system events to a database
(check for event-like tables via Supabase MCP or migrations: anything
resembling action logs, decision logs, notification logs, job/batch run
logs). If the project has no such tables, skip this component entirely and
tell the user why.

## Design requirements

1. **CLI script**, runnable standalone (e.g. `node scripts/export-txn-logs.mjs`)
2. **Date-scoped** — defaults to "today" in the project's primary timezone
   convention, accepts a `--date` override
3. **Dry-run mode** — `--dry-run` flag using fixture data, so the script can
   be tested without a live DB connection
4. **Discovers the actual event tables** rather than assuming fixed table
   names — query `information_schema` or read migration files to find
   tables that look like event/action/decision/job logs
5. **Two output shapes**:
   - **Per-user file** — one file per active user for that day, narrative
     style matching the User Journey Logger's format
   - **Platform/system file** — daily summary + any batch/scheduled job
     results for that day
6. **Output location**: `ops/logs/session-log/users/` and
   `ops/logs/session-log/system/`, as plain `.txt` files, append-safe
   (never silently overwrites an existing day's file — appends instead)
7. **Privacy rule**: same as the loggers — never write raw emails, JWTs,
   passwords. Truncate user IDs. Only the project's own confirmed
   non-sensitive fields go into the narrative.
8. **Env loading**: read DB connection details from whatever env file
   convention the project already uses (discovered in the parent skill's
   secrets-related steps) — do not hardcode a fixed env var naming scheme
   from an unrelated project.

## Required env (names will vary by project — discover the actual ones)

- A Supabase (or equivalent DB) URL
- A service-role or sufficiently-privileged key for read access

Generate the actual script adapted to the real table names, real timezone
convention, and real action vocabulary discovered for this project.
