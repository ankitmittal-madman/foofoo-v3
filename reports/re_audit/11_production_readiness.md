# Phase 10/11 — Production Knowledge & Readiness Coverage

Status: DRAFT (working audit output). Every percentage below is a qualitative estimate grounded in
the cited evidence from reports 02-09 — not a precise measured count except where a report gives an
exact ratio. Where confidence is low, it is stated as such rather than smoothed over.

## Coverage by component

| Component | Estimate | Evidence / basis |
|---|---|---|
| Algorithm (v1 scope: D1-D7, hard filters, BASE, Q15, pairing, assemble-7, exploration) | **~80%** | report 02 — every core-path component is Implemented; the two real gaps are D7 (stub) and the personal-history term (built, inert by design, not a bug); G6 pairing bug is a known, tracked non-fix, not an oversight |
| Algorithm (spec-generation-1 concepts: MMR, Never/Not-Today decay, 4-state model) | **0%, but by deliberate replacement, not oversight** | report 02, 01 §B — none of these specific algorithms exist; functionally-equivalent different mechanisms exist for variety/suppression; the 4-state model has no replacement at all |
| Meal Genome (RE-DOC-02's literal 20 dimensions) | **0% literal match; ~70% functional-equivalent coverage** | report 03 — no dimension is a byte-for-byte match; ~14/20 have a working analogue in the live golden-sample engine |
| Meal Genome (real 802-810-dish catalogue population) | **~30%**, uneven across dimensions | report 03 — only 6/20 dimensions confirmed bulk-populated for the real catalogue (occasion, cuisine, cook-time, difficulty, calories, tier); several others depend on unverified tag-seed row counts |
| Food Ontology / Graph | **~35%** | report 04 — every "edge" exists as a bespoke table/bitmask (functional, not literal graph); substitution graph and hidden-derivative allergen layer are both structurally near-empty/dropped |
| Knowledge Base — Research Priors | **~25%** | report 05 §6 — 4 of ~10+ candidate research artifacts reach the live engine; the rest terminate at build-tooling |
| Knowledge Base — Weather | **~70%** for the golden sample's 3 documented conditions; likely much lower at full-catalogue scale | report 05 §6 |
| Knowledge Base — Pairings | **~90%** of the frozen v1 rule set; 0% learned/v2 | report 05 §6 |
| Knowledge Base — Regional Intelligence (PRIOR table) | **~10-15%** | report 05 §6 — spine's own admission, only 3 illustrative cells populated |
| Knowledge Base — Safety (allergen completeness) | **~50%, explicitly not launch-ready** | report 05 §6, report 04 §3 — basic explicit-flag filter works; hidden-derivative layer is the spine's own named pre-launch blocker |
| Knowledge Base — Seed Quality | **Mixed, self-flagged** | report 05 §6 — at least one confirmed real curation defect caught and documented (`cohort_weights.yaml:32`), sig-scores beyond the golden sample are AI-assigned/unreviewed |
| Database (schema hygiene, RLS, table lifecycle) | **~85%** | report 07 — RLS fully present on every RE-relevant table; two dead schemas cleanly dropped with backups; remaining gaps are ~11 orphaned tables (hygiene, not risk) and one non-conforming filename |
| Seed Data — core ICD-1 catalogue | **~99-100%** | report 06 §1 — production-scale, ETL'd, checksummed |
| Seed Data — dish-ontology aliases | **786 rows committed / 37 rows (4.7%) certified** | report 06 §4 |
| Synergies (cross-module interactions) | **6/9 real, 1/9 partial, 2/9 not built** — ~72% weighted | report 08 |
| Deployment / production reachability | **0% — nothing is deployed** | RE-DOC-13 Executive Summary, unchanged by this audit (out of scope, no infra access) |

## What "production readiness" means given the two-generation history

The single most important framing fact for this section: **spec generation 2 (RE-DOC-10-13 / Core
Spine) is what was actually engineered, and it is engineered to a high internal standard** — 93/93
tests passing (report 02, 09), honest FD-11 gating on the personal-history term rather than a faked
learning signal, disclosed data-quality bugs caught in-repo rather than hidden, two dead schemas
cleanly dropped with JSON backups rather than left to rot. Spec generation 1's algorithms (MMR,
weight ladder, 4-state model, Never/Not-Today decay) were not built — but this looks like a
considered pivot to a different, evidenced design (BASE×GAIN_Q15, epsilon-greedy, lifecycle_stage),
not an abandoned or forgotten requirement. No governance document currently records that pivot as a
decision, however (same gap RE-DOC-12 already flagged for the two-engine question) — this is a
documentation/governance gap, not an engineering one.

Given that framing, "production readiness" should be scored against **what spec generation 2 itself
says must be true before public launch**, not against spec generation 1's now-superseded algorithm
list:

| Spine's own pre-launch gate | Status |
|---|---|
| Allergen hidden-derivative folding (SP-F13) | **Not met** — schema-and-data both absent post schema-drop |
| Jain filter correctness against full catalogue | **Code correct; full-catalogue data population unverified** |
| Real catalogue cutover (dishes, sig scores, PRIOR table, nutrition) | **Not met** — golden sample still in production scoring path |
| Contract/CI gates (schema validation, golden-master regression) | **Met** — confirmed live in CI per RE-DOC-12, re-confirmed by 93/93 passing tests this session |
| Deployment (Fly.io live, HMAC verified in production) | **Not met** — nothing deployed |

**Net: the engine is well-built for what it claims to be (a v1 rule-based recommendation core on a
golden sample), but is not yet safe or complete to serve the real, full catalogue to real users in
production** — the gating items above are the spine's own words, not this audit's invention.

## Critical Self-Review

Every percentage in this document is traceable to a specific report (02-09) and, through those
reports, to a file/line/count. Where a report itself flagged low confidence (e.g. "qualitative
judgment, not a measured percentage" — report 05 §6's own closing line), that caveat is preserved
here rather than presented as more precise than it is. This document does not independently verify
anything beyond what reports 02-09 already established; it is a synthesis layer, not a new audit
pass.
