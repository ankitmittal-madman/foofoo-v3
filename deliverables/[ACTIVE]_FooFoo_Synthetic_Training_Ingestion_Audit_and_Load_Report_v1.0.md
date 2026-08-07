# FooFoo Synthetic Training Ingestion Audit and Load Report

**Status:** ACTIVE  
**Version:** 1.0  
**Date:** 2026-08-07  
**Placement:** `deliverables/`  
**Supersedes:** None  
**Dependencies:** Canonical Planning Semantics Architecture v1.0; Canonical RE Architecture Final Review v1.0; Food Intelligence and Meal Episode Architecture v2.0; migrations 055–087

## Executive Summary

The two supplied workbooks are generated synthetic training data. They are suitable for governed
offline/shadow learning and QA, but they are not consented production identities, behavioral
events, or persisted user meal plans. The approved destination is therefore the private
`research`/`ml` boundary introduced by migration 087. Direct writes to `auth.users`,
`public.profiles`, household authorization tables, production plans/slates, or production event
tables are prohibited.

The current database is domain-shaped, not Excel-shaped. Production facts, governed food
knowledge, research evidence, ML control state, and operational audit records have separate
owners. A few legacy RE tables originated as spreadsheet-shaped precomputed outputs; the active
architecture explicitly says not to repeat that pattern. This ingestion stores immutable source
rows for lineage, validates and blocks unsafe rows, and writes normalized training entities only
to private research staging.

## 1. Audit Scope and Evidence

The audit used the migration chain through `087_auto_training_control_plane.sql`, paired rollback
and validation SQL, the current training/auto-engine code, the two XLSX files themselves, and the
active RE/food architecture documents. Live anonymous REST access verified `public.dishes`; RLS
correctly prevents anonymous inspection of private user and research tables. A privileged database
URL is required for migration application and execute-mode loading.

| Source | SHA-256 | Classification |
|---|---|---|
| Dataset 1 workbook | `e6efcea356a8e0619869ca54b4bf75c2ab1028ad3c7011c91a429c9aa905a99a` | Synthetic training/QA |
| Dataset 2 workbook | `9bdf7240c2adb7c30ae5226815f66e5e5f3397765488e426b4b5e3839b8641b0` | Synthetic training/QA |
| Canonical training snapshot | Manifest version `foofoo-training-v1` | Derived synthetic ML input |

## 2. Database Structure and Purpose Audit

| Schema/layer | Purpose | Authoritative examples | Derived/private examples | Direct-insert rule |
|---|---|---|---|---|
| `auth` | Supabase account identity | `auth.users` | None | Auth service only; never training import |
| `public` household | Live tenant identity, membership, consent and onboarding | `profiles`, `households`, `household_memberships`, `consent_records` | `household_context` | Application/API only; never synthetic import |
| `public` food | Serving catalogue and governed compatibility surfaces | `dishes`, ingredients, aliases, constraints | taxonomy-current/read models | Only governed food ingestion/publication pipelines |
| `public` planning/events | User-visible plans, immutable exposures and outcomes | `slates`, `slate_items`, `outcome_events` | `week_plans`, compatibility recommendation events | Runtime services only; never generated training plans |
| `food` | Governed ontology, recipes, episodes and evidence graph | ontology nodes/edges, recipes, meal episodes | published episode projections | Governed enrichment/review only |
| `re_engine` | Private configuration and per-user adaptive runtime state | scoring/event configs | taste, cadence, variety and bandit state | Engine functions only; no raw import |
| `research` | Consented studies and isolated research/synthetic evidence | studies/annotations under their consent rules | `auto_training_records`, training source rows | Approved target for this dataset |
| `ml` | Feature/model registry, experiments and training control/audit | feature definitions, model registry | `auto_training_*`, import batches/counts | Approved control-plane target |
| `ops` | Data sources, publication, AI/provider and maintenance audit | data-source/catalog version records | run/task/usage logs | Pipeline audit only |
| retired `ghar_re` | Historical isolated golden-sample schema | None in current target | Historical sample objects | Never load; schema was retired |

