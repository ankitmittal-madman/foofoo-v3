# [ACTIVE]_WP-8C_Auth_Framework_and_Consent_Endpoint_v1.0

**Status:** ACTIVE — auth framework + `/v1/consent` DESIGNED & EXECUTED (certified REPO-CERT-011). Onboarding portion of WP-8C is DEFERRED (see §7).
**Version:** v1.0
**Date:** 2026-07-14
**Placement:** docs/project-history/work-packages/[ACTIVE]_WP-8C_Auth_Framework_and_Consent_Endpoint_v1.0.md
**Supersedes:** none
**Dependencies:** DOC-P4-00 (WP-8A backend architecture) · WP-8B scaffold (REPO-CERT-008) · DOC-P3-06 v1.2 §04/§05/§06.1/§21 (API contract) · DOC-P3-03 §15 LF-M01 · DOC-P3-04 §03.4 (`consent_records`) · DOC-P3-07 (security) · DOC-09 §03 (DPDP). All consumed as FROZEN — none modified.

---

## Executive Summary

WP-8C's frozen scope (DOC-P4-00 §313) is **"Auth/authz framework + onboarding + consent."** This work package delivers the two dependency-free thirds of that scope, built on the WP-8B foundation with **no schema, migration, seed, canonical-data, validation-SQL, or security-model change**:

1. **Authentication framework** — real JWT signature verification (via Supabase Auth/GoTrue) as an injectable middleware, closing the verification gap WP-8B explicitly deferred to WP-8C; plus the single Surface-B authorization boundary (`requireOwnership`) mandated by DOC-P3-06 §05.
2. **`POST /v1/consent`** — the complete vertical slice (validation → handler → service → repository) implementing LF-M01 `captureConsent()` exactly per DOC-P3-06 §06.1, DOC-P3-03 §15, and the frozen `consent_records` schema.

**Onboarding is deferred** (§7): its frozen `/v1/onboarding` contract returns a *first week plan* (DOC-P3-03 §03; DOC-P3-06 §06.2), which requires the RE runtime core — scoped by DOC-P4-00 itself to **WP-8D/8E**, not WP-8C — and the boundary that would formally resolve the plan-timing question lives in **DOC-P4-02, which is not yet authored.** Building it now would require inventing business logic, which the governance forbids.

Verification: `deno fmt --check`, `deno lint`, `deno check`, and `deno test` all pass — **24 tests, 0 failures** (8 pre-existing foundation + 16 new). Executed locally on Deno 2.1.4; no production or database touched. Certified **REPO-CERT-011**.

---

## 1. Scope Delivered

| Capability | Frozen source | Status |
|---|---|---|
| JWT signature verification middleware (`authenticate`) | DOC-P3-06 §04; DOC-P4-00 §7 | ✅ Built + tested |
| Ownership authorization (`requireOwnership`) | DOC-P3-06 §05 / §05.1 | ✅ Built + tested |
| API error codes (`ERR_UNAUTHENTICATED`/`ERR_OWNERSHIP_MISMATCH`/`ERR_VALIDATION_FAILED`/`ERR_CONSENT_TYPE_INVALID`) | DOC-P3-06 §21.1 | ✅ Built (only the codes used now — no dead entries) |
| `POST /v1/consent` (LF-M01) | DOC-P3-06 §06.1; DOC-P3-03 §15 | ✅ Built + tested |
| Consent validation mirroring the DB CHECK | DOC-P3-04 §03.4 | ✅ Built + tested |
| `/v1/onboarding` (LF-A01–A09) | DOC-P3-06 §06.2 | ⛔ DEFERRED — see §7 |

## 2. Files (all under `supabase/`, backend code only)

**New:** `functions/_shared/errors/api-catalogue.ts`, `functions/_shared/auth/authenticate.ts`, `functions/_shared/validation/consent-schema.ts`, `functions/_shared/repositories/consent-repository.ts`, `functions/_shared/services/consent-service.ts`, `functions/consent/handler.ts`, `functions/consent/index.ts`, `functions/_tests/consent.test.ts`.
**Extended (additive only, no behavior change to WP-8B):** `functions/_shared/api/response.ts` (added `jsonContract`), `functions/_shared/di/container.ts` (consent getters), `functions/_shared/errors/index.ts` + `functions/_shared/mod.ts` (barrel exports).

## 3. Architecture Notes (this slice)

Follows DOC-P4-00 exactly — thin handler → service (LF orchestration) → repository (only SQL) → DB; DI via the per-request container; structured logger only; no PII in logs. Because Edge Functions run as `service_role` (RLS bypassed), authorization is explicit in code (DOC-P3-06 §05): the `authenticate` middleware verifies the JWT and the handler asserts `JWT user_id == body profile_id` before any write. The verifier is injectable, so every layer is unit-testable without a live GoTrue or database.

