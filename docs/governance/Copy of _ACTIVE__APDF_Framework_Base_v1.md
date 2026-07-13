# AI-First Product Development Framework (APDF)
**Version:** 1.0  
**Date:** June 2026  
**Purpose:** Complete documentation framework for building large-scale technology products using AI as PM, Architect, and Engineer  
**Design principle:** Every document is a prerequisite for the next. No stage is skipped. Documents are written in plain language. Completeness never sacrifices clarity.

---

## How to read this framework

Each document has a specific job. That job produces outputs that become inputs for the next document. The framework enforces one rule above all others:

> **You cannot design what you have not understood. You cannot build what you have not designed. You cannot test what you have not specified.**

The most common failure in product development — with human or AI teams — is jumping from understanding to building without a complete design stage. This framework prevents that.

---

## Framework overview — 6 phases

| Phase | Name | Question it answers | Documents |
|---|---|---|---|
| **0** | Discovery | Why are we building this? | 4 documents |
| **1** | Product Definition | What exactly are we building? | 4 documents |
| **2** | User Experience | How will people use it? | 3 documents |
| **3** | Solution Architecture | How does it work? | 8 documents |
| **4** | Technical Implementation | How is it built? | 6 documents |
| **5** | Quality and Operations | How do we know it works? | 5 documents |
| **6** | Growth and Evolution | How does it improve? | 3 documents |

**Total: 33 documents across 6 phases**

---

## Phase 0 — Discovery
*Purpose: Establish the problem, the market, and the user before any solution thinking begins.*

### DOC-P0-01: Business Model and Vision

| Field | Detail |
|---|---|
| **Purpose** | Define what the product is, who it serves, how it makes money, and why it will succeed |
| **Why necessary** | Every subsequent decision — features, architecture, technology choices — must serve the business model. Without this, teams optimise for the wrong things. |
| **Sequence** | First document created. No prerequisites. |
| **Prerequisites** | None |
| **Key outputs** | Product vision statement · Target market definition · Revenue model · Competitive positioning · Success definition |
| **Feeds into** | DOC-P0-02 (Market Research validates the vision) · DOC-P1-01 (PRD must serve the business model) |
| **Owner** | Founder / Product Manager |
| **Mandatory** | Yes |
| **Level of detail** | High level. 1–2 pages. No technical content. |
| **Common mistake if skipped** | Teams build impressive technology that solves the wrong problem or serves the wrong customer. The product works but the business fails. |
| **How it evolves** | Revisited when market feedback changes the core value proposition. Usually stable after initial validation. |

---

### DOC-P0-02: Market Research and Competitive Analysis

| Field | Detail |
|---|---|
| **Purpose** | Understand the market size, existing solutions, what competitors do well and where they fail, and where the opportunity is |
| **Why necessary** | Differentiators must be designed deliberately. If you do not know what exists, you cannot know what is genuinely new. |
| **Sequence** | Second |
| **Prerequisites** | DOC-P0-01 (business vision defines what market to research) |
| **Key outputs** | Market size · Competitor map · Feature gap analysis · Positioning opportunity · Pricing benchmarks |
| **Feeds into** | DOC-P0-04 (opportunity defines the problem) · DOC-P1-01 (competitive gaps inform features) |
| **Owner** | Product Manager / Researcher |
| **Mandatory** | Yes |
| **Level of detail** | Medium. Factual. Data-sourced where possible. |
| **Common mistake if skipped** | Building a feature that already exists at a competitor. Pricing incorrectly. Entering a market that is already closed. |
| **How it evolves** | Updated quarterly or when a major competitor launches a new product. |

---

### DOC-P0-03: User Research and Personas

| Field | Detail |
|---|---|
| **Purpose** | Define exactly who the user is — their context, goals, frustrations, behaviours, and constraints — based on research, not assumptions |
| **Why necessary** | Every product decision must serve a real human. Personas make the user visible throughout design and development. Decisions made without a user in mind produce features no one uses. |
| **Sequence** | Third |
| **Prerequisites** | DOC-P0-01 (target market defines which users to research) |
| **Key outputs** | 2–4 named personas with goals, frustrations, context, usage patterns, and priority (P0/P1/P2) |
| **Feeds into** | DOC-P1-01 (PRD must prioritise features by persona) · DOC-P2-01 (user journeys are built per persona) |
| **Owner** | UX Researcher / Product Manager |
| **Mandatory** | Yes |
| **Level of detail** | Medium. Narrative with specific quotes and behaviours, not demographics only. |
| **Common mistake if skipped** | Features are designed for the founder, not the user. The product feels clever but not useful. |
| **How it evolves** | Refined after real user feedback. New personas added as the product expands to new segments. |

---

### DOC-P0-04: Problem Statement and Opportunity Definition

| Field | Detail |
|---|---|
| **Purpose** | State the problem precisely — the gap between what exists and what users need — and why this moment is the right time to solve it |
| **Why necessary** | This is the foundation all features must answer to. Any feature that does not address the stated problem is scope creep by definition. |
| **Sequence** | Fourth |
| **Prerequisites** | DOC-P0-02 (market context) · DOC-P0-03 (user context) |
| **Key outputs** | Problem statement (one paragraph) · Root cause analysis · Why existing solutions fail · Why now |
| **Feeds into** | DOC-P1-01 (PRD features must solve this problem) |
| **Owner** | Product Manager |
| **Mandatory** | Yes |
| **Level of detail** | Concise and precise. Usually 1 page. |
| **Common mistake if skipped** | The product solves a symptom not a cause. Features address visible frustrations while the root problem remains. |
| **How it evolves** | Stable. If this changes significantly, the product direction has pivoted. |

---

## Phase 1 — Product Definition
*Purpose: Define precisely what the product does and does not do, with clear acceptance criteria.*

### DOC-P1-01: Product Requirements Document (PRD)

