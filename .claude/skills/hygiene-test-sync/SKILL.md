---
name: hygiene-test-sync
description: >
  Ensures a test/mirror module stays synchronized with the real application
  logic it's testing against — catches drift in business logic, scoring
  weights, constraint rules, or type definitions between the source of truth
  and its test mirror. Generic — discovers what the test suite mirrors and
  what the actual source of truth is from the project's own structure,
  rather than assuming a fixed pair of files.

  Trigger: slash command /hygiene-testsync only. Does not trigger automatically.
  REQUIRES a test module to already exist — this skill does not create one.
---

# Test-App Sync Hygiene Skill

Some projects maintain a separate test harness that re-implements core logic
(e.g. a scoring algorithm) to test against, independent of importing the real
implementation. This is powerful for testing but creates a real risk: the
mirror drifts from the real thing silently. This skill catches that drift.

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
/hygiene-testsync
```
## Activation
- Activation Type: Manual
- Recommended Phase: Repository, Implementation, QA or/and Production

## Prerequisite — this skill needs a test mirror to exist

If the project has no separate test mirror of business logic (most projects
test by importing the real code directly, which can't drift) — tell the user
this skill doesn't apply and stop. Don't fabricate a sync target.

---

## Step 0 — Self-install check (run once per repo)

```bash
ls .claude/skills/hygiene-test-sync/SKILL.md 2>/dev/null && echo "INSTALLED" || echo "MISSING"
```

**If MISSING:** fetch from `ankitmittal-madman/dotfiles` →
`.claude/skills/hygiene-test-sync/SKILL.md` via GitHub MCP, write to the same
path in this repo, commit and push.

**If INSTALLED:** continue below.

---

## Step 1 — Discover the source of truth and its mirror

Don't assume specific file names or paths. Discover the pattern:

```bash
# Look for a separate test project/folder with its own re-implementation
find . -maxdepth 2 -type d -iname "*test*" 2>/dev/null | grep -vE "node_modules|__tests__"

# Within a candidate test folder, look for files that re-declare types/logic
# also present in the main source (same interface/function names, different file)
```

Ask the user to confirm which is the **source of truth** (the real,
deployed implementation) and which is the **mirror** (the test
re-implementation) if it's not unambiguous from the folder structure —
getting this backwards means "fixing" the real code to match a stale test,
which is the opposite of what this skill should do.

State explicitly: *"The mirror is always updated to match the source of
truth. The source of truth is never changed by this skill."*

---

## Step 2 — Compare logic/constants between source and mirror

For whatever core logic the mirror re-implements (commonly: scoring
weights, constraint/filter rules, threshold constants, type interfaces),
do a structured comparison:

**Numeric constants / weights:**
- Extract every named constant from the source of truth
- Extract the corresponding constant from the mirror
- Flag any value mismatch as `WEIGHT_MISMATCH` (or more generically
  `CONSTANT_MISMATCH`)

**Logic/rules:**
- For each piece of conditional logic in the source (filters, exclusions,
  eligibility checks), find the equivalent in the mirror
- Flag any difference in the actual condition (not just formatting) as
  `LOGIC_MISMATCH`

**Type definitions:**
- Compare interface/type shapes between source and mirror
- Flag missing fields, extra fields, or type differences

---

## Step 3 — Check for stale test fixtures referencing old data

Test fixtures/persona definitions can reference data that no longer exists
(renamed entities, removed fields, old IDs). Check:

```bash
# Find fixture/persona definition files in the test area
grep -rln "persona\|fixture\|mock.*data" {test_directory} 2>/dev/null
```

For each fixture referencing named entities (e.g. specific product/dish
names, category names), spot-check whether those names still exist in the
current schema/seed data. Flag any that don't as a stale reference, with
the exact line that needs updating.

---

## Step 4 — Write the report

`logs/hygiene-reports/test-sync-audit.md`:

```markdown
# Test-App Sync Audit — [date]
Source of truth: [path]
Mirror: [path]

## Constant/weight mismatches
| Constant | Source value | Mirror value | Status |
|---|---|---|---|

## Logic mismatches
| Rule | Source behavior | Mirror behavior | Status |
|---|---|---|---|

## Stale fixture references
| File | Line | Reference | Issue |
|---|---|---|---|
```

---

## Step 5 — Apply sync fixes

Unlike other hygiene skills, sync fixes are corrections toward an already-
confirmed source of truth, not judgement calls — apply them directly once
the user has confirmed the source-of-truth/mirror direction in Step 1.

Update the mirror only. Never modify the source of truth as part of this
skill.

After applying:
```bash
npm run typecheck 2>/dev/null
npm run test:unit 2>/dev/null || npm test 2>/dev/null
```

Confirm previously-passing tests still pass — a sync fix that breaks
existing tests needs investigation before committing, since it may mean the
mismatch was intentional (an undocumented variant) rather than drift.

---

## Step 6 — Completion summary

Append to `logs/hygiene-reports/test-sync-audit.md`:

```
## Completed [date]
Constant mismatches fixed: N
Logic mismatches fixed: N
Stale fixtures fixed: N
Typecheck: PASS / FAIL
Tests: X/Y passing
```

Commit:
```bash
git add -A
git commit -m "fix: test-app sync — [N] mismatches corrected"
git push
```

Tell the user what drifted and what's now back in sync.
