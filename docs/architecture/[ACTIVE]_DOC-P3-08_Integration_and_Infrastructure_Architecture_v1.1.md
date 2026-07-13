# [ACTIVE]_DOC-P3-08_Integration_and_Infrastructure_Architecture_v1.1

**Status:** ACTIVE — APPROVED AND FROZEN.
**Version:** v1.1
**Date:** 2026-07-01
**Supersedes:** `[ACTIVE]_DOC-P3-08_Integration_and_Infrastructure_Architecture_v1.0` — governance refinement only, no architecture changes
**Approved By:** Pending confirmation of this session's regression review (Section 41)
**Current Phase:** APDF Phase 3 (Solution Architecture) — this document completes the mandatory Phase 3 document set
**Depends On:**
- `[ACTIVE]_DOC-P3-04_Data_Architecture_ERD_v1.3` (FROZEN)
- `[ACTIVE]_DOC-P3-05_Parts_a-d` (FROZEN)
- `[ACTIVE]_DOC-P3-06_API_Contract_Specification_v1.2` (FROZEN)
- `[ACTIVE]_DOC-P3-07_Security_Architecture_v1.2` (FROZEN)
- `[ACTIVE]_DOC-P3-03A_Logic_Governance_Matrix_v1.0`
- `[ACTIVE]_RE-DOC-01_Architecture_v1.0`

**Fulfills:** APDF Phase 3 Deliverable DOC-P3-08 (Integration & Infrastructure Architecture) per `[ACTIVE]_APDF_Framework_v1`
**Document Authority:** This document consolidates integration and infrastructure architecture. It does not have precedence over any document under Depends On — where a conflict exists, the Project Baseline Register's document-precedence rules apply, and the dependency wins.
**Source Documents Referenced:** all of the above, plus `[ACTIVE]_Project_Baseline_Register_v1.4`, `[ACTIVE]_Engineering_Handover_Project_Continuity_Package_v1.2`, `[ACTIVE]_DOC-P3-05_Architecture_Gap_Register_v1.1`, `[ACTIVE]_DOC-10_Technical_Architecture_v1.0` (partial — see Section 00 and DCR log), `[ACTIVE]_APDF_Framework_v1`, `[ACTIVE]_DOC-P3-08_Readiness_Report_v1.1`
**Downstream Documents Dependent On This Document:** DOC-P4-01, DOC-P4-02, DOC-P5-01/02

**Governance basis (immutable for this session):** DOC-P3-02 through DOC-P3-07 (all frozen), the Project Baseline Register, and the Engineering Handover are treated as authoritative, unmodifiable fact. **This document does not redesign infrastructure, deployment, APIs, security, database architecture, or the Recommendation Engine.** It consolidates and formalizes integration/infrastructure decisions already made — most of them in DOC-10, which predates the frozen Phase 3 documents and was never itself carried into one. Every section states its source, and every genuinely new formalization is classified DCR or AGR, never silently assumed.

---

## Revision Summary — v1.0 → v1.1 (read before the rest of this document)

**Nature of this revision:** governance refinement only, per explicit instruction. **No architecture, schema, API, business logic, security, or Recommendation Engine change is made anywhere in this revision.**

### Exact list of modified sections and why

| Section | What changed | Why |
|---|---|---|
| Header | Version bumped to v1.1; Supersedes updated | Version increment discipline |
| 02 (Architecture Principles), 03 (Integration Principles) | "2 weeks" replaceability language relabeled as an illustrative engineering estimate, not an architectural commitment | Instruction Item 1 |
| 07 (External Integration Inventory) | Every "1 week"/"2 weeks" replacement-strategy figure relabeled as an illustrative estimate; explicit "actual effort depends on implementation context" added | Instruction Item 1 |
| 25 (Timeout Strategy) | Removed the invented "low hundreds of ms" OpenWeatherMap timeout figure; replaced with architectural intent only ("must satisfy the approved API SLA; exact value is a Phase 4 implementation detail") | Instruction Item 3 |
| 29 (Cost & Operational Considerations) | Removed hardcoded "$25/month" Supabase Pro figure; replaced with "Refer to current vendor pricing during implementation and deployment planning" | Instruction Item 2 |
| 30 (Vendor Lock-in Assessment) | "2-week" language relabeled as illustrative estimate throughout | Instruction Item 1 |
| 31 (Scalability Considerations) | Redis, read replica, and "Supabase Pro" relabeled as illustrative future-evolution examples, not commitments | Instruction Item 4 |
| 36 (Risks) | "2-week replaceability bar" wording aligned to "illustrative replaceability estimate" | Consequence of Item 1 |
| 37 (Architecture Decision Log) | ID-P3-08-003 wording aligned to illustrative-estimate framing | Consequence of Item 1 |
| **New: Integration Validation Matrix** | Added | Instruction Item 5 |
| **New: Operational Runbook Summary** | Added | Instruction Item 6 |
| **New: Integration Lifecycle Governance** | Added | Instruction Item 7 |
| 38 (Traceability Matrix) | Extended with rows for the 3 new sections | Consequence of Items 5–7 |
| 40 (DCR/AGR Register) | Extended with DCR-P3-08-004 (governance-refinement classification) | Instruction Item 9 |
| 41 (Regression Review) | Full v1.0→v1.1 regression check added | Instruction Item 8 |
| 42 (Founder Sign-off) | Updated to v1.1, frozen status, statistics updated | Instruction Item 10 |

**Sections NOT modified (confirmed intact, unchanged from v1.0):** 00, 01, 04, 05, 06, 08, 09, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 26, 27, 28, 32, 33, 34, 35, 39. **No section was renumbered. No section was removed. The three new sections were inserted as 39A, 39B, 39C — between the existing Section 39 and Section 40 — specifically so no existing section number changes.**

---

## Section 00 — Pre-Writing Verification (per established project discipline: verify before duplicating)

Before drafting, this check was performed: does DOC-P3-06 v1.2 already own API-contract-facing integration facts? **Yes** — Section 10 (Rate Limiting), Section 23 (Consumer Matrix, including the DCR-007-resolved shared recommendation service). This document references, not restates, those. Does DOC-P3-07 v1.2 already own security-facing integration facts? **Yes** — Sections 14 (Secrets Management, including 14.1 Secret Rotation), 29 (Dependency Security), 30 (Supply Chain Security), 31 (Infrastructure Security) explicitly deferred their operational detail to a future document — **this is that document.** Does DOC-P3-04 already own schema-facing integration facts? **Yes** — `weather_cache` (§03.18) is cited, not redefined. Does DOC-P3-03A already own scheduling facts? **Yes** — §07's execution classification (CRON schedules) is cited, not reinvented.

**DOC-10 status note:** DOC-10 §02 (external services), §10 (CI/CD, environment map, environment variables), §11 (scalability path), and §13 (ADRs) are this document's richest raw material — but DOC-10 predates DOC-P3-04/06/07 and carries the same "known open documentation gap" (G-4, Engineering Handover) on anything touching schema or endpoint naming. Where DOC-10 names a table (`plan_cache`, `cohort_matrix`, `re_class_taxonomy`) or an endpoint (`GET /v1/plan/{user_id}/{week}` as one of "five endpoints") that DOC-P3-04/DOC-P3-06 have since superseded with different names or a different, larger contract, **DOC-P3-04/DOC-P3-06 win, and this is stated as a resolved DCR (Section 40), not silently corrected.** Where DOC-10 describes external services, CI/CD, environment strategy, or cost tiers — territory no frozen Phase 3 document has touched — its content is treated as sound raw material to formalize here, the same relationship DOC-P3-07 had with DOC-10 §06.

---

## Section 01 — Purpose and Scope

