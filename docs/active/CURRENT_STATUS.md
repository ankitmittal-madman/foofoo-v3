# Current Status

**As of:** 2026-08-08. Sources: the active recommendation modernization deployment runbook plus
`docs/archive/audits/re_audit_v2/` for the earlier clean-room baseline. This file states current
state only; deployment run IDs and rollback instructions live in the active runbook.

> **Recommendation modernization Phase A:** production migrations 092–101 and validations
> 944–953 are live. Publication
> `sha256:e9c7b524dc5480895d5b675caaa88a51788980cbfb3e1aea95bc5994a7ce3269`
> contains 642 fully enriched, safety-closed and meal-class-mapped dishes from 3,402 active dishes;
> the same generation is present in Ghar, Qdrant and one isolated Aux Machine. `plan` and
> `recommendations` are deployed, and the final protected transition records production Edge
> `AUX_RE_MODE=off`, so no user request is sent to Aux. The default Ghar request path therefore
> remains authoritative and may use its 810-dish deterministic fallback when no canonical
> shortlist is supplied. Authenticated cold-start/experienced-user smoke is still pending an
> explicitly selected test household. Aux quality run `31256081581` passed installation, all 86
> service tests, model gates, local Qdrant and an exact-body signed packaged-service request;
> its evidence explicitly prohibits active promotion because training is synthetic and online
> shadow/real-outcome evidence does not exist.

> **Catalogue expansion audit:** the deployed immutable generation remains 642 dishes. Protected
> aggregate run `31257431526` measured 3,410 stored rows, 3,402 active rows and 646 rows passing
> the existing presence-based publication gates; only 547 of those 646 also passed the stricter
> confidence policy. Run `31257875325` then proved the complete meal-class remediation cohort is
> 255 dishes: 99 are presence-eligible but below the class-confidence gate and 156 have complete
> serving facts but remain in ontology review. All 255 mappings are provisional internal-research
> outputs (238 `chef_rubric`, 17 `chef_rubric_secondary`), with zero curated-exact, human-reviewed
> or accepted evidence. They must receive new independent evidence or human review; confidence
> cannot be raised mechanically. Aux remains off and no catalogue or mapping changed in either
> audit.

> **Primary versus component serving model:** migration 106 is live through protected run
> `31258906340`. It models reviewed, slot-aware compatibility for staples, sides and accompaniments
> separately from primary meal-class identity, normalizes the legacy `snack` alias to canonical
> `snacks`, and keeps machine/rule proposals non-serving until reviewed. The first aggregate
> baseline found 1,402 canonical dish-slot routes: 603 primary-ready, 262 needing primary-class
> review and 537 needing component review; there are zero proposals and zero accepted component
> facts. That v1 report is slot-only; the additive v2 report described below now closes its
> active-dish denominator gap. Neither migration changes the 642-row publication gate or either
> engine. Aux remains off.