### 2.1 Keys, constraints, indexes, policies and triggers

- Production identities use UUID primary keys and tenant-continuity foreign keys; synthetic IDs
  such as `HH-00001` and `U-00001` are not valid production identities.
- Content and research objects use unique canonical/natural keys plus UUID row identities.
- Migration 087 makes research records idempotent on `(target_table, record_key)` and records first
  and last batch IDs plus a monotonically increasing version.
- Public user data is RLS protected. Private `research`, `ml`, `food`, `ops`, and `re_engine`
  objects are not exposed through the public API schema; migration 087 explicitly revokes access
  from `PUBLIC`, `anon`, and `authenticated` and grants its loader surfaces only to `service_role`.
- Runtime derivation, tenant-continuity, append-only event, owner-membership, and catalogue safety
  triggers/functions mean their target tables must not receive ad-hoc imports.
- Existing indexes cover tenant/time access, canonical lookup, batch/run audit, confidence bands,
  queue leasing, and recommendation lineage. The ingestion extension adds batch/source-row and
  normalized-record lookup indexes only.

### 2.2 Authoritative versus derived records

| Record | Authority | Notes |
|---|---|---|
| Account/household membership | Production auth + household APIs | Synthetic workbook identities are never authoritative |
| Canonical food safety and ontology | Governed `public`/`food` publication | External/training data is evidence, never runtime truth |
| Recommendation exposure/outcome | Runtime slate/outcome writers | Workbook recommendation rows are synthetic labels only |
| Weekly plan | Derived live from classes, constraints and state | Never import a workbook plan as production truth |
| Training raw row | Immutable research source row | Authoritative only for what the input file contained |
| Training entity/model | Derived, versioned `research`/`ml` record | Shadow/QA use only; never active without promotion gates |

## 3. Incoming Data Audit

| Dataset | Households | Users | Meal history | Recommendation events | Dish namespace | Decision |
|---|---:|---:|---:|---:|---:|---|
| Dataset 1 | 5,000 | 5,000 | 10,000 | 10,000 | 37 | Accept into private training staging |
| Dataset 2 | 5,000 | 5,000 | 15,000 | 5 | 65 | Accept valid rows; block orphan sample rows |
| Combined derived snapshot | 10,000 | Not production identities | 64,842 normalized interactions | Included in interactions | 86 canonical training dishes | Shadow/QA only |

Dataset 2 contains five orphan rows in each of six relationship checks, including member,
regional, exclusion, consumer, recommendation-household, and recommendation-user references.
Those rows must remain visible in raw lineage with rejection reasons and must not become normalized
training entities. There is no source meal-plan sheet. `weekly_signals.jsonl` contains derived
behavior summaries, not user-approved meal plans.

## 4. Destination Map

| Incoming class | Target | Action |
|---|---|---|
| Raw workbook rows | `research.training_source_rows` | Store immutable payload, file hash, sheet, row number and validation result |
| Import/version metadata | `ml.training_import_batches` | Store deterministic batch, source/generation/transformation versions and counts |
| Canonical training dishes | `research.auto_training_records` | `research.training_dishes`; synthetic-only and lineage-bearing |
| Household feature vectors | `research.auto_training_records` | `research.household_personas`; never `public.profiles/households` |
| Normalized interactions | `research.auto_training_records` | `research.interactions`; never production feedback/outcomes |
| Weekly signals | `research.auto_training_records` | `research.weekly_signals`; never production plans/slates |
| Household graph edges | `research.auto_training_records` | `research.household_preference_edges` |
| Orphan/invalid rows | Raw source table with `rejected` status | Do not normalize or load elsewhere |
| Model artifacts/metrics | Existing `ml.auto_training_model_runs` and artifact registry | Shadow-only; separate promotion remains mandatory |

