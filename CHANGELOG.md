# FooFoo — Master Change Log
*Every code change goes here. Format is at the bottom of this file.*

---

## [Unreleased]

### Deployed
- Applied migrations 070–072 and redeployed `cron-dish-ontology` and `plan`: controlled external
  provider evaluation, exact-only USDA nutrients, normalized recommendation request/run/candidate
  lineage, and database-enforced Groq field/AI assertion policy are live.
- Evaluated USDA's free demo key on 12 Indian dishes (4 exact, 5 wrong-food matches, 3 no record),
  retained 16 exact-match provisional nutrients and removed mismatched provisional assertions.
- Activated budgeted Groq ontology enrichment in production with migrations 066–069 and the
  scheduled `cron-dish-ontology` worker. `openai/gpt-oss-120b` retains low-risk candidates at
  confidence 0.65 and directly publishes allowlisted aliases/tags/regions at 0.80, under atomic
  UTC-day limits of 800 requests and 160,000 tokens. The controlled run completed 9 catalogue
  dishes with zero failed rows and 10,535 tokens used; the remaining backfill continues every ten
  minutes and automatically defers at the free-tier cap. Latest verification reached 11/802
  complete with zero failed rows, 12 requests and 12,665 tokens used.
- Added independent per-dish AI retry state, provider usage reservations/settlement, service-role
  RPC facades, complete model/source provenance, and deterministic guards against canonical or
  component aliases and non-canonical regional shorthand. Safety-sensitive fields are absent from
  both the model schema and database promotion function.
- Published commit `c6321f2` to the production Vercel site and passed the one-persona post-deploy
  journey, including weekly-plan finalization, complete episode rendering, reasoned feedback,
  recipe navigation, slate persistence and validated report artifacts.
- Completed the first external-enrichment attempt for all 802 production dishes with zero pending
  or failed jobs. FoodOn matched 104 dishes; USDA remained isolated at HTTP 403 for the configured
  credential.
- Applied migration 065 and deployed the updated `dish-ontology` function. Canonical dish records
  can now be read through one authenticated provenance-bearing ontology response without exposing
  raw external payloads.
- Deployed `dish-ontology` v5 and `plan` v13; both continue to reject unauthenticated requests.

### Added
- Ontology snapshot v2 contains every one of 1,599 canonical/compatibility class lookup names and
  multi-class memberships. The recommendation runtime now uses only that immutable snapshot;
  legacy mapping CSVs are offline ETL inputs and are omitted from the rebuilt bundle.
- Field-level source, derivation, model, confidence, review and verification metadata for dish
  ingredients, aliases, class mappings, constraints, regional affinities and nutrient assertions.
- Full eligible-set, household-snapshot and episode-response evidence in slate decision traces so
  deterministic recommendation exposures can be reproduced instead of only listing shown items.

### Deployed (food-intelligence foundation)
- Production Supabase received migrations 060–064 and comprehensive seed 147. The live catalogue
  now has normalized recipes, meal episodes, ontology graph edges, nutrition assertions,
  constraints and regional affinities for all 802 canonical dishes, plus scheduled ten-minute
  enrichment and daily reconciliation jobs.
- Deployed the `cron-dish-ontology`, `dish-ontology`, `plan`, `research-panel` and
  `research-annotations` Edge Functions. The first controlled enrichment batch completed 20/20
  jobs; FoodOn evidence succeeded while USDA FoodData Central returned HTTP 403 for the configured
  credential and remains isolated as a provider-level failure.

### Added (food-intelligence foundation)
- A mobile missing-dish submission flow with conservative evidence-based promotion, and normalized
  food graph, nutrition, recipe, meal-episode, ML-control, replay, outcome, research-panel and
  annotation foundations.
- Canonical food-intelligence architecture v2.0 and PRD/database traceability updates; superseded
  PRD, technical-architecture and ontology documents were moved to the historical archive.

### Changed
- Complete meal episodes are now the default mobile planning surface. Published catalogue episode
  identity, ordered slate items, predictions and selection propensity are persisted for replay and
  outcome learning while the established dish/class recommendation path remains a compatibility
  fallback.

