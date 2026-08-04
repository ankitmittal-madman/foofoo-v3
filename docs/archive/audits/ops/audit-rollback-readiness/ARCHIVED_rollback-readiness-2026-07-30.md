# STATUS

ARCHIVED

## Reason

Implementation completed.

This document is retained for historical reference only.

It must not be used as the primary implementation guide.

Refer to the active documentation for the current source of truth.

---

# Rollback Readiness — 2026-07-30

Deploy scope: not a specific pending deploy — this run audits the full
current state of `database/migrations/`, `database/seeds/`, and
`database/rollback/` on branch `claude/foofoo-skills-dotfiles-e93096`
(HEAD `e7bb584`), per explicit request. REPORT ONLY — no fixes applied,
consistent with this skill's own "auto-fixes: never" declaration.

## Step 1 — Production branch convention

No documented production-branch convention was found. Checked:
- `docs/governance/` — 30 files present (naming standard, APDF, AGRs,
  baseline register, rollback decision log, etc.) — none define a branch
  mapping or environment convention.
- Root `README.md` — no mention of "production", "branch", or "deploy".
- `SYSTEM_STATE.md` — does not exist anywhere in the repo.
- `knowledge-book/operations/core/deployment-guide.md` and
  `environments.md` — path does not exist in this repo.
- No `vercel.json`; `supabase/config.toml` exists (local CLI config only,
  no environment/branch mapping).

Git shows two branches: `main` and `claude/foofoo-skills-dotfiles-e93096`
(current). Nothing in the repo asserts `main` is the deployed-to-production
branch — this is a plausible default, not a documented fact.

**Finding (informational, not guessed):** there is no authoritative
document naming the production branch or an environment map. Recommend the
Founder either point to an existing doc or have one written
(`docs/governance/` per the Placement Rule) before this becomes load-bearing
for a real deploy decision.

## Step 2 — Migration rollback coverage

Compared `database/migrations/` (structural band, 001–038, 38 files) against
`database/rollback/` by basename.

**Result: complete.** All 38 structural migrations (001–038) have a
matching `_rollback.sql` file. No gaps, no orphaned rollback files with no
forward migration.

This matches and extends the prior certified finding in
`docs/archive/reports/project-history/ARCHIVED_Rollback_Evidence_Register_v1.0.md` (which
evidenced 001–026 specifically) and
`docs/governance/[ACTIVE]_Rollback_Decision_Log_v1.0.md` (WP-5C, which
reconstructed 001–030) — migrations 031–038, added since those documents,
also have rollbacks present, though **no evidence-register entry exists yet
for 027–038** (only decision-log precedent, not a per-migration evidence
row). Recommend extending the Evidence Register to cover 027–038 the next
time that document is revised.

## Step 3 — Seed rollback coverage (gap found)

Compared `database/seeds/` (seed band, 100–121, 20 files) against
`database/rollback/`.

**Result: 2 of 20 seed files have NO matching rollback.**

| Seed file | Rollback exists? |
|---|---|
| `100_seed_config_tables.sql` | Yes |
| `101_seed_reference_data_framework.sql` | **No — MISSING** |
| `102_seed_illustrative_content_and_dependents.sql` | **No — MISSING** |
| `103_seed_ingredients.sql` | Yes |
| `104_seed_tags.sql` | Yes |
| `105_seed_cuisines.sql` | Yes |
| `106_seed_dishes.sql` | Yes |
| `107_seed_dish_ingredients.sql` | Yes |
| `108_seed_dish_tags.sql` | Yes |
| `109_seed_dish_combos.sql` | Yes |
| `110`–`117`, `120`, `121` | Yes (all present) |

**CRITICAL finding.** `101_seed_reference_data_framework.sql` (135 lines)
seeds illustrative rows into 15 `re_engine` reference tables (re_states,
re_main_cohorts, re_personas, re_subcohorts, re_routing_rules,
re_meal_classes, overlap_rules, class_dish_options, addon classes/options,
cohorts, weekly_class_plans, household_addon_plans, nonveg_logic,
city_migration_overlays) — per its own header comment, this is a deliberate
partial/illustrative seed (IDR-001), standing in for a ~30,000-row dataset
not yet available. `102_seed_illustrative_content_and_dependents.sql`
(83 lines) seeds ingredients, dishes, dish_ingredients, and dish_tags rows
that 101's reference rows and file `902`'s trigger tests depend on.

