# [DRAFT]_DOC-P4-02_Service_and_Edge_Function_Specifications_v1.0

**Status:** **DRAFT — pending Founder sign-off.** Contains one open architectural decision (AD-01) that GATES onboarding implementation. Not authoritative until ratified. No code, no schema/DB/migration/seed/security change is made by this document.
**Version:** v1.0
**Date:** 2026-07-14
**Placement:** docs/architecture/[DRAFT]_DOC-P4-02_Service_and_Edge_Function_Specifications_v1.0.md
**Supersedes:** none (first issue of the DOC-P4-02 artifact that DOC-P3-06 and DOC-P4-00 both name as a downstream dependency).
**Authored because:** the WP-8C Architectural Reconciliation Report (Phase 5, Option B) proved this artifact is a required-but-absent specification for the onboarding→plan runtime boundary.
**Governance basis (frozen, authoritative, NOT redesigned here):** DOC-P3-02 (CDM), DOC-P3-03 v1.0 (Business Logic — LF-A01–A09, B01/B02, C01/C02, L01–L04, M01), DOC-P3-03A v1.0 (Logic Governance & Execution Matrix — §02 R/W matrix, §07 execution classification, §08 auditability), DOC-P3-04 v1.3 (Schema/ERD), DOC-P3-06 v1.2 (API Contract — §04/§05/§06.1/§06.2/§12/§13/§14.1/§21), DOC-P4-00 v1.0 (Backend Foundation Architecture), DOC-09 §03 (DPDP), RE-DOC-01 (RE isolation), SER-001 (city_tier), REPO-CERT-007/010 (Data Gate).

> **Scope discipline.** This document specifies *how the onboarding and consent services/Edge Functions are structured and sequenced* on the already-frozen platform, schema, API contract, and RE design. It introduces **no new endpoint, table, schema element, or business rule.** Every specification below either cites a frozen artifact or is explicitly flagged as an implementation-layer convention (DCR-class) or an open decision (AD-01) requiring Founder ratification. **No business logic, algorithm, mapping, or API behaviour is invented.**

---

## Section 0 — Purpose & Position

DOC-P4-00 (WP-8A) is the backend *architecture* umbrella; it explicitly names DOC-P4-02 as its downstream **Service/Edge-Function Specifications** (DOC-P4-00 §8). DOC-P3-06 lists DOC-P4-02 among its downstream dependents. This document fills that slot for the **onboarding + consent** surface (the WP-8C scope) and defines the **hand-off contracts to WP-8D (RE core) and WP-8E (recommendations + nightly plan)**. It does not re-specify the RE scoring pipeline (that is DOC-P3-03 §06–11, realized in WP-8D) — it specifies the *service boundaries and sequencing* around it.

**One-source-of-truth:** where DOC-P3-04 (schema), DOC-P3-06 (contract), or DOC-P3-03/03A (logic) already state a fact, this document **cites** it and does not restate-and-risk-divergence.

---

## Section 1 — Onboarding Lifecycle (states, evidence-cited)

Reproduces DOC-P3-06 §19.1 + DOC-P3-03 §03/§14, no new state:

```
[Signed Up] --POST /v1/consent (personalization=true, §06.1)--> [Consented]
[Consented] --app renders OB-01..OB-08a (LF-A01..A07 captured client-side, submitted at end)-->
[Onboarding In Progress] --(OB-08b plan preview; LF-L04 events accepted, onboarding_completed=false)-->
[Onboarding Submit] --POST /v1/onboarding (LF-A01..A09 server-side)-->
[Onboarding Complete] (profiles.onboarding_completed=true, user_re_state.persona_id set)
        --(first week plan produced: see AD-01)--> [Cold Start Active] (cold_start_mode=true, interaction_count<14)
```

