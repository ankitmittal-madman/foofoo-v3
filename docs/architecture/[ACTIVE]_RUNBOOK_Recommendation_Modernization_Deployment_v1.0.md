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
| Bounded direct-slot review pack | Run `31270121136` | Migration 110 live; all 1,802 proposals fresh/pending, 7,222 evidence links reconciled (4–8 each), deterministic 10-name-per-slot sample produced with no identifiers/raw source/user data; no proposal decision or serving change |
| Direct-slot proposal provenance | Run `31270627753` | Migration 111 live; all 7,222 links are apply-mode lineage, but every one of the 1,802 proposals reduces to one logical source row from one source file/version repeated across 4–8 runs; repetition is not independent evidence, so every proposal remains pending and no confidence, publication or serving state changed |
| Direct-slot source integrity | Run `31271426471` | Migration 112 live; all 7,222 links identify the exact checked-in source and apply mode, but 7,204 links point to stale `running` imports and only 18 to completed imports; 1,801 proposals therefore fail the run-completion health gate and no decision or serving state changed |
| Dish-import lifecycle correction | Commit `6fa17e0` | Future imports record their actor and close from `running` to exactly one terminal status on success, failure or interruption; historical run statuses were deliberately not rewritten |
| Direct-slot row-manifest integrity | Run `31272114382` | Migration 114 live; a 4,806-row direct-course manifest independently matched every one of the 7,222 proposal links by source row, fingerprint, checked-in file identity and proposed slot, so all 1,802 proposals may enter mapping-policy review; this is evidence verification, not approval or application |
| Direct-slot application boundary | Run `31273351076` | Migration 116 and validation 968 live from commit `314948c`; protected tests and exact production identity passed, while every apply/rollback/Aux-mode step was skipped; the artifact records zero dish, proposal, publication or serving change |
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

The 7,222 direct-slot evidence links must not be read as 7,222 independent confirmations. The
provenance report proves that all 1,802 pending proposals have one distinct logical source row and
one source file/version; each was repeated through four to eight apply-mode import runs. The source
integrity report then proved the exact checked-in file identity while exposing a separate import
health defect: 7,204 links reference historical runs left in `running`, while only 18 reference
completed runs. The ingestion lifecycle now closes future runs safely, but historical status is not
rewritten or treated as proof.

The independent row-manifest report recovered the per-row integrity question without rewriting
history: all 7,222 links match the checked-in source row, row fingerprint and exact proposed slot,
covering all 1,802 proposals. This permits the cohort to enter explicit source-to-slot mapping-policy
review. It does not accept a proposal, mutate `public.dishes`, republish the catalogue or change
serving. Product must still approve the mapping policy—particularly `Appetizer` to `snacks`—before
any reversible application workflow is allowed to run.

### Direct-slot application boundary — installed, policy not applied

The repository now contains a count-bound candidate policy and a protected reversible workflow.
Run `31273351076` installed and validated the additive boundary only. It did not approve the policy,
change a proposal or dish, rebuild a publication, alter serving or touch Aux mode. The exact policy
identity is `direct-import-course-slot-v1` with SHA-256
`2dda4d35c8ab9314c89b6e56ab2d637eb9e7ba1fce9d3f113242813bdb01d3db`.

| Exact checked-in source course | Candidate canonical slot |
|---|---|
| `Lunch` | `lunch` |
| `Dinner` | `dinner` |
| `Snack` | `snacks` |
| `Appetizer` | `snacks` |
| `South Indian Breakfast` | `breakfast` |
| `World Breakfast` | `breakfast` |
| `North Indian Breakfast` | `breakfast` |
| `Indian Breakfast` | `breakfast` |

The policy is valid only for exactly 1,802 proposals, 7,222 evidence links, 4,806 direct manifest
rows and the recorded slot distribution: 275 breakfast, 667 lunch, 294 dinner and 566 snacks. Any
count, row fingerprint, source identity, slot distribution or policy hash drift aborts before a
dish write.

Use `Govern direct meal-slot policy application` only from `main` in the protected production
environment:

1. `install_only` requires confirmation `install-direct-meal-slot-policy-boundary`. It installs
   migration 116 and validation 968 but changes no proposal or dish.
