---
name: audit-dpdp-compliance
description: >
  Audits the project for compliance risk under India's Digital Personal Data
  Protection Act 2023 (DPDP) — sensitive data leaking into third-party
  analytics/error-tracking, consent flow completeness, and data subject
  rights implementation (export, deletion, audit retention). Generic —
  discovers what counts as sensitive data and which third-party services are
  in use from the project itself, rather than assuming a fixed list.

  REPORT ONLY. This skill never applies fixes automatically, even for
  findings it is confident about — legal/regulatory compliance requires
  human and likely legal sign-off, not an AI judgement call applied silently.

  Trigger: slash command /audit-dpdp only. Does not trigger automatically.
---

# DPDP Legal Compliance Audit Skill

⚠️ **REPORT ONLY — THIS SKILL NEVER MODIFIES CODE OR DATA.**

This is a hard rule, not a default that can be overridden by a confident
finding or a user asking for auto-fix. A wrong call here is a legal risk, not
a bug. Every finding in this audit is a *recommendation for the user (and
likely their legal counsel) to act on* — never an automatic code change.

If the user asks this skill to "just fix it", decline and explain why:
compliance fixes need human/legal review of the proposed approach, not just
the code correctness that other audits can self-verify.

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
/audit-dpdp
```
## Activation
- Activation Type: Manual
- Recommended Phase: Repository, Implementation, QA or/and Production

## Step 0 — Self-install check (run once per repo)

```bash
ls .claude/skills/audit-dpdp-compliance/SKILL.md 2>/dev/null && echo "INSTALLED" || echo "MISSING"
```

**If MISSING:** fetch from `ankitmittal-madman/dotfiles` →
`.claude/skills/audit-dpdp-compliance/SKILL.md` via GitHub MCP, write to the
same path in this repo, commit and push.

**If INSTALLED:** continue below directly.

---

## Step 1 — Discover what counts as sensitive data in this project

Do not assume a fixed list of sensitive fields. DPDP treats certain
categories as sensitive (health data, financial data, biometric data,
genetic data, sexual orientation, religious/caste affiliation, among others)
— what's actually sensitive depends on what the product collects.

Check the knowledge book first — security and architecture docs often
explicitly classify sensitive data:

```bash
ls knowledge-book/architecture/core/security.md \
   knowledge-book/architecture/core/db-schema.md \
   knowledge-book/architecture/core/system-design.md 2>/dev/null
```

**If `knowledge-book/architecture/core/security.md` exists:** read it first.
Security docs often explicitly list sensitive fields, data classification
decisions, and consent design decisions made during architecture — this is
the most reliable source and avoids re-deriving what was already decided.

**If no knowledge-book security doc exists:** search the schema and codebase:

```bash
# Schema-level search for column names suggesting sensitive categories
grep -rniE "health|allerg|diet|religio|caste|disability|medical|biometric|sexual|financ|income|aadhaar|pan_number" \
  supabase/migrations/ 2>/dev/null

# Also check any data model / ERD docs for explicit sensitivity labels
find . -iname "*data*model*" -o -iname "*erd*" -o -iname "*schema*doc*" 2>/dev/null \
  | grep -vE "node_modules|\.git|knowledge-book"
```

Present your discovered list of likely-sensitive fields to the user and ask
them to confirm or correct it before proceeding — this classification
materially changes the rest of the audit, and getting it wrong either misses
real risk or wastes time chasing non-issues.

---

## Step 2 — Discover third-party services in use

```bash
grep -rlE "posthog|sentry|mixpanel|amplitude|segment|firebase.*analytics|datadog" \
  package.json 2>/dev/null

grep -rln "\.track(\|\.capture(\|captureException\|captureMessage\|\.identify(" \
  --include=*.{ts,tsx,js,jsx} . 2>/dev/null | grep -vE "node_modules"
