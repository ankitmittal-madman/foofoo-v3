Status: ACTIVE
Version: 1.0
Date: 2026-08-08
Placement: docs/architecture (production deployment and rollback runbook)
Supersedes: None
Dependencies: `.github/workflows/deploy-recommendation-modernization.yml`,
  `.github/workflows/recommendation-catalogue-publication.yml`,
  `.github/workflows/recommendation-catalogue-qdrant.yml`,
  `.github/workflows/recommendation-catalogue-ghar-deploy.yml`,
  `.github/workflows/aux-re-deploy.yml`,
  `.github/workflows/deploy-recommendation-edge-functions.yml`,
  `.github/workflows/aux-re-load-report.yml`,
  `.github/workflows/aux-re-offline-report.yml`,
  `.github/workflows/aux-re-rollout-inputs.yml`,
  `.github/workflows/aux-re-rollout-evidence.yml`, and
  `.github/workflows/aux-re-rollout-control.yml`

# Recommendation Modernization Deployment Runbook

## Executive Summary

This runbook moves FooFoo from the legacy 810-dish serving bundle to one governed, immutable
catalogue generation shared by Ghar RE and Aux RE. It also activates the database structures used
for canonical events, meal-class learning, temporal spacing, governed household context,
catalogue lineage, shadow observations and production guardrails.

Deployment is deliberately staged:

```text
OFF -> schema -> publish once -> Ghar + Qdrant/Aux -> Edge deploy -> smoke
    -> SHADOW -> evidence gates -> approved CANARY -> wider rollout
```

`OFF` means Ghar remains the user-visible recommender. `SHADOW` means Aux evaluates the same
requests but cannot change the response. A canary means a stable, approved subset of households
may receive Aux influence. No existing workflow automatically changes `AUX_RE_MODE` to `active`.

This document does not claim that production has been migrated. A database row count of 3,409 is
not the serving count: the immutable publication manifest supplies the exact number of active,
safety-closed, enriched and class-mapped dishes that are eligible to serve.

## 1. Roles and evidence record

| Role | Responsibility |
|---|---|
| Release operator | Runs protected workflows from `main`, records run IDs and checks exact versions |
| Product/Founder approver | Ratifies quality targets and explicitly approves any user-visible canary |
| Data/privacy owner | Confirms consent basis and approves the real-outcome replay source |
| On-call operator | Watches guardrails and sets `AUX_RE_MODE=off` on any breach |

Create one change record before starting. Record, without copying secret values:

- Git commit SHA and every GitHub workflow run ID;
- production Supabase project reference;
- current Edge `AUX_RE_MODE`, deployed Edge function versions and last known good release;
- current Ghar and Aux Fly release/image identifiers;
- current Ghar and Aux `/v1/meta` responses;
- current catalogue publication version, row count and coverage summary;
- previous Qdrant collection name and its verified point count;
- approved rollback owner, observation window and acceptance-target reference.

Do not put database URLs, access tokens, API keys, user IDs, household IDs, raw requests or raw
events in the change record or workflow artifacts.

## 2. Preconditions — stop if any one fails

| Gate | Required evidence | Failure action |
|---|---|---|
| Source | Commit is pushed to `main`; protected `production` environment approval is active | Stop |
| Project identity | `PRODUCTION_PROJECT_REF` exactly matches the database URL and Supabase CLI target | Stop |
| User-visible mode | Edge secret is explicitly verified as `AUX_RE_MODE=off` | Set `off`, redeploy Edge if required, then verify |
| Ghar fallback | Current Today/Week request succeeds through Ghar with safety filters intact | Stop and restore last known good Ghar/Edge release |
| Backups | Supabase point-in-time recovery/backup is healthy; prior images and catalogue remain addressable | Stop |
| Secrets | Required Supabase, Fly and Qdrant secrets exist in the protected environment | Stop; never print values |
| Targets | Product targets have an approval reference and `ratified=true` | Shadow may run; canary may not start |
| Consent | Real-outcome replay has documented consent and a privacy-approved producer | Synthetic tests may run; real-user quality may not be claimed |