### Deployed (earlier)
- Deployed Fly.io release v125 with weekly class-affinity learning and corrected live-vocabulary
  life-stage add-ons. Both machine checks and `/healthz`, `/readyz`, `/v1/meta` pass; the governed
  data bundle remains `sha256:3d4cf579d1cf2565`.
- Production Supabase received migrations 057–059. Live validation reports zero exposed audited
  trigger-function grants, zero missing leading foreign-key indexes, zero duplicate indexes, a
  complete automated six-month event-partition horizon, zero profiles without households/active
  owner memberships, and zero null household IDs in scoped fact/context tables.
- Deployed `recommendations` v11, `plan` v10 and `feedback` v7 with explicit household IDs on all
  affected dual writes. Fly health/readiness/metadata and Edge unauthenticated-boundary probes pass.
- Production Supabase received migrations 054, 055 and 056 plus deterministic ontology seed 146.
  Validation preserved all 802 canonical dishes and produced usable meal-class mappings for all
  of them: 547 enriched and 255 review-routed, with no pending jobs.
- Deployed `dish-ontology` v1, `plan` v9 and `feedback` v6. Unauthenticated smoke tests return
  401 and the ontology CORS preflight returns 204.
- Deployed Fly.io release v124 with ontology-aware bundle `sha256:3d4cf579d1cf2565`; `/healthz`,
  `/readyz` and `/v1/meta` passed after the rolling release.

### Fixed
- Reconnected the polished FooFoo mobile redesign to the server-authoritative weekly class plan
  and complete meal-episode surface. Removed hard-coded 2024 dates and example meal decisions,
  restored persisted 7×3 finalization, and added regression tests covering all 21 weekly slots
  plus breakfast, lunch and dinner episode sections. Production persona run `31006023576` passed.
- Reconciled the production persona driver with the meal-episode-first UI contract. Stable episode
  test hooks now cover primary meals, alternatives, locks, reasoned rejection, make-this feedback
  and recipe navigation instead of waiting for retired dish-card selectors.
- Made the Edge recommendation contract deployable without schema drift: the runtime mirror lives
  inside the Supabase function bundle, and both backend workflows reject any byte-level difference
  from the canonical root contract.
- Added database-enforced profile-to-household continuity and tenant attribution. New profiles are
  provisioned transactionally; historical gaps were reconciled before household columns became
  non-null.
- Added monthly event-partition maintenance with an auditable run ledger and a rolling six-month
  horizon. Removed advisor-reported duplicate indexes and added missing leading FK indexes.
- Weekly class planning now generalizes explicit dish affinities into a bounded, explainable class
  contribution, closing the gap where daily ranking learned but the next weekly plan did not.
- Life-stage add-ons now accept the live household-member vocabulary (`weaning`, `child`,
  `senior`) in addition to historical core aliases.
- Protected the GitHub `Production` environment with a required reviewer and main-only deployment
  branch policy.
- The ontology layer now feeds the current recommendation engine through a deterministic,
  content-hashed `food_ontology_snapshot.json` bundled at build time. Runtime lookup preserves the
  existing class-first primary/multi-membership contract and falls back to legacy CSVs for staged
  rollout and non-catalogue fixtures. The class-backing cache is now scoped to its catalogue
  instance, preventing one bundle/test catalogue from contaminating another.
- **Root-caused the "nobody completes onboarding" gap**: live Edge Function logs showed a real
  test signup hitting `household` from a browser (Expo web) and getting a wall of
  `OPTIONS | 401`. The platform gateway's `verify_jwt` check runs on the CORS preflight too,
  which never carries an `Authorization` header by spec — so every browser-based caller failed
  before the real request was ever sent. Fixed in `supabase/functions/_shared/api/handler.ts`:
  `OPTIONS` is now answered directly with CORS headers before the auth pipeline runs. Redeployed
  live to `household`, `recommendations`, `consent` (v5 each).
- `cron-hard-delete`/`cron-retention-purge` previously shipped with `verify_jwt=false` and zero
  application-level auth — a real gap (confirmed not yet live). Added
  `supabase/functions/_shared/auth/service-role.ts` (`requireServiceRole()`), which requires the
  caller's bearer token to exactly match the project's own service_role key. Removed the
  `verify_jwt=false` override in `supabase/config.toml`. Deployed both functions live for the
  first time with the fix already in place.

