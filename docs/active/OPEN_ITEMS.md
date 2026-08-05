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

- Replace or activate `USDA_FOODDATA_API_KEY` (the controlled worker evaluation returned HTTP
  403), run `ops.requeue_external_provider('usda_fdc')`, and evaluate Indian-dish match quality.
- Expand comfort-hero mapping beyond 17 of 36 resolved heroes.
- Populate the regional-prior table for PanIndia and Global zones; 187 of 810 dishes currently
  receive no regional-prior boost.
- Monitor the ontology-aware Fly release and legacy CSV compatibility fallback for one verified
  rollout window; remove the fallback only after parity and rollback evidence remain clean.
- Create/approve a funded Fly staging app and configure `FLY_STAGING_*` variables/secrets. The
  GitHub `Production` environment is now protected by a required reviewer and a main-only custom
  deployment-branch policy.
- Contract legacy dish/event compatibility tables only after one monitored episode dual-write,
  export/delete and rollback-parity window; no new feature may target those legacy facts.
- Deploy and operationally verify the remaining client/operational release candidate: mobile
  search and filters, richer explanations, selective refresh, restart-safe query/feedback
  persistence, and CI/deployment workflow changes. The ontology database, affected Edge
  Functions, cached-weather/MMR-capable RE image and immutable bundle are live.
- Run production catalogue-scale load/soak tests and revisit Fly.io sizing. The local 810-dish run
  is evidence for local behavior only.
- Replace the current one-profile/one-household compatibility authorization rule with explicit
  membership/role checks before enabling multi-user shared households or invitations. Migration
  059 guarantees tenant continuity for the current product model; it does not by itself launch
  shared-household collaboration.

## P3 — Product and intelligence evolution

- Add festival-calendar mapping.
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

- Production migrations 057–059 resolved exposed trigger-function grants, 77 missing leading
  foreign-key indexes, two duplicate indexes, event-partition horizon automation, post-profile
  household provisioning, tenant backfill, and non-null household ownership on scoped facts.
- The production advisor audit now reports zero unindexed foreign keys and zero duplicate indexes;
  all six trigger-only functions audited in migration 057 have zero client execute grants.
- Event partitions are present through the six-month horizon and are maintained monthly by the
  `foofoo-event-partition-horizon` cron job.
- `recommendations` v11, `plan` v10, and `feedback` v7 are live with household-aware writes; all
  production tenant-continuity validation counts are zero.

## Active implementation documents retained for review

The following specific-phase documents remain active because their completion or continuing value
is not yet certain. They are intentionally not archived:

- `docs/project-history/work-packages/[ACTIVE]_REPO-WP-04DA_Validation_Script_Corrections_v1.0.md`
- `docs/project-history/work-packages/[ACTIVE]_WP-6_Deferred_Knowledge_Register_v1.0.csv`
- `docs/project-history/work-packages/[DRAFT]_WP-12_Per_User_Recommendation_Decision_Trace_v1.0.md`
- `docs/project-history/work-packages/[DRAFT]_WP-14_RE_Intelligence_Roadmap_v1.0.md`
- `docs/project-history/work-packages/[DRAFT]_WP-18_Onboarding_Plan_Recipe_Flow_v1.0.md`
- `docs/project-history/work-packages/[DRAFT]_WP-22_Synthetic_Persona_UI_Journey_Reports_v1.0.md`
