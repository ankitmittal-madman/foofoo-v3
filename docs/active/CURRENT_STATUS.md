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
> The ontology rollout initially activated `dish-ontology` v1, `plan` v9 and `feedback` v6;
> current Edge versions are recorded in the production-hardening block below. Fly.io release v125
> is healthy on both checks and serves immutable RE bundle `sha256:3d4cf579d1cf2565`. The legacy
> CSV fallback remains enabled for one monitored rollback window.
>
> **Food-intelligence/episode completion release:** migrations 060–065 and seed 147 are live.
> They add the leased enrichment worker and schedules, generic ontology graph, nutrient
> assertions, complete catalogue constraints/regions/recipes/episodes, safe exact-match unknown
> dish promotion, catalogue episode resolution, replay, ML/catalog controls, and research and
> annotation operations. `dish-ontology`, `cron-dish-ontology`, `plan`, `research-panel`, and
> `research-annotations` were deployed. The first full external pass completed for all 802 dishes
> with zero failed or pending jobs; FoodOn matched 104 dishes, while USDA returned HTTP 403 for
> every attempted lookup with the configured key. Mobile
> meal episodes are now default-on with compatibility fallback, and the missing-dish submission
> screen is implemented. Migration 065 adds complete assertion/relationship provenance and the
> authenticated consolidated ontology-record API. The production Expo web build is live at
> `https://foofoo-v3.vercel.app`; the post-deploy persona journey passed on 2026-08-05 with
> meal-episode rendering, feedback, recipes, slate persistence and evidence publication verified.
> The later polished mobile shell was reconciled with the same server-authoritative 7×3 weekly
> planner and live episode surface; production workflow `31006023576` passed after deployment.
> The new RE eligible-set response is committed and tested but its Fly production rollout is
> waiting for approval in GitHub's protected `Production` environment.
>
> **Budgeted generative ontology enrichment:** migrations 066–069 and the updated
> `cron-dish-ontology` worker are live. Groq `openai/gpt-oss-120b` independently processes every
> canonical dish, retains candidates at confidence `>=0.65`, and directly publishes only aliases,
> low-risk taxonomy tags and regional affinity at `>=0.80`. Deterministic alias/region guards and
> database field allowlists exclude allergens, religious or clinical suitability, nutrition,
> ingredients and other safety-sensitive claims. Atomic UTC-day limits are 800 requests and
> 160,000 tokens. At the latest verification, 11/802 dishes were complete, 791 pending, with zero
> failed rows; 12 requests used 12,665 tokens and no tokens remained reserved. The ten-minute
> schedule continues the backfill automatically and defers cleanly at the daily token cap.
>
> **Production hardening:** migrations 057–059 are live. They close all audited trigger-function
> execute grants, all 77 missing leading foreign-key indexes and both duplicate-index findings;
> automate a six-month event-partition horizon; provision a household and owner membership for
> every new profile; backfill existing tenant IDs; and enforce non-null household ownership on the
> five household-scoped fact/context tables. `recommendations` v11, `plan` v13 and `feedback` v7
> are live with household-aware writes. GitHub's `Production` environment now requires review and
> permits deployments from `main` only.
>
> **Remaining local release candidate:** search/filter UI, cached live
> weather context, richer explanation contributions, lock-aware selective refresh, restart-safe
> query/feedback persistence, MMR reranking, offline ranking evaluation, a bounded food graph,
> pinned container bases, staging/manual-production workflows and
> mobile CI are implemented. Verification passes: 715 Python tests (27 skipped), 93 Deno tests,
> 16 mobile tests across 8 suites, Python/Deno/mobile type checks and an Expo web export. A full
> 810-dish local load
> run completed 300 requests at concurrency 20 with 0 errors and p95 2.03s.

| Dimension | % |
|---|---|
| Overall Production Readiness | ~78% |
| Architecture | 80% |
| Backend (Edge Functions) | 90% |
| Recommendation Engine | 85% |
| Food Ontology | 90% (production graph/read API, full catalogue coverage and governed Groq backfill live; USDA remains an external gate) |
| Knowledge Graph | 70% (normalized production graph with provenance; subjective/festival/substitution breadth remains iterative) |
| Seed Data | 90% |
| Database | 95% |
| Security | 88% (database advisor remediations live; leaked-password screening needs a paid Supabase plan) |
| Testing | 75% (backend suites green — 93 Deno + 715 repository Python tests; mobile has infra but no physical-device coverage yet) |
| Deployment | 95% (ontology DB/Edge and RE bundle live-verified 2026-08-05; mobile/device release remains) |
| Frontend (mobile) | 70% |
| Observability | 60% (scheduled production smoke/issue alerting added; application 500-level webhook destination remains unconfigured) |

## One-line state per major component
- **RE core/service:** implemented, repository Python suite green (715 passed, 27 skipped), Fly
  release v125 live-healthy with bundle `sha256:3d4cf579d1cf2565`.
- **Edge Functions:** implemented and tested (93 tests); current single-owner authorization model
  is enforced; `dish-ontology` v5, `recommendations` v11, `plan` v13 and `feedback` v7 deployed
  2026-08-05. Explicit membership/role authorization is still required before shared-household
  collaboration is enabled.
- **Mobile app:** onboarding/cold-start/weekly-plan work; complete meal episodes are live on the
  production web client and passed the post-deploy persona journey; explanation, history,
  profile-edit, and
  DPDP export/delete UI added 2026-08-04 (P0-2/P0-4/P1-2/P1-3/P1-4); jest infra stood up with 9
  pure-logic tests; Expo SDK 53 + OneSignal SDK integration passes typecheck, Expo Doctor, and an
  Android production bundle export; no component-render or physical-device tests yet (P1-5 partial).
- **Database:** real production data (802 dishes, 77 profiles at the 2026-08-05 continuity audit),
  RLS enabled; household context writes and tenant continuity are fixed and live. All profiles have
  a household and active owner membership, all scoped household IDs are non-null, advisor-reported
  missing FK indexes/duplicate indexes are resolved, and partition creation is automated.
- **Knowledge layer:** ingredient/cuisine/meal-class ontologies complete; a normalized,
  provenance-backed dish enrichment layer and class-bound candidate view are live for all 802
  production dishes;
  every production dish now has constraint, regional, nutrition-estimate, recipe and published
  episode coverage. The production relational graph connects dishes, aliases, ingredients,
  classes and catalogue features with provenance. USDA validation is blocked by its rejecting
  credential. Groq low-risk enrichment is live under strict budgets and field allowlists;
  festival mapping and clinically governed health-condition suitability remain absent/pending.

See `docs/active/OPEN_ITEMS.md` for what's actionable, `docs/active/LAUNCH_BLOCKERS.md` for what
gates a public launch, `docs/active/ROADMAP.md` for sequencing.