2. `apply` requires confirmation `apply-direct-meal-slot-policy-v1`, a durable Product/Founder
   approval reference and a safe reviewer identifier. The workflow first forces Aux routing off,
   rebuilds the exact policy-bound manifest, then approves and applies the entire cohort in one
   transaction. Every prior and resulting `meal_occasion` array is retained in the service-only
   ledger. This changes database facts but does not alter the existing immutable publication.
3. `rollback` requires confirmation `rollback-direct-meal-slot-policy-v1` and a durable rollback
   reference. It restores all 1,802 arrays only when every current dish still exactly equals its
   recorded applied value. Any later edit makes rollback fail closed. Proposal history remains
   `applied`; the ledger records the active application as `rolled_back`.

Local evidence covers 55 focused tests, the broader 315-pass recommendation gate (one expected
skip), SQL/YAML/shell parsing and a disposable PostgreSQL proof
using the full 1,802/7,222/4,806 cohort. The proof applied exactly, treated the second apply as
idempotent, rejected rollback after deliberate post-apply drift and restored all original arrays
after the drift was removed. This is implementation evidence only, not product approval.

### Contextual multi-slot proposals — generated for review, not applied

The remaining contextual course cohort is deliberately separate from the 1,802 direct proposals.
`Side Dish`, `Main Course`, `One Pot Dish`, `Dessert` and `Brunch` do not identify one exact meal
moment. The candidate policy therefore proposes slot **sets** for review and contains no apply
function:

| Exact checked-in source course | Candidate slot set | Audited dishes |
|---|---|---:|
| `Side Dish` | `lunch,dinner` | 394 |
| `Dessert` | `lunch,dinner` | 247 |
| `Main Course` | `lunch,dinner` | 120 |
| `One Pot Dish` | `lunch,dinner` | 12 |
| `Brunch` | `breakfast,lunch` | 2 |

The exact proposal-only scope is 775 dishes: 773 possible lunch+dinner dishes and two possible
breakfast+lunch dishes. Another 22 dishes whose course field contains a diet value and one dish
with conflicting direct evidence remain deferred. The policy
`contextual-import-course-slot-set-v1` is pinned to SHA-256
`5afca8a6da05a6070abc6678d0a4f73924cafad62835e9152916efe6e7596154` and a deterministic
2,003-row checked-in source manifest. The `Dessert` mapping is explicitly a candidate Product
decision, not accepted food truth.

Use `Generate contextual meal-slot set proposals` only from `main` in the protected production
environment:

1. `install_only` requires confirmation `install-contextual-meal-slot-proposals`. It installs
   migration 118 and validation 970 but creates no proposal or dish fact.
2. `generate` requires confirmation `generate-contextual-meal-slot-proposals-v1`. It verifies the
   production project, exact policy hash, 797 contextual-review denominator, source checksum,
   2,003-row manifest and 775-dish category/slot-set distribution. It may create only pending,
   service-only proposals plus immutable evidence links. It cannot update `public.dishes`, publish
   a catalogue, deploy a service or change Aux mode.
3. Rollback 118 disables further generation while retaining every proposal and evidence row.

Local evidence covers 45 focused tests, SQL/YAML parsing, the broader 318-pass recommendation gate
(one expected skip), and a disposable PostgreSQL proof. The proof generated all 775 pending
proposals, inserted zero duplicates on retry, retained proposal/evidence history after disabling
the generator and changed zero dish rows.

Production run `31274648925` installed migration 118 and validation 970, then generated exactly
775 pending proposals and 3,121 immutable evidence links from the 2,003-row manifest. The artifact
reported `dishes_changed=false`, `serving_changed=false`, `publication_changed=false` and
`pending_review`. Product approval and a separate reversible application design are still required
before any candidate can become a dish fact. Governed mode-control run `31274851421` then recorded
`mode=off` and passed; neither shadow nor active serving is enabled.

### Contextual application boundary — installed, not applied

Migration 120 and validation 972 add the separately governed application boundary. Installation
only extends the private proposal lifecycle and creates a service-only before/after ledger; it
does not review a proposal or update `public.dishes`. The protected workflow supports:

1. `install_only` with confirmation `install-contextual-meal-slot-policy-boundary`.
2. `apply` with confirmation `apply-contextual-meal-slot-policy-v1`, plus a durable Product/Founder
   approval reference and safe reviewer identifier. Application is pinned to exactly 775 proposals,
   3,121 evidence links, the 2,003-row manifest, the existing candidate-policy hash and the 2/773
   slot-set distribution. It forces Aux routing OFF before opening the mutation transaction.