```

List every third-party analytics/error-tracking/logging service found.

---

## RISK 1 — Sensitive data in third-party service payloads

For every call site found to any third-party service identified in Step 2,
inspect the payload/metadata/extra properties passed in. Check whether any
field from the sensitive-fields list (confirmed in Step 1) appears, directly
or nested.

If ANY sensitive field appears in a third-party payload: **CRITICAL_FINDING**

For each finding, document:
- File and line
- The third-party call (e.g. `posthog.capture(...)`, `Sentry.captureException(...)`)
- The exact sensitive field(s) found in the payload
- **Suggested fix pattern** (for the user to review and apply themselves —
  do not apply it):
  ```js
  // Example pattern only — user reviews and applies
  const sanitizeForAnalytics = (data) => {
    const { /* sensitive fields */, ...safe } = data;
    return safe;
  };
  ```

---

## RISK 2 — Consent flow completeness

Look for a consent-tracking table or mechanism:

```sql
-- Adapt table name based on what's actually found in the schema
SELECT COUNT(*) FROM information_schema.tables 
WHERE table_name ILIKE '%consent%';
```

If found, check:
- Is consent recorded at signup (a row exists for new users)?
- Is a consent version/timestamp being saved (so changes to consent terms
  are tracked, not just a boolean)?

Check the codebase for:
- A way for the user to **view** what consent was given
- A way for the user to **withdraw** consent (required under DPDP)

If no consent mechanism exists at all in a project that collects personal
data, flag this as **CRITICAL_FINDING** — this is a foundational requirement,
not an edge case.

---

## RISK 3 — Data subject rights implementation

Check for three required capabilities. Discover the actual implementation —
do not assume specific function/table names; search for the *concept*:

**A. Data export** — search for any export-related function:
```bash
grep -rli "export.*data\|data.*export\|gdpr.*export\|dsr.*export" \
  supabase/functions/ 2>/dev/null
```
If found, check what tables/data it actually includes — does it cover all
the personal data categories discovered in Step 1, or only some?

**B. Account deletion pipeline** — search for deletion-related logic:
```bash
grep -rli "delete.*account\|account.*delet\|soft.*delete\|deleted_at" \
  supabase/functions/ supabase/migrations/ 2>/dev/null
```
Check whether the discovered flow handles: soft delete → grace period →
cascade delete of personal data → anonymization of data needed for
legitimate retained purposes → deletion from the auth provider.

**C. Audit log retention** — search for any audit/log table and any
scheduled purge/cleanup job:
```bash
grep -rli "audit_log\|audit.*trail" supabase/migrations/ 2>/dev/null
grep -rli "cron\|pg_cron\|scheduled" supabase/functions/ supabase/migrations/ 2>/dev/null
```
Verify any audit log table is **exempt** from auto-purge jobs (DPDP requires
audit retention; other operational logs may have shorter retention by
design — confirm the audit log specifically isn't being swept up in a
generic retention job).

---

## Step 3 — Write the compliance report

`dpdp-compliance-report.md`:

| Risk | Finding | Severity | Recommended action | Status |
|---|---|---|---|---|

**Status is always one of:** `NEEDS USER REVIEW` or `NEEDS LEGAL REVIEW` —
never `FIXED`, since this skill does not apply fixes.

For CRITICAL_FINDING items specifically, add a clear note at the top of the
report flagging that these likely need legal counsel input, not just
engineering action.

---

## Step 4 — Completion summary

```
## Audit completed [date]
Sensitive fields confirmed: N
Third-party services checked: N
RISK 1 findings: N (CRITICAL: N)
RISK 2 findings: N
RISK 3 findings: N
NOTE: No fixes were applied. All findings require user/legal review.
```

Commit only the report — no code changes:
```bash
git add dpdp-compliance-report.md
git commit -m "docs: DPDP compliance audit — [N] findings, report only"
git push
```

Tell the user clearly: this is a report, not a fix. Walk through CRITICAL
findings first, and recommend legal review for anything involving sensitive
data exposure or consent mechanics.
