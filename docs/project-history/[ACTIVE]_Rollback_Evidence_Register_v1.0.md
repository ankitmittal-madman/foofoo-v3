# [ACTIVE]_Rollback_Evidence_Register_v1.0

**Status:** ACTIVE — evidence register
**Version:** v1.0
**Date:** 2026-07-13
**Placement:** docs/project-history/[ACTIVE]_Rollback_Evidence_Register_v1.0.md
**Supersedes:** None
**Dependencies:** [ACTIVE]_WP-5C_Rollback_Recovery_Report_v1.0.

---

## Executive Summary

Per-migration record of exactly what each recovered rollback reverses and the evidence it was reconstructed from. Evidence for every entry is the forward migration file of the same number (read this session); for 021–026 that forward file was itself recovered in WP-5B. No rollback drops anything its migration did not create.

## 1. Evidence Matrix

| # | Reverses (objects the migration created) | Rollback action |
|---|---|---|
| 001 | extension pgcrypto; schema re_engine; grants; default privileges | revoke default-priv + grants; `DROP SCHEMA re_engine RESTRICT`; `DROP EXTENSION IF EXISTS pgcrypto` |
| 002 | ingredients, tags, re_states, re_main_cohorts | drop 4 tables (reverse order) |
| 003 | re_personas, re_subcohorts, re_routing_rules, re_meal_classes, public.meal_classes | drop 5 tables |
| 004 | 9 tier-2 re_engine tables (overlap rules → city_migration_overlays) | drop 9 tables |
| 005 | public.profiles | drop 1 table |
| 006 | household_members, onboarding_sessions, consent_records | drop 3 tables |
| 007 | user_re_state, user_taste_vectors, never_list, not_today_suppression, variety_window_state, re_dish_bandit_state | drop 6 tables |
| 008 | public.dishes, public.dish_combos (+ REVOKE on derived columns) | drop 2 tables (REVOKE moot after drop) |
| 009 | dish_ingredients, dish_tags, dish_combo_items | drop 3 tables |
| 010 | derivation_conflicts; 4 functions; 4 triggers | drop 4 triggers, 4 functions, 1 table |
| 011 | week_plans, plan_slots, addon_slots | drop 3 tables |
| 012 | interaction_events, suggestion_logs (partitioned parents), context_log, weather_cache | drop 4 tables |
| 013 | 10 re_engine config tables | drop 10 tables |
| 014 | re_persona_assignment_rules, re_cohort_class_priors | drop 2 tables |
| 015 | audit_log, coverage_gap_log, safety_gate_log, push_notification_logs, feature_flags, etl_job_runs | drop 6 tables |
| 016 | re_engine.dish_features | drop 1 table |
| 017 | initial monthly partitions of the two parents (runtime-named) | `DO` block drops all partitions via pg_inherits |
| 018 | nothing (retired empty placeholder) | no-op (`SELECT 1`) |
| 019 | RLS ENABLE on 19 tables + 23 policies | drop 23 policies, disable RLS on 19 tables |
| 020 | 36 explicit indexes | drop 36 indexes (schema-qualified) |
| 021 | cuisines table; cuisine_id FK on dishes & dish_combos; RLS + policy | drop policy, drop 2 columns, drop table |
| 022 | dishes.calories, serving_size, food_dna_tier_1 | drop 3 columns |
| 023 | tags UNIQUE(dimension,tag_name); fn_assign_tag_vector_positions() (base UNIQUE(tag_name) dropped) | drop function; drop composite unique; restore global unique |
| 024 | re_engine.re_dish_regional_affinity | drop 1 table |
| 025 | dish_combo_items.component_type; re_meal_classes.slot text→text[] | drop column; convert slot text[]→text; restore original CHECK |
| 026 | public.meal_classes.slot text→text[] | convert slot text[]→text; restore original CHECK |

## 2. Evidence provenance

- **001–020:** forward migration files present in the repo since the S1 restructure; never had rollbacks (REPO-WP-02 §6 discovery: "zero rollback files existed for 001–020").
- **021–026:** forward migration files recovered in WP-5B from live-database introspection + repository cross-check; their original rollbacks were lost in the apverse-labs migration ("025/026 rollback precedent" cited in the 027 rollback confirms they once existed).
- **027–028:** rollbacks already present; used as the header/warning style precedent, not modified.

## Critical Self-Review

- **Considered** re-verifying every object name against the live database. **Partially reused** WP-5B introspection (trigger bindings, constraint names) but did not re-query — the forward migration files are the authoritative source per the session-resume discipline (documentation over database), and WP-5C is a repository reconstruction, not a database audit.
- **Limitation:** object *existence* in the live DB is assumed consistent with the forward files (verified for 021–026 in WP-5B; assumed for 001–020, which were applied per REPO-WP-02's certified execution).

## Versioning & Placement

`[ACTIVE]_Rollback_Evidence_Register_v1.0.md` → docs/project-history/. New file.

## Founder Sign-off

Founder acceptance: _______________________ Date: ___________
