# Unified Catalogue Source Cutover

**Status:** DRAFT
**Version:** v1.0
**Date:** 2026-08-13
**Placement:** `docs/project-history/work-packages/`
**Supersedes:** Nothing. WP-23 remains the active modernization program; this WP closes one gap WP-23 named ("the serving-catalogue split") but did not itself resolve.
**Dependencies:** RE-DOC-10 §8 (frozen immutable-bundle architecture); migrations 097, 124; `ghar_re_service/scripts/build_catalogue.py`; `ghar_re_service/ghar_re_service/published_catalogue.py`; `ops/recommendation/catalogue_publication.py`

## Executive Summary

Ghar RE and Aux RE currently recommend dishes from two different dish masters. Ghar scores a
809-dish catalogue built at image-build time from a spreadsheet (`data/source/dishes.xlsx`). Aux
retrieves candidates from Qdrant, which is loaded from an entirely separate pipeline that reads
production Postgres through `re_engine.catalogue_publication_rows()`. Neither pipeline reads the
other's output. Nothing in the current architecture prevents the two from drifting, and nothing
detects it when they do.

This is not a guarded, staged rollout awaiting a defined check. Investigation for this WP found no
executed catalogue-parity process, no published catalogue version (`public.catalogue_versions` is
empty), and no scoped task for the Postgres cutover that RE-DOC-10 §8 specifies. The phrase
"remains the production fallback until shadow parity is proven" in migration 097 borrows the
"shadow" vocabulary of the Aux rollout, but the Aux shadow process holds the catalogue constant and
compares engines — it never compares catalogue sources. The condition that comment sets has no
implemented referent.

This WP does two things, in order. Workstream A makes one publication the single source feeding
both engines' delivery mechanisms, so divergence becomes structurally impossible rather than merely
unobserved. Workstream B then promotes that DB-derived catalogue to primary and demotes the static
809-dish bundle to an explicit last-resort fallback, through the staged gate migration 124 already
provides but which has never been used.

Two hard blockers are documented and must be resolved before any cutover. §3: the existing
publication-row-to-Ghar mapper zeroes the signature score for every dish, which would silently
disable a 0.30-weighted scoring term across the entire catalogue if swapped in as-is. §3b, found by
executing this WP's own parity tool: a 2,599-row bulk import on 2026-08-06 filled `public.dishes`
with scraped recipe-website page titles (2,582 active rows contain the word "recipe"), including
duplicate rows for dishes that already exist canonically. The eligibility gate does not check name
quality or duplication, and continued enrichment steadily makes more of these rows publication-
eligible — so dish-identity normalization is now a prerequisite for Workstream B, and the
enrichment programme's "every dish publishable" target needs re-examining independently of this WP.

## 1. Verified Baseline and Evidence Classes

Evidence class is retained per repository philosophy. A live database query, a local file count and
a code comment are not interchangeable.

| Fact | Evidence | Confidence |
|---|---|---|
| Ghar bundle contains 809 canonical dishes | `ghar_re_service/data/bundle/manifest.json` `dish_count`, and a direct count of `catalogue.json` | High for repository artifact |
| Ghar bundle is built from `data/source/dishes.xlsx`, not Postgres | `build_catalogue.py` module docstring and `manifest.json` `catalogue_source` | High |
| Ghar never queries Postgres during scoring or startup | RE-DOC-10 §8; service/container code | High |
| Qdrant is loaded from Postgres via the publication pipeline | `.github/workflows/recommendation-catalogue-qdrant.yml` consumes the `catalogue-publication` artifact; `catalogue_publication.py` reads `re_engine.catalogue_publication_rows()` | High for code path |
| Aux retrieves candidates from Qdrant | `aux_re_service/aux_re_service/retrieval.py` | High |
| Production active dishes: 3,401 | Live query, `re_engine.catalogue_publication_coverage()`, 2026-08-13 | High for that timestamp |
| Production enriched dishes: 2,929 | Same query | High for that timestamp |
| Production safety-closed dishes: 2,925 | Same query | High for that timestamp |
| Production class-mapped dishes: 3,393 | Same query | High for that timestamp |
| Production **publishable** dishes: **703** | Same query, re-measured later the same session | High for that timestamp |
| The publishable count is actively moving | Measured 692, then 703 roughly an hour later while enrichment ran | High — and the reason no figure here may be cited as current without re-measuring |
| No catalogue version has ever been published | Live query: `SELECT count(*) FROM public.catalogue_versions` returns 0 | High for that timestamp |
| Rollout gate has never left its default | Live query: `catalogue_rollout_state.mode = 'OFF'`, `updated_by = 'migration_102_default'` | High for that timestamp |
| 809/809 bundle dishes carry a real `sig_band` | Direct count over `catalogue.json` | High for repository artifact |
| `to_ghar_dish()` sets `sig_band` to `None` unconditionally | `published_catalogue.py` | High |
| `sig_score` carries weight `W_SIG: 0.30` in BASE scoring | `data/source/base_weights.yaml`; `ghar_re_core/scoring.py` | High |
| `sig_scores_v1.csv` is authored, keyed by dish name, and absent from Postgres | `data/sig_scores_v1.csv` (809 data rows); no corresponding table found in schema | High for repository; Medium for the "absent from Postgres" claim, which rests on schema search rather than exhaustive enumeration |