## 4. Design Decisions (classified, not silently assumed)

- **DCR-8C-01 — response envelope.** The frozen contract (§06.1) shows the success body as top-level fields; WP-8B's `jsonOk` wraps payloads under `data`. The frozen contract outranks the scaffold convenience, so a new `jsonContract` helper returns the contract shape plus an additive `trace_id` (required by §22.1, non-breaking per §17.2). `jsonOk` retained for internal responses.
- **DCR-8C-02 — 400 vs 422 split.** Per §07/§21, structural failures → `ERR_VALIDATION_FAILED` (400); a well-formed but out-of-CHECK `consent_type` → `ERR_CONSENT_TYPE_INVALID` (422). `consent_type` is validated as a string by Zod (structure) and its enum membership checked separately, so the two map to the correct distinct codes.
- **DCR-8C-03 — `ip_address_hash` deferred.** The column is nullable (DOC-P3-04 §03.4); population needs an IP-hash salt secret (DOC-P3-07 §14). Passed `null` now (schema-valid), flagged for a later WP — not a placeholder.
- **Foundation error codes vs §21 codes.** WP-8B's `AUTH_REQUIRED`/`FORBIDDEN`/`VALIDATION_FAILED` are infrastructure codes; the client-facing `ERR_*` codes are added here per §21 as WP-8B intended. `authenticate` normalizes a missing bearer into `ERR_UNAUTHENTICATED` so the client sees a single, contract-correct 401.

## 5. Verification (real, reproducible)

`cd supabase && deno task verify` → `deno fmt --check` PASS · `deno lint` PASS (37 files) · `deno check functions/_shared/mod.ts` PASS · `deno test --allow-env functions/_tests/` → **24 passed / 0 failed**. Coverage: consent validation (happy + missing field + empty array + non-boolean + invalid enum), ownership (match/mismatch), `authenticate` (claims attached / missing bearer / verifier reject), `ConsentService` personalization resolution (granted/denied/absent), and the assembled pipeline (201 happy path, 403 ownership, 422 invalid enum). Full evidence in REPO-CERT-011.

## 6. Governance Compliance

No `CREATE`/`ALTER`/`DROP`, no migration, seed, canonical data, validation SQL, or RLS/privilege change. `consent_records` DDL confirmed identical between DOC-P3-04 §03.4 and live migration `006`. Every function cites its `LF-*`/contract section (coding-standards-enforcer). Work performed on branch `feat/wp-8c-auth-onboarding-consent`; **not** pushed to `main` (DOC-P4-00 §230/§269).

## 7. Deferred: `/v1/onboarding` (evidence-backed blocker)

`/v1/onboarding` (LF-A01–A09) resolves persona/cohort/RE-state AND returns a **first week plan** (DOC-P3-03 §03 header; DOC-P3-06 §06.2 response `first_week_plan`). Generating that plan is the full RE pipeline (LF-B01→L01), which DOC-P4-00 §310–314 scopes to **WP-8D (RE core)** and **WP-8E (recommendations + nightly CRON)** — later than WP-8C. **DOC-P4-02** (Service/Edge-Function Specs), the document that would formally resolve whether onboarding generates the plan synchronously or the nightly CRON does, **does not exist.** Recommendation: author DOC-P4-02 to close the plan-timing boundary (raise as a DCR against DOC-P3-06 §06.2), then implement onboarding's persona/cohort/state resolution in a WP-8C continuation, with plan generation delegated to WP-8E. **Founder decision requested** before onboarding is built.

## Critical Self-Review

- **Did I change frozen artifacts?** No — schema, migrations, seeds, canonical data, validation SQL, and security model are untouched; only backend TypeScript was added/extended.
- **Did I invent business logic?** No — every rule cites a frozen source; the one place invention would have been required (onboarding's first-week-plan) was deferred and reported, not fabricated.
- **Are the tests real?** Yes — `deno task verify` output is reproduced in REPO-CERT-011; they exercise real code paths with injected fakes (no mocked business rules).
- **Is WP-8C complete?** No — this delivers two of its three parts. The WP Status reflects that honestly; onboarding remains open.

## Versioning & Placement

v1.0, placed in docs/project-history/work-packages/ per the Placement Rule; naming per WP-5AA standard. Companion certificate: REPO-CERT-011.

## Founder Sign-off

Founder acceptance of WP-8C (auth framework + consent) and of the onboarding deferral decision: _______________________ Date: ___________
