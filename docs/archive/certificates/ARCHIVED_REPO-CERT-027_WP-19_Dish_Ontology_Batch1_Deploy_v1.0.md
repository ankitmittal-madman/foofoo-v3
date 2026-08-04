# STATUS

ARCHIVED

## Reason

Implementation completed.

This document is retained for historical reference only.

It must not be used as the primary implementation guide.

Refer to the active documentation for the current source of truth.

---

# [ACTIVE]_REPO-CERT-027_WP-19_Dish_Ontology_Batch1_Deploy_v1.0

**Status:** ACTIVE
**Version:** v1.0
**Date:** 2026-08-03
**Placement:** docs/archive/certificates/ARCHIVED_REPO-CERT-027_WP-19_Dish_Ontology_Batch1_Deploy_v1.0.md
**Certifies:** WP-19 (Dish Ontology & Regional Names) — schema migration 045 + cited alias seed 122 batch 1, committed `aa841f5` / `44795f7`
**Supersedes:** N/A

---

## What this certifies

WP-19 batch 1 was **executed against the live Supabase project** (`cmkswalqpmmqojwdmqbv`) on 2026-08-03 with Founder authorization, via the Supabase Management API `POST /v1/projects/{ref}/database/query`. This records the real execution output so the WP-19 batch-1 work may be read as DEPLOYED. Continued research batches (the remaining ~800 catalogue dishes) are tracked separately and handled in a parallel session.

## Execution evidence

### 1. Pre-state (clean first apply)
`ghar_re.dish_name_synonyms` carried **0 rows** and **none** of the WP-19 columns before apply.

### 2. Applied, in order (each returned success, no error)
- `database/migrations/045_dish_name_synonyms_ontology.sql` → added `alias_type, region, language, source_url, confidence`; `NOT VALID` citation constraint; region index.
- `database/seeds/122_seed_dish_aliases.sql` → 37 cited aliases (8 dishes), each insert `WHERE EXISTS` on the target dish.
- `database/validation/907_dish_ontology_validation.sql` → returned no error (all fail-loud checks passed).

### 3. Post-state (verified in prod)
```
columns present : alias_type, confidence, language, region, source_url
aliases loaded  : 17  (Chole 5, Dhokla 4, Pithla 4, Undhiyu 4)
cited (source)  : 17 / 17
orphans         : 0
```
Only 4 of the 8 batch-1 dishes are currently in the prod catalogue (prod holds the 39-dish
golden sample, not the full 810). The `WHERE EXISTS` guard loaded exactly those 4 dishes' aliases
and skipped the rest without FK failure; the remaining 4 dishes' aliases load automatically (the
seed is idempotent, `ON CONFLICT DO NOTHING`) once the full catalogue is present.

## Critical Self-Review

- **Not the full catalogue.** Batch 1 covers 8 dishes; ~800 remain. This certifies batch 1 only.
- **Prod is golden-sample-only.** The 17 rows reflect the 4 batch-1 dishes present in prod today; this is expected, not a partial failure — re-running the seed after the full catalogue loads completes the batch with no edits.
- **Constraint is `NOT VALID`.** Enforced on all new/updated rows; legacy rows (none exist today) are not retro-validated. Full `VALIDATE CONSTRAINT` can follow once any legacy sources are backfilled.
- **Credentials.** The deploy used a Founder-supplied access token pasted into the session transcript; it and the service/secret keys should be rotated.

## Versioning & Placement
v1.0, first issue. Placed in docs/project-history/certificates/ per the certificate naming standard (WP-5AA). Companion to KNOWLEDGE.html session S50.

## Founder Sign-off

