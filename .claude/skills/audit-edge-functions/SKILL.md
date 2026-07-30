---
name: audit-edge-functions
description: >
  Audits every backend serverless/edge function in the project against a
  standard error-handling matrix — auth failures, database errors, external
  API failures, empty-result states, and timeouts. Generic — discovers the
  project's actual error-response standard from its own docs rather than
  assuming one.

  Trigger: slash command /audit-edge-functions only. Does not trigger automatically.
---

# Edge Function Error Boundaries Audit Skill

A repeatable, on-demand audit that checks every serverless/edge function against
a complete error matrix, and fixes gaps without touching business logic.

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
/audit-edge-functions
```

It does not run automatically. Modifying error handling across every backend
function is consequential — this is always a deliberate action.

## Activation
- Activation Type: Manual
- Recommended Phase: Repository, Implementation, QA or/and Production
  
---

## Step 0 — Self-install check (run once per repo)

```bash
ls .claude/skills/audit-edge-functions/SKILL.md 2>/dev/null && echo "INSTALLED" || echo "MISSING"
```

**If MISSING:** fetch this skill file from `ankitmittal-madman/dotfiles` →
`.claude/skills/audit-edge-functions/SKILL.md` via GitHub MCP, write it to
`.claude/skills/audit-edge-functions/SKILL.md` in the current repo, commit:

```bash
git add .claude/skills/audit-edge-functions/
git commit -m "chore: install edge function audit skill"
git push
```

**If INSTALLED:** continue below directly.

---

## Step 1 — Find the project's error-handling standard (do not assume one)

Every project that has formal docs defines its own standard error response shape
and error codes. Check the knowledge book first, then code:

```bash
# Check knowledge-book first — architecture docs are the authoritative source
ls knowledge-book/architecture/core/system-design.md \
   knowledge-book/architecture/core/api-contracts.md \
   knowledge-book/architecture/core/security.md 2>/dev/null
```

**If `knowledge-book/architecture/core/` docs exist:** read them first and
extract the error-handling standard, response shapes, and defined error codes
from there. This is the stated intent — use it as the baseline.

**If no knowledge-book docs exist**, search the codebase:

```bash
# Look for technical architecture / API standards docs
find . -iname "*architecture*" -o -iname "*api-standard*" -o -iname "*error*handling*" 2>/dev/null \
  | grep -vE "node_modules|\.git|knowledge-book"

# Look for an existing shared error helper in code — often reveals the real standard
grep -rl "success.*false\|ApiError\|ErrorResponse" --include=*.{ts,js} . 2>/dev/null \
  | grep -vE "node_modules|\.git" | head -10
```

**If a docs file is found** (e.g. a Technical Architecture document, API style
guide, or similar): read it and extract:
- The standard success/error response shape
- The defined error codes
- Any explicitly documented failure modes (e.g. specific to that project's domain)

**If no docs file is found:** look for a shared error-handling utility already used
by multiple functions in the codebase — that's the de facto standard. Use it.

**If neither exists:** tell the user no standard was found, and propose a minimal
standard based on common practice:
```
Success: { success: true, data: { ... } }
Error:   { success: false, error: { code, message, retry, details } }
```
Ask for confirmation before proceeding with this as the standard, since introducing
a new standard is a bigger decision than auditing against an existing one.

---

## Step 2 — Locate every backend function

```bash
# Common locations across platforms — check whichever exists
find . -path "*/supabase/functions/*" -name "index.ts" 2>/dev/null
find . -path "*/functions/*" -name "*.ts" -o -path "*/api/*" -name "*.ts" 2>/dev/null
find . -path "*/.netlify/functions/*" 2>/dev/null
find . -path "*/pages/api/*" -o -path "*/app/api/*" 2>/dev/null
```

State which platform was detected (Supabase Edge Functions, Next.js API routes,
Netlify Functions, etc.) and list every function file found before proceeding.

---

## Step 3 — Audit every function against the error matrix

For each function found, check:

1. **Auth validation** — does it verify the auth token/session before doing
   anything else? (JWT check, session check, or equivalent for the platform)
2. **Database error handling** — are all database queries wrapped in
   try/catch (or equivalent), with failures returned in the standard error format?
3. **External API failure** — if the function calls any third-party API
   (weather, payment, email, AI providers, etc.), what happens when that API is
   down, slow, or returns an error? Does it fail gracefully or crash?
4. **Empty/null result handling** — if a query or computation can legitimately
   return nothing (empty pool, no matches, no data yet), does the function return
   a specific, named error/state for that — or does it crash or return a
   misleading success?
5. **Timeout handling** — does the function respect the platform's execution
   time limit, and return a clean error or partial result rather than hanging
   or crashing on timeout?
6. **Response format compliance** — does every code path (not just the happy
   path) return the standard format identified in Step 1?

---

## Step 4 — Write the audit report

Create or update `edge-function-audit.md`:

| Function | Auth check | DB errors caught | External API fallback | Empty/null handled | Timeout handled | Standard format | Missing coverage |
|---|---|---|---|---|---|---|---|

One row per function. Be specific in "Missing coverage" — name the exact gap, not
a generic note.

---

## Step 5 — Fix gaps (only after presenting the report — do not auto-apply silently)

Show the full report to the user first. Then, only if the user confirms:

- Add the missing error handling to each function
- **Do not change any business logic** — only add error boundaries around
  existing logic
- Every fixed code path must return the standard format from Step 1

After fixing each function:
- Redeploy it using the platform's deploy command (detect from `package.json`
  scripts or platform CLI — e.g. `supabase functions deploy [name]`)
- Write or run a test call confirming it returns the standard error format for
  at least one of its failure modes

---

## Step 6 — Completion summary

Append to `edge-function-audit.md`:

```
## Audit completed [date]
Functions audited: N
Functions with gaps found: N
Functions fixed: N
Functions redeployed: N
Remaining known gaps (if any, with reason): ...
```

Commit:
```bash
git add edge-function-audit.md supabase/functions/ 2>/dev/null
git commit -m "fix: edge function error boundaries — [one-line summary]"
git push
```

Tell the user the summary in plain English — how many functions were checked,
how many had real gaps, what was fixed, and anything still needing their decision.