If either of these were applied and then needed to be undone (e.g. to
re-seed cleanly once the real ~30,000-row source file arrives, per the
file's own stated intent that "a follow-up seed migration (102+) supersedes
the illustrative rows"), there is currently no authored rollback SQL to do
that with. This is exactly the scenario the files themselves anticipate
("follow-up... supersedes the illustrative rows below") — makes the gap
more likely to actually matter, not less.

This gap is **not mentioned** in the existing Rollback Evidence Register or
Rollback Decision Log — both predate or don't cover the seed band's
completeness, so this is a newly-surfaced finding, not a previously-flagged
and accepted risk.

## Step 4 — Rollback content quality (spot-checked, not stubs)

Sorted all 56 rollback files by line count to find suspiciously thin files,
then read the shortest ones in full:

- `110_seed_re_states_rollback.sql`, `113_seed_re_cohorts_rollback.sql`,
  `114_seed_re_weekly_class_plans_rollback.sql`,
  `115_seed_re_household_addon_plans_rollback.sql`,
  `116_seed_re_nonveg_logic_rollback.sql` (4 lines each) — each is a
  complete, correctly-scoped `DELETE FROM ... WHERE <specific keys> ;`
  wrapped in `BEGIN`/`COMMIT`, on one long line. **Not stubs** — they
  target the exact rows their much-longer forward seed file inserted (e.g.
  113's forward file is 2,967 lines; 114's is 20,678 lines; the corresponding
  rollback deletes by the exact composite keys used on insert).
- `035_ghar_re_household_runtime_rollback.sql` (7 lines),
  `036_ghar_re_safety_support_rollback.sql` (6 lines),
  `037_ghar_re_knowledge_base_rollback.sql` (6 lines) — each is a list of
  `DROP TABLE IF EXISTS` statements, one per table the corresponding forward
  migration created (verified against `CREATE TABLE` statements in 034–037).
  **Not stubs** — correctly scoped, just legitimately short because DDL
  rollback is one line per object.
- No zero-byte or whitespace-only rollback file exists (checked all 56 by
  byte count; smallest non-trivial file is well over 20 bytes).

**No stub/placeholder rollback files were found among the 56 that exist.**
The only defect found is the coverage gap in Step 3, not quality of what's
there.

## Step 5 — Deployment platform rollback path

No Vercel config, no CI/CD deploy workflow found beyond a generic `.github`
directory (not inspected further — out of scope for a DB-focused rollback
check per this repo's evident architecture, which is Supabase Postgres +
Expo/React Native mobile app with Supabase Edge Functions, not a
Vercel-hosted web app). `supabase/config.toml` present (local dev CLI
config only — does not identify a specific hosted project ref or branch
mapping). **Could not verify** whether the currently-live deployment is
identifiable/re-deployable, or whether Edge Function deploys have an
automatic previous-version rollback — this requires either a documented
deployment guide (absent, see Step 1) or live Supabase project access,
neither available to this audit. Flagged as an open item, not guessed at.

## Step 6 — Feature flag / kill-switch coverage

A `public.feature_flags` table exists (created in migration `015`, dropped
in its rollback — confirmed paired). Per
`docs/architecture/[ACTIVE]_DOC-P3-03A_Logic_Governance_Matrix_v1.0.md`
(§ Feature Flag column) and `docs/architecture/[ACTIVE]_DOC-P3-04_Data_
Architecture_ERD_v1.3.md`, this table is the documented mechanism for at
least two named MVP-relevant toggles:

| Feature | Flag-gated | Recommendation |
|---|---|---|
| Festival-aware boosting (`festival_boost`) | Yes — `feature_flags` table, documented "disabled in MVP" | Adequate — already the intended kill-switch pattern |
| Mood selector (`mood_selector`) | Yes — `feature_flags` table, documented "disabled in MVP" | Adequate |
| RE engine version (v1/v2 / shadow mode) | Yes — via `re_engine_versions`, not `feature_flags` directly | Adequate — separate, purpose-built toggle table |
| The two illustrative seed files (101, 102) themselves | **No** — not a runtime feature, but their own header text explicitly anticipates being superseded by a real data load | Not a flag candidate (it's data, not behavior) — the real risk is the missing rollback in Step 3, not lack of a flag |

No new, un-flagged risky runtime feature was found in this pass that
would need a flag it doesn't have.

## Overall verdict

**READY WITH CAVEATS**

- Structural migration rollback coverage (001–038): complete, spot-checked
  for substance, no stubs.
- Seed rollback coverage: **gap** — `101` and `102` have no rollback files.
  Given both are explicitly self-described as temporary/illustrative and
  intended to be superseded, this should be closed before either is
  re-applied or superseded, not treated as low-risk by default.
- Production branch / deployment rollback path: **undocumented** — cannot
  verify instant-rollback capability or migration/code compatibility on
  rollback for real deploys until a deployment guide or live project access
  exists.
- Feature flag coverage: adequate for the two flagged MVP-deferred features
  found; no gap identified.

## Readiness check completed 2026-07-30
Migrations checked: 38 structural + 20 seed = 58 (irreversible/risky: 0 —
all are additive DDL or scoped DELETE, no DROP COLUMN/TABLE-with-data-loss
pattern found without a rollback)
Seed rollback gap: 2 (101, 102)
Deployment rollback path: **Undocumented — cannot verify**
Flag coverage gaps: 0
Verdict: READY WITH CAVEATS