**Source:** APDF Framework v1.0 (DOC-P3-08's canonical definition, confirmed in the Readiness Report v1.1 §2)
**Tag:** DOCUMENTED

> Define every third-party integration, external API, and infrastructure service — how they are connected, managed, and what happens when they fail.

This document is **not** a general infrastructure document and **not** a second security document. It covers external dependencies and their operational/failure characteristics — the same discipline DOC-P3-07 applied to security boundaries, applied here to availability, cost, and integration-failure boundaries. It does not redesign anything; where DOC-10 already made a sound decision, this document formalizes it as frozen Phase 3 architecture rather than leaving it in a Phase-1-vintage, partially-superseded document.

**What this document must never do:** propose a new integration not already named somewhere in the approved documents (per the explicit "Do not invent new integrations" instruction); redesign any endpoint, table, security control, or RE algorithm it references.

---

## Section 02 — Architecture Principles

**Source:** DOC-10 §01 (6 principles, reproduced verbatim — this content is not schema/endpoint-naming-specific, so it is not affected by the G-4 gap)
**Tag:** DOCUMENTED

| # | Principle | What it rules out |
|---|---|---|
| 1 | Free tier first — every infrastructure choice runs on free tiers until 500 DAU | Any paid infrastructure decision before that milestone |
| 2 | RE is sovereign — the app talks to RE only via the versioned API contract (now DOC-P3-06 v1.2, superseding DOC-10's own five-endpoint sketch — see Section 40 DCR) | Scoring weights, class codes, or cohort logic anywhere in the app codebase |
| 3 | Offline by default — the user must see today's plan without internet | Architectures requiring live API calls for basic plan display |
| 4 | Security is not an afterthought | Shortcuts like skipping RLS or storing keys in source (now the exact territory DOC-P3-07 formalizes) |
| 5 | Performance is a feature — 60fps gestures, <3s plan generation, <100ms swipe response | Any blocking network call during gesture animations |
| 6 | Build for replacement — every external service must be replaceable within an illustrative timeframe (Section 30 uses "2 weeks" as an engineering estimate, not a commitment) | Proprietary lock-in for core functionality (directly informs Section 30, Vendor Lock-in Assessment) |

**These 6 principles are ranked** — when two valid infrastructure approaches conflict, the lower-numbered principle wins. This ranking is inherited unchanged; this document does not reorder or reweight it.

---

## Section 03 — Integration Principles

**Source:** Synthesized from DOC-10 §01 Principle 6, DOC-P3-06 v1.2 §16 (Contract Stability), DOC-P3-07 §29–31
**Tag:** CONFIRMED (synthesis of existing principles, no new principle invented)

1. **Every integration must have a documented replacement path** (DOC-10 Principle 6). DOC-10's "2 weeks" figure is an illustrative engineering estimate, not an architectural commitment — actual effort depends on implementation context and is not fixed by this document.
2. **Integrations are called server-side wherever they touch a secret** (DOC-P3-07 §14) — client-side SDKs are only used for services whose keys are safe to be public (PostHog, Sentry, OneSignal app ID, Cloudinary cloud name — see Section 09).
3. **An integration going down must degrade the product, never break it** (extends DOC-P3-06 v1.2 §16's Contract Stability principle to third parties: an external outage is exactly the kind of "internal implementation change" that must never alter externally observable behavior beyond an explicit, designed fallback).
4. **No integration may be added without a stated replacement path** — consistent with Principle 6 above, and the reason every row in Section 05 has one.

---

## Section 04 — Infrastructure Principles

**Source:** DOC-10 §01 (Principles 1, 3, 5), §10 (locked environment map), DOC-P3-07 §31
**Tag:** DOCUMENTED

1. **Free tier first, always** (Section 02, Principle 1).
2. **The environment map is locked** — Local development, Staging (`foofoo-staging`), Production (`foofoo-mvp`) — and may not be modified without Founder approval (DOC-10 §10; DOC-P3-07 §31 already stated the same rule; this document adds no new environment).
3. **Production deploys are never automatic** — explicit Founder approval required for every production deploy, and Claude Code must never commit or push to `main`/`develop` without it (DOC-10 §10, carried forward unchanged as a permanent rule, consistent with memory's own "Claude Code discipline" principle).
4. **Database region is fixed at `ap-south-1` (Mumbai)** for latency reasons (DOC-10 §10) — this document does not revisit that choice.

---

## Section 05 — Complete Integration Inventory

**Source:** DOC-10 §02 (external services table) + backend layer table, cross-checked against DOC-P3-04/06/07 for anything superseded
**Tag:** DOCUMENTED (consolidation) — **this is the authoritative, frozen version of DOC-10 §02's table going forward**

| # | Integration | Category | Role |
|---|---|---|---|
| 1 | **Supabase** | Core platform (not a "third party" in the replaceable sense — it is the platform itself) | PostgreSQL, Auth, Edge Functions, Storage |
| 2 | **OpenWeatherMap** | External API | Live weather context for RE scoring (LF-I01–I02) |
| 3 | **OneSignal** | External service | Push notification delivery |
| 4 | **PostHog** | External service | Product analytics |
| 5 | **Sentry** | External service | Error monitoring, crash reporting |
| 6 | **Cloudinary** | External service | CDN + image resizing for dish photos |
| 7 | **EAS (Expo)** | Build infrastructure | Cloud builds, app store submission |
| 8 | **GitHub Actions** | CI/CD infrastructure | Typecheck, lint, tests, safety gates, build triggers |

**No integration beyond these 8 exists anywhere in the approved documents.** Per instruction, none is invented here. (Supabase Storage and Supabase Auth are sub-components of Supabase, not separate integrations — listed as one row consistent with DOC-10's own "Backend layer" framing.)

---

## Section 06 — Internal Component Interaction

**Source:** DOC-10 §03 (System architecture overview), superseded in specifics by DOC-P3-04/06 where they conflict
**Tag:** DOCUMENTED, with DCR-40-001 noted where DOC-10's specifics are superseded

| Component | Talks to | Via | Authoritative contract |
|---|---|---|---|
| Mobile client | Supabase Auth | JWT issuance/refresh | DOC-P3-07 §05 |
| Mobile client | Supabase PostgreSQL (Surface A) | Direct PostgREST + RLS | DOC-P3-06 v1.2 §01.1, §02 |
| Mobile client | RE Edge Functions (Surface B) | HTTPS, `/v1/*` | DOC-P3-06 v1.2 §01.2, full endpoint set §03 |
| Edge Functions | PostgreSQL (both schemas) | `service_role`, bypasses RLS | DOC-P3-07 §10, §13 |
| Edge Functions | OpenWeatherMap | Server-side HTTPS call, cached | DOC-P3-04 §03.18 (`weather_cache`); Section 19 below |
| Scheduled jobs | Shared internal recommendation service | Direct internal call, **not** a network call to `/v1/recommendations` | DOC-P3-06 v1.2 §23 (DCR-P3-06-007, Resolved) |
| Mobile client / Edge Functions | OneSignal, PostHog, Sentry, Cloudinary | SDK (client) or server-side API call (Edge Functions) | Section 09 below |

**DOC-10's five-endpoint sketch (§03) and its `plan_cache`/`cohort_matrix`/`re_class_taxonomy` table names are superseded** by DOC-P3-06 v1.2's actual 10-endpoint contract and DOC-P3-04's actual frozen schema (`week_plans`, `plan_slots`, `re_engine.*`) — see DCR-40-001, Section 40. This table above uses only the current, authoritative names.

---

## Section 07 — External Integration Inventory (full detail per integration)

**Source:** DOC-10 §02, §10 (env vars); rate limits cross-checked against DOC-P3-06 v1.2 §10 and Engineering Handover §7.4 where they overlap (Weather API only)
**Tag:** DOCUMENTED (consolidation)

| Integration | Purpose | Owner | Auth mechanism | Data exchanged | Rate limit (free tier) | Caching | Replacement strategy |
|---|---|---|---|---|---|---|---|
| **Supabase** | DB, Auth, Edge Functions, Storage | Platform (not replaceable in 2 weeks — see Section 30) | Service role key (server), anon key + JWT (client) | Everything | 500MB DB, 1GB storage, 50K MAU, 500K Edge Function invocations/month | N/A (platform) | Self-host (Postgres is open-source) — long-term; the "2 weeks" illustrative estimate used elsewhere in this table does not apply to Supabase, flagged honestly in Section 30 |
| **OpenWeatherMap** | Weather context for RE scoring | Edge Functions (server-side only) | API key, server-side secret | City, date → temp/condition | 1,000 calls/day (60K/month) | `weather_cache`, 12h TTL (DOC-P3-04 §03.18) | WeatherAPI.com or Tomorrow.io, same data structure. *Illustrative estimate: ~2 weeks — actual effort depends on implementation context.* |
| **OneSignal** | Push notification delivery (morning plan reminder) | Client SDK (public app ID) + Edge Functions (server-side scheduling, private REST API key) | App ID (public), REST API key (server secret) | Device tokens, scheduled push payloads | Unlimited devices, basic segmentation | N/A | Direct FCM/APNs. *Illustrative estimate: ~2 weeks — actual effort depends on implementation context.* |
| **PostHog** | Product analytics (DAU, funnels, acceptance rate) | Client SDK (public key) | Public API key | Event names, anonymized user props | 1M events/month | N/A | Mixpanel or Amplitude, data exportable via API. *Illustrative estimate: ~2 weeks — actual effort depends on implementation context.* |
| **Sentry** | Error monitoring, crash reports | Client SDK (public DSN) | Public DSN | Stack traces, device/OS metadata | 5,000 errors/month | N/A | Datadog or self-hosted Glitchtip. *Illustrative estimate: ~2 weeks — actual effort depends on implementation context.* |
| **Cloudinary** | CDN + on-the-fly image resizing for dish photos | Client (public cloud name for URL construction) | Public cloud name; upload happens server-side if ever needed | Dish photo binaries, resize parameters in URL | 25GB bandwidth/month | CDN-native caching | Supabase Storage + Image Transformation. *Illustrative estimate: ~1 week — actual effort depends on implementation context.* |
| **EAS (Expo)** | Cloud builds, app store submission | Build infrastructure, founder-approved trigger only | EAS account auth | Source code, build artifacts | 30 builds/month free | N/A | Local builds via Xcode + Android Studio. *Illustrative estimate: ~1 week — actual effort depends on implementation context.* |
| **GitHub Actions** | CI/CD pipeline | Repo-level, no runtime data exposure | GitHub repo secrets | Source code, test results, build triggers | 2,000 minutes/month free | N/A | GitLab CI or CircleCI. *Illustrative estimate: ~1 week — actual effort depends on implementation context.* |

**Monitoring, alerting, cost, and test-strategy columns** for each integration are covered in Sections 27 (Monitoring), 29 (Cost), and 39 (Validation Checklist) respectively, rather than repeated in this already-wide table — consistent with this document's own consolidation principle (Section 00).

---

## Section 08 — Integration Ownership Matrix

**Source:** Synthesis — no single document previously stated ownership this explicitly
**Tag:** CONFIRMED

| Integration | Architectural owner (this document) | Operational owner (who holds the account/keys) | Consumes secret via |
|---|---|---|---|
| Supabase | This document + DOC-P3-04/06/07 jointly | Founder | Edge Function env secrets (DOC-P3-07 §14) |
| OpenWeatherMap | This document | Founder | Edge Function env secrets |
| OneSignal | This document | Founder | Public: client bundle. Private: Edge Function env secrets |
| PostHog | This document | Founder | Public: client bundle (EAS env) |
| Sentry | This document | Founder | Public: client bundle (EAS env) |
| Cloudinary | This document | Founder | Public: client bundle (EAS env) |
| EAS | This document (CI/CD sections) | Founder | EAS account itself |
| GitHub Actions | This document (CI/CD sections) | Founder | GitHub repo secrets |

**Every operational owner is the Founder at MVP scale** — there is no separate ops team yet. This is stated explicitly so a future session doesn't assume a role that doesn't exist.

---

## Section 09 — Authentication & Authorization per Integration

**Source:** DOC-10 §10 (Environment variables — complete list) + DOC-P3-07 §14 (Secrets Management, authoritative — referenced not restated)
**Tag:** DOCUMENTED

| Variable | Integration | Sensitive? | Where stored |
|---|---|---|---|
| `EXPO_PUBLIC_SUPABASE_URL` | Supabase | No | EAS env + `.env.local` |
| `EXPO_PUBLIC_SUPABASE_ANON_KEY` | Supabase | No (RLS protects data — DOC-P3-07 §11) | EAS env + `.env.local` |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase | **Yes — never in client** (DOC-P3-07 §10) | EAS secrets (server) + `.env.local` (gitignored) |
| `SUPABASE_DB_URL` | Supabase | Yes | EAS secrets |
| `ONESIGNAL_APP_ID` | OneSignal | No | EAS env + `.env.local` |
| `ONESIGNAL_REST_API_KEY` | OneSignal | Yes | EAS secrets |
| `OPENWEATHERMAP_API_KEY` | OpenWeatherMap | Yes | EAS secrets |
| `POSTHOG_API_KEY` | PostHog | No | EAS env + `.env.local` |
| `SENTRY_DSN` | Sentry | No | EAS env + `.env.local` |
| `CLOUDINARY_CLOUD_NAME` | Cloudinary | No | EAS env + `.env.local` |

**Authorization model:** none of these integrations perform *authorization* on FooFoo's behalf — that remains entirely owned by DOC-P3-07 §05/§06 (Supabase Auth + Edge Function ownership checks). Third-party services only authenticate *FooFoo's own server* to *them* (API keys), never a FooFoo user directly.

**What implementation must do:** store every "Yes" row exclusively as an Edge Function/EAS server-side secret, per DOC-P3-07 §14's rotation rule (14.1) — rotatable without code or schema change.
**What implementation must never do:** place any "Yes" row in client-bundle-visible EAS env or `.env.local` outside the gitignored server path.

---

## Section 10 — Data Flow Between Components

**Source:** DOC-10 §03 "Data flow — a morning plan request" (8-step table), reconciled against DOC-P3-06 v1.2's actual contract
**Tag:** DOCUMENTED, reconciled

```
CRON (23:30 UTC / 05:00 IST, per DOC-P3-03A §07 LF-L01)
   |
   v
Shared internal recommendation service (NOT the public /v1/recommendations endpoint — DOC-P3-06 v1.2 §23)
   |  generates plans for active users, writes to week_plans/plan_slots (DOC-P3-04 §03.12-13)
   v
OneSignal scheduled push queued (per user's configured push_notification_time, DOC-P3-04 §03.1)
   |
   v
Mobile client: user taps notification -> GET /v1/plan/{user_id}/{week} (DOC-P3-06 v1.2 §06.5)
   |
   v
Mobile client: user swipes/locks/accepts -> POST /v1/events (DOC-P3-06 v1.2 §06.3)
   |
   v
Edge Function: logs to interaction_events; Never/Not-Today sync sub-path writes to re_engine (DOC-P3-06 v1.2 §06.3)
```

**This supersedes DOC-10 §03's version of the same flow**, which named `plan_cache` and a five-endpoint contract — the flow *shape* is unchanged and correctly anticipated by DOC-10, only the *object names* are updated to the frozen schema/contract (DCR-40-001).

---

## Section 11 — Event Flow Between Components

**Source:** DOC-P3-06 v1.2 §20 (API Event Contract, authoritative — referenced not restated)
**Tag:** DOCUMENTED

DOC-P3-06 v1.2 §20 already fully specifies producer/consumer/payload-ownership for every domain event (`dish_accepted`, `dish_never`, `slate_generated`, `persona_assigned`, `consent_granted`, etc.). This document adds only the **infrastructure-level** events DOC-P3-06 didn't need to cover:

| Infrastructure event | Producer | Consumer | New here? |
|---|---|---|---|
| CI pipeline pass/fail | GitHub Actions | Founder (via GitHub UI/notifications) | Yes — Section 16 |
| Safety-gate query failure in CI | GitHub Actions (running the 3 SQL queries) | Founder — P0 release blocker | Yes — Section 16, 23 |
| RE health check failure (3 consecutive) | Scheduled health poll, every 5 min (DOC-10 §04) | On-call/Founder alert | Yes — Section 27 |
| EAS build completion | EAS | Founder (build notification) | Yes — Section 14 |

---

## Section 12 — Infrastructure Topology

**Source:** DOC-10 §03, §10
**Tag:** DOCUMENTED

```
                    ┌─────────────────────┐
                    │   Mobile Client      │
                    │ (React Native+Expo)  │
                    └──────────┬───────────┘
                               │ HTTPS
              ┌────────────────┼────────────────┐
              v                v                 v
   ┌──────────────────┐ ┌─────────────┐  ┌──────────────┐
   │  Supabase Auth    │ │  Supabase   │  │ RE Edge      │
   │  (JWT issuer)      │ │  PostgREST  │  │ Functions    │
   └──────────────────┘ │  (Surface A) │  │ (Surface B)  │
                          └──────┬──────┘  └──────┬───────┘
                                 │  service_role   │ service_role
                                 v                  v
                          ┌────────────────────────────┐
                          │  PostgreSQL (public +       │
                          │  re_engine schemas)          │
                          │  region: ap-south-1          │
                          └────────────────────────────┘
                                        │
                    ┌───────────────────┼────────────────────┐
                    v                   v                    v
            OpenWeatherMap        OneSignal (server leg)   Cloudinary/PostHog/Sentry
            (Edge Fn only)        (Edge Fn scheduling)      (client SDK, public keys)
```

**Two Supabase projects exist** — `foofoo-mvp` (production) and `foofoo-staging` (staging) — same schema, separate secrets, per the locked environment map (Section 04, Section 15).

---

## Section 13 — Runtime Architecture

**Source:** DOC-10 §02 (Supabase Edge Functions row), §10 (connection pooling)
**Tag:** DOCUMENTED

- **Edge Functions run on Deno runtime**, sub-100ms cold start, colocated with the database for low RE-query latency.
- **Connection pooling via PgBouncer** (Supabase built-in) — required once Edge Functions scale beyond a trivial concurrency level, to prevent connection exhaustion.
- **Edge Function timeout ceiling: 150 seconds** (Supabase platform limit) — the RE pipeline's own target is <800ms/<3s (DOC-P3-06 v1.2 §18.2), so this ceiling is not a binding constraint at MVP, only a documented platform fact.

---

## Section 14 — Deployment Architecture

**Source:** DOC-10 §10 (EAS Build and submit table)
**Tag:** DOCUMENTED

| Profile | Output | When used |
|---|---|---|
| `development` | Dev client APK + IPA | Feature development, daily testing |
| `preview` | Internal distribution build (no store) | QA testing, founder review |
| `production` | App Store + Play Store ready build | Release only — explicit approval required |
| `submit-android` | Google Play upload (Internal → Closed → Production) | After production build approval |
| `submit-ios` | App Store Connect upload (TestFlight → Review → Release) | After production build approval |

**Edge Functions deploy via Supabase CLI**, alongside migrations, following the same numbered-migration discipline as the frozen schema (DOC-P3-05 Part a).

---

## Section 15 — Environment Strategy (Dev/Test/UAT/Prod)

**Source:** DOC-10 §10 (locked environment map, reproduced verbatim per instruction Section 18: "reference P3-07"; also DOC-P3-07 §31)
**Tag:** DOCUMENTED — **this table is locked and may not be modified without Founder approval**

| Environment | Branch | Supabase project | What deploys here | Deploy trigger |
|---|---|---|---|---|
| Local development | Any feature branch | `foofoo-staging` (local Supabase CLI) | Developer's own test builds via Expo Go | Manual (`expo start`) |
| Staging | `apverse-labs-RE` | `foofoo-staging` | RE development, schema changes, integration tests | Push to `apverse-labs-RE` |
| Production | `main` | `foofoo-mvp` | Live app for real users | **Explicit Founder approval required — never auto-deploy** |

**No UAT environment exists separately from Staging at MVP scale** — this is stated plainly rather than invented; a dedicated UAT tier is a Phase 1+ consideration, not an MVP gap.

**What implementation must never do:** modify this map, or have Claude Code (or any agent) commit/push to `main` or `develop` without explicit Founder approval in the conversation (DOC-10 §10, carried forward as a permanent rule).

---

## Section 16 — CI/CD Architecture

**Source:** DOC-10 §10 (GitHub Actions CI pipeline table)
**Tag:** DOCUMENTED

| Step | Trigger | Action | Blocks deploy if fails? |
|---|---|---|---|
| TypeScript typecheck | Every push | `tsc --noEmit`, zero errors | Yes |
| ESLint | Every push | Zero errors | Yes |
| Unit tests | Every push | All must pass | Yes |
| **RE safety gate queries** | Push touching `supabase/` or RE client code | 3 SQL queries against `foofoo-staging`, must return 0 rows each (diet, allergen, Jain violations) | **Yes — P0 release blocker** |
| Secret scan | Every push | `gitleaks` — detects hardcoded keys/passwords/JWTs | Yes |
| Build check | Push to `apverse-labs-RE` or `main` | EAS Build (development profile) | Yes for staging; manual for production |

**This pipeline is the concrete implementation of DOC-P3-07 §34's instruction to "extend the existing behavioral-validation pattern"** to CI — the safety-gate step above is exactly that extension, now formalized as infrastructure rather than left as a DOC-P3-07 forward reference.

---

## Section 17 — Configuration Management

**Source:** DOC-10 §10 (env var table, Section 09 above); DOC-P3-07 §14
**Tag:** DOCUMENTED

- **Non-sensitive config** (public keys, URLs): EAS env + `.env.local` (gitignored, never committed).
- **Sensitive config** (service role key, private API keys): EAS secrets (server) — never appears in any client-reachable configuration surface.
- **No configuration is schema-dependent** — a config change (e.g., rotating an API key) never requires a migration, consistent with DOC-P3-07 §14.1's rotation rule.

---

## Section 18 — Secrets & Environment Variables

**Source:** DOC-P3-07 v1.2 §14, §14.1 (**authoritative — referenced, not restated**, per explicit instruction "reference P3-07")
**Tag:** DOCUMENTED

The complete secrets-management architecture — narrow `service_role` usage, EAS Secrets vs. Supabase Edge Function secrets, the rotation governance rule (rotatable without code/schema change, ops-owned, no frequency specified) — is owned entirely by DOC-P3-07 §14/§14.1. Section 09 above is this document's *inventory* of which variables exist per integration; DOC-P3-07 remains the *policy* owner for how they are protected and rotated. **This document introduces no new secret and no new rotation rule.**

---

## Section 19 — Caching Strategy

**Source:** DOC-P3-04 §03.18 (`weather_cache`, authoritative) + DOC-10 §04 (TanStack Query / MMKV client-side caching)
**Tag:** DOCUMENTED

| Layer | What's cached | TTL | Source |
|---|---|---|---|
| Server-side (`weather_cache` table) | OpenWeatherMap responses, per city/date | 12 hours | DOC-P3-04 §03.18; Engineering Handover §7.4 |
| Client-side (TanStack Query + MMKV persister) | Plan data, dish data | Stale-while-revalidate, offline-persisted | DOC-10 §02 (client layer table) |
| Client-side (offline-by-default, Architecture Principle 3) | Last successfully fetched plan | Until next successful fetch | DOC-10 §01 Principle 3; DOC-P3-06 v1.2 §07 fallback table |

**Only the Weather API has a caching need among the 8 integrations** — no other integration (OneSignal, PostHog, Sentry, Cloudinary, EAS, GitHub Actions) has a caching requirement, since none of them is queried per-recommendation-request the way weather is. This is stated explicitly rather than left ambiguous.

---

## Section 20 — Background Jobs & Scheduling

**Source:** DOC-P3-03A §07 (execution classification, authoritative) cross-checked against DOC-10 §04's Cron jobs table
**Tag:** DOCUMENTED — **DOC-P3-03A is authoritative wherever the two overlap; DOC-10 corroborates without conflict**

| Job | Schedule (UTC) | Source function | Corroborated by DOC-10? |
|---|---|---|---|
| Weekly plan pre-generation | 23:30 UTC (05:00 IST) | LF-L01 `generateWeekPlan` | Yes — DOC-10 §04 "Morning plan pre-generation," same time |
| Learning batch processor | Every 15 minutes | LF-J02–J06 | Not named in DOC-10 — DOC-P3-03A is the sole source |
| Cohort weight recalibration | Sunday 18:00 UTC | LF-J08 | Yes — DOC-10 §04, same time |
| Feature/interaction cleanup | Daily 00:00 UTC | LF-J09 | Yes — DOC-10 §04 "Feature store cleanup," same time |
| Never-list reactivation check | Weekly | LF-G05 | Not named in DOC-10 |
| **RE health check** | Every 5 minutes | **Not a business-logic function — infrastructure-only** | DOC-10 §04 only — **this is genuinely new infrastructure content this document formalizes, not previously owned by any Phase 3 document** |

**All scheduled jobs run under `service_role`, invoking the shared internal recommendation service directly** (DOC-P3-06 v1.2 §23) — never over the public network, consistent with Section 10 above.

---

## Section 21 — Third-Party Dependency Management

**Source:** DOC-P3-07 §29, §30 (**DCRs explicitly deferred to this document — being closed here**)
**Tag:** DOCUMENTED (closes DCR-P3-07-006)

DOC-P3-07 §29 (Dependency Security) and §30 (Supply Chain Security) were both marked `[SCOPE NOTE — non-binding Phase 4 implementation guidance]` because no frozen document addressed them — and §29 explicitly recommended the policy be adopted "in DOC-P4-02," while this document's own Readiness Report (§8.3) recommended DOC-P3-08 instead, as an infrastructure decision rather than a per-service spec decision. **This document adopts the DOC-P3-08 placement** (see Section 22 below for the actual policy) — closing DCR-P3-07-006.

**What implementation must do:** pin dependency versions via lockfiles (already implied by the npm/Expo toolchain, DOC-10 §02); prefer well-maintained packages for anything touching secrets or auth.
**What implementation must never do:** add a third-party SDK with write access to `service_role`-protected resources without a security review (DOC-P3-07 §30, carried forward unchanged).

---

## Section 22 — Dependency Scanning Strategy

**Source:** New policy content, closing DCR-P3-07-006 per Section 21 above
**Tag:** `[CONFIRMED — architectural governance decision, placement resolved]`

**Why this belongs here, not DOC-P4-02:** dependency scanning is a CI/CD pipeline decision (Section 16), not a per-service implementation spec decision — it runs identically regardless of which Edge Function or service is being built, the same reasoning the Readiness Report (§8.3) already gave.

**Policy:** extend the existing GitHub Actions pipeline (Section 16) with an automated dependency vulnerability scan (`npm audit` or Dependabot-equivalent), run on every push, **blocking deploy on any `high` or `critical` advisory** — the same severity bar the pipeline already applies to typecheck/lint/test/safety-gate/secret-scan failures (Section 16).

**What implementation must do:** add this as a seventh CI step, alongside the six in Section 16.
**What implementation must never do:** treat a known-vulnerable dependency as acceptable because it's a dev dependency, without checking whether it runs in any CI/build context that touches secrets (DOC-P3-07 §29, carried forward).

---

## Section 23 — Failure Handling Strategy

**Source:** RE-DOC-01 §05 (fallback/failure table, authoritative — referenced, not restated) + DOC-P3-06 v1.2 §07
**Tag:** DOCUMENTED

The complete RE-specific fallback table (RE response slow/5xx/low-confidence/empty-slate/down/constraint-violation → app behavior) is owned entirely by RE-DOC-01 §05 and reproduced in DOC-P3-06 v1.2 §07 — not restated a third time here. **This document's contribution is the equivalent table for the 7 non-RE integrations**, which no document has stated before:

| Integration down | App/system behavior |
|---|---|
| OpenWeatherMap | `weather_cache` serves last-known value past its 12h TTL rather than blocking (extends Section 19's cache into a fallback); if cache is also empty, RE proceeds without weather context — this is not a hard constraint (RE-DOC-03), so scoring degrades gracefully, it does not fail |
| OneSignal | Morning push simply doesn't send; no user-facing error, since the app's own offline-first plan display (Architecture Principle 3) means the push is a convenience, not a dependency |
| PostHog | Analytics events queue client-side and retry later, or are dropped silently — never blocks any user-facing action |
| Sentry | Errors go unreported for that window; does not affect app function at all |
| Cloudinary | Dish photos fail to load; app shows a placeholder (already implied by `expo-image`'s blurhash placeholder support, DOC-10 §02) |
| EAS | Blocks builds/releases only — zero runtime impact on the live app |
| GitHub Actions | Blocks CI/deploy only — zero runtime impact on the live app |

**Principle applied uniformly:** every non-RE integration's failure is designed to be invisible or near-invisible to the end user — only RE failure (already fully handled by RE-DOC-01 §05) has a user-visible fallback UI state.

---

## Section 24 — Retry Strategy (architecture only)

**Source:** DOC-P3-06 v1.2 §18.4 (authoritative retry/backoff principles, referenced) — extended here to third-party integrations, which §18.4 didn't cover
**Tag:** `[CONFIRMED — architecture-level only, no implementation code]`

| Integration | Retry-safe? | Architectural rule |
|---|---|---|
| OpenWeatherMap | Yes | Retry once on timeout before falling back to cache (Section 23) — idempotent GET, safe to retry |
| OneSignal (scheduling call) | Yes | Retry with backoff; a duplicate schedule call is not harmful (OneSignal dedupes by notification ID) |
| PostHog / Sentry | Yes, client-side | SDK's own built-in retry/queue behavior is sufficient; no custom architecture needed |
| Cloudinary | N/A | Client fetches a URL; standard HTTP client retry behavior applies, nothing FooFoo-specific |

**This section states architecture-level policy only** (which calls are safe to retry and why) — per instruction, it does not specify exponential-backoff code, timers, or implementation detail, which belongs in DOC-P4-02.

---

## Section 25 — Timeout Strategy

**Source:** DOC-P3-06 v1.2 §18.4 (2s client timeout for `/v1/recommendations`, authoritative, referenced) — extended to third parties
**Tag:** DOCUMENTED + `[CONFIRMED for third parties — architectural intent only]`

**Architectural intent, stated once, applying to every row below:** every timeout in this system must be set such that it satisfies the approved API SLA (DOC-P3-06 v1.2 §18.2/§18.4) it sits inside. **Exact millisecond/second values are a Phase 4 implementation detail** — this document fixes the constraint the value must satisfy, not the value itself.

| Call | Timeout | Consequence on timeout |
|---|---|---|
| `/v1/recommendations` (RE, for reference) | 2s (DOC-P3-06 v1.2 §18.4) | Show cached plan |
| OpenWeatherMap (server-side, inside the RE pipeline) | Must be set such that it cannot cause the RE pipeline to exceed its own approved SLA (DOC-P3-06 v1.2 §18.2) — the exact millisecond value is a Phase 4 implementation detail, not fixed by this document | Fall back to cache (Section 19), then to no-weather-context (Section 23) |
| OneSignal / PostHog / Sentry / Cloudinary | Not on any user-facing request path — no timeout budget constraint from the RE pipeline applies | N/A |

**No specific millisecond figure for the OpenWeatherMap server-side timeout is fixed by any frozen document** — this is flagged as a Phase 4 implementation detail (DOC-P4-02), consistent with how DOC-P3-06 v1.2 itself distinguished binding architecture from non-binding implementation numbers (§18's own framing pattern, applied here).

---

## Section 26 — Circuit Breaker Philosophy

**Source:** New synthesis — no document names "circuit breaker" explicitly, but RE-DOC-01 §05's "auto-restart, alert on 3+ consecutive 5xx" and DOC-10 §04's "RE health check... alerts if health check fails 3 consecutive times" are the same pattern under a different name
**Tag:** CONFIRMED (naming an existing pattern, not inventing a new one)

**Philosophy:** a integration that fails repeatedly should stop being called for a cooldown window rather than being retried indefinitely against a dead endpoint — this is exactly what the "3 consecutive failures → alert" pattern already does for RE health, generalized as a principle for every integration in Section 05.

**What implementation must do:** apply the same "N consecutive failures → stop calling, alert" pattern to OpenWeatherMap specifically (the one integration on a user-facing latency path) — falling back to cache (Section 19) rather than retrying a dead API on every single request.
**What implementation must never do:** implement a circuit breaker for OneSignal/PostHog/Sentry/Cloudinary calls that would block or delay any user-facing action — per Section 23, these must fail invisibly, not trigger a visible breaker state.

---

## Section 27 — Integration Monitoring

**Source:** DOC-10 §04 (RE health check), DOC-P3-07 §21 (Observability, authoritative, referenced)
**Tag:** DOCUMENTED

| Integration | Monitored how | Alert threshold |
|---|---|---|
| RE / Supabase Edge Functions | `GET /v1/health` polled every 5 minutes | 3 consecutive failures → alert; down >5 min → page on-call (RE-DOC-01 §05, DOC-10 §04) |
| OpenWeatherMap | Implicit via `weather_cache` staleness (Section 19) | No explicit alert threshold in any document — `[SCOPE NOTE]`, Phase 4 to define |
| OneSignal / PostHog / Sentry / Cloudinary | Vendor-side dashboards only | No FooFoo-side alerting defined — acceptable at MVP scale given Section 23's "failure is invisible" design |
| GitHub Actions / EAS | Build/pipeline failure notifications (native to each platform) | N/A — these block deploy, not runtime |

---

## Section 28 — Observability Across Integrations

**Source:** DOC-P3-07 §21, §22 (authoritative, referenced not restated)
**Tag:** DOCUMENTED

DOC-P3-07 §21–22 already establish `trace_id` correlation, the operational-vs-analytics logging distinction, and the metrics tied to RE endpoints. This document's only addition: **PostHog and Sentry are themselves the observability tooling** for two of the categories DOC-P3-07 §22.2 named (analytics events; error/crash reporting) — they are not additional systems to observe, they are the systems FooFoo observes *through*. No new observability architecture is introduced.

---

## Section 29 — Cost & Operational Considerations (high-level only)

**Source:** DOC-10 §02 (free-tier limits), §11 (scalability path) — **presented here at high level only, per explicit instruction that detailed capacity planning is out of scope**
**Tag:** DOCUMENTED, deliberately non-exhaustive

| Integration | Free tier ceiling | Cost if exceeded |
|---|---|---|
| Supabase | 500MB DB, 1GB storage, 50K MAU, 500K Edge Function invocations/month | Paid tier available beyond free-tier ceiling. Refer to current vendor pricing during implementation and deployment planning — architecture does not freeze commercial pricing. |
| OpenWeatherMap | 1,000 calls/day | Paid tier, low cost, mitigated further by 12h caching |
| OneSignal | Unlimited devices (basic tier) | N/A at MVP scale |
| PostHog | 1M events/month | Usage-based paid tier beyond that |
| Sentry | 5,000 errors/month | Usage-based paid tier beyond that |
| Cloudinary | 25GB bandwidth/month | Usage-based paid tier beyond that |
| EAS | 30 builds/month | Paid tier for higher build volume |
| GitHub Actions | 2,000 minutes/month | Paid tier for higher CI volume |

**All 8 integrations are on free tiers at MVP scale, consistent with Architecture Principle 1.** Detailed capacity planning (exact DAU-to-cost curves, tier-by-tier infrastructure changes) is **explicitly out of scope for this document** per instruction — DOC-10 §11 contains a more detailed scalability-tier table for reference, but that level of projection belongs to operational planning, not Phase 3 architecture, and is not reproduced or endorsed as binding here.

---

## Section 30 — Vendor Lock-in Assessment

**Source:** DOC-10 §01 Principle 6, §02 (replacement paths, already captured per-integration in Section 07)
**Tag:** DOCUMENTED

| Integration | Lock-in risk | Honest assessment |
|---|---|---|
| Supabase | **Medium-high** | PostgreSQL itself is portable (self-hostable), but Auth/Edge Functions/Storage are Supabase-specific; a full migration is realistically longer than the "~2 weeks" illustrative estimate used for other integrations — this is the one integration where that estimate does not apply, and this document states that honestly rather than claiming otherwise |
| OpenWeatherMap, OneSignal, PostHog, Sentry, Cloudinary | **Low** | Each has a stated, credible replacement path with an illustrative 1–2 week engineering estimate (Section 07) — actual effort depends on implementation context |
| EAS | **Low-medium** | Replacement (local builds) is more operationally demanding than a drop-in swap, but is a well-understood, documented path (illustrative estimate ~1 week, Section 07 — actual effort depends on implementation context) |
| GitHub Actions | **Low** | Standard CI/CD migration (illustrative estimate ~1 week — actual effort depends on implementation context) |

**This is a more candid assessment than DOC-10 offered** — DOC-10's Principle 6 states a blanket "2 weeks" illustrative estimate; this document notes Supabase itself is the one exception where that estimate does not apply, since it wasn't previously stated explicitly anywhere. This is flagged as a DCR-level observation (Section 40), not silently smoothed over.

---

## Section 31 — Scalability Considerations

**Source:** DOC-10 §11 (scalability path) — high-level direction only, not detailed capacity planning (Section 29)
**Tag:** DOCUMENTED, directional only

At MVP (100–500 DAU), free tier is sufficient across all 8 integrations (Section 29). Beyond that, DOC-10 §11 sketches a general direction for future evolution — such as a managed Postgres upgrade, a read replica, or an in-memory cache layer (e.g., Redis) for hot RE data — **offered here purely as illustrative future-evolution examples, not architectural commitments.** This document does not commit to any specific technology, figure, or timeline for a future scaling tier. **This document defers detailed scalability planning to a future operational document**, consistent with the "no capacity planning" instruction.

---

## Section 32 — Availability Considerations

**Source:** DOC-P3-07 §18.1 (authoritative honest-target-setting pattern, referenced) + Section 23 above
**Tag:** DOCUMENTED

Consistent with DOC-P3-07 §18.1's own precedent (no formal SLA exists for free-tier infrastructure; an honest internal target is the right instrument, not an invented guarantee), this document does not state uptime numbers for any of the 8 integrations. **Availability is instead handled entirely through Section 23's failure-handling design** — the product is architected so that no single integration's downtime causes a user-facing outage, RE excepted (which already has its own fully-specified fallback chain).

---

## Section 33 — Disaster Recovery Integration Considerations

**Source:** DOC-P3-07 §33 (authoritative, referenced not restated)
**Tag:** DOCUMENTED

DOC-P3-07 §33 already covers disaster recovery for the core database/RE stack. **This document's addition:** none of the 7 non-Supabase integrations hold any data that isn't reconstructable or re-fetchable — OpenWeatherMap data is ephemeral cache, OneSignal/PostHog/Sentry hold their own vendor-side history (not FooFoo's system of record), and Cloudinary's images are transformations of Supabase Storage originals. **No additional disaster-recovery consideration exists beyond what DOC-P3-07 §33 already states for the core stack.**

---

## Section 34 — Operational Constraints

**Source:** DOC-10 §01 Principle 1, §10 (Founder-approval-only production deploys)
**Tag:** DOCUMENTED

1. Free tier first, until 500 DAU (Section 02).
2. Production deploys require explicit Founder approval, every time, no exceptions (Section 15).
3. No dedicated ops team exists at MVP — the Founder is the sole operational owner for every integration (Section 08).
4. The environment map is locked and may not be modified without Founder approval (Section 04, 15).

---

## Section 35 — Assumptions

**Source:** Synthesized, following the same A/B categorization precedent DOC-P3-07 v1.1 established (Architectural vs. Platform assumptions)
**Tag:** CONFIRMED

### A. Architectural Assumptions
| Assumption | Risk if wrong |
|---|---|
| The shared internal recommendation service (DOC-P3-06 v1.2 §23) remains the sole invocation path for scheduled plan generation, never a network call to the public endpoint | Low — already Founder-confirmed (DCR-P3-06-007, Resolved) |
| No integration beyond the 8 listed will be needed before Phase 4 begins | Low-medium — a genuinely new integration would require an AGR/SER against this document |

### B. Platform Assumptions
| Assumption | Risk if wrong |
|---|---|
| All 8 integrations' free-tier terms, as stated in DOC-10 §02/§10 (dated June 2026), remain current | Low-medium — flagged as DCR-40-002 (Section 40), not verified in this session |
| Supabase's stated Edge Function timeout ceiling (150s) and cold-start figure (~100ms) remain accurate | Low |

---

## Section 36 — Risks

**Source:** Synthesized from Sections 21–30 above
**Tag:** CONFIRMED

| Risk | Severity | Mitigation status |
|---|---|---|
| Supabase lock-in exceeds the illustrative replaceability estimate the other 7 integrations meet | Medium | Documented honestly (Section 30), not mitigated — a real, accepted trade-off given Architecture Principle 2 (Supabase's Edge Functions are load-bearing for RE sovereignty itself) |
| DOC-10's free-tier figures may be stale | Low-Medium | DCR-40-002, non-blocking |
| No dependency-scanning process existed until this document | Now mitigated | Closed via Section 22 |
| OpenWeatherMap server-side timeout has no fixed figure | Low | Flagged as Phase 4 implementation detail (Section 25), not a blocking gap |

---

## Section 37 — Architecture Decision Log

**Source:** DOC-10 §13 (9 ADRs, ADR-001 through ADR-009) — reproduced by reference, not restated in full; plus this document's own new decisions
**Tag:** DOCUMENTED (reference) + CONFIRMED (new decisions)

**DOC-10's 9 ADRs (React Native+Expo, Supabase, RE-as-Edge-Functions, TanStack Query, MMKV, Expo Router, FlashList, OneSignal, TypeScript strict mode) are ratified as still valid and are not restated here** — they are stack-selection decisions, not integration/infrastructure decisions this document needs to re-litigate, and none of them touches schema/endpoint naming (the only category DOC-10 has a known gap in).

**New decisions made by this document:**
| ID | Decision |
|---|---|
| ID-P3-08-001 | Dependency scanning is placed in DOC-P3-08/CI pipeline, not DOC-P4-02 (Section 22, closing DCR-P3-07-006) |
| ID-P3-08-002 | Circuit-breaker pattern is named and generalized from the existing RE-health-check precedent (Section 26) — no new mechanism invented, existing pattern formalized |
| ID-P3-08-003 | Supabase is explicitly carved out as the one integration where the illustrative replaceability estimate used elsewhere does not apply (Section 30) — stated honestly rather than smoothed over |

---

## Section 38 — Cross-Document Traceability Matrix

**Source:** Synthesis, following the same pattern as DOC-P3-06 §12–13 and DOC-P3-07 §36
**Tag:** CONFIRMED

| This document's section | Traces to |
|---|---|
| 02 Architecture Principles | DOC-10 §01 |
| 05, 07 Integration Inventory | DOC-10 §02 |
| 09, 18 Secrets | DOC-P3-07 §14, §14.1 |
| 15 Environment Strategy | DOC-10 §10; DOC-P3-07 §31 |
| 16 CI/CD | DOC-10 §10 |
| 19 Caching | DOC-P3-04 §03.18 |
| 20 Scheduling | DOC-P3-03A §07 |
| 21, 22 Dependency/Supply Chain | DOC-P3-07 §29, §30 (DCR-P3-07-006, closed here) |
| 23 Failure Handling (RE) | RE-DOC-01 §05; DOC-P3-06 v1.2 §07 |
| 24, 25 Retry/Timeout | DOC-P3-06 v1.2 §18.4, §18.2 |
| 28 Observability | DOC-P3-07 §21, §22 |
| 33 Disaster Recovery | DOC-P3-07 §33 |
| 37 ADRs | DOC-10 §13 |
| **39A Integration Validation Matrix** `(new)` | Sections 07, 23, 24, 25, 27 (synthesis) |
| **39B Operational Runbook Summary** `(new)` | Sections 23, 26, 27 (synthesis) |
| **39C Integration Lifecycle Governance** `(new)` | DOC-P3-06 v1.2 §16, §17 (extended to integrations) |

---

## Section 39 — Validation Checklist

| Requirement | Status |
|---|---|
| Every integration in Section 05 traces to an existing approved document | ✅ — DOC-10 §02, cross-checked, no invention |
| No new integration introduced | ✅ — confirmed, 8 total, matching instruction's expected list exactly |
| No endpoint, schema, security control, or RE logic redesigned | ✅ — every reference is a citation, not a redefinition |
| Secrets management fully deferred to DOC-P3-07 | ✅ — Section 18 |
| Dependency-scanning placement question (Readiness Report §8.3) resolved | ✅ — Section 22, ID-P3-08-001 |
| DOC-10's superseded table/endpoint names identified and not silently used | ✅ — DCR-40-001 |
| Capacity planning excluded per instruction | ✅ — Section 29, 31 explicitly directional-only |
| Retry/timeout stated at architecture level only, no implementation code | ✅ — Section 24, 25 |

---

## Section 39A — Integration Validation Matrix `(new in v1.1)`

**Source:** New synthesis — consolidates validation intent already implied by Sections 07, 23, 24, 25, 27, but never before assembled as a checklist
**Tag:** CONFIRMED
**Purpose statement (per instruction):** this section becomes the authoritative integration validation checklist for Phase 5. It states *what* must be validated and *how*, not the validation *code* itself.

| Integration | Validation objective | Validation method | Expected behaviour | Failure criteria | Acceptance criteria | Responsible owner | Upstream dependency | Downstream dependency |
|---|---|---|---|---|---|---|---|---|
| Supabase (DB/Auth/Edge Fn) | RLS and `service_role` boundaries hold under real traffic | Two-user impersonation test (extending `903_behavioral_rls_validation.sql` pattern, DOC-P3-07 §34) | No cross-user data access via any surface | Any row from another user's data returned | Zero cross-user leakage across all tested tables | Founder / QA | DOC-P3-04 RLS policies | All app features |
| OpenWeatherMap | Cache-first behavior and graceful fallback on API failure | Simulate API timeout/5xx in staging; inspect `weather_cache` reads | RE proceeds using cache or no-weather-context, never blocks | Recommendation request fails or exceeds SLA due to weather call | RE pipeline completes within its approved SLA regardless of weather API state | Founder / QA | `weather_cache` (DOC-P3-04 §03.18) | RE scoring (LF-I01–I02) |
| OneSignal | Scheduled push fires at configured time; failure is silent to user | Manual test account, configured `push_notification_time`; simulate OneSignal outage | Push delivered on success; no user-facing error on failure | User sees an error state due to OneSignal failure | Zero user-facing errors attributable to OneSignal in any failure scenario | Founder / QA | `profiles.push_notification_time` | None (habit-loop feature only) |
| PostHog | Events captured without blocking UI; consent-gated correctly | Trigger known events; verify consent gate (DOC-P3-06 v1.2 §06.1) blocks capture when `analytics` consent is false | Events appear in PostHog only when consent granted | Event captured despite consent being denied | Zero consent violations across a full test matrix of consent states | Founder / QA | `consent_records` (DOC-P3-04 §03.4) | None |
| Sentry | Crashes/errors captured without leaking sensitive data | Trigger a test error; inspect payload for JWTs/dietary data (DOC-P3-07 §22.1) | Error captured; payload contains no raw JWT or health/dietary field | Sensitive field appears in a Sentry event | Zero sensitive-data leaks across a sample of captured events | Founder / QA | DOC-P3-07 §21 logging discipline | None |
| Cloudinary | Image resize/CDN delivery works; placeholder shows on failure | Simulate Cloudinary outage; inspect client rendering | Blurhash placeholder renders, no broken-image state | Broken image icon or crash on Cloudinary failure | Zero broken-image states across a simulated outage | Founder / QA | Supabase Storage originals | Dish photo display (all screens) |
| EAS | Build profiles produce installable artifacts for both platforms | Run each profile (`development`, `preview`, `production`) at least once before relying on it | Build completes, artifact installs | Build fails or artifact does not install | All 3 profiles produce a working artifact | Founder | Source code, `eas.json` | App distribution |
| GitHub Actions | CI pipeline blocks deploy on any of its 6 (soon 7, Section 22) failure conditions | Deliberately introduce one failure of each type in a test branch | Pipeline blocks deploy for every deliberate failure | Pipeline passes despite a known-planted failure | 100% of planted failures are caught | Founder / QA | Section 16 pipeline definition | All deploys |

---

## Section 39B — Operational Runbook Summary `(new in v1.1)`

**Source:** Synthesis of Sections 23 (Failure Handling), 26 (Circuit Breaker), 27 (Monitoring) into a per-integration operational view
**Tag:** CONFIRMED
**Scope boundary (per instruction):** this is architecture-level guidance only — it describes *what should happen* and *who is responsible*, not a step-by-step operational SOP. A future DOC-P5 or ops document may expand any row below into an actual runbook; this table is not that document.

| Integration | Failure scenario | Expected system behaviour | Automatic recovery | Manual recovery action | Operational owner | Escalation trigger | User impact |
|---|---|---|---|---|---|---|---|
| Supabase / RE | Edge Functions unreachable | Cached plan shown (RE-DOC-01 §05) | Platform auto-restart | Founder investigates via Supabase dashboard | Founder | Down >5 min (RE-DOC-01 §05) | Degraded (stale plan) but not blank |
| OpenWeatherMap | API down or rate-limited | Cache serves stale value past TTL, then no-weather-context (Section 23) | None specified — cache-based degradation is automatic by design | Founder checks API key validity/quota if prolonged | Founder | Not formally defined — `[SCOPE NOTE]`, Phase 4/5 to set a threshold | None (invisible) |
| OneSignal | Push delivery fails | Push simply doesn't send | None | Founder checks OneSignal dashboard/API key | Founder | Not formally defined | None (invisible) |
| PostHog | Analytics ingestion down | Events queue or drop client-side | SDK-native retry/queue | Founder checks PostHog status page | Founder | Not formally defined | None |
| Sentry | Error ingestion down | Errors go unreported for that window | None | Founder checks Sentry status page | Founder | Not formally defined | None |
| Cloudinary | CDN/resize failure | Placeholder image shown | `expo-image` blurhash fallback | Founder checks Cloudinary dashboard | Founder | Not formally defined | Minor (placeholder instead of photo) |
| EAS | Build failure | Build blocked | None | Founder inspects build logs | Founder | Immediate (blocks release) | None (pre-release only) |
| GitHub Actions | CI failure | Deploy blocked | None | Founder inspects CI logs | Founder | Immediate (blocks deploy) | None (pre-release only) |

**Every "not formally defined" escalation trigger above is stated honestly rather than invented** — setting a concrete threshold (e.g., "alert after N cache-stale hours for weather") is Phase 4/5 operational work, not a Phase 3 architecture decision this document is positioned to make.

---

## Section 39C — Integration Lifecycle Governance `(new in v1.1)`

**Source:** New governance synthesis — extends the change-control discipline DOC-P3-06 v1.2 §16/§17 already established for the API contract to integrations generally
**Tag:** CONFIRMED — **governance only, introduces no new architecture**

| Lifecycle stage | Governance rule |
|---|---|
| **Evaluation** | A candidate integration is evaluated against Section 03's Integration Principles (2-week-class replaceability estimate, server-side secret handling, graceful degradation, stated replacement path) before being proposed. |
| **Approval** | Adding any integration beyond the 8 in Section 05 requires an AGR or SER against this document (Section 40) and explicit Founder approval — never a silent addition during implementation. |
| **Integration** | Follows Section 09 (auth/secrets placement) and Section 17 (configuration management) exactly as specified for the 8 existing integrations. |
| **Configuration** | Managed per Section 17/18 — non-sensitive config in EAS env/`.env.local`, sensitive config in EAS/Edge Function secrets, never schema-dependent. |
| **Monitoring** | Follows Section 27's existing per-integration monitoring approach; a newly added integration must have its monitoring approach stated at approval time, not left undefined. |
| **Version upgrades** | An SDK/API version upgrade for an existing integration is not, by itself, an architecture change and does not require an AGR — unless it changes the integration's auth mechanism, data exchanged, or failure behavior, in which case Sections 07/09/23 must be updated via DCR. |
| **Deprecation** | An integration being deprecated must have its replacement (Section 30) actively underway before removal — deprecation is never a reason to skip the replacement-path requirement Section 03 already establishes. |
| **Replacement** | Follows the replacement strategy already stated per-integration in Section 07; executing a replacement is a DCR-level documentation update to this table, not a redesign of this document's structure. |
| **Retirement** | A fully retired integration's row is never deleted from Section 05/07 — it is marked `[RETIRED — see version history]`, consistent with this project's "never delete a row" discipline (Architecture Gap Register's own stated practice). |

**What this section explicitly does not do:** define a new approval workflow tool, a new ticketing system, or any implementation mechanism — it states the governance *rule* at each stage, exactly as the instruction requires ("governance only... must not introduce new architecture").

---

**Governance statement (same discipline as DOC-P3-07 §40):** No DCR or AGR raised in this document modifies or supersedes any ACTIVE frozen architecture document. All open items recorded here are governance records only.

| ID | Type | Status | Summary |
|---|---|---|---|
| **DCR-P3-08-001** | DCR | **Resolved by precedence** | DOC-10 §03's five-endpoint sketch and `plan_cache`/`cohort_matrix`/`re_class_taxonomy` table names are superseded by DOC-P3-06 v1.2's actual 10-endpoint contract and DOC-P3-04's actual frozen schema. This document uses only current names throughout (Section 06, 10). |
| **DCR-P3-08-002** | DCR | **Open, non-blocking** | DOC-10 §02/§10's free-tier figures are dated June 2026 and were not independently re-verified in this session (same caution DOC-P3-07 applied to DOC-10 §06). Recommend a one-time verification before launch. |
| **DCR-P3-08-003** | DCR | **Resolved** | Placement of dependency-scanning policy (DOC-P3-07 §29/30's open question) — resolved to DOC-P3-08/CI, closing DCR-P3-07-006. |
| **DCR-P3-08-004** `(new in v1.1)` | DCR | **Resolved** | This v1.1 revision itself: relabeled illustrative timelines/estimates, removed hardcoded pricing and an invented timeout figure, labeled future-scalability technologies as non-binding examples, and added 3 new governance sections (39A–C) — classified as a governance refinement, not an architecture change, per the explicit instruction and the Section 41 regression review. |
| *(inherited)* AGR-P3-07-001 | AGR | **Open — unrelated to this document** (confirmed in Readiness Report §8.4) | No integration/infrastructure dependency exists in either direction; not re-litigated here. |
| *(inherited)* DCR-P3-06-002, 004, 005, 006, 008; DCR-P3-07-001–005 | DCR | Open/Resolved, unchanged, carried forward | See DOC-P3-06 §25, DOC-P3-07 §40 — not restated here. |

**No new AGR was raised.** Every finding in this document was a consolidation-completeness gap (something no document had yet formalized) or a precedence resolution (DOC-10 vs. a later frozen document) — never a defect in any frozen document's internal correctness.

---

## Section 41 — Regression Review

### v1.0 → v1.1 regression check `(new in v1.1, per instruction Item 8)`

| Check | Result |
|---|---|
| Zero architecture changes | ✅ Confirmed — every edit is a wording/labeling change (illustrative-estimate framing, pricing removal, timeout-intent-only framing, future-evolution labeling) or a new governance section (39A–C); no endpoint, table, security control, or RE logic touched |
| Zero schema changes | ✅ Confirmed — no table, column, or constraint referenced differently than in v1.0 |
| Zero API changes | ✅ Confirmed — DOC-P3-06 v1.2 untouched, not even cited differently |
| Zero business logic changes | ✅ Confirmed — DOC-P3-03/03A citations unchanged |
| Zero security changes | ✅ Confirmed — DOC-P3-07 v1.2 untouched; Section 18 still refers to it exactly, doesn't restate or alter it |
| Zero Recommendation Engine changes | ✅ Confirmed — RE-DOC-01 §05 citation in Section 23 unchanged |
| Zero infrastructure redesign | ✅ Confirmed — Sections 12–17 (topology, runtime, deployment, environment, CI/CD, configuration) are content-identical to v1.0 |
| Only governance clarifications and documentation additions | ✅ Confirmed — every change traces to one of the 10 numbered instruction items; nothing exceeds them |
| Every section modified is listed with justification | ✅ Confirmed — Revision Summary (top of document) lists all 15 touch-points |

### v1.0 baseline regression (carried forward, re-confirmed)

| Check | Result |
|---|---|
| No architecture changed | ✅ Confirmed — zero redesign of infrastructure, deployment, APIs, security, database, or RE (per explicit instruction, and verified section-by-section above) |
| No business logic changed | ✅ Confirmed — Sections 19–20's scheduling content cites DOC-P3-03A exactly, no LF function altered |
| No schema changed | ✅ Confirmed — zero `CREATE`/`ALTER`; `weather_cache` cited, not redefined |
| No API contract changed | ✅ Confirmed — DOC-P3-06 v1.2's 10 endpoints untouched; Section 06/10 only correct DOC-10's stale naming, they don't touch the actual frozen contract |
| No security model changed | ✅ Confirmed — DOC-P3-07 v1.2 untouched; Sections 09, 18, 21 reference it exactly, DCR-P3-07-006 is closed by *placement*, not by altering DOC-P3-07's text |
| No Recommendation Engine logic changed | ✅ Confirmed — RE-DOC-01 §05's fallback table reproduced by reference only (Section 23); no scoring, ranking, or pipeline stage touched |
| No undocumented assumption introduced | ✅ Confirmed — every genuinely new statement is tagged `[CONFIRMED]` and justified; Section 35 explicitly separates architectural from platform assumptions |
| Every new issue classified, not silently resolved | ✅ Confirmed — 3 DCRs raised and classified (Section 40), zero silently patched |

**Overall regression verdict (v1.0): PASS.** This document consolidates 8 upstream/frozen sources into the final mandatory Phase 3 artifact, introduces zero architecture change, and resolves exactly one previously-open placement question (DCR-P3-07-006) while flagging one new non-blocking verification item (DCR-P3-08-002).

### Overall v1.1 verdict

**PASS.** This governance refinement touched 15 locations (header, 8 wording/labeling sections, 3 new sections, plus 3 closing-sections updates), all mapping directly to the 10 numbered instruction items. Zero architecture, schema, API, business logic, security, or Recommendation Engine changes. Zero infrastructure redesign. All new content is governance clarification or documentation addition. No new AGR was raised; one new DCR (DCR-P3-08-004) records this revision itself.

---

## Section 42 — Founder Sign-off

| Field | Value |
|---|---|
| Document | DOC-P3-08 · Integration and Infrastructure Architecture |
| Version | v1.1 |
| Status | **ACTIVE — APPROVED — FROZEN** |
| Supersedes | v1.0 — governance refinement only |
| Integrations covered | 8 of 8 approved integrations — zero invented, zero removed |
| New sections added | 3 — Integration Validation Matrix (39A), Operational Runbook Summary (39B), Integration Lifecycle Governance (39C) |
| DCRs raised (total) | 4 (DCR-P3-08-001 through 004) — 3 resolved, 1 open non-blocking (DCR-P3-08-002) |
| AGRs raised | 0 |
| Architecture/schema/logic/API/security changes made | 0 |
| Closes | DCR-P3-07-006 (dependency-scanning placement, resolved in v1.0, unchanged in v1.1) |
| Regression review result | PASS (Section 41) — v1.0 baseline and v1.0→v1.1 checks both clean |
| **Freeze rule** | No further changes without a future AGR, DCR, SER, IDR, or explicit Founder instruction reopening this document — same standing as DOC-P3-04/05/06/07 |
| Prerequisite for | DOC-P4-01, DOC-P4-02, DOC-P5-01/02 |

### Document Statistics
- 42 numbered sections + 3 lettered sub-sections (39A–C) = 45 total content sections, all present
- 8 integrations fully profiled; Section 39A adds a 9-column validation view; Section 39B adds a 7-column operational view; Section 39C adds a 9-stage lifecycle governance view — all for the same 8 integrations, zero new ones
- 4 DCRs total (1 carried from v1.0's own drafting, 3 more from v1.0's DCR log, plus 1 new in v1.1); 0 AGRs

### Cross-Document Dependency Summary
Unchanged from v1.0: depends on 6 documents (DOC-P3-03A, 04, 05, 06, 07, RE-DOC-01) plus DOC-10 as historical raw material; is itself depended on by DOC-P4-01, DOC-P4-02, DOC-P5-01/02. No circular dependency.

### Regression Summary
PASS across all checks, both v1.0 baseline and v1.0→v1.1 (Section 41). Zero architecture, schema, business logic, API, or security changes at any point across both versions.

### Readiness Assessment

**This document is now ACTIVE — APPROVED — FROZEN.** Per explicit instruction, no further Founder review is requested for this document, and no previous Phase 3 document has been reopened.

---

## Formal Declaration

**APDF Phase 3 (Solution Architecture) is formally complete. All mandatory Phase 3 deliverables are now ACTIVE, APPROVED, and FROZEN. Remaining work (Knowledge Integration / Phase 3.5 and Phase 4 implementation) proceeds from this frozen architectural baseline.**

Founder sign-off: **Approved** — session #033, 2026-07-01