| Field | Detail |
|---|---|
| **Purpose** | Define every feature of the product — what it does, who it serves, in what priority order, and to what acceptance standard — before any design or engineering begins |
| **Why necessary** | Without a PRD, design and engineering work without a shared definition of done. Scope creep is uncontrollable. There is no way to say a feature is complete. |
| **Sequence** | Fifth |
| **Prerequisites** | All Phase 0 documents |
| **Key outputs** | Feature registry with phases · User stories with acceptance criteria · Out-of-scope list · Success metrics · Non-functional requirements |
| **Feeds into** | DOC-P2-01 (user journeys implement the features) · DOC-P3-02 (business logic must support the features) |
| **Owner** | Product Manager |
| **Mandatory** | Yes |
| **Level of detail** | High. Every feature has an ID, priority, persona, phase, and acceptance criteria. |
| **Common mistake if skipped** | Engineering builds the wrong thing. Features change mid-sprint. There is no agreed definition of done. Launch is delayed indefinitely. |
| **How it evolves** | Versioned when features are added, moved between phases, or removed. Change log maintained. |

---

### DOC-P1-02: User Journey Maps

| Field | Detail |
|---|---|
| **Purpose** | Map the complete experience of each primary persona — every step from first awareness through deep product use — identifying moments of delight and friction |
| **Why necessary** | The PRD defines what features exist. Journey maps define the experience of moving through them. A product can have all the right features and still feel wrong. |
| **Sequence** | Sixth |
| **Prerequisites** | DOC-P0-03 (personas) · DOC-P1-01 (features) |
| **Key outputs** | Per-persona journey maps · Emotional arc · Critical friction points · Moments that drive retention · Moments that cause drop-off |
| **Feeds into** | DOC-P2-01 (screens must support the journey) · DOC-P3-02 (business logic must serve journey moments) |
| **Owner** | UX Designer / Product Manager |
| **Mandatory** | Yes — especially for consumer apps where habit formation is the goal |
| **Level of detail** | Medium. Visual where possible. Annotated with user emotions at each step. |
| **Common mistake if skipped** | Individual screens are designed correctly but the path between screens creates friction. Users drop off at transition points. |
| **How it evolves** | Updated after user testing reveals new friction points or unexpected delight moments. |

---

### DOC-P1-03: Feature Prioritisation and Roadmap

| Field | Detail |
|---|---|
| **Purpose** | Sequence features by value and effort across releases, with clear criteria for what goes into each release and why |
| **Why necessary** | A PRD lists all features. A roadmap decides the order. Without this, everything is priority one and nothing ships. |
| **Sequence** | Seventh |
| **Prerequisites** | DOC-P1-01 (all features defined) |
| **Key outputs** | Release plan with phases · Go/no-go criteria per phase · Dependency map between features · Resource requirements per phase |
| **Feeds into** | All implementation phases (defines what to build first) |
| **Owner** | Product Manager |
| **Mandatory** | Yes |
| **Level of detail** | Medium. Timeline is indicative, not contractual at this stage. |
| **Common mistake if skipped** | Teams work on whatever is most interesting, not what creates most user value. Releases contain random feature sets. Dependencies are discovered too late. |
| **How it evolves** | Updated after each release based on what shipped, what user feedback said, and what business goals shifted. |

---

### DOC-P1-04: Legal, Compliance, and Risk Register

| Field | Detail |
|---|---|
| **Purpose** | Identify all legal obligations, data regulations, risk scenarios, and compliance requirements before any architecture decision is made |
| **Why necessary** | Legal constraints shape architecture. DPDP consent requirements determine database structure. Security obligations determine API design. Discovering these after implementation is expensive. |
| **Sequence** | Eighth — must be created before architecture begins |
| **Prerequisites** | DOC-P0-01 (business model defines what data is used) · DOC-P1-01 (features define what data is collected) |
| **Key outputs** | Data regulations applicable (DPDP, GDPR etc.) · Consent requirements · Data retention rules · Security obligations · Risk register with mitigations |
| **Feeds into** | DOC-P3-04 (database schema must enforce compliance) · DOC-P3-05 (security architecture) · DOC-P4-03 (API must implement consent) |
| **Owner** | Legal / Product Manager |
| **Mandatory** | Yes |
| **Level of detail** | High for legal obligations (precise requirements). Medium for risk register (likelihood and impact). |
| **Common mistake if skipped** | Architecture that cannot comply with regulations without rewrite. User data handled incorrectly. App store rejection. |
| **How it evolves** | Updated when regulations change or new markets are entered. |

---

## Phase 2 — User Experience Design
*Purpose: Define how the product looks, feels, and behaves from the user's perspective.*

### DOC-P2-01: Information Architecture and Screen Inventory

| Field | Detail |
|---|---|
| **Purpose** | Define every screen in the product, how screens are organised, how users navigate between them, and what states each screen has |
| **Why necessary** | Navigation structure is a product decision, not an engineering decision. Getting it wrong after implementation requires rebuilding the app. It also serves as the specification that engineers implement against. |
| **Sequence** | Ninth |
| **Prerequisites** | DOC-P1-01 (features define what screens exist) · DOC-P1-02 (journey maps define the navigation) |
| **Key outputs** | Complete screen hierarchy · Screen IDs · Entry and exit points · Screen states · Navigation model · Deep link structure · Critical user flows |
| **Feeds into** | DOC-P2-02 (wireframes implement each screen) · DOC-P3-02 (business logic must support each state) · DOC-P4-01 (implementation spec per screen) |
| **Owner** | UX Designer / Product Manager |
| **Mandatory** | Yes |
| **Level of detail** | High. Every screen has an ID, all states listed, all entry/exit points defined. No ambiguity. |
| **Common mistake if skipped** | Engineers make navigation decisions. Inconsistencies emerge between screens. States are missed. Users get stuck. |
| **How it evolves** | Updated when new features add screens or navigation is restructured. |

---

### DOC-P2-02: UX Design System and Wireframes

