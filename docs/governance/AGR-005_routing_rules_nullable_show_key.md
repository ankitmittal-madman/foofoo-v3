# AGR-005 — re_routing_rules.show_question_key Incorrectly NOT NULL

**Type:** Architecture Gap Register entry
**Status:** RESOLVED via migration 027 (pending Founder sign-off below)
**Discovered:** WP-4B execution, 2026-07-09, statement 3 of 10 (`re_routing_rules` seed load)
**Placement:** `docs/project-history/AGR-005_routing_rules_nullable_show_key.md`

---

## Gap

`re_engine.re_routing_rules.show_question_key` was specified `NOT NULL` in migration `003_reference_tier1.sql` (implementing `DOC-P3-04 v1.3 §03.27`). The authoritative 8-row dataset for this table (`101_seed_reference_data_framework.sql`, sourced from `DOC-P3-03 §03 LF-A02`, marked "COMPLETE, 8 of 8, no IDR applies") requires `NULL` in this column for 4 of its 8 rows — the "skip rule" rows, which by design show no question and therefore have no question key to store.

## Evidence

- Live schema confirmed: `show_question_key` is `text NOT NULL` (`information_schema.columns`, verified live 2026-07-09).
- Live rejection reproduced: `ERROR 23502: null value in column "show_question_key" violates not-null constraint`, failing on the `MC_SOLO` row.
- Seed file content confirmed unchanged and correctly authoritative (not placeholder): the file's own comment states "COMPLETE (8 of 8 — fully specified in DOC-P3-03 §03 LF-A02; no IDR)".
- Catalog scan confirmed no view, trigger, function, or index depends on this column's nullability.
- Table confirmed at 0 rows at time of discovery — no existing data required migration, only the constraint shape.

## Resolution

Migration `027_routing_rules_show_question_key_nullable.sql`:
1. Drops the `NOT NULL` constraint on `show_question_key`.
2. Adds `CHECK (show_question_key IS NOT NULL OR skip_if_answered IS NOT NULL)` — a stricter, more correct invariant than the original: every rule must do at least one of (show a question, skip questions), but a rule doing neither is now correctly rejected, whereas previously a rule doing only the "skip" half was incorrectly rejected.

Paired rollback: `027_routing_rules_show_question_key_nullable_rollback.sql`.

## Why This Is Not a Redesign

This corrects a transcription-level error in one column's constraint, discovered only because it was never exercised until real data was loaded against it. It does not change the table's purpose, its other columns, its relationships, or any RE algorithm's use of it. `DOC-P3-04` receives an additive v1.4 amendment note; `v1.3`'s original text is not edited, per the standing persistence rule.

## Impact if Not Fixed

Alternative (rejected): define a sentinel value (e.g. `'NONE'`) instead of allowing `NULL`. Rejected because it would require BUILD-02's dynamic onboarding engine to special-case a magic string, embedding business logic into data — contrary to this project's standing anti-pattern guidance ("business logic in DB columns... confirmed anti-pattern to eliminate").

## Founder Sign-off

Approved: _______________________ Date: ___________
