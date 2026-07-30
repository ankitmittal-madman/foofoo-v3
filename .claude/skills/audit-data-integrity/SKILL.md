---
name: audit-data-integrity
description: >
  Runs referential integrity and data completeness checks across the database —
  foreign key violations, orphaned records, NULL/empty fields that would cause
  silent application failures. Generic — discovers foreign key relationships
  and likely-critical NOT NULL fields from the schema itself rather than
  assuming a fixed table/column list.

  Trigger: slash command /audit-data-integrity only. Does not trigger automatically.
---

# Data Integrity Checks Audit Skill

Checks the actual data in the database for problems that won't show up as
errors — orphaned foreign keys, NULLs in fields the application logic depends
on, and incomplete records that will cause silent failures or be silently
excluded from features (e.g. a recommendation engine, a search index, a
matching algorithm).

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
/audit-data-integrity
```
## Activation
- Activation Type: Manual
- Recommended Phase: Repository, Implementation, QA or/and Production

## Step 0 — Self-install check (run once per repo)

```bash
ls .claude/skills/audit-data-integrity/SKILL.md 2>/dev/null && echo "INSTALLED" || echo "MISSING"
```

**If MISSING:** fetch from `ankitmittal-madman/dotfiles` →
`.claude/skills/audit-data-integrity/SKILL.md` via GitHub MCP, write to the
same path in this repo, commit and push.

**If INSTALLED:** continue below directly.

---

## Step 1 — Confirm prerequisites

Requires Supabase MCP (or equivalent DB access) to run SQL directly. If
unavailable, tell the user and stop.

---

## Step 2 — Discover foreign key relationships (do not assume specific tables)

```sql
SELECT
  tc.table_name AS child_table,
  kcu.column_name AS fk_column,
  ccu.table_name AS parent_table,
  ccu.column_name AS parent_column
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
  ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage ccu
  ON tc.constraint_name = ccu.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema = 'public';
```

Also check for **self-referencing columns that look like foreign keys but
aren't formally constrained** — common pattern: a column named
`*_id` (e.g. `parent_dish_id`, `category_id`) with no actual FK constraint in
the schema. These are exactly the kind that silently rot, since the database
won't stop bad data from being inserted. Find them:

```sql
SELECT table_name, column_name
FROM information_schema.columns
WHERE table_schema = 'public'
  AND column_name LIKE '%\_id'
  AND table_name NOT IN ('information_schema');
```

Cross-reference against the formal FK list from above — any `*_id` column NOT
in that list is an informal/unenforced reference worth checking manually.

---

## Step 3 — Run referential integrity checks

For every formal FK relationship found in Step 2, run the general pattern:

```sql
SELECT COUNT(*) FROM {child_table} c
WHERE c.{fk_column} IS NOT NULL
AND NOT EXISTS (SELECT 1 FROM {parent_table} p WHERE p.{parent_column} = c.{fk_column});
```

For every informal `*_id` column found (not formally constrained), run the
same check against its likely parent table (inferred from the column name,
e.g. `dish_id` → `dishes` table) — but state your inference to the user, since
this is a best guess, not a guarantee.

Report the count of violations for each relationship checked.

---

## Step 4 — Data completeness checks (discover likely-critical fields)

Look for signals of which NULL-able fields are actually critical to the
application's core logic — these typically show up as:
- `WHERE column IS NOT NULL` or `column IS NULL` filters in application code
  or SQL functions/views (search the codebase for these patterns against each
  table's columns)
- Columns referenced in matching, filtering, search, or recommendation logic

```bash
# Find code that filters on NULL-ness of specific columns — a strong signal
# that NULL in that column causes a silent functional failure
grep -rn "IS NOT NULL\|IS NULL\|!= null\|=== null\|?? \[\]\||| \[\]" \
  --include=*.{ts,js,sql} . | grep -vE "node_modules|\.git"
```

For each such field identified, run:

```sql
SELECT id, {identifying_column} FROM {table} WHERE {field} IS NULL;
SELECT id, {identifying_column} FROM {table} WHERE {array_field} = '{}' OR {array_field} IS NULL;
```

Also check for **rows with zero related child records**, where the application
logic implies every row should have at least one (e.g. a catalogue item with
no linked attributes/tags) — discover this expectation the same way, by
checking what the code joins against.

---

## Step 5 — Fix or flag

For each violation found:
- **Count < 5**: present the specific rows to the user and propose a fix; only
  apply automatically if it's an unambiguous correction (e.g. clearly orphaned
  test data) — otherwise still ask first
- **Count >= 5**: do not attempt auto-fix. Write all violating IDs to
  `data-integrity.md` for manual review — bulk data issues usually need human
  judgement about the right fix (delete vs backfill vs reassign)

---

## Step 6 — Write the report

`data-integrity.md`:

```markdown
## Referential Integrity
| Relationship | Violations | Severity |
|---|---|---|

## Informal References (unenforced *_id columns)
| Column | Inferred parent table | Violations found | Note |
|---|---|---|---|

## Data Completeness
| Table.Field | NULL/empty count | Why this matters | Severity |
|---|---|---|---|
```

---

## Step 7 — Completion summary

```
## Audit completed [date]
FK relationships checked: N
Violations found: N (auto-fixed: N, flagged for review: N)
Completeness issues found: N
```

Commit:
```bash
git add data-integrity.md
git commit -m "chore: data integrity audit — [one-line summary]"
git push
```

Tell the user the summary in plain English — what's broken, what was fixed,
and what needs their manual decision.
