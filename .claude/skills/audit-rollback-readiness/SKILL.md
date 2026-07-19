---
name: audit-rollback-readiness
description: >
  Before a risky production deploy, verifies a real rollback path actually
  exists — DB migrations have working Down scripts, the previous deployment
  is identifiable and re-deployable, and new behavior is flag-gated where
  appropriate. Generic — discovers the project's actual deploy/migration
  tooling rather than assuming a fixed setup.

  Trigger: slash command /audit-rollback-readiness only. Does not trigger automatically.
---

# Rollback Readiness Audit Skill

A deploy gate that asks the question that's easy to skip under launch
pressure: *if this goes wrong in production, how fast can we undo it, and
does that path actually work?* This audit verifies the rollback path exists
and is real — it does not perform the deploy itself.

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
/audit-rollback-readiness
```

Run this before any deploy the team considers risky — a new migration, a
major feature, anything touching the production database schema.

## Activation
- Activation Type: Manual
- Recommended Phase: Repository, Implementation, QA or/and Production

## Step 0 — Self-install check (run once per repo)

```bash
ls .claude/skills/audit-rollback-readiness/SKILL.md 2>/dev/null && echo "INSTALLED" || echo "MISSING"
```

**If MISSING:** fetch from `ankitmittal-madman/dotfiles` →
`.claude/skills/audit-rollback-readiness/SKILL.md` via GitHub MCP, write to
the same path in this repo, commit and push.

**If INSTALLED:** continue below.

---

## Step 1 — Identify what's actually changing in this deploy

```bash
# What's different between the current branch and what's live
git log --oneline {production_branch}..HEAD 2>/dev/null
git diff --name-status {production_branch}..HEAD 2>/dev/null
```

Check for deployment conventions in this order:

1. **`knowledge-book/operations/core/`** — deployment guide and environments
   docs are the authoritative source for branch conventions, rollback
   procedures, and environment definitions:
   ```bash
   ls knowledge-book/operations/core/deployment-guide.md \
      knowledge-book/operations/core/environments.md 2>/dev/null
   ```
   If found, read them before proceeding — they define what "production"
   means for this project, which environments exist, and any documented
   rollback procedures.

2. **`CLAUDE.md` / `SYSTEM_STATE.md`** — if knowledge-book docs don't exist,
   check these for protected branches and deployment mapping.

Use whatever is found to identify the actual production branch and what's
pending deploy.

Categorize the changes:
- Database migrations
- Backend/Edge Function changes
- Client/frontend changes
- Config/infra changes

---

## Step 2 — Check migration rollback safety

For every new migration in this deploy:

```bash
ls supabase/migrations/ 2>/dev/null | tail -10
```

Check each new migration file for:
- **Is it reversible in principle?** (adding a column = reversible; dropping
  a column or table = often NOT safely reversible without data loss — flag
  this explicitly, it's the highest-risk category)
- **Does a corresponding Down/rollback script exist** — check the project's
  actual migration convention (some store Down scripts as a paired file,
  some as a comment block, some don't have a formal Down convention at all
  — discover which, don't assume)
- **Is the migration additive-only** (the safest pattern — new columns/
  tables that don't break existing code if rolled back) or does it modify/
  remove existing structure that current production code depends on?

For any migration that is NOT safely reversible (drops data, removes a
column other live code reads), flag this as **CRITICAL** — these need an
explicit, deliberate rollback plan from the user, not an assumed one.

---

## Step 3 — Check deployment rollback path

Discover the actual deployment platform and check its rollback mechanism:

```bash
# Vercel
cat vercel.json 2>/dev/null

# Check recent deployment history if Vercel MCP is available
```

Verify:
- Is the currently-live deployment identifiable (a specific commit/
  deployment ID that can be redeployed if needed)?
- Does the platform support instant rollback to the previous deployment
  (most do — confirm this project's setup doesn't have anything unusual
  blocking that, like a migration that's already been applied and isn't
  backward compatible with the old code)

**The most common rollback trap:** code rolls back instantly, but the
database migration that went with it does not roll back automatically. If
the new migration changed something the *old* code depends on differently
than the *new* code does, rolling back the deploy alone can leave the app
broken against the now-mismatched database schema. Check explicitly for
this mismatch risk for every migration in this deploy.

---

## Step 4 — Check feature flag / kill-switch coverage

```bash
grep -rn "FEATURES\|FEATURE_FLAGS\|featureFlag" --include=*.{ts,tsx} . \
  | grep -vE "node_modules" | head -20
```

For new, risky, or major features in this deploy:
- Is the feature behind a flag that can be toggled off without a redeploy
  (fastest possible rollback for behavior, even before a code rollback)?
- If not flag-gated, is that an acceptable risk for this specific change,
  or should the user consider adding one before deploying?

Not every change needs a flag — small fixes don't. State this judgement
explicitly rather than flagging everything.

---

## Step 5 — Write the readiness report

`logs/hygiene-reports/rollback-readiness-[date].md`:

```markdown
# Rollback Readiness — [date]
Deploy scope: [branch/commit range]

## Migrations in this deploy
| Migration | Reversible? | Down script exists | Risk |
|---|---|---|---|

## Deployment rollback path
Platform: [discovered]
Previous deployment identifiable: Yes/No
Migration/code compatibility on rollback: [Safe / AT RISK — explain]

## Feature flag coverage
| Feature | Flag-gated | Recommendation |
|---|---|---|

## Overall verdict
READY TO DEPLOY / NOT READY — [reason] / READY WITH CAVEATS — [list]
```

---

## Step 6 — Do not deploy, do not modify migrations

This skill reports readiness — it does not execute a deploy and does not
write a missing Down script unprompted, since the right rollback behavior
for an irreversible migration (e.g. how to handle data that would be lost)
is a product decision, not something to invent silently.

If the user asks this skill to also create missing Down scripts, that's
fine to do — but always show the proposed script and explain what it does
and doesn't restore before applying it.

---

## Step 7 — Completion summary

```
## Readiness check completed [date]
Migrations checked: N (irreversible/risky: N)
Deployment rollback path: [Safe / At risk]
Flag coverage gaps: N
Verdict: [READY / NOT READY / READY WITH CAVEATS]
```

Commit only the report:
```bash
git add logs/hygiene-reports/rollback-readiness-*.md
git commit -m "docs: rollback readiness check — [verdict]"
git push
```

Tell the user the verdict first, plainly — then the detail. If NOT READY,
be specific about exactly what needs to happen before it would be.
