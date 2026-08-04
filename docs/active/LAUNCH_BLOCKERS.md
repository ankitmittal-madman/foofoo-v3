# Launch Blockers

Only items that prevent a public launch. Full detail/evidence: `docs/active/OPEN_ITEMS.md`.
Source audit: `docs/archive/audits/re_audit_v2/`.

1. **Live-database plan-persistence anomaly is unexplained.** 126 `recommendation_events` exist but `week_plans`/`plan_slots`/`household_context`/`interaction_events` all have 0 rows. Must be traced and understood before claiming the plan-generation flow works for real users — launching without knowing why is launching blind.
2. **DPDP export/delete are unreachable from the mobile app.** Legally required data-subject rights (India DPDP Act) have a working backend and zero UI entry point. This blocks any public launch in India.
3. **The actively-routed recommendation surface has no feedback UI.** Real users generate recommendations but have no way to like/dislike/accept on the screens they actually use — feedback data will not accumulate post-launch, which also permanently blocks personalization from ever activating.
4. **Leaked-password-protection is disabled.** Trivial one-click Supabase Auth fix; leaving it off going into a public launch is an unforced risk.

Everything else in `OPEN_ITEMS.md`/`ROADMAP.md` is real but does not, on its own, prevent a launch.
</content>
