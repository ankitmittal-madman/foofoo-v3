# REPO-CERT-010 — WP-6E.3 Security Hardening & Validation Modernization v1.0

**Status:** ACTIVE — Production Security & Validation Certificate (ICD-1 scope).
**Version:** v1.0
**Date:** 2026-07-14
**Placement:** docs/project-history/certificates/[ACTIVE]_REPO-CERT-010_WP-6E3_Security_Hardening_and_Validation_Modernization_v1.0.md
**Supersedes:** none. **Resolves:** REPO-CERT-009 §7.1 Finding F-1 (derived-column privilege drift).
**Dependencies:** REPO-CERT-009 (WP-6E.2 sync); REPO-CERT-007 (GREEN baseline); migration 029 (pf1); migration 030; validation 900–905.

---

## Executive Summary

WP-6E.3 completed the post-synchronization engineering left open by REPO-CERT-009: it (1) investigated and root-caused the derived-column **privilege drift** on the live project `cmkswalqpmmqojwdmqbv`, (2) restored repository parity by applying **only** the missing privilege statements from migration 029, (3) **modernized** the validation suite (900–905) to the canonical ICD-1 baseline, and (4) re-ran the **full regression** — now passing end-to-end. **No canonical/business/reference data, counts, or schema were changed.** The only live-database change was the privilege reconciliation (REVOKE/GRANT/ALTER FUNCTION); the only repository changes were four validation scripts plus documentation.

**Production security posture: HARDENED. Repository parity: RESTORED (privilege + validation). Production readiness: READY for Backend Engineering.**

---

## 1. Security Drift Report (Phase 1)

**Question:** why is migration 029 recorded as applied while its derived-column REVOKEs are not in force?

**Evidence gathered (all live/repository, no assumptions):**

1. **Repo migration 029 was never edited after creation** — `git log` shows a single commit (`7ffe7b3`, WP-5D). Not tampered.
2. **The applied migration DID contain the REVOKEs.** The recorded `supabase_migrations.schema_migrations.statements` for `pf1_security_hardening` (version `20260710101630`) contain verbatim: `REVOKE INSERT, UPDATE, REFERENCES (diet_type, is_jain, allergen_flags, genome_vector, popularity_score, acceptance_rate_7d, acceptance_rate_30d) ON public.dishes FROM authenticated, anon;` plus the four `REVOKE EXECUTE … FROM PUBLIC, anon, authenticated`. So it was **not** partially recorded or edited.
3. **The effective ACL shows the REVOKEs are absent.** `pg_class.relacl` for `public.dishes` = `anon=arwdDxtm/postgres`, `authenticated=arwdDxtm/postgres` (full ALL, granted by `postgres`); and every derived column's `pg_attribute.attacl` = **NULL** (no column-level revoke exception exists). If pf1's REVOKE were in force, those columns would carry explicit ACL exceptions. Likewise all four trigger functions were EXECUTE-able by `anon`/`authenticated`.
4. **The grant source is the Supabase platform default privilege, not a repo migration.** `pg_default_acl` for schema `public` shows `GRANT ALL ON TABLES TO anon, authenticated, service_role`, owned by `supabase_admin` **and** `postgres` (platform bootstrap). Repo migration 001 only sets `re_engine` defaults (→ service_role); it does not grant public tables to anon/authenticated.
5. **No later migration or WP-6E.2 seed re-granted.** A scan of every recorded migration's statements found grants only in `001` (platform-style, pre-dishes) and `pf1` itself; migration 030 and repository seeds 103–117 contain no GRANT to anon/authenticated.

**Root cause (evidence-backed):** On this newly-provisioned project, `public.dishes` (created by migration 008) inherited **table-level ALL** for `anon`/`authenticated` from the Supabase **platform default privilege** (`GRANT ALL ON TABLES`, owner `supabase_admin`/`postgres`). A table-level `GRANT ALL` supersedes column-level REVOKE exceptions, and the effective ACL proves pf1/029's column-level REVOKEs are **not reflected** in this project (relacl = ALL; all derived attacl = NULL). The migration is recorded as applied, but the certified privilege hardening did not survive the platform default grant on this provisioning. This is environment drift from the certified clean-room (REPO-CERT-007), **not** a repository defect, a partial execution, or a post-hoc application re-grant.

