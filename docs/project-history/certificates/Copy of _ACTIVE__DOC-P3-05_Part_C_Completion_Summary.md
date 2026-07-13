# DOC-P3-05 Part (c) — Operational Tables, Triggers, Functions, RLS, Policies: Completion Summary
**Date:** June 2026
**Status:** Files `010`–`020` complete. **Three Architecture Gap Reports raised (AGR-002, AGR-003, AGR-004), one resolved inline with disclosed reasoning, two informational.**
**Implements:** DOC-P3-04 v1.3, per the file allocation frozen in DOC-P3-05 Part (a) v1.1

---

## Pre-work reconfirmation (per founder's explicit Part (c) requirements)

| Reconfirmation required | Status |
|---|---|
| Latest approved P3-04 being implemented | ✅ v1.3 (post AGR-001) — verified via direct grep before any file in Part (c) was written |
| Part (a) remains the implementation governance authority | ✅ All file numbers, naming, and allocations in this part match Part (a)'s frozen Phase 7/8 matrices exactly — no file renumbered, reorganized, or redistributed |
| Part (b) unchanged except AGR-001's direct consequence | ✅ Verified — only file `008`'s REVOKE statement and header were touched; files `001`–`007`, `009` byte-identical to their originally approved state |

---

## Files produced

| File | Objects created | Rollback |
|---|---|---|
| `010_trigger_functions_and_triggers.sql` | 4 functions, 4 triggers | ✅ paired |
| `011_planning_tables.sql` | `week_plans`, `plan_slots`, `addon_slots` — **AGR-002 raised here** | ✅ paired |
| `012_interaction_audit_appendonly.sql` | `interaction_events` (partitioned parent), `suggestion_logs` (partitioned parent), `context_log`, `weather_cache` | ✅ paired |
| `013_config_tables.sql` | 10 configuration tables | ✅ paired |
| `014_persona_assignment_and_priors.sql` | `re_persona_assignment_rules`, `re_cohort_class_priors` | ✅ paired |
| `015_operational_audit_public.sql` | `audit_log`, `derivation_conflicts`, `coverage_gap_log`, `safety_gate_log`, `push_notification_logs`, `feature_flags`, `etl_job_runs` — **AGR-003 raised here** | ✅ paired |
| `016_dish_features.sql` | `re_engine.dish_features` | ✅ paired |
| `017_initial_partitions.sql` | 6 partition children (3 months × 2 partitioned tables) | ✅ paired |
| `018_meal_classes_mirror_sync.sql` | `meal_classes` — **AGR-002 resolved here** | ✅ paired |
| `019_rls_policies.sql` | 19 `ENABLE ROW LEVEL SECURITY` + 23 `CREATE POLICY` = 42 statements | ✅ paired |
| `020_indexes.sql` | 36 indexes — **AGR-004 raised here** (count discrepancy + 2 textual ambiguities) | ✅ paired |

