# Launch Blockers

Only items that prevent a public launch. Full detail/evidence: `docs/active/OPEN_ITEMS.md`.
Source audit: `docs/archive/audits/re_audit_v2/`.

1. ~~Live-database plan-persistence anomaly is unexplained.~~ **RESOLVED 2026-08-04** — root
   cause found (`plan/handler.ts` never called `recordHouseholdContext`) and fixed; deployed to
   production. See `OPEN_ITEMS.md` P0-1.
2. ~~DPDP export/delete are unreachable from the mobile app.~~ **RESOLVED 2026-08-04** — wired
   into a new Settings screen. See `OPEN_ITEMS.md` P0-2.
3. ~~The actively-routed recommendation surface has no feedback UI.~~ **RESOLVED 2026-08-04** —
   like/dislike + explanation UI added to `today.tsx`, deployed to production. See
   `OPEN_ITEMS.md` P0-4.
4. **Leaked-password-protection is disabled.** Trivial one-click Supabase Auth fix; leaving it off
   going into a public launch is an unforced risk. **Explicitly deferred per Founder instruction
   2026-08-04 (P1-1) — not touched this round.**

Everything else in `OPEN_ITEMS.md`/`ROADMAP.md` is real but does not, on its own, prevent a launch.
</content>
