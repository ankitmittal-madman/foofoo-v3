# REPO-WP-03_Seed_Readiness_Engineering_v1.0

**Repository Engineering Work Package #3 — Seed Readiness Engineering**
**Project:** FooFoo (apverse-labs/foofoo-v3) · **Supabase:** `slsqtlygeekdppuyiiff`
**Placement:** `docs/project-history/` (continuing REPO-BOOT-01/02 → REPO-WP-02 lineage)
**Date:** 2026-07-06 · **Status:** DESIGNED — awaiting Founder approval to execute
**Prerequisites:** WP-1 COMPLETE · WP-2 COMPLETE · Founder Decision FROZEN: Option A — `public.meal_classes.slot` becomes `text[]`

**Success criterion (governing this entire package):** WP-4 Seed Engineering can execute with effectively zero avoidable structural errors. Every sub-package below justifies itself against that test, not against "completing tasks."

**Execution order: 3B → 3A → 3C → 3D** (reordered from the proposed 3A-first: migration 026 completes the final structural state first, so the rollback set, documentation, and certification each address one final, stable schema exactly once).

**Founder approval is required between every sub-package. Claude Code stops after each and produces an Execution Report.**

---

## WP-3B — Mirror Parity (Migration 026) — *executes first*

| Field | Content |
|---|---|
| **Objective** | Convert `public.meal_classes.slot` from `text` to `text[]`, matching `re_engine.re_meal_classes.slot` exactly (same 4-value CHECK: `breakfast/lunch/dinner/snack`, `<@` containment + non-empty), per the frozen Founder decision. |
| **Context** | Live divergence verified: mirror is `text`, source is `text[]` (post-025). No sync mechanism exists yet (verified: zero functions reference `meal_classes`); both tables 0 rows — this is the zero-cost conversion window. |
| **Dependencies** | WP-2 complete (025 applied). Nothing else. |
| **Authority** | Founder Decision (FROZEN, this document's header) > `Phase3_5_Architecture_Freeze_v1.0` §5 (the 025 pattern to mirror) > migration 025 as committed (the implementation precedent to match). |
| **Required Documents** | `database/migrations/025_combo_component_type_and_slot_array.sql` (+ its rollback) — the pattern source; `DOC-P3-04 v1.3` §meal_classes (mirror's frozen definition). |
| **Required Discovery** | Read 025's actual committed text (not its description) and replicate its conversion idiom (USING clause, CHECK shape, legacy-value handling) on the mirror — discovering whether the mirror column has any dependent view/index/constraint that 026 must handle. |
| **Founder Decisions** | None — already frozen. |
| **Execution Strategy** | Author `026_meal_classes_mirror_slot_array.sql` + paired rollback; apply; verify. |
| **Validation Strategy** | `information_schema` confirms `udt_name='_text'`; behavioral proof per the 025 precedent (insert `['snack']`, compound `['lunch','dinner']`, reject empty array, reject scalar-era values; delete test rows). |
| **Rollback Strategy** | Paired `026_*_rollback.sql`, tested (apply → rollback → reapply, counted). |
| **Deliverables** | Migration 026 + rollback, both committed; behavioral verification output in the Execution Report. |
| **Acceptance Criteria** | Mirror column is `text[]` with identical CHECK semantics to source; rollback proven. |
| **Exit Criteria** | Acceptance met, Execution Report produced, **STOP for Founder approval**. |
| **Risks** | Minimal — 0-row table, no consumers. Residual risk: an unnoticed dependent object (view/index) on the old column — covered by Required Discovery. |
| **Stop Conditions** | Any dependent object on `meal_classes.slot` not resolvable by the 025 idiom; any CHECK-shape ambiguity vs. 025. |
| **Why WP-3, not WP-4** | Seed file 101 INSERTs into this mirror; loading against a scalar column that architecture says must be an array would seed wrong-shaped data requiring migration later. Shape must be final before data exists. |
| **Critical Self-Review** | Considered folding 026 into a WP-4 pre-step — rejected: it is approved *architecture*, and architecture completes before seed engineering begins, per the operating model's layer separation. |

---

## WP-3A — Rollback Completion (001–019) — *executes second*

**Revised after WP-3B post-execution review (fresh discovery, 2026-07-08) — one scope adjustment made, detailed in Critical Self-Review below.**

| Field | Content |
|---|---|
| **Objective** | Author the 19 missing paired rollback files for migrations 001–019, completing the §5.3 convention repo-wide (020–026 already paired, confirmed live: 26/26 migrations applied, no drift since WP-3B). |
| **Context** | WP-2 discovered zero rollback files existed for the frozen baseline — specified in `DOC-P3-05` §5.3 ("written at the same time as the forward migration") but never delivered. Overdue specified debt. Re-verified this session: `018_meal_classes_mirror_sync` remains the intentionally-empty placeholder (no new risk introduced by 026). |
| **Dependencies** | WP-3B complete and confirmed frozen (fresh discovery: 26 migrations in `supabase_migrations.schema_migrations`, `meal_classes` carries exactly PK + the recreated CHECK, no surprise objects). |
| **Authority** | `DOC-P3-05 Part A v1.2` §5.3 (reversal-ordering rules) + **WP-3B's own demonstrated discovery method** (combined `pg_depend`/`pg_views`/`pg_indexes`/`pg_constraint`/`pg_trigger`/`pg_proc` catalog scan per object, performed live, before authoring) — adopted here as the required discovery method, not merely reading forward-file text. |
| **Required Documents** | All of `database/migrations/001–019` and their group context per `DOC-P3-05` Phase 5.1's 15-group taxonomy; `DOC-P3-05` §5.3. |
| **Required Discovery** | For each of the 15 groups (in `DOC-P3-05`'s own dependency order — schema/extensions → reference tables → ... → triggers → ... → RLS → indexes): read the forward file(s) AND run a live catalog dependency scan for every object it creates, exactly as WP-3B did — because a forward file's own text doesn't necessarily reveal what has come to depend on it by migration 026's time. |
| **Founder Decisions** | None. |
| **Execution Strategy** | Author 19 rollback files, following the documented 15-group order (not a risk-reprioritized order — see Critical Self-Review). Two files require manual reasoning beyond mechanical reversal, per `DOC-P3-05` §5.3's own flag: `010_trigger_functions_and_triggers` (drop triggers before functions) and `019_rls_policies` (drop policies before disabling RLS). The other 17 are direct DROP-in-reverse-creation-order. Do NOT execute any of the 19 against the live, 26-migration database — the baseline must remain applied and undisturbed. |
| **Validation Strategy** | Per group: object-inventory diff (every object the forward file(s) created has a corresponding DROP, in valid dependency order) — structural, non-destructive. No live rollback execution for 001–019 (unlike 020's proof-of-mechanism test) — rolling back e.g. `002_reference_tier0` would cascade-break 26 live, applied migrations built on top of it; the risk of that destructive test exceeds its evidentiary value. |
| **Rollback Strategy** | N/A — these files ARE the rollback layer; authorship is additive, zero live-database effect. |
| **Deliverables** | 19 `_rollback.sql` files, committed, organized by the same 15-group logical sequence. |
| **Acceptance Criteria** | 26 of 26 migrations carry a paired rollback; object-inventory diff clean for all 19 new files; the 2 manual-review files (010, 019) explicitly confirmed to reverse triggers-before-functions and policies-before-RLS-disable respectively. |
| **Exit Criteria** | Acceptance met, Execution Report, **STOP for Founder approval — do not continue to WP-3C.** |
| **Risks** | A rollback authored wrong stays latent until used. Mitigated by per-group inventory-diff validation using WP-3B's live-discovery method, not text-only inference. |
| **Stop Conditions** | Any forward file/group whose object inventory is ambiguous (e.g., dynamic SQL, an object with dependents not evident from the file text alone) — report, don't guess, exactly as WP-3B's discovery pass would have stopped had it found something non-trivial. |
| **Why WP-3, not WP-4** | Last moment before the schema becomes load-bearing. If WP-4 surfaces a structural defect needing correction, correction safety presumes the rollback layer exists. |
| **Critical Self-Review** | **Scope adjustment from the original v1.0 spec:** "Required Discovery" now mandates the live catalog-scan method WP-3B demonstrated, rather than deriving rollbacks from forward-file text alone — a forward file doesn't show what came to depend on its objects later in the 26-migration sequence. **Execution-order self-challenge:** considered authoring the two manual-review files (010, 019) first on a "hardest-first" theory — rejected, because authoring in `DOC-P3-05`'s own documented 15-group dependency order means each group's rollback can be checked against an already-internally-consistent partial rollback set, which a reprioritized order would forfeit. |

---

## WP-3C — Documentation & Validation Synchronization — *executes third*

| Field | Content |
|---|---|
| **Objective** | Bring `DOC-P3-04` and the 900-series validation scripts into agreement with the final live schema (62 tables, migrations 021–026), so WP-4's document-driven discovery meets zero false contradictions. |
| **Context** | Three confirmed staleness items: (1) `DOC-P3-04` headline counts contradict its own DDL (WP-2 finding — "51 FK"/"31 CHECK"/"37 indexes"/§02 schema split); (2) `DOC-P3-04` does not reflect 021–026 at all; (3) `900_structural_validation.sql` Check 1 expects exactly 60 tables (now 62) and no 900-series check covers any 021–026 object (verified by direct read this design session). |
| **Dependencies** | WP-3B complete (docs/scripts must describe the FINAL schema). |
| **Authority** | `DOC-P3-09` §06E persistence rule — frozen v1.3 is never edited; a **v1.4 additive amendment** is created (the established v1.1→v1.2→v1.3 pattern). Validation scripts are repository artifacts, updated in place with git history. |
| **Required Documents** | `DOC-P3-04 v1.3` (full), WP-2 Execution Report (the count-discrepancy specifics), migrations 021–026 as committed, all five 900-series scripts. |
| **Required Discovery** | Recount every headline figure directly from the live database (not from either document) — the live DB is the arbiter for *counts*; `DOC-P3-04` remains the arbiter for *design intent*. |
| **Founder Decisions** | None anticipated. One contingent: if recounting surfaces a discrepancy that is neither a doc typo nor a 021–026 addition (i.e., genuine unexplained drift), STOP — that would be a Founder-level finding. |
| **Execution Strategy** | Author `DOC-P3-04` v1.4 amendment section (additive, documenting 021–026 objects + corrected counts + the §02 prose fix); update 900-series scripts (table count 62, new checks for `cuisines`, `re_dish_regional_affinity`, `component_type`, both `slot text[]` columns, `vector_position` uniqueness-per-dimension). |
| **Validation Strategy** | Run the updated 900-series against the live DB: every structural check must PASS; seed-gate checks (Check 7) are expected to FAIL on row counts (0 rows — unseeded) and must be reported as expected-fail, not masked. |
| **Rollback Strategy** | Documents/scripts are git-tracked; revert = git revert. No database effect. |
| **Deliverables** | `DOC-P3-04_Data_Architecture_ERD_v1_4.md` (additive amendment), updated 900-series scripts, both committed. |
| **Acceptance Criteria** | Updated 900-series structural checks all PASS against live; v1.4 amendment contains zero design changes (counts + 021–026 records only). |
| **Exit Criteria** | Acceptance met, Execution Report, **STOP for Founder approval**. |
| **Risks** | Scope creep into "improving" the doc — bounded by the additive-amendment-only rule. |
| **Stop Conditions** | Unexplained live-vs-doc drift (see Founder Decisions); any temptation to alter v1.3 content itself. |
| **Why WP-3, not WP-4** | WP-4's prompt will treat `DOC-P3-04` as authority and the 900-series as its gate. Stale authority = spurious STOPs; stale gates = false failures or false confidence. Both are avoidable structural errors, which is WP-3's entire success criterion. |
| **Critical Self-Review** | Challenged whether doc sync is cosmetic — concluded no, for the specific mechanical reason above (WP-4's discovery reads these files as ground truth). |

---

## WP-3D — Seed Readiness Certification — *executes last*

| Field | Content |
|---|---|
| **Objective** | Certify, with evidence, that the repository and database are ready for WP-4 Seed Engineering — including an explicit compatibility audit of the existing seed files against the final schema. |
| **Context** | **Confirmed incompatibility already found at design time:** `101_seed_reference_data_framework.sql` INSERTs `'breakfast'` (scalar) into `re_meal_classes.slot` (`text[]` post-025) — guaranteed first-execution failure in WP-4 if unflagged. The same file seeds `public.meal_classes` (same issue post-026). The full extent across 100/101/102 is unknown — that is this sub-package's job to establish. |
| **Dependencies** | WP-3B, 3A, 3C all complete. |
| **Authority** | Final live schema (as certified by 3C's updated 900-series) is the compatibility target; seed files are audited *against* it, never the reverse. |
| **Required Documents** | `100_seed_config_tables.sql`, `101_seed_reference_data_framework.sql`, `102_seed_illustrative_content_and_dependents.sql` (full reads), updated 900-series, `DOC-P3-04 v1.4`. |
| **Required Discovery** | Statement-level audit of all three seed files: every INSERT's column list and value shapes diffed against the live schema. Classify each finding: COMPATIBLE / STALE-SHAPE (e.g., scalar slot) / STALE-TARGET (column renamed/added) / ILLUSTRATIVE-SUPERSEDED (rows the real master workbook replaces per IDR-001). |
| **Founder Decisions** | None in this sub-package — the audit *informs* WP-4's design decisions (rewrite vs. regenerate seed files), it does not make them. |
| **Execution Strategy** | Audit + certify only. **No seed file is modified, no row is loaded** — fixing is WP-4 Seed Engineering's work; certifying the ground is WP-3's. |
| **Validation Strategy** | The certification is the validation: updated 900-series full run (structural PASS, seed-gates expected-fail-at-0-rows), rollback-pairing completeness check (26/26), migration-history integrity check (Supabase log matches files), seed-file audit table complete. |
| **Rollback Strategy** | N/A — read-only sub-package. |
| **Deliverables** | **Seed Readiness Certificate** (a dated report: schema state, validation results, rollback completeness, seed-file compatibility table, explicit GO/NO-GO for WP-4). |
| **Acceptance Criteria** | Every certification dimension carries direct evidence; the seed-file audit covers 100% of statements in all three files; a clear GO or NO-GO verdict with reasons. |
| **Exit Criteria** | Certificate produced, **STOP — WP-3 complete, Founder approval gates WP-4**. |
| **Risks** | Audit misses a stale statement → exactly the WP-4 failure this package exists to prevent. Mitigated by statement-level (not file-level) coverage requirement. |
| **Stop Conditions** | Any audit finding suggesting the *schema* (not the seed file) is wrong — that inverts authority and is a Founder-level stop. |
| **Why WP-3, not WP-4** | Certification is the boundary artifact between structural engineering and seed engineering — it belongs to the side that produces the guarantee, not the side that consumes it. |
| **Critical Self-Review** | Challenged whether the seed-file audit is premature WP-4 work — concluded no: *auditing* compatibility is certification (WP-3); *rewriting* the files is engineering (WP-4). The line is bright: WP-3D changes nothing, it only knows things. |

---

## Package-Level Seed Safety Review (Part 8)

Test: can WP-4 execute with effectively zero avoidable structural errors after WP-3? With the two scope additions (seed-file audit, validation-script currency), every currently-known failure path is covered: shape mismatches (3B + 3D audit), missing safety net (3A), authority-document contradiction (3C), stale gates (3C), unknown-unknowns in seed files (3D's statement-level coverage). The remaining WP-4 risk is *data* correctness (wrong values from source files) — which is genuinely seed engineering's own domain, not avoidable structural error.

## Versioning & Placement

`[SUPERSEDED]_REPO-WP-03_Seed_Readiness_Engineering_v1.0.md` → `docs/project-history/`, committed **before** execution begins (lesson from WP-2's Step-0 finding — the Work Package file precedes its prompt this time).

## Sign-off

Founder approval to begin WP-3B: _______________ Date: _______
Approval 3B→3A: _______ · 3A→3C: _______ · 3C→3D: _______ · WP-3 closure: _______