**Determinable now (frozen):** the server-side onboarding call runs LF-A01–A09 synchronously (DOC-P3-03A §07: A01–A09 all "Synchronous", <200ms/step), resolves persona (LF-A09, DB lookup on `re_persona_assignment_rules`, Option-B fallback per §03), computes confidence (LF-A08, §03 formula), and writes `profiles`, `household_members`, `onboarding_sessions`, `re_engine.user_re_state`, `re_engine.user_taste_vectors` (DOC-P3-06 §13; DOC-P3-03A §02). It is idempotent per household — a retry after `onboarding_completed=true` returns `409 ERR_ONBOARDING_ALREADY_COMPLETE` (DOC-P3-06 §06.2/§08/§21.1).

**NOT determinable from frozen docs → AD-01 (Section 3).**

---

## Section 2 — Service / Edge-Function Ownership & Boundaries

| Concern | Owner (this spec) | Evidence |
|---|---|---|
| JWT verification | `_shared/auth/authenticate` middleware | DOC-P3-06 §04; DOC-P4-00 §7; built REPO-CERT-011 |
| Ownership check (JWT `sub` == body `user_id`) | in-function `requireOwnership` | DOC-P3-06 §05/§05.1 |
| Consent capture (LF-M01) | `ConsentService` → `ConsentRepository` → `consent_records` | DOC-P3-03 §15; built REPO-CERT-011 |
| Onboarding orchestration (LF-A01–A09) | `OnboardingService` (new, WP-8C) → repositories | DOC-P3-03 §03; DOC-P3-03A §02 |
| Persona/cohort/state resolution | `OnboardingService` via `PersonaRepository`/`CohortRepository` (read-only on RE reference tables) | DOC-P3-03 §03 LF-A09, §04 LF-B01/B02 |
| Week-plan generation (LF-L01) | **RE core service (WP-8D) invoked by WP-8E endpoint/CRON — NOT owned by onboarding** | DOC-P3-03 §14 (CRON); DOC-P3-03A §07 (Scheduled CRON); DOC-P4-00 §310–322 |
| Derived columns / genome vectors | **DB triggers — never written by backend** | DOC-P4-00 §15; CDM Invariant 6; REPO-CERT-010 |

**Hard boundary (frozen, RE-DOC-01 §02; DOC-P4-00 §3):** the RE core reads RE-owned tables and writes only RE-owned plan/log tables; onboarding never writes `week_plans`/`plan_slots` (DOC-P3-06 §13; DOC-P3-03A §02). Because Edge Functions run as `service_role` (RLS bypassed), **every** ownership check is explicit in code (DOC-P3-06 §01.2/§05).

---

## Section 3 — AD-01 (OPEN DECISION — Founder sign-off required, GATES onboarding)

**Decision needed:** what does `POST /v1/onboarding` do with the first weekly plan? The frozen docs do not specify the mechanism/timing (WP-8C Reconciliation Report, Phase 3). This document **surfaces** the decision; it does **not** resolve it. Three options, each strictly evidence-consistent:

| Option | Behaviour | Consistent with | Tension with |
|---|---|---|---|
| **1 — Capture-only + separate generation** | Onboarding persists persona/cohort/state and returns persona/confidence/`onboarding_completed`; the first plan is produced by the RE path (nightly CRON LF-L01, or "first app open after gap"), fetched via `GET /v1/plan`. `first_week_plan` in §06.2 is populated only once generated (or returned as a `plan_pending` handle). | DOC-P3-03A §02 (onboarding writes no plan tables); DOC-P3-03 §14 (L01 CRON); DOC-P4-00 §302/§310–322 (plan gen = WP-8E) | DOC-P3-06 §06.2/§14.1 literal synchronous `first_week_plan` |
| **2 — Synchronous first plan** | Onboarding, after LF-A09, invokes the **shared RE service** (DCR-P3-06-007) to generate + persist the first `week_plans`/`plan_slots` within the call, returning the handle. | DOC-P3-06 §06.2/§14.1 (synchronous handle); the OB-08b preview implies an available plan | Requires the RE core (WP-8D) before onboarding ships; crosses the WP-8C→WP-8E ordering in DOC-P4-00 §302; onboarding indirectly triggers plan-table writes |
| **3 — Cohort-only, defer planning** | Onboarding resolves persona/cohort only; taste-vector/plan deferred entirely to later flows. | Minimal WP-8C surface | Weakest fit to DOC-P3-06 §06.2 (`first_week_plan`) and DOC-P3-03 §03 output |

