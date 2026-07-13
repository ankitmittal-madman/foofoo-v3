# REPO-WP-03D_Seed_Readiness_Certification_v1.0

**Repository Engineering Work Package #3D — Seed Readiness Certification**
**Project:** FooFoo (`apverse-labs/foofoo-v3`) · **Supabase:** `slsqtlygeekdppuyiiff`
**Placement:** `docs/project-history/[ACTIVE]_REPO-WP-03D_Seed_Readiness_Certification_v1.0.md`
**Date:** 2026-07-09 · **Status:** DESIGNED — awaiting Founder approval to execute
**Prerequisites:** WP-3B ✅ · WP-3A ✅ · WP-3C ✅ (all independently live-verified this session — see Verification Summary below)

**Success criterion (governing this entire package):** Produce a single, evidence-backed Seed Readiness Certificate — a GO/NO-GO verdict on whether the repository, database, and validation infrastructure are genuinely ready for WP-4 Seed Engineering to begin. This package **certifies**; it does not fix, load, or execute anything beyond the one small validation-script patch scoped in Section 5.

---

## Pre-Design Independent Verification Summary

Before designing this package, the founder-provided status summary ("WP-1/2/3B/3A/3C all Complete") was independently checked against live sources rather than accepted at face value.

| Claim | Verified how | Result |
|---|---|---|
| 26/26 migrations applied | Live query: `supabase_migrations.schema_migrations` | ✅ Confirmed, unchanged since last session |
| WP-3C's 3 files actually committed | `raw.githubusercontent.com` HTTP 200 checks | ✅ All 3 exist |
| Check 1 fix (60→62) + Checks 8–12 added | Read live file content directly | ✅ Matches WP-3C's report exactly |
| Check 2 bug is real | Ran the exact broken query live | ✅ Reproduced — returns empty |
| The 7 FKs Check 2 is supposed to find actually exist | Ran an unbroken equivalent query | ✅ All 7 present |
| Checks 8–12 pass live | Spot-checked `cuisines` table existence | ✅ Confirmed |
| Seed file 101 is still scalar-incompatible with `slot text[]` | Read live file content directly | ⚠️ **Confirmed still broken** — inserts `'breakfast'`, `'addon'` as scalars |
| Rollback file count (26/26) | Not re-verified this session (GitHub API rate-limited) | Carried forward from last session's confirmed count — **not freshly re-checked**; WP-3D execution must re-confirm |

**One correction to the founder's summary:** WP-3A/3B/3C being "Complete" is accurate for what each was scoped to do. It does **not** mean the repository is seed-ready — seed file `101` has not been touched by any WP-3 sub-package (correctly; that was never its job) and remains shape-incompatible with the current schema. WP-3D exists specifically to certify this state plainly, not let "WP-3 complete" imply something it doesn't.

---

## 1. Objective

Produce a single, evidence-backed **Seed Readiness Certificate** — a GO/NO-GO verdict on whether the repository, database, and validation infrastructure are genuinely ready for WP-4 Seed Engineering to begin. This package **certifies**; it does not fix, load, or execute anything.

## 2. What "Ready" Means Here (bright line)

WP-3D is done the moment every dimension below has direct evidence and a verdict. It is **not** done by inferring readiness from "WP-3A/B/C all said Complete" — that would be exactly the "described vs. verified" failure mode this project has repeatedly guarded against.

## 3. Certification Dimensions & Live Findings