| Field | Detail |
|---|---|
| **Purpose** | Define the visual language, interaction patterns, component library, and wireframes for every screen |
| **Why necessary** | Design decisions made inconsistently across screens create a product that feels broken even when it works. The design system is the single source of truth for all visual and interaction decisions. |
| **Sequence** | Tenth |
| **Prerequisites** | DOC-P2-01 (screens defined) |
| **Key outputs** | Design tokens (colours, typography, spacing) · Component library · Interaction patterns · Wireframes per screen · Gesture specifications |
| **Feeds into** | DOC-P4-01 (frontend implementation uses design system) |
| **Owner** | UX Designer |
| **Mandatory** | Yes |
| **Level of detail** | High for design system. Medium for wireframes (structure and states, not pixel-perfect). |
| **Common mistake if skipped** | Each screen is designed differently. The product looks and feels inconsistent. Small design decisions consume engineering time unnecessarily. |
| **How it evolves** | Figma designs override wireframes when delivered. Design system versioned when new components added. |

---

### DOC-P2-03: Content Strategy and Localisation Plan

| Field | Detail |
|---|---|
| **Purpose** | Define the voice, tone, and language of the product — every label, error message, empty state, onboarding text — and the plan for other languages or regional variants |
| **Why necessary** | For Indian consumer products, content is a differentiator. "Aaj kya banaye?" lands differently than "What would you like to eat today?" Content decisions must be deliberate. |
| **Sequence** | Eleventh |
| **Prerequisites** | DOC-P2-01 (screens define what content is needed) · DOC-P0-03 (personas define the voice) |
| **Key outputs** | Voice and tone guidelines · All UI text strings · Error message library · Empty state messages · Notification copy |
| **Feeds into** | DOC-P4-01 (implementation uses content strings) |
| **Owner** | Product Manager / Content Designer |
| **Mandatory** | Yes for consumer products |
| **Level of detail** | Medium. Every screen's key strings defined. Not every pixel annotated — that comes from Figma. |
| **Common mistake if skipped** | Developers write UI copy. It is generic, inconsistent, and often wrong for the target culture. |
| **How it evolves** | Updated as new features ship. Localisation added when new markets are entered. |

---

## Phase 3 — Solution Architecture
*Purpose: Define completely how the system works — every computation, algorithm, data model, and integration — before any code is written. This is the most commonly skipped and most consequential phase.*

### DOC-P3-01: System Design and Technical Architecture

| Field | Detail |
|---|---|
| **Purpose** | Define the overall technical approach — which technologies, how components connect, how the system scales, how it is deployed — and record the reasoning behind each major technical decision |
| **Why necessary** | Technical decisions made without this document are often irreversible. Choosing the wrong database, the wrong runtime, or the wrong API pattern can require complete rewrites months later. |
| **Sequence** | Twelfth |
| **Prerequisites** | All Phase 0–2 documents · DOC-P1-04 (legal constraints shape tech choices) |
| **Key outputs** | Technology stack with rationale · System component diagram · Deployment architecture · Environment map (dev/staging/production) · Architecture Decision Records (ADRs) for every significant choice |
| **Feeds into** | All subsequent Phase 3 documents (every design must fit this architecture) |
| **Owner** | Solution Architect / Tech Lead |
| **Mandatory** | Yes |
| **Level of detail** | High for decisions (why this technology, not another). Medium for diagrams (component level, not code level). |
| **Common mistake if skipped** | Each component is built by different engineers using different patterns. The system cannot be assembled. Security and scaling are afterthoughts. |
| **How it evolves** | ADRs are added as new decisions are made. Major architecture changes create new versions. |

---

### DOC-P3-02: Conceptual Domain Model

| Field | Detail |
|---|---|
| **Purpose** | Map every real-world concept in the problem domain — not as database tables, but as business concepts — and define how they relate to each other |
| **Why necessary** | This is the bridge between business language and technical language. Without it, engineers model the wrong things. The database ends up with tables that mirror document structure rather than business reality. This document answers: what things exist in this domain? How do they relate? What rules govern them? |
| **Sequence** | Thirteenth — must come before any schema work |
| **Prerequisites** | DOC-P1-01 (defines the business domain) · DOC-P3-01 (defines the technical constraints) |
| **Key outputs** | Entity glossary with precise definitions · Relationship map between entities · Cardinality rules · Business invariants (rules that must always be true) · Lifecycle of each key entity |
| **Feeds into** | DOC-P3-03 (business logic operates on these concepts) · DOC-P3-04 (data model is derived from this) |
| **Owner** | Solution Architect / Data Architect |
| **Mandatory** | Yes — especially for domain-driven products |
| **Level of detail** | High. Every entity defined in plain language. Every relationship rule stated explicitly. |
| **Common mistake if skipped** | The database schema mirrors document structure instead of business reality. Engineers create tables that cannot support the business logic. This is the root cause of most architectural rewrites. |
| **How it evolves** | Updated when the business domain expands (new product areas). Stable within a product area. |

---

### DOC-P3-03: Business Logic and Algorithm Specification ← THE CRITICAL DOCUMENT

| Field | Detail |
|---|---|
| **Purpose** | Define every business rule, decision tree, algorithm, formula, computation, scoring mechanism, threshold, and derived calculation in the system — precisely enough that two different engineers would implement the same logic |
| **Why necessary** | This is the most important and most commonly skipped document in product development. The RE documents describe what the system does. This document defines how each computation works. Without it, engineers make assumptions. Every assumption is a potential bug. For AI-driven products like FooFoo, this document IS the product — the RE is only as good as the specifications of its algorithms. |
| **Sequence** | Fourteenth — must be complete before any schema or API design |
| **Prerequisites** | DOC-P3-01 (technical constraints) · DOC-P3-02 (domain concepts) · DOC-P1-01 (all features requiring logic) |
| **Key outputs** | Complete list of every logical function · Inputs and outputs for each function · Exact formula or decision tree for each computation · All thresholds, weights, and parameters with their values · Configuration strategy (which parameters are in config tables vs hardcoded) · Dependency map between computations (what depends on what) · Fallback rules for every error or missing data case · Event definitions with semantic meaning |
| **Feeds into** | DOC-P3-04 (schema must store everything this logic needs) · DOC-P4-02 (service specifications implement these functions) · DOC-P5-01 (test cases are derived from this document) |
| **Owner** | Solution Architect / Senior Engineer |
| **Mandatory** | Yes — without exception for logic-heavy products |
| **Level of detail** | Maximum. Every formula written out. Every decision tree enumerated. Every parameter value specified. No "to be determined" entries in this document. If a value is unknown, that is a product decision that must be made before this document is complete. |
| **Common mistake if skipped** | Engineers implement their best guess of the algorithm. Different engineers implement the same algorithm differently. Behaviour is undefined at edge cases. The product works in demos and fails in production. For AI-driven products, the algorithm is the entire value — skipping this document means you are building a product without defining what the product does. |
| **How it evolves** | Updated when algorithms are tuned post-launch. Version history critical — every change to a formula must be traceable. |

