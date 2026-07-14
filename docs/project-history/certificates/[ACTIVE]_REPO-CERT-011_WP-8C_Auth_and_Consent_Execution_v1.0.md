# REPO-CERT-011 — WP-8C Auth Framework & Consent Endpoint Execution v1.0

**Status:** ACTIVE — Execution Certificate.
**Version:** v1.0
**Date:** 2026-07-14
**Placement:** docs/project-history/certificates/[ACTIVE]_REPO-CERT-011_WP-8C_Auth_and_Consent_Execution_v1.0.md
**Attests:** [ACTIVE]_WP-8C_Auth_Framework_and_Consent_Endpoint_v1.0.md
**Dependencies:** DOC-P4-00 (WP-8A) · REPO-CERT-008 (WP-8B scaffold) · DOC-P3-06 v1.2 · DOC-P3-03 §15 · DOC-P3-04 §03.4 · DOC-09 §03.

---

## Certification

The **FooFoo backend authentication framework** and the **`POST /v1/consent` endpoint** (LF-M01) are
certified **built and validated** on the WP-8B foundation, implementing the frozen contract
(DOC-P3-06 §04/§05/§06.1/§21) and business logic (DOC-P3-03 §15) exactly, with **no schema,
migration, seed, canonical-data, validation-SQL, RLS, or privilege change.**

## Basis (directly executed this session, Deno 2.1.4)

- **New code (8 files):** API error catalogue (§21 client codes), `authenticate` JWT-verification
  middleware + `requireOwnership` guard, consent validation (Zod + enum-membership split),
  `ConsentRepository` (append-only insert into `public.consent_records`), `ConsentService`
  (LF-M01), thin `/v1/consent` handler + entrypoint, and the consent test suite.
- **Additive scaffold extensions (4 files):** `jsonContract` response helper, DI container consent
  getters, and two barrel re-exports. No WP-8B behavior changed.
- **`deno task verify` (fmt:check → lint → check → test):**
  - `deno fmt --check` → **PASS**
  - `deno lint` → **PASS** (37 files)
  - `deno check functions/_shared/mod.ts` → **PASS**; `deno check functions/consent/index.ts` → **PASS**
  - `deno test --allow-env functions/_tests/` → **24 passed / 0 failed** (8 foundation + 16 consent)
- **Test coverage (the 16 new):** validation happy path; missing `profile_id` → 400
  `ERR_VALIDATION_FAILED`; empty `consents` → 400; non-boolean `granted` → 400; unknown
  `consent_type` → 422 `ERR_CONSENT_TYPE_INVALID`; ownership match / mismatch (403
  `ERR_OWNERSHIP_MISMATCH`); `authenticate` attaches claims / missing bearer → 401 / verifier
  reject → 401 `ERR_UNAUTHENTICATED`; `captureConsent` personalization granted / denied / absent;
  assembled pipeline 201 happy path (contract-shaped body + `trace_id`), 403 ownership, 422 enum.

## Scope & limits

Certifies the **auth framework + `/v1/consent` only.** Does NOT certify any other endpoint, the RE
runtime, or `/v1/onboarding` (none built — onboarding DEFERRED per WP-8C §7, blocked on the RE core
WP-8D/8E and the unauthored DOC-P4-02). JWT verification and ownership logic are exercised with an
injected fake verifier + fake repository; **no live GoTrue and no database connection** were made
this session, so privilege/RLS behavior against a live project is unchanged and unexercised here
(consistent with the WP-8B posture). Live behavioral validation against a Supabase instance is a
later WP.

## Governance verification

- **Schema/migration/seed/validation/canonical-data/security:** unchanged — zero SQL of any kind
  authored or run. `consent_records` DDL confirmed identical between DOC-P3-04 §03.4 and live
  migration `006_profile_dependent_public.sql`.
- **Frozen-contract fidelity:** request/response fields, the 4 `consent_type` CHECK values, the
  `ERR_*` codes + HTTP statuses, and the personalization-gate semantics all match DOC-P3-06 §06.1 /
  §21.1 and DOC-P3-03 §15 verbatim. Two DCR-class implementation decisions (response envelope;
  400-vs-422 split) and one deferral (`ip_address_hash`) are recorded in WP-8C §4, not silently
  applied.
- **Deploy discipline:** work on branch `feat/wp-8c-auth-onboarding-consent`; **not pushed to
  `main`** (DOC-P4-00 §230/§269; Founder-gated).

## Consequence

**WP-8C auth framework + consent COMPLETE and certified.** Backend engineering may proceed to
**WP-8D** (RE runtime core) per DOC-P4-00 §310–314, and to a WP-8C continuation for `/v1/onboarding`
once DOC-P4-02 resolves the first-week-plan boundary (WP-8C §7). Deploy discipline (Supabase CLI +
numbered migrations + CI safety gates; Founder-approved production only) remains in force.

## Critical Self-Review

- **Is execution real or claimed?** Real — `deno task verify` ran to completion this session
  (24/0). No result is asserted that was not observed.
- **Any frozen artifact touched?** No.
- **Any business logic invented?** No — the only place it would have been required (onboarding's
  first-week-plan) was deferred with evidence, not fabricated.
- **Honest limit:** tests use injected fakes for GoTrue and the DB; end-to-end behavior against a
  live Supabase project is not certified here and is scoped to a later WP.

## Versioning & Placement

v1.0, placed in docs/project-history/certificates/ per the Placement Rule; naming per WP-5AA standard.

## Founder Countersignature

Founder acceptance of WP-8C Auth Framework & Consent execution: _______________________ Date: ___________
