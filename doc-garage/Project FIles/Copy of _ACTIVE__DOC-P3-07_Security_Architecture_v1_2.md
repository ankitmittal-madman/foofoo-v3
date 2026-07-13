# [ACTIVE]_DOC-P3-07_Security_Architecture_v1.2

**Status:** **ACTIVE — APPROVED — FROZEN**
**Version:** v1.2
**Date:** 2026-07-01
**Supersedes:** `[ACTIVE]_DOC-P3-07_Security_Architecture_v1.1` (same session — governance-only refinement prior to final sign-off, not an architectural revision)
**Approved By:** Founder Sign-off: Approved
**Freeze rule (added at approval, permanent):** No further changes to this document shall be made unless a future AGR, DCR, IDR, SER, or explicit Founder instruction reopens it. This document is now an immutable upstream dependency for DOC-P4-01, DOC-P4-02, and DOC-P3-08, in exactly the same standing as DOC-P3-04/DOC-P3-05/DOC-P3-06 under Baseline Register Step 10. AGR-P3-07-001 remains explicitly OPEN despite this freeze — freezing the document freezes its *content*, not its outstanding governance items; the AGR survives the freeze as a recorded, unresolved item requiring separate Founder direction.
**Current Phase:** APDF Phase 3 (Solution Architecture) — this document completes the mandatory DOC-P3-07 artifact
**Depends On:**
- `[ACTIVE]_DOC-P3-06_API_Contract_Specification_v1.2` (APPROVED — ACTIVE — FROZEN)
- `[ACTIVE]_DOC-P3-04_Data_Architecture_ERD_v1.3` (FROZEN)
- `[ACTIVE]_DOC-P3-05_Parts_a-d` (FROZEN)
- `[ACTIVE]_DOC-P3-03_Business_Logic_Specification_v1.0`
- `[ACTIVE]_DOC-P3-03A_Logic_Governance_Matrix_v1.0`
- `[ACTIVE]_DOC-P3-02_Conceptual_Domain_Model_v1.1`

**Fulfills:**
- APDF Phase 3 Deliverable DOC-P3-07 (Security Architecture) per `[ACTIVE]_APDF_Framework_v1`

**Document Authority:** This document consolidates security architecture. It does not itself have precedence over any document it depends on — where a conflict exists between this document and any document listed under Depends On, the Project Baseline Register's document-precedence rules apply, and the dependency wins.