**Recommended (NOT binding until Founder signs): Option 1**, because the preponderance of frozen evidence (DOC-P3-03A §02 R/W matrix, DOC-P3-03 §14 CRON classification, DOC-P4-00 build order) places plan generation *outside* onboarding, and DOC-P3-06 §06.2's response is a *handle* (`week_plan_id` + `week_start_date`), satisfiable by a `plan_pending`/deferred-then-fetched pattern without onboarding owning plan writes. Adopting Option 1 lets **onboarding ship in WP-8C independent of the RE core**, with the first plan delivered by WP-8E. **If the Founder prefers Option 2**, onboarding implementation must wait for WP-8D and a DCR against DOC-P3-06 §06.2 confirming synchronous generation.

**Until AD-01 is ratified, onboarding is NOT implemented** (per the Reconciliation Report Option-B decision).

---

## Section 4 — API Responsibilities (onboarding + consent)

Cites DOC-P3-06 verbatim; adds no field.

- **`POST /v1/consent`** — §06.1; LF-M01; 201 `{recorded[], personalization_granted}`; 4-value `consent_type` CHECK (§03.4); errors `ERR_VALIDATION_FAILED`/`ERR_CONSENT_TYPE_INVALID`/`ERR_UNAUTHENTICATED`/`ERR_OWNERSHIP_MISMATCH` (§21.1). **Implemented, REPO-CERT-011.**
- **`POST /v1/onboarding`** — §06.2; LF-A01–A09; request `answers{OB-01..OB-08}` + `skipped_screens`; response `{profile_id, persona_id, overlay_persona_ids[], confidence_score, cold_start_mode, onboarding_completed, first_week_plan?}` where `first_week_plan` semantics = **AD-01**; ownership `JWT sub == body user_id` (§05); consent-gate: reject with `403 ERR_CONSENT_REQUIRED` if personalization consent not granted (§06.1/§21.1); idempotent per household → `409 ERR_ONBOARDING_ALREADY_COMPLETE` (§08). **Blocked on AD-01.**

---

## Section 5 — Interaction with WP-8D (RE core) and WP-8E (recommendations + plan)

- **WP-8D (RE core)** owns LF-B01–B03, D01–D07, E01–E08, F01–F03, H01–H04, I01–I05 as a shared, versioned module (DOC-P4-00 §14; RE-DOC-01). Onboarding depends on WP-8D **only under AD-01 Option 2**; under Option 1 it does not.
- **WP-8E** owns `POST /v1/recommendations`, `POST /v1/plan/refresh`, and the `_cron/nightly-plan` job (LF-L01) that writes `week_plans`/`plan_slots` via the shared RE core (DCR-P3-06-007). The first week plan is produced here under AD-01 Option 1.
- **Contract at the boundary:** onboarding hands off `{profile_id, persona_id, overlay_persona_ids[], cohort_id (resolved), confidence_score, cold_start_mode}` via `re_engine.user_re_state` (persisted), which WP-8D/8E read (DOC-P3-03A §02; DOC-P3-06 §13). No new inter-service payload is invented — the hand-off is the persisted `user_re_state` row.

---

## Section 6 — Sequencing & Runtime Ownership

| Runtime | Trigger | Host | Writes | Evidence |
|---|---|---|---|---|
| consent | `POST /v1/consent` | Edge Function (sync) | `consent_records` | §06.1; DOC-P3-03A §07 |
| onboarding | `POST /v1/onboarding` | Edge Function (sync) | profiles/household_members/onboarding_sessions/user_re_state/user_taste_vectors | §06.2; DOC-P3-03A §02/§07 |
| first plan | AD-01 | AD-01 (CRON/WP-8E, or shared RE service) | week_plans/plan_slots/addon_slots | DOC-P3-03 §14; AD-01 |
| nightly plan | 23:30 UTC CRON | `_cron/nightly-plan` (WP-8E) | week_plans/plan_slots | DOC-P3-03 §14 LF-L01 |
| derived cols/genome | DB INSERT/UPDATE | DB triggers | dishes derived cols | DOC-P4-00 §15 |