`AUX_RE_MODE=off` is the first operational action and the last rollback safety net. Do not infer it
from the Aux service's own `mode=shadow`; the Edge secret controls whether Aux can affect serving.

## 3. Phase A — deploy foundations while Aux influence is off

Run each step separately. Save its successful run ID before continuing.

| Order | Action | Workflow / check | Required result |
|---:|---|---|---|
| 1 | Verify/set Edge mode off | Protected Supabase secret operation, then redeploy `Deploy recommendation Edge Functions` if the secret changed | Edge is healthy; Today/Week remains Ghar-visible |
| 2 | Apply schema 092–101 | `Deploy recommendation modernization schema` | One transaction passes validations 944–953; artifact records `apply` or read-only `validate` |
| 3 | Publish catalogue | `Recommendation catalogue publication` | Exactly three user-free files; manifest has full SHA-256 version, positive row count and closed coverage gates |
| 4 | Upload same version to Qdrant | `Publish recommendation catalogue to Qdrant` using the publication run ID and full version | New hash-named collection is green; point count equals manifest row count |
| 5 | Deploy same version to Ghar | `Deploy Ghar with recommendation catalogue` using the same publication run and version | Ghar `/readyz` passes; `/v1/meta` reports the exact version and positive row count |
| 6 | Deploy Aux shadow service | `Deploy Aux RE in shadow mode` using the Qdrant run ID, same version and exact row count | Aux `/readyz` passes; `/v1/meta` says enabled, shadow and exact version |
| 7 | Deploy Edge code | `Deploy recommendation Edge Functions` while `AUX_RE_MODE` is still `off` | Both `plan` and `recommendations` deploy; Ghar response remains authoritative |
| 8 | Smoke test | Authenticated synthetic/test household only | Cold-start and experienced-user requests succeed; hard diet/allergen exclusions hold; canonical IDs, selected date and meal class survive end to end |

The publication artifact is one generation of catalogue facts, not a database replacement. It
must not contain user profiles, history or events. Edge reads the user's governed database context
and sends request-scoped features; Ghar and Aux use those features against the same catalogue
version.

### Phase A stop conditions

Stop and roll back serving if any service is unhealthy, any version/count differs, a safety gate
fails, canonical dish or meal-class identity is lost, selected-date context changes, or a workflow
cannot prove its source lineage. Never “fix” a mismatch by editing a published file or an existing
Qdrant collection. Publish a new immutable generation instead.

## 4. Phase B — shadow observation

Only after Phase A passes, use a protected, audited operation to set Edge `AUX_RE_MODE=shadow` and
redeploy/verify the Edge functions. Shadow must preserve the Ghar response byte-for-byte at the
authority boundary while recording privacy-minimized Aux comparison observations.

Collect at least the ratified observation window, covering:

- cold-start and experienced households;
- breakfast, lunch and dinner separately;
- weekdays and weekends;
- explicit dish and meal-class feedback;
- spacing/repetition and recent-event cases;
- vegetarian, allergy and other hard-safety slices;
- explicit context separately from governed probabilistic context;
- catalogue version, timeouts, fallback and error behaviour.

Then run, in order:

1. `Aux RE deployed load report` against the deployed shadow service.
2. `Aux RE governed offline report` against a consented, household-disjoint, time-split real-outcome
   replay. Synthetic input is supporting evidence only.
3. The production shadow/guardrail aggregation for the exact observation window.
4. `Aux RE governed rollout inputs` with the exact catalogue generation and ratified targets.
5. `Aux RE rollout evidence` to compose offline, load and live aggregate proof.
6. `Aux RE rollout control` to evaluate the package. It may enforce `off`; it never activates Aux.

Any missing report, version mismatch, insufficient sample, unratified target or absent consent is
a failed promotion gate, not an exception to document away.

## 5. Phase C — approved canary

A canary requires explicit Product/Founder approval referencing the exact evidence package. It
must use a stable household assignment so the same household does not oscillate between policies.
Start with the smallest approved percentage and keep Ghar available as the fallback.

For every canary window, verify the ratified limits for:

