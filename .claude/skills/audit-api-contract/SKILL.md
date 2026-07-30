---
name: audit-api-contract
description: >
  Verifies that frontend code and backend endpoints (Edge Functions, API
  routes) actually agree on request and response shapes. Catches the most
  common cause of "works on staging, breaks in prod" bugs — client and
  backend edited in separate sessions drifting out of sync. Generic —
  discovers the actual contract points from the codebase rather than
  assuming fixed endpoint names.

  Trigger: slash command /audit-api-contract only. Does not trigger automatically.
---

# API Contract Audit Skill

Backend and frontend code are often written in separate Claude Code sessions
days apart. Neither session sees the other's full context. This is exactly
the condition that produces silent contract drift — a field renamed on one
side, an optional field that became required, a response shape that changed
shape without the client being told. This skill finds that drift before a
user does.

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
/audit-api-contract
```

## Activation
- Activation Type: Manual
- Recommended Phase: Repository, Implementation, QA or/and Production

## Step 0 — Self-install check (run once per repo)

```bash
ls .claude/skills/audit-api-contract/SKILL.md 2>/dev/null && echo "INSTALLED" || echo "MISSING"
```

**If MISSING:** fetch from `ankitmittal-madman/dotfiles` →
`.claude/skills/audit-api-contract/SKILL.md` via GitHub MCP, write to the
same path in this repo, commit and push.

**If INSTALLED:** continue below.

---

## Step 1 — Check for a documented contract baseline first

Before reading any code, check if the project maintains a written API
contract document:

```bash
ls knowledge-book/architecture/core/api-contracts.md 2>/dev/null && echo "EXISTS" || echo "NONE"
```

**If `knowledge-book/architecture/core/api-contracts.md` exists:** read it
first. This is the *stated* contract — what the team intended. The audit
then compares the actual code against this stated contract, which is a
stronger check than code-to-code comparison alone. Any drift between the
doc and the code is itself a finding (either the doc is stale, or the code
regressed — the user decides which).

**If no doc exists:** proceed to discover contracts from code only (Step 2).
Note this as a gap in the report — maintaining `knowledge-book/architecture/
core/api-contracts.md` as a living document would make future audits
significantly more reliable.

---

## Step 2 — Discover every contract point from code (don't assume a fixed endpoint list)

```bash
# Backend handlers — adapt to whichever pattern(s) the project actually uses
find . -path "*/supabase/functions/*" -name "index.ts" 2>/dev/null
find . -path "*/pages/api/*" -o -path "*/app/api/*" 2>/dev/null
find . -path "*/.netlify/functions/*" 2>/dev/null

# Client-side call sites — where the frontend actually invokes each backend endpoint
grep -rln "supabase\.functions\.invoke\|fetch(.*\/api\/\|axios\." \
  --include=*.{ts,tsx} . 2>/dev/null | grep -vE "node_modules"
```

Build a list of every (backend handler ↔ client call site) pair. Not every
backend handler necessarily has a client caller in this repo (it might be
called by a cron job, another service, or be genuinely orphaned — note
those separately, don't force-pair them).

State the full list of discovered pairs to the user before proceeding.

---

## Step 3 — Extract the backend's actual contract

For each backend handler, read the actual code (not just type annotations —
the real `return`/`res.json`/response-building logic) to determine:

- **Request shape it expects** — required fields, optional fields, types
- **Success response shape** — exact fields and types returned
- **Error response shape** — does it follow a consistent error format
  (discover the project's standard the same way `audit-edge-functions` does
  — check docs first, then existing shared error-handling code)
- **Status codes used** for different outcomes

If the project has explicit TypeScript types/interfaces for request/response
(e.g. in a shared types file), use those as the stated contract — but verify
the actual runtime code matches what the type claims, since types can drift
from implementation too.

---

## Step 4 — Extract the client's actual expectations

For each client call site, read the actual code to determine:

- **What fields it sends** in the request
- **What fields it reads** from the response (not just what the type says
  is available — what's actually accessed, e.g. `response.data.foo.bar`)
- **How it handles errors** — does it check for the backend's actual error
  shape, or assume something else?
- **Does it handle every status code** the backend can actually return, or
  only the happy path?

---

## Step 5 — Compare and flag drift

For each pair, compare backend-actual against client-actual:

| Drift type | Example | Severity |
|---|---|---|
| Field renamed on one side | Backend returns `userId`, client reads `user_id` | CRITICAL |
| Field removed but still read | Client reads a field the backend stopped returning | CRITICAL |
| Required field not sent | Backend expects a field the client never sends | CRITICAL |
| Type mismatch | Backend returns a number, client expects a string | HIGH |
| New optional field unused | Backend added a field, client doesn't use it yet | LOW (not a bug, just noted) |
| Error shape mismatch | Client checks for an error format the backend doesn't actually produce | HIGH |
| Unhandled status code | Backend can return 429, client has no handling for it | MEDIUM |

For orphaned handlers (no client caller found in this repo), list separately
with a note: confirm whether they're called externally (cron, other service)
or are genuinely dead — don't auto-classify, since this skill isn't the dead
code skill and shouldn't make that call.

---

## Step 6 — Write the report

`ops/audits/audit-api-contract/api-contract-audit-[date].md`:

```markdown
# API Contract Audit — [date]

## Contract pairs checked: N
## Orphaned handlers (no client caller found in this repo): N

## Drift findings
| Endpoint | Client file | Drift type | Severity | Detail |
|---|---|---|---|---|
```

---

## Step 7 — Present before fixing

Show the full report first. Drift fixes touch both client and backend code
and can be ambiguous about which side is "correct" (sometimes the backend
changed intentionally and the client is stale; sometimes the reverse) — the
user should confirm direction for each CRITICAL/HIGH finding before any fix
is applied, the same way `hygiene-test-sync` requires direction confirmation.

After confirmation, apply fixes to whichever side is actually wrong (not
always the client — sometimes the backend regressed).

---

## Step 8 — Verify after fixing

```bash
npm run typecheck 2>/dev/null
npm run test:unit 2>/dev/null || npm test 2>/dev/null
```

If the project has any integration/contract tests specifically, run those
too — they're the most direct verification for this exact class of bug.

---

## Step 9 — Completion summary

```
## Audit completed [date]
Contract baseline doc found: Yes / No (gap flagged)
Contract pairs checked: N
CRITICAL drift found: N (fixed: N)
HIGH drift found: N (fixed: N)
Orphaned handlers flagged: N
Typecheck: PASS / FAIL
Tests: X/Y passing
```

Commit:
```bash
git add ops/audits/audit-api-contract/ -A
git commit -m "fix: API contract drift — [N] mismatches corrected"
git push
```

Tell the user plainly which drift was real (would have caused a production
bug) vs. cosmetic, and what's now aligned.