---

### DOC-P3-04: Data Architecture and Entity Relationship Model

| Field | Detail |
|---|---|
| **Purpose** | Define how all data is organised — what entities exist, their attributes, how they relate, cardinality, and what data is stored vs computed — as a formal model that precedes and informs the database schema |
| **Why necessary** | The ERD is the blueprint the schema is built from. Without a formal data model, the schema is written based on intuition, producing denormalised structures, missing relationships, or tables that cannot support the required computations. |
| **Sequence** | Fifteenth — after business logic, because the data model must support the computations |
| **Prerequisites** | DOC-P3-02 (domain concepts) · DOC-P3-03 (computations define what data is needed) |
| **Key outputs** | Complete ERD with all entities and relationships · Attribute list per entity with data types and constraints · Normalisation decisions with rationale · What is stored vs derived · Data volumes (rough row counts) · Data access patterns (how data is queried) |
| **Feeds into** | DOC-P3-05 (database schema implements this model) · DOC-P3-06 (APIs expose this data) |
| **Owner** | Data Architect |
| **Mandatory** | Yes |
| **Level of detail** | High. Every entity, relationship, and attribute defined. Access patterns documented. Volume estimates included. |
| **Common mistake if skipped** | Schema is designed without understanding access patterns. Indexes are missing. Tables are denormalised for the wrong reasons. Data that needs to be queried together is stored separately. |
| **How it evolves** | Updated when new features require new entities. Major structural changes are migrations. |

---

### DOC-P3-05: Database Schema Specification

| Field | Detail |
|---|---|
| **Purpose** | Define every table, column, type, constraint, index, and policy in the database — derived from the ERD — precisely enough that migration files can be written directly from this document |
| **Why necessary** | The schema is the foundation everything else is built on. Schema mistakes are the most expensive to fix — they require data migrations in production. Getting this right requires having done all prior Phase 3 documents. |
| **Sequence** | Sixteenth — after ERD |
| **Prerequisites** | DOC-P3-04 (ERD) · DOC-P3-03 (business logic defines what columns must support) · DOC-P1-04 (legal defines retention and consent tables) |
| **Key outputs** | Complete table definitions with all columns · Data types and constraints · Primary and foreign keys · Indexes with rationale · Row Level Security policies · Migration file sequence · Seed data requirements · Safety gate queries |
| **Feeds into** | DOC-P4-02 (service specs query these tables) · DOC-P4-03 (API responses come from these tables) |
| **Owner** | Data Architect / Senior Engineer |
| **Mandatory** | Yes |
| **Level of detail** | Maximum. Every column defined. Every constraint stated. Every index justified. No ambiguity. |
| **Common mistake if skipped** | Columns are added reactively as features are built. Constraints are missing. RLS is added late. Production data migrations are required. |
| **How it evolves** | Versioned via numbered migration files. Never modified retroactively — new migrations only. |

---

### DOC-P3-06: API Contract Specification

| Field | Detail |
|---|---|
| **Purpose** | Define every API endpoint — request format, response format, authentication, error codes, rate limits, and versioning — that the system exposes |
| **Why necessary** | The API is the contract between frontend and backend. Without a contract, both sides are built based on assumptions. When they connect, they do not match. The contract also defines what data the app can access and what it cannot, which has security and architecture implications. |
| **Sequence** | Seventeenth |
| **Prerequisites** | DOC-P3-05 (schema defines what data is available) · DOC-P3-03 (business logic defines what computations APIs trigger) |
| **Key outputs** | All endpoints with HTTP method and path · Request schema · Response schema · Authentication requirements · Error codes and messages · Rate limits · Versioning strategy |
| **Feeds into** | DOC-P4-01 (frontend calls these APIs) · DOC-P4-02 (backend implements these contracts) |
| **Owner** | Tech Lead / Backend Engineer |
| **Mandatory** | Yes |
| **Level of detail** | High. Every field in request and response defined. Every error code enumerated. |
| **Common mistake if skipped** | Frontend and backend implement incompatible interfaces. API changes in sprint 3 break frontend built in sprint 1. Versioning is bolted on late. |
| **How it evolves** | Major versions when breaking changes. Minor versions for additions. All changes documented. |

---

### DOC-P3-07: Security Architecture

| Field | Detail |
|---|---|
| **Purpose** | Define how every security concern is addressed — authentication, authorisation, data encryption, secrets management, API security, Row Level Security policies |
| **Why necessary** | Security is not a feature — it is a property of every feature. Adding security after implementation means rewriting every component. For a product handling household dietary data, security failure means user data exposure. |
| **Sequence** | Eighteenth |
| **Prerequisites** | DOC-P3-01 (technical stack) · DOC-P3-05 (schema to define RLS) · DOC-P1-04 (legal requirements) |
| **Key outputs** | Authentication model · Authorisation rules (who can access what) · RLS policy per table · Secrets management approach · Encryption at rest and in transit · API security measures · Vulnerability management approach |
| **Feeds into** | DOC-P3-05 (RLS policies in schema) · DOC-P4-02 (services implement security rules) |
| **Owner** | Security Engineer / Solution Architect |
| **Mandatory** | Yes |
| **Level of detail** | High for rules (precise, no vagueness). Medium for implementation guidance. |
| **Common mistake if skipped** | Every table is readable by every user. API endpoints lack authorisation. Secrets are committed to the repository. Security must be retrofitted. |
| **How it evolves** | Updated when new surfaces are added. Penetration test findings drive updates. |

