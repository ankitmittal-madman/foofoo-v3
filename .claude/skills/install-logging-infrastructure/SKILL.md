---
name: install-logging-infrastructure
description: >
  Installs the organization-standard logging infrastructure into a project —
  a structured system logger, a human-readable user journey logger (if the
  project has end-user accounts/actions), a lightweight client logger, a
  transaction log export script, and a master change log file. On re-run,
  checks the project for compliance (raw console.log usage, missing change
  log entries) rather than reinstalling.

  Trigger: slash command /install-logging only. Does not trigger automatically.
  Run once near project start; re-run anytime to check compliance.
---

# Logging Infrastructure Installer

Scaffolds a consistent, organization-wide logging standard into any project,
then can be re-run as a compliance check.

## Skill Authority

This skill provides reusable engineering practices.

It must never override:

- Project Documentation
- Architecture
- Governance
- Founder Decisions
- Project Workflow (APDF)

If the project already defines an approach, the project takes precedence.
## Trigger

Activates ONLY on:
```
/install-logging
```
## Activation
- Activation Type: Manual
- Recommended Phase: Repository, Implementation, QA or/and Production

## Step 0 — Self-install check (run once per repo)

```bash
ls .claude/skills/install-logging-infrastructure/SKILL.md 2>/dev/null && echo "INSTALLED" || echo "MISSING"
```

**If MISSING:** fetch from `ankitmittal-madman/dotfiles` →
`.claude/skills/install-logging-infrastructure/SKILL.md` via GitHub MCP, and
also fetch the reference templates (see Reference files at the bottom) into
`.claude/skills/install-logging-infrastructure/references/`. Commit and push.

**If INSTALLED:** continue below.

---

## Step 1 — Detect what's already present (decide install vs compliance-check mode)

```bash
ls src/utils/systemLogger.ts src/lib/logger.ts 2>/dev/null
ls src/utils/userJourneyLogger.ts 2>/dev/null
ls scripts/export-txn-logs.* 2>/dev/null
ls CHANGELOG.md 2>/dev/null
```

**If none of these exist → INSTALL MODE** (Steps 2–6).
**If some/all exist → COMPLIANCE-CHECK MODE** (skip to Step 7).

State to the user which mode you're running in and why.

---

## Step 2 — Detect project shape before scaffolding (don't assume FooFoo's structure)

```bash
# Platform — React Native/Expo, Next.js, plain Node, etc.
grep -E '"expo"|"react-native"|"next"' package.json 2>/dev/null

# Error tracking already in use?
grep -E '"@sentry/|"@bugsnag/|"@rollbar/' package.json 2>/dev/null

# Does the project have end-user accounts / a concept of per-user actions?
# (signal: an auth-related table/file, a "user" concept in the schema)
grep -rli "user_id\|auth\.uid\|getUser" --include=*.{ts,tsx} . 2>/dev/null | grep -vE "node_modules" | head -5

# Does the project have a computation/decision engine? (recommendation engine,
# pricing engine, matching algorithm, scoring system — anything that makes a
# non-trivial decision a human would want explained)
grep -rli "score\|recommend\|engine\|algorithm\|decision" --include=*.{ts,tsx} . 2>/dev/null \
  | grep -vE "node_modules|\.test\.|\.spec\." | head -5
```

Based on findings, decide which components to scaffold:
- **System Logger** — always scaffold (every project benefits)
- **Lightweight client logger** — scaffold if a separate hot-path-friendly
  logger makes sense (e.g. mobile/web client code, where AsyncStorage I/O on
  every log call is too expensive) — otherwise the System Logger alone is enough
- **User Journey Logger** — only if user-accounts/actions signal found in Step 2
- **Computation/Decision Logger** — only if a computation/decision engine
  signal found in Step 2 (see Step 5)
- **Transaction export script** — only if using Supabase/a DB that holds the
  event tables these loggers would write to (skip for pure client-only apps
  with no backend persistence of events)
- **Change log** — always scaffold

State your scaffolding plan to the user before writing any files.

---

## Step 3 — Scaffold the System Logger

Read `references/system-logger-template.md` for the full template.

Adapt to the detected stack:
- If Sentry (or another tracker) is present, wire ERROR/WARN forwarding to it
- If no error tracker is present, note this to the user — the logger still
  works for console + local persistence, but flag that production errors
  currently have no remote visibility, which is worth fixing before launch
- Adapt the persistence layer to what's available (AsyncStorage for React
  Native, localStorage for web-only, or skip persistence for a pure backend
  service)

