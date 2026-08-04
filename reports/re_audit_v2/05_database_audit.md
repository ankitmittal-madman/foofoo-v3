# Database Audit (fresh, 2026-08-04) — live-verified via Supabase MCP this session

## Live row counts (executed this session, real production data)

| Table | Rows | Note |
|---|---|---|
| `dishes` | 802 | |
| `ingredients` | 191 | |
| `cuisines` | 66 | |
| `tags` | 125 | |
| `dish_tags` | 11,297 | |
| `dish_ingredients` | 7,108 | |
| `dish_combos` | 35 | |
| `dish_name_synonyms` | 430 | |
| `meal_classes` | 131 | |
| `profiles` | 33 | real users |
| `household_members` | 25 | |
| `household_answers` | 36 | |
| `onboarding_sessions` | 471 | much higher than profiles — many onboarding attempts per completion, or abandoned sessions |
| `consent_records` | 164 | |
| `recommendation_events` | 126 | real recommendations have been served |
| `feedback_events` | **9** | far below any usable training threshold |
| **`week_plans`** | **0** | **despite 126 recommendation events, no weekly plan has ever been persisted** |
| **`plan_slots`** | **0** | same |
| **`household_context`** | **0** | despite the write path being coded and reportedly fixed |
| **`interaction_events`** | **0** | |
| `context_log`, `weather_cache`, `addon_slots`, `audit_log` | 0 | consistent with known-scaffolding/unused status |
| `derivation_conflicts` | 186 | live, actively written by trigger — correctly not a candidate for removal |

**This is the single most important live-database finding**: the gap between 126 served
recommendations and 0 rows in `week_plans`/`plan_slots`/`household_context`/`interaction_events`
means either (a) the persistence write calls are failing silently, (b) they're gated behind a code
path real users haven't hit yet, or (c) the 126 events came from a testing/synthetic source that
bypassed the normal write path. This needs a direct trace, not a guess — flagged as a P0 backlog
item.

## Schema hygiene (live security/performance advisors, executed this session)

- **RLS**: every user-facing table has RLS enabled with a real ownership policy. 12 internal-only
  tables (audit_log, derivation_conflicts, partition children, bandit/suppression state tables)
  show as "RLS enabled, no policy" — this is a known, reviewed pattern (no client grants exist on
  these), not a live gap.
- **Auth**: leaked-password-protection is **disabled** — a real, one-click Supabase Auth setting
  fix, not yet applied.
- **Performance**: ~20 unindexed foreign keys (INFO level — not urgent at current scale), 1
  duplicate index (`tags.idx_tags_vector_position` / `tags_vector_position_key`), several RLS
  policies re-evaluate `auth.uid()` per-row instead of `(select auth.uid())` (a real, cheap
  performance fix at scale, not urgent today given table sizes).
- `pg_net` extension installed in `public` schema rather than a dedicated schema (WARN, low
  urgency).

## Migrations/seeds/validation counts (fresh)
52 migrations, 43 seeds, 9 validation scripts, 72 rollback files — all internally consistent
(every migration has a paired rollback).

## Confirmed dead, correctly disposed of
`re_engine` schema (dropped, migration 047) and `ghar_re` schema (dropped, migration 050) are both
gone from the live database, each with a JSON backup preserved. The `feature_flags` table was
dropped in the latest migration (052) as confirmed-unused scaffolding.

## Confirmed dead, not yet disposed of
`database/etl/generate_re_seeds.py` and 3 validation scripts (`900`, `904`, `905` in relation to
the now-dropped `re_engine` schema pieces) target schemas that no longer exist. Not urgent
(historical artifacts, not live-code risk) but should be archived or clearly labeled.
</content>