| Category | Minimum decision signal |
|---|---|
| Safety | Zero prohibited diet/allergen/never-list violations |
| Reliability | Error, timeout, fallback and latency targets pass |
| Catalogue | Zero publication-version mismatch; candidate count is exact |
| Product quality | Acceptance/non-rejection and diversity/repetition targets pass overall and by required slice |
| Learning | Experienced users improve over cold-start without suppressing exploration or over-repeating dishes/classes |
| Context | Explicit facts outrank inferred context; low-confidence inference cannot become a hard restriction |
| Explainability | Every served choice has allowed reason codes and decision lineage |

Increase exposure only through a new approval backed by a new complete window. Never jump from
shadow directly to broad active serving.

## 6. Immediate serving rollback

Rollback order is designed to restore the user experience first:

1. Set Edge `AUX_RE_MODE=off` through the protected Supabase operation. The rollout-control
   workflow must enforce this automatically when its evaluator returns a kill-switch decision.
2. Verify an authenticated Today/Week request is served successfully by Ghar and hard safety still
   holds.
3. If Edge itself is faulty, redeploy the last known good Edge commit while keeping mode `off`.
4. If Ghar is faulty, redeploy its last known good image and previous immutable publication; verify
   `/readyz` and `/v1/meta` before closing the incident.
5. If Aux is faulty, remove it from request flow by keeping Edge off, then redeploy its last known
   good image/collection for diagnosis. Aux recovery is not on the critical user-serving path.
6. Preserve the failed and previous Qdrant collections, manifests, reports and release IDs during
   the investigation. Do not mutate or delete them as part of immediate rollback.

The additive migrations 092–101 remain in place during an ordinary serving rollback. Their
presence does not require Aux influence and retaining them preserves event and decision evidence.

## 7. Exceptional database rollback

Database rollback is a separate reviewed change, not an incident reflex. It is allowed only after
all code that reads/writes the new schema is rolled back, data impact is assessed, and a verified
backup/export exists.

Use the paired non-seed rollback files in strict reverse order: `101, 100, 099, 098, 097, 096,
095, 094, 093, 092`. Run them under the same production identity verification, serialization and
transaction discipline as deployment. Review whether dropping event lineage or context state
would destroy evidence before approval. Never run seed rollback files as schema rollback.

After an exceptional rollback, rerun the prerequisite validations, smoke Ghar in off mode and
attach aggregate results to the incident record. Restore from backup instead of improvising if
the reverse migration cannot prove data preservation.

## 8. Completion record

The modernization release is complete only when all of the following are recorded:

- schema deployment and validation artifact;
- immutable publication manifest with exact publishable count and coverage;
- matching Ghar metadata, Qdrant count and Aux metadata;
- Edge mode history and deployed commit;
- passing smoke, load, consented offline and live shadow reports;
- ratified target policy and approval reference;
- canary decision, observation window and slice results;
- kill-switch rehearsal and last-known-good recovery proof.

Until then, describe the state precisely as “implemented”, “deployed off”, “shadowing” or
“canary”; do not call it fully active or validated.

## 9. Critical Self-Review

- The repository currently provides an automated fail-safe path to `off`, but no dedicated
  protected workflow for a human to move exactly `off -> shadow` or to manage a household-stable
  canary. That control must be added before live shadow/canary activation.
- The consented real-outcome replay producer and its privacy approval are not yet present. The
  offline evaluator correctly fails closed, so promotion evidence cannot yet be complete.
- Numerical targets exist as governed inputs but require a Product/Founder approval reference;
  engineering defaults are not product ratification.
- The live publishable count is unknown until the production publication workflow runs. `3,409`
  database rows and the legacy `810` bundle are inventory observations, not the new serving count.
- A protected workflow does not prove backup health, secret correctness or on-call readiness;
  those remain operator assertions with external evidence.

## 10. Versioning & Placement

This ACTIVE v1.0 runbook lives in `docs/architecture` because it owns the cross-service production
sequence. Change the version when workflow names, gates, rollout semantics or rollback behaviour
change. Implementation work packages may link here but must not duplicate this operational truth.

## Founder Sign-off

No sign-off is required to keep this runbook ACTIVE. A user-visible canary still requires an
explicit approval reference for the exact catalogue generation, target policy and evidence
package described above.