## 2. The Two Confirmed Gaps

**Gap 1 — two dish masters.** Ghar's universe is spreadsheet-derived (809 dishes). Aux's universe
is database-derived (692 publishable dishes at the time of writing). These sets are built by
different code, from different sources, on different schedules, with no cross-check. A dish
enriched in production today reaches Aux's retrieval space but never reaches Ghar's scoring space.

**Gap 2 — the intended primary source was never activated.** RE-DOC-10 §8 specifies a build-time
export that "pulls the current `dishes`, `dish_ingredients`, `cuisines`, and KB tables from
Postgres." What shipped reads a spreadsheet instead. Migrations 097 and 124 built the surrounding
machinery — eligibility gating, immutable versioning, a staged rollout switch — but the switch sits
at `OFF` and no version has ever been written.

## 3. Blocking Finding: Signature Score Fidelity

`published_catalogue.py::to_ghar_dish()` already translates a publication row into Ghar's catalogue
constructor shape, and is the natural mapper to reuse for Workstream A. It is, however, written for
a narrower job than a full catalogue swap: re-validating at most 500 dish IDs that Aux has already
selected. For that job, substituting defaults for non-safety fields is defensible. For a whole-
catalogue swap it is not.

Measured substitutions, and their impact if swapped in unchanged:

| Field | Bundle (current) | `to_ghar_dish()` | Impact |
|---|---|---|---|
| `sig_band` | 809/809 real values | hardcoded `None` → `sig_score = 0.0` | **Blocking.** Disables the `W_SIG: 0.30` signature term for every dish |
| `prep_mins` | 807/809 non-zero | hardcoded `0` | Degrades effort/time-based filtering and display |
| `macro` | 50/809 have values beyond calories | `{"calories": ...}` only | Minor; the bundle is itself sparse here |
| `difficulty` | authored | defaults to `"intermediate"` | Moderate; affects effort filtering |
| `serving_temp`, `fermentation`, `scope_tier`, `sweetness` | authored | default to `"hot"`, `"none"`, `"experimental"`, `0` | Moderate, field-dependent |

The `sig_band` case is the blocker. `sig_scores_v1.csv` is an authored artifact keyed by dish name
that has no representation in Postgres, so the publication row cannot supply it today. Two options,
to be decided before Workstream A completes:

- **A1 — Overlay at build time.** Join `sig_scores_v1.csv` onto publication rows by canonical name
  during the bundle build. Lowest effort; preserves the current authored-data workflow; leaves a
  name-keyed join in the pipeline, which is fragile against renames.
- **A2 — Migrate signature scores into Postgres.** Add a governed table plus seed, and extend
  `catalogue_publication_rows()` to emit `sig_band`. Higher effort; removes the name-keyed join;
  makes signature score a first-class, reviewable catalogue fact consistent with every other field.

**Recommendation: A2**, with A1 as an interim if Workstream A must land sooner. A2 is the only
option that leaves one source of truth at the end, which is the entire point of this WP.

## 3a. A.1 Executed — Measured Parity Result

Step A.1 was implemented (`ops/recommendation/catalogue_parity.py`, 12 unit tests in
`ops/quality/suites/test_catalogue_parity.py`) and run against the live publication set on
2026-08-13. This is the first time the two catalogue sources have been compared. Results:

| Measure | Value |
|---|---|
| Bundle dishes (Ghar today) | 809 |
| Publication dishes (eligible in Postgres) | 703 |
| Matched by normalized name | 699 |
| **Bundle-only — lost on a straight cutover** | **110** |
| **Publication-only — gained** | **4** |
| Net change | **−106 dishes** |

The 4 "gained" dishes are not the win that number implies. Inspected individually, three are
un-normalized scraped page titles rather than dish names, and two duplicate a canonical dish that
is already present separately:

- `Kerala Chicken Curry Recipe With Freshly Ground Spices` — while `Kerala Chicken Curry` also
  exists as its own row, as does `Kerala Chicken Curry Recipe - Nadan Kozhi Curry` (three rows,
  one dish, all `ontology_status = 'enriched'`)
