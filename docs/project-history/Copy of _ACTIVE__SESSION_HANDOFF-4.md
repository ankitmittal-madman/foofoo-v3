# Foofoo — Session Handoff Document
**Date:** June 2026  
**Session type:** Full PM + Engineering Architecture layer  
**Prepared by:** Claude (Sonnet) for APVerse Labs  
**Purpose:** Complete state handoff — any new session or Claude Code agent reads this first

---

## 1. Product in one paragraph

Foofoo is an AI-powered meal decision assistant for Indian households. It solves the daily "aaj kya banaye?" problem. Every morning, the app shows a personalised Breakfast / Lunch / Dinner plan built for the household — accounting for home state, current city, diet type, allergens, household members (infant, elder, diabetic), and cook capability. The user swipes, locks, or swaps. The AI learns. The plan gets better.

**Positioning:** "Zomato solved how to get food. We solve what to eat."  
**Primary persona:** Meera — 32, family meal planner, Mumbai, cooks 3 meals a day.  
**MVP goal:** 500 DAU within 90 days of launch.  
**Budget:** Under ₹25,000 total.

---

## 2. Complete document inventory

### PM Layer (all complete — DRAFT status, pending founder sign-off)

| Doc | Title | Version | Paragraphs | Key content |
|---|---|---|---|---|
| DOC-01 | Product Brief | v1.1 | — | Vision, 4-layer RE science, ₹25K budget, 500 DAU goal |
| DOC-02 | Market Research | v1.0 | — | TAM/SAM/SOM, 5 tailwinds, competitor map, whitespace proof |
| DOC-03 | User Personas | v1.0 | — | 5 personas (Meera P0 → Priya P2b), day-in-the-life, journey maps |
| DOC-04 | PRD | v1.1 | 672 | 59 features F-01–F-59, 13 MVP user stories, NFRs, phasing |
| DOC-05 | Information Architecture | v1.2 | 472 | 35 MVP screens, 5 flows, swipe-reveal gesture, deep links |
| DOC-06 | UI/UX Design System | v1.1 | 560 | Cream/Green/Saffron palette, 11 components, Figma-replaceable |
| DOC-07 | Go-To-Market | v1.0 | 417 | 5-phase GTM, ₹0 MVP launch, persona messaging, ASO strategy |
| DOC-08 | Revenue & Monetisation | v1.0 | 396 | Freemium ₹99/₹149, 3-year projections, unit economics |
| DOC-09 | Legal & Compliance | v1.0 | 282 | DPDP 2023, entity setup, app store compliance, 30-item checklist |

### RE Document Set (all complete)

| Doc | Title | Version |
|---|---|---|
| RE-DOC-01 | Architecture & Module Design | v1.0 |
| RE-DOC-02 | The Four Layers | v1.0 |
| RE-DOC-03 | Meal Class Taxonomy & Scoring | v1.0 |
| RE-DOC-04 | Cold Start, Variety Guard & Suppression | v1.0 |
| RE-DOC-05 | Evolution Roadmap & Testing | v1.0 |

### Supplementary PM (complete, dual format)

| Doc | Title | Formats |
|---|---|---|
| PM-SUPP-01 | Product Roadmap | .docx + .md |
| PM-SUPP-02 | Consolidated Risk Register (30 risks) | .docx + .md |

### Engineering Layer (in progress)

| Doc | Title | Status |
|---|---|---|
| DOC-10 | Technical Architecture | ✅ COMPLETE — 1,076 paragraphs |
| DOC-11 | Database Schema | ⬜ Not started — NEXT |
| DOC-12 | API Contract Specification | ⬜ Not started |
| DOC-13 | Onboarding Answer-to-Feature Mapping | ⬜ Not started |
| DOC-14 | Sprint Plan (execution-plan.md) | ⬜ Not started |
| DOC-15 | QA & Testing Specification | ⬜ Not started |
| DOC-16 | Content & Data Operations Plan | ⬜ Not started |
| DOC-17 | Deployment & Launch Runbook | ⬜ Not started |

### Interactive HTML Visuals (complete)

| File | Companion to | What it shows |
|---|---|---|
| RE-Visual-01_Pipeline_Explorer.html | RE-DOC-01/02 | 4-layer pipeline, weight bar animation |
| RE-Visual-02_ColdStart_Scoring.html | RE-DOC-03/04 | Live scoring simulator, decay chart |
| RE-Visual-03_Evolution_Map.html | RE-DOC-05 | 4-state model, ML upgrade path |
| DOC-06-Visual_Design_System_Explorer.html | DOC-06 | Color swatches, type scale, working gesture demo, phone mockup |

**Total files produced: 24**

---

## 3. Key decisions — with rationale

### Product decisions