## 5. Pipeline and Repair Plan

1. Hash and inventory each actual source file; create a deterministic batch ID.
2. Read each workbook row with its real worksheet and Excel row number; preserve the raw JSON
   payload and payload hash.
3. Validate required sheets/fields, duplicate primary keys, types, enums, null critical values,
   and workbook foreign keys. Mark every row accepted or rejected with explicit error codes.
4. Enforce the destination allowlist in code. Any production target request fails closed.
5. Reuse the checked-in canonical transformation outputs for dish ontology, household features,
   interactions, weekly signals, and preference edges, after verifying their manifest checksums.
6. Attach batch, file, dataset, transformation version and source-reference lineage to every
   transformed record.
7. Execute one transaction with an advisory batch lock and idempotent upserts. A rerun skips
   unchanged records and versions only changed records of equal-or-higher confidence.
8. Verify source parity, accepted/rejected counts, relationship closure, synthetic-only invariants,
   private privileges, and zero writes to the production denylist.

## 6. Product-Policy Alignment

The normalized training features retain home state separately from current city, household
composition, cooking capability, member/life-stage signals, weekday/weekend rhythm, dietary and
non-veg patterns, feedback weights, and versioned model evidence. They support class-first and
Food-DNA research without storing precomputed production answers. Infant/toddler/elder/pregnancy/
fitness/diabetic needs remain independent semantic conditions that may route through absorb, swap,
or add logic at runtime; they are not flattened into new persona columns or imported plan rows.

## 7. Security, Privacy and Rollback Decision

The dataset is synthetic, but household dietary and health-like fields are still treated as
sensitive-shaped data. The research tables are service-role only, are excluded from the public API
schema, and cannot be joined into production tenants by the loader. No secret values are stored in
reports or command output.

The schema change is additive. Its paired rollback drops only the new ingestion batch/source-row
objects and removes additive lineage columns; it never deletes production users, dishes, plans, or
events. Applying the rollback after a real training load intentionally deletes only the isolated
training-import lineage added by this change and therefore requires an explicit operator decision.

## 8. Critical Self-Review

- Migration-defined structure can drift from the live database; a privileged audit is required
  before execute mode and the loader fails if its expected private objects are absent.
- The 86-dish training ontology is incomplete and only 43% has ingredient coverage. It cannot
  become canonical safety authority.
- Synthetic offline lift is not production quality evidence. Active model promotion remains
  blocked until consented real events and online shadow/A/B evidence exist.
- Dataset 2's five-row supporting samples are internally inconsistent and are retained only as
  rejected lineage evidence.

## 9. Versioning and Placement

This report governs the first dedicated workbook-to-private-training ingestion implementation.
Later source, schema, transformation, or promotion-policy changes require a new version. Execution
evidence and final counts are appended below only after the corresponding commands have run.

## 10. Execution Results

The content-derived batch is `06a38fd3-ec53-54ab-ab0f-ef04bdf92c44`; its source bundle SHA-256 is
`a5b0390ee59767a7c6c4ef0f5e77e64bee4af393b75d9e79c0abc8bb85a9769b`.

### 10.1 Verified dry run

| Check | Result |
|---|---:|
| Physical workbook rows read | 132,586 |
| Accepted source rows | 132,541 |
| Rejected source rows | 45 |
| Normalized private research records | 113,868 |
| Exact duplicate preference edges skipped | 80 |
| Production records requested | 0 |
| Training dishes | 86 |
| Household feature records | 10,000 |
| Normalized interactions | 64,842 |
| Weekly signal records | 10,000 |
| Unique household preference edges | 28,940 |

