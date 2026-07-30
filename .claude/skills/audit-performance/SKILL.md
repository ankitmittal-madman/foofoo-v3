---
name: audit-performance-baseline
description: >
  Establishes a performance baseline against the project's own documented
  targets — app launch time, key user-facing operations, API/Edge Function
  response times. Generic — discovers performance targets from the project's
  own requirements docs rather than assuming fixed thresholds; if no targets
  are documented, asks the user rather than inventing numbers.

  Trigger: slash command /audit-performance only. Does not trigger automatically.
---

# Performance Baseline Audit Skill

Measures actual performance against documented targets, not invented ones —
performance targets are a product decision, not something this skill should
guess at.

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
/audit-performance
```
## Activation
- Activation Type: Manual
- Recommended Phase: Repository, Implementation, QA or/and Production

## Step 0 — Self-install check (run once per repo)

```bash
ls .claude/skills/audit-performance-baseline/SKILL.md 2>/dev/null && echo "INSTALLED" || echo "MISSING"
```

**If MISSING:** fetch from `ankitmittal-madman/dotfiles` →
`.claude/skills/audit-performance-baseline/SKILL.md` via GitHub MCP, write to
the same path in this repo, commit and push.

**If INSTALLED:** continue below directly.

---

## Step 1 — Find the project's documented performance targets

Do not assume any thresholds. Check the knowledge book first:

```bash
# Check knowledge-book first — NFR/performance targets belong in architecture core
ls knowledge-book/architecture/core/system-design.md 2>/dev/null
grep -rli "performance\|response time\|< [0-9]*\s*ms\|nfr\|non-functional" \
  knowledge-book/ 2>/dev/null
```

**If `knowledge-book/architecture/` contains performance targets:** read them
and use them as the authoritative source. This is the intended spec — use it.

**If nothing in knowledge-book:** search the broader codebase:

```bash
find . -iname "*non-functional*" -o -iname "*nfr*" -o -iname "*performance*requirement*" \
  -o -iname "*sla*" 2>/dev/null | grep -vE "node_modules|\.git|knowledge-book"

grep -rli "launch time\|response time\|< [0-9]*\s*ms\|< [0-9]*\s*sec" \
  --include=*.md --include=*.docx --include=*.txt . 2>/dev/null | grep -vE "node_modules|\.git"
```

**If a requirements doc with explicit numeric targets is found:** read it and
extract every target (metric name, threshold, condition).

**If multiple candidate docs are found and it's unclear which is authoritative:**
list them to the user and ask which one to use.

**If no documented targets exist anywhere:** tell the user explicitly that no
performance targets were found, and ask them to either point to the right doc
or provide the targets directly. Do not invent thresholds — a wrong
self-invented target makes the whole report misleading.

---

## Step 2 — Identify what to actually measure

From the targets found in Step 1, map each one to a measurable point in the
codebase. Common categories (only include what the project's targets
actually cover):

- **App/page launch or load time** — find the app's root entry point
  (e.g. `App.tsx`, `_layout.tsx`, `pages/_app.tsx`, `main.ts`) to instrument
- **Key user action response time** (e.g. a core interaction specific to this
  product) — find the relevant component/handler by searching for the
  feature name from the target doc
- **API / Edge Function / backend response time** — find the actual
  endpoint(s) referenced by name or by feature in the target doc
- **Batch/background job duration** — find the relevant scheduled
  function/cron job in the codebase

State your mapping (target → what you'll measure → where in the code) to the
user before instrumenting, so they can correct it if you've mapped a target
to the wrong place.

---

## Step 3 — Instrument and measure

For each mapped target, add lightweight timing — do not leave permanent
performance-logging code in without flagging it for removal/gating behind a
debug flag afterward:

```js
// Generic pattern — adapt variable names to the actual code found
const start = performance.now(); // or Date.now() in Node contexts
// ... operation ...
console.log(`[perf] {operation_name}: ${performance.now() - start}ms`);
```

Run each measured operation multiple times (5 is a reasonable default unless
the target doc specifies otherwise) and record each run.

For batch/background jobs that can't be run live in this environment (e.g. a
job designed for 10,000 production users), build the estimate analytically
from the per-unit timing instead of trying to run it at scale:

```
estimated_total = (total_units / batch_size) × (avg_time_per_batch + inter_batch_delay)
```

State the formula and inputs used so the estimate is auditable, not a black box.

---

## Step 4 — Write the report

`performance-baseline.md`:

| Metric | Target (source: doc/section) | Actual (avg of N runs) | Status |
|---|---|---|---|

Flag any metric exceeding its target as **NEEDS_OPTIMISATION**.

For analytically-estimated metrics (e.g. large-scale batch jobs), label the
row clearly as **ESTIMATED** rather than measured, and show the formula used.

---

## Step 5 — Clean up instrumentation

After measuring, ask the user whether to:
- Remove the added timing code entirely, or
- Keep it but gate it behind an existing debug/dev flag in the project

Do not leave raw `console.log` performance instrumentation in production code
paths without an explicit decision from the user.

---

## Step 6 — Completion summary

```
## Audit completed [date]
Metrics measured: N
Targets met: N
NEEDS_OPTIMISATION: N
Estimated (not directly measured): N
```

Commit:
```bash
git add performance-baseline.md
git commit -m "chore: performance baseline audit — [one-line summary]"
git push
```

Tell the user the summary in plain English — what's fast enough, what isn't,
and what's only an estimate vs measured.
