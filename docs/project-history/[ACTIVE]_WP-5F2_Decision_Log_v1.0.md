# WP-5F2 Decision Log v1.0

**Status:** ACTIVE — decision log
**Version:** v1.0
**Date:** 2026-07-13
**Placement:** docs/project-history/[ACTIVE]_WP-5F2_Decision_Log_v1.0.md
**Supersedes:** None
**Dependencies:** WP-5F2 Execution Report, Validation Report, Evidence Register.

---

| ID | Decision | Verdict | Reasoning |
|---|---|---|---|
| F2D-01 | Use a **local Docker PostgreSQL 15**, not the Supabase MCP, as the disposable DB | MADE | Supabase MCP is pinned to production `slsqtlygeekdppuyiiff`; brief forbids production; a Supabase branch is production-derived and non-empty. Local Docker is disposable, empty, isolated |
| F2D-02 | Add a documented Supabase-compatibility bootstrap (roles, auth schema, auth.users, auth.uid(), default grants) | MADE | Migrations 005/019 assume platform prerequisites vanilla PG lacks; without them the build cannot run. Scaffolding is separated from repo SQL and disclosed |
| F2D-03 | Run all steps with `ON_ERROR_STOP` for build/teardown, WITHOUT it for validation | MADE | Build/teardown must halt on first failure (brief STEP 3); validation must run every check to completion to classify each |
| F2D-04 | Execute the WP-04DC row-count diagnostic to resolve SEC-901T5 | MADE | The clean room finally allows the direct measurement WP-04DC designed but never ran; regression-check mandate (STEP 7) |
| F2D-05 | Classify 901 Test 5 as **test-design defect**, not security breach | MADE | Measured UPDATE = 0 rows → RLS default-deny held → data safe. GRANT gap is real but defense-in-depth (WP-5D) |
| F2D-06 | Demonstrate loud-fail on seeded data, then do the teardown on a **fresh unseeded rebuild** | MADE | Rollbacks are designed clean-on-unseeded / loud-fail-on-seeded; the seeded loud-fail proof perturbs 027/028 constraint state, so a pristine rebuild gives the definitive teardown-to-empty proof |
| F2D-07 | **Do NOT fix** the validation-script defects found (VAL2-01/02/03) | MADE | WP-5F2 is validation-only (execute + report); editing scripts is correction work owned by WP-04DA / a WP-5E follow-up. Brief: no repo reconstruction |
| F2D-08 | **Do NOT commit** the bootstrap SQL into `database/` | MADE | It is not a repository migration; the brief forbids authoring migrations. Preserved verbatim in the Evidence Register |
| F2D-09 | Destroy the disposable containers after evidence capture | MADE | Disposable-by-design; nothing persistent, nothing external |
| F2D-10 | Answer "Can WP-5D begin?" = **YES** (do not begin it) | MADE | See recommendation; execution established the verified baseline WP-5D needs and a concrete execution-grounded justification (the GRANT gap → pf1_security_hardening) |

## Critical Self-Review

- **Considered** F2D-01 as a blocker (STOP because no non-production Supabase DB). **Rejected** — Docker provides a genuinely disposable database in-sandbox; stopping would have withheld achievable, high-value execution evidence when a safe path existed.
- **Considered** classifying VAL2-01 (vacuous Check 2) as out-of-scope noise. **Rejected** — a validation check that silently verifies nothing is a false-assurance risk worth first-class recording, even though WP-5F2 does not fix it.

## Founder Sign-off

Founder acceptance of the WP-5F2 Decision Log: _______________________ Date: ___________
