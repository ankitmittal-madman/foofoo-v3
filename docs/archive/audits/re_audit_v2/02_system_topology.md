STATUS: ARCHIVED
Reason: Superseded by docs/active/ (2026-08-04 documentation restructure). This audit remains the evidentiary source for docs/active/CURRENT_STATUS.md, OPEN_ITEMS.md, ROADMAP.md, and LAUNCH_BLOCKERS.md.

# System Topology (fresh, 2026-08-04)

```
[Mobile app: Expo/React Native]
   |  Supabase Auth (JWT)               -- IMPLEMENTED
   |
   v
[Supabase Edge Functions: Deno]         -- IMPLEMENTED, deployed via gateway
   |-- household (onboarding writes)    -- IMPLEMENTED
   |-- consent                          -- IMPLEMENTED
   |-- recommendations                  -- IMPLEMENTED, but UI screen calling it is DEAD CODE
   |-- plan (calibration/cold_start/weekly_plan/class_dishes/recipe) -- IMPLEMENTED, actively routed
   |-- feedback                         -- IMPLEMENTED, reachable from only 2 of many screens
   |-- user-export / user-delete        -- IMPLEMENTED backend, MISSING mobile entry point (P0)
   |-- cron-hard-delete / cron-retention-purge -- IMPLEMENTED, service_role only
   |
   v
[Postgres: Supabase, public schema]     -- IMPLEMENTED, RLS on every user table
   |
   v (recommendations/plan functions call out to:)
[Fly.io: ghar_re_service, FastAPI]      -- IMPLEMENTED, DEPLOYED, live-healthy (verified this session)
   |
   v
[ghar_re_core: pure-Python RE domain]   -- IMPLEMENTED, 111 tests passing
   |-- catalogue.json (810 dishes, baked into image) -- IMPLEMENTED
   |-- config bundle (YAML weights)     -- IMPLEMENTED
```

## Component status

| Component | Status |
|---|---|
| Mobile onboarding, cold-start, weekly-plan, today, recipe screens | Implemented, actively routed |
| Mobile `recommendations.tsx` screen | **Dead code** — own header comment confirms no route links to it |
| Mobile explanation/decision-trace UI | **Missing** — no screen renders `contributions`/`decision_trace` anywhere |
| Mobile history/past-plans UI | **Missing** — no read endpoint exists server-side either |
| Mobile profile-edit UI | **Missing** — no route, no backend re-entry path |
| Mobile DPDP export/delete UI | **Missing** — backend fully implemented, unreachable |
| Edge Functions (all 9) | Implemented |
| RE service (Fly.io) | Implemented, deployed, live |
| RE core scoring/filtering/pairing/assembly | Implemented |
| RE personalization (`s_pref`) | **Stubbed** — wired into scoring, numerically inert by config (`enabled: false`) |
| RE feedback-training pipeline | **Stubbed** — real code, never run against production data |
| RE cosine-similarity distance (spec's `d(a,b)`) | **Partially implemented** — exists (`similarity.py`) but not wired into pairing/scoring |
| RE ingredient substitution graph | Implemented (narrow, 13 pairs), not wired into scoring, discovery-only |
| Database schema/RLS/migrations | Implemented |
| Auth (Supabase JWT + in-function re-check) | Implemented |
| Secrets (Fly + Supabase encrypted stores) | Implemented |
| Logging (structured, Edge Function layer) | Implemented |
| Monitoring/observability (Sentry/PostHog/APM) | **Missing** — seams only, zero concrete third-party wiring |
| Feature flags | **Deprecated/removed** — table created, never used, since dropped |
| CI/CD (backend/RE/quality-gate/deploy) | Implemented |
| CI/CD (mobile test/typecheck) | **Missing** — no workflow runs it, no tests exist to run |
</content>