- `Gujarati Badshahi Pulao Recipe - A Rich Preparation Of Rice, Vegetables, Nuts And Spices`
- `Goan Prawns Vindaloo Recipe`

The realistic read is therefore: a cutover today loses 110 canonical dishes and gains roughly one
genuinely new dish plus three malformed duplicates.

## 3b. Blocking Finding: Scraped-Title Bulk Import in `public.dishes`

Investigating those malformed names surfaced a larger issue that was not visible from aggregate
coverage counts, and which was not known when this WP was drafted.

| Measure | Value |
|---|---|
| Active dishes created on 2026-08-06 (single bulk import) | 2,599 |
| Active dishes with `recipe` in the name | 2,582 |
| Active dishes with names longer than 60 characters | 531 |
| Of the 703 currently publishable, how many carry `recipe` in the name | 3 |

Sampled names from that import include `Achappam Recipe | Kerala Style Fried Rose Cookies`,
`15 Minutes Mexican Fried Rice Recipe`, and both `Aar Macher Jhol Recipe - Bengali Fish Curry` and
`Aar Macher Jhol Recipe - Bengali Style Fish In Tomato Gravy`. These are recipe-website page
titles, complete with pipe separators and descriptive subtitles — not canonical dish names.

Three consequences follow, and they matter beyond this WP:

1. **`public.dishes` is not 3,401 distinct dishes.** Roughly 2,582 of the active rows are scraped
   titles, an unknown but material share of which duplicate the canonical ~800.
2. **The eligibility gate is currently holding, but only incidentally.** Just 3 of 703 publishable
   rows carry a `recipe` name — not because the gate checks name quality (it does not) but because
   these rows mostly still lack complete taxonomy. The gate has no name-normalization or
   duplicate-detection rule at all.
3. **Ongoing enrichment actively erodes that protection.** Every enrichment pass makes more of
   these scraped rows eligible. The 692 → 703 movement observed within a single session is
   consistent with exactly this. Pursuing "every dish publishable" as an unqualified goal would
   progressively fill the recommendation catalogue with duplicate, malformed dish names.

This is a prerequisite for Workstream B, not a footnote: **dish-identity normalization and
de-duplication must precede any cutover**, or the cutover ships scraped page titles to users. It
also warrants re-examining the enrichment programme's current target independently of this WP.

## 4. Workstream A — One Source, Two Delivery Pipes

Goal: both engines' delivery mechanisms are built from one publication run, at one version hash, so
divergence cannot occur silently.

| Step | Deliverable | Gate |
|---|---|---|
| A.1 | ~~**Parity audit tool.**~~ **DONE** — `ops/recommendation/catalogue_parity.py` + 12 tests; first executed run recorded in §3a | Ran read-only against production; no writes. Results in §3a |
| A.2 | Resolve the `sig_band` blocker per §3 (A1 or A2, Founder decision) | Publication rows carry a real signature score for every dish that has one |
| A.3 | Close remaining §3 fidelity gaps in the mapper, or document each residual default as accepted with rationale | No silent defaults; every substitution is either fixed or explicitly signed off |
| A.4 | Repoint `build_catalogue.py` to consume the published artifact instead of `dishes.xlsx` | A.1 shows acceptable parity; bundle builds reproducibly from a named publication version |
| A.5 | Same-version enforcement in CI/deploy: fail if Ghar's bundle and the Qdrant collection derive from different `publication_version` hashes | Deploy blocks on mismatch, proven by a deliberate negative test |
| A.6 | Demote `dishes.xlsx` to reference/manual-override input; update `re-ci.yml`'s `export_bundle --check` accordingly | CI green; source-of-truth documented in one place |

## 5. Workstream B — Promote DB Catalogue to Primary, Static Bundle to Backup

Goal: the design the Founder described — a live, latest, versioned DB-derived catalogue as the
everyday source for both engines, with the static bundle as a genuine last-resort safety net rather
than the de facto primary.

| Step | Deliverable | Gate |
|---|---|---|
| B.0 | **Dish-identity normalization and de-duplication** for the 2026-08-06 scraped-title import (§3b). Prerequisite, added after A.1 surfaced it | Publication contains no scraped page titles and no same-dish duplicates |
| B.1 | Publish a first real catalogue version to `public.catalogue_versions` | Version row exists with positive row count and verified hash |
| B.2 | Coverage decision. Measured today: **−106 net** (110 canonical dishes lost, 4 gained of which 3 are malformed duplicates — §3a). Either accept with rationale, or close the gap first | Explicit Founder decision recorded; figures re-measured at decision time, not cited from this document |
| B.3 | Advance `catalogue_rollout_state` `OFF → SHADOW`: publication runs and is compared, users still served by the existing path | Parity evidence from A.1 reviewed at real scale |
| B.4 | `SHADOW → CANARY`: bounded, reversible slice of real traffic | Guardrails defined and observed; rollback rehearsed |
| B.5 | `CANARY → LIVE` | Founder approval; rollback path proven |
| B.6 | Scheduled re-publish so "latest" stays latest rather than becoming a second stale snapshot | A publication older than its threshold raises an alert |
| B.7 | Document the static bundle explicitly as last-resort fallback, with the conditions under which it is used | No path silently treats it as primary |

