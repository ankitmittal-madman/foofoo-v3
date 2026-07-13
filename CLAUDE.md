# CLAUDE.md — FooFoo Repository Operating Guide

## Session Start Protocol (mandatory, every session)
1. git fetch && git pull origin main
2. Verify HEAD == origin/main, clean tree — stop and report if not
3. Invoke every relevant skill in .claude/skills/ — report invoked/skipped/why
4. Read this file, then docs/README.md to find only what's relevant to the task
5. Do NOT reread the entire repository unless structure changed or Founder requests full reconstruction

## Repository Philosophy
Documentation-first. Class-first Recommendation Engine (household → cohort →
class plan → dish pool). Discovery before recommendation, evidence before
conclusion — never trust memory or prior summaries over live repository state.
This repository's Git history begins 2026-07-13 (see docs/project-history/
certificates/REPO-BOOT-03) after the original apverse-labs account was lost —
a reconstructed baseline, not continuous lineage.

## Folder Structure
docs/product        — what FooFoo is, for whom
docs/architecture    — how it's built (schema, RE design, UX, PRD)
docs/governance      — standing rules (APDF, AGRs, Baseline Register)
docs/project-history/work-packages   — proposed engineering work, DESIGNED until certified
docs/project-history/certificates    — proof something was actually executed
docs/research        — Batch1-6 discovery/canonicalization process
docs/roadmaps        — forward plans
docs/visuals         — interactive HTML explainers
database/migrations, rollback, seeds, validation — SQL, numbered bands (structural 001-020, seed 100-199, validation 900-999)
data/source          — raw seed spreadsheets
engineering/templates — reusable document skeletons (see below)

## Placement Rule (mandatory for every new document)
Read document → read metadata → determine purpose → determine canonical
destination → validate against this structure → only then write.
Never use filename pattern alone. Never use a convenience/temporary folder.
No top-level folder without an approved Repository Architecture Change
Request (RACR) — this architecture is frozen pending Founder approval.

## Documentation Standard
Header: Status / Version / Date / Placement / Supersedes / (Dependencies if any)
Body: Executive Summary → numbered sections → Critical Self-Review →
Versioning & Placement → Founder Sign-off (blank line, always last)

## Naming Standard (ratified WP-5AA — mandatory, never violate)
See docs/governance/[ACTIVE]_Repository_Naming_Standard_v1.0.md (authoritative).
Documents: [STATUS]_Document_Name_vMAJOR.MINOR.md where STATUS is exactly one of
ACTIVE / DRAFT / FROZEN / SUPERSEDED / ARCHIVED (the five DOC-P3-09 §06E values).
Version is a single dot (v1.0, v1.20) — never v1_0, 1.0, or v1.
SQL: NNN_description.sql (migrations, matching the live Supabase ledger),
NNN_description_rollback.sql, 1NN_ seeds, 9NN_ validation — no status prefix, no version.
Certificates/Runbooks/Templates: [ACTIVE]_REPO-CERT-NNN_/RUNBOOK_/TEMPLATE_Name_vX.Y.md.
Never create a file that violates this. Choose STATUS from the document's own header;
if the status is a non-token lifecycle word or is ambiguous, STOP and ask — never guess.
Bulk-renaming existing files requires explicit Founder authorization (as WP-5AA gave).

## Version & Lifecycle Rules
Never delete a superseded document — stamp SUPERSEDED BY vX.Y with a
changelog note, keep both (see docs/project-history/work-packages/
REPO-WP-03 v1.0 for the reference example).
A Work Package's Status may only read COMPLETED if a companion certificate
exists in docs/project-history/certificates/ with real execution output —
never edited in place to claim completion.

## Git Workflow
Fetch/pull before work. One commit per logical change. Never force-push.
GitHub MCP is available via .mcp.json using ${GH_TOKEN}.

## Rules for AI Behaviour
Never fabricate execution, versions, commit history, or content that wasn't
actually provided. If required input (a template, a section, a file) is
missing, stop and report the gap rather than inventing placeholder content.