| # | Dimension | Live Evidence (this session) | Verdict |
|---|---|---|---|
| 1 | Migration history integrity | 26/26 migrations in `supabase_migrations.schema_migrations`, matches file-by-file naming | ✅ PASS |
| 2 | Rollback pairing completeness | 26/26 confirmed **last session** (repo tree read); **not re-verified this session** due to GitHub API rate-limit | 🟡 CARRIED FORWARD, not fresh — WP-3D execution must re-confirm live, not assume |
| 3 | Structural validation currency (900-series) | Checks 1, 8–12 read live, match WP-3C's report exactly; Check 1 constant correct (62) | ✅ PASS |
| 4 | Structural validation correctness (does every check actually work) | Check 2 reproduced as broken — `regclass::text` comparison returns empty despite all 7 target FKs existing (confirmed via a working equivalent query) | ❌ **Confirmed defect, unresolved** |
| 5 | Documentation currency (`DOC-P3-04 v1.4`) | File exists, additive-only per WP-3C report | ✅ PASS (not re-read line-by-line this session — reasonable to trust given WP-3C's own live-recount rigor) |
| 6 | Seed file structural compatibility | `101_seed_reference_data_framework.sql` still inserts scalar `'breakfast'`/`'addon'` into now-`text[]` columns — read live, confirmed unfixed | ❌ **Confirmed incompatibility, exactly as originally flagged at WP-3 design time, still present** |
| 7 | Safety-gate readiness (diet/never-list/Jain violations) | Cannot be tested — 0 rows loaded in any table | ⚪ NOT YET TESTABLE (expected at this stage, not a defect) |

## 4. Classification — Real Blocker vs. Documentation vs. Validation vs. Future Improvement

**Real blockers for WP-4 (must be resolved before seed loading, but NOT by WP-3D):**
- Seed file 101's scalar/array mismatch (`slot` column). This is genuinely **WP-4's** first task, not WP-3D's — WP-3D's job is to certify *that this exists and is understood*, not touch the seed file. Touching it here would blur the WP-3/WP-4 boundary this framework has held since `REPO-WP-03 v1.0`'s own stated line: *"WP-3D changes nothing, it only knows things."*

**Validation issues (repository artifact, not seed/schema problem):**
- Check 2's `regclass::text` bug. Real, reproducible, confirmed the underlying FKs exist. This is a **validation-script defect**, not a schema or seed defect.

**Documentation issues:**
- None newly found this session beyond what WP-3C already closed. `DOC-P3-04 v1.4`'s additive amendment stands as reported.

**Future improvements (not blocking, not urgent):**
- Rollback-file re-verification tooling that doesn't depend on GitHub API rate limits (e.g., a repo-side manifest file future sessions can read without hitting external rate limits) — candidate for `DOC-P3-12` Governance Improvement Backlog, not action here.

## 5. Should Check 2 Be Fixed In WP-3D? — Recommendation and Justification

**Recommendation: Yes, fix it inside WP-3D, as a small, explicitly-scoped, non-architectural patch — not deferred to WP-4 or left standing.**

**Justification:**
- **What kind of thing it is:** Check 2 is validation *infrastructure*, exactly the same category of object WP-3C already touched. It is not a schema change, not a seed change, and not an architecture decision — it requires no Founder decision, same as WP-3C's Check 1 fix required none.
- **Why not defer to WP-4:** WP-4's own design will presumably lean on the 900-series as its post-load verification gate (the established pattern — "WP-4's prompt will treat DOC-P3-04 as authority and the 900-series as its gate," stated verbatim in `REPO-WP-03 v1.0`). Handing WP-4 a certified-ready validation suite that still contains one confirmed-broken check means WP-4 either re-discovers this defect mid-execution (wasted cycles) or worse, doesn't notice a genuinely broken FK later because Check 2 is silently useless.
- **Why not leave it as a footnote:** A "known broken but not fixed" validation check sitting inside a document titled *Certificate* undermines what a certificate is for.
- **Why this doesn't violate WP-3D's "certify, don't fix" rule:** That rule was about **seed files and schema** — "no seed file is modified, no row is loaded." It was never about validation-script bugs; WP-3C already established 900-series scripts are living repository artifacts, "updated in place with git history," not frozen governance documents.
- **Size/risk check:** The fix is small and mechanical — replace the `conrelid::regclass::text IN (...)` string comparison with a schema-qualified join that reliably matches. Effort and risk are proportionate to including it here.

**If the founder disagrees and wants it deferred instead:** the only valid reason would be preferring WP-3D stay a strictly zero-code-change certification exercise. Legitimate stylistic preference — this is the founder's call, not a technical requirement either way.

## 6. Dependencies

WP-3A, WP-3B, WP-3C — all complete, independently verified above (with the one noted rollback-recheck caveat).

## 7. Authority

`REPO-WP-03 v1.0`'s own WP-3D definition (execution order, certify-don't-fix boundary) — this document supersedes only its file-naming/placement, not its substance. `DOC-P3-09` §06E for documentation persistence rules (unaffected — WP-3D produces a new certificate document, doesn't touch frozen ones).

## 8. Scope — What WP-3D Does

1. Re-verify rollback pairing (26/26) live against the repo — do not carry forward last session's count without a fresh check.
2. Fix Check 2's `regclass::text` bug in `900_structural_validation.sql` (small, scoped, per Section 5).
3. Run the full 900-series (now including the Check 2 fix) against live DB; capture full real output.
4. Perform the statement-level seed-file compatibility audit across `100_seed_config_tables.sql`, `101_seed_reference_data_framework.sql`, `102_seed_illustrative_content_and_dependents.sql` — classify every INSERT: COMPATIBLE / STALE-SHAPE / STALE-TARGET / ILLUSTRATIVE-SUPERSEDED. The scalar-slot issue in 101 must appear here explicitly, not just as a footnote.
5. Produce the **Seed Readiness Certificate**: schema state, validation results (post-fix), rollback completeness (freshly confirmed), seed-file compatibility table, explicit GO/NO-GO verdict for WP-4.

## 9. Out of Scope

- No seed file is modified or rewritten (only audited/classified)
- No row is loaded anywhere
- No schema or architecture change
- No WP-4 design or seed-engineering strategy decisions — the audit *informs* WP-4, it doesn't design it

## 10. Founder Decisions Required

One, carried over unchanged from `REPO-WP-03 v1.0`'s original WP-3D scope: **none anticipated**, except the contingent case — if the seed-file audit surfaces something suggesting the *schema* (not the seed file) is wrong, that inverts authority and is a Founder-level stop.

One new, small one: **approve fixing Check 2 inside this package** (Section 5), or explicitly say defer.

## 11. Execution Strategy

1. Live rollback re-check (repo tree read, 26 forward + 26 rollback file pairs)
2. Check 2 fix, applied and tested against the live 7-FK spot-check
3. Full 900-series run, all checks reported with real output (Check 7 still expected-fail — unseeded)
4. Statement-level audit of 100/101/102 seed files
5. Certificate authored and committed

## 12. Validation Strategy

The certification *is* the validation — same principle as `REPO-WP-03 v1.0`'s original WP-3D. No separate validation-of-the-validation step beyond what's already in Execution Strategy.

## 13. Rollback Strategy

Check 2's fix is a git-tracked script edit — `git revert` if needed. Nothing else in this package touches anything reversible-or-not, since nothing else changes state.

## 14. Deliverables

- `900_structural_validation.sql` — Check 2 fixed (small diff)
- `REPO-WP-03D_Seed_Readiness_Certificate_v1_0.md` — the certificate itself: schema state, validation results, rollback completeness, seed-file compatibility table, explicit GO/NO-GO
- Execution Report

## 15. Acceptance Criteria

- Rollback pairing freshly confirmed 26/26 (not carried forward from a prior session)
- Check 2 fixed and proven against the known 7-FK spot-check
- Full 900-series run with real, complete output (all checks, including expected-fails, reported honestly)
- Seed-file audit covers 100% of statements across all three files, each classified
- Certificate carries an explicit, evidenced GO or NO-GO — not a hedge

## 16. Exit Criteria

Acceptance met, Execution Report produced, **STOP — WP-3 fully closed, Founder approval gates WP-4.**

## 17. Risks

- Seed-file audit is large (three files, many statements) — risk of shallow, file-level pass instead of statement-level. Mitigated by the explicit statement-level acceptance criterion.
- Temptation to "just fix 101 while we're in there" since the incompatibility is now doubly confirmed — must be resisted; that is WP-4's job, named explicitly in Out of Scope.

## 18. Stop Conditions

- Rollback re-check finds fewer than 26/26 pairs — Founder-level stop, this would be new information contradicting last session's finding
- Seed-file audit finds a discrepancy implying the *schema* (not the file) is wrong — Founder-level stop, inverted authority
- Any temptation, noticed mid-execution, to modify a seed file "just to fix the obvious thing" — explicit self-stop, not a Founder-level one, since Out of Scope already forbids it

## 19. Critical Self-Review

- **Considered:** leaving Check 2 for WP-4 to discover and fix as part of its own validation-setup work — rejected per Section 5's full reasoning; the cost of shipping a known-broken gate inside a document called "Certificate" outweighs the small effort to fix it here.
- **Considered:** re-stating "WP-3A/B/C are Complete" as simple fact per the founder's summary without independent re-verification — rejected; this session's own live checks were the entire point of the exercise, and they did surface one real gap (seed file 101 still broken) that a "Complete = Complete" reading would have papered over.
- **Considered:** skipping the fresh rollback re-check since it was already confirmed once — rejected; a rate-limit-induced skip this session is not the same as genuine re-confirmation, and WP-3D is specifically the "last moment before this becomes load-bearing" package per its own stated purpose.
- **Considered:** whether classifying seed file 101's issue as anything other than a stated, named "real blocker" would be more diplomatic — rejected; softening this would contradict the Permanent Evidence Rule this project operates under. It is confirmed, live, unfixed — stated plainly.

## Versioning & Placement

`[ACTIVE]_REPO-WP-03D_Seed_Readiness_Certification_v1.0.md` → `docs/project-history/`, committed **before** execution begins (established pattern from WP-3).

## Sign-off

Founder approval to execute WP-3D: _______________________ Date: ___________
Approval on Check 2 fix being folded into WP-3D scope (Section 5/10): _______________________