**D-001: MVP scope — 6 features deferred to Phase TBD**  
F-24 (Order Instead CTA), F-27 (Grocery list), F-28 (Ingredient check-off), F-46 (Freemium tier visible), F-50 (Referral programme), F-57 (Daily email digest) moved out of MVP.  
*Rationale: Simplify MVP scope. Grocery features consolidated. No monetisation signalling before habit forms. Referral requires freemium to be active first. Email digest adds engineering overhead when PostHog dashboard is sufficient.*  
*Status: Founder to assign exact phases at next planning session.*

**D-002: F-59 My Meals tab added to MVP**  
Replaces Grocery tab in the 5-tab navigation bar.  
*Rationale: Cooking history is genuinely useful in MVP and requires no external integration. Grocery tab required F-27/F-28 which are deferred.*

**D-003: Onboarding updated from prototype analysis**  
OB-00 (conversational intro with stats bubbles — no skip) added.  
OB-03 updated to include migration duration slider (< 1yr / 1–3yr / 3–7yr / 7yr+).  
OB-07 changed from vertical class thumbnail swipe to left/right card swipe with visible ♥/✕ buttons.  
OB-08b (single-day plan preview before Done) added.  
*Rationale: Prototype showed more engaging onboarding pattern. Migration duration feeds RE city overlay weight directly. Left/right card swipe is more intuitive. Plan preview creates aha moment at end of onboarding.*

**D-004: Dish preference pool is Indian-only**  
OB-07 card pool: Idli Sambar, Poha, Aloo Paratha, Rajma Chawal, Masala Dosa, Paneer Butter Masala, Chole Bhature, Dal Makhani, Khichdi, Biryani. No Pizza, no Pasta.  
*Rationale: Foofoo is Indian-first. Western dishes produce RE signals the cohort matrix cannot use meaningfully. Showing Pizza sets wrong product expectation.*

**D-005: Long-press gesture completely removed**  
Long-press + drag for Never / Not Today removed from the entire product.  
Replaced with: swipe left on meal card → reveal Not Today (amber) and Never (red) action buttons.  
Carousel now accessed via tap on swap icon (🔄), not left swipe.  
*Rationale: Long-press is a hidden gesture with no visual affordance. Swipe-reveal is a platform-native pattern (iOS Mail, Gmail, WhatsApp) — users already know it without instructions. Every action now has a visible entry point.*

**D-006: Figma replaceability — DOC-06 is structural, not final visual design**  
When Figma designs are delivered, they supersede: color palette, typography, component aesthetics, imagery, iconography.  
Figma does NOT override: structural wireframes, gesture specification, spacing system (4px base), screen inventory.  
*Rationale: Founder is working on Figma separately. DOC-06 provides engineering defaults and structural authority.*

**D-007: Document format — .docx primary + .md for GitHub**  
All PM documents: .docx  
Supplementary documents (roadmap, risk register): .docx + .md companion  
Going forward: all new documents in both formats.  
*Rationale: .docx for sharing/review. .md for GitHub as source of truth.*

---

### Architecture decisions (locked in DOC-10)

**D-008: React Native + Expo SDK 52+ as the mobile framework**  
Single codebase for iOS + Android. TypeScript strict mode throughout. Expo eliminates native build complexity.  
*ADR-001. Rationale: Best AI coding agent support. No local Xcode/Android Studio needed.*

**D-009: Supabase as the entire backend**  
PostgreSQL + Auth + Edge Functions + Storage. Region: ap-south-1 (Mumbai).  
*ADR-002. Rationale: PostgreSQL mandatory for RE queries. Free tier adequate until 500 DAU. Open-source exit path.*

**D-010: RE implemented as Supabase Edge Functions at MVP**  
Not a separate microservice. RE has its own schema (re_engine) and versioned API endpoints (/v1/recommendations etc.).  
Migration to dedicated microservice planned for Phase 3 if scale demands.  
*ADR-003. Rationale: Zero additional infrastructure. Adjacent to database (low latency). Deno TypeScript.*

**D-011: TanStack Query v5 for server state, MMKV for local persistence**  
MMKV persister on TanStack Query for offline plan caching. Synchronous reads prevent flicker on offline open.  
*ADR-004, ADR-005. Rationale: Purpose-built for server state with offline support. MMKV is 10× faster than AsyncStorage.*

**D-012: Expo Router v3 for navigation**  
File-based routing. Maps directly to DOC-05 screen IDs. Deep linking automatic.  
*ADR-006.*

**D-013: TypeScript strict mode — no exceptions**  
No @ts-ignore. No `any` types.  
*ADR-009. Rationale: Allergen data is safety-critical. A type error in allergen exclusions could surface a dish containing an allergen the user excluded.*

**D-014: All timestamps UTC, IST = UTC+5:30**  
Every DB column is timestamptz. Plan dates computed in IST. Morning cron: 23:30 UTC = 05:00 IST.  
*Rationale: Mishandling produces plans with wrong date for Indian users.*