---

### DOC-P3-08: Integration and Infrastructure Architecture

| Field | Detail |
|---|---|
| **Purpose** | Define every third-party integration, external API, and infrastructure service — how they are connected, managed, and what happens when they fail |
| **Why necessary** | Third-party services introduce failure modes, rate limits, and costs that must be planned for. Discovering that a free-tier API has a 1,000-call-per-day limit after the product launches is a production incident. |
| **Sequence** | Nineteenth |
| **Prerequisites** | DOC-P3-01 (technical stack) · DOC-P1-01 (features define which integrations are needed) |
| **Key outputs** | Integration inventory · Rate limits and free tier constraints · Caching strategy per integration · Fallback behaviour per integration · Cost at scale · CI/CD pipeline design |
| **Feeds into** | DOC-P3-05 (cache tables in schema) · DOC-P4-02 (services must implement caching and fallbacks) |
| **Owner** | Infrastructure Engineer / Tech Lead |
| **Mandatory** | Yes |
| **Level of detail** | Medium. Each integration fully specified. Failure modes documented. |
| **Common mistake if skipped** | API rate limits hit in production. No fallback when a third-party service goes down. Unexpected costs at scale. |
| **How it evolves** | Updated as new integrations are added or existing ones change pricing. |

---

## Phase 4 — Technical Implementation
*Purpose: Define precisely how each component is built, before building it.*

### DOC-P4-01: Frontend Implementation Specification

| Field | Detail |
|---|---|
| **Purpose** | Define every screen's implementation — component structure, state management, data fetching, offline behaviour, and animations — giving engineers a complete specification to build from |
| **Why necessary** | UX wireframes define the design. This document defines the implementation. Without it, engineers make implementation decisions that may contradict design intent or create inconsistency. |
| **Sequence** | Twentieth |
| **Prerequisites** | DOC-P2-01 (screens) · DOC-P2-02 (design system) · DOC-P3-06 (API contracts) |
| **Key outputs** | Component breakdown per screen · State management plan · API calls per screen · Offline cache strategy · Animation and transition specs · Accessibility requirements |
| **Feeds into** | Actual frontend code |
| **Owner** | Frontend Engineer / Tech Lead |
| **Mandatory** | Yes for complex apps |
| **Level of detail** | High. Per-screen specification. No design decisions left to the engineer building it. |
| **Common mistake if skipped** | Each engineer implements screens differently. State management is inconsistent. Offline behaviour is missing. The app feels like it was built by multiple people with no shared vision. |
| **How it evolves** | Updated as new screens are added. Major changes when design system is revised. |

---

### DOC-P4-02: Service and Edge Function Specification

| Field | Detail |
|---|---|
| **Purpose** | Define every backend service or Edge Function — its inputs, outputs, algorithm it implements, database queries it runs, error handling, and performance contract |
| **Why necessary** | This is where the business logic specification (DOC-P3-03) becomes implementation instructions. Without per-function specifications, engineers implement the same algorithm differently, produce inconsistent results, and create bugs that are difficult to trace. |
| **Sequence** | Twenty-first |
| **Prerequisites** | DOC-P3-03 (business logic) · DOC-P3-05 (schema) · DOC-P3-06 (API contracts) |
| **Key outputs** | Per-function specification: purpose · inputs · outputs · algorithm steps in order · database queries · config dependencies · error handling · performance target · unit test cases |
| **Feeds into** | Actual backend code · DOC-P5-02 (test cases derived from these specs) |
| **Owner** | Senior Engineer / Tech Lead |
| **Mandatory** | Yes |
| **Level of detail** | Maximum. The specification is precise enough that two engineers independently would produce the same implementation. |
| **Common mistake if skipped** | Engineers interpret business logic documents differently. The same computation produces different results in different functions. Bugs are introduced at implementation with no specification to validate against. |
| **How it evolves** | Updated when business logic changes. Version history critical. |

---

### DOC-P4-03: Data Seeding and Migration Plan

| Field | Detail |
|---|---|
| **Purpose** | Define the exact sequence, format, and validation rules for populating the database with all reference and seed data before the product can function |
| **Why necessary** | For data-driven products like FooFoo, the product cannot work without its reference data. Seed data is not an afterthought — it is a prerequisite to functionality. Migration order matters because of foreign key dependencies. Missing seed data produces silent failures. |
| **Sequence** | Twenty-second |
| **Prerequisites** | DOC-P3-05 (schema) · DOC-P3-03 (business logic defines what seed data is needed) |
| **Key outputs** | Numbered migration file sequence · Seed data per table with row count validation · Import order (dependency-ordered) · Validation queries to confirm seed data integrity · Rollback plan |
| **Feeds into** | Actual database setup · DOC-P5-01 (test data strategy) |
| **Owner** | Data Engineer / Tech Lead |
| **Mandatory** | Yes for data-driven products |
| **Level of detail** | High. Every migration file specified. Every seed table with expected row count. Validation queries included. |
| **Common mistake if skipped** | Seed data is loaded in wrong order (foreign key errors). Reference data is incomplete. Product appears to work but produces wrong results silently. |
| **How it evolves** | New migrations added for each schema change. Seed data updated when content is added. |

---

### DOC-P4-04: Performance and Scalability Plan