Write to `src/utils/systemLogger.ts` (or the equivalent conventional location
for the detected stack — e.g. `lib/logger.ts` for a Next.js project).

---

## Step 4 — Scaffold the User Journey Logger (only if applicable)

Read `references/user-journey-logger-template.md`.

This logger writes **plain English** narrative entries for end-user actions
— written so a non-technical PM can read exactly what a user did and why the
app responded the way it did, without needing to read code or raw event
tables.

Adapt the action vocabulary to the project's actual user actions (discover
these from the codebase's gesture handlers, form submissions, or API
endpoints — don't assume a fixed action list).

Write to `src/utils/userJourneyLogger.ts` (or equivalent).

---

## Step 5 — Scaffold the Computation/Decision Logger (only if applicable)

If Step 2 found a computation/decision engine (recommendation engine,
pricing logic, matching algorithm, eligibility scoring, etc.), this project
needs decision-level logging: every time the engine makes a non-trivial
choice, log the winner, the alternatives considered, and **why** in plain
English — this is the PM's window into "why did the system do that" without
reading code.

Discover the engine's actual decision points (the function(s) that produce a
final scored/ranked output) and design a logger function specific to that
decision shape — following the same plain-English narrative pattern as the
User Journey Logger's decision-logging method (see
`references/user-journey-logger-template.md`'s `logREDecision`-equivalent
method as a structural example, adapted to this project's actual decision
output shape, not copied verbatim).

State your design to the user before writing it, since this one is the most
project-specific and benefits most from a quick sanity check.

---

## Step 6 — Scaffold supporting pieces

**Lightweight client logger** (if applicable per Step 2):
Read `references/structured-logger-template.md`. Write to `src/lib/logger.ts`
or equivalent — note in its own header comment that it's for hot-path code
and that `systemLogger`/equivalent is the full-featured option elsewhere.

**Transaction export script** (if applicable per Step 2):
Read `references/transaction-export-template.md`. Adapt the table names and
event shape to what this project's schema actually has (discover via
Supabase MCP or migration files) rather than assuming fixed table names.
Write to `scripts/export-txn-logs.mjs` (or equivalent for the project's
runtime).

**Change log:**
Read `references/changelog-template.md`. Create `CHANGELOG.md` at the
project root if it doesn't exist, seeded with the project name and today's
date as the first entry's placeholder.

---

## Step 7 — Compliance check (run on re-invocation, or after install)

Whether freshly installed or pre-existing, verify the project is actually
using the logging infrastructure correctly:

```bash
# Raw console.* calls outside the logger files themselves
grep -rn "console\.\(log\|warn\|error\)" --include=*.{ts,tsx,js,jsx} . \
  | grep -vE "node_modules|systemLogger|userJourneyLogger|lib/logger|\.test\.|\.spec\."
```

For every match found, this is a **compliance gap** — code that should be
using the structured logger but is using raw console calls instead.

```bash
# CHANGELOG.md — check it's been updated recently relative to recent commits
git log -1 --format="%ad" --date=short -- CHANGELOG.md
git log -5 --oneline
```

If there are recent feature commits with no corresponding CHANGELOG.md
update, flag this as a gap too.

---

## Step 8 — Write the compliance report

`logs/hygiene-reports/logging-compliance.md`:

```markdown
# Logging Infrastructure — [Install / Compliance Check] — [date]

## Components scaffolded/present
| Component | Status | Location |
|---|---|---|

## Compliance gaps
| File | Line | Issue | Suggested fix |
|---|---|---|---|

## Change log status
Last updated: [date] | Recent commits without entry: N
```

Present this to the user. For compliance gaps (raw console.* calls), ask
before mass-replacing them — this can be a large mechanical change across
many files, and the user may want to batch it differently than a single pass.

---

## Step 9 — Completion summary and commit

```bash
git add src/utils/ src/lib/ scripts/ CHANGELOG.md logs/hygiene-reports/ 2>/dev/null
git commit -m "chore: logging infrastructure [install / compliance check] — [summary]"
git push
```

Tell the user plainly: what's now in place, what's still raw console.*
output needing migration, and whether the change log is being kept current.

---

## Reference files (fetch once during self-install)

- `references/system-logger-template.md` — full System Logger implementation pattern
- `references/user-journey-logger-template.md` — full User Journey Logger pattern
- `references/structured-logger-template.md` — lightweight client logger pattern
- `references/transaction-export-template.md` — DB-to-text transaction export script pattern
- `references/changelog-template.md` — CHANGELOG.md format and entry template

All reference templates are adapted to the detected project's actual stack
and schema — never copied verbatim with foofoo-specific names intact.