---

## Section 7 — Validation Rules (for onboarding, when built)

- **Structural:** onboarding writes must satisfy all FKs and CHECKs (DOC-P3-04); `persona_id` must reference a valid `re_personas` row (CDM Invariant 13; DOC-P3-03A §09); `confidence_score` within the CHECK range 0.35–1.0 (DOC-P3-03 §03 LF-A08).
- **Behavioural (extend the 90x pattern, DOC-P4-00 §21):** a household completing onboarding yields exactly one `user_re_state` row with a non-null persona; personalization-denied consent blocks onboarding (403); a duplicate onboarding returns 409; OB-08b events are accepted with `onboarding_completed=false` (LF-L04).
- **Data prerequisites already validated:** persona/cohort/state/weekly-plan seed gates pass (905; REPO-CERT-007/010) — onboarding does not need to re-seed them.
- **Auth-fixture gap (carried):** live cross-user + planning-role validations self-SKIP without seeded test profiles (REPO-CERT-010 §7) — add auth fixtures when onboarding lands.

---

## Section 8 — Architectural Decisions Log

| ID | Decision | Status |
|---|---|---|
| **AD-01** | Onboarding first-plan mechanism/timing (Section 3) | **OPEN — Founder sign-off required; gates onboarding** |
| AD-02 | Response envelope: contract-shaped body + additive `trace_id` (`jsonContract`) | Adopted in WP-8C (REPO-CERT-011); DCR-8C-01 |
| AD-03 | 400 (`ERR_VALIDATION_FAILED`) vs 422 (`ERR_CONSENT_TYPE_INVALID`) split per §07/§21 | Adopted in WP-8C; DCR-8C-02 |
| AD-04 | `ip_address_hash` deferred (needs salt secret) | Deferred; DCR-8C-03 |
| AD-05 | Onboarding hand-off to WP-8D/8E via persisted `user_re_state` (no new payload) | Proposed (frozen-consistent); confirm at WP-8D |

---

## Section 9 — Implementation Roadmap

1. **AD-01 ratified by Founder** (blocking).
2. If Option 1: implement `OnboardingService` (LF-A01–A09) + `PersonaRepository`/`CohortRepository` (read-only RE reference reads) + `/v1/onboarding` handler; `first_week_plan` returned as `plan_pending` handle; first plan delivered by WP-8E. **No dependency on WP-8D.**
3. If Option 2: defer onboarding until WP-8D (RE core) exists; raise a DCR against DOC-P3-06 §06.2.
4. Add onboarding behavioural validations (Section 7) + auth fixtures.
5. Proceed to WP-8D (RE core) and WP-8E (recommendations + nightly plan) per DOC-P4-00 §308–322.

---

## Critical Self-Review

- **No invented behaviour:** every service/boundary cites a frozen artifact; the one undecidable item (AD-01) is surfaced as an open decision with three evidence-consistent options and a *recommendation*, not a silent resolution.
- **No frozen doc modified;** no schema/DB/migration/seed/security touched.
- **Honest status:** DRAFT — this document is not authoritative and does not authorize onboarding implementation until AD-01 is ratified.
- **One-source-of-truth:** cites DOC-P3-03/03A/04/06 rather than restating them.

## Versioning & Placement

v1.0 DRAFT, docs/architecture/ beneath the DOC-P4 umbrella (DOC-P4-00 §8). Naming per WP-5AA. On Founder ratification of AD-01, re-issue as `[ACTIVE]_DOC-P4-02_..._v1.1` recording the chosen option.

## Founder Sign-off (ratifies AD-01 and this specification)

Chosen AD-01 option (1 / 2 / 3): ______  Founder: _______________________ Date: ___________
