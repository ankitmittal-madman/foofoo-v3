# CLAUDE.md — FooFoo Repository Operating Guide

## Session Start Protocol (mandatory, every session)
1. git fetch && git pull origin main
2. Verify HEAD == origin/main, clean tree — stop and report if not
3. Apply the Skill Activation Policy below — report invoked/skipped/why
4. Read this file, then docs/README.md to find only what's relevant to the task
5. Do NOT reread the entire repository unless structure changed or Founder requests full reconstruction

## Skill Activation Policy (source of truth — this repo, not dotfiles)
This table is the authoritative activation policy for THIS repository.
dotfiles/.claude/CLAUDE.md is only the install source for skill files; its
own activation table is never re-read once a skill is vendored in here —
so this table, not that one, is what a session actually follows.

**Amended 2026-07-30 (Founder directive, superseding the prior policy below):**
Every installed skill under `.claude/skills/` — including all `audit-*`,
`hygiene-*`, `install-*`, and `incident-*` skills previously gated to
explicit slash-command invocation — is now automatically activated every
session, applied as the task at hand needs it. A slash command still
invokes a skill directly and explicitly; the change is that a session no
longer has to wait for one before an applicable skill's discipline applies.
Skills whose own SKILL.md declares "auto-fixes: never" (audit-dpdp,
hygiene-secrets, incident-postmortem, audit-rollback-readiness) still never
apply fixes automatically — always-on here means their checks/discipline
run proactively, not that their no-autofix rule is lifted.

Full always-on roster:
- session-knowledge-doc — update KNOWLEDGE.html whenever code/DB/config/docs
  were touched this session (see Session End below)
- coding-standards-enforcer — shapes new code as it's written (inline docs,
  structured logging), does not retrofit old code
- debug-root-cause — activates on natural language ("this is broken", a
  pasted error), not just an explicit command
- session-resume / session-resumption-protocol — reconstructs execution
  state at session start from actually-read repo content
- audit-dependencies, audit-edge-functions, audit-rls, audit-data-integrity,
  audit-eas, audit-performance, audit-prelaunch, audit-api-contract,
  audit-onboarding-funnel, audit-rollback-readiness — run proactively when
  their subject matter is touched, not only on their slash command
- audit-dpdp — checks proactively; report-only, never auto-fixes
- hygiene-dead-code, hygiene-test-sync — run proactively, auto-fix on
  confirmation as their own SKILL.md specifies
- hygiene-secrets — checks proactively; report + rotation advice only,
  never prints secret values, never auto-fixes
- install-logging-infrastructure — applied when scaffolding new
  code/services that need logging, not only on explicit request
- incident-postmortem — report-only, drafted proactively once an incident
  is resolved rather than waiting to be asked

Previous policy (superseded, kept for record): all other skills stayed
registered but inactive until the Founder or an explicit slash command
invoked them.

## Session End (mandatory whenever code, DB, config, or docs were touched)
Update KNOWLEDGE.html per .claude/skills/session-knowledge-doc/SKILL.md
before ending the turn — inject at the existing points, do not rewrite the
file. If this step is skipped, say so explicitly and why, rather than
silently ending the session.

## Repository Philosophy
Documentation-first. Class-first Recommendation Engine (household → cohort →
class plan → dish pool). Discovery before recommendation, evidence before
conclusion — never trust memory or prior summaries over live repository state.
This repository's Git history begins 2026-07-13 (see
`docs/archive/certificates/ARCHIVED_REPO-BOOT-03_Repository_Migration_Certification_v1.0.md`)
after the original apverse-labs account was lost —
a reconstructed baseline, not continuous lineage.

## Folder Structure
docs/product        — what FooFoo is, for whom
docs/architecture    — how it's built (schema, RE design, UX, PRD)
docs/governance      — standing rules (APDF, AGRs, Baseline Register)
docs/project-history/work-packages   — unresolved/current engineering work only
docs/archive/certificates            — historical proof of completed execution
docs/archive                         — completed, superseded, and historical records; never primary guidance
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
See docs/governance/[ACTIVE]_Repository_Naming_Standard_v1.1.md (authoritative).
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
Never delete a superseded document — archive it with its history intact.
A Work Package's Status may only read COMPLETED if a companion certificate
exists in docs/archive/certificates/ with real execution output —
never edited in place to claim completion.

## Git Workflow
Fetch/pull before work. One commit per logical change. Never force-push.
GitHub MCP is available via .mcp.json using ${GH_TOKEN}.

## Rules for AI Behaviour
Never fabricate execution, versions, commit history, or content that wasn't
actually provided. If required input (a template, a section, a file) is
missing, stop and report the gap rather than inventing placeholder content.

### Synthetic training placement — mandatory

- Synthetic, generated, expert-template, shadow, QA, and research-training records must be
  written only to the dedicated training Supabase project through `TRAINING_DATABASE_URL`.
- Never use `FOOFOO_SUPABASE_URI`, `DATABASE_URL`, or `SUPABASE_DB_URL` as a fallback write target
  for `research.auto_training_records`, `research.training_source_rows`, or `ml.auto_training_*`.
- Production may be queried read-only for aggregate readiness signals. Transfer only bounded,
  non-identifying audit snapshots across the boundary; never copy production identities or raw
  behavioral events into training storage without a separately approved consented-data design.
- Every database-writing workflow must verify its expected Supabase project reference and record
  an application/run actor. If the target cannot be proved, fail closed before opening a write
  transaction.
- Moving or deleting research records requires copy → checksum/count verification → exact-source
  cleanup. Never truncate a mixed research table.

## "Read" Means Complete Read (non-negotiable, never relaxed)
When the Founder asks Claude (in any session — claude.ai or Claude Code)
to "read" a file or document, this means reading it completely, start to
finish, before responding. Not a sample. Not a representative excerpt.
Not "the parts that seemed relevant." Not skipped because a similar file
was read before or its content assumed from memory. Every line, every
section.

This is distinct from "check," "search," "skim," or "look up," which may
legitimately use partial reads, grep, or targeted queries — those verbs
are fine to interpret narrowly. "Read" is not one of them.

If a file is too large to read in full within the current context or
tooling constraints, STOP and say so explicitly, rather than silently
reading a portion and reporting as if the whole file was read. A partial
read disclosed honestly is acceptable; a partial read presented as
complete is not.

This rule applies retroactively to every future session's self-review:
if a session claims something was "read" and it was not read in full,
that claim is inaccurate and must be corrected, not defended.
