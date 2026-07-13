# AGR-006 — re_weight_ladder_config Exact-Equality CHECK on REAL Columns

**Type:** Architecture Gap Register entry
**Status:** RESOLVED via migration 028 (pending Founder sign-off below)
**Discovered:** WP-4C execution, 2026-07-09, statement 1 of 23 (`re_weight_ladder_config` seed load)
**Placement:** `docs/project-history/AGR-006_weight_ladder_numeric_conversion.md`

---

## Gap

`re_engine.re_weight_ladder_config`'s five weight columns (`w_cohort`, `w_content`, `w_history`, `w_context`, `w_explore`) were declared `real` (`float4`), with a CHECK requiring their sum to equal exactly `1.0`. The authoritative seed data (`100_seed_config_tables.sql`, sourced from `DOC-P3-03 §16`, confirmed values, no IDR) is mathematically correct in decimal arithmetic for all 5 tiers, but binary floating-point cannot represent several of the decimal literals exactly, and the rounding errors do not cancel for the `emerging` tier's specific combination.

## Evidence

- Live schema confirmed: all 5 columns `real`; CHECK confirmed exact-equality against `1.0`.
- Live reproduction: `(0.20::real + 0.25::real + 0.35::real + 0.15::real + 0.05::real)::double precision` evaluates to `0.999999940395355`, not `1.0`.
- All 5 tiers independently re-verified: `cold_start`, `early`, `established`, `mature` happen to round to exactly `1.0` under `float4`; only `emerging` does not — confirmed this is a rounding coincidence, not a data error.
- Repository + live-catalog audit (full schema, all `real`/`float8`/`numeric` columns with any CHECK constraint) found **exactly one** occurrence of exact-equality arithmetic on a floating-point type anywhere in the schema — this table. All other float-typed CHECK constraints (`profiles.city_overlay_weight`, `user_re_state.confidence_score`, `dish_tags.confidence`) use range comparisons (`BETWEEN`/`>=`/`<=`), which are immune to this failure mode regardless of type.
- No tolerance-based (`ABS(...) < epsilon`) comparison exists anywhere in the repository — confirmed by direct search.
- No SQL-side function, trigger, or view reads or performs arithmetic on these columns anywhere in the live database (confirmed via `pg_proc` scan for `weight`/`interpolat`/`score`/`ladder` — zero results). The only in-database reference is the behavioral smoke test (`904_behavioral_config_and_smoke_test.sql`), which validates the CHECK constraint itself, not business logic.
- The real consumer (`LF-E01 interpolateWeightLadder()`) is documented as application-layer code (`DOC-P4` territory) not yet built in this repository.

## Precedent Correction

An earlier working assumption cited migration 024 (`re_dish_regional_affinity.affinity_score`, also `numeric`) as architectural precedent for this fix. On deeper review, **this precedent does not actually apply**: `affinity_score` is an independent bounded score per `(dish, state)` pair, validated only by a range check, with no sum invariant — a fundamentally different problem shape from a normalized weight vector that must sum to exactly `1.0`. This migration's justification rests on the exact-sum-invariant reasoning below, not on consistency with migration 024.

## Lifecycle Verification

`RE-DOC-05_Evolution_Roadmap` was reviewed to determine whether these weights are expected to become machine-learned values in future phases, which would argue against an exact-equality invariant. Finding: these weights remain **hand-tuned, business-owned configuration** through `classfirst_v1`/`v2`/`v3`. When true ML-learned scoring arrives (`ltr_v1`, Phase 3), the roadmap explicitly states the hand-tuned-weight approach is **replaced**, with trained parameters stored in a new, separate table (`re_engine.model_artifacts`, per `DOC-P3-04` §12's Schema Evolution Strategy) — this table is not repurposed to hold ML output. The exact-sum invariant is therefore not expected to require loosening at any future, currently-documented product stage.

## Resolution

Migration `028_weight_ladder_config_numeric_weights.sql`:
1. Converts all 5 weight columns from `real` to `numeric`.
2. Re-applies the same exact-equality CHECK, now reliable since `numeric` represents decimal literals like `0.20` without rounding error.

Paired rollback: `028_weight_ladder_config_numeric_weights_rollback.sql`.

## Why NUMERIC Over a Tolerance-Based CHECK

Considered and rejected: replacing the exact-equality CHECK with a tolerance comparison (`ABS(sum - 1.0) < epsilon`) instead of changing the column type. Rejected because:
- These columns hold hand-authored constants with no acceptable margin of error by definition — treating them as if they carried measurement uncertainty misrepresents what kind of data they are.
- A tolerance constant requires its own justification (why this epsilon, not a smaller or larger one) and becomes a piece of unexplained "magic" in the schema for future readers to trust without re-deriving.
- This repository has zero existing precedent for tolerance-based float comparison anywhere — introducing one here would establish a new, unprecedented pattern rather than close an isolated gap.
- Runtime precision downstream (in the not-yet-built scoring Edge Function) is unaffected by this choice either way, since the weight-ladder interpolation step re-introduces ordinary floating-point arithmetic in application code regardless of how the anchor values are stored in Postgres — so the decision is properly scoped to validating the at-rest authored data correctly, which `numeric` does exactly and a tolerance constant only approximates.

## Standing Rule (for future tables)

Documented for `DOC-P3-04`'s architecture guidance: **any column group with a mathematically exact-sum or exact-proportion invariant (a normalized weight/probability distribution) must use `numeric`.** Independent bounded scores, confidences, or similarities — even when range-checked — may remain `real`, since range checks are immune to this failure mode regardless of type. This rule is scoped to the specific pattern that caused this defect, not a blanket ban on `real`.

## Impact if Not Fixed

`re_weight_ladder_config` cannot be seeded at all — the `emerging` tier row is permanently rejected by the live CHECK constraint regardless of how many times the same seed data is re-attempted, since the failure is deterministic (a property of the values and the type, not transient).

## Founder Sign-off

Approved: _______________________ Date: ___________