> **Meal-slot remediation evidence:** protected run `31259220512` installed the v2 report and
> reconciled all 3,402 active dishes. Exactly 802 have a canonical slot and 2,600 do not; 2,596
> lack a hero role and 918 carry at least one unrecognized slot label. Protected run `31267459809`
> installed migration 108 and split the 2,600 slotless dishes into 1,802 single-direct proposals
> (667 lunch, 566 snacks, 294 dinner and 275 breakfast), 797 contextual-review rows and one direct
> conflict. Contextual rows comprise 394 side dishes, 247 desserts, 120 main courses, 22 diet
> values misplaced in the course field, 12 one-pot dishes and two brunch dishes. The audit created
> no proposal, exposed no raw source text and made no serving change.
>
> **Governed direct meal-slot proposals:** migration 109, validation 961, its evidence-preserving
> rollback and the protected generation workflow are repository-ready. The design binds each
> proposal to immutable import rows, requires the exact audited candidate count, creates only
> `pending` records, blocks automatic acceptance and performs no serving or publication write.
> Twenty-five focused tests, SQL/YAML parsing and an isolated PostgreSQL execution prove exact
> candidate filtering, idempotency, evidence enforcement, forward-only review state and rollback
> preservation. This foundation is not yet installed in production and the 1,802 proposals have
> not yet been generated. Aux remains off.

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
> live on `cmkswalqpmmqojwdmqbv`. The original 802-dish ontology cohort has a meal-class mapping
> for every dish: 547 meet the current strict confidence policy and 255 require class-evidence
> remediation. The later expanded inventory is not fully mapped or enriched. The ontology rollout
> initially activated `dish-ontology` v1, `plan` v9 and `feedback` v6;
> current Edge versions are recorded in the production-hardening block below. Fly.io release v125
> is healthy on both checks and serves immutable RE bundle `sha256:3d4cf579d1cf2565`. Snapshot v2
> now preserves all 1,599 canonical/compatibility class lookups. Production workflow 31013721486
> deployed commit `f88d0a2` with bundle `sha256:ffad5c55384244e3`; both legacy class-mapping CSVs
> are absent from the live runtime image and `/readyz` passed.
>
> **Food-intelligence/episode completion release:** migrations 060–065 and seed 147 are live.
> They add the leased enrichment worker and schedules, generic ontology graph, nutrient
> assertions, complete catalogue constraints/regions/recipes/episodes, safe exact-match unknown
> dish promotion, catalogue episode resolution, replay, ML/catalog controls, and research and
> annotation operations. `dish-ontology`, `cron-dish-ontology`, `plan`, `research-panel`, and
> `research-annotations` were deployed. The first full external pass completed for all 802 dishes
> with zero failed or pending jobs; FoodOn matched 104 dishes. A controlled 12-dish USDA demo-key
> evaluation produced four exact matches, five unsafe non-exact matches and three no-record cases.
> Migration 070 and the worker now retain nutrient assertions only for exact normalized USDA
> names; 16 provisional exact-match assertions survived the cleanup. Mobile
> meal episodes are now default-on with compatibility fallback, and the missing-dish submission
> screen is implemented. Migration 065 adds complete assertion/relationship provenance and the
> authenticated consolidated ontology-record API. The production Expo web build is live at
> `https://foofoo-v3.vercel.app`; the post-deploy persona journey passed on 2026-08-05 with
> meal-episode rendering, feedback, recipes, slate persistence and evidence publication verified.
> The later polished mobile shell was reconciled with the same server-authoritative 7×3 weekly
> planner and live episode surface; production workflow `31006023576` passed after deployment.
> The RE eligible-set/episode release is live: Fly workflow `31028623979` passed and
> `https://ghar-re.fly.dev/readyz` reports ready with immutable bundle
> `sha256:ffad5c55384244e3`.
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
> **Normalized policy and recommendation lineage:** migrations 070–072 are live. USDA evaluation
> runs/items are durable, Groq field policies and immutable review/AI assertion lineage are
> database-enforced, and recommendation requests, contexts, feature snapshots, runs, candidates
> and candidate stages are normalized. The production backfill contains 53 linked slates/runs,
> 192 candidates and 192 stage records, with no unlinked slate. `plan` and
> `cron-dish-ontology` were redeployed against these contracts.
>
> **Shared-household collaboration:** migrations 073–074 are live and ledgered. They enforce
> one active owner per household, records membership lifecycle history, supports atomic owner
> transfer, role change, revoke, leave, invite creation and invite acceptance, and exposes
> membership-aware RLS. Invite tokens are stored only as SHA-256 hashes. `household-access` v2,
> `recommendations` v18 and `plan` v19 are live; recommendation reads accept any active role while
> plan writes require owner or planner. `feedback` v14 separates the authenticated actor from the
> selected household and enforces the complete role matrix: owner/planner control plans; cook can
> record execution and missing ingredients; members can record attributable preference feedback;
> viewers are read-only. Production validation and rollback-only role-transition
> smoke tests and an authenticated cross-user anti-probing validation passed with zero invalid
> households. The mobile household screen now discovers and selects joined households, accepts
> one-time invite tokens, and supports owner invite, role, transfer and revoke operations plus
> member leave. Plan requests, feedback, offline feedback queues and persisted query caches are
> scoped to the authenticated user and selected household. Commit `323f470` passed backend and
> mobile CI. The repaired seven-day Home and segmented weekly-plan flows passed production persona
> workflows `31027622263` and `31032523507`; the latter also redeployed Expo web and published its
> HTML, Excel and ZIP evidence. Final production health and authentication workflow `31032523928`
> passed.
>
> **Production hardening:** migrations 057–059 are live. They close all audited trigger-function
> execute grants, all 77 missing leading foreign-key indexes and both duplicate-index findings;
> automate a six-month event-partition horizon; provision a household and owner membership for
> every new profile; backfill existing tenant IDs; and enforce non-null household ownership on the
> five household-scoped fact/context tables. The initial hardening release used
> `recommendations` v11, `plan` v13 and `feedback` v7; current versions are recorded above.
> GitHub's `Production` environment now requires review and
> permits deployments from `main` only.
>
> **Latest production release:** search/filter UI, cached live
> weather context, richer explanation contributions, lock-aware selective refresh, restart-safe
> query/feedback persistence, MMR reranking, offline ranking evaluation, a bounded food graph,
> pinned container bases, staging/manual-production workflows and
> mobile CI are implemented and deployed. The current closure adds canonical episode grammars,
> weekly constraint repair, normalized `food` festival-calendar resolution and explicit-evidence
> household fairness. Migration 075 and validation 930 are live; the calendar tables remain private
> and only the service-role `active_festivals_on(date)` facade is exposed.
> Verification passes: 720 Python tests (27 skipped), 108 Deno tests,
> 31 mobile tests across 15 suites, Python/Deno/mobile type checks and an Expo web export. A full
> 810-dish local load
> run completed 300 requests at concurrency 20 with 0 errors and p95 2.03s.

