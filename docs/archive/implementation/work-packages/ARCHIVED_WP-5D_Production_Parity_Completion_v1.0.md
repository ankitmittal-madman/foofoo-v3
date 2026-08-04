# STATUS

ARCHIVED

## Reason

Implementation completed.

This document is retained for historical reference only.

It must not be used as the primary implementation guide.

Refer to the active documentation for the current source of truth.

---

# WP-5D — Production Parity Completion (Founder Option B) v1.0

**Status:** ACTIVE — COMPLETED (canonical `pf1` recovered & committed; production overlay documented; parity closed to canonical scope). Companion certificate: REPO-CERT-005.
**Version:** v1.0
**Date:** 2026-07-13
**Placement:** docs/archive/implementation/work-packages/ARCHIVED_WP-5D_Production_Parity_Completion_v1.0.md
**Supersedes:** the open recommendations of [ACTIVE]_WP-5D_Production_Parity_Recovery_v1.0 (the WP-5D investigation; retained as history). Per Founder Option B this is the single consolidated completion package.
**Dependencies:** WP-5D investigation set (Evidence Register, Engineering Decision Log, Validation Report, Production Parity Report, REPO-CERT-004) — referenced, not duplicated; WP-5F2 execution; migrations 008/010/019/023.

> **Documentation note (why this is consolidated):** Per the Founder's Option B instruction, all engineering evidence, validation, decisions, parity, verification and conclusions are embedded here in one document. Separate sub-reports were **not** created. The **only** separate artifact is the execution certificate (REPO-CERT-005), because CLAUDE.md governance explicitly requires a companion certificate before a Work Package may read COMPLETED. The verbatim recovered SQL and full introspection evidence already live in the committed [ACTIVE]_WP-5D_Evidence_Register_v1.0; this document references rather than re-pastes it.

---

## 1. Founder Decision (final)

**Option B approved.** `rls_auto_enable()`, `ensure_rls`, and the postgres-owned automatic-RLS behaviour are a **Production Operational Overlay** and **SHALL NOT** become canonical repository objects. The repository remains the canonical engineering source of truth and must rebuild correctly without them. This decision supersedes every unresolved WP-5D recommendation.

## 2. Canonical `pf1` — recovered & committed

**File:** `database/migrations/029_pf1_security_hardening.sql` (+ paired `database/rollback/029_pf1_security_hardening_rollback.sql`).
**Identity:** production ledger `pf1_security_hardening`, version `20260710101630`. Recovered **verbatim** from `supabase_migrations.schema_migrations.statements` (HIGH confidence — exact applied SQL). Ordinal `029_` continues the repo convention (as `027_`/`028_` did for their bare ledger names).

**Engineering intent preserved:** Finding 1 (lock `fn_assign_tag_vector_positions` to service_role + pin search_path); Finding 2 (complete migration-008 AGR-001 by revoking INSERT/REFERENCES on the derived `dishes` columns in addition to UPDATE); Finding 3 (revoke PUBLIC/anon/authenticated EXECUTE on the 3 trigger functions, grant service_role only); Finding 4 (pin search_path on the trigger functions).

### 2.1 Quarantine (the single Option-B exclusion)
Production `pf1` also contained:
```sql
REVOKE EXECUTE ON FUNCTION public.rls_auto_enable() FROM PUBLIC, anon, authenticated;
```
- **Why quarantined:** `public.rls_auto_enable()` is a production operational-overlay object (see §3); it exists in no canonical migration, so this statement would error in a clean repository rebuild.
- **How:** the line is **retained as a comment** in `029_…sql` (not deleted), with inline evidence, the Founder Option-B reference, and its operational dependency documented.
- **Evidence:** exact SQL and provenance in [ACTIVE]_WP-5D_Evidence_Register_v1.0 §2/§4.
- **Founder approval:** Option B (this document §1).
- **Operational dependency:** on production only, the overlay owner applies that REVOKE as part of the same operational hardening; it is intentionally out of canonical scope.
- **Result:** every other `pf1` statement is canonical and executes cleanly (verified §4).

