# Open Items

This file contains only unresolved work. Completed implementation and the evidence behind earlier
findings are retained under `docs/archive/`.

## P1 — Launch readiness

### Enable Supabase leaked-password protection

- **Area:** Security
- **Status:** Blocked by the current Supabase plan, not by repository work.
- **Evidence:** The Auth setting remains disabled. A verified Management API attempt to enable
  `password_hibp_enabled` on 2026-08-05 returned HTTP 402; Supabase exposes the Have I Been Pwned
  check on Pro plans and above.
- **Completion:** Approve a Supabase plan upgrade, enable the setting, and verify the advisor clears.

### Configure and verify alert delivery

- **Area:** Observability
- **Status:** Partially complete; repository-owned production smoke alerting is implemented, while
  application 500-level webhook delivery still needs a destination.
- **Evidence:** `.github/workflows/production-smoke.yml` checks Fly health/readiness/metadata and
  Edge authentication boundaries every 15 minutes, opening or updating a GitHub issue on failure
  and closing it after recovery. `TELEMETRY_WEBHOOK_URL` is not configured.
- **Completion:** Configure an approved real webhook destination and verify a controlled 500-level
  event arrives. The smoke monitor is complementary and does not prove application-error delivery.

### Complete physical-device E2E coverage

- **Area:** Mobile testing
- **Status:** Open. Local Jest/component gates exist; device journeys remain.
- **Completion:** Verify offline reconnect, queued-feedback flush, and push delivery on native builds.

## P2 — Production improvement

- Obtain a personal free data.gov USDA key if higher throughput is needed. The public demo key is
  active only for controlled evaluation: 4/12 sampled Indian dishes matched exactly, 5/12 matched
  the wrong food and 3/12 had no record. Non-exact nutrients are now rejected by policy.
- Curate or ingest catalogue dishes for the 13 comfort heroes that remain absent or ambiguous.
  Safe exact/orthographic resolution now covers 23 of 36 unique authored heroes (26 of 39 rows);
  the remaining names require a domain-approved dish or catalogue addition, not a guessed alias.
- Create/approve a funded Fly staging app and configure `FLY_STAGING_*` variables/secrets. The
  GitHub `Production` environment is now protected by a required reviewer and a main-only custom
  deployment-branch policy.
- Contract legacy dish/event compatibility tables only after one monitored episode dual-write,
  export/delete and rollback-parity window; no new feature may target those legacy facts.
- Run production catalogue-scale load/soak tests and revisit Fly.io sizing. The local 810-dish run
  is evidence for local behavior only.

## P3 — Product and intelligence evolution

- Complete WP-23 after its deployed-OFF Phase A foundation: run authenticated cold-start and
  experienced-user smoke on an explicitly selected test household; remediate the 255
  low-confidence provisional meal-class mappings without relabelling their confidence; deploy and
  run the protected primary/component readiness audit; review slot-aware component proposals for
  staples, sides and accompaniments; enrich and map the remaining expanded inventory; update Ghar,
  Aux and publication eligibility only after accepted compatibility evidence and runtime tests
  prove parity; publish one quality-closed immutable generation; ratify and run load gates; then
  collect consented real-outcome and shadow evidence before separately approving any canary. Aux
  remains off until those gates pass. Protected runs `31257431526` and `31257875325` own the
  current aggregate counts and provenance split. Run `31258906340` installed migration 106 and
  measured 603 primary-ready, 262 primary-review and 537 component-review dish-slot routes with
  no accepted component facts. Run `31259220512` completed migration 107's full-inventory
  extension: 802 active dishes
  have canonical slots, 2,600 do not, 2,596 lack hero roles and 918 contain unrecognized slot
  labels. Run the migration-108 aggregate source-evidence audit next; only then design non-serving
  slot and hero-role proposals.
- Add health-condition suitability only with appropriate clinical governance.
- Activate `s_pref` personalization after real feedback volume meets a defined training threshold.
- Expand and safety-review the bounded dish/ingredient/substitution graph and its provenance.
- Monitor Groq free-tier ontology backfill completion and sample low-risk alias/tag/region quality;
  keep safety-sensitive fields excluded regardless of model confidence.

## Recently closed with live evidence

- Founder AI policy is active: Groq `openai/gpt-oss-120b`, candidate threshold 0.65, direct
  low-risk publication threshold 0.80, and daily limits of 800 requests/160,000 tokens. Migrations
  066–069 and the scheduled worker provide independent retries, atomic budget accounting,
  provenance, and deterministic alias/region guards without a routine human-review bottleneck.
- USDA controlled evaluation is complete and durable: migration 070 records labelled runs/items,
  and exact-name confidence `>=0.90` is required before provisional nutrients can be retained.
- Recommendation lineage normalization is live through migration 071: all existing slates are
  linked to request/context/feature/run/candidate/stage facts without fabricating unavailable
  historical scores.
