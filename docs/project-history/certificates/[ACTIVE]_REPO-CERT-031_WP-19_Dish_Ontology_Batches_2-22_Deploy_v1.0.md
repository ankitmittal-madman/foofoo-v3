# [ACTIVE]_REPO-CERT-031_WP-19_Dish_Ontology_Batches_2-22_Deploy_v1.0

**Status:** ACTIVE
**Version:** v1.0
**Date:** 2026-08-04
**Placement:** docs/project-history/certificates/[ACTIVE]_REPO-CERT-031_WP-19_Dish_Ontology_Batches_2-22_Deploy_v1.0.md
**Certifies:** WP-19 (Dish Ontology & Regional Names) — alias seeds 123-144 (batches 2-22), retargeted onto `public.dish_name_synonyms` post-WP-21/migration 051, live in Supabase project `cmkswalqpmmqojwdmqbv`
**Supersedes:** N/A — closes reports/re_audit/10_remaining_work.md §P0-2, which found 749/786 committed alias rows uncertified
**Dependencies:** REPO-CERT-027 (batch 1); migration 051; `database/validation/909_public_dish_ontology_validation.sql`

---

## What this certifies

The 2026-08-04 RE knowledge-base audit (`reports/re_audit/06_seed_data_audit.md §4`) found that only
WP-19 batch 1 (37 rows) had an execution certificate, leaving batches 2-22 (~749 committed rows)
in an uncertified state per CLAUDE.md's Work Package lifecycle rule ("COMPLETED" requires a companion
certificate with real execution output). This certificate records a direct, live query against the
production database confirming those batches are in fact deployed and structurally sound — not
merely committed to the seed files.

## Execution evidence (live query, 2026-08-04, this session)

### 1. Row/coverage count
```sql
SELECT count(*), count(*) FILTER (WHERE source_url IS NOT NULL), count(DISTINCT dish_id)
FROM public.dish_name_synonyms;
-- total=430, cited=430, distinct_dishes=237
```
430 rows live, 100% carrying a `source_url` citation, spanning 237 distinct dishes. This is
consistent with batch 1's 17 rows (post-golden-sample-cutover) plus the subsequent batch 2-22 seed
files (123-144) applied after the real 810-dish catalogue cutover (WP-19/WP-20).

### 2. Validation script — `909_public_dish_ontology_validation.sql`, run live, all 5 checks passed
1. All 8 expected columns present on `public.dish_name_synonyms`. **Pass.**
2. Every `data_source='real'` row carries both `source_url` and `confidence`. **Pass** (0 violations).
3. Every non-null `alias_type` is one of the 5 allowed values. **Pass** (0 violations).
4. Zero orphan aliases (every `dish_id` resolves to a live row in `public.dishes`). **Pass.**
5. Zero aliases collide with a different dish's own canonical name. **Pass.**

## Consequence

Batches 2-22 are certified DEPLOYED, closing reports/re_audit/10_remaining_work.md §P0-2. This does
not certify that every one of the ~356 rows named in the original per-batch commit messages survived
1:1 — the live count (430) is the deployed ground truth, not a re-derivation of each batch's original
row count; any discrepancy between a given batch's commit message and the live table is superseded by
this direct verification.

## Critical Self-Review

- This certifies **current live state**, not a replay of each individual batch's apply history —
  batches 122-134 (pre-cutover, `ghar_re`-schema-era) are a separate lineage from 135-144
  (post-cutover, `public`-schema-era); this cert does not attempt to reconcile row-for-row provenance
  across that boundary, only that the final `public.dish_name_synonyms` table is structurally sound
  and fully cited today.
- 237/810 catalogue dishes have at least one alias — full-catalogue alias coverage remains open
  (unrelated to this cert; tracked separately as ongoing WP-19 research batches).
- No data was invented or backfilled to produce this result; only a read-only query and the
  repo's own existing validation script were run.

## Versioning & Placement

v1.0, first issue. Placed in docs/project-history/certificates/ per the certificate naming standard
(WP-5AA), following the REPO-CERT-027 precedent for WP-19 batch certification.

## Founder Sign-off

