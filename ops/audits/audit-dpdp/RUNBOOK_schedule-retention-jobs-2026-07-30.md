# Runbook — Schedule the DPDP retention/hard-delete cron jobs (manual step)

Two Edge Functions exist and are deployable but **not yet scheduled**:
- `supabase/functions/cron-retention-purge/` — purges `interaction_events` older than 2 years and
  `audit_log` older than 3 years (DCR-P3-07-004, two separate deletes).
- `supabase/functions/cron-hard-delete/` — permanently erases any profile whose `deleted_at` was
  set more than 72 hours ago (LF-M03).

`pg_cron` and `pg_net` extensions are enabled (migration `040_enable_pg_cron_extension.sql`). What's
left requires the project's `service_role` key, which this session never had access to and should
never be pasted into a migration file or SQL history in plain text.

## Steps (do this in the Supabase Dashboard, not via a committed migration)

1. Deploy both functions if not already live: `supabase functions deploy cron-retention-purge` and
   `supabase functions deploy cron-hard-delete`.
2. In the Supabase Dashboard → Project Settings → Vault, store the service_role key as a secret
   (e.g. `service_role_key`) if not already present.
3. In the Dashboard → Database → Cron (or via SQL executed directly in the Dashboard's SQL editor,
   never committed to the repo), create two schedules using `cron.schedule()` +
   `net.http_post()`, pointing at each function's URL with an `Authorization: Bearer <service_role
   key from vault>` header. Suggested cadence: daily, off-peak hours, for both.
4. Verify with a manual `net.http_post` test call and check the function's logs
   (`supabase functions logs cron-retention-purge`) before trusting the schedule.

Once scheduled, update this runbook's status line below.

**Status: NOT YET SCHEDULED as of 2026-07-30.**
