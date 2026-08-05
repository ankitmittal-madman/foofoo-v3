# Current Status

**As of:** 2026-08-05. Source: `docs/archive/audits/re_audit_v2/` (fresh clean-room audit, live-verified where noted). This file states current state only — no history. See `docs/archive/audits/` for how these numbers were derived.

> **Deployed P0 backend:** migration 053 and its associated RE and Edge changes close
> the P0 feedback/personalization, suppression, persisted-plan, lock, add-to-date, eight-option,
> lifecycle-add-on, analytics/experiment and notification-worker gaps. Migration 053, plan,
> feedback and the morning notification worker are live on `cmkswalqpmmqojwdmqbv`; the worker is
> scheduled every five minutes with its credential held in Supabase Vault.
> The mobile client now runs Expo SDK 53 with the supported OneSignal Expo/native SDK,
> consent gating, and Supabase user IDs as external identities. Local typecheck, Jest,
> Expo Doctor (18/18), Android bundle export and Vercel web export pass. OneSignal server
> credentials are configured; a physical-device native build remains the final push-delivery test.

> **Production ontology/recommendation release:** migrations 054, 055 and 056 plus seed 146 are
> live on `cmkswalqpmmqojwdmqbv`. All 802 production dishes are mapped to usable meal classes:
> 547 are enriched and 255 are explicitly in review, with no pending enrichment jobs. The
> `dish-ontology` v1, `plan` v9 and `feedback` v6 Edge Functions are active. Fly.io release v124
> is healthy on both checks and serves immutable RE bundle `sha256:3d4cf579d1cf2565`. The legacy
> CSV fallback remains enabled for one monitored rollback window. Unknown-dish AI promotion is
> still disabled pending the Section 8 model/safety decisions in the ontology architecture.
>
> **Remaining local release candidate:** search/filter UI, cached live
> weather context, richer explanation contributions, lock-aware selective refresh, restart-safe
> query/feedback persistence, MMR reranking, offline ranking evaluation, a bounded food graph,
> pinned container bases, staging/manual-production workflows and
> mobile CI are implemented. Verification passes: 712 Python tests (27 skipped), 85 Deno tests,
> 16 mobile tests across 8 suites, Python/Deno/mobile type checks and an Expo web export. A full
> 810-dish local load
> run completed 300 requests at concurrency 20 with 0 errors and p95 2.03s.

| Dimension | % |
|---|---|
| Overall Production Readiness | ~78% |
| Architecture | 80% |
| Backend (Edge Functions) | 90% |
| Recommendation Engine | 85% |
| Food Ontology | 75% |
| Knowledge Graph | 0% (no graph structure exists — flat lookup tables only) |
| Seed Data | 90% |
| Database | 95% |
| Security | 80% |
| Testing | 75% (backend suites green — 85 Deno + 712 repository Python tests; mobile has infra but no physical-device coverage yet) |
| Deployment | 95% (ontology DB/Edge and RE bundle live-verified 2026-08-05; mobile/device release remains) |
| Frontend (mobile) | 70% |
| Observability | 45% (webhook alerting sink wired to every 500-level error path; no webhook URL configured yet) |

## One-line state per major component
- **RE core/service:** implemented, repository Python suite green (712 passed, 27 skipped), Fly
  release v124 live-healthy with bundle `sha256:3d4cf579d1cf2565`.
- **Edge Functions:** implemented and tested (85 tests); auth/ownership model correct;
  `dish-ontology` v1, `plan` v9 and `feedback` v6 deployed 2026-08-05.
- **Mobile app:** onboarding/cold-start/weekly-plan work; explanation, history, profile-edit, and
  DPDP export/delete UI added 2026-08-04 (P0-2/P0-4/P1-2/P1-3/P1-4); jest infra stood up with 9
  pure-logic tests; Expo SDK 53 + OneSignal SDK integration passes typecheck, Expo Doctor, and an
  Android production bundle export; no component-render or physical-device tests yet (P1-5 partial).
- **Database:** real production data (802 dishes, 33 real users, 126+ recommendation events), RLS
  correct; the `household_context` write gap (P0-1) is fixed and deployed — new requests now
  persist correctly.
- **Knowledge layer:** ingredient/cuisine/meal-class ontologies complete; a normalized,
  provenance-backed dish enrichment layer and class-bound candidate view are live for all 802
  production dishes;
  region/nutrition/comfort-hero/substitution real but narrow. A local bounded graph
  traversal/provenance layer now connects dishes, ingredients and curated substitutions; broader
  ontology review, festival mapping and clinically governed health-condition suitability remain
  absent/pending.

See `docs/active/OPEN_ITEMS.md` for what's actionable, `docs/active/LAUNCH_BLOCKERS.md` for what
gates a public launch, `docs/active/ROADMAP.md` for sequencing.
</content>
