# Migration Recovery Validation Report v1.0 (WP-5B)

**Status:** ACTIVE — Validation report (internal-consistency validation; live-apply deferred)
**Version:** v1.0
**Date:** 2026-07-13
**Placement:** docs/project-history/[ACTIVE]_Migration_Recovery_Validation_Report_v1.0.md
**Supersedes:** None
**Dependencies:** Migration_Recovery_Report_v1_0, Migration_Recovery_Evidence_Register_v1_0, Migration_Recovery_Decision_Log_v1_0.

---

## Executive Summary

Internal-consistency validation of the six recovered migrations (`021`–`026`), per WP-5B Step 8. All checks **PASS**. Validation was performed against the repository files and the read-only live-schema evidence; it did **not** apply the migrations to any database (a clean-room apply on a throwaway branch is recommended in WP-5F, deferred here to honor "inspect only, do not modify the database"). Rollback recovery is scoped and handed to WP-5C (Step 7).

## 1. Validation Checks

| # | Check | Result | Evidence |
|---|---|---|---|
| 1 | Migration numbering contiguous 001–028 | ✅ PASS | `ls` shows 001..028 with no gap |
| 2 | No duplicated objects vs base 001–020 | ✅ PASS | `CREATE TABLE cuisines` and `CREATE TABLE re_dish_regional_affinity` each appear in exactly one file |
| 3 | No conflict with 027/028 | ✅ PASS | 021–026 touch none of 027/028's targets (`re_routing_rules`, `re_weight_ladder_config`) |
| 4 | Dependency chain valid | ✅ PASS | 021 before 022 (cuisine_id FK precedes display cols; ordinals confirm); 024 depends on `dishes`+`re_states` (both from 003/008, present); 025/026 depend on base slot columns (003) |
| 5 | Forward compatibility | ✅ PASS | 027 alters `re_routing_rules`, 028 alters `re_weight_ladder_config` — neither depends on 021–026; recovered files change nothing they read |
| 6 | References / cross-references resolve | ✅ PASS | All FKs point to tables created earlier (`cuisines` 021, `dishes` 008, `re_states` 002) |
| 7 | Validation-script compatibility (900–904) | ✅ PASS (by inspection) | 900 expects `re_meal_classes.slot` as `text[]` with 4-value CHECK and the 60+ object baseline; recovered 025/026 produce exactly that. No 900-series edit needed. |
| 8 | Seed compatibility (100–102; 103_* out of scope) | ✅ PASS | Seed 101/102 load into the reference/content tables these migrations shape; `component_type`/`cuisine_id` are nullable so existing seeds remain valid |
| 9 | AGR consistency | ✅ PASS | AGR-005 (027) and AGR-006 (028) are untouched; 028's header note about migration 024 remains accurate (024 now present, uses `numeric` — consistent) |
| 10 | No fabricated business logic | ✅ PASS | Only recovered logic is `fn_assign_tag_vector_positions()` (verbatim) and two `USING` expressions (flagged, evidence-forced) |
| 11 | RR-01 (Critical) resolved in-repo | ✅ PASS | `re_engine.re_dish_regional_affinity` now has a CREATE statement in `024_*.sql` |

## 2. Confidence Score

**Aggregate: HIGH (0.95).** Per file: 021 High; 022 High; 023 High (function verbatim); 024 High; 025 High-on-state / Medium-on-conversion-text; 026 High-on-state / Medium-on-conversion-text. The 0.05 residual is entirely the two reconstructed `USING` expressions and the un-reproduced grants/comments — none of which affect a structural rebuild.

## 3. Residual Uncertainty

1. The `ALTER … USING` expressions in 025/026 are reconstructed (result verified; text not). If a multi-slot row existed at original apply time whose scalar value was not `addon`, the expression still maps correctly; the risk is only cosmetic-textual.
2. Live-apply not executed (by design). A clean-room apply of 001–028 to a disposable branch, diffed against production, would upgrade the two Medium sub-scores to High — recommended for WP-5F.
3. Table grants/comments not reproduced (provenance = migration 001 defaults; cosmetic).

## 4. Rollback Feasibility (Step 7 — analysis only, NO SQL written)

| Migration | Rollback recoverable? | Required WP-5C work |
|---|---|---|
| 021 | Yes | drop policy `cuisines_public_read`; disable RLS; drop `dishes.cuisine_id` & `dish_combos.cuisine_id` FKs/columns; drop `public.cuisines` |
| 022 | Yes | drop 3 columns from `dishes` |
| 023 | Yes | drop `fn_assign_tag_vector_positions()`; swap `UNIQUE(dimension,tag_name)` back to global `UNIQUE(tag_name)` |
| 024 | Yes | drop `re_engine.re_dish_regional_affinity` |
| 025 | Yes, **with data caveat** | reverse `component_type`; convert `re_meal_classes.slot` `text[]`→`text` — **lossy for any row with cardinality>1**; must fail loudly on multi-slot data (same pattern as 027/028 rollbacks) |
| 026 | Yes, same caveat | same lossy `slot` reversal for `public.meal_classes` |

**Conclusion:** rollbacks for all six are recoverable/authorable and belong to **WP-5C**. The 025/026 array→scalar reversals must carry the loud-fail-on-seeded-data warning already established by the 027/028 rollback precedent. **No rollback SQL was written in WP-5B.**

## Critical Self-Review

- **Considered** applying the migrations to a Supabase preview branch to prove they replay cleanly. **Rejected for WP-5B** — the mandate is inspect-only; branch creation is a database operation. Deferred to WP-5F where DB validation is in scope.
- **Limitation:** check 7 (validation-script compatibility) is by inspection of 900's expectations, not by running 900; running the validation suite is WP-5D/WP-5F territory.

## Versioning & Placement

`[ACTIVE]_Migration_Recovery_Validation_Report_v1.0.md` → `docs/project-history/`. New file.

## Founder Sign-off

Founder acceptance of the Migration Recovery Validation Report: _______________________ Date: ___________
