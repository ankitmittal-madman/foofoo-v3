# WP-5E — Repository Engineering Corrections / Validation Remediation v1.0

**Status:** ACTIVE — executed (repository-evidence corrections to seed + validation scripts only)
**Version:** v1.0
**Date:** 2026-07-13
**Placement:** docs/project-history/work-packages/[ACTIVE]_WP-5E_Validation_Remediation_v1.0.md
**Supersedes:** None
**Dependencies:** WP-5F Clean-Room Validation Report (defined SEED-01 & VALIDATION-01); migration 025 (slot→text[]); REPO-WP-02 §7.6/§7.7; REPO-WP-04B v1.1 (records the lost WP-4A seed fix); Batch1 Mapping/Canonicalization (MAP-DEC-003). Companions: WP-5E Engineering Decision Log, Validation Report, Evidence Register, and REPO-CERT-002 execution certificate.

---

## 1. Objective

Correct the two engineering defects WP-5F proved in an otherwise-recovered repository, using repository evidence only. Not feature work, not architecture redesign, not production work, not migration recovery. The final engineering correction sprint before Green Certification.

## 2. Scope

**In scope:** edit `database/seeds/101_seed_reference_data_framework.sql` (the 9 `re_meal_classes` rows) and `database/validation/900_structural_validation.sql` (Check 1 only).

**Out of scope:** any migration/rollback file; any schema, privilege or architecture change; any migration/rollback numbering; any production/live-DB action; any new feature; the WP-04DA-owned checks (900 Check 3, Check 5, 901 Test 1) which require live-DB values a repository-evidence-only package cannot derive; the three production-parity migrations (WP-5D).

## 3. Repository state before execution

HEAD `1e89bbe`, clean tree. Seed 101 `re_meal_classes` rows used scalar `slot` with `'addon'` (pre-migration-025 form). Validation 900 Check 1 expected 60 tables. Both are the exact WP-5F findings, re-confirmed live from the files this session (Step 3).

## 4. Execution strategy

Read every SQL file and the relevant WP/AGR/IDR docs again; independently reproduce both findings; correct only what repository evidence proves; re-validate; document; one commit.

## 5. Repository evidence (why each correction is recovery, not invention)

- **SEED-01:** Migration `025` (in-repo) converts `re_meal_classes.slot` to `text[]` with CHECK `slot <@ {breakfast,lunch,dinner,snack}`, legacy `'addon'`→`ARRAY['snack']`. REPO-WP-04B v1.1 records that all 9 rows were already `ARRAY[...]` with `'addon'`→`ARRAY['snack']` "genuinely on main" (2026-07-09) — a fix lost in the apverse-labs reconstruction. Batch1 MAP-DEC-003 forbids re-mapping Snack→addon at the planning_role level. The correction restores the documented, applied array form.
- **VALIDATION-01:** Repository migration inventory contains 62 `CREATE TABLE` statements (`grep -cE '^\s*CREATE TABLE' database/migrations/*.sql` = 62). The "60" in Check 1 predates migrations `021` (cuisines) and `024` (re_dish_regional_affinity). The corrected expected value 62 is derived from the migration set, not documentation.

## 6. Corrections performed

- **A — seed 101:** the 9 `re_meal_classes` slot values wrapped as single-element `text[]`; the two `'addon'`-slot rows (`ADDON_INFANT`, `ADDON_DIABETIC`) set to `ARRAY['snack']`. `planning_role`, `day_type`, fits, `cuisine_family`, `diet_type` unchanged. Per-row rationale documented inline. `re_addon_classes` rows deliberately NOT changed (that column is plain `text`, never array-converted).
- **B — validation 900 Check 1:** expected 60→62, self-evaluating (`pass` column), with an inline repository-derived derivation and a maintenance rule tying the number to the migration set.

## 7. Validation

Post-edit re-checks (no DB executed): all 9 seed slots are arrays within the allowed value set; no scalar/`'addon'` remains; re_addon_classes unchanged; independent base-table recount = 62 matches new Check 1; no migration/rollback file changed; exactly two files modified. Full detail in the WP-5E Validation Report.

## 8. Risks

Corrections not executed against a live DB (repository-evidence-only mandate) — mitigated by post-edit re-read and by grounding both fixes in already-applied evidence (migration 025 is live-applied; the seed array form was previously live per WP-04B). Residual: five auto-generated constraint names remain a WP-5G live-apply confirmation item (carried from WP-5F, unchanged here).

## 9. Acceptance criteria

Both WP-5F findings corrected from repository evidence; every changed row documented with rationale; nothing outside scope changed; no fabrication.

## 10. Exit criteria

Corrections + five project-history documents + KNOWLEDGE Session committed as one logical commit and pushed; STOP for Founder approval before WP-5F2/5D/5G.

## 11. Critical Self-Review

- **Considered** also applying WP-04DA's Check 3/Check 5/901 corrections while in the files. **Rejected** — those depend on live-DB values (33 RLS tables, 24 policies, trigger attachment) a repository-evidence-only package cannot derive, and they belong to the separately-approved WP-04DA. Absorbing them would blur the governance boundary and violate Step 4C.
- **Considered** rewriting Check 1 to enumerate all 62 table names and diff them (maximally "verify reality"). **Deferred** — larger than the named finding; the repository-derived count + derivation comment resolves VALIDATION-01 without over-reaching WP-5E's minimal-correction mandate.
- **Discovery:** the WP-04B document asserts a seed state that the reconstructed file did not carry — a doc↔file inconsistency directly required to complete WP-5E (it is the evidence for the seed fix). Recorded in the Decision Log rather than expanded into a broader audit.

## 12. Founder Sign-off

Founder acceptance of WP-5E: _______________________ Date: ___________