The 45 rejected physical rows comprise 40 household-reference failures, five meal-event-reference
failures, and five user-reference failures; some rows fail more than one relationship, so reason
counts sum to 50. The full row numbers and record keys are present in the generated dry-run report
and will be stored in `research.training_source_rows` with `validation_status='rejected'`.
The transformer also found 80 byte-equivalent preference-graph edges sharing the same natural key;
they are reported and collapsed before load rather than relying on the database to reject them.

### 10.2 Automated verification

Focused importer plus related training/auto-engine suites: 58 passed. Ruff, mypy, Python compile,
workflow-YAML parsing, migration validation, and knowledge-page structural checks also pass.
Checksum drift, unsafe destinations, orphan handling, exact-duplicate handling, deterministic batch
IDs, private privileges, rollback presence, and repeatable load behavior are covered.

### 10.3 Privileged load

The protected, confirmation-gated production workflow completed successfully on 2026-08-07 in
8m02s: [GitHub Actions run 31167064957](https://github.com/ankitmittal-madman/foofoo-v3/actions/runs/31167064957).
It verified/applied migrations 087/088, passed validations 939/940, committed the private load,
checked the synthetic-only invariant, and uploaded the non-sensitive report as artifact
`governed-training-ingestion-31167064957-1` (artifact ID `8989623234`, retained for 30 days).

| Live committed result | Count/status |
|---|---:|
| Import status | `completed_with_rejections` |
| Physical source rows retained | 132,586 |
| Accepted source rows retained | 132,541 |
| Rejected source rows retained with reasons | 45 |
| Total normalized private research records | 113,868 |
| `research.training_dishes` | 86 |
| `research.household_personas` | 10,000 |
| `research.interactions` | 64,842 |
| `research.weekly_signals` | 10,000 |
| `research.household_preference_edges` | 28,940 |
| Synthetic production users inserted | 0 |
| Synthetic production meal plans inserted | 0 |
| Synthetic production events inserted | 0 |
| Production targets requested by loader | 0 |

The live public catalogue independently reports **3,409 rows in `public.dishes`**. These are the
production dish records and are separate from the 86 synthetic training-dish records. Anonymous
RLS views of user-owned tables intentionally return no usable production-user/plan census; the
training result is established instead by the fixed private target allowlist, recorded target list,
and the successful post-load synthetic-only verification.

An earlier attempt, run `31166273820`, correctly rolled back its data transaction after discovering
80 exact duplicate preference-edge inputs. The loader was repaired to report and deterministically
collapse those duplicates; the successful run above is the committed batch. Migrations are
additive and idempotent, so the earlier schema application did not duplicate data.

### 10.4 Storage relocation completed

On 2026-08-07 the normalized batch was copied to a dedicated private training Supabase project,
with only the 45 rejected raw rows retained in PostgreSQL. Protected cleanup then removed all
132,586 raw source rows and all 113,868 workbook-seed normalized records from production. The 461
synthetic Auto Engine records initially preserved by that operation were subsequently copied and
verified in training before exact production cleanup in protected workflow run
[31178058011](https://github.com/ankitmittal-madman/foofoo-v3/actions/runs/31178058011).
Production now contains zero synthetic records from these two governed batches; the training
project contains 114,329 normalized records in total. This move did not activate a model or change
the user-facing recommendation path. Full evidence, secret boundaries and recovery instructions
are recorded in
`deliverables/[ACTIVE]_FooFoo_Synthetic_Training_Storage_Relocation_Report_v1.0.md`.

## 11. Remaining Gaps

- The 45 rejected workbook rows require source-data repair before they can enter normalized
  training records; their exact sheet, row, key and rejection reasons remain in private training
  storage for audit.
- The synthetic ontology has only 86 training dishes and incomplete ingredient coverage, so it
  remains unsuitable as production catalogue or safety authority.
- No synthetic model is promoted to the active recommender. Promotion still requires consented
  real feedback, shadow evaluation, quality/fairness gates, and an explicit approval workflow.

## Founder Sign-off

Founder acceptance: _______________________ Date: ___________
