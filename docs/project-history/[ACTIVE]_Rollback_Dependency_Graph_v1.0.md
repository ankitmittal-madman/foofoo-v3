# [ACTIVE]_Rollback_Dependency_Graph_v1.0

**Status:** ACTIVE — dependency graph
**Version:** v1.0
**Date:** 2026-07-13
**Placement:** docs/project-history/[ACTIVE]_Rollback_Dependency_Graph_v1.0.md
**Supersedes:** None
**Dependencies:** [ACTIVE]_WP-5C_Rollback_Recovery_Report_v1.0; [ACTIVE]_Rollback_Validation_Report_v1.0.

---

## Executive Summary

The rollback layer must be applied in strict **reverse migration order (028 → 001)**. This document states that order, the specific cross-migration dependencies that force it, and the one intra-layer special case (partitions vs. their parents). Following it, every rollback reverses cleanly; violating it makes a rollback fail loudly (by design).

## 1. Canonical rollback order

```
028 → 027 → 026 → 025 → 024 → 023 → 022 → 021 → 020 → 019 → 018 → 017
    → 016 → 015 → 014 → 013 → 012 → 011 → 010 → 009 → 008 → 007
    → 006 → 005 → 004 → 003 → 002 → 001
```
This is simply the migration sequence reversed. It is correct because a forward migration may depend on objects from any earlier migration, so its rollback must run before those earlier objects are removed.

## 2. Dependency chains that force the order

```
FK / structural dependencies (must drop the dependent side first):

021 cuisine_id FKs (on dishes, dish_combos)   ┐ drop in 021 rollback
024 re_dish_regional_affinity → dishes, re_states │ before 008/002/003 drop those parents
009 dish_* junctions → dishes, dish_combos, tags  │
010 triggers → dish_ingredients, dish_tags, ...   │
011 plan_slots → week_plans, meal_classes         ▼
008 dishes/dish_combos → (cuisines via 021)   ── drop after 021, 022, 024, 025, 009, 010
006 household_members/... → profiles (005)
004 re_engine tier-2 → re_states/personas/... (002,003)
002/003 reference parents ── drop near-last
001 schema re_engine ── drop LAST (RESTRICT fails if any re_engine object remains)

Partition special case:
017 partitions ARE children of 012's interaction_events / suggestion_logs
   → 017 rollback (drop partitions) MUST run before 012 rollback (drop parents).
   Reverse order already guarantees this (017 > 012).

Trigger/function special case:
010 triggers sit ON tables from 002/006/009 (ingredients, household_members,
   dish_ingredients, dish_tags). 010 rollback (drop triggers) runs before those
   tables are dropped — reverse order guarantees it (010 > 009 > 006 > 002).
```

## 3. Impossible / lossy reversals (documented, not blocking)

| Rollback | Nature | Consequence if run on populated data |
|---|---|---|
| 025, 026 | `slot` text[] → text | multi-slot rows cannot be represented → data loss (loud warning; clean while unseeded) |
| 023 | restore global `UNIQUE(tag_name)` | fails loudly if cross-dimension duplicate tag names exist (intended) |
| 027, 028 (pre-existing) | restore original defect constraints | fail loudly on already-loaded rows (intended) |

None is "impossible" in the Class-D sense on the current unseeded database; all are safe now and self-warn for the future.

## 4. Clean-state property

Applied in order (§1) against the current database state, each rollback returns the schema to exactly the state before its migration — i.e. the layer supports a full teardown `028→001` ending at the pre-`001` empty database, and any partial teardown `028→N` ending at the state after migration `N-1`. This is the property that makes the repository reconstructable.

## Critical Self-Review

- **Considered** claiming a fully order-independent rollback set (each with CASCADE). **Rejected** — order-independence via CASCADE would mask real dependency violations; an explicit ordered graph with loud-failing plain DROPs is safer and truthful about the actual dependencies.
- **Limitation:** the graph is derived from FK/inheritance relationships in the forward files; it was not exercised by a live teardown (that is WP-5F).

## Versioning & Placement

`[ACTIVE]_Rollback_Dependency_Graph_v1.0.md` → docs/project-history/. New file.

## Founder Sign-off

Founder acceptance: _______________________ Date: ___________