**Timeline (evidence-anchored):**
- 2026-07-06 — migrations 001 (re_engine defaults → service_role) and 008 (dishes created; inherits platform default ALL for anon/authenticated).
- 2026-07-10 — pf1/029 recorded + applied (column REVOKEs + function EXECUTE revokes present in `statements`).
- (project provisioning) — effective `dishes` ACL = platform default ALL for anon/authenticated; pf1 column REVOKEs absent (attacl NULL) → **drift**.
- 2026-07-14 — REPO-CERT-009 (WP-6E.2) detects & reports the drift (F-1); no fix (out of Phase-2 scope).
- 2026-07-14 — WP-6E.3 reconciles (§2 below).

**Honest limit:** PostgreSQL does not journal GRANT/REVOKE events, so the exact wall-clock moment the platform grant took precedence cannot be timestamped. The ACL state + migration record + absence of any re-grant in migrations/seeds are conclusive as to *what* is in force and *why*.

## 2. Reconciliation (Phase 2) — repository parity restored

Repository evidence proves drift (certified baseline REVOKEs the derived columns + function EXECUTE; live had them granted). Reconciliation applied **only the missing privilege statements from migration 029** — verbatim, active statements only (the repo-quarantined `rls_auto_enable` REVOKE, Option B, was **not** applied). No unrelated SQL. No data, schema, RLS, or counts touched.

**SQL executed (one transaction):**
```
REVOKE EXECUTE ON FUNCTION public.fn_assign_tag_vector_positions() FROM PUBLIC, anon, authenticated;
GRANT  EXECUTE ON FUNCTION public.fn_assign_tag_vector_positions() TO service_role;
ALTER FUNCTION public.fn_assign_tag_vector_positions() SET search_path = public, pg_catalog;
REVOKE INSERT, UPDATE, REFERENCES (diet_type, is_jain, allergen_flags, genome_vector,
  popularity_score, acceptance_rate_7d, acceptance_rate_30d) ON public.dishes FROM authenticated, anon;
REVOKE EXECUTE ON FUNCTION public.fn_derive_dish_attributes()      FROM PUBLIC, anon, authenticated;
GRANT  EXECUTE ON FUNCTION public.fn_derive_dish_attributes()      TO service_role;
REVOKE EXECUTE ON FUNCTION public.fn_propagate_ingredient_change() FROM PUBLIC, anon, authenticated;
GRANT  EXECUTE ON FUNCTION public.fn_propagate_ingredient_change() TO service_role;
REVOKE EXECUTE ON FUNCTION public.fn_update_dish_genome_vector()   FROM PUBLIC, anon, authenticated;
GRANT  EXECUTE ON FUNCTION public.fn_update_dish_genome_vector()   TO service_role;
ALTER FUNCTION public.fn_derive_dish_attributes()      SET search_path = public, pg_catalog;
ALTER FUNCTION public.fn_propagate_ingredient_change() SET search_path = public, pg_catalog;
ALTER FUNCTION public.fn_update_dish_genome_vector()   SET search_path = public, pg_catalog;
ALTER FUNCTION public.fn_sync_profile_allergen_union() SET search_path = public, pg_catalog;
```

**Before → After verification:**

| Check | Before | After |
|---|---|---|
| authenticated UPDATE dishes.diet_type | **true** | **false** |
| anon UPDATE dishes.allergen_flags | **true** | **false** |
| authenticated UPDATE dishes.popularity_score | **true** | **false** |
| fn_derive/propagate/genome/assign EXECUTE by anon/authenticated | **true** | **false** |
| fn_* EXECUTE by service_role | true | **true** (retained) |
| authenticated SELECT dishes (app read) | true | **true** (unaffected) |
| anon SELECT dishes (public read) | true | **true** (unaffected) |
| service_role SELECT/INSERT/UPDATE dishes | true | **true** (backend unaffected) |
| dishes RLS enabled | true | **true** (unchanged) |

