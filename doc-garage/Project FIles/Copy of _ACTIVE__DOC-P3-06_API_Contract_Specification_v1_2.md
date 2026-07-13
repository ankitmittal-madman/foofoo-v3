# [ACTIVE]_DOC-P3-06_API_Contract_Specification_v1.2

**Status:** **APPROVED — ACTIVE — FROZEN** (Founder approval received; frozen under change control per Founder instruction, session #028)
**Version:** v1.2
**Date:** 2026-07-01
**Supersedes:** `[ACTIVE]_DOC-P3-06_API_Contract_Specification_v1.1` (same session — final polish before sign-off)
**Reason for revision:** Founder architecturally approved v1.1 pending final polish. This revision (a) closes DCR-P3-06-007, (b) adds a Contract Stability statement, (c) adds governance rules for application error codes, (d) adds an authentication/authorization failure matrix, and (e) explicitly labels certain existing content as non-binding Phase 4 implementation guidance rather than architectural requirement. **No API contract change is made** — no endpoint, request/response field, schema reference, business-logic reference, or traceability row is added, removed, or altered.
**Approved By:** Founder — approved and frozen, session #028
**Freeze rule (added at approval, permanent):** No further improvements, enhancements, optimizations, or refinements shall be made to this document unless a future AGR, DCR, or explicit Founder instruction reopens it. This document is now an immutable upstream dependency for all downstream architecture and implementation work (DOC-P4-01, DOC-P4-02, DOC-P3-07, and beyond), in exactly the same standing as DOC-P3-04/DOC-P3-05 under Baseline Register Step 10.
**Current Phase:** APDF Phase 3 (Solution Architecture) — this document completes the mandatory DOC-P3-06 artifact
**Prerequisites (read before this document, per APDF sequencing):** DOC-P3-02 v1.1, DOC-P3-03 v1.0, DOC-P3-03A v1.0, DOC-P3-04 v1.3, DOC-P3-05 Parts (a)–(d), RE-DOC-01 v1.0, DOC-04 PRD v1.1
**Source Documents Referenced:** `[ACTIVE]_Project_Baseline_Register_v1_2`, `[ACTIVE]_Engineering_Handover_Project_Continuity_Package_v1_0`, `[ACTIVE]_DOC-P3-03_Business_Logic_Specification_v1`, `[ACTIVE]_DOC-P3-03A_Logic_Governance_Matrix_v1`, `[ACTIVE]_DOC-P3-04_Data_Architecture_ERD_v1_3`, `[ACTIVE]_RE-DOC-01_Architecture`, `[ACTIVE]_DOC-04_PRD_v1_1`, `[ACTIVE]_APDF_Framework_v1`
**Downstream Documents Dependent On This Document:** DOC-P4-01 (Frontend Implementation Spec), DOC-P4-02 (Service/Edge Function Specifications), DOC-P3-07 (Security Architecture — now in progress, this document is a direct frozen input to it), DOC-P5-02 (QA Specification)

**Governance basis (immutable for this session):** The Project Baseline Register, Engineering Handover, DOC-P3-03, DOC-P3-03A, DOC-P3-04 v1.3, and DOC-P3-05 Parts (a)–(d) are treated as frozen, authoritative fact for this document. **This document does not redesign architecture, does not modify the database schema, and introduces no undocumented assumption.** Every endpoint, field, and rule below is either a direct citation of an existing frozen artifact or an explicitly classified DCR (Documentation Clarification Report) — never a silent addition. This is an architecture document only; no implementation code is produced here.

---

## Revision Notice — v1.1 → v1.2 (read before the rest of this document)

**What changed (five targeted additions, all Founder-directed, all polish-level):**

1. **DCR-P3-06-007 closed** (Section 25 and Section 23) — scheduled recommendation generation (LF-L01) and `/v1/recommendations` are now documented as sharing a common internal recommendation service; scheduled jobs do not invoke the public HTTP endpoint. This was already the *recommended reading* in v1.1 (unconfirmed); v1.2 records Founder confirmation and marks it Resolved.
2. **Contract Stability statement added** — new Section 16.4.
3. **Error code governance rules added** — new Section 21.0 (immutability, uniqueness, deprecation of `ERR_*` codes), inserted before the existing catalogue table, which is otherwise untouched.
4. **Authentication and Authorization Failure Matrix added** — new Section 05.1, covering missing/expired/invalid JWT, ownership failure, and deleted-account access.
5. **Non-binding implementation guidance explicitly labelled** — Section 18.3 (throughput estimates) and 18.4 (retry/backoff) now carry an explicit "non-binding Phase 4 implementation guidance, not an architectural requirement" label. A short framing note is added at the top of Section 18 for the same reason. No numbers, targets, or recommendations within those subsections were changed — only their status label.

**What did not change:** Every endpoint (Section 06), every DCR's original description (Section 25), every traceability row (Sections 12–13), every sequence diagram (Section 14), and all v1.0/v1.1 governance statements remain word-for-word as approved. No new endpoint, table, schema element, or business-logic function is introduced. No section was renumbered in this revision — all new content was added as sub-sections (16.4, 21.0, 05.1) within existing sections, so **every existing section number from v1.1 is unchanged in v1.2.**

**Regression review (performed as part of this revision, per the same discipline as the v1.0→v1.1 review):**

| Check | Result |
|---|---|
| Every endpoint from v1.1 Section 03/06 still present, unmodified | ✅ Confirmed — 10 endpoints, identical contracts |
| Every DCR from v1.1 (001–007) still present with its original description intact | ✅ Confirmed — only DCR-007's *status* field changed (Draft/Recommended → Resolved), per explicit Founder instruction to close it |
| Every traceability row (Sections 12, 13) still present, unmodified | ✅ Confirmed |
| Every sequence diagram (Section 14) still present, unmodified | ✅ Confirmed |
| Any v1.1 content deleted | ❌ None — zero deletions |
| Any v1.1 rule weakened | ❌ None |
| Any new endpoint, table, schema change, or business-logic function introduced | ❌ None |
| Any section renumbered | ❌ None — all five additions are sub-sections within existing section numbers |
| Any new ambiguity found while making these five additions | ⚠️ Yes, one — **DCR-P3-06-008**, surfaced while building the Section 05.1 failure matrix, classified and logged in Section 25, not silently resolved |

---

### Prior Revision Notice — v1.0 → v1.1 (preserved verbatim for history)

**What changed:** Eight new sections were added — Sections 16–23 (API Design Principles and Contract Governance, API Versioning Strategy, Non-Functional API Requirements, System State Transition Model, API Event Contract, API Error Catalogue, API Observability and Operational Contract, API Consumer Matrix). **Nothing else changed in substance.**

**What did not change:** Every v1.0 endpoint definition (Section 06), every DCR (001–006), every traceability matrix (Sections 12–13), every sequence diagram (Section 14), and every governance statement remains word-for-word as approved. Sections 00–15 of this document are content-identical to v1.0's Sections 00–15.

**Numbering change (mechanical only, not a content change):** To avoid inserting new material in the middle of the heavily cross-referenced Sections 00–15, the 8 new sections were appended as Sections 16–23, and the two v1.0 closing sections were shifted down to make room:
- v1.0 Section 16 "Validation Checklist" → **v1.1 Section 24** (content preserved, extended with new rows confirming the 8 new sections and this regression review)
- v1.0 Section 17 "Issue Classification Log" → **v1.1 Section 25** (content preserved verbatim, extended with the one new DCR raised while drafting Sections 16–23)

No other section number changed. No cross-reference inside Sections 00–15 pointed to Section 16 or 17 in v1.0 (verified by direct text search before this revision — the only internal citations found were to Sections 12–15, which are unchanged), so this renumbering carries zero risk of a cross-reference now pointing to the wrong content.

**Regression review (performed as part of this revision, per Founder instruction):**

| Check | Result |
|---|---|
| Every endpoint from v1.0 Section 03/06 still present, unmodified | ✅ Confirmed — 10 endpoints, identical contracts |
| Every DCR from v1.0 (001–006) still present, unmodified, same classification | ✅ Confirmed — now in Section 25 |
| Every traceability row (Sections 12, 13) still present, unmodified | ✅ Confirmed |
| Every sequence diagram (Section 14) still present, unmodified | ✅ Confirmed |
| Every governance statement (Sections 01, 04, 05, 07–11) still present, unmodified | ✅ Confirmed |
| Any v1.0 content deleted | ❌ None — zero deletions |
| Any v1.0 rule weakened (e.g., a `[CONFIRMED]` tag downgraded, a constraint loosened) | ❌ None — all tags and rules carried forward exactly as written |
| Any new endpoint, table, or business-logic function introduced | ❌ None — the 8 new sections consume and cross-reference the existing 10 endpoints and existing DOC-P3-03/04 content only |
| Any new ambiguity found while drafting Sections 16–23 | ⚠️ Yes, one — **DCR-P3-06-007**, classified and logged in Section 25, not silently resolved |

---

## Section 00 — How to Read This Document

This is the first-ever DOC-P3-06. It did not previously exist in any form (confirmed absent from project storage per the Phase 3 Completion Audit, session #024). It is written entirely from the frozen artifacts listed above — RE-DOC-01 §03 already defines a partial API contract for the RE module; this document formalizes it completely, extends it only where DOC-P3-03's business logic functions demonstrably require an endpoint that RE-DOC-01 did not yet enumerate, and classifies every such extension explicitly rather than silently inventing it.

**Status tags used throughout (same convention as DOC-P3-03):**
- `[DOCUMENTED]` — directly stated in a frozen source document
- `[CONFIRMED]` — decided during this session, requires Founder sign-off before Phase 4 begins
- `[DCR]` — Documentation Clarification Report raised in this document — architecture is correct, nothing changes, ambiguity is resolved
- `[SCOPE NOTE]` — explicitly deferred or out of scope, cited to its source

---

## Section 01 — API Surface Philosophy (Two Surfaces, Not One)

FooFoo's API surface has two genuinely different parts, and conflating them was the risk this document exists to prevent.

### 1.1 — Surface A: Direct table access via Supabase PostgREST + RLS
For `public` schema tables where DOC-P3-04 already defines a client-facing RLS policy (`profiles`, `household_members`, `onboarding_sessions` [SELECT only], `consent_records` [SELECT only], `week_plans`, `plan_slots`, `addon_slots`, `interaction_events`, `weather_cache` [public SELECT]), the mobile app talks **directly** to Supabase's auto-generated REST API using the Supabase client SDK. **This document does not re-specify these as custom endpoints** — DOC-P3-04 §03.1–03.18 already is the authoritative contract for this surface; re-describing it here would create exactly the kind of dual-source-of-truth risk the Baseline Register's Version Conflict Policy exists to prevent. Section 02 below provides a compact index into DOC-P3-04 for this surface, nothing more.

### 1.2 — Surface B: Custom Edge Function endpoints (the RE module boundary)
Everything that touches `re_engine` schema objects — which are locked to `service_role` only (DOC-P3-04 §03.26: `REVOKE ALL ON SCHEMA re_engine FROM PUBLIC, anon, authenticated`) — **cannot** be reached by the client SDK at all, by design (RE-DOC-01 §01–§02: "RE module owns... never writes to app user tables"; the isolation is the point). The only way into or out of the RE is the versioned HTTP contract RE-DOC-01 §03 already began defining. **This is the surface this document exists to complete.** Sections 03–16 below are entirely about Surface B.

**Governance consequence (stated once, applies throughout):** because Edge Functions execute under `service_role`, **RLS provides zero protection at this layer.** Every authorization check that RLS would normally provide for a client-authenticated request must instead be explicitly coded inside the Edge Function. This is not a schema change — DOC-P3-04's RLS design is correct and unchanged — but it is a rule this API Contract must state explicitly, since no prior document does so in one place. See Section 05.

---

## Section 02 — Surface A Index (reference only, not a new contract)

| Table | RLS policy (DOC-P3-04 §) | Client operations permitted | Custom endpoint needed? |
|---|---|---|---|
| `profiles` | §03.1 | SELECT/UPDATE own row | No — direct SDK |
| `household_members` | §03.2 | ALL own rows | No — direct SDK |
| `onboarding_sessions` | §03.3 | SELECT own only (INSERT service-role only) | Partially — INSERT happens inside POST /v1/onboarding (Section 06.2) |
| `consent_records` | §03.4 | SELECT own only (append-only, no client INSERT) | Yes — POST /v1/consent (Section 06.1) writes here |
| `week_plans` | §03.12 | SELECT/UPDATE own | No — direct SDK (UPDATE limited to `is_locked` at the plan level, if the app exposes that; primary read path is GET /v1/plan, Section 06.4) |
| `plan_slots` | §03.13 | SELECT/UPDATE own | No for `is_locked` toggling — direct SDK. **DCR-P3-06-003** below clarifies this boundary. |
| `addon_slots` | §03.14 | SELECT own | No — direct SDK |
| `interaction_events` | §03.15 | INSERT/SELECT own | **See DCR-P3-06-002 — do not use this path for writes; see Section 06.3** |
| `weather_cache` | §03.18 | SELECT (public) | No — direct SDK, if a future weather widget needs it (F-41 is Phase 1, not MVP) |
| `dishes`, `ingredients`, `dish_tags`, `tags` | §03.5–03.9 | Read-only content browsing (RLS not shown as client-restrictive in DOC-P3-04 for these — treated as public reference content) | No — direct SDK. **Grocery-list-style aggregation over these tables is explicitly out of MVP scope per DOC-04 v1.1 changelog (F-27/F-28 moved out of MVP) — not contracted here.** `[SCOPE NOTE: DOC-04 v1.1 §changelog]` |

**F-59 (My Meals tab — cooking history) note:** DOC-04 v1.1 adds F-59 to MVP, replacing the removed Grocery tab. This is read-only history over `interaction_events` (`dish_cooked` events) joined to `dishes`, entirely servable via Surface A (direct SELECT, RLS already permits `ie_select_own`). No custom endpoint required. `[DOCUMENTED: DOC-04 v1.1 changelog]`

---

## Section 03 — Endpoint Inventory (Surface B — complete)

| # | Endpoint | Method | Status | Business logic (DOC-P3-03) | Execution class (DOC-P3-03A §07) | Auth |
|---|---|---|---|---|---|---|
| 1 | `/v1/consent` | POST | **[DCR-P3-06-001] new, formalizing LF-M01** | LF-M01 | Synchronous, blocking, <200ms | JWT required |
| 2 | `/v1/onboarding` | POST | Existing (RE-DOC-01 §03) | LF-A01–A09 | Synchronous, sequential, <200ms/step | JWT required |
| 3 | `/v1/recommendations` | POST | Existing (RE-DOC-01 §03) | LF-B01–B02, C01–C02, D01–D07, E01–E08, F01–F03, H01–H04, I01–I05 | Synchronous, <800ms total pipeline budget | JWT required |
| 4 | `/v2/recommendations` | POST | **Reserved** — not implemented at MVP (RE-DOC-01 §04) | Same functions, future LTR/ML variants | Synchronous | JWT required |
| 5 | `/v1/events` | POST | Existing (RE-DOC-01 §03), **contract completed in this document** | LF-J01 (+ synchronous LF-G01/G02 sub-path) | Synchronous (log) <100ms; Never/Not-Today sub-path synchronous <200ms; J02–J06 async batch (15 min) | JWT required |
| 6 | `/v1/plan/{user_id}/{week}` | GET | Existing (RE-DOC-01 §03) | Read of LF-L01 output | Synchronous, cached read | JWT required, ownership-checked |
| 7 | `/v1/plan/refresh` | POST | **[DCR-P3-06-004] new, formalizing LF-L02 as a single client-facing call** | LF-L02 | Synchronous (on-demand), <3s | JWT required |
| 8 | `/v1/user/export` | GET | Existing (DOC-P3-03 §15, LF-M02) | LF-M02 | Asynchronous, queued, <72h | JWT required |
| 9 | `/v1/user/delete` | POST | **[DCR-P3-06-005] new, formalizing LF-M03 as a callable endpoint** | LF-M03 | Asynchronous, queued, <72h | JWT required |
| 10 | `/v1/health` | GET | Existing (RE-DOC-01 §03) | N/A — infrastructure check | Synchronous, <50ms | **None — public** |

**Not part of this contract (internal, service-role-invoked, no HTTP exposure to the app):** LF-L01 `generateWeekPlan` (23:30 UTC CRON), LF-J02–J06 batch processor (15-min CRON), LF-J08 `cohortWeightRecalibration` (Sunday 18:00 UTC CRON, currently no-op per DOC-P3-03 §17 U-002), LF-J09 `dailyDishFeatureSnapshot` (00:00 UTC CRON), LF-G05 `checkNeverReactivation` (weekly CRON), LF-K01/K02 (database triggers per DOC-P3-04 §03.6A, not HTTP at all), LF-K04 (manual content-ops gate, not automated). These are cited here **only for completeness of traceability** (Section 12) — they are Phase 4 CRON/trigger implementation concerns, not API contract concerns, and are explicitly out of this document's scope.

---

## Section 04 — Authentication Model

**Mechanism:** Supabase Auth issues a JWT on sign-in/sign-up. All Surface B endpoints except `/v1/health` require `Authorization: Bearer <jwt>`. `[DOCUMENTED: RE-DOC-01 §03 implies authenticated `user_id`; Supabase Auth is the platform's standard mechanism per DOC-10 §01 stack selection]`

**Edge Function verification:** Supabase Edge Functions natively support `verify_jwt` at the function-gateway level (rejects unauthenticated requests with `401` before the function body executes) — this must be enabled for every endpoint in Section 03 except `/v1/health`. `[CONFIRMED — Founder sign-off required, since no existing document states this explicitly; this is the closure of the exact gap the Phase 3 Audit flagged for a Security Architecture document]`

**Internal/CRON invocations:** The five scheduled jobs listed in Section 03 (not part of this contract) execute under `service_role` via Supabase's scheduled Edge Function / `pg_cron` mechanism and are never reachable over the public internet with a user JWT. `[CONFIRMED — standard Supabase deployment pattern, consistent with DOC-P3-04 §03.26's service-role-only lockdown of `re_engine`]`

**`/v1/health` exception:** Unauthenticated by design — RE-DOC-01 §05: "App uses this to decide whether to show cached plan," which must work even if a user's session has expired.

---

## Section 05 — Authorization Model

Because every Surface B endpoint runs under `service_role` (Section 01.2), **RLS enforces nothing here.** The following rule is `[CONFIRMED]` and must be implemented identically by whichever engineer or Claude Code session builds DOC-P4-02:

> **Every Edge Function must extract `user_id` from the verified JWT (`auth.uid()` equivalent, available in the Edge Function's request context) and compare it against the `user_id`/`profile_id` in the request body or path parameter. If they do not match, return `403 Forbidden` before touching any table.** This is the sole authorization boundary for Surface B — there is no database-level backstop, by design (Section 01.2).

| Endpoint | Ownership check required | What is compared |
|---|---|---|
| `/v1/consent` | Yes | JWT `user_id` == request body `profile_id` |
| `/v1/onboarding` | Yes | JWT `user_id` == request body `user_id` |
| `/v1/recommendations` | Yes | JWT `user_id` == request body `user_id` |
| `/v1/events` | Yes | JWT `user_id` == request body `profile_id` |
| `/v1/plan/{user_id}/{week}` | Yes | JWT `user_id` == path `user_id` |
| `/v1/plan/refresh` | Yes | JWT `user_id` == request body `user_id` |
| `/v1/user/export` | Yes | JWT `user_id` == request body `user_id` (or JWT-derived, no body param needed) |
| `/v1/user/delete` | Yes | JWT `user_id` == request body `user_id`, **plus a confirmation step (Section 08)** |
| `/v1/health` | No | N/A — no user data touched |

**No role-based authorization exists beyond this** — FooFoo MVP has exactly one role ("household account owner"); there is no admin/staff API surface in this contract. `[DOCUMENTED: no admin endpoints appear anywhere in RE-DOC-01, DOC-P3-03, or DOC-04 — absence confirmed by source review, not assumed]`

### 05.1 — Authentication and Authorization Failure Matrix `(new in v1.2)`

Consolidates, in one place, every failure mode that can occur before an Edge Function's own business logic runs at all. Each row maps to an existing rule already stated in Section 04 or Section 05 above — this matrix adds no new rule, it only enumerates the failure states that those rules imply and gives each a single reference point.

| Failure state | Detected where | HTTP status | `error.code` (Section 21) | Applies to |
|---|---|---|---|---|
| **Missing JWT** — no `Authorization` header, or header present but empty | Edge Function gateway `verify_jwt` (Section 04) | `401` | `ERR_UNAUTHENTICATED` | All Surface B endpoints except `/v1/health` |
| **Expired JWT** — token present, signature valid, `exp` claim in the past | Edge Function gateway `verify_jwt` (Section 04) | `401` | `ERR_UNAUTHENTICATED` | All Surface B endpoints except `/v1/health` |
| **Invalid JWT** — malformed token, or signature does not verify against Supabase Auth's key | Edge Function gateway `verify_jwt` (Section 04) | `401` | `ERR_UNAUTHENTICATED` | All Surface B endpoints except `/v1/health` |
| **Ownership failure** — JWT is valid, but its `user_id` does not match the request's `user_id`/`profile_id` | Inside the Edge Function body, first check performed (Section 05's `[CONFIRMED]` rule) | `403` | `ERR_OWNERSHIP_MISMATCH` | All Surface B endpoints except `/v1/health` |
| **Deleted account** — JWT is valid and belongs to the requesting user, but `profiles.deleted_at` is already set (§03.1) | Inside the Edge Function body, after the ownership check passes | `403` | `ERR_OWNERSHIP_MISMATCH` — **no separate code is introduced for this state** `[DCR — observation]`: a soft-deleted account attempting any Surface B call other than checking its own deletion/export status is, functionally, no longer an authorized account; reusing `ERR_OWNERSHIP_MISMATCH` rather than minting a new code (e.g., a hypothetical `ERR_ACCOUNT_DELETED`) is a deliberate choice consistent with Section 21.0's uniqueness rule not being violated — the two situations ("not yours" and "no longer exists as an active account") are different causes producing the same client-observable outcome (access denied), and Section 21.0 governs *codes*, not *causes*. **Flagged for Founder confirmation** — if a distinct client-facing signal for "your account was deleted" is wanted (e.g., to show a specific message rather than a generic access-denied one), a new `ERR_ACCOUNT_DELETED` code should be added as a DCR-classified, additive (non-breaking, per Section 17.2) change in a future revision, not silently introduced here. |

**Ordering note:** the three JWT-level failures (missing/expired/invalid) are indistinguishable from the client's point of view by design — all three return `401` with the same generic `ERR_UNAUTHENTICATED` code. This is intentional and not a gap: distinguishing them in the response body would leak information about *why* a token failed (e.g., confirming a token's signature format was almost-correct), which is a minor but real information-disclosure surface with no corresponding client-side benefit, since the client's only correct action in all three cases is identical — re-authenticate.

---

## Section 06 — Request / Response Contracts

Every field below traces to an actual DOC-P3-04 column or a DOC-P3-03 logical-function output. No field is invented; where a field is genuinely new (because it is a request/response envelope concept, not a stored value — e.g., `idempotency_key`), it is marked `[DCR]` and justified.

### 06.1 — POST /v1/consent
**Business logic:** LF-M01 `captureConsent()` · **Schema:** `public.consent_records` (DOC-P3-04 §03.4) · **PRD:** DOC-09 §03 (DPDP) · **CDM:** no numbered entity (consent is a compliance record, not a domain entity per DOC-P3-02) · **Rule enforced:** personalization consent must be granted before any onboarding data collection (DOC-09 §03; DOC-P3-03 LF-M01).

```json
// Request
{
  "profile_id": "uuid",
  "consents": [
    { "consent_type": "personalization", "granted": true },
    { "consent_type": "analytics", "granted": true },
    { "consent_type": "push_notifications", "granted": false },
    { "consent_type": "data_retention", "granted": true }
  ],
  "privacy_policy_version": "string"
}
```
```json
// Response 201
{
  "recorded": [
    { "consent_type": "personalization", "granted": true, "granted_at": "ISO8601" },
    { "consent_type": "analytics", "granted": true, "granted_at": "ISO8601" },
    { "consent_type": "push_notifications", "granted": false, "granted_at": "ISO8601" },
    { "consent_type": "data_retention", "granted": true, "granted_at": "ISO8601" }
  ],
  "personalization_granted": true
}
```
**Field-level table:**
| Field | Type | Required | Source | Notes |
|---|---|---|---|---|
| `profile_id` | uuid | Yes | `profiles.id` | Must equal JWT `user_id` (Section 05) |
| `consents[].consent_type` | enum | Yes | `consent_records.consent_type` CHECK constraint (§03.4) | Exactly the 4 values in the CHECK — no others accepted |
| `consents[].granted` | boolean | Yes | `consent_records.granted` | |
| `privacy_policy_version` | text | Yes | `consent_records.privacy_policy_version` | |
| `recorded[].granted_at` | timestamptz | — (response only) | `consent_records.granted_at` DEFAULT now() | |

**Error behaviour:** If `personalization_granted` resolves to `false`, the response includes `"personalization_granted": false` and `/v1/onboarding` **must** reject any subsequent call for this `profile_id` with `403` (DOC-09 §03 rule, Section 07).

---

### 06.2 — POST /v1/onboarding
**Business logic:** LF-A01–LF-A09 · **Schema writes:** `profiles`, `household_members`, `onboarding_sessions`, `re_engine.user_re_state`, `re_engine.user_taste_vectors` · **PRD:** F-01 through F-09 · **CDM:** User (1), Household Members (3), Main Cohort (9), Sub-cohort (10), Persona (11), Overlay (12), Confidence Score (13).

```json
// Request
{
  "user_id": "uuid",
  "answers": {
    "OB-01_main_cohort": "MC_NUCLEAR_FAMILY",
    "OB-02_household_branch": {
      "members": [
        { "segment": "SCHOOL_CHILD", "member_name": "string (optional)" }
      ]
    },
    "OB-03_regional_identity": {
      "home_state": "MH",
      "current_city": "Mumbai",
      "migration_duration_band": "3_7yr"
    },
    "OB-04_diet_configuration": {
      "diet_type": "veg",
      "religious_pref": "hindu_veg"
    },
    "OB-05_allergen_exclusions": { "allergen_flags": 6 },
    "OB-06_cook_capability": "intermediate",
    "OB-07_class_preference_swipes": [
      { "dish_id": "uuid", "class_code": "BF_LIGHT_GRAIN", "swipe": "yes" }
    ],
    "OB-08_profile_setup": {
      "primary_cook_name": "string",
      "push_notification_time": "07:00:00"
    }
  },
  "skipped_screens": ["OB-05"]
}
```
```json
// Response 201
{
  "profile_id": "uuid",
  "persona_id": "uuid",
  "overlay_persona_ids": ["uuid"],
  "confidence_score": 0.58,
  "cold_start_mode": true,
  "onboarding_completed": true,
  "first_week_plan": { "week_plan_id": "uuid", "week_start_date": "YYYY-MM-DD" }
}
```
**Field-level table (selected — full field set mirrors DOC-P3-03 §03 exactly):**
| Field | Type | Required | Source | Notes |
|---|---|---|---|---|
| `answers.OB-01_main_cohort` | enum | Yes* | `re_engine.re_main_cohorts.cohort_code` | *If absent: LF-A01 fallback = `MC_SOLO`, confidence −0.05 |
| `answers.OB-03_regional_identity.home_state` | text (FK) | No | `profiles.home_state` → `re_engine.re_states` | Skip penalty −0.08 (LF-A03) |
| `answers.OB-04_diet_configuration.diet_type` | enum | Yes* | `profiles.diet_type` CHECK | *Skip penalty −0.15 (LF-A04); Jain auto-sets `religious_pref='jain'` per CDM Entity 5 |
| `answers.OB-05_allergen_exclusions.allergen_flags` | integer bitfield | No | `profiles.allergen_flags` | Bit definitions per DOC-P3-03 §03 LF-A05 table — not restated here to avoid duplicate source of truth |
| `skipped_screens` | array of screen_id | No | Drives `onboarding_sessions.skipped=true` rows | Used by LF-A08 confidence computation |
| `persona_id` (response) | uuid | — | `re_engine.user_re_state.persona_id`, resolved via LF-A09 | Never exposed as anything but an opaque ID — "user never sees it" (LF-A09 purpose statement) |
| `confidence_score` (response) | real, 0.35–1.0 | — | `re_engine.user_re_state.confidence_score` CHECK | Range per LF-A08: 0.40–0.65 at Day 0 |

**Idempotency rule (Section 08):** This endpoint **must** be idempotent per household — LF-B01's own comment states persona is "assigned exactly once." A retried call with the same `user_id` after `onboarding_completed=true` must return `409 Conflict`, not re-run assignment. `[CONFIRMED — direct consequence of DOC-P3-03 §02 Stage 2 note, not a new rule]`

---

### 06.3 — POST /v1/events
**Business logic:** LF-J01 (+ synchronous LF-G01/G02 sub-path) · **Schema:** `public.interaction_events` (§03.15), synchronously also `re_engine.never_list` / `re_engine.not_today_suppression` for the two gesture types · **PRD:** implicit across F-01–F-10 (all swipe/lock/rate gestures) · **CDM:** Interaction Events (29), Never List (30), Not Today Suppression (31), Class Affinity (46).

```json
// Request
{
  "profile_id": "uuid",
  "event_type": "dish_never",
  "dish_id": "uuid",
  "meal_slot": "breakfast",
  "slot_date": "YYYY-MM-DD",
  "rank_at_interaction": 1,
  "time_viewed_ms": 3400,
  "rating": null,
  "context": { "weather": "rainy" },
  "re_version": "classfirst_v1",
  "confidence_at_time": 0.58
}
```
```json
// Response 202 (for event_type NOT in [dish_never, dish_not_today])
{ "event_id": "uuid", "logged_at": "ISO8601", "synced_to_re": false }

// Response 200 (for event_type IN [dish_never, dish_not_today] — synchronous side-effect completed)
{
  "event_id": "uuid",
  "logged_at": "ISO8601",
  "suppression_applied": {
    "type": "never",
    "dish_id": "uuid",
    "is_active": true,
    "class_affinity_adjusted": false
  }
}
```
**Field-level table:**
| Field | Type | Required | Source | Notes |
|---|---|---|---|---|
| `event_type` | enum | Yes | `interaction_events.event_type` CHECK (11 values, §03.15) | Exhaustive list — no others accepted |
| `dish_id` | uuid | Conditionally required | `interaction_events.dish_id` FK | Required for all dish-level events; null-able for `plan_opened`/`session_depth` |
| `rating` | smallint 1–5 | Only for `dish_rated` | `interaction_events.rating` CHECK | |
| `synced_to_re` (response) | boolean | — | `interaction_events.synced_to_re` DEFAULT false | Flips true only after the 15-min batch (LF-J02–J06); **this field is NOT flipped by this endpoint's own request/response cycle** |

**`[DCR-P3-06-002]` — write-path resolution (raised, not silently assumed):**
**Finding:** DOC-P3-04 §03.15 grants a client-facing RLS `INSERT` policy (`ie_insert_own`) on `interaction_events`. Taken alone, this would let the mobile app write directly via the Supabase SDK, bypassing this Edge Function entirely.
**Why this cannot be the actual write path for `dish_never`/`dish_not_today`:** `re_engine.never_list` and `re_engine.not_today_suppression` are locked to `service_role` (§03.26). A direct client `INSERT` into `interaction_events` has no mechanism to also write these rows — the Never/Not-Today suppression LF-G01/LF-G02 side-effects (RE-DOC-04 §03) would simply never happen, silently breaking the very hard-constraint filter (LF-D06) and penalty calc (LF-G03) these gestures exist to drive.
**Classification:** DCR, not AGR — the schema/RLS design itself is correct and untouched (Section 6.4 discipline: architecture correct, documentation needs clarification without changing meaning). The RLS `INSERT` policy on `interaction_events` is retained as-is for analytics-only event types (`plan_opened`, `session_depth`) where no `re_engine` side-effect exists and either path is safe — **but for the 9 dish-level event types, POST /v1/events is the only correct write path, and this must be documented as a client-implementation rule, not left to inference.**
**Resolution required before Phase 4:** Founder confirms this reading, or raises a counter-reading if RLS `INSERT` was intended as the general path with a separate sync mechanism to `re_engine` (no such mechanism is documented anywhere, so this alternative currently has zero supporting evidence).

---

### 06.4 — POST /v1/recommendations
**Business logic:** LF-B01, LF-B02, LF-C01–C02, LF-D01–D07, LF-E01–E08, LF-F01–F03, LF-H01–H04, LF-I01–I05 (the full 9-stage pipeline, DOC-P3-03 §02) · **Schema:** reads across `re_engine.*` seed/config tables, writes `plan_slots.slate_dish_ids`/`slate_reasons`/`slate_confidence`, `public.suggestion_logs`, `public.context_log` · **PRD:** F-39 (RE v1), F-40 (RE v2 personal history) · **CDM:** Meal Class (20), Plan Slot (24), Class-Dish Option (21).

**Contract is unchanged from RE-DOC-01 §03** (this is the one endpoint that document already fully specified) — reproduced here verbatim for completeness of a single-source contract document, with field provenance added:

```json
// Request
{
  "user_id": "uuid",
  "meal_slot": "breakfast",
  "date": "YYYY-MM-DD",
  "context": { "weather": "rainy", "temp_c": 18, "city": "Mumbai", "day_of_week": "tuesday" },
  "n_results": 8,
  "exclude_dish_ids": []
}
```
```json
// Response 200
{
  "slate_id": "uuid",
  "confidence": 0.84,
  "cold_start_mode": false,
  "re_version": "classfirst_v1",
  "class_code": "BF_LIGHT_GRAIN",
  "dishes": [
    { "dish_id": "uuid", "rank": 1, "score": 0.91, "reason_tags": ["regional", "weather"] }
  ]
}
```
| Field | Source | Notes |
|---|---|---|
| `context.*` | LF-I01 `assembleContext()` inputs | Client-supplied; server also independently fetches weather via LF-I02 cache — client-supplied weather is advisory/fallback only `[DCR-P3-06-006, minor]`: RE-DOC-01's contract doesn't state which wins if client and server weather disagree. Recommend: server-fetched `re_engine`-cached value is authoritative, client value used only if `LF-I02` cache miss and external API also fails. **Flagged for Founder confirmation, non-blocking.** |
| `n_results` | Maps to `re_scoring_config`-bounded slate size | RE-DOC-01 default 8; DOC-P3-04 §03.16 `rank_in_slate` CHECK enforces 1–8 at the storage layer regardless of what is requested |
| `exclude_dish_ids` | Used by LF-D01 candidate exclusion, and directly by LF-L03 `promoteSlateDish()` | This is the mechanism by which Never/Not-Today gestures produce a fresh slate (Section 06.3) |
| `dishes[].reason_tags` | Stored verbatim to `suggestion_logs.slate_reasons` jsonb | Per DOC-P3-03A §08 auditability requirement |

**Failure/fallback behaviour:** unchanged from RE-DOC-01 §05 (reproduced in full in Section 07 below — not re-invented here).

---

### 06.5 — GET /v1/plan/{user_id}/{week}
**Business logic:** read of LF-L01's stored output · **Schema:** `week_plans` (§03.12), `plan_slots` (§03.13), `addon_slots` (§03.14) · **PRD:** F-10 (Day View reads a slice of this).

```
GET /v1/plan/{user_id}/{week}
```
```json
// Response 200
{
  "week_plan_id": "uuid",
  "week_start_date": "YYYY-MM-DD",
  "is_locked": false,
  "re_version": "classfirst_v1",
  "slots": [
    {
      "slot_id": "uuid",
      "slot_date": "YYYY-MM-DD",
      "meal_slot": "breakfast",
      "class_code": "BF_LIGHT_GRAIN",
      "selected_dish_id": "uuid",
      "is_locked": false,
      "slate_dish_ids": ["uuid"],
      "slate_confidence": 0.84,
      "cold_start_mode": true,
      "addons": [
        { "addon_slot_id": "uuid", "household_member_id": "uuid", "addon_class_code": "ADDON_TODDLER", "dish_id": "uuid" }
      ]
    }
  ]
}
```
**Path parameter `{week}` format:** `YYYY-MM-DD` (Monday of the target week) — matches `week_plans.week_start_date` exactly, no derived-date logic on the server side. `[DCR — RE-DOC-01 §03 named the parameter `{week}` without specifying format; resolved here to the only format that matches the underlying column, no ambiguity remains]`

**Not found behaviour:** If no `week_plans` row exists for the requested week (e.g., requested before LF-L01's nightly CRON has run for a new user), return `404` with `{"reason": "plan_not_yet_generated"}` — the app's documented fallback (RE-DOC-01 §05) is to show the last successfully cached plan, which is a client-side concern, not this endpoint's.

---

### 06.6 — POST /v1/plan/refresh
**`[DCR-P3-06-004]`** — this endpoint does not exist in RE-DOC-01's contract. It is added here to give LF-L02 `refreshUnlockedSlots()` a single, well-defined client call instead of requiring the app to loop `N` individual `POST /v1/recommendations` calls (one per unlocked slot) client-side.
**Why this is a DCR, not an AGR or new architecture:** LF-L02 already fully specifies the *logic* ("for each unlocked slot: re-run LF-D01 through F02"); RE-DOC-01 §03 already specifies the *pipeline* those re-runs invoke. This endpoint is pure composition/orchestration of already-approved logic — it changes no table, no algorithm, no scoring formula. It only answers a question neither document explicitly closed: is pull-to-refresh one API call or many? Given the 800ms-per-slot budget (DOC-P3-03 §02) and a typical week having up to 21 unlocked slots, sequential client-side calls would risk the `<3s` NFR (DOC-P3-03 §14 LF-L01); a single server-side batched call, parallelising internally, is the only design that can plausibly meet it.

```json
// Request
{
  "user_id": "uuid",
  "week_plan_id": "uuid"
}
```
```json
// Response 200
{
  "week_plan_id": "uuid",
  "refreshed_slots": [
    { "slot_id": "uuid", "slate_dish_ids": ["uuid"], "slate_confidence": 0.81 }
  ],
  "skipped_locked_slots": ["uuid"]
}
```
**Server-side behaviour:** For each `plan_slot` in `week_plan_id` WHERE `is_locked = false` (matches the exact predicate on DOC-P3-04's `idx_plan_slots_locked` index, §03.13 — that index exists *specifically* to serve this query pattern, confirming this endpoint's shape is consistent with the frozen schema's own design intent, not a new access pattern being retrofitted onto it): re-run the candidate generation → scoring → MMR sequence (LF-D01–F02) with `class_code` held fixed. Locked slots pass through untouched in `skipped_locked_slots`.

**Recommendation for Founder confirmation:** this is the one genuinely new endpoint in this document. It should be reviewed alongside DCR-P3-06-005 below before Phase 4 service specs are written, since both affect the endpoint count DOC-P4-02 will need to specify.

---

### 06.7 — GET /v1/user/export
**Business logic:** LF-M02 `executeDataExport()` · **Schema scope (verbatim from DOC-P3-03 §15):** `profiles, household_members, interaction_events, week_plans, plan_slots, never_list, onboarding_sessions, consent_records` · **PRD:** DOC-09 §03.

```
GET /v1/user/export
Authorization: Bearer <jwt>
```
```json
// Response 202 (job queued)
{ "export_job_id": "uuid", "status": "queued", "estimated_completion": "ISO8601 (<=72h)" }
```
```json
// Response 200 (job complete, polled via GET /v1/user/export/{export_job_id} — see idempotency note)
{ "export_job_id": "uuid", "status": "complete", "download_url": "signed URL, expires in 24h", "format": "json" }
```
**Note on the second response shape:** RE-DOC-01/DOC-P3-03 specify this as "Format: JSON. Queued job completes within 72 hours" but do not specify a polling contract. **`[DCR]`** — a job-status sub-resource (`GET /v1/user/export/{export_job_id}`) is the minimum necessary completion of this contract; without it, "queued job" has no way to ever report completion to the client. This is the same class of gap as DCR-P3-06-004 (logic fully specified, delivery mechanism not yet closed) and is flagged the same way rather than silently invented.

---

### 06.8 — POST /v1/user/delete
**`[DCR-P3-06-005]`** — LF-M03 `executeDataDeletion()` is fully specified in DOC-P3-03 §15 as logic ("soft-delete immediately... hard-delete within 72h via CRON") but, unlike LF-M02, no endpoint path was ever named for triggering it (DOC-P3-03 §15 LF-M03 has no `**Endpoint:**` line, unlike LF-M02's explicit one). This is added here as the necessary client-facing trigger; the CRON-based hard-delete itself remains, correctly, an internal scheduled job (Section 03).

```json
// Request
{
  "user_id": "uuid",
  "confirmation_phrase": "DELETE MY ACCOUNT"
}
```
```json
// Response 202
{ "deletion_job_id": "uuid", "soft_deleted_at": "ISO8601", "hard_delete_estimated_by": "ISO8601 (<=72h)" }
```
| Field | Source | Notes |
|---|---|---|
| `confirmation_phrase` | Not a stored column — request-only safety gate | `[DCR]` — a permanent, irreversible action needs an explicit confirmation step; this is standard API-safety practice, not a business-logic rule, and does not touch the schema |
| `soft_deleted_at` (response) | `profiles.deleted_at` (§03.1) | Set immediately per LF-M03 |
| Exception scope | `audit_log` retained 3 years per DPDP (DOC-P3-03 §15) | Explicitly **not** deleted — this response does not claim full erasure at `soft_deleted_at` time, only at hard-delete completion, matching LF-M03's own wording exactly |

---

### 06.9 — GET /v1/health
```
GET /v1/health
```
```json
// Response 200
{ "status": "healthy", "re_version_active": "classfirst_v1", "checked_at": "ISO8601" }
// Response 503
{ "status": "degraded", "reason": "string" }
```
**Behavioural contract (verbatim from RE-DOC-01 §05):** the app polls this to decide whether to show a cached plan instead of calling `/v1/recommendations`. No authentication, no user data, no side effects.

---

## Section 07 — Error Model

**Envelope (applies to every Surface B endpoint):**
```json
{ "error": { "code": "string", "message": "string", "trace_id": "uuid" } }
```
`trace_id` is included specifically so that any error can be joined back to `suggestion_logs`/`context_log`/`interaction_events` for the auditability reconstruction queries DOC-P3-03A §08 already defines — this is a `[DCR]`-level addition (an envelope field, not a schema change) made *because* Section 08 of DOC-P3-03A already requires reconstructability and no prior document specified how an error-time request maps back to it.

| HTTP status | Used when | Source |
|---|---|---|
| `400` | Request fails validation (Stage 1 `validateRequest()`) | DOC-P3-03 §02 Stage 1 — "Return 400. App falls back to cached plan." |
| `401` | Missing/invalid JWT | Section 04 |
| `403` | JWT `user_id` ≠ resource owner (Section 05); or personalization consent not granted (Section 06.1) | DCR/CONFIRMED rules above |
| `404` | Resource does not exist (e.g., plan not yet generated, Section 06.5) | — |
| `409` | Duplicate onboarding attempt on an already-completed profile (Section 06.2, Section 08) | DOC-P3-03 §02 Stage 2 note |
| `422` | Semantically invalid but well-formed request (e.g., `event_type` not in the 11-value CHECK list) | Matches `interaction_events.event_type` CHECK, §03.15 |
| `500` + cached-plan signal | Safety gate failure after 2 retries (Stage 8) | DOC-P3-03 §02 Stage 8 — reproduced verbatim, not reinterpreted |
| `503` | RE down / degraded (`/v1/health` reports it) | RE-DOC-01 §05 |

**Fallback behaviour table — reproduced verbatim from RE-DOC-01 §05 (this document adds no new fallback rule; restating it here only for single-document completeness):**

| Failure scenario | App behaviour | RE response |
|---|---|---|
| RE response time > 2s | Show cached plan from last successful call | Log slow response |
| RE returns 5xx | Show cached plan; log to Sentry | Auto-restart; alert on 3+ consecutive 5xx |
| RE confidence < 0.3 | Show plan with "Still learning" message | Flag for onboarding enrichment prompt |
| RE returns empty slate | Show static fallback (8 popular dishes, diet-filtered) | Log critical; investigate constraint conflict |
| RE completely down | Cached-plan-only mode | Auto-restart; page on-call if >5min |
| Constraint violation detected | Block slate; request fresh from RE | Log P0; block deployment until fixed |

---

## Section 08 — Idempotency

| Endpoint | Idempotent? | Mechanism |
|---|---|---|
| `POST /v1/consent` | Yes, naturally | `consent_records` is append-only (§03.4) — repeated identical calls simply add more history rows, which is the intended DPDP audit behaviour, not a bug to guard against |
| `POST /v1/onboarding` | **Must be enforced, not natural** | `409 Conflict` if `profiles.onboarding_completed = true` already (Section 06.2). No `Idempotency-Key` header needed — the natural key is `profile_id` + the completion flag itself |
| `POST /v1/recommendations` | Yes, naturally | Each call is a pure function of its inputs; retries simply produce a new `slate_id` — DOC-P3-03A §08 already logs every slate, so duplicate slates are an auditability non-issue, not a correctness one |
| `POST /v1/events` | **Requires client-side dedup awareness** `[DCR]` | No `Idempotency-Key` field exists in `interaction_events` (§03.15) today. A network retry of a `dish_cooked` event, for example, would double-count in LF-J02's `interaction_count++`. **Recommendation for Founder confirmation:** either (a) the mobile client is responsible for not retrying a successfully-sent event (simplest, no schema impact), or (b) a future `SER` (Schema Evolution Request, per Baseline Register Step 10) adds a client-generated dedup key column. **Option (a) is recommended for MVP — no schema change required, consistent with the freeze.** |
| `POST /v1/plan/refresh` | Yes, naturally | Same reasoning as `/v1/recommendations` — re-running produces a fresh (idempotent-in-effect) slate per unlocked slot |
| `GET /v1/user/export` | Yes, naturally | Repeated calls should return the same `export_job_id` while queued/in-progress rather than spawning duplicate jobs — `[DCR]`: server-side dedup on "one active export job per user" is a sensible, non-schema-changing implementation rule |
| `POST /v1/user/delete` | Yes, naturally, with the confirmation gate as the real safety mechanism | Repeated calls on an already-soft-deleted profile should return the existing `deletion_job_id`, not create a second one |

---

## Section 09 — Pagination

**No endpoint in this contract requires pagination at MVP.** Justification, not assumption:
- `/v1/plan/{user_id}/{week}` returns a bounded set (21 primary slots + a small number of add-on slots per DOC-P3-04 §03.13/§03.14 — no unbounded list).
- `/v1/recommendations` returns at most 8 dishes (`n_results` bounded, and `rank_in_slate` CHECK BETWEEN 1 AND 8 at storage, §03.16).
- No endpoint in this contract exposes a raw `interaction_events` or `suggestion_logs` history list — those are Surface A concerns (direct SELECT via RLS, F-59's My Meals tab) and are explicitly out of Surface B scope (Section 02).

**`[SCOPE NOTE]`** If a future phase adds a paginated history endpoint to Surface B (rather than Surface A), it must use keyset pagination on `(occurred_at, id)` to match the existing partitioned-table index shape (`idx_ie_profile_dish`, §03.15) — noted here only so a future session does not default to offset pagination against a partitioned append-only table, which would be a real performance risk given the partitioning rationale in DOC-P3-04 §07.

---

## Section 10 — Rate Limiting

| Endpoint | Recommended limit | Why | Source |
|---|---|---|---|
| `/v1/recommendations` | Per-user: reasonable interactive ceiling (e.g., 1 call per slot per few seconds) to prevent a broken client from hammering the 800ms-budget pipeline | Protects the shared free-tier Edge Function compute budget | `[CONFIRMED — no numeric ceiling exists in any frozen document; recommend Founder set an explicit number before Phase 4, this document only establishes that a limit must exist]` |
| `/v1/events` | Per-user: high ceiling, since legitimate rapid swiping is expected UX | Must not throttle real interaction — event logging is cheap (<100ms, log-only) | DOC-P3-03A §07 |
| `/v1/plan/refresh` | Per-user: low ceiling (e.g., a few per hour) | Pull-to-refresh is a deliberate user action, not a polling loop; each call fans out to potentially 21 slot re-runs | This document (DCR-P3-06-004) |
| `/v1/user/export`, `/v1/user/delete` | Per-user: effectively one active job at a time (Section 08) | DPDP jobs are rare, high-cost, queued | DOC-09 §03 |
| `/v1/onboarding` | Per-user: one successful call ever (409 thereafter) | Section 06.2/08 | DOC-P3-03 §02 |
| `/v1/health` | Unlimited / excluded from rate limiting | Must remain available precisely when the system is under stress | RE-DOC-01 §05 |

**Free-tier infrastructure constraint (carried forward, not new):** the Weather API called internally by LF-I02 has a 1,000-call/day free-tier limit, mitigated by `weather_cache` (12h TTL) — this is not a client-facing rate limit but is the reason `/v1/recommendations`' internal fan-out to LF-I02 must always check cache first. `[DOCUMENTED: Engineering Handover §7.4]`

---

## Section 11 — API Lifecycle

| Stage | Meaning | Governance |
|---|---|---|
| **Draft** | This document's current state for the 3 DCR-flagged new endpoints (`/v1/consent` formalized, `/v1/plan/refresh`, `/v1/user/delete`) | Requires Founder sign-off before DOC-P4-02 treats them as final |
| **Active** | `/v1/onboarding`, `/v1/recommendations`, `/v1/events`, `/v1/plan/{user_id}/{week}`, `/v1/health` — already active-by-design per RE-DOC-01 | No further approval needed to proceed to Phase 4 implementation of these |
| **Shadow** | Applies only to internal RE version transitions (`classfirst_v2`, `ltr_v1`, etc.), never to the endpoint contract itself — the `/v1` path is stable across all internal RE version changes per RE-DOC-01 §04's explicit design ("app is unaware") | RE-DOC-01 §04 — 72h shadow run, rollback <5min if any offline metric regresses |
| **Deprecated → Sunset** | Reserved for `/v1` if/when `/v2` becomes the primary breaking-change surface (RE-DOC-01 §04: LTR/ML phase) | Not yet triggered — `/v2/recommendations` is reserved, not implemented |
| **Any endpoint change post-approval** | Must go through the same AGR/SER discipline as schema changes (Baseline Register Step 10), extended here explicitly to the API surface for the first time | `[CONFIRMED — this document is the first to state that API contract changes require the same governance discipline as schema changes; recommend Founder ratify this extension explicitly]` |

---

## Section 12 — Traceability to Business Logic (DOC-P3-03)

| Endpoint | LF functions | DOC-P3-03 section | DOC-P3-03A execution class |
|---|---|---|---|
| `/v1/consent` | LF-M01 | §15 | Synchronous, blocking |
| `/v1/onboarding` | LF-A01–LF-A09 | §03 | Synchronous, sequential |
| `/v1/recommendations` | LF-B01–B02, C01–C02, D01–D07, E01–E08, F01–F03, H01–H04, I01–I05 | §04–§08, §10–§11 | Synchronous, <800ms |
| `/v1/events` | LF-J01, LF-G01, LF-G02 (sync sub-path); LF-J02–J06 (async, triggered downstream) | §09, §12 | Mixed — see Section 06.3 |
| `/v1/plan/{user_id}/{week}` | Read of LF-L01 output | §14 | Synchronous cached read |
| `/v1/plan/refresh` | LF-L02 | §14 | Synchronous, on-demand |
| `/v1/user/export` | LF-M02 | §15 | Asynchronous, queued |
| `/v1/user/delete` | LF-M03 | §15 | Asynchronous, queued |
| `/v1/health` | N/A | RE-DOC-01 §05 | Synchronous |

**Coverage confirmation:** all 9 LF groups with a client-facing surface (A, B, C, D, E, F, G [sync sub-path], L, M) are represented. Groups H (safety gates), I (context assembly), J (async learning), K (dish content) are correctly **not** independently exposed as endpoints — they are internal to the pipeline invoked by `/v1/recommendations` or run as CRON/triggers (Section 03), exactly matching DOC-P3-03A §07's execution classification. No LF function with a documented client trigger is missing an endpoint; no endpoint exists without a citable LF function.

---

## Section 13 — Traceability to Schema (DOC-P3-04)

| Endpoint | Tables read | Tables written | DOC-P3-04 § |
|---|---|---|---|
| `/v1/consent` | — | `consent_records` | §03.4 |
| `/v1/onboarding` | `re_engine.re_main_cohorts`, `re_engine.re_persona_assignment_rules` | `profiles`, `household_members`, `onboarding_sessions`, `re_engine.user_re_state`, `re_engine.user_taste_vectors` | §03.1–03.3, §03.27, §03.29 |
| `/v1/recommendations` | `re_engine.re_class_dish_options`, `re_engine.re_cohorts`, `re_engine.re_weekly_class_plans`, `re_engine.never_list`, `re_engine.not_today_suppression`, `re_engine.variety_window_state`, `dishes`, `dish_ingredients`, `weather_cache` | `plan_slots` (slate fields), `suggestion_logs`, `context_log` | §03.6–03.9, §03.13, §03.16–03.18, §03.27–03.29 |
| `/v1/events` | `interaction_events` (for dedup checks, if implemented) | `interaction_events`; conditionally `re_engine.never_list`, `re_engine.not_today_suppression` | §03.15, §03.29 |
| `/v1/plan/{user_id}/{week}` | `week_plans`, `plan_slots`, `addon_slots` | — | §03.12–03.14 |
| `/v1/plan/refresh` | `plan_slots` (WHERE `is_locked=false`), same reads as `/v1/recommendations` | `plan_slots` (slate fields, unlocked rows only) | §03.13 (`idx_plan_slots_locked` — see Section 06.6) |
| `/v1/user/export` | All 8 tables named in LF-M02 (Section 06.7) | Export job metadata (**not itself a `[CONFIRMED]` new table — see Section 15 gap below**) | Multiple |
| `/v1/user/delete` | `profiles` | `profiles.deleted_at` immediately; all 8 LF-M02-scope tables at hard-delete (CRON) | §03.1 |
| `/v1/health` | `re_engine.re_engine_versions` (`is_active`) | — | §03.28 |

**RLS interaction note:** every write listed above that touches a `re_engine` table happens under `service_role`, bypassing RLS entirely by architecture (Section 01.2/05). Every write to a `public` table listed above **also** happens under `service_role` within these Edge Functions — meaning the `public`-schema RLS policies (e.g., `profiles_update_own`) are **not** what protects these writes either; the Edge Function's own ownership check (Section 05) is what protects them. This is worth stating plainly because it is easy to mistakenly believe RLS is "still doing its job" for `public` tables just because the policies exist and are enabled — they are not consulted at all when the connection is `service_role`.

---

## Section 14 — Sequence Diagrams

### 14.1 — Onboarding
```
App                          Edge Function (/v1/consent)         Edge Function (/v1/onboarding)
 |--- POST consents -------->|                                    |
 |<-- 201 recorded ----------|                                    |
 |                                                                 |
 |--- POST onboarding answers ---------------------------------->|
 |                                          [LF-A01..A08 sequential, <200ms/step]
 |                                          [LF-A09 assignPersona — DB lookup, exactly-once]
 |<-- 201 {persona_id, confidence, first_week_plan} --------------|
```

### 14.2 — Recommendation + Never/Not-Today feedback loop
```
App                    /v1/recommendations         /v1/events              /v1/recommendations (retry)
 |--- POST slot ------->|                            |                        |
 |<-- 200 8 dishes ------|                            |                        |
 |  [user swipes Never on dish #1]                                            |
 |--- POST dish_never ------------------------------->|                        |
 |                          [LF-G01 sync: write never_list, log event <200ms] |
 |<-- 200 suppression_applied -------------------------|                        |
 |  [UI immediately promotes next-ranked dish from existing slate — LF-L03]   |
 |--- POST slot, exclude_dish_ids=[dish#1] ------------------------------------>|
 |<-- 200 fresh 8 dishes -------------------------------------------------------|
```

### 14.3 — Pull-to-refresh
```
App                              /v1/plan/refresh
 |--- POST {week_plan_id} -------->|
 |                    [server: for each unlocked slot, LF-D01..F02 in parallel]
 |                    [locked slots untouched]
 |<-- 200 {refreshed_slots[], skipped_locked_slots[]} --|
```

### 14.4 — DPDP export/delete (async)
```
App                    /v1/user/export                    /v1/user/export/{job_id}
 |--- GET export -------->|                                  |
 |<-- 202 {job_id, queued} -|                                  |
 |  [poll later, up to 72h]                                    |
 |--- GET status ------------------------------------------------->|
 |<-- 200 {status: complete, download_url} --------------------------|
```

---

## Section 15 — Dependency Matrix

| Endpoint | Depends on (must have succeeded first) | Reason |
|---|---|---|
| `/v1/onboarding` | `/v1/consent` (personalization granted) | Section 06.1 / DOC-09 §03 |
| `/v1/recommendations` | `/v1/onboarding` (persona assigned) | LF-B01 fallback (Option B) applies otherwise — degraded, not blocked, per DOC-P3-03 §02 Stage 2 |
| `/v1/events` (dish-level types) | An existing `plan_slots`/`suggestion_logs` row for the referenced `dish_id`/`slot_date` | Implicit in LF-G01–G03's queries (Section 06.3), though not enforced by a hard FK in `interaction_events` (`dish_id` FK exists to `dishes`, not to a specific slot — `[DCR]`: this means an event can reference a dish never actually shown to this user in this slot; DOC-P3-04 does not constrain this, and this document does not propose adding such a constraint, only notes the absence for Founder awareness) |
| `/v1/plan/refresh` | An existing `week_plans` row (i.e., `/v1/recommendations`/LF-L01 has run at least once) | Section 06.6 |
| `/v1/user/export`, `/v1/user/delete` | Valid JWT only — no functional dependency on any other endpoint | DOC-09 §03 — these are independent rights, not feature-gated |

---

## Section 16 — API Design Principles and Contract Governance

*(New in v1.1. This section states principles that were already being followed implicitly throughout Sections 00–15 of v1.0 — it makes them explicit rather than introducing new behaviour.)*

### 16.1 — Design principles

| Principle | What it means here | Where it was already being applied (v1.0) |
|---|---|---|
| **Contract-first, schema-second** | Every field in every request/response traces to an existing column or LF output — the contract never gets ahead of what the frozen schema/logic can actually support | Section 06's field-level tables throughout |
| **Two surfaces, never conflated** | Direct RLS access (Surface A) and the RE Edge Function contract (Surface B) are never redundantly re-specified against each other | Section 01 |
| **Additive evolution preferred; breaking changes get a new path version** | A new optional field is not a breaking change; removing a field, changing a type, or making an optional field required is | Formalized fully in Section 17 below |
| **Explicit over inferred** | Every genuinely new element is tagged `[DCR]` or `[CONFIRMED]` rather than presented as settled fact | Sections 06.3, 06.6, 06.8, 07 |
| **Authorization lives in code, not in RLS, at this layer** | Because Edge Functions run under `service_role`, every ownership check is explicit application logic | Section 05 |
| **Fail documented, never fail silent** | Every failure mode maps to a named HTTP status and a stated app-side fallback | Section 07 |
| **One canonical source of truth per fact** | A table's shape is defined once (DOC-P3-04), a rule is defined once (DOC-P3-03) — this document cites, it does not restate-and-risk-diverging | Stated explicitly in Section 01.1 |

### 16.2 — Contract governance rules

These are a direct, explicit restatement — not a new rule — of the principle Section 11 (API Lifecycle) already established for post-approval changes, gathered here so contract governance has one obvious home:

> **Any change to this contract — a new endpoint, a new required field, a changed error code, a changed latency target — must go through the same AGR/SER/DCR discipline that governs the frozen schema (Baseline Register Step 10).** A new *optional* field or a new *internal-only* endpoint (no client impact) may be proposed as a documentation-only revision (as this v1.1 itself was); anything with client impact requires the full discipline and a version bump per Section 17.

### 16.3 — Ownership and review process

| Role | Responsibility |
|---|---|
| Founder | Sign-off authority for this document and any future revision (unchanged from v1.0 header) |
| Whoever drafts DOC-P4-02 | Must treat this document as frozen input in exactly the way this document treats DOC-P3-04 as frozen input — the same discipline, one layer up |
| Any future session proposing a contract change | Must classify it (AGR/SER/DCR) per 16.2 before drafting, exactly as this document's own DCRs (Section 25) were classified before being resolved |

### 16.4 — Contract Stability statement `(new in v1.2)`

> **Internal implementation changes must never alter externally observable API behavior without going through API versioning (Section 17).**
>
> This is the general principle that DCR-P3-06-007's resolution (Section 23, Section 25) is one specific instance of: the fact that scheduled recommendation generation shares a common internal recommendation service with `/v1/recommendations` is an *implementation* fact, entirely invisible to the mobile app, and it must stay that way. If a future engineer refactors that shared service, changes its internal call pattern, or even genuinely does route the CRON job through the public endpoint instead of a shared module — none of that is a contract change **as long as** every request/response shape, field, status code, and error code defined in Sections 03–13 and 21 remains exactly as specified. The moment an internal change would cause any of those to differ, it stops being "internal" and becomes a contract change, and must be handled per Section 17.2 (backward compatibility) and Section 16.2 (contract governance) — not shipped silently.
>
> This statement exists so that "internal" and "silently breaking" are never confused with each other by a future session under time pressure.

---

## Section 17 — API Versioning Strategy

*(New in v1.1. This section distinguishes three separate versioning axes that were present but never named as distinct in v1.0 or in RE-DOC-01 — a genuine clarification, not new architecture.)*

### 17.1 — Three distinct version numbers in this system (stated explicitly for the first time)

| Axis | Example values | What it governs | Who changes it |
|---|---|---|---|
| **This document's own version** | v1.0, v1.1 | The API *contract specification* itself — this document | Whoever drafts a revision, Founder sign-off |
| **API path version** | `/v1`, `/v2` | The wire-level request/response shape the app must speak | Breaking changes only (17.2) |
| **Internal RE algorithm version** | `classfirst_v1`, `classfirst_v2`, `ltr_v1` (RE-DOC-01 §04) | Which scoring/ranking algorithm runs behind an unchanged `/v1` contract | RE team, via shadow-mode promotion (RE-DOC-01 §04) — **the app is never aware this changed**, by design |

**This is the single most important clarification in this section:** RE-DOC-01 §04's entire versioning roadmap (`classfirst_v1` → `classfirst_v2` → `ltr_v1` → `ml_v1`) happens **without** a path version bump, because the contract (request/response shape) is unchanged across all of them — only `/v2` (reserved, Section 03) represents an actual breaking *contract* change (RE-DOC-01 §04: "Breaking change — new API version"). v1.0 already implied this by keeping `/v1` fixed across the roadmap table; this section states it as an explicit rule so a future session does not confuse an internal RE version bump with a contract version bump.

### 17.2 — Backward compatibility rules `[CONFIRMED — new policy, requires Founder sign-off]`

| Change type | Breaking? | Action required |
|---|---|---|
| Add a new optional response field | No | Document it, no version bump |
| Add a new optional request field | No | Document it, no version bump |
| Add a new endpoint | No | DCR/SER per Section 16.2, no version bump to existing endpoints |
| Remove a field | Yes | New path version (`/v2`) |
| Change a field's type or semantics | Yes | New path version |
| Make an optional field required | Yes | New path version |
| Change an error code's HTTP status | Yes | New path version (clients may branch on status) |
| Change an internal RE algorithm (scoring, ranking) | **No, by architectural design** | Shadow-mode promotion only (RE-DOC-01 §04) — this is the entire point of the RE isolation boundary (Section 01.2) |

### 17.3 — Deprecation policy `[CONFIRMED — new policy, no prior document specified a concrete window; recommended for Founder sign-off]`

No frozen document states a deprecation timeline for `/v1` once `/v2` becomes primary. Recommended, pending confirmation: **`/v1` remains fully supported for a minimum of 6 months after `/v2` reaches general availability**, with deprecation communicated via the app's own release notes (not a novel mechanism — the app is already versioned and released through app-store channels). This is a policy recommendation only; it changes nothing about the current `/v1`-only MVP state and does not require any action before Phase 4.

### 17.4 — Lifecycle (cross-reference, not a duplicate)

Full lifecycle stages (Draft → Active → Shadow → Deprecated → Sunset) are already defined in Section 11 and are not repeated here. Section 17.1–17.3 add the missing backward-compatibility and deprecation *rules* that Section 11 named the *stages* for but did not itself specify.

---

## Section 18 — Non-Functional API Requirements

*(New in v1.1. Consolidates NFRs that were scattered across DOC-P3-03, DOC-P3-03A, and RE-DOC-01 — cited, not re-derived — and adds the small number of genuinely new targets explicitly marked `[CONFIRMED]`.)*

**Status of guidance in this section `(clarified in v1.2)`:** Sections 18.1, 18.2, and 18.5 reproduce targets and rules that already exist in frozen source documents (DOC-P3-03, DOC-P3-03A, RE-DOC-01) — these are **binding architectural requirements**, exactly as their sources are. Section 18.3 (Throughput expectations) in full, and one specific row within Section 18.4 (Timeout and retry philosophy — the recommended backoff row only), contain genuinely new numbers and recommendations authored in this document, with no frozen source specifying them — these are **non-binding Phase 4 implementation guidance**: useful starting points for whoever writes DOC-P4-02, not architectural requirements this document is imposing. Nothing in 18.3/18.4's actual content changed in this relabelling — only their status is now stated explicitly, per-row where a subsection mixes both statuses, rather than left to be inferred from the `[CONFIRMED]` tag alone.

### 18.1 — Availability

No frozen document states a formal uptime SLA — reasonable, since MVP infrastructure is entirely free-tier (Handover §7.4) and a contractual SLA would be inconsistent with that reality. `[CONFIRMED — informal internal target only, not a guarantee]`: recommend a working target of reasonable best-effort availability for the RE Edge Functions during MVP, understanding that Supabase/Vercel free-tier has no uptime guarantee of its own to build a stricter internal target on top of. This is an honest target-setting exercise, not an invented guarantee.

### 18.2 — Latency targets (reproduced from source, not newly invented)

| Endpoint | Target | Source |
|---|---|---|
| `/v1/onboarding` (per step) | <200ms/step | DOC-P3-03A §07 |
| `/v1/recommendations` | <800ms Edge Function execution; <3s total end-to-end (network + render, Pixel 3a reference device) | DOC-P3-03 §02, DOC-04 NFR |
| `/v1/events` (log-only path) | <100ms | DOC-P3-03A §07 |
| `/v1/events` (Never/Not-Today sync sub-path) | <200ms | DOC-P3-03A §07 |
| `/v1/plan/{user_id}/{week}` | Cached read, no documented target beyond "fast" | `[SCOPE NOTE]` — no explicit number exists in any source; not invented here |
| `/v1/plan/refresh` | <3s | DOC-P3-03 §14 LF-L01's end-to-end NFR, applied by this document to the batched-refresh case (Section 06.6) |
| `/v1/user/export`, `/v1/user/delete` | <72h (DPDP legal requirement, not a performance target) | DOC-09 §03 |
| `/v1/health` | <50ms | DOC-P3-03A §07 |

**Note on precision:** source documents specify single target numbers, not percentile (p50/p95/p99) breakdowns. This section reproduces exactly what exists — it does not invent percentile SLOs the frozen documents never specified.

### 18.3 — Throughput expectations — **non-binding Phase 4 implementation guidance, not an architectural requirement** `[CONFIRMED — illustrative estimate for capacity planning]`

Using the product's own 90-day target of 500 DAU (project brief) and an illustrative assumption of roughly 3 meal-slot recommendation requests per user per day: order-of-magnitude peak load is on the order of 1,500 `/v1/recommendations` calls/day, concentrated around the 05:00 IST plan-generation window (LF-L01 CRON) and normal daytime usage. This is a planning estimate, not a contractual throughput guarantee, and does not require any architectural change — it is offered so DOC-P4-02 has a concrete number to size Edge Function concurrency against.

### 18.4 — Timeout and retry philosophy

*(Status varies by row — labelled individually below, since this subsection mixes a reproduced binding rule with genuinely new guidance.)*

| Rule | Source | Status |
|---|---|---|
| Client-side timeout for `/v1/recommendations`: 2s, after which the app shows the cached plan | RE-DOC-01 §05 (reproduced in Section 07, not new) | **Binding** — reproduced architectural rule |
| Which endpoints are safe to retry automatically | Section 08 (Idempotency) — already established; this section adds no new idempotency rule, only states the retry *policy* that follows from it | **Binding** — direct consequence of an existing rule |
| Recommended client backoff on `5xx`/`429` | `[CONFIRMED — new guidance, no schema/contract impact]`: exponential backoff starting at 1s, consistent with the "auto-restart, alert on 3+ consecutive 5xx" operational behaviour already documented in RE-DOC-01 §05 — a client retrying faster than the server can restart would defeat that documented behaviour | **Non-binding Phase 4 implementation guidance** — a recommended starting point, not a requirement this document imposes |
| Endpoints that must **never** be blindly retried without idempotency awareness | `/v1/events` (Section 08) — restated here as a retry-philosophy consequence, not a new rule | **Binding** — direct consequence of an existing rule |

### 18.5 — Resilience expectations

The complete fallback/failure table already exists in Section 07 (reproduced verbatim from RE-DOC-01 §05) and is not duplicated here. The philosophy behind it, stated explicitly for the first time: **graceful degradation over hard failure — the user should always see *a* plan, even a stale cached one or a static popular-dish fallback, and should never see a blank screen or a crash as a direct consequence of RE unavailability.** Every row in Section 07's fallback table is an instance of this one principle.

---

## Section 19 — System State Transition Model

*(New in v1.1. This models the household's lifecycle across existing states already implied by `profiles.onboarding_completed`, `re_engine.user_re_state.cold_start_mode`, and `profiles.deleted_at` — no new state, column, or table is introduced.)*

### 19.1 — Primary lifecycle (household account)

```
[Unauthenticated]
      | Supabase Auth sign-up (Surface A / infra — out of this contract's scope)
      v
[Signed Up, No Consent]
      | POST /v1/consent (personalization=true)         — Section 06.1
      v
[Consented]
      | App presents OB-01..OB-08b screens; interactions on OB-08b are
      | valid events per LF-L04 even though onboarding_completed=false
      v
[Onboarding In Progress]  <-- /v1/events accepted here (LF-L04, Section 06.3)
      | POST /v1/onboarding (final submit)              — Section 06.2
      v
[Onboarding Complete]  (profiles.onboarding_completed=true, persona_id assigned)
      |
      v
[Cold Start Active]  (user_re_state.cold_start_mode=true, interaction_count<14)
      | 14th qualifying interaction event processed by LF-J02 (async, 15-min batch)
      v
[Personalized / Warm]  (cold_start_mode=false — LF-J05 exitColdStart)
```

**Terminal branch — deletion (independent of the above, can occur from any state after Consented):**
```
[Any state] --- POST /v1/user/delete (Section 06.8) --->
[Deletion Requested] --- immediate --->
[Soft Deleted]  (profiles.deleted_at set)  --- CRON, <=72h (LF-M03) --->
[Hard Deleted]  (all personal data erased except audit_log, retained 3yr per DPDP)
```

**Side-channel — data export (does not change lifecycle state):**
```
[Any authenticated state] --- GET /v1/user/export (Section 06.7) --->
[Export Requested] ---> [Export Queued] ---> [Export Complete] (<=72h)
```

### 19.2 — Per-week plan lifecycle (nested inside "Onboarding Complete" and later states)

```
[No Plan for this week]
      | LF-L01 nightly CRON (23:30 UTC) — not part of this contract's client surface
      v
[Plan Generated]  (week_plans row exists, 21 plan_slots)
      | POST /v1/plan/refresh (unlocked slots only) — Section 06.6
      | -- or -- POST /v1/recommendations (single slot, e.g. after Never/Not-Today) — Section 06.4
      v
[Plan Partially Refreshed]
      | Direct SDK update on plan_slots.is_locked (Surface A, DCR-P3-06-003)
      v
[Slot Locked]  (excluded from all future refresh operations, per LF-L02)
```

**Note:** this per-week model is nested — a household can be in "Cold Start Active" (19.1) while simultaneously having some slots "Locked" and others "Plan Generated" (19.2) in the current week. The two models are orthogonal, which is why they are presented separately rather than merged into one diagram that would misleadingly imply a single linear path.

---

## Section 20 — API Event Contract

*(New in v1.1. This formalizes DOC-P3-03 §12's existing event-routing table — already the authoritative source — into a Producer/Consumer/Payload-ownership view. No event type, table, or routing rule is added or changed.)*

| Domain event | Producer (who emits it) | Synchronous consumer(s) | Asynchronous consumer(s) | Payload owner (table) |
|---|---|---|---|---|
| `dish_accepted`, `dish_locked`, `dish_cooked`, `dish_ordered` | App, via `/v1/events` | `interaction_events` write (LF-J01, <100ms) | LF-J02 (interaction_count), LF-J03 (genome affinity), LF-J04 (bandit state) — 15-min batch | `public.interaction_events` |
| `dish_rated` | App, via `/v1/events` | `interaction_events` write | LF-J03 (genome affinity, positive/negative branch by rating) | `public.interaction_events` |
| `dish_never` | App, via `/v1/events` | `interaction_events` write **+ LF-G01 synchronous** (`re_engine.never_list` write, <200ms) | LF-G04 (class-level affinity, within J02 batch) | `public.interaction_events` (event log) + `re_engine.never_list` (suppression state) |
| `dish_not_today` | App, via `/v1/events` | `interaction_events` write **+ LF-G02 synchronous** (`re_engine.not_today_suppression` write, <200ms) | LF-J02/J04 (interaction_count, bandit β) | `public.interaction_events` + `re_engine.not_today_suppression` |
| `dish_swiped_past` | App, via `/v1/events` | `interaction_events` write | LF-J02/J03/J04 | `public.interaction_events` |
| `onboarding_class_preference` | App, via `/v1/onboarding` (OB-07 swipes) | LF-J06 (class affinity) only — no interaction_count contribution beyond the OB-07-specific cap (DOC-P3-03 §03 LF-A07) | — | `public.interaction_events` (via `onboarding_sessions` origin) |
| `plan_opened`, `session_depth` | App, via `/v1/events` | `interaction_events` write only — analytics, no RE learning function | — | `public.interaction_events` |
| **Slate generated** (system event, not a client-sent `event_type`) | RE Edge Function, via `/v1/recommendations` | `suggestion_logs`, `context_log` writes (LF-J07, inline, <50ms) | Feeds `LF-H01–H04` safety gates immediately, synchronously, before response | `public.suggestion_logs` + `public.context_log` |
| **Persona assigned** (system event) | RE Edge Function, via `/v1/onboarding` | `re_engine.user_re_state` write (LF-A09) | — | `re_engine.user_re_state` |
| **Consent granted/denied** (system event) | App Edge Function, via `/v1/consent` | `consent_records` write (LF-M01) | Gates whether `/v1/onboarding` may proceed at all (Section 06.1) | `public.consent_records` |
| **Export completed** (system event) | Compliance job, via `/v1/user/export` polling path | Export job status update | — | Export job metadata (Section 13 notes this is not itself a `[CONFIRMED]` new table) |
| **Deletion completed** (system event) | Compliance CRON, via LF-M03 | `profiles.deleted_at` (immediate), full erasure (72h) | — | `public.profiles` + all 8 LF-M02-scope tables |

**Coverage confirmation:** every `event_type` in `interaction_events`'s CHECK constraint (§03.15, 11 values) appears above exactly once. No event type is invented; no consumer is added beyond what DOC-P3-03 §12's routing table and Section 06.3's DCR-002 resolution already established.

---

## Section 21 — API Error Catalogue

*(New in v1.1. Extends Section 07's HTTP status table with stable, machine-readable application error codes. Section 07 itself is not modified — this section adds a codified layer on top of it, consistent with the "only add the 8 requested sections" instruction.)*

### 21.0 — Governance rules for application error codes `(new in v1.2)`

These rules apply to every `ERR_*` code in the table below (21.1) and to any code added to it in the future:

| Rule | Statement |
|---|---|
| **Immutability** | Once an `ERR_*` code is published in an ACTIVE version of this document, its **meaning** (the condition it represents) may never change. A code's *wording* in `error.message` may be improved at any time (Section 17.2 already establishes that message text is not a compatibility-relevant field) — but `error.code` itself, and the condition it maps to, is fixed for the life of the code. |
| **Uniqueness** | Each `ERR_*` code maps to exactly one condition and one endpoint-scope. No two rows in Section 21.1 may share a code. A new condition that resembles an existing one gets a new, distinct code rather than overloading an existing one — overloading would silently break any client that branches on `error.code` (the entire reason Section 21's closing note in v1.1 gave this property in the first place). |
| **Deprecation** | An `ERR_*` code is never deleted outright while `/v1` is active. If a condition it represents becomes impossible under the current architecture (e.g., a future schema change removes the underlying CHECK constraint it was mapped to), the code is marked `[DEPRECATED — reason, version]` in the table and retained for historical/client-compatibility reference. Actual removal from the catalogue may only happen at the same time as, and for the same reason as, a breaking path-version change (Section 17.2) — never independently of one. |
| **New code addition** | Adding a new `ERR_*` code for a genuinely new condition is additive, not breaking (consistent with Section 17.2's general rule for new fields/endpoints) — it requires a DCR/SER per Section 16.2 if it corresponds to a new business rule, or a documentation-only note if it simply names a condition that already existed but was previously uncatalogued (as `ERR_RATE_LIMITED` itself was in this document's own history, Section 21.1 note). |

### 21.1 — Catalogue

| Error code | HTTP status | Endpoint(s) | Meaning | Source rule |
|---|---|---|---|---|
| `ERR_VALIDATION_FAILED` | 400 | All | Generic request validation failure (Stage 1) | DOC-P3-03 §02 Stage 1 |
| `ERR_DELETE_CONFIRMATION_MISMATCH` | 400 | `/v1/user/delete` | `confirmation_phrase` did not match | Section 06.8 |
| `ERR_UNAUTHENTICATED` | 401 | All except `/v1/health` | Missing/invalid JWT | Section 04 |
| `ERR_OWNERSHIP_MISMATCH` | 403 | All except `/v1/health` | JWT `user_id` ≠ resource owner | Section 05 |
| `ERR_CONSENT_REQUIRED` | 403 | `/v1/onboarding` | Personalization consent not granted | Section 06.1, DOC-09 §03 |
| `ERR_PLAN_NOT_FOUND` | 404 | `/v1/plan/{user_id}/{week}` | No `week_plans` row for requested week | Section 06.5 |
| `ERR_ONBOARDING_ALREADY_COMPLETE` | 409 | `/v1/onboarding` | Retried call after `onboarding_completed=true` | Section 06.2, Section 08 |
| `ERR_EXPORT_ALREADY_IN_PROGRESS` | 409 | `/v1/user/export` | An active export job already exists for this user | Section 08 |
| `ERR_DELETION_ALREADY_REQUESTED` | 409 | `/v1/user/delete` | `profiles.deleted_at` already set | Section 08 |
| `ERR_EVENT_TYPE_INVALID` | 422 | `/v1/events` | `event_type` not one of the 11 CHECK-constrained values | §03.15 CHECK constraint |
| `ERR_RATING_OUT_OF_RANGE` | 422 | `/v1/events` | `rating` outside 1–5 | §03.15 CHECK constraint |
| `ERR_CONSENT_TYPE_INVALID` | 422 | `/v1/consent` | `consent_type` not one of the 4 CHECK-constrained values | §03.4 CHECK constraint |
| `ERR_RATE_LIMITED` | 429 | Any (Section 10) | Per-endpoint rate limit exceeded | Section 10 — **this is the one genuinely new HTTP status this catalogue introduces relative to Section 07's table**, needed because Section 10 (v1.0) already established rate limits without ever naming the status code they'd return; adding it here, in the new error catalogue, avoids modifying Section 07 itself |
| `ERR_SAFETY_GATE_FAILURE` | 500 | `/v1/recommendations` | Safety gate failed after 2 retries (Stage 8) | DOC-P3-03 §02 Stage 8 |
| `ERR_RE_DEGRADED` | 503 | `/v1/recommendations`, `/v1/plan/refresh` | RE reports degraded via `/v1/health` state | RE-DOC-01 §05 |

**Every code above maps to exactly one row in this table and one HTTP status — this is the "stable" property the Founder's request asked for: a client can branch on `error.code` without depending on `error.message` text, which may change wording over time without being a breaking change (Section 17.2 — message wording is not a compatibility-relevant field, unlike the code).**

---

## Section 22 — API Observability and Operational Contract

*(New in v1.1. Extends the `trace_id` concept Section 07 already introduced, and consolidates monitoring expectations already scattered across RE-DOC-01 §05 and DOC-P3-03A §08 — cited, not duplicated in full.)*

### 22.1 — Correlation IDs and request tracing

- Every Surface B response — success or error — includes `trace_id` (Section 07 already established this for errors; this section extends the same field to success responses, since DOC-P3-03A §08's auditability requirement needs it on the success path too, not only on failure).
- `slate_id` (already present in `/v1/recommendations` responses, §03.16) remains the correct correlation key for anything RE-pipeline-specific; `trace_id` is the correlation key for the HTTP request/response cycle itself. The two are related but distinct — a single `trace_id` could in principle wrap a request that produces no `slate_id` at all (e.g., `/v1/consent`).
- **`[DCR — observation, not a schema change]`:** none of `suggestion_logs`, `context_log`, or `interaction_events` currently has a `trace_id` column, so a full request-to-log correlation is not yet mechanically possible end-to-end — only `slate_id`-based correlation (already fully supported, Section 12 auditability queries) works today. This is noted for DOC-P4-02/a future SER, not resolved here, consistent with "do not modify schema."

### 22.2 — Logging (operational vs. analytics — a distinction worth making explicit)

Two categories of logging exist in this system and must not be conflated:
| Category | Examples | Consent-gated? | Source |
|---|---|---|---|
| **Operational request logs** | method, path, status, latency, `trace_id`, hashed `user_id` | No — required for basic reliability regardless of consent, same category as `ip_address_hash` already stored unconditionally in `consent_records` itself (§03.4) | Standard operational necessity, not previously stated but not in tension with any frozen rule |
| **Analytics events** | PostHog event tracking | **Yes** — gated by `consent_type='analytics'` | DOC-09 §03, LF-M01 |

This distinction resolves a plausible point of confusion (does declining analytics consent mean the server can log nothing at all?) without changing any consent rule — `[DCR]`, minor, non-blocking.

### 22.3 — Metrics

The product's own success metrics are already fully defined (DOC-P3-03 §18: acceptance rate, never rate, session depth, class hit rate, constraint compliance, variety score, plus the offline evaluation metrics for RE version promotion). This section's only addition is mapping them to the API layer that produces the data they're computed from:

| Metric (DOC-P3-03 §18) | Computed from | Which endpoint's writes feed it |
|---|---|---|
| Acceptance rate | `dish_locked`/`dish_cooked`/`dish_ordered` ÷ shown | `/v1/events` ÷ `/v1/recommendations` |
| Never rate | `dish_never` ÷ shown | `/v1/events` ÷ `/v1/recommendations` |
| Constraint compliance | Safety gate results | Internal to `/v1/recommendations` (Section 07 `ERR_SAFETY_GATE_FAILURE`) |
| Class hit rate | `plan_slots.class_code` vs `selected_dish_id.class_code` | `/v1/plan/{user_id}/{week}` read path |

### 22.4 — Health checks and monitoring expectations (cross-reference, not duplicated)

`/v1/health` (Section 06.9) is the contract-level health check. Alert thresholds already exist verbatim in RE-DOC-01 §05 (Section 07): "auto-restart, alert on 3+ consecutive 5xx," "page on-call if down >5 min." This section does not restate them — it confirms they are the correct and complete operational monitoring contract for this API surface, with no gap identified.

---

## Section 23 — API Consumer Matrix

*(New in v1.1. Identifies who calls each endpoint. No new consumer, integration, or endpoint is introduced.)*

| Endpoint | Primary consumer | Internal/secondary consumer | External consumer |
|---|---|---|---|
| `/v1/consent` | Mobile app (React Native/Expo) | — | None |
| `/v1/onboarding` | Mobile app | — | None |
| `/v1/recommendations` | Mobile app | Scheduled recommendation generation (LF-L01 nightly CRON) — via the shared internal recommendation service, **not** via this HTTP endpoint (DCR-P3-06-007, Resolved) | None |
| `/v1/events` | Mobile app | — | None |
| `/v1/plan/{user_id}/{week}` | Mobile app | — | None |
| `/v1/plan/refresh` | Mobile app | — | None |
| `/v1/user/export` | Mobile app | DPDP compliance job (job execution, not a "call" of the endpoint itself) | None |
| `/v1/user/delete` | Mobile app | DPDP compliance CRON (executes the queued hard-delete; does not call this endpoint again) | None |
| `/v1/health` | Mobile app | Could plausibly also be polled by an external uptime monitor (e.g., a free-tier status-check service) — not currently documented as configured, noted only as a natural future use, not a claim that one exists today | Possibly, in future — not currently |

**No third-party/partner API consumer exists anywhere in this system.** `[DOCUMENTED by absence]` — no partner integration, webhook consumer, or B2B API client appears in RE-DOC-01, DOC-P3-03, or DOC-04; the "Order Instead" deep-link feature (F-24) that might have implied one was explicitly moved out of MVP scope (DOC-04 v1.1 changelog, already cited in Section 02).

**`[DCR-P3-06-007 — Resolved in v1.2]`:** whether the nightly `generateWeekPlan()` CRON (LF-L01) invokes the same pipeline as `/v1/recommendations` via a shared internal code module, or via a network call to the public endpoint itself, was open in v1.1. **Founder-confirmed resolution:** scheduled recommendation generation and `/v1/recommendations` share a common internal recommendation service. LF-L01's nightly CRON calls this shared service directly; it does not invoke, and never invokes, the public HTTP endpoint. This keeps the RE pipeline as internal logic that happens to be *exposed* at `/v1/recommendations` (Section 01.2), not logic that *is* the HTTP endpoint. **This is an internal implementation-sharing fact, not a change to any endpoint's contract** — see Section 16.4 (Contract Stability) for why this distinction matters and is stated explicitly rather than left implicit.

---

## Section 24 — Validation Checklist (Definition of Done for this document)

| Requirement | Status |
|---|---|
| Every endpoint traces to DOC-04 PRD | ✅ — F-01–F-10, F-37, F-39, F-40, F-59 cited throughout; F-27/F-28 (grocery) confirmed correctly excluded per DOC-04 v1.1 changelog |
| Every endpoint traces to DOC-P3-03 business logic | ✅ — Section 12, complete LF coverage confirmed, no orphan endpoint, no orphan client-facing LF |
| Every endpoint traces to DOC-P3-04 schema | ✅ — Section 13, every read/write cites an exact table and section number, zero invented tables/columns |
| Every endpoint traces to DOC-P3-02 domain model | ✅ — CDM entity numbers cited per endpoint in Section 06 (carried forward from their originating LF functions in DOC-P3-03, not re-derived) |
| No schema modification proposed | ✅ — zero `CREATE`/`ALTER` statements anywhere in this document; the one schema-adjacent observation (Section 15, missing FK from `interaction_events` to a specific slot) is flagged, not fixed |
| No architecture redesign | ✅ — the two-surface model (Section 01) describes existing RLS + existing RE isolation exactly as DOC-P3-04/RE-DOC-01 already built it; nothing about *how the system works* changes here, only *how it is called* |
| Every new element classified (DCR/CONFIRMED), never silently assumed | ✅ — 8 DCRs (P3-06-001 through 008) and explicit `[CONFIRMED]` tags throughout; Issue Classification Log, Section 25 |
| No implementation code produced | ✅ — JSON examples are contract illustrations, not runnable code; no Edge Function source, no SQL migration |
| Sequence diagrams provided where appropriate | ✅ — Section 14, covering the 4 flows with genuine multi-step/async structure; single-call endpoints (`/v1/health`, `/v1/consent`) correctly omitted as trivial |
| Dependency matrix provided | ✅ — Section 15 |
| **(v1.1)** API Design Principles and Contract Governance provided | ✅ — Section 16 |
| **(v1.1)** API Versioning Strategy (backward compatibility, deprecation, semver, lifecycle) provided | ✅ — Section 17 |
| **(v1.1)** Non-Functional API Requirements provided | ✅ — Section 18 |
| **(v1.1)** System State Transition Model provided | ✅ — Section 19 |
| **(v1.1)** API Event Contract provided | ✅ — Section 20 |
| **(v1.1)** API Error Catalogue provided | ✅ — Section 21 |
| **(v1.1)** API Observability and Operational Contract provided | ✅ — Section 22 |
| **(v1.1)** API Consumer Matrix provided | ✅ — Section 23 |
| **(v1.1)** No new endpoint, table, schema change, or business logic introduced by Sections 16–23 | ✅ — every new section cites and reorganizes existing frozen content; the sole new item is DCR-P3-06-007 (classified, not silently resolved) |
| **(v1.1)** Regression review performed — no v1.0 content removed or weakened | ✅ — see Revision Notice at top of document |
| **(v1.2)** DCR-P3-06-007 closed | ✅ — Section 23, Section 25 |
| **(v1.2)** Contract Stability statement provided | ✅ — Section 16.4 |
| **(v1.2)** Error code governance rules (immutability, uniqueness, deprecation) provided | ✅ — Section 21.0 |
| **(v1.2)** Authentication/authorization failure matrix provided | ✅ — Section 05.1 |
| **(v1.2)** Implementation guidance clearly labelled non-binding where genuinely new | ✅ — Section 18 framing note, 18.3 header, 18.4 per-row labels |
| **(v1.2)** No endpoint, schema, business-logic, or traceability change made | ✅ — confirmed in Revision Notice regression review; the sole new item is DCR-P3-06-008 (classified, not silently resolved) |

---

## Section 25 — Issue Classification Log

Per the project's mandatory classification discipline (Handover §6.4): every issue found, classified before any resolution was assumed.

| ID | Classification | Description | Resolution status |
|---|---|---|---|
| **DCR-P3-06-001** | DCR | `/v1/consent` had no named endpoint despite LF-M01 requiring one before onboarding | Endpoint defined (Section 06.1); no schema change |
| **DCR-P3-06-002** | DCR | `interaction_events` RLS permits direct client INSERT, which would silently skip `re_engine` side-effects for Never/Not-Today | Write-path rule stated explicitly (Section 06.3); **awaiting Founder confirmation of the recommended reading** |
| **DCR-P3-06-003** | DCR | `plan_slots.is_locked` toggle path (client SDK vs custom endpoint) was never explicitly named | Resolved as Surface A (direct SDK) — no new endpoint needed (Section 02) |
| **DCR-P3-06-004** | DCR | LF-L02 pull-to-refresh had no named endpoint and RE-DOC-01 did not specify one-call-vs-many | New endpoint `/v1/plan/refresh` defined (Section 06.6); **awaiting Founder confirmation** |
| **DCR-P3-06-005** | DCR | LF-M03 (account deletion) had no `**Endpoint:**` line, unlike its sibling LF-M02 | New endpoint `/v1/user/delete` defined (Section 06.8); **awaiting Founder confirmation** |
| **DCR-P3-06-006** | DCR (minor) | Client-supplied vs server-fetched weather precedence in `/v1/recommendations` context was never stated | Recommended resolution given (Section 06.4); **non-blocking, Founder confirmation optional** |
| **DCR-P3-06-007** | DCR | While drafting Section 23 (Consumer Matrix) in v1.1, it became apparent that no frozen document states whether LF-L01's nightly `generateWeekPlan()` CRON invokes the pipeline via an internal call to the same code the public `/v1/recommendations` Edge Function runs, or via a self-referential HTTP call to that endpoint | **Resolved in v1.2 — Founder confirmed.** Scheduled recommendation generation (LF-L01) and `/v1/recommendations` share a common internal recommendation service; scheduled jobs invoke this shared service directly and never call the public HTTP endpoint over the network. See Section 23 for the closed statement. |
| **Open, non-DCR** | Observation | `interaction_events.dish_id` has no FK constraint tying it to a specific `plan_slots`/`suggestion_logs` row | Flagged (Section 15) as an absence, not fixed — no action taken, consistent with "do not modify schema" |
| **DCR-P3-06-008 (new in v1.2)** | DCR | While building the Authentication and Authorization Failure Matrix (Section 05.1), it became apparent that "deleted account" and "ownership mismatch" currently share one error code (`ERR_OWNERSHIP_MISMATCH`), with no distinct client-facing signal for the deleted-account case | Recommended reading given in Section 05.1: this is an acceptable, deliberate reuse under Section 21.0's governance rules (same client-observable outcome, different cause — not a uniqueness violation). **Non-blocking; awaiting Founder confirmation of whether a distinct `ERR_ACCOUNT_DELETED` code is wanted in a future revision** |

**No AGR was raised, in v1.0 or in this v1.1 revision.** Nothing about the approved architecture (DOC-P3-04, DOC-P3-05) was found incomplete, inconsistent, or incorrect during either pass — every gap found was a *contract-completeness* gap in the layer this document itself exists to write, not a defect in frozen schema/logic.

---

## Document Sign-off

| Field | Value |
|---|---|
| Document | DOC-P3-06 · API Contract Specification |
| Version | v1.2 |
| Status | **APPROVED — ACTIVE — FROZEN** |
| Supersedes | v1.1 (same session — final polish before sign-off) |
| Endpoints specified | 10 (Surface B) + 1 reference index (Surface A) — unchanged from v1.0/v1.1 |
| New endpoints requiring confirmation | 3 (`/v1/consent` formalized, `/v1/plan/refresh`, `/v1/user/delete`) — DCR-001, 004, 005 — **approved as part of this document's freeze** |
| Documentation clarifications | 8 total (DCR-001 through 008) — DCR-007 Resolved; **DCR-002, 004, 005, 006, 008 remain open but non-blocking, carried forward into Phase 4 and, where relevant, into DOC-P3-07** |
| New sections/subsections added in v1.2 | 4 (16.4, 21.0, 05.1, plus Section 18's framing note and per-row labels) — zero new top-level sections, zero renumbering |
| Architecture changes proposed | 0 |
| Schema changes proposed | 0 |
| Endpoint contract changes proposed | 0 |
| v1.0/v1.1 content removed or weakened | 0 — confirmed via Revision Notice regression review |
| **Freeze rule** | **No further changes without a future AGR, DCR, or explicit Founder instruction reopening this document.** |
| Prerequisite for | DOC-P4-01, DOC-P4-02, **DOC-P3-07 (in progress)** |

Founder sign-off: **APPROVED** — session #028, 2026-07-01