## 6. Impacted Files and Dependencies

Identified by direct search; each requires review, not all require change.

**Build and source path**
- `ghar_re_service/scripts/build_catalogue.py` — primary change site (A.4)
- `ghar_re_service/scripts/export_bundle.py` — `CATALOGUE_SOURCE`, manifest provenance
- `ghar_re_service/ghar_re_service/published_catalogue.py` — `to_ghar_dish()` fidelity (A.2, A.3)
- `data/source/dishes.xlsx` — demoted (A.6)
- `data/sig_scores_v1.csv`, `data/dish_macro_v1.csv` — authored overlays; A2 migrates the former

**Publication and delivery**
- `ops/recommendation/catalogue_publication.py` — file-based publisher
- `ops/recommendation/catalogue_db_publish.py` — DB version recorder (B.1)
- `database/migrations/097_publish_scalable_recommendation_catalogue.sql` — row shape extension if A2
- `database/migrations/124_catalogue_version_control_plane.sql` — rollout gate (B.3–B.5)

**Workflows**
- `.github/workflows/recommendation-catalogue-publication.yml`
- `.github/workflows/recommendation-catalogue-qdrant.yml`
- `.github/workflows/recommendation-catalogue-ghar-deploy.yml` — same-version gate (A.5)
- `.github/workflows/re-ci.yml` — `export_bundle --check` (A.6)

**Tests requiring review**
- `ghar_re_service/tests/test_bundle.py`, `test_service.py`, `test_ontology_compatibility.py`
- `ops/quality/suites/test_catalogue_publication.py`, `test_catalogue_publication_workflow.py`,
  `test_catalogue_qdrant_workflow.py`, `test_catalogue_db_publish.py`

**Explicitly not impacted**
- `AUX_RE_MODE` and the Aux shadow/canary rollout. That gate governs which engine's output reaches
  the user and is orthogonal to which catalogue both engines read. This WP does not change it.

## 7. Sequencing

Workstream A precedes Workstream B without exception. Promoting the DB catalogue to primary while
the two engines can still build from different snapshots would make an unverified source
authoritative — the opposite of the intent. Within A, step A.1 precedes all others: no cutover
decision should be made without the parity evidence that step produces.

## 8. Out of Scope

Aux's embedding quality (`local_embedding()` is a deterministic hash encoding, not a trained
semantic model); the ~12,000 stranded candidate assertions awaiting human review; dish photography;
any change to `AUX_RE_MODE`.

## 9. Critical Self-Review

**Where this WP is weakest.** The claim that signature scores are absent from Postgres rests on a
schema search, not an exhaustive enumeration of every table; A.2 must verify before choosing A1 vs
A2. The coverage figures are single-timestamp readings and demonstrably move — the publishable count
changed from 692 to 703 within one session — so B.2 must re-measure rather than cite this document.
The §3b duplicate claim is established for a sampled handful of dishes and by name pattern across
2,582 rows; the true duplicate count against the canonical set has not been computed and needs its
own pass in B.0. Whether the Qdrant pipeline has ever
actually run in production could not be confirmed from the repository: the code path is complete and
the workflows exist, but `catalogue_versions` being empty means there is no durable record of a
successful publish, and Qdrant's live contents were not inspected. Aux's retrieval space may
therefore be empty, stale, or populated by a path not visible here.

**Where a reader could be misled.** §3's impact table compares against the bundle, which is itself
an imperfect baseline — 50/809 dishes have real macros there, so "the bundle has it and the DB does
not" overstates bundle quality for some fields. The parity tool in A.1 should report both
directions, including fields where the DB is richer than the bundle.

**What this WP deliberately does not decide.** The A1/A2 choice and the B.2 coverage trade-off are
Founder decisions, presented with a recommendation but not pre-empted. Executing A.1 does not commit
the repository to a cutover.

## 10. Versioning & Placement

Placed in `docs/project-history/work-packages/` as unresolved, current engineering work per the
Folder Structure rule. Status DRAFT until Founder sign-off. This WP may only move to COMPLETED with
a companion certificate in `docs/archive/certificates/` containing real execution output. Supersedes
nothing; WP-23 remains active and this WP closes one gap it identified.

## 11. Founder Sign-off


