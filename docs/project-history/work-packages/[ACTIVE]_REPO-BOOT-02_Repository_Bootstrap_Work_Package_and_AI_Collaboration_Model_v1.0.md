# [ACTIVE]_REPO-BOOT-02_Repository_Bootstrap_Work_Package_and_AI_Collaboration_Model_v1.0

**Naming note:** `REPO-BOOT-` prefix retained deliberately (see `REPO-BOOT-01`) — this document supersedes `REPO-BOOT-01`'s work-package framing with the permanent 3-AI collaboration model, but stays outside `DOC-`/`APDF-`/governance naming so it remains independently removable.
**Scope:** Design only, per instruction. No repository created, no code written, no Claude Code prompt generated.
**Date:** 2026-07-03 · **Status:** Draft — Ready for Founder Review

---

## Task 1 — APDF Responsibility Transfer Points

Reviewed against `[ACTIVE]_APDF_Framework_vNext_v2.0.md`'s 7-phase model:

| Phase | Claude.ai → Claude Code Transfer? | Exact Transfer Point |
|---|---|---|
| 1–5 (Discovery through Architecture Finalization) | **No transfer** | Claude.ai owns all of it; no repository exists to transfer to |
| 6 (Repository Bootstrap) | **First transfer point** | The moment Repository Gate's binary test (trivial migration applies + rolls back) is attempted — everything before that point in Phase 6 (verification, sequencing, work-package authoring) stays with Claude.ai |
| 7 (Implementation) | **Full, permanent transfer for execution work** | Claude Code owns Seed SQL → Backend → Frontend → Testing → Launch mechanics; Claude.ai retains authorship of any *new specification* (DOC-P4 series) that Claude Code then implements |