**Table count check:** files `010`–`020` create 6 (file 007's table count was already counted in Part (b)... correction: file 011 creates 3, 012 creates 4, 013 creates 10, 014 creates 2, 015 creates 7, 016 creates 1, 018 creates 1 = **28 tables**, exactly matching Part (a) Phase 8.1's stated remainder (60 total − 32 from Part (b) = 28). **Confirmed: 28 of 28.**

---

## Architecture Gap Report — AGR-002

| Field | Detail |
|---|---|
| **Inconsistency found** | DOC-P3-05 Part (a) v1.1, Phase 7 (Migration Dependency Matrix), states for file `011_planning_tables.sql`: *"`plan_slots.class_code` → `public.meal_classes` (created alongside `003` per the mirror-table grouping decision below)"* — implying `meal_classes` exists by file `003`. But Part (a)'s own Phase 8.1 (Object-to-Migration Allocation Matrix) explicitly allocates `meal_classes` to file `018`, **after** file `011`. This is a self-contradiction **within the frozen Part (a) document itself**, not a defect in DOC-P3-04. |
| **Why implementation could not proceed as literally specified** | DOC-P3-04 v1.3 §03.13 declares `plan_slots.class_code` with an inline `REFERENCES public.meal_classes(class_code)` FK. Applying this FK at file `011`'s creation time would fail — `public.meal_classes` does not exist yet at that point in the frozen file sequence. |
| **Which document is responsible** | DOC-P3-05 Part (a) — the inconsistency is between two of that document's own sections (Phase 7 narrative vs. Phase 8.1 matrix), not a flaw in DOC-P3-04. |
| **Resolution applied** | File `011` was written **without** the FK (plain `text NOT NULL` on `class_code`), with an inline comment naming this gap explicitly. The FK was then added in file `018` — the earliest point in the frozen sequence where `meal_classes` actually exists — via a deferred `ALTER TABLE ... ADD CONSTRAINT`. This restores the **exact constraint DOC-P3-04 specifies**, applied at the first structurally possible moment, without renumbering, reorganizing, or redistributing any object across files (which the founder's instructions for both Part (b) freeze and Part (c) explicitly forbid). |
| **Was this silently done?** | No — flagged inline in file `011` at the point of omission, flagged again and resolved with full reasoning in file `018`, and reported here as a third, consolidated point of visibility. |
| **Requires founder confirmation?** | **Yes.** The deferred-ALTER-TABLE approach is presented as the most conservative fix available within the frozen file structure, but it is a judgment call about *how* to resolve a contradiction inside governance, not a pre-approved instruction — recommend explicit sign-off before treating this as closed, consistent with how AGR-001 required founder direction rather than unilateral resolution. |

---

## Architecture Gap Report — AGR-003

| Field | Detail |
|---|---|
| **Inconsistency found** | `fn_derive_dish_attributes()` (deployed in file `010`) contains an `INSERT INTO public.derivation_conflicts (...)` statement. The `derivation_conflicts` table itself is not created until file `015` — five files later. |
| **Why this does not block migration application** | Unlike a table-level FK, this is a function *body* referencing another table by name. PL/pgSQL does not validate that referenced tables exist at `CREATE FUNCTION` time — only at actual execution time. Files `010` through `014` will apply without error. |
| **What actually breaks, and when** | If the trigger fires for real (any INSERT/UPDATE/DELETE on `dish_ingredients`) **and** a genuine derivation conflict is detected (Rule 5 of the function, §03.6A) **before** file `015` has run, the `INSERT INTO public.derivation_conflicts` statement inside the trigger will fail at runtime with `relation "derivation_conflicts" does not exist` — and because this happens inside an `AFTER` trigger on the same transaction as the original `dish_ingredients` write, **that original write would also fail and roll back**, even though it had nothing wrong with it. |
| **Practical risk level** | **Low in the intended deployment sequence** (files are applied in strict numeric order with no gaps, per Part (a) Phase 1's mandatory ordering rule), but **non-zero** if anyone ever applies files out of order, or runs file `010` in isolation against a test database for unit-testing the trigger function alone — which is a realistic scenario during Part (d)'s smoke-test authoring. |
| **Resolution** | **Not resolved in this part** — flagged here for explicit visibility rather than worked around, since reordering files `010`–`015` would violate the founder's standing "do not reorganize migration files" instruction for material that is otherwise correctly allocated per Part (a). Recommend either: (a) accepting this as a documented, sequence-dependent constraint (the migration runner must never skip ahead or apply files out of order — which is already Part (a)'s stated discipline anyway), or (b) the architecture owner deciding the trigger's conflict-logging behavior should degrade gracefully (e.g., wrap the INSERT in its own exception handler that logs to `RAISE WARNING` instead of failing the outer transaction if the target table doesn't yet exist) — but option (b) would be a behavior change to the function body approved in DOC-P3-04 §03.6A, and is therefore **flagged, not applied**, pending founder direction. |

---

## Architecture Gap Report — AGR-004 (informational, non-blocking)

| Field | Detail |
|---|---|
| **Finding 1** | DOC-P3-04's own raw index-statement count (37, as previously reported in the Part (a) readiness assessment) included one duplicate: `idx_ingredients_allergen` is created, then `DROP INDEX`'d, then re-created with a different index type, as a self-correction documented inline in P3-04's own DDL comments (§03.5). The true count of **distinct** index names is **36**, not 37. This file implements all 36. |
| **Finding 2** | `idx_tags_vector_position` (a `UNIQUE INDEX` explicitly named in P3-04 §03.8) is functionally redundant with the `UNIQUE` column constraint already present on `tags.vector_position` in its `CREATE TABLE` statement (file `002`) — Postgres auto-creates a backing index for any `UNIQUE` column constraint. P3-04 names both. Reproduced verbatim in file `020` per the "implement exactly what is approved" discipline, with the redundancy flagged rather than silently dropped. |
| **Finding 3** | `idx_sl_gate_diet`, as literally described in P3-04 §03.16, uses a partial-index predicate referencing `now()` — `WHERE suggested_at > now() - interval '1 hour'`. This is **not valid Postgres syntax** for a partial index, because partial index predicates are evaluated once at creation time, not per-query; P3-04's own text acknowledges this ("in practice this is implemented as a plain composite index"). File `020` implements the plain composite fallback P3-04 itself describes, with the specific column ordering flagged as this migration's interpretation, not a literal transcription, pending confirmation against real `EXPLAIN` output once Part (d)'s safety-gate scripts exist. |
| **Resolution** | All three findings are disclosed for transparency. None block Part (c) completion. None required a P3-04 architecture change — they are clarifications of intent already present (if imperfectly expressed) in the approved document's own text. |

---

## One-to-one traceability confirmation

Every object created in files `010`–`020` carries a header comment citing its DOC-P3-04 v1.3 section, DOC-P3-03 logical function(s), DOC-P3-03A governance reference, and relevant CDM entity/invariant — consistent with the convention frozen in Part (a) Phase 4, with no exceptions.

---

## Completion checklist

| Requirement | Status |
|---|---|
| Every allocated object implemented exactly once | ✅ 28 of 28 tables (010–020 remainder), 4 of 4 functions, 4 of 4 triggers, 42 of 42 RLS statements, 36 of 36 distinct indexes (corrected from the previously-stated 37, per AGR-004 Finding 1) |
| Nothing omitted | ✅ Confirmed by direct re-extraction from P3-04 v1.3, catching and correcting an initial 32-vs-36 index undercount before delivery |
| Nothing duplicated | ✅ No object created in more than one file |
| Nothing added beyond approved architecture | ✅ with two disclosed exceptions: the AGR-002 deferred-FK resolution (restores an already-approved constraint, at a different statement than P3-04's inline DDL shows, due to Part (a)'s own file-sequencing) and the `idx_sl_gate_diet` interpretation (AGR-004 Finding 3) |
| Zero architecture drift | ✅ — no table, column, business rule, or relationship was changed; all three gap reports concern *sequencing and documentation precision*, not the architecture's substance |
| Undocumented assumptions | ✅ **None** — every judgment call made (AGR-002's resolution, AGR-004's index interpretations) is explicitly surfaced, not silently assumed |
| Silent corrections | ✅ **None** — every discrepancy found during this part was raised as a gap report before being acted on, including the index-count error caught mid-build |
| Part (a) treated as frozen | ✅ — even where Part (a) itself was found to be internally inconsistent (AGR-002), the response was to flag and work within the frozen file structure, not to revise Part (a) |
| Part (b) treated as frozen | ✅ — no file in `001`–`009` was touched during Part (c) |

**Verdict: Part (c) is complete, with two gap reports (AGR-002, AGR-003) requiring explicit founder review before being considered closed, and one informational gap report (AGR-004) requiring no action.** Recommend founder review of AGR-002 and AGR-003 before proceeding to Part (d), since Part (d)'s smoke tests (Phase 5.5 of Part (a)) will directly exercise both the `dishes`/`plan_slots` FK chain (AGR-002) and the derivation-trigger conflict-logging path (AGR-003) — better to settle both before writing tests against behavior that might still change.

---

Founder review of AGR-002 (deferred-FK resolution approach): ___________________________ Date: _______________
Founder direction on AGR-003 (accept sequence-dependency vs. modify trigger behavior): ___________________________ Date: _______________
Confirmation to proceed to Part (d): ___________________________ Date: _______________