### Added
- Scheduled production smoke monitoring for Fly health/readiness/metadata and Edge authentication
  boundaries. Failures open or update one GitHub issue; recovery closes it.
- A database-enforced food ontology and meal-taxonomy ingestion gate: normalized evidence,
  confidence/provenance, class-role safeguards, review queues and class-bound candidate views;
  deterministic research ETL/seed/validation; and an authenticated `dish-ontology` Edge Function
  that stages user dishes and queries FoodOn plus optional USDA FoodData Central evidence.
- `CHANGELOG.md` (this file) — initialised by the `install-logging-infrastructure` skill.
- Lightweight client logger `mobile/src/lib/logger.ts` (Expo/React Native, AsyncStorage-backed,
  hot-path friendly) — replaces the bare `console.warn` in `mobile/src/auth/supabaseClient.ts`.
- Transaction export script `ops/scripts/export-txn-logs.mjs` — exports
  `public.recommendation_events` / `public.feedback_events` / `public.interaction_events` /
  `public.suggestion_logs` rows to plain-English per-user and per-system daily log files under
  `ops/logs/session-log/`.
- User Journey Logger `supabase/functions/_shared/logging/userJourney.ts` — plain-English,
  per-profile narrative log built on top of the existing structured
  `_shared/logging/logger.ts`, covering consent, onboarding/household writes, and
  recommendation-request outcomes.
- Decision logger `ghar_re_core/decision_log.py` — logs the Assemble-7 dish-pool decision
  (winners, top alternatives considered, plain-English reasoning) from
  `ghar_re_core/pairing.py`'s `assemble_7()`, using Python's stdlib `logging` in the same
  structured-JSON convention as `ghar_re_service/lifecycle.py`. Logging-only: does not alter
  scoring, ranking, or the plates returned (verified against the golden-master test).
- `logs/hygiene-reports/logging-compliance.md` — logging infrastructure install/compliance report.

### Added
- `database/migrations/041_re_engine_rls_defense_in_depth.sql` (+ rollback) — enables Row Level
  Security on all 34 `re_engine.*` tables (closing a CRITICAL finding from Supabase's security
  advisor) and revokes the stray `anon`/`authenticated` EXECUTE grant on `public.rls_auto_enable()`.
  Verified beforehand that `anon`/`authenticated` already held no `SCHEMA USAGE` on `re_engine`, so
  this is defense-in-depth, not a functional access change.

### Changed
- Live Supabase project (`foofoo-v3`, `cmkswalqpmmqojwdmqbv`) — applied migrations 034–038 (the
  `ghar_re` schema), which existed in the repo but had never been run against the live database.
  Seeded `ghar_re.cuisine_groups`/`cuisines`/`dishes` from `database/seeds/120`/`121`. Confirmed via
  direct row counts that `public.*`/`re_engine.*` catalogue and reference data were already fully
  seeded — an earlier in-session claim that the database was empty was based on a stale row-count
  statistic, not a real count, and was corrected.
- `mobile/src/auth/supabaseClient.ts` — startup env-var check now logs via the new client logger
  instead of a raw `console.warn`.
- `ghar_re_core/pairing.py` (`assemble_7`) — added an optional `household_label` parameter and a
  one-line call to `decision_log.log_assemble7_decision(...)` at the end of the function, after
  the final plate list is decided. No existing behaviour, signature (for existing positional
  callers), or return value changed.
- `ghar_re_core/pipeline.py` (`recommend`) — passes `household["label"]` through to
  `pairing.assemble_7` so decision-log entries can name the household.

### Context (prior session, referenced by this entry)
- `dd2b824` — imported all remaining org dotfiles skills into `.claude/skills/` and amended the
  Skill Activation Policy so every installed skill runs proactively per session need.
- `c7904bb` — recorded that skill-import/activation-policy change as Session 45 in
  `KNOWLEDGE.html`.

---

## Change Log Entry Format

When adding an entry, use this template:

```markdown
## [vX.Y.Z] — [Milestone Name] — YYYY-MM-DD

### Added
- ...

### Changed
- ...

### Fixed
- ...
```

---
*This file lives at the project root. Every Claude Code session that produces code must add an
entry here.*