3. `rollback` with confirmation `rollback-contextual-meal-slot-policy-v1` and a durable rollback
   reference. It restores all 775 previous arrays only if every dish and proposal still equals the
   recorded applied state; one later edit refuses the whole rollback.

Local proof covers 324 passing recommendation tests with one expected skip, SQL and YAML parsing,
and a disposable PostgreSQL execution. That execution applied 775, returned `already_applied` on
retry, refused rollback after one deliberate dish drift, restored all 775 after the drift was
removed, and retained all ledger rows when the mutation functions were disabled. This proves the
mechanism only. Production run `31275561817` subsequently installed migration 120 and validation
972. Its install-only artifact records `dishes_changed=false`, `proposals_changed=false`,
`publication_changed=false` and `serving_changed=false`. The five mappings remain unapproved and
no production application has run.

### Final deferred meal-slot evidence audit — prepared, not run in production

The remaining source-evidence denominator contains 23 active dishes with no canonical meal slot:
22 whose imported `Course` value is actually a diet label and one whose source rows contain two
conflicting direct slots. The repository now contains a report-only shifted-field audit for this
exact cohort. It uses the adjacent imported `Cuisine` field only where the checked-in row structure
proves that value was shifted; it never infers from a dish name or exposes dish identity or raw
source text.

The fixed source policy covers 62 malformed rows. It classifies 12 source rows as possible slot
evidence—ten direct and two contextual—and leaves 50 source rows as `unresolved_food_role`. Those
source-row totals are not assumed to equal production dish totals: the protected database report
must independently reconcile the exact 22 deferred dishes, the one direct conflict and every
source-row fingerprint before returning aggregate route counts.

Migration 121, validation 973 and the protected `Audit deferred meal-slot shifted-field evidence`
workflow are additive and service-only. The workflow installs or revalidates the aggregate report,
runs it inside a read-only transaction and uploads one identity-free JSON artifact. It contains no
Aux mode change, catalogue publication or Fly deployment step. Local evidence includes 331 passing
recommendation tests with one expected skip, SQL/YAML/lint gates and a disposable PostgreSQL proof
that returned the exact 22+1 scope, zero manifest failures and then removed the function cleanly.
Successful production aggregate execution and the resulting remediation cohort remain pending; no
mapping is approved or applied by this audit.

The first protected attempt, run `31276361197`, installed and validated the report function but
stopped before query execution because PostgreSQL CSV COPY interpreted an unquoted empty slot key as
`NULL`. It produced no accepted artifact and made no dish, proposal, publication or serving change.
The manifest writer now quotes every field; a regression and direct PostgreSQL COPY proof verify all
62 rows load, all 50 unresolved rows retain an empty string and zero slot keys become null. After
reconciling concurrent audit tests, the full local gate remained at 331 tests with one expected skip
before the protected retry.

Protected retry `31276594131` then passed the exact production audit. Its aggregate-only artifact
proved 22 diet-deferred dishes and one `dinner,snacks` direct conflict. Within the 22, three are
shifted-direct candidates (two breakfast and one dinner), two are shifted-contextual
`lunch,dinner` candidates and 17 require food-role review. All 88 diet-evidence links matched the
checked-in manifest; zero failed source identity or fingerprint validation. The artifact again
records `automatic_acceptance_allowed=false` and zero dish, proposal, publication or serving
change.

### Final deferred case boundary — prepared, not installed

Migration 122 and validation 974 define a private, RLS-enabled case ledger for the exact 23-dish
result. The five candidate cases retain proposed slot arrays only as pending review evidence; the 17
food-role cases and one direct conflict retain no proposed mapping. A separate immutable evidence
table preserves every source-row fingerprint. The boundary cannot write `public.dishes`, either
existing proposal table, a publication or serving configuration, and it grants clients no access.

`Govern deferred meal-slot cases` separates `install_only` from `generate`. Generation binds the
production project, both policy hashes, 62-row manifest, exact 23-case route distribution, five
candidate slot distribution and 88 diet-evidence links. It also compares full dish meal-slot and
existing proposal-table signatures before and after. Local evidence includes 335 passing
recommendation tests with one expected skip plus a disposable PostgreSQL proof: 23 pending cases,
92 synthetic evidence links, zero duplicate rows on retry, immutable evidence, unchanged dishes and
rollback that disabled generation while retaining all case history. Production install/generation
and every review decision remain pending.

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