### 2.2 Effectiveness (measured, not assumed)
Clean-room (fresh PostgreSQL 15, Supabase-compat bootstrap) after building 001→029:
- `anon` EXECUTE on `fn_derive_dish_attributes` → **false**; `service_role` → **true**; search_path → `public, pg_catalog`. ✅
- `public.dishes` derived column `diet_type` for `authenticated`: **col_UPDATE / col_INSERT / tbl_UPDATE / tbl_INSERT = false**, **col_SELECT = true**.

This is a material improvement over WP-5F2 (which, at 001–028 only, measured `authenticated` col_UPDATE = **true**). So `pf1` **actively closes** the WP-5F2 / WP-04DA "Sixth Finding" GRANT-level gap on the derived columns (read retained, write removed), on top of the RLS default-deny that WP-5F2 already proved protects row data. Recovering `pf1` therefore hardens the canonical repository, not just documents production.

## 3. Production Operational Overlay — documentation (Option B, embedded)

| Aspect | Detail |
|---|---|
| **Objects** | `public.rls_auto_enable()` (event-trigger function, SECURITY DEFINER, owner `postgres`) + `ensure_rls` event trigger (`ON ddl_command_end`, owner `postgres`, `EXECUTE FUNCTION rls_auto_enable()`). |
| **Purpose** | Defensive automation: auto-enables Row Level Security on every newly-created `public` table at DDL time, so no table is ever accidentally left RLS-disabled. |
| **History** | Created out-of-band in production (no migration provenance — `migrations_creating = null`); referenced only by `pf1`. Postgres-owned, i.e. added manually/operationally, not via the tracked migration pipeline. |
| **Behaviour** | On `CREATE TABLE`/`CREATE TABLE AS`/`SELECT INTO` in `public`, runs `ALTER TABLE … ENABLE ROW LEVEL SECURITY`. Enabling RLS without a policy = default-deny (service_role bypasses). |
| **Difference vs repo** | Measured: production has RLS enabled on **33** public tables vs a canonical repo build's **20** (+13 = 7 internal audit tables + 6 partition children). This **diverges from the frozen migration-019 design**, which deliberately leaves internal audit tables without RLS. Policies (24) and base tables (62) are identical. |
| **Reason for exclusion** | Founder Option B: it changes the frozen migration-019 RLS design; adopting it as canonical would be an architecture change. It is operational, not engineering-canonical. |
| **Future maintenance** | Owned and maintained operationally on production by the overlay owner, outside the migration pipeline. If a future engineer sees RLS on tables migration 019 didn't enable, this overlay is why. |
| **Founder decision** | Option B — remain operational, never canonical (this document §1). |
| **Future engineering rule** | Do not add `rls_auto_enable`/`ensure_rls` (or equivalent auto-RLS event triggers) to `database/migrations`. Canonical RLS is defined exclusively and explicitly by migration 019 (+021 for cuisines). Any future canonical RLS change is a normal, numbered migration. |

## 4. Repository Verification (STEP 3, execution-backed)

Clean-room (disposable local PostgreSQL 15, never production) — full results:

| Check | Result |
|---|---|
| Build 001→029 (unseeded) | ✅ 29/29 apply cleanly (029 included) |
| Teardown 029→001 | ✅ 29/29 reverse cleanly; end state **0 base tables, `re_engine` dropped** |
| Migration chain | ✅ contiguous 001–029, no renumbering of 001–028 |
| Rollback chain | ✅ **29/29** paired (invariant preserved; was 28/28) |
| Seed layer | ✅ unchanged (100–102; SEED-01 fix from WP-5E intact) |
| Validation layer | ✅ unchanged (900–904) |
| Architecture / freeze | ✅ untouched — overlay deliberately not introduced |
| Governance / naming / versioning | ✅ `029_pf1_security_hardening.sql` matches SQL naming (NNN_description, no status/version); docs use `[ACTIVE]_…_vX.Y.md` |
| Cross-references | ✅ 029 headers cite migrations 008/010/023, WP-5D evidence, Option B |
| Self-containment / rebuildability | ✅ repo rebuilds with **no** dependency on the operational overlay |
| Developer onboarding | ✅ overlay divergence now documented (§3) so a new engineer is not surprised by production RLS state |

