# Launch Blockers

Only unresolved items that prevent a public launch belong here. Detailed evidence and
non-blocking work are maintained in `OPEN_ITEMS.md`.

1. **Fund and enable Supabase leaked-password protection.** The Supabase Auth advisor reports that
   it is disabled. A Management API attempt to enable `password_hibp_enabled` on 2026-08-05 returned
   HTTP 402 because the capability requires a paid plan. Repository work cannot clear this blocker;
   it requires an approved Supabase plan upgrade followed by advisor verification.

Resolved launch blockers are retained in the archived audit and implementation records; they are
not repeated in this active list.
