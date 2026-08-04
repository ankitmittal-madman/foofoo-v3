# STATUS

ARCHIVED

## Reason

Implementation completed.

This document is retained for historical reference only.

It must not be used as the primary implementation guide.

Refer to the active documentation for the current source of truth.

---

# Data Integrity Audit

Report only. Live Supabase project `cmkswalqpmmqojwdmqbv` (foofoo-v3). FK relationships and NOT-NULL-equivalent completeness discovered live from `information_schema` rather than assumed. No data was modified.

## Context: current data state
Catalogue/reference tables are seeded; all transactional/user tables are empty (pre-launch, no real users yet):

| Table | Rows |
|---|---|
| dishes | 802 |
| ingredients | 191 |
| cuisines | 66 |
| tags | 125 |
| dish_tags | 11,297 |
| dish_ingredients | 7,108 |
| meal_classes | 131 |
| profiles / household_members / week_plans / consent_records / interaction_events | 0 |

Because transactional tables are empty, FK-violation checks against `profiles` (interaction_events, suggestion_logs, week_plans, consent_records, context_log, coverage_gap_log, push_notification_logs → profiles) are trivially 0/0 right now — that is a true "clean" result, not a false negative, but it means this round of the audit really only exercised the **catalogue-data** integrity, which is the one part of the schema with real rows to check.

## Referential Integrity (catalogue tables, formally FK-constrained)

| Relationship | Violations | Severity |
|---|---|---|
| dishes.cuisine_id → cuisines.id | 0 | — |
| dishes.parent_dish_id → dishes.id | 0 | — |
| dish_tags.dish_id → dishes.id | 0 | — |
| dish_tags.tag_id → tags.id | 0 | — |
| dish_ingredients.dish_id → dishes.id | 0 | — |
| dish_ingredients.ingredient_id → ingredients.id | 0 | — |
| ingredients.can_substitute_id → ingredients.id | 0 | — |
| dish_combos.cuisine_id → cuisines.id | 0 | — |
| dish_combo_items.dish_id → dishes.id | 0 | — |
| dish_combo_items.combo_id → dish_combos.id | 0 | — |
| profiles.home_state → re_engine.re_states.state_code | 0 | — |

**Result: zero FK violations found anywhere in the currently-populated data.** The catalogue import (dishes/ingredients/cuisines/tags/combos) is referentially clean.

## Informal references (`*_id` columns not backed by a formal FK constraint)
Discovered via `information_schema.columns` and cross-referenced against the formal FK list. All found instances are **intentional, not bugs**:
- `audit_log.actor_id`, `audit_log.record_id` — polymorphic references by design (an audit log row can point at a row in any table); no single parent table applies.
- `context_log.slate_id`, `suggestion_logs*.slate_id` — a generated correlation UUID grouping one recommendation "slate" across `suggestion_logs`/`context_log`/`plan_slots.slate_dish_ids`. No `slates` table exists in the schema (confirmed — not in `list_tables` output), and migration `012_interaction_audit_appendonly.sql` defines `slate_id` as a bare `uuid NOT NULL` with no `REFERENCES` clause, confirming this is deliberate, not an oversight.
- `onboarding_sessions.screen_id` — a UI screen identifier/slug, not a foreign key.
- `push_notification_logs.onesignal_id` — external OneSignal delivery ID, not a foreign key.

No unenforced/informal reference showed evidence of being an accidentally-uncensored real FK.

## Data Completeness

| Table.Field | NULL/empty count | Why this matters | Severity |
|---|---|---|---|
| dishes.photo_url | **802 / 802 (100%)** | Every dish in the catalogue has no photo. Any dish-card / swipe UI that expects a photo (the RE's core recommendation surface) will render with zero images across the entire catalogue. This is either a genuine pre-launch content gap or a not-yet-run image-import step. | **HIGH** — user-facing, affects 100% of content, not a handful of rows |
| dish_combos: combos with zero `dish_combo_items` rows | **7 / ~N combos** (Sadya Thali, Dal Pakwan, Thali Meals (South Indian), Keema Pav, Chole Bhature (Delhi), Matar Kulcha, Daal Bafla — all `is_active = true`) | These are active, user-servable combos with no component dishes attached. If the RE serves one of these as a suggestion, there is nothing to actually show/cook — a silent empty-plate bug. | **MEDIUM** — small count (7), active, needs manual review per Step 5's <5-vs-≥5 threshold logic (this is just over that threshold) |
| dishes.name / diet_type / cuisine_id / genome_vector / popularity_score | 0 NULL each | Core matching fields are fully populated | — |
| dishes: rows with no linked dish_ingredients or dish_tags | 0 | Every dish has at least one ingredient and one tag link | — |
| ingredients.name, tags.tag_name, cuisines.display_name, meal_classes.display_name, meal_classes.slot | 0 NULL/empty each | — | — |
| dishes.calories | 0 NULL | — | — |

## Step 7 — Completion summary

```
## Audit completed 2026-07-30
FK relationships checked: 11 (all catalogue-side; profile-side relationships have 0 rows to check)
Violations found: 0
Informal *_id references reviewed: 6 (all confirmed intentional, no FK gap)
Completeness issues found: 2
  - dishes.photo_url NULL on 100% of 802 rows (HIGH — flagged for review, not fixed)
  - 7 active dish_combos with zero dish_combo_items (MEDIUM — flagged for manual review per ≥5-row threshold rule)
```

No fixes were applied — this was a REPORT-ONLY round per explicit instruction, and the two completeness findings above are past the "count < 5 auto-fixable" threshold in the skill's own rules regardless.