**Prerequisites:** DOC-P3-02 v1.1, DOC-P3-03 v1.0, DOC-P3-03A v1.0, DOC-P3-04 v1.3, DOC-P3-05 Parts (a)–(d), DOC-P3-06 v1.2 (**APPROVED — ACTIVE — FROZEN**, session #028), RE-DOC-01 v1.0, DOC-04 PRD v1.1, DOC-09 Legal v1.0, DOC-10 Technical Architecture v1.0 (partial — see Section 37)
**Source Documents Referenced:** all of the above, plus `[ACTIVE]_Project_Baseline_Register_v1_2`, `[ACTIVE]_Engineering_Handover_Project_Continuity_Package_v1_0`, `[ACTIVE]_APDF_Framework_v1`, migration files 001–020, 900–904
**Downstream Documents Dependent On This Document:** DOC-P4-01, DOC-P4-02, DOC-P5-01/02, DOC-P3-08 (readiness assessment in progress, Task 3)

**Governance basis (immutable for this session):** DOC-P3-02 through DOC-P3-06 (all frozen), the Project Baseline Register, and the Engineering Handover are treated as authoritative, unmodifiable fact. **This document does not redesign architecture, does not introduce new business logic, and does not silently close any gap it finds.** Every section below states its originating document, its classification (DOCUMENTED / CONFIRMED / DCR / AGR), why the decision exists, what implementation must do, and what implementation must never do. Where information already has an authoritative owner elsewhere, this document references it rather than restating it — this document is a **consolidation and cross-reference layer**, not a second source of truth.

**This is not a cybersecurity checklist.** It is the system security architecture — the set of decisions, already made across six documents, that together determine how FooFoo protects data, enforces identity, and fails safely. Where a genuine gap was found between what DPDP/legal requires and what the frozen architecture actually provides, it is raised here as an AGR, not quietly patched.

---

## Revision Summary — v1.1 → v1.2 (read before the rest of this document; this supersedes v1.1 as the current revision, the v1.0→v1.1 summary below is preserved for history)

**Nature of this revision:** governance-only refinement prior to final sign-off, per explicit Founder instruction. **This is NOT an architectural revision, NOT a redesign, NOT a schema change, NOT an API change.** Every v1.1 section remains at its original number with its original substantive content intact, except for the five narrowly-scoped governance changes listed below.

### Exact list of modified sections

| Section | What changed | Why (justification) |
|---|---|---|
| **Header block** | Added `Depends On`, `Fulfills`, `Document Authority` fields; version bumped to v1.2 | Task 1, Item 5 — explicit dependency and precedence declaration |
| **Section 06** | AGR-P3-07-001 reworded: reframed as an implementation omission relative to DOC-10's stated requirement, not a defect in or justification to redesign DOC-P3-02/03/04/05 themselves; explicit statement that resolution requires Founder direction through controlled governance | Task 1, Item 1 — precise reframing requested; no schema/onboarding/new-field content added, none proposed |
| **Section 19** | Same AGR-P3-07-001 reframing applied for consistency (this document's own established practice of keeping every AGR-P3-07-001 mention consistent, carried forward from the v1.0→v1.1 revision) | Direct consequence of Task 1, Item 1 |
| **Section 35** | Every occurrence of "Phase 4 to implement" replaced with "Required before Production Release" | Task 1, Item 2 — architecture document defines production-readiness criteria, not implementation sequencing |
| **Section 38** | AGR-P3-07-001 risk-row wording aligned to the reframing in Section 06/19 | Direct consequence of Task 1, Item 1 |
| **Section 40** | AGR-P3-07-001 entry reworded to match Section 06; new governance statement added at the top of the section | Task 1, Items 1 and 3 |
| **Section 41** | New executive summary appended above the existing (fully preserved) v1.0/v1.1 regression tables, plus a new v1.1→v1.2 regression table | Task 1, Item 4 — enhancement is additive, nothing removed |
| **Section 42** | Sign-off block updated to v1.2 | Consequence of version increment |

**Sections NOT modified (confirmed intact, unchanged from v1.1):** 00, 01, 02, 03, 04, 05, 07 through 18 (including 14.1), 20 through 34, 36, 37, 39. **No section was renumbered. No section was removed. No traceability row was weakened or deleted. No schema, API contract, or business logic was touched.**

### What this revision explicitly does not do (per Task 1 preamble)

Per instruction: no schema change, no onboarding redesign, no DOB/age-bracket/new-field introduced anywhere in this revision. AGR-P3-07-001 is reworded for precision, not resolved, not silently closed, and no solution is invented for it — it remains exactly as open as it was in v1.1, only more precisely described.

---

**Nature of this revision:** refinement only, per explicit Founder instruction. **No architectural redesign, no rewrite, no restructuring, no renumbering.** Every v1.0 section remains at its original number with its original content intact, except where a specific, narrow change is listed below.

### Exact list of modified sections

| Section | What changed | Why (justification) |
|---|---|---|
| **Section 06** | AGR-P3-07-001 entry updated: added explicit verification record (DOC-P3-02/03/04/05 re-checked in this revision, confirmed no date-of-birth/age/age-category field or logic exists anywhere) and precise status label `Founder Decision Required` | Founder instruction §5 — verify frozen architecture before any decision; confirmed absence, so AGR stays open with the exact classification requested |
| **Section 14** | New subsection **14.1 — Secret Rotation** added | Founder instruction §4 — governance statement only, no rotation frequency specified |
| **Section 17** | Wording refined: distinguishes FooFoo Architectural Decisions / Managed Platform Capabilities / Phase 4 Implementation Responsibilities, replacing "platform default = architecture" framing | Founder instruction §1 — architectural precision, zero behavior change |
| **Section 18** | Same wording refinement as Section 17 | Founder instruction §1 |
| **Section 19** | AGR-P3-07-001 status label updated to `Founder Decision Required` for consistency with Section 06 | Direct consequence of Founder instruction §5 — same fact, same wording, two places it was already stated in v1.0 |
| **Section 28** | Scope clarified: security headers apply only to server-side HTTP responses (Edge Functions), explicitly not to the React Native app | Founder instruction §2 — scope clarification only, no new header introduced |
| **Section 32** | Wording refined using the same three-way distinction as Section 17/18, applied to the non-binding backup-verification guidance | Founder instruction §1 |
| **Section 33** | Same wording refinement applied to the non-binding DR guidance | Founder instruction §1 |
| **Section 37** | Restructured *within the section only* into "A. Architectural Assumptions" and "B. Platform Assumptions" — the three existing assumptions reclassified, zero new assumptions added | Founder instruction §3 |
| **Section 38** | Risk row for AGR-P3-07-001 label aligned to `Founder Decision Required` for consistency | Direct consequence of Founder instruction §5 |
| **Section 39** | One new Security Decision (SD-006) added, recording the v1.1 verification act itself | Transparency — records that a verification was performed, per Founder instruction §5, without inventing a new architectural decision |
| **Section 40** | AGR-P3-07-001 entry updated with verification evidence and confirmed status | Founder instruction §5 |
| **Section 41** | Regression Report expanded with v1.1-specific confirmations | Founder instruction §6 |
| **Section 42** | Sign-off block updated to v1.1 | Founder instruction §7 |

**Sections NOT modified (confirmed intact, unchanged from v1.0):** 00, 01, 02, 03, 04, 05, 07, 08, 09, 10, 11, 12, 13, 15, 16, 20, 21, 22, 23, 24, 25, 26, 27, 29, 30, 31, 34, 35, 36. **No section was renumbered. No section was removed. No traceability row was weakened or deleted.**

### AGR-P3-07-001 verification record (Founder instruction §5)

Before making any change to this document, DOC-P3-02, DOC-P3-03, DOC-P3-04, and DOC-P3-05 were re-searched directly (text search against actual file contents, not memory) for `date_of_birth`, `dob`, `age`, `age_category`, `age_band`, `birth_date`, `minor`, `under-13`. **Result: zero matches for any account-holder age-verification concept.** The only "age" references found anywhere in these four documents concern *household members'* (dependents') age bands for meal-planning segment classification (`SC_WITH_INFANT`, `SC_WITH_TODDLER`, `SC_WITH_SCHOOL_CHILD` — DOC-P3-03 §03 LF-A02) — a different concept entirely from verifying the *primary account holder's* age for DPDP minor-protection purposes. **No frozen document was modified or reinterpreted during this check.** Per Founder instruction, since no existing architectural mechanism was found: AGR-P3-07-001 **remains OPEN**, is **not resolved by reference to existing architecture**, and is classified **`Founder Decision Required`**. No schema change, SER, or onboarding redesign is proposed in this document, consistent with the instruction's explicit prohibition.

---

## Section 00 — Pre-Writing Verification (per Founder instruction: verify before duplicating)

Before drafting, the following check was performed: does DOC-P3-06 v1.2 already own authentication/authorization content that this document should reference rather than restate? **Yes** — Sections 04, 05, 05.1, 18, 21, 22 of DOC-P3-06 v1.2 are the authoritative source for API-layer auth, error codes, and observability. This document cites them by section number throughout (Sections 05, 06, 09, 10, 12, 15, 20–22 below) rather than reproducing their tables. Does DOC-P3-04 already own RLS/schema-level security? **Yes** — Sections 11, 13 below cite DOC-P3-04 §03.x and §03.26 directly. Does DOC-09 already own DPDP/legal content? **Yes** — Section 19 cites it directly rather than re-deriving retention/consent rules. **The single authoritative owner for every fact below is identified in that section's Source line; this document adds no competing definition of any fact it cites.**

---

## Section 01 — Security Principles

| Principle | Source | Tag |
|---|---|---|
| Zero-trust at the API layer — every request validated, no session cookies, stateless | DOC-10 §06 | DOCUMENTED |
| RLS enforced at the database layer, not the application layer, for Surface A | DOC-P3-04 §03.1–03.18 (every table's `ENABLE ROW LEVEL SECURITY`) | DOCUMENTED |
| Authorization enforced in Edge Function code, not RLS, for Surface B (because `service_role` bypasses RLS entirely) | DOC-P3-06 v1.2 §01.2, §05 | DOCUMENTED |
| RE module isolation is itself a security boundary, not just an architectural one — `re_engine` schema is unreadable by any client credential | DOC-P3-04 §03.26; RE-DOC-01 §01–02 | DOCUMENTED |
| No column is ever dropped; sensitive columns are renamed, never deleted, preserving audit continuity | Handover §Key learnings (project-wide governance rule) | DOCUMENTED |
| Fail documented, never fail silent — every failure mode has a named status and app-side fallback | DOC-P3-06 v1.2 §07 | DOCUMENTED |
| Any schema/architecture change requires AGR or SER before implementation — this applies to security-relevant objects (RLS policies, REVOKE statements) exactly as to any other schema object | Project Baseline Register v1.2, Step 10 | DOCUMENTED |

**Implementation must:** treat every principle above as a constraint on Phase 4 code, not a suggestion.
**Implementation must never:** add a security control that isn't traceable to one of these principles or to a specific gap this document raises (Sections 37–39) — an untraceable security addition is exactly the kind of undocumented assumption this project's governance discipline exists to prevent.

---

## Section 02 — Security Objectives

| Objective | Source | Tag |
|---|---|---|
| Zero dietary/religious/allergen safety violations ever served to a user | DOC-P3-03 §10 (4 Safety Gates); RE-DOC-03 §03 (6 hard constraints) | DOCUMENTED |
| No user can read or write another user's data via any surface | DOC-P3-04 RLS policies throughout; DOC-P3-06 v1.2 §05 ownership-check rule | DOCUMENTED |
| No client credential can ever read the RE's scoring logic, weights, or cohort data | DOC-P3-04 §03.26; DOC-10 §06 ("Prevents reverse-engineering of the RE algorithm") | DOCUMENTED |
| DPDP Act 2023 compliance — consent, export, deletion, retention, minor protection — met before launch | DOC-09 §03 | DOCUMENTED |
| Every recommendation fully reconstructable after the fact for audit purposes | DOC-P3-03A §08 | DOCUMENTED |
| No secret ever committed to source control or exposed to client code | DOC-10 §06; DOC-P3-06 v1.2 §01.2/§05 (service_role never in client) | DOCUMENTED |

**Implementation must:** validate every one of these objectives against the Security Validation Checklist (Section 35) before any Phase 4 deployment.
**Implementation must never:** treat "no known violation yet" as equivalent to "objective met" — Objective 1 specifically requires the Safety Gates to run and pass, not merely to exist.

---

## Section 03 — Trust Boundaries

*(Synthesized from DOC-P3-06 v1.2 §01 and RE-DOC-01 §01–02 — both already describe boundaries that together form a trust model; this section names that model explicitly for the first time.)*

| Boundary | What crosses it | What is trusted on each side | Source |
|---|---|---|---|
| **Client ↔ Supabase (Surface A)** | Direct PostgREST calls (profiles, household_members, week_plans, etc.) | Client: holds only its own JWT, never a service credential. Server: RLS is the sole enforcement point. | DOC-P3-06 v1.2 §01.1, §02 |
| **Client ↔ Edge Functions (Surface B)** | HTTP requests to `/v1/*` | Client: JWT only. Server: `service_role`, RLS bypassed — Edge Function code is the sole enforcement point (DOC-P3-06 v1.2 §01.2, §05). | DOC-P3-06 v1.2 §01.2, §05 |
| **Edge Functions ↔ `re_engine` schema** | All RE reads/writes | Only `service_role` may cross this boundary; `anon`/`authenticated` are explicitly `REVOKE`d | DOC-P3-04 §03.26 |
| **Edge Functions ↔ external services** | Weather API, OneSignal (push), Cloudinary (images, per DOC-10 §08) | Server holds API keys; client never sees them. Weather API responses are cached (§03.18) precisely so an untrusted/rate-limited third party cannot become a per-request dependency. | Engineering Handover §7.4; DOC-P3-04 §03.18 |
| **Scheduled jobs ↔ shared recommendation service** | Internal function calls only, no network hop | `service_role`, same trust level as Edge Functions — this boundary does not cross the public internet at all (DOC-P3-06 v1.2 §23, DCR-007 Resolved) | DOC-P3-06 v1.2 §23 |
| **App ↔ device secure storage** | JWT storage on-device | SecureStore (device keychain), never AsyncStorage | DOC-10 §06 |

**Implementation must:** treat every arrow above as a place where an authorization check or a credential boundary is mandatory.
**Implementation must never:** introduce a new crossing point (e.g., a client-side code path that reads `re_engine` directly, or an Edge Function that forwards its `service_role` key to another service) without raising an AGR first — such a crossing would silently move a trust boundary this document has just made explicit.

---

## Section 04 — Threat Model

*(New synthesis — no single frozen document lists threats explicitly, but every mitigation below already exists in a frozen document; this section is the first to organize them by threat rather than by mitigation.)*

| Threat | Mitigated by | Source | Tag |
|---|---|---|---|
| A user reads/modifies another user's household data | RLS ownership policies (Surface A) + Edge Function ownership check (Surface B) | DOC-P3-04 throughout; DOC-P3-06 v1.2 §05 | DOCUMENTED |
| A user reverse-engineers the RE scoring algorithm/weights | `re_engine` schema lockdown, service-role-only | DOC-P3-04 §03.26; DOC-10 §06 | DOCUMENTED |
| A compromised anon/authenticated credential is used to bulk-read data | RLS enforced at DB layer, cannot be bypassed by client code, per-row not per-table | DOC-10 §06; DOC-P3-04 RLS policies | DOCUMENTED |
| A malicious or malformed request causes a diet/allergen/Jain safety violation to be served | 6 hard constraints (pre-scoring) + 4 Safety Gates (pre-serving), both mandatory, non-negotiable ordering | DOC-P3-03 §06, §10; RE-DOC-03 §03 | DOCUMENTED |
| A retried request double-processes a side-effecting event | Idempotency rules per endpoint | DOC-P3-06 v1.2 §08 | DOCUMENTED |
| A client is told *why* its JWT failed, enabling credential-guessing refinement | All three JWT failure modes collapse to one generic `401`/`ERR_UNAUTHENTICATED` | DOC-P3-06 v1.2 §05.1 | DOCUMENTED |
| A secret leaks via source control or client bundle | `.env.local` gitignored, EAS Secrets for build-time, CI secret-scanning, service_role never in client code | DOC-10 §06 | DOCUMENTED |
| A minor (under 13) creates an account, in violation of DPDP | **No mitigation exists in frozen architecture** | — | **AGR-P3-07-001 — see Section 06, Section 19, Section 39** |
| An account that should be deleted continues to be reachable via a stale JWT | JWT itself isn't revoked on deletion (JWTs are stateless/self-verifying); ownership check in Edge Functions checks `profiles.deleted_at`, not JWT validity, for this case | DOC-P3-06 v1.2 §05.1 (deleted-account row) | DOCUMENTED, **with DCR-P3-06-008 already open on the specific error code returned** |
| A dependency (npm/Expo package) introduces a supply-chain vulnerability | **No documented process exists** | — | **DCR-P3-07-006 — see Section 29, Section 38** |

**Implementation must:** treat the two flagged rows as open items requiring Founder decision before Phase 4 closes them — not as already-solved.
**Implementation must never:** assume a threat is mitigated because a *related* control exists — e.g., the deleted-account row is *documented* but still shares an ambiguous error code with a different failure (DCR-008), so "documented" here means "identified and given a defined behavior," not "fully polished."

---

## Section 05 — Authentication Architecture

**Source:** DOC-P3-06 v1.2 §04 (authoritative, referenced not restated) · DOC-10 §06 (device-side storage detail, still valid)
**Tag:** DOCUMENTED

**Why this decision exists:** Supabase Auth issuing a JWT, validated at the Edge Function gateway via `verify_jwt`, is the platform-standard mechanism for the chosen stack (DOC-10 §02) and requires no custom session-management code — reducing the attack surface relative to a hand-rolled session system.

**What implementation must do:** enable `verify_jwt` on every Surface B endpoint except `/v1/health` (DOC-P3-06 v1.2 §04, `[CONFIRMED]`); store the JWT in device SecureStore, never AsyncStorage (DOC-10 §06); send it as `Authorization: Bearer <jwt>` on every authenticated call.

**What implementation must never:** implement a parallel/custom authentication mechanism alongside Supabase Auth; store the JWT in plaintext, AsyncStorage, or any location outside the device's secure enclave; expose `/v1/health` behind authentication (RE-DOC-01 §05 requires it to work even with an expired session).

**Cross-reference, not duplicated:** full endpoint-by-endpoint auth requirement table already exists at DOC-P3-06 v1.2 §04.

---

## Section 06 — Authorization Architecture

**Source:** DOC-P3-06 v1.2 §05 (authoritative) · DOC-P3-04 RLS policies (authoritative for Surface A)
**Tag:** DOCUMENTED, with one AGR raised below

**Why this decision exists:** because `service_role` bypasses RLS entirely (Section 03), RLS cannot be the authorization mechanism for Surface B — DOC-P3-06 v1.2 §05 correctly identifies that Edge Function code itself must be the enforcement point, and states the exact rule (`JWT user_id == resource owner`).

**What implementation must do:** implement the ownership check from DOC-P3-06 v1.2 §05's table on every Surface B endpoint, before touching any table, exactly as specified; rely on RLS alone (no additional code) for Surface A.

**What implementation must never:** assume RLS provides any protection inside an Edge Function; skip the ownership check "because the JWT was already validated" — validity and ownership are two different checks (Section 05.1 of DOC-P3-06 already distinguishes these explicitly).

**`AGR-P3-07-001` — raised in v1.0, re-verified in v1.1, reworded for precision in v1.2, detailed in Section 19/38/40:** DOC-10 §06 states that age verification is a required technical implementation ("OB-03 or signup includes age verification... QA test case: under-13 input blocked"), directly reflecting DOC-09 §03's non-negotiable DPDP minor-protection requirement. **The frozen P3 architecture (DOC-P3-02, DOC-P3-03, DOC-P3-04, DOC-P3-05) currently contains no implemented mechanism for this** — DOC-P3-03 §03 LF-A03 (`processRegionalIdentity`, the actual OB-03 function) covers only home_state/current_city/migration_duration; DOC-P3-04 §03.1 `profiles` has no date-of-birth or age-confirmation column; no onboarding LF function (A01–A09) performs age verification. **v1.2 reframing (precision only, no new finding):** this is correctly understood as **an implementation omission relative to DOC-10's stated requirement**, not a defect in DOC-P3-02/03/04/05 themselves and not, by itself, justification to redesign the frozen architecture. DOC-10 describes a capability that was never actually carried through into the Phase 3 conceptual/logic/schema documents that followed it — the gap sits in the handoff between DOC-10 and DOC-P3-02 onward, not in any single frozen document being internally wrong. **v1.1 verification (direct text search against DOC-P3-02, DOC-P3-03, DOC-P3-04, DOC-P3-05, performed per Founder instruction before any decision was made):** zero matches for `date_of_birth`, `dob`, `age_category`, `age_band`, `birth_date`, or `minor` anywhere in these four documents in the account-holder-age sense — the only "age" references found concern household members' (dependents') age bands for meal-planning segments (`SC_WITH_INFANT` etc., DOC-P3-03 §03 LF-A02), an unrelated concept. **Status: OPEN.** Resolution requires explicit Founder direction through controlled governance (an AGR-approved architecture correction or a Founder-accepted policy-only mitigation) if pursued in the future — this document raises the omission and does not invent, propose, or default to any particular resolution path. No schema change, SER, or onboarding redesign is proposed here.

---

## Section 07 — Identity Lifecycle

**Source:** DOC-P3-06 v1.2 §19.1 (System State Transition Model — authoritative, referenced not restated) · DOC-P3-04 §03.1 (`profiles.deleted_at`)
**Tag:** DOCUMENTED

**Why this decision exists:** the household account's lifecycle (Unauthenticated → Consented → Onboarding → Cold Start → Personalized → Deletion) is already fully modeled; security architecture's job is to identify which transitions are security-relevant, not to re-model the lifecycle.

**Security-relevant transitions:**
| Transition | Security relevance |
|---|---|
| Unauthenticated → Signed Up | Supabase Auth account creation — **this is where AGR-P3-07-001's missing age gate would need to be enforced, and currently is not** |
| Signed Up → Consented | Gates whether any personal data may be collected at all (DOC-09 §03; DOC-P3-06 v1.2 §06.1) |
| Any state → Soft Deleted → Hard Deleted | `profiles.deleted_at` immediately blocks further access via the ownership-check path (Section 06); JWT itself remains technically valid until expiry — see Section 08 |

**What implementation must do:** enforce consent-before-data-collection exactly as DOC-P3-06 v1.2 §06.1/Section 06.3 already specifies; treat `deleted_at IS NOT NULL` as an authorization failure state, not merely a data-visibility filter.
**What implementation must never:** allow any onboarding data collection to begin before personalization consent is recorded (DOC-09 §03 — no exceptions, including for testing/staging, since `foofoo-mvp` is the same production Supabase project referenced throughout).

---

## Section 08 — Session Management

**Source:** Supabase platform default (no frozen document states specific values) · DOC-10 §06 (storage mechanism)
**Tag:** `[CONFIRMED — platform default, not an invented value]`

**Why this decision exists:** Supabase Auth's default JWT access-token expiry (short-lived, refreshed via a separate refresh token) is the standard session model for the chosen stack; no document overrides it, so the platform default is the architecture.

**What implementation must do:** use Supabase's standard refresh-token rotation flow client-side; treat token refresh failures the same as `ERR_UNAUTHENTICATED` (DOC-P3-06 v1.2 §21.1) rather than inventing a distinct error state.

**What implementation must never:** extend token lifetime beyond the Supabase default to "improve UX," since a longer-lived token increases the window in which a stolen device's SecureStore compromise remains exploitable.

**`DCR-P3-07-002` (minor, non-blocking):** no frozen document states the exact access-token TTL or refresh behavior as a project-specific decision (it is simply "whatever Supabase defaults to"). This is flagged for Founder awareness, not because it's wrong — an explicit decision to *rely on the platform default* is itself a valid architecture decision, but it should be recorded as one rather than left implicit.

---

## Section 09 — JWT Security

**Source:** DOC-P3-06 v1.2 §04, §05.1 (authoritative) · DOC-10 §06 (storage)
**Tag:** DOCUMENTED

**Why this decision exists:** a JWT is a bearer credential; its entire security model depends on (a) never being exposed outside the device/server boundary and (b) its three failure modes never leaking distinguishing information.

**What implementation must do:** verify signature and expiry at the Edge Function gateway (`verify_jwt`) before any function code runs; collapse missing/expired/invalid JWT to one generic response, exactly as DOC-P3-06 v1.2 §05.1 already specifies and justifies (information-disclosure avoidance); store client-side only in SecureStore.

**What implementation must never:** log a raw JWT anywhere (Section 22 addresses what *is* safe to log); return a response body that distinguishes *why* a JWT was rejected; accept a JWT whose `user_id` claim doesn't match Supabase Auth's own record for that session.

---

## Section 10 — Service Role Usage

**Source:** DOC-P3-04 §03.26 (authoritative) · DOC-10 §06 · DOC-P3-06 v1.2 §01.2
**Tag:** DOCUMENTED

**Why this decision exists:** `service_role` is the single most powerful credential in the system — it bypasses every RLS policy on every table in both schemas. Its usage must be as narrow as the architecture already makes it.

**What implementation must do:** use `service_role` only inside Edge Functions (server-side execution environment) and scheduled jobs, per DOC-P3-06 v1.2 §23's confirmed shared-service model; perform the ownership check (Section 06) as the very first action of any `service_role`-context function, before any query.

**What implementation must never:** include the `service_role` key in any React Native/Expo client bundle, any git commit, or any log line; use `service_role` for any read that a narrower credential could perform; pass the `service_role` key to a third-party service (weather, push, image CDN) — those integrations use their own separate API keys (Section 14), never Supabase's.

---

## Section 11 — RLS Security Model

**Source:** DOC-P3-04 §03.1–03.18 (every `public` table's policy block — authoritative, not restated in full)
**Tag:** DOCUMENTED

**Why this decision exists:** RLS is the sole protection for Surface A (Section 03) and is enforced at the database layer, meaning it cannot be bypassed by any client-side logic error — this is the correct security placement for data that only ever needs owner-only access, per DOC-10 §06's own stated rationale ("cannot be bypassed by client code").

**What implementation must do:** enable RLS on every new `public` table exactly as the existing 18+ tables already do (Baseline Register Step 10 — this is schema-frozen, so "every new table" refers only to a future SER-approved addition, not a Phase 4 discretion); use `auth.uid() = profile_id`-style policies exactly as already implemented.

**What implementation must never:** create a `public` table without RLS enabled; add an RLS policy that grants broader access than owner-only without an explicit product requirement and an SER (per Baseline Register Step 10, RLS policies are schema objects and are covered by the freeze).

---

## Section 12 — Edge Function Security

**Source:** DOC-P3-06 v1.2 §01.2, §05, §05.1 (authoritative)
**Tag:** DOCUMENTED

**Why this decision exists:** Edge Functions are the one execution context where `service_role` and untrusted client input meet directly — this is the highest-risk code surface in the system.

**What implementation must do:** verify JWT (Section 09) → check ownership (Section 06) → validate request shape (Section 25) → only then touch any table, in that exact order, for every Surface B endpoint; treat DOC-P3-06 v1.2's 10 endpoint contracts as the complete and only Surface B surface (no undocumented endpoint may exist).

**What implementation must never:** perform any database write before both the JWT check and the ownership check have passed; trust any field in the request body as an authorization signal (only the JWT's own claims are trusted for identity).

---

## Section 13 — Database Security

**Source:** DOC-P3-04 §03.26 (`re_engine` lockdown), §03.1–03.18 (RLS), migration `019_rls_policies` (42 statements, per Engineering Handover §3.4)
**Tag:** DOCUMENTED

**Why this decision exists:** two schemas, two trust levels — `public` is RLS-protected and partially client-visible; `re_engine` is `service_role`-only with zero client visibility, by explicit `REVOKE` (Section 03).

**What implementation must do:** preserve the two-schema boundary exactly; run the migration files in their frozen numbered sequence (Baseline Register Step 10) for any future SER-approved change.

**What implementation must never:** grant `anon` or `authenticated` any privilege on any `re_engine` object, under any circumstance, including "just for debugging" — DOC-10 §06's own stated rationale ("prevents reverse-engineering of the RE algorithm") is a business-critical protection, not merely a nice-to-have.

---

## Section 14 — Secrets Management

**Source:** DOC-10 §06 · Engineering Handover §8 (Knowledge Sources — API key handling context)
**Tag:** DOCUMENTED, with one clarification

**Why this decision exists:** secrets (Supabase `service_role` key, Weather API key, OneSignal key, Cloudinary key) must never be reachable from client code or source control, since any of them leaking would compromise either user data (`service_role`) or a paid/rate-limited third-party account.

**What implementation must do:** store client-build-time values (if any are genuinely needed client-side, e.g., the `anon` public key, which is *designed* to be public and RLS-protected) via EAS Secrets; store all server-side secrets (`service_role`, Weather API key, OneSignal key, Cloudinary key) as Supabase Edge Function environment secrets, never in the mobile app bundle at all; run automated secret-pattern scanning in CI (DOC-10 §06) on every commit.

**What implementation must never:** commit any secret to git, including in `.env` files without `.gitignore` coverage; use the same secret across `foofoo-mvp` (production) and any future staging project without explicit rotation.

### 14.1 — Secret Rotation `(new in v1.1)`

**Source:** No frozen document addresses rotation explicitly — this is a governance statement derived from Section 10's and Section 14's existing narrow-usage principle, not a new architectural mechanism.
**Tag:** `[CONFIRMED — architectural governance statement, no operational frequency specified]`

**Why this decision exists:** a secret that can only be rotated by changing application code or schema is a secret whose blast radius, if compromised, extends far beyond the credential itself — this statement exists to ensure rotation is a pure operations action, isolated from every other layer.

**What implementation must do:** ensure every secret (`service_role` key, Weather API key, OneSignal key, Cloudinary key) is rotatable by updating the Supabase Edge Function secret store or EAS Secrets value alone, with zero code deployment and zero schema change required; treat rotation ownership as belonging to operations, not to any application-layer or business-logic component.

**What implementation must never:** hardcode a secret anywhere in source, tests, or configuration files that would require a code change to update; design any schema object (table, column, constraint) whose correctness depends on a specific secret value, which would couple rotation to a migration.

**What this section explicitly does not do:** specify a rotation cadence, trigger, or schedule — that is an operational decision for a future runbook (DOC-P5 or an operations document), not an architectural one, and is deliberately left unspecified here per Founder instruction.

**`DCR-P3-07-003` (clarification, non-blocking):** DOC-10 §06 describes secrets management primarily in terms of `.env.local` and "EAS Secrets," which are client-build-time mechanisms — but the `service_role` key and third-party API keys used *inside Edge Functions* are properly Supabase project-level Edge Function secrets, a distinct mechanism DOC-10 does not separately name. This is a documentation gap in DOC-10 (already flagged more generally as open gap G-4 in the Engineering Handover), not a new architectural decision — resolved here by naming both mechanisms explicitly so Phase 4 doesn't conflate them.

---

## Section 15 — API Security

**Source:** DOC-P3-06 v1.2 (all of Sections 04, 05, 05.1, 07, 08, 21, 22 — authoritative, cross-referenced not restated)
**Tag:** DOCUMENTED

**Why this decision exists:** DOC-P3-06 v1.2 already is the API security contract in most of its substance; this section exists only to confirm that every API-security-relevant fact has exactly one home (DOC-P3-06) and this document does not compete with it.

**What implementation must do:** treat DOC-P3-06 v1.2 as frozen (Section 00 above, Founder freeze instruction, session #028) for every API-layer security fact — authentication, authorization, error codes, idempotency, rate limiting.

**What implementation must never:** re-specify an endpoint's auth/authz behavior differently here or in any future document without a DCR/AGR against DOC-P3-06 itself — this document adds threat-model and cross-cutting context (Sections 01–04, 16–39) around DOC-P3-06's contract, it does not modify the contract.

---

## Section 16 — Data Classification

**Source:** DOC-P3-04 (table-by-table, synthesized here for the first time) · DOC-09 §03 (DPDP category language)
**Tag:** DOCUMENTED (synthesis of existing facts, no new classification invented)

| Class | Examples | Protection | Source |
|---|---|---|---|
| **Personal identifying** | `profiles` (name, home_state, city) | RLS owner-only; DPDP export/delete scope | DOC-P3-04 §03.1; DOC-P3-03 §15 |
| **Health/dietary (sensitive, separate consent required)** | `diet_type`, `religious_pref`, `allergen_flags`, `household_members` | RLS owner-only; separate `personalization` consent gate before collection | DOC-09 §03 ("health/dietary data requires separate consent") |
| **Behavioral/interaction** | `interaction_events`, `suggestion_logs`, `context_log` | RLS owner-only (client-visible tables); append-only; DPDP 2-year retention ceiling | DOC-P3-04 §03.15–03.17; DOC-09 §03 |
| **RE-internal (never client-visible, regardless of ownership)** | `re_engine.*` — cohorts, weights, taste vectors, never_list | `service_role`-only, zero RLS exposure to the owning user themselves | DOC-P3-04 §03.26–03.29 |
| **Compliance/audit** | `consent_records`, `audit_log` | Append-only; retained per DPDP schedule independent of account deletion (`audit_log` survives hard-delete) | DOC-P3-04 §03.4; DOC-P3-03 §15 LF-M03 |
| **Public/non-personal** | `dishes`, `ingredients`, `tags`, `weather_cache` | Public read; zero personal data | DOC-P3-04 §03.5–03.9, §03.18 |

**Implementation must:** apply the protection level of the *most sensitive* class whenever a query joins across classes (e.g., a query joining `household_members` to `dishes` is still health/dietary-classified for RLS purposes, because `household_members` is).
**Implementation must never:** treat `re_engine` data as merely "internal implementation detail" for classification purposes — it is classified this strictly *because* it is commercially sensitive (the RE algorithm itself), not because it contains personal data (much of it doesn't).

---

## Section 17 — Encryption at Rest

**Source:** Supabase managed infrastructure (DOC-10 §02 stack selection) — no frozen document states a FooFoo-specific encryption configuration
**Tag:** `[CONFIRMED — reliance on managed platform capability, distinct from a FooFoo architectural decision]`

**Why this decision exists `(wording refined in v1.1 — no behavior change)`:** FooFoo's architecture makes a deliberate decision to build on a managed platform (Supabase) rather than operating its own database infrastructure (DOC-10 §02). Encryption at rest is not itself a FooFoo architectural decision — it is a **managed platform capability** that decision brings with it. The distinction matters: FooFoo decided *to rely on Supabase*; Supabase, not FooFoo, decides *how* data is encrypted at rest. Conflating the two (as v1.0's wording risked doing by calling the platform default "the architecture") would incorrectly suggest this project made an encryption-specific design choice, when it made a platform choice and inherited this capability as a consequence.

**FooFoo Architectural Decision:** rely on a managed PostgreSQL provider (Supabase) rather than self-hosting, per DOC-10 §02.
**Managed Platform Capability:** encryption at rest, provided and operated entirely by Supabase, outside this project's configuration surface.
**Phase 4 Implementation Responsibility:** verify, once, that the specific Supabase plan/region in production actually provides encryption at rest as advertised, before launch — ownership for this verification sits with implementation, not with this architecture document.

**What implementation must do:** perform the verification above as a one-time pre-launch check.
**What implementation must never:** implement a redundant, custom, application-level encryption layer on top of the managed capability without a documented reason — this would add complexity and key-management risk without a stated threat it addresses beyond what the platform already provides.

---

## Section 18 — Encryption in Transit

**Source:** Supabase/Vercel managed infrastructure (TLS) · DOC-10 §06 (`Authorization: Bearer` over what is implicitly HTTPS)
**Tag:** `[CONFIRMED — reliance on managed platform capability, distinct from a FooFoo architectural decision]`

**Why this decision exists `(wording refined in v1.1 — no behavior change)`:** as with Section 17, FooFoo's architectural decision is to build on Supabase and Vercel (DOC-10 §02); TLS termination and enforcement is a **managed platform capability** that comes with that decision, not a separate FooFoo-specific security design. No document states a project-specific TLS configuration, because none is needed — the platform already enforces HTTPS-only by default.

**FooFoo Architectural Decision:** build on Supabase and Vercel rather than self-hosted infrastructure.
**Managed Platform Capability:** HTTPS/TLS enforcement on every Supabase and Vercel endpoint, by default.
**Phase 4 Implementation Responsibility:** ensure every third-party integration this project *adds* (Weather API, OneSignal, Cloudinary) is also called over HTTPS only — those are outside Supabase/Vercel's managed boundary, so this specific check is implementation's responsibility, not something inherited automatically.

**What implementation must do:** verify HTTPS-only for every external integration call, per the responsibility above.
**What implementation must never:** disable certificate validation on any client-side HTTP client "for testing" in a way that could persist into a release build.

---

## Section 19 — Privacy & DPDP Compliance

**Source:** DOC-09 §03 (authoritative for legal requirements) · DOC-P3-03 §15 (LF-M01–M03, authoritative for technical implementation) · DOC-P3-06 v1.2 §06.1, §06.7, §06.8 (authoritative for the API contract)
**Tag:** DOCUMENTED, with one AGR and one clarifying DCR

**Why this decision exists:** DPDP Act 2023 compliance is a legal precondition for launch (DOC-09 §01: "must be complete BEFORE the app is published"), and the technical implementation of every DPDP requirement already has a specified owner across DOC-P3-03/DOC-P3-06.

| DPDP requirement (DOC-09 §03) | Technical owner | Status |
|---|---|---|
| Granular, separate consent per category | LF-M01; `/v1/consent` (DOC-P3-06 v1.2 §06.1); `consent_records` table (DOC-P3-04 §03.4) | ✅ Fully specified |
| Data export within 72h | LF-M02; `/v1/user/export` (DOC-P3-06 v1.2 §06.7) | ✅ Fully specified |
| Account deletion within 72h, full erasure | LF-M03; `/v1/user/delete` (DOC-P3-06 v1.2 §06.8) | ✅ Fully specified |
| Data retention policy | Interaction logs 2yr max (DOC-09 §03); `audit_log` 3yr (DOC-P3-03 §15) | ✅ **DCR-P3-07-004, resolved below — not a conflict** |
| Minor protection (no under-13 users) | **No implemented mechanism exists in the frozen P3 architecture** | ❌ **AGR-P3-07-001 — OPEN. Implementation omission relative to DOC-10 §06's stated requirement (Section 06) — this is where it becomes a launch-blocking legal gap, not merely an architectural one** |
| Data minimisation | DOC-04 NFR ("only data that materially changes the meal plan") | ✅ Documented principle; no per-field audit performed in this document (out of scope — see Section 39) |

**`DCR-P3-07-004` (resolved, not a conflict):** DOC-09 §03 states interaction logs are retained "2 years maximum," while DOC-P3-03 §15 LF-M03 states `audit_log` rows are retained 3 years. These are **different tables** (`public.interaction_events` vs. the separate audit/compliance log per DOC-P3-04 §03.19–24) governing different data categories (behavioral data vs. compliance audit trail) — not a version conflict. Stated explicitly here because the similarity of the two numbers (2 vs. 3 years) invites exactly the kind of misreading a security document should prevent.

**What implementation must do:** implement every ✅ row exactly per its cited owner document; escalate AGR-P3-07-001 to the Founder before any public launch, since DOC-09 §01 makes DPDP compliance a hard pre-launch gate and this specific implementation omission currently has zero remediation path without explicit Founder direction through controlled governance.

**What implementation must never:** launch publicly with AGR-P3-07-001 unresolved — DOC-09 itself states this is not optional ("violation risks app removal and regulatory action").

---

## Section 20 — Audit Logging

**Source:** DOC-P3-03A §08 (authoritative — full reconstruction-query detail, not restated) · DOC-P3-04 §03.15–03.17
**Tag:** DOCUMENTED, with one known limitation already disclosed upstream

**Why this decision exists:** every recommendation must be fully reconstructable (Section 02, Objective 5) — this is a business/regulatory need (explaining *why* a dish was suggested), not merely an operational convenience.

**What implementation must do:** write to `suggestion_logs`, `context_log`, and `interaction_events` exactly as DOC-P3-03A §08 specifies, on every recommendation request, with no sampling at MVP for these three tables (the known 5%-sampled `recommendation_debug_log` is a *separate*, lower-fidelity, Phase 1 enhancement — DOC-P3-03A §08 — and its absence at MVP is already disclosed, not a new gap this document is raising).

**What implementation must never:** allow any of the three core audit tables to be written to by any credential other than the owning Edge Function under `service_role`, or allow a client `UPDATE`/`DELETE` on any of them (all are append-only by RLS policy design, DOC-P3-04 §03.15–03.17).

---

## Section 21 — Observability & Security Monitoring

**Source:** DOC-P3-06 v1.2 §22 (authoritative — correlation IDs, logging categories, metrics)
**Tag:** DOCUMENTED

**Why this decision exists:** security monitoring and general operational monitoring share the same `trace_id`/logging infrastructure (DOC-P3-06 v1.2 §22.1–22.2) — there is no separate "security log" architecture, by design, since splitting them would create two sources of truth for the same request.

**What implementation must do:** treat `ERR_OWNERSHIP_MISMATCH` and `ERR_UNAUTHENTICATED` rates as security-relevant metrics in addition to their operational role (a spike in either is a plausible attack signal, not only a plausible bug signal); apply DOC-P3-06 v1.2 §22.2's operational-vs-analytics distinction consistently — security-relevant operational logs are never consent-gated, exactly as that section already establishes for reliability logs generally.

**What implementation must never:** log a raw JWT, a raw request body containing dietary/health fields, or any `re_engine` row content in a way that would defeat Section 13's schema-level lockdown by making the same data readable via log-aggregator access instead.

---

## Section 22 — Incident Detection

**Source:** RE-DOC-01 §05 (fallback/failure table, authoritative) · DOC-P3-03 §10 (Safety Gates)
**Tag:** DOCUMENTED

**Why this decision exists:** the two categories of incident this system is specifically built to detect — RE unavailability and safety gate violations — already have fully specified detection and response behavior; a security incident (unauthorized access attempt) is detected via the same operational monitoring (Section 21), not a separate mechanism.

**What implementation must do:** treat "3+ consecutive 5xx" and "down >5min" (RE-DOC-01 §05) as the existing incident-detection thresholds for availability; treat any non-zero Safety Gate result as a P0 incident with zero tolerance (DOC-P3-03 §10 — "Any non-zero result is a P0 production incident"), which is the single most severe incident class in this system, security or otherwise.

**What implementation must never:** treat a Safety Gate violation as a "bug to fix in the next sprint" — DOC-P3-03 §10's own language ("P0") already forecloses that response.

---

## Section 23 — Security Event Flow

*(New synthesis — traces an authorization failure end-to-end through already-existing mechanisms, introduces no new mechanism.)*

```
Client sends request with bad/missing JWT
      |
      v
Edge Function gateway verify_jwt --> 401 ERR_UNAUTHENTICATED (DOC-P3-06 v1.2 Section 05.1)
      |  (logged: method, path, status, latency, trace_id -- Section 21;
      |   NOT logged: the JWT itself)
      v
Operational metrics: ERR_UNAUTHENTICATED rate (Section 21) --> spike is a monitoring signal
      |
      v
[If pattern of repeated failures from same source is later investigated]
Founder/on-call reviews operational logs via trace_id correlation (DOC-P3-06 v1.2 Section 22.1)
```
```
Client sends request with valid JWT but wrong resource ownership
      |
      v
Edge Function ownership check --> 403 ERR_OWNERSHIP_MISMATCH (Section 06)
      |  (same logging discipline as above)
      v
Same monitoring path as above
```
```
Recommendation pipeline produces a slate that fails a Safety Gate
      |
      v
Gate failure --> discard slate, regenerate (max 2 retries) --> DOC-P3-03 Section 02 Stage 8
      |
      v
After 2 failures: 500 ERR_SAFETY_GATE_FAILURE + cached-plan signal (DOC-P3-06 v1.2 Section 21.1)
      |
      v
P0 incident (Section 22) -- logged to suggestion_logs/context_log for full reconstruction (Section 20)
```

**Implementation must:** ensure every arrow above is actually wired to the logging/metrics infrastructure of Section 21 — this diagram describes intended flow, not yet-built code.
**Implementation must never:** treat this diagram as authorizing any new table, field, or endpoint — every box above already exists in a cited source document.

---

## Section 24 — Abuse Prevention

**Source:** DOC-P3-06 v1.2 §10 (Rate Limiting, authoritative) · Section 05.1 (generic auth failure responses as an anti-enumeration measure)
**Tag:** DOCUMENTED, with implementation guidance clearly separated (per Founder instruction)

**Why this decision exists:** the two abuse vectors this architecture is specifically shaped to resist are (a) credential enumeration via distinguishing error responses (already prevented, Section 09) and (b) resource exhaustion via uncapped request volume (already addressed in principle by DOC-P3-06 v1.2 §10, though without concrete numbers).

**What implementation must do:** implement rate limiting per DOC-P3-06 v1.2 §10's table; treat the *existence* of a limit on every endpoint as binding (that a limit must exist is architectural), while treating the *specific numbers* DOC-P3-06 v1.2 §10 suggests as non-binding Phase 4 implementation guidance (that document's own Section 10 already flags this: "no numeric ceiling exists in any frozen document; recommend Founder set an explicit number before Phase 4").

**What implementation must never:** ship any Surface B endpoint with no rate limit at all, even `/v1/health` at a very high ceiling (DoS resistance, distinct from the auth-exemption Section 05 already grants it).

---

## Section 25 — Rate Limiting Strategy

**Source:** DOC-P3-06 v1.2 §10 (authoritative, cross-referenced not restated) · §21.1 (`ERR_RATE_LIMITED`/`429`)
**Tag:** Mixed — binding principle, **non-binding specific numbers** (label carried forward explicitly per Founder instruction in this session)

**What implementation must do (binding):** return `429`/`ERR_RATE_LIMITED` when any limit is exceeded, per DOC-P3-06 v1.2 §21.1; apply per-user (not per-IP-only) limiting, since the JWT already identifies the caller uniquely and IP-based limiting alone would be both weaker and would risk penalizing shared-NAT mobile users unfairly.

**What implementation must do (non-binding guidance, Phase 4 to confirm actual numbers):** the specific per-endpoint ceilings suggested in DOC-P3-06 v1.2 §10 (e.g., "reasonable interactive ceiling" for `/v1/recommendations`, "a few per hour" for `/v1/plan/refresh`) are starting points, not requirements — DOC-P3-06 v1.2 §10 itself already labels them this way, and this document does not strengthen that label into a binding one.

**What implementation must never:** rate-limit `/v1/events` aggressively enough to throttle legitimate rapid swiping — DOC-P3-06 v1.2 §10 explicitly warns against this ("must not throttle real interaction").

---

## Section 26 — Input Validation

**Source:** DOC-P3-03 §02 Stage 1 (`validateRequest()`, authoritative) · DOC-P3-04 CHECK constraints throughout (authoritative) · DOC-P3-06 v1.2 §21.1 (`ERR_VALIDATION_FAILED`, `ERR_EVENT_TYPE_INVALID`, etc.)
**Tag:** DOCUMENTED

**Why this decision exists:** input validation already exists at two layers by design — Stage 1 of the pipeline (business-logic-level, DOC-P3-03) and CHECK constraints (database-level, DOC-P3-04) — providing defense in depth: even if an Edge Function's own validation had a bug, the database itself rejects a structurally invalid row.

**What implementation must do:** validate every request field against the exact enums/ranges DOC-P3-04's CHECK constraints already define (e.g., `event_type` against the 11-value list, `rating` against 1–5) *before* attempting a write, so the client gets a `422` with a specific `ERR_*` code (DOC-P3-06 v1.2 §21.1) rather than a raw database constraint-violation error.

**What implementation must never:** rely on the database CHECK constraint as the *only* validation layer — that would leak PostgreSQL error text to the client and bypass the stable error-code contract DOC-P3-06 v1.2 §21 establishes.

---

## Section 27 — Output Validation

**Source:** No frozen document addresses this explicitly
**Tag:** `[SCOPE NOTE — non-binding Phase 4 implementation guidance]`

**Why this is flagged rather than specified:** unlike input validation, no document defines what "output validation" means for this system's specific response shapes — this is standard API hygiene (never returning more fields than the contract specifies, never leaking a stack trace in an error body) rather than a FooFoo-specific architectural decision.

**What implementation should do (non-binding):** ensure every Surface B response matches exactly the shape DOC-P3-06 v1.2 §06 specifies — no extra fields, no internal identifiers beyond what's contracted; ensure error responses never include a raw exception message or stack trace, only the `error.code`/`error.message`/`trace_id` envelope (DOC-P3-06 v1.2 §07).

**What implementation should never do (non-binding):** return a `re_engine` internal identifier (e.g., a raw `re_personas.id` beyond the already-contracted opaque `persona_id`) in any response — this would be a data classification violation (Section 16) even though no document explicitly names "output validation" as its own control.

---

## Section 28 — Security Headers

**Source:** No frozen document addresses this
**Tag:** `[SCOPE NOTE — non-binding Phase 4 implementation guidance]`

**Scope clarification `(added in v1.1 — no new header introduced, no behavior change)`:** security headers are an HTTP response-layer concern. They apply **only** to HTTP responses served by Edge Functions or any other server-side HTTP endpoint (Surface B, per DOC-P3-06 v1.2 §01.2, and any Vercel-hosted surface). **They do not apply to the React Native mobile application itself** — the app is an HTTP *client*, not an HTTP server; it has no responses of its own to attach headers to, and concepts like `Strict-Transport-Security` or `X-Content-Type-Options` are meaningless in a native client context. Any future web-based surface (e.g., a marketing site, if one is ever added) would be a separate, explicitly server-side context this section already covers — not a reason to apply these headers to the app.

**What implementation should do (non-binding):** apply standard security headers (`Strict-Transport-Security`, `X-Content-Type-Options: nosniff`, etc.) on any Vercel-hosted or Edge Function HTTP surface, per platform defaults where available; this is conventional web-security hygiene, not a FooFoo-specific decision, and is labeled non-binding for exactly that reason — no architectural document mandates specific header values.

**What implementation should never do (non-binding):** disable a platform-default security header without a documented reason; attempt to apply HTTP response headers within the React Native app's own code, which would be a scope error, not a security improvement.

---

## Section 29 — Dependency Security

**Source:** No frozen document addresses this
**Tag:** `[SCOPE NOTE — non-binding Phase 4 implementation guidance]`

**What implementation should do (non-binding):** run automated dependency vulnerability scanning (e.g., `npm audit`, Dependabot or equivalent) in the CI pipeline DOC-10 §10 already establishes, as a natural extension of that pipeline's existing "automated secret scan" step (DOC-10 §06) rather than a new pipeline.

**What implementation should never do (non-binding):** treat a known-vulnerable dependency as acceptable "because it's a dev dependency" without checking whether it runs in any CI/build context that touches secrets (Section 14).

**`DCR-P3-07-006`:** flagged (Section 04, Section 38) as an open item with no documented process — recommend a lightweight policy (e.g., CI fails on any `high`/`critical` advisory) be adopted in DOC-P4-02, not invented here as a binding rule.

---

## Section 30 — Supply Chain Security

**Source:** No frozen document addresses this
**Tag:** `[SCOPE NOTE — non-binding Phase 4 implementation guidance]`

**What implementation should do (non-binding):** pin dependency versions (lockfiles already implied by the npm/Expo toolchain, DOC-10 §02); prefer well-maintained, widely-used packages for anything touching secrets or auth (already true of the chosen stack — Supabase SDK, Expo, not obscure alternatives).

**What implementation should never do (non-binding):** add a third-party SDK with write access to `service_role`-protected resources without a security review, given that Section 10's narrow `service_role` usage principle would otherwise be defeated by a compromised dependency.

---

## Section 31 — Infrastructure Security

**Source:** DOC-10 §02 (stack selection), §10 (CI/CD, environment map "locked — do not modify without founder approval")
**Tag:** DOCUMENTED

**Why this decision exists:** the environment map (dev/staging/production separation) is already locked by Founder decision (DOC-10 §10) — infrastructure security here means respecting that lock, not designing new infrastructure.

**What implementation must do:** respect the locked environment map exactly; ensure `foofoo-mvp` (production Supabase project, per project memory/Baseline Register) is never used as a testing target for anything that could trigger Section 19's deletion/export flows against real user data.

**What implementation must never:** modify the environment map without Founder approval, per DOC-10 §10's own explicit statement; provision a new environment outside this map without the same approval.

---

## Section 32 — Backup & Recovery Security Considerations

**Source:** No frozen document addresses this explicitly beyond migration rollback files (DOC-P3-05 Part a — every forward migration paired with a `_rollback.sql`, per Engineering Handover §6.2)
**Tag:** DOCUMENTED (for schema rollback) + `[CONFIRMED — reliance on managed platform capability]` (for data backup, non-binding)

**What implementation must do (binding, already documented):** maintain the paired rollback-file discipline for any future SER-approved migration, exactly as the existing 001–020/100–102 sequence already does.

**Backup, refined `(v1.1 — no behavior change)`:** data backup is not a FooFoo architectural decision — it is a **managed platform capability** inherited from the decision to build on Supabase (DOC-10 §02), the same distinction drawn in Section 17.

**FooFoo Architectural Decision:** rely on Supabase's managed database rather than operating custom backup infrastructure.
**Managed Platform Capability:** automated backups, provided and operated by Supabase.
**Phase 4 Implementation Responsibility:** verify that restore procedures are actually tested at least once before launch — no document specifies a backup *testing* cadence, so this ownership is stated here as guidance, not requirement, and sits with implementation.

**What implementation must never do (binding):** treat a schema rollback file as a substitute for a data backup, or vice versa — they solve different problems (structure vs. content) and conflating them is a common recovery-planning error.

---

## Section 33 — Disaster Recovery Security Considerations

**Source:** No frozen document addresses this explicitly
**Tag:** `[SCOPE NOTE — non-binding Phase 4 implementation guidance]`

**Refined `(v1.1 — no behavior change)`:** disaster recovery for the underlying infrastructure is a **managed platform capability** consideration, not a FooFoo architectural decision, following the same distinction as Sections 17, 18, and 32.

**FooFoo Architectural Decision:** rely on free-tier managed infrastructure (Supabase, Vercel) for MVP, per Engineering Handover §7.4.
**Managed Platform Capability:** whatever disaster-recovery posture the underlying free-tier services provide — typically no formal SLA at this tier.
**Phase 4 Implementation Responsibility:** define an actual recovery-time objective in DOC-P4-02 or a future DOC-P5 document, given that free-tier services frequently have no recovery SLA to build a stricter internal one on top of (the same honest-target-setting pattern already used in DOC-P3-06 v1.2 §18.1 for availability) — this ownership sits with implementation, not with this architecture document.

**What implementation must never do (binding, by inheritance from Section 19):** allow a disaster-recovery restore to reintroduce data for an account whose deletion had already completed and been confirmed to the user under DPDP (Section 19) — a backup restore must be reconciled against the deletion log, not blindly applied.

---

## Section 34 — Security Testing Strategy

**Source:** DOC-P3-05 Parts 900–904 (structural + behavioral validation, authoritative pattern) · DOC-P3-03 §10 (Safety Gates as living queries)
**Tag:** DOCUMENTED (pattern to extend, per Handover §6.6's own instruction: "extend the behavioral-validation pattern from files 901–904 rather than reinventing it")

**What implementation must do:** extend the existing behavioral-validation pattern — live mutation tests, two-user RLS impersonation (already proven in `903_behavioral_rls_validation.sql`), planted-violation detection (already proven in `902_behavioral_safety_gates.sql`) — to cover the new Surface B endpoints (Section 12) once DOC-P4-02 implements them; re-run the 4 Safety Gate queries (Section 04) as a mandatory pre-deploy gate for every future release, exactly as DOC-09 §06's ongoing compliance calendar already requires ("Before every major release... RE safety gate queries must return 0 violations").

**What implementation must never:** consider Phase 4 "security-tested" based on structural checks alone (table/RLS/trigger existence) — Handover §6.6 already establishes that structural verification alone is insufficient, and this applies to security testing specifically, not only to general correctness testing.

---

## Section 35 — Security Validation Checklist

| Requirement | Status |
|---|---|
| Every Surface B endpoint has `verify_jwt` enabled except `/v1/health` | ⬜ Required before Production Release — architecturally specified (Section 05) |
| Every Surface B endpoint performs the ownership check before any table access | ⬜ Required before Production Release — architecturally specified (Section 06) |
| No `service_role` key appears in any client bundle or git history | ⬜ Required before Production Release — architecturally specified (Section 10, 14) |
| Every `public` table has RLS enabled with owner-only policies | ✅ Already true per DOC-P3-04, verified in `903_behavioral_rls_validation.sql` |
| `re_engine` schema is unreachable by `anon`/`authenticated` | ✅ Already true per DOC-P3-04 §03.26, structurally verified in `900_structural_validation.sql` |
| All 4 Safety Gates return 0 rows | ✅ Verified live in `902_behavioral_safety_gates.sql` (illustrative data); must be re-verified at real scale post-Phase 3.5 |
| Consent is captured before any onboarding data collection | ⬜ Required before Production Release — architecturally specified (Section 07, 19) |
| Age gate for DPDP minor protection | ❌ **Not possible to check — no mechanism exists (AGR-P3-07-001)** |
| Data export/deletion complete within 72h | ⬜ Required before Production Release — architecturally specified (Section 19) |
| No JWT, request body, or `re_engine` content appears in operational logs | ⬜ Required before Production Release — architecturally specified (Section 21) |

---

## Section 36 — Security Traceability Matrix

| Security control | DOC-P3-02 (CDM) | DOC-P3-03 (Logic) | DOC-P3-04 (Schema) | DOC-P3-06 (API) |
|---|---|---|---|---|
| Ownership-based access | Invariant references throughout (e.g., Invariant 11, one plan per household) | LF functions operate per `profile_id` throughout | RLS policies, every table §03.1–03.18 | §05, §05.1 |
| `re_engine` isolation | 8-layer dependency map implies RE as a distinct layer | RE functions (Groups B–J) never described as client-callable | §03.26 | §01.2, §23 |
| Safety gates | Invariant 12 (hard constraints before scoring) | §10 LF-H01–H04 | Gate queries reference §03.15–03.16 | Not directly — internal to `/v1/recommendations`, §06.4 |
| Consent gating | Not a numbered CDM entity (compliance record, not domain entity — DOC-P3-03 §15) | LF-M01 | §03.4 | §06.1 |
| Error/auth failure handling | — | §02 Stage 1 | CHECK constraints throughout | §05.1, §07, §21 |

**This matrix exists to make explicit what Sections 05–15 already state individually: every security control traces to all four layers, and no layer is missing for any control except where a gap is explicitly raised (AGR-P3-07-001 has no CDM/Schema/API entry at all — that absence is the gap).**

---

## Section 37 — Security Assumptions

*(Reclassified in v1.1 into two categories per Founder instruction. The three assumptions are unchanged in substance — zero new assumptions were added; only their grouping changed, to make explicit which are about this project's own architecture and which are about the platforms it depends on.)*

### A. Architectural Assumptions

| Assumption | Why it's an assumption, not a fact | Risk if wrong |
|---|---|---|
| No admin/staff role will be added without revisiting Section 06 | DOC-P3-06 v1.2 §05 states no role-based authorization exists beyond the single household-owner role; this document assumes that remains true | Medium — an admin surface added without a corresponding authorization redesign would be a significant, easy-to-miss gap |
| DOC-10 §06's security content is accurate wherever it doesn't touch schema-specific naming | DOC-10 is known-partially-superseded (Engineering Handover open gap G-4) — this document relied on its auth/secrets/storage content while explicitly discounting its schema-naming and endpoint-naming content (Sections 08, 14, and the resolved DCRs below) | Low — the discounted parts were identified and resolved (DCR-P3-07-001/002 below), not silently trusted |

### B. Platform Assumptions

| Assumption | Why it's an assumption, not a fact | Risk if wrong |
|---|---|---|
| Supabase/Vercel managed platform capabilities (encryption at rest/in transit, backup — Sections 17, 18, 32) meet FooFoo's actual security bar | No independent verification performed in this document; this project's architectural decision is to *rely on* these managed capabilities (Sections 17/18/32's v1.1 wording), and this assumption is specifically about whether that reliance is well-founded | Low probability, given both are established platforms, but unverified |

**`DCR-P3-07-001` (resolved by precedence, logged for completeness):** DOC-10 §06 describes consent as stored in `profiles.consent_record` (JSONB). DOC-P3-04 §03.4 (frozen, authoritative, later) defines a separate, append-only `consent_records` table instead. DOC-P3-04 wins per the Baseline Register's document-precedence rules; DOC-10's description is superseded, consistent with the already-open G-4 gap.

**`DCR-P3-07-005` (resolved by precedence, logged for completeness):** DOC-10 §06 names the deletion/export endpoints as `DELETE /v1/user` and `GET /v1/user/export`. DOC-P3-06 v1.2 (frozen, authoritative, later) specifies `POST /v1/user/delete` and `GET /v1/user/export`. DOC-P3-06 wins; DOC-10's naming is superseded, same G-4 lineage.

---

## Section 38 — Security Risks

| Risk | Severity | Mitigation status |
|---|---|---|
| Minor (under-13) account creation possible today | **High** — direct DPDP violation, launch-blocking per DOC-09 §01 | Unmitigated — AGR-P3-07-001, OPEN. Implementation omission relative to DOC-10 §06, requires Founder direction through controlled governance if pursued |
| Deleted-account and ownership-mismatch failures share one error code | Low | Open, non-blocking — DCR-P3-06-008 (inherited, not new) |
| No dependency/supply-chain scanning process defined | Low–Medium | Open, non-binding guidance only — Sections 29, 30 |
| No disaster-recovery RTO/RPO defined for free-tier infrastructure | Low at MVP scale, grows with DAU | Open, non-binding guidance only — Section 33 |
| Reliance on unverified platform-default encryption/backup claims | Low | Open — Section 37 assumption, recommend one-time verification before launch |

**Implementation must:** carry the High-severity row into the Founder's pre-launch checklist explicitly — this document does not have the authority to close it, only to surface it clearly.

---

## Section 39 — Security Decisions Log

| ID | Decision | Reasoning | Source |
|---|---|---|---|
| SD-001 | Authorization enforced in Edge Function code, never assumed from RLS, for all Surface B | `service_role` bypasses RLS entirely | DOC-P3-06 v1.2 §01.2/§05, ratified here |
| SD-002 | `re_engine` schema security is treated as a business-confidentiality control, not only a privacy control | Protects the RE algorithm itself, per DOC-10 §06's own stated rationale | Section 16 |
| SD-003 | Three JWT failure modes collapse to one response, deliberately | Prevents credential-guessing information disclosure | DOC-P3-06 v1.2 §05.1, ratified here |
| SD-004 | Platform defaults (encryption, session TTL, backups) are treated as the architecture where no document overrides them, rather than left undefined | Consistent with this project's own precedent (DOC-P3-06 v1.2 §18.1's honest-target-setting for availability) | Sections 08, 17, 18, 32 |
| SD-005 | AGR-P3-07-001 (missing age gate) is escalated, not silently patched with an invented mechanism | Per Founder's explicit instruction: raise AGRs, don't silently close gaps | Section 06, 19 |
| SD-006 `(new in v1.1)` | AGR-P3-07-001 confirmed OPEN after direct re-verification against DOC-P3-02/03/04/05, rather than assumed still-open from v1.0 memory | Per Founder instruction §5: verify frozen architecture before any decision. No age/DOB/age-category mechanism found; no schema change or SER proposed as a result — the verification itself, not a fix, is the decision recorded here | Section 06, Revision Summary |

---

## Section 40 — Open DCR / AGR Register

**Governance statement `(added in v1.2, Task 1 Item 3):** No DCR or AGR raised in this document modifies or supersedes any ACTIVE frozen architecture document. All open items recorded here are governance records only and require formal approval before changing any architectural baseline.

| ID | Type | Status | Summary |
|---|---|---|---|
| AGR-P3-07-001 | AGR | **OPEN.** Implementation omission relative to DOC-10 §06's stated requirement — not a defect in, and not grounds to redesign, DOC-P3-02/03/04/05 | DOC-10 requires an age-verification capability; the frozen P3 architecture contains no implemented mechanism for it. v1.1 performed a direct text search of DOC-P3-02/03/04/05 confirming zero matches for any account-holder age concept. Resolution requires explicit Founder direction through controlled governance if pursued — see Revision Summary and Section 06 |
| DCR-P3-07-001 | DCR | Resolved by precedence | DOC-10's JSONB consent description superseded by DOC-P3-04's `consent_records` table |
| DCR-P3-07-002 | DCR | Non-blocking, flagged for Founder awareness | JWT TTL/refresh behavior relies on unstated platform default |
| DCR-P3-07-003 | DCR | Resolved | Secrets management: distinguished client-build-time (EAS) vs. server-side (Supabase Edge Function secrets) mechanisms DOC-10 conflated |
| DCR-P3-07-004 | DCR | Resolved — not a conflict | 2-year vs. 3-year retention periods apply to different tables |
| DCR-P3-07-005 | DCR | Resolved by precedence | DOC-10's endpoint naming (`DELETE /v1/user`) superseded by DOC-P3-06's actual contract |
| DCR-P3-07-006 | DCR | Open, non-blocking | No dependency/supply-chain security process defined |
| *(inherited)* DCR-P3-06-002, 004, 005, 006, 008 | DCR | Open, non-blocking, carried forward unchanged | See DOC-P3-06 v1.2 §25 — not restated here, referenced per Section 00's duplication-avoidance rule |

**No new AGR was raised against DOC-P3-04, DOC-P3-05, or DOC-P3-06 themselves.** AGR-P3-07-001 is raised against the gap between DOC-10's stated requirement and its absence in DOC-P3-02/DOC-P3-03/DOC-P3-04 — it does not allege any of those documents are *internally* incorrect, only that a requirement DOC-10 specifies was never carried into them.

---

## Section 41 — Regression Review

### Executive Summary `(added in v1.2, Task 1 Item 4 — appended, nothing below removed)`

| Metric | v1.0→v1.1 | v1.1→v1.2 | Cumulative (v1.0→v1.2) |
|---|---|---|---|
| **Sections Added** | 0 top-level (1 subsection: 14.1) | 0 top-level, 0 subsections | 0 top-level sections added; 1 subsection (14.1) |
| **Sections Removed** | 0 | 0 | 0 |
| **Architecture Decisions Modified** | 0 | 0 | 0 |
| **Security Decisions Added** | 1 (SD-006) | 0 (no new SD entry — this revision is wording-only, no new decision was made) | 6 total (SD-001–SD-006) |
| **DCR Status Summary** | 6 raised (001–006); 4 resolved-by-precedence/clarification, 2 open non-blocking | No new DCR raised or closed; DCR-P3-07-001 through 006 statuses unchanged | 6 DCRs total (DOC-P3-07-owned), plus 5 inherited unchanged from DOC-P3-06 |
| **AGR Status Summary** | 1 raised (AGR-P3-07-001), re-verified against DOC-P3-02/03/04/05, confirmed OPEN | 0 new AGRs; AGR-P3-07-001 reworded for precision (implementation-omission framing per Task 1 Item 1), **status remains OPEN, not closed, not resolved** | 1 AGR total, still OPEN after two revisions |

### v1.1 → v1.2 regression check (per Task 1, Item 6)

| Check | Result |
|---|---|
| Zero deleted sections | ✅ Confirmed — all 43 section headers (00–42) present, identical titles, identical order to v1.1 |
| Zero weakened controls | ✅ Confirmed — every "must"/"must never" rule in Sections 05–36 is present verbatim; the only textual changes are to Sections 06, 19, 35, 38, 40 (AGR wording and checklist labels), none of which loosen a control — if anything, "Required before Production Release" is a stricter release gate than "Phase 4 to implement," not a weaker one |
| Zero modified API contracts | ✅ Confirmed — DOC-P3-06 v1.2 is not touched by this revision at all |
| Zero schema changes | ✅ Confirmed — no table, column, or constraint referenced differently than in v1.1 |
| Zero business logic changes | ✅ Confirmed — no LF function citation altered |
| Zero security architecture redesign | ✅ Confirmed — Sections 01–36 (the substantive architecture) are untouched except for the five specifically-requested wording/labeling changes; no new control, mechanism, or boundary introduced |
| Nothing changed beyond the requested governance refinements | ✅ Confirmed — the 8 touched locations (header, Section 06, 19, 35, 38, 40, 41, 42) map exactly to Task 1's 5 numbered items; no incidental change was made elsewhere. **Nothing to stop and report — regression is clean.** |

---

### v1.0 baseline and v1.0→v1.1 regression (preserved verbatim from v1.1, not re-derived)


| Check | Result |
|---|---|
| Every source document referenced (complete list) | DOC-P3-02 v1.1, DOC-P3-03 v1.0 (+ supporting Context Baseline/Logic Inventory), DOC-P3-03A v1.0, DOC-P3-04 v1.3, DOC-P3-05 Parts (a)–(d) + Gap Register, DOC-P3-06 v1.2, RE-DOC-01 v1.0, DOC-04 v1.1, DOC-09 v1.0, DOC-10 v1.0, Project Baseline Register v1.2, Engineering Handover v1.0, APDF Framework v1.0, migration files 001–020/900–904 |
| No upstream architecture changed | ✅ Confirmed — zero `CREATE`/`ALTER` statements; zero modifications to any DOC-P3-02/03/04/05/06 content |
| No business logic changed | ✅ Confirmed — no LF function's formula, threshold, or behavior is altered; AGR-P3-07-001 identifies an *absence*, it does not add logic to fill it |
| No schema changed | ✅ Confirmed — no table, column, RLS policy, or constraint is added or altered |
| No API contract changed | ✅ Confirmed — DOC-P3-06 v1.2's 10 endpoints, request/response shapes, and error codes are cited exactly as frozen, zero additions |
| No undocumented assumption introduced | ✅ Confirmed — every genuinely new statement in this document is tagged `[CONFIRMED]` or `[SCOPE NOTE — non-binding]` and justified against a named source |
| Anything that could affect DOC-P3-04, DOC-P3-05, or DOC-P3-06 | **AGR-P3-07-001 could eventually affect DOC-P3-04 (a new column, e.g. a date-of-birth or age-confirmation field on `profiles`) and DOC-P3-02/DOC-P3-03 (a new CDM concept and LF function for age verification) if the Founder resolves it by adding the capability rather than by a policy-only fix (e.g., a Terms-of-Service checkbox with no stored field).** This document does not decide which resolution path is correct — that remains explicitly a Founder decision (Section 06), and either path is legitimate; only the *schema-touching* path would require a follow-on SER per Baseline Register Step 10. **v1.1 changes nothing about this note** — it is carried forward unweakened, exactly as it stood in v1.0. |

### v1.1-specific regression checks (per Founder instruction §6)

| Check | Result |
|---|---|
| No security architecture weakened | ✅ Confirmed — every v1.0 "must"/"must never" rule in Sections 05–36 is present verbatim; the wording refinements in 17/18/32/33 change *framing* (platform capability vs. architectural decision), not any control, requirement, or behavior; diff-verified below |
| No API contract changed | ✅ Confirmed — DOC-P3-06 v1.2 is not touched by this revision at all |
| No schema changed inside this document | ✅ Confirmed — zero schema references altered; AGR-P3-07-001 remains explicitly un-resolved-by-schema-change, per instruction |
| No business logic changed inside this document | ✅ Confirmed — Sections 01–16, 20–27, 29–31, 34–36 (all business-logic-adjacent content) are untouched |
| No upstream document modified | ✅ Confirmed — DOC-P3-02, DOC-P3-03, DOC-P3-04, DOC-P3-05 were read-only searched for the AGR-P3-07-001 verification (Revision Summary), never edited; DOC-P3-06 v1.2 remains frozen and untouched |
| No undocumented assumptions introduced | ✅ Confirmed — the one new subsection (14.1 Secret Rotation) is tagged `[CONFIRMED — architectural governance statement]` and traces to Sections 10/14's existing principle, not to an invented fact |
| No section renumbered | ✅ Confirmed — Sections 00–42 retain their exact v1.0 numbers; only sub-content within 06, 14, 17, 18, 19, 28, 32, 33, 37, 38, 39, 40 changed, and 14.1 is a new subsection, not a renumbering of anything |
| No section removed | ✅ Confirmed — all 43 headers (00–42) present, verified by direct comparison against v1.0 |
| No traceability row weakened or deleted | ✅ Confirmed — Section 36's traceability matrix is untouched; every Source/Tag citation in the 13 modified sections was preserved or strengthened (e.g., Section 06's AGR entry gained a verification citation, it lost nothing) |
| AGR-P3-07-001 resolution path followed exactly as instructed | ✅ Confirmed — verified against DOC-P3-02/03/04/05 (found nothing), left OPEN, classified `Founder Decision Required`, no schema change/SER/onboarding redesign proposed |

**Overall regression verdict (v1.0→v1.1): PASS.** This revision is confirmed to be refinement-only: 13 of 43 sections received narrowly-scoped edits, all other sections are byte-identical to v1.0, and no architecture, schema, business logic, or API contract was altered anywhere in the process.

### Overall v1.2 verdict

**PASS.** This governance-only refinement touched exactly 8 locations (header block, Sections 06, 19, 35, 38, 40, 41, 42), all mapping directly to Task 1's 5 numbered items. Zero sections added or removed. Zero controls weakened. Zero API, schema, or business-logic changes. AGR-P3-07-001 remains OPEN — reworded for precision, not resolved, not silently closed, no solution invented. Nothing was found that exceeded the requested scope; there is nothing to stop and report.

---

## Section 42 — Founder Sign-off

| Field | Value |
|---|---|
| Document | DOC-P3-07 · Security Architecture |
| Version | v1.2 |
| Status | **ACTIVE — APPROVED — FROZEN** |
| Supersedes | v1.1 (same session — governance-only refinement, not an architectural revision) |
| Sections | 42 (per Founder specification) — all present, none renumbered, none removed, across all three versions |
| Sections modified in v1.2 | 8 touch-points — header block, Sections 06, 19, 35, 38, 40, 41, 42 — all governance-only, per Task 1's 5 numbered items |
| Sections unchanged, byte-identical to v1.1 | 35 of 43 — see Revision Summary for the complete list |
| AGRs raised | 1 — AGR-P3-07-001, **OPEN — implementation omission relative to DOC-10 §06, requires Founder direction through controlled governance if pursued. Freezing this document does NOT close this AGR.** |
| DCRs raised (DOC-P3-07-owned, unchanged since v1.0) | 6 — DCR-P3-07-001 through 006, 4 resolved-by-precedence/clarification, 2 open non-blocking |
| DCRs inherited unchanged from DOC-P3-06 | 5 — DCR-P3-06-002, 004, 005, 006, 008 (not restated, referenced) |
| Architecture/schema/logic/API changes made (this document, all versions) | 0 |
| New architectural mechanisms introduced in v1.2 | 0 — every v1.2 change is wording, labeling, or header metadata |
| Regression review result | PASS (Section 41) — v1.0 baseline, v1.0→v1.1, and v1.1→v1.2 checks, plus new Executive Summary |
| **Freeze rule** | **No further changes without a future AGR, DCR, IDR, SER, or explicit Founder instruction reopening this document.** |
| Prerequisite for | DOC-P4-01, DOC-P4-02 (both should treat AGR-P3-07-001's eventual resolution as a possible late-arriving input), **DOC-P3-08 (readiness assessment in progress, Task 3)** |
| Recommended immediate next step | AGR-P3-07-001 remains open and separately tracked; it does not block this document's approval/freeze per Founder instruction (Task 2). Proceed to DOC-P3-08 readiness assessment (Task 3) |

Founder sign-off: **Approved** — session #030, 2026-07-01
