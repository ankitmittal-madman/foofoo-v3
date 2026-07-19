---
name: coding-standards-enforcer
description: >
  Organization-wide coding standard applied to every piece of code written in
  any Claude Code session — JSDoc/inline documentation on every function and
  component, and structured logger usage instead of raw console.* calls.
  This is a writing-time standard, not an audit — it shapes how code is
  written as it's written, every session, automatically.

  RUNS AUTOMATICALLY, every session, via CLAUDE.md — not a slash command.
  See dotfiles CLAUDE.md Session Start block for the trigger wiring.
---

# Coding Standards Enforcer

This is not an on-demand audit. This is a standing rule that shapes every
line of code written in this project, every session, without the developer
needing to ask for it each time.

## Why this is wired differently from the audit skills

Audits (`/hygiene-deadcode`, `/audit-deps`, etc.) check code *after* it's
written, on request. This skill governs code *as it's written* — documentation
and logging discipline are much cheaper to apply at write-time than to
retrofit later, so this should be muscle memory from the first line of a
session, not a periodic catch-up pass.

It is wired into project `CLAUDE.md` (via the dotfiles Session Start block)
rather than triggered by a phrase, because a phrase-based trigger would mean
forgetting to say it once means a whole session's code ships without the
standard applied.

## Skill Authority

This skill provides reusable engineering practices.

It must never override:

- Project Documentation
- Architecture
- Governance
- Founder Decisions
- Project Workflow (APDF)

If the project already defines an approach, the project takes precedence.

## Activation
- Activation Type: Automatic
- Recommended Phase: Every Session
  
---

## Step 0 — Self-install check (run once per repo, at session start)

```bash
ls .claude/skills/coding-standards-enforcer/SKILL.md 2>/dev/null && echo "INSTALLED" || echo "MISSING"
```

**If MISSING:** fetch from `ankitmittal-madman/dotfiles` →
`.claude/skills/coding-standards-enforcer/SKILL.md` via GitHub MCP, write to
the same path in this repo, commit and push.

**If INSTALLED:** apply the standards below for the rest of the session.

---

## Standard 1 — Inline documentation

Every function, component, and backend/edge-function handler written or
substantially modified in this session must carry a documentation comment
matching the project's language convention (JSDoc for TS/JS, docstrings for
Python, etc.). Detect the convention from existing code in the repo if any
exists; otherwise default to JSDoc for TS/JS projects.

**For UI components:**
```
/**
 * ComponentName — one sentence description.
 *
 * @param propName - what it is and where its data comes from
 * @param onAction - what triggers it and what it writes/changes
 */
```

**For backend/edge function handlers:**
```
/**
 * functionName — one sentence description.
 *
 * Trigger: [how it's called — cron, webhook, client call, etc.]
 * Writes to: [which tables/resources]
 * Reads from: [which tables/resources]
 * Error codes: [which standard error codes it can return, if the project
 *               has a standard error format]
 */
```

**For utility functions:**
```
/**
 * functionName — one sentence description.
 * @param paramName - what it is
 * @returns what it returns
 * @throws when it throws and why
 */
```

**Rule:** documentation must describe *what a non-technical PM needs to
know* (what triggers it, what it affects, what it returns) — not just
restate the type signature. `@param dish - the dish` is not acceptable;
`@param dish - the dish or combo object currently shown in the carousel`
is.

This applies only to code written or substantially modified in the current
session — this is not a retroactive documentation pass over the whole
codebase (that's a separate, explicit task if ever requested).

---

## Standard 2 — Structured logging only, never raw console.*

Before writing any `console.log`, `console.warn`, or `console.error` in
application code, check whether a project logger already exists:

```bash
ls src/utils/systemLogger.ts src/lib/logger.ts 2>/dev/null
```

**If a logger exists:** use it instead of raw console calls.
- `console.log(...)` → `Logger.info('MODULE_NAME', 'event description', { meta })`
- `console.error(...)` → `Logger.error('MODULE_NAME', 'event description', { meta })`

**If no logger exists yet:** tell the user that this project doesn't have
the logging infrastructure installed yet, and suggest running
`/install-logging` before continuing — don't silently write raw
console.* calls and don't silently invent a logger inline either, since
that creates exactly the kind of inconsistency this standard exists to
prevent.

**Privacy rule (always applies):** never pass a field the project treats as
sensitive into a log call's metadata — discover the project's actual
sensitive fields from its schema/docs (the same discovery the
`audit-dpdp-compliance` skill performs, if that's relevant to this project)
rather than assuming a fixed list.

---

## Standard 3 — Update the change log

If `general/changelog.md` exists in the project and this session made any
non-trivial code change (new file, new feature, meaningful fix — not a typo
fix), add an entry under `[Unreleased]` before the session ends, following
the format in `general/changelog.md`'s own footer template.

If `general/changelog.md` doesn't exist yet, don't create it as a side
effect of this standard — that's `/install-logging`'s job. Just note to
the user that one doesn't exist yet.

---

## What this skill does NOT do

- Does not retroactively document or refactor existing code — only governs
  new/modified code in the current session
- Does not replace existing console.* calls project-wide — that's the
  `/install-logging` compliance-check pass
- Does not invent a logger if one doesn't exist — flags the gap instead