| Field | Detail |
|---|---|
| **Purpose** | Define performance targets for every user-facing operation, how those targets will be achieved, and what changes will be needed at each scale milestone |
| **Why necessary** | Performance is not something to optimise after launch. Architectural decisions must support performance targets from day one. A system that works for 100 users and fails at 10,000 is not a success. |
| **Sequence** | Twenty-third |
| **Prerequisites** | DOC-P3-01 (architecture) · DOC-P3-05 (schema) |
| **Key outputs** | Performance targets per operation · Caching strategy · Query optimisation plan · Indexing strategy · Scale thresholds and what changes at each |
| **Feeds into** | DOC-P3-05 (indexes) · DOC-P4-02 (services must meet performance contracts) |
| **Owner** | Tech Lead / Infrastructure Engineer |
| **Mandatory** | Yes |
| **Level of detail** | Medium. Targets precise, implementation guidance indicative. |
| **Common mistake if skipped** | Database queries are missing indexes. Full table scans run in production. The app becomes unusable at scale. |
| **How it evolves** | Updated at each scale milestone as new bottlenecks are identified. |

---

### DOC-P4-05: Observability and Monitoring Plan

| Field | Detail |
|---|---|
| **Purpose** | Define what is logged, what is monitored, what alerts are triggered, and how the team knows when something is wrong — before launch, not after the first incident |
| **Why necessary** | Without observability, production failures are invisible until users complain. For a recommendation engine, silent quality degradation (plans get worse but no error is thrown) is the most dangerous failure mode. |
| **Sequence** | Twenty-fourth |
| **Prerequisites** | DOC-P3-01 (tech stack) · DOC-P1-01 (success metrics to monitor) |
| **Key outputs** | Log strategy · Error monitoring setup · Performance monitoring · Business metric dashboards · Alert thresholds · On-call runbook |
| **Feeds into** | Actual deployment · DOC-P5-03 (launch readiness) |
| **Owner** | Infrastructure Engineer / Tech Lead |
| **Mandatory** | Yes |
| **Level of detail** | Medium. Monitoring plan detailed. Dashboards defined before built. |
| **Common mistake if skipped** | Production issues are discovered by users, not by the team. RE quality degrades silently. Debugging requires guesswork because nothing is logged. |
| **How it evolves** | Expanded as new failure modes are discovered. |

---

## Phase 5 — Quality and Operations

### DOC-P5-01: Test Strategy and Quality Standards

| Field | Detail |
|---|---|
| **Purpose** | Define what is tested, how it is tested, and the quality bar that must be met before anything is released |
| **Why necessary** | Without a test strategy, testing is reactive and incomplete. Critical paths go untested. The safety gate queries in FooFoo are an example of production-level tests — these must be defined before code is written. |
| **Sequence** | Twenty-fifth |
| **Prerequisites** | DOC-P3-03 (business logic defines what must be tested) · DOC-P4-02 (service specs define unit test cases) |
| **Key outputs** | Test types and coverage targets · Unit test specifications per function · Integration test strategy · Safety gate queries · Performance test criteria · Manual test cases for UX |
| **Feeds into** | Actual test files · DOC-P5-03 (launch readiness requires passing all tests) |
| **Owner** | QA Engineer / Tech Lead |
| **Mandatory** | Yes |
| **Level of detail** | High for unit test specs. Medium for integration. |
| **Common mistake if skipped** | Testing happens at the end. Critical bugs discovered after launch. Safety violations missed until a user reports them. |
| **How it evolves** | New test cases added for every bug found. Coverage targets increase as product matures. |

---

### DOC-P5-02: QA Specification and Test Cases

| Field | Detail |
|---|---|
| **Purpose** | Define every specific test case — the exact input, expected output, and pass/fail criteria — for every business logic function |
| **Why necessary** | The test strategy says what to test. This document says how. Without test cases derived from the business logic specification, engineers test what they think the code does, not what it is supposed to do. |
| **Sequence** | Twenty-sixth |
| **Prerequisites** | DOC-P3-03 (business logic) · DOC-P5-01 (test strategy) |
| **Key outputs** | Test case ID per logical function · Input values · Expected output · Edge cases · Performance criteria per case |
| **Feeds into** | Actual test code |
| **Owner** | QA Engineer |
| **Mandatory** | Yes |
| **Level of detail** | Maximum. Test cases are as precise as the business logic specification. |
| **Common mistake if skipped** | Tests cover happy paths only. Edge cases are untested. Failures are discovered in production. |
| **How it evolves** | Every bug found adds a new test case. |

---

### DOC-P5-03: Deployment and Launch Runbook

| Field | Detail |
|---|---|
| **Purpose** | Define every step required to deploy the product to production, in order, with verification checks and rollback procedures |
| **Why necessary** | Launches fail not because the product is wrong but because the deployment process is underdefined. Runbooks ensure reproducible, safe deployments. |
| **Sequence** | Twenty-seventh |
| **Prerequisites** | DOC-P3-08 (infrastructure) · DOC-P5-01 (tests must pass) |
| **Key outputs** | Pre-launch checklist · Deployment step sequence · Smoke tests post-deploy · Rollback triggers · Communication plan |
| **Feeds into** | Actual deployment |
| **Owner** | DevOps / Tech Lead |
| **Mandatory** | Yes |
| **Level of detail** | High. Step by step. No ambiguity. |
| **Common mistake if skipped** | Launch is chaotic. Steps are done out of order. Rollback is improvised. |
| **How it evolves** | Updated after every deployment with lessons learned. |

---

### DOC-P5-04: Analytics and Metrics Framework

| Field | Detail |
|---|---|
| **Purpose** | Define exactly which metrics are tracked, how they are computed, what the targets are, and how they are used to make product decisions |
| **Why necessary** | Without this, teams collect data but do not know what to do with it. Metrics must be defined before the product launches so the right data is logged from Day 1. |
| **Sequence** | Twenty-eighth |
| **Prerequisites** | DOC-P1-01 (success metrics defined in PRD) · DOC-P4-05 (observability plan) |
| **Key outputs** | North Star metric · Supporting metrics · Dashboard design · Decision rules (if metric X falls below Y, do Z) |
| **Feeds into** | Ongoing product decisions · DOC-P6-01 |
| **Owner** | Product Manager / Data Analyst |
| **Mandatory** | Yes |
| **Level of detail** | Medium. Metrics defined precisely. Dashboards outlined. |
| **Common mistake if skipped** | Teams collect all data but analyse none. Or they optimise for the wrong metric. |
| **How it evolves** | New metrics added as product matures. Targets updated based on learning. |

