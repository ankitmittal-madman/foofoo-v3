Status: ACTIVE
Version: 1.0
Date: 2026-08-08
Placement: docs/architecture (production deployment and rollback runbook)
Supersedes: None
Dependencies: `.github/workflows/deploy-recommendation-modernization.yml`,
  `.github/workflows/recommendation-modernization-readiness.yml`,
  `.github/workflows/provision-aux-re-fly-app.yml`,
  `.github/workflows/recommendation-catalogue-publication.yml`,
  `.github/workflows/recommendation-catalogue-qdrant.yml`,
  `.github/workflows/recommendation-catalogue-ghar-deploy.yml`,
  `.github/workflows/aux-re-deploy.yml`,
  `.github/workflows/aux-re-mode-control.yml`,
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

Phase A has now been executed in production with Aux routing kept off. This is a deployed
foundation, not a completed rollout: authenticated test-household smoke, load targets, real-outcome
evaluation, shadow observation and any approved canary remain outstanding. A database row count of
3,409 is not the serving count: the immutable publication manifest supplies the exact number and
currently proves 642 active, safety-closed, enriched and class-mapped dishes.

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
| User-visible mode | A successful `Aux RE off and shadow mode control` run records `off` | Run the protected `off` transition, then verify Ghar |
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
| 1 | Audit Phase A configuration | `Recommendation modernization production readiness` with target `foundation` | Name-only evidence says foundation ready; it does not authorize a deployment |
| 2 | Create/verify Aux Fly app | `Provision Aux RE Fly app` | Exact app exists in Ghar's Fly organization; no Machine or code is deployed by this step |
| 3 | Verify/set Edge mode off | `Aux RE off and shadow mode control` with desired mode `off` | The protected transition artifact records `off`; Today/Week remains Ghar-visible |
| 4 | Apply schema 092–101 | `Deploy recommendation modernization schema` | One transaction passes validations 944–953; artifact records `apply` or read-only `validate` |
| 5 | Publish catalogue | `Recommendation catalogue publication` | Exactly three user-free files; manifest has full SHA-256 version, positive row count and closed coverage gates |
| 6 | Upload same version to Qdrant | `Publish recommendation catalogue to Qdrant` using the publication run ID and full version | New hash-named collection is green; point count equals manifest row count |
| 7 | Deploy same version to Ghar | `Deploy Ghar with recommendation catalogue` using the same publication run and version | Ghar `/readyz` passes; `/v1/meta` reports the exact version and positive row count |
| 8 | Deploy isolated Aux service | `Deploy Aux RE in shadow mode` using the Qdrant run ID, same version and exact row count | Aux `/readyz` passes and reports the exact version; Edge remains `off`, so Aux cannot influence a response |
| 9 | Deploy Edge code | `Deploy recommendation Edge Functions` while `AUX_RE_MODE` is still `off` | Both `plan` and `recommendations` deploy; Ghar response remains authoritative |
| 10 | Smoke test | Authenticated synthetic/test household only | Cold-start and experienced-user requests succeed; hard diet/allergen exclusions hold; canonical IDs, selected date and meal class survive end to end |

The publication artifact is one generation of catalogue facts, not a database replacement. It
must not contain user profiles, history or events. Edge reads the user's governed database context
and sends request-scoped features; Ghar and Aux use those features against the same catalogue
version.

### Phase A production execution — 08 August 2026

Founder-approved execution completed Orders 1–9 with production Edge routing kept `off` throughout.
No shadow or active transition was requested or executed.