**Application-safety note (evidence-backed):** PostgreSQL cannot represent "table-level UPDATE minus specific columns", so revoking column privileges from a role holding a table-level grant removes the table-level INSERT/UPDATE entirely (authenticated column UPDATE is now false for *all* dishes columns, not only the derived ones). This is **acceptable and stricter, not a regression**: end-users never write the dish catalog (canonical content is owned by `service_role`/admin), `SELECT` for both client roles is preserved (catalog reads work), `service_role` retains full write access (backend WP-8B unaffected), and RLS remains the primary row-level guard. DELETE was intentionally left as migration 029 defines it (029 does not revoke DELETE; RLS governs it), preserving exact 029 parity.

## 3. Validation Modernization Report (Phase 3)

Four scripts were modernized. **Intent preserved, accuracy improved, nothing weakened** — every removed illustrative fixture was replaced with a canonical equivalent that exercises the *same* logic, and every stale target was mapped to the certified ICD-1 baseline.

| Script / check | Was (stale) | Now (canonical) | Why |
|---|---|---|---|
| 900 Check 2 | `conrelid::regclass::text IN ('public.dishes',…)` → 0 rows | compare by OID: `conrelid = ANY(ARRAY[…]::regclass[])` | regclass renders unqualified on search_path; text match never hit — now returns the 7 safety-critical FKs |
| 900 Check 3 | "expect 4+4"; lists all non-internal triggers (incl. Supabase storage) | "expect 5 fn_* + 4 app triggers"; triggers scoped to public/re_engine | there are 5 `fn_*` functions; removes system-trigger noise |
| 900 Check 5 | fixed count "expect 19" (pre-migration-021) | invariant: **0 public tables without RLS** | stale + brittle; the real invariant is "no table lacks RLS" — stronger |
| 900 Check 7 | S-08=1050, S-10=142, S-15=324 (pre-Option-C) | S-08=165, S-10=6, S-15=0 (ICD-1) | Founder-approved Option C; remainder in Deferred Register; matches 905 |
| 901 Test 1 | expected Poha diet_type='veg' (file-102) | 'vegan' (canonical seeds 103/106/107) | canonical Poha derives vegan |
| 901 Test 2 | dish 'Aloo Poha with Peanuts' (removed) | 'Bharli Vangi' (canonical, carries nut bit) | same allergen-union path |
| 901 Test 4 | 'Aloo Poha with Peanuts' + 'Peanuts' (removed) | 'Bharli Vangi' + canonical slug 'peanut' | same fn_propagate_ingredient_change proof |
| 902 Test 1 | class 'DIN_NON_VEG_MAIN' (illustrative) | 'LD_CHICKEN_HOME_CURRY' (canonical) | same Gate-1 data-dependency proof |
| 902 Test 3 | class 'ADDON_INFANT' (illustrative) | 'BF_INFANT_6M_SOFT' (canonical) | same Gate-4 planning-role proof |
| 904 smoke | `day_of_week='monday'`; IDR-001 "1 illustrative row" PARTIAL branches | `'Mon'` (canonical seed-114 format); PARTIAL→hard FAIL | canonical uses 3-letter days; full RE layer loaded — strengthened |

**Untouched:** 903 (no stale fixtures; its cross-user SKIP is an auth-fixture environment limit) and 905 (already Option-C-aware; the authoritative RE validation). No validation intent was changed or weakened.

## 4. Regression Validation Report (Phase 4)

Full suite re-run against the live canonical database. **All pass** (two SKIPs are auth-fixture environment limits, identical to the certified baseline — not failures):