**D-015: Environment map locked**  
- Feature branches → foofoo-staging (Supabase `kwypxyqxojauhiehuirz`, ap-south-1)  
- apverse-labs-RE branch → foofoo-staging (RE development)  
- main → foofoo-mvp production (Supabase `ufgfznpqixplcbhmsqqw`). **Requires explicit founder approval for any commit/push. Claude Code never commits to main without approval.**

---

### RE architecture decisions (non-negotiable — locked in RE-DOC-01 to RE-DOC-05)

**D-016: Class-first architecture is non-negotiable**  
Pipeline: cohort → meal class plan → dish expansion. Never dish-first. Never cuisine-first.  
No RE logic lives in the React Native app. App talks to RE via /v1/ API contract only.

**D-017: Cohort matrix lives in DB, not hardcoded**  
`re_engine.cohort_matrix` table with weight, source, version columns. Auto-recalibrated weekly.  
New class creation = human decision. New cluster = automated from Phase 2.

**D-018: Three SQL safety gate queries are release blockers**  
Must return 0 rows before any sprint advance or production deploy:  
1. Diet constraint violations  
2. Allergen violations  
3. Jain dish violations  
These run in GitHub Actions CI as automated checks.

**D-019: Annotation columns renamed, never dropped**  
When normalising schema, columns are renamed (e.g., `_FounderInfoOnly`). No column is ever dropped.

---

## 4. Constraints locked in (cannot change without explicit decision)

| # | Constraint | Source |
|---|---|---|
| C-01 | Budget: ₹25,000 total. No paid infrastructure before 500 DAU. | DOC-01 |
| C-02 | MVP free period: 90 days non-negotiable. No paywall before Day 90. | DOC-08 |
| C-03 | Indian-only dish pool in OB-07 preference swipe. | D-004 |
| C-04 | RE safety gate queries must return 0 violations before any release. | RE-DOC-05 |
| C-05 | Claude Code never commits to main or develop without explicit founder approval. | DOC-10 |
| C-06 | Service role key never in client code. Only in Edge Functions. | DOC-10, ADR-009 |
| C-07 | RLS enabled on every Supabase table. No exceptions. | DOC-10 |
| C-08 | TypeScript strict mode. No @ts-ignore. No `any` except where documented. | ADR-009 |
| C-09 | All timestamps stored as UTC timestamptz. Plan dates use IST computation. | DOC-10 |
| C-10 | RE annotation columns renamed, never dropped. | Memories |
| C-11 | No RE logic in React Native app. API contract only. | RE-DOC-01 |
| C-12 | OB-07 dish pool: Indian dishes only. No Western dishes. | D-004 |
| C-13 | Figma visual decisions override DOC-06 when delivered. Structural wireframes remain. | D-006 |
| C-14 | Reference test device for performance: Pixel 3a (4GB RAM, Snapdragon 670, Android 12). | DOC-10 |
| C-15 | ap-south-1 (Mumbai) Supabase region. | DOC-10 |

---

## 5. Assumptions locked in

| # | Assumption |
|---|---|
| A-01 | Supabase free tier handles MVP (500 DAU) without upgrade. Monitor at 70% capacity. |
| A-02 | OneSignal free tier adequate for MVP push notification volume. |
| A-03 | PostHog free tier (1M events/month) sufficient through Phase 1. |
| A-04 | Sentry free tier (5K errors/month) adequate through Phase 1. |
| A-05 | OpenWeatherMap free tier (1K calls/day) sufficient for RE weather context. |
| A-06 | EAS free tier (30 builds/month) sufficient during development. |
| A-07 | RE pipeline executes in < 800ms in Edge Functions (within 3s total plan generation target). |
| A-08 | 500 dishes fully tagged before launch — this is a content gate, not an assumption to relax. |
| A-09 | Foofoo trademark available (Class 42 + 35) — check pending on IP India database. |
| A-10 | Legal entity (Private Limited) can be incorporated before launch. |

---

## 6. Open questions — pending founder decision

| # | Question | Impact | Priority |
|---|---|---|---|
| OQ-01 | Phase assignment for F-24, F-27, F-28, F-46, F-50, F-57 | Roadmap, DOC-04, DOC-05, DOC-07, DOC-08 | High |
| OQ-02 | Figma design delivery timeline | DOC-06 visual decisions remain provisional until then | Medium |
| OQ-03 | Legal entity type — LLP or Private Limited? | DOC-09 entity setup, IP ownership | High |
| OQ-04 | App name — is "Foofoo" final or still working name? | Trademark filing, app store listing | High |
| OQ-05 | Google Drive upload of DOC-10 — confirm success or retry needed | File management | Low |
| OQ-06 | DOC-11 Database Schema — should it include the current RE staging DB state or start fresh? | Engineering scope | High (next doc) |
| OQ-07 | Content operations — who builds the 500-dish database and how? (covered in DOC-16) | Launch readiness | Medium |
| OQ-08 | Migration duration slider in OB-03 — 4-step pill selector confirmed, or continuous slider? | DOC-05, DOC-06 component spec | Low |

