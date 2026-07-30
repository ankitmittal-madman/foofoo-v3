---
name: audit-dependencies
description: >
  Runs a comprehensive dependency and security audit on the current project.
  Checks for security vulnerabilities, unused packages, duplicate-functionality
  packages, and framework/SDK compatibility issues. Generic — auto-detects the
  project's package manager, framework, and structure rather than assuming a
  fixed stack.

  Trigger: slash command /audit-deps only. Does not trigger automatically.
---

# Dependency & Security Audit Skill

A repeatable, on-demand audit any lead developer can run on any project with one
command. Produces a written report (`dependency-audit.md`) and, on request, applies
safe fixes automatically.

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

This skill activates ONLY when the developer runs:
```
/audit-deps
```

It does not run automatically at session start, and does not run from typed phrases
alone — this is a deliberate, on-demand action because dependency changes are
consequential and should never happen silently.

## Activation
- Activation Type: Manual
- Recommended Phase: Repository, Implementation, QA or/and Production
  
---

## Step 0 — Self-install check (run once per repo)

```bash
ls .claude/skills/audit-dependencies/SKILL.md 2>/dev/null && echo "INSTALLED" || echo "MISSING"
```

**If MISSING:** fetch this skill file from `ankitmittal-madman/dotfiles` →
`.claude/skills/audit-dependencies/SKILL.md` via GitHub MCP, write it to
`.claude/skills/audit-dependencies/SKILL.md` in the current repo, commit:

```bash
git add .claude/skills/audit-dependencies/
git commit -m "chore: install dependency audit skill"
git push
```

Then continue below.

**If INSTALLED:** continue below directly.

---

## Step 1 — Detect the project's stack (do not assume FooFoo's stack)

Before running anything, identify:

```bash
# Package manager + manifest
ls package.json pnpm-lock.yaml yarn.lock package-lock.json 2>/dev/null

# Framework signals
cat package.json | grep -E '"expo"|"react-native"|"next"|"react"|"vite"' 2>/dev/null

# Monorepo or single package?
find . -maxdepth 2 -name "package.json" 2>/dev/null
```

Determine:
- Package manager: npm / pnpm / yarn
- Project root(s) containing `package.json` (could be one, could be multiple in a monorepo)
- Framework/runtime (Expo, Next.js, plain React, Node service, etc.) — this matters for Step 4

State your findings to the user in one line before proceeding, e.g.:
*"Detected: npm, single package at repo root, Expo SDK 56 app."*

---

## Step 2 — Security vulnerabilities

Run in every detected package root:

```bash
npm audit --json > audit-results.json
```
(use `pnpm audit --json` or `yarn audit --json` if that's the detected package manager)

Parse and report:
```
CRITICAL: [count] — [package names]
HIGH:     [count] — [package names]
MODERATE: [count] — [package names]
LOW:      [count]
```

For CRITICAL and HIGH only: give the exact fix command for each.

---

## Step 3 — Unused packages

Build a list of every package actually imported anywhere in the codebase:

```bash
grep -rhoE "from ['\"][a-zA-Z0-9@][^'\"]*['\"]" --include=*.{js,jsx,ts,tsx} . \
  | sed -E "s/from ['\"]//;s/['\"]//" | sort -u
```

Compare against every dependency in `package.json` (and `devDependencies`).

For every package in `package.json` NOT found in any import:
- Confirm it is truly unused — check build configs, test configs (jest/vitest),
  babel config, framework-specific config files (e.g. `app.json`/`app.config.js`
  for Expo, `next.config.js` for Next.js), and `package.json` `scripts`
- If confirmed unused → mark **REMOVE**
- If used only in config (not imported in code) → mark **KEEP** with a note why

Write the unused list to `dependency-audit.md`:

| Package | Version | Where used (or "nowhere found") | Safe to remove | Command |
|---|---|---|---|---|

---

## Step 4 — Duplicate functionality

Flag any case where two packages solve the same problem. Common patterns to check
for (not exhaustive — use judgement based on what's actually installed):
- Two date/time libraries (e.g. `moment` + `dayjs`, or `date-fns` + `dayjs`)
- Two HTTP client libraries (e.g. `axios` + native `fetch` wrapper)
- Two state management libraries with overlapping responsibility
- Two animation libraries where one is a subset of the other
- Two icon libraries
- Two form libraries

For each duplicate pair found:
- Which one the codebase actually uses more (by import count)
- Which one to remove
- Any migration work needed before removal is safe

---

## Step 5 — Framework/SDK compatibility check

Only run the checks relevant to the framework detected in Step 1.

**If Expo project:** check `app.json`/`app.config.js` for the Expo SDK version,
then verify common version-sensitive packages against it:
`react-native-gesture-handler`, `react-native-reanimated`, `expo-notifications`,
`react-native-safe-area-context`, and any Supabase/Firebase client libraries.

**If Next.js / plain React project:** check React version compatibility for
major UI libraries, and Node engine compatibility in `package.json` `engines`.

**If a backend/Node service:** check Node engine version against what's declared,
and flag any packages requiring a newer Node than the deployment target.

If the framework doesn't match any of the above, state that explicitly and skip
this step rather than guessing.

---

## Step 6 — Apply fixes (only after presenting the report — do not auto-apply silently)

Show the full report to the user first. Then, only if the user confirms:

- CRITICAL/HIGH vulnerabilities → apply fix via package manager install
- REMOVE packages → remove from `package.json` and uninstall
- Duplicates → remove the less-used one, after confirming no unique usage remains

After all changes:
```bash
# Run whatever typecheck/test scripts exist — check package.json scripts first
npm run typecheck 2>/dev/null
npm run test:unit 2>/dev/null || npm test 2>/dev/null
```

Both must pass (or be explicitly absent) before the audit is considered complete.

---

## Step 7 — Write completion summary

Append to the bottom of `dependency-audit.md`:

```
## Audit completed [date]
Vulnerabilities fixed: N (CRITICAL: N, HIGH: N)
Packages removed: N
Duplicates resolved: N
Typecheck: PASS / FAIL / N/A
Tests: X/Y passing / N/A
```

Commit:
```bash
git add dependency-audit.md package.json package-lock.json
git commit -m "chore: dependency & security audit — [one-line summary]"
git push
```

Tell the user the summary in plain English — counts, what changed, anything that
needs their attention before merging.