- **900:** Check 1 (62 tables) ✓ · Check 2 (7 safety FKs present) ✓ · Check 3 (5 fn_* + 4 app triggers) ✓ · **Check 4 (authenticated cannot UPDATE derived cols) ✓** · Check 5 (0 tables without RLS; 33/33) ✓ · Check 6 (re_engine locked) ✓ · **Check 7 (all 15 seed gates exact, incl. ICD-1 S-08/10/15) ✓**.
- **901:** Test 1 Poha=vegan/jain=false ✓ · Test 2 Bharli Vangi nut bit ✓ · Test 3 Butter Chicken=non_veg ✓ · **Test 4 propagate re-derive (1→33) ✓** · **Test 5 authenticated blocked from derived write ✓**.
- **902:** Gate-1 data dependency ✓ · Gate-3 (Poha is_jain=false) ✓ · Gate-4 (BF_INFANT_6M_SOFT planning role) ✓ · Test 4 SKIP (no profile fixture).
- **903:** anon write-block ✓ · re_engine invisibility ✓ · cross-user SKIP (no fixtures).
- **904:** weight-ladder sums=1.0 ✓ · invalid weight rejected ✓ · event weights ✓ · **smoke test full pass (Mon plan resolved) ✓**.
- **905 (authoritative RE validation): FULL PASS** — 12 seed gates, ICD-1 dish-linked >0, GAP-002 (2952 distinct, 0 without tier, weekly=cohorts×7), **9/9 FK anti-joins = 0 orphans**, planning-role safety = 0 violations.

**Post-regression integrity (no drift introduced):** the 901 Test 4 mutation reverted cleanly — `peanut.allergen_flags=1`, `Bharli Vangi.allergen_flags=1`; counts unchanged (dishes 802, ingredients 191, dish_tags 10456, weekly 20664); genome 802/802; diet_type NULL = 0; no leftover fixtures; no idle-in-transaction sessions.

## 5. Production Security Posture

- Client roles (`anon`, `authenticated`) **cannot write** any `public.dishes` column (derived or otherwise) and **cannot EXECUTE** the derivation/genome/tag trigger functions; they retain `SELECT` for catalog reads.
- `service_role` retains full access (backend Edge Functions unaffected).
- `re_engine` schema is invisible to client roles; RLS enabled on every public table and blocks anon writes (defense-in-depth intact).
- Trigger functions have pinned `search_path` (injection hardening) and remain SECURITY DEFINER (triggers fire regardless of client EXECUTE).
- Result: the certified AGR-001 / Invariant-6 posture is now **in force on the live canonical environment** — parity with REPO-CERT-007.

## 6. Deliverables

1. Security Drift Report — §1. 2. Reconciliation — §2. 3. Validation Modernization Report — §3. 4. Regression Validation Report — §4. 5. Final Production Security Certificate — this document (§5 posture). 6. Updated KNOWLEDGE.html — Session 20.

## Critical Self-Review

- **Did I change canonical/business data?** No. The only live change was privilege statements from migration 029; the one test-induced mutation (peanut) reverted to `1` (verified). Counts, derivations, schema, RLS unchanged.
- **Is the root cause proven or guessed?** The *what* (REVOKEs absent; platform default GRANT ALL in force) is proven by ACL + migration records. The exact GRANT timestamp is unknowable (PG doesn't log it) — stated honestly, not fabricated.
- **Did modernization weaken any check?** No — every change replaced a removed fixture with a canonical equivalent or tightened a stale target/invariant; two checks became *stricter* (900 Check 5 invariant; 904 PARTIAL→FAIL).
- **Scope discipline:** applied only the missing 029 privilege statements; did not reapply the whole migration, did not touch the quarantined rls_auto_enable line, did not run unrelated SQL.

## 7. Remaining Technical Debt

- **S-15 `re_city_migration_overlays`** — DEFERRED (canonically 0; needs `migration_duration_band` source). Unchanged from baseline.
- **Auth-fixture-dependent validations** (902 Test 4 live Gate-4 insert; 903 cross-user isolation) self-SKIP without seeded profile fixtures — a CI/fixture gap, not a data or logic defect; recommend adding test profile fixtures when the auth flow (WP-8C) lands.
- **ICD-1 Deferred Knowledge Register** (S-08/S-10 dish remainder) — unchanged product backlog.

## Versioning & Placement

v1.0, placed in docs/project-history/certificates/ per the Placement Rule. Resolves REPO-CERT-009 §7.1 F-1. Naming per WP-5AA standard.

## Founder Sign-off

Founder acceptance of WP-6E.3 Security Hardening & Validation Modernization: _______________________ Date: ___________
