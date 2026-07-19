---
name: audit-rls-policies
description: >
  Verifies that Row Level Security (RLS) policies on every database table are
  not just enabled but actually correct — every table has working SELECT/INSERT/
  UPDATE policies, user data isolation is enforced, and reference tables remain
  readable. Generic — discovers the actual schema and table roles from the
  database itself rather than assuming a fixed table list.

  Trigger: slash command /audit-rls only. Does not trigger automatically.
---

# RLS Policy Correctness Audit Skill

A table can have RLS enabled with zero policies, which silently blocks ALL
access — the app gets empty results with no error. This audit catches that,
plus the opposite failure (policies too loose, leaking data across users).

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
/audit-rls
```

Modifying RLS policies is security-critical and must always be a deliberate,
reviewed action — never automatic.

## Activation
- Activation Type: Manual
- Recommended Phase: Repository, Implementation, QA or/and Production

---

## Step 0 — Self-install check (run once per repo)

```bash
ls .claude/skills/audit-rls-policies/SKILL.md 2>/dev/null && echo "INSTALLED" || echo "MISSING"
```

**If MISSING:** fetch from `ankitmittal-madman/dotfiles` →
`.claude/skills/audit-rls-policies/SKILL.md` via GitHub MCP, write to the same
path in this repo, commit and push.

**If INSTALLED:** continue below directly.

---

## Step 1 — Confirm prerequisites

This skill requires the **Supabase MCP** (or equivalent DB access) to run SQL
queries directly. If not available, tell the user and stop — do not guess at
schema from migration files alone, since live policy state can drift from
migrations.

---

## Step 2 — Discover the actual schema (do not assume a fixed table list)

```sql
SELECT 
  schemaname, tablename, policyname, permissive, roles, cmd, qual, with_check
FROM pg_policies 
WHERE schemaname = 'public'
ORDER BY tablename, cmd;
```

Also get the full table list, including which have RLS enabled at all:

```sql
SELECT schemaname, tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY tablename;
```

From this, build your own working list of every table in the project —
do not assume a count or a specific set of table names.

---

## Step 3 — Classify each table's role (discover, don't assume)

For each table, determine its likely role by inspecting its columns:

```sql
SELECT table_name, column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'public'
ORDER BY table_name, ordinal_position;
```

- **User-owned table**: has a `user_id` (or similar FK to the auth/users table) column
  → should restrict rows to their owner
- **Reference/lookup table**: no `user_id`-style column, holds shared data
  (e.g. categories, tags, catalogue items) → should typically be readable by
  all authenticated users, not row-restricted
- **Junction/join table**: composite of two foreign keys → inherits access
  pattern from its parent tables — check both sides

State your classification of each table to the user before proceeding, so they
can correct any misclassification before you flag false positives.

---

## Step 4 — Verify each table against its expected pattern

**For user-owned tables**, verify:
- a) At least one SELECT policy exists allowing authenticated users to read
     their own rows
- b) Users CANNOT read another user's rows — the policy's `qual` must contain
     an `auth.uid()` comparison against the owning column
- c) A service-role bypass exists if backend functions need full access
     (for edge/serverless functions)

**For reference/lookup tables**, verify:
- They are readable by all authenticated users, not accidentally restricted
  by a `user_id` or ownership check that doesn't apply to them

**For junction tables**, verify:
- Access is governed correctly via the parent table's ownership, either
  directly or via a `EXISTS` subquery check

---

## Step 5 — Flag and classify findings

- Table with RLS enabled but **zero SELECT policies** → **CRITICAL** (silent
  total access block)
- Table with a policy missing the `auth.uid()` ownership check → **HIGH**
  (data leak risk)
- Reference table accidentally restricted by `user_id` → **HIGH** (breaks
  legitimate shared-data access)
- Table with RLS **disabled** entirely and containing user data → **CRITICAL**

Write `rls-audit.md`:

| Table | Role (user-owned/reference/junction) | Policies count | SELECT ok | INSERT ok | UPDATE ok | Status |
|---|---|---|---|---|---|---|

---

## Step 6 — Present findings before fixing

Show the full report to the user first. Only after confirmation, fix:
- Missing SELECT policies on user-owned tables
- Policies missing the `auth.uid()` check
- Reference tables incorrectly restricted

Do not silently rewrite security policy — security changes always get shown
to the user before being applied, even for "obvious" fixes.

---

## Step 7 — Test cross-user isolation after fixing

Where the platform/test setup allows it, run a practical isolation test:

```sql
-- Conceptual flow — adapt to actual test users available in the project
-- 1. Insert a row as user_A
-- 2. Attempt SELECT as user_B — must return 0 rows
-- 3. Confirm user_A can still SELECT their own row — must return 1 row
```

If no test user infrastructure exists in the project, note this as a MANUAL
follow-up in the report rather than fabricating a test.

---

## Step 8 — Completion summary

Append to `rls-audit.md`:

```
## Audit completed [date]
Tables audited: N
CRITICAL findings: N (fixed: N)
HIGH findings: N (fixed: N)
Cross-user isolation test: PASS / FAIL / MANUAL (not run)
```

Commit:
```bash
git add rls-audit.md supabase/migrations/ 2>/dev/null
git commit -m "fix: RLS policy correctness audit — [one-line summary]"
git push
```

Tell the user the summary in plain English, emphasising any CRITICAL findings
clearly since these mean real data was either inaccessible or leaking.