Nothing introduced by WP-5D breaks repository integrity.

## 5. Production Parity (STEP 4, final — every difference classified)

| Item | Classification | Status |
|---|---|---|
| Migrations 001–026 | Canonical | Parity ✅ |
| 027/028 (repo ordinals vs bare ledger names) | Canonical (naming convention) | Parity ✅ (cosmetic filename note; no rename performed — needs Founder authorization) |
| `pf1_security_hardening` → `029_pf1_security_hardening` | Canonical | **Parity ✅ (now committed)** |
| `rls_auto_enable()` + `ensure_rls` + auto-RLS on +13 tables | **Operational Overlay** | Excluded by Option B; documented §3 ✅ |
| `103_production_cuisines` | **Illustrative/Environment-Specific Data** | Excluded (production seed data; repo uses illustrative 100–102 per IDR-001) ✅ |
| `103_production_ingredients` | **Illustrative/Environment-Specific Data** | Excluded (same) ✅ |

**No remaining difference is unexplained.** Schema parity: base tables 62=62, policies 24=24 ✅. Security parity: `pf1` canonical content now in repo ✅; the RLS-enablement delta is fully attributed to the Operational Overlay. Functions/constraints/indexes: identical at the migration level (a byte-level `pg_dump` diff is a WP-5G live-cert activity).

- **Canonical migration parity: 29 / 29 = 100%** (all canonical engineering migrations now in the repo).
- Non-canonical production artifacts (overlay + production data seeds) are classified and intentionally excluded.

## 6. Repository Completeness Assessment (STEP 5)

| Dimension | State | Note |
|---|---|---|
| Migration completeness | ✅ 100% canonical (001–029) | execution-proven |
| Rollback completeness | ✅ 29/29 | execution-proven teardown to empty |
| Documentation completeness | ✅ | lean; WP history + KNOWLEDGE current |
| Architecture completeness | ✅ | frozen; overlay boundary documented |
| Governance completeness | ✅ | naming/versioning/certificate rules honoured |
| Engineering completeness | ✅ | build→seed→validate→teardown all proven (WP-5F2 + this WP) |
| Developer readiness | ✅ | self-contained rebuild; overlay caveat documented |
| Knowledge preservation | ✅ | KNOWLEDGE Sessions 1–9 |
| Operational readiness | ⚠️ deferred | live/prod certification is WP-5G scope |
| Maintainability / integrity | ✅ | no hidden behaviour; every prod difference classified |

## 7. Standards Check (STEP 7)

Filenames, status prefixes (`[ACTIVE]`), version (`v1.0`), SQL naming (`029_pf1_security_hardening.sql` / `…_rollback.sql`), placement (migrations/, rollback/, work-packages/, certificates/), and cross-references all conform. No unrelated historical files renamed.

## 8. Conclusion

Founder Option B is fully executed. The single canonical gap (`pf1`) is recovered, committed, and clean-room-verified; the production operational overlay is documented and deliberately excluded; every production difference is classified with no unexplained residue. Canonical engineering parity is **100%**. The repository is the complete engineering source of truth and rebuilds deterministically without any production-only object.

## 9. Founder Decision section

No new architectural contradiction, no unexpected production difference, no integrity uncertainty, and no competing interpretation remained open after Option B — so no further Founder decision is required for WP-5D. (Any future adoption of the overlay, or the 027/028 filename normalization, would each be a separate, explicitly-authorized action.)

## Critical Self-Review

- **Considered** committing `pf1` verbatim including the `rls_auto_enable` REVOKE. **Rejected** — it would break clean rebuild; Option B + quarantine is the correct resolution.
- **Considered** dropping the quarantined line entirely. **Rejected** — the brief requires retaining it (commented) with rationale, so provenance is not lost.
- **Considered** re-pasting all verbatim SQL/evidence here. **Rejected** — it already exists in the committed WP-5D Evidence Register; duplication contradicts the lean directive.
- **Limitation:** parity is asserted at migration + key-object level with clean-room execution; a full byte-level production `pg_dump` diff is intentionally left to WP-5G.

## Founder Sign-off

Founder acceptance of WP-5D Completion: _______________________ Date: ___________
