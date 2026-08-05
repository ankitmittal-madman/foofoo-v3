# Open Items

This file contains only unresolved work. Completed implementation and the evidence behind earlier
findings are retained under `docs/archive/`.

## P1 — Launch readiness

### Enable Supabase leaked-password protection

- **Area:** Security
- **Status:** Open; explicitly deferred by Founder instruction dated 2026-08-04.
- **Evidence:** Supabase Auth advisor reported the setting disabled.
- **Completion:** Enable it in the Supabase dashboard and verify the advisor clears.

### Configure and verify alert delivery

- **Area:** Observability
- **Status:** Open operational configuration.
- **Evidence:** The webhook sink is implemented, but `TELEMETRY_WEBHOOK_URL` is not configured.
- **Completion:** Configure a real destination and verify a controlled 500-level event arrives.

### Complete physical-device E2E coverage

- **Area:** Mobile testing
- **Status:** Open. Local Jest/component gates exist; device journeys remain.
- **Completion:** Verify offline reconnect, queued-feedback flush, and push delivery on native builds.

## P2 — Production improvement

- Expand nutrition data beyond 50 of 810 dishes.
- Expand comfort-hero mapping beyond 17 of 36 resolved heroes.
- Populate the regional-prior table for PanIndia and Global zones; 187 of 810 dishes currently
  receive no regional-prior boost.
- Apply and live-verify migration 054, including its RLS-policy performance change and rollback.
- Apply the concurrent migration 055, then migration 056 and seed 146; deploy and live-verify the
  `dish-ontology` Edge Function before routing user-added dishes through it.
- Configure `FLY_STAGING_*` variables/secrets and a protected `production` environment.
- Archive dead `re_engine`-era ETL and validation scripts that target retired schemas.
- Resolve unindexed-foreign-key and duplicate-index advisor findings.
- Deploy and operationally verify the local release candidate: cached weather context, search and
  filters, richer explanations, selective refresh, restart-safe query/feedback persistence, MMR
  reranking, offline evaluation, bounded graph traversal, migration 054, and CI/deployment changes.
- Run production catalogue-scale load/soak tests and revisit Fly.io sizing. The local 810-dish run
  is evidence for local behavior only.

## P3 — Product and intelligence evolution

- Add festival-calendar mapping.
- Add health-condition suitability only with appropriate clinical governance.
- Activate `s_pref` personalization after real feedback volume meets a defined training threshold.
- Expand and safety-review the bounded dish/ingredient/substitution graph and its provenance.
- Approve the unknown-dish AI policy: model/data residency, confidence thresholds, safety-field
  treatment, multi-label limits, reviewer workflow and training-data consent.

## Active implementation documents retained for review

The following specific-phase documents remain active because their completion or continuing value
is not yet certain. They are intentionally not archived:

- `docs/project-history/work-packages/[ACTIVE]_REPO-WP-04DA_Validation_Script_Corrections_v1.0.md`
- `docs/project-history/work-packages/[ACTIVE]_WP-6_Deferred_Knowledge_Register_v1.0.csv`
- `docs/project-history/work-packages/[DRAFT]_WP-12_Per_User_Recommendation_Decision_Trace_v1.0.md`
- `docs/project-history/work-packages/[DRAFT]_WP-14_RE_Intelligence_Roadmap_v1.0.md`
- `docs/project-history/work-packages/[DRAFT]_WP-18_Onboarding_Plan_Recipe_Flow_v1.0.md`
- `docs/project-history/work-packages/[DRAFT]_WP-22_Synthetic_Persona_UI_Journey_Reports_v1.0.md`