| Dimension | % |
|---|---|
| Overall Production Readiness | ~78% |
| Architecture | 80% |
| Backend (Edge Functions) | 90% |
| Recommendation Engine | 85% |
| Food Ontology | 92% (production graph/read API, full coverage and governed Groq backfill live; USDA exact-only controlled use active) |
| Knowledge Graph | 70% (normalized production graph with provenance; subjective/festival/substitution breadth remains iterative) |
| Seed Data | 90% |
| Database | 95% |
| Security | 88% (database advisor remediations live; leaked-password screening needs a paid Supabase plan) |
| Testing | 80% (backend suites green — 108 Deno + 720 repository Python tests; 31 mobile tests are green, but physical-device coverage remains) |
| Deployment | 95% (ontology DB/Edge and RE bundle live-verified 2026-08-05; mobile/device release remains) |
| Frontend (mobile) | 70% |
| Observability | 60% (scheduled production smoke/issue alerting added; application 500-level webhook destination remains unconfigured) |

## One-line state per major component
- **RE core/service:** Ghar is the only user-authoritative engine. It exposes the immutable
  642-row production publication but keeps the 810-dish deterministic fallback for requests that
  arrive without a canonical shortlist. Aux is deployed on one isolated Machine against the same
  publication and Qdrant generation, but Edge routing is off. The independent Aux quality run
  `31256081581` is green and remains shadow-only/not active-eligible.
- **Edge Functions:** implemented and tested (108 tests); membership-aware authorization is live
  in `household-access` v2, `recommendations` v18, `plan` v19 and `feedback` v14. The backend
  supports governed invitations, owner transfer and lifecycle history, and enforces distinct
  owner/planner, cook, member and viewer mutation permissions.
- **Mobile app:** onboarding/cold-start/weekly-plan work; complete meal episodes are live on the
  production web client; shared-household discovery, selection, invite acceptance, owner
  administration and member leave are active. Plan/feedback traffic and offline persistence are
  tenant- and user-scoped. Explanation, history,
  profile-edit, and
  DPDP export/delete UI added 2026-08-04 (P0-2/P0-4/P1-2/P1-3/P1-4); jest infra stood up with 9
  pure-logic tests; Expo SDK 53 + OneSignal SDK integration passes typecheck, Expo Doctor, and an
  Android production bundle export; no component-render or physical-device tests yet (P1-5 partial).
- **Database:** protected run `31257431526` measured 3,410 stored dish rows, 3,402 active dishes,
  1,719 with usable class mappings and 646 passing the current presence-based publication gates.
  Of those 646, 547 meet the stricter confidence policy; the deployed immutable generation remains
  642. Earlier continuity evidence recorded 77 profiles on 2026-08-05.
  RLS enabled; household context writes and tenant continuity are fixed and live. All profiles have
  a household and active owner membership, all scoped household IDs are non-null, advisor-reported
  missing FK indexes/duplicate indexes are resolved, and partition creation is automated.
  Migration 073 adds membership history and guarantees exactly one active owner; the live
  validation reports zero invalid households. Migration 075 adds private normalized festival
  identities/occurrences under `food`; validation 930 confirms table privacy and RPC results.
- **Knowledge layer:** normalized ontology and provenance structures are live, but coverage is not
  complete across the expanded inventory. The database currently has 646 presence-eligible rows,
  only 547 meet the stricter confidence policy, and 1,719 active dishes have any usable meal-class
  mapping. Run `31257875325` shows all 255 weak mappings lack curated or human evidence. Missing
  ingredient, cuisine, safety, taxonomy and class facts must be completed under the existing review
  rules rather than bypassed.
  USDA remains exact-match provisional evidence, Groq remains limited to governed low-risk fields,
  and clinically governed health-condition suitability remains pending.

See `docs/active/OPEN_ITEMS.md` for what's actionable, `docs/active/LAUNCH_BLOCKERS.md` for what
gates a public launch, `docs/active/ROADMAP.md` for sequencing.
