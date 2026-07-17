# [ACTIVE]_DOC-P4-02_Service_and_Edge_Function_Specifications_v1.1

**Status:** ACTIVE — AD-01 ratified by the Founder as **Option 2 (synchronous first-plan generation)**, 2026-07-16. This document is now authoritative for the onboarding→plan runtime boundary. No further code, schema/DB/migration/seed/security change is made by this document itself — it records the ratified design; implementation proceeds through the normal governance process.
**Version:** v1.1
**Date:** 2026-07-16
**Placement:** docs/architecture/[ACTIVE]_DOC-P4-02_Service_and_Edge_Function_Specifications_v1.1.md
**Supersedes:** `[DRAFT]_DOC-P4-02_Service_and_Edge_Function_Specifications_v1.0.md` (retained unchanged, stamped SUPERSEDED, per `CLAUDE.md`'s never-delete rule). All content below is carried forward from v1.0 unchanged except Section 3 (AD-01 resolution), Section 8 (AD-01 status), Section 9 (roadmap), and this header — no other frozen fact is altered.
**Authored because:** the WP-8C Architectural Reconciliation Report (Phase 5, Option B) proved this artifact is a required-but-absent specification for the onboarding→plan runtime boundary; this revision records the Founder's ratification of the one decision (AD-01) that v1.0 left open.
**Governance basis (frozen, authoritative, NOT redesigned here):** DOC-P3-02 (CDM), DOC-P3-03 v1.0 (Business Logic — LF-A01–A09, B01/B02, C01/C02, L01–L04, M01), DOC-P3-03A v1.0 (Logic Governance & Execution Matrix — §02 R/W matrix, §07 execution classification, §08 auditability), DOC-P3-04 v1.3 (Schema/ERD), DOC-P3-06 v1.2 (API Contract — §04/§05/§06.1/§06.2/§12/§13/§14.1/§21), DOC-P4-00 v1.0 (Backend Foundation Architecture), DOC-09 §03 (DPDP), RE-DOC-01 (RE isolation), SER-001 (city_tier), REPO-CERT-007/010 (Data Gate), `[ACTIVE]_Founder_Decision_Register_v1.0.md` FD-04, `[ACTIVE]_Founder_Ratification_Certificate_2026-07-16_v1.0.md`.

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
[Onboarding Submit] --POST /v1/onboarding (LF-A01..A09 server-side, now including synchronous first-plan generation per AD-01 Option 2)-->
[Onboarding Complete] (profiles.onboarding_completed=true, user_re_state.persona_id set, week_plans/plan_slots row(s) persisted)
        --> [Cold Start Active] (cold_start_mode=true, interaction_count<14)
```

**Determinable now (frozen):** the server-side onboarding call runs LF-A01–A09 synchronously (DOC-P3-03A §07: A01–A09 all "Synchronous", <200ms/step), resolves persona (LF-A09, DB lookup on `re_persona_assignment_rules`, Option-B fallback per §03), computes confidence (LF-A08, §03 formula), and writes `profiles`, `household_members`, `onboarding_sessions`, `re_engine.user_re_state`, `re_engine.user_taste_vectors` (DOC-P3-06 §13; DOC-P3-03A §02). It is idempotent per household — a retry after `onboarding_completed=true` returns `409 ERR_ONBOARDING_ALREADY_COMPLETE` (DOC-P3-06 §06.2/§08/§21.1). **Now also determinable: the first weekly plan is generated within this same call — see Section 3.**

---

## Section 2 — Service / Edge-Function Ownership & Boundaries

| Concern | Owner (this spec) | Evidence |
|---|---|---|
| JWT verification | `_shared/auth/authenticate` middleware | DOC-P3-06 §04; DOC-P4-00 §7; built REPO-CERT-011 |
| Ownership check (JWT `sub` == body `user_id`) | in-function `requireOwnership` | DOC-P3-06 §05/§05.1 |
| Consent capture (LF-M01) | `ConsentService` → `ConsentRepository` → `consent_records` | DOC-P3-03 §15; built REPO-CERT-011 |
| Onboarding orchestration (LF-A01–A09) | `OnboardingService` (new, WP-8C) → repositories | DOC-P3-03 §03; DOC-P3-03A §02 |
| Persona/cohort/state resolution | `OnboardingService` via `PersonaRepository`/`CohortRepository` (read-only on RE reference tables) | DOC-P3-03 §03 LF-A09, §04 LF-B01/B02 |
| First week-plan generation (LF-L01) | **RE core service (WP-8D), invoked synchronously by `OnboardingService` at the end of `POST /v1/onboarding` — per AD-01 Option 2** | DOC-P3-03 §14; DOC-P3-03A §07; DOC-P4-00 §310–322; FD-04 |
| Nightly week-plan generation (LF-L01) | RE core service (WP-8D) invoked by WP-8E CRON, for all subsequent weeks | DOC-P3-03 §14 (CRON); DOC-P3-03A §07 (Scheduled CRON); DOC-P4-00 §310–322 |
| Derived columns / genome vectors | **DB triggers — never written by backend** | DOC-P4-00 §15; CDM Invariant 6; REPO-CERT-010 |

**Hard boundary (frozen, RE-DOC-01 §02; DOC-P4-00 §3):** the RE core reads RE-owned tables and writes only RE-owned plan/log tables; onboarding never writes `week_plans`/`plan_slots` *directly* — it invokes the shared RE core service, which does (DOC-P3-06 §13; DOC-P3-03A §02; unchanged module boundary, only the caller/timing changes under Option 2). Because Edge Functions run as `service_role` (RLS bypassed), **every** ownership check is explicit in code (DOC-P3-06 §01.2/§05).

---

## Section 3 — AD-01 (RATIFIED — Founder sign-off received 2026-07-16)

**Decision:** what does `POST /v1/onboarding` do with the first weekly plan? v1.0 of this document surfaced three evidence-consistent options without resolving the question. The Founder has now ratified **Option 2**.

| Option | Behaviour | Status |
|---|---|---|
| 1 — Capture-only + separate generation | Onboarding persists persona/cohort/state only; first plan produced later by nightly CRON or "first app open after gap." | Not selected. |
| **2 — Synchronous first plan** | **Onboarding, after LF-A09, invokes the shared RE service (DCR-P3-06-007) to generate + persist the first `week_plans`/`plan_slots` within the same call, returning the handle in the response.** | **RATIFIED, 2026-07-16.** |
| 3 — Cohort-only, defer planning | Onboarding resolves persona/cohort only; taste-vector/plan deferred entirely. | Not selected. |

**Ratified rationale:** Option 2 is consistent with DOC-P3-06 §06.2/§14.1's literal synchronous `first_week_plan` handle, and matches the existing product decision at OB-08b — the plan preview is designed as onboarding's "aha moment," which requires a real, already-generated plan to show rather than a `plan_pending` placeholder. See `[ACTIVE]_Founder_Decision_Register_v1.0.md` FD-04 and `[ACTIVE]_Founder_Ratification_Certificate_2026-07-16_v1.0.md`.

**Consequence (per v1.0's own Section 5/Section 9 framing, now resolved):** onboarding implementation depends on WP-8D (RE core) existing before `POST /v1/onboarding` can be completed — the WP-8C→WP-8D ordering noted as a tension in v1.0 is now the accepted sequencing, not an open risk. `OnboardingService` must call the shared RE core service in-process; onboarding indirectly triggers `week_plans`/`plan_slots` writes via that shared service, as anticipated by v1.0's Option 2 description.

**AD-01 is now ratified — onboarding implementation is no longer gated by this decision.** Remaining implementation work is ordinary engineering execution (see Section 9), not further Founder-level ratification.

---

## Section 4 — API Responsibilities (onboarding + consent)

Cites DOC-P3-06 verbatim; adds no field.

- **`POST /v1/consent`** — §06.1; LF-M01; 201 `{recorded[], personalization_granted}`; 4-value `consent_type` CHECK (§03.4); errors `ERR_VALIDATION_FAILED`/`ERR_CONSENT_TYPE_INVALID`/`ERR_UNAUTHENTICATED`/`ERR_OWNERSHIP_MISMATCH` (§21.1). **Implemented, REPO-CERT-011.**
- **`POST /v1/onboarding`** — §06.2; LF-A01–A09; request `answers{OB-01..OB-08}` + `skipped_screens`; response `{profile_id, persona_id, overlay_persona_ids[], confidence_score, cold_start_mode, onboarding_completed, first_week_plan}` where `first_week_plan` is now **always populated synchronously, per AD-01 Option 2** (no longer a `plan_pending` handle); ownership `JWT sub == body user_id` (§05); consent-gate: reject with `403 ERR_CONSENT_REQUIRED` if personalization consent not granted (§06.1/§21.1); idempotent per household → `409 ERR_ONBOARDING_ALREADY_COMPLETE` (§08). **No longer blocked on AD-01; blocked only on ordinary WP-8D/8E build sequencing.**

---

## Section 5 — Interaction with WP-8D (RE core) and WP-8E (recommendations + plan)

- **WP-8D (RE core)** owns LF-B01–B03, D01–D07, E01–E08, F01–F03, H01–H04, I01–I05 as a shared, versioned module (DOC-P4-00 §14; RE-DOC-01). Onboarding depends on WP-8D directly — **AD-01 Option 2 is now ratified**, so this dependency is required, not conditional.
- **WP-8E** owns `POST /v1/recommendations`, `POST /v1/plan/refresh`, and the `_cron/nightly-plan` job (LF-L01) that writes `week_plans`/`plan_slots` via the shared RE core (DCR-P3-06-007), for all weeks after the first. The first week plan is produced synchronously inside onboarding, per AD-01 Option 2.
- **Contract at the boundary:** onboarding hands off `{profile_id, persona_id, overlay_persona_ids[], cohort_id (resolved), confidence_score, cold_start_mode}` via `re_engine.user_re_state` (persisted), which WP-8D/8E read (DOC-P3-03A §02; DOC-P3-06 §13). No new inter-service payload is invented — the hand-off is the persisted `user_re_state` row, plus the in-process synchronous call to the shared RE core service for first-plan generation.

---

## Section 6 — Sequencing & Runtime Ownership

| Runtime | Trigger | Host | Writes | Evidence |
|---|---|---|---|---|
| consent | `POST /v1/consent` | Edge Function (sync) | `consent_records` | §06.1; DOC-P3-03A §07 |
| onboarding + first plan | `POST /v1/onboarding` | Edge Function (sync) | profiles/household_members/onboarding_sessions/user_re_state/user_taste_vectors/week_plans/plan_slots/addon_slots | §06.2; DOC-P3-03A §02/§07; AD-01 Option 2 |
| nightly plan (week 2+) | 23:30 UTC CRON | `_cron/nightly-plan` (WP-8E) | week_plans/plan_slots | DOC-P3-03 §14 LF-L01 |
| derived cols/genome | DB INSERT/UPDATE | DB triggers | dishes derived cols | DOC-P4-00 §15 |

---

## Section 7 — Validation Rules (for onboarding, when built)

- **Structural:** onboarding writes must satisfy all FKs and CHECKs (DOC-P3-04); `persona_id` must reference a valid `re_personas` row (CDM Invariant 13; DOC-P3-03A §09); `confidence_score` within the CHECK range 0.35–1.0 (DOC-P3-03 §03 LF-A08; note the Day-0 clamp at 0.65, FD-03).
- **Behavioural (extend the 90x pattern, DOC-P4-00 §21):** a household completing onboarding yields exactly one `user_re_state` row with a non-null persona and exactly one first-week `week_plans` row; personalization-denied consent blocks onboarding (403); a duplicate onboarding returns 409; OB-08b events are accepted with `onboarding_completed=false` (LF-L04).
- **Data prerequisites already validated:** persona/cohort/state/weekly-plan seed gates pass (905; REPO-CERT-007/010) — onboarding does not need to re-seed them.
- **Auth-fixture gap (carried):** live cross-user + planning-role validations self-SKIP without seeded test profiles (REPO-CERT-010 §7) — add auth fixtures when onboarding lands.

---

## Section 8 — Architectural Decisions Log

| ID | Decision | Status |
|---|---|---|
| **AD-01** | Onboarding first-plan mechanism/timing (Section 3) | **RATIFIED 2026-07-16 — Option 2 (synchronous first plan). See FD-04.** |
| AD-02 | Response envelope: contract-shaped body + additive `trace_id` (`jsonContract`) | Adopted in WP-8C (REPO-CERT-011); DCR-8C-01 |
| AD-03 | 400 (`ERR_VALIDATION_FAILED`) vs 422 (`ERR_CONSENT_TYPE_INVALID`) split per §07/§21 | Adopted in WP-8C; DCR-8C-02 |
| AD-04 | `ip_address_hash` deferred (needs salt secret) | Deferred; DCR-8C-03 |
| AD-05 | Onboarding hand-off to WP-8D/8E via persisted `user_re_state` (no new payload) | Confirmed — unchanged by AD-01's resolution |

---

## Section 9 — Implementation Roadmap

1. **AD-01 ratified by Founder as Option 2 (done, 2026-07-16).**
2. Implement `OnboardingService` (LF-A01–A09) + `PersonaRepository`/`CohortRepository` (read-only RE reference reads) + `/v1/onboarding` handler, invoking the shared RE core service synchronously for first-plan generation before responding. **Requires WP-8D (RE core) to exist first** — the WP-8C→WP-8D ordering is now mandatory, not optional.
3. Add onboarding behavioural validations (Section 7) + auth fixtures.
4. Proceed to WP-8E (recommendations + nightly plan for week 2+) per DOC-P4-00 §308–322.

---

## Critical Self-Review

- **No invented behaviour beyond the ratification itself:** every service/boundary still cites a frozen artifact; AD-01's resolution is stated as exactly what the Founder ratified (Option 2), not elaborated with new mechanism detail beyond what v1.0 already described for Option 2.
- **No frozen doc modified beyond this artifact;** no schema/DB/migration/seed/security touched by this document.
- **Honest status:** ACTIVE — ratified 2026-07-16; v1.0 (DRAFT) is retained, stamped SUPERSEDED, not deleted.
- **One-source-of-truth:** cites DOC-P3-03/03A/04/06 rather than restating them; carries v1.0's content forward unchanged except where AD-01's resolution required an update.

## Versioning & Placement

v1.1 ACTIVE, docs/architecture/ beneath the DOC-P4 umbrella (DOC-P4-00 §8). Naming per WP-5AA. Supersedes v1.0 DRAFT (retained, stamped, not deleted, per `CLAUDE.md`).

## Founder Sign-off (ratifies AD-01 and this specification)

Chosen AD-01 option: **2 (synchronous first plan)**  Founder: Ankit Mittal  Date: 2026-07-16
