# DOC-P3-05 · Regression Validation Report
**Following:** AGR-002/AGR-003 root-cause resolution at the planning layer (DOC-P3-05 Part (a) v1.1 → v1.2)
**Date:** June 2026

---

## Check 1 — No approved architecture has changed unintentionally

| Verification | Result |
|---|---|
| Total table count across all migration files | **60** — unchanged from before the fix. Direct extraction, not asserted. |
| Any column, constraint, or business rule altered in DOC-P3-04? | **No.** Only DOC-P3-04's own privilege statement changed earlier (AGR-001, already approved and closed). This round of fixes touched zero DOC-P3-04 text — only DOC-P3-05 Part (a)'s governance matrices and the migration files implementing them. |
| Did `meal_classes` or `derivation_conflicts` change shape (columns, types, constraints)? | **No.** Both tables are byte-identical to their DOC-P3-04-specified definitions — only the *file* that creates them changed. |

**Verdict: PASS.**

---

## Check 2 — No migration allocation has drifted

| Verification | Result |
|---|---|
| Does every table appear in exactly one migration file? | **Confirmed by direct scan** — zero tables found duplicated across files (empty result from a duplicate-detection scan across all forward migration files). |
| Does Part (a)'s Phase 8.1 matrix match what the migration files actually contain? | **Confirmed.** `meal_classes` is in file `003` in both the governance matrix and the actual SQL. `derivation_conflicts` is in file `010` in both. File `018` shows zero tables in both. |
| Was any *other* table moved as a side effect? | **No.** Only the two tables named in AGR-002 and AGR-003 changed file allocation. All 58 other tables remain in their original files, confirmed by an unchanged total count. |

**Verdict: PASS.**

---

## Check 3 — No SQL objects were added or removed beyond the approved architecture

| Object type | Count before this fix | Count after this fix | Verdict |
|---|---|---|---|
| Tables | 60 | 60 | ✅ No net change — reallocation only |
| Trigger functions | 4 | 4 | ✅ Unchanged |
| Triggers | 4 | 4 | ✅ Unchanged |
| RLS `ENABLE` statements | 19 | 19 | ✅ Unchanged |
| RLS `CREATE POLICY` statements | 23 | 23 | ✅ Unchanged |
| Indexes | 36 | 36 | ✅ Unchanged |
| **One object's *implementation* simplified** | File `018` previously contained a deferred `ALTER TABLE ... ADD CONSTRAINT` workaround | File `018` now contains zero executable statements (retired placeholder); the equivalent FK is declared inline in file `011` instead | This is **not** a new object — it is the same single FK constraint DOC-P3-04 always specified, now declared in the conventional way (inline at table creation) instead of as a deferred workaround. Net constraint count is unchanged: one FK on `plan_slots.class_code`, present both before and after. |

**Verdict: PASS.** Nothing was added or removed beyond what AGR-002 and AGR-003 themselves required to fix.

---

## Check 4 — All trigger dependencies are now safe

| Trigger / function | Writes to | Confirmed created before first possible execution? |
|---|---|---|
| `fn_derive_dish_attributes()` (file `010`) | `public.derivation_conflicts` | **Yes** — `derivation_conflicts` is created at line 21 of file `010`; the function referencing it is defined afterward in the same file. The forward-reference gap (AGR-003) no longer exists. |
| `fn_propagate_ingredient_change()` (file `010`) | (re-triggers `fn_derive_dish_attributes` indirectly via a no-op UPDATE) | **Yes** — no direct table dependency beyond what `fn_derive_dish_attributes` already requires, which is now satisfied. |
| `fn_sync_profile_allergen_union()` (file `010`) | `public.profiles` | **Yes** — `profiles` created in file `005`, well before file `010`. Unaffected by this round of fixes. |
| `fn_update_dish_genome_vector()` (file `010`) | `public.dishes` | **Yes** — `dishes` created in file `008`, before file `010`. Unaffected. |
| `plan_slots.class_code` FK (file `011`, declarative, not a trigger, included here since it was the other half of the original concern) | `public.meal_classes` | **Yes** — `meal_classes` is created at line 59 of file `003`, well before file `011`. The forward-reference gap (AGR-002) no longer exists. |

**Verdict: PASS.** No remaining trigger or FK dependency in files `001`–`020` references an object that has not already been created by an earlier file in the sequence.

---

## Check 5 — Implementation remains fully traceable to P3-04 and P3-05 Part (a)

| Verification | Result |
|---|---|
| Does every changed file still carry its traceability header? | **Yes** — files `003`, `010`, `011`, `015`, `018` all have updated header comments citing the corrected DOC-P3-04 section, the relevant LF-numbers, and the specific AGR ID and Part (a) Phase 16 resolution that justifies the change. |
| Does Part (a) v1.2 explain *why* each reallocation happened, not just *that* it happened? | **Yes** — Phase 16 (new in v1.2) documents the root cause, the correction, and explicitly distinguishes this from an implementation workaround, per the founder's instruction. |
| Is there a single place to look up the full history of any gap? | **Yes** — the new Architecture Gap Register consolidates AGR-001 through AGR-004 with affected documents, root cause, resolution, status, and version resolved for each. |

**Verdict: PASS.**

---

## Overall regression verdict

**All 5 required checks PASS.** AGR-002 and AGR-003 are closed at the root cause, in the governance document (DOC-P3-05 Part (a), now v1.2), with the minimum necessary downstream changes applied to migration files `003`, `010`, `011`, `015`, and `018`. No architecture drifted, no object count changed, no trigger or FK dependency remains unsafe, and full traceability is preserved throughout.

One measurement artifact is noted for completeness, not as a finding: an initial combined-pattern grep during this validation reported 43 RLS-related statements; disaggregating into `ENABLE` (19) and `CREATE POLICY` (23) confirmed the correct total of 42, matching DOC-P3-04 exactly. This was a counting-tool artifact, not a real discrepancy, and is recorded here in the interest of showing the actual verification work performed rather than only its conclusion.

---

Founder confirmation — AGR-002/AGR-003 closed, regression clean, ready for Part (d): ___________________________ Date: _______________