---

## 7. Next steps — ordered

### Immediate (next session)

1. **DOC-11 — Database Schema**  
   Every table, column, data type, constraint, index, RLS policy. Two schemas: `public` (app data) and `re_engine` (RE data). Source: DOC-10 Section 05 (backend architecture), RE-DOC-01 to RE-DOC-05.

2. **DOC-12 — API Contract Specification**  
   Every Edge Function endpoint. Request/response shapes. Error formats. Auth requirements. Rate limits.

3. **DOC-13 — Onboarding Answer-to-Feature Mapping**  
   Every OB question → backend field stored → RE impact → confidence score change. Critical for Claude Code to implement onboarding correctly.

4. **DOC-14 — Sprint Plan (execution-plan.md)**  
   14-week build, sprint-by-sprint. This is the `execution-plan.md` file requested at the start. Week-by-week tasks, dependencies, definition of done per sprint.

5. **DOC-15 — QA & Testing Specification**  
   Test types, device matrix, safety gate implementation, acceptance criteria.

6. **DOC-16 — Content & Data Operations Plan**  
   500-dish database build plan, tagging workflow, photo sourcing, quality gates.

7. **DOC-17 — Deployment & Launch Runbook**  
   Environments, CI/CD pipeline, EAS configuration, go-live checklist, rollback plan.

### After engineering documents complete

8. Begin Claude Code build — Sprint 1 (project scaffolding, confirmed via SETUP.sh in project knowledge)
9. Founder phase assignment for Phase TBD features
10. Legal entity incorporation
11. Trademark filing for Foofoo

---

## 8. Claude Code operating rules (must read before every build session)

1. **Never commit or push to `main` or `develop` without explicit founder approval in the conversation.** Hard stop.
2. **Hard stop and report if expected folders/files are not found.** Do not create speculatively.
3. **Run RE safety gate queries after every change to RE-related code.** All three must return 0 rows.
4. **All RE build sessions must reference RE-DOC non-negotiable rules** before writing any code.
5. **Service role key (`SUPABASE_SERVICE_ROLE_KEY`) goes in Edge Functions only.** Never in React Native code. Never in git.
6. **TypeScript strict mode.** Zero type errors before any commit.
7. **All DB migrations are numbered.** Run `supabase db reset` to apply in order.
8. **Annotation columns are renamed, never dropped.** If a column needs to be deprecated, rename it with `_FounderInfoOnly` suffix.
9. **Prompts must be self-contained** — include all context needed for the session because Claude Code sessions lose context.
10. **CLAUDE.md must be updated at the end of every sprint** with current state.

---

## 9. Tech stack — quick reference

| Layer | Technology | Version |
|---|---|---|
| Mobile framework | React Native + Expo | SDK 52+ |
| Language | TypeScript | Strict mode |
| Navigation | Expo Router | v3 |
| Animations / gestures | Reanimated + Gesture Handler | v3 / v2 |
| Server state | TanStack Query | v5 |
| Client state | Zustand | v4 |
| Local storage | MMKV | Latest |
| Backend | Supabase | Latest |
| Database | PostgreSQL | 15 (via Supabase) |
| Edge Functions | Deno TypeScript | Via Supabase |
| Push notifications | OneSignal | Free tier |
| Analytics | PostHog | Free tier |
| Error monitoring | Sentry | Free tier |
| Weather | OpenWeatherMap | Free tier |
| Image CDN | Cloudinary | Free tier |
| Builds | EAS (Expo) | Free tier |
| CI/CD | GitHub Actions | Free tier |

**Repo:** github.com/apverse-labs/foofoo  
**Staging Supabase:** `kwypxyqxojauhiehuirz` (ap-south-1)  
**Production Supabase:** `ufgfznpqixplcbhmsqqw` (ap-south-1)

---

## 10. Critical risk blockers (must resolve before launch)

| Risk ID | Risk | Status |
|---|---|---|
| R-007 | SQL safety gate queries return 0 violations — allergen constraint | Build it — release blocker |
| R-011 | Allergen violation reaches user with severe allergy | Allergen disclaimer in onboarding + safety gate |
| R-018 | App store rejection at submission | Legal review + Apple guidelines check before submission |
| R-006 | Dish database incomplete at launch | Content gate: 500 dishes fully tagged |
| R-027 | Dish content quality insufficient | Pre-launch content audit |

---

*This document was generated at the end of a full PM + Engineering Architecture session. It supersedes any previous session summaries. Next session should begin with DOC-11 Database Schema.*