---

### DOC-P5-05: Incident Management and On-Call Runbook

| Field | Detail |
|---|---|
| **Purpose** | Define how production incidents are detected, classified, responded to, and learned from |
| **Why necessary** | Production incidents are inevitable. How quickly and cleanly they are resolved is what separates good operations from poor ones. |
| **Sequence** | Twenty-ninth |
| **Prerequisites** | DOC-P4-05 (monitoring defines what triggers incidents) |
| **Key outputs** | Incident severity definitions · Response procedures per severity · Escalation paths · Post-incident review template |
| **Feeds into** | Operations |
| **Owner** | Tech Lead / Operations |
| **Mandatory** | Yes |
| **Level of detail** | Medium. Runbook precise. |
| **Common mistake if skipped** | Incidents are chaotic. Same issues recur. No learning captured. |
| **How it evolves** | Every incident review adds to or improves the runbook. |

---

## Phase 6 — Growth and Evolution

### DOC-P6-01: Growth and GTM Strategy

| Field | Detail |
|---|---|
| **Purpose** | Define how users discover the product, how acquisition is driven, and how growth is measured |
| **Why necessary** | A great product with no users fails. GTM must be designed in parallel with the product. |
| **Sequence** | Thirtieth |
| **Prerequisites** | DOC-P0-02 (market) · DOC-P0-03 (personas) · DOC-P1-01 (product) |
| **Key outputs** | Launch channels · Acquisition strategy · Retention strategy · Referral mechanics · Paid vs organic balance |
| **Feeds into** | Marketing execution |
| **Owner** | Product Manager / Growth |
| **Mandatory** | Yes |
| **Level of detail** | Medium. Strategy-level, not campaign-level. |
| **Common mistake if skipped** | Product launches with no users. Acquisition is improvised. |
| **How it evolves** | Updated per launch phase based on what channels work. |

---

### DOC-P6-02: Revenue and Monetisation Strategy

| Field | Detail |
|---|---|
| **Purpose** | Define exactly how the product makes money, at what price points, with what conversion strategy, and what the financial model looks like |
| **Why necessary** | Revenue model shapes product design. Freemium vs subscription vs advertising changes what features are built and how they are prioritised. |
| **Sequence** | Thirty-first |
| **Prerequisites** | DOC-P0-01 (business model) · DOC-P0-02 (market) |
| **Key outputs** | Pricing tiers · Revenue model · Unit economics · Break-even analysis |
| **Feeds into** | DOC-P6-01 (GTM must serve revenue model) |
| **Owner** | Founder / Product Manager |
| **Mandatory** | Yes |
| **Level of detail** | Medium. Financial model precise. Implementation details in PRD. |
| **Common mistake if skipped** | Monetisation is bolted on after product-market fit. Often too late. |
| **How it evolves** | Revised based on actual conversion and retention data. |

---

### DOC-P6-03: Product Evolution and Versioning Roadmap

| Field | Detail |
|---|---|
| **Purpose** | Define how the product evolves after launch — which capabilities are added in which phases, and what the architectural upgrade path looks like |
| **Why necessary** | Products that are not designed to evolve become technical debt. The RE evolution roadmap in FooFoo is an example of this document — it defines the upgrade path from rules to ML before the rules are even built. |
| **Sequence** | Thirty-second (ongoing) |
| **Prerequisites** | All prior documents |
| **Key outputs** | Phase-by-phase capability additions · Architectural upgrade paths · ML model evolution plan · API versioning strategy |
| **Feeds into** | Future iterations of all documents |
| **Owner** | Product Manager / Tech Lead |
| **Mandatory** | Yes |
| **Level of detail** | Medium. Strategic. Specific implementation detail added per phase when ready. |
| **Common mistake if skipped** | The product cannot scale without rewrites. Phase 2 features require Phase 1 architecture to be rebuilt. |
| **How it evolves** | Updated after each major release. |

---

### DOC-P6-04: Session Continuity and Knowledge Management

| Field | Detail |
|---|---|
| **Purpose** | In an AI-first development workflow, define how knowledge is preserved across sessions, how context is handed off between sessions, and how the project remains coherent over time without a fixed team |
| **Why necessary** | This document is unique to the AI-first approach. Unlike a human team where context lives in people's heads, AI has no persistent memory between sessions. Without an explicit knowledge management system, every session starts from scratch and re-discovers the same things. |
| **Sequence** | Thirty-third (created early, maintained continuously) |
| **Prerequisites** | DOC-P0-01 |
| **Key outputs** | Session handoff format · Conversation indexing protocol · Decision log · Open questions register · Document change log · Claude Code discipline rules |
| **Feeds into** | Every session in the project |
| **Owner** | Founder |
| **Mandatory** | Yes — unique to AI-first development |
| **Level of detail** | High. Must be detailed enough that a fresh AI session can pick up without any prior context. |
| **Common mistake if skipped** | Every AI session re-explores the same ground. Decisions are made and then unmade because they are not recorded. The project loses coherence over time. |
| **How it evolves** | Updated after every session. |

---

## FooFoo Current State Assessment

### Document-by-document mapping

