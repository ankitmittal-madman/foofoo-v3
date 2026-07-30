---
name: audit-onboarding-funnel
description: >
  Walks the actual onboarding/first-run code path and reports every point a
  new user could silently get stuck or drop off — validation traps, infinite
  loaders, dead-end error states, missing back/exit paths. Generic —
  discovers the onboarding flow from the project's own routing structure
  rather than assuming a fixed number of steps.

  Trigger: slash command /audit-onboarding-funnel only. Does not trigger automatically.
---

# Onboarding Funnel Audit Skill

Most early-stage apps lose more users to a confusing first five minutes than
to any backend bug. This audit doesn't run the app — it reads the actual
onboarding code path and reasons about every state a real user could end up
stuck in, the way a careful human QA pass would, but exhaustively and for
every screen.

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
/audit-onboarding-funnel
```
## Activation
- Activation Type: Manual
- Recommended Phase: Repository, Implementation, QA or/and Production
  
## Step 0 — Self-install check (run once per repo)

```bash
ls .claude/skills/audit-onboarding-funnel/SKILL.md 2>/dev/null && echo "INSTALLED" || echo "MISSING"
```

**If MISSING:** fetch from `ankitmittal-madman/dotfiles` →
`.claude/skills/audit-onboarding-funnel/SKILL.md` via GitHub MCP, write to
the same path in this repo, commit and push.

**If INSTALLED:** continue below.

---

## Step 1 — Check for a documented onboarding spec first

Before reading any code, check if the project has a written onboarding spec:

```bash
ls knowledge-book/product/specs/*/product-spec.md 2>/dev/null | head -5
ls knowledge-book/qa/specs/*/test-plan.md 2>/dev/null | head -5
```

**If onboarding-related specs exist** (e.g. `knowledge-book/product/specs/
001-onboarding/product-spec.md` or a corresponding QA test plan): read them
first. They define the *intended* flow — what screens were planned, what
each step should do, and what was considered a success state. The audit then
checks whether the actual code matches the spec. Gaps between spec and code
are themselves findings (either the spec is stale, or the code never fully
implemented the intent).

**If no spec exists:** proceed to discover the flow from code only (Step 2).
Note this as a gap — a written onboarding spec in `knowledge-book/product/
specs/` would make this audit and future QA significantly more reliable.

---

## Step 2 — Discover the actual onboarding flow from code

Don't assume a fixed step count or names. Discover the real flow:

```bash
# File-based routing conventions — adapt to the project's actual router
find . -path "*onboarding*" -o -path "*(onboarding)*" -o -path "*sign-up*" \
  -o -path "*welcome*" -o -path "*intro*" 2>/dev/null | grep -vE "node_modules"
```

Read the entry point (e.g. app root / index route) to find how it decides
whether to route a user into onboarding vs. straight to the main app —
this decision logic is itself a common source of bugs (e.g. a user who
half-completed onboarding getting stuck in a routing loop).

Build an ordered map of every screen in the flow, including auth screens
(sign-up, email verification, sign-in) if they're part of first-run.

State the discovered flow to the user before proceeding, so they can correct
your map if you've misread the routing.

---

## Step 3 — Walk every screen for drop-off risk

For each screen in the discovered flow, read its actual code and check:

**Validation traps**
- Can a validation error message be unclear or missing entirely (user sees
  a disabled button with no explanation)?
- Are there fields with strict validation but no inline guidance on the
  expected format before the user fails?

**Loading/async states**
- Every async operation (API call, auth check) — does it have a timeout or
  can it spin forever on a slow/failed network?
- Is there a visible loading indicator, or could the screen look frozen?

**Error states**
- If an API call fails, does the user see a way forward (retry button,
  clear message) or a dead end?
- Network failure specifically — is it distinguished from a validation
  error, or does it show a confusing generic message?

**Navigation/exit paths**
- Can the user go back from every step, or are some steps a one-way door?
- If the user closes the app mid-flow and reopens it, where do they land —
  back at step 1 (frustrating), or resumed correctly?
- Is there any way to skip a non-essential step, or is everything forced
  sequential even where it doesn't need to be?

**Silent failures**
- Does any step write to the backend (e.g. save partial profile data)
  without confirming the write succeeded before advancing the UI?
- Are there any `.catch(() => {})` or swallowed errors in the onboarding
  path specifically (these are especially costly here since the user has no
  established trust yet to tolerate a silent failure)?

---

## Step 4 — Check the resume logic specifically

Onboarding resume (returning to an interrupted flow) is a uniquely common
bug source. Find the resume logic:

```bash
grep -rn "onboarding_step\|onboardingStep\|resume" --include=*.{ts,tsx} . \
  | grep -vE "node_modules"
```

Verify:
- Does it correctly compute "next step" from stored progress, or could it
  ever compute an out-of-range step (off-by-one, hardcoded max)?
- If the stored step references something that no longer exists (e.g. a
  step that was removed/renumbered in a later release), what happens? —
  this is a real regression risk as the flow evolves over sprints

---

## Step 5 — Write the report

`ops/audits/audit-onboarding/onboarding-funnel-audit-[date].md`:

```markdown
# Onboarding Funnel Audit — [date]
Spec found: [path or "none — gap flagged"]
Flow discovered: [ordered list of screens]

## Spec vs code gaps (if spec exists)
| Spec item | Code status | Notes |
|---|---|---|

## Drop-off risks found
| Screen | Risk type | Description | Severity | Suggested fix |
|---|---|---|---|---|

## Resume logic
Status: [verified safe / issues found]
```

Severity guide:
- **CRITICAL** — a real user can get fully stuck with no way forward (true
  dead end)
- **HIGH** — confusing/silent failure that would likely cause abandonment
  but isn't a hard dead end
- **MEDIUM** — friction that costs conversion but isn't broken
- **LOW** — polish item

---

## Step 6 — Present before fixing

Show the report first. Some findings (e.g. "should this step be skippable")
are product decisions, not pure bugs — ask before changing UX flow, even
where the technical fix is obvious.

After confirmation, apply fixes for confirmed CRITICAL/HIGH items.

---

## Step 7 — Verify

```bash
npm run typecheck 2>/dev/null
npm run test:unit 2>/dev/null || npm test 2>/dev/null
```

This skill cannot run a real device/browser walkthrough — note in the
summary that a manual click-through of the fixed paths is still recommended
before considering this fully verified.

---

## Step 8 — Completion summary

```
## Audit completed [date]
Spec found: Yes / No (gap flagged)
Screens audited: N
Spec vs code gaps: N
CRITICAL drop-off risks: N (fixed: N)
HIGH risks: N (fixed: N)
Resume logic: [status]
```

Commit:
```bash
git add ops/audits/audit-onboarding/ -A
git commit -m "fix: onboarding funnel — [N] drop-off risks addressed"
git push
```

Tell the user clearly which findings are true dead-ends a real user could
hit, versus polish — lead with the dead-ends.
