---
name: hygiene-secrets
description: >
  Maps every secret across env files, config files, and deployment configs —
  flags hardcoded secret values in source code. Generic — discovers what
  secrets the project actually uses rather than assuming fixed names. Never
  logs or displays actual secret values, only names and locations.

  Trigger: slash command /hygiene-secrets only. Does not trigger automatically.
---

# Secrets Hygiene Audit Skill

Finds where secrets live, confirms they're stored correctly, and flags any
hardcoded secret values committed to source — without ever printing the
actual secret value anywhere, including in this skill's own output.

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
/hygiene-secrets
```
## Activation
- Activation Type: Manual
- Recommended Phase: Repository, Implementation, QA or/and Production

## Step 0 — Self-install check (run once per repo)

```bash
ls .claude/skills/hygiene-secrets/SKILL.md 2>/dev/null && echo "INSTALLED" || echo "MISSING"
```

**If MISSING:** fetch from `ankitmittal-madman/dotfiles` →
`.claude/skills/hygiene-secrets/SKILL.md` via GitHub MCP, write to the same
path in this repo, commit and push.

**If INSTALLED:** continue below.

---

## ⚠️ Hard rule — never print secret values

Throughout this entire skill: list secret **names** only. Never echo, log,
print, or write an actual secret value anywhere — not in the terminal output,
not in the report file, not in a commit message. If a hardcoded value is
found, reference it by file+line, not by pasting the value into the report.

---

## Step 1 — Discover all env/config locations actually used

Don't assume fixed file names. Discover them:

```bash
find . -maxdepth 2 -iname ".env*" 2>/dev/null | grep -vE "node_modules"
find . -iname "*.toml" -o -iname "eas.json" -o -iname "vercel.json" 2>/dev/null | grep -vE "node_modules"
cat .gitignore 2>/dev/null
```

For each `.env*` file found, list only the **variable names** present
(never the values):
```bash
grep -oE "^[A-Z_][A-Z0-9_]*=" .env.local 2>/dev/null | sed 's/=$//'
```

Check `.gitignore` — confirm every `.env*` file (except any explicit
`.env.example`/`.env.*.example` template) is listed.

---

## Step 2 — Check for hardcoded secrets in source

Search for common secret-shaped patterns — adapt based on what services the
project actually integrates with (discover from `package.json` and env
variable names found in Step 1):

```bash
# JWT-shaped tokens
grep -rn "eyJ[A-Za-z0-9_-]\{10,\}" --include=*.{ts,tsx,js,jsx} . | grep -vE "node_modules"

# Common secret key prefixes (Stripe, generic API keys, etc.)
grep -rnE "sk_live_|sk_test_|AIza[A-Za-z0-9_-]{30,}|ghp_[A-Za-z0-9]{30,}" \
  --include=*.{ts,tsx,js,jsx} . | grep -vE "node_modules"

# Suspicious password/secret string assignments (not type defs)
grep -rniE "(password|secret|api_?key|token)\s*[:=]\s*['\"][^'\"]{8,}" \
  --include=*.{ts,tsx,js,jsx} . \
  | grep -vE "node_modules|type |interface |Props|process\.env"

# Any reference to a service name found in package.json, outside of process.env access
# — e.g. if Cloudinary is a dependency, flag any CLOUDINARY-related string that 
# isn't accessed via process.env
```

For each match, record: file, line, severity. **CRITICAL** if it looks like
a real secret value (not a variable name, not a type definition, not a
placeholder like `"your-api-key-here"`).

---

## Step 3 — Write the secrets map

`logs/hygiene-reports/secrets-map.md`:

```markdown
# Secrets Map — [date]

## Discovered secrets (names only)
| Secret name | Found in | Should be in (per project convention) | In .gitignore | Hardcoded anywhere |
|---|---|---|---|---|

## Hardcoded value findings
| File | Line | Pattern matched | Severity | Action needed |
|---|---|---|---|---|
```

Determine "should be in" by discovering the project's actual deployment
setup (check for Supabase Vault usage, EAS env references, Vercel env
settings) rather than asserting a fixed canonical pattern — state what you
found, and if no clear convention exists yet, note that as a gap rather than
inventing one.

---

## Step 4 — Flag critical issues, do not auto-fix

If any **actual secret value** (not just a name) appears in committed source:

- Mark **CRITICAL** in the report
- **Do not attempt to fix automatically.** A hardcoded secret in git history
  requires git history rewriting (or, more simply, immediate rotation of
  that credential) — both are consequential actions outside what this audit
  should do silently.
- Recommend to the user: rotate the credential immediately (treat it as
  compromised the moment it was committed, regardless of repo visibility),
  then remove it from current source, then decide separately whether git
  history needs cleaning.

---

## Step 5 — Completion summary

Append to `logs/hygiene-reports/secrets-map.md`:

```
## Completed [date]
Secrets discovered: N
Hardcoded findings: N (CRITICAL: N)
Files missing from .gitignore: N
```

Commit (the report only — never commit anything containing an actual secret
value):
```bash
git add logs/hygiene-reports/secrets-map.md .gitignore
git commit -m "chore: secrets hygiene audit — [N] findings"
git push
```

Tell the user clearly: any CRITICAL finding first, with the rotation
recommendation, before anything else in the summary.
