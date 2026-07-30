---
name: hygiene-dead-code
description: >
  Finds and removes unused functions, variables, commented-out blocks, stale
  console.log statements, and orphaned files/modules. Generic — scans the
  actual codebase for real usage rather than assuming specific file names.
  Classifies findings as auto-fixable vs needs-human-judgement (e.g. two
  competing implementations of the same feature).

  Trigger: slash command /hygiene-deadcode only. Does not trigger automatically.
---

# Dead Code Removal Skill

Finds dead code and ALWAYS shows a written report before removing anything —
even items it's confident are safe to delete.

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
/hygiene-deadcode
```
## Activation
- Activation Type: Manual
- Recommended Phase: Repository, Implementation, QA or/and Production

## Step 0 — Self-install check (run once per repo)

```bash
ls .claude/skills/hygiene-dead-code/SKILL.md 2>/dev/null && echo "INSTALLED" || echo "MISSING"
```

**If MISSING:** fetch from `ankitmittal-madman/dotfiles` →
`.claude/skills/hygiene-dead-code/SKILL.md` via GitHub MCP, write to the same
path in this repo, commit and push.

**If INSTALLED:** continue below.

---

## Step 1 — Find candidate dead code

```bash
# Find report output directory convention — use existing if present, else create
mkdir -p logs/hygiene-reports

# Functions/components exported but never imported elsewhere
# (search per-file: get every export, then grep the rest of the repo for an import of it)
grep -rn "^export " --include=*.{ts,tsx,js,jsx} . | grep -vE "node_modules|\.test\.|\.spec\."

# console.log statements outside of designated logger files
grep -rn "console\.\(log\|warn\|error\)" --include=*.{ts,tsx,js,jsx} . \
  | grep -vE "node_modules|logger\.ts|Logger\.ts|systemLogger"

# Commented-out code blocks (5+ consecutive comment lines containing code-like syntax)
grep -rn "^\s*//.*[;{}()]" --include=*.{ts,tsx,js,jsx} . | grep -vE "node_modules"

# TODO comments — check git blame date for staleness
grep -rn "TODO\|FIXME" --include=*.{ts,tsx,js,jsx} . | grep -vE "node_modules"
```

For every TODO/FIXME found, check its age:
```bash
git log -1 --format="%ad" --date=short -S "TODO" -- {file}
```
Flag any older than 30 days as stale.

---

## Step 2 — Verify each candidate, don't trust grep blindly

A grep hit is a *candidate*, not a finding. For every exported
function/component found with no apparent importer, double check:
- Is it used in a config file (jest config, babel config, app config)?
- Is it re-exported from an index file that something else imports?
- Is it a route/page file that Next.js/Expo Router loads by convention
  (file-based routing — these have no explicit import anywhere, that's normal)?

If genuinely zero references found anywhere → candidate confirmed.

**For orphaned files (entire file never imported):** before marking
"safe to remove", check if there are TWO competing implementations of the
same feature (e.g. one wired in, one orphaned parallel version) — this is a
NEEDS_REVIEW case, not a safe auto-delete, since the orphaned one might be
the more correct/newer one rather than genuinely dead.

---

## Step 3 — Write the report BEFORE touching anything

`logs/hygiene-reports/dead-code-audit.md`:

```markdown
# Dead Code Audit — [date]

## Summary
| Category | Found | Safe to remove | Needs review |
|---|---|---|---|
| Unused exports/functions | N | N | N |
| Unused files | N | N | N |
| Stray console.log | N | N | N |
| Stale commented-out code | N | N | N |
| Stale TODOs (30+ days) | N | N | N |

## Findings
| File | Line | Type | Content preview | Safe to remove | Reason |
|---|---|---|---|---|---|
```

For every "needs review" item, write a clear reason (e.g. "two competing
implementations exist — confirm which is canonical before deleting either").

**Present this report to the user. Do not proceed to Step 4 until they
confirm.**

---

## Step 4 — Apply only confirmed removals

After user confirmation:
- Remove every item marked "safe to remove: yes"
- Do NOT remove items marked "needs review" — those require an explicit
  separate decision from the user, item by item

---

## Step 5 — Verify nothing broke

```bash
npm run typecheck 2>/dev/null
npm run test:unit 2>/dev/null || npm test 2>/dev/null
```

If either fails:
- Identify which specific removal caused it
- Revert that one change
- Mark it `REVERTED — caused [typecheck/test] failure` in the report
- Continue verifying the rest

---

## Step 6 — Completion summary

Append to `logs/hygiene-reports/dead-code-audit.md`:

```
## Completed [date]
Items removed: N
Items reverted (caused failures): N
Items still needing review: N
Typecheck: PASS / FAIL
Tests: X/Y passing
```

Commit:
```bash
git add -A
git commit -m "chore: dead code cleanup — [one-line summary]"
git push
```

Tell the user plainly: what was removed, what's still pending their review,
whether everything still works.
