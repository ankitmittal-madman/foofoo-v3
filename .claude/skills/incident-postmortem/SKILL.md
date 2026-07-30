---
name: incident-postmortem
description: >
  Structures a resolved production incident into a proper postmortem —
  timeline, verified root cause, impact, and action items with owners.
  REPORT ONLY — produces documentation, never code changes (the fix itself
  should already be done via /debug-root-cause before this runs). Draws on
  the debug-log.md record if one exists for this incident.

  Trigger: slash command /incident-postmortem only. Does not trigger automatically.
---

# Incident Postmortem Skill

Turns a resolved incident into a structured record the team can learn from
— without re-litigating the fix (that's already done) and without assigning
blame to a person (the point is the system, not who touched it).

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
/incident-postmortem
```

This is always retrospective — run after an incident is resolved, not during
active firefighting (during active firefighting, use `/debug-root-cause`
directly).

## Activation
- Activation Type: Manual
- Recommended Phase: Repository, Implementation, QA or/and Production

## Step 0 — Self-install check (run once per repo)

```bash
ls .claude/skills/incident-postmortem/SKILL.md 2>/dev/null && echo "INSTALLED" || echo "MISSING"
```

**If MISSING:** fetch from `ankitmittal-madman/dotfiles` →
`.claude/skills/incident-postmortem/SKILL.md` via GitHub MCP, write to the
same path in this repo, commit and push.

**If INSTALLED:** continue below.

---

## ⚠️ Report only — this skill never changes code

If the underlying issue isn't actually fixed yet, say so and direct the user
to `/debug-root-cause` first. A postmortem written before the fix is
confirmed risks documenting a guess as a confirmed root cause.

---

## Step 1 — Gather what's already known

```bash
# Debug log from root-cause investigation (correct path per repo structure)
cat ops/logs/session-log/debug-log.md 2>/dev/null | tail -50
git log --oneline -10

# Check knowledge-book decisions log — helps establish what "correct" behavior was
ls knowledge-book/architecture/core/decisions-log.md 2>/dev/null
```

If a matching entry exists in `debug-log.md` for this incident, use it as
the foundation — root cause, evidence, and fix are already recorded there
from `/debug-root-cause`. Don't re-derive what's already confirmed.

**If `knowledge-book/architecture/core/decisions-log.md` exists:** check it
for any entries relevant to the affected area. Past architecture decisions
establish what the *intended* behavior was — critical for correctly stating
the root cause as a deviation from intent, not just a deviation from current
code behavior.

If no `debug-log.md` entry exists (the fix happened outside that skill, or
in a much earlier session), ask the user for:
- What broke and how it was first noticed
- When it started and when it was resolved
- What the actual fix was (files/commits)

---

## Step 2 — Build the timeline

Reconstruct, with actual timestamps where available (commit times, log
timestamps, deployment times — not estimates if real data exists):

- When the issue was introduced (if identifiable — which commit/deploy)
- When it was first detected (and how — user report, monitoring alert,
  manual discovery)
- When investigation started
- When root cause was confirmed
- When the fix was deployed
- When it was verified resolved

Gaps in this timeline (e.g. "introduced" unknown) are fine to leave as
"unknown" — don't fabricate precision that isn't there.

---

## Step 3 — State impact honestly

Discover actual impact where possible rather than assuming severity:

```bash
# If event/log tables exist, check actual affected scope for the incident window
```

Report:
- How many users/requests were actually affected (real number if
  determinable, otherwise honest estimate range with the basis stated)
- What the user-facing symptom was (in plain English — what did an actual
  user experience?)
- Whether any data was lost, corrupted, or needs backfill (this matters a
  lot more than most other impact dimensions — call it out prominently if
  applicable)

---

## Step 4 — Write the root cause section (verified, not guessed)

Pull directly from `debug-log.md` if available. The root cause statement
must be the **confirmed** one (with its evidence), never the first
hypothesis that was later revised — if the investigation went through a
wrong turn first (like a misattributed cause), it's worth noting that
explicitly as a "what we initially suspected vs. what was actually true" —
this is itself valuable learning, not something to hide.

---

## Step 5 — Identify what would have caught this sooner

This is the most valuable section for prevention, not the root cause itself.
Ask, based on the confirmed root cause:

- Would an existing audit skill have caught this if run beforehand? (e.g.
  would `/audit-rls` have caught this, would `/audit-api-contract` have
  caught this) — check honestly, don't force-fit
- Was there a missing test that would have caught this?
- Was there a missing monitoring/alert that would have surfaced it faster?
- Is this part of a broader pattern that `/debug-root-cause` flagged as a
  "pattern risk elsewhere" — if so, has that been addressed?

---

## Step 6 — Action items, with owners and no vague language

Every action item must be concrete and assigned, not aspirational:

**Bad:** "Improve error handling"
**Good:** "Add try/catch + ELIGIBLE_POOL_EMPTY error code to
generate-daily-plan — Owner: [name] — Before next deploy"

If an action item is "run `/audit-X` skill regularly going forward" — that's
acceptable and concrete (it's a defined, repeatable action), not vague.

---

## Step 7 — Write the postmortem

`logs/incident-reports/postmortem-[date]-[short-slug].md`:

```markdown
# Incident Postmortem — [one-line title]
Date: [date] | Severity: [Critical/High/Medium] | Status: Resolved

## Summary
[2-3 sentences — what happened, impact, current status]

## Timeline
| Time | Event |
|---|---|

## Impact
[Plain English — who/what was affected, any data impact]

## Root cause
[The confirmed statement, with evidence]

## What we initially suspected (if different from above)
[Optional — only if investigation took a wrong turn first]

## What would have caught this sooner
[Specific, honest answer — including "nothing currently in place would
have" if that's true]

## Action items
| Item | Owner | Status |
|---|---|---|

## Blameless note
This postmortem documents a system gap, not an individual mistake. The goal
is preventing recurrence, not assigning fault.
```

---

## Step 8 — Completion

Commit:
```bash
git add logs/incident-reports/ -A
git commit -m "docs: incident postmortem — [short title]"
git push
```

Tell the user the summary in plain English, leading with the root cause and
the most important action item — not the full timeline detail.
