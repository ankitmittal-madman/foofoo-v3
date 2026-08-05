# Current Status

**As of:** 2026-08-04. Source: `docs/archive/audits/re_audit_v2/` (fresh clean-room audit, live-verified where noted). This file states current state only — no history. See `docs/archive/audits/` for how these numbers were derived.

> **Deployed P0 backend:** migration 053 and its associated RE and Edge changes close
> the P0 feedback/personalization, suppression, persisted-plan, lock, add-to-date, eight-option,
> lifecycle-add-on, analytics/experiment and notification-worker gaps. Migration 053, plan,
> feedback and the morning notification worker are live on `cmkswalqpmmqojwdmqbv`; the worker is
> scheduled every five minutes with its credential held in Supabase Vault.
> The mobile client now runs Expo SDK 53 with the supported OneSignal Expo/native SDK,
> consent gating, and Supabase user IDs as external identities. Local typecheck, Jest,
> Expo Doctor (18/18), Android bundle export and Vercel web export pass. OneSignal server
> credentials are configured; a physical-device native build remains the final push-delivery test.

> **Local release candidate (not yet claimed deployed):** search/filter UI and API, cached live
> weather context, richer explanation contributions, lock-aware selective refresh, restart-safe
> query/feedback persistence, MMR reranking, offline ranking evaluation, a bounded food graph,
> migration 054 RLS optimization, pinned container bases, staging/manual-production workflows and
> mobile CI are implemented. Verification passes: 699 Python tests (27 skipped), 80 Deno tests,
> 16 mobile tests across 8 suites, Python/Deno/mobile type checks and an Expo web export. A full
> 810-dish local load
> run completed 300 requests at concurrency 20 with 0 errors and p95 2.03s.
> A normalized food-ontology ingestion gate is also implemented locally in migration 056 + seed
> 146: all 810 bundled dishes have deterministic per-field evidence and class mappings; future
> canonical dish writes are queued at the database boundary; user dishes stage through a new
> authenticated Edge Function with FoodOn and optional USDA research. It is not deployed, and
> unknown-dish AI promotion remains disabled pending model/safety policy approval.

| Dimension | % |
|---|---|
| Overall Production Readiness | ~78% |
| Architecture | 80% |
| Backend (Edge Functions) | 90% |
| Recommendation Engine | 80% |
| Food Ontology | 60% |
| Knowledge Graph | 0% (no graph structure exists — flat lookup tables only) |
| Seed Data | 90% |
| Database | 90% |
| Security | 80% |
| Testing | 75% (backend 100% green — 79 Deno + 190 Python tests; mobile has infra + 9 pure-logic tests, no component-render tests yet) |
| Deployment | 90% (live-verified healthy; `household`/`plan` redeployed 2026-08-04 with this session's fixes) |
| Frontend (mobile) | 70% |
| Observability | 45% (webhook alerting sink wired to every 500-level error path; no webhook URL configured yet) |

## One-line state per major component
- **RE core/service:** implemented, tested (190 tests passing), deployed, live-healthy.
- **Edge Functions:** all 9 implemented and tested (79 tests); auth/ownership model correct;
  `household` and `plan` redeployed 2026-08-04 with the P0-1/P0-4/P1-3/P1-4/P1-7 fixes.
- **Mobile app:** onboarding/cold-start/weekly-plan work; explanation, history, profile-edit, and
  DPDP export/delete UI added 2026-08-04 (P0-2/P0-4/P1-2/P1-3/P1-4); jest infra stood up with 9
  pure-logic tests; Expo SDK 53 + OneSignal SDK integration passes typecheck, Expo Doctor, and an
  Android production bundle export; no component-render or physical-device tests yet (P1-5 partial).
- **Database:** real production data (802 dishes, 33 real users, 126+ recommendation events), RLS
  correct; the `household_context` write gap (P0-1) is fixed and deployed — new requests now
  persist correctly.
- **Knowledge layer:** ingredient/cuisine/meal-class ontologies complete; a normalized,
  provenance-backed dish enrichment layer and class-bound candidate view are implemented locally;
  region/nutrition/comfort-hero/substitution real but narrow. A local bounded graph
  traversal/provenance layer now connects dishes, ingredients and curated substitutions; broader
  ontology review, festival mapping and clinically governed health-condition suitability remain
  absent/pending.

See `docs/active/OPEN_ITEMS.md` for what's actionable, `docs/active/LAUNCH_BLOCKERS.md` for what
gates a public launch, `docs/active/ROADMAP.md` for sequencing.
</content>
