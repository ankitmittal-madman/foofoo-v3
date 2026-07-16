# [ACTIVE]_WP-K01_Decision_Log_v1.0

**Status:** ACTIVE — Decision Log.
**Version:** v1.0
**Date:** 2026-07-15
**Placement:** docs/project-history/[ACTIVE]_WP-K01_Decision_Log_v1.0.md
**Attests to:** [ACTIVE]_WP-K01_Knowledge_Platform_Refactoring_v1.0.md
**Dependencies:** none modified; references the same sources as the WP-K01 report.

---

## Purpose

Records *why* each of the 14 new Operating System pages exists, and the structural decisions made while rebuilding KNOWLEDGE.html — separate from the *what changed* record (Repository Impact Report) and the *is it real* record (REPO-CERT-016).

## Decisions

| ID | Decision | Reasoning |
|---|---|---|
| **D-01** | Add an Operating System layer instead of continuing the append-only session diary. | The book had decayed exactly where it lacked a living layer — cumulative registers stopped updating at S2/S10 while the timeline kept growing. An operating system needs pages that are *replaced*, not *appended to*. |
| **D-02** | Executive Dashboard becomes the default page, not the latest session. | The WP-K01 mandate is "Founder understands the project in under 5 minutes." A session block answers "what happened", not "where are we" — the two questions need different pages, and the second is what a cold-open reader needs first. |
| **D-03** | Preserve every historical session block verbatim; treat rewriting history as the worst failure mode. | Standing project discipline (CLAUDE.md: never fabricate execution or rewrite history) and explicit WP-K01 instruction ("complete historical traceability"). Enforced mechanically: the rebuild script asserts single-occurrence string matches before any insertion, so it aborts rather than silently touching preserved text. |
| **D-04** | Each dashboard links to its authoritative document/certificate instead of restating facts. | The WP-K01 brief explicitly forbids duplicated truth. A dashboard that copies a number (e.g. "802 dishes") without a citation will drift the next time the source changes; a link can't drift. |
| **D-05** | Completion percentages are labelled "engineering estimates" with their basis stated inline. | No frozen document defines a completion metric. Presenting invented-but-precise-looking numbers as measured fact would violate the no-fabrication rule; labelling them as judgement calls with a stated basis lets a reader audit and disagree. |
| **D-06** | Stale orientation documents found during the review (root README, docs/README, supabase/README, Roadmap v1.1 percentages) were NOT edited in this work package. | WP-K01's certified scope is the knowledge platform only. Those are separately governed ACTIVE documents; fixing them here would be exactly the kind of drive-by scope creep the repository's governance model forbids. They are recorded in the new Technical Debt register instead, so the finding isn't lost. |
| **D-07** | Fix the pre-existing `page-s2`/`page-s3`/`page-s18` triple-default-page defect and the missing S3/S4 sidebar links. | These are defects in the file's own mechanics (invalid state: three pages simultaneously not `display:none`; two pages unreachable from navigation) discovered during the structural review — correcting them is scope-appropriate hygiene on the file being refactored, not an unrelated change. Disclosed explicitly in the Impact Report rather than silently folded into "insertions." |
| **D-08** | Session S26 is written through the same injection-point contract (`SESSIONS_INJECT`, `NAV_INJECT`, `TIMELINE_INJECT`, `FILES_INJECT`, `MODULES_INJECT`, `DECISIONS_INJECT`) that every prior session used. | Keeps the `session-knowledge-doc` skill fully compatible going forward — a future session's normal workflow (grep the injection comment, insert above it) is unaffected by this refactoring. |
| **D-09** | The 14 OS pages are ordered Executive → Roadmap → Features → Repository → Backend → RE → Database → API → Implementation → Decisions → Debt → Validation → Deployment → Metrics, with Session History last. | Mirrors the WP-K01 brief's own numbering and a natural reading order: state, then plan, then what it does, then how it's built (coarse→fine: repo shape → backend → the one specialized subsystem → data), then proof-of-work layers (API/WP/decisions/debt/validation/deploy), then raw metrics, then history. |
| **D-10** | Live database counts (dishes, cohorts, weekly plans, etc.) shown on the Database dashboard are attributed to REPO-CERT-009/010 rather than re-queried this session. | No live Supabase connection was made or authorized for this documentation-only work package; citing the certifying document is honest about the evidence's age and avoids an unauthorized DB touch. |

## Versioning & Placement

v1.0, docs/project-history/ (loose, per the existing convention for point-in-time WP decision logs — see WP-5D/5E/5F2 Engineering Decision Logs at the same path level). Naming per WP-5AA.

## Founder Sign-off

Founder acknowledgement of the WP-K01 design decisions above: _______________________ Date: ___________