| Order | Evidence | Result |
|---:|---|---|
| 1 | Run `31252583245` | Foundation configuration ready |
| 2 | Run `31252605522` | `foofoo-aux-re` created in the governed Fly organization |
| 3 | Runs `31252632149` and final reassertion `31253563043` | Production `AUX_RE_MODE=off`; every shadow-only step skipped |
| 4 | Run `31252653075` | Migrations 092–101 and validations 944–953 passed atomically |
| 5 | Run `31252699487` | Publication `sha256:e9c7b524dc5480895d5b675caaa88a51788980cbfb3e1aea95bc5994a7ce3269`; 642 publishable dishes |
| 6 | Run `31252998303` | Exact 642-point Qdrant collection verified |
| 7 | Run `31253028990` | Ghar healthy and exposes the same 642-row publication |
| 8 | Run `31253301316` | One isolated Aux Machine healthy on the same Qdrant generation; Edge still off |
| 9 | Run `31253527126` | `plan` and `recommendations` deployed after 151 Edge tests passed |
| Boundary smoke | Run `31253604331` | Fly health/meta and unauthenticated Edge boundaries passed |
| Aux model quality | Run `31256081581` | 86 tests, model gate, local Qdrant and signed packaged-service shadow flow passed; active promotion remained prohibited |
| Catalogue quality audit | Run `31257431526` | 3,410 stored, 3,402 active, 646 presence-eligible and 547 strict-quality-ready; no serving change |
| Meal-class provenance audit | Run `31257875325` | 255 low-confidence mappings, all provisional internal research; zero curated, human-reviewed or accepted evidence; no serving change |
| Primary/component readiness v1 | Run `31258906340` | Migration 106 live; 1,402 canonical dish-slot routes split into 603 primary-ready, 262 primary review and 537 component review; zero proposals/facts; no serving change |
| Full-inventory serving-role coverage | Run `31259220512` | Migration 107 live; all 3,402 active dishes reconcile: 802 with canonical slots, 2,600 without, 2,596 missing hero roles and 918 with unrecognized slot labels; no serving change |
| Meal-slot source-evidence audit | Run `31267459809` | Migration 108 live; 1,802 single-direct candidates (667 lunch, 566 snacks, 294 dinner, 275 breakfast), 797 contextual review and one conflict; no raw text, proposals or serving change |
| Governed direct-slot proposals | Run `31269668506` | Migration 109 live; exactly 1,802 pending proposals and 7,222 evidence links created (667 lunch, 566 snacks, 294 dinner, 275 breakfast); zero automatic acceptance, publication or serving change; Aux remains off |
| Bounded direct-slot review pack | Repository checkpoint only | Migration 110 plus validation 962 and the protected read-only review workflow pass 28 focused tests, parsing and isolated PostgreSQL sampling/bounds/privacy/rollback execution; no proposal decision or serving change |
| 10 | Not yet executed | Requires an explicitly selected synthetic/test household; do not substitute a real user implicitly |

The Aux process reports its internal policy as `mode=shadow`, meaning it is built to return a
non-authoritative candidate list. This is not the production traffic switch. The Edge secret is the
traffic switch, and the final protected transition evidence records it as `off`; therefore no live
recommendation request is sent to Aux.

The 642 count is the actual safety-closed publication, not the full active dish inventory. At
publication time the coverage report showed 3,402 active dishes, 1,719 class-mapped dishes and 642
fully enriched/safety-closed/publishable dishes. These coverage gaps remain data work; they must not
be bypassed by publishing incomplete rows.

The later audits do not replace that deployed-generation count. They show that the live database
has moved to 646 presence-eligible rows, but only 547 meet the stricter evidence policy. The 255
weak meal-class mappings comprise 99 of those presence-eligible rows plus 156 otherwise-complete
rows still in ontology review. Because none has curated, human-reviewed or accepted evidence, do
not raise confidence or republish them merely by rerunning the legacy classifier. Generate
independently evaluated proposals, route unresolved items to review, then publish a new immutable
generation only after the quality report passes.

### Phase A stop conditions

Stop and roll back serving if any service is unhealthy, any version/count differs, a safety gate
fails, canonical dish or meal-class identity is lost, selected-date context changes, or a workflow
cannot prove its source lineage. Never “fix” a mismatch by editing a published file or an existing
Qdrant collection. Publish a new immutable generation instead.

## 4. Phase B — shadow observation

Only after Phase A passes, configure and ratify the protected load thresholds, run `Recommendation
modernization production readiness` with target `shadow`, and run `Aux RE deployed load report`
for the exact deployed publication. Then run `Aux RE off and shadow mode control` with desired mode `shadow`, the
successful Aux/Ghar deploy run IDs, the signed load run ID, full publication version and exact row
count. The workflow first forces `off`, verifies every source came from `main`, rechecks both live
engines and only then sets the Supabase Edge secrets to `shadow`. Supabase makes updated Edge
secrets available immediately, so a code redeploy is not required for this mode transition (see
[Supabase Environment Variables](https://supabase.com/docs/guides/functions/secrets)).
Shadow must preserve the Ghar response at the authority boundary while recording privacy-minimized
Aux comparison observations.

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

1. Retain the passing `Aux RE deployed load report` used by the mode transition; rerun it if the
   service or catalogue generation changes.
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

1. Run `Aux RE off and shadow mode control` with desired mode `off`. The rollout-control workflow
   must also enforce this automatically when its evaluator returns a kill-switch decision. Both
   workflows share one concurrency group, so an off and shadow mutation cannot race.
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

- The repository provides one protected, serialized `off`/`shadow` transition and deliberately has
  no automated user-visible activation path. A separate household-stable canary mechanism and
  explicit approval design are still required before any active influence.
- The consented real-outcome replay producer and its privacy approval are not yet present. The
  offline evaluator correctly fails closed, so promotion evidence cannot yet be complete.
- Numerical targets exist as governed inputs but require a Product/Founder approval reference;
  engineering defaults are not product ratification.
- The production publication is known: 642 of 3,402 active dishes are deployed. A later audit found
  646 presence-eligible database rows but only 547 strict-quality-ready; a separate provenance
  audit found 255 weak provisional class mappings with no curated or human evidence. The remaining
  rows require governed data completion; the legacy `810` bundle and total database inventory are
  not substitutes for the publication count.
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