| Framework doc | FooFoo equivalent | Status | Completeness |
|---|---|---|---|
| DOC-P0-01 Business Model | DOC-01 Product Brief v1.1 | ✅ Complete | High |
| DOC-P0-02 Market Research | DOC-02 Market Research v1.0 | ✅ Complete | High |
| DOC-P0-03 User Personas | DOC-03 User Personas v1.0 | ✅ Complete | High |
| DOC-P0-04 Problem Statement | Within DOC-01 | ✅ Adequate | Medium |
| DOC-P1-01 PRD | DOC-04 PRD v1.1 | ✅ Complete | High |
| DOC-P1-02 User Journeys | Within DOC-05 (flows only) | ⚠️ Partial | Medium — journey maps proper not produced |
| DOC-P1-03 Roadmap | PM-SUPP-01 Roadmap v1.0 | ✅ Complete | High |
| DOC-P1-04 Legal & Risk | DOC-09 Legal v1.0 + PM-SUPP-02 Risk | ✅ Complete | High |
| DOC-P2-01 Information Architecture | DOC-05 IA v1.2 | ✅ Complete | High |
| DOC-P2-02 Design System | DOC-06 UX Design System v1.1 | ✅ Complete | High |
| DOC-P2-03 Content Strategy | Within DOC-06 partially | ⚠️ Partial | Low — not formally produced |
| DOC-P3-01 System Architecture | DOC-10 Technical Architecture v1.0 | ✅ Complete | High |
| DOC-P3-02 Conceptual Domain Model | ❌ Not produced | ❌ Missing | None |
| DOC-P3-03 Business Logic Specification | RE-DOC-01 to RE-DOC-05 (concept only) | ⚠️ Critical gap | Very Low — RE docs describe concepts, not implementation |
| DOC-P3-04 Data Architecture / ERD | ❌ Not produced | ❌ Missing | None |
| DOC-P3-05 Database Schema | DOC-11 multiple drafts | ⚠️ Premature | Cannot be correct without P3-02, P3-03, P3-04 |
| DOC-P3-06 API Contract Specification | ❌ Not produced | ❌ Missing | None |
| DOC-P3-07 Security Architecture | Within DOC-10 partially | ⚠️ Partial | Medium |
| DOC-P3-08 Integration Architecture | Within DOC-10 partially | ⚠️ Partial | Medium |
| DOC-P4-01 Frontend Spec | ❌ Not produced | ❌ Missing | None |
| DOC-P4-02 Service Specification | ❌ Not produced | ❌ Missing | None |
| DOC-P4-03 Data Seeding Plan | ❌ Not produced | ❌ Missing | None |
| DOC-P4-04 Performance Plan | Within DOC-04 NFRs only | ⚠️ Partial | Low |
| DOC-P4-05 Observability Plan | ❌ Not produced | ❌ Missing | None |
| DOC-P5-01 Test Strategy | ❌ Not produced | ❌ Missing | None |
| DOC-P5-02 QA Specification | ❌ Not produced | ❌ Missing | None |
| DOC-P5-03 Deployment Runbook | ❌ Not produced | ❌ Missing | None |
| DOC-P5-04 Analytics Framework | Within DOC-04 metrics only | ⚠️ Partial | Low |
| DOC-P5-05 Incident Management | ❌ Not produced | ❌ Missing | None |
| DOC-P6-01 GTM Strategy | DOC-07 GTM v1.0 | ✅ Complete | High |
| DOC-P6-02 Revenue Strategy | DOC-08 Revenue v1.0 | ✅ Complete | High |
| DOC-P6-03 Evolution Roadmap | RE-DOC-05 Evolution Roadmap | ✅ Complete for RE | High for RE specifically |
| DOC-P6-04 Session Continuity | SESSION_HANDOFF docs + CLAUDE.md | ✅ Active | High |

---

### Gap risk assessment

| Phase | Documents missing | Risk | Impact |
|---|---|---|---|
| **Phase 2** | Content strategy | Low | Poor copy in app |
| **Phase 3** | Conceptual Domain Model | **Critical** | Schema built on wrong mental model of the domain |
| **Phase 3** | Business Logic Specification | **Critical — P0** | RE cannot be implemented correctly. Every algorithm is a guess. |
| **Phase 3** | Data Architecture / ERD | **Critical** | Schema cannot be correct without this. Current drafts are premature. |
| **Phase 3** | API Contract Specification | **High** | Frontend and backend built on different assumptions |
| **Phase 3** | Schema (correct version) | **High** | Current drafts need complete revision after P3-02, P3-03, P3-04 |
| **Phase 4** | All implementation specs | **High** | Claude Code has no specifications to implement against |
| **Phase 5** | All QA specs | **High** | No way to validate correctness after implementation |

---

### Correct next sequence for FooFoo

These must be completed in order before any code is written.

| Step | Document | Estimated sessions | Blocker if skipped |
|---|---|---|---|
| **1** | DOC-P3-02 Conceptual Domain Model | 1 session | Schema is built on wrong concepts |
| **2** | DOC-P3-03 Business Logic Specification (full) | 2–3 sessions | RE cannot be implemented. This is the largest gap. |
| **3** | DOC-P3-04 Data Architecture and ERD | 1 session | Schema cannot be derived correctly |
| **4** | DOC-P3-05 Database Schema v2.0 (complete rewrite from P3-04) | 1 session | Database is wrong if built now |
| **5** | DOC-P3-06 API Contract Specification | 1 session | Frontend and backend disconnect |
| **6** | DOC-P4-02 Service Specifications | 2 sessions | Claude Code has nothing to implement against |
| **7** | DOC-P4-03 Data Seeding Plan | 1 session | RE cannot run without seed data |
| **8** | DOC-P5-01 Test Strategy and Safety Gates | 1 session | No way to validate correctness |
| **THEN** | Claude Code begins implementation | — | Only after all above are complete |

---

## The fundamental principle this framework enforces

A document at each stage answers a different question. No document can be written before the question it answers has been fully answered by its prerequisites.

The question each phase answers:

- Phase 0: Why?
- Phase 1: What?
- Phase 2: How does it feel?
- Phase 3: How does it work? ← Where most projects fail
- Phase 4: How is it built?
- Phase 5: How do we know it works?
- Phase 6: How does it improve?

Phase 3 is the bridge between understanding (Phase 0–2) and building (Phase 4–5). Skipping Phase 3 means building something without knowing how it works. For a product where the recommendation engine IS the product, this is the entire difference between a product that works and one that does not.