**There is exactly one structural transfer point in the entire APDF: the Repository Gate.** Every session before it stayed correctly with Claude.ai (confirmed by this project's own history — no Claude Code work has occurred yet). This matches the "AI Operating Model" instruction that Claude.ai does not directly implement repository code.

---

## Task 2 — Repository Bootstrap Work Package (Standard Work Package format, per Task 8)

### 1. Objective
Stand up and verify a working `foofoo-v2` repository, connected to Google Drive (staging) and populated with classified, versioned project documents — ready for Claude Code to begin Phase 7.

### 2. Context
Architecture Freeze is signed (Ankit, 3rd Jul'26). `REPO-BOOT-01` (prior session) scored the Repository Gate at 5/13 PASS, 8/13 NOT VERIFIED — this package supersedes that partial verification with the fuller AI Collaboration Model now that Drive-as-staging and a 3-AI operating model have been adopted.

### 3. Required Repository Documents
`CLAUDE.md` (to verify/create), `[ACTIVE]_DOC-P3-05_Part_A_Readiness_Migration_Strategy_v1.2.md`, `[ACTIVE]_DOC-P3-04_Data_Architecture_ERD_v1.3.md`, `[ACTIVE]_Phase3_5_Architecture_Freeze_v1.0.md`, this document.

### 4. Founder Decisions Required
- Confirm Google Drive connector authorization (Claude.ai side) — see (a) above
- Confirm GitHub auth method for Claude Code (`gh auth login` recommended over PAT) — see (b)/(c) above
- Confirm secrets management approach formally (currently ⬜ per `project-kickoff` checklist)
- Approve Pattern A (Framework at Root) as the folder structure — see Task 4 below

### 5. Risks
Same primary risk as `REPO-BOOT-01`: treating "described" as "verified." New risk this session: a Drive→repo sync mechanism that silently overwrites a newer ACTIVE document with an older one if version-detection logic is wrong — addressed directly in Task 3 below.

### 6. Acceptance Criteria
All Repository Gate items PASS with real evidence; Drive folder successfully discovered and classified by Claude Code; folder structure matches Pattern A; zero framework files (`app/`, `src/`, `supabase/`, `package.json`) touched or moved.

### 7. Expected Outputs
Verified repo state, populated `knowledge-book/` structure, a Bootstrap Verification Report with real (not assumed) results.

### 8. Repository Changes
Creation of `knowledge-book/`, `qa/`, `ops/`, `general/` folders alongside existing Expo/Supabase framework files (Pattern A); no framework file touched.

### 9. Validation Required
Trivial migration + rollback test (unchanged from `REPO-BOOT-01`); Drive-sync dry-run showing correct classification before any real copy operation.

### 10. Rollback Strategy
All new folders/files are additive; if sync misclassifies something, the fix is deleting the wrongly-placed copy — source documents in Drive and this project's knowledge base are never modified by a sync operation, only read from.

### 11. Definition of Done
Repository Gate scores 13/13 PASS with real evidence; first Drive→repo sync completed with a written conflict report (even if the report says "zero conflicts").

---

## Task 3 — Repository Synchronization Strategy

**Recommended strategy: Claude.ai-mediated sync, not direct Claude Code↔Drive sync** (reasoning given in answer (a) above — Claude Code has no native Drive connector, so building a two-connector mental model adds risk for no benefit).

**Mechanics:**
1. Founder uploads a document to `Claude_Foofoo-v2` in Google Drive.
2. Claude.ai (which has the Drive connector) periodically or on-request lists recent files, reads each new/changed document, and **classifies** it: document type (architecture/governance/APDF/review/roadmap/research/seed-data), extracts its stated version and `[ACTIVE]`/`[FROZEN]`/etc. status from its own header (per `DOC-P3-09` §06E, already established).
3. Claude.ai **detects conflicts** by comparing the new document's declared version against what's already recorded as the latest known version for that document name — if the new file has a *lower* or *equal* version number than what's already tracked, it is never auto-copied; it's flagged for Founder review instead.
4. Claude.ai commits the classified, correctly-versioned document into the repo's `knowledge-book/` structure (per Task 4's folder map) — this is a repo write, so it happens via a GitHub connector/PAT-authenticated commit, not via Claude Code.
5. Claude Code, on its next session, reads only from the repo — it never touches Drive directly, and therefore never needs Drive credentials at all.

**Why this is the safest option:** it keeps exactly one system (Claude.ai) responsible for interpreting ambiguous human-uploaded files, and exactly one system (Claude Code) responsible for deterministic repo operations — matching the AI Operating Model's own stated split (Claude.ai = documentation authority, Claude Code = implementation) rather than blurring it by giving Claude Code a second, less-structured input source.

**Never overwrite newer versions:** enforced by step 3's version-comparison rule — this is a hard rule, not a heuristic; if version metadata is missing or ambiguous, the document is quarantined (flagged, not copied) rather than guessed at.

---

## Task 4 — Repository Folder Structure (Pattern A — Framework at Root)

Per the `repo-structure-setup` skill, directly applicable since FooFoo is Expo/React Native + Supabase (confirmed via project memory: "React Native + Expo, Supabase"). **Framework owns the root; our structure sits alongside it, never replacing it:**

```
foofoo-v2/
├── CLAUDE.md
├── README.md
├── INDEX.md
│
│   ← FRAMEWORK ZONE — never reorganized
├── app/                  (Expo)
├── src/
├── supabase/
│   └── migrations/
│       ├── 001-020_*.sql        (structural, FROZEN)
│       ├── 100-199_*.sql        (seed — Phase 7)
│       └── 900-999_*.sql        (validation)
├── assets/
├── package.json
├── app.json
│
│   ← OUR ZONE
├── knowledge-book/
│   ├── product/core/          (DOC-01–04, Personas, PRD)
│   ├── architecture/core/     (DOC-P3-02–08, ERD, API Contract, Security)
│   ├── governance/core/       (DOC-P3-09/11/12, Baseline Register)
│   ├── apdf/core/              (APDF_Framework_v1, vNext_v2.0)
│   ├── reviews/                (PIR, Architecture Decision Review, Architecture Freeze)
│   ├── roadmaps/               (FooFoo_Project_Roadmap v1.0/v1.1, PM-SUPP-01)
│   ├── research/                (Batch 1–6 Pipeline Packages)
│   ├── seed-data/               (source CSVs/XLSX — or pointer/manifest if too large for repo)
│   └── operations/core/
├── qa/
│   └── reports/
├── ops/
│   ├── logs/session-log/
│   └── audits/
└── general/
    ├── glossary.md
    └── changelog.md
```

**This directly answers Task 4's requirement list** (Architecture, Governance, APDF, Reviews, Roadmaps, Research, Seed Data, Implementation, Operations, Future Growth) — Implementation is the framework zone itself (`app/`, `src/`, `supabase/`); Future Growth has no dedicated folder yet since nothing in the project currently populates it — adding an empty placeholder folder for a concept with zero content would violate the "don't invent" discipline this project has held throughout; it can be added the moment real content exists for it.

---

## Task 5 — Claude Code Ownership Model (full list)

Repository creation/folder creation (once Founder-approved) · document import from repo (never from Drive directly) · migration generation · seed SQL · backend (Edge Functions) · frontend (React Native/Expo) · testing · validation script execution · refactoring · documentation updates *within the repo* (not authoring new architecture) · version synchronization *within the repo* (detecting drift between repo state and what Claude.ai last committed).

## Task 6 — Claude.ai Ownership Model (full list, permanent)

Architecture · planning · governance · APDF ownership and evolution · reviews (PIR, Architecture Decision Review, Architecture Freeze-style checkpoints) · decision packs · Founder guidance · Drive document classification and version-conflict detection (Task 3) · authoring the repo commit for classified documents · work package generation (this document's own format) · generating Claude Code prompts when implementation is actually required.

---

## Task 7 — Founder Workflow

1. Review Claude.ai's work package / decision pack
2. Approve
3. Upload new documents to `Claude_Foofoo-v2` (Google Drive)
4. Execute approved Claude Code prompts

**Suggested improvement, since independent thinking was requested:** add a 5th, optional step — **spot-check the version-conflict quarantine list** (Task 3, step 3) periodically, since that's the one place in this whole model where an automated system might silently do nothing (correctly cautious) rather than something wrong. A quarantine that nobody ever looks at is equivalent to data loss over time. This is a small addition, not a new burden — it only requires attention when something is actually flagged.

---

## Task 8 — Standard Work Package Format

Already demonstrated in Task 2 above (11-part structure exactly as specified) — adopted as the template for every future implementation cycle. No further design needed; this section confirms the format, doesn't repeat it.

---

## Task 9 — Repository Bootstrap Execution Strategy: A, B, or C?

**Recommendation: Option C — a hybrid, reasoned specifically from this project's evidence, not a generic best practice.**

Neither pure Option A (repo setup first, then import) nor pure Option B (import first, then repo setup) fits cleanly:

- **Pure Option A is wrong for this project** because "repository setup" without knowing what documents need to land where means guessing at the `knowledge-book/` subfolder taxonomy (Task 4) — and this project already has ~50+ real documents whose categories are already known. Setting up empty folders first and hoping they match is exactly the kind of unforced assumption this project's entire discipline (evidence over inference) argues against.

- **Pure Option B is wrong** because importing documents with nowhere correctly structured to land them means either dumping them at repo root (chaos) or guessing a folder structure ad hoc per document (inconsistent, and contradicts having just designed Task 4's structure deliberately).

- **Option C (recommended): Structure-and-classify-in-parallel, import-last.** First, Claude Code creates the *empty* Pattern A folder skeleton (Task 4) — this is fast, mechanical, and needs no document content to do correctly, since the skeleton is generic. Simultaneously (not sequentially), Claude.ai performs the Drive classification pass (Task 3, steps 2–3) against the *already-known* set of project documents, since their categories are already evident from this project's own document-type naming (`DOC-P3-XX` = architecture, `Batch*` = research, etc.) — no repo access is needed to classify, only Drive access. Only once both are ready does the actual document *copy* into the skeleton happen, as a single reconciled operation with the version-conflict check (Task 3, step 3) already applied.

This is faster than strict sequencing (folder creation and classification genuinely don't depend on each other) and safer than pure Option B (nothing gets copied into a structure that doesn't exist yet, and nothing gets structured based on guesswork about what will arrive).

---

## Task 10 — Permanent Implementation Lifecycle Diagram

```
┌──────────┐
│ ChatGPT  │  Independent review, architecture challenge
└────┬─────┘
     │ (advisory only — never becomes project authority)
     ▼
┌───────────┐
│ Claude.ai │  Architecture · Planning · Governance · Decision Packs
└────┬──────┘  Reads: Google Drive (Claude_Foofoo-v2)
     │         Writes: Repo commits (classified docs only)
     │ (Repository Gate — the one structural transfer point)
     ▼
┌─────────────┐
│ Claude Code │  Implementation · Migrations · Backend · Frontend · Tests
└────┬────────┘  Reads: GitHub repo ONLY (never Drive directly)
     │           Writes: Repo commits (code + repo-side doc sync)
     ▼
┌──────────┐
│ GitHub   │  Permanent source of truth
└────┬─────┘
     │
     ▼
┌──────────┐
│ Founder  │  Review → Approve → Upload (Drive) → Execute (Claude Code prompts)
└────┬─────┘
     │
     └──────────────► Repeat
```

---

## Task 9 (Final Output item) — Repository Bootstrap Recommendation

Proceed with Option C sequencing (Task 9), using Pattern A folder structure (Task 4), with Claude.ai-mediated Drive sync (Task 3) rather than direct Claude Code↔Drive access. Formalize the secrets/auth decision (GitHub connector for Claude.ai, `gh auth login` for Claude Code) before the first real Claude Code session, per (a)–(c) above.

## Go / No-Go Assessment

**Conditional GO.** The design is complete and internally consistent. Actual execution still requires: (1) Founder to authorize the Google Drive and GitHub connectors in Claude.ai settings, (2) Founder to confirm the GitHub auth method for Claude Code, (3) the still-outstanding `REPO-BOOT-01` verification items (repo structure, Supabase reachability, `CLAUDE.md` presence) to be checked with real evidence, not assumed. None of these are design gaps — they're access/credential steps only the Founder can complete.

---

## Regression Review

- ✅ No architecture, governance, or APDF content changed — this document references but does not modify `APDF_Framework_vNext_v2.0`, `DOC-P3-09`, or any frozen document
- ✅ No repository created, no code written, no Claude Code prompt generated, per explicit instruction
- ✅ Skills consulted (`repo-structure-setup`, `project-kickoff`) used as evidence for Task 4/7, not treated as new project rules
- ✅ `REPO-BOOT-01` not modified — this document supersedes its work-package framing explicitly, both retained as historical artifacts

Founder sign-off: _______________________ Date: ___________