- Migration 072 makes AI field authority a database policy and normalizes AI generation inputs,
  assertion sources, AI-run links and immutable review decisions.
- Production workflow 31013721486 deployed snapshot v2 and passed `/readyz`; the live Fly image no
  longer contains either legacy class-mapping CSV, while parity covers all 1,599 lookup names.
- Migrations 073–074 are live and ledgered with exactly-one-owner enforcement, membership lifecycle
  history, membership-based RLS and service-only permission RPCs. `household-access` v2,
  `recommendations` v17 and `plan` v19 are active; validation 927 and the rollback-only owner
  transfer/revoke smoke 928 and authenticated anti-probing validation 929 passed, and all
  production households have exactly one active owner.
- Shared-household mobile collaboration and the complete feedback mutation matrix are active.
  `feedback` v13 authorizes plan controls for owner/planner, execution and pantry evidence for
  owner/planner/cook, attributable preference feedback for owner/planner/cook/member, and no writes
  for viewer. The client discovers/selects memberships, accepts hashed-token invites, exposes
  owner administration and member leave, and scopes plan requests, feedback queues and persisted
  queries by authenticated user/selected household. Commit `323f470` passed backend and mobile CI.
- The episode/weekly-plan release candidate is fully deployed. All five commit checks passed,
  Fly workflow `31028623979` is green, `recommendations` v18 and `feedback` v14 are active, and
  `plan` v19 already matched the release bundle. Production smoke `31032523928` and persona journey
  `31032523507` passed; the latter deployed Expo web and published HTML, Excel and ZIP evidence.
- Migration 075 implements the target-schema `food.festivals` and
  `food.festival_calendar_occurrences` tables with explicit provenance and a service-role-only
  `active_festivals_on(date)` facade. Production validation 930 passed privacy, authority and
  active-date result checks; the retired `re_engine` calendar was not resurrected.

- Production migrations 057–059 resolved exposed trigger-function grants, 77 missing leading
  foreign-key indexes, two duplicate indexes, event-partition horizon automation, post-profile
  household provisioning, tenant backfill, and non-null household ownership on scoped facts.
- The production advisor audit now reports zero unindexed foreign keys and zero duplicate indexes;
  all six trigger-only functions audited in migration 057 have zero client execute grants.
- Event partitions are present through the six-month horizon and are maintained monthly by the
  `foofoo-event-partition-horizon` cron job.
- `recommendations` v17, `plan` v19, and `feedback` v13 are live with household-aware writes; all
  production tenant-continuity validation counts are zero.

## Recently closed in the repository and production

- Complete meal episodes now have a canonical request/response schema plus published, versioned
  `SINGLE_PRIMARY`, `BASE_WITH_SIDES` and `THALI` runtime grammars. The service validates both
  sides of `/v1/meal-episodes`; mobile compatibility episodes identify themselves as unscored.
- Weekly plans use formal MMR and explicit repair for recent repeats, per-slot weekly caps and a
  rank-one weekend special. Thin catalogues return residual constraint violations instead of a
  false success claim.
- Festival context is resolved from normalized private `food` calendar tables through migration
  075's service-role-only `active_festivals_on(date)` facade.
- Shared-household preference aggregation uses only active members' explicit dish evidence and a
  Nash-style geometric welfare score. Missing member evidence remains missing rather than being
  inferred from demographics.
- `PanIndia` and `Global` are dish provenance zones, not household regions. The household regional
  prior grid already covers every derivable household zone; adding those rows would invent an
  invalid household state and counteract the intentional cold-start foreign-dish policy.
- The weekly-plan persona driver switches between Weekdays and Weekend before clicking the 21
  visible choices, eliminating the hidden duplicate-card selector timeout. Production runs
  `31027622263` and `31032523507` passed.

## Active implementation documents retained for review

The following specific-phase documents remain active because their completion or continuing value
is not yet certain. They are intentionally not archived:

- `docs/project-history/work-packages/[ACTIVE]_REPO-WP-04DA_Validation_Script_Corrections_v1.0.md`
- `docs/project-history/work-packages/[ACTIVE]_WP-6_Deferred_Knowledge_Register_v1.0.csv`
- `docs/project-history/work-packages/[DRAFT]_WP-12_Per_User_Recommendation_Decision_Trace_v1.0.md`
- `docs/project-history/work-packages/[DRAFT]_WP-14_RE_Intelligence_Roadmap_v1.0.md`
- `docs/project-history/work-packages/[DRAFT]_WP-18_Onboarding_Plan_Recipe_Flow_v1.0.md`
- `docs/project-history/work-packages/[DRAFT]_WP-22_Synthetic_Persona_UI_Journey_Reports_v1.0.md`
- `docs/project-history/work-packages/[DRAFT]_WP-23_Recommendation_Modernization_Program_v1.0.md`